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

ms3d_str = {
        'lang': "en-US",
        'RUNTIME_KEY': "Human friendly presentation",

        ###############################
        # blender key names
        'OBJECT_LAYER_GROUP': "ms3d_group_layer",
        'OBJECT_LAYER_SMOOTHING_GROUP': "ms3d_smoothing_group_layer",
        'OBJECT_MODIFIER_SMOOTHING_GROUP': "ms3d_smoothing_groups",
        # for some reason after bm.to_mesh(..)
        # the names of 'bm.loops.layers.uv' becomes to 'bm.faces.layers.tex'
        # to bypass this issue, i give both the same name.
        # 'OBJECT_LAYER_TEXTURE': "ms3d_texture_layer",
        'OBJECT_LAYER_TEXTURE': "ms3d_uv_layer",
        'OBJECT_LAYER_UV': "ms3d_uv_layer",

        ###############################
        # strings to be used with 'str().format()'
        'STRING_FORMAT_GROUP': "Group.{:03d}",
        'WARNING_IMPORT_SKIP_FACE_DOUBLE': "skipped face #{}:"\
                " contains double faces with same vertices!",
        'WARNING_IMPORT_SKIP_LESS_VERTICES': "skipped face #{}:"\
                " contains faces too less vertices!",
        'WARNING_IMPORT_SKIP_VERTEX_DOUBLE': "skipped face #{}:"\
                " contains faces with double vertices!",
        'SUMMARY_IMPORT': "elapsed time: {0:.4}s (media io:"\
                " ~{1:.4}s, converter: ~{2:.4}s)",
        'SUMMARY_EXPORT': "elapsed time: {0:.4}s (converter:"\
                " ~{1:.4}s, media io: ~{2:.4}s)",

        ###############################
        'TEXT_OPERATOR': "MilkShape3D MS3D (.ms3d)",
        'FILE_EXT': ".ms3d",
        'FILE_FILTER': "*.ms3d",
        'BL_DESCRIPTION_EXPORTER': "Export to a MS3D file format (.ms3d)",
        'BL_DESCRIPTION_IMPORTER': "Import from a MS3D file format (.ms3d)",
        'BL_LABEL_EXPORTER': "Export MS3D",
        'BL_LABEL_GROUP_OPERATOR': "MS3D - Group Collection Operator",
        'BL_LABEL_IMPORTER': "Import MS3D",
        'BL_LABEL_PANEL_SMOOTHING_GROUP': "MS3D - Smoothing Group",
        'BL_LABEL_SMOOTHING_GROUP_OPERATOR': "MS3D Set Smoothing Group"\
                " Operator",
        'ENUM_ADD_GROUP_1': "Add",
        'ENUM_ADD_GROUP_2': "adds an item",
        'ENUM_ASSIGN_1': "Assign",
        'ENUM_ASSIGN_2_GROUP': "assign selected faces to selected group",
        'ENUM_ASSIGN_2_SMOOTHING_GROUP': "assign all selected faces to"\
                " selected smoothing group",
        'ENUM_DESELECT_1': "Deselect",
        'ENUM_DESELECT_2_GROUP': "deselects faces of selected group",
        'ENUM_DESELECT_2_SMOOTHING_GROUP': "deselects all faces of selected"\
                " smoothing group",
        'ENUM_FLAG_DIRTY_1': "Dirty",
        'ENUM_FLAG_DIRTY_2': "[TODO]",
        'ENUM_FLAG_HIDDEN_1': "Hidden",
        'ENUM_FLAG_HIDDEN_2': "[TODO]",
        'ENUM_FLAG_ISKEY_1': "Is Key",
        'ENUM_FLAG_ISKEY_2': "[TODO]",
        'ENUM_FLAG_MARKED_1': "Marked",
        'ENUM_FLAG_MARKED_2': "[TODO]",
        'ENUM_FLAG_NEWLYCREATED_1': "Newly Created",
        'ENUM_FLAG_NEWLYCREATED_2': "[TODO]",
        'ENUM_FLAG_NONE_1': "None",
        'ENUM_FLAG_NONE_2': "[TODO]",
        'ENUM_FLAG_SELECTED_1': "Selected",
        'ENUM_FLAG_SELECTED_2': "[TODO]",
        'ENUM_FLAG_SELECTED2_1': "Selected Ex.",
        'ENUM_FLAG_SELECTED2_2': "[TODO]",
        'ENUM_REMOVE_1': "Remove",
        'ENUM_REMOVE_2_GROUP': "remove selected faces from selected group",
        'ENUM_REMOVE_GROUP_1': "Remove",
        'ENUM_REMOVE_GROUP_2': "removes an item",
        'ENUM_SELECT_1': "Select",
        'ENUM_SELECT_2_GROUP': "selects faces of selected group",
        'ENUM_SELECT_2_SMOOTHING_GROUP': "selects all faces of selected"\
                " smoothing group",
        'LABEL_NAME_ANIMATION': "Animation Processing:",
        'LABEL_NAME_OBJECT': "World Processing:",
        'LABEL_NAME_OPTIONS': "Advanced Options:",
        'LABEL_NAME_PROCESSING': "Object Processing:",
        'LABEL_PANEL_BUTTON_NONE': "None",
        'LABEL_PANEL_GROUPS': "MS3D - Groups",
        'LABEL_PANEL_JOINTS': "MS3D - Joint",
        'LABEL_PANEL_MATERIALS': "MS3D - Material",
        'LABEL_PANEL_MODEL': "MS3D - Model",
        'PROP_DESC_ALPHA_REF': "ms3d internal raw 'alpha_ref' of Model",
        'PROP_DESC_ALPHAMAP': "ms3d internal raw 'alphamap' file name of"\
                " Material",
        'PROP_DESC_AMBIENT': "ms3d internal raw 'ambient' of Material",
        'PROP_DESC_ANIMATION': "keyframes (rotations, positions)",
        'PROP_DESC_COLOR_JOINT': "ms3d internal raw 'color' of Joint",
        'PROP_DESC_COMMENT_GROUP': "ms3d internal raw 'comment' of Group",
        'PROP_DESC_COMMENT_JOINT': "ms3d internal raw 'comment' of Joint",
        'PROP_DESC_COMMENT_MATERIAL': "ms3d internal raw 'comment' of Material",
        'PROP_DESC_COMMENT_MODEL': "ms3d internal raw 'comment' of Model",
        'PROP_DESC_COORDINATESYSTEM': "Select a coordinate system to export to",
        'PROP_DESC_DIFFUSE': "ms3d internal raw 'diffuse' of Material",
        'PROP_DESC_EMISSIVE': "ms3d internal raw 'emissive' of Material",
        'PROP_DESC_FLAGS_GROUP': "ms3d internal raw 'flags' of Group",
        'PROP_DESC_FLAGS_JOINT': "ms3d internal raw 'flags' of Joint",
        'PROP_DESC_GROUP_NAME': "ms3d internal raw 'name' of Group",
        'PROP_DESC_JOINT_SIZE': "ms3d internal raw 'joint_size' of Model",
        'PROP_DESC_MODE_TEXTURE': "ms3d internal raw 'mode' of Material",
        'PROP_DESC_NAME_ARMATURE': "ms3d internal raw 'name' of Model",
        'PROP_DESC_NAME_JOINT': "ms3d internal raw 'name' of Joint",
        'PROP_DESC_NAME_MATERIAL': "ms3d internal raw 'name' of Material",
        'PROP_DESC_NAME_MODEL': "ms3d internal raw 'name' of Model",
        'PROP_DESC_OBJECTS_EXP': "What to process during export",
        'PROP_DESC_OBJECTS_IMP': "What to process during import",
        'PROP_DESC_SCALE': "Scale all data",
        'PROP_DESC_SELECTED': "Export only selected mesh(es), when enabled",
        'PROP_DESC_SHININESS': "ms3d internal raw 'shininess' of Material",
        'PROP_DESC_SPECULAR': "ms3d internal raw 'specular' of Material",
        'PROP_DESC_TEXTURE': "ms3d internal raw 'texture' file name of"\
                " Material",
        'PROP_DESC_TRANSPARENCY': "ms3d internal raw 'transparency' of"\
                " Material",
        'PROP_DESC_TRANSPARENCY_MODE': "ms3d internal raw 'transparency_mode'"\
                " of Model",
        'PROP_DESC_UNIT_MM': "Setup blender unit to metric [mm]",
        'PROP_DESC_VERBOSE': "Run the converter in debug mode."\
                " Check the console for output (Warning, may be very slow)",
        'PROP_FLAG_TEXTURE_COMBINE_ALPHA_1': "Combine Alpha",
        'PROP_FLAG_TEXTURE_COMBINE_ALPHA_2': "see MilkShape3D documents",
        'PROP_FLAG_TEXTURE_HAS_ALPHA_1': "Has Alpha",
        'PROP_FLAG_TEXTURE_HAS_ALPHA_2': "see MilkShape3D documents",
        'PROP_FLAG_TEXTURE_SPHERE_MAP_1': "Sphere Map",
        'PROP_FLAG_TEXTURE_SPHERE_MAP_2': "see MilkShape3D documents",
        'PROP_ITEM_COORDINATESYSTEM_1_BY_1_1': "xyz -> xyz (1:1)",
        'PROP_ITEM_COORDINATESYSTEM_1_BY_1_2': "Take axis as is (1:1)",
        'PROP_ITEM_COORDINATESYSTEM_EXP_1': "xyz -> yzx (export)",
        'PROP_ITEM_COORDINATESYSTEM_EXP_2': "swap axis to fit to viewport"\
                " (export blender to ms3d)",
        'PROP_ITEM_COORDINATESYSTEM_IMP_1': "yzx -> xyz (import)",
        'PROP_ITEM_COORDINATESYSTEM_IMP_2': "swap axis to fit to viewport"\
                " (import ms3d to blender)",
        'PROP_ITEM_OBJECT_ANIMATION_1': "Animation **)",
        'PROP_ITEM_OBJECT_ANIMATION_2': "keyframes",
        'PROP_ITEM_OBJECT_GROUP_1': "Group",
        'PROP_ITEM_OBJECT_GROUP_2': "organize all file objects to a single"\
                " group, named with the filename",
        'PROP_ITEM_OBJECT_JOINT_1': "Joints",
        'PROP_ITEM_OBJECT_JOINT_2': "joints, bones",
        'PROP_ITEM_OBJECT_MATERIAL_1': "Materials",
        'PROP_ITEM_OBJECT_MATERIAL_2': "ambient, diffuse, specular, emissive,"\
                " shininess, transparency, diffuse texture, alpha texture",
        'PROP_ITEM_OBJECT_MESH_1': "Meshes",
        'PROP_ITEM_OBJECT_MESH_2': "vertices, triangles, uv",
        'PROP_ITEM_OBJECT_SMOOTHGROUPS_1': "Smoothing Groups",
        'PROP_ITEM_OBJECT_SMOOTHGROUPS_2': "split mesh faces according its"\
                " smoothing groups",
        'PROP_MODE_TRANSPARENCY_DEPTH_BUFFERED_WITH_ALPHA_REF_1': "Depth"\
                " Buffered with Alpha Ref",
        'PROP_MODE_TRANSPARENCY_DEPTH_BUFFERED_WITH_ALPHA_REF_2': "see"\
                " MilkShape3D document",
        'PROP_MODE_TRANSPARENCY_DEPTH_SORTED_TRIANGLES_1': "Depth Sorted"\
                " Triangles",
        'PROP_MODE_TRANSPARENCY_DEPTH_SORTED_TRIANGLES_2': "see MilkShape3D"\
                " document",
        'PROP_MODE_TRANSPARENCY_SIMPLE_1': "Simple",
        'PROP_MODE_TRANSPARENCY_SIMPLE_2': "see MilkShape3D document",
        'PROP_NAME_ALPHA_REF': "Alpha Ref.",
        'PROP_NAME_ALPHAMAP': "Alphamap",
        'PROP_NAME_AMBIENT': "Ambient",
        'PROP_NAME_ANIMATION': "Animation **)",
        'PROP_NAME_COLOR': "Color",
        'PROP_NAME_COMMENT': "Comment",
        'PROP_NAME_COORDINATESYSTEM': "Coordinate system",
        'PROP_NAME_DIFFUSE': "Diffuse",
        'PROP_NAME_EMISSIVE': "Emissive",
        'PROP_NAME_FLAGS': "Flags",
        'PROP_NAME_JOINT_SIZE': "Joint Size",
        'PROP_NAME_MODE': "Mode",
        'PROP_NAME_NAME': "Name",
        'PROP_NAME_OBJECTS_EXP': "Export processing",
        'PROP_NAME_OBJECTS_IMP': "Import processing",
        'PROP_NAME_SCALE': "Scale",
        'PROP_NAME_SELECTED': "Only selected mesh(es)",
        'PROP_NAME_SHININESS': "Shininess",
        'PROP_NAME_SPECULAR': "Specular",
        'PROP_NAME_TEXTURE': "Texture",
        'PROP_NAME_TRANSPARENCY': "Transparency",
        'PROP_NAME_TRANSPARENCY_MODE': "Transp. Mode",
        'PROP_NAME_UNIT_MM': "Metric [mm]",
        'PROP_NAME_VERBOSE': "Verbose",
        'PROP_SMOOTHING_GROUP_INDEX': "Smoothing group id",
        'REMARKS_1': "*)   partial implemented yet",
        'REMARKS_2': "**) not implemented yet",
        'REMARKS_3': "***) risk of unwanted results",
        'PROP_NAME_APPLY_MODIFIER': "Apply Modifier",
        'PROP_DESC_APPLY_MODIFIER': "applies modifier before process",
        'PROP_NAME_APPLY_MODIFIER_MODE': "Mode",
        'PROP_DESC_APPLY_MODIFIER_MODE': "apply mode, if applicable",
        'PROP_ITEM_APPLY_MODIFIER_MODE_PREVIEW_1': "Preview",
        'PROP_ITEM_APPLY_MODIFIER_MODE_PREVIEW_2': "takes the 'preview' settings of modifier, if applicable",
        'PROP_ITEM_APPLY_MODIFIER_MODE_RENDER_1': "Render",
        'PROP_ITEM_APPLY_MODIFIER_MODE_RENDER_2': "takes the 'render' settings of modifier, if applicable",

        'PROP_NAME_': "Name",
        'PROP_DESC_': "Description",
        # ms3d_str['']
        }


###############################################################################
#234567890123456789012345678901234567890123456789012345678901234567890123456789
#--------1---------2---------3---------4---------5---------6---------7---------
# ##### END OF FILE #####
