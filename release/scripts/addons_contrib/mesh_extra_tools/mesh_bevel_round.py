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

# Ported from RoundCorner Ruby program for Sketchup by Fredo6
# Fredo6 gave permission to port and distribute with Blender

bl_info = {
    "name": "Bevel Round",
    "author": "Fredo6, Howard Trickey",
    "version": (0, 1),
    "blender": (2, 6, 3),
    "location": "View3D > Tools",
    "description": "Bevel selected edges, possibly rounded",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"\
        "Scripts",
    "tracker_url": "http://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=32582",
    "category": "Mesh"}

import math
import functools
import bpy
import bmesh
import mathutils
from bpy.props import (BoolProperty,
                       EnumProperty,
                       IntProperty,
                       FloatProperty,
                       )
from mathutils import Vector

EPSILON = 1e-6

class BevelRound(bpy.types.Operator):
    bl_idname = "mesh.bevel_round"
    bl_label = "Bevel Round"
    bl_description = "Bevel selected edges, possibly rounded"
    bl_options = {'REGISTER', 'UNDO'}

    bevel_kind = EnumProperty(name="Bevel Kind",
        description="Style for beveling edges and corners",
        items=[
            ('ROUND', "Round",
                "Round edges and corners"),
            ('SHARP', "Sharp",
                "Round edges, peaked corners"),
            ('BEVEL', "Bevel",
                "Flat edges and corners")
            ],
        default='BEVEL')

    offset_amount = FloatProperty(name="Offset",
        description="Amount to offset edges along faces",
        default=0.2,
        min=0.0,
        max=1000.0,
        soft_min=0.0,
        soft_max=10.0,
        unit='LENGTH')

    segments = IntProperty(name="Segments",
        description="How many segments on bevel profile",
        min=1,
        max=100,
        default=1)

    strict_offset = BoolProperty(name="Strict Offset",
        description="Keep offset the same on all faces",
        default=True)

    rounding = BoolProperty(name="Inner Rounding",
        description="Round inside faces at concave corners",
        default=True)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH')

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label("Bevel Round Options:")
        box.prop(self, "bevel_kind")
        box.prop(self, "offset_amount")
        box.prop(self, "segments")
        box.prop(self, "strict_offset")
        box.prop(self, "rounding")

    def invoke(self, context, event):
        self.action(context)
        return {'FINISHED'}

    def execute(self, context):
        self.action(context)
        return {'FINISHED'}

    def action(self, context):
        obj = bpy.context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        # make sure vert, edge, face indexes match their positions
        bm.verts.index_update()
        bm.edges.index_update()
        bm.faces.index_update()
        algo = BevelRoundAlgo(bm, self.bevel_kind, self.offset_amount,
            self.segments, self.strict_offset, self.rounding)
        algo.execute()
        # Force mesh data recalculation
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()

class rbevel_help(bpy.types.Operator):
	bl_idname = 'help.bevelround'
	bl_label = ''

	def draw(self, context):
		layout = self.layout
		layout.label('To use:')
		layout.label('Select edges or faces to bevel with the option of rounded bevels.')
		layout.label('best used on flat edges & simple edgeflow')
		layout.label('may error if vert joins multiple edges/complex edge selection.')
	
	def execute(self, context):
		return {'FINISHED'}

	def invoke(self, context, event):
		return context.window_manager.invoke_popup(self, width = 400)

