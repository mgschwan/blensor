# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you may redistribute it, and/or
# modify it, under the terms of the GNU General Public License
# as published by the Free Software Foundation - either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, write to:
#
#	the Free Software Foundation Inc.
#	51 Franklin Street, Fifth Floor
#	Boston, MA 02110-1301, USA
#
# or go online at: http://www.gnu.org/licenses/ to view license options.
#
# ***** END GPL LICENCE BLOCK *****

bl_info = {
    "name": "WallFactory",
    "author": "Jambay, Brikbot",
    "version": (0, 6, 0),
    "blender": (2, 6, 1),
    "location": "View3D > Add > Mesh",
    "description": "Adds a block/rock wall.",
    "warning": "WIP - updates pending and API not final for Blender",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"\
        "Scripts/Add_Mesh/WallFactory",
    "tracker_url": "https://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=111",
    "category": "Add Mesh"}

"""
    This script builds a wall; at current 3D-Cursor location.
    The wall can be modified to be a disc (radial), curved (slope), or dome (radial+slope).
    Actually, it could be a path, or a tower, or anything made with blocks.
    Crenelations also work which can double as arrow slits or support beam holes.
    Slots, both vertical and horizontal, can be added as openings.
    Steps and platforms may be added as extensions to the wall.
"""

# Version History
# v0.59 2011/09/13	Restructured as "factory" set of scripts - preparation for including rocks.
# v0.58 2010/12/06	Added "backside" for shelf and steps, and "cantilevered step" options.
# v0.57 2010/12/03	Minor updates for Blender SVN maintenance.
# v0.56 2010/11/19	Revised UI for property access/display.
# V0.55 2010/11/15	Added stairs, improved shelf, fixed plan generation.
# V0.54 2010/11/11	Changed version number to match sourceforge check-in,
# 			basic shelf, and, some general cleanup.
# V0.5 2010/10/31	Converted to Blender 2.5.4
# V0.4 2009/11/29	Converted to Blender 2.5
# V0.3 2009/11/28	Re-did much of the internals, everything works better, 
# 			especially edge finding.
# V0.2 2008/03/??	Reworked nearly all the code, many new features
# V0.1 2007/09/14	First release!


if "bpy" in locals():
    import imp
    imp.reload(Wallfactory)
else:
    from add_mesh_walls import Wallfactory

import bpy

################################################################################
##### REGISTER #####

# Define "Wall" menu
def add_mesh_wall_ops(self, context):
    self.layout.operator(Wallfactory.add_mesh_wallb.bl_idname, text="Block Wall", icon="PLUGIN")
#    self.layout.operator(Wallfactory.add_mesh_wallr.bl_idname, text="Rocks", icon="PLUGIN")
#    self.layout.operator(Wallfactory.add_mesh_column.bl_idname, text="Columns", icon="PLUGIN")


# Add "Wall" options to the "Add Mesh" menu
def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_mesh_add.append(add_mesh_wall_ops)
#    bpy.types.INFO_MT_mesh_add.append(add_mesh_rockwall_button)
#    bpy.types.INFO_MT_mesh_add.append(add_mesh_column_button)

# Remove "Wall" options from the "Add Mesh" menu
def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_mesh_add.remove(add_mesh_wall_ops)
#    bpy.types.INFO_MT_mesh_add.remove(add_mesh_rockwall_button)
#    bpy.types.INFO_MT_mesh_add.remove(add_mesh_column_button)
    
if __name__ == "__main__":
    register()
