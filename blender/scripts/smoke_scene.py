"""MCP_SMOKE_SCENE_V0_1: a teal desktop instrument on a studio pedestal."""
import math
from pathlib import Path
import sys
import bpy

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
from scene_utils import reset_scene, material, rounded_box, camera, lighting


def create_scene():
    scene = reset_scene()
    teal = material('Anodized_Teal', (0.012, 0.31, 0.29), metallic=0.65, roughness=0.29)
    gold = material('Champagne_Gold', (0.83, 0.49, 0.17), metallic=0.8, roughness=0.25)
    dark = material('Graphite_Panel', (0.008, 0.018, 0.025), metallic=0.25, roughness=0.35)
    stone = material('Porcelain_Pedestal', (0.4, 0.48, 0.56), metallic=0.15, roughness=0.38)
    floor = material('Midnight_Floor', (0.028, 0.045, 0.07), roughness=0.52)

    rounded_box('Product_Body', (0, 0, 1.84), (2.35, 1.65, 2.5), teal, 0.22)
    rounded_box('Front_Panel', (0, -0.815, 1.93), (1.91, 0.08, 1.79), dark, 0.16)
    rounded_box('Gold_Top_Inlay', (0, -0.838, 2.87), (1.65, 0.035, 0.055), gold, 0.025)

    # Large dial faces the camera, along the front (-Y) side of the product.
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=0.43, depth=0.13,
                                       location=(0, -0.93, 2.03), rotation=(math.pi / 2, 0, 0))
    dial = bpy.context.object
    dial.name = 'Gold_Dial'
    dial.data.materials.append(gold)
    bevel = dial.modifiers.new('Dial bevel', 'BEVEL')
    bevel.width, bevel.segments = 0.045, 5
    dial.modifiers.new('Dial normals', 'WEIGHTED_NORMAL')
    for face in dial.data.polygons:
        face.use_smooth = True
    rounded_box('Dial_Indicator', (0, -1.005, 2.29), (0.035, 0.012, 0.17), dark, 0.007)

    for index in range(5):
        rounded_box('Vent_%02d' % index, (-0.44 + index * 0.22, -0.866, 1.34),
                    (0.105, 0.024, 0.06), gold, 0.022)
    font = bpy.data.curves.new('Product_Label', 'FONT')
    font.body, font.align_x, font.size, font.extrude = 'M C P   /   0 1', 'CENTER', 0.115, 0.001
    label = bpy.data.objects.new('Product_Label', font)
    scene.collection.objects.link(label)
    label.location, label.rotation_euler = (0, -0.864, 2.59), (math.pi / 2, 0, 0)
    label.data.materials.append(gold)

    bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=2.15, depth=0.58, location=(0, 0, 0.3))
    pedestal = bpy.context.object
    pedestal.name = 'Pedestal'
    pedestal.data.materials.append(stone)
    bevel = pedestal.modifiers.new('Pedestal roundover', 'BEVEL')
    bevel.width, bevel.segments = 0.1, 6
    pedestal.modifiers.new('Pedestal normals', 'WEIGHTED_NORMAL')
    for face in pedestal.data.polygons:
        face.use_smooth = True
    bpy.ops.mesh.primitive_torus_add(major_radius=2.1, minor_radius=0.025,
                                   major_segments=128, minor_segments=12, location=(0, 0, 0.13))
    bpy.context.object.name = 'Pedestal_Gold_Trim'
    bpy.context.object.data.materials.append(gold)
    bpy.ops.mesh.primitive_plane_add(size=200)
    bpy.context.object.name = 'Ground'
    bpy.context.object.data.materials.append(floor)
    camera(scene)
    lighting(scene)
    bpy.context.view_layer.update()
    # Show the same composition in Blender's normal 3D viewport.
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces.active.region_3d.view_perspective = 'CAMERA'
    return scene


scene = create_scene()
result = {'scene': scene.name, 'objects': len(scene.objects),
          'camera': scene.camera.name, 'materials': sorted({m.name for o in scene.objects
                      for m in getattr(o.data, 'materials', []) if m})}