class BevelRoundAlgo(object):
    def __init__(self, bm, kind, offset, num_seg, strict, round):
        # The bmesh object
        self.bm = bm

        # How much to move offset edges
        # (projected onto 90deg angle planes, unless strict_offset)
        self.offset = offset

        # How many segments in the profile of an edge
        self.num_seg = num_seg

        # Cache of profiles in standard position, keyed by "kind-numseg"
        # Kind will be one of 'C' or 'P', for now
        self.hsh_profile_pts = {}

        # bmesh Edge index -> BEdge for it
        # Will have one for all the edges in the bevel selection
        self.hsh_ed = {}

        # bmesh Vertex index -> BCorner for it
        # Will have one for all ends of edges in hsh_ed
        self.hsh_corners = {}

        # bmesh Face index -> BFace for it
        self.hsh_faces = {}

        # List of [Vector, Vector], each a border line segment (for display only?)
        self.lpt_borders = []

        # Catenas are chains of edges with related offsets
        # Each has eds, a list of BEdges;
        #  chain, a list of [BEdge, face index]l
        #  nbsmall: seems to be some kind of edge count
        self.lst_catenas = []

        # List of Vector, pivot points for star corners
        self.lst_mark_points = []

        # lst_triangulate is list of [vd, ed1, ed2, seg1, seg2]
        # for each vd for a vert with only two edges and >=3 pairs
        self.lst_triangulated = []

        # List of BCorner, those signaled as errors (pair lines don't cross (?))
        self.hsh_error_vertex = {}

        # Edge index -> bmesh Edge for edges to bevel
        self.hash_edges = {}

        # hash_edges_extra : Edge index -> bmesh Edge added for valence >= 4 reasons
        self.hash_edges_extra = {}

        # Vertex index -> list of bmesh edges to bevel attached
        self.hsh_vertex_edges = {}

        # Vertex index -> list of all bmesh edges attached to it
        self.hsh_vertex_info = {}

        # Map from point to BMVert
        self.points = Points(self.bm)

        # Used to orient asymmetric corner mesh patterns
        self.golden_axis = Vector([0.0, 0.0, 1.0])

        # Profile spec for edges: [string, number]
        # where string is 'C' for quarter circle, 'CR' for concave quarter circle,
        # 'BZ' for Bezier, 'P' for 'perso' (?, some kind of multi-bezier).
        # number is number of line segments in profile (so 1 means just
        # a single straight line from start to end)
        if kind == 'BEVEL':
            self.profile_type = ['C', 1]
            self.num_seg = 1
        else:
            self.profile_type = ['C', num_seg]

        # Controls whether or not to use a round profile in certain disagreeing cases (?)
        self.mode_profile = 1

        # Corners come to peaks if mode_sharp
        self.mode_sharp = True if kind == 'SHARP' else False

        # Forces offset along faces to  be uniform rather than adjusted
        # to make them uniform when projected on 90deg-meeting-faces
        self.strict_offset = strict

        # Should we round the edges in the faces themselves too?
        self.mode_rounding = round

    def execute(self):
        bm = self.bm

        # Add the bmesh edges and compute everything
        # needed for bevel
        self.build_model(bm)

        # print("after build:")
        # self.print()

        # Initialization for geometry making
        self.prepare_geometry()

        # print("after prepare_geometry")
        # self.print()

        self.lst_corners = list(self.hsh_corners.values())
        self.nb_corners = len(self.lst_corners) - 1
        self.lst_eds = list(self.hsh_ed.values())
        self.nb_eds = len(self.lst_eds) - 1
        self.hsh_edge_erase = {}
        self.nb_borders = len(self.lpt_borders) // 2 - 1

        # Process geometry

        self.lst_edge_erase = []
        self.nb_edge_erase = -1

        # Creating the rounding faces
        for k in range(0, self.nb_eds + 1):
            ed = self.lst_eds[k]
            if ed.vmesh:
                self.create_geometry_vmesh(ed.vmesh)

        # Creating the triangulated  vmesh if any
        self.create_geometry_vmesh(self.lst_vmesh_triangulated)
        self.create_geometry_vborders(self.lst_vborders_triangulated)

        # Creating the corner round faces
        for k in range(0, self.nb_corners + 1):
           vd = self.lst_corners[k]
           if vd.vmesh:
               self.create_geometry_vmesh(vd.vmesh)

        # Creating the new faces
        for fc in self.hsh_faces.values():
            if not fc.anynew():
                continue
            lv = []
            for i in range(len(fc.bmverts)):
                npl = fc.newpts[i]
                if npl:
                    lv.extend(self.get_bmverts(npl))
                else:
                    lv.append(fc.bmverts[i])
            self.bm.faces.new(lv)

        # Deleting the unneeded geometry
        for f in self.hsh_faces.values():
            if f.face.is_valid:
                if not f.anynew():
                    continue
                fedges = f.face.edges[::]
                self.bm.faces.remove(f.face)
                for e in fedges:
                    if e.is_valid:
                        if e.is_wire:
                            self.bm.edges.remove(e)
        for k in range(0, self.nb_corners + 1):
            vd = self.lst_corners[k]
            if len(vd.leds) == 1:
                edge = vd.leds[0].edge
                if edge.is_valid:
                    self.bm.edges.remove(edge)
            else:
                # print("remove edges:", vd.vertex.link_edges)
                pass  # is there stuff to do here?
            if vd.vertex.is_valid:
                self.bm.verts.remove(vd.vertex)

    # Prepare the geometry
    def prepare_geometry(self):
        # Compute the corners
        for vd in self.hsh_corners.values():
            self.corner_compute(vd)

        # Compute the edge roundings
        for ed in self.hsh_ed.values():
            self.compute_mesh_edge(ed)

        # Compute the edge roundings for triangulated corners, if any
        self.lst_vmesh_triangulated = []
        self.lst_vborders_triangulated = []
        for ll in self.lst_triangulated:
            self.compute_mesh_edge_triangulated(ll[0], ll[1], ll[2], ll[3], ll[4])

        # Compute the faces
        for fc in self.hsh_faces.values():
            self.compute_face(fc)

    # Adds more edges if needed to make it so that for
    # vertices of valence 4 or more, all edges are beveled if any are.
    # Fills hsh_vertex_info for involved vertices with list of all bmesh
    # edges attached to a vertex.
    # Fills hsh_ed with BEdge for each edge to be beveled.
    # Fills hsh_corners with BCorner for each vertex involved in each BEdge.
    # Computes pairs at each BCorner.
    # Add bmesh edges to be beveled and compute the other
    # structures needed for the bevel.
    def build_model(self, bm):
        # Fill self.hash_edges with selected bmesh edges
        # if they are acceptable (separate two faces, not-coplanar)
        for bme in bm.edges:
            if bme.select and self.acceptable_edge(bme):
                self.hash_edges[bme.index] = bme

        if len(self.hash_edges) == 0:
            return

       # Fill self.hash_vertex_edges[i] with list of
       # bmesh edges attached to vertex with bmesh index i
        self.hsh_vertex_edges = {}
        for edge in self.hash_edges.values():
            self.register_vertex(edge.verts[0], edge)
            self.register_vertex(edge.verts[1], edge)

        # Add extra edges needed to make valence
        # >=4 verts have all edges beveled if any are.
        # Extra edges go in self.hash_edges and
        # self.hash_edges_extra.
        self.hash_edges_extra = {}
        for edge in self.hash_edges.values():
            self.verify_vertex(edge.verts[0])
            self.verify_vertex(edge.verts[1])
        
        # create BEdges in hsh_ed, BCorners in hsh_corners
        for edge in self.hash_edges.values():
            self.integrate_edge(edge)

        # create BPairs in vd.pairs for each BCorner vd.
        for vd in self.hsh_corners.values():
            self.compute_pairs_at_vertex(vd)

        # create BCatenas in ed.catenas for each BEdge ed.
        self.catena_compute_all()
        if self.strict_offset:
            self.catena_offset_all()

        self.lpt_borders = []
        for ed in self.hsh_ed.values():
            self.nsection = None
            for pair in ed.pairs:
                pair.ptcross = None
            self.compute_borders(ed)

        # Scan the corners to determine the roundings
        self.corner_scan_all()

        # Compute the faces orientation: tricky when # segments is odd
        self.compute_face_orientation()

        # Compute alone pairs in case of triangulation
        self.evaluate_pair_triangulated()

        # Compute the roundings
        for vd in self.hsh_corners.values():
            self.rounding_compute(vd)
        for ed in self.hsh_ed.values():
            self.compute_borders_for_display(ed)


    def acceptable_edge(self, bme):
        # algorithm requires that edges separate
        # exactly two, non coplanar faces
        if len(bme.link_faces) == 2:
            f1 = bme.link_faces[0]
            f2 = bme.link_faces[1]
            return not parallel(f1.normal, f2.normal)
        return False

    def register_vertex(self, vertex, bme):
        if vertex.index not in self.hsh_vertex_edges:
            self.hsh_vertex_edges[vertex.index] = []
        ledges = self.hsh_vertex_edges[vertex.index]
        if bme not in ledges:
            ledges.append(bme)
        self.register_faces(vertex.link_faces)

    def verify_vertex(self, vertex):
        # algorithm requires that vertices with valence >= 4
        # must have all edges included
        if vertex.index not in self.hsh_vertex_info:
            ledges = []
            self.hsh_vertex_info[vertex.index] = list(vertex.link_edges)
        ledges = self.hsh_vertex_info[vertex.index]  # list of bmesh edges
        lsel = self.hsh_vertex_edges[vertex.index]
        nsel = len(lsel)
        if nsel <=3 or nsel == len(ledges):
            return
        # add extra edges
        for bme in ledges:
            if bme.index in self.hash_edges:
                continue
            # kind of an impasse if edge is unacceptable - oh well
            if self.acceptable_edge(bme):
                self.hash_edges[edge.index] = bme
                self.register_vertex(edge.verts[0], bme)
                self.register_vertex(edge.verts[1], bme)
                self.hash_edges_extra[edge.index] = bme

    def register_faces(self, faces):
        for f in faces:
            if f.index not in self.hsh_faces:
                self.hsh_faces[f.index] = BFace(f)

    # Evaluate and treat pairs at triangulated corners
    def evaluate_pair_triangulated(self):
        self.lst_triangulated = []
        lalone = [ vd for vd in self.hsh_corners.values() \
                   if len(vd.leds) == 2 and len(vd.pairs) >= 3 ]
        for i, vd in enumerate(lalone):
            ed1 = vd.leds[0]
            ed2 = vd.leds[1]
            pairs1 = [ pair for pair in vd.pairs if pair.alone and pair.leds[0] == ed1 ]
            pairs2 = [ pair for pair in vd.pairs if pair.alone and pair.leds[0] == ed2 ]
            if not pairs1 or not pairs2:
                continue
            ptcross10 = pairs1[0].ptcross
            ptcross11 = pairs1[1].ptcross if len(pairs1) > 1 else None
            ptcross20 = pairs2[0].ptcross
            ptcross21 = pairs2[1].ptcross if len(pairs2) > 1 else None
            if ptcross21 and (ptcross21 - ptcross10).length < (ptcross20 - ptcross10).length:
                seg1 = [ptcross10, ptcross21]
            else:
                seg1 = [ptcross10, ptcross20]
            seg2 = None
            if ptcross11:
                if ptcross21 and (ptcross21 - ptcross11).length < (ptcross20 - ptcross11).length:
                    seg2 = [ptcross11, ptcross21]
                else:
                    seg2 = [ptcross11, ptcross20]
            self.lpt_borders.extend(seg1)
            if seg2:
                self.lpt_borders.extend(seg2)
            self.lst_triangulated.append([vd, ed1, ed2, seg1, seg2])

    def integrate_edge(self, edge):
        if not self.acceptable_edge(edge):
            return None
        index = edge.index
        if index in self.hsh_ed:
            return self.hsh_ed[index]
        ed = BEdge(edge)
        self.hsh_ed[index] = ed
        ed.corners.append(self.create_corner(edge.verts[0], ed))
        ed.corners.append(self.create_corner(edge.verts[1], ed))
        return ed

    def create_corner(self, vertex, ed):
        index = vertex.index
        if index not in self.hsh_corners:
            vd = BCorner(vertex, ed)
            self.hsh_corners[index] = vd
        else:
            vd = self.hsh_corners[index]
            if ed not in vd.leds:
                vd.leds.append(ed)
        return vd

    # vd should be for a vertex and one end of ed1's edge and face1
    # should be one or the other of the faces incident to it.
    # Similarly for ed2, face2 if present
    def create_pair(self, vd, ed1, face1, ed2=None, face2=None):
        edge1 = ed1.edge
        edge2 = ed2.edge if ed2 else None
        pair = BPair(vd, ed1, face1, ed2, face2)
        vd.pairs.append(pair)
        vertex = vd.vertex
        iface1 = 0 if face1 == ed1.lfaces[0] else 1
        ivtx = 0 if vertex == edge1.verts[0] else 1
        ed1.pairs[iface1 + 2 * ivtx] = pair
        if edge2:
            iface2 = 0 if face2 == ed2.lfaces[0] else 1
            ivtx = 0 if vertex == edge2.verts[0] else 1
            if not ed2.pairs:
                ed2.pairs = [None, None, None, None]
            ed2.pairs[iface2 + 2 * ivtx] = pair
            pair.monoface = (face1 == face2) or parallel(face1.normal, face2.normal)
            if pair.monoface:
                pair.convex = convex_at_vertex(vertex, face1, ed1.edge, ed2.edge, face2)
                pair.vd.convex = pair.convex
        # computing planes for cross points - special for termination corners
        if pair.alone:
            self.compute_edge_terms(pair, pair.ledges[0], pair.lfaces[0], pair.vd.vertex)
        return pair

    # Find the matching edges at a vertex
    def compute_pairs_at_vertex(self, vd):
        nb_edge = len(vd.leds)
        if nb_edge == 1:
            ed = vd.leds[0]
            self.create_pair(vd, ed, ed.lfaces[0])
            self.create_pair(vd, ed, ed.lfaces[1])
        elif nb_edge == 2:
            self.check_pair_2(vd, vd.leds[0], vd.leds[1])
        else:
            for i in range(0, nb_edge - 1):
                for j in range(i+1, nb_edge):
                    self.check_pair_N(vd, vd.leds[i], vd.leds[j], vd.leds)

    # Find the common faces (or coplanar) to 2 edges when there are 2 at vertex.
    # Makes a pair for the two edges matching when there's common or coplanar faces.
    # Also makes pairs for the two edges matching when there's a common edge
    # between them (and some convexity test I don't understand).
    # Finally, makes an alone pair for any (edge, face) pairs not otherwise used.
    def check_pair_2(self, vd, ed1, ed2):
        edge1 = ed1.edge
        edge2 = ed2.edge
        faces1 = list(edge1.link_faces)
        faces2 = list(edge2.link_faces)

        # Finding faces on the same plane
        for f1 in edge1.link_faces:
            for f2 in edge2.link_faces:
                if f1 == f2 or parallel(f1.normal, f2.normal):
                    self.create_pair(vd, ed1, f1, ed2, f2)
                    faces1.remove(f1)
                    faces2.remove(f2)

        # Finding faces with common edges
        lf1 = []
        lf2 = []
        for f1 in faces1:
            for f2 in faces2:
                linter = list(set(f1.edges).intersection(set(f2.edges)))
                if len(linter) > 0:
                    e = linter[0]
                    if not (convex_at_vertex(vd.vertex, f1, edge1, e) or \
                            convex_at_vertex(vd.vertex, f2, edge2, e)):
                        self.create_pair(vd, ed1, f1, ed2, f2)
                        lf1.append(f1)
                        lf2.append(f2)

        # Creating alone pair if any unaffected faces left
        for f1 in faces1:
            if f1 not in lf1:
                self.create_pair(vd, ed1, f1)
        for f2 in faces2:
            if f2 not in lf2:
                self.create_pair(vd, ed2, f2)

    # Find the common faces (or coplanar) to 2 edges when there are more than 2 total.
    # Makes a pair for the the two edges matching the first of any common faces
    # and returns if so.
    # Else makes a pair matching up the two edges with faces that are parallel
    # and returns if it finds one.
    # Else makes a pair matching up the two edges with faces sharing an edge
    # and that edge isn't in leds, and returns if it finds one.
    # Otherwise makes no pair.
    def check_pair_N(self, vd, ed1, ed2, leds):
        edge1 = ed1.edge
        edge2 = ed2.edge
        if edge1 == edge2:
            return
        faces1 = list(edge1.link_faces)
        faces2 = list(edge2.link_faces)
        lfaces = list(set(faces1).intersection(set(faces2)))

        # Common face found
        if len(lfaces) >= 1:
            return self.create_pair(vd, ed1, lfaces[0], ed2, lfaces[0])

        # Finding faces that are on the same plane
        for f1 in edge1.link_faces:
            for f2 in edge2.link_faces:
                if parallel(f1.normal, f2.normal):
                    return self.create_pair(vd, ed1, f1, ed2, f2)
 
        # Check common edges
        for f1 in faces1:
            for f2 in faces2:
                linter = list(set(f1.edges).intersection(set(f2.edges)))
                if len(linter) > 0 and not find(leds, lambda ed: ed.edge == linter[0]):
                    return self.create_pair(vd, ed1, f1, ed2, f2)
                    
    def compute_borders(self, ed):
        pairs = ed.pairs
        for i in range(0,4):
            if pairs[i]:
               self.compute_pair_ptcross(pairs[i])

    # Compute the borders for display, including the rounding
    def compute_borders_for_display(self, ed):
        pairs = ed.pairs
        lseg = []
        lroundings = []
        for i in [0, 2, 1, 3]:
            pair = pairs[i]
            lpt = pair.rounding
            if lpt and len(lpt) > 0:
                if on_line(lpt[0], [pair.ptcross, ed.vec]):
                    pt = lpt[0]
                else:
                    pt = lpt[-1]
            else:
                pt = pair.ptcross
            lseg.append(pt)
        self.lpt_borders.extend(lseg)


    # Compute and return the vector representing the border
    def compute_edge_terms(self, pair, edge, face, vertex):
        normal = face.normal
        for e in vertex.link_edges:
            if e == edge:
                continue
            for f in e.link_faces:
                if f == face or parallel(f.normal, normal):
                    pair.edge_terms.append(e)

    # Compute the cross points for the pair
    def compute_pair_ptcross(self, pair):
        if pair.ptcross:
            return
        line1 = self.line_border(pair, 0)
        if pair.alone:
            pair.ptcross = self.find_intersect_edge_term(pair, line1)
        else:
            line2 = self.line_border(pair, 1)
            if parallel(line1[1], line2[1]):
                pair.ptcross = intersect_line_plane(line1,
                        [pair.vd.vertex.co, line1[1]])
            else:
                pair.ptcross = intersect_line_line(line1, line2)
                if not pair.ptcross:
                    self.signal_error_vd(pair.vd)
                    lpt = closest_points(line1, line2)
                    pair.ptcross = lpt[0]

    # Fine the best stop point for a standalone edge pair
    def find_intersect_edge_term(self, pair, line):
        ed = pair.leds[0]
        lptinter = []
        for edge in pair.edge_terms:
            pt = intersect_edge_line(edge, line)
            if pt:
                lptinter.append(pt)
        # if no intersection just take the orthogonal plane
        if len(lptinter) == 0:
            return intersect_line_plane(line, [pair.vd.vertex.co, ed.vec])
        # sort the interesection point and take the farthest
        ptmid = ed.ptmid
        lptinter.sort(key = lambda p: (ptmid-p).length)
        return lptinter[-1]

    # Compute the line defining a border on  a face
    # (Maybe don't need this function if not drawing borders)
    def line_border(self, pair, iedge):
        edge = pair.ledges[iedge]
        ed = self.hsh_ed[edge.index]
        face = pair.lfaces[iedge]
        iface = 0 if face == ed.lfaces[0] else 1
        offset = self.offset * ed.lfactors[iface]
        vecin = normal_in_to_edge(edge, face)
        pt = ed.ptmid + offset * vecin
        return [pt, ed.vec]

    # Compute the orthogonal profile for an edge at its midpoint
    def compute_profile_edge(self, ed):
        if ed.nsection:
            return ed.nsection
        offset1 = self.offset * ed.lfactors[0]
        offset2 = self.offset * ed.lfactors[1]
        vec1 = ed.lvecins[0]
        vec2 = ed.lvecins[1]
        ptcenter = ed.ptmid
        profile = ['C', self.num_seg] if ed.round_profile else self.profile_type
        section = self.profile_compute_by_offset(profile, ptcenter,
                    vec1, offset1, vec2, offset2)
        if not on_plane(section[0], face_plane(ed.facemain)):
            section.reverse()
        ed.nsection = section
        return section

    # Compute the section for an edge at corners
    # The section will go from the facemain face to the non-facemain one.
    def compute_sections_multi(self, ed, icorner):
        vd = ed.corners[icorner]
        vpos = vd.vertex.co
        iA = 0 if ed.facemain == ed.lfaces[0] else 1
        iB = 1 - iA
        pairA = ed.pairs[2 * icorner + iA]
        pairB = ed.pairs[2 * icorner + iB]

        ptA = pairA.ptcross
        ptB = pairB.ptcross

        profile = ['C', self.num_seg] if ed.round_profile else self.profile_type

        if len(vd.leds) <= 1:
            vecA = ptA - vpos
            vecB = ptB - vpos
            offsetA = vecA.length
            offsetB = vecB.length
            section = self.profile_compute_by_offset(profile, vpos,
                        vecA, offsetA, vecB, offsetB)
        elif len(vd.leds) == 2:
            vecA = ptA - vpos
            vecB = ptB - vpos
            section = self.profile_compute_by_vectors(profile,
                        ptA, vecA, ptB, ed.vec.cross(vecB))
        else:
            edA = find(pairA.leds, lambda edd: edd != ed)
            edB = find(pairB.leds, lambda edd: edd != ed)
            vecA = edA.vec.copy()
            if vecA.dot(edA.ptmid - vpos) < 0:
                vecA.negate()
            vecB = edB.vec.copy()
            if vecB.dot(edB.ptmid - vpos) < 0:
                vecB.negate()
            section = self.profile_compute_by_vectors(profile,
                        ptA, vecA, ptB, ed.vec.cross(vecB))

        if not on_plane(section[0], face_plane(ed.facemain)):
            section.reverse()
        ed.cross_sections[icorner] = section
        return section

    # Construct the lattice for the rounding of an edge
    def build_lattice(self, i, xsection1, xsection2, sh_section1, sh_section2):
        if vec_approx_eq(xsection1[i], xsection2[i]):
            lpts = [xsection1[i]]
        else:
            lpts = [xsection1[i], xsection2[i]]

        if sh_section2 and sh_section2[i] and len(sh_section2[i]) > 0:
            for pt in sh_section2[i]:
                if not (vec_approx_eq(pt, xsection2[i]) or vec_approx_eq(pt, xsection2[i+1])):
                    lpts.append(pt)

        lpts.append(xsection2[i + 1])
        if not vec_approx_eq(xsection2[i + 1], xsection1[i + 1]):
            lpts.append(xsection1[i + 1])

        if sh_section1 and sh_section1[i] and len(sh_section1[i]) > 0:
            lpt1 = []
            for pt in sh_section1[i]:
                if not (vec_approx_eq(pt, xsection1[i]) or vec_approx_eq(pt, xsection1[i+1])):
                    lpt1.append(pt)
            lpt1.reverse()
            lpts.extend(lpt1)

        return lpts

    # Compute the round border on an edge as a vmesh
    def compute_mesh_edge(self, ed):
        xsection1 = ed.cross_sections[0]
        xsection2 = ed.cross_sections[1]
        sh_section1 = ed.sharp_sections[0]
        sh_section2 = ed.sharp_sections[1]
 
        nblat = len(xsection1) - 1
        n2 = nblat // 2
        n1 = nblat - n2
 
        # Part close to main face
        face1 = ed.facemain
        mesh1 = []
        for i in range(0, n1):
            mesh1.append(self.build_lattice(i, xsection1, xsection2, sh_section1, sh_section2))
        if n1 > 0:
            normalref1 = self.compute_normal_reference(ed, face1, xsection1[0], xsection1[1])

        # Part close to the other face
        face2 = ed.lfaces[1] if ed.lfaces[0] == ed.facemain else ed.lfaces[0]
        mesh2 = []
        for i in range(n1, nblat):
            mesh2.append(self.build_lattice(i, xsection1, xsection2, sh_section1, sh_section2))
        if n2 > 0:
            normalref2 = self.compute_normal_reference(ed, face2, xsection1[n1+1], xsection1[n1])

        # Creating the vmesh, single or double
        ed.vmesh = []
        if edge_reversed_in_face(ed.edge, face1) == edge_reversed_in_face(ed.edge, face2):
            if n1 > 0:
                ed.vmesh.append([mesh1, face1, normalref1])
            if n2 > 0:
                ed.vmesh.append([mesh2, face2, normalref2])
        else:
            ed.vmesh.append([mesh1 + mesh2, face1, normalref1])

        # Creating the border edges
        ed.vborders = []
        ed.vborders.append([[xsection1[0], xsection2[0]], 'S'])
        ed.vborders.append([[xsection1[-1], xsection2[-1]], 'S'])

        # Termination edges
        xs = [xsection1, xsection2]
        for i in range(0, 2):
            if len(ed.corners[i].leds) == 1:
                ed.vborders.append([xs[i], 'P'])

    def compute_mesh_edge_triangulated(self, vd, ed1, ed2, seg1, seg2):
        icorner1 = 0 if ed1.corners[0] == vd else 1
        icorner2 = 0 if ed2.corners[0] == vd else 1
        xsection1 = ed1.cross_sections[icorner1]
        xsection2 = ed2.cross_sections[icorner2]
        reversed = (xsection1[0] - xsection2[0]).length > (xsection1[0] - xsection2[-1]).length and \
                   (xsection1[-1] - xsection2[-1]).length >= (xsection1[-1] - xsection2[0]).length

        nblat = len(xsection1) - 1
        n2 = nblat // 2
        n1 = nblat - n2

        # Part close to main face
        face1 = ed1.facemain
        mesh1 = []
        for i in range(0, n1):
            mesh1.append(self.build_lattice(i, xsection1, xsection2, None, None))
        if n1 > 0:
            normalref1 = self.compute_normal_reference(ed1, face1, xsection1[0], xsection1[1])

        # Part close to the other face
        if reversed:
            face2 = ed2.facemain
        else:
            face2 = find(ed2.lfaces, lambda f: f != ed2.facemain)
        mesh2 = []
        for i in range(0, nblat):
            mesh1.append(self.build_lattice(i, xsection1, xsection2, None, None))
        if n2 > 0:
            normalref2 = self.compute_normal_reference(ed2, face2, xsection1[n1+1], xsection1[n1])

        # Creating the vmesh, single or double
        if n1 > 0:
            self.lst_vmesh_triangulated.append([mesh1, face1, normalref1])
        if n2 > 0:
            self.lst_vmesh_triangulated.append([mesh2, face2, normalref2])

        # Creating the border edges
        if xsection1[0] != xsection2[0]:
            self.lst_vborders_triangulated.append([[xsection1[0], xsection2[0]], 'S'])
        if xsection1[-1] != xsection2[-1]:
            self.lst_vborders_triangulated.append([[xsection1[-1], xsection2[-1]], 'S'])

    def sort_corners_for_orientation(self, vda, vdb):
        eda = vda.gold_ed
        edb = vdb.gold_ed
        if vda.convex:
            return -1
        if vdb.convex:
            return 1
        if eda and edb:
            return  cmp(eda.golden, edb.golden)
        elif eda:
            return -1
        elif edb:
            return 1
        else:
            return 0

    # Compute right orientation at corner
    def orientation_at_corner(self, vd):
        edgold = vd.gold_ed
        if not edgold:
            return
        ledface = []
        for ed in vd.leds:
            for face in ed.lfaces:
                if ed == edgold:
                    continue
                if self.ed_common_face(ed, face, edgold):
                    iface = 0 if ed.lfaces[0] == face else 1
                    ledface.append([ed, iface])
                    break
        main = 0 if find(ledface, lambda ll: ll[0].facemain) else 1
        for ll in ledface:
            ed = ll[0]
            iface = ll[1]
            iface2 = (iface + main) % 2
            if not ed.facemain:
                ed.facemain = ed.lfaces[iface2]
            catena = ed.catenas[iface2]
            if catena.nbsmall <= 0:
                self.assign_ed_facemain(catena)
            ed.catenas[iface].nbsmall += 1

    # Find if 2 edges share a common face
    def ed_common_face(self, ed0, face0, ed1):
        for face in ed1.lfaces:
            if parallel(face.normal, face0.normal):
                return True
        return False

    # Compute all face orientations - needed for odd number of segments
    def compute_face_orientation(self):
        # Starting with the round corners
        lcorners = list(self.hsh_corners.values())
        lcorners.sort(key = functools.cmp_to_key(
            lambda x, y : self.sort_corners_for_orientation(x,y)))

        hsh = {}
        for vd in lcorners:
            if vd in hsh:
                continue
            hsh[vd] = True
            edgold = vd.gold_ed
            if not edgold:
                continue
            self.orientation_at_corner(vd)
            vd2 = edgold.corners[1] if edgold.corners[0] == vd else edgold.corners[0]
            if vd2 and vd2 not in hsh:
                hsh[vd2] = True
                self.orientation_at_corner(vd)

        # Assigning the main faces to edge
        for catena in self.lst_catenas:
            if catena.nbsmall == 0:
                self.assign_ed_facemain(catena)

        # Remaining edges
        for ed in self.hsh_ed.values():
            if not ed.facemain:
                ed.facemain = ed.lfaces[0]

    # Propagate face orientation on a catena
    def assign_ed_facemain(self, catena):
        for ll in catena.chain:
            ed = ll[0]
            iface = ll[1]
            other_catena = ed.catenas[1] if ed.catenas[0] == catena else ed.catenas[1]
            if not ed.facemain:
                ed.facemain = ed.lfaces[iface]
            other_catena.nbsmall += 1

    # Scan all corners for determining golden edges
    def corner_scan_all(self):
        # find golden edge if vd has valence 3 or 4
        for vd in self.hsh_corners.values():
            self.corner_scan_golden(vd)
        # Final golden edge calc, for valence 3
        for vd in self.hsh_corners.values():
            self.corner_determine_golden(vd)

        # For valence 3, which have round profile?
        # (TODO: is it really necessary to do this twice?)
        for vd in self.hsh_corners.values():
            self.corner_round_profile(vd)
        for vd in self.hsh_corners.values():
            self.corner_round_profile(vd)

    # Search and propagate the golden edges.
    # Only assigns a value if valence is 3 or 4.
    # In those caes, sets the vd.gold_ed to
    # the corner's ed that is best for golden edge.
    # When valence is 3, picks the golden edge
    # (somehow) and sets the edge's aligned property
    # to True if the other pairs edges intersect.
    def corner_scan_golden(self, vd):
        if len(vd.leds) == 4:
            vd.leds.sort(key = functools.cmp_to_key(compare_gold_ed))
            vd.gold_ed = vd.leds[0]

        if len(vd.leds) != 3:
            return

        # Identifying convex corners
        leds = vd.leds
        pairs = vd.pairs
        for pair in pairs:
            ed1 = pair.leds[0]
            ed2 = pair.leds[1]
            ed0 = find(leds, lambda ed: ed != ed1 and ed != ed2)
            if pair.convex:
                ed0.golden = -1
                vd.gold_ed = ed0
            otherpairs = [p for p in pairs if p != pair]
            if ed1 in otherpairs[0].leds:
                pair1 = otherpairs[0]
                pair2 = otherpairs[1]
            else:
                pair1 = otherpairs[1]
                pair2 = otherpairs[0]
            ed0.aligned = intersect_line_line(
                [pair1.ptcross, ed1.vec],
                [pair2.ptcross, ed2.vec])

    # Compare two edges to determine which one has to be gold.
    # If the vertex is convex, then the 'golden' member of the
    # edge should be set to something to help compare.
    # Else if the cosines of the angles the edges faces
    # differ from 90 differ a lot then the one that
    # is more acute wins.
    # Else the one that is more closely aligned with the
    # golden axis wins.
    # Else the longer edge wins.
    def compare_gold_ed(self, vd, eda, edb):
        if vd.convex:
            return cmp(eda.golden, edb.golden)
        if eda.aligned and not edb.aligned:
            return -1
        elif edb.aligned and not eda.aligned:
            return 1
        cosa = eda.cos
        cosb = edb.cos
        val = 0 if abs(cosa - cosb) < 0.5 else cmp(cosa, cosb)
        if val == 0:
            val = -cmp(abs(eda.vec.dot(self.golden_axis)), abs(edb.vec.dot(self.golden_axis)))
        if val == 0:
            val = -cmp(eda.length, edb.length)
        return val

    # Determine the golden edge at a 3 edges corner
    def corner_determine_golden(self, vd):
        if len(vd.leds) != 3:
            return
        lsgold = vd.leds[::]
        lsgold.sort(key = functools.cmp_to_key(lambda x, y: self.compare_gold_ed(vd, x, y)))
        ed0 = lsgold[0]
        if not vd.gold_ed:
            vd.gold_ed = ed0
        for pair in vd.pairs:
            if ed0 in pair.leds:
                continue
            vd.round_pair = pair

    # Calculate whether edges at a vertex should have a round profile
    def corner_round_profile(self, vd):
        if len(vd.leds) != 3:
            return
        ed0 = vd.gold_ed
        ledothers = [ed for ed in vd.leds if ed != ed0]
        ed1 = ledothers[0]
        ed2 = ledothers[1]
 
        ed0.round_profile = self.use_round_profile(ed0)
        if self.use_round_profile(ed1) or self.use_round_profile(ed2):
            ed1.round_profile = True
            ed2.round_profile = True

    # Get the profiles for the edge depending on the hybrid settings
    def use_round_profile(self, ed):
        if ed.round_profile:
            return True
        if self.mode_profile == -1:
            return False
        elif self.mode_profile == 0:
            return ed.golden == -1
        else:
            return ed.golden == -1 or ed.corners[0].gold_ed == ed or ed.corners[1].gold_ed == ed
 
    # Calculate rounding at corner, if applicable
    def rounding_compute(self, vd):
        if not self.mode_rounding:
            return
        if self.num_seg == 1 or (self.mode_sharp and not vd.convex) or len(vd.leds) !=3:
            return
        # Getting the golden edge and determining the metal pair
        ed_gold = vd.gold_ed
        pair_gold = find(vd.pairs, lambda pair: ed_gold not in pair.leds)
        pair_silver = None
        pair_bronze = None
        ed_silver = None
        ed_bronze = None
        facemain = ed_gold.facemain
        otherface = ed_gold.lfaces[1] if ed_gold.lfaces[0] == facemain else ed_gold.lfaces[0]
        for pair in vd.pairs:
            if pair == pair_gold:
                continue
            if on_plane(pair.ptcross, face_plane(facemain)):
                pair_silver = pair
                ed_silver = pair.leds[1] if pair.leds[0] == ed_gold else pair.leds[0]
            else:
                pair_bronze = pair
                ed_bronze = pair.leds[1] if pair.leds[0] == ed_gold else pair.leds[0]
        if not (pair_silver and pair_bronze):
            return

        # Calculate the planes for the golden edge
        gold_ptcross = pair_gold.ptcross
        plane_silver = [pair_silver.ptcross, ed_silver.vec]
        line_silver = [gold_ptcross, ed_silver.vec]
        plane_bronze = [pair_bronze, ed_bronze.vec]
        line_bronze = [gold_ptcross, ed_bronze.vec]
        pt_silver = intersect_line_plane([gold_ptcross, ed_silver.vec], [pair_silver.ptcross, ed_silver.vec])
        pt_bronze = intersect_line_plane([gold_ptcross, ed_bronze.vec], [pair_bronze.ptcross, ed_bronze.vec])

        # Rounding is not materialized
        if not pt_silver or not pt_bronze or vec_approx_eq(pt_silver, pt_bronze) or \
                vec_approx_eq(pt_silver, gold_ptcross) or vec_approx_eq(pt_bronze, gold_ptcross):
            return


        # Computing the rounding
        vpos = vd.vertex.co
        vec1 = ed_silver.ptmid - vpos
        vec2 = ed_bronze.ptmid - vpos
        normal2 = vec1.cross(vec2)
        offset1 = (pt_silver - gold_ptcross).length
        offset2 = (pt_bronze - gold_ptcross).length
        pair_gold.rounding = self.profile_compute_by_offset(['C', self.num_seg],
                gold_ptcross, vec1, offset1, vec2, offset2)

    # Corner calculation
    def corner_compute(self, vd):
        mode_sharp = self.mode_sharp
        n = len(vd.leds)
        if n == 1 or n == 2:
            self.corner_compute_12(vd)
        elif n == 3:
            if self.num_seg == 1:
                self.corner_compute_3round(vd)
            elif (not mode_sharp and self.num_seg != 1) or vd.convex:
                self.corner_compute_3round(vd)
            elif self.strict_offset:
                self.corner_compute_any_sharp(vd)
            else:
                self.corner_compute_3sharp(vd)
        elif n == 4:
            if mode_sharp:
                self.corner_compute_any_sharp(vd)
            else:
                self.corner_compute_round_4(vd)
        else:
            if mode_sharp:
                self.corner_compute_any_sharp(vd)
            else:
                self.corner_compute_star(vd)
 
    # Compute a corner with 1 or 2 edges (sharp)
    def corner_compute_12(self, vd):
        for ed in vd.leds:
            icorner = 0 if ed.corners[0] == vd else 1
            section = self.compute_sections_multi(ed, icorner)
            if len(vd.leds) == 1:
                # Do we need an extra face between end of beveled
                # edge and vd?  Usually yes, but not in certain cases.
                # One case where we don't: if there are only 3 faces
                # at the vertex and the 3rd face contains the
                # beveled end completely.
                needcornerface = True
                vfaces = vd.vertex.link_faces
                if len(vfaces) == 3:
                    f3 = find(vfaces, lambda f: f != ed.lfaces[0] and f != ed.lfaces[1])
                    if not f3:
                        print("whoops, couldn't find 3rd face")
                    bf3 = self.hsh_faces[f3.index]
                    # test segment containment by containment of midpoint
                    # in face - for this case, should be ok
                    mid = section[0].lerp(section[1], 0.5)
                    if bf3.contains_point(mid):
                        needcornerface = False
                if needcornerface:
                    facepts = section + [vd.vertex.co]
                    norm = ed.lfaces[0].normal + ed.lfaces[1].normal
                    norm.normalize()
                    vd.vmesh = [[[facepts], ed.lfaces[0], norm]]
 
    # Compute a round corner with 3 edges
    def corner_compute_3round(self, vd):
        leds = vd.leds

        # Using the golden edge and compute the golden section0
        # which is the profile for the end of the golden edge,
        # going from its main face to its non-main face.
        ed0 = vd.gold_ed
        icorner0 = 0 if ed0.corners[0] == vd else 1
        section0 = self.compute_sections_multi(ed0, icorner0)

        # Computing the other edges
        # Pair A is the one for ed0 going around its facemain
        # Pair B is the remaining one
        iA = 0 if ed0.facemain == ed0.lfaces[0] else 1
        iB = 1 - iA
        pairA = ed0.pairs[2 * icorner0 + iA]
        pairB = ed0.pairs[2 * icorner0 + iB]
        ed1 = find(pairA.leds, lambda ed: ed != ed0 and \
                        self.ed_common_face(ed0, ed0.facemain, ed))
        ed2 = find(pairB.leds, lambda ed: ed != ed0 and ed != ed1)
        pair_other = find(vd.pairs, lambda pair: ed0 not in pair.leds)

        # Computing the grid
        # Make lpts be an array of sections, where the start points
        # are the cross-point of the non-golden-edge pair (or, if that
        # is rounded, the rounding points for that), and the end points
        # are the points on the golden section (going from its facemain
        # to the other face).
        n0 = len(section0) - 1
        origin = pair_other.ptcross
        if pair_other.rounding:
            lorigin = pair_other.rounding[::]
            lorigin.reverse()
        else:
            lorigin = (n0+1) * [ None ]
            for i in range(0, n0+1):
                lorigin[i] = origin
        vec0 = ed0.vec
        if icorner0 == 1:
            vec0 = vec0.copy()
            vec0.negate()
        normal = ed1.vec.cross(ed2.vec)
        vec = origin - vd.vertex.co
        lpts = []
        profile = ['C', self.num_seg] if (ed1.round_profile or ed2.round_profile) \
                else self.profile_type
        for i in range(0, n0 + 1):
            lpt = self.profile_compute_by_vectors(profile, section0[i],
                vec0, lorigin[i], normal)
            lpts.append(lpt)
        icorner1 = 0 if ed1.corners[0] == vd else 1
        icorner2 = 0 if ed2.corners[0] == vd else 1

        # ed1 is the edge sharing the golden edge's facemain, so it
        # gets the first section in lpts
        section1 = lpts[0]
        if not on_plane(section1[0], face_plane(ed1.facemain)):
            section1 = section1[::]
            section1.reverse()

        # ed2 is the other of the non-golden pair, so it gets the last
        # section in lpts
        section2 = lpts[-1]
        if not on_plane(section2[0], face_plane(ed2.facemain)):
            section2 = section2[::]
            section2.reverse()

        ed1.cross_sections[icorner1] = section1
        ed2.cross_sections[icorner2] = section2

        # Constructing the mesh.
        # Makes nseg strips of nseg quads (the first quad
        # in the strip will really be a tri unless this corner has rounding).
        # Strip i starts at the other-pair cross point (or the ith point on
        # it, if rounded), and proceeds to end at the edge between
        # (section0[i], section0[i+1]).
        vmesh = []
        lquads =[]
        n = len(lpts) - 2
        for i in range(0, n + 1):
            pts1 = lpts[i]
            pts2 = lpts[i + 1]
            m = len(pts1) - 2
            for j in range(0, m + 1):
                if vec_approx_eq(pts1[j + 1], pts2[j + 1]):
                    pts = [pts1[j], pts1[j + 1], pts2[j]]
                elif vec_approx_eq(pts1[j], pts2[j]):
                    pts = [pts1[j], pts1[j + 1], pts2[j + 1]]
                else:
                    pts = [pts1[j], pts1[j + 1], pts2[j + 1], pts2[j]]
                lquads.append(pts)

        nb = self.num_seg
        n0 = nb // 2
        odd = (nb % 2) != 0

        # Triangle corner
        if parallel(ed1.facemain.normal, ed0.facemain.normal):
            n1 = n0 - 1
            face1 = ed1.lfaces[1] if ed1.lfaces[0] == ed1.facemain else ed1.lfaces[0]
        else:
            n1 = n0 - 1 + odd
            face1 = ed1.facemain
        lq1 = []
        for i in range(0, nb):
            for j in range(0, n1 + 1):
                lq1.append(lquads[i * nb + j])
        if len(lq1) > 0:
            quad = lquads[0]
            normalref = self.compute_normal_reference(ed1, face1, quad[0], quad[1])
            vmesh.append([lq1, face1, normalref])

        # Side corner 1
        lq2 = []
        for i in range(0, n0 + odd):
            for j in range(n1 + 1, nb):
                lq2.append(lquads[i * nb + j])
        if len(lq2) > 0:
            quad = lquads[n1 + 1]
            normalref = self.compute_normal_reference(ed1, ed0.facemain, quad[1], quad[0])
            vmesh.append([lq2, ed0.facemain, normalref])

        # Side corner 2
        lq3 = []
        for i in range(n0 + odd, nb):
            for j in range(n1 + 1, nb):
                lq3.append(lquads[i * nb + j])
        if parallel(ed2.facemain.normal, face1.normal):
            face2 = ed2.lfaces[1] if ed2.lfaces[0] == ed2.facemain else ed2.lfaces[0]
        else:
            face2 = ed2.lfaces[0] if ed2.lfaces[0] == ed2.facemain else ed2.lfaces[1]
        if len(lq3) > 0:
            quad = lquads[(n0 + odd) * nb + 1]
            normalref = self.compute_normal_reference(ed2, face2, quad[1], quad[0])
            vmesh.append([lq3, face2, normalref])

        # Storing the mesh
        vd.vmesh = vmesh

    # Compute round corner for termination with 4 edges
    def corner_compute_round_4(self, vd):
        # Computing the cross sections for each edge
        leds = vd.leds
        for ed in leds:
            icorner0 = 0 if ed.corners[0] == vd else 1
            self.compute_sections_multi(ed, icorner0)

        # picking one edge
        ed0 = leds[0]

        # looking for adjacent edges
        oface0 = ed0.lfaces[1] if ed0.facemain == ed0.lfaces[0] else ed0.lfaces[0]
        ed1 = find(leds, lambda ed: ed != ed0 and self.ed_common_face(ed0, ed0.facemain, ed))
        ed2 = find(leds, lambda ed: ed != ed0 and ed != ed1 and \
                        self.ed_common_face(ed0, oface, ed))
        ed4 = find(leds, lambda ed: ed != ed0 and ed != ed1 and ed != ed2)

        # orientation of the edges
        icorner0 = 0 if ed0.corners[0] == vd else 1
        icorner1 = 0 if ed1.corners[0] == vd else 1
        icorner2 = 0 if ed2.corners[0] == vd else 1
        icorner4 = 0 if ed4.corners[0] == vd else 1

        xsection0 = ed0.cross_sections[icorner0]
        xsection1 = ed1.cross_sections[icorner1]
        xsection2 = ed2.cross_sections[icorner2]
        xsection4 = ed4.cross_sections[icorner4]
 
        if xsection1[0] in xsection0:
            xfirst = xsection0
            xlast = xsection4
        else:
            xlast = xsection0
            xfirst = xsection4

        if xfirst[0] in xsection1:
            xfirst = xfirst[::]
            xfirst.reverse()
        if xlast[0] in xsection1:
            xlast = xlast[::]
            xlast.reverse()
        if (xsection2[0] - xsection1[0]).length > (xsection2[0] - xsection1[-1]).length and \
            (xsection2[-1] - xsection1[0]).length < (xsection2[-1] - xsection1[-1]).length:
            xsection2 = xsection2[::]
            xsection2.reverse()
 
        # creating the grid sections
        profile0 = ['C', self.num_seg] if ed0.round_profile else self.profile_type
        vec1 = ed1.ptmid - vd.vertex.co
        vec2 = ed2.ptmid - vd.vertex.co

        lpts = [xfirst]
        n = len(xsection1) - 2
        n1 = n // 2
        for i in range(1, n1 + 1):
            norm = (xsection1[i + 1] - xsection1[i]).cross(vec1)
            sec = self.profile_compute_by_vectors(profile0, xsection2[i], vec2,
                    xsection1[i], norm)
            sec.reverse()
            lpts.append(sec)
        for i in range(n1 + 1, n + 1):
            norm = (xsection2[i + 1] - xsection2[i]).cross(vec2)
            lpts.append(self.profile_compute_by_vectors(profile0, xsection1[i],
                    vec1, xsection2[i], norm))
        lpts.append(xlast)

        # Constructing the vmesh
        vmesh = []
        lquads = []
        n = len(lpts) - 2
        for i in range(0, n + 1):
            pts1 = lpts[i]
            pts2 = lpts[i + 1]
            m = len(pts1) - 2
            for j in range(0, m + 1):
                if vec_approx_eq(pts1[j + 1], pts2[j + 1]):
                    pts = [pts1[j], pts1[j + 1], pts2[j]]
                elif vec_approx_eq(pts1[j], pts2[j]):
                    pts = [pts1[j], pts1[j + 1], pts2[j + 1]]
                else:
                    pts = [pts1[j], pts1[j + 1], pts2[j + 1], pts2[j]]
                lquads.append(pts)

        # List of faces
        nb = self.num_seg
        n0 = nb // 2
        odd = (nb % 2) == 1

        # First quadrant
        quad = lquads[0]
        pt = quad[0]
        ll = self.locate_point_face_4(pt, ed0, ed1, ed2, ed4)
        faceA = ll[0]
        edA = ll[1]
        edB = ll[2]
        lq = []
        ni = n0 + odd if parallel(faceA.normal, edB.facemain.normal) else n0
        nj = n0 + odd if faceA == edA.facemain else n0
        for i in range(0, ni):
            for j in range(0, nj):
                lq.append(lquads[i * nb + j])
        if len(lq) > 0:
            normalref = self.compute_normal_reference(edA, faceA, quad[0], quad[1])
            vmesh.push([lq, faceA, normalref])

        # second quadrant
        quad = lquads[nb - 1]
        pt = quad[1]
        ll = self.locate_point_face_4(pt, ed0, ed1, ed2, ed4)
        faceA = ll[0]
        edA = ll[1]
        edB = ll[2]
        ni2 = n0 + odd if parallel(faceA.normal, edB.facemain.normal) else n0
        for i in range(0, ni2):
            for j in range(nj, nb):
                lq.append(lquads[i * nb + j])
        if len(lq) > 0:
            normalref = self.compute_normal_reference(edA, faceA, quad[1], quad[2])
            vmesh.append([lq, faceA, normalref])

        # third quadrant
        quad = lquads[nb * (nb - 1)]
        pt = quad[3]
        ll = self.locate_point_face_4(pt, ed0, ed1, ed2, ed4)
        faceA = ll[0]
        edA = ll[1]
        edB = ll[2]
        lq = []
        nj = n0 + odd if faceA == edA.facemain else n0
        for i in range(ni, nb):
            for j in range(0, nj):
                lq.append(lquads[i * nb + j])

        if len(lq) > 0:
            normalref = self.compute_normal_reference(edA, faceA, quad[0], quad[1])
            vmesh.append([lq, faceA, normalref])

        # fourth quadrant
        quad = lquads[nb * nb - 1]
        pt = quad[2]
        ll = self.locate_point_face_4(pt, ed0, ed1, ed2, ed4)
        faceA = ll[0]
        edA = ll[1]
        edB = ll[2]
        lq = []
        for i in range(ni2, nb):
            for j in range(nj, nb):
                lq.append(lquads[i * nb + j])
        if len(lq) > 0:
            normalref = self.compute_normal_reference(edA, faceA, quad[1], quad[0])
            vmesh.append([lq, faceA, normalref])

        # Storing the vmesh
        vd.mesh = vmesh

    # Locate on which edge is the given point
    def locate_point_face_4(self, pt, ed0, ed1, ed2, ed4):
        for ll in [[ed0, ed1], [ed0, ed2], [ed4, ed1], [ed4, ed2]]:
            face = self.which_face_4(pt, ll[0], ll[1])
            if face:
                return [face] + ll
        return None

    # Determine on which face is a given point
    def which_face_4(self, pt, eda, edb):
        plane = [eda.ptmid, eda.vec.cross(edb.vec)]
        if not on_plane(pt, plane):
            return
        for face in eda.lfaces:
            if self.ed_common_face(eda, face, edb):
                return face
        return None

    # Orthogonal section to an edge at a vertex
    # Let ptA and ptB be the pair intersection points
    # at for the edge at the vertex.
    # Make a plane that goes through ptA and the
    # average normal of the two planes for the edge.
    # Calculate the cross section for the edge at the
    # vertex and project onto the plane, and return that.
    def orthogonal_section_ed(self, ed, vd):
        # getting the pairs and cross points
        icorner = 0 if ed.corners[0] == vd else 1
        iA = 0 if ed.facemain == ed.lfaces[0] else 1
        iB = 1 - iA
        pairA = ed.pairs[2 * icorner + iA]
        pairB = ed.pairs[2 * icorner + iB]
        ptA = pairA.ptcross
        ptB = pairB.ptcross
        vf1 = ed.lfaces[0].normal
        vf2 = ed.lfaces[1].normal
        if vf1.dot(vf2) <= 0:
            vf2 = vf2.copy()
            vf2.negate()
        vfmean = vf1.lerp(vf2, 0.5)

        # computing the projection on plane
        plane = [ptA, vfmean.cross(ptB - ptA)]
        section = self.compute_profile_edge(ed)
        ed.cross_sections[icorner] = [intersect_line_plane([pt, ed.vec], plane) \
                                        for pt in section]
        return ed.cross_sections[icorner]

    # Compute a round corner with 5 or more edges -
    # Triangulation of Rastapopoulos
    def corner_compute_star(self, vd):
        # Computing the cross sections for each edge
        # These cross sections are at the corner but projected onto a plane
        # (see comment for orthogonal_section_ed).
        lsec = [[ed, self.orthogonal_section_ed(ed, vd)] for ed in vd.leds]

        # Finding the pivot point and plane that best fit cross points
        # ptpivot will be the point in the center of the star.
        # It is fac (0.5) of the way between the corner vertex and
        # a point on the best-fitting plane for points on the edge cross sections.
        nb = self.num_seg // 2 + 1
        lptcross = [ll[1][nb] for ll in lsec]
        plane = fit_plane_to_points(lptcross)
        vpos = vd.vertex.co
        ptproj = project_to_plane(vpos, plane)
        normal = vpos - ptproj
        fac = 0.5
        ptpivot = vpos.lerp(ptproj, fac)
        self.lst_mark_points.append(ptpivot)

        # Create the mesh
        vmesh = []
        profile0 = ['C', nb]
        for ll in lsec:
            ed = ll[0]
            xsection = ll[1]
            # For edge ed, take each point in the cross section and make a profile going
            # from the pivot to that point, putting the results lpts.
            lpts = [self.profile_compute_by_vectors(profile0, pt, (pt - vpos), ptpivot, normal) \
                    for pt in xsection]
            lquads = []
            n = len(lpts) - 2
            # For each i, use the pivot->point on edge cross section profile
            # for i and i+1 to make tris and quads.  The first will be a tri.
            for i in range(0, n + 1):
                pts1 = lpts[i]
                pts2 = lpts[i + 1]
                m = len(pts1) - 2
                for j in range(0, m + 1):
                    if vec_approx_eq(pts1[j + 1], pts2[j + 1]):
                        pts = [pts1[j], pts1[j + 1], pts2[j]]
                    elif vec_approx_eq(pts1[j], pts2[j]):
                        pts = [pts1[j], pts1[j + 1], pts2[j + 1]]
                    else:
                        pts = [pts1[j], pts1[j + 1], pts2[j + 1], pts2[j]]
                    lquads.append(pts)

            # Separating the vmesh in two parts
            odd = (self.num_seg % 2) == 1
            if odd == 0:
                n1 = self.num_seg // 2 + odd
                m1 = n1 * (nb + odd) - 1
            else:
                n1 = self.num_seg // 2 + odd + 1
                m1 = n1 * (nb - odd)

            quad = lquads[0]
            faceref = ed.facemain
            normalref = self.compute_normal_reference(ed, faceref, quad[1], quad[0])
            vmesh.append([lquads[0:m1 + 1], faceref, normalref])

            quad = lquads[-1]
            faceref = ed.lfaces[1] if ed.lfaces[0] == ed.facemain else ed.lfaces[0]
            normalref = self.compute_normal_reference(ed, faceref, quad[1], quad[0])
            if m1 >= 0:
                vmesh.append([lquads[m1 + 1:], faceref, normalref])

        vd.vmesh = vmesh

    # Compute a sharp corner with 3 edges in standardized offset mode
    def corner_compute_3sharp(self, vd):
        leds = vd.leds

        # Calculating the bisecting planes
        vpos = vd.vertex.co
        lplanes = []
        for pair in vd.pairs:
            ed1 = pair.leds[0]
            ed2 = pair.leds[1]
            ed0 = find(leds, lambda ed: ed != ed1 and ed != ed2)
            plane = plane_by_3_points(pair.ptcross, vpos, ed0.ptmid)
            lplanes.append([ed0, plane])

        # Calculating the intersections of edge profiles with stop planes
        for ed in leds:
            cross_section = []
            section = compute_profile_edge(ed)
            ptmid = ed.ptmid
            vec = vpos - ptmid
            icorner = 0 if ed.corners[0] == vd else 1
            ed_planes = []
            for ll in lplanes:
                if ll[0] != ed:
                    ed_planes.append(ll[1])
            for pt in section:
                pt1 = intersect_line_plane([pt, vec], ed_planes[0])
                pt2 = intersect_line_plane([pt, vec], ed_planes[1])
                cross_section.append(pt1 \
                    if (pt1 - ptmid).length < (pt2 - ptmid).length else pt2)
            if not on_plane(cross_section[0], plane(ed.facemain)):
                cross_section.reverse()
            ed.cross_sections[icorner] = cross_section

        # Compute the corner triangle if the number of segments is odd
        n = self.num_seg // 2
        if n * 2 == self.num_seg:
            return
        lfaces = []
        for ed in leds:
            lfaces.append(ed.facemain)
        face0 = lfaces[0]
        if parallel(face0.normal, lfaces[1].normal):
            ieds = [0, 1]
        elif parallel(face0.normal, lfaces[2].normal):
            ieds = [0, 2]
        else:
            ieds = [1, 2]
        lpt = []
        ed1 = leds[ieds[0]]
        icorner1 = 0 if ed1.corners[0] == vd else 1
        ed2 = leds[ieds[1]]
        icorner2 = 0 if ed2.corners[0] == vd else 1

        pt1 = ed1.cross_sections[icorner1][n]
        pt2 = ed1.cross_sections[icorner1][n+1]
        pt3 = ed2.cross_sections[icorner2][n+1]
        if pt3 == pt1 or pt3 == pt2:
            pt3 = ed2.cross_sections[icorner2][n]

        lpt.extend([pt1, pt2, pt3]) # or should it be .append??
        faceref = ed1.facemain
        normalref = compute_normal_reference(ed1, faceref, pt1, pt2)
        vd.mesh = [[[lpt], faceref, normalref]]

    # Compute a sharp corner with any number of edges
    def corner_compute_any_sharp(self, vd):
        leds = vd.leds

        hshcross = {}
        for ed in leds:
            hshcross[ed] = []

        # Calculating the sections
        for ed in leds:
            self.intersection_any_sharp(vd, ed)

        # Filtering the edge termination
        # linter will be a hash from (ed, index in cross section for ed)
        # to one of the intersection data calculated for ed at vd.
        # We want the one that minimizes the length of the intersection
        # to the point on the mid-point edge for the index.
        linter = {}
        for inter in vd.sharp_inter:
            pt = inter[0]
            ed0 = inter[1]
            i0 = inter[2]
            icorner0 = 0 if ed0.corners[0] == vd else 1
            nsection0 = ed0.nsection
            make_index_valid(ed0.cross_sections[icorner0], i0)
            ptold = ed0.cross_sections[icorner0][i0]
            if ptold and (pt - nsection0[i0]).length > (ptold - nsection0[i0]).length:
                continue
            ed0.cross_sections[icorner0][i0] = pt
            make_index_valid(inter, 5)
            inter[5] = 0
            make_index_valid(hshcross[ed0], i0)
            hshcross[ed0][i0] = [inter]
            linter[(ed0, i0)] = inter

        # Assigning the intermediate points
        for inter in linter.values():
            pt = inter[0]
            ed1 = inter[3]
            j1 = inter[4]
            icorner1 = 0 if ed1.corners[0] == vd else 1
            ptcross = ed1.cross_sections[icorner1][j1]
            if vec_approx_eq(pt, ptcross):
                continue
            inter = inter[::]
            line = [ptcross, ed1.cross_sections[icorner1][j1 + 1] - ptcross]

            origin = ed1.cross_sections[icorner1][j1]
            ptmid = ed1.cross_sections[icorner1][j1 + 1]
            vec0 = origin - ptmid

            inter[5] = vec0.angle(pt - ptmid)

            hsh = hshcross[ed1][j1]
            hsh.append(inter)
            hsh.sort(key = lambda inter: inter[5])
            make_index_valid(ed1.sharp_sections[icorner1], j1)
            ed1.sharp_sections[icorner1][j1] = [inter[0] for inter in hsh]

        # Identifying the holes
        hsh_edplanes = {}
        for ed in leds:
            lcross = hshcross[ed]
            n0 = len(lcross) - 2
            for i in range(0, n0 + 1):
                linter = lcross[i] + [lcross[i + 1][0]]
                n1 = len(linter) - 2
                for j in range(0, n1 + 1):
                    inter1 = linter[j]
                    inter2 = linter[j + 1]
                    lled = []
                    edc = None
                    for edd in [inter1[1], inter1[3], inter2[1], inter2[3]]:
                        if edd in lled:
                            edc = edd
                        else:
                            lled.append(edd)
                    if len(lled) > 2:
                        self.lst_mark_points.extend([inter1[0], inter2[0]])
                        pt = edc.nsection[i].lerp(edc.nsection[i + 1], 0.5)
                        plane = [pt, (edc.nsection[i + 1] - edc.nsection[i]).cross(edc.vec)]
                        key = (edc, i)
                        hsh_edplanes[key] = [key, edc, i, plane, inter1[0], inter2[0]]
                        self.lst_mark_points.append(pt)

        # Finding the plane intersections
        lst_loops = self.sharp_find_loops(hsh_edplanes)
        for loop in lst_loops:
            for i in range(0, len(loop)):
                lst_insert = self.sharp_intersect_planes(vd, loop)
                if lst_insert:
                    for ll in lst_insert:
                        self.sharp_insert_in_section(vd, ll[0], ll[1], ll[2])
                    break

    # Compute the section for an edge in Sharp mode at a vertex
    # Sets vd.sharp_inter to a list of data about where lines on
    # the cross section for ed0 intersect lines on segments
    # of cross sections of other edges at vd.
    # Each element of list is:
    # [intersection pt, ed0, index in ed0's cross section,
    #  ed1 (another edge), index in ed1's cross section]
    def intersection_any_sharp(self, vd, ed0):
        nsection0 = self.compute_profile_edge(ed0)
        n0 = len(nsection0) - 1
        vec0 = ed0.vec
        for ed1 in vd.leds:
            if ed1 == ed0:
                continue
            vec1 = ed1.vec
            nsection1 = self.compute_profile_edge(ed1)
            for i0 in range(0, n0 + 1):
                pt0 = nsection0[i0]
                line0 = [pt0, vec0]
                for j1 in range(0, n0):
                    pt = self.intersect_between_two_lines(line0, vec1,
                                nsection1[j1], nsection1[j1+1])
                    if pt:
                        vd.sharp_inter.append([pt, ed0, i0, ed1, j1])

    # Determine if a line cuts a segment defined by two points and a vector.
    # line0 is the line we are trying to intersect.
    # Two other lines are defined by direction v1 through points pt1A and pt1B.
    # Where line0 intersections the plane defined by those other two lines,
    # the segment in question is between the two lines at the closest points
    # to the intersection point.
    def intersect_between_two_lines(self, line0, vec1, pt1A, pt1B):
        plane1 = [pt1A, (pt1B - pt1A).cross(vec1)]
        pt = intersect_line_plane(line0, plane1)
        if not pt:
            return None
        ptprojA = project_to_line(pt, [pt1A, vec1])
        ptprojB = project_to_line(pt, [pt1B, vec1])
        vA = ptprojA - pt
        if vA.length < EPSILON:
            return pt
        vB = ptprojB - pt
        if vB.length < EPSILON:
            return pt
        if vA.dot(vB) <= 0.0:
            return pt
        else:
            return None

    # Identify the loops in the holes
    def sharp_find_loops(self, hsh_edplanes):
        lplanes = hsh_edplanes.values()

        # Loop on edges to det
        hshed = {}
        lst_loops = []
        loop = []

        while True:
            # Resuming or continuing at current loop end, or initiating a new loop
            if len(loop) > 0:
                edp0 = loop[-1][1]
                ptend = edp0[4] if edp0[5] == loop[-1][0] else edp0[5]
            else:
                edp0 = find(lplanes, lambda edp: edp[0] not in hshed)
                if not edp0:
                    break
                ptend = edp0[5]
                loop = [[edp0[4], edp0]]
            hshed[edp0[0]] = 1

            # Getting new segment
            edp1 = find(lplanes, lambda edp: edp[0]!= edp0[0] and \
                        (edp[0] not in hshed or hshed[edp[0]] != -1) and \
                        (vec_approx_eq(edp[4], ptend) or vec_approx_eq(edp[5], ptend)))
            if not edp1:
                break

            # Checking if segment was already set
            for i, ll in enumerate(loop):
                if ptend == ll[0]:
                    newloop = [a[1] for a in loop[i:]]
                    for edp in newloop:
                        hshed[edp[0]] = -1
                    lst_loops.append(newloop)
                    loop[i:] = []
                    edp1 = None

            # New segment in loop
            if edp1:
                loop.append([ptend, edp1])

        lst_loops.append([a[1] for a in loop if len(loop) > 0])
        return lst_loops

    # Determinethe intersection of planes for sharp corners.
    # Progressive algorithm, based on heuristics
    def sharp_intersect_planes(self, vd, lplanes):

        # Sorting the planes by inclinations
        # lplanes = self.sharp_sort_planes_by_inclination(vd, lplanes)

        # Algorithm to explore intersections of planes by group of 3
        n = len(lplanes)
        for i0 in range(0, n):
            lst_insert = []
            lst_pt = []
            for i in range(i0, n + i0):
                icur = i0 % n
                inext = (i + 1) % n
                iprev = (i + 2) % n
                lst_3planes = [lplanes[icur], lplanes[inext], lplanes[iprev]]
                ptinter = self.sharp_compute_intersect_planes(vd, lplanes, lst_3planes)
                if not ptinter:
                    continue
                lst_pt.append(ptinter)
                for edp in lst_3planes:
                    lst_insert.append([edp[1], edp[2], ptinter])
                if len(lst_pt) == n - 2:
                    for pt in lst_pt:
                        self.lst_mark_points.append(pt)
                    return lst_insert
        return None

    # Determine the intersection point between 3 planes, and check if valid
    def sharp_compute_intersect_planes(self, vd, all_planes, lst_3planes):
        # Computing the intersection of the 3 planes
        planes = [edp[3] for edp in lst_3planes]
        line = intersect_plane_plane(planes[0], planes[1])
        if not line:
            return None
        ptinter = intersect_line_plane(line, planes[2])
        if not ptinter:
            return None
        if len(all_planes) == 3:
            return ptinter

        # List of all other planes
        otherplanes = [p for p in all_planes if p not in lst_3planes]

        # Check if point is not 'above' otherplane
        vpos = vd.vertex.co
        for edp in otherplanes:
            plane = edp[3]
            if on_plane(ptinter, plane):
                continue
            vdproj = project_to_plane(vpos, plane)
            ptproj = project_to_plane(ptinter, plane)
            if (vdproj - vpos).dot(ptproj - ptinter) > 0:
                # Above
                return None
        return ptinter

    # Insert an intermediate point for the latte
    def sharp_insert_in_section(self, vd, ed, j, ptinter):
        icorner = 0 if ed.corners[0] == vd else 1
        sharp_section = ed.sharp_sections[icorner][j]

        # No point already in the intermediate section
        if not (sharp_section and len(sharp_section) > 0):
            ed.sharp_sections[icorner][j] = [ptinter]
            return

        # Inserting the point in the right place
        ptmid = ed.cross_sections[icorner][j + 1]
        vec0 = ed.cross_sections[icorner][j] - ptmid
        angle0 = vec0.angle(ptinter - ptmid)
        for i, pt in enumerate(sharp_section):
            if pt == ptinter:
                return
            angle = vec0.angle(pt - ptmid)
            if angle > angle0:
                if i == 0:
                    ed.sharp_sections[icorner][j] = [ptinter] + sharp_section
                else:
                    ed.sharp_sections[icorner][j] = sharp_section[0:i] + \
                            [ptinter] + sharp_section[i:]
                return
        ed.sharp_section[icorner][j].append(ptinter)


    # Compute the normal reference at a position of the edge or corner profile,
    # This is done for the right orientation of faces created
    def compute_normal_reference(self, ed, face, pt1, pt2):
        iface = 0 if ed.lfaces[0] == face else 1
        vy = ed.lvecins[iface] + face.normal
        vec = pt2 - pt1
        return vec.cross(vy)

    def compute_face(self, fc):
        f = fc.face
        for i, bmv in enumerate(fc.bmverts):
            if bmv.index in self.hsh_corners:
                v = self.hsh_corners[bmv.index]
                pr = self.pair_for_face(v.pairs, f)
                if pr:
                   fc.newpts[i] = [pr.ptcross]
                else:
                    # This is a face that is not adjacent to
                    # a beveled edge, yet there is a beveled
                    # edge going into this corner.
                    # What to do depends on whether or
                    # not this face is adjacent to a face
                    # that is adjacent to a beveled edge.

                    # One case is that this is a valence-three corner
                    # with only one beveled edge,
                    # and this is the third (unaffected) face.
                    # We need to cut the corner off this face if
                    # we are in the case where the beveled end
                    # is in the plane of this face - we should have
                    # a corner mesh, if so.
                    # TODO: this corner cutting may happen even in
                    # valence > 3 cases, but hard to do.
                    if len(v.vertex.link_edges) == 3 and not v.vmesh:
                       ed = v.leds[0]
                       icorner = 0 if ed.corners[0] == v else 1
                       section = ed.cross_sections[icorner]
                       # Now need to find if we have to
                       # reverse the section.
                       # Find the pairs.
                       e1 = f.loops[i].edge
                       e2 = f.loops[i].link_loop_prev.edge
                       for f1 in e1.link_faces:
                           if f1 != f:
                               pr1 = self.pair_for_face(v.pairs, f1)
                               if pr1:
                                   break
                       for f2 in e2.link_faces:
                           if f2 != f:
                               pr2 = self.pair_for_face(v.pairs, f2)
                               if pr2:
                                   break
                       if not pr1 or not pr2:
                           print("whoops, couldn't find term face pairs")
                           # just so we won't create a dup face:
                           fc.newpts[i] = [v.vertex.co]
                       else:
                           if vec_approx_eq(pr2.ptcross, section[0]):
                               fc.newpts[i] = section
                           else:
                               rsection = section[::]
                               rsection.reverse()
                               fc.newpts[i] = rsection
                    elif len(v.vertex.link_edges) > 3:
                        # Either or both of the edges into this vertex
                        # may have been split because the adjacent face
                        # was adjacent to a beveled edge.
                        e1 = f.loops[i].edge
                        f1 = find(e1.link_faces, lambda g: g != f)
                        e2 = f.loops[i].link_loop_prev.edge
                        f2 = find(e2.link_faces, lambda g: g != f)
                        nco1 = None
                        nco2 = None
                        for ed in v.leds:
                            if f in ed.lfaces:
                                continue
                            if f1 in ed.lfaces:
                                pr1 = self.pair_for_face(v.pairs, f1)
                                if pr1:
                                    nco1 = pr1.ptcross
                            if f2 in ed.lfaces:
                                pr2 = self.pair_for_face(v.pairs, f2)
                                if pr2:
                                    nco2 = pr2.ptcross
                        fc.newpts[i] = [v.vertex.co]
                        if nco1:
                            fc.newpts[i] = fc.newpts[i] + [nco1]
                        if nco2:
                            fc.newpts[i] = [nco2] + fc.newpts[i]

    def pair_for_face(self, lpairs, f):
        for pr in lpairs:
            if pr.lfaces[0] == f:
                return pr
            if pr.lfaces[1] == f:
                return pr
        return None

    # Catena calculations: chain of edges with related offsets
 
    # Compute the extension of a catena for an edge, and its face and corner
    def catena_extend(self, catena, chain, ed, iface, icorner):
        k = 2 * icorner + iface
        if k >= len(ed.pairs):
            return None  # shouldn't happen
        pair = ed.pairs[k]
        if not pair or pair.alone:
            return None
        # should only be two ed's in pair.leds,
        # one is for ed, the other is ed2
        ed2 = find(pair.leds, lambda edd: edd != ed)
        n = 0
        for i, pair2 in enumerate(ed2.pairs):
            if pair2 == pair:
                n = i
                break
        iface2 = n % 2
        if ed2.catenas[iface2] == catena:
            return None
        icorner2 = (n - iface2) // 2
        icorner2 = (icorner2 + 1) % 2
        chain.append([ed2, iface2])
        ed2.catenas[iface2] = catena
        return [ed2, iface2, icorner2]

    # Compute the half chain in a direction for an edge.
    # This is the extension of the chain for (ed, iface) in the
    # direction given by the end of the edge whose vertex
    # has index icorner.
    def catena_compute_half_by_face(self, catena, ed, iface, icorner):
        chain = []
        ll = [ed, iface, icorner]
        while True:
            ll = self.catena_extend(catena, chain, ll[0], ll[1], ll[2])
            if not ll or ll[0] == ed:
                break
        return chain

    # Compute the catena for an initial edge.
    # The catena is for the edge ed as associated
    # with the side of the edge indicated by index
    # iface in its faces.
    def catena_compute(self, ed, iface):
        catena = BCatena()
        self.lst_catenas.append(catena)
        ed.catenas[iface] = catena
        chain1 = self.catena_compute_half_by_face(catena, ed, iface, 0)
        chain2 = []
        if len(chain1) == 0 or chain1[-1] == None or chain1[-1][0] != ed:
            chain2 = self.catena_compute_half_by_face(catena, ed, iface, 1)
        chain2.reverse()
        catena.chain = chain2 + [[ed, iface]] + chain1
        return catena

    # Compute all the catenas in the selection.
    # There are two catenas for each BEdge: one for each incident face.
    # The catena is a chain - list of [ed, face-index] pairs that
    # traverse along matched-up pairs as computed at each vertex.
    def catena_compute_all(self):
        for ed in self.hsh_ed.values():
            for iface in range(0, 2):
                if ed.catenas[iface] is None:
                    self.catena_compute(ed, iface)

        # sorting the eds by angle
        for i, catena in enumerate(self.lst_catenas):
            catena.leds = [ll[0] for ll in catena.chain]
            catena.leds.sort(key = functools.cmp_to_key(lambda ed1, ed2: cmp(ed1.cos, ed2.cos)))

        # sorting the catenas
        for i, catena in enumerate(self.lst_catenas):
            self.catena_sort(catena)

    def catena_offset_all(self):
        for catena in self.lst_catenas:
            icur = self.catena_begin_ed(catena)
            while self.catena_propagate_offset_factors(catena, icur, 1):
                icur += 1
            while self.catena_propagate_offset_factors(catena, icur, -1):
                icur -= 1

    def catena_begin_ed(self, catena):
        # Assigning 1 to the first edge in the sorted list
        ed = catena.leds[0]
        for icur, ll in enumerate(catena.chain):
            if ll[0] == ed:
                if self.strict_offset:
                     ed.lfactors[ll[1]] = 1.0
                return icur
 
    # Propagate the offset factors from an edge to the next one
    def catena_propagate_offset_factors(self, catena, icur, incr):
        chain = catena.chain

        # Checking if end of chain
        inext = icur + incr
        if inext < 0 or inext >= len(catena.chain):
            return False
        llnext = catena.chain[inext]
 
        # Current edge
        llcur = catena.chain[icur]
        edcur = llcur[0]
        ifacecur = llcur[1]
        edgecur = edcur.edge
        facecur = edcur.lfaces[ifacecur]
        ptmidcur = edcur.ptmid
        factorcur = edcur.lfactors[ifacecur]

        # Next edge
        ednext = llnext[0]
        ifacenext = llnext[1]
        edgenext = ednext.edge
        facenext = ednext.lfaces[ifacenext]
        ptmidnext = ednext.ptmid

        # Computing the intersection of the two face planes
        normalcur = facecur.normal
        normalnext = facenext.normal
        if parallel(normalcur, normalnext):
            if self.strict_offset:
                ednext.lfactors[ifacenext] = edcur.lfactors[ifacecur]
            return True
        lineinter = intersect_plane_plane([ptmidcur, normalcur], [ptmidnext, normalnext])

        # Computing the intersection of the offset lines with the intersection of faces
        ptcur = intersect_line_line(edcur.parallels[ifacecur], lineinter)
        ptnext = intersect_line_line(ednext.parallels[ifacenext], lineinter)

        # It is possible that the offset lines don't intersect the face intersection if
        # either face is non-planar.
        if not ptcur or not ptnext:
            return False

        # Common vertex
        vertex = None
        for v1 in edgecur.verts:
            for v2 in edgenext.verts:
                if v1 == v2:
                    vertex = v1
                    break
        vpos = vertex.co

        # Computing the factor for next edge
        dcur = (ptcur - vpos).length
        dnext = (ptnext - vpos).length
        if self.strict_offset:
            ednext.lfactors[ifacenext] = factorcur * dcur / dnext

        return True

    # ??? This is a complete no-op
    def catena_sort(self, catena):
        for ll in catena.chain:
            ed = ll[0]
            iface = ll[1]

    # Create geometry for mesh borders
    def create_geometry_vborders(self, vborders):
        for vb in vborders:
            lpt = vb[0]
            style = vb[1]
            # print("new edge:", V3(lpt[0]), V3(lpt[1]), "style:", style)
            # style could be 'S' or 'P'
            # 'S' means: apply prop_borders (?) to edges
            # 'P' means: not soft or smooth

    # Create geometry for mesh
    def create_geometry_vmesh(self, vmesh):
        for vm in vmesh:
            faceref = vm[1]
            normalref = vm[2]
            # use faceref as example for material, etc.
            allfaces = []
            for lpt in vm[0]:
                # print("new face:", LV3(lpt), "norm:", V3(normalref), "ref:", faceref)
                bmverts = self.get_bmverts(lpt)
                newf = self.bm.faces.new(bmverts)
                allfaces.append(newf)
            for lface in allfaces:
                if normalref and allfaces[0] and allfaces[0].normal.dot(normalref) < 0:
                    bmesh.utils.face_flip(lface)

    def get_bmverts(self, ptlist):
        return [ self.points.get_bmvert(p) for p in ptlist ]

    # Signal errors in preparing the geometry
    def signal_error_vd(self, vd):
        if vd:
            self.hsh_error_vertex[vd.vertex.index] = vd.vertex

    # Profile methods

    # Compute the transformed profile by indicating the start and end point,
    # and the start vector and end face normal.
    # The profile will go from pt2 to pt1, and the origin for the profile
    # will be at the intersection of the line through pt1 in direction vec1
    # and the plane containing pt2 with normal normal2.
    def profile_compute_by_vectors(self, profile_type, pt1, vec1, pt2, normal2):
        origin = intersect_line_plane([pt1, vec1], [pt2, normal2])
        if not origin:
            # Can happen if one of the faces is non-planar
            # Just make an origin to avoid a crash
            origin = pt1.lerp(pt2, 0.5) + (pt2 - pt1).length * Vector([0.1, 0.1, 0.2])
        offset1 = (pt1 - origin).length
        offset2 = (pt2 - origin).length
        vec2 = pt2 - origin
        return self.profile_compute_by_offset(profile_type, origin, vec1, offset1, vec2, offset2)

    def profile_compute_by_vectors2(self, profile_type, pt1, vec1, pt2, vec2):
        lpt = closest_points([pt1, vec1], [pt2, vec2])
        origin = lpt[0].lerp(lpt[1], 0.5)
        vec1 = pt1 - origin
        vec2 = pt2 - origin
        offset1 = vec1.length
        offset2 = vec2.length
        return self.profile_compute_by_offset(profile_type, origin, vec1, offset1, vec2, offset2)

    # Compute the transformed profile by indicating the offsets and direction on faces.
    # The origin is mapped to the 0,0 of the profile (e.g., the center of the circle
    # for a quarter-circle profile).
    # The start of the profile will be mapped to offset2 in the direction of vec2 from origin.
    # The end of the profile will be mapped to offset1 in the direction of vec1 from the origin.
    # (Think of vec1 -> the x-axis, vec2 -> y-axis, and profile goes from (0, 1) to (1, 0) in 2d).
    def profile_compute_by_offset(self, profile_type, origin, vec1, offset1, vec2, offset2):
        # Getting the nominal profile
        pts = self.nominal_profile(profile_type)

        # Transformation from golden normalized form:
        # Takes nominal profile endpoints (0,1,0) and (1,0,0)
        # to (0, offset1, 0) and (offset1, 0, 0) respectively
        tsg = mathutils.Matrix([[0.0, -offset1, 0.0, offset1],
                               [-offset1, 0.0, 0.0, offset1],
                               [0.0, 0.0, 1.0, 0.0],
                               [0.0, 0.0, 0.0, 1.0]])

        # Scaling and shearing to adjust differences of offset and angle
        angle = 0.5 * math.pi - vec1.angle(vec2, 0.0)
        tgt = math.tan(angle)
        fac = offset2 / offset1 * math.cos(angle)

        # Stretch y by fac
        ts = mathutils.Matrix([[1.0, 0.0, 0.0, 0.0],
                               [0.0, fac, 0.0, 0.0],
                               [0.0, 0.0, 1.0, 0.0],
                               [0.0, 0.0, 1.0, 1.0]])

        # Shear in x, by factor of tgt as move up in y
        tsh = mathutils.Matrix([[1.0, tgt, 0.0, 0.0],
                                [0.0, 1.0, 0.0, 0.0],
                                [0.0, 0.0, 1.0, 0.0],
                                [0.0, 0.0, 0.0, 1.0]])

        # Transforming to match given coordinates at origin, vec1, vec2
        normal = vec1.cross(vec2)
        normal.normalize()
        ux = vec1
        ux.normalize()
        uy = normal.cross(ux)
        uz = normal
        taxe = mathutils.Matrix()
        taxe = mathutils.Matrix([[ux[0], uy[0], uz[0], origin[0]],
                                 [ux[1], uy[1], uz[1], origin[1]],
                                 [ux[2], uy[2], uz[2], origin[2]],
                                 [0.0, 0.0, 0.0, 1.0]])
        t = taxe * tsh * ts * tsg

        # Performing the transformation
        return [t * pt for pt in pts]

    # Get the nominal profile and compute Nb of segment
    def verify_profile(self, profile_type, numseg = None):
        ty = profile_type
        self.num_seg_lock = ty == 'P'
        if numseg and not self.num_seg_lock:
            self.profile_type[1] = numseg
        pts = self.nominal_profile(self.profile_type)
        self.num_seg = len(pts) - 1

    # Get the nominal profile and compute Nb of segment
    def nominal_profile(self, profile_type):
        # Computing the normalized profile in X, Y
        ty = profile_type[0]
        param = profile_type[1]
        key = ty + "-" + str(param)

        # Standard profiles
        if key in self.hsh_profile_pts:
            pts = self.hsh_profile_pts[key]
        else:
            if ty == 'BZ':
                pts = self.golden_bezier(param)
            elif key == 'CR':
                pts = self.golden_circular_reverse(param)
            elif key == 'P':
                pts = self.golden_perso(param)
            else:
                pts = self.golden_circular(param)
            self.hsh_profile_pts[key] = pts
        return pts

    # Makes a quarter circle profile from
    # (0, 1, 0) to (1, 0, 0) with nb_seg line segments
    def golden_circular(self, nb_seg):
        pts = []
        anglesec = 0.5 * math.pi / nb_seg
        for i in range(0, nb_seg + 1):
            angle = anglesec * i
            x = math.cos(angle)
            y = math.sin(angle)
            pts.append(Vector([x, y, 0.0]))
        pts.reverse()
        return pts

    # Makes a a concave quarter circle profile from
    # (0, 1, 0) to (1, 0, 0)
    def golden_circular_reverse(self, nb_seg):
        pts = []
        anglesec = 0.5 * math.pi / nb_seg
        for i in range(0, nb_seg + 1):
            angle = anglesec * i
            x = 1.0 - math.sin(angle)
            y = 1.0 - math.cos(angle)
            pts.append(Vector([x, y, 0.0]))
        pts.reverse()
        return pts

    def golden_bezier(self, nb_seg):
        pt1 = Vector([0.0, 1.0, 0.0])
        pt2 = Vector([1.0, 1.0, 0.0])
        pt3 = Vector([1.0, 0.0, 0.0])
        ctrl_pts = [pt1, pt2, pt3]
        # TODO: BezierCurve.compute(ctrl_pts, nb_seg)
        return []

    def golden_perso(self, fac):
        pt1 = Vector([0.0, 1.0, 0.0])
        pt2 = Vector([1.0, 1.0, 0.0])
        pt3 = Vector([1.0, 0.0, 0.0])
        pt4 = Vector([fac, fac, 0.0])
        ctrl_pts = [pt1, pt2, pt3]
        # TODO: BezierCurve.compute(ctrl_pts, 8)
        ctrl_pts = [crv[3], pt4, crv[5]]
        crv2 = BezierCurve.compute(ctrl_pts, 6)
        crv = crv1[1:3] + crv2 + crv1[6:]
        return crv

    def print(self):  # XXX - better call something else
        print("BevelRoundAlgo:")
        print("offset", self.offset)
        print("num_seg", self.num_seg)
        print("hsh_ed:")
        for i, ed in self.hsh_ed.items():
            print("E%d ->" % i)
            ed.print()
        print("hsh_corners:")
        for i, v in self.hsh_corners.items():
            print("V%d ->"  % i)
            v.print()
        print("hsh_faces:")
        for i, fc in self.hsh_faces.items():
            print("F%d ->" % i)
            fc.print()
        print("lst_catenas", " ".join([str(cat) for cat in self.lst_catenas]))
        print("lpt_borders:")
        print("  ", " ".join([V3(p) for p in self.lpt_borders]))
        print("hsh_profile_pts:")
        for s, pts in self.hsh_profile_pts.items():
            print(s, "->", LV3(pts))
        print("lst_mark_points", self.lst_mark_points)
        print("lst_triangulated", self.lst_triangulated)
        print("hsh_error_vertex", self.hsh_error_vertex)
        print("hash_edges", self.hash_edges)
        print("hash_edges_extra", self.hash_edges_extra)
        print("hsh_vertex_info", self.hsh_vertex_info)
        print("profile_type", self.profile_type)
        print("mode_profile", self.mode_profile)
        print("mode_sharp", self.mode_sharp)
        print("strict_offset", self.strict_offset)
        print("mode_rounding", self.mode_rounding)


