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
from random import (
        randrange,
        )

# To support reload properly, try to access a package var,
# if it's there, reload everything
if ('bpy' in locals()):
    import imp
    if 'io_scene_ms3d.ms3d_strings' in locals():
        imp.reload(io_scene_ms3d.ms3d_strings)
    if 'io_scene_ms3d.ms3d_spec' in locals():
        imp.reload(io_scene_ms3d.ms3d_spec)
    if 'io_scene_ms3d.ms3d_utils' in locals():
        imp.reload(io_scene_ms3d.ms3d_utils)
    #if 'io_scene_ms3d.ms3d_import' in locals():
    #    imp.reload(io_scene_ms3d.ms3d_import)
    #if 'io_scene_ms3d.ms3d_export' in locals():
    #    imp.reload(io_scene_ms3d.ms3d_export)
else:
    from io_scene_ms3d.ms3d_strings import (
            ms3d_str,
            )
    from io_scene_ms3d.ms3d_spec import (
            Ms3dSpec,
            )
    from io_scene_ms3d.ms3d_utils import (
            enable_edit_mode,
            )
    #from io_scene_ms3d.ms3d_import import ( Ms3dImporter, )
    #from io_scene_ms3d.ms3d_export import ( Ms3dExporter, )


#import blender stuff
from bmesh import (
        from_edit_mesh,
        )
from bpy.utils import (
        register_class,
        unregister_class,
        )
from bpy_extras.io_utils import (
        ExportHelper,
        ImportHelper,
        )
from bpy.props import (
        BoolProperty,
        CollectionProperty,
        EnumProperty,
        FloatProperty,
        FloatVectorProperty,
        IntProperty,
        StringProperty,
        PointerProperty,
        )
from bpy.types import (
        Operator,
        PropertyGroup,
        Panel,
        Armature,
        Bone,
        Mesh,
        Material,
        Action,
        Group,
        )
from bpy.app import (
        debug,
        )


class Ms3dUi:
    DEFAULT_VERBOSE = debug

    ###############################################################################
    FLAG_TEXTURE_COMBINE_ALPHA = 'COMBINE_ALPHA'
    FLAG_TEXTURE_HAS_ALPHA = 'HAS_ALPHA'
    FLAG_TEXTURE_SPHERE_MAP = 'SPHERE_MAP'

    @staticmethod
    def texture_mode_from_ms3d(ms3d_value):
        ui_value = set()
        if (ms3d_value & Ms3dSpec.FLAG_TEXTURE_COMBINE_ALPHA) \
                == Ms3dSpec.FLAG_TEXTURE_COMBINE_ALPHA:
            ui_value.add(Ms3dUi.FLAG_TEXTURE_COMBINE_ALPHA)
        if (ms3d_value & Ms3dSpec.FLAG_TEXTURE_HAS_ALPHA) \
                == Ms3dSpec.FLAG_TEXTURE_HAS_ALPHA:
            ui_value.add(Ms3dUi.FLAG_TEXTURE_HAS_ALPHA)
        if (ms3d_value & Ms3dSpec.FLAG_TEXTURE_SPHERE_MAP) \
                == Ms3dSpec.FLAG_TEXTURE_SPHERE_MAP:
            ui_value.add(Ms3dUi.FLAG_TEXTURE_SPHERE_MAP)
        return ui_value

    @staticmethod
    def texture_mode_to_ms3d(ui_value):
        ms3d_value = Ms3dSpec.FLAG_TEXTURE_NONE

        if Ms3dUi.FLAG_TEXTURE_COMBINE_ALPHA in ui_value:
            ms3d_value |= Ms3dSpec.FLAG_TEXTURE_COMBINE_ALPHA
        if Ms3dUi.FLAG_TEXTURE_HAS_ALPHA in ui_value:
            ms3d_value |= Ms3dSpec.FLAG_TEXTURE_HAS_ALPHA
        if Ms3dUi.FLAG_TEXTURE_SPHERE_MAP in ui_value:
            ms3d_value |= Ms3dSpec.FLAG_TEXTURE_SPHERE_MAP
        return ms3d_value


    MODE_TRANSPARENCY_SIMPLE = 'SIMPLE'
    MODE_TRANSPARENCY_DEPTH_BUFFERED_WITH_ALPHA_REF \
            = 'DEPTH_BUFFERED_WITH_ALPHA_REF'
    MODE_TRANSPARENCY_DEPTH_SORTED_TRIANGLES = 'DEPTH_SORTED_TRIANGLES'

    @staticmethod
    def transparency_mode_from_ms3d(ms3d_value):
        if(ms3d_value == Ms3dSpec.MODE_TRANSPARENCY_SIMPLE):
            return Ms3dUi.MODE_TRANSPARENCY_SIMPLE
        elif(ms3d_value == Ms3dSpec.MODE_TRANSPARENCY_DEPTH_BUFFERED_WITH_ALPHA_REF):
            return Ms3dUi.MODE_TRANSPARENCY_DEPTH_BUFFERED_WITH_ALPHA_REF
        elif(ms3d_value == Ms3dSpec.MODE_TRANSPARENCY_DEPTH_SORTED_TRIANGLES):
            return Ms3dUi.MODE_TRANSPARENCY_DEPTH_SORTED_TRIANGLES
        return None

    @staticmethod
    def transparency_mode_to_ms3d(ui_value):
        if(ui_value == Ms3dUi.MODE_TRANSPARENCY_SIMPLE):
            return Ms3dSpec.MODE_TRANSPARENCY_SIMPLE
        elif(ui_value == Ms3dUi.MODE_TRANSPARENCY_DEPTH_BUFFERED_WITH_ALPHA_REF):
            return Ms3dSpec.MODE_TRANSPARENCY_DEPTH_BUFFERED_WITH_ALPHA_REF
        elif(ui_value == Ms3dUi.MODE_TRANSPARENCY_DEPTH_SORTED_TRIANGLES):
            return Ms3dSpec.MODE_TRANSPARENCY_DEPTH_SORTED_TRIANGLES
        return None


    FLAG_NONE = 'NONE'
    FLAG_SELECTED = 'SELECTED'
    FLAG_HIDDEN = 'HIDDEN'
    FLAG_SELECTED2 = 'SELECTED2'
    FLAG_DIRTY = 'DIRTY'
    FLAG_ISKEY = 'ISKEY'
    FLAG_NEWLYCREATED = 'NEWLYCREATED'
    FLAG_MARKED = 'MARKED'

    @staticmethod
    def flags_from_ms3d(ms3d_value):
        ui_value = set()
        if (ms3d_value & Ms3dSpec.FLAG_SELECTED) == Ms3dSpec.FLAG_SELECTED:
            ui_value.add(Ms3dUi.FLAG_SELECTED)
        if (ms3d_value & Ms3dSpec.FLAG_HIDDEN) == Ms3dSpec.FLAG_HIDDEN:
            ui_value.add(Ms3dUi.FLAG_HIDDEN)
        if (ms3d_value & Ms3dSpec.FLAG_SELECTED2) == Ms3dSpec.FLAG_SELECTED2:
            ui_value.add(Ms3dUi.FLAG_SELECTED2)
        if (ms3d_value & Ms3dSpec.FLAG_DIRTY) == Ms3dSpec.FLAG_DIRTY:
            ui_value.add(Ms3dUi.FLAG_DIRTY)
        if (ms3d_value & Ms3dSpec.FLAG_ISKEY) == Ms3dSpec.FLAG_ISKEY:
            ui_value.add(Ms3dUi.FLAG_ISKEY)
        if (ms3d_value & Ms3dSpec.FLAG_NEWLYCREATED) == Ms3dSpec.FLAG_NEWLYCREATED:
            ui_value.add(Ms3dUi.FLAG_NEWLYCREATED)
        if (ms3d_value & Ms3dSpec.FLAG_MARKED) == Ms3dSpec.FLAG_MARKED:
            ui_value.add(Ms3dUi.FLAG_MARKED)
        return ui_value

    @staticmethod
    def flags_to_ms3d(ui_value):
        ms3d_value = Ms3dSpec.FLAG_NONE
        if Ms3dUi.FLAG_SELECTED in ui_value:
            ms3d_value |= Ms3dSpec.FLAG_SELECTED
        if Ms3dUi.FLAG_HIDDEN in ui_value:
            ms3d_value |= Ms3dSpec.FLAG_HIDDEN
        if Ms3dUi.FLAG_SELECTED2 in ui_value:
            ms3d_value |= Ms3dSpec.FLAG_SELECTED2
        if Ms3dUi.FLAG_DIRTY in ui_value:
            ms3d_value |= Ms3dSpec.FLAG_DIRTY
        if Ms3dUi.FLAG_ISKEY in ui_value:
            ms3d_value |= Ms3dSpec.FLAG_ISKEY
        if Ms3dUi.FLAG_NEWLYCREATED in ui_value:
            ms3d_value |= Ms3dSpec.FLAG_NEWLYCREATED
        if Ms3dUi.FLAG_MARKED in ui_value:
            ms3d_value |= Ms3dSpec.FLAG_MARKED
        return ms3d_value

    ###########################################################################
    ICON_OPTIONS = 'LAMP'
    ICON_OBJECT = 'WORLD'
    ICON_PROCESSING = 'OBJECT_DATAMODE'
    ICON_ANIMATION = 'RENDER_ANIMATION'


    ###########################################################################
    PROP_DEFAULT_VERBOSE = DEFAULT_VERBOSE


    ###########################################################################
    PROP_ITEM_COORDINATESYSTEM_1BY1 = '0'
    PROP_ITEM_COORDINATESYSTEM_IMP = '1'
    PROP_ITEM_COORDINATESYSTEM_EXP = '2'
    PROP_DEFAULT_COORDINATESYSTEM_IMP = PROP_ITEM_COORDINATESYSTEM_IMP
    PROP_DEFAULT_COORDINATESYSTEM_EXP = PROP_ITEM_COORDINATESYSTEM_EXP


    ###########################################################################
    PROP_DEFAULT_SCALE = 1.0
    PROP_MIN_SCALE = 0.001
    PROP_MAX_SCALE = 1000.0
    PROP_SMIN_SCALE = 0.01
    PROP_SMAX_SCALE = 100.0


    ###########################################################################
    PROP_DEFAULT_UNIT_MM = True


    ###########################################################################
    PROP_DEFAULT_SELECTED = False


    ###########################################################################
    PROP_ITEM_OBJECT_ANIMATION = 'ANIMATION'
    PROP_ITEM_OBJECT_GROUP = 'GROUP'
    PROP_ITEM_OBJECT_JOINT = 'JOINT'
    PROP_ITEM_OBJECT_MATERIAL = 'MATERIAL'
    PROP_ITEM_OBJECT_MESH = 'MESH'
    PROP_ITEM_OBJECT_SMOOTHGROUPS = 'SMOOTHGROUPS'
    ###########################################################################
    PROP_DEFAULT_OBJECTS_IMP = {
            #PROP_ITEM_OBJECT_MESH,
            PROP_ITEM_OBJECT_MATERIAL,
            PROP_ITEM_OBJECT_JOINT,
            PROP_ITEM_OBJECT_SMOOTHGROUPS,
            PROP_ITEM_OBJECT_GROUP,
            }


    ###########################################################################
    PROP_DEFAULT_OBJECTS_EXP = {
            #PROP_ITEM_OBJECT_MESH,
            PROP_ITEM_OBJECT_MATERIAL,
            }


    ###########################################################################
    PROP_DEFAULT_ANIMATION = False

    ###########################################################################
    PROP_DEFAULT_APPLY_MODIFIER = False
    PROP_ITEM_APPLY_MODIFIER_MODE_PREVIEW = 'PREVIEW'
    PROP_ITEM_APPLY_MODIFIER_MODE_RENDER = 'RENDER'
    PROP_DEFAULT_APPLY_MODIFIER_MODE = PROP_ITEM_APPLY_MODIFIER_MODE_PREVIEW

    ###########################################################################
    OPT_SMOOTHING_GROUP_APPLY = 'io_scene_ms3d.apply_smoothing_group'
    OPT_GROUP_APPLY = 'io_scene_ms3d.apply_group'


