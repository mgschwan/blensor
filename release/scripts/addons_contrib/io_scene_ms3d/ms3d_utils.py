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

# <pep8 compliant>

###############################################################################
#234567890123456789012345678901234567890123456789012345678901234567890123456789
#--------1---------2---------3---------4---------5---------6---------7---------


# ##### BEGIN COPYRIGHT BLOCK #####
#
# initial script copyright (c)2011,2012 Alexander Nussbaumer
#
# ##### END COPYRIGHT BLOCK #####


#import python stuff
from os import (
        path
        )
from math import (
        radians,
        )
from mathutils import (
        Matrix,
        )


# To support reload properly, try to access a package var,
# if it's there, reload everything
if ('bpy' in locals()):
    import imp
    pass
else:
    pass


#import blender stuff
from bpy import (
        context,
        ops,
        )


###############################################################################
def enable_edit_mode(enable, blender_context=context):
    if blender_context.active_object is None \
            or not blender_context.active_object.type in {'MESH', 'ARMATURE', }:
        return

    if enable:
        modeString = 'EDIT'
    else:
        modeString = 'OBJECT'

    if ops.object.mode_set.poll():
        ops.object.mode_set(mode=modeString)


###############################################################################
def enable_pose_mode(enable, blender_context=context):
    if blender_context.active_object is None \
            or not blender_context.active_object.type in {'ARMATURE', }:
        return

    if enable:
        modeString = 'POSE'
    else:
        modeString = 'OBJECT'

    if ops.object.mode_set.poll():
        ops.object.mode_set(mode=modeString)


###############################################################################
def select_all(select):
    if select:
        actionString = 'SELECT'
    else:
        actionString = 'DESELECT'

    if ops.object.select_all.poll():
        ops.object.select_all(action=actionString)

    if ops.mesh.select_all.poll():
        ops.mesh.select_all(action=actionString)

    if ops.pose.select_all.poll():
        ops.pose.select_all(action=actionString)


###############################################################################
def create_coordination_system_matrix(options):
    # DEBUG
    #return Matrix(), Matrix()

    matrix_coordination_system = None

    if (options.is_coordinate_system_import):
        matrix_coordination_system = Matrix.Rotation(radians(+90), 4, 'Z') \
                * Matrix.Rotation(radians(+90), 4, 'X')
    elif (options.is_coordinate_system_export):
        matrix_coordination_system = Matrix.Rotation(radians(-90), 4, 'X') \
                * Matrix.Rotation(radians(-90), 4, 'Z')
    else:
        matrix_coordination_system = Matrix()

    return matrix_coordination_system * options.prop_scale, \
            matrix_coordination_system


###############################################################################
def pre_setup_environment(porter, blender_context):
    # inject undo to porter
    # and turn off undo
    porter.undo = blender_context.user_preferences.edit.use_global_undo
    blender_context.user_preferences.edit.use_global_undo = False

    # inject active_object to self
    porter.active_object = blender_context.scene.objects.active

    # change to a well defined mode
    enable_edit_mode(True)

    # enable face-selection-mode
    blender_context.tool_settings.mesh_select_mode = (False, False, True)

    # change back to object mode
    enable_edit_mode(False)

    blender_context.scene.update()

    # inject matrix_scaled_coordination_system to self
    porter.matrix_scaled_coordination_system, \
            porter.matrix_coordination_system \
            = create_coordination_system_matrix(porter.options)

    # inject splitted filepath
    porter.filepath_splitted = path.split(porter.options.filepath)


###############################################################################
def post_setup_environment(porter, blender_context):
    # restore active object
    blender_context.scene.objects.active = porter.active_object

    if not blender_context.scene.objects.active \
            and blender_context.selected_objects:
        blender_context.scene.objects.active \
                = blender_context.selected_objects[0]

    # restore pre operator undo state
    blender_context.user_preferences.edit.use_global_undo = porter.undo

###############################################################################



###############################################################################
#234567890123456789012345678901234567890123456789012345678901234567890123456789
#--------1---------2---------3---------4---------5---------6---------7---------
# ##### END OF FILE #####
