#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you may redistribute it, and/or
# modify it, under the terms of the GNU General Public License
# as published by the Free Software Foundation - either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, write to:
#
#	the Free Software Foundation Inc.
#	51 Franklin Street, Fifth Floor
#	Boston, MA 02110-1301, USA
#
# or go online at: http://www.gnu.org/licenses/ to view license options.
#
# ***** END GPL LICENCE BLOCK *****
#

bl_info = {
    "name": "Columns",
    "author": "Jim Bates, jambay",
    "version": (0, 11),
    "blender": (2, 5, 7),
    "location": "View3D > Add > Mesh > Columns",
    "description": "Add architectural column(s).",
    "warning": "WIP - Initial implementation; updates pending and API not final for Blender",
    "wiki_url": "http://www.uthynq.com/JBDoc/index.php?title=Column",
    "tracker_url": "http://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=27655",
    "category": "Add Mesh"
}


'''

Create a column for use as an architectural element in a scene. Basically a glorified cylinder/cube.

A column consists of three elements; base, shaft, and capital. They can be square or round, straight or tapered.
 The base and capital are optional.

The shaft may be fluted and twisted.

Only one column is created, at the current 3D cursor, expecting the user to duplicate and place as needed.

This script is based on features from add_mesh_gears, add_curve_aceous_galore.py, and add_mesh_BoltFactory/createMesh.py.

'''

#
# List of "enhancements"/"fixes" needed to finalize this script.
#
# @todo: Round top and bottom of flutes.
# @todo: Add "plinth" (square platform) to base and "finale" for capital - different proportions for base and capital but same objective.
# @todo: Create Ionic and Corinthian style capitals. External "mesh", quadrant, mirror-x, select all/join, then mirror-y.
#    will need to "scale" to match column radius (size to column).
# @todo: Allow control of negative radius for base and column functions.
#    Interesting effect (inverts), but want to use separate from column setting.
#


# Version History
# v0.11 2011/06/14	Added width parameter for base and capital.
# v0.10 2011/06/13	Consolidated base and capital "add" functions. More styles. Fixed taper with negative radius.
# v0.09 2011/06/06	Column fluting - 90%. Added "sides" parameter for flutes, not sure I want to fix "odd" behavior.
# v0.08 2011/05/24	Common function to generate base and capitals, more types added.
# v0.07 2011/05/21	Added Capitals, more base types, general cleanup.
# v0.06 2011/05/20	Changed radius usage, separated base from column and use spin to generate base.
# v0.05 2011/05/19	Added closing faces (top and bottom) to base and column.
# v0.04 2011/05/17	Major "cleanup"; Flutes now not square, but not rounded either.
# v0.03 2011/05/16	Made "flutes" a value; added taper and base options to UI; added wiki and tracker links.
# v0.02 2011/05/14	UI mods and param checks added.
# v0.01 2011/05/13	Initial implementation.


import bpy
import mathutils
from math import *
from bpy.props import *

# A very simple "bridge" tool.
# Connects two equally long vertex rows with faces.
# Returns a list of the new faces (list of  lists)
#
# vertIdx1 ... First vertex list (list of vertex indices).
# vertIdx2 ... Second vertex list (list of vertex indices).
# closed ... Creates a loop (first & last are closed).
# flipped ... Invert the normal of the face(s).
#
# Note: You can set vertIdx1 to a single vertex index to create
#       a fan/star of faces.
# Note: If both vertex idx list are the same length they have
#       to have at least 2 vertices.
def createFaces(vertIdx1, vertIdx2, closed=False, flipped=False):
    faces = []

    if not vertIdx1 or not vertIdx2:
        return None

    if len(vertIdx1) < 2 and len(vertIdx2) < 2:
        return None

    fan = False
    if (len(vertIdx1) != len(vertIdx2)):
        if (len(vertIdx1) == 1 and len(vertIdx2) > 1):
            fan = True
        else:
            return None

    total = len(vertIdx2)

    if closed:
        # Bridge the start with the end.
        if flipped:
            face = [
                vertIdx1[0],
                vertIdx2[0],
                vertIdx2[total - 1]]
            if not fan:
                face.append(vertIdx1[total - 1])
            faces.append(face)

        else:
            face = [vertIdx2[0], vertIdx1[0]]
            if not fan:
                face.append(vertIdx1[total - 1])
            face.append(vertIdx2[total - 1])
            faces.append(face)

    # Bridge the rest of the faces.
    for num in range(total - 1):
        if flipped:
            if fan:
                face = [vertIdx2[num], vertIdx1[0], vertIdx2[num + 1]]
            else:
                face = [vertIdx2[num], vertIdx1[num],
                    vertIdx1[num + 1], vertIdx2[num + 1]]
            faces.append(face)
        else:
            if fan:
                face = [vertIdx1[0], vertIdx2[num], vertIdx2[num + 1]]
            else:
                face = [vertIdx1[num], vertIdx2[num],
                    vertIdx2[num + 1], vertIdx1[num + 1]]
            faces.append(face)

    return faces