###############################################################################
class Ms3dImportOperator(Operator, ImportHelper):
    """ Load a MilkShape3D MS3D File """
    bl_idname = 'io_scene_ms3d.import'
    bl_label = ms3d_str['BL_LABEL_IMPORTER']
    bl_description = ms3d_str['BL_DESCRIPTION_IMPORTER']
    bl_options = {'PRESET', }
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    @staticmethod
    def menu_func(cls, context):
        cls.layout.operator(
                Ms3dImportOperator.bl_idname,
                text=ms3d_str['TEXT_OPERATOR'],
                )

    filename_ext = ms3d_str['FILE_EXT']

    filter_glob = StringProperty(
            default=ms3d_str['FILE_FILTER'],
            options={'HIDDEN', 'SKIP_SAVE', }
            )

    filepath = StringProperty(
            subtype='FILE_PATH',
            options={'HIDDEN', 'SKIP_SAVE', }
            )

    prop_verbose = BoolProperty(
            name=ms3d_str['PROP_NAME_VERBOSE'],
            description=ms3d_str['PROP_DESC_VERBOSE'],
            default=Ms3dUi.PROP_DEFAULT_VERBOSE,
            )

    prop_coordinate_system = EnumProperty(
            name=ms3d_str['PROP_NAME_COORDINATESYSTEM'],
            description=ms3d_str['PROP_DESC_COORDINATESYSTEM'],
            items=( (Ms3dUi.PROP_ITEM_COORDINATESYSTEM_1BY1,
                            ms3d_str['PROP_ITEM_COORDINATESYSTEM_1_BY_1_1'],
                            ms3d_str['PROP_ITEM_COORDINATESYSTEM_1_BY_1_2']),
                    (Ms3dUi.PROP_ITEM_COORDINATESYSTEM_IMP,
                            ms3d_str['PROP_ITEM_COORDINATESYSTEM_IMP_1'],
                            ms3d_str['PROP_ITEM_COORDINATESYSTEM_IMP_2']),
                    (Ms3dUi.PROP_ITEM_COORDINATESYSTEM_EXP,
                            ms3d_str['PROP_ITEM_COORDINATESYSTEM_EXP_1'],
                            ms3d_str['PROP_ITEM_COORDINATESYSTEM_EXP_2']),
                    ),
            default=Ms3dUi.PROP_DEFAULT_COORDINATESYSTEM_IMP,
            )

    prop_scale = FloatProperty(
            name=ms3d_str['PROP_NAME_SCALE'],
            description=ms3d_str['PROP_DESC_SCALE'],
            default=Ms3dUi.PROP_DEFAULT_SCALE,
            min=Ms3dUi.PROP_MIN_SCALE,
            max=Ms3dUi.PROP_MAX_SCALE,
            soft_min=Ms3dUi.PROP_SMIN_SCALE,
            soft_max=Ms3dUi.PROP_SMAX_SCALE,
            )

    prop_unit_mm = BoolProperty(
            name=ms3d_str['PROP_NAME_UNIT_MM'],
            description=ms3d_str['PROP_DESC_UNIT_MM'],
            default=Ms3dUi.PROP_DEFAULT_UNIT_MM,
            )

    prop_animation = BoolProperty(
            name=ms3d_str['PROP_NAME_ANIMATION'],
            description=ms3d_str['PROP_DESC_ANIMATION'],
            default=Ms3dUi.PROP_DEFAULT_ANIMATION,
            )


    @property
    def is_coordinate_system_1by1(self):
        return (Ms3dUi.PROP_ITEM_COORDINATESYSTEM_1BY1 \
                in self.prop_coordinate_system)

    @property
    def is_coordinate_system_import(self):
        return (Ms3dUi.PROP_ITEM_COORDINATESYSTEM_IMP \
                in self.prop_coordinate_system)

    @property
    def is_coordinate_system_export(self):
        return (Ms3dUi.PROP_ITEM_COORDINATESYSTEM_EXP \
                in self.prop_coordinate_system)


    # draw the option panel
    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label(ms3d_str['LABEL_NAME_OPTIONS'], icon=Ms3dUi.ICON_OPTIONS)
        box.prop(self, 'prop_verbose', icon='SPEAKER')

        box = layout.box()
        box.label(ms3d_str['LABEL_NAME_OBJECT'], icon=Ms3dUi.ICON_OBJECT)
        box.prop(self, 'prop_unit_mm', icon='SCENE_DATA', expand=True)
        box.prop(self, 'prop_coordinate_system', icon='WORLD_DATA', expand=True)
        box.prop(self, 'prop_scale', icon='MESH_DATA')

        box = layout.box()
        box.label(ms3d_str['LABEL_NAME_ANIMATION'], icon=Ms3dUi.ICON_ANIMATION)
        box.prop(self, 'prop_animation')
        if (self.prop_animation):
            box.label(ms3d_str['REMARKS_2'], icon='ERROR')

    # entrypoint for MS3D -> blender
    def execute(self, blender_context):
        """ start executing """
        from io_scene_ms3d.ms3d_import import (Ms3dImporter, )
        return Ms3dImporter(self).read(blender_context)

    def invoke(self, blender_context, event):
        blender_context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL', }


