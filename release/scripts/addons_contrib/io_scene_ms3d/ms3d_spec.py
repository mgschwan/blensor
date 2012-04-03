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
import collections
import io
import struct
import sys


#import blender stuff
import bpy_extras.io_utils


PROP_NAME_NAME = "name"
PROP_NAME_MODE = "mode"
PROP_NAME_TEXTURE = "texture"
PROP_NAME_ALPHAMAP = "alphamap"
PROP_NAME_FLAGS = "flags"
PROP_NAME_PARENTNAME = "parentName"
PROP_NAME_EXTRA = "extra"
PROP_NAME_COMMENT = "comment"
PROP_NAME_AMBIENT = "ambient"
PROP_NAME_EMISSIVE = "emissive"
PROP_NAME_COLOR = "color"

#
#
#
# MilkShape 3D 1.8.5 File Format Specification
#
#
# This specifcation is written in Python 3.1 style. (C was original)
#
#
# The data structures are defined in the order as they appear
# in the .ms3d file.
#
#
#
#
#


###############################################################################
#
# max values
#
MAX_VERTICES = 65534 # 0..65533; note: (65534???, 65535???)
MAX_TRIANGLES = 65534 # 0..65533; note: (65534???, 65535???)
MAX_GROUPS = 255 # 1..255; note: (0 default group)
MAX_MATERIALS = 128 # 0..127; note: (-1 no material)
MAX_JOINTS = 128 # 0..127; note: (-1 no joint)
MAX_SMOOTH_GROUP = 32 # 0..32; note: (0 no smoothing group)


###############################################################################
#
# flags
#
FLAG_NONE = 0
FLAG_SELECTED = 1
FLAG_HIDDEN = 2
FLAG_SELECTED2 = 4
FLAG_DIRTY = 8


###############################################################################
#
# values
#
HEADER = "MS3D000000"

###############################################################################
#
# sizes
#
SIZE_BYTE = 1
SIZE_CHAR = 1
SIZE_WORD = 2
SIZE_DWORD = 4
SIZE_FLOAT = 4


LENGTH_ID = 10
LENGTH_NAME = 32
LENGTH_FILENAME = 128


###############################################################################
def read_byte(file):
    """ read a single byte from file """
    value = struct.unpack("<B", file.read(SIZE_BYTE))[0]
    return value

def write_byte(file, value):
    """ write a single byte to file """
    file.write(struct.pack("<B", value))

###############################################################################
def read_char(file):
    """ read a single char (signed byte) from file """
    value = struct.unpack("<b", file.read(SIZE_CHAR))[0]
    return value

def write_char(file, value):
    """ write a single char (signed byte) to file """
    file.write(struct.pack("<b", value))

###############################################################################
def read_word(file):
    """ read a single word from file """
    value = struct.unpack("<H", file.read(SIZE_WORD))[0]
    return value

def write_word(file, value):
    """ write a single word to file """
    file.write(struct.pack("<H", value))

###############################################################################
def read_dword(file):
    """ read a single double word from file """
    value = struct.unpack("<I", file.read(SIZE_DWORD))[0]
    return value

def write_dword(file, value):
    """ write a single double word to file """
    file.write(struct.pack("<I", value))

###############################################################################
def read_float(file):
    """ read a single float from file """
    value = struct.unpack("<f", file.read(SIZE_FLOAT))[0]
    return value

def write_float(file, value):
    """ write a single float to file """
    file.write(struct.pack("<f", value))

###############################################################################
def read_array(file, itemReader, count):
    """ read an array[count] of objects from file, by using a itemReader """
    value = []
    for i in range(count):
        itemValue = itemReader(file)
        value.append(itemValue)
    return tuple(value)

###############################################################################
def write_array(file, itemWriter, count, value):
    """ write an array[count] of objects to file, by using a itemWriter """
    for i in range(count):
        itemValue = value[i]
        itemWriter(file, itemValue)

###############################################################################
def read_array2(file, itemReader, count, count2):
    """ read an array[count][count2] of objects from file,
        by using a itemReader """
    value = []
    for i in range(count):
        itemValue = read_array(file, itemReader, count2)
        value.append(tuple(itemValue))
    return value #tuple(value)

###############################################################################
def write_array2(file, itemWriter, count, count2, value):
    """ write an array[count][count2] of objects to file,
        by using a itemWriter """
    for i in range(count):
        itemValue = value[i]
        write_array(file, itemWriter, count2, itemValue)

###############################################################################
def read_string(file, length):
    """ read a string of a specific length from file """
    value = []
    skip = False
    for i in range(length):
        raw = struct.unpack("<b", file.read(SIZE_CHAR))[0]
        if (raw >= 32) & (raw <= 255):
            pass
        else:
            if (raw == 0):
                raw = 0
                skip = True
            else:
                raw = 32

        c = chr(raw)

        if (not skip):
            value.append(c)

    finalValue = "".join(value)
    return finalValue

###############################################################################
def write_string(file, length, value):
    """ write a string of a specific length to file """
    l = len(value)
    for i in range(length):
        if(i < l):
            c = value[i]

            if (isinstance(c, str)):
                c = c[0]
                raw = ord(c)
            elif (isinstance(c, int)):
                raw = c
            else:
                pass
        else:
            raw = 0

        file.write(struct.pack("<b", raw % 255))


###############################################################################
#
# multi complex types
#
###############################################################################
class ms3d_header_t:
    """
    ms3d_header_t
    """
    #char id[LENGTH_ID]; // always "MS3D000000"
    #int version; // 4
    __slots__ = (
            "id",
            "version"
            )

    def __init__(
            self,
            defaultId=HEADER,
            defaultVersion=4
            ):
        """
        initialize

        :arg id: magic number of file
        :type id: :class:`string`
        :arg version: version number of file
        :type version: :class:`dword`
        """

        self.id = defaultId
        self.version = defaultVersion

    def __repr__(self):
        return "\n<id='{0}', version={1}>".format(
            self.id,
            self.version
            )

    def __hash__(self):
        return hash(self.id) ^ hash(self.version)

    def __eq__(self, other):
        return ((self is not None) and (other is not None)
                and (self.id == other.id)
                and (self.version == other.version))

    def read(self, file):
        self.id = read_string(file, LENGTH_ID)
        self.version = read_dword(file)
        return self

    def write(self, file):
        write_string(file, LENGTH_ID, self.id)
        write_dword(file, self.version)


