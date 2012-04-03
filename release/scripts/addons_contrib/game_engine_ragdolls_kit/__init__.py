# ***** BEGIN GPL LICENSE BLOCK *****
#
# Script copyright (C) Marcus Jenkins (Blenderartists user name FunkyWyrm)
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
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
# --------------------------------------------------------------------------

bl_info = {
    "name": "BRIK - Blender Ragdoll Implementation Kit",
    "author": "FunkyWyrm",
    "version": (0,2),
    "blender": (2, 5, 5),
    "location": "View 3D > Tool Shelf > BRIK Panel",
    "description": "Kit for creating ragdoll structures from armatures and implementing them in the game engine.",
    "warning": "Preliminary release for testing purposes. Use with caution on important files.",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"\
        "Scripts/Game_Engine/BRIK_ragdolls",
    "tracker_url": "https://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=24946",
    "category": "Game Engine"}


if "bpy" in locals():
    import imp
    imp.reload(brik)
else:
    from . import brik

import bpy

################################################################################
##### REGISTER #####
def register():
    bpy.utils.register_module(__name__)
    pass

def unregister():
    bpy.utils.unregister_module(__name__)
    pass
    
if __name__ == "__main__":
    register()
