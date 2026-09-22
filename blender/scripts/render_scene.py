from pathlib import Path
import sys
import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scene_utils import SCENE_NAME
from render_utils import save_and_render

if bpy.context.scene.name != SCENE_NAME:
    raise RuntimeError('Create the smoke scene before rendering')
result = save_and_render(bpy.context.scene)
