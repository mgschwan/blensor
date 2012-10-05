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

"""
TODO: Add 'scene creation for each clip' option

"""

import bpy
import os
import sys
from bpy.props import BoolProperty
from bpy.props import EnumProperty
from . import functions

scn = bpy.context.scene

bpy.types.Scene.default_recursive = BoolProperty(
name='Recursive',
description='Load in recursive folders',
default=False)
scn.default_recursive = False

bpy.types.Scene.default_recursive_ext = BoolProperty(
name='Recursive ext',
description='Load only clips with selected extension',
default=False)
scn.default_recursive_ext = False

bpy.types.Scene.default_recursive_proxies = BoolProperty(
name='Recursive proxies',
description='Load in recursive folders + proxies',
default=False)
scn.default_recursive_proxies = False

movieextlist = [("1", ".avi", ""),
            ("2", ".flc", ""),
            ("3", ".mov", ""),
            ("4", ".movie", ""),
            ("5", ".mp4", ""),
            ("6", ".m4v", ""),
            ("7", ".m2v", ""),
            ("8", ".m2t", ""),
            ("9", ".m2ts", ""),
            ("10", ".mts", ""),
            ("11", ".mv", ""),
            ("12", ".avs", ""),
            ("13", ".wmv", ""),
            ("14", ".ogv", ""),
            ("15", ".dv", ""),
            ("16", ".mpeg", ""),
            ("17", ".mpg", ""),
            ("18", ".mpg2", ""),
            ("19", ".vob", ""),
            ("20", ".mkv", ""),
            ("21", ".flv", ""),
            ("22", ".divx", ""),
            ("23", ".xvid", ""),
            ("24", ".mxf", "")]

bpy.types.Scene.default_ext = EnumProperty(
items=movieextlist,
name="ext enum",
default="3")
scn.default_ext = "3"


def loader(filelist):
    if filelist:
        for i in filelist:
            functions.setpathinbrowser(i[0], i[1])
            try:
                if scn.default_recursive_proxies:
                    bpy.ops.sequencerextra.placefromfilebrowserproxy(
                        proxy_suffix=scn.default_proxy_suffix,
                        proxy_extension=scn.default_proxy_extension,
                        proxy_path=scn.default_proxy_path,
                        build_25=scn.default_build_25,
                        build_50=scn.default_build_50,
                        build_75=scn.default_build_75,
                        build_100=scn.default_build_100)
                else:
                    bpy.ops.sequencerextra.placefromfilebrowser()
            except:
                print("Error loading file (recursive loader error): ", i[1])
                functions.add_marker(i[1])
                #self.report({'ERROR_INVALID_INPUT'}, 'Error loading file ')
                #return {'CANCELLED'}
                pass


def onefolder():
    '''
    returns a list of MOVIE type files from folder selected in file browser
    '''
    filelist = []
    path, filename = functions.getfilepathfrombrowser()
    extension = filename.rpartition(".")[2]
    #extension = scn.default_ext
    scn = bpy.context.scene

    if functions.detect_strip_type(path + filename) == 'MOVIE':
        if scn.default_recursive_ext == True:
            for file in os.listdir(path):
                if file.rpartition(".")[2] == extension:
                    filelist.append((path, file))
        else:
            for file in os.listdir(path):
                filelist.append((path, file))
    return (filelist)
    #loader(sortlist(filelist))


def recursive():
    '''
    returns a list of MOVIE type files recursively from file browser
    '''
    filelist = []
    path = functions.getpathfrombrowser()
    scn = bpy.context.scene
    for i in movieextlist:
        if i[0] == scn.default_ext:
            extension = i[1].rpartition(".")[2]
    #pythonic way to magic:
    for root, dirs, files in os.walk(path):
        for f in files:
            if scn.default_recursive_ext == True:
                if f.rpartition(".")[2] == extension:
                    filelist.append((root, f))
            else:
                filelist.append((root, f))
    return filelist
    #loader(sortlist(filelist))


class Sequencer_Extra_RecursiveLoader(bpy.types.Operator):
    bl_idname = "sequencerextra.recursiveload"
    bl_label = "recursive load"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scn = bpy.context.scene
        if scn["default_recursive"] == True:
            loader(functions.sortlist(recursive()))
        else:
            loader(functions.sortlist(onefolder()))
        return {'FINISHED'}