###############################################################################
class ms3d_vertex_t:
    """
    ms3d_vertex_t
    """
    #byte flags; // FLAG_NONE | FLAG_SELECTED | FLAG_SELECTED2 | FLAG_HIDDEN
    #float vertex[3];
    #char boneId; // -1 = no bone
    #byte referenceCount;
    __slots__ = (
            PROP_NAME_FLAGS,
            "_vertex",
            "boneId",
            "referenceCount",
            )

    def __init__(
            self,
            defaultFlags=FLAG_NONE,
            defaultVertex=(0.0 ,0.0 ,0.0),
            defaultBoneId=-1,
            defaultReferenceCount=0
            ):
        """
        initialize

        :arg flags: selection flag
        :type flags: :class:`byte`
        :arg vertex: vertex
        :type vertex: :class:`float[3]`
        :arg boneId: bone id
        :type boneId: :class:`char`
        :arg referenceCount: reference count
        :type referenceCount: :class:`byte`
        """

        self.flags = defaultFlags
        self._vertex = defaultVertex
        self.boneId = defaultBoneId
        self.referenceCount = defaultReferenceCount
        __hash_cash = None

    def __repr__(self):
        return "\n<flags={0}, vertex={1}, boneId={2},"\
                " referenceCount={3}>".format(
                self.flags,
                self._vertex,
                self.boneId,
                self.referenceCount
                )

    def __hash__(self):
        return (hash(self.vertex)
                #^ hash(self.flags)
                #^ hash(self.boneId)
                #^ hash(self.referenceCount)
                )

    def __eq__(self, other):
        return ((self.vertex == other.vertex)
                #and (self.flags == other.flags)
                #and (self.boneId == other.boneId)
                #and (self.referenceCount == other.referenceCount)
                )


    @property
    def vertex(self):
        return self._vertex


    def read(self, file):
        self.flags = read_byte(file)
        self._vertex = read_array(file, read_float, 3)
        self.boneId = read_char(file)
        self.referenceCount = read_byte(file)
        return self

    def write(self, file):
        write_byte(file, self.flags)
        write_array(file, write_float, 3, self.vertex)
        write_char(file, self.boneId)
        write_byte(file, self.referenceCount)


###############################################################################
class ms3d_triangle_t:
    """
    ms3d_triangle_t
    """
    #word flags; // FLAG_NONE | FLAG_SELECTED | FLAG_SELECTED2 | FLAG_HIDDEN
    #word vertexIndices[3];
    #float vertexNormals[3][3];
    #float s[3];
    #float t[3];
    #byte smoothingGroup; // 1 - 32
    #byte groupIndex;
    __slots__ = (
            PROP_NAME_FLAGS,
            "_vertexIndices",
            "_vertexNormals",
            "_s",
            "_t",
            "smoothingGroup",
            "groupIndex"
            )

    def __init__(
            self,
            defaultFlags=FLAG_NONE,
            defaultVertexIndices=(0, 0, 0),
            defaultVertexNormals=(
                    (0.0, 0.0, 0.0),
                    (0.0, 0.0, 0.0),
                    (0.0, 0.0, 0.0)),
            defaultS=(0.0, 0.0, 0.0),
            defaultT=(0.0, 0.0, 0.0),
            defaultSmoothingGroup=1,
            defaultGroupIndex=0
            ):
        """
        initialize

        :arg flags: selection flag
        :type flags: :class:`word`
        :arg vertexIndices: vertex indices
        :type vertexIndices: :class:`word[3]`
        :arg vertexNormals: vertex normales
        :type vertexNormals: :class:`float[3][3]`
        :arg s: s-component
        :type s: :class:`float[3]`
        :arg t: t-component
        :type t: :class:`float[3]`
        :arg smoothingGroup: smooth group
        :type smoothingGroup: :class:`byte`
        :arg groupIndex: group index
        :type groupIndex: :class:`byte`
        """

        self.flags = defaultFlags
        self._vertexIndices = defaultVertexIndices
        self._vertexNormals = defaultVertexNormals
        self._s = defaultS
        self._t = defaultT
        self.smoothingGroup = defaultSmoothingGroup
        self.groupIndex = defaultGroupIndex

    def __repr__(self):
        return "\n<flags={0}, vertexIndices={1}, vertexNormals={2}, s={3},"\
                " t={4}, smoothingGroup={5}, groupIndex={6}>".format(
                self.flags,
                self.vertexIndices,
                self.vertexNormals,
                self.s,
                self.t,
                self.smoothingGroup,
                self.groupIndex
                )


    @property
    def vertexIndices(self):
        return self._vertexIndices

    @property
    def vertexNormals(self):
        return self._vertexNormals

    @property
    def s(self):
        return self._s

    @property
    def t(self):
        return self._t


    def read(self, file):
        self.flags = read_word(file)
        self._vertexIndices = read_array(file, read_word, 3)
        self._vertexNormals = read_array2(file, read_float, 3, 3)
        self._s = read_array(file, read_float, 3)
        self._t = read_array(file, read_float, 3)
        self.smoothingGroup = read_byte(file)
        self.groupIndex = read_byte(file)
        return self

    def write(self, file):
        write_word(file, self.flags)
        write_array(file, write_word, 3, self.vertexIndices)
        write_array2(file, write_float, 3, 3, self.vertexNormals)
        write_array(file, write_float, 3, self.s)
        write_array(file, write_float, 3, self.t)
        write_byte(file, self.smoothingGroup)
        write_byte(file, self.groupIndex)


###############################################################################
class ms3d_group_t:
    """
    ms3d_group_t
    """
    #byte flags; // FLAG_NONE | FLAG_SELECTED | FLAG_HIDDEN
    #char name[32];
    #word numtriangles;
    #word triangleIndices[numtriangles]; // the groups group the triangles
    #char materialIndex; // -1 = no material
    __slots__ = (
            PROP_NAME_FLAGS,
            PROP_NAME_NAME,
            "_numtriangles",
            "_triangleIndices",
            "materialIndex"
            )

    def __init__(
            self,
            defaultFlags=FLAG_NONE,
            defaultName="",
            defaultNumtriangles=0,
            defaultTriangleIndices=None,
            defaultMaterialIndex=-1
            ):
        """
        initialize

        :arg flags: selection flag
        :type flags: :class:`byte`
        :arg name: name
        :type name: :class:`string`
        :arg numtriangles: number of triangles
        :type numtriangles: :class:`word`
        :arg triangleIndices: array of triangle indices
        :type triangleIndices: :class:`word`
        :arg materialIndex: material index
        :type materialIndex: :class:`char`
        """

        if (defaultName is None):
            defaultName = ""

        if (defaultTriangleIndices is None):
            defaultTriangleIndices = []

        self.flags = defaultFlags
        self.name = defaultName
        #self._numtriangles = defaultNumtriangles
        self._triangleIndices = defaultTriangleIndices
        self.materialIndex = defaultMaterialIndex

    def __repr__(self):
        return "\n<flags={0}, name='{1}', numtriangles={2},"\
                " triangleIndices={3}, materialIndex={4}>".format(
                self.flags,
                self.name,
                self.numtriangles,
                self.triangleIndices,
                self.materialIndex
                )


    @property
    def numtriangles(self):
        if self.triangleIndices is None:
            return 0
        return len(self.triangleIndices)

    @property
    def triangleIndices(self):
        return self._triangleIndices


    def read(self, file):
        self.flags = read_byte(file)
        self.name = read_string(file, LENGTH_NAME)
        _numtriangles = read_word(file)
        self._triangleIndices = read_array(file, read_word, _numtriangles)
        self.materialIndex = read_char(file)
        return self

    def write(self, file):
        write_byte(file, self.flags)
        write_string(file, LENGTH_NAME, self.name)
        write_word(file, self.numtriangles)
        write_array(file, write_word, self.numtriangles, self.triangleIndices)
        write_char(file, self.materialIndex)


