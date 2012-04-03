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

bl_info = {
        "name": "MilkShape3D MS3D format (.ms3d)",
        "description": "Import / Export MilkShape3D MS3D files"
                " (conform with v1.8.4)",
        "author": "Alexander Nussbaumer",
        "version": (0, 3, 8),
        "blender": (2, 60, 0),
        "location": "File > Import-Export",
        "warning": "[2012-01-17] side-by-side implementation for Matrix handling around rev.42816",
        "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"\
                "Scripts/Import-Export/MilkShape3D_MS3D",
        "tracker_url": "http://projects.blender.org/tracker/index.php"\
                "?func=detail&aid=29404",
        "category": 'Import-Export',
        }

###############################################################################
#234567890123456789012345678901234567890123456789012345678901234567890123456789
#--------1---------2---------3---------4---------5---------6---------7---------


# ##### BEGIN COPYRIGHT BLOCK #####
#
# initial script copyright (c)2011 Alexander Nussbaumer
#
# ##### END COPYRIGHT BLOCK #####


# To support reload properly, try to access a package var,
# if it's there, reload everything
if ("bpy" in locals()):
    import imp
    if "ms3d_utils" in locals():
        imp.reload(ms3d_utils)
    if "ms3d_export" in locals():
        imp.reload(ms3d_export)
    if "ms3d_import" in locals():
        imp.reload(ms3d_import)
    pass

else:
    from . import ms3d_utils
    from . import ms3d_export
    from . import ms3d_import
    pass


#import blender stuff
import bpy
import bpy_extras


###############################################################################
# registration
def menu_func_import(self, context):
    self.layout.operator(
            ms3d_import.ImportMS3D.bl_idname,
            text=ms3d_utils.TEXT_OPERATOR
            )


def menu_func_export(self, context):
    self.layout.operator(
            ms3d_export.ExportMS3D.bl_idname,
            text=ms3d_utils.TEXT_OPERATOR
            )


def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_file_export.append(menu_func_export)
    bpy.types.INFO_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_file_export.remove(menu_func_export)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)


###############################################################################
# global entry point
if (__name__ == "__main__"):
    register()


###############################################################################
#234567890123456789012345678901234567890123456789012345678901234567890123456789
#--------1---------2---------3---------4---------5---------6---------7---------
# ##### END OF FILE #####