# Wraps a bmesh edge involved in beveling
class BEdge(object):
    def __init__(self, edge):
        self.edge = edge
        self.index = edge.index
        if len(edge.link_faces) != 2:
            print("whoops, edge doesn't have exactly two faces")
            return
        face1 = edge.link_faces[0]
        face2 = edge.link_faces[1]
        self.lfaces = [face1, face2]
        # lvecins are in face1, face2 planes, perp to edge, pointing in
        self.lvecins = [normal_in_to_edge(edge, face1), normal_in_to_edge(edge, face2)]
        # angle is deviation of two planes meeting angle from 90 degrees
        # (positive angle: they meet at less than 90)
        self.angle = 0.5 * math.pi - self.lvecins[0].angle(self.lvecins[1], 0.0)
        self.cos = math.cos(self.angle)
        # cosinv is the amount one should move along a face to have the
        # same effect as moving 1.0 along the 90 degree-meeting face
        self.cosinv = 1 / self.cos if abs(self.cos) >= 1e-2 else 100.0
        self.lfactors = [self.cosinv, self.cosinv]
        self.corners = []
        # catenas is indexed by corner index (0 for first vert, 1 for second)
        self.catenas = [None, None]
        # pairs is indexed by 2 * (corner index) + face index
        # each gives a pair matching the this to a corresponding
        # (edge, corner index, face index) that this edge can continue to
        self.pairs = [None, None, None, None]
        self.cross_sections = [[], []]
        self.sharp_sections = [[], []]
        self.golden = 100
        self.aligned = False
        vxbeg = edge.verts[0]
        vxend = edge.verts[1]
        # vec is normalized edge direction and length is edge length
        self.vec = vxend.co - vxbeg.co
        self.length = self.vec.length
        self.vec.normalize()
        self.round_profile = False
        # ptmid is the midpoint of the edge
        self.ptmid = vxend.co.lerp(vxbeg.co, 0.5)
        self.parallels = [[self.ptmid + vecin, self.vec] for vecin in self.lvecins]
        self.loffset = [None, None]
        self.profile = None
        self.facemain = None
        self.nsection = None
        self.vmesh = None
        self.vborders = None

    def __str__(self):
        return "ed%d" % self.index

    def print(self):
        print("BEdge", self.index)
        print("  edge", V3(self.edge.verts[0].co), V3(self.edge.verts[1].co))
        print("  lfaces", F(self.lfaces[0]), F(self.lfaces[1]))
        print("  lvecins", V3(self.lvecins[0]), V3(self.lvecins[1]))
        print("  angle %.3f" % self.angle)
        print("  lfactors", ["%.3f" % fac for fac in self.lfactors])
        print("  corners", [str(v) for v in self.corners])
        print("  catenas", [str(cat) for cat in self.catenas])
        print("  vec", V3(self.vec))
        print("  ptmid", V3(self.ptmid))
        print("  pairs: (icorner, iface) in (0,0), (0,1), (1,0), (1,1)")
        for pair in self.pairs:
            pair.print()
        print("  parallels", [[V3(p), V3(n)] for (p,n) in self.parallels])
        if self.cross_sections:
            print("  cross_sections:")
            for cs in self.cross_sections:
                print("   ", LV3(cs))
        if self.sharp_sections:
            print("  sharp_sections:")
            for cs in self.sharp_sections:
                print("   ", cs)
        print("  round_profile", self.round_profile)
        print("  loffset", self.loffset)
        print("  profile", self.profile)
        print("  facemain", F(self.facemain))
        print("  nsection", LV3(self.nsection))
        if self.vmesh:
            print("  vmesh:")
            for vm in self.vmesh:
                print("    face: faceref=%s, norm=%s" % (F(vm[1]), V3(vm[2])))
                for lpt in vm[0]:
                    print("     ", ",".join([V3(p) for p in lpt]))
        if self.vborders:
            print("  vborders:")
            for vb in self.vborders:
                if len(vb[0]) == 2:
                    (p1, p2) = vb[0]
                    print("    edge:", V3(p1), V3(p2), vb[1])


