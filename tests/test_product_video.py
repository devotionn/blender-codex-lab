"""Real artifact checks for the parameterized towel video pipeline."""
import json
import hashlib
from pathlib import Path
import subprocess
import unittest

from PIL import Image, ImageStat

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / 'experiments/002_product_video/product.json').read_text())


def ffprobe(path: Path) -> dict:
    return json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=codec_name,width,height,avg_frame_rate,nb_frames,duration',
        '-show_entries', 'format=duration,size', '-of', 'json', str(path),
    ], text=True))


class ProductVideo(unittest.TestCase):
    def assert_video(self, relative: str, size: tuple[int, int]):
        path = ROOT / relative
        self.assertGreater(path.stat().st_size, 100_000)
        info = ffprobe(path)
        stream = info['streams'][0]
        expected_frames = round(CONFIG['camera']['duration_seconds'] * CONFIG['render']['fps'])
        self.assertEqual(stream['codec_name'], 'h264')
        self.assertEqual((stream['width'], stream['height']), size)
        self.assertEqual(stream['avg_frame_rate'], f"{CONFIG['render']['fps']}/1")
        self.assertEqual(int(stream['nb_frames']), expected_frames)
        self.assertAlmostEqual(float(info['format']['duration']), CONFIG['camera']['duration_seconds'], delta=0.05)

    def test_preview_and_final_video(self):
        self.assert_video(CONFIG['render']['preview_output_path'], (960, 540))
        self.assert_video(CONFIG['render']['output_path'], (1920, 1080))
        decoded = subprocess.check_output([
            'ffmpeg', '-v', 'error', '-i', str(ROOT / CONFIG['render']['output_path']),
            '-map', '0:v:0', '-f', 'framemd5', '-'], text=True)
        rows = [line for line in decoded.splitlines() if line and not line.startswith('#')]
        hashes = [line.rsplit(',', 1)[-1].strip() for line in rows]
        self.assertEqual(len(rows), 168)
        self.assertEqual(len(set(hashes)), 168)

    def test_key_frames_are_valid_and_exposed(self):
        directory = ROOT / '.local/product_towel_final_frames'
        for frame in (1, 84, 168):
            path = directory / f'frame_{frame:04d}.png'
            self.assertGreater(path.stat().st_size, 50_000)
            with Image.open(path) as image:
                self.assertEqual(image.size, (1920, 1080))
                stats = ImageStat.Stat(image.convert('RGB'))
                self.assertGreater(min(stats.stddev), 25)
                extrema = image.convert('L').getextrema()
                self.assertGreater(extrema[0], 5)
                self.assertLess(extrema[1], 250)

    def test_saved_scene_reopens_with_animation(self):
        blend = ROOT / 'blender/scenes/product_towel_v0_1.blend'
        self.assertGreater(blend.stat().st_size, 10_000)
        completed = subprocess.run([
            str(ROOT / 'scripts/start-blender'), '-b', str(blend), '--python-exit-code', '1',
            '--python', str(ROOT / 'blender/scripts/verify_product_video.py'),
        ], cwd=ROOT, text=True, capture_output=True, timeout=90)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        output = completed.stdout
        result, _ = json.JSONDecoder().raw_decode(output[output.index('{'):])
        self.assertEqual(result['status'], 'PASS')
        self.assertTrue(result['background'])
        self.assertEqual(result['frame_range'], [1, 168])
        self.assertEqual(result['resolution'], [1920, 1080])
        self.assertEqual(len(result['towel_objects']), 3)
        self.assertIn('Key_Softbox', result['lights'])
        self.assertIn('Fill_Softbox', result['lights'])
        self.assertIn('Rim_Softbox', result['lights'])
        self.assertEqual(set(result['camera_samples']), {'start', 'middle', 'end'})

    def test_committed_evidence_matches_local_artifacts(self):
        evidence = json.loads((ROOT / 'experiments/002_product_video/result.json').read_text())
        self.assertEqual(evidence['status'], 'PASS')
        for relative, expected in evidence['artifacts'].items():
            path = ROOT / relative
            self.assertEqual(path.stat().st_size, expected['bytes'])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected['sha256'])
        for expected in evidence['key_frames'].values():
            path = ROOT / expected['path']
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected['sha256'])


if __name__ == '__main__':
    unittest.main()