#####
#
# @todo: fine-tune curvature for flutes.
# @todo: handle odd number of sides (flat in middle).
#
def add_col_flute(angle, target, zpos, radius, Ad, sides=6):
    '''
 Create "flute" for column at passed location.

    Parameters:
        angle - starting point for column faces.
            (type=float)
        target - angle offset to end point for column faces.
            (type=float)
        zpos - vertical position for vertices.
            (type=float)
        radius - column face radius from current 3D cursor position.
            (type=float)
        Ad - Flute "depth" offset from radius
            (type=float)
        sides - number of faces for flute
            (type=int)

    Returns:
        newpoints - a list of coordinates for flute points (list of tuples), [[x,y,z],[x,y,z],...n]
            (type=list)
    '''
    newpoints = []

    if sides < 2: sides = 2 # min number of sides.

    halfSides = sides/2 # common value efficiency variable.

    stepD = Ad/halfSides # in and out depth variation per side.

    divSides = 0
    curStep = 1

    while curStep <= halfSides:
        divSides += curStep*curStep
        curStep+=1

    stepCurve = target/(divSides*2) # logorithmic delta along radius for sides.

    curStep = 0

    t = angle

    # curvature in
    while curStep < halfSides:
        t = t + (curStep*curStep*stepCurve)
        x1 = (radius - (stepD * (curStep+1))) * cos(t)
        y1 = (radius - (stepD * (curStep+1))) * sin(t)
        newpoints.append([x1, y1, zpos])
        curStep+=1

    # curvature out - includes mid-point, and end-point...
    while curStep:
        t = t + (curStep*curStep*stepCurve)
        x1 = (radius - (stepD * curStep)) * cos(t)
        y1 = (radius - (stepD * curStep)) * sin(t)
        newpoints.append([x1, y1, zpos])
        curStep-=1

    return newpoints


# save a copy of add_col_flute, v 0.8, in case it gets "fixed"...
# makes flower petal/notch effect...
def add_notch(angle, target, zpos, radius, Ad, sides=6):

    newpoints = []

    if sides < 2: sides = 2 # min number of sides.

    stepD = Ad/(sides/2) # in and out depth variation per side.
    stepCurve = target/sides # points along radius for sides.

    curStep = 0

    # curvature in
    while curStep < sides/2:
        t = angle + (curStep*stepCurve)
        x1 = (radius - (stepD * curStep)) * cos(t)
        y1 = (radius - (stepD * curStep)) * sin(t)
        newpoints.append([x1, y1, zpos])
        curStep+=1

    # curvature out
    while curStep:
        t = angle + ((sides-curStep)*stepCurve)
        x1 = (radius - (stepD * curStep)) * cos(t)
        y1 = (radius - (stepD * curStep)) * sin(t)
        newpoints.append([x1, y1, zpos])
        curStep-=1

    # add the end point
    x1 = radius * cos(angle+target)
    y1 = radius * sin(angle+target)
    newpoints.append([x1, y1, zpos])

    return newpoints


# save a copy of add_col_flute, v 0.4, in case it gets "fixed"...
# this makes some interesting "fans" when addendum is more than radius
def add_sawtooth(angle, target, zpos, radius, Ad, sides=6):
    newpoints = []

    step = target/sides
    stepD = Ad/sides

    i = 0
    while i < sides:
        t = angle + (i*step)
        x1 = (radius - (stepD*i)) * cos(t)
        y1 = (radius - (stepD*i)) * sin(t)
        newpoints.append([x1, y1, zpos])
        i+=1

    return newpoints


