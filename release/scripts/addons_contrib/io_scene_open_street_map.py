# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****

# <pep8 compliant>

bl_info = {
    "name": "Open Street Map (.osm)",
    "author": "Michael Anthrax Schlachter",
    "version": (0, 1),
    "blender": (2, 6, 3),
    "location": "File > Import",
    "description": "Load Open Street Map File",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export"}

# originally written for blender 2.4x by (manthrax _at_ hotmail.com),
# updated by for blender 2.6x by ideasman42
# If you use it for something cool, send me an email and let me know!

import bpy
from mathutils import Vector, Matrix


def parseBranch(nodes, bm, nmap, scale=100.0):
    tidx = 0
    inNode = 0
    dlat = dlong = clat = clong = minlat = maxlat = minlong = maxlong = 0.0
    for node in nodes:
        if node.localName == "bounds":
            if node.hasAttributes():
                for i in range(node.attributes.length):
                    at = node.attributes.item(i)
                    if at.name == "minlat":
                        minlat = float(at.nodeValue)
                    elif at.name == "minlon":
                        minlong = float(at.nodeValue)
                    elif at.name == "maxlat":
                        maxlat = float(at.nodeValue)
                    elif at.name == "maxlon":
                        maxlong = float(at.nodeValue)
                dlat = maxlat - minlat
                dlong = maxlong - minlong
                clat = (maxlat + minlat) * 0.5
                clong = (maxlong + minlong) * 0.5

                print(dlat, dlong, clat, clong)

        if node.localName == "way":
            nid = None
            refs = []
            '''
            if node.hasAttributes():
                for i in range(node.attributes.length):
                    at=node.attributes.item(i)
                    print(at.name)
            '''

            for ch in node.childNodes:
                if ch.localName == "nd":
                    for i in range(ch.attributes.length):
                        at = ch.attributes.item(i)
                        #print(at.name)
                        if at.name == "ref":
                            refs.append(int(at.nodeValue))

            first = 1
            for r in refs:
                if first == 0:
                    edge = bm.edges.get((nmap[pr], nmap[r]))
                    if edge is None:
                        edge = bm.edges.new((nmap[pr], nmap[r]))
                    del edge  # don't actually use it
                else:
                    first = 0
                pr = r

        if node.localName == "node":
            if node.hasAttributes():
                nid = None
                nlong = None
                nlat = None
                logged = 0
                for i in range(node.attributes.length):
                    at = node.attributes.item(i)
                    #print(at.name)
                    if at.name == "id":
                        nid = at.nodeValue
                    elif at.name == "lon":
                        nlong = at.nodeValue
                    elif at.name == "lat":
                        nlat = at.nodeValue

                    if (nid is not None) and (nlat is not None) and (nlong is not None):
                        fla = (float(nlat) - clat) * scale / dlat
                        flo = (float(nlong) - clong) * scale / dlat
                        vert = bm.verts.new((fla, flo, 0.0))
                        nmap[int(nid)] = vert
                        logged = 1
                        break
        tidx += 1
        #if tidx > 1000:
        #    break
        tidx += parseBranch(node.childNodes, bm, nmap)

    return tidx


def read(context, filepath, scale=100.0):
    import bmesh
    from xml.dom import minidom

    xmldoc = minidom.parse(filepath)

    print("Starting parse: %r..." % filepath)
    bm = bmesh.new()

    nmap = {}
    tidx = parseBranch(xmldoc.childNodes, bm, nmap)

    # create mesh
    name = bpy.path.display_name_from_filepath(filepath)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    obj = bpy.data.objects.new(name, me)

    # scale by 1.5 is odd, need to look into that
    global_matrix = Matrix(((+0.0, +1.0, +0.0, +0.0),
                            (+1.5, -0.0, +0.0, +0.0),
                            (+0.0, -0.0, -1.0, +0.0),
                            (+0.0, +0.0, +0.0, +1.0)))
    me.transform(global_matrix)

    # create the object in the scene
    scene = context.scene
    scene.objects.link(obj)
    scene.objects.active = obj
    obj.select = True

    print("Parse done... %d" % tidx)

    return {'FINISHED'}

## for testing
#if __name__ == "__main__":
#    read("/data/downloads/osm_parser/map.osm", bpy.context)


# ----------------------------------------------------------------------------
# blender integration

from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper

from bpy.props import StringProperty, FloatProperty


class ImportOSM(Operator, ImportHelper):
    '''Import OSM'''
    bl_idname = "import.open_street_map"
    bl_label = "Import OpenStreetMap (.osm)"

    # ExportHelper mixin class uses this
    filename_ext = ".osm"

    filter_glob = StringProperty(
            default="*.osm",
            options={'HIDDEN'},
            )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    scale = FloatProperty(
            name="Scale",
            default=100.0,
            )

    def execute(self, context):
        return read(context, self.filepath, self.scale)


# Only needed if you want to add into a dynamic menu
def menu_func_export(self, context):
    self.layout.operator(ImportOSM.bl_idname)


def register():
    bpy.utils.register_class(ImportOSM)
    bpy.types.INFO_MT_file_import.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ImportOSM)
    bpy.types.INFO_MT_file_import.remove(menu_func_export)
