"""Parameterized native-Blender generator for a premium folded-towel shot."""
from __future__ import annotations

import json
import math
from pathlib import Path
import time

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / 'experiments/002_product_video/product.json'
SCENE_NAME = 'PRODUCT_TOWEL_V0_1'


def load_config(path: Path = CONFIG_PATH) -> dict:
    config = json.loads(path.read_text())
    required = {'product', 'towel_stack_count', 'camera', 'render'}
    if required - config.keys():
        raise ValueError('Missing config sections: ' + ', '.join(sorted(required - config.keys())))
    if not 1 <= int(config['towel_stack_count']) <= 6:
        raise ValueError('towel_stack_count must be between 1 and 6')
    if config['render']['resolution'] != [1920, 1080]:
        raise ValueError('v0.1 final resolution must be 1920x1080')
    return config


def repo_path(relative: str) -> Path:
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError('Path must stay inside the repository')
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def reset_scene() -> bpy.types.Scene:
    scene = bpy.context.scene
    safe_names = {'Scene', 'MCP_SMOKE_SCENE_V0_1', SCENE_NAME}
    if scene.name not in safe_names:
        raise RuntimeError(f'Refusing to reset unrelated scene {scene.name!r}')
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


def _principled(material: bpy.types.Material):
    material.use_nodes = True
    return material.node_tree.nodes.get('Principled BSDF')