###############################################################################
class ms3d_material_t:
    """
    ms3d_material_t
    """
    #char name[LENGTH_NAME];
    #float ambient[4];
    #float diffuse[4];
    #float specular[4];
    #float emissive[4];
    #float shininess; // 0.0f - 128.0f
    #float transparency; // 0.0f - 1.0f
    #char mode; // 0, 1, 2 is unused now
    #char texture[LENGTH_FILENAME]; // texture.bmp
    #char alphamap[LENGTH_FILENAME]; // alpha.bmp
    __slots__ = (
            PROP_NAME_NAME,
            "_ambient",
            "_diffuse",
            "_specular",
            "_emissive",
            "shininess",
            "transparency",
            PROP_NAME_MODE,
            PROP_NAME_TEXTURE,
            PROP_NAME_ALPHAMAP
            )

    def __init__(
            self,
            defaultName="",
            defaultAmbient=(0.0, 0.0, 0.0, 0.0),
            defaultDiffuse=(0.0, 0.0, 0.0, 0.0),
            defaultSpecular=(0.0, 0.0, 0.0, 0.0),
            defaultEmissive=(0.0, 0.0, 0.0, 0.0),
            defaultShininess=0.0,
            defaultTransparency=0.0,
            defaultMode=0,
            defaultTexture="",
            defaultAlphamap=""
            ):
        """
        initialize

        :arg name: name
        :type name: :class:`string`
        :arg ambient: ambient
        :type ambient: :class:`float[4]`
        :arg diffuse: diffuse
        :type diffuse: :class:`float[4]`
        :arg specular: specular
        :type specular: :class:`float[4]`
        :arg emissive: emissive
        :type emissive: :class:`float[4]`
        :arg shininess: shininess
        :type shininess: :class:`float`
        :arg transparency: transparency
        :type transparency: :class:`float`
        :arg mode: mode
        :type mode: :class:`char`
        :arg texture: texture name
        :type texture: :class:`string`
        :arg alphamap: alphamap name
        :type alphamap: :class:`string`
        """

        if (defaultName is None):
            defaultName = ""

        if (defaultTexture is None):
            defaultTexture = ""

        if (defaultAlphamap is None):
            defaultAlphamap = ""

        self.name = defaultName
        self._ambient = defaultAmbient
        self._diffuse = defaultDiffuse
        self._specular = defaultSpecular
        self._emissive = defaultEmissive
        self.shininess = defaultShininess
        self.transparency = defaultTransparency
        self.mode = defaultMode
        self.texture = defaultTexture
        self.alphamap = defaultAlphamap

    def __repr__(self):
        return "\n<name='{0}', ambient={1}, diffuse={2}, specular={3},"\
                " emissive={4}, shininess={5}, transparency={6}, mode={7},"\
                " texture='{8}', alphamap='{9}'>".format(
                self.name,
                self.ambient,
                self.diffuse,
                self.specular,
                self.emissive,
                self.shininess,
                self.transparency,
                self.mode,
                self.texture,
                self.alphamap
                )

    def __hash__(self):
        return (hash(self.name)

                ^ hash(self.ambient)
                ^ hash(self.diffuse)
                ^ hash(self.specular)
                ^ hash(self.emissive)

                ^ hash(self.shininess)
                ^ hash(self.transparency)
                ^ hash(self.mode)

                ^ hash(self.texture)
                ^ hash(self.alphamap)
                )

    def __eq__(self, other):
        return ((self.name == other.name)

                and (self.ambient == other.ambient)
                and (self.diffuse == other.diffuse)
                and (self.specular == other.specular)
                and (self.emissive == other.emissive)

                and (self.shininess == other.shininess)
                and (self.transparency == other.transparency)
                and (self.mode == other.mode)

                #and (self.texture == other.texture)
                #and (self.alphamap == other.alphamap)
                )


    @property
    def ambient(self):
        return self._ambient

    @property
    def diffuse(self):
        return self._diffuse

    @property
    def specular(self):
        return self._specular

    @property
    def emissive(self):
        return self._emissive


    def read(self, file):
        self.name = read_string(file, LENGTH_NAME)
        self._ambient = read_array(file, read_float, 4)
        self._diffuse = read_array(file, read_float, 4)
        self._specular = read_array(file, read_float, 4)
        self._emissive = read_array(file, read_float, 4)
        self.shininess = read_float(file)
        self.transparency = read_float(file)
        self.mode = read_char(file)
        self.texture = read_string(file, LENGTH_FILENAME)
        self.alphamap = read_string(file, LENGTH_FILENAME)
        return self

    def write(self, file):
        write_string(file, LENGTH_NAME, self.name)
        write_array(file, write_float, 4, self.ambient)
        write_array(file, write_float, 4, self.diffuse)
        write_array(file, write_float, 4, self.specular)
        write_array(file, write_float, 4, self.emissive)
        write_float(file, self.shininess)
        write_float(file, self.transparency)
        write_char(file, self.mode)
        write_string(file, LENGTH_FILENAME, self.texture)
        write_string(file, LENGTH_FILENAME, self.alphamap)


###############################################################################
class ms3d_keyframe_rot_t:
    """
    ms3d_keyframe_rot_t
    """
    #float time; // time in seconds
    #float rotation[3]; // x, y, z angles
    __slots__ = (
            "time",
            "_rotation"
            )

    def __init__(
            self,
            defaultTime=0.0,
            defaultRotation=(0.0, 0.0, 0.0)
            ):
        """
        initialize

        :arg time: time
        :type time: :class:float`
        :arg rotation: rotation
        :type rotation: :class:`float[3]`
        """

        self.time = defaultTime
        self._rotation = defaultRotation

    def __repr__(self):
        return "\n<time={0}, rotation={1}>".format(
                self.time,
                self.rotation,
                )


    @property
    def rotation(self):
        return self._rotation


    def read(self, file):
        self.time = read_float(file)
        self._rotation = read_array(file, read_float, 3)
        return self

    def write(self, file):
        write_float(file, self.time)
        write_array(file, write_float, 3, self.rotation)


###############################################################################
class ms3d_keyframe_pos_t:
    """
    ms3d_keyframe_pos_t
    """
    #float time; // time in seconds
    #float position[3]; // local position
    __slots__ = (
            "time",
            "_position"
            )

    def __init__(
            self,
            defaultTime=0.0,
            defaultPosition=(0.0, 0.0, 0.0)
            ):
        """
        initialize

        :arg time: time
        :type time: :class:`float`
        :arg position: position
        :type position: :class:`float[3]`
        """

        self.time = defaultTime
        self._position = defaultPosition

    def __repr__(self):
        return "\n<time={0}, position={1}>".format(
                self.time,
                self.position,
                )


    @property
    def position(self):
        return self._position


    def read(self, file):
        self.time = read_float(file)
        self._position = read_array(file, read_float, 3)
        return self

    def write(self, file):
        write_float(file, self.time)
        write_array(file, write_float, 3, self.position)


