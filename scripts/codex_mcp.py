"""Call the official server through Codex's real MCP client (no LLM subtask).

Uses the experimental App Server API shipped with the installed Codex CLI.
The ephemeral context is never run as an agent and is not a sidebar task.
"""
import argparse
import asyncio
import base64
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CodexMCP:
    async def __aenter__(self):
        self.sequence = 0
        self.log = (ROOT / '.local/codex-app-server.log').open('ab')
        self.process = await asyncio.create_subprocess_exec(
            'codex', 'app-server', '--stdio', cwd=ROOT,
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            stderr=self.log, limit=32 * 1024 * 1024,
        )
        try:
            await self.rpc('initialize', {
                'clientInfo': {'name': 'blender-codex-lab', 'version': '0.1.0'},
                'capabilities': {'experimentalApi': True},
            })
            self.process.stdin.write(b'{"jsonrpc":"2.0","method":"initialized"}\n')
            context = await self.rpc('thread/start', {
                'cwd': str(ROOT), 'ephemeral': True,
            })
            self.thread_id = context['thread']['id']
        except BaseException:
            await self.__aexit__()
            raise
        return self

    async def __aexit__(self, *_):
        self.process.stdin.close()
        try:
            await asyncio.wait_for(self.process.wait(), 10)
        except asyncio.TimeoutError:
            self.process.terminate()
            await self.process.wait()
        self.log.close()

    async def rpc(self, method, params):
        self.sequence += 1
        request_id = self.sequence
        request = {'jsonrpc': '2.0', 'id': request_id, 'method': method, 'params': params}
        self.process.stdin.write((json.dumps(request) + '\n').encode())
        await self.process.stdin.drain()
        while True:
            line = await asyncio.wait_for(self.process.stdout.readline(), 330)
            if not line:
                raise RuntimeError('Codex App Server closed; see .local/codex-app-server.log')
            message = json.loads(line)
            if message.get('id') == request_id and 'method' not in message:
                if 'error' in message:
                    raise RuntimeError(json.dumps(message['error']))
                return message['result']
            if 'id' in message and 'method' in message:
                raise RuntimeError('Unexpected server request: ' + message['method'])

    async def inventory(self):
        cursor = None
        while True:
            page = await self.rpc('mcpServerStatus/list', {
                'threadId': self.thread_id, 'cursor': cursor,
            })
            for server in page['data']:
                if server['name'] == 'blender':
                    return server
            cursor = page.get('nextCursor')
            if not cursor:
                raise RuntimeError('Blender MCP missing from Codex live inventory')

    async def call(self, tool, arguments):
        response = await self.rpc('mcpServer/tool/call', {
            'threadId': self.thread_id, 'server': 'blender',
            'tool': tool, 'arguments': arguments,
        })
        if response.get('isError'):
            raise RuntimeError(json.dumps(response))
        for block in response['content']:
            if block.get('type') == 'text':
                try:
                    value = json.loads(block['text'])
                except json.JSONDecodeError:
                    continue
                if isinstance(value, dict) and value.get('status') == 'error':
                    raise RuntimeError(json.dumps(value))
        return response


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['inspect', 'execute', 'screenshot'])
    parser.add_argument('--file', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--script-action', help='Optional action string exposed to the Blender script')
    args = parser.parse_args()
    if args.output and not args.output.resolve().is_relative_to(ROOT):
        parser.error('Output must stay inside this repository')
    async with CodexMCP() as client:
        inventory = await client.inventory()
        if args.action == 'inspect':
            result = {'name': inventory['name'], 'tools': inventory['tools']}
        elif args.action == 'execute':
            if not args.file:
                parser.error('execute requires --file')
            script = args.file.resolve()
            if not script.is_relative_to(ROOT):
                parser.error('Only scripts inside this repository may be executed')
            prefix = f'__file__ = {str(script)!r}\n'
            if args.script_action:
                prefix += f'PRODUCT_VIDEO_ACTION = {args.script_action!r}\n'
            code = prefix + script.read_text()
            result = await client.call('execute_blender_code', {'code': code})
        else:
            result = await client.call('get_screenshot_of_window_as_image', {})
            if not args.output:
                parser.error('screenshot requires --output')
            for block in result['content']:
                if block.get('type') == 'image':
                    args.output.write_bytes(base64.b64decode(block['data']))
                    print('Saved MCP screenshot:', args.output)
                    return
            raise RuntimeError('No image returned')
        output = json.dumps(result, indent=2, ensure_ascii=False)
        if args.output:
            args.output.write_text(output + '\n')
        else:
            print(output)


if __name__ == '__main__':
    asyncio.run(main())
