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
# initial script copyright (c)2011 Alexander Nussbaumer
#
# ##### END COPYRIGHT BLOCK #####


#import python stuff
import math
import mathutils
import os
import sys


#import blender stuff
import bpy
import bpy.ops


_VERBOSE_DEFAULT = bpy.app.debug


###############################################################################
TEXT_OPERATOR = "MilkShape3D MS3D (.ms3d)"

FILE_EXT = ".ms3d"
FILE_FILTER = "*.ms3d"


###############################################################################
OPT_HIDDEN = 'HIDDEN'
OPT_ANIMATABLE = 'ANIMATABLE'
OPT_ENUM_FLAG = 'ENUM_FLAG'

LABEL_NAME_OPTIONS = "Advanced Options:"
LABEL_ICON_OPTIONS = 'LAMP'

LABEL_NAME_OBJECT = "World Processing:"
LABEL_ICON_OBJECT = 'WORLD'

LABEL_NAME_PROCESSING = "Object Processing:"
LABEL_ICON_PROCESSING = 'OBJECT_DATAMODE'

LABEL_NAME_ANIMATION = "Animation Processing:"
LABEL_ICON_ANIMATION = 'RENDER_ANIMATION'

LABLE_NAME_REUSE = "ReUse existing data"
LABLE_ICON_REUSE = 'FILE_REFRESH'


###############################################################################
PROP_NAME_VERBOSE = "Verbose"
PROP_DESC_VERBOSE = "Run the converter in debug mode. Check the console for"\
        " output (Warning, may be very slow)"
PROP_DEFAULT_VERBOSE = _VERBOSE_DEFAULT
PROP_OPT_VERBOSE = {OPT_ANIMATABLE}


###############################################################################
PROP_ITEM_COORDINATESYSTEM_1_BY_1 = '0'
PROP_ITEM_COORDINATESYSTEM_IMP = '1'
PROP_ITEM_COORDINATESYSTEM_EXP = '2'
PROP_NAME_COORDINATESYSTEM = "Coordinate system"
PROP_DESC_COORDINATESYSTEM = "Select a coordinate system to export to"
PROP_DEFAULT_COORDINATESYSTEM_IMP = PROP_ITEM_COORDINATESYSTEM_IMP
PROP_DEFAULT_COORDINATESYSTEM_EXP = PROP_ITEM_COORDINATESYSTEM_EXP
PROP_ITEMS_COORDINATESYSTEM = (
        (PROP_ITEM_COORDINATESYSTEM_1_BY_1, "xyz -> xyz (1:1)", "Take axis as"\
                " is (1:1)"),
        (PROP_ITEM_COORDINATESYSTEM_IMP, "yzx -> xyz (import)", "swap axis to"\
                " fit to viewport (import ms3d to blender)"),
        (PROP_ITEM_COORDINATESYSTEM_EXP, "xyz -> yzx (export)", "swap axis to"\
                " fit to viewport (export blender to ms3d)"),
        )
PROP_OPT_COORDINATESYSTEM = {OPT_ANIMATABLE}


###############################################################################
PROP_NAME_SCALE = "Scale"
PROP_DESC_SCALE = "Scale all data"
PROP_DEFAULT_SCALE = 1.0
PROP_MIN_SCALE = 0.001
PROP_MAX_SCALE = 1000.0
PROP_SMIN_SCALE = 0.01
PROP_SMAX_SCALE = 100.0
PROP_OPT_SCALE = {OPT_ANIMATABLE}


###############################################################################
PROP_NAME_UNIT_MM = "Metric [mm]"
PROP_DESC_UNIT_MM = "Setup blender unit to metric [mm]"
PROP_DEFAULT_UNIT_MM = True
PROP_OPT_UNIT_MM = {OPT_ANIMATABLE}


###############################################################################
PROP_NAME_SELECTED = "Only selected mesh(es)"
PROP_DESC_SELECTED = "Export only selected mesh(es), when enabled"
PROP_DEFAULT_SELECTED = False
PROP_OPT_SELECTED = {OPT_ANIMATABLE}