###############################################################################
class ms3d_joint_t:
    """
    ms3d_joint_t
    """
    #byte flags; // FLAG_NONE | FLAG_SELECTED | FLAG_DIRTY
    #char name[LENGTH_NAME];
    #char parentName[LENGTH_NAME];
    #float rotation[3]; // local reference matrix
    #float position[3];
    #word numKeyFramesRot;
    #word numKeyFramesTrans;
    #// local animation matrices
    #ms3d_keyframe_rot_t keyFramesRot[numKeyFramesRot];
    #// local animation matrices
    #ms3d_keyframe_pos_t keyFramesTrans[numKeyFramesTrans];
    __slots__ = (
            PROP_NAME_FLAGS,
            PROP_NAME_NAME,
            PROP_NAME_PARENTNAME,
            "_rotation",
            "_position",
            "_numKeyFramesRot",
            "_numKeyFramesTrans",
            "_keyFramesRot",
            "_keyFramesTrans"
            )

    def __init__(
            self,
            defaultFlags=FLAG_NONE,
            defaultName="",
            defaultParentName="",
            defaultRotation=(0.0, 0.0, 0.0),
            defaultPosition=(0.0, 0.0, 0.0),
            defaultNumKeyFramesRot=0,
            defaultNumKeyFramesTrans=0,
            defaultKeyFramesRot=None,
            defaultKeyFramesTrans=None
            ):
        """
        initialize

        :arg flags: flags
        :type flags: :class:`byte`
        :arg name: name
        :type name: :class:`string`
        :arg parentName: parentName
        :type parentName: :class:`string`
        :arg rotation: rotation
        :type rotation: :class:`float[3]`
        :arg position: position
        :type position: :class:`float[3]`
        :arg numKeyFramesRot: numKeyFramesRot
        :type numKeyFramesRot: :class:`word`
        :arg numKeyFramesTrans: numKeyFramesTrans
        :type numKeyFramesTrans: :class:`word`
        :arg keyFramesRot: keyFramesRot
        :type nkeyFramesRotame: :class:`ms3d_spec.ms3d_keyframe_rot_t[]`
        :arg keyFramesTrans: keyFramesTrans
        :type keyFramesTrans: :class:`ms3d_spec.ms3d_keyframe_pos_t[]`
        """

        if (defaultName is None):
            defaultName = ""

        if (defaultParentName is None):
            defaultParentName = ""

        if (defaultKeyFramesRot is None):
            defaultKeyFramesRot = [] #ms3d_keyframe_rot_t()

        if (defaultKeyFramesTrans is None):
            defaultKeyFramesTrans = [] #ms3d_keyframe_pos_t()

        self.flags = defaultFlags
        self.name = defaultName
        self.parentName = defaultParentName
        self._rotation = defaultRotation
        self._position = defaultPosition
        #self._numKeyFramesRot = defaultNumKeyFramesRot
        #self._numKeyFramesTrans = defaultNumKeyFramesTrans
        self._keyFramesRot = defaultKeyFramesRot
        self._keyFramesTrans = defaultKeyFramesTrans

    def __repr__(self):
        return "\n<flags={0}, name='{1}', parentName='{2}', rotation={3},"\
                " position={4}, numKeyFramesRot={5}, numKeyFramesTrans={6},"\
                " keyFramesRot={7}, keyFramesTrans={8}>".format(
                self.flags,
                self.name,
                self.parentName,
                self.rotation,
                self.position,
                self.numKeyFramesRot,
                self.numKeyFramesTrans,
                self.keyFramesRot,
                self.keyFramesTrans
                )


    @property
    def rotation(self):
        return self._rotation

    @property
    def position(self):
        return self._position

    @property
    def numKeyFramesRot(self):
        if self.keyFramesRot is None:
            return 0
        return len(self.keyFramesRot)

    @property
    def numKeyFramesTrans(self):
        if self.keyFramesTrans is None:
            return 0
        return len(self.keyFramesTrans)

    @property
    def keyFramesRot(self):
        return self._keyFramesRot

    @property
    def keyFramesTrans(self):
        return self._keyFramesTrans


    def read(self, file):
        self.flags = read_byte(file)
        self.name = read_string(file, LENGTH_NAME)
        self.parentName = read_string(file, LENGTH_NAME)
        self._rotation = read_array(file, read_float, 3)
        self._position = read_array(file, read_float, 3)
        _numKeyFramesRot = read_word(file)
        _numKeyFramesTrans = read_word(file)
        self._keyFramesRot = []
        for i in range(_numKeyFramesRot):
            self.keyFramesRot.append(ms3d_keyframe_rot_t().read(file))
        self._keyFramesTrans = []
        for i in range(_numKeyFramesTrans):
            self.keyFramesTrans.append(ms3d_keyframe_pos_t().read(file))
        return self

    def write(self, file):
        write_byte(file, self.flags)
        write_string(file, LENGTH_NAME, self.name)
        write_string(file, LENGTH_NAME, self.parentName)
        write_array(file, write_float, 3, self.rotation)
        write_array(file, write_float, 3, self.position)
        write_word(file, self.numKeyFramesRot)
        write_word(file, self.numKeyFramesTrans)
        for i in range(self.numKeyFramesRot):
            self.keyFramesRot[i].write(file)
        for i in range(self.numKeyFramesTrans):
            self.keyFramesTrans[i].write(file)


###############################################################################
class ms3d_comment_t:
    """
    ms3d_comment_t
    """
    #int index; // index of group, material or joint
    #int commentLength; // length of comment (terminating '\0' is not saved),
    #    "MC" has comment length of 2 (not 3)
    #char comment[commentLength]; // comment
    __slots__ = (
            "index",
            "_commentLength",
            PROP_NAME_COMMENT
            )

    def __init__(
            self,
            defaultIndex=0,
            defaultCommentLength=0,
            defaultComment=""
            ):
        """
        initialize

        :arg index: index
        :type index: :class:`dword`
        :arg commentLength: commentLength
        :type commentLength: :class:`dword`
        :arg comment: comment
        :type comment: :class:`string`
        """

        if (defaultComment is None):
            defaultComment = ""

        self.index = defaultIndex
        #self._commentLength = defaultCommentLength
        self.comment = defaultComment

    def __repr__(self):
        return "\n<index={0}, commentLength={1}, comment={2}>".format(
                self.index,
                self.commentLength,
                self.comment
                )


    @property
    def commentLength(self):
        if self.comment is None:
            return 0
        return len(self.comment)


    def read(self, file):
        self.index = read_dword(file)
        _commentLength = read_dword(file)
        self.comment = read_string(file, _commentLength)
        return self

    def write(self, file):
        write_dword(file, self.index)
        write_dword(file, self.commentLength)
        write_string(file, self.commentLength, self.comment)


