# Paul "BrikBot" Marshall
# Created: July 24, 2011
# Last Modified: November 20, 2011
# Homepage (blog): http://post.darkarsenic.com/
#                       //blog.darkarsenic.com/
#
# Coded in IDLE, tested in Blender 2.59.
# Search for "@todo" to quickly find sections that need work.
#
# ##### BEGIN GPL LICENSE BLOCK #####
#
#  The Blender Rock Creation tool is for rapid generation of mesh rocks in Blender.
#  Copyright (C) 2011  Paul Marshall
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "StairBuilder",
    "author": "Nick van Adium",
    "version": (1,1),
    "blender": (2, 6, 1),
    "location": "View3D > Add > Stairs",
    "description": "Creates a straight-run staircase with railings and stringer",
    "warning": "Add-on is very feature incomplete beyond basic functionality.",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Add Mesh"}

if "bpy" in locals():
    import imp
    imp.reload(stairbuilder)
else:
    from add_mesh_stairs import stairbuilder

import bpy

# Register:

def menu_func_stairs(self, context):
    self.layout.operator(stairbuilder.stairs.bl_idname, text="StairBuilder", icon = "PLUGIN")

def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_mesh_add.append(menu_func_stairs)

def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_mesh_add.remove(menu_func_stairs)

if __name__ == "__main__":
    register()