###############################################################################
PROP_ITEM_REUSE_NONE = 'NONE'
PROP_ITEM_REUSE_MATCH_HASH = 'MATCH_HASH'
PROP_ITEM_REUSE_MATCH_VALUES = 'MATCH_VALUES'
###############################################################################
PROP_NAME_REUSE = "Reuse existing data"
PROP_DESC_REUSE = "Reuses existing blender data, by trying to find similar"\
        " data objects to reduce the filesize. (With risk of taking the wrong"\
        " existing data!)"
PROP_DEFAULT_REUSE = PROP_ITEM_REUSE_NONE
#PROP_DEFAULT_REUSE = PROP_ITEM_REUSE_MATCH_VALUES
PROP_ITEMS_REUSE = (
        (PROP_ITEM_REUSE_NONE, "Disabled", "Create every time new data."),
        #(PROP_ITEM_REUSE_MATCH_HASH, "Match by hash ***)", "Take data with"\
        #        " the same custom property 'ms3d_i_hash' value. (even if content is modified or different!)"),
        (PROP_ITEM_REUSE_MATCH_VALUES, "Match by values ***)", "Take data"\
                " with similar color values (diffuse_color, specular_color)"\
                " and texture_slots (images). (even if untested content is"\
                " different!)"),
        )
PROP_OPT_REUSE = {OPT_ANIMATABLE}


###############################################################################
PROP_ITEM_OBJECT_ANIMATION = 'ANIMATION'
PROP_ITEM_OBJECT_GROUP = 'GROUP'
PROP_ITEM_OBJECT_JOINT = 'JOINT'
PROP_ITEM_OBJECT_MATERIAL = 'MATERIAL'
PROP_ITEM_OBJECT_MESH = 'MESH'
PROP_ITEM_OBJECT_SMOOTHGROUPS = 'SMOOTHGROUPS'
PROP_ITEM_OBJECT_TRI_TO_QUAD = 'TRI_TO_QUAD'
###############################################################################
PROP_NAME_OBJECTS_IMP = "Import processing"
PROP_DESC_OBJECTS_IMP = "What to process during import"
PROP_DEFAULT_OBJECTS_IMP = {
        #PROP_ITEM_OBJECT_MESH,
        PROP_ITEM_OBJECT_MATERIAL,
        PROP_ITEM_OBJECT_JOINT,
        PROP_ITEM_OBJECT_SMOOTHGROUPS,
        PROP_ITEM_OBJECT_GROUP,
        #PROP_ITEM_OBJECT_TRI_TO_QUAD,
        }
PROP_ITEMS_OBJECTS_IMP = (
        #(PROP_ITEM_OBJECT_MESH, "Meshes", "vertices, triangles, uv"),
        (PROP_ITEM_OBJECT_MATERIAL, "Materials", "ambient, diffuse, specular,"\
                " emissive, shininess, transparency, diffuse texture,"\
                " alpha texture"),
        (PROP_ITEM_OBJECT_JOINT, "Joints", "joints, bones"),
        #(PROP_ITEM_OBJECT_ANIMATION, "Animation **)", "keyframes"),
        (PROP_ITEM_OBJECT_SMOOTHGROUPS, "Smoothing Groups", "split mesh faces"\
                " according its smoothing groups"),
        (PROP_ITEM_OBJECT_GROUP, "Group", "organize all file objects to a"\
                " single group, named with the filename"),
        (PROP_ITEM_OBJECT_TRI_TO_QUAD, "Tris to Quad", "try to convert"\
                " triangles to quads"),
        )
PROP_OPT_OBJECTS_IMP = {OPT_ENUM_FLAG}


###############################################################################
PROP_NAME_OBJECTS_EXP = "Export processing"
PROP_DESC_OBJECTS_EXP = "What to process during export"
PROP_DEFAULT_OBJECTS_EXP = {
        #PROP_ITEM_OBJECT_MESH,
        PROP_ITEM_OBJECT_MATERIAL,
        }
PROP_ITEMS_OBJECTS_EXP = (
        #(PROP_ITEM_OBJECT_MESH, "Meshes", "vertices, triangles, uv, normals"),
        (PROP_ITEM_OBJECT_MATERIAL, "Materials", "ambient, diffuse, specular,"\
                " emissive, shininess, transparency, diffuse texture,"\
                " alpha texture"),
        (PROP_ITEM_OBJECT_JOINT, "Joints **)", "joints, bones"),
        #(PROP_ITEM_OBJECT_ANIMATION, "Animation **)", "keyframes"),
        )
