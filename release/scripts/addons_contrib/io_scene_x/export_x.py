# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation, either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#  All rights reserved.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

from math import radians

import bpy
from mathutils import *


class DirectXExporter:
    def __init__(self, Config, context):
        self.Config = Config
        self.context = context

        self.File = File(self.Config.filepath)

        self.Log("Setting up coordinate system...")
        # SystemMatrix converts from right-handed, z-up to left-handed, y-up
        self.SystemMatrix = (Matrix.Scale(-1, 4, Vector((0, 0, 1))) *
            Matrix.Rotation(radians(-90), 4, 'X'))
        self.Log("Done")

        self.Log("Generating object lists for export...")
        if self.Config.SelectedOnly:
            ExportList = list(self.context.selected_objects)
        else:
            ExportList = list(self.context.scene.objects)

        # ExportMap maps Blender objects to ExportObjects
        self.ExportMap = {} # XXX Do we keep ExportMap around in self?  Or should it be local?
        for Object in ExportList:
            if Object.type == 'EMPTY':
                self.ExportMap[Object] = ExportObject(self.Config, self, Object)
            elif Object.type == 'MESH':
                self.ExportMap[Object] = MeshExportObject(self.Config, self,
                    Object)
            elif Object.type == 'ARMATURE':
                self.ExportMap[Object] = ArmatureExportObject(self.Config, self,
                    Object)

        # Find the objects who do not have a parent or whose parent we are
        # not exporting
        self.RootExportList = [Object for Object in self.ExportMap.values()
            if Object.BlenderObject.parent not in ExportList]
        self.RootExportList = Util.SortByNameField(self.RootExportList)

        # Determine each object's children from the pool of ExportObjects
        for Object in self.ExportMap.values():
            Children = Object.BlenderObject.children
            Object.Children = []
            for Child in Children:
                if Child in self.ExportMap:
                    Object.Children.append(self.ExportMap[Child])
        self.Log("Done")

    # "Public" Interface

    def Export(self):
        self.Log("Exporting to {}".format(self.File.FilePath),
            MessageVerbose=False)

        self.Log("Opening file...")
        self.File.Open()
        self.Log("Done")

        self.Log("Writing header...")
        self.__WriteHeader()
        self.Log("Done")

        self.Log("Opening Root frame...")
        self.__OpenRootFrame()
        self.Log("Done")

        self.Log("Writing objects...")
        for Object in self.RootExportList:
            Object.Write()
        self.Log("Done")

        self.Log("Closing Root frame...")
        self.__CloseRootFrame()
        self.Log("Done")

        self.File.Close()

    def Log(self, String, MessageVerbose=True):
        if self.Config.Verbose is True or MessageVerbose == False:
            print(String)

    # "Private" Methods

    def __WriteHeader(self):
        self.File.Write("xof 0303txt 0032\n\n")

        if self.Config.IncludeFrameRate:
            self.File.Write("template AnimTicksPerSecond {\n\
  <9E415A43-7BA6-4a73-8743-B73D47E88476>\n\
  DWORD AnimTicksPerSecond;\n\
}\n\n")
        if self.Config.ExportSkinWeights:
            self.File.Write("template XSkinMeshHeader {\n\
  <3cf169ce-ff7c-44ab-93c0-f78f62d172e2>\n\
  WORD nMaxSkinWeightsPerVertex;\n\
  WORD nMaxSkinWeightsPerFace;\n\
  WORD nBones;\n\
}\n\n\
template SkinWeights {\n\
  <6f0d123b-bad2-4167-a0d0-80224f25fabb>\n\
  STRING transformNodeName;\n\
  DWORD nWeights;\n\
  array DWORD vertexIndices[nWeights];\n\
  array float weights[nWeights];\n\
  Matrix4x4 matrixOffset;\n\
}\n\n")

    # Start the Root frame and write its transform matrix
    def __OpenRootFrame(self):
        self.File.Write("Frame Root {\n")
        self.File.Indent()

        self.File.Write("FrameTransformMatrix {\n")
        self.File.Indent()
        Util.WriteMatrix(self.File, self.SystemMatrix)
        self.File.Unindent()
        self.File.Write("}\n")

    def __CloseRootFrame(self):
        self.File.Unindent()
        self.File.Write("} // End of Root\n")