class Ms3dExportOperator(Operator, ExportHelper):
    """Save a MilkShape3D MS3D File"""
    bl_idname = 'io_scene_ms3d.export'
    bl_label = ms3d_str['BL_LABEL_EXPORTER']
    bl_description = ms3d_str['BL_DESCRIPTION_EXPORTER']
    bl_options = {'PRESET', }
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    def menu_func(cls, context):
        cls.layout.operator(
                Ms3dExportOperator.bl_idname,
                text=ms3d_str['TEXT_OPERATOR']
                )

    filename_ext = ms3d_str['FILE_EXT']

    filter_glob = StringProperty(
            default=ms3d_str['FILE_FILTER'],
            options={'HIDDEN', 'SKIP_SAVE', }
            )

    filepath = StringProperty(
            subtype='FILE_PATH',
            options={'HIDDEN', 'SKIP_SAVE', }
            )

    prop_verbose = BoolProperty(
            name=ms3d_str['PROP_NAME_VERBOSE'],
            description=ms3d_str['PROP_DESC_VERBOSE'],
            default=Ms3dUi.PROP_DEFAULT_VERBOSE,
            )

    prop_coordinate_system = EnumProperty(
            name=ms3d_str['PROP_NAME_COORDINATESYSTEM'],
            description=ms3d_str['PROP_DESC_COORDINATESYSTEM'],
            items=( (Ms3dUi.PROP_ITEM_COORDINATESYSTEM_1BY1,
                            ms3d_str['PROP_ITEM_COORDINATESYSTEM_1_BY_1_1'],
                            ms3d_str['PROP_ITEM_COORDINATESYSTEM_1_BY_1_2']),
                    (Ms3dUi.PROP_ITEM_COORDINATESYSTEM_IMP,
                            ms3d_str['PROP_ITEM_COORDINATESYSTEM_IMP_1'],
                            ms3d_str['PROP_ITEM_COORDINATESYSTEM_IMP_2']),
                    (Ms3dUi.PROP_ITEM_COORDINATESYSTEM_EXP,
                            ms3d_str['PROP_ITEM_COORDINATESYSTEM_EXP_1'],
                            ms3d_str['PROP_ITEM_COORDINATESYSTEM_EXP_2']),
                    ),
            default=Ms3dUi.PROP_DEFAULT_COORDINATESYSTEM_EXP,
            )

    prop_scale = FloatProperty(
            name=ms3d_str['PROP_NAME_SCALE'],
            description=ms3d_str['PROP_DESC_SCALE'],
            default=1.0 / Ms3dUi.PROP_DEFAULT_SCALE,
            min=Ms3dUi.PROP_MIN_SCALE,
            max=Ms3dUi.PROP_MAX_SCALE,
            soft_min=Ms3dUi.PROP_SMIN_SCALE,
            soft_max=Ms3dUi.PROP_SMAX_SCALE,
            )

    prop_objects = EnumProperty(
            name=ms3d_str['PROP_NAME_OBJECTS_EXP'],
            description=ms3d_str['PROP_DESC_OBJECTS_EXP'],
            items=( #(Ms3dUi.PROP_ITEM_OBJECT_MESH,
                    #        ms3d_str['PROP_ITEM_OBJECT_MESH_1'],
                    #        ms3d_str['PROP_ITEM_OBJECT_MESH_2']),
                    (Ms3dUi.PROP_ITEM_OBJECT_MATERIAL,
                            ms3d_str['PROP_ITEM_OBJECT_MATERIAL_1'],
                            ms3d_str['PROP_ITEM_OBJECT_MATERIAL_2']),
                    (Ms3dUi.PROP_ITEM_OBJECT_JOINT,
                            ms3d_str['PROP_ITEM_OBJECT_JOINT_1'],
                            ms3d_str['PROP_ITEM_OBJECT_JOINT_2']),
                    #(Ms3dUi.PROP_ITEM_OBJECT_ANIMATION,
                    #        ms3d_str['PROP_ITEM_OBJECT_ANIMATION_1'],
                    #        ms3d_str['PROP_ITEM_OBJECT_ANIMATION_2']),
                    ),
            default=Ms3dUi.PROP_DEFAULT_OBJECTS_EXP,
            options={'ENUM_FLAG', 'ANIMATABLE', },
            )

    prop_selected = BoolProperty(
            name=ms3d_str['PROP_NAME_SELECTED'],
            description=ms3d_str['PROP_DESC_SELECTED'],
            default=Ms3dUi.PROP_DEFAULT_SELECTED,
            )

    prop_animation = BoolProperty(
            name=ms3d_str['PROP_NAME_ANIMATION'],
            description=ms3d_str['PROP_DESC_ANIMATION'],
            default=Ms3dUi.PROP_DEFAULT_ANIMATION,
            )

    prop_apply_modifier = BoolProperty(
            name=ms3d_str['PROP_NAME_APPLY_MODIFIER'],
            description=ms3d_str['PROP_DESC_APPLY_MODIFIER'],
            default=Ms3dUi.PROP_DEFAULT_APPLY_MODIFIER,
            )
    prop_apply_modifier_mode = EnumProperty(
            name=ms3d_str['PROP_NAME_APPLY_MODIFIER_MODE'],
            description=ms3d_str['PROP_DESC_APPLY_MODIFIER_MODE'],
            items=( (Ms3dUi.PROP_ITEM_APPLY_MODIFIER_MODE_PREVIEW,
                            ms3d_str['PROP_ITEM_APPLY_MODIFIER_MODE_PREVIEW_1'],
                            ms3d_str['PROP_ITEM_APPLY_MODIFIER_MODE_PREVIEW_2']),
                    (Ms3dUi.PROP_ITEM_APPLY_MODIFIER_MODE_RENDER,
                            ms3d_str['PROP_ITEM_APPLY_MODIFIER_MODE_RENDER_1'],
                            ms3d_str['PROP_ITEM_APPLY_MODIFIER_MODE_RENDER_2']),
                    ),
            default=Ms3dUi.PROP_DEFAULT_APPLY_MODIFIER_MODE,
            )

    @property
    def handle_animation(self):
        return (Ms3dUi.PROP_ITEM_OBJECT_ANIMATION in self.prop_objects)

    @property
    def handle_materials(self):
        return (Ms3dUi.PROP_ITEM_OBJECT_MATERIAL in self.prop_objects)

    @property
    def handle_joints(self):
        return (Ms3dUi.PROP_ITEM_OBJECT_JOINT in self.prop_objects)

    @property
    def handle_smoothing_groups(self):
        return (Ms3dUi.PROP_ITEM_OBJECT_SMOOTHGROUPS in self.prop_objects)

    @property
    def handle_groups(self):
        return (Ms3dUi.PROP_ITEM_OBJECT_GROUP in self.prop_objects)


    @property
    def is_coordinate_system_1by1(self):
        return (Ms3dUi.PROP_ITEM_COORDINATESYSTEM_1BY1 \
                in self.prop_coordinate_system)

    @property
    def is_coordinate_system_import(self):
        return (Ms3dUi.PROP_ITEM_COORDINATESYSTEM_IMP \
                in self.prop_coordinate_system)

    @property
    def is_coordinate_system_export(self):
        return (Ms3dUi.PROP_ITEM_COORDINATESYSTEM_EXP \
                in self.prop_coordinate_system)


    # draw the option panel
    def draw(self, context):
        layout = self.layout

        # DEBUG:
        layout.row().label(ms3d_str['REMARKS_2'], icon='ERROR')

        box = layout.box()
        box.label(ms3d_str['LABEL_NAME_OPTIONS'], icon=Ms3dUi.ICON_OPTIONS)
        box.prop(self, 'prop_verbose', icon='SPEAKER')

        box = layout.box()
        box.label(ms3d_str['LABEL_NAME_OBJECT'], icon=Ms3dUi.ICON_OBJECT)
        box.prop(self, 'prop_coordinate_system', icon='WORLD_DATA', expand=True)
        box.prop(self, 'prop_scale', icon='MESH_DATA')

        box = layout.box()
        box.label(ms3d_str['LABEL_NAME_PROCESSING'],
                icon=Ms3dUi.ICON_PROCESSING)
        box.prop(self, 'prop_selected', icon='ROTACTIVE')
        """
        box.prop(self, 'prop_objects', icon='MESH_DATA', expand=True)

        if (Ms3dUi.PROP_ITEM_OBJECT_JOINT in self.prop_objects):
            box.label(ms3d_str['REMARKS_2'], icon='ERROR')

            box = layout.box()
            box.label(ms3d_str['LABEL_NAME_ANIMATION'],
                    icon=Ms3dUi.ICON_ANIMATION)
            box.prop(self, 'prop_animation')
        """

    # entrypoint for blender -> MS3D
    def execute(self, blender_context):
        """start executing"""
        from io_scene_ms3d.ms3d_export import (Ms3dExporter, )
        return Ms3dExporter(self).write(blender_context)

    #
    def invoke(self, blender_context, event):
        blender_context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL", }