def make_towel_material(config: dict) -> bpy.types.Material:
    mat = bpy.data.materials.new('Towel_White_Fabric')
    bsdf = _principled(mat)
    srgb = config['product']['color_srgb']
    bsdf.inputs['Base Color'].default_value = (*srgb, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.78
    if bsdf.inputs.get('Sheen Weight'):
        bsdf.inputs['Sheen Weight'].default_value = 0.24
    if bsdf.inputs.get('Sheen Roughness'):
        bsdf.inputs['Sheen Roughness'].default_value = 0.72
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    tex = nodes.new('ShaderNodeTexNoise')
    tex.name = 'Fine woven fibers'
    tex.inputs['Scale'].default_value = 155.0
    tex.inputs['Detail'].default_value = 3.0
    tex.inputs['Roughness'].default_value = 0.72
    bump = nodes.new('ShaderNodeBump')
    bump.name = 'Fabric micro-bump'
    bump.inputs['Strength'].default_value = 0.34
    bump.inputs['Distance'].default_value = 0.045
    links.new(tex.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    mat.diffuse_color = (*srgb, 1.0)
    return mat


def make_simple_material(name: str, color: tuple[float, float, float], roughness: float,
                         metallic: float = 0.0) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    bsdf = _principled(mat)
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    mat.diffuse_color = (*color, 1.0)
    return mat


def soft_box(name: str, location, dimensions, material, bevel: float,
             rotation_z: float = 0.0, displacement: float = 0.0, seed: int = 0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location, rotation=(0, 0, rotation_z))
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel_mod = obj.modifiers.new('Soft rounded cloth edges', 'BEVEL')
    bevel_mod.width = bevel
    bevel_mod.segments = 6
    if displacement:
        subdiv = obj.modifiers.new('Cloth surface subdivisions', 'SUBSURF')
        subdiv.subdivision_type = 'SIMPLE'
        subdiv.levels = 2
        subdiv.render_levels = 2
        texture = bpy.data.textures.new(name + '_Macro_Weave', type='CLOUDS')
        texture.noise_scale = 0.18 + (seed % 3) * 0.01
        texture.noise_depth = 2
        texture.noise_basis = 'IMPROVED_PERLIN'
        displace = obj.modifiers.new('Subtle cloth irregularity', 'DISPLACE')
        displace.texture = texture
        displace.strength = displacement
        displace.mid_level = 0.5
        displace.texture_coords = 'GLOBAL'
    obj.data.materials.append(material)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def create_towel_stack(scene: bpy.types.Scene, config: dict, towel_mat: bpy.types.Material):
    count = int(config['towel_stack_count'])
    width_cm = float(config['product']['width_cm'])
    length_cm = float(config['product']['length_cm'])
    folded_ratio = width_cm / (length_cm / 3.0)
    width = 3.22
    depth = width / folded_ratio
    height = 0.34
    base_z = 0.62
    towels = []
    offsets = [(0.02, 0.00, math.radians(-0.8)), (-0.06, 0.01, math.radians(1.3)),
               (0.04, -0.03, math.radians(-1.6)), (-0.03, 0.02, math.radians(0.7))]
    for index in range(count):
        ox, oy, rz = offsets[index % len(offsets)]
        z = base_z + index * 0.39
        scale = 1.0 - index * 0.018
        body = soft_box(f'Towel_{index + 1:02d}_Body', (ox, oy, z),
                        (width * scale, depth * scale, height), towel_mat,
                        bevel=0.14, rotation_z=rz, displacement=0.035, seed=index + 1)
        body['product_component'] = 'folded_towel'
        body['nominal_width_cm'] = width_cm
        body['nominal_length_cm'] = length_cm
        body['nominal_weight_g'] = float(config['product']['weight_g'])
        towels.append(body)
        # Raised hems and a loose folded lip create readable textile layers.
        for side, y_sign in [('Front', -1), ('Back', 1)]:
            local_y = y_sign * depth * scale * 0.47
            x = ox - math.sin(rz) * local_y
            y = oy + math.cos(rz) * local_y
            hem = soft_box(f'Towel_{index + 1:02d}_{side}_Hem', (x, y, z + 0.02),
                           (width * scale * 0.91, 0.16, height * 0.64), towel_mat,
                           bevel=0.065, rotation_z=rz, displacement=0.012, seed=20 + index)
            hem['product_component'] = 'woven_hem'
    # The top folded end gives a soft, layered silhouette instead of a stack of blocks.
    top_z = base_z + (count - 1) * 0.39
    flap = soft_box('Towel_Top_Folded_End', (0.06, -depth * 0.36, top_z + 0.21),
                    (width * 0.90, depth * 0.44, 0.20), towel_mat, bevel=0.11,
                    rotation_z=offsets[(count - 1) % len(offsets)][2], displacement=0.026, seed=77)
    flap['product_component'] = 'folded_end'
    return towels


def create_cyclorama(scene: bpy.types.Scene, material: bpy.types.Material):
    profile = [(-6.0, 0.0), (2.8, 0.0), (3.7, 0.12), (4.35, 0.55),
               (4.75, 1.25), (4.9, 2.2), (4.9, 4.2), (4.9, 7.0)]
    vertices = []
    for x in (-20.0, 20.0):
        vertices.extend((x, y, z) for y, z in profile)
    n = len(profile)
    faces = [(i, i + 1, n + i + 1, n + i) for i in range(n - 1)]
    mesh = bpy.data.meshes.new('Cyclorama_Mesh')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new('Studio_Cyclorama', mesh)
    scene.collection.objects.link(obj)
    obj.data.materials.append(material)
    bevel = obj.modifiers.new('Seamless backdrop', 'BEVEL')
    bevel.width = 0.28
    bevel.segments = 8
    for face in mesh.polygons:
        face.use_smooth = True
    return obj


def aim(obj: bpy.types.Object, target) -> None:
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def add_area_light(scene, name, location, energy, color, size, target):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy = energy
    data.color = color
    data.shape = 'DISK'
    data.size = size
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = location
    aim(obj, target)
    return obj


def setup_lighting(scene: bpy.types.Scene, target):
    add_area_light(scene, 'Key_Softbox', (-4.5, -4.8, 6.4), 1050, (1.0, 0.84, 0.68), 4.6, target)
    add_area_light(scene, 'Fill_Softbox', (4.8, -2.8, 3.8), 620, (0.76, 0.84, 1.0), 5.0, target)
    add_area_light(scene, 'Rim_Softbox', (2.2, 4.0, 5.5), 1150, (1.0, 0.75, 0.52), 3.2, target)
    add_area_light(scene, 'Top_Softbox', (-0.5, 0.4, 7.6), 540, (1.0, 0.92, 0.82), 3.8, target)
    world = bpy.data.worlds.new('Warm_Studio_World') if scene.world is None else scene.world
    world.name = 'Warm_Studio_World'
    world.use_nodes = True
    bg = world.node_tree.nodes.get('Background')
    bg.inputs['Color'].default_value = (0.105, 0.092, 0.078, 1.0)
    bg.inputs['Strength'].default_value = 0.32
    scene.world = world


def setup_camera(scene: bpy.types.Scene, config: dict):
    camera_config = config['camera']
    target = bpy.data.objects.new('Camera_Target', None)
    target.empty_display_type = 'PLAIN_AXES'
    target.empty_display_size = 0.18
    target.location = camera_config['target']
    scene.collection.objects.link(target)
    data = bpy.data.cameras.new('Camera_Product_Animated')
    data.lens = camera_config['lens_start_mm']
    data.sensor_width = 36
    data.clip_start = 0.1
    data.clip_end = 100
    data.dof.use_dof = True
    data.dof.focus_object = target
    data.dof.aperture_fstop = 7.1
    camera = bpy.data.objects.new('Camera_Product_Animated', data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    constraint = camera.constraints.new('TRACK_TO')
    constraint.name = 'Product focus'
    constraint.target = target
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.up_axis = 'UP_Y'
    frame_start = 1
    frame_end = round(float(camera_config['duration_seconds']) * int(config['render']['fps']))
    frame_mid = round((frame_start + frame_end) / 2)
    edit_preferences = bpy.context.preferences.edit
    previous_interpolation = edit_preferences.keyframe_new_interpolation_type
    try:
        edit_preferences.keyframe_new_interpolation_type = 'BEZIER'
        for frame, position, lens in (
            (frame_start, camera_config['start'], camera_config['lens_start_mm']),
            (frame_mid, camera_config['middle'], camera_config['lens_middle_mm']),
            (frame_end, camera_config['end'], camera_config['lens_end_mm']),
        ):
            camera.location = position
            camera.keyframe_insert('location', frame=frame)
            data.lens = lens
            data.keyframe_insert('lens', frame=frame)
    finally:
        edit_preferences.keyframe_new_interpolation_type = previous_interpolation
    scene.frame_start = frame_start
    scene.frame_end = frame_end
    scene.frame_set(frame_start)
    return camera


def configure_render(scene: bpy.types.Scene, config: dict):
    render = config['render']
    scene.render.engine = render['engine']
    if getattr(scene, 'eevee', None) is not None:
        scene.eevee.taa_render_samples = 64
    scene.render.resolution_x, scene.render.resolution_y = render['resolution']
    scene.render.resolution_percentage = 100
    scene.render.fps = render['fps']
    scene.render.fps_base = 1.0
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.color_depth = '8'
    scene.render.film_transparent = False
    scene.render.use_file_extension = True
    scene.render.use_overwrite = True
    scene.render.use_placeholder = False
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.render.filepath = str(repo_path('.local/product_towel_final_frames/frame_'))
    return scene


def build_scene(config: dict):
    scene = reset_scene()
    scene['generator'] = 'blender/scripts/render_product_video.py'
    scene['product_config'] = 'experiments/002_product_video/product.json'
    scene['product_name'] = config['product']['name']
    scene['duration_seconds'] = float(config['camera']['duration_seconds'])
    towel_mat = make_towel_material(config)
    pedestal_mat = make_simple_material('Pedestal_Warm_Stone', (0.31, 0.27, 0.22), 0.58)
    backdrop_mat = make_simple_material('Backdrop_Warm_Gray', (0.23, 0.20, 0.17), 0.72)
    accent_mat = make_simple_material('Brushed_Brass_Accent', (0.48, 0.22, 0.07), 0.36, 0.72)
    create_cyclorama(scene, backdrop_mat)
    bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=2.55, depth=0.34, location=(0, 0, 0.22))
    pedestal = bpy.context.object
    pedestal.name = 'Product_Pedestal'
    pedestal.data.materials.append(pedestal_mat)
    bevel = pedestal.modifiers.new('Pedestal soft edge', 'BEVEL')
    bevel.width = 0.10
    bevel.segments = 6
    for polygon in pedestal.data.polygons:
        polygon.use_smooth = True
    bpy.ops.mesh.primitive_torus_add(major_radius=2.48, minor_radius=0.018,
                                   major_segments=128, minor_segments=12, location=(0, 0, 0.08))
    trim = bpy.context.object
    trim.name = 'Pedestal_Brass_Trim'
    trim.data.materials.append(accent_mat)
    towels = create_towel_stack(scene, config, towel_mat)
    setup_lighting(scene, config['camera']['target'])
    camera = setup_camera(scene, config)
    configure_render(scene, config)
    bpy.context.view_layer.update()
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces.active.region_3d.view_perspective = 'CAMERA'
    return scene, camera, towels


def save_scene(scene: bpy.types.Scene) -> Path:
    destination = repo_path('blender/scenes/product_towel_v0_1.blend')
    previous = bpy.context.preferences.filepaths.save_version
    try:
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(destination), compress=True, check_existing=False)
    finally:
        bpy.context.preferences.filepaths.save_version = previous
    return destination


def render_frames(scene: bpy.types.Scene, config: dict, quality: str, first: int, last: int) -> dict:
    if not scene.name == SCENE_NAME:
        raise RuntimeError('Build the product scene before rendering')
    expected_start, expected_end = 1, round(config['camera']['duration_seconds'] * config['render']['fps'])
    if first < expected_start or last > expected_end or first > last:
        raise ValueError('Invalid frame chunk')
    preview = quality == 'preview'
    directory = repo_path(f'.local/product_towel_{quality}_frames')
    scene.render.resolution_percentage = config['render']['preview_scale_percent'] if preview else 100
    scene.render.filepath = str(directory / 'frame_')
    old_start, old_end = scene.frame_start, scene.frame_end
    scene.frame_start, scene.frame_end = first, last
    started = time.monotonic()
    try:
        bpy.ops.render.render(animation=True)
    finally:
        scene.frame_start, scene.frame_end = old_start, old_end
    elapsed = time.monotonic() - started
    frames = last - first + 1
    return {'quality': quality, 'first': first, 'last': last, 'frames': frames,
            'elapsed_seconds': round(elapsed, 3),
            'average_frame_seconds': round(elapsed / frames, 4),
            'directory': str(directory.relative_to(ROOT)),
            'resolution_percent': scene.render.resolution_percentage}


def render_check_frames(scene: bpy.types.Scene, config: dict) -> dict:
    frames = [scene.frame_start, round((scene.frame_start + scene.frame_end) / 2), scene.frame_end]
    directory = repo_path('.local/product_towel_checks')
    scene.render.resolution_percentage = config['render']['preview_scale_percent']
    old_path = scene.render.filepath
    started = time.monotonic()
    paths = []
    for label, frame in zip(('start', 'middle', 'end'), frames):
        scene.frame_set(frame)
        path = directory / f'{label}_{frame:04d}.png'
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        paths.append(str(path.relative_to(ROOT)))
    scene.render.filepath = old_path
    scene.frame_set(scene.frame_start)
    return {'frames': frames, 'paths': paths, 'elapsed_seconds': round(time.monotonic() - started, 3)}