###############################################################################
class ms3d_modelcomment_t:
    """
    ms3d_modelcomment_t
    """
    #int commentLength; // length of comment (terminating '\0' is not saved),
    #    "MC" has comment length of 2 (not 3)
    #char comment[commentLength]; // comment
    __slots__ = (
            "_commentLength",
            PROP_NAME_COMMENT
            )

    def __init__(
            self,
            defaultCommentLength=0,
            defaultComment=""
            ):
        """
        initialize

        :arg commentLength: commentLength
        :type commentLength: :class:`dword`
        :arg comment: comment
        :type comment: :class:`string`
        """

        if (defaultComment is None):
            defaultComment = ""

        #self._commentLength = defaultCommentLength
        self.comment = defaultComment

    def __repr__(self):
        return "\n<commentLength={0}, comment={1}>".format(
                self.commentLength,
                self.comment
                )


    @property
    def commentLength(self):
        if self.comment is None:
            return 0
        return len(self.comment)


    def read(self, file):
        _commentLength = read_dword(file)
        self.comment = read_string(file, _commentLength)
        return self

    def write(self, file):
        write_dword(file, self.commentLength)
        write_string(file, self.commentLength, self.comment)


###############################################################################
class ms3d_vertex_ex1_t:
    """
    ms3d_vertex_ex1_t
    """
    #char boneIds[3]; // index of joint or -1, if -1, then that weight is
    #    ignored, since subVersion 1
    #byte weights[3]; // vertex weight ranging from 0 - 255, last weight is
    #    computed by 1.0 - sum(all weights), since subVersion 1
    #// weight[0] is the weight for boneId in ms3d_vertex_t
    #// weight[1] is the weight for boneIds[0]
    #// weight[2] is the weight for boneIds[1]
    #// 1.0f - weight[0] - weight[1] - weight[2] is the weight for boneIds[2]
    __slots__ = (
            "_boneIds",
            "_weights"
            )

    def __init__(
            self,
            defaultBoneIds=(-1, -1, -1),
            defaultWeights=(0, 0, 0)
            ):
        """
        initialize

        :arg boneIds: boneIds
        :type boneIds: :class:`char[3]`
        :arg weights: weights
        :type weights: :class:`byte[3]`
        """

        self._boneIds = defaultBoneIds
        self._weights = defaultWeights

    def __repr__(self):
        return "\n<boneIds={0}, weights={1}>".format(
                self.boneIds,
                self.weights
                )


    @property
    def boneIds(self):
        return self._boneIds

    @property
    def weights(self):
        return self._weights


    def read(self, file):
        self._boneIds = read_array(file, read_char, 3)
        self._weights = read_array(file, read_byte, 3)
        return self

    def write(self, file):
        write_array(file, write_char, 3, self.boneIds)
        write_array(file, write_byte, 3, self.weights)


###############################################################################
class ms3d_vertex_ex2_t:
    """
    ms3d_vertex_ex2_t
    """
    #char boneIds[3]; // index of joint or -1, if -1, then that weight is
    #    ignored, since subVersion 1
    #byte weights[3]; // vertex weight ranging from 0 - 100, last weight is
    #    computed by 1.0 - sum(all weights), since subVersion 1
    #// weight[0] is the weight for boneId in ms3d_vertex_t
    #// weight[1] is the weight for boneIds[0]
    #// weight[2] is the weight for boneIds[1]
    #// 1.0f - weight[0] - weight[1] - weight[2] is the weight for boneIds[2]
    #unsigned int extra; // vertex extra, which can be used as color or
    #    anything else, since subVersion 2
    __slots__ = (
            "_boneIds",
            "_weights",
            PROP_NAME_EXTRA
            )

    def __init__(
            self,
            defaultBoneIds=(-1, -1, -1),
            defaultWeights=(0, 0, 0),
            defaultExtra=0
            ):
        """
        initialize

        :arg boneIds: boneIds
        :type boneIds: :class:`char[3]`
        :arg weights: weights
        :type weights: :class:`byte[3]`
        :arg extra: extra
        :type extra: :class:`dword`
        """

        self._boneIds = defaultBoneIds
        self._weights = defaultWeights
        self.extra = defaultExtra

    def __repr__(self):
        return "\n<boneIds={0}, weights={1}, extra={2}>".format(
                self.boneIds,
                self.weights,
                self.extra
                )


    @property
    def boneIds(self):
        return self._boneIds

    @property
    def weights(self):
        return self._weights


    def read(self, file):
        self._boneIds = read_array(file, read_char, 3)
        self._weights = read_array(file, read_byte, 3)
        self.extra = read_dword(file)
        return self

    def write(self, file):
        write_array(file, write_char, 3, self.boneIds)
        write_array(file, write_byte, 3, self.weights)
        write_dword(file, self.extra)


###############################################################################
class ms3d_vertex_ex3_t:
    """
    ms3d_vertex_ex3_t
    """
    #char boneIds[3]; // index of joint or -1, if -1, then that weight is
    #    ignored, since subVersion 1
    #byte weights[3]; // vertex weight ranging from 0 - 100, last weight is
    #    computed by 1.0 - sum(all weights), since subVersion 1
    #// weight[0] is the weight for boneId in ms3d_vertex_t
    #// weight[1] is the weight for boneIds[0]
    #// weight[2] is the weight for boneIds[1]
    #// 1.0f - weight[0] - weight[1] - weight[2] is the weight for boneIds[2]
    #unsigned int extra; // vertex extra, which can be used as color or
    #    anything else, since subVersion 2
    __slots__ = (
            "_boneIds",
            "_weights",
            PROP_NAME_EXTRA
            )

    def __init__(
            self,
            defaultBoneIds=(-1, -1, -1),
            defaultWeights=(0, 0, 0),
            defaultExtra=0
            ):
        """
        initialize

        :arg boneIds: boneIds
        :type boneIds: :class:`char[3]`
        :arg weights: weights
        :type weights: :class:`byte[3]`
        :arg extra: extra
        :type extra: :class:`dword`
        """

        self._boneIds = defaultBoneIds
        self._weights = defaultWeights
        self.extra = defaultExtra

    def __repr__(self):
        return "\n<boneIds={0}, weights={1}, extra={2}>".format(
                self.boneIds,
                self.weights,
                self.extra
                )


    @property
    def boneIds(self):
        return self._boneIds

    @property
    def weights(self):
        return self._weights


    def read(self, file):
        self._boneIds = read_array(file, read_char, 3)
        self._weights = read_array(file, read_byte, 3)
        self.extra = read_dword(file)
        return self

    def write(self, file):
        write_array(file, write_char, 3, self.boneIds)
        write_array(file, write_byte, 3, self.weights)
        write_dword(file, self.extra)


###############################################################################
class ms3d_joint_ex_t:
    """
    ms3d_joint_ex_t
    """
    #float color[3]; // joint color, since subVersion == 1
    __slots__ = (
            "_color"
            )

    def __init__(
            self,
            defaultColor=(0.0, 0.0, 0.0)
            ):
        """
        initialize

        :arg color: color
        :type color: :class:`float[3]`
        """

        self._color = defaultColor

    def __repr__(self):
        return "\n<color={0}>".format(self.color)


    @property
    def color(self):
        return self._color


    def read(self, file):
        self._color = read_array(file, read_float, 3)
        return self

    def write(self, file):
        write_array(file, write_float, 3, self.color)


