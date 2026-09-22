import bpy

result = {
    'version': bpy.app.version_string,
    'background': bpy.app.background,
    'scene': bpy.context.scene.name,
    'objects': [{'name': o.name, 'type': o.type} for o in bpy.context.scene.objects],
    'addon_enabled': 'bl_ext.user_default.mcp' in bpy.context.preferences.addons,
}
