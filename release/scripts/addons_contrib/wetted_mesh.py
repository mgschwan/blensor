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

bl_info = {
    "name": "Add Wetted Mesh",
    "author": "freejack",
    "version": (0, 2, 1),
    "blender": (2, 58, 0),
    "location": "View3D > Tool Shelf > Wetted Mesh Panel",
    "description": "Adds separated fluid, dry and wetted mesh for selected pair.",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"\
        "Scripts/Mesh/Wetted_Mesh",
    "tracker_url": "http://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=27156",
    "category": "Mesh"}

import bpy
import collections
import math

### Tool Panel ###
class VIEW3D_PT_tools_WettedMesh(bpy.types.Panel):
    """Wetted Mesh Tool Panel"""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = 'Wetted Mesh'
    bl_context = 'objectmode'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        slcnt = len(context.selected_objects)

        if slcnt != 2:
            col.label(text = 'Select two mesh objects')
            col.label(text = 'to generate separated')
            col.label(text = 'fluid, dry and wetted')
            col.label(text = 'meshes.')
        else:
            (solid, fluid) = getSelectedPair(context)
            col.label(text = 'solid = '+solid.name)
            col.label(text = 'fluid = '+fluid.name)
            col.operator('mesh.primitive_wetted_mesh_add', text='Generate Meshes')

### Operator ###
class AddWettedMesh(bpy.types.Operator):
    """Add wetted mesh for selected mesh pair"""
    bl_idname = "mesh.primitive_wetted_mesh_add"
    bl_label = "Add Wetted Mesh"
    bl_options = {'REGISTER', 'UNDO'}
    statusMessage = ''

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.label(text = self.statusMessage)

    def execute(self, context):
        # make sure a pair of objects is selected
        if len(context.selected_objects) != 2:
            # should not happen if called from tool panel
            self.report({'WARNING'}, "no mesh pair selected, operation cancelled")
            return {'CANCELLED'}

        print("add_wetted_mesh begin")
        
        # super-selected object is solid, other object is fluid
        (solid, fluid) = getSelectedPair(context)
        print("   solid = "+solid.name)
        print("   fluid = "+fluid.name)
            
        # make a copy of fluid object, convert to mesh if required
        print("   copy fluid")
        bpy.ops.object.select_all(action='DESELECT')
        fluid.select = True
        context.scene.objects.active = fluid
        bpy.ops.object.duplicate()
        bpy.ops.object.convert(target='MESH', keep_original=False)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        fluidCopy = context.object
        
        # substract solid from fluidCopy
        print("   bool: fluidCopy DIFFERENCE solid")
        bpy.ops.object.modifier_add(type='BOOLEAN')
        bop = fluidCopy.modifiers.items()[0]
        bop[1].operation = 'DIFFERENCE'
        bop[1].object = solid
        bpy.ops.object.modifier_apply(apply_as='DATA', modifier=bop[0])
        fluidMinusSolid = fluidCopy
        fluidMinusSolid.name = "fluidMinusSolid"
        
        # make a second copy of fluid object
        print("   copy fluid")
        bpy.ops.object.select_all(action='DESELECT')
        fluid.select = True
        context.scene.objects.active = fluid
        bpy.ops.object.duplicate()
        bpy.ops.object.convert(target='MESH', keep_original=False)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        fluidCopy = context.object
        
        # make union from fluidCopy and solid
        print("   bool: fluidCopy UNION solid")
        bpy.ops.object.modifier_add(type='BOOLEAN')
        bop = fluidCopy.modifiers.items()[0]
        bop[1].operation = 'UNION'
        bop[1].object = solid
        bpy.ops.object.modifier_apply(apply_as='DATA', modifier=bop[0])
        fluidUnionSolid = fluidCopy
        fluidUnionSolid.name = "fluidUnionSolid"
        
        # index meshes
        print("   KDTree index fluidMinusSolid")
        fluidMinusSolidKDT = KDTree(3, fluidMinusSolid.data.vertices)
        print("   KDTree index fluidUnionSolid")
        fluidUnionSolidKDT = KDTree(3, fluidUnionSolid.data.vertices)
        kdtrees = (fluidMinusSolidKDT, fluidUnionSolidKDT)
        
        # build mesh face sets
        faceDict = { }
        vertDict = { }
        
        print("   processing fluidMinusSolid faces")
        cacheDict = { }
        setFMSfaces = set()
        numFaces = len(fluidUnionSolid.data.faces)
        i = 0
        for f in fluidMinusSolid.data.faces:
            if i % 500 == 0:
                print("      ", i, " / ", numFaces)
            i += 1
            fuid = unifiedFaceId(kdtrees, f, fluidMinusSolid.data.vertices, \
                                 faceDict, vertDict, cacheDict)
            setFMSfaces.add(fuid)
        
        print("   processing fluidUnionSolid faces")
        cacheDict = { }
        setFUSfaces = set()
        numFaces = len(fluidUnionSolid.data.faces)
        i = 0
        for f in fluidUnionSolid.data.faces:
            if i % 500 == 0:
                print("      ", i, " / ", numFaces)
            i += 1
            fuid = unifiedFaceId(kdtrees, f, fluidUnionSolid.data.vertices, \
                                 faceDict, vertDict, cacheDict)
            setFUSfaces.add(fuid)
        
        # remove boolean helpers
        print("   delete helper objects")
        bpy.ops.object.select_all(action='DESELECT')
        fluidUnionSolid.select = True
        fluidMinusSolid.select = True
        bpy.ops.object.delete()

        # wetted = FMS - FUS
        print("   set operation FMS diff FUS")
        setWetFaces = setFMSfaces.difference(setFUSfaces)
        print("   build wetted mesh")
        verts, faces = buildMesh(setWetFaces, faceDict, vertDict)
        print("   create wetted mesh")
        wetted = createMesh("Wetted", verts, faces)

        # fluid = FMS x FUS
        print("   set operation FMS intersect FUS")
        setFluidFaces = setFMSfaces.intersection(setFUSfaces)
        print("   build fluid mesh")
        verts, faces = buildMesh(setFluidFaces, faceDict, vertDict)
        print("   create fluid mesh")
        fluid = createMesh("Fluid", verts, faces)
        
        # solid = FUS - FMS
        print("   set operation FUS diff FMS")
        setSolidFaces = setFUSfaces.difference(setFMSfaces)
        print("   build solid mesh")
        verts, faces = buildMesh(setSolidFaces, faceDict, vertDict)
        print("   create solid mesh")
        solid = createMesh("Solid", verts, faces)
        
        # parent wetted mesh
        print("   parent mesh")
        bpy.ops.object.add(type='EMPTY')
        wettedMesh = context.object
        solid.select = True
        fluid.select = True
        wetted.select = True
        wettedMesh.select = True
        bpy.ops.object.parent_set(type='OBJECT')
        wettedMesh.name = 'WettedMesh'
        
        print("add_wetted_mesh done")
        self.statusMessage = 'created '+wettedMesh.name

        return {'FINISHED'}