###############################################################################
class ms3d_model_ex_t:
    """
    ms3d_model_ex_t
    """
    #float jointSize; // joint size, since subVersion == 1
    #int transparencyMode; // 0 = simple, 1 = depth buffered with alpha ref,
    #    2 = depth sorted triangles, since subVersion == 1
    #float alphaRef; // alpha reference value for transparencyMode = 1,
    #    since subVersion == 1
    __slots__ = (
            "jointSize",
            "transparencyMode",
            "alphaRef"
            )

    def __init__(
            self,
            defaultJointSize=0.0,
            defaultTransparencyMode=0,
            defaultAlphaRef=0.0
            ):
        """
        initialize

        :arg jointSize: jointSize
        :type jointSize: :class:`float[3]`
        :arg transparencyMode: transparencyMode
        :type transparencyMode: :class:`dword`
        :arg alphaRef: alphaRef
        :type alphaRef: :class:`float[3]`
        """

        self.jointSize = defaultJointSize
        self.transparencyMode = defaultTransparencyMode
        self.alphaRef = defaultAlphaRef

    def __repr__(self):
        return "\n<jointSize={0}, transparencyMode={1}, alphaRef={2}>".format(
                self.jointSize,
                self.transparencyMode,
                self.alphaRef
                )

    def read(self, file):
        self.jointSize = read_float(file)
        self.transparencyMode = read_dword(file)
        self.alphaRef = read_float(file)
        return self

    def write(self, file):
        write_float(file, self.jointSize)
        write_dword(file, self.transparencyMode)
        write_float(file, self.alphaRef)


