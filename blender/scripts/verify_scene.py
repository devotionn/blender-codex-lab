"""Assert actual Blender datablocks and camera-space bounds, after MCP render."""
from pathlib import Path
import json
import sys
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scene_utils import SCENE_NAME
from render_utils import ROOT, output_path

scene = bpy.context.scene
assert scene.name == SCENE_NAME
expected = {'Product_Body', 'Ground', 'Pedestal', 'Gold_Dial', 'Camera_Product',
            'Key_Light', 'Fill_Light', 'Rim_Light'}
assert expected <= set(scene.objects.keys())
assert scene.camera and scene.camera.type == 'CAMERA'
assert scene.render.engine == 'CYCLES'
assert (scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage) == (1920, 1080, 100)
lights = [o for o in scene.objects if o.type == 'LIGHT']
assert len(lights) == 3 and all(o.data.energy > 0 for o in lights)
body = scene.objects['Product_Body']
mat = body.data.materials[0]
assert mat.use_nodes and mat.name == 'Anodized_Teal'
bsdf = mat.node_tree.nodes['Principled BSDF']
assert bsdf.inputs['Metallic'].default_value > 0.5
assert any(m.type == 'BEVEL' and m.width > 0 for m in body.modifiers)
bpy.context.view_layer.update()
bounds = {}
for name in ('Product_Body', 'Pedestal', 'Gold_Dial'):
    obj = scene.objects[name]
    projected = [world_to_camera_view(scene, scene.camera, obj.matrix_world @ Vector(c)) for c in obj.bound_box]
    assert all(0.04 < p.x < 0.96 and 0.04 < p.y < 0.96
               and scene.camera.data.clip_start < p.z < scene.camera.data.clip_end for p in projected), name
    bounds[name] = {'x': [round(min(p.x for p in projected), 4), round(max(p.x for p in projected), 4)],
                    'y': [round(min(p.y for p in projected), 4), round(max(p.y for p in projected), 4)]}
blend = output_path('blender/scenes/mcp_smoke_v0_1.blend')
png = output_path('renders/mcp_smoke_v0_1.png')
assert Path(bpy.data.filepath).resolve() == blend
assert blend.stat().st_size > 1000 and png.stat().st_size > 1000
result = {
    'status': 'PASS', 'blender_version': bpy.app.version_string,
    'background': bpy.app.background, 'scene': scene.name,
    'objects': [{'name': o.name, 'type': o.type} for o in scene.objects],
    'camera': scene.camera.name, 'camera_bounds': bounds,
    'lights': [{'name': o.name, 'energy': o.data.energy} for o in lights],
    'materials': sorted({m.name for o in scene.objects for m in getattr(o.data, 'materials', []) if m}),
    'render': {'engine': scene.render.engine, 'samples': scene.cycles.samples,
               'device': scene.cycles.device, 'resolution': [1920, 1080],
               'stored_path': scene.render.filepath},
    'blend_file': str(blend.relative_to(ROOT)), 'render_file': str(png.relative_to(ROOT)),
}
if __name__ == '__main__':
    print(json.dumps(result, indent=2))