# Wraps a bmesh vertex involved in beveling
class BCorner(object):
    def __init__(self, v, ed):
        self.vertex = v
        self.index = v.index
        self.leds = [ed]
        self.pairs = []
        self.gold_ed = None
        self.sharp_inter = []
        self.round_pair = None
        self.convex = None
        self.vmesh = None

    def __str__(self):
        return "c%d" % self.index

    def print(self):
        print("BCorner", self.index)
        print("  vertex", V3(self.vertex.co))
        print("  leds", [str(ed) for ed in self.leds])
        print("  pairs", [str(pair) for pair in self.pairs])
        print("  gold_ed", self.gold_ed)
        if self.sharp_inter:
            print("  sharp_inter:")
            for si in self.sharp_inter:
                print(V3(si[0]), si[1], si[2], si[3], si[4])
        print("  round_pair", self.round_pair)
        print("  convex", self.convex)
        if self.vmesh:
            print("  vmesh:")
            for vm in self.vmesh:
                print("    face: faceref=%s, norm=%s" % (F(vm[1]), V3(vm[2])))
                for lpt in vm[0]:
                    print("     ", ",".join([V3(p) for p in lpt]))

# Wraps a bmesh face involved in beveling
class BFace(object):
    def __init__(self, f):
        self.face = f
        self.index = f.index
        self.bmverts = [lp.vert for lp in f.loops]
        self.bmedges = [lp.edge for lp in f.loops]
        self.edgereversed = [self.bmedges[i].verts[0] == self.bmverts[i] \
            for i in range(0, len(self.bmverts))]
        # for verts that change to one or more new points,
        # self.newpts[i] is list of float triple for replacement
        self.newpts = len(self.bmverts) * [None]

    def anynew(self):
        for p in self.newpts:
            if p is not None:
                return True
        return False

    # Probably should give access to C routine BM_face_point_inside_test
    # but for now reimplement it here
    def contains_point(self, v):
        (ax, ay) = axis_dominant(self.face.normal)
        co2 = Vector([v[ax], v[ay]])
        cent = Vector([0.0, 0.0])
        for l in self.face.loops:
            v = l.vert.co
            cent = cent + Vector([v[ax], v[ay]])
        cent = cent / len(self.face.loops)
        crosses = 0
        onepluseps = 1.0 + EPSILON * 150.0
        out = Vector([1e30, 1e30])
        for l in self.face.loops:
            vprev = l.link_loop_prev.vert.co
            v = l.vert.co
            v1 = (Vector([vprev[ax], vprev[ay]]) - cent) * onepluseps + cent
            v2 = (Vector([v[ax], v[ay]]) - cent) * onepluseps + cent
            if line_segments_cross(v1, v2, co2, out):
                crosses += 1
        return crosses % 2 != 0

    def __str__(self):
        return "f%d" % self.index

    def print(self):
        print("BFace", self.index)
        print("  bmverts", [V(v) for v in self.bmverts])
        print("  bmedges", [E(e) for e in self.bmedges])
        print("  edgereversed", self.edgereversed)
        print("  newpts", [LV3(pl) if pl else 'None' \
            for pl in self.newpts])
        