class ExportObject:
    def __init__(self, Config, Exporter, BlenderObject):
        self.Config = Config
        self.Exporter = Exporter
        self.BlenderObject = BlenderObject

        self.name = self.BlenderObject.name # Simple alias
        self.SafeName = Util.SafeName(self.BlenderObject.name)
        self.Children = []

    def __repr__(self):
        return "[ExportObject: {}]".format(self.BlenderObject.name)

    # "Public" Interface

    def Write(self):
        self._OpenFrame()

        self._WriteChildren()

        self._CloseFrame()

    # "Protected" Interface

    def _OpenFrame(self):
        self.Exporter.File.Write("Frame {} {{\n".format(self.SafeName))
        self.Exporter.File.Indent()

        self.Exporter.File.Write("FrameTransformMatrix {\n")
        self.Exporter.File.Indent()
        Util.WriteMatrix(self.Exporter.File, self.BlenderObject.matrix_local)
        self.Exporter.File.Unindent()
        self.Exporter.File.Write("}\n")

    def _CloseFrame(self):
        self.Exporter.File.Unindent()
        self.Exporter.File.Write("}} // End of {}\n".format(self.SafeName))

    def _WriteChildren(self):
        for Child in Util.SortByNameField(self.Children):
            Child.Write()


class MeshExportObject(ExportObject):
    def __init__(self, Config, Exporter, BlenderObject):
        ExportObject.__init__(self, Config, Exporter, BlenderObject)

    def __repr__(self):
        return "[MeshExportObject: {}]".format(self.BlenderObject.name)

    # "Public" Interface

    def Write(self):
        self._OpenFrame()

        if self.Exporter.Config.ExportMeshes:
            # Generate the export mesh
            Mesh = None
            if self.Config.ApplyModifiers:
                Mesh = self.BlenderObject.to_mesh(self.Exporter.context.scene,
                    True, 'PREVIEW')
            else:
                Mesh = self.BlenderObject.to_mesh(self.Exporter.context.scene,
                    False, 'PREVIEW')
                    
            self.__WriteMesh(Mesh)

        self._WriteChildren()

        self._CloseFrame()

    # "Private" Methods

    def __WriteMesh(self, Mesh):
        self.Exporter.File.Write("Mesh {{ // {} mesh\n".format(self.SafeName))
        self.Exporter.File.Indent()

        if (self.Exporter.Config.ExportUVCoordinates and Mesh.uv_textures):# or \
           #self.Exporter.Config.ExportVertexColors: XXX
            VertexCount = 0
            for Polygon in Mesh.polygons:
                VertexCount += len(Polygon.vertices)
            
            # Write vertex positions
            Index = 0
            self.Exporter.File.Write("{};\n".format(VertexCount))
            for Polygon in Mesh.polygons:
                Vertices = list(Polygon.vertices)[::-1]
                
                for Vertex in [Mesh.vertices[Vertex] for Vertex in Vertices]:
                    Position = Vertex.co
                    self.Exporter.File.Write("{:9f};{:9f};{:9f};".format(
                        Position[0], Position[1], Position[2]))
                    Index += 1
                    if Index == VertexCount:
                        self.Exporter.File.Write(";\n", Indent=False)
                    else:
                        self.Exporter.File.Write(",\n", Indent=False)
            
            # Write face definitions
            Index = 0
            self.Exporter.File.Write("{};\n".format(len(Mesh.polygons)))
            for Polygon in Mesh.polygons:
                self.Exporter.File.Write("{};".format(len(Polygon.vertices)))
                for Vertex in Polygon.vertices:
                    self.Exporter.File.Write("{};".format(Index), Indent=False)
                    Index += 1
                if Index == VertexCount:
                    self.Exporter.File.Write(";\n", Indent=False)
                else:
                    self.Exporter.File.Write(",\n", Indent=False)
        else:
            # Write vertex positions
            self.Exporter.File.Write("{};\n".format(len(Mesh.vertices)))
            for Index, Vertex in enumerate(Mesh.vertices):
                Position = Vertex.co
                self.Exporter.File.Write("{:9f};{:9f};{:9f};".format(
                    Position[0], Position[1], Position[2]))
                if Index == len(Mesh.vertices) - 1:
                    self.Exporter.File.Write(";\n", Indent=False)
                else:
                    self.Exporter.File.Write(",\n", Indent=False)
    
            # Write face definitions
            self.Exporter.File.Write("{};\n".format(len(Mesh.polygons)))
            for Index, Polygon in enumerate(Mesh.polygons):
                # Change the winding order of the face
                Vertices = list(Polygon.vertices)[::-1]
    
                self.Exporter.File.Write("{};".format(len(Vertices)))
                for Vertex in Vertices:
                    self.Exporter.File.Write("{};".format(Vertex), Indent=False)
                if Index == len(Mesh.polygons) - 1:
                    self.Exporter.File.Write(";\n", Indent=False)
                else:
                    self.Exporter.File.Write(",\n", Indent=False)

        if self.Exporter.Config.ExportNormals:
            self.__WriteMeshNormals(Mesh)
            
        if self.Exporter.Config.ExportUVCoordinates:
            self.__WriteMeshUVCoordinates(Mesh)

        if self.Exporter.Config.ExportMaterials:
            self.__WriteMeshMaterials(Mesh)
        
        #if self.Exporter.Config.ExportVertexColor:
        #    self.__WriteMeshVertexColors(Mesh)

        self.Exporter.File.Unindent()
        self.Exporter.File.Write("}} // End of {} mesh\n".format(self.SafeName))

    def __WriteMeshNormals(self, Mesh):
        self.Exporter.File.Write("MeshNormals {{ // {} normals\n".format(
            self.SafeName))
        self.Exporter.File.Indent()

        # Determine the number of normals to write
        NormalCount = 0
        for Polygon in Mesh.polygons:
            if Polygon.use_smooth:
                NormalCount += len(Polygon.vertices)
            else:
                NormalCount += 1

        # Write mesh normals
        self.Exporter.File.Write("{};\n".format(NormalCount))
        NormalIndex = 0
        for Polygon in Mesh.polygons:
            # If the face is faceted, write the face normal only once
            if not Polygon.use_smooth:
                Normal = Polygon.normal
                self.Exporter.File.Write("{:9f};{:9f};{:9f};".format(Normal[0],
                    Normal[1], Normal[2]))
                NormalIndex += 1
                if NormalIndex < NormalCount:
                    self.Exporter.File.Write(",\n", Indent=False)
            # Otherwise, write each vertex normal
            else:
                # Change the winding order of the face
                VertexNormals = [Mesh.vertices[Vertex].normal for Vertex in
                    Polygon.vertices][::-1]
                for Normal in VertexNormals:
                    self.Exporter.File.Write("{:9f};{:9f};{:9f};".format(
                        Normal[0], Normal[1], Normal[2]))
                    NormalIndex += 1
                    if NormalIndex < NormalCount:
                        self.Exporter.File.Write(",\n", Indent=False)
        self.Exporter.File.Write(";\n", Indent=False)

        # Write face definitions
        self.Exporter.File.Write("{};\n".format(len(Mesh.polygons)))
        NormalIndex = 0
        for Polygon in Mesh.polygons:
            VertexCount = len(Polygon.vertices)
            self.Exporter.File.Write("{};".format(VertexCount))
            # If the face is faceted, use the normal at Index for each vertex
            if not Polygon.use_smooth:
                VertexIndices = [NormalIndex] * VertexCount
                NormalIndex += 1
            # Otherwise, use the next couple normals for the face
            else:
                VertexIndices = list(range(NormalIndex,
                    NormalIndex + VertexCount))
                NormalIndex += VertexCount
            # Write the indices for the face
            for VertexIndex in VertexIndices:
                self.Exporter.File.Write("{};".format(VertexIndex),
                    Indent=False)
            if NormalIndex == NormalCount:
                self.Exporter.File.Write(";\n", Indent=False)
            else:
                self.Exporter.File.Write(",\n", Indent=False)

        self.Exporter.File.Unindent()
        self.Exporter.File.Write("}} // End of {} normals\n".format(
            self.SafeName))
     
    def __WriteMeshUVCoordinates(self, Mesh):
        if not Mesh.uv_textures:
            return
        
        self.Exporter.File.Write("MeshTextureCoords {{ // {} UV coordinates\n".
            format(self.SafeName))
        self.Exporter.File.Indent()
        
        UVCoordinates = Mesh.uv_layers.active.data
        
        VertexCount = 0
        for Polygon in Mesh.polygons:
            VertexCount += len(Polygon.vertices)
        
        Index = 0
        self.Exporter.File.Write("{};\n".format(VertexCount))
        for Polygon in Mesh.polygons:
            Vertices = []
            for Vertex in [UVCoordinates[Vertex] for Vertex in
                Polygon.loop_indices]:
                Vertices.append(tuple(Vertex.uv))
            for Vertex in Vertices:
                self.Exporter.File.Write("{:9f};{:9f};".format(Vertex[0],
                    Vertex[1]))
                Index += 1
                if Index == VertexCount:
                    self.Exporter.File.Write(";\n", Indent=False)
                else:
                    self.Exporter.File.Write(",\n", Indent=False)
                    
        self.Exporter.File.Unindent()
        self.Exporter.File.Write("}} // End of {} UV coordinates\n".format(
            self.SafeName))

    def __WriteMeshMaterials(self, Mesh):
        def WriteMaterial(Exporter, Material):
            def GetMaterialTextureFileName(Material):
                if Material:
                    # Create a list of Textures that have type 'IMAGE'
                    ImageTextures = [Material.texture_slots[TextureSlot].texture
                        for TextureSlot in Material.texture_slots.keys()
                        if Material.texture_slots[TextureSlot].texture.type ==
                        'IMAGE']
                    # Refine to only image file names if applicable
                    ImageFiles = [bpy.path.basename(Texture.image.filepath)
                        for Texture in ImageTextures
                        if getattr(Texture.image, "source", "") == 'FILE']
                    if ImageFiles:
                        return ImageFiles[0]
                return None
            
            Exporter.File.Write("Material {} {{\n".format(
                Util.SafeName(Material.name)))
            Exporter.File.Indent()
            
            Diffuse = list(Vector(Material.diffuse_color) *
                Material.diffuse_intensity)
            Diffuse.append(Material.alpha)
            # Map Blender's range of 1 - 511 to 0 - 1000
            Specularity = 1000 * (Material.specular_hardness - 1.0) / 510.0
            Specular = list(Vector(Material.specular_color) *
                Material.specular_intensity)
            
            Exporter.File.Write("{:9f};{:9f};{:9f};{:9f};;\n".format(Diffuse[0],
                Diffuse[1], Diffuse[2], Diffuse[3]))
            Exporter.File.Write(" {:9f};\n".format(Specularity))
            Exporter.File.Write("{:9f};{:9f};{:9f};;\n".format(Specular[0],
                Specular[1], Specular[2]))
            Exporter.File.Write(" 0.000000; 0.000000; 0.000000;;\n")
            
            TextureFileName = GetMaterialTextureFileName(Material)
            if TextureFileName:
                Exporter.File.Write("TextureFilename {{\"{}\";}}\n".format(
                    TextureFileName))
            
            Exporter.File.Unindent()
            Exporter.File.Write("}\n");
        
        Materials = Mesh.materials
        # Do not write materials if there are none
        if not Materials.keys():
            return
        
        self.Exporter.File.Write("MeshMaterialList {{ // {} material list\n".
            format(self.SafeName))
        self.Exporter.File.Indent()
        
        self.Exporter.File.Write("{};\n".format(len(Materials)))
        self.Exporter.File.Write("{};\n".format(len(Mesh.polygons)))
        for Index, Polygon in enumerate(Mesh.polygons):
            self.Exporter.File.Write("{}".format(Polygon.material_index))
            if Index == len(Mesh.polygons) - 1:
                self.Exporter.File.Write(";;\n", Indent=False)
            else:
                self.Exporter.File.Write(",\n", Indent=False)
        
        for Material in Materials:
            WriteMaterial(self.Exporter, Material)
        
        self.Exporter.File.Unindent()
        self.Exporter.File.Write("}} // End of {} material list\n".format(
            self.SafeName))
    
    def __WriteMeshVertexColors(self, Mesh):
        pass
    
    def __WriteMeshSkinWeights(self, Mesh):
        ArmatureModifierList = [Modifier for Modifier in Object.modifiers
            if Modifier.type == 'ARMATURE']
        
        if not ArmatureModifierList:
            return
        
        pass