###############################################################################
##
###############################################################################


###############################################################################
class Ms3dSetSmoothingGroupOperator(Operator):
    bl_idname = Ms3dUi.OPT_SMOOTHING_GROUP_APPLY
    bl_label = ms3d_str['BL_LABEL_SMOOTHING_GROUP_OPERATOR']
    bl_options = {'INTERNAL', }

    smoothing_group_index = IntProperty(
            name=ms3d_str['PROP_SMOOTHING_GROUP_INDEX'],
            options={'HIDDEN', 'SKIP_SAVE', },
            )

    @classmethod
    def poll(cls, context):
        return (context
                and context.object
                and context.object.type in {'MESH', }
                and context.object.data
                and context.object.data.ms3d is not None
                and context.mode == 'EDIT_MESH'
                and context.tool_settings.mesh_select_mode[2]
                )

    def execute(self, context):
        custom_data = context.object.data.ms3d
        blender_mesh = context.object.data
        bm = from_edit_mesh(blender_mesh)
        layer_smoothing_group = bm.faces.layers.int.get(
                ms3d_str['OBJECT_LAYER_SMOOTHING_GROUP'])
        if custom_data.apply_mode in {'SELECT', 'DESELECT', }:
            if layer_smoothing_group is not None:
                is_select = (custom_data.apply_mode == 'SELECT')
                for bmf in bm.faces:
                    if (bmf[layer_smoothing_group] \
                            == self.smoothing_group_index):
                        bmf.select_set(is_select)
        elif custom_data.apply_mode == 'ASSIGN':
            if layer_smoothing_group is None:
                layer_smoothing_group = bm.faces.layers.int.new(
                        ms3d_str['OBJECT_LAYER_SMOOTHING_GROUP'])
                blender_mesh_object = context.object
                blender_modifier = blender_mesh_object.modifiers.get(
                        ms3d_str['OBJECT_MODIFIER_SMOOTHING_GROUP'])
                if blender_modifier is None:
                    blender_modifier = blender_mesh_object.modifiers.new(
                            ms3d_str['OBJECT_MODIFIER_SMOOTHING_GROUP'],
                            type='EDGE_SPLIT')
                    blender_modifier.show_expanded = False
                    blender_modifier.use_edge_angle = False
                    blender_modifier.use_edge_sharp = True
            blender_face_list = []
            for bmf in bm.faces:
                if not bmf.smooth:
                    bmf.smooth = True
                if bmf.select:
                    bmf[layer_smoothing_group] = self.smoothing_group_index
                    blender_face_list.append(bmf)
            edge_dict = {}
            for bmf in blender_face_list:
                bmf.smooth = True
                for bme in bmf.edges:
                    if edge_dict.get(bme) is None:
                        edge_dict[bme] = 0
                    else:
                        edge_dict[bme] += 1
                    is_border = (edge_dict[bme] == 0)
                    if is_border:
                        surround_face_smoothing_group_index \
                                = self.smoothing_group_index
                        for bmf in bme.link_faces:
                            if bmf[layer_smoothing_group] \
                                    != surround_face_smoothing_group_index:
                                surround_face_smoothing_group_index \
                                        = bmf[layer_smoothing_group]
                                break;
                        if surround_face_smoothing_group_index \
                                == self.smoothing_group_index:
                            is_border = False
                    bme.seam = is_border
                    bme.smooth = not is_border
        bm.free()
        enable_edit_mode(False)
        enable_edit_mode(True)
        return {'FINISHED', }


class Ms3dGroupOperator(Operator):
    bl_idname = Ms3dUi.OPT_GROUP_APPLY
    bl_label = ms3d_str['BL_LABEL_GROUP_OPERATOR']
    bl_options = {'INTERNAL', }

    mode = EnumProperty(
            items=( ('', "", ""),
                    ('ADD_GROUP',
                            ms3d_str['ENUM_ADD_GROUP_1'],
                            ms3d_str['ENUM_ADD_GROUP_2']),
                    ('REMOVE_GROUP',
                            ms3d_str['ENUM_REMOVE_GROUP_1'],
                            ms3d_str['ENUM_REMOVE_GROUP_2']),
                    ('ASSIGN',
                            ms3d_str['ENUM_ASSIGN_1'],
                            ms3d_str['ENUM_ASSIGN_2_GROUP']),
                    ('REMOVE',
                            ms3d_str['ENUM_REMOVE_1'],
                            ms3d_str['ENUM_REMOVE_2_GROUP']),
                    ('SELECT',
                            ms3d_str['ENUM_SELECT_1'],
                            ms3d_str['ENUM_SELECT_2_GROUP']),
                    ('DESELECT',
                            ms3d_str['ENUM_DESELECT_1'],
                            ms3d_str['ENUM_DESELECT_2_GROUP']),
                    ),
            options={'HIDDEN', 'SKIP_SAVE', },
            )

    @classmethod
    def poll(cls, context):
        return (context
                and context.object
                and context.object.type in {'MESH', }
                and context.object.data
                and context.object.data.ms3d is not None
                and context.mode == 'EDIT_MESH'
                #and context.object.data.ms3d.selected_group_index != -1
                )

    def execute(self, context):
        custom_data = context.object.data.ms3d
        blender_mesh = context.object.data
        bm = None
        bm = from_edit_mesh(blender_mesh)

        if self.mode == 'ADD_GROUP':
            item = custom_data.create_group()
            layer_group = bm.faces.layers.int.get(
                    ms3d_str['OBJECT_LAYER_GROUP'])
            if layer_group is None:
                bm.faces.layers.int.new(ms3d_str['OBJECT_LAYER_GROUP'])

        elif self.mode == 'REMOVE_GROUP':
            custom_data.remove_group()

        elif (custom_data.selected_group_index >= 0) and (
                custom_data.selected_group_index < len(custom_data.groups)):
            if self.mode in {'SELECT', 'DESELECT', }:
                layer_group = bm.faces.layers.int.get(
                        ms3d_str['OBJECT_LAYER_GROUP'])
                if layer_group is not None:
                    is_select = (self.mode == 'SELECT')
                    id = custom_data.groups[
                            custom_data.selected_group_index].id
                    for bmf in bm.faces:
                        if bmf[layer_group] == id:
                            bmf.select_set(is_select)

            elif self.mode in {'ASSIGN', 'REMOVE', }:
                layer_group = bm.faces.layers.int.get(
                        ms3d_str['OBJECT_LAYER_GROUP'])
                if layer_group is None:
                    layer_group = bm.faces.layers.int.new(
                            ms3d_str['OBJECT_LAYER_GROUP'])

                is_assign = (self.mode == 'ASSIGN')
                id = custom_data.groups[custom_data.selected_group_index].id
                for bmf in bm.faces:
                    if bmf.select:
                        if is_assign:
                            bmf[layer_group] = id
                        else:
                            bmf[layer_group] = -1
        if bm is not None:
            bm.free()
        enable_edit_mode(False)
        enable_edit_mode(True)
        return {'FINISHED', }