# At vertices to be beveled, the incoming edges involved
# in beveling are matched up in pairs (to be connected up).
# There will be two pairs for such a matchup: one for each
# face-side of the edge.
# So (ed1, face1) is a BEdge and one of the bmesh faces
# that is incident on it, and similarly for (ed2, face2).
# Some edges won't get matched and are 'alone' pairs
# with None for all of the second components.
class BPair(object):
    def __init__(self, vd, ed1, face1, ed2, face2):
        edge1 = ed1.edge
        edge2 = ed2.edge if ed2 else None
        self.vd = vd
        self.ledges = [edge1, edge2]
        self.leds = [ed1, ed2]
        self.lfaces = [face1, face2]
        self.ptcross = None
        self.edge_terms = []
        self.monoface = True
        self.convex = False
        self.alone = not edge2
        self.rounding = None
        self.mode = None

    def __str__(self):
        if not self.alone:
            return "pr2(%s,%s)(%s,%s)" % \
                (self.leds[0], F(self.lfaces[0]), self.leds[1], F(self.lfaces[1]))
        else:
            return "pr1(%s,%s)" % (self.leds[0], F(self.lfaces[0]))

    def print(self):
        print("BPair", str(self))
        print("  ptcross", V3(self.ptcross))
        print("  edge_terms", [E(e) for e in self.edge_terms])
        print("  monoface", self.monoface, "convex", self.convex,
            "rounding", self.rounding, "mode", self.mode)