# save a copy of add_col_flute, v 0.5, in case it gets "fixed"...
# this makes some interesting "fans" when addendum is more than radius
def add_sawtooth2(angle, target, zpos, radius, Ad, sides=6):
    newpoints = []

    step = target/sides
    stepD = Ad/(sides/2)

    # First point
    x1 = radius * cos(angle)
    y1 = radius * sin(angle)
    newpoints.append([x1, y1, zpos])

    # curve in...
    i = 0
    while i < sides/2:
        t = angle + (i*step)
        x1 = (radius - (stepD * i)) * cos(t)
        y1 = (radius - (stepD * i)) * sin(t)
        newpoints.append([x1, y1, zpos])
        i+=1

    # curve out...
    while i:
        t = angle + ((sides - i)*step)
        x1 = (radius - (stepD * i)) * cos(t)
        y1 = (radius - (stepD * i)) * sin(t)
# Interesting... not "regular" if this is only change.
#        y1 = (radius + (stepD * (sides - i))) * sin(t)
        newpoints.append([x1, y1, zpos])
        i-=1

# Also cool -
    # curve out... jagged.
#    while i:
#        t = angle + ((sides - i)*step)
#        x1 = (radius + (stepD * i)) * cos(t)
#        y1 = (radius + (stepD * i)) * sin(t)
#        newpoints.append([x1, y1, zpos])
#        i-=1

    # end point
    x1 = radius * cos(angle+step*(sides-1))
    y1 = radius * sin(angle+step*(sides-1))
    newpoints.append([x1, y1, zpos])

    return newpoints


#####
def add_col_face(angle, target, zpos, radius):
    '''
Calculate the vertex coordinates for column face.

    Parameters:
        angle - starting point for column faces.
            (type=float)
        target - end point for column faces.
            (type=float)
        zpos - vertical position for vertices.
            (type=float)
        radius - column face radius from current 3D cursor position.
            (type=float)

    Returns:
        a list of coordinates for column face points (list of four tuples), [[x,y,z],[x,y,z],...4]
            (type=list)
    '''
    targStep = target/4

    verts_outer_face = [(radius * cos(angle+(targStep*I)), radius * sin(angle+(targStep*I)), zpos)
        for I in range(4)]

    return (verts_outer_face)


#####
#
# Returns a list of faces that makes up a fill pattern for a circle.
# copied from add_mesh_BoltFactory/createMesh.py - works like fill.
#
# @todo: replace this with call to mesh.fill() - must have mesh, and select vertices.
#
def Fill_Ring_Face(OFFSET, NUM, FACE_DOWN = 0):
    Ret =[]
    Face = [1,2,0]
    TempFace = [0,0,0]
    A = 0
    B = 1
    C = 2
    if NUM < 3:
        return None
    for i in range(NUM-2):
        if (i%2):
            TempFace[0] = Face[C];
            TempFace[1] = Face[C] + 1;
            TempFace[2] = Face[B];
            if FACE_DOWN:
                Ret.append([OFFSET+Face[2],OFFSET+Face[1],OFFSET+Face[0]])
            else:
                Ret.append([OFFSET+Face[0],OFFSET+Face[1],OFFSET+Face[2]])
        else:
            TempFace[0] =Face[C];
            if Face[C] == 0:
                TempFace[1] = NUM-1; 
            else:
                TempFace[1] = Face[C] - 1;
            TempFace[2] = Face[B];
            if FACE_DOWN:
                Ret.append([OFFSET+Face[0],OFFSET+Face[1],OFFSET+Face[2]])
            else:
                Ret.append([OFFSET+Face[2],OFFSET+Face[1],OFFSET+Face[0]])
        
        Face[0] = TempFace[0]
        Face[1] = TempFace[1]
        Face[2] = TempFace[2]
    return Ret