###############################################################################
class Ms3dGroupProperties(PropertyGroup):
    name = StringProperty(
            name=ms3d_str['PROP_NAME_NAME'],
            description=ms3d_str['PROP_DESC_GROUP_NAME'],
            default="",
            #options={'HIDDEN', },
            )

    flags = EnumProperty(
            name=ms3d_str['PROP_NAME_FLAGS'],
            description=ms3d_str['PROP_DESC_FLAGS_GROUP'],
            items=(#(Ms3dUi.FLAG_NONE, ms3d_str['ENUM_FLAG_NONE_1'],
                   #         ms3d_str['ENUM_FLAG_NONE_2'],
                   #         Ms3dSpec.FLAG_NONE),
                    (Ms3dUi.FLAG_SELECTED,
                            ms3d_str['ENUM_FLAG_SELECTED_1'],
                            ms3d_str['ENUM_FLAG_SELECTED_2'],
                            Ms3dSpec.FLAG_SELECTED),
                    (Ms3dUi.FLAG_HIDDEN,
                            ms3d_str['ENUM_FLAG_HIDDEN_1'],
                            ms3d_str['ENUM_FLAG_HIDDEN_2'],
                            Ms3dSpec.FLAG_HIDDEN),
                    (Ms3dUi.FLAG_SELECTED2,
                            ms3d_str['ENUM_FLAG_SELECTED2_1'],
                            ms3d_str['ENUM_FLAG_SELECTED2_2'],
                            Ms3dSpec.FLAG_SELECTED2),
                    (Ms3dUi.FLAG_DIRTY,
                            ms3d_str['ENUM_FLAG_DIRTY_1'],
                            ms3d_str['ENUM_FLAG_DIRTY_2'],
                            Ms3dSpec.FLAG_DIRTY),
                    (Ms3dUi.FLAG_ISKEY,
                            ms3d_str['ENUM_FLAG_ISKEY_1'],
                            ms3d_str['ENUM_FLAG_ISKEY_2'],
                            Ms3dSpec.FLAG_ISKEY),
                    (Ms3dUi.FLAG_NEWLYCREATED,
                            ms3d_str['ENUM_FLAG_NEWLYCREATED_1'],
                            ms3d_str['ENUM_FLAG_NEWLYCREATED_2'],
                            Ms3dSpec.FLAG_NEWLYCREATED),
                    (Ms3dUi.FLAG_MARKED,
                            ms3d_str['ENUM_FLAG_MARKED_1'],
                            ms3d_str['ENUM_FLAG_MARKED_2'],
                            Ms3dSpec.FLAG_MARKED),
                    ),
            default=Ms3dUi.flags_from_ms3d(Ms3dSpec.DEFAULT_FLAGS),
            options={'ENUM_FLAG', 'ANIMATABLE', },
            )

    comment = StringProperty(
            name=ms3d_str['PROP_NAME_COMMENT'],
            description=ms3d_str['PROP_DESC_COMMENT_GROUP'],
            default="",
            #options={'HIDDEN', },
            )

    template_list_controls = StringProperty(
            default="",
            options={'HIDDEN', 'SKIP_SAVE', },
            )

    id = IntProperty(options={'HIDDEN', },)


class Ms3dModelProperties(PropertyGroup):
    name = StringProperty(
            name=ms3d_str['PROP_NAME_NAME'],
            description=ms3d_str['PROP_DESC_NAME_MODEL'],
            default="",
            #options={'HIDDEN', },
            )

    joint_size = FloatProperty(
            name=ms3d_str['PROP_NAME_JOINT_SIZE'],
            description=ms3d_str['PROP_DESC_JOINT_SIZE'],
            min=0, max=1, precision=3, step=0.1,
            default=Ms3dSpec.DEFAULT_MODEL_JOINT_SIZE,
            subtype='FACTOR',
            #options={'HIDDEN', },
            )

    transparency_mode = EnumProperty(
            name=ms3d_str['PROP_NAME_TRANSPARENCY_MODE'],
            description=ms3d_str['PROP_DESC_TRANSPARENCY_MODE'],
            items=( (Ms3dUi.MODE_TRANSPARENCY_SIMPLE,
                            ms3d_str['PROP_MODE_TRANSPARENCY_SIMPLE_1'],
                            ms3d_str['PROP_MODE_TRANSPARENCY_SIMPLE_2'],
                            Ms3dSpec.MODE_TRANSPARENCY_SIMPLE),
                    (Ms3dUi.MODE_TRANSPARENCY_DEPTH_SORTED_TRIANGLES,
                            ms3d_str['PROP_MODE_TRANSPARENCY_DEPTH_SORTED_TRIANGLES_1'],
                            ms3d_str['PROP_MODE_TRANSPARENCY_DEPTH_SORTED_TRIANGLES_2'],
                            Ms3dSpec.MODE_TRANSPARENCY_DEPTH_SORTED_TRIANGLES),
                    (Ms3dUi.MODE_TRANSPARENCY_DEPTH_BUFFERED_WITH_ALPHA_REF,
                            ms3d_str['PROP_MODE_TRANSPARENCY_DEPTH_BUFFERED_WITH_ALPHA_REF_1'],
                            ms3d_str['PROP_MODE_TRANSPARENCY_DEPTH_BUFFERED_WITH_ALPHA_REF_2'],
                            Ms3dSpec.MODE_TRANSPARENCY_DEPTH_BUFFERED_WITH_ALPHA_REF),
                    ),
            default=Ms3dUi.transparency_mode_from_ms3d(
                    Ms3dSpec.DEFAULT_MODEL_TRANSPARENCY_MODE),
            #options={'HIDDEN', },
            )

    alpha_ref = FloatProperty(
            name=ms3d_str['PROP_NAME_ALPHA_REF'],
            description=ms3d_str['PROP_DESC_ALPHA_REF'],
            min=0, max=1, precision=3, step=0.1,
            default=0.5,
            subtype='FACTOR',
            #options={'HIDDEN', },
            )

    comment = StringProperty(
            name=ms3d_str['PROP_NAME_COMMENT'],
            description=ms3d_str['PROP_DESC_COMMENT_MODEL'],
            default="",
            #options={'HIDDEN', },
            )

    ##########################
    # ms3d group handling
    #
    apply_mode = EnumProperty(
            items=( ('ASSIGN',
                            ms3d_str['ENUM_ASSIGN_1'],
                            ms3d_str['ENUM_ASSIGN_2_SMOOTHING_GROUP']),
                    ('SELECT',
                            ms3d_str['ENUM_SELECT_1'],
                            ms3d_str['ENUM_SELECT_2_SMOOTHING_GROUP']),
                    ('DESELECT',
                            ms3d_str['ENUM_DESELECT_1'],
                            ms3d_str['ENUM_DESELECT_2_SMOOTHING_GROUP']),
                    ),
            default='SELECT',
            options={'HIDDEN', 'SKIP_SAVE', },
            )

    selected_group_index = IntProperty(
            default=-1,
            min=-1,
            options={'HIDDEN', 'SKIP_SAVE', },
            )
    #
    # ms3d group handling
    ##########################

    groups = CollectionProperty(
            type=Ms3dGroupProperties,
            #options={'HIDDEN', },
            )


    def generate_unique_id(self):
        return randrange(1, 0x7FFFFFFF) # pseudo unique id

    def create_group(self):
        item = self.groups.add()
        item.id = self.generate_unique_id()
        length = len(self.groups)
        self.selected_group_index = length - 1

        item.name = ms3d_str['STRING_FORMAT_GROUP'].format(length)
        return item

    def remove_group(self):
        index = self.selected_group_index
        length = len(self.groups)
        if (index >= 0) and (index < length):
            if index > 0 or length == 1:
                self.selected_group_index = index - 1
            self.groups.remove(index)