# A catena is a chain - a list of [ed, face-index] pairs that
# traverse along matched-up pairs as computed at each vertex.
class BCatena(object):
    def __init__(self):
        self.chain = []
        self.leds = []
        self.nbsmall = 0

    def __str__(self):
        return "catena(" + \
            " ".join(["(%s,%d)" % (p[0], p[1]) for p in self.chain]) + \
            ", %d)" % self.nbsmall


# distances less than about DISTTOL will be considered
# essentially zero
DISTTOL = 1e-4
INVDISTTOL = 1e4

class Points(object):
    """Container of points without duplication, each mapped to a BMVert

    Points are triples of floats.

    Implementation:
    In order to efficiently find duplicates, we quantize the points
    to triples of ints and map from quantized triples to vertex
    index.
    """

    def __init__(self, bm):
        self.pos = []
        self.bm = bm
        self.invmap = dict()

    def get_bmvert(self, p):
        """Return the BMVert for the given point, making one if necessary.

        Args:
          p: 3-tuple of float - coordinates
        Returns:
          BMVert - the vertex of added (or existing) point
        """

        qp = tuple([int(round(v * INVDISTTOL)) for v in p])
        if qp in self.invmap:
            return self.invmap[qp]
        else:
            newv = self.bm.verts.new(p)
            self.invmap[qp] = newv
            self.pos.append(p)
            return newv


