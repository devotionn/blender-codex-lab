"""One-command orchestrator for the complete MCP-driven product video pipeline."""
import argparse
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / '.venv/bin/python'
MCP = ROOT / 'scripts/codex_mcp.py'
BLENDER_ENTRY = ROOT / 'blender/scripts/render_product_video.py'


def mcp(action: str, evidence_name: str):
    subprocess.run([
        str(PYTHON), str(MCP), 'execute', '--file', str(BLENDER_ENTRY),
        '--script-action', action, '--output', str(ROOT / f'.local/{evidence_name}.json'),
    ], cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview-only', action='store_true',
                        help='Stop after generating the preview video and check frames')
    args = parser.parse_args()
    if not PYTHON.exists():
        raise SystemExit('Run python3 scripts/setup.py first')
    mcp('build', 'product-build')
    mcp('checks', 'product-check-render')
    for index, (first, last) in enumerate(((1, 84), (85, 168)), start=1):
        mcp(f'preview:{first}:{last}', f'preview-chunk-{index}')
    subprocess.run([str(PYTHON), str(ROOT / 'scripts/encode_product_video.py'), 'preview'],
                   cwd=ROOT, check=True)
    if args.preview_only:
        return
    for index, (first, last) in enumerate(((1, 42), (43, 84), (85, 126), (127, 168)), start=1):
        mcp(f'final:{first}:{last}', f'final-chunk-{index}')
    subprocess.run([str(PYTHON), str(ROOT / 'scripts/encode_product_video.py'), 'final'],
                   cwd=ROOT, check=True)
    subprocess.run([str(PYTHON), '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
                   cwd=ROOT, check=True)


if __name__ == '__main__':
    main()
