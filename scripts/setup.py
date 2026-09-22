"""Install the pinned official Blender Lab release into this project only."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'https://projects.blender.org/lab/blender_mcp.git'
REVISION = '2cea8d566dde07fbac28a61d698909d69724e853'
VERSION = '1.0.3'
ADDON_SHA256 = 'a7a9da816192502e5a0a202a396444e266b47d8fc4f74ad4698048bd43040707'


def run(*args, **kwargs):
    return subprocess.check_output(args, cwd=ROOT, text=True, **kwargs).strip()


def main():
    blender = Path(os.environ.get('BLENDER_EXECUTABLE', '/Applications/Blender.app/Contents/MacOS/Blender'))
    if not blender.is_file() or not shutil.which('uv'):
        raise SystemExit('Install Blender 5.1+ and uv, or set BLENDER_EXECUTABLE')
    version_line = run(str(blender), '--version').splitlines()[0]
    version = tuple(int(n) for n in version_line.split()[1].split('.'))
    if version < (5, 1, 0):
        raise SystemExit('The official add-on requires Blender 5.1+')
    bundled_python = blender.parent.parent / 'Resources' / f'{version[0]}.{version[1]}' / 'python/bin'
    python = next(p for p in sorted(bundled_python.glob('python3.*')) if p.is_file())
    local = ROOT / '.local'
    local.mkdir(exist_ok=True)
    checkout = local / 'blender_mcp'
    if not checkout.exists():
        run('git', 'clone', '--depth', '1', '--branch', 'v' + VERSION, SOURCE, str(checkout))
    if run('git', '-C', str(checkout), 'remote', 'get-url', 'origin') != SOURCE:
        raise SystemExit('Unexpected upstream; refusing to reuse this checkout')
    if run('git', '-C', str(checkout), 'rev-parse', 'HEAD') != REVISION:
        raise SystemExit('Unexpected official revision; refusing to replace it')
    if run('git', '-C', str(checkout), 'status', '--porcelain', '--untracked-files=no'):
        raise SystemExit('Official checkout has modified tracked files')
    archive = local / f'mcp-{VERSION}.zip'
    if not archive.exists():
        url = f'https://projects.blender.org/lab/blender_mcp/releases/download/v{VERSION}/mcp-{VERSION}.zip'
        with urllib.request.urlopen(url, timeout=60) as response:
            archive.write_bytes(response.read())
    if hashlib.sha256(archive.read_bytes()).hexdigest() != ADDON_SHA256:
        raise SystemExit('Official add-on archive checksum mismatch')
    venv_python = ROOT / '.venv/bin/python'
    if not venv_python.exists():
        run('uv', 'venv', '--python', str(python), str(ROOT / '.venv'))
    run('uv', 'pip', 'install', '--python', str(venv_python), '--constraint',
        str(ROOT / 'requirements.lock'), str(checkout / 'mcp'), 'pillow')
    env = dict(os.environ, BLENDER_USER_RESOURCES=str(local / 'blender-user'))
    # Do not inherit overrides pointing at the user's normal Blender profile.
    for name in ('BLENDER_USER_CONFIG', 'BLENDER_USER_SCRIPTS',
                 'BLENDER_USER_EXTENSIONS', 'BLENDER_USER_DATAFILES'):
        env.pop(name, None)
    manifest = local / 'blender-user/extensions/user_default/mcp/blender_manifest.toml'
    if not manifest.exists():
        print(run(str(blender), '--online-mode', '-b', '--command', 'extension',
                  'install-file', str(archive), '--repo', 'user_default', '--enable', env=env))
    with zipfile.ZipFile(archive) as bundle:
        for item in bundle.infolist():
            if not item.is_dir():
                installed = manifest.parent / item.filename
                if not installed.is_file() or installed.read_bytes() != bundle.read(item):
                    raise SystemExit('Installed add-on differs from the verified official archive')
    verification = "import bpy; a=bpy.context.preferences.addons.get('bl_ext.user_default.mcp'); assert a, 'MCP disabled'; assert a.preferences.use_autostart; print('ADDON_ENABLED')"
    print(run(str(blender), '--online-mode', '-b', '--python-exit-code', '1',
              '--python-expr', verification, env=env))
    (local / 'setup.json').write_text(json.dumps({
        'blender': version_line, 'official_version': VERSION, 'revision': REVISION,
        'addon_sha256': ADDON_SHA256, 'profile': '.local/blender-user',
    }, indent=2) + '\n')
    print('SETUP=PASS; start the project Blender with ./scripts/start-blender')


if __name__ == '__main__':
    main()
