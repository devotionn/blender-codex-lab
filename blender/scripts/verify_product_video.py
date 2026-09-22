"""Verify the generated towel scene inside Blender and return structured evidence."""
from pathlib import Path
import json
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
from product_video_generator import CONFIG_PATH, ROOT, SCENE_NAME, load_config

config = load_config(CONFIG_PATH)
scene = bpy.context.scene
assert scene.name == SCENE_NAME
assert scene.camera and scene.camera.name == 'Camera_Product_Animated'
assert scene.camera.animation_data and scene.camera.animation_data.action
assert scene.camera.data.animation_data and scene.camera.data.animation_data.action
assert scene.frame_start == 1
assert scene.frame_end == round(config['camera']['duration_seconds'] * config['render']['fps'])
assert [scene.render.resolution_x, scene.render.resolution_y] == config['render']['resolution']
assert scene.render.fps == config['render']['fps']
assert scene.render.engine == config['render']['engine']
towels = [obj for obj in scene.objects if obj.get('product_component') == 'folded_towel']
assert len(towels) == config['towel_stack_count']
assert all(any(mod.type == 'BEVEL' for mod in obj.modifiers) for obj in towels)
assert all(any(mod.type == 'DISPLACE' for mod in obj.modifiers) for obj in towels)
material = bpy.data.materials['Towel_White_Fabric']
assert material.use_nodes
assert material.node_tree.nodes.get('Fabric micro-bump')
lights = [obj for obj in scene.objects if obj.type == 'LIGHT']
assert {'Key_Softbox', 'Fill_Softbox', 'Rim_Softbox'} <= {obj.name for obj in lights}
frame_bounds = {}
camera_samples = {}
for label, frame in [('start', scene.frame_start),
                     ('middle', round((scene.frame_start + scene.frame_end) / 2)),
                     ('end', scene.frame_end)]:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    camera_samples[label] = {'location': [round(value, 5) for value in scene.camera.location],
                             'lens_mm': round(scene.camera.data.lens, 5)}
    projected = []
    for obj in towels:
        projected.extend(world_to_camera_view(scene, scene.camera, obj.matrix_world @ Vector(corner))
                         for corner in obj.bound_box)
    bounds = {'x': [min(p.x for p in projected), max(p.x for p in projected)],
              'y': [min(p.y for p in projected), max(p.y for p in projected)],
              'depth': [min(p.z for p in projected), max(p.z for p in projected)]}
    assert 0.04 < bounds['x'][0] < bounds['x'][1] < 0.96, (label, bounds)
    assert 0.04 < bounds['y'][0] < bounds['y'][1] < 0.96, (label, bounds)
    assert scene.camera.data.clip_start < bounds['depth'][0]
    frame_bounds[label] = {key: [round(value, 5) for value in values] for key, values in bounds.items()}
scene.frame_set(scene.frame_start)
assert len({tuple(sample['location']) for sample in camera_samples.values()}) == 3
assert len({sample['lens_mm'] for sample in camera_samples.values()}) == 3
blend = ROOT / 'blender/scenes/product_towel_v0_1.blend'
assert blend.stat().st_size > 10_000
result = {
    'status': 'PASS', 'blender_version': bpy.app.version_string,
    'scene': scene.name, 'background': bpy.app.background,
    'object_count': len(scene.objects), 'towel_objects': [obj.name for obj in towels],
    'material': material.name, 'lights': [obj.name for obj in lights],
    'camera': scene.camera.name,
    'camera_samples': camera_samples,
    'frame_range': [scene.frame_start, scene.frame_end], 'fps': scene.render.fps,
    'resolution': [scene.render.resolution_x, scene.render.resolution_y],
    'engine': scene.render.engine,
    'render_samples': getattr(getattr(scene, 'eevee', None), 'taa_render_samples', None),
    'render_backend': getattr(bpy.context.preferences.system, 'gpu_backend', 'UNKNOWN'),
    'frame_bounds': frame_bounds,
    'blend_file': str(blend.relative_to(ROOT)),
}
if __name__ == '__main__':
    print(json.dumps(result, indent=2))