#####
#
# Common/shared function to create base or capital.
#
#    May need to separate in future but handy for now for "simple" styles. Simply use "menu select" to set type for
#    base or capital if they shouldn't be same.
#
def add_extent(radius, height, width, zPos, type=1):
    '''
Create geometry for base/capital (shared function).

    Params:
	radius    area of the column (inner vertice for base/capital).
	height    height of base/capital.
	width     width (radius) of base/capital.
        zPos      vertical origin (base height+column height for capital, zero for base).
        type      type of base/capital to generate.

    Returns:
	list of vertices and edges

    '''
    verts = []
    edges = []

    if type == 2: # Angled
        verts, edges = makeProfile(radius, zPos, 0, height, width, 2, 1, 1, False, False)
        return verts, edges

    if type == 3: #  straight half-Beveled half
        verts, edges = makeProfile(radius, zPos, 0, height, width, 1, 1, 1, False, False)
        return verts, edges

    if type == 4: # Rounded
        verts, edges = makeProfile(radius, zPos, 0, height, width, 6, 1.2, 0.05, True, False)
        return verts, edges

    if type == 5: # Curved
        verts, edges = makeProfile(radius, zPos, 0, height, width, 6, 1.2, 0.05)
        return verts, edges

    if type == 6: # Bird-bath overshot
        verts, edges = makeProfile(radius, zPos, 0, height, width, 6, 1.0, 0.15, False)
        return verts, edges

    if type == 7: # Complex type....
        verts1, edges1 = makeProfile(radius, zPos, radius, height/2, width/2, 6, 1.2, 0.05)
        verts.extend(verts1)
        edges.extend(edges1)

        edges.append([len(edges), len(edges)+1]) # add connector edge...
        verts1, edges1 = makeProfile(radius, zPos+height/2, 0, height/2, width/2, 0, 0, 0, False, False, len(edges) )
        verts.extend(verts1)
        edges.extend(edges1)

        return verts, edges

    if type == 8: # Complex type.... 2
        verts1, edges1 = makeProfile(radius, zPos, radius, height/4, width/4, 6, 1.2, 0.05)
        verts.extend(verts1)
        edges.extend(edges1)

        edges.append([len(edges), len(edges)+1]) # add connector edge...
        verts1, edges1 = makeProfile(radius, zPos+height/4, radius, height/4, width/4, 0, 0, 0, False, False, len(edges) )
        verts.extend(verts1)
        edges.extend(edges1)

        edges.append([len(edges), len(edges)+1]) # add connector edge...
        verts1, edges1 = makeProfile(radius, zPos+height/2, 0, height/2, width/2, 2, 1, 1, False, False, len(edges) )
        verts.extend(verts1)
        edges.extend(edges1)

        return verts, edges

    if type == 9: # Complex type.... 3
# @todo: figure out "inner" connectors without using makeProfile...
        workZ = zPos # track "base" for each segment.

        verts1, edges1 = makeProfile(radius, workZ, radius, height/8, width/4, 0, 0, 0, False, False)
        verts.extend(verts1)
        edges.extend(edges1)

        workZ += height/8

        edges.append([len(edges), len(edges)+1]) # add connector edge...
        verts1, edges1 = makeProfile(radius, workZ, radius, height/4, width/4, 6, 1.2, 0.05, startRow=len(edges) )
        verts.extend(verts1)
        edges.extend(edges1)

        workZ += height/4

        edges.append([len(edges), len(edges)+1]) # add connector edge...
        verts1, edges1 = makeProfile(radius-width/4, workZ, radius-width/4, height/8, width/4, 0, 0, 0, False, False, len(edges) )
        verts.extend(verts1)
        edges.extend(edges1)

        workZ += height/8

        edges.append([len(edges), len(edges)+1]) # add connector edge...
        verts1, edges1 = makeProfile(radius-width/4, workZ, radius-width/4, height/8, width/4, 6, 1.2, 0.05, startRow=len(edges) )
        verts.extend(verts1)
        edges.extend(edges1)

# should be height/8 but usiing height/4 to fill out height. Makes inner "straight edge" connector without makeProfile.
        workZ += height/4

        edges.append([len(edges), len(edges)+1]) # add connector edge...
        verts1, edges1 = makeProfile(radius-width/4, workZ, 0, height/4, width/2, 2, 1, 1, False, False, len(edges) )
        verts.extend(verts1)
        edges.extend(edges1)

        return verts, edges

    if type == 10: # Complex type.... Doric, Sans square topping.
        workZ = zPos # track "base" for each segment.

        verts1, edges1 = makeProfile(radius, workZ, radius, height/8, width/8, 0, 0, 0, False, False)
        verts.extend(verts1)
        edges.extend(edges1)

        workZ += height/8

        edges.append([len(edges), len(edges)+1]) # add connector edge...
        verts1, edges1 = makeProfile(radius, workZ, radius, height/8, width/4, 6, 1.2, 0.05, startRow=len(edges) )
        verts.extend(verts1)
        edges.extend(edges1)

# should be height/8 but usiing height/4 to fill out height. Makes inner "straight edge" connector without makeProfile.
        workZ += height/4

        edges.append([len(edges), len(edges)+1]) # add connector edge...
        verts1, edges1 = makeProfile(radius-width/4, workZ, radius-width/4, height/8, width/2, 0, 0, 0, False, False, len(edges) )
        verts.extend(verts1)
        edges.extend(edges1)

        workZ += height/4

        edges.append([len(edges), len(edges)+1]) # add connector edge...
        verts1, edges1 = makeProfile(radius-width/4, workZ, radius-width/4, height/8, width/4, 6, 1.2, 0.05, startRow=len(edges) )
        verts.extend(verts1)
        edges.extend(edges1)

