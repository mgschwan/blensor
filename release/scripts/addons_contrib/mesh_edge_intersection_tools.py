'''
BEGIN GPL LICENSE BLOCK

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software Foundation,
Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

END GPL LICENCE BLOCK
'''

bl_info = {
    "name": "Edge tools : tinyCAD VTX",
    "author": "zeffii",
    "version": (0, 5, 1),
    "blender": (2, 56, 0),
    "category": "Mesh",
    "location": "View3D > EditMode > (w) Specials",
    "warning": "Still under development",
    "wiki_url": "http://wiki.blender.org/index.php/"\
        "Extensions:2.6/Py/Scripts/Modeling/Edge_Slice",
    "tracker_url": "http://projects.blender.org/tracker/"\
        "?func=detail&aid=25227"
   }

"""
parts based on Keith (Wahooney) Boshoff, cursor to intersection script and
Paul Bourke's Shortest Line Between 2 lines, and thanks to PKHG from BA.org
for attempting to explain things to me that i'm not familiar with.
TODO: [ ] allow multi selection ( > 2 ) for Slice/Weld intersection mode
TODO: [ ] streamline this code !

1) Edge Extend To Edge ( T )
2) Edge Slice Intersecting ( X )
3) Edge Project Converging  ( V )

"""

import bpy
import sys
from mathutils import Vector, geometry
from mathutils.geometry import intersect_line_line as LineIntersect

VTX_PRECISION = 1.0e-5 # or 1.0e-6 ..if you need

#   returns distance between two given points
def mDist(A, B): return (A-B).length


#   returns True / False if a point happens to lie on an edge
def isPointOnEdge(point, A, B):
    eps = ((mDist(A, B) - mDist(point,B)) - mDist(A,point))
    if abs(eps) < VTX_PRECISION: return True
    else:
        print('distance is ' + str(eps))
        return False


#   returns the number of edges that a point lies on.
def CountPointOnEdges(point, outer_points):
    count = 0
    if(isPointOnEdge(point, outer_points[0][0], outer_points[0][1])): count+=1
    if(isPointOnEdge(point, outer_points[1][0], outer_points[1][1])): count+=1
    return count


#   takes Vector List and returns tuple of points in expected order. 
def edges_to_points(edges):
    (vp1, vp2) = (Vector((edges[0][0])), Vector((edges[0][1])))
    (vp3, vp4) = (Vector((edges[1][0])), Vector((edges[1][1])))
    return (vp1,vp2,vp3,vp4)


#   takes a list of 4 vectors and returns True or False depending on checks
def checkIsMatrixCoplanar(verti):
    (v1, v2, v3, v4) = edges_to_points(verti)   #unpack
    shortest_line = LineIntersect(v1, v2, v3, v4)
    if mDist(shortest_line[1], shortest_line[0]) > VTX_PRECISION: return False
    else: return True


#   point = the halfway mark on the shortlest line between two lines
def checkEdges(Edge, obj):
    (p1, p2, p3, p4) = edges_to_points(Edge)
    line = LineIntersect(p1, p2, p3, p4)
    point = ((line[0] + line[1]) / 2) # or point = line[0]
    return point

#   returns (object, number of verts, number of edges) && object mode == True
def GetActiveObject():
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.delete(type='EDGE') # removes edges + verts
    (vert_count, edge_count) = getVertEdgeCount()
    (vert_num, edge_num) = (len(vert_count),len(edge_count))

    bpy.ops.object.mode_set(mode='OBJECT') # to be sure.
    o = bpy.context.active_object
    return (o, vert_num, edge_num)


def AddVertsToObject(vert_count, o, mvX, mvA, mvB, mvC, mvD):
    o.data.vertices.add(5)
    pointlist = [mvX, mvA, mvB, mvC, mvD]
    for vpoint in range(len(pointlist)):
        o.data.vertices[vert_count+vpoint].co = pointlist[vpoint]


