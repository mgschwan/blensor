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
import io
from math import (
        radians,
        )
from mathutils import (
        Vector,
        Euler,
        Matrix,
        )
from os import (
        path,
        )
from sys import (
        exc_info,
        float_info,
        )
from time import (
        time,
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
    if 'io_scene_ms3d.ms3d_ui' in locals():
        imp.reload(io_scene_ms3d.ms3d_ui)
    pass
else:
    from io_scene_ms3d.ms3d_strings import (
            ms3d_str,
            )
    from io_scene_ms3d.ms3d_spec import (
            Ms3dSpec,
            Ms3dModel,
            )
    from io_scene_ms3d.ms3d_utils import (
            select_all,
            enable_pose_mode,
            enable_edit_mode,
            pre_setup_environment,
            post_setup_environment,
            )
    from io_scene_ms3d.ms3d_ui import (
            Ms3dUi,
            )
    pass


#import blender stuff
from bpy import (
        data,
        ops,
        )
import bmesh
from bpy_extras.image_utils import (
        load_image,
        )


###############################################################################
class Ms3dImporter():
    """ Load a MilkShape3D MS3D File """
    def __init__(self, options):
        self.options = options
        pass

    ###########################################################################
    # create empty blender ms3d_model
    # read ms3d file
    # fill blender with ms3d_model content
    def read(self, blender_context):
        """ read ms3d file and convert ms3d content to bender content """

        t1 = time()
        t2 = None
        self.has_textures = False

        try:
            # setup environment
            pre_setup_environment(self, blender_context)

            # create an empty ms3d template
            ms3d_model = Ms3dModel(self.filepath_splitted[1])

            self.file = None
            try:
                # open ms3d file
                self.file = io.FileIO(self.options.filepath, 'rb')

                # read and inject ms3d data from disk to internal structure
                ms3d_model.read(self.file)
            finally:
                # close ms3d file
                if self.file is not None:
                    self.file.close()

            # if option is set, this time will enlargs the io time
            if self.options.prop_verbose:
                ms3d_model.print_internal()

            t2 = time()

            is_valid, statistics = ms3d_model.is_valid()

            if is_valid:
                # inject ms3d data to blender
                self.to_blender(blender_context, ms3d_model)

                blender_scene = blender_context.scene

                # finalize/restore environment
                if self.options.prop_unit_mm:
                    # set metrics
                    blender_scene.unit_settings.system = 'METRIC'
                    blender_scene.unit_settings.system_rotation = 'DEGREES'
                    blender_scene.unit_settings.scale_length = 0.001 #1.0mm
                    blender_scene.unit_settings.use_separate = False
                    blender_context.tool_settings.normal_size = 1.0 # 1.0mm


                    # set all 3D views to texture shaded
                    # and set up the clipping
                    if self.has_textures:
                        viewport_shade = 'TEXTURED'
                    else:
                        viewport_shade = 'SOLID'

                    for screen in blender_context.blend_data.screens:
                        for area in screen.areas:
                            if (area.type != 'VIEW_3D'):
                                continue

                            for space in area.spaces:
                                if (space.type != 'VIEW_3D'):
                                    continue

                                space.viewport_shade = viewport_shade
                                #screen.scene.game_settings.material_mode \
                                #        = 'MULTITEXTURE'
                                #space.show_textured_solid = True
                                space.clip_start = 0.1 # 0.1mm
                                space.clip_end = 1000000.0 # 1km

                blender_scene.update()

                post_setup_environment(self, blender_context)

            print()
            print("##########################################################")
            print("MS3D -> Blender : [{0}]".format(self.filepath_splitted[1]))
            print(statistics)
            print("##########################################################")

        except Exception:
            type, value, traceback = exc_info()
            print("read - exception in try block\n  type: '{0}'\n"
                    "  value: '{1}'".format(type, value, traceback))

            if t2 is None:
                t2 = time()

            raise

        else:
            pass

        t3 = time()
        print(ms3d_str['SUMMARY_IMPORT'].format(
                (t3 - t1), (t2 - t1), (t3 - t2)))

        return {"FINISHED"}


    ###########################################################################
    def to_blender(self, blender_context, ms3d_model):
        blender_mesh_object = self.create_geometry(blender_context, ms3d_model)
        blender_armature_object = self.create_animation(blender_context, ms3d_model, blender_mesh_object)

        self.organize_objects(blender_context, ms3d_model, [blender_mesh_object, blender_armature_object])


    ###########################################################################
    def organize_objects(self, blender_context, ms3d_model, blender_objects):
        ##########################
        # blender_armature_object to blender_mesh_object
        # that has bad side effects to the armature
        # and causes cyclic dependecies
        ###blender_armature_object.parent = blender_mesh_object
        ###blender_mesh_object.parent = blender_armature_object

        blender_scene = blender_context.scene

        blender_group = blender_context.blend_data.groups.new(ms3d_model.name + ".g")
        blender_empty_object = blender_context.blend_data.objects.new(ms3d_model.name + ".e", None)
        blender_empty_object.location = blender_scene.cursor_location
        blender_scene.objects.link(blender_empty_object)
        blender_group.objects.link(blender_empty_object)

        for blender_object in blender_objects:
            if blender_object is not None:
                blender_group.objects.link(blender_object)
                blender_object.parent = blender_empty_object


    ###########################################################################
    def create_geometry(self, blender_context, ms3d_model):
        ##########################
        # blender stuff:
        # create a blender Mesh
        blender_mesh = blender_context.blend_data.meshes.new(ms3d_model.name + ".m")
        blender_mesh.ms3d.name = ms3d_model.name
        ms3d_comment = ms3d_model.comment_object
        if ms3d_comment is not None:
            blender_mesh.ms3d.comment = ms3d_comment.comment
        ms3d_model_ex = ms3d_model.model_ex_object
        if ms3d_model_ex is not None:
            blender_mesh.ms3d.joint_size = ms3d_model_ex.joint_size
            blender_mesh.ms3d.alpha_ref = ms3d_model_ex.alpha_ref
            blender_mesh.ms3d.transparency_mode \
                    = Ms3dUi.transparency_mode_from_ms3d(
                            ms3d_model_ex.transparency_mode)

        ##########################
        # blender stuff:
        # link to blender object
        blender_mesh_object = blender_context.blend_data.objects.new(
                ms3d_model.name + ".m", blender_mesh)

        ##########################
        # blender stuff:
        # create edge split modifire, to make sharp edges visible
        blender_modifier = blender_mesh_object.modifiers.new(
                "ms3d_smoothing_groups", type='EDGE_SPLIT')
        blender_modifier.show_expanded = False
        blender_modifier.use_edge_angle = False
        blender_modifier.use_edge_sharp = True

        ##########################
        # blender stuff:
        # link to blender scene
        blender_scene = blender_context.scene
        blender_scene.objects.link(blender_mesh_object)
        blender_mesh_object.location = blender_scene.cursor_location
        enable_edit_mode(False)
        select_all(False)
        blender_mesh_object.select = True
        blender_scene.objects.active = blender_mesh_object

        ##########################
        # blender stuff:
        # create all (ms3d) groups
        ms3d_to_blender_group_index = {}
        blender_group_manager = blender_mesh.ms3d
        for ms3d_group_index, ms3d_group in enumerate(ms3d_model.groups):
            blender_group = blender_group_manager.create_group()
            blender_group.name = ms3d_group.name
            blender_group.flags = Ms3dUi.flags_from_ms3d(ms3d_group.flags)
            blender_group.material_index = ms3d_group.material_index

            ms3d_comment = ms3d_group.comment_object
            if ms3d_comment is not None:
                blender_group.comment = ms3d_comment.comment

            # translation dictionary
            ms3d_to_blender_group_index[ms3d_group_index] = blender_group.id

        ####################################################
        # begin BMesh stuff
        #

        ##########################
        # BMesh stuff:
        # create an empty BMesh
        bm = bmesh.new()

        ##########################
        # BMesh stuff:
        # create new Layers for custom data per "mesh face"
        layer_texture = bm.faces.layers.tex.get(
                ms3d_str['OBJECT_LAYER_TEXTURE'])
        if layer_texture is None:
            layer_texture = bm.faces.layers.tex.new(
                    ms3d_str['OBJECT_LAYER_TEXTURE'])

        layer_smoothing_group = bm.faces.layers.int.get(
                ms3d_str['OBJECT_LAYER_SMOOTHING_GROUP'])
        if layer_smoothing_group is None:
            layer_smoothing_group = bm.faces.layers.int.new(
                    ms3d_str['OBJECT_LAYER_SMOOTHING_GROUP'])

        layer_group = bm.faces.layers.int.get(
                ms3d_str['OBJECT_LAYER_GROUP'])
        if layer_group is None:
            layer_group = bm.faces.layers.int.new(
                    ms3d_str['OBJECT_LAYER_GROUP'])

        ##########################
        # BMesh stuff:
        # create new Layers for custom data per "face vertex"
        layer_uv = bm.loops.layers.uv.get(ms3d_str['OBJECT_LAYER_UV'])
        if layer_uv is None:
            layer_uv = bm.loops.layers.uv.new(ms3d_str['OBJECT_LAYER_UV'])

        ##########################
        # BMesh stuff:
        # create all vertices
        for ms3d_vertex_index, ms3d_vertex in enumerate(ms3d_model.vertices):
            bmv = bm.verts.new(
                    self.matrix_scaled_coordination_system
                    * Vector(ms3d_vertex.vertex))

        ##########################
        # blender stuff (uses BMesh stuff):
        # create all materials / image textures
        ms3d_to_blender_material = {}
        for ms3d_material_index, ms3d_material in enumerate(
                ms3d_model.materials):
            blender_material = blender_context.blend_data.materials.new(ms3d_material.name)

            # custom datas
            blender_material.ms3d.name = ms3d_material.name
            blender_material.ms3d.ambient = ms3d_material.ambient
            blender_material.ms3d.diffuse = ms3d_material.diffuse
            blender_material.ms3d.specular = ms3d_material.specular
            blender_material.ms3d.emissive = ms3d_material.emissive
            blender_material.ms3d.shininess = ms3d_material.shininess
            blender_material.ms3d.transparency = ms3d_material.transparency
            blender_material.ms3d.mode = Ms3dUi.texture_mode_from_ms3d(
                    ms3d_material.mode)

            if ms3d_material.texture:
                blender_material.ms3d.texture = ms3d_material.texture
                self.has_textures = True

            if ms3d_material.alphamap:
                blender_material.ms3d.alphamap = ms3d_material.alphamap

            ms3d_comment = ms3d_material.comment_object
            if ms3d_comment is not None:
                blender_material.ms3d.comment = ms3d_comment.comment

            # blender datas
            blender_material.ambient = ((
                    (ms3d_material.ambient[0]
                    + ms3d_material.ambient[1]
                    + ms3d_material.ambient[2]) / 3.0)
                    * ms3d_material.ambient[3])

            blender_material.diffuse_color[0] = ms3d_material.diffuse[0]
            blender_material.diffuse_color[1] = ms3d_material.diffuse[1]
            blender_material.diffuse_color[2] = ms3d_material.diffuse[2]
            blender_material.diffuse_intensity = ms3d_material.diffuse[3]

            blender_material.specular_color[0] = ms3d_material.specular[0]
            blender_material.specular_color[1] = ms3d_material.specular[1]
            blender_material.specular_color[2] = ms3d_material.specular[2]
            blender_material.specular_intensity = ms3d_material.specular[3]

            blender_material.emit = ((
                    (ms3d_material.emissive[0]
                    + ms3d_material.emissive[1]
                    + ms3d_material.emissive[2]) / 3.0)
                    * ms3d_material.emissive[3])

            blender_material.specular_hardness = ms3d_material.shininess * 2.0

            if (ms3d_material.transparency):
                blender_material.use_transparency = True
                blender_material.alpha = ms3d_material.transparency
                blender_material.specular_alpha = blender_material.alpha

            if (blender_material.game_settings):
                blender_material.game_settings.use_backface_culling = False
                blender_material.game_settings.alpha_blend = 'ALPHA'

            # diffuse texture
            if ms3d_material.texture:
                dir_name_diffuse = self.filepath_splitted[0]
                file_name_diffuse = path.split(ms3d_material.texture)[1]
                blender_image_diffuse = load_image(
                        file_name_diffuse, dir_name_diffuse)
                blender_texture_diffuse = blender_context.blend_data.textures.new(
                        name=file_name_diffuse, type='IMAGE')
                blender_texture_diffuse.image = blender_image_diffuse
                blender_texture_slot_diffuse \
                        = blender_material.texture_slots.add()
                blender_texture_slot_diffuse.texture = blender_texture_diffuse
                blender_texture_slot_diffuse.texture_coords = 'UV'
                blender_texture_slot_diffuse.uv_layer = layer_uv.name
                blender_texture_slot_diffuse.use_map_color_diffuse = True
                blender_texture_slot_diffuse.use_map_alpha = False
            else:
                blender_image_diffuse = None

            # alpha texture
            if ms3d_material.alphamap:
                dir_name_alpha = self.filepath_splitted[0]
                file_name_alpha = path.split(ms3d_material.alphamap)[1]
                blender_image_alpha = load_image(
                        file_name_alpha, dir_name_alpha)
                blender_texture_alpha = blender_context.blend_data.textures.new(
                        name=file_name_alpha, type='IMAGE')
                blender_texture_alpha.image = blender_image_alpha
                blender_texture_slot_alpha \
                        = blender_material.texture_slots.add()
                blender_texture_slot_alpha.texture = blender_texture_alpha
                blender_texture_slot_alpha.texture_coords = 'UV'
                blender_texture_slot_alpha.uv_layer = layer_uv.name
                blender_texture_slot_alpha.use_map_color_diffuse = False
                blender_texture_slot_alpha.use_map_alpha = True
                blender_texture_slot_alpha.use_rgb_to_intensity = True
                blender_material.alpha = 0
                blender_material.specular_alpha = 0

            # append blender material to blender mesh, to be linked to
            blender_mesh.materials.append(blender_material)

            # translation dictionary
            ms3d_to_blender_material[ms3d_material_index] \
                    = blender_image_diffuse

        ##########################
        # BMesh stuff:
        # create all triangles
        smoothing_group_blender_faces = {}
        for ms3d_triangle_index, ms3d_triangle in enumerate(
                ms3d_model.triangles):
            bmv_list = []
            for vert_index in ms3d_triangle.vertex_indices:
                bmv = bm.verts[vert_index]
                if [[x] for x in bmv_list if x == bmv]:
                    self.options.report(
                            {'WARNING', 'INFO'},
                            ms3d_str['WARNING_IMPORT_SKIP_VERTEX_DOUBLE'].format(
                                    ms3d_triangle_index))
                    continue
                bmv_list.append(bmv)

            if len(bmv_list) < 3:
                self.options.report(
                        {'WARNING', 'INFO'},
                        ms3d_str['WARNING_IMPORT_SKIP_LESS_VERTICES'].format(
                                ms3d_triangle_index))
                continue
            bmf = bm.faces.get(bmv_list)
            if bmf is not None:
                self.options.report(
                        {'WARNING', 'INFO'},
                        ms3d_str['WARNING_IMPORT_SKIP_FACE_DOUBLE'].format(
                                ms3d_triangle_index))
                continue

            bmf = bm.faces.new(bmv_list)

            # blender uv custom data per "face vertex"
            bmf.loops[0][layer_uv].uv = Vector(
                    (ms3d_triangle.s[0], 1.0 - ms3d_triangle.t[0]))
            bmf.loops[1][layer_uv].uv = Vector(
                    (ms3d_triangle.s[1], 1.0 - ms3d_triangle.t[1]))
            bmf.loops[2][layer_uv].uv = Vector(
                    (ms3d_triangle.s[2], 1.0 - ms3d_triangle.t[2]))

            # ms3d custom data per "mesh face"
            bmf[layer_smoothing_group] = ms3d_triangle.smoothing_group

            blender_group_id = ms3d_to_blender_group_index.get(
                    ms3d_triangle.group_index)
            if blender_group_id is not None:
                bmf[layer_group] = blender_group_id

            if ms3d_triangle.group_index >= 0 \
                    and ms3d_triangle.group_index < len(ms3d_model.groups):
                ms3d_material_index \
                        = ms3d_model.groups[ms3d_triangle.group_index].material_index
                if ms3d_material_index != Ms3dSpec.NONE_GROUP_MATERIAL_INDEX:
                    # BMFace.material_index expects...
                    # index of material in types.Mesh.materials,
                    # not index of material in blender_context.blend_data.materials!
                    bmf.material_index = ms3d_material_index

                    # apply diffuse texture image to face, to be visible in 3d view
                    bmf[layer_texture].image = ms3d_to_blender_material.get(
                            ms3d_material_index)
                else:
                    # set material index to highes possible index
                    # - in most cases there is no maretial assigned ;)
                    bmf.material_index = 32766
                    pass

            # helper dictionary for post-processing smoothing_groups
            smoothing_group_blender_face = smoothing_group_blender_faces.get(
                    ms3d_triangle.smoothing_group)
            if smoothing_group_blender_face is None:
                smoothing_group_blender_face = []
                smoothing_group_blender_faces[ms3d_triangle.smoothing_group] \
                        = smoothing_group_blender_face
            smoothing_group_blender_face.append(bmf)

        ##########################
        # BMesh stuff:
        # create all sharp edges for blender to make smoothing_groups visible
        for ms3d_smoothing_group_index, blender_face_list \
                in smoothing_group_blender_faces.items():
            edge_dict = {}
            for bmf in blender_face_list:
                bmf.smooth = True
                for bme in bmf.edges:
                    if edge_dict.get(bme) is None:
                        edge_dict[bme] = 0
                    else:
                        edge_dict[bme] += 1
                    bme.seam = (edge_dict[bme] == 0)
                    bme.smooth = (edge_dict[bme] != 0)

        ##########################
        # BMesh stuff:
        # finally tranfer BMesh to Mesh
        bm.to_mesh(blender_mesh)
        bm.free()


        #
        # end BMesh stuff
        ####################################################

        return blender_mesh_object

    ###########################################################################
    def create_animation(self, blender_context, ms3d_model, blender_mesh_object):
        ##########################
        # setup scene
        blender_scene = blender_context.scene
        blender_scene.render.fps = ms3d_model.animation_fps
        if ms3d_model.animation_fps:
            blender_scene.render.fps_base = (blender_scene.render.fps /
                    ms3d_model.animation_fps)

        blender_scene.frame_start = 1
        blender_scene.frame_end = (ms3d_model.number_total_frames
                + blender_scene.frame_start) - 1
        blender_scene.frame_current = (ms3d_model.current_time
                * ms3d_model.animation_fps)

        ##########################
        if not ms3d_model.joints:
            return

        ##########################
        ms3d_armature_name = ms3d_model.name + ".a"
        ms3d_action_name = ms3d_model.name + ".act"

        ##########################
        # create new blender_armature_object
        blender_armature = blender_context.blend_data.armatures.new(ms3d_armature_name)
        blender_armature.ms3d.name = ms3d_model.name
        blender_armature.draw_type = 'STICK'
        blender_armature.show_axes = True
        blender_armature.use_auto_ik = True
        blender_armature_object = blender_context.blend_data.objects.new(
                ms3d_armature_name, blender_armature)
        blender_scene.objects.link(blender_armature_object)
        blender_armature_object.location = blender_scene.cursor_location
        blender_armature_object.show_x_ray = True

        ##########################
        # prepare for vertex groups
        ms3d_to_blender_vertex_groups = {}
        for ms3d_vertex_index, ms3d_vertex in enumerate(ms3d_model.vertices):
            # prepare for later use for blender vertex group
            if ms3d_vertex.bone_id != Ms3dSpec.NONE_VERTEX_BONE_ID:
                blender_vertex_group = ms3d_to_blender_vertex_groups.get(
                        ms3d_vertex.bone_id)
                if blender_vertex_group is None:
                    ms3d_to_blender_vertex_groups[ms3d_vertex.bone_id] \
                            = blender_vertex_group = []
                blender_vertex_group.append(ms3d_vertex_index)

        ##########################
        # blender stuff:
        # create all vertex groups to be used for bones
        for ms3d_bone_id, blender_vertex_index_list \
                in ms3d_to_blender_vertex_groups.items():
            ms3d_name = ms3d_model.joints[ms3d_bone_id].name
            blender_vertex_group = blender_mesh_object.vertex_groups.new(
                    ms3d_name)
            blender_vertex_group.add(blender_vertex_index_list, 1.0, 'REPLACE')

        blender_modifier = blender_mesh_object.modifiers.new(
                ms3d_armature_name, type='ARMATURE')
        blender_modifier.show_expanded = False
        blender_modifier.use_vertex_groups = True
        blender_modifier.use_bone_envelopes = False
        blender_modifier.object = blender_armature_object

        ##########################
        # prepare joint data for later use
        ms3d_joint_by_name = {}
        for ms3d_joint in ms3d_model.joints:
            item = ms3d_joint_by_name.get(ms3d_joint.name)
            if item is None:
                ms3d_joint.__children = []
                ms3d_joint.__matrix_local = Matrix()
                ms3d_joint.__matrix_global = Matrix()
                ms3d_joint_by_name[ms3d_joint.name] = ms3d_joint

            matrix_local = (Matrix.Rotation(ms3d_joint.rotation[2], 4, 'Z')
                    * Matrix.Rotation(ms3d_joint.rotation[1], 4, 'Y')
                    ) * Matrix.Rotation(ms3d_joint.rotation[0], 4, 'X')
            matrix_local = Matrix.Translation(Vector(ms3d_joint.position)
                    ) * matrix_local

            ms3d_joint.__matrix_local = matrix_local
            ms3d_joint.__matrix_global = matrix_local

            if ms3d_joint.parent_name:
                ms3d_joint_parent = ms3d_joint_by_name.get(
                        ms3d_joint.parent_name)
                if ms3d_joint_parent is not None:
                    ms3d_joint_parent.__children.append(ms3d_joint)

                    matrix_global = ms3d_joint_parent.__matrix_global \
                            * matrix_local
                    ms3d_joint.__matrix_global = matrix_global

        ##########################
        # ms3d_joint to blender_edit_bone
        blender_scene.objects.active = blender_armature_object
        enable_edit_mode(True)
        for ms3d_joint in ms3d_model.joints:
            blender_edit_bone = blender_armature.edit_bones.new(ms3d_joint.name)
            blender_edit_bone.use_connect = False
            blender_edit_bone.use_inherit_rotation = True
            blender_edit_bone.use_inherit_scale = True
            blender_edit_bone.use_local_location = True
            blender_armature.edit_bones.active = blender_edit_bone

            ms3d_joint = ms3d_joint_by_name[ms3d_joint.name]
            ms3d_joint_vector = ms3d_joint.__matrix_global * Vector()

            blender_edit_bone.head \
                    = self.matrix_scaled_coordination_system \
                    * ms3d_joint_vector

            number_children = len(ms3d_joint.__children)
            if number_children > 0:
                vector_midpoint = Vector()
                for item_child in ms3d_joint.__children:
                    ms3d_joint_child_vector \
                            = ms3d_joint_by_name[item_child.name].__matrix_global \
                            * Vector()
                    vector_midpoint += ms3d_joint_child_vector \
                            - ms3d_joint_vector
                vector_midpoint /= number_children
                vector_midpoint.normalize()
                blender_edit_bone.tail = blender_edit_bone.head \
                        + self.matrix_scaled_coordination_system \
                        * vector_midpoint
            else:
                vector_tail_end = Vector()
                if ms3d_joint.parent_name:
                    ms3d_joint_parent_vector \
                            = ms3d_joint_by_name[ms3d_joint.parent_name].__matrix_global \
                            * Vector()
                    vector_tail_end = ms3d_joint_vector \
                            - ms3d_joint_parent_vector
                else:
                    #dummy tail
                    vector_tail_end = ms3d_joint.__matrix_global * Vector()
                vector_tail_end.normalize()
                blender_edit_bone.tail = blender_edit_bone.head \
                        + self.matrix_scaled_coordination_system * vector_tail_end

            if ms3d_joint.parent_name:
                ms3d_joint_parent = ms3d_joint_by_name[ms3d_joint.parent_name]
                blender_edit_bone_parent = ms3d_joint_parent.blender_edit_bone
                blender_edit_bone.parent = blender_edit_bone_parent

            ms3d_joint.blender_bone_name = blender_edit_bone.name
            ms3d_joint.blender_edit_bone = blender_edit_bone
        enable_edit_mode(False)

        ##########################
        # post process bones
        enable_edit_mode(True)
        select_all(True)
        if ops.armature.calculate_roll.poll():
            ops.armature.calculate_roll(type='Y')
        select_all(False)
        enable_edit_mode(False)

        ##########################
        # post process bones
        enable_edit_mode(False)
        for ms3d_joint_name, ms3d_joint in ms3d_joint_by_name.items():
            blender_bone = blender_armature.bones.get(
                    ms3d_joint.blender_bone_name)
            if blender_bone is None:
                continue

            blender_bone.ms3d.name = ms3d_joint.name
            blender_bone.ms3d.flags = Ms3dUi.flags_from_ms3d(ms3d_joint.flags)

            ms3d_joint_ex = ms3d_joint.joint_ex_object
            if ms3d_joint_ex is not None:
                blender_bone.ms3d.color = ms3d_joint_ex.color

            ms3d_comment = ms3d_joint.comment_object
            if ms3d_comment is not None:
                blender_bone.ms3d.comment = ms3d_comment.comment

        ##########################
        if not self.options.prop_animation:
            return blender_armature_object


        ##########################
        # process pose bones
        enable_pose_mode(True)

        blender_action = blender_context.blend_data.actions.new(ms3d_action_name)
        if blender_armature_object.animation_data is None:
            blender_armature_object.animation_data_create()
        blender_armature_object.animation_data.action = blender_action

        ##########################
        # this part is not correct implemented !
        # currently i have absolute no idea how to fix.
        # maybe somebody else can fix it.
        for ms3d_joint_name, ms3d_joint  in ms3d_joint_by_name.items():
            blender_pose_bone = blender_armature_object.pose.bones.get(
                    ms3d_joint.blender_bone_name)
            if blender_pose_bone is None:
                continue
            ms3d_joint_local_matrix = ms3d_joint.__matrix_local
            ms3d_joint_global_matrix = ms3d_joint.__matrix_global

            data_path = blender_pose_bone.path_from_id('location')
            fcurve_location_x = blender_action.fcurves.new(data_path, index=0)
            fcurve_location_y = blender_action.fcurves.new(data_path, index=1)
            fcurve_location_z = blender_action.fcurves.new(data_path, index=2)
            for translation_key_frames in ms3d_joint.translation_key_frames:
                frame = (translation_key_frames.time * ms3d_model.animation_fps)
                matrix_local = Matrix.Translation(
                        Vector(translation_key_frames.position))
                v = (matrix_local) * Vector()
                fcurve_location_x.keyframe_points.insert(frame, v[0])
                fcurve_location_y.keyframe_points.insert(frame, v[1])
                fcurve_location_z.keyframe_points.insert(frame, v[2])

            blender_pose_bone.rotation_mode = 'QUATERNION'
            data_path = blender_pose_bone.path_from_id("rotation_quaternion")
            fcurve_rotation_w = blender_action.fcurves.new(data_path, index=0)
            fcurve_rotation_x = blender_action.fcurves.new(data_path, index=1)
            fcurve_rotation_y = blender_action.fcurves.new(data_path, index=2)
            fcurve_rotation_z = blender_action.fcurves.new(data_path, index=3)
            for rotation_key_frames in ms3d_joint.rotation_key_frames:
                frame = (rotation_key_frames.time * ms3d_model.animation_fps)
                matrix_local = (Matrix.Rotation(
                        rotation_key_frames.rotation[2], 4, 'Z')
                        * Matrix.Rotation(
                                rotation_key_frames.rotation[1],
                                4,
                                'Y')) \
                                * Matrix.Rotation(
                                        rotation_key_frames.rotation[0],
                                        4,
                                        'X')
                q = (matrix_local).to_quaternion()
                fcurve_rotation_w.keyframe_points.insert(frame, q.w)
                fcurve_rotation_x.keyframe_points.insert(frame, q.x)
                fcurve_rotation_y.keyframe_points.insert(frame, q.y)
                fcurve_rotation_z.keyframe_points.insert(frame, q.z)

        enable_pose_mode(False)

        return blender_armature_object


###############################################################################
#234567890123456789012345678901234567890123456789012345678901234567890123456789
#--------1---------2---------3---------4---------5---------6---------7---------
# ##### END OF FILE #####