# using different height accumulation value (more or less) makes inner "edge connector" without makeProfile.
# should be height/8 but usiing height/4 to fill out height. Makes inner "straight edge" connector without makeProfile.
        workZ += height/8

        edges.append([len(edges), len(edges)+1]) # add connector edge...
        verts1, edges1 = makeProfile(radius, workZ, 0, height/4, width, 6, 1.3, 0.05, True, False, len(edges))
        verts.extend(verts1)
        edges.extend(edges1)

        return verts, edges

    if type == 11: # Complex type.... Doric, attempt square topping 2.
        workZ = zPos # track "base" for each segment.

        # square step - 1/8th.
        workHeight = height/8
        verts1, edges1 = makeProfile(radius, workZ, radius, workHeight, width/10, 0, 0, 0, False, False)
        verts.extend(verts1)
        edges.extend(edges1)

        workZ += workHeight # accumulate offset...

        # Rounded step - 1/8th; offset from radius reduction...
#        workHeight = height/8
        edges.append([len(edges), len(edges)+1]) # add connector edge...
        verts1, edges1 = makeProfile(radius-width/4, workZ, radius-width/4, workHeight, width/2, 6, 1.2, 0.05, startRow=len(edges) )
        verts.extend(verts1)
        edges.extend(edges1)

# using different height accumulation value (more or less) makes inner "edge connector" without makeProfile.
#        workZ += height/8
        workZ += workHeight # accumulate offset...

        # inverted round - half-height
        workHeight = height/2
        edges.append([len(edges), len(edges)+1]) # add connector edge...
        verts1, edges1 = makeProfile(radius, workZ, radius, workHeight, width/8, 6, -1.2, 0.05, startRow=len(edges) )
        verts.extend(verts1)
        edges.extend(edges1)

        workZ += workHeight # accumulate offset...
# using different height accumulation value (more or less) makes inner "edge connector" without makeProfile.
#        workZ += height/4 # Added to workZ after previous line - "normal accumulation"; caused "criss-cross" connection...
# and overstepped height - which is fine, except for criss-cross thing.

        # Rounded step - 1/8th; offset from radius reduction...
        workHeight = height/8
        edges.append([len(edges), len(edges)+1]) # add connector edge...
        verts1, edges1 = makeProfile(radius-width/4, workZ, radius-width/4, workHeight, width, 6, 1.2, 0.05, startRow=len(edges) )
        verts.extend(verts1)
        edges.extend(edges1)

        workZ += workHeight # accumulate offset...

        # Curved step - 1/8th.
#        workHeight = height/8
        edges.append([len(edges), len(edges)+1]) # add connector edge...
        verts1, edges1 = makeProfile(radius, workZ, 0, workHeight, width, 6, 1.3, 0.05, True, False, len(edges))
        verts.extend(verts1)
        edges.extend(edges1)

        return verts, edges

# default, type 1 - straight side, full height.
    verts, edges = makeProfile(radius, zPos, 0, height, width, 0, 0, 0)
    return verts, edges