class ArmatureExportObject(ExportObject):
    def __init__(self, Config, Exporter, BlenderObject):
        ExportObject.__init__(self, Config, Exporter, BlenderObject)

    def __repr__(self):
        return "[ArmatureExportObject: {}]".format(self.BlenderObject.name)
    
    # "Public" Interface

    def Write(self):
        self._OpenFrame()
        
        if self.Config.ExportArmatureBones:
            Armature = self.BlenderObject.data
            RootBones = [Bone for Bone in Armature.bones if Bone.parent is None]
            self.__WriteBones(RootBones)

        self._WriteChildren()

        self._CloseFrame()
    
    # "Private" Methods
    
    def __WriteBones(self, Bones):
        for Bone in Bones:
            BoneMatrix = Matrix()
            
            PoseBone = self.BlenderObject.pose.bones[Bone.name]
            if Bone.parent:
                BoneMatrix = PoseBone.parent.matrix.inverted()
            BoneMatrix *= PoseBone.matrix
            
            BoneSafeName = Util.SafeName(Bone.name)
            self.__OpenBoneFrame(BoneSafeName, BoneMatrix)
            
            self.__WriteBoneChildren(Bone)
            
            self.__CloseBoneFrame(BoneSafeName)
            
    
    def __OpenBoneFrame(self, BoneSafeName, BoneMatrix):
        self.Exporter.File.Write("Frame {} {{\n".format(BoneSafeName))
        self.Exporter.File.Indent()

        self.Exporter.File.Write("FrameTransformMatrix {\n")
        self.Exporter.File.Indent()
        Util.WriteMatrix(self.Exporter.File, BoneMatrix)
        self.Exporter.File.Unindent()
        self.Exporter.File.Write("}\n")
    
    def __CloseBoneFrame(self, BoneSafeName):
        self.Exporter.File.Unindent()
        self.Exporter.File.Write("}} // End of {}\n".format(BoneSafeName))
    
    def __WriteBoneChildren(self, Bone):
        self.__WriteBones(Util.SortByNameField(Bone.children))


