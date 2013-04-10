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
    "name": "Geodesic Domes",
    "author": "PKHG , Meta Androcto, Kilon original for 2.49 from Andy Houston",
    "version": (0,2,3),
    "blender": (2, 61, 0),
    "location": "View3D > UI > Geodesic...",
    "description": "Choice for objects",
    "warning": "not yet finished",
    "wiki_url": "http://wiki.blender.org/index.php?title=Extensions:2.6/Py/Scripts/Modeling/Geodesic_Domes",
    "tracker_url": "http://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=29609",
    "category": "Object"}

"""
Added save and load of parameters 14-12-2011 PKHG
Added one possible *.bak for GD_0.GD (one time) 17-12-2011
"""
if "bpy" in locals():
    import imp
    imp.reload(third_domes_panel)
    
else:
    from geodesic_domes import third_domes_panel
   
import bpy
from bpy.props import *

def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()



