"""Single deterministic entry point for build, inspect and frame rendering.

MCP usage example:
  scripts/codex_mcp.py execute --file blender/scripts/render_product_video.py --script-action build
"""
from pathlib import Path
import importlib
import sys

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import product_video_generator as _generator
_generator = importlib.reload(_generator)
from product_video_generator import (SCENE_NAME, build_scene, load_config, render_check_frames,
                                     render_frames, save_scene)
import bpy


def run(action: str) -> dict:
    config = load_config()
    if action == 'build':
        scene, camera, towels = build_scene(config)
        blend = save_scene(scene)
        return {'status': 'PASS', 'action': action, 'scene': scene.name,
                'objects': len(scene.objects), 'towels': [obj.name for obj in towels],
                'camera': camera.name, 'frame_range': [scene.frame_start, scene.frame_end],
                'blend_file': str(blend.relative_to(Path(__file__).resolve().parents[2]))}
    scene = bpy.context.scene
    if scene.name != SCENE_NAME:
        raise RuntimeError('Current Blender scene is not the generated product scene')
    if action == 'checks':
        return {'status': 'PASS', 'action': action, **render_check_frames(scene, config)}
    parts = action.split(':')
    if len(parts) == 3 and parts[0] in {'preview', 'final'}:
        return {'status': 'PASS', 'action': parts[0],
                **render_frames(scene, config, parts[0], int(parts[1]), int(parts[2]))}
    raise ValueError(f'Unknown action: {action}')


action = globals().get('PRODUCT_VIDEO_ACTION')
if action is None:
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    action = argv[0] if argv else 'build'
result = run(action)