# Returns vector perpendicular to edge in face plane
# pointing to the interior of the fac
def normal_in_to_edge(edge, face):
    pt1 = edge.verts[0].co
    pt2 = edge.verts[1].co
    vec = face.normal.cross(pt2 - pt1)
    vec.normalize()
    if edge_reversed_in_face(edge, face):
        vec.negate()
    return vec


# Returns True if if two edges form a convex corner in face
# at vertex
def convex_at_vertex(vertex, face, edge1, edge2, face2=None):
    vother1 = edge1.other_vert(vertex)
    vec1 = vother1.co - vertex.co
    vecin1 = normal_in_to_edge(edge1, face)
    vecin2 = normal_in_to_edge(edge2, face2 if face2 else face)
    # I don't understand this computation: seems to take dot
    # product of two vectors that are the face normal (?)
    return vec1.cross(vecin1).dot(vecin1.cross(vecin2)) >= 0


# For the functions on 'planes' and 'lines':
# A plane defined by [point-on-plane, plane-normal]
# A line is defined by [point-on-line, line-direction-vector]


# Return Vector that is point where line intersects plane,
def intersect_line_plane(line, plane):
    (lv, vec) = line
    (pp, pnorm) = plane
    return mathutils.geometry.intersect_line_plane(lv, lv + vec, pp, pnorm)