#   Used when the user chooses to slice/Weld, vX is intersection point
def makeGeometryWeld(vX,outer_points):
    (o, vert_count, edge_count) =  GetActiveObject()
    (vA, vB, vC, vD) =  edges_to_points(outer_points)
    AddVertsToObject(vert_count, o, vA, vX, vB, vC, vD) # o is the object

    oe = o.data.edges
    oe.add(4)
    oe[edge_count].vertices = [vert_count,vert_count+1]
    oe[edge_count+1].vertices = [vert_count+2,vert_count+1]
    oe[edge_count+2].vertices = [vert_count+3,vert_count+1]
    oe[edge_count+3].vertices = [vert_count+4,vert_count+1]


#   Used for extending an edge to a point on another edge.
def ExtendEdge(vX, outer_points, count):
    (o, vert_count, edge_count) =  GetActiveObject()
    (vA, vB, vC, vD) =  edges_to_points(outer_points)
    AddVertsToObject(vert_count, o, vX, vA, vB, vC, vD)

    oe = o.data.edges
    oe.add(4)
    # Candidate for serious optimization.
    if isPointOnEdge(vX, vA, vB):
        oe[edge_count].vertices = [vert_count, vert_count+1]
        oe[edge_count+1].vertices = [vert_count, vert_count+2]
        # find which of C and D is farthest away from X
        if mDist(vD, vX) > mDist(vC, vX):
            oe[edge_count+2].vertices = [vert_count, vert_count+3]
            oe[edge_count+3].vertices = [vert_count+3, vert_count+4]
        if mDist(vC, vX) > mDist(vD, vX):
            oe[edge_count+2].vertices = [vert_count, vert_count+4]
            oe[edge_count+3].vertices = [vert_count+3, vert_count+4]

    if isPointOnEdge(vX, vC, vD):
        oe[edge_count].vertices = [vert_count, vert_count+3]
        oe[edge_count+1].vertices = [vert_count, vert_count+4]
        # find which of A and B is farthest away from X 
        if mDist(vB, vX) > mDist(vA, vX):
            oe[edge_count+2].vertices = [vert_count, vert_count+1]
            oe[edge_count+3].vertices = [vert_count+1, vert_count+2]
        if mDist(vA, vX) > mDist(vB, vX):
            oe[edge_count+2].vertices = [vert_count, vert_count+2]
            oe[edge_count+3].vertices = [vert_count+1, vert_count+2]


#   ProjectGeometry is used to extend two edges to their intersection point.
def ProjectGeometry(vX, opoint):

    def return_distance_checked(X, A, B):
        dist1 = mDist(X, A)
        dist2 = mDist(X, B)
        point_choice = min(dist1, dist2)
        if point_choice == dist1: return A, B
        else: return B, A

    (o, vert_count, edge_count) =  GetActiveObject()
    vA, vB = return_distance_checked(vX, Vector((opoint[0][0])), Vector((opoint[0][1])))
    vC, vD = return_distance_checked(vX, Vector((opoint[1][0])), Vector((opoint[1][1])))
    AddVertsToObject(vert_count, o, vX, vA, vB, vC, vD)

    oe = o.data.edges
    oe.add(4)
    oe[edge_count].vertices = [vert_count, vert_count+1]
    oe[edge_count+1].vertices = [vert_count, vert_count+3]
    oe[edge_count+2].vertices = [vert_count+1, vert_count+2]
    oe[edge_count+3].vertices = [vert_count+3, vert_count+4]


def getMeshMatrix(obj):
    is_editmode = (obj.mode == 'EDIT')
    if is_editmode:
        bpy.ops.object.mode_set(mode='OBJECT')

    (edges, meshMatrix) = ([],[])
    mesh = obj.data
    verts = mesh.vertices
    for e in mesh.edges:
        if e.select:
            edges.append(e)

    edgenum = 0
    for edge_to_test in edges:
        p1 = verts[edge_to_test.vertices[0]].co
        p2 = verts[edge_to_test.vertices[1]].co
        meshMatrix.append([Vector(p1),Vector(p2)])
        edgenum += 1

    return meshMatrix


def getVertEdgeCount():
    bpy.ops.object.mode_set(mode='OBJECT')
    vert_count = bpy.context.active_object.data.vertices
    edge_count = bpy.context.active_object.data.edges
    return (vert_count, edge_count)