class File:
    def __init__(self, FilePath):
        self.FilePath = FilePath
        self.File = None
        self.__Whitespace = 0

    def Open(self):
        if not self.File:
            self.File = open(self.FilePath, 'w')

    def Close(self):
        self.File.close()
        self.File = None

    def Write(self, String, Indent=True):
        if Indent:
            # Escape any formatting braces
            String = String.replace("{", "{{")
            String = String.replace("}", "}}")
            self.File.write(("{}" + String).format("  " * self.__Whitespace))
        else:
            self.File.write(String)

    def Indent(self, Levels=1):
        self.__Whitespace += Levels

    def Unindent(self, Levels=1):
        self.__Whitespace -= Levels
        if self.__Whitespace < 0:
            self.__Whitespace = 0


class Util:
    @staticmethod
    def SafeName(Name):
        # Replaces each character in OldSet with NewChar
        def ReplaceSet(String, OldSet, NewChar):
            for OldChar in OldSet:
                String = String.replace(OldChar, NewChar)
            return String

        import string

        NewName = ReplaceSet(Name, string.punctuation + " ", "_")
        if NewName[0].isdigit() or NewName in ["ARRAY", "DWORD", "UCHAR",
            "FLOAT", "ULONGLONG", "BINARY_RESOURCE", "SDWORD", "UNICODE",
            "CHAR", "STRING", "WORD", "CSTRING", "SWORD", "DOUBLE", "TEMPLATE"]:
            NewName = "_" + NewName
        return NewName

    @staticmethod
    def WriteMatrix(File, Matrix):
        File.Write("{:9f},{:9f},{:9f},{:9f},\n".format(Matrix[0][0],
            Matrix[1][0], Matrix[2][0], Matrix[3][0]))
        File.Write("{:9f},{:9f},{:9f},{:9f},\n".format(Matrix[0][1],
            Matrix[1][1], Matrix[2][1], Matrix[3][1]))
        File.Write("{:9f},{:9f},{:9f},{:9f},\n".format(Matrix[0][2],
            Matrix[1][2], Matrix[2][2], Matrix[3][2]))
        File.Write("{:9f},{:9f},{:9f},{:9f};;\n".format(Matrix[0][3],
            Matrix[1][3], Matrix[2][3], Matrix[3][3]))
    
    @staticmethod
    def SortByNameField(List):
        def SortKey(x):
            return x.name
        
        return sorted(List, key=SortKey)