PROP_OPT_OBJECTS_EXP = {OPT_ENUM_FLAG}


###############################################################################
PROP_NAME_ANIMATION = "Animation **)"
PROP_DESC_ANIMATION = "keyframes (rotations, positions)"
PROP_DEFAULT_ANIMATION = True
PROP_OPT_ANIMATION = {OPT_ANIMATABLE}


###############################################################################
REMARKS_1 = "*)   partial implemented yet"
REMARKS_2 = "**) not implemented yet"
REMARKS_3 = "***) risk of unwanted results"


###############################################################################
def SetupMenuImport(self, layout):
    box = layout.box()
    box.label(LABEL_NAME_OPTIONS, icon=LABEL_ICON_OPTIONS)
    box.prop(self, "prop_verbose", icon='SPEAKER')

    box2 = box.box()
    box2.label(LABLE_NAME_REUSE, icon=LABLE_ICON_REUSE)
    box2.prop(self, "prop_reuse", icon='FILE_REFRESH', expand=True)
    if (PROP_ITEM_REUSE_NONE != self.prop_reuse):
        box2.label(REMARKS_3, icon='ERROR')

    box = layout.box()
    box.label(LABEL_NAME_OBJECT, icon=LABEL_ICON_OBJECT)
    box.prop(self, "prop_unit_mm", icon='SCENE_DATA', expand=True)
    box.prop(self, "prop_coordinate_system", icon='WORLD_DATA', expand=True)
    box.prop(self, "prop_scale", icon='MESH_DATA')

    box = layout.box()
    box.label(LABEL_NAME_PROCESSING, icon=LABEL_ICON_PROCESSING)
    box.prop(self, "prop_objects", icon='MESH_DATA', expand=True)

    if (PROP_ITEM_OBJECT_JOINT in self.prop_objects):
        box = layout.box()
        box.label(LABEL_NAME_ANIMATION, icon=LABEL_ICON_ANIMATION)
        box.prop(self, "prop_animation")
        if (self.prop_animation):
            box.label(REMARKS_2, icon='ERROR')


###############################################################################
def SetupMenuExport(self, layout):
    box = layout.box()
    box.label(LABEL_NAME_OPTIONS, icon=LABEL_ICON_OPTIONS)
    if (bpy.app.debug):
        box.prop(self, "prop_debug", icon='ERROR')
    box.prop(self, "prop_verbose", icon='SPEAKER')

    box = layout.box()
    box.label(LABEL_NAME_OBJECT, icon=LABEL_ICON_OBJECT)
    box.prop(self, "prop_coordinate_system", icon='WORLD_DATA', expand=True)
    box.prop(self, "prop_scale", icon='MESH_DATA')

    box = layout.box()
    box.label(LABEL_NAME_PROCESSING, icon=LABEL_ICON_PROCESSING)
    box.prop(self, "prop_selected", icon='ROTACTIVE')
    box.prop(self, "prop_objects", icon='MESH_DATA', expand=True)

    if (PROP_ITEM_OBJECT_JOINT in self.prop_objects):
        box.label(REMARKS_2, icon='ERROR')

        box = layout.box()
        box.label(LABEL_NAME_ANIMATION, icon=LABEL_ICON_ANIMATION)
        box.prop(self, "prop_animation")


###############################################################################


###############################################################################


TYPE_ARMATURE = 'ARMATURE'
TYPE_EMPTY = 'EMPTY'
TYPE_MESH = 'MESH'
APPLY_TO = 'PREVIEW'


###############################################################################
def EnableEditMode(enable):
    if enable:
        modeString = 'EDIT'
    else:
        modeString = 'OBJECT'

    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode=modeString)


###############################################################################
def EnablePoseMode(enable):
    if enable:
        modeString = 'POSE'
    else:
        modeString = 'OBJECT'

    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode=modeString)


###############################################################################
def SelectAll(select):
    if select:
        actionString = 'SELECT'
    else:
        actionString = 'DESELECT'

    if bpy.ops.object.select_all.poll():
        bpy.ops.object.select_all(action=actionString)

    if bpy.ops.mesh.select_all.poll():
        bpy.ops.mesh.select_all(action=actionString)

    if bpy.ops.pose.select_all.poll():
        bpy.ops.pose.select_all(action=actionString)


