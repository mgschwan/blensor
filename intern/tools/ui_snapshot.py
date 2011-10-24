# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Contributor(s): Campbell Barton
#
# ***** END GPL LICENSE BLOCK *****

# screenshot panels, corrently only works for render, scene and world.
# needs some further work to setup blender contexts for all possible panels.

import os

REMOVE_CMP_IMAGES = True
TEMP_DIR = "/tmp"

PROPERTY_MAPPING = {
    "armature_edit": 'DATA',
    "bone": 'BONE',
    "bone_constraint": '',
    "constraint": '',
    "curve_edit": '',
    "data": '',
    "imagepaint": '',
    "lattice_edit": 'DATA',
    "material": 'MATERIAL',
    "mball_edit": '',
    "mesh_edit": '',
    "modifier": '',
    "object": 'OBJECT',
    "objectmode": '',
    "particle": '',
    "particlemode": '',
    "physics": '',
    "posemode": '',  # toolbar
    "render": 'RENDER',
    "scene": 'SCENE',
    "surface_edit": '',
    "text_edit": '',
    "texture": '',
    "vertexpaint": '',
    "weightpaint": '',
    "world": 'WORLD',
}

# format: % (new, blank, out)
magick_command = 'convert "%s" "%s" \( -clone 0 -clone 1 -compose difference -composite -threshold 0 \) -delete 1 -alpha off -compose copy_opacity -composite -trim "%s" '

import bpy


def clear_startup_blend():
    import bpy
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')

    import bpy

    for scene in bpy.data.scenes:
        for obj in scene.objects:
            scene.objects.unlink(obj)


def force_redraw():
    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

def fake_poll(cls, context):
    return True

def screenshot(path):
    force_redraw()
    bpy.ops.screen.screenshot(filepath=path)

def context_setup(bl_context, class_name):    
    if bl_context == "object":
        bpy.ops.object.add(type='EMPTY')
    elif bl_context == "bone":
        bpy.ops.object.armature_add()
        bpy.ops.object.mode_set(mode='EDIT')
    elif bl_context == "armature_edit":
        bpy.ops.object.armature_add()
        bpy.ops.object.mode_set(mode='EDIT')
    elif bl_context == "posemode":
        bpy.ops.object.armature_add()
        bpy.ops.object.mode_set(mode='POSE')
    elif bl_context == "lattice_edit":
        bpy.ops.object.add(type='LATTICE')
        bpy.ops.object.mode_set(mode='EDIT')
    elif bl_context == "material":
        bpy.ops.object.add(type='MESH')
        bpy.context.object.data.materials.append(bpy.data.materials.new("Material"))
        bpy.ops.object.mode_set(mode='EDIT')
    

def main():
    panel_subclasses = []

    for cls_name in dir(bpy.types):
        cls = getattr(bpy.types, cls_name)
        if issubclass(cls, bpy.types.Panel):
            if bpy.types.Panel is cls:
                continue

            panel_subclasses.append((cls, getattr(cls, "poll", None)))

    for cls, poll in panel_subclasses:
        cls.poll = classmethod(fake_poll)
        cls.bl_options = set()  # so we dont get 'DEFAULT_CLOSED'
        bpy.utils.unregister_class(cls)

    # collect context types
    button_contexts = {None}
    for cls, poll in panel_subclasses:
        button_contexts.add(getattr(cls, "bl_context", None))
    button_contexts.remove(None)

    # get the properties space
    space_props = None
    for sa in bpy.context.screen.areas:
        space = sa.spaces.active
        if space.type == 'PROPERTIES':
            space_props = space
            break
    if space_props is None:
        raise Exception("no properties space type found")
    
    for bl_context in sorted(button_contexts):
        print(list(sorted(button_contexts)))
        # TODO
        # if bl_context in PROPERTY_SKIP:
        #     continue

        ## TESTING ONLY
        #if bl_context != "material":
        #    continue

        prop_context = PROPERTY_MAPPING[bl_context]
        if not prop_context:
            print("    TODO, skipping", bl_context)
            continue

        space_props.context = prop_context

        for cls, poll in panel_subclasses:
            if cls.bl_space_type == 'PROPERTIES':
                if cls.bl_region_type == 'WINDOW':
                    if cls.bl_context == bl_context:
                        
                        clear_startup_blend()
                        context_setup(bl_context, cls.__name__)
                        
                        file_base = os.path.join(TEMP_DIR, "%s_%s" % (bl_context, "_" + cls.__name__.replace(".", "_")))
                        file_old = file_base + "_old.png"
                        file_new = file_base + "_new.png"
                        file_crop = file_base + ".png"
                        
                        screenshot(file_old)
                        
                        # we need a new unique name so old 'closed' settings dont get applied
                        idname = getattr(cls, "bl_idname", cls.__name__.split(".")[-1])
                        cls.bl_idname = idname + "_"
                        
                        bpy.utils.register_class(cls)

                        screenshot(file_new)

                        bpy.utils.unregister_class(cls)

                        # screenshot magic
                        from os import system
                        system(magick_command % (file_new, file_old, file_crop))
                        
                        if REMOVE_CMP_IMAGES:
                            from os import remove
                            remove(file_old)
                            remove(file_new)


if __name__ == "__main__":
    main()