###############################################################################
#
# file format
#
###############################################################################
class ms3d_file_t:
    """
    ms3d_file_t
    """
    __slot__ = (
            "header",
            "_nNumVertices",
            "_vertices",
            "_nNumTriangles",
            "_triangles",
            "_nNumGroups",
            "_groups",
            "_nNumMaterials",
            "_materials",
            "fAnimationFPS",
            "fCurrentTime",
            "iTotalFrames",
            "_nNumJoints",
            "_joints",
            "subVersionComments",
            "_nNumGroupComments",
            "_groupComments",
            "_nNumMaterialComments",
            "_materialComments",
            "_nNumJointComments",
            "_jointComments",
            "_nHasModelComment",
            "_modelComment",
            "subVersionVertexExtra",
            "_vertex_ex",
            "subVersionJointExtra",
            "_joint_ex",
            "subVersionModelExtra",
            "model_ex",
            "_str_cash",
            PROP_NAME_NAME
            )

    def __init__(
            self,
            defaultName=""
            ):
        """
        initialize
        """

        if (defaultName is None):
            defaultName = ""

        self.name = defaultName

        # First comes the header (sizeof(ms3d_header_t) == 14)
        self.header = ms3d_header_t()

        # Then comes the number of vertices
        #self.nNumVertices = 0

        # Then comes nNumVertices times ms3d_vertex_t structs
        # (sizeof(ms3d_vertex_t) == 15)
        self._vertices = [] #ms3d_vertex_t()

        # Then comes the number of triangles
        #self.nNumTriangles = 0

        # Then come nNumTriangles times ms3d_triangle_t structs
        # (sizeof(ms3d_triangle_t) == 70)
        self._triangles = [] #ms3d_triangle_t()


        # Then comes the number of groups
        #self.nNumGroups = 0

        # Then comes nNumGroups times groups (the sizeof a group is dynamic,
        # because of triangleIndices is numtriangles long)
        self._groups = [] #ms3d_group_t()


        # number of materials
        #self.nNumMaterials = 0

        # Then comes nNumMaterials times ms3d_material_t structs
        # (sizeof(ms3d_material_t) == 361)
        self._materials = [] #ms3d_material_t()


        # save some keyframer data
        self.fAnimationFPS = 0.0
        self.fCurrentTime = 0.0
        self.iTotalFrames = 0


        # number of joints
        #self.nNumJoints = 0

        # Then comes nNumJoints joints (the size of joints are dynamic,
        # because each joint has a differnt count of keys
        self._joints = [] #ms3d_joint_t()


        # Then comes the subVersion of the comments part, which is not
        # available in older files
        self.subVersionComments = 1


        # Then comes the numer of group comments
        #self.nNumGroupComments = 0

        # Then comes nNumGroupComments times group comments, which are dynamic,
        # because the comment can be any length
        self._groupComments = [] #ms3d_comment_t()


        # Then comes the number of material comments
        #self.nNumMaterialComments = 0

        # Then comes nNumMaterialComments times material comments, which are
        # dynamic, because the comment can be any length
        self._materialComments = [] #ms3d_comment_t()


        # Then comes the number of joint comments
        #self.nNumJointComments = 0

        # Then comes nNumJointComments times joint comments, which are dynamic,
        # because the comment can be any length
        self._jointComments = [] #ms3d_comment_t()


        # Then comes the number of model comments, which is always 0 or 1
        #self.nHasModelComment = 0

        # Then comes nHasModelComment times model comments, which are dynamic,
        # because the comment can be any length
        self._modelComment = None #ms3d_modelcomment_t()


        # Then comes the subversion of the vertex extra information like bone
        # weights, extra etc.
        self.subVersionVertexExtra = 2

        # ms3d_vertex_ex_t for subVersionVertexExtra in {1, 2, 3}
        #ms3d_vertex_ex1_t() #ms3d_vertex_ex2_t() #ms3d_vertex_ex3_t()
        self._vertex_ex = []
        # Then comes nNumVertices times ms3d_vertex_ex_t structs
        # (sizeof(ms3d_vertex_ex_t) == 10)
        ##

        # Then comes the subversion of the joint extra information like
        # color etc.
        self.subVersionJointExtra = 1 # ??? in spec it is 2,
        # but in MilkShake3D 1.8.4 a joint subversion of 2 is unknown

        # ms3d_joint_ex_t for subVersionJointExtra == 1
        self._joint_ex = [] #ms3d_joint_ex_t()
        # Then comes nNumJoints times ms3d_joint_ex_t structs
        # (sizeof(ms3d_joint_ex_t) == 12)
        ##

        # Then comes the subversion of the model extra information
        self.subVersionModelExtra = 1

        # ms3d_model_ex_t for subVersionModelExtra == 1
        self.model_ex = ms3d_model_ex_t()


    @property
    def nNumVertices(self):
        if self.vertices is None:
            return 0
        return len(self.vertices)

    @property
    def vertices(self):
        return self._vertices


    @property
    def nNumTriangles(self):
        if self.triangles is None:
            return 0
        return len(self.triangles)

    @property
    def triangles(self):
        return self._triangles


    @property
    def nNumGroups(self):
        if self.groups is None:
            return 0
        return len(self.groups)

    @property
    def groups(self):
        return self._groups


    @property
    def nNumMaterials(self):
        if self.materials is None:
            return 0
        return len(self.materials)

    @property
    def materials(self):
        return self._materials


    @property
    def nNumJoints(self):
        if self.joints is None:
            return 0
        return len(self.joints)

    @property
    def joints(self):
        return self._joints


    @property
    def nNumGroupComments(self):
        if self.groupComments is None:
            return 0
        return len(self.groupComments)

    @property
    def groupComments(self):
        return self._groupComments


    @property
    def nNumMaterialComments(self):
        if self.materialComments is None:
            return 0
        return len(self.materialComments)

    @property
    def materialComments(self):
        return self._materialComments


    @property
    def nNumJointComments(self):
        if self.jointComments is None:
            return 0
        return len(self.jointComments)

    @property
    def jointComments(self):
        return self._jointComments


    @property
    def nHasModelComment(self):
        if self.modelComment is None:
            return 0
        return 1

    @property
    def modelComment(self):
        return self._modelComment


    @property
    def vertex_ex(self):
        return self._vertex_ex

    @property
    def joint_ex(self):
        return self._joint_ex


    def print_internal(self):
        print()
        print("##############################################################")
        print("## the internal data of ms3d_file_t object...")
        print("##")

        print("header={0}".format(self.header))

        print("nNumVertices={0}".format(self.nNumVertices))
        print("vertices=[", end="")
        if self.vertices:
            for obj in self.vertices:
                print("{0}".format(obj), end="")
        print("]")

        print("nNumTriangles={0}".format(self.nNumTriangles))
        print("triangles=[", end="")
        if self.triangles:
            for obj in self.triangles:
                print("{0}".format(obj), end="")
        print("]")

        print("nNumGroups={0}".format(self.nNumGroups))
        print("groups=[", end="")
        if self.groups:
            for obj in self.groups:
                print("{0}".format(obj), end="")
        print("]")

        print("nNumMaterials={0}".format(self.nNumMaterials))
        print("materials=[", end="")
        if self.materials:
            for obj in self.materials:
                print("{0}".format(obj), end="")
        print("]")

        print("fAnimationFPS={0}".format(self.fAnimationFPS))
        print("fCurrentTime={0}".format(self.fCurrentTime))
        print("iTotalFrames={0}".format(self.iTotalFrames))

        print("nNumJoints={0}".format(self.nNumJoints))
        print("joints=[", end="")
        if self.joints:
            for obj in self.joints:
                print("{0}".format(obj), end="")
        print("]")

        print("subVersionComments={0}".format(self.subVersionComments))

        print("nNumGroupComments={0}".format(self.nNumGroupComments))
        print("groupComments=[", end="")
        if self.groupComments:
            for obj in self.groupComments:
                print("{0}".format(obj), end="")
        print("]")

        print("nNumMaterialComments={0}".format(self.nNumMaterialComments))
        print("materialComments=[", end="")
        if self.materialComments:
            for obj in self.materialComments:
                print("{0}".format(obj), end="")
        print("]")

        print("nNumJointComments={0}".format(self.nNumJointComments))
        print("jointComments=[", end="")
        if self.jointComments:
            for obj in self.jointComments:
                print("{0}".format(obj), end="")
        print("]")

        print("nHasModelComment={0}".format(self.nHasModelComment))
        print("modelComment={0}".format(self.modelComment))

        print("subVersionVertexExtra={0}".format(self.subVersionVertexExtra))
        print("vertex_ex={0}".format(self.vertex_ex))

        print("subVersionJointExtra={0}".format(self.subVersionJointExtra))
        print("joint_ex={0}".format(self.joint_ex))

        print("subVersionModelExtra={0}".format(self.subVersionModelExtra))
        print("model_ex={0}".format(self.model_ex))

        print("##")
        print("## ...end")
        print("##############################################################")
        print()


    def read(self, file):
        """
        opens, reads and pars MS3D file.
        add content to blender scene

        :arg file: file
        :type file: :class:`io.FileIO`
        """

        self.header.read(file)

        _nNumVertices = read_word(file)
        self._vertices = []
        for i in range(_nNumVertices):
            self.vertices.append(ms3d_vertex_t().read(file))

        _nNumTriangles = read_word(file)
        self._triangles = []
        for i in range(_nNumTriangles):
            self.triangles.append(ms3d_triangle_t().read(file))

        _nNumGroups = read_word(file)
        self._groups = []
        for i in range(_nNumGroups):
            self.groups.append(ms3d_group_t().read(file))

        _nNumMaterials = read_word(file)
        self._materials = []
        for i in range(_nNumMaterials):
            self.materials.append(ms3d_material_t().read(file))

        self.fAnimationFPS = read_float(file)
        self.fCurrentTime = read_float(file)
        self.iTotalFrames = read_dword(file)

        progressCount = 0

        try:
            # optional part
            # doesn't matter if doesn't existing.

            _nNumJoints = read_word(file)
            self._joints = []
            for i in range(_nNumJoints):
                self.joints.append(ms3d_joint_t().read(file))

            progressCount += 1

            self.subVersionComments = read_dword(file)

            progressCount += 1

            _nNumGroupComments = read_dword(file)
            self._groupComments = []
            for i in range(_nNumGroupComments):
                self.groupComments.append(ms3d_comment_t().read(file))

            progressCount += 1

            _nNumMaterialComments = read_dword(file)
            self._materialComments = []
            for i in range(_nNumMaterialComments):
                self.materialComments.append(ms3d_comment_t().read(file))

            progressCount += 1

            _nNumJointComments = read_dword(file)
            self._jointComments = []
            for i in range(_nNumJointComments):
                self.jointComments.append(ms3d_comment_t().read(file))

            progressCount += 1

            _nHasModelComment = read_dword(file)
            if (_nHasModelComment != 0):
                self._modelComment = ms3d_modelcomment_t().read(file)
            else:
                self._modelComment = None

            progressCount += 1

            self.subVersionVertexExtra = read_dword(file)
            if (self.subVersionVertexExtra in {1, 2, 3}):
                self._vertex_ex = []
                for i in range(_nNumVertices):
                    if self.subVersionVertexExtra == 1:
                        item = ms3d_vertex_ex1_t()
                    if self.subVersionVertexExtra == 2:
                        item = ms3d_vertex_ex2_t()
                    if self.subVersionVertexExtra == 3:
                        item = ms3d_vertex_ex3_t()
                    self.vertex_ex.append(item.read(file))
            else:
                self._vertex_ex = None

            progressCount += 1

            self.subVersionJointExtra = read_dword(file)
            self._joint_ex = []
            for i in range(_nNumJoints):
                self.joint_ex.append(ms3d_joint_ex_t().read(file))

            progressCount += 1

            self.subVersionModelExtra = read_dword(file)

            progressCount += 1

            self.model_ex.read(file)

        except Exception:
            #type, value, traceback = sys.exc_info()
            #print("ms3d_file.read - exception in optional try block,"
            #        " progressCount={0}\n  type: '{1}'\n  value: '{2}'".format(
            #        progressCount, type, value, traceback))

            if (progressCount):
                if (progressCount <= 0):
                    _nNumJoints = None
                    self._joints = None

                if (progressCount <= 1):
                    self.subVersionComments = None

                if (progressCount <= 2):
                    _nNumGroupComments = None
                    self._groupComments = None

                if (progressCount <= 3):
                    _nNumMaterialComments = None
                    self._materialComments = None

                if (progressCount <= 4):
                    _nNumJointComments = None
                    self._jointComments = None

                if (progressCount <= 5):
                    _nHasModelComment = None
                    self._modelComment = None

                if (progressCount <= 6):
                    self.subVersionVertexExtra = None
                    self._vertex_ex = None

                if (progressCount <= 7):
                    self.subVersionJointExtra = None
                    self._joint_ex = None

                if (progressCount <= 8):
                    self.subVersionModelExtra = None

                if (progressCount <= 9):
                    self.model_ex = None

        else:
            pass

        return


    def write(self, file):
        """
        add blender scene content to MS3D
        creates, writes MS3D file.

        :arg file: file
        :type file: :class:`io.FileIO`
        """

        self.header.write(file)

        write_word(file, self.nNumVertices)
        for i in range(self.nNumVertices):
            self.vertices[i].write(file)

        write_word(file, self.nNumTriangles)
        for i in range(self.nNumTriangles):
            self.triangles[i].write(file)

        write_word(file, self.nNumGroups)
        for i in range(self.nNumGroups):
            self.groups[i].write(file)

        write_word(file, self.nNumMaterials)
        for i in range(self.nNumMaterials):
            self.materials[i].write(file)

        write_float(file, self.fAnimationFPS)
        write_float(file, self.fCurrentTime)
        write_dword(file, self.iTotalFrames)

        try:
            # optional part
            # doesn't matter if it doesn't complete.
            write_word(file, self.nNumJoints)
            for i in range(self.nNumJoints):
                self.joints[i].write(file)

            write_dword(file, self.subVersionComments)

            write_dword(file, self.nNumGroupComments)
            for i in range(self.nNumGroupComments):
                self.groupComments[i].write(file)

            write_dword(file, self.nNumMaterialComments)
            for i in range(self.nNumMaterialComments):
                self.materialComments[i].write(file)

            write_dword(file, self.nNumJointComments)
            for i in range(self.nNumJointComments):
                self.jointComments[i].write(file)

            write_dword(file, self.nHasModelComment)
            if (self.nHasModelComment != 0):
                self.modelComment.write(file)

            write_dword(file, self.subVersionVertexExtra)
            if (self.subVersionVertexExtra in {1, 2, 3}):
                for i in range(self.nNumVertices):
                    self.vertex_ex[i].write(file)

            write_dword(file, self.subVersionJointExtra)
            for i in range(self.nNumJoints):
                self.joint_ex[i].write(file)

            write_dword(file, self.subVersionModelExtra)
            self.model_ex.write(file)

        except Exception:
            #type, value, traceback = sys.exc_info()
            #print("ms3d_file.write - exception in optional try block"
            #        "\n  type: '{0}'\n  value: '{1}'".format(
            #        type, value, traceback))
            pass

        else:
            pass

        return


    def isValid(self):
        valid = True
        result = []

        format1 = "\n  number of {0}: {1}"
        format2 = " limit exceeded! (limit is {0})"

        result.append("MS3D statistics:")
        result.append(format1.format("vertices ........", self.nNumVertices))
        if (self.nNumVertices > MAX_VERTICES):
            result.append(format2.format(MAX_VERTICES))
            valid &= False

        result.append(format1.format("triangles .......", self.nNumTriangles))
        if (self.nNumTriangles > MAX_TRIANGLES):
            result.append(format2.format(MAX_TRIANGLES))
            valid &= False

        result.append(format1.format("groups ..........", self.nNumGroups))
        if (self.nNumGroups > MAX_GROUPS):
            result.append(format2.format(MAX_GROUPS))
            valid &= False

        result.append(format1.format("materials .......", self.nNumMaterials))
        if (self.nNumMaterials > MAX_MATERIALS):
            result.append(format2.format(MAX_MATERIALS))
            valid &= False

        result.append(format1.format("joints ..........", self.nNumJoints))
        if (self.nNumJoints > MAX_JOINTS):
            result.append(format2.format(MAX_JOINTS))
            valid &= False

        result.append(format1.format("model comments ..",
                self.nHasModelComment))
        result.append(format1.format("group comments ..",
                self.nNumGroupComments))
        result.append(format1.format("material comments",
                self.nNumMaterialComments))
        result.append(format1.format("joint comments ..",
                self.nNumJointComments))

        #if (not valid):
        #    result.append("\n\nthe data may be corrupted.")

        return (valid, ("".join(result)))


    # some other helper
    def get_group_by_key(self, key):
        if key is None:
            return None

        items = self.groups

        if items is None:
            return None

        elif isinstance(key, int):
            if (key >= 0) and (key < self.nNumGroups):
                return items[key]

        elif isinstance(key, string):
            for item in items:
                if item.name == key:
                    return item

        elif isinstance(key, ms3d_spec.ms3d_triangle_t):
            if (key.groupIndex >= 0) and (key.groupIndex < self.nNumGroups):
                return item[key.groupIndex]

        return None


    def get_group_comment_by_key(self, key):
        if key is None:
            return None

        items = self.groupComments

        if items is None:
            return None

        elif isinstance(key, int):
            for item in items:
                if (item.index == key):
                    return item

        return None


    def get_material_by_key(self, key):
        if key is None:
            return None

        items = self.materials

        if items is None:
            return None

        elif isinstance(key, int):
            if (key >= 0) and (key < self.nNumMaterials):
                return items[key]

        elif isinstance(key, string):
            for item in items:
                if item.name == key:
                    return item

        elif isinstance(key, ms3d_spec.ms3d_group_t):
            if (key.materialIndex >= 0) and (key.materialIndex < self.nNumMaterials):
                return item[key.materialIndex]

        return None


    def get_material_comment_by_key(self, key):
        if key is None:
            return None

        items = self.materialComments

        if items is None:
            return None

        elif isinstance(key, int):
            for item in items:
                if (item.index == key):
                    return item

        return None


    def get_joint_by_key(self, key):
        if key is None:
            return None

        items = self.joints

        if items is None:
            return None

        elif isinstance(key, int):
            if (key >= 0) and (key < self.nNumJoints):
                return items[key]

        elif isinstance(key, string):
            for item in items:
                if item.name == key:
                    return item

        elif isinstance(key, ms3d_spec.ms3d_vertex_t):
            if (key.boneId >= 0) and (key.boneId < self.nNumJoints):
                return item[key.boneId]

        return None


    def get_joint_ex_by_key(self, key):
        if key is None:
            return None

        items = self.joint_ex

        if items is None:
            return None

        elif isinstance(key, int):
            if (key >= 0) and (key < self.nNumJoints):
                return items[key]

        elif isinstance(key, string):
            for i, item in enumerate(self.joints):
                if item.name == key:
                    return items[i]

        elif isinstance(key, ms3d_spec.ms3d_joint_t):
            for i, item in enumerate(self.joints):
                if item.name == key.name:
                    return items[i]

        elif isinstance(key, ms3d_spec.ms3d_vertex_t):
            if (key.boneId >= 0) and (key.boneId < self.nNumJoints):
                return item[key.boneId]

        return None


    def get_joint_comment_by_key(self, key):
        if key is None:
            return None

        items = self.jointComments

        if items is None:
            return None

        elif isinstance(key, int):
            for item in items:
                if (item.index == key):
                    return item

        return None


###############################################################################
#234567890123456789012345678901234567890123456789012345678901234567890123456789
#--------1---------2---------3---------4---------5---------6---------7---------
# ##### END OF FILE #####
