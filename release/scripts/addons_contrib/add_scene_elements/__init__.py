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
# by meta-androcto, parts based on work by Erich Toven #

bl_info = {
    "name": "Scene Elements",
    "author": "Meta Androcto, ",
    "version": (0, 2),
    "blender": (2, 64, 0),
    "location": "View3D > Add > Scene Elements",
    "description": "Add Scenes & Lights, Objects.",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6"\
        "/Py/Scripts",
    "tracker_url": "http://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=32682",
    "category": "Object"}


if "bpy" in locals():
    import imp
    imp.reload(scene_camera)
    imp.reload(scene_lighting)
    imp.reload(scene_materials)
    imp.reload(scene_objects)
    imp.reload(scene_objects_cycles)

else:
    from . import scene_camera
    from . import scene_lighting
    from . import scene_materials
    from . import scene_objects
    from . import scene_objects_cycles
	
import bpy

class INFO_MT_mesh_objects_add(bpy.types.Menu):
    # Define the "mesh objects" menu
    bl_idname = "INFO_MT_scene_elements"
    bl_label = "Scene Elements"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("camera.add_scene",
            text="Scene_Camera")
        layout.operator("materials.add_scene",
            text="Scene_Objects_BI")
        layout.operator("plane.add_scene",
            text="Scene_Plane")
        layout.operator("objects_cycles.add_scene",
            text="Scene_Objects_Cycles")

class INFO_MT_mesh_lamps_add(bpy.types.Menu):
    # Define the "mesh objects" menu
    bl_idname = "INFO_MT_scene_lamps"
    bl_label = "Lighting Elements"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("object.add_single_spot",
            text="Add Single Spot")
        layout.operator("object.add_basic_3point",
            text="Add 3 Point Spot Setup")
        layout.operator("object.add_basic_2point",
            text="Add 2 Point Setup")
        layout.operator("object.add_area_3point",
            text="Add 3 Point Setup")

# Register all operators and panels
# Define "Extras" menu
def menu_func(self, context):
    self.layout.menu("INFO_MT_scene_elements", icon="PLUGIN")
    self.layout.menu("INFO_MT_scene_lamps", icon="PLUGIN")
def register():
    bpy.utils.register_module(__name__)
    # Add "Extras" menu to the "Add Mesh" menu
    bpy.types.INFO_MT_add.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    # Remove "Extras" menu from the "Add Mesh" menu.
    bpy.types.INFO_MT_add.remove(menu_func)

if __name__ == "__main__":
    register()
