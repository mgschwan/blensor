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
import io
import math
import mathutils
import os
import sys
import time


# To support reload properly, try to access a package var,
# if it's there, reload everything
if ("bpy" in locals()):
    import imp
    if "ms3d_spec" in locals():
        imp.reload(ms3d_spec)
    if "ms3d_utils" in locals():
        imp.reload(ms3d_utils)
    pass

else:
    from . import ms3d_spec
    from . import ms3d_utils
    pass


#import blender stuff
import bpy
import bpy_extras.io_utils

from bpy_extras.image_utils import load_image
from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        StringProperty,
        )


###############################################################################
def prop(name):
    return "ms3d_{0}".format(name)


###############################################################################
def hashStr(obj):
    return str(hash(obj))


PROP_NAME_HASH = "import_hash"
PROP_NAME_SMOOTH_GROUP = "smoothingGroup{0}"


###############################################################################
_idb_ms3d = 0
_idb_blender = 1
_idb_roll = 2

_bone_dummy = 1.0
_bone_distort = 0.00001 # sys.float_info.epsilon


###############################################################################
# registered entry point import
class ImportMS3D(
        bpy.types.Operator,
        bpy_extras.io_utils.ImportHelper
        ):
    """ Load a MilkShape3D MS3D File """

    bl_idname = "io_scene_ms3d.ms3d_import"
    bl_label = "Import MS3D"
    bl_description = "Import from a MS3D file format (.ms3d)"
    bl_options = {'PRESET'}
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    filename_ext = ms3d_utils.FILE_EXT
    filter_glob = StringProperty(
            default=ms3d_utils.FILE_FILTER,
            options={'HIDDEN'}
            )

    filepath = StringProperty(subtype='FILE_PATH')

    prop_verbose = BoolProperty(
            name=ms3d_utils.PROP_NAME_VERBOSE,
            description=ms3d_utils.PROP_DESC_VERBOSE,
            default=ms3d_utils.PROP_DEFAULT_VERBOSE,
            options=ms3d_utils.PROP_OPT_VERBOSE,
            )

    prop_coordinate_system = EnumProperty(
            name=ms3d_utils.PROP_NAME_COORDINATESYSTEM,
            description=ms3d_utils.PROP_DESC_COORDINATESYSTEM,
            items=ms3d_utils.PROP_ITEMS_COORDINATESYSTEM,
            default=ms3d_utils.PROP_DEFAULT_COORDINATESYSTEM_IMP,
            options=ms3d_utils.PROP_OPT_COORDINATESYSTEM,
            )

    prop_scale = FloatProperty(
            name=ms3d_utils.PROP_NAME_SCALE,
            description=ms3d_utils.PROP_DESC_SCALE,
            default=ms3d_utils.PROP_DEFAULT_SCALE,
            min=ms3d_utils.PROP_MIN_SCALE,
            max=ms3d_utils.PROP_MAX_SCALE,
            soft_min=ms3d_utils.PROP_SMIN_SCALE,
            soft_max=ms3d_utils.PROP_SMAX_SCALE,
            options=ms3d_utils.PROP_OPT_SCALE,
            )

    prop_unit_mm = BoolProperty(
            name=ms3d_utils.PROP_NAME_UNIT_MM,
            description=ms3d_utils.PROP_DESC_UNIT_MM,
            default=ms3d_utils.PROP_DEFAULT_UNIT_MM,
            options=ms3d_utils.PROP_OPT_UNIT_MM,
            )

    prop_objects = EnumProperty(
            name=ms3d_utils.PROP_NAME_OBJECTS_IMP,
            description=ms3d_utils.PROP_DESC_OBJECTS_IMP,
            items=ms3d_utils.PROP_ITEMS_OBJECTS_IMP,
            default=ms3d_utils.PROP_DEFAULT_OBJECTS_IMP,
            options=ms3d_utils.PROP_OPT_OBJECTS_IMP,
            )

    prop_animation = BoolProperty(
            name=ms3d_utils.PROP_NAME_ANIMATION,
            description=ms3d_utils.PROP_DESC_ANIMATION,
            default=ms3d_utils.PROP_DEFAULT_ANIMATION,
            options=ms3d_utils.PROP_OPT_ANIMATION,
            )

    prop_reuse = EnumProperty(
            name=ms3d_utils.PROP_NAME_REUSE,
            description=ms3d_utils.PROP_DESC_REUSE,
            items=ms3d_utils.PROP_ITEMS_REUSE,
            default=ms3d_utils.PROP_DEFAULT_REUSE,
            options=ms3d_utils.PROP_OPT_REUSE,
            )


    # draw the option panel
    def draw(self, context):
        layout = self.layout
        ms3d_utils.SetupMenuImport(self, layout)

    # entrypoint for MS3D -> blender
    def execute(self, blenderContext):
        """ start executing """
        return self.ReadMs3d(blenderContext)

    def invoke(self, blenderContext, event):
        blenderContext.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    # create empty blender ms3dTemplate
    # read ms3d file
    # fill blender with ms3dTemplate content
    def ReadMs3d(self, blenderContext):
        """ read ms3d file and convert ms3d content to bender content """

        t1 = time.time()
        t2 = None

        try:
            # setup environment
            ms3d_utils.PreSetupEnvironment(self)

            # create an empty ms3d template
            ms3dTemplate = ms3d_spec.ms3d_file_t(self.filepath_splitted[1])

            # open ms3d file
            self.file = io.FileIO(self.properties.filepath, "r")

            # read and inject ms3d data disk to blender
            ms3dTemplate.read(self.file)

            # close ms3d file
            self.file.close()

            t2 = time.time()

            # inject dictionaries
            # handle internal ms3d names to external blender names
            # to prevent potential name collisions on multiple imports
            # with same names but different content
            self.dict_actions = {}
            self.dict_armatures = {}
            self.dict_armature_objects = {}
            self.dict_groups = {}
            self.dict_images = {}
            self.dict_materials = {}
            self.dict_meshes = {}
            self.dict_mesh_objects = {}
            self.dict_textures = {}
            self.dict_comment_objects = {}

            # inject ms3d data to blender
            self.BlenderFromMs3d(blenderContext, ms3dTemplate)

            # finalize/restore environment
            ms3d_utils.PostSetupEnvironment(self, self.prop_unit_mm)

        except Exception:
            type, value, traceback = sys.exc_info()
            print("ReadMs3d - exception in try block\n  type: '{0}'\n"
                    "  value: '{1}'".format(type, value, traceback))

            if t2 is None:
                t2 = time.time()

            raise

        else:
            pass

        t3 = time.time()
        print("elapsed time: {0:.4}s (disk io: ~{1:.4}s, converter:"
                " ~{2:.4}s)".format((t3 - t1), (t2 - t1), (t3 - t2)))

        return {"FINISHED"}


    ###########################################################################
    def BlenderFromMs3d(self, blenderContext, ms3dTemplate):
        isValid, statistics = ms3dTemplate.isValid()

        if (self.prop_verbose):
            ms3dTemplate.print_internal()

        if (isValid):
            if ms3dTemplate.modelComment is not None:
                blenderEmpty, setupEmpty = self.GetCommentObject(ms3dTemplate)
                blenderContext.scene.objects.link(blenderEmpty)
                if setupEmpty:
                    blenderEmpty[prop(ms3d_spec.PROP_NAME_COMMENT)] = \
                            ms3dTemplate.modelComment.comment

            if (ms3d_utils.PROP_ITEM_OBJECT_JOINT in self.prop_objects):
                dict_bones, blenderArmatureObject = self.CreateArmature(
                        blenderContext, ms3dTemplate)

                if self.prop_animation:
                    self.CreateAnimation(blenderContext, ms3dTemplate,
                            dict_bones, blenderArmatureObject)
                    pass

            for ms3dGroupIndex, ms3dGroup in enumerate(ms3dTemplate.groups):
                blenderMesh = self.CreateMesh(blenderContext, ms3dTemplate,
                        ms3dGroup, ms3dGroupIndex)

                # apply material if available
                if ((ms3d_utils.PROP_ITEM_OBJECT_MATERIAL in self.prop_objects)
                        and (ms3dGroup.materialIndex >= 0)):
                    blenderMaterial = self.CreateMaterial(blenderContext,
                            ms3dTemplate, ms3dGroup.materialIndex,
                            blenderMesh.uv_textures[0])
                    blenderMesh.materials.append(blenderMaterial)

                # apply smoothing groups
                if (ms3d_utils.PROP_ITEM_OBJECT_SMOOTHGROUPS in
                        self.prop_objects):
                    self.GenerateSmoothGroups(blenderContext, ms3dTemplate,
                            ms3dGroup, blenderMesh.faces)

                # apply tris to quads
                if (ms3d_utils.PROP_ITEM_OBJECT_TRI_TO_QUAD in
                        self.prop_objects):
                    ms3d_utils.EnableEditMode(True)

                    # remove double vertices
                    ms3d_utils.SelectAll(True) # mesh

                    # convert tris to quads
                    if bpy.ops.mesh.tris_convert_to_quads.poll():
                        bpy.ops.mesh.tris_convert_to_quads()

                    ms3d_utils.EnableEditMode(False)

                self.PostSetupMesh()

            # put all objects to group
            if (ms3d_utils.PROP_ITEM_OBJECT_GROUP in self.prop_objects):
                blenderGroup, setupGroup = self.GetGroup(ms3dTemplate)
                if setupGroup:
                    for item in self.dict_mesh_objects.values():
                        blenderGroup.objects.link(item)
                        item.select = True
                    for item in self.dict_armature_objects.values():
                        blenderGroup.objects.link(item)
                        item.select = True
                    for item in self.dict_comment_objects.values():
                        blenderGroup.objects.link(item)
                        item.select = True

            print()
            print("##########################################################")
            print("MS3D -> Blender : [{0}]".format(self.filepath_splitted[1]))
            print(statistics)
            print("##########################################################")


    ###########################################################################
    def CreateArmature(self, blenderContext, ms3dTemplate):
        if (ms3dTemplate.nNumJoints <= 0):
            return None, None

        blenderScene = blenderContext.scene

        blenderArmature, setupArmature = self.GetArmature(ms3dTemplate)
        if setupArmature:
            blenderArmature.draw_type = 'STICK'
            blenderArmature.show_axes = True
            blenderArmature.use_auto_ik = True

        blenderObject, setupObject = self.GetArmatureObject(ms3dTemplate,
                blenderArmature)
        if setupObject:
            blenderObject.location = blenderContext.scene.cursor_location
            blenderObject.show_x_ray = True
            blenderScene.objects.link(blenderObject)

        blenderScene.objects.active = blenderObject

        ms3d_utils.EnableEditMode(True)

        dict_bones = {}
        for iBone, ms3dJoint in enumerate(ms3dTemplate.joints):
            blenderBone = blenderArmature.edit_bones.new(ms3dJoint.name)
            blenderBone[prop(ms3d_spec.PROP_NAME_NAME)] = ms3dJoint.name
            blenderBone[prop(ms3d_spec.PROP_NAME_FLAGS)] = ms3dJoint.flags

            ms3dComment = ms3dTemplate.get_joint_comment_by_key(iBone)
            if ms3dComment is not None:
                blenderBone[prop(ms3d_spec.PROP_NAME_COMMENT)] = \
                        ms3dComment.comment

            ms3dJointEx = ms3dTemplate.get_joint_ex_by_key(iBone)
            if ms3dJointEx is not None:
                blenderBone[prop(ms3d_spec.PROP_NAME_COLOR)] = \
                        ms3dJointEx.color

            blenderBone.select = True
            blenderArmature.edit_bones.active = blenderBone

            # [ms3d bone, number of references, blender bone, roll vector]
            dict_bones[ms3dJoint.name] = [ms3dJoint, blenderBone, None]

            mathVector = mathutils.Vector(ms3dJoint.position)
            mathVector = mathVector * self.matrixViewport

            if (not ms3dJoint.parentName):
                blenderBone.head = mathVector
                matrixRotation = None

                #dummy tail
                blenderBone.tail = blenderBone.head + mathutils.Vector(
                        (_bone_dummy, 0.0, 0.0))

            else:
                boneItem = dict_bones[ms3dJoint.parentName]
                blenderBoneParent = boneItem[_idb_blender]

                blenderBone.parent = blenderBoneParent
                if self.prop_animation:
                    blenderBone.use_inherit_rotation = False
                    blenderBone.use_inherit_scale = False

                matrixRotation = mathutils.Matrix()
                for blenderBoneParent in blenderBone.parent_recursive:
                    key = blenderBoneParent.name

                    # correct rotaion axis
                    rotationAxis = mathutils.Vector((
                            -dict_bones[key][_idb_ms3d].rotation[0],
                            -dict_bones[key][_idb_ms3d].rotation[1],
                            -dict_bones[key][_idb_ms3d].rotation[2]))
                    rotationAxis = rotationAxis * self.matrixSwapAxis

                    mathRotation = mathutils.Euler(rotationAxis, 'XZY')
                    matrixRotation = matrixRotation * mathRotation.to_matrix(
                            ).to_4x4()

                mathVector = blenderBone.parent.head + (mathVector
                        * matrixRotation)

                # at some very rare models, bones share the same place.
                # but blender removes bones that share the same space,
                # so distort the location a little bit
                if mathVector ==  blenderBone.parent.head:
                    mathVector -= mathutils.Vector((_bone_distort, 0.0, 0.0))
                    print("Info: distort bone in blender: '{0}'".format(blenderBone.name))

                blenderBone.head = mathVector

                # dummy tail
                blenderBone.tail = blenderBone.head + (
                        mathutils.Vector((_bone_dummy, 0.0, 0.0))
                        * self.matrixSwapAxis
                        * matrixRotation)

            if matrixRotation is not None:
                mathRollVector = (mathutils.Vector((0.0, 0.0, 1.0))
                        * matrixRotation)
                boneItem[_idb_roll] = mathRollVector

        # an adjustment pass
        # to adjust connection and tails of bones
        for blenderBone in blenderArmature.edit_bones:
            # skip if it has no parent
            if blenderBone.parent is None:
                continue

            # make nice blunt ending
            if not blenderBone.children:
                blenderBone.tail = blenderBone.parent.head

            # skip if parent has more than one children
            numberChildren = len(blenderBone.children)
            if (numberChildren == 1):
                blenderBone.tail = blenderBone.children[0].head
                blenderBone.children[0].use_connect = True

        # an extra additional adjustment pass
        # to re-correct possible modified bonerolls
        for key in dict_bones:
            boneItem = dict_bones[key]
            blenderBone = boneItem[_idb_blender]
            mathRollVector = boneItem[_idb_roll]
            if mathRollVector is not None:
                blenderBone.align_roll(mathRollVector)

            # make dict lightweight
            boneItem[_idb_blender] = boneItem[_idb_blender].name
            #boneItem[_idb_ms3d] = boneItem[_idb_ms3d]
            boneItem[_idb_roll] = None

        ms3d_utils.EnableEditMode(False)

        return dict_bones, blenderObject


    ###########################################################################
    def CreateAnimation(self, blenderContext, ms3dTemplate, dict_bones, blenderObject):
        if (ms3dTemplate.nNumJoints <= 0):
            return None

        blenderScene = blenderContext.scene

        blenderScene.render.fps = ms3dTemplate.fAnimationFPS
        if ms3dTemplate.fAnimationFPS:
            blenderScene.render.fps_base = (blenderScene.render.fps /
                    ms3dTemplate.fAnimationFPS)
        blenderScene.frame_start = 1
        blenderScene.frame_end = (ms3dTemplate.iTotalFrames
                + blenderScene.frame_start) - 1
        blenderScene.frame_current = (ms3dTemplate.fCurrentTime
                * blenderScene.render.fps
                / blenderScene.render.fps_base)

        blenderAction, setupAction = self.GetAction(ms3dTemplate)
        if blenderObject.animation_data is None:
            blenderObject.animation_data_create()
        blenderObject.animation_data.action = blenderAction

        for boneName in dict_bones:
            item = dict_bones[boneName]
            blenderBoneName = item[_idb_blender]
            ms3dJoint =  item[_idb_ms3d]

            blenderBoneObject = blenderObject.pose.bones.get(blenderBoneName)
            if blenderBoneObject is None:
                # no idea why at some models are
                # bones are missing in blender, but are present in dict
                print("Info: missing bone in blender: '{0}'".format(blenderBoneName))
                continue

            blenderBone = blenderObject.data.bones.get(blenderBoneName)

            data_path = blenderBoneObject.path_from_id("location")
            fcurveTransX = blenderAction.fcurves.new(data_path, index=0)
            fcurveTransY = blenderAction.fcurves.new(data_path, index=1)
            fcurveTransZ = blenderAction.fcurves.new(data_path, index=2)
            for keyFramesTrans in ms3dJoint.keyFramesTrans:
                frame = (keyFramesTrans.time
                        * blenderScene.render.fps
                        / blenderScene.render.fps_base)
                translationAxis = mathutils.Vector((
                        keyFramesTrans.position[0],
                        keyFramesTrans.position[1],
                        keyFramesTrans.position[2]))
                translationAxis = translationAxis * self.matrixSwapAxis
                fcurveTransX.keyframe_points.insert(frame, translationAxis[0])
                fcurveTransY.keyframe_points.insert(frame, translationAxis[1])
                fcurveTransZ.keyframe_points.insert(frame, translationAxis[2])

            data_path = blenderBoneObject.path_from_id("rotation_euler")
            blenderBoneObject.rotation_mode = 'XZY'
            #data_path = blenderBoneObject.path_from_id("rotation_quaternion")
            #fcurveRotW = blenderAction.fcurves.new(data_path, index=0)
            fcurveRotX = blenderAction.fcurves.new(data_path, index=0)
            fcurveRotY = blenderAction.fcurves.new(data_path, index=1)
            fcurveRotZ = blenderAction.fcurves.new(data_path, index=2)
            for keyFramesRot in ms3dJoint.keyFramesRot:
                frame = (keyFramesRot.time
                        * blenderScene.render.fps
                        / blenderScene.render.fps_base)
                rotationAxis = mathutils.Vector((
                        -keyFramesRot.rotation[0],
                        -keyFramesRot.rotation[1],
                        -keyFramesRot.rotation[2]))
                rotationAxis = rotationAxis * self.matrixSwapAxis
                mathRotEuler = mathutils.Euler(rotationAxis, 'XZY')

                fcurveRotX.keyframe_points.insert(frame, mathRotEuler.x)
                fcurveRotY.keyframe_points.insert(frame, mathRotEuler.y)
                fcurveRotZ.keyframe_points.insert(frame, mathRotEuler.z)

                #mathRotQuaternion = mathRotEuler.to_quaternion()
                #fcurveRotW.keyframe_points.insert(frame, mathRotQuaternion.w)
                #fcurveRotX.keyframe_points.insert(frame, mathRotQuaternion.x)
                #fcurveRotY.keyframe_points.insert(frame, mathRotQuaternion.y)
                #fcurveRotZ.keyframe_points.insert(frame, mathRotQuaternion.z)


    ###########################################################################
    def CreateImageTexture(self, ms3dMaterial, alphamap, allow_create=True):
        blenderImage, setupImage = self.GetImage(ms3dMaterial, alphamap,
                allow_create=allow_create)
        if setupImage:
            pass

        blenderTexture, setupTexture = self.GetTexture(ms3dMaterial, alphamap,
                blenderImage, allow_create=allow_create)
        if setupTexture:
            blenderTexture.image = blenderImage

            if (alphamap):
                blenderTexture.use_preview_alpha = True

        return blenderTexture


    ###########################################################################
    def CreateMaterial(self, blenderContext, ms3dTemplate, ms3dMaterialIndex,
            blenderUvLayer):
        ms3dMaterial = ms3dTemplate.materials[ms3dMaterialIndex]

        blenderMaterial, setupMaterial = self.GetMaterial(ms3dMaterial)
        if setupMaterial:
            blenderMaterial[prop(PROP_NAME_HASH)] = hashStr(ms3dMaterial)
            blenderMaterial[prop(ms3d_spec.PROP_NAME_MODE)] = ms3dMaterial.mode
            blenderMaterial[prop(ms3d_spec.PROP_NAME_AMBIENT)] = \
                    ms3dMaterial.ambient
            blenderMaterial[prop(ms3d_spec.PROP_NAME_EMISSIVE)] = \
                    ms3dMaterial.emissive

            ms3dComment = \
                    ms3dTemplate.get_material_comment_by_key(ms3dMaterialIndex)
            if ms3dComment is not None:
                blenderMaterial[prop(ms3d_spec.PROP_NAME_COMMENT)] = \
                        ms3dComment.comment

            blenderMaterial.ambient = ((
                    (ms3dMaterial.ambient[0]
                    + ms3dMaterial.ambient[1]
                    + ms3dMaterial.ambient[2]) / 3.0)
                    * ms3dMaterial.ambient[3])

            blenderMaterial.diffuse_color[0] = ms3dMaterial.diffuse[0]
            blenderMaterial.diffuse_color[1] = ms3dMaterial.diffuse[1]
            blenderMaterial.diffuse_color[2] = ms3dMaterial.diffuse[2]
            blenderMaterial.diffuse_intensity = ms3dMaterial.diffuse[3]

            blenderMaterial.specular_color[0] = ms3dMaterial.specular[0]
            blenderMaterial.specular_color[1] = ms3dMaterial.specular[1]
            blenderMaterial.specular_color[2] = ms3dMaterial.specular[2]
            blenderMaterial.specular_intensity = ms3dMaterial.specular[3]

            blenderMaterial.emit = ((
                    (ms3dMaterial.emissive[0]
                    + ms3dMaterial.emissive[1]
                    + ms3dMaterial.emissive[2]) / 3.0)
                    * ms3dMaterial.emissive[3])

            blenderMaterial.specular_hardness = ms3dMaterial.shininess * 2.0

            if (ms3dMaterial.transparency):
                blenderMaterial.use_transparency = True
                blenderMaterial.alpha = ms3dMaterial.transparency
                blenderMaterial.specular_alpha = blenderMaterial.alpha

            if (blenderMaterial.game_settings):
                blenderMaterial.game_settings.use_backface_culling = False
                blenderMaterial.game_settings.alpha_blend = 'ALPHA'

            # diffuse texture
            if (ms3dMaterial.texture):
                blenderMaterial[prop(ms3d_spec.PROP_NAME_TEXTURE)] = \
                        ms3dMaterial.texture
                blenderTexture = self.CreateImageTexture(ms3dMaterial, False)

                blenderTextureSlot = blenderMaterial.texture_slots.add()
                blenderTextureSlot.texture = blenderTexture
                blenderTextureSlot.texture_coords = 'UV'
                blenderTextureSlot.uv_layer = blenderUvLayer.name
                blenderTextureSlot.use_map_color_diffuse = True
                blenderTextureSlot.use_map_alpha = False

                # apply image also to uv's
                for blenderTextureFace in blenderUvLayer.data:
                    blenderTextureFace.image = blenderTexture.image

            # alpha texture
            if (ms3dMaterial.alphamap):
                blenderMaterial[prop(ms3d_spec.PROP_NAME_ALPHAMAP)] = \
                        ms3dMaterial.alphamap
                blenderMaterial.alpha = 0
                blenderMaterial.specular_alpha = 0

                blenderTexture = self.CreateImageTexture(ms3dMaterial, True)

                blenderTextureSlot = blenderMaterial.texture_slots.add()
                blenderTextureSlot.texture = blenderTexture
                blenderTextureSlot.texture_coords = 'UV'
                blenderTextureSlot.uv_layer = blenderUvLayer.name
                blenderTextureSlot.use_map_color_diffuse = False
                blenderTextureSlot.use_map_alpha = True
                blenderTextureSlot.use_rgb_to_intensity = True

        else:
            if (ms3dMaterial.texture):
                blenderTexture = self.CreateImageTexture(ms3dMaterial, False,
                        allow_create=False)

                # apply image also to uv's
                if blenderTexture:
                    for blenderTextureFace in blenderUvLayer.data:
                        blenderTextureFace.image = blenderTexture.image

        return blenderMaterial


    ###########################################################################
    def CreateMesh(self, blenderContext, ms3dTemplate, ms3dGroup,
            ms3dGroupIndex):
        vertices = []
        edges = []
        faces = []

        boneIds = {}
        dict_vertices = {}

        for iTriangle in ms3dGroup.triangleIndices:
            face = []
            for iVertex in ms3dTemplate.triangles[iTriangle].vertexIndices:
                iiVertex = dict_vertices.get(iVertex)
                if iiVertex is None:
                    # add to ms3d to blender translation dictionary
                    dict_vertices[iVertex] = iiVertex = len(vertices)

                    # prepare vertices of mesh
                    ms3dVertex = ms3dTemplate.vertices[iVertex]
                    mathVector = mathutils.Vector(ms3dVertex.vertex)
                    mathVector = mathVector * self.matrixViewport
                    vertices.append(mathVector)

                    # prepare boneId dictionary for later use
                    iBone = boneIds.get(ms3dVertex.boneId)
                    if iBone is not None:
                        iBone.append(iiVertex)
                    else:
                        boneIds[ms3dVertex.boneId] = [iiVertex, ]

                face.append(iiVertex)
            faces.append(face)

        blenderScene = blenderContext.scene

        blenderMesh, setupMesh = self.GetMesh(ms3dGroup)

        blenderObject, setupObject = self.GetMeshObject(ms3dGroup, blenderMesh)
        blenderObject.location = blenderScene.cursor_location
        blenderScene.objects.link(blenderObject)
        if setupObject:
            blenderObject[prop(ms3d_spec.PROP_NAME_FLAGS)] = ms3dGroup.flags
            ms3dComment = ms3dTemplate.get_group_comment_by_key(ms3dGroupIndex)
            if ms3dComment is not None:
                blenderObject[prop(ms3d_spec.PROP_NAME_COMMENT)] = \
                        ms3dComment.comment

        # setup mesh
        blenderMesh.from_pydata(vertices, edges, faces)
        if (not edges):
            blenderMesh.update(calc_edges=True)

        # make new object as active and only selected object
        ms3d_utils.SelectAll(False) # object
        blenderObject.select = True
        bpy.context.scene.objects.active = blenderObject

        # create vertex groups for boneIds
        for boneId, vertexIndices in boneIds.items():
            if boneId < 0:
                continue

            # put selected to vertex_group
            #n = ms3dTemplate.get_joint_by_key(boneId)
            n = ms3dTemplate.joints[boneId]
            blenderBoneIdKey = n.name
            blenderVertexGroup = \
                bpy.context.active_object.vertex_groups.new(blenderBoneIdKey)

            for iiVertex in vertexIndices:
                blenderVertexGroup.add([iiVertex], 1.0, 'REPLACE')

            # add group to armature modifier
            if (ms3d_utils.PROP_ITEM_OBJECT_JOINT in self.prop_objects):
                blenderArmatureObject = self.GetArmatureObject(
                        ms3dTemplate, None)
                if blenderArmatureObject[0] is not None:
                    name = ms3dTemplate.get_joint_by_key(boneId).name
                    blenderBone = blenderArmatureObject[0].data.bones.get(name)
                    if blenderBone is not None:
                        blenderModifier = blenderObject.modifiers.new(
                                name, type='ARMATURE')
                        blenderModifier.object = blenderArmatureObject[0]
                        blenderModifier.vertex_group = blenderVertexGroup.name

        # handle UVs
        # add UVs
        if ((not blenderMesh.uv_textures)
                and bpy.ops.mesh.uv_texture_add.poll()):
            bpy.ops.mesh.uv_texture_add()

        # convert ms3d-ST to blender-UV
        for i, blenderUv in enumerate(blenderMesh.uv_textures[0].data):
            blenderUv.uv1[0], blenderUv.uv1[1] = ms3dTemplate.triangles[
                    ms3dGroup.triangleIndices[i]].s[0], (1.0 -
                    ms3dTemplate.triangles[ms3dGroup.triangleIndices[i]].t[0])
            blenderUv.uv2[0], blenderUv.uv2[1] = ms3dTemplate.triangles[
                    ms3dGroup.triangleIndices[i]].s[1], (1.0 -
                    ms3dTemplate.triangles[ms3dGroup.triangleIndices[i]].t[1])
            blenderUv.uv3[0], blenderUv.uv3[1] = ms3dTemplate.triangles[
                    ms3dGroup.triangleIndices[i]].s[2], (1.0 -
                    ms3dTemplate.triangles[ms3dGroup.triangleIndices[i]].t[2])

        ms3d_utils.EnableEditMode(False)

        return blenderMesh


    ###########################################################################
    def GenerateSmoothGroups(self, blenderContext, ms3dTemplate, ms3dGroup,
            blenderFaces):
        """ split faces of a smoothingGroup.
            it will preserve the UVs and materials.

            SIDE-EFFECT: it will change the order of faces! """

        # smooth mesh to see its smoothed region
        if bpy.ops.object.shade_smooth.poll():
            bpy.ops.object.shade_smooth()

        nFaces = len(blenderFaces)

        # collect smoothgroups and its faces
        smoothGroupFaceIndices = {}
        for iTriangle, ms3dTriangleIndex in \
                enumerate(ms3dGroup.triangleIndices):
            smoothGroupKey = \
                    ms3dTemplate.triangles[ms3dTriangleIndex].smoothingGroup

            if (smoothGroupKey == 0):
                continue

            if (smoothGroupKey not in smoothGroupFaceIndices):
                smoothGroupFaceIndices[smoothGroupKey] = []

            smoothGroupFaceIndices[smoothGroupKey].append(iTriangle)

        nKeys = len(smoothGroupFaceIndices)

        # handle smoothgroups, if more than one is available
        if (nKeys <= 1):
            return

        # enable edit-mode
        ms3d_utils.EnableEditMode(True)

        for smoothGroupKey in smoothGroupFaceIndices:
            # deselect all "faces"
            ms3d_utils.SelectAll(False) # mesh

            # enable object-mode (important for face.select = value)
            ms3d_utils.EnableEditMode(False)

            # select faces of current smoothgroup
            for faceIndex in smoothGroupFaceIndices[smoothGroupKey]:
                blenderFaces[faceIndex].select = True

            # enable edit-mode again
            ms3d_utils.EnableEditMode(True)

            ## split selected faces
            ## WARNING: it will reorder the faces!
            ## after that, with that logic, it is impossible to use the
            ## dictionary for the next outstanding smoothgroups anymore
            # if bpy.ops.mesh.split.poll():
            #     bpy.ops.mesh.split()

            # SPLIT WORKAROUND part 1
            # duplicate selected faces
            if bpy.ops.mesh.duplicate.poll():
                bpy.ops.mesh.duplicate()

            # put selected to vertex_group
            blenderVertexGroup = bpy.context.active_object.vertex_groups.new(
                    prop(PROP_NAME_SMOOTH_GROUP).format(smoothGroupKey))
            bpy.context.active_object.vertex_groups.active = blenderVertexGroup
            if bpy.ops.object.vertex_group_assign.poll():
                bpy.ops.object.vertex_group_assign()

        ## SPLIT WORKAROUND START part 2
        # cleanup old faces
        #
        ms3d_utils.SelectAll(False) # mesh

        # enable object-mode (important for face.select = value)
        ms3d_utils.EnableEditMode(False)

        # select all old faces
        for faceIndex in range(nFaces):
            blenderFaces[faceIndex].select = True
            pass

        # enable edit-mode again
        ms3d_utils.EnableEditMode(True)

        # delete old faces and its vertices
        if bpy.ops.mesh.delete.poll():
            bpy.ops.mesh.delete(type='VERT')
        #
        ## SPLIT WORKAROUND END part 2


        # enable object-mode
        ms3d_utils.EnableEditMode(False)

        pass


    ###########################################################################
    def PostSetupMesh(self):
        ms3d_utils.EnableEditMode(True)
        ms3d_utils.SelectAll(True) # mesh
        ms3d_utils.EnableEditMode(False)


    ###########################################################################
    def GetAction(self, ms3dObject):
        nameAction = ms3dObject.name

        # already available
        blenderAction = self.dict_actions.get(nameAction)
        if blenderAction is not None:
            return blenderAction, False

        # create new
        blenderAction = bpy.data.actions.new(nameAction)
        self.dict_actions[nameAction] = blenderAction
        if blenderAction is not None:
            blenderAction[prop(ms3d_spec.PROP_NAME_NAME)] = nameAction
        return blenderAction, True


    ###########################################################################
    def GetArmature(self, ms3dObject):
        nameArmature = ms3dObject.name

        # already available
        blenderArmature = self.dict_armatures.get(nameArmature)
        if blenderArmature is not None:
            return blenderArmature, False

        # create new
        blenderArmature = bpy.data.armatures.new(nameArmature)
        self.dict_armatures[nameArmature] = blenderArmature
        if blenderArmature is not None:
            blenderArmature[prop(ms3d_spec.PROP_NAME_NAME)] = nameArmature
        return blenderArmature, True


    ###########################################################################
    def GetArmatureObject(self, ms3dObject, objectData):
        nameObject = ms3dObject.name

        # already available
        blenderObject = self.dict_armature_objects.get(nameObject)
        if blenderObject is not None:
            return blenderObject, False

        # create new
        blenderObject = bpy.data.objects.new(nameObject, objectData)
        self.dict_armature_objects[nameObject] = blenderObject
        if blenderObject is not None:
            blenderObject[prop(ms3d_spec.PROP_NAME_NAME)] = nameObject
        return blenderObject, True


    ###########################################################################
    def GetGroup(self, ms3dObject):
        nameGroup = ms3dObject.name

        # already available
        blenderGroup = self.dict_groups.get(nameGroup)
        if blenderGroup is not None:
            return blenderGroup, False

        # create new
        blenderGroup = bpy.data.groups.new(nameGroup)
        self.dict_groups[nameGroup] = blenderGroup
        if blenderGroup is not None:
            blenderGroup[prop(ms3d_spec.PROP_NAME_NAME)] = nameGroup
        return blenderGroup, True


    ###########################################################################
    def GetImage(self, ms3dMaterial, alphamap, allow_create=True):
        if alphamap:
            nameImageRaw = ms3dMaterial.alphamap
            propName = ms3d_spec.PROP_NAME_ALPHAMAP
        else:
            nameImageRaw = ms3dMaterial.texture
            propName = ms3d_spec.PROP_NAME_TEXTURE

        nameImage = os.path.split(nameImageRaw)[1]
        nameDirectory = self.filepath_splitted[0]

        # already available
        blenderImage = self.dict_images.get(nameImage)
        if blenderImage is not None:
            return blenderImage, False

        # OPTIONAL: try to find an existing one, that fits
        if (self.prop_reuse == ms3d_utils.PROP_ITEM_REUSE_MATCH_VALUES):
            testBlenderImage = bpy.data.images.get(nameImage, None)
            if (testBlenderImage):
                # take a closer look to its content
                if ((not testBlenderImage.library)
                        and (os.path.split(
                        testBlenderImage.filepath)[1] == nameImage)):
                    return testBlenderImage, False

        # elif (self.prop_reuse == ms3d_utils.PROP_ITEM_REUSE_MATCH_HASH):
        #     # irrespecting its real content
        #     # take materials, that have the same "ms3d_import_hash"
        #     # custom property (of an previous import)
        #     propKey = prop(PROP_NAME_HASH)
        #     hexHash = hex(hash(nameImage))
        #     for testBlenderImage in bpy.data.images:
        #         if ((testBlenderImage) and (not testBlenderImage.library)
        #                 and (propKey in testBlenderImage)
        #                 and (testBlenderImage[propKey] == hexHash)):
        #             return testBlenderImage, False

        if not allow_create:
            return None, False

        # create new
        blenderImage = load_image(nameImage, nameDirectory)
        self.dict_images[nameImage] = blenderImage
        if blenderImage is not None:
            blenderImage[prop(ms3d_spec.PROP_NAME_NAME)] = ms3dMaterial.name
            blenderImage[prop(propName)] = nameImageRaw
        return blenderImage, True


    ###########################################################################
    def GetTexture(self, ms3dMaterial, alphamap, blenderImage,
            allow_create=True):
        if alphamap:
            nameTextureRaw = ms3dMaterial.alphamap
            propName = ms3d_spec.PROP_NAME_ALPHAMAP
        else:
            nameTextureRaw = ms3dMaterial.texture
            propName = ms3d_spec.PROP_NAME_TEXTURE

        nameTexture = os.path.split(nameTextureRaw)[1]

        # already available
        blenderTexture = self.dict_textures.get(nameTexture)
        if blenderTexture is not None:
            return blenderTexture, False

        # OPTIONAL: try to find an existing one, that fits
        if self.prop_reuse == ms3d_utils.PROP_ITEM_REUSE_MATCH_VALUES:
            testBlenderTexture = bpy.data.textures.get(nameTexture, None)
            if (testBlenderTexture):
                # take a closer look to its content
                if ((not testBlenderTexture.library)
                        and (testBlenderTexture.type == 'IMAGE')
                        and (testBlenderTexture.image)
                        and (blenderImage)
                        and (testBlenderTexture.image.filepath
                        == blenderImage.filepath)
                        ):
                    return testBlenderTexture, False

        #elif self.prop_reuse == ms3d_utils.PROP_ITEM_REUSE_MATCH_HASH:
        #    # irrespecting its real content
        #    # take materials, that have the same "ms3d_import_hash"
        #    # custom property (of an previous import)
        #    propKey = prop(PROP_NAME_HASH)
        #    hexHash = hex(hash(nameTexture))
        #    for testBlenderTexture in bpy.data.textures:
        #        if ((testBlenderTexture) and (not testBlenderTexture.library)
        #                 and (propKey in testBlenderTexture)
        #                 and (testBlenderTexture[propKey] == hexHash)):
        #            return testBlenderTexture, False

        if not allow_create:
            return None, False

        # create new
        blenderTexture = bpy.data.textures.new(name=nameTexture, type='IMAGE')
        self.dict_textures[nameTexture] = blenderTexture
        if blenderTexture is not None:
            blenderTexture[prop(ms3d_spec.PROP_NAME_NAME)] = ms3dMaterial.name
            blenderTexture[prop(propName)] = nameTextureRaw
        return blenderTexture, True


    ###########################################################################
    def GetMaterial(self, ms3dMaterial):
        nameMaterial = ms3dMaterial.name

        # already available
        blenderMaterial = self.dict_materials.get(nameMaterial)
        if blenderMaterial is not None:
            return blenderMaterial, False

        # OPTIONAL: try to find an existing one, that fits
        if self.prop_reuse == ms3d_utils.PROP_ITEM_REUSE_MATCH_VALUES:
            # irrespecting non tested real content
            # take materials, that have similar values
            epsilon = 0.00001
            for testBlenderMaterial in bpy.data.materials:
                # take a closer look to its content
                if ((testBlenderMaterial)
                        and (not testBlenderMaterial.library)
                        and (epsilon > abs(testBlenderMaterial.ambient - ((
                            ms3dMaterial.ambient[0] + ms3dMaterial.ambient[1]
                            + ms3dMaterial.ambient[2]) / 3.0)
                            * ms3dMaterial.ambient[3]))
                        and (epsilon > abs(testBlenderMaterial.diffuse_color[0]
                            - ms3dMaterial.diffuse[0]))
                        and (epsilon > abs(testBlenderMaterial.diffuse_color[1]
                            - ms3dMaterial.diffuse[1]))
                        and (epsilon > abs(testBlenderMaterial.diffuse_color[2]
                            - ms3dMaterial.diffuse[2]))
                        and (epsilon > abs(
                            testBlenderMaterial.diffuse_intensity
                            - ms3dMaterial.diffuse[3]))
                        and (epsilon > abs(
                            testBlenderMaterial.specular_color[0]
                            - ms3dMaterial.specular[0]))
                        and (epsilon > abs(
                            testBlenderMaterial.specular_color[1]
                            - ms3dMaterial.specular[1]))
                        and (epsilon > abs(
                            testBlenderMaterial.specular_color[2]
                            - ms3dMaterial.specular[2]))
                        and (epsilon > abs(
                            testBlenderMaterial.specular_intensity
                            - ms3dMaterial.specular[3]))
                        and (epsilon > abs(testBlenderMaterial.emit - ((
                            ms3dMaterial.emissive[0] + ms3dMaterial.emissive[1]
                            + ms3dMaterial.emissive[2]) / 3.0)
                            * ms3dMaterial.emissive[3]))
                        and (epsilon > abs(
                            testBlenderMaterial.specular_hardness
                            - (ms3dMaterial.shininess * 2.0)))
                        ):

                    # diffuse texture
                    fitTexture = False
                    testTexture = False
                    if (ms3dMaterial.texture):
                        testTexture = True

                        if (testBlenderMaterial.texture_slots):
                            nameTexture = os.path.split(ms3dMaterial.texture)[1]

                            for blenderTextureSlot in testBlenderMaterial.texture_slots:
                                if ((blenderTextureSlot)
                                        and (blenderTextureSlot.use_map_color_diffuse)
                                        and (blenderTextureSlot.texture)
                                        and (blenderTextureSlot.texture.type == 'IMAGE')
                                        and (
                                            ((blenderTextureSlot.texture.image)
                                                and (blenderTextureSlot.texture.image.filepath)
                                                and (os.path.split(blenderTextureSlot.texture.image.filepath)[1] == nameTexture)
                                            )
                                            or
                                            ((not blenderTextureSlot.texture.image)
                                                and (blenderTextureSlot.texture.name == nameTexture)
                                            )
                                        )):
                                    fitTexture = True
                                    break;

                    fitAlpha = False
                    testAlpha = False
                    # alpha texture
                    if (ms3dMaterial.alphamap):
                        testAlpha = True

                        if (testBlenderMaterial.texture_slots):
                            nameAlpha = os.path.split(ms3dMaterial.alphamap)[1]

                            for blenderTextureSlot in testBlenderMaterial.texture_slots:
                                if ((blenderTextureSlot)
                                        and (blenderTextureSlot.use_map_alpha)
                                        and (blenderTextureSlot.texture)
                                        and (blenderTextureSlot.texture.type == 'IMAGE')
                                        and (
                                            ((blenderTextureSlot.texture.image)
                                                and (blenderTextureSlot.texture.image.filepath)
                                                and (os.path.split(blenderTextureSlot.texture.image.filepath)[1] == nameAlpha)
                                            )
                                            or
                                            ((not blenderTextureSlot.texture.image)
                                                and (blenderTextureSlot.texture.name == nameAlpha)
                                                )
                                        )):
                                    fitAlpha = True
                                    break;

                    if (((not testTexture) or (testTexture and fitTexture))
                            and ((not testAlpha) or (testAlpha and fitAlpha))):
                        return testBlenderMaterial, False

        # elif self.prop_reuse == ms3d_utils.PROP_ITEM_REUSE_MATCH_HASH:
        #    # irrespecting its real content
        #    # take materials, that have the same "ms3d_import_hash"
        #    # custom property (of an previous import)
        #    propKey = prop(PROP_NAME_HASH)
        #    hexHash = hex(hash(ms3dMaterial))
        #    for testBlenderMaterial in bpy.data.materials:
        #        if ((testBlenderMaterial) and (not testBlenderMaterial.library)
        #                and (propKey in testBlenderMaterial)
        #                and (testBlenderMaterial[propKey] == hexHash)):
        #            return testBlenderMaterial, False

        # create new
        blenderMaterial = bpy.data.materials.new(nameMaterial)
        self.dict_materials[nameMaterial] = blenderMaterial
        if blenderMaterial is not None:
            blenderMaterial[prop(ms3d_spec.PROP_NAME_NAME)] = nameMaterial
        return blenderMaterial, True


    ###########################################################################
    def GetMesh(self, ms3dGroup):
        nameMesh = ms3dGroup.name

        # already available
        blenderMesh = self.dict_meshes.get(nameMesh)
        if blenderMesh is not None:
            return blenderMesh, False

        # create new
        blenderMesh = bpy.data.meshes.new(nameMesh)
        self.dict_meshes[nameMesh] = blenderMesh
        if blenderMesh is not None:
            blenderMesh[prop(ms3d_spec.PROP_NAME_NAME)] = nameMesh
        return blenderMesh, True


    ###########################################################################
    def GetMeshObject(self, ms3dObject, objectData):
        nameObject = ms3dObject.name

        # already available
        blenderObject = self.dict_mesh_objects.get(nameObject)
        if blenderObject is not None:
            return blenderObject, False

        # create new
        blenderObject = bpy.data.objects.new(nameObject, objectData)
        self.dict_mesh_objects[nameObject] = blenderObject
        if blenderObject is not None:
            blenderObject[prop(ms3d_spec.PROP_NAME_NAME)] = nameObject
        return blenderObject, True


    ###########################################################################
    def GetCommentObject(self, ms3dObject):
        nameObject = ms3dObject.name

        # already available
        blenderObject = self.dict_comment_objects.get(nameObject)
        if blenderObject is not None:
            return blenderObject, False

        # create new
        blenderObject = bpy.data.objects.new(nameObject, None)
        self.dict_comment_objects[nameObject] = blenderObject
        if blenderObject is not None:
            blenderObject[prop(ms3d_spec.PROP_NAME_NAME)] = nameObject
        return blenderObject, True


###############################################################################
#234567890123456789012345678901234567890123456789012345678901234567890123456789
#--------1---------2---------3---------4---------5---------6---------7---------
# ##### END OF FILE #####
