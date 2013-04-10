# ***** BEGIN GPL LICENSE BLOCK *****
#
# Script copyright (C) Marcus Jenkins (Blenderartists user name FunkyWyrm)
# Modified by Kees Brouwer (Blenderartists user name Wraaah)
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
    "blender": (2, 55, 0),
    "api": 31965,
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
    #Register brik add-on
    bpy.utils.register_module(__name__)

    #Set-up gui menu properties using the bpy.types.Scene type
    scnType = bpy.types.Scene
    
    FloatProperty = bpy.props.FloatProperty
    scnType.brik_ragdoll_mass = FloatProperty( name = "Ragdoll mass", 
                                               default = 80.0, min = 0.05, max= 99999,
                                               description = "The total mass of the ragdoll rigid body structure created with BRIK",  
                                               update = brik.calc_ragdoll_mass)
                                    
    # triplet setup.... ( return value, name, description )
    EnumProperty = bpy.props.EnumProperty
    menu_options = [  ( "All", "All", "Use all armature bones" ) ]
    #enumProp = EnumProperty( name = "Bone selection", items = menu_options, 
    enumProp = EnumProperty( name = "Bone selection", items = brik_bone_list, 
                    description = "Use the bones from the selected bone group" )
  
    scnType.brik_bone_groups = enumProp
    pass

def unregister():
    bpy.utils.unregister_module(__name__)
    pass
    
def brik_bone_list(self, context):
    ob = bpy.context.object
    group_list = [  ( "All", "All", "Use all armature bones" ) ]
    if ob.type == 'ARMATURE':
        #Select bone groups
        ob_pose = ob.pose
        bone_groups = ob_pose.bone_groups
        for item in bone_groups:
            group_list = group_list + [(item.name, item.name, "Use bones in selected bone group")]
            
    return group_list

if __name__ == "__main__":
    register()
    
