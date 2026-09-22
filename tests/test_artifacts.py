"""Integration assertions against actual local output, never mock renders."""
import json
from pathlib import Path
import subprocess
import unittest
from PIL import Image, ImageStat

ROOT = Path(__file__).resolve().parents[1]


class Artifacts(unittest.TestCase):
    def test_png_content(self):
        path = ROOT / 'renders/mcp_smoke_v0_1.png'
        self.assertGreater(path.stat().st_size, 10_000)
        with Image.open(path) as image:
            self.assertEqual(image.format, 'PNG')
            self.assertEqual(image.size, (1920, 1080))
            image.verify()
        with Image.open(path) as image:
            image.load()
            self.assertGreater(min(ImageStat.Stat(image.convert('RGB')).stddev), 15)
            self.assertGreater(len(image.convert('RGB').resize((128, 72)).getcolors(9216) or []), 1000)

    def test_saved_blend_reopens(self):
        path = ROOT / 'blender/scenes/mcp_smoke_v0_1.blend'
        self.assertGreater(path.stat().st_size, 10_000)
        completed = subprocess.run([
            str(ROOT / 'scripts/start-blender'), '-b', str(path), '--python-exit-code', '1',
            '--python', str(ROOT / 'blender/scripts/verify_scene.py'),
        ], cwd=ROOT, text=True, capture_output=True, timeout=60)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        text = completed.stdout
        scene, _ = json.JSONDecoder().raw_decode(text[text.index('{'):])
        self.assertEqual(scene['status'], 'PASS')
        self.assertEqual(len(scene['lights']), 3)
        self.assertEqual(scene['camera'], 'Camera_Product')
        self.assertIn('Anodized_Teal', scene['materials'])
        self.assertTrue(scene['background'])


if __name__ == '__main__':
    unittest.main()
