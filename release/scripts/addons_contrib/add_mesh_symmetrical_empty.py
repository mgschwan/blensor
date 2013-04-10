# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Add Symmetrical Empty",
    "author": "Pablo Vazquez",			
    "version": (1,0,2),
    "blender": (2, 64, 0),
    "location": "View3D > Add > Mesh > Symmetrical Empty",
    "description": "Add an empty mesh with a Mirror Modifier for quick symmetrical modeling",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"\
        "Scripts/Add_Mesh/Add_Symmetrical_Empty",
    "tracker_url": "",
    "category": "Add Mesh"}
'''
Adds an empty mesh with a mirror modifier.
'''    

import bpy
from bpy.props import BoolProperty

def Add_Symmetrical_Empty():

    bpy.ops.mesh.primitive_plane_add(enter_editmode = True)

    sempty = bpy.context.object
    sempty.name = "SymmEmpty"

    # check if we have a mirror modifier, otherwise add
    if (sempty.modifiers and sempty.modifiers['Mirror']):
        pass
    else:
        bpy.ops.object.modifier_add(type ='MIRROR')

    # Delete all!
    bpy.ops.mesh.select_all(action='TOGGLE')
    bpy.ops.mesh.select_all(action='TOGGLE')
    bpy.ops.mesh.delete(type ='VERT')


class AddSymmetricalEmpty(bpy.types.Operator):
    
    bl_idname = "mesh.primitive_symmetrical_empty_add"
    bl_label = "Add Symmetrical Empty Mesh"
    bl_description = "Add an empty mesh with a Mirror Modifier for quick symmetrical modeling"
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        layout = self.layout
        mirror = bpy.context.object.modifiers['Mirror']

        layout.prop(mirror,'use_clip', text="Use Clipping")

        layout.label("Mirror Axis")
        row = layout.row(align=True)
        row.prop(mirror, "use_x")
        row.prop(mirror, "use_y")
        row.prop(mirror, "use_z")

    def execute(self, context):
        Add_Symmetrical_Empty()
        return {'FINISHED'}

## menu option ##
def menu_item(self, context):
    # only in object mode
    if bpy.context.mode == "OBJECT":
        self.layout.operator("mesh.primitive_symmetrical_empty_add",
            text="Symmetrical Empty", icon="EMPTY_DATA")

## register and add it on top of the list ##
def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_mesh_add.prepend(menu_item)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_mesh_add.remove(menu_item)

if __name__ == "__main__":
    register()
