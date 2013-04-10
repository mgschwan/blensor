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

# these must be all lower case for comparisons

# correct spelling but ignore
dict_custom = {
    "instantiation",
    "iterable",
    "prepend",
    "subclass", "subclasses", "subclassing",
    "merchantability",
    "precalculate",
    "unregister",
    "unselected",
    "subdirectory",
    "decrement",
    "boolean",
    "decrementing",

    # python types
    "str",
    "enum", "enums",
    "int", "ints",
    "tuple", "tuples",

    # python functions
    "repr",
    "func",

    # accepted abbreviations
    "config",
    "recalc",
    "addon", "addons",
    "subdir",
    "struct", "structs",
    "lookup", "lookups",
    "autocomplete",
    "namespace",
    "multi",
    "keyframe", "keyframing",
    "coord", "coords",
    "dir",
    "tooltip",

    # general computer terms
    "endian",
    "contructor",
    "unicode",
    "jitter",
    "quantized",
    "searchable",
    "metadata",
    "hashable",
    "stdin",
    "stdout",
    "stdin",
    "opengl",
    "boids",
    "keymap",
    "voxel", "voxels",
    "vert", "verts",
    "euler", "eulers",
    "booleans",
    "intrinsics",
    "XXX",
    "segfault",
    "wiki",
    "foo",
    "diff",
    "diffs",
    "sudo",
    "http",
    "url",
    "usr",
    "env",
    "app",
    "preprocessor",

    # specific computer terms/brands
    "posix",
    "unix",
    "amiga",
    "netscape",
    "mozilla",
    "irix",
    "kde",
    "qtcreator",
    "ack",

    # general computer graphics terms
    "colinear",
    "coplanar",
    "barycentric",
    "bezier",
    "fresnel",
    "radiosity",
    "reflectance",
    "specular",
    "nurbs",
    "ngon", "ngons",
    "bicubic",
    "compositing",
    "deinterlace",
    "shader",
    "shaders",
    "centroid",
    "emissive",
    "quaternions",
    "lacunarity",
    "musgrave",
    "normals",

    # blender terms
    "bmain",
    "bmesh",
    "bpy",
    "bge",
    "mathutils",
    "fcurve",
    "animviz",
    "animsys",
    "eekadoodle",
    "editmode",
    "obdata",
    "doctree",

    # should have apostrophe but ignore for now
    # unless we want to get really picky!
    "indices",
    "vertices",
}

# incorrect spelling but ignore anyway
dict_ignore = {
    "tri",
    "quad",
    "eg",
    "ok",
    "ui",
    "uv",
    "arg", "args",
    "vec",
    "loc",
    "dof",
    "bool",
    "dupli",
    "readonly",
    "filepath",
    "filepaths",
    "filename", "filenames",
    "submodule", "submodules",
    "dirpath",
    "x-axis",
    "y-axis",
    "z-axis",
    "a-z",
    "id-block",
    "node-trees",
    "pyflakes",
    "pylint",

    # acronyms
    "cpu",
    "gpu",
    "nan",
    "utf",
    "rgb",
    "gzip",
    "ppc",
    "gpl",
    "rna",
    "nla",
    "api",
    "rhs",
    "lhs",
    "ik",
    "smpte",
    "svn",
    "hg",
    "gl",

    # extensions
    "xpm",
    "xml",
    "py",
    "rst",

    # tags
    "fixme",
    "todo",

    # sphinx/rst
    "rtype",

    # slang
    "hrmf",
    "automagically",

    # names
    "jahka",
    "campbell",
    "mikkelsen", "morten",
}
