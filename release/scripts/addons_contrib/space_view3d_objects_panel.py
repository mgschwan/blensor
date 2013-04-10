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
#  Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Add Objects Panel",
    "author": "Murat Egretli (Demohero)",
    "version": (1,2),
    "blender": (2, 61, 0),
    "location": "View3D > Toolbar",
    "description": "add objects(mesh, curve etc.) from Toolbar",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"\
        "Scripts/",
    "tracker_url": "https://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=22154",
    "category": "3D View"}


import bpy


class View3DPanel():
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    

class VIEW3D_PT_add_menu(View3DPanel,bpy.types.Panel):
    bl_context = "objectmode"
    bl_label = "Add Objects"
    bl_options = {"DEFAULT_CLOSED"}
    
    def draw(self, context):
        layout = self.layout

        layout.menu("INFO_MT_mesh_add", text="Mesh", icon='OUTLINER_OB_MESH')
        layout.menu("INFO_MT_curve_add", text="Curve", icon='OUTLINER_OB_CURVE')
        layout.menu("INFO_MT_surface_add", text="Surface", icon='OUTLINER_OB_SURFACE')
        layout.operator_menu_enum("object.metaball_add", "type", text="Metaball", icon='OUTLINER_OB_META')
        layout.menu("INFO_MT_armature_add", icon='OUTLINER_OB_ARMATURE')
        layout.operator_menu_enum("object.lamp_add", "type", text="Lamp", icon='OUTLINER_OB_LAMP')
        layout.operator_menu_enum("object.effector_add", "type", text="Force Field", icon='OUTLINER_OB_EMPTY')
        layout.operator("object.add", text="Lattice", icon='OUTLINER_OB_LATTICE').type = 'LATTICE'
        layout.operator("object.add", text="Empty", icon='OUTLINER_OB_EMPTY').type = 'EMPTY'
        layout.operator("object.speaker_add", text="Speaker", icon='OUTLINER_OB_SPEAKER')
        layout.operator("object.camera_add", text="Camera", icon='OUTLINER_OB_CAMERA')
        layout.operator("object.text_add", text="Text", icon='OUTLINER_OB_FONT')
      
# register the class
def register():
    bpy.utils.register_module(__name__)
 
    pass 

def unregister():
    bpy.utils.unregister_module(__name__)
 
    pass 

if __name__ == "__main__": 
    register()