class Ms3dArmatureProperties(PropertyGroup):
    name = StringProperty(
            name=ms3d_str['PROP_NAME_NAME'],
            description=ms3d_str['PROP_DESC_NAME_ARMATURE'],
            default="",
            #options={'HIDDEN', },
            )


class Ms3dJointProperties(PropertyGroup):
    name = StringProperty(
            name=ms3d_str['PROP_NAME_NAME'],
            description=ms3d_str['PROP_DESC_NAME_JOINT'],
            default="",
            #options={'HIDDEN', },
            )

    flags = EnumProperty(
            name=ms3d_str['PROP_NAME_FLAGS'],
            description=ms3d_str['PROP_DESC_FLAGS_JOINT'],
            items=(#(Ms3dUi.FLAG_NONE,
                   #         ms3d_str['ENUM_FLAG_NONE_1'],
                   #         ms3d_str['ENUM_FLAG_NONE_2'],
                   #         Ms3dSpec.FLAG_NONE),
                    (Ms3dUi.FLAG_SELECTED,
                            ms3d_str['ENUM_FLAG_SELECTED_1'],
                            ms3d_str['ENUM_FLAG_SELECTED_2'],
                            Ms3dSpec.FLAG_SELECTED),
                    (Ms3dUi.FLAG_HIDDEN,
                            ms3d_str['ENUM_FLAG_HIDDEN_1'],
                            ms3d_str['ENUM_FLAG_HIDDEN_2'],
                            Ms3dSpec.FLAG_HIDDEN),
                    (Ms3dUi.FLAG_SELECTED2,
                            ms3d_str['ENUM_FLAG_SELECTED2_1'],
                            ms3d_str['ENUM_FLAG_SELECTED2_2'],
                            Ms3dSpec.FLAG_SELECTED2),
                    (Ms3dUi.FLAG_DIRTY,
                            ms3d_str['ENUM_FLAG_DIRTY_1'],
                            ms3d_str['ENUM_FLAG_DIRTY_2'],
                            Ms3dSpec.FLAG_DIRTY),
                    (Ms3dUi.FLAG_ISKEY,
                            ms3d_str['ENUM_FLAG_ISKEY_1'],
                            ms3d_str['ENUM_FLAG_ISKEY_2'],
                            Ms3dSpec.FLAG_ISKEY),
                    (Ms3dUi.FLAG_NEWLYCREATED,
                            ms3d_str['ENUM_FLAG_NEWLYCREATED_1'],
                            ms3d_str['ENUM_FLAG_NEWLYCREATED_2'],
                            Ms3dSpec.FLAG_NEWLYCREATED),
                    (Ms3dUi.FLAG_MARKED,
                            ms3d_str['ENUM_FLAG_MARKED_1'],
                            ms3d_str['ENUM_FLAG_MARKED_2'],
                            Ms3dSpec.FLAG_MARKED),
                    ),
            default=Ms3dUi.flags_from_ms3d(Ms3dSpec.DEFAULT_FLAGS),
            options={'ENUM_FLAG', 'ANIMATABLE', },
            )

    color = FloatVectorProperty(
            name=ms3d_str['PROP_NAME_COLOR'],
            description=ms3d_str['PROP_DESC_COLOR_JOINT'],
            subtype='COLOR', size=3, min=0, max=1, precision=3, step=0.1,
            default=(0.8, 0.8, 0.8),
            #options={'HIDDEN', },
            )

    comment = StringProperty(
            name=ms3d_str['PROP_NAME_COMMENT'],
            description=ms3d_str['PROP_DESC_COMMENT_JOINT'],
            default="",
            #options={'HIDDEN', },
            )


class Ms3dMaterialHelper:
    @staticmethod
    def on_update_ambient(cls, context):
        pass

    @staticmethod
    def on_update_diffuse(cls, context):
        cls.id_data.diffuse_color = cls.diffuse[0:3]
        cls.id_data.diffuse_intensity = cls.diffuse[3]
        pass

    @staticmethod
    def on_update_specular(cls, context):
        cls.id_data.specular_color = cls.specular[0:3]
        cls.id_data.specular_intensity = cls.specular[3]
        pass

    @staticmethod
    def on_update_emissive(cls, context):
        cls.id_data.emit = (cls.emissive[0] + cls.emissive[1] \
                + cls.emissive[2]) / 3.0
        pass

    @staticmethod
    def on_update_shininess(cls, context):
        cls.id_data.specular_hardness = cls.shininess * 4.0
        pass

    @staticmethod
    def on_update_transparency(cls, context):
        cls.id_data.alpha = cls.transparency
        pass


class Ms3dMaterialProperties(PropertyGroup):
    name = StringProperty(
            name=ms3d_str['PROP_NAME_NAME'],
            description=ms3d_str['PROP_DESC_NAME_MATERIAL'],
            default="",
            #options={'HIDDEN', },
            )

    ambient = FloatVectorProperty(
            name=ms3d_str['PROP_NAME_AMBIENT'],
            description=ms3d_str['PROP_DESC_AMBIENT'],
            subtype='COLOR', size=4, min=0, max=1, precision=3, step=0.1,
            default=(0.2, 0.2, 0.2, 1.0), # OpenGL default for ambient
            update=Ms3dMaterialHelper.on_update_ambient,
            #options={'HIDDEN', },
            )

    diffuse = FloatVectorProperty(
            name=ms3d_str['PROP_NAME_DIFFUSE'],
            description=ms3d_str['PROP_DESC_DIFFUSE'],
            subtype='COLOR', size=4, min=0, max=1, precision=3, step=0.1,
            default=(0.8, 0.8, 0.8, 1.0), # OpenGL default for diffuse
            update=Ms3dMaterialHelper.on_update_diffuse,
            #options={'HIDDEN', },
            )

    specular = FloatVectorProperty(
            name=ms3d_str['PROP_NAME_SPECULAR'],
            description=ms3d_str['PROP_DESC_SPECULAR'],
            subtype='COLOR', size=4, min=0, max=1, precision=3, step=0.1,
            default=(0.0, 0.0, 0.0, 1.0), # OpenGL default for specular
            update=Ms3dMaterialHelper.on_update_specular,
            #options={'HIDDEN', },
            )

    emissive = FloatVectorProperty(
            name=ms3d_str['PROP_NAME_EMISSIVE'],
            description=ms3d_str['PROP_DESC_EMISSIVE'],
            subtype='COLOR', size=4, min=0, max=1, precision=3, step=0.1,
            default=(0.0, 0.0, 0.0, 1.0), # OpenGL default for emissive
            update=Ms3dMaterialHelper.on_update_emissive,
            #options={'HIDDEN', },
            )

    shininess = FloatProperty(
            name=ms3d_str['PROP_NAME_SHININESS'],
            description=ms3d_str['PROP_DESC_SHININESS'],
            min=0, max=Ms3dSpec.MAX_MATERIAL_SHININESS, precision=3, step=0.1,
            default=0,
            subtype='FACTOR',
            update=Ms3dMaterialHelper.on_update_shininess,
            #options={'HIDDEN', },
            )

    transparency = FloatProperty(
            name=ms3d_str['PROP_NAME_TRANSPARENCY'],
            description=ms3d_str['PROP_DESC_TRANSPARENCY'],
            min=0, max=1, precision=3, step=0.1,
            default=0,
            subtype='FACTOR',
            update=Ms3dMaterialHelper.on_update_transparency,
            #options={'HIDDEN', },
            )

    mode = EnumProperty(
            name=ms3d_str['PROP_NAME_MODE'],
            description=ms3d_str['PROP_DESC_MODE_TEXTURE'],
            items=( (Ms3dUi.FLAG_TEXTURE_COMBINE_ALPHA,
                            ms3d_str['PROP_FLAG_TEXTURE_COMBINE_ALPHA_1'],
                            ms3d_str['PROP_FLAG_TEXTURE_COMBINE_ALPHA_2'],
                            Ms3dSpec.FLAG_TEXTURE_COMBINE_ALPHA),
                    (Ms3dUi.FLAG_TEXTURE_HAS_ALPHA,
                            ms3d_str['PROP_FLAG_TEXTURE_HAS_ALPHA_1'],
                            ms3d_str['PROP_FLAG_TEXTURE_HAS_ALPHA_2'],
                            Ms3dSpec.FLAG_TEXTURE_HAS_ALPHA),
                    (Ms3dUi.FLAG_TEXTURE_SPHERE_MAP,
                            ms3d_str['PROP_FLAG_TEXTURE_SPHERE_MAP_1'],
                            ms3d_str['PROP_FLAG_TEXTURE_SPHERE_MAP_2'],
                            Ms3dSpec.FLAG_TEXTURE_SPHERE_MAP),
                    ),
            default=Ms3dUi.texture_mode_from_ms3d(
                    Ms3dSpec.DEFAULT_MATERIAL_MODE),
            options={'ANIMATABLE', 'ENUM_FLAG', },
            )

    texture = StringProperty(
            name=ms3d_str['PROP_NAME_TEXTURE'],
            description=ms3d_str['PROP_DESC_TEXTURE'],
            default="",
            subtype = 'FILE_PATH'
            #options={'HIDDEN', },
            )

    alphamap = StringProperty(
            name=ms3d_str['PROP_NAME_ALPHAMAP'],
            description=ms3d_str['PROP_DESC_ALPHAMAP'],
            default="",
            subtype = 'FILE_PATH'
            #options={'HIDDEN', },
            )

    comment = StringProperty(
            name=ms3d_str['PROP_NAME_COMMENT'],
            description=ms3d_str['PROP_DESC_COMMENT_MATERIAL'],
            default="",
            #options={'HIDDEN', },
            )


