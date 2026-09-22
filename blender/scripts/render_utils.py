"""Repository-contained outputs and explicit rendering settings."""
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[2]


def output_path(relative):
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError('Output must stay inside this repository')
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def configure_render(scene, preview=False):
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 24 if preview else 64
    scene.cycles.use_denoising = True
    scene.cycles.seed = 11
    scene.render.resolution_x = 960 if preview else 1920
    scene.render.resolution_y = 540 if preview else 1080
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.color_depth = '8'
    scene.render.film_transparent = False
    scene.view_settings.view_transform = 'AgX'
    # First Metal kernel initialization stalled on the audited Mac.
    # CPU is explicit and reproducible for this small v0.1 experiment.
    scene.cycles.device = 'CPU'
    scene.render.filepath = '//../../renders/mcp_smoke_v0_1.png'


def save_and_render(scene, preview=False):
    configure_render(scene, preview)
    blend = output_path('blender/scenes/mcp_smoke_v0_1.blend')
    png = output_path('.local/preview.png' if preview else 'renders/mcp_smoke_v0_1.png')
    if preview:
        scene.render.filepath = str(png)
    else:
        # Store a portable render path in the .blend, and avoid .blend1 backups.
        previous = bpy.context.preferences.filepaths.save_version
        try:
            bpy.context.preferences.filepaths.save_version = 0
            bpy.ops.wm.save_as_mainfile(filepath=str(blend), compress=True, check_existing=False)
        finally:
            bpy.context.preferences.filepaths.save_version = previous
    bpy.ops.render.render(write_still=True)
    return {'blend': str(blend.relative_to(ROOT)), 'render': str(png.relative_to(ROOT)),
            'resolution': [scene.render.resolution_x, scene.render.resolution_y],
            'engine': scene.render.engine, 'device': scene.cycles.device,
            'samples': scene.cycles.samples}
