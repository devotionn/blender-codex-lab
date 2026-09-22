"""Small reusable scene primitives; only operate on the active experiment scene."""
import bpy
from mathutils import Vector

SCENE_NAME = 'MCP_SMOKE_SCENE_V0_1'


def reset_scene():
    scene = bpy.context.scene
    names = {o.name for o in scene.objects}
    if scene.name != SCENE_NAME and (bpy.data.filepath or names - {'Cube', 'Camera', 'Light'}):
        raise RuntimeError('Refusing to reset an unrelated scene; start a fresh project Blender')
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for obj in list(scene.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for library in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                    bpy.data.cameras, bpy.data.lights):
        for item in list(library):
            if item.users == 0:
                library.remove(item)
    scene.name = SCENE_NAME
    return scene


def material(name, color, metallic=0.0, roughness=0.4):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    mat.diffuse_color = (*color, 1)
    return mat


def rounded_box(name, location, dimensions, mat, bevel=0.12):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    mod = obj.modifiers.new('Soft machined edges', 'BEVEL')
    mod.width, mod.segments = bevel, 6
    obj.modifiers.new('Weighted corner normals', 'WEIGHTED_NORMAL')
    obj.data.materials.append(mat)
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def camera(scene, location=(7, -11, 6.8), target=(0, 0, 1.45)):
    data = bpy.data.cameras.new('Camera_Product')
    obj = bpy.data.objects.new('Camera_Product', data)
    scene.collection.objects.link(obj)
    obj.location = location
    aim(obj, target)
    data.type, data.ortho_scale = 'ORTHO', 9.7
    data.clip_start, data.clip_end = 0.1, 200
    scene.camera = obj
    return obj


def area_light(scene, name, location, energy, color, size, target=(0, 0, 1.5)):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy, data.color, data.shape, data.size = energy, color, 'DISK', size
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = location
    aim(obj, target)
    return obj


def lighting(scene):
    area_light(scene, 'Key_Light', (1, -5, 7), 1150, (1.0, 0.83, 0.68), 5)
    area_light(scene, 'Fill_Light', (-4, -2, 3.5), 800, (0.52, 0.77, 1.0), 4)
    area_light(scene, 'Rim_Light', (3, 4, 6), 1700, (0.72, 0.9, 1.0), 3)
    world = bpy.data.worlds.new('Studio_World') if scene.world is None else scene.world
    world.name = 'Studio_World'
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.075, 0.11, 0.16, 1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.3
    scene.world = world
