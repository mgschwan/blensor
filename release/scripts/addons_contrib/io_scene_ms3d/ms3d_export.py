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

from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        StringProperty,
        )


# registered entry point export
class ExportMS3D(
        bpy.types.Operator,
        bpy_extras.io_utils.ExportHelper
        ):
    """Save a MilkShape3D MS3D File"""

    bl_idname = "io_scene_ms3d.ms3d_export"
    bl_label = "Export MS3D"
    bl_description = "Export to a MS3D file format (.ms3d)"
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
            default=ms3d_utils.PROP_DEFAULT_COORDINATESYSTEM_EXP,
            options=ms3d_utils.PROP_OPT_COORDINATESYSTEM,
            )

    prop_scale = FloatProperty(
            name=ms3d_utils.PROP_NAME_SCALE,
            description=ms3d_utils.PROP_DESC_SCALE,
            default=1.0 / ms3d_utils.PROP_DEFAULT_SCALE,
            min=ms3d_utils.PROP_MIN_SCALE,
            max=ms3d_utils.PROP_MAX_SCALE,
            soft_min=ms3d_utils.PROP_SMIN_SCALE,
            soft_max=ms3d_utils.PROP_SMAX_SCALE,
            options=ms3d_utils.PROP_OPT_SCALE,
            )

    prop_objects = EnumProperty(
            name=ms3d_utils.PROP_NAME_OBJECTS_EXP,
            description=ms3d_utils.PROP_DESC_OBJECTS_EXP,
            items=ms3d_utils.PROP_ITEMS_OBJECTS_EXP,
            default=ms3d_utils.PROP_DEFAULT_OBJECTS_EXP,
            options=ms3d_utils.PROP_OPT_OBJECTS_EXP,
            )

    prop_selected = BoolProperty(
            name=ms3d_utils.PROP_NAME_SELECTED,
            description=ms3d_utils.PROP_DESC_SELECTED,
            default=ms3d_utils.PROP_DEFAULT_SELECTED,
            options=ms3d_utils.PROP_OPT_SELECTED,
            )

    prop_animation = BoolProperty(
            name=ms3d_utils.PROP_NAME_ANIMATION,
            description=ms3d_utils.PROP_DESC_ANIMATION,
            default=ms3d_utils.PROP_DEFAULT_ANIMATION,
            options=ms3d_utils.PROP_OPT_ANIMATION,
            )


    # draw the option panel
    def draw(self, context):
        layout = self.layout
        ms3d_utils.SetupMenuExport(self, layout)

    # entrypoint for blender -> MS3D
    def execute(self, blenderContext):
        """start executing"""
        return self.WriteMs3d(blenderContext)

    #
    def invoke(self, blenderContext, event):
        blenderContext.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    # create a empty ms3d ms3dTemplate
    # fill ms3dTemplate with blender content
    # writer ms3d file
    def WriteMs3d(self, blenderContext):
        """convert bender content to ms3d content and write it to file"""

        t1 = time.time()
        t2 = None

        try:
            # setup environment
            ms3d_utils.PreSetupEnvironment(self)

            # create an empty ms3d template
            ms3dTemplate = ms3d_spec.ms3d_file_t()

            # inject blender data to ms3d file
            self.Ms3dFromBlender(blenderContext, ms3dTemplate)

            t2 = time.time()

            # write ms3d file to disk
            self.file = io.FileIO(self.filepath, "w")

            ms3dTemplate.write(self.file)

            self.file.flush()
            self.file.close()

            # finalize/restore environment
            ms3d_utils.PostSetupEnvironment(self, False)

        except Exception:
            type, value, traceback = sys.exc_info()
            print("WriteMs3d - exception in try block\n  type: '{0}'\n"
                    "  value: '{1}'".format(type, value, traceback))

            if t2 is None:
                t2 = time.time()

            raise

        else:
            pass

        t3 = time.time()
        print("elapsed time: {0:.4}s (converter: ~{1:.4}s, disk io:"
                " ~{2:.4}s)".format((t3 - t1), (t2 - t1), (t3 - t2)))

        return {"FINISHED"}


    ###########################################################################
    def Ms3dFromBlender(self, blenderContext, ms3dTemplate):
        """ known limitations:
            - bones unsupported yet
            - joints unsupported yet
            - very bad performance

        notes:
            - interpreating a blender-mesh-objects as ms3d-group
            - only one material allowed per group in ms3d,
              maybe sub-split a mesh in to material groups???"""

        blender = blenderContext.blend_data

        # todo: use an optimized collection for quick search vertices;
        # with ~(o log n); currently its (o**n)
        ms3dVertices = []

        ms3dTriangles = []
        ms3dMaterials = []
        ms3dGroups = []

        flagHandleMaterials = \
                (ms3d_utils.PROP_ITEM_OBJECT_MATERIAL in self.prop_objects)

        # handle blender-materials (without mesh's uv texture image)
        if (flagHandleMaterials):
            for blenderMaterial in blender.materials:
                if (blenderMaterial.users <= 0):
                    continue

                ms3dMaterial = self.CreateMaterial(blenderMaterial, None)
                if ms3dMaterial and (ms3dMaterial not in ms3dMaterials):
                    ms3dMaterials.append(ms3dMaterial)

        nLayers = len(blenderContext.scene.layers)
        # handle blender-objects
        for blenderObject in blender.objects:

            # do not handle non-mesh objects or unused objects
            if (blenderObject.type != 'MESH') or (blenderObject.users <= 0):
                continue

            # skip unselected objects in "only selected"-mode
            if (self.prop_selected) and (not blenderObject.select):
                continue

            # skip meshes of invisible layers
            skip = True
            for iLayer in range(nLayers):
                if ((blenderObject.layers[iLayer]
                        and blenderContext.scene.layers[iLayer])):
                    skip = False
                    break
            if (skip):
                continue

            # make new object as active and only selected object
            bpy.context.scene.objects.active = blenderObject

            matrixObject = blenderObject.matrix_basis

            blenderMesh = blenderObject.data

            ms3dGroup = ms3d_spec.ms3d_group_t()
            ms3dGroup.name = blenderObject.name

            # handle blender-vertices
            for blenderVertex in blenderMesh.vertices:
                ms3dVertex = self.CreateVertex(matrixObject, blenderVertex)

                # handle referenceCount and/or
                # put vertex without duplicates
                if (ms3dVertex in ms3dVertices):
                    ms3dVertices[ms3dVertices.index(ms3dVertex)]\
                            .referenceCount += 1
                else:
                    ms3dVertex.referenceCount = 1
                    ms3dVertices.append(ms3dVertex)

            # handle smoothing groups
            smoothGroupFaces = self.GenerateSmoothGroups(
                    blenderContext, ms3dTemplate, blenderMesh.faces)

            # handle blender-faces
            groupIndex = len(ms3dGroups)
            for iFace, blenderFace in enumerate(blenderMesh.faces):
                if (smoothGroupFaces) and (iFace in smoothGroupFaces):
                    smoothingGroup = smoothGroupFaces[iFace]
                else:
                    smoothingGroup = 0

                if (len(blenderFace.vertices) == 4):
                    # 1'st tri of quad
                    ms3dTriangle = self.CreateTriangle(matrixObject,
                            ms3dVertices, blenderMesh, blenderFace,
                            groupIndex, smoothingGroup, 0)
                    # put triangle
                    ms3dTriangles.append(ms3dTriangle)
                    # put triangle index
                    ms3dGroup.triangleIndices.append(
                            ms3dTriangles.index(ms3dTriangle))

                    # 2'nd tri of quad
                    ms3dTriangle = self.CreateTriangle(matrixObject,
                            ms3dVertices, blenderMesh, blenderFace,
                            groupIndex, smoothingGroup, 1)

                else:
                    ms3dTriangle = self.CreateTriangle(matrixObject,
                            ms3dVertices, blenderMesh, blenderFace,
                            groupIndex, smoothingGroup)

                # put triangle
                ms3dTriangles.append(ms3dTriangle)
                # put triangle index
                ms3dGroup.triangleIndices.append(
                        ms3dTriangles.index(ms3dTriangle))

            # handle material (take the first one)
            if (flagHandleMaterials) and (blenderMesh.materials):
                if (blenderMesh.uv_textures):
                    tmpMaterial1 = self.CreateMaterial(
                            blenderMesh.materials[0],
                            blenderMesh.uv_textures[0])
                else:
                    tmpMaterial1 = self.CreateMaterial(
                            blenderMesh.materials[0],
                            None)

                if tmpMaterial1:
                    ms3dGroup.materialIndex = ms3dMaterials.index(tmpMaterial1)

                    # upgrade poor material.texture with rich material.texture
                    tmpMaterial2 = ms3dMaterials[ms3dGroup.materialIndex]
                    if (tmpMaterial1.texture) and (not tmpMaterial2.texture):
                        tmpMaterial2.texture = tmpMaterial1.texture

            # put group
            ms3dGroups.append(ms3dGroup)

        # injecting common data
        ms3dTemplate._vertices = ms3dVertices
        ms3dTemplate._triangles = ms3dTriangles
        ms3dTemplate._groups = ms3dGroups
        ms3dTemplate._materials = ms3dMaterials

        # inject currently unsupported data
        ms3dTemplate._vertex_ex = []
        if (ms3dTemplate.subVersionVertexExtra == 1):
            for i in range(ms3dTemplate.nNumVertices):
                ms3dTemplate.vertex_ex.append(ms3d_spec.ms3d_vertex_ex1_t())
        elif (ms3dTemplate.subVersionVertexExtra == 2):
            for i in range(ms3dTemplate.nNumVertices):
                ms3dTemplate.vertex_ex.append(ms3d_spec.ms3d_vertex_ex2_t())
        elif (ms3dTemplate.subVersionVertexExtra == 3):
            for i in range(ms3dTemplate.nNumVertices):
                ms3dTemplate.vertex_ex.append(ms3d_spec.ms3d_vertex_ex3_t())
        else:
            pass

        if (self.prop_verbose):
            ms3dTemplate.print_internal()

        isValid, statistics = ms3dTemplate.isValid()
        print()
        print("##############################################################")
        print("Blender -> MS3D : [{0}]".format(self.filepath_splitted[1]))
        print(statistics)
        print("##############################################################")


    ###########################################################################
    def CreateMaterial(self, blenderMaterial, blenderUvLayer):
        if (not blenderMaterial):
            return None

        ms3dMaterial = ms3d_spec.ms3d_material_t()

        ms3dMaterial.name = blenderMaterial.name

        ms3dMaterial._ambient = (
                blenderMaterial.diffuse_color[0],
                blenderMaterial.diffuse_color[1],
                blenderMaterial.diffuse_color[2],
                blenderMaterial.ambient
                )

        ms3dMaterial._diffuse = (
                blenderMaterial.diffuse_color[0],
                blenderMaterial.diffuse_color[1],
                blenderMaterial.diffuse_color[2],
                blenderMaterial.diffuse_intensity
                )

        ms3dMaterial._specular = (
                blenderMaterial.specular_color[0],
                blenderMaterial.specular_color[1],
                blenderMaterial.specular_color[2],
                blenderMaterial.specular_intensity
                )

        ms3dMaterial._emissive = (
                blenderMaterial.diffuse_color[0],
                blenderMaterial.diffuse_color[1],
                blenderMaterial.diffuse_color[2],
                blenderMaterial.emit
                )

        ms3dMaterial.shininess = blenderMaterial.specular_hardness / 2.0
        if ms3dMaterial.shininess > 128:
            ms3dMaterial.shininess = 128
        if ms3dMaterial.shininess < 1:
            ms3dMaterial.shininess = 1

        if (blenderMaterial.use_transparency):
            ms3dMaterial.transparency = blenderMaterial.alpha

        if (blenderMaterial.texture_slots):
            imageDiffuse = None
            imageAlpha = None

            for blenderTextureSlot in blenderMaterial.texture_slots:
                if ((not blenderTextureSlot)
                        or (not blenderTextureSlot.texture)
                        or (blenderTextureSlot.texture_coords != 'UV')
                        or (blenderTextureSlot.texture.type != 'IMAGE')
                        ):
                    continue

                if ((not imageDiffuse)
                        and (blenderTextureSlot.use_map_color_diffuse)):
                    if ((blenderTextureSlot.texture.image)
                            and (blenderTextureSlot.texture.image.filepath)):
                        imageDiffuse = os.path.split(
                                blenderTextureSlot.texture.image.filepath)[1]
                    elif (not blenderTextureSlot.texture.image):
                        # case it image was not loaded
                        imageDiffuse = os.path.split(
                                blenderTextureSlot.texture.name)[1]

                elif ((not imageAlpha)
                        and (blenderTextureSlot.use_map_color_alpha)):
                    if ((blenderTextureSlot.texture.image)
                            and (blenderTextureSlot.texture.image.filepath)):
                        imageAlpha = os.path.split(
                                blenderTextureSlot.texture.image.filepath)[1]
                    elif (not blenderTextureSlot.texture.image):
                        # case it image was not loaded
                        imageAlpha = os.path.split(
                                blenderTextureSlot.texture.name)[1]

            # if no diffuse image was found, try to find a uv texture image
            if (not imageDiffuse) and (blenderUvLayer):
                for blenderTextureFace in blenderUvLayer.data:
                    if ((blenderTextureFace) and (blenderTextureFace.image)
                            and (blenderTextureFace.image.filepath)):
                        imageDiffuse = os.path.split(
                                blenderTextureFace.image.filepath)[1]
                        break

            if (imageDiffuse):
                ms3dMaterial.texture = imageDiffuse

            if (imageAlpha):
                ms3dMaterial.alphamap = imageDiffuse

        return ms3dMaterial


    ###########################################################################
    def CreateNormal(self,  matrixObject, blenderVertex):
        mathVector = mathutils.Vector(blenderVertex.normal)

        # apply its object matrix (translation, rotation, scale)
        mathVector = (matrixObject * mathVector)

        # apply export swap axis matrix
        mathVector = mathVector * self.matrixSwapAxis

        ms3dNormal = tuple(mathVector)

        return ms3dNormal


    ###########################################################################
    def CreateTriangle(self, matrixObject, ms3dVertices,
            blenderMesh, blenderFace,
            groupIndex=0, smoothingGroup=None, subIndex=0):
        """
        known limitations:
            - it will take only the first uv_texture-data,
              if one or more are present
        """
        ms3dTriangle = ms3d_spec.ms3d_triangle_t()

        ms3dTriangle.groupIndex = groupIndex

        if (smoothingGroup) and (smoothingGroup > 0):
            ms3dTriangle.smoothingGroup = \
                    (smoothingGroup % ms3d_spec.MAX_GROUPS) + 1

        if (blenderFace.select):
            ms3dTriangle.flags |= ms3d_spec.FLAG_SELECTED

        if (blenderFace.hide):
            ms3dTriangle.flags |= ms3d_spec.FLAG_HIDDEN

        tx = None
        l = len(blenderFace.vertices)

        if (l == 3):
            # it is already a triangle geometry
            if (subIndex != 0):
                return None

            # no order-translation needed
            tx = (0, 1, 2)

        elif (l == 4):
            # it is a quad geometry
            if (subIndex > 1) or (subIndex < 0):
                return None

            if (subIndex == 0):
                # order-translation for 1'st triangle
                tx = (0, 1, 3)
            else:
                # order-translation for 2'nd triangle
                tx = (3, 1, 2)

        else:
            # it is any unhandled geometry
            return None

        # take blender-vertex from blender-mesh
        # to get its vertex and normal coordinates
        v = blenderMesh.vertices[blenderFace.vertices_raw[tx[0]]]
        v0 = self.CreateVertex(matrixObject, v)
        n0 = self.CreateNormal(matrixObject, v)

        # take blender-vertex from blender-mesh
        # to get its vertex and normal coordinates
        v = blenderMesh.vertices[blenderFace.vertices_raw[tx[1]]]
        v1 = self.CreateVertex(matrixObject, v)
        n1 = self.CreateNormal(matrixObject, v)

        # take blender-vertex from blender-mesh
        # to get its vertex and normal coordinates
        v = blenderMesh.vertices[blenderFace.vertices_raw[tx[2]]]
        v2 = self.CreateVertex(matrixObject, v)
        n2 = self.CreateNormal(matrixObject, v)

        # put the indices of ms3d-vertices!
        ms3dTriangle._vertexIndices = (
                ms3dVertices.index(v0),
                ms3dVertices.index(v1),
                ms3dVertices.index(v2)
                )

        # put the normales
        ms3dTriangle._vertexNormals = (n0, n1, n2)

        # if uv's present
        if (blenderMesh.uv_textures):
            # take 1'st uv_texture-data
            blenderUv = \
                    blenderMesh.uv_textures[0].data[blenderFace.index].uv_raw

            # translate uv to st
            #
            # blender uw
            # y(v)
            # |(0,1)  (1,1)
            # |
            # |
            # |(0,0)  (1,0)
            # +--------x(u)
            #
            # ms3d st
            # +--------x(s)
            # |(0,0)  (1,0)
            # |
            # |
            # |(0,1)  (1,1)
            # y(t)
            s0, t0 = blenderUv[tx[0] << 1], 1.0 - blenderUv[(tx[0] << 1) + 1]
            s1, t1 = blenderUv[tx[1] << 1], 1.0 - blenderUv[(tx[1] << 1) + 1]
            s2, t2 = blenderUv[tx[2] << 1], 1.0 - blenderUv[(tx[2] << 1) + 1]

            # put the uv-coordinates
            ms3dTriangle._s = (s0, s1, s2)
            ms3dTriangle._t = (t0, t1, t2)

        return ms3dTriangle


    ###########################################################################
    def CreateVertex(self,  matrixObject, blenderVertex):
        """ known limitations:
            - boneId not supported """
        ms3dVertex = ms3d_spec.ms3d_vertex_t()

        if (blenderVertex.select):
            ms3dVertex.flags |= ms3d_spec.FLAG_SELECTED

        if (blenderVertex.hide):
            ms3dVertex.flags |= ms3d_spec.FLAG_HIDDEN

        mathVector = mathutils.Vector(blenderVertex.co)

        # apply its object matrix (translation, rotation, scale)
        mathVector = (matrixObject * mathVector)

        # apply export viewport matrix
        mathVector = mathVector * self.matrixViewport

        ms3dVertex._vertex = tuple(mathVector)

        return ms3dVertex


    ###########################################################################
    def GenerateSmoothGroups(self, blenderContext, ms3dTemplate, blenderFaces):
        ms3d_utils.EnableEditMode(True)

        # enable face-selection-mode
        bpy.context.tool_settings.mesh_select_mode = [False, False, True]

        # deselect all "faces"
        ms3d_utils.SelectAll(False) # mesh

        # enable object-mode (important for face.select = value)
        ms3d_utils.EnableEditMode(False)

        handledFacesSet = set()
        smoothGroupVertices = {}

        blenderVertices = blenderContext.active_object.data.vertices

        # run throug the faces
        # mark linked faces and set its smoothGroup value
        nFaces = len(blenderFaces)

        for iFace in range(nFaces):
            if (blenderFaces[iFace].select) or (iFace in handledFacesSet):
                continue

            # a new unhandled face found
            blenderFaces[iFace].select = True

            ms3d_utils.EnableEditMode(True)

            if bpy.ops.mesh.select_linked.poll():
                bpy.ops.mesh.select_linked()

            ms3d_utils.EnableEditMode(False)

            # build a set of vertices hashes
            currentFaceSet = set()
            currentVertexSet = set()
            for iiFace in range(nFaces):
                if ((blenderFaces[iiFace].select)
                        and (iiFace not in handledFacesSet)):
                    handledFacesSet.add(iiFace)
                    currentFaceSet.add(iiFace)

                    iVertex = blenderFaces[iiFace].vertices[0]
                    mathVector = blenderVertices[iVertex].co
                    currentVertexSet.add(
                            hash(mathVector[0])
                            ^ hash(mathVector[1])
                            ^ hash(mathVector[2]))

                    iVertex = blenderFaces[iiFace].vertices[1]
                    mathVector = blenderVertices[iVertex].co
                    currentVertexSet.add(
                            hash(mathVector[0])
                            ^ hash(mathVector[1])
                            ^ hash(mathVector[2]))

                    iVertex = blenderFaces[iiFace].vertices[2]
                    mathVector = blenderVertices[iVertex].co
                    currentVertexSet.add(
                            hash(mathVector[0])
                            ^ hash(mathVector[1])
                            ^ hash(mathVector[2]))

                    if(len(blenderFaces[iiFace].vertices) == 4):
                        iVertex = blenderFaces[iiFace].vertices[3]
                        mathVector = blenderVertices[iVertex].co
                        currentVertexSet.add(
                                hash(mathVector[0])
                                ^ hash(mathVector[1])
                                ^ hash(mathVector[2]))

            # search for collision set
            reused_smoothgroup = False
            for iSmoothGroup in smoothGroupVertices:
                smoothVertexSet = smoothGroupVertices[iSmoothGroup][1]
                intersectionVertexSet = currentVertexSet & smoothVertexSet
                if(len(intersectionVertexSet) == 0):
                    # no shared vertices, you can use that smoothgroup without collision
                    item = smoothGroupVertices[iSmoothGroup]
                    item[0] |= currentFaceSet
                    item[1] |= currentVertexSet
                    reused_smoothgroup = True
                    break

            if not reused_smoothgroup:
                smoothGroupVertices[len(smoothGroupVertices)] = [currentFaceSet, currentVertexSet]

        # put result to a smoothGroupFaces dictionary
        smoothGroupFaces = {}
        for iSmoothGroup in smoothGroupVertices:
            for iFace in smoothGroupVertices[iSmoothGroup][0]:
                smoothGroupFaces[iFace] = iSmoothGroup

        return smoothGroupFaces


###############################################################################
#234567890123456789012345678901234567890123456789012345678901234567890123456789
#--------1---------2---------3---------4---------5---------6---------7---------
# ##### END OF FILE #####