###############################################################################
def CreateMatrixViewport(coordinate_system, scale):
    matrixSwapAxis = None

    if bpy.app.build_revision < '42816':
        # for OLD implementation, older than blender rev. 42816
        if (coordinate_system == PROP_ITEM_COORDINATESYSTEM_IMP):
            # MS3D -> Blender
            matrixSwapAxis = mathutils.Matrix((
                    (0.0, 0.0, 1.0, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 0.0, 1.0)
                    ))

        elif (coordinate_system == PROP_ITEM_COORDINATESYSTEM_EXP):
            # Blender -> MS3D
            matrixSwapAxis = mathutils.Matrix((
                    (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 0.0, 0.0, 1.0)
                    ))

        else:
            # 1:1
            matrixSwapAxis = mathutils.Matrix((
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (0.0, 0.0, 0.0, 1.0)
                    ))
    else:
        # for new implementation since blender rev. 42816
        if (coordinate_system == PROP_ITEM_COORDINATESYSTEM_IMP):
            # MS3D -> Blender (since Blender rev.42816)
            matrixSwapAxis = mathutils.Matrix((
                    (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 0.0, 0.0, 1.0)
                    ))

        elif (coordinate_system == PROP_ITEM_COORDINATESYSTEM_EXP):
            # Blender -> MS3D (since Blender rev.42816)
            matrixSwapAxis = mathutils.Matrix((
                    (0.0, 0.0, 1.0, 0.0),
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 0.0, 1.0)
                    ))

        else:
            # 1:1
            matrixSwapAxis = mathutils.Matrix((
                    (1.0, 0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (0.0, 0.0, 0.0, 1.0)
                    ))


    return matrixSwapAxis * scale, matrixSwapAxis


###############################################################################
def PreSetupEnvironment(porterSelf):
    # inject undo to self
    # and turn off undo
    porterSelf.undo = bpy.context.user_preferences.edit.use_global_undo
    bpy.context.user_preferences.edit.use_global_undo = False

    # inject activeObject to self
    porterSelf.activeObject = bpy.context.scene.objects.active

    # change to a well defined mode
    EnableEditMode(True)

    # enable face-selection-mode
    bpy.context.tool_settings.mesh_select_mode = (False, False, True)

    # change back to object mode
    EnableEditMode(False)

    bpy.context.scene.update()

    # inject matrixViewport to self
    porterSelf.matrixViewport, porterSelf.matrixSwapAxis =\
            CreateMatrixViewport(
                    porterSelf.prop_coordinate_system,
                    porterSelf.prop_scale)

    # inject splitted filepath
    porterSelf.filepath_splitted = os.path.split(porterSelf.filepath)


###############################################################################
def PostSetupEnvironment(porterSelf, adjustView):
    if (adjustView):
        # set metrics
        bpy.context.scene.unit_settings.system = 'METRIC'
        bpy.context.scene.unit_settings.system_rotation = 'DEGREES'
        bpy.context.scene.unit_settings.scale_length = 0.001 # 1.0mm
        bpy.context.scene.unit_settings.use_separate = False
        bpy.context.tool_settings.normal_size = 1.0 # 1.0mm

        # set all 3D views to texture shaded
        # and set up the clipping
        for screen in bpy.context.blend_data.screens:
            for area in screen.areas:
                if (area.type != 'VIEW_3D'):
                    continue

                for space in area.spaces:
                    if (space.type != 'VIEW_3D'):
                        continue

                    screen.scene.game_settings.material_mode = 'MULTITEXTURE'
                    space.viewport_shade = 'SOLID'
                    space.show_textured_solid = True
                    space.clip_start = 0.1 # 0.1mm
                    space.clip_end = 1000000.0 # 1km

    bpy.context.scene.update()

    # restore active object
    bpy.context.scene.objects.active = porterSelf.activeObject

    if ((not bpy.context.scene.objects.active)
            and (bpy.context.selected_objects)):
        bpy.context.scene.objects.active = bpy.context.selected_objects[0]

    # restore pre operator undo state
    bpy.context.user_preferences.edit.use_global_undo = porterSelf.undo


###############################################################################
#234567890123456789012345678901234567890123456789012345678901234567890123456789
#--------1---------2---------3---------4---------5---------6---------7---------
# ##### END OF FILE #####