# Return intersection point of the two lines, or None.
def intersect_line_line(linea, lineb):
    (av, avec) = linea
    (bv, bvec) = lineb
    (cv1, cv2) = mathutils.geometry.intersect_line_line(av, av + avec, bv, bv + bvec)
    if vec_approx_eq(cv1, cv2):
        return cv1
    else:
        return None


# Return intersection line of two planes
def intersect_plane_plane(plane1, plane2):
    (pp1, pnorm1) = plane1
    (pp2, pnorm2) = plane2
    (a, b) = mathutils.geometry.intersect_plane_plane(pp1, pnorm1, pp2, pnorm2)
    # seems like it returns (pt-on-line, line-dir)
    return (a, b)

# Return closes points of two lines as tuple of two.
def closest_points(linea, lineb):
    (av, avec) = linea
    (bv, bvec) = lineb
    return mathutils.geometry.intersect_line_line(av, av + avec, bv, bv + bvec)


# Intersection where point must be between endpoints of edge
def intersect_edge_line(edge, line):
    pt = intersect_line_line([edge.verts[0].co, edge.verts[1].co - edge.verts[0].co], line)
    if not pt:
        return None
    ptbeg = edge.verts[0].co
    if vec_approx_eq(pt, ptbeg):
        return pt
    ptend = edge.verts[1].co
    if vec_approx_eq(pt, ptend):
        return pt
    if (ptbeg-pt).dot(ptend-pt) < 0:
        return pt
    else:
        return None


# Project a point onto a plane
def project_to_plane(point, plane):
    (pco, pnorm) = plane
    ptb = point + pnorm
    return mathutils.geometry.intersect_line_plane(point, ptb, pco, pnorm)


# Project a point onto a line
def project_to_line(point, line):
    (lv, lvec) = line
    (ptproj, _) = mathutils.geometry.intersect_point_line(point, lv, lv + lvec)
    return ptproj


# Return the plane the best fits the points.
# The right way to do this involves finding a singular value decomposition.
# (search for "Orthogonal Distance Regression Planes").
# For now, just use the centroid as point on the plane and
# the average normal.
def fit_plane_to_points(pts):
    n = len(pts)
    if n < 3:
        return None
    center = pts[0]
    for i in range(1, n):
        center = center + pts[i]
    center = center / n
    # Newell method for normal, pretending this is a polygon
    sumx = 0.0
    sumy = 0.0
    sumz = 0.0
    for i in range(0, n):
        a = pts[i]
        b = pts[(i + 1) % n]
        sumx += (a[1] - b[1]) * (a[2] + b[2])
        sumy += (a[2] - b[2]) * (a[0] + b[0])
        sumz += (a[0] - b[0]) * (a[1] + b[1])
    norm = mathutils.Vector([sumx, sumy, sumz])
    norm.normalize()
    return [center, norm]


# Return True if point is on the plane
def on_plane(point, plane):
    (pp, pnorm) = plane
    d = mathutils.geometry.distance_point_to_plane(point, pp, pnorm)
    return abs(d) < EPSILON


# Return True if point is on the line
def on_line(point, line):
    (lv, lvec) = line
    (vint, _) = mathutils.geometry.intersect_point_line(point, lv, lv + lvec)
    return (point-vint).length < EPSILON


def parallel(v1, v2):
    return abs(v1.cross(v2).length) < EPSILON


# A plane is a [point-on-plane, normal-vec] tuple
def face_plane(face):
    return [face.verts[0].co, face.normal]


# Return True if Vectors are approximately equal
def vec_approx_eq(a, b):
    return (a-b).length < EPSILON


# Return True if edge points in CW direction around face
# when viewed from the side the normal is pointing to
def edge_reversed_in_face(edge, face):
    for lp in face.loops:
        if lp.edge == edge:
            return lp.vert != edge.verts[0]
    print("whoops, edge_reversed_in_face: edge not in face")
    return False


# Find the indices of axes which make for closest
# alignment with vector axis, for a fast projection
# of 3d -> 2d
def axis_dominant(axis):
    xn = abs(axis[0])
    yn = abs(axis[1])
    zn = abs(axis[2])
    if zn >= xn and zn >= yn:
        return (0, 1)
    elif yn >= xn and yn >= zn:
        return (0, 2)
    else:
        return (1, 2)


# Return True if v3 is to the right of line v1v2
# but False if v3 is the same as v1 or v2
# (all points are 2d Vectors)
def test_edge_side(v1, v2, v3):
    inp = (v2[0] - v1[0]) * (v1[1] - v3[1]) + (v1[1] - v2[1]) * (v1[0] - v3[0])
    if inp < 0.0:
        return False
    elif inp < 0.0:
        if v1 == v3 or v2 == v3:
            return False
    return True


# Return True if two line segments cross each other
# with careful attention to edge cases
def line_segments_cross(v1, v2, v3, v4):
    eps = EPSILON * 15
    w1 = test_edge_side(v1, v3, v2)
    w2 = test_edge_side(v2, v4, v1)
    w3 = not test_edge_side(v1, v2, v3)
    w4 = test_edge_side(v3, v2, v4)
    w5 = not test_edge_side(v3, v1, v4)
    if w1 == w2 == w3 == w4 == w5:
        return True
    mv1= (min(v1[0], v2[0]), min(v1[1], v2[1]))
    mv2 = (max(v1[0], v2[0]), max(v1[1], v2[1]))
    mv3= (min(v3[0], v4[0]), min(v3[1], v4[1]))
    mv4 = (max(v3[0], v4[0]), max(v3[1], v4[1]))
    if abs(v1[1] - v2[1]) < eps and abs(v3[1] - v4[1]) < eps and abs(v1[1] - v3[1]) < eps:
        return (mv4[0] >= mv1[0] and mv3[0] <= mv2[0])
    if abs(v1[0] - v2[0]) < eps and abs(v3[0] - v4[0]) < eps and abs(v1[0] - v3[0]) < eps:
        return (mv4[1] >= mv1[1] and mv3[1] <= mv2[1])
    return False


# Three-way compare
def cmp(a, b):
    return (a > b) - (a < b)


# A find-in-iterable function
def find(iterable, func):
    for x in iterable:
        if func(x):
            return x
    return None

# Grow a sequence, if necessary, with Nones, to make i a valid index
def make_index_valid(s, i):
    if i >= len(s):
        s.extend((i - len(s) + 1) * [None])

# for debug prints
def V3(v):
    return "None" if not v else "(%.2f,%.2f,%.2f)" % (v[0], v[1], v[2])

def V2(v):
    return "None" if not v else "(%.2f,%.2f)" % (v[0], v[1])

def LV3(lv):
    return "None" if not lv else ",".join([V3(v) for v in lv])

def F(f):
    return "None" if not f else "F%d" % f.index

def E(e):
    return "None" if not e else "E%d" % e.index

def V(v):
    return "None" if not v else "V%d" % v.index

def printmat(mat, str):
    print(str)
    for i in range(0,4):
        print("  |" + " ".join(["%5.2f" % mat[i][j] for j in range(0,4)]) + "|")


def panel_func(self, context):
    self.layout.label(text="Bevel Round:")
    self.layout.operator("mesh.bevel_round", text="Bevel Round")


def register():
    bpy.utils.register_class(BevelRound)
    bpy.types.VIEW3D_PT_tools_meshedit.append(panel_func)


def unregister():
    bpy.utils.unregister_class(BevelRound)
    bpy.types.VIEW3D_PT_tools_meshedit.remove(panel_func)


if __name__ == "__main__":
    register()
