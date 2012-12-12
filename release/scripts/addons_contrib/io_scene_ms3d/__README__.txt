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


files:
__README__.txt
__init__.py
ms3d_export.py
ms3d_import.py
ms3d_spec.py
ms3d_utils.py
ms3d_ui.py
ms3d_strings.py


description:
__README__.txt      : this file
                    § Blender maintenance

__init__.py         : entry point for blender plugins
                      initialize and registers/unregisters plugin functions
                    § Blender maintenance

ms3d_export.py      : entry point for exporter
                      functions to bring Blender content in a correct way to
                      MilkShape
                    § Blender -> MilkShape3D maintenance

ms3d_import.py      : entry point for importer
                      functions to bring MilkShape content in a correct way to
                      Blender
                    § MilkShape3D -> Blender maintenance

ms3d_spec.py        : objects and structures that specified a MilkShape3D file
                      base functions to write/read its objects itself
                    § MilkShape maintenance

ms3d_ui.py          : additional custom properties for Blender objects
                      give user access to MilkShape specific properties
                    § Blender maintenance

ms3d_strings.py     : most of the strings used in the addon to have a
                      central point for optional internationalization


known issues:
  importer issues:
    -/-

  exporter issues:
    - does only export active mesh object
    - does only export the first existing UV texture coordinates,
            if more than one UV texture is used per mesh


todo / nice to have:
    - export options to ms3d joints/animation/extra parts optional


###############################################################################
    exporter:
        Ms3dModel
            .vertices
                Ms3dVertex
                    .vertex: 100%
                    .bone_id: 100%
                    .reference_count: 100%
                    .flags: 0%
                    .vertex_ex
                        Ms3dVertexEx
                            .bone_ids: 100%
                            .weights: 100%
                            .extra: 100% (not exposed to UI)
            .triangles
                Ms3dTriangle
                    .vertex_indices: 100%
                    .s: 100%
                    .t: 100%
                    .group_index: 100%
                    .smoothing_group: 100%
                    .flags: 0%
                    .vertex_normals: 100%
            .groups
                Ms3dGroup
                    .name: 100%
                    .triangle_indices: 100%
                    .material_index: 100%
                    .comment: 100%
                    .flags: 100%
            .materials
                Ms3dMaterial
                    name: 100%
                    ambient: 100%
                    diffuse: 100%
                    specular: 100%
                    emissive: 100%
                    shininess: 100%
                    transparency: 100%
                    mode: 100%
                    texture: 100%
                    alphamap: 100%
                    comment: 100%
            .comment: 100%
            .model_ex
                Ms3dModelEx
                    .joint_size: 100%
                    .transparency_mode: 100%
                    .alpha_ref: 100%
            .joints
                Ms3dJoint
                    .name: 100%
                    .parent_name: 100%
                    .rotation: 100%
                    .position: 100%
                    .rotation_keyframes: 100%
                    .translation_keyframes: 100%
                    .joint_ex
                        Ms3DJointEx
                            .color: 100%
                    .comment: 100%
###############################################################################
    importer:
        Ms3dModel
            .vertices
                Ms3dVertex
                    .vertex: 100%
                    .bone_id: 100%
                    .reference_count: 0%
                    .flags: 0%
                    .vertex_ex
                        Ms3dVertexEx
                            .bone_ids: 100%
                            .weights: 100%
                            .extra: 100% (not exposed to UI)
            .triangles
                Ms3dTriangle
                    .vertex_indices: 100%
                    .s: 100%
                    .t: 100%
                    .group_index: 100%
                    .smoothing_group: 100%
                    .flags: 0%
                    .vertex_normals: 0%
            .groups
                Ms3dGroup
                    .name: 100%
                    .triangle_indices: 100%
                    .material_index: 100%
                    .comment: 100%
                    .flags: 100%
            .materials
                Ms3dMaterial
                    name: 100%
                    ambient: 100%
                    diffuse: 100%
                    specular: 100%
                    emissive: 100%
                    shininess: 100%
                    transparency: 100%
                    mode: 100%
                    texture: 100%
                    alphamap: 100%
                    comment: 100%
            .comment: 100%
            .model_ex
                Ms3dModelEx
                    .joint_size: 100%
                    .transparency_mode: 100%
                    .alpha_ref: 100%
            .joints
                Ms3dJoint
                    .name: 100%
                    .parent_name: 100%
                    .rotation: 100%
                    .position: 100%
                    .rotation_keyframes: 100%
                    .translation_keyframes: 100%
                    .joint_ex
                        Ms3DJointEx
                            .color: 100%
                    .comment: 100%
###############################################################################