#####
#
# x is always zero. This is just a series of vertexes... on a plane (zero X) for spin dupli-replication.
#
# Expect that results are pairs, 0,1 (edgeSets) - two minimum (0,1).
#
# @todo: Fix for starts, or factors not valid; return default (square) values on error.
#
def makeProfile(startY, startZ, endY, height, width, facets, factor1, factor2, doubler=True, twoPart=True, startRow=0):
    '''
Create list of vertexes and edges that outline defined shape (as per parameters).

    Params:
	startY    Radius origin for vertexes.
	startZ    Vertical origin.
        endY      Radius end-point for vertexes.
        height    Vertical offset from startZ for shape.
        width     Horizontal dimension of shape.
        facets    Number of edges (rows), use 0 for straight.
        factor1   Horizontal multiplier.
        factor2   Vertical multiplier, used with doubler.
        doubler   Square factor2 for each facet if true.
        twoPart   Repeat inverse of shape if true.
        startRow  Edge list offset for concatenated shapes.

    Returns:
	list of vertices and edges

    '''

    # start here...
    shapeVerts = []
    shapeEdges = [] # invalid at this point.

    halfHeight = height/2 # common calculated value, effeciency.
    halfWidth = width/2 # common calculated value, effeciency.

    capRadius = startY+halfWidth # "working radius" for base/capital.

    if not facets:
        rowVariance = 0
        twoPart = False # override default for square.
    else:
        rowVariance = halfWidth/facets # width / 2 / number of angles to curve edge

    workFactor = 0

    shapeVerts.append([0, startY, startZ]) # starting point
    numRows = startRow

    for Ivec in range(facets): # skipped if no facets

        if not doubler:
            workFactor = Ivec * factor2

        shapeVerts.append([0, capRadius+rowVariance*(Ivec*factor1), startZ+halfHeight*workFactor])
        shapeEdges.append([numRows, numRows+1])
        numRows += 1

        if doubler:
            if Ivec:
                workFactor *= 2
            else:
                workFactor = factor2

    # middle row... outer edge; bottom if no facets.

    if not facets: # square?
        workY = capRadius+halfWidth
        workZ = startZ
    else: # shaped
        workY = capRadius+rowVariance*((facets-1)*factor1)
        workZ = startZ+halfHeight

    shapeVerts.append([0, workY, workZ])

    shapeEdges.append([numRows, numRows+1])
    numRows += 1

    # do the middle up part...

    if twoPart:
        for Rvec in range(1,facets): # inverse...

            if not doubler:
                workFactor = Rvec * factor2
            else:
                workFactor /= 2

            shapeVerts.append([0, capRadius+rowVariance*((facets-Rvec)*factor1), startZ+height-halfHeight*workFactor])
            shapeEdges.append([numRows, numRows+1]) 
            numRows += 1

    # end here...

    workZ = startZ+height

    if twoPart: # match top to bottom for rounded styles
        shapeVerts.append([0, capRadius, workZ])
    else:
        shapeVerts.append([0, startY+width, workZ])

    shapeEdges.append([numRows, numRows+1]) # outer edge top
    numRows += 1

    shapeVerts.append([0, endY, workZ])
    shapeEdges.append([numRows, numRows+1]) # last edge....

#    print(shapeVerts)

    return shapeVerts, shapeEdges


#####
#
# @todo: fix closing faces on top/bottom for flutes.
#
def add_column(colBase, radius, taper, c_faces, rows, height, flutes, Ad, fsides, skew, colCap=False):
    '''
Create column geometry.

    Params:
	colBase   starting zPos for column (put on top of base).
	radius    area of the column, negative for flute extrusions.
	taper     radius reduction per row to taper column.
	c_faces   surfaces (faces) on column per quadrant, 1 = square, increase to smooth, max 360, 180 is plenty.
	rows      number of rows/vertical blocks for column. Use +1 to complete row (2 is working min).
	flutes    make curfs, gouges, gear like indents.
	Ad        Addendum, extent of flute from radius.
        fsides    number of "sides" (faces) for flute.
	height    height of column row.
	skew      twist for column, use negative value for left twist.
        colCap    true if adding cap to eliminate top fill.

    Returns:
	list of vertices
	list of faces

    '''
    if flutes: # set working faces and modulo/flag for doing flutes...
        c_faces -= c_faces % flutes
        fluteFaces = c_faces / flutes
    else:
        fluteFaces = 0

    isFluted = False

    t = 2 * pi / c_faces # c_faces == 1 makes a square

    verts = []
    faces = []

    edgeloop_prev = []
    for Row in range(rows):
        edgeloop = []

        if Row: # apply taper to rows after base verts added.
            if radius > 0: 
                radius -= taper # decrease radius
            else:
                radius += taper # will decrease neg radius

        for faceCnt in range(c_faces):
            a = faceCnt * t

            rSkew = Row * skew
            zPos = colBase + Row * height

            if fluteFaces and not faceCnt % fluteFaces: # making "flutes", and due a flute?
                isFluted = True
                verts1 = add_col_flute(a + rSkew, t, zPos, radius, Ad, fsides)

            else: # column surface for section...
                isFluted = False
                verts1 = add_col_face(a + rSkew, t, zPos, radius)

            verts_current = list(range(len(verts), len(verts) + len(verts1)))
            verts.extend(verts1)

            edgeloop.extend(verts_current)

        # Create faces between rings/rows.
        if edgeloop_prev:
            faces.extend(createFaces(edgeloop, edgeloop_prev, closed=True))
        else: # close column bottom if unfluted and no base.
            if not fluteFaces and not colBase:
                faces.extend(Fill_Ring_Face(0, c_faces*4))

        # Remember last ring/row of vertices for next ring/row iteration.
        edgeloop_prev = edgeloop

    # close column top
    if not fluteFaces and not colCap:
        faces.extend(Fill_Ring_Face(len(edgeloop)*(rows-1), c_faces*4))

    return verts, faces