def runCleanUp():
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='TOGGLE')
    bpy.ops.mesh.select_all(action='TOGGLE')
    bpy.ops.mesh.remove_doubles(threshold=VTX_PRECISION)
    bpy.ops.mesh.select_all(action='TOGGLE') #unselect all


def initScriptV(context, self):
    obj = bpy.context.active_object
    meshMatrix = getMeshMatrix(obj)
    (vert_count, edge_count) = getVertEdgeCount()

    #need 2 edges to be of any use.
    if len(meshMatrix) < 2: 
        print(str(len(meshMatrix)) +" select, make sure (only) 2 are selected")
        return

    #dont go any further if the verts are not coplanar
    if checkIsMatrixCoplanar(meshMatrix): print("seems within tolerance, proceed")
    else: 
        print("check your geometry, or decrease tolerance value")
        return

    # if we reach this point, the edges are coplanar
    # force edit mode
    bpy.ops.object.mode_set(mode='EDIT')
    vSel = bpy.context.active_object.data.total_vert_sel

    if checkEdges(meshMatrix, obj) == None: print("lines dont intersect")
    else:
        count = CountPointOnEdges(checkEdges(meshMatrix, obj), meshMatrix)
        if count == 0:
            ProjectGeometry(checkEdges(meshMatrix, obj), meshMatrix)
            runCleanUp()
        else:
            print("The intersection seems to lie on 1 or 2 edges already")


def initScriptT(context, self):
    obj = bpy.context.active_object
    meshMatrix = getMeshMatrix(obj)
    ## force edit mode
    bpy.ops.object.mode_set(mode='EDIT')
    vSel = bpy.context.active_object.data.total_vert_sel

    if len(meshMatrix) != 2:
        print(str(len(meshMatrix)) +" select 2 edges")
    else:
        count = CountPointOnEdges(checkEdges(meshMatrix, obj), meshMatrix)
        if count == 1:
            print("Good, Intersection point lies on one of the two edges!")
            ExtendEdge(checkEdges(meshMatrix, obj), meshMatrix, count)
            runCleanUp()    #neutral function, for removing potential doubles
        else:
            print("Intersection point not on chosen edges")


def initScriptX(context, self):
    obj = bpy.context.active_object
    meshMatrix = getMeshMatrix(obj)
    ## force edit mode
    bpy.ops.object.mode_set(mode='EDIT')

    if len(meshMatrix) != 2:
        print(str(len(meshMatrix)) +" select, make sure (only) 2 are selected")
    else:
        if checkEdges(meshMatrix, obj) == None:
            print("lines dont intersect")
        else: 
            count = CountPointOnEdges(checkEdges(meshMatrix, obj), meshMatrix)
            if count == 2:
                makeGeometryWeld(checkEdges(meshMatrix, obj), meshMatrix)
                runCleanUp()


class EdgeIntersections(bpy.types.Operator):
    """Makes a weld/slice/extend to intersecting edges/lines"""
    bl_idname = 'mesh.intersections'
    bl_label = 'Edge tools : tinyCAD VTX'
    # bl_options = {'REGISTER', 'UNDO'}

    mode = bpy.props.IntProperty(name = "Mode",
                    description = "switch between intersection modes",
                    default = 2)

    @classmethod
    def poll(self, context):
        obj = context.active_object
        return obj != None and obj.type == 'MESH'

    def execute(self, context):
        if self.mode == -1:
            initScriptV(context, self)
        if self.mode == 0:
            initScriptT(context, self)
        if self.mode == 1:
            initScriptX(context, self)
        if self.mode == 2:
            print("something undefined happened, send me a test case!")
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(EdgeIntersections.bl_idname, text="Edges V Intersection").mode = -1
    self.layout.operator(EdgeIntersections.bl_idname, text="Edges T Intersection").mode = 0
    self.layout.operator(EdgeIntersections.bl_idname, text="Edges X Intersection").mode = 1

def register():
    bpy.utils.register_class(EdgeIntersections)
    bpy.types.VIEW3D_MT_edit_mesh_specials.append(menu_func)

def unregister():
    bpy.utils.unregister_class(EdgeIntersections)
    bpy.types.VIEW3D_MT_edit_mesh_specials.remove(menu_func)

if __name__ == "__main__":
    register()