###############################################################################
class Ms3dMeshPanel(Panel):
    bl_label = ms3d_str['LABEL_PANEL_MODEL']
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'

    @classmethod
    def poll(cls, context):
        return (context
                and context.object
                and context.object.type in {'MESH', }
                and context.object.data
                and context.object.data.ms3d is not None
                )

    def draw_header(self, context):
        layout = self.layout
        layout.label(icon='PLUGIN')

    def draw(self, context):
        layout = self.layout
        custom_data = context.object.data.ms3d

        row = layout.row()
        row.prop(custom_data, 'name')

        col = layout.column()
        row = col.row()
        row.prop(custom_data, 'joint_size')
        row = col.row()
        row.prop(custom_data, 'transparency_mode')
        row = col.row()
        row.prop(custom_data, 'alpha_ref', )

        row = layout.row()
        row.prop(custom_data, 'comment')


class Ms3dMaterialPanel(Panel):
    bl_label = ms3d_str['LABEL_PANEL_MATERIALS']
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'material'

    @classmethod
    def poll(cls, context):
        return (context
                and context.object
                and context.object.type in {'MESH', }
                and context.object.data
                and context.object.data.ms3d is not None
                and context.material
                and context.material.ms3d is not None
                )

    def draw_header(self, context):
        layout = self.layout
        layout.label(icon='PLUGIN')

    def draw(self, context):
        layout = self.layout
        custom_data = context.material.ms3d

        row = layout.row()
        row.prop(custom_data, 'name')

        col = layout.column()
        row = col.row()
        row.prop(custom_data, 'ambient')
        row.prop(custom_data, 'diffuse')
        row = col.row()
        row.prop(custom_data, 'specular')
        row.prop(custom_data, 'emissive')
        row = col.row()
        row.prop(custom_data, 'shininess')
        row.prop(custom_data, 'transparency')

        col = layout.column()
        row = col.row()
        row.prop(custom_data, 'texture')
        row = col.row()
        row.prop(custom_data, 'alphamap')
        row = col.row()
        row.prop(custom_data, 'mode', expand=True)

        row = layout.row()
        row.prop(custom_data, 'comment')


class Ms3dBonePanel(Panel):
    bl_label = ms3d_str['LABEL_PANEL_JOINTS']
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'bone'

    @classmethod
    def poll(cls, context):
        return (context
                and context.object.type in {'ARMATURE', }
                and context.active_bone
                and isinstance(context.active_bone, Bone)
                and context.active_bone.ms3d is not None
                )

    def draw_header(self, context):
        layout = self.layout
        layout.label(icon='PLUGIN')

    def draw(self, context):
        import bpy
        layout = self.layout
        custom_data = context.active_bone.ms3d

        row = layout.row()
        row.prop(custom_data, 'name')
        row = layout.row()
        row.prop(custom_data, 'flags', expand=True)
        row = layout.row()
        row.prop(custom_data, 'color')
        row = layout.row()
        row.prop(custom_data, 'comment')


class Ms3dGroupPanel(Panel):
    bl_label = ms3d_str['LABEL_PANEL_GROUPS']
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'

    @classmethod
    def poll(cls, context):
        return (context
                and context.object
                and context.object.type in {'MESH', }
                and context.object.data
                and context.object.data.ms3d is not None
                )

    def draw_header(self, context):
        layout = self.layout
        layout.label(icon='PLUGIN')

    def draw(self, context):
        layout = self.layout
        custom_data = context.object.data.ms3d

        row = layout.row()
        row.template_list(
                custom_data, 'groups',
                custom_data, 'selected_group_index',
                prop_list='template_list_controls',
                rows=2,
                type='DEFAULT',
                )

        col = row.column(align=True)
        col.operator(
                Ms3dUi.OPT_GROUP_APPLY,
                text="", icon='ZOOMIN').mode = 'ADD_GROUP'
        col.operator(
                Ms3dUi.OPT_GROUP_APPLY,
                text="", icon='ZOOMOUT').mode = 'REMOVE_GROUP'

        index = custom_data.selected_group_index
        collection = custom_data.groups
        if (index >= 0 and index < len(collection)):
            row = layout.row()
            row.prop(collection[index], 'name')

            if (context.mode == 'EDIT_MESH') and (
                    context.tool_settings.mesh_select_mode[2]):
                row = layout.row()
                subrow = row.row(align=True)
                subrow.operator(
                        Ms3dUi.OPT_GROUP_APPLY,
                        text=ms3d_str['ENUM_ASSIGN_1']).mode = 'ASSIGN'
                subrow.operator(
                        Ms3dUi.OPT_GROUP_APPLY,
                        text=ms3d_str['ENUM_REMOVE_1']).mode = 'REMOVE'
                subrow = row.row(align=True)
                subrow.operator(
                        Ms3dUi.OPT_GROUP_APPLY,
                        text=ms3d_str['ENUM_SELECT_1']).mode = 'SELECT'
                subrow.operator(
                        Ms3dUi.OPT_GROUP_APPLY,
                        text=ms3d_str['ENUM_DESELECT_1']).mode = 'DESELECT'

            row = layout.row()
            row.prop(collection[index], 'flags', expand=True)

            row = layout.row()
            row.prop(collection[index], 'comment')