#####
#
class AddColumn(bpy.types.Operator):
    '''
Add a column mesh.

    UI functions and object creation.

    '''
    bl_idname = "mesh.primitive_column"
    bl_label = "Add Column"
    bl_options = {'REGISTER', 'UNDO'}

    radius = FloatProperty(name="Radius",
        description="Radius of the column; use negative to extrude flutes.",
        min=-100.0,
        max=100.0,
        default=1.0)
    taper = FloatProperty(name="Taper",
        description="Radius reduction for taper - cannot exceed radius.",
        min=0.00,
        max=10.0,
        default=0.0)
    col_faces = IntProperty(name="Faces",
        description="Number of faces per quadrant, 1 = square.",
        min=1,
        max=360,
        default=10)
    col_blocks = IntProperty(name="Rows",
        description="Number of blocks in the column",
        min=1,
        max=100,
        default=1)
    row_height = FloatProperty(name="Row Height",
        description="Height of each block row",
        min=0.05,
        max=100.0,
        default=2)
    skew = FloatProperty(name="Skew",
        description="Twist the column (degrees) - neg for left twist.",
        min=-180,
        max=180,
        default=0.00)

    col_flutes = IntProperty(name="Flutes",
        description="Channels on column",
        min=0,
        max=100,
        default=0)
    addendum = FloatProperty(name="Addendum",
        description="flute (depth) offset from radius.",
        min=0.01,
        max=100.0,
        default=0.1)
    flute_sides = IntProperty(name="Sides",
        description="facets for flute",
        min=2,
        max=100,
        default=12)

    col_base = BoolProperty(name="Base",
         description="Column base",
         default = False)
    base_type = IntProperty(name="Type",
        description="Type of base to generate, until menu selection added.",
        min=1,
        max=20,
        default=1)
    base_faces = IntProperty(name="Faces",
        description="Number of faces per quadrant, 1 = square.",
        min=1,
        max=360,
        default=1)
    base_height = FloatProperty(name="Height",
        description="Height of base",
        min=0.05,
        max=10.0,
        default=0.5)
    base_width = FloatProperty(name="Width",
        description="Width of base (radius)",
        min=0.05,
        max=10.0,
        default=0.5)

    col_cap = BoolProperty(name="Capital",
         description="Column capital",
         default = False)
    cap_type = IntProperty(name="Type",
        description="Type of capital to generate, until menu selection added.",
        min=1,
        max=20,
        default=1)
    cap_faces = IntProperty(name="Faces",
        description="Number of faces per quadrant, 1 = square.",
        min=1,
        max=360,
        default=1)
    cap_height = FloatProperty(name="Height",
        description="Height of capital",
        min=0.05,
        max=10.0,
        default=0.5)
    cap_width = FloatProperty(name="Width",
        description="Width of capital (radius)",
        min=0.05,
        max=10.0,
        default=0.5)

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text='Column Sizing')
        box.prop(self, 'radius')
        box.prop(self, 'taper')
        box.prop(self, 'col_faces')
        box.prop(self, 'col_blocks')
        box.prop(self, 'row_height')
        box.prop(self, 'skew')

        box = layout.box()
        box.prop(self, 'col_flutes')
        if self.properties.col_flutes:
            box.prop(self, 'addendum')
            box.prop(self, 'flute_sides')

        box = layout.box()
        box.prop(self, 'col_base')
        if self.properties.col_base:
            box.prop(self, 'base_type')
            box.prop(self, 'base_faces')
            box.prop(self, 'base_height')
            box.prop(self, 'base_width')

        box = layout.box()
        box.prop(self, 'col_cap')
        if self.properties.col_cap:
            box.prop(self, 'cap_type')
            box.prop(self, 'cap_faces')
            box.prop(self, 'cap_height')
            box.prop(self, 'cap_width')

    def execute(self, context):

        # Taper can't exceed radius
        if self.properties.radius < 0:
            checkRadius = -self.properties.radius
        else:
            checkRadius = self.properties.radius

        if self.properties.taper > checkRadius:
            self.properties.taper = checkRadius # Reset UI if input out of bounds...

        # Flutes can't exceed faces
        if self.properties.col_flutes > self.properties.col_faces:
            self.properties.col_flutes = self.properties.col_faces # Reset UI if input out of bounds...

        baseH = 0.00
        vertsBase = []
        edgesBase = []

        if self.col_base: # makig a base?
            baseH = self.base_height

            vertsBase, edgesBase = add_extent(
                self.radius,
                baseH,
                self.base_width,
                0,
                self.base_type
                )

        vertsCap = []
        edgesCap = []

        if self.col_cap: # making a capital?
            vertsCap, edgesCap = add_extent(
                self.radius - self.properties.taper, # fit to top of column
                self.cap_height,
                self.cap_width,
                baseH + (self.row_height * self.col_blocks),
                self.cap_type
                )

        verts, faces = add_column(
            baseH,
            self.radius, # use neg to get extrusions.
            self.taper/self.col_blocks, # taper column per number of rows.
            self.col_faces, # "faces" on column, per quadrant, 1 = square.
            self.col_blocks + 1, # need extra to complete row :)
            self.row_height,
            self.col_flutes,
            self.addendum,
            self.flute_sides,
            radians(self.skew),
            self.col_cap)

        scene = context.scene

        # Deselect all objects.
        bpy.ops.object.select_all(action='DESELECT')

        # Create new mesh

        # Make a mesh from a list of verts/edges/faces.

        if self.col_base:
            meshBase = bpy.data.meshes.new("Base")
            meshBase.from_pydata(vertsBase, edgesBase, [])
            meshBase.update()

            ob_new = bpy.data.objects.new("Base", meshBase)
            scene.objects.link(ob_new)
            scene.objects.active = ob_new
            ob_new.select = True
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.spin(steps=(self.base_faces*4), dupli=False, degrees=360, center=(0,0,0), axis=(0,0,1))
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.object.editmode_toggle()

            # since base and cap use same logic to generate, rotate and reposition base for use with column...
            bpy.ops.transform.rotate(value=(3.14159,), axis=(1,0,0), constraint_axis=(True,False,False), constraint_orientation='GLOBAL',
                mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1, snap=False,
                snap_target='CLOSEST', snap_point=(0,0,0), snap_align=False, snap_normal=(0,0,0), release_confirm=False)

            bpy.ops.transform.translate(value=(0,0,baseH), constraint_axis=(False,False,True), constraint_orientation='GLOBAL',
                mirror=False, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1, snap=False,
                snap_target='CLOSEST', snap_point=(0,0,0), snap_align=False, snap_normal=(0,0,0), texture_space=False, release_confirm=False)

        if self.col_cap:
            meshCap = bpy.data.meshes.new("Capital")
            meshCap.from_pydata(vertsCap, edgesCap, [])
            meshCap.update()

            ob_new = bpy.data.objects.new("Capital", meshCap)
            scene.objects.link(ob_new)
            scene.objects.active = ob_new
            ob_new.select = True
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.spin(steps=(self.cap_faces*4), dupli=False, degrees=360, center=(0,0,0), axis=(0,0,1))
            bpy.ops.object.editmode_toggle()
        
        mesh = bpy.data.meshes.new("Column")
        mesh.from_pydata(verts, [], faces)

        mesh.update()

        ob_new = bpy.data.objects.new("Column", mesh)
        scene.objects.link(ob_new)
        scene.objects.active = ob_new
        ob_new.select = True

        if self.col_base or self.col_cap:
            bpy.ops.object.join()
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.remove_doubles(mergedist=0.0001)
            bpy.ops.object.editmode_toggle()

        ob_new.location = tuple(context.scene.cursor_location)
#        ob_new.rotation_quaternion = [1.0,0.0,0.0,0.0]
#        ob_new.rotation_quaternion = [0.0,0.0,0.0,0.0]

        return {'FINISHED'}


class INFO_MT_mesh_columns_add(bpy.types.Menu):
    # Create the "Columns" menu
    bl_idname = "INFO_MT_mesh_columns_add"
    bl_label = "Columns"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("mesh.primitive_column", text="Column")


def menu_func(self, context): # Define "Columns" menu
    self.layout.menu("INFO_MT_mesh_columns_add", icon="PLUGIN")


def register(): # Add entry to the "Add Mesh" menu.
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_mesh_add.append(menu_func)


def unregister(): # Remove entry from the "Add Mesh" menu.
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_mesh_add.remove(menu_func)


if __name__ == "__main__":
    register()
