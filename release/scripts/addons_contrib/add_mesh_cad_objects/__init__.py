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
# Contributed to by
# SAYproductions, meta-androcto #

bl_info = {
    "name": "Cad Objects",
    "author": "SAYproductions, meta-androcto",
    "version": (0, 2),
    "blender": (2, 6, 4),
    "location": "View3D > Add > Mesh > Cad Objects",
    "description": "Add cad object types",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"\
        "Scripts",
    "tracker_url": "https://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=32711",
    "category": "Add Mesh"}


if "bpy" in locals():
    import imp
    imp.reload(add_mesh_balcony)
    imp.reload(add_mesh_sove)
    imp.reload(add_mesh_window)
    imp.reload(add_mesh_beam_builder)

else:
    from . import add_mesh_balcony
    from . import add_mesh_sove
    from . import add_mesh_window
    from . import add_mesh_beam_builder

import bpy


class INFO_MT_mesh_objects_add(bpy.types.Menu):
    # Define the "mesh objects" menu
    bl_idname = "INFO_MT_cad_objects_add"
    bl_label = "Cad Objects"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.menu("INFO_MT_mesh_beambuilder_add",
            text="Beam Builder")
        layout.operator("mesh.add_say3d_balcony",
            text="Balcony")
        layout.operator("mesh.add_say3d_sove",
            text="Sove")
        layout.operator("mesh.add_say3d_pencere",
            text="Window")


# Register all operators and panels

# Define "Extras" menu
def menu_func(self, context):
    self.layout.menu("INFO_MT_cad_objects_add", icon="PLUGIN")


def register():
    bpy.utils.register_module(__name__)

    # Add "Extras" menu to the "Add Mesh" menu
    bpy.types.INFO_MT_mesh_add.append(menu_func)


def unregister():
    bpy.utils.unregister_module(__name__)

    # Remove "Extras" menu from the "Add Mesh" menu.
    bpy.types.INFO_MT_mesh_add.remove(menu_func)

if __name__ == "__main__":
    register()