### Registration ###
def register():
    bpy.utils.register_class(VIEW3D_PT_tools_WettedMesh)
    bpy.utils.register_class(AddWettedMesh)


def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_tools_WettedMesh)
    bpy.utils.unregister_class(AddWettedMesh)

if __name__ == "__main__":
    register()


#
# KD tree (used to create a geometric index of mesh vertices)
#

def distance(a, b):
    return (a-b).length

Node = collections.namedtuple("Node", 'point axis label left right')

class KDTree(object):
    """A tree for nearest neighbor search in a k-dimensional space.

    For information about the implementation, see
    http://en.wikipedia.org/wiki/Kd-tree

    Usage:
    objects is an iterable of (co, index) tuples (so MeshVertex is useable)
    k is the number of dimensions (=3)
    
    t = KDTree(k, objects)
    point, label, distance = t.nearest_neighbor(destination)
    """

    def __init__(self, k, objects=[]):

        def build_tree(objects, axis=0):

            if not objects:
                return None

            objects.sort(key=lambda o: o.co[axis])
            median_idx = len(objects) // 2
            median_point = objects[median_idx].co
            median_label = objects[median_idx].index

            next_axis = (axis + 1) % k
            return Node(median_point, axis, median_label,
                        build_tree(objects[:median_idx], next_axis),
                        build_tree(objects[median_idx + 1:], next_axis))

        self.root = build_tree(list(objects))
        self.size = len(objects)


    def nearest_neighbor(self, destination):

        best = [None, None, float('inf')]
        # state of search: best point found, its label,
        # lowest distance

        def recursive_search(here):

            if here is None:
                return
            point, axis, label, left, right = here

            here_sd = distance(point, destination)
            if here_sd < best[2]:
                best[:] = point, label, here_sd

            diff = destination[axis] - point[axis]
            close, away = (left, right) if diff <= 0 else (right, left)

            recursive_search(close)
            if math.fabs(diff) < best[2]:
                recursive_search(away)

        recursive_search(self.root)
        return best[0], best[1], best[2]


#
# helper functions
#

# get super-selected object and other object from selected pair
def getSelectedPair(context):
    objA = context.object
    objB = context.selected_objects[0]
    if objA == objB:
        objB = context.selected_objects[1]
    return (objA, objB)

# get a unified vertex id for given coordinates
def unifiedVertexId(kdtrees, location, vertDict):
    eps = 0.0001
    offset = 0
    for t in kdtrees:
        co, index, d = t.nearest_neighbor(location)
        if d < eps:
            uvid = offset + index
            if uvid not in vertDict:
                vertDict[uvid] = co
            return uvid
        offset += t.size
    return -1

# get a unified face id tuple
#    Stores the ordered face id tuple in faceDict
#    and the used coordinates for vertex id in vertDict.
#    cacheDict caches the unified vertex id (lookup in kdtree is expensive).
#    For each mesh (where the face belongs to) a separate cacheDict is expected.
def unifiedFaceId(kdtrees, face, vertices, faceDict, vertDict, cacheDict):
    fids = [ ]
    for v in face.vertices:
        uvid = cacheDict.get(v)
        if uvid == None:
            uvid = unifiedVertexId(kdtrees, vertices[v].co, vertDict)
            cacheDict[v] = uvid
        fids.append(uvid)
    ofids = tuple(fids)
    fids.sort()
    fuid = tuple(fids)
    if fuid not in faceDict:
        faceDict[fuid] = ofids
    return fuid

# build vertex and face array from unified face sets
def buildMesh(unifiedFaceSet, faceDict, vertDict):
    verts = [ ]
    nextV = 0
    myV = { }
    faces = [ ]
    for uf in unifiedFaceSet:
        of = faceDict[uf]
        myf = [ ]
        for uV in of:
            v = myV.get(uV)
            if v == None:
                v = nextV
                myV[uV] = nextV
                verts.append(vertDict[uV])
                nextV += 1
            myf.append(v)
        faces.append(myf)
    return verts, faces

# create mesh object and link to scene
def createMesh(name, verts, faces):
    me = bpy.data.meshes.new(name+"Mesh")
    ob = bpy.data.objects.new(name, me)
    ob.show_name = True
    bpy.context.scene.objects.link(ob)
    me.from_pydata(verts, [], faces)
    me.update(calc_edges=True)
    return ob