class Ms3dSmoothingGroupPanel(Panel):
    bl_label = ms3d_str['BL_LABEL_PANEL_SMOOTHING_GROUP']
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'

    def preview(self, dict, id, text):
        item = dict.get(id)
        if item is None:
            return "{}".format(text)
        elif item:
            return "{}:".format(text)

        return "{}.".format(text)

    def build_preview(self, context):
        dict = {}
        if (context.mode != 'EDIT_MESH') or (
                not context.tool_settings.mesh_select_mode[2]):
            return dict

        custom_data = context.object.data.ms3d
        blender_mesh = context.object.data
        bm = from_edit_mesh(blender_mesh)
        layer_smoothing_group = bm.faces.layers.int.get(
                ms3d_str['OBJECT_LAYER_SMOOTHING_GROUP'])
        if layer_smoothing_group is not None:
            for bmf in bm.faces:
                item = dict.get(bmf[layer_smoothing_group])
                if item is None:
                    dict[bmf[layer_smoothing_group]] = bmf.select
                else:
                    if not item:
                        dict[bmf[layer_smoothing_group]] = bmf.select
        return dict

    @classmethod
    def poll(cls, context):
        return (context
                and context.object
                and context.object.type in {'MESH', }
                and context.object.data
                and context.object.data.ms3d is not None
                )

    def draw_header(self, context):
        layout = self.layout
        layout.label(icon='PLUGIN')

    def draw(self, context):
        dict = self.build_preview(context)

        custom_data = context.object.data.ms3d
        layout = self.layout

        if True:
            row = layout.row()
            row.enabled = (context.mode == 'EDIT_MESH') and (
                    context.tool_settings.mesh_select_mode[2])
            subrow = row.row()
            subrow.prop(custom_data, 'apply_mode', expand=True)

            col = layout.column(align=True)
            subrow = col.row(align=True)
            subrow.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 1, "1")
                    ).smoothing_group_index = 1
            subrow.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 2, "2")
                    ).smoothing_group_index = 2
            subrow.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 3, "3")
                    ).smoothing_group_index = 3
            subrow.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 4, "4")
                    ).smoothing_group_index = 4
            subrow.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 5, "5")
                    ).smoothing_group_index = 5
            subrow.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 6, "6")
                    ).smoothing_group_index = 6
            subrow.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 7, "7")
                    ).smoothing_group_index = 7
            subrow.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 8, "8")
                    ).smoothing_group_index = 8
            subrow = col.row(align=True)
            subrow.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 9, "9")
                    ).smoothing_group_index = 9
            subrow.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 10, "10")
                    ).smoothing_group_index = 10
            subrow.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 11, "11")
                    ).smoothing_group_index = 11
            subrow.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 12, "12")
                    ).smoothing_group_index = 12
            subrow.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 13, "13")
                    ).smoothing_group_index = 13
            subrow.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 14, "14")
                    ).smoothing_group_index = 14
            subrow.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 15, "15")
                    ).smoothing_group_index = 15
            subrow.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 16, "16")
                    ).smoothing_group_index = 16
            subrow = col.row(align=True)
            subrow.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 17, "17")
                    ).smoothing_group_index = 17
            subrow.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 18, "18")
                    ).smoothing_group_index = 18
            subrow.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 19, "19")
                    ).smoothing_group_index = 19
            subrow.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 20, "20")
                    ).smoothing_group_index = 20
            subrow.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 21, "21")
                    ).smoothing_group_index = 21
            subrow.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 22, "22")
                    ).smoothing_group_index = 22
            subrow.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 23, "23")
                    ).smoothing_group_index = 23
            subrow.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 24, "24")
                    ).smoothing_group_index = 24
            subrow = col.row(align=True)
            subrow.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 25, "25")
                    ).smoothing_group_index = 25
            subrow.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 26, "26")
                    ).smoothing_group_index = 26
            subrow.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 27, "27")
                    ).smoothing_group_index = 27
            subrow.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 28, "28")
                    ).smoothing_group_index = 28
            subrow.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 29, "29")
                    ).smoothing_group_index = 29
            subrow.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 30, "30")
                    ).smoothing_group_index = 30
            subrow.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 31, "31")
                    ).smoothing_group_index = 31
            subrow.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 32, "32")
                    ).smoothing_group_index = 32
            subrow = col.row()
            subrow.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 0, ms3d_str['LABEL_PANEL_BUTTON_NONE'])
                    ).smoothing_group_index = 0
        else:
            col = layout.column()
            #box = col.box()
            col.enabled = (context.mode == 'EDIT_MESH') and (
                    context.tool_settings.mesh_select_mode[2])
            row = col.row()
            row.prop(custom_data, 'apply_mode', expand=True)

            col = col.column(align=True)
            row = col.row(align=True)
            row.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 1, "1")
                    ).smoothing_group_index = 1
            row.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 2, "2")
                    ).smoothing_group_index = 2
            row.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 3, "3")
                    ).smoothing_group_index = 3
            row.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 4, "4")
                    ).smoothing_group_index = 4
            row.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 5, "5")
                    ).smoothing_group_index = 5
            row.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 6, "6")
                    ).smoothing_group_index = 6
            row.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 7, "7")
                    ).smoothing_group_index = 7
            row.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 8, "8")
                    ).smoothing_group_index = 8
            row = col.row(align=True)
            row.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 9, "9")
                    ).smoothing_group_index = 9
            row.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 10, "10")
                    ).smoothing_group_index = 10
            row.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 11, "11")
                    ).smoothing_group_index = 11
            row.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 12, "12")
                    ).smoothing_group_index = 12
            row.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 13, "13")
                    ).smoothing_group_index = 13
            row.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 14, "14")
                    ).smoothing_group_index = 14
            row.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 15, "15")
                    ).smoothing_group_index = 15
            row.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 16, "16")
                    ).smoothing_group_index = 16
            row = col.row(align=True)
            row.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 17, "17")
                    ).smoothing_group_index = 17
            row.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 18, "18")
                    ).smoothing_group_index = 18
            row.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 19, "19")
                    ).smoothing_group_index = 19
            row.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 20, "20")
                    ).smoothing_group_index = 20
            row.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 21, "21")
                    ).smoothing_group_index = 21
            row.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 22, "22")
                    ).smoothing_group_index = 22
            row.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 23, "23")
                    ).smoothing_group_index = 23
            row.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 24, "24")
                    ).smoothing_group_index = 24
            row = col.row(align=True)
            row.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 25, "25")
                    ).smoothing_group_index = 25
            row.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 26, "26")
                    ).smoothing_group_index = 26
            row.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 27, "27")
                    ).smoothing_group_index = 27
            row.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 28, "28")
                    ).smoothing_group_index = 28
            row.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 29, "29")
                    ).smoothing_group_index = 29
            row.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 30, "30")
                    ).smoothing_group_index = 30
            row.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 31, "31")
                    ).smoothing_group_index = 31
            row.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 32, "32")
                    ).smoothing_group_index = 32
            row = col.row()
            row.operator(
                    Ms3dUi.OPT_SMOOTHING_GROUP_APPLY,
                    text=self.preview(dict, 0, ms3d_str['LABEL_PANEL_BUTTON_NONE'])
                    ).smoothing_group_index = 0



###############################################################################
def register():
    register_class(Ms3dGroupProperties)
    register_class(Ms3dModelProperties)
    register_class(Ms3dArmatureProperties)
    register_class(Ms3dJointProperties)
    register_class(Ms3dMaterialProperties)
    inject_properties()
    register_class(Ms3dSetSmoothingGroupOperator)
    register_class(Ms3dGroupOperator)

def unregister():
    unregister_class(Ms3dGroupOperator)
    unregister_class(Ms3dSetSmoothingGroupOperator)
    delete_properties()
    unregister_class(Ms3dMaterialProperties)
    unregister_class(Ms3dJointProperties)
    unregister_class(Ms3dArmatureProperties)
    unregister_class(Ms3dModelProperties)
    unregister_class(Ms3dGroupProperties)

def inject_properties():
    Mesh.ms3d = PointerProperty(type=Ms3dModelProperties)
    Armature.ms3d = PointerProperty(type=Ms3dArmatureProperties)
    Bone.ms3d = PointerProperty(type=Ms3dJointProperties)
    Material.ms3d = PointerProperty(type=Ms3dMaterialProperties)
    Action.ms3d = PointerProperty(type=Ms3dArmatureProperties)
    Group.ms3d = PointerProperty(type=Ms3dGroupProperties)

def delete_properties():
    del Mesh.ms3d
    del Armature.ms3d
    del Bone.ms3d
    del Material.ms3d
    del Action.ms3d
    del Group.ms3d

###############################################################################
register()


###############################################################################
#234567890123456789012345678901234567890123456789012345678901234567890123456789
#--------1---------2---------3---------4---------5---------6---------7---------
# ##### END OF FILE #####
