"""Encode preserved Blender PNG frames into preview or final H.264 MP4."""
import argparse
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / 'experiments/002_product_video/product.json').read_text())


def probe(path: Path) -> dict:
    raw = subprocess.check_output([
        'ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=codec_name,width,height,avg_frame_rate,nb_frames,duration',
        '-show_entries', 'format=duration,size', '-of', 'json', str(path),
    ], text=True)
    return json.loads(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('quality', choices=['preview', 'final'])
    args = parser.parse_args()
    render = CONFIG['render']
    frames = ROOT / f'.local/product_towel_{args.quality}_frames'
    relative_output = render['preview_output_path'] if args.quality == 'preview' else render['output_path']
    output = (ROOT / relative_output).resolve()
    if not output.is_relative_to(ROOT):
        raise SystemExit('Output must stay inside repository')
    expected = round(CONFIG['camera']['duration_seconds'] * render['fps'])
    found = sorted(frames.glob('frame_*.png'))
    if len(found) != expected:
        raise SystemExit(f'Expected {expected} frames, found {len(found)} in {frames}')
    output.parent.mkdir(parents=True, exist_ok=True)
    crf = '22' if args.quality == 'preview' else '18'
    subprocess.run([
        'ffmpeg', '-y', '-loglevel', 'warning', '-framerate', str(render['fps']),
        '-start_number', '1', '-i', str(frames / 'frame_%04d.png'),
        '-c:v', 'libx264', '-preset', 'medium', '-crf', crf,
        '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(output),
    ], check=True)
    info = probe(output)
    print(json.dumps({'quality': args.quality, 'output': str(output.relative_to(ROOT)),
                      'frames': len(found), 'probe': info}, indent=2))


if __name__ == '__main__':
    main()
