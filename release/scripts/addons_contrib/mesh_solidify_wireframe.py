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
    "name": "Solid Wire Frame ALT",
    "author": "Campbell Barton",
    "version": (1, 0),
    "blender": (2, 6, 2),
    "location": "3D View Toolbar",
    "description": "Make solid wire",
    "warning": "",  # used for warning icon and text in addons panel
    # "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"
    #             "Scripts/Modeling/Mesh_WireFrane',
    # "tracker_url": "https://projects.blender.org/tracker/index.php?"
    #                "func=detail&aid=22929",
    "category": "Mesh"}


import bmesh
import bpy


def add_nor(no_a, no_b):
    if no_a.dot(no_b) > 0.0:
        return no_a + no_b
    else:
        return no_a - no_b


def calc_boundary_tangent(v):
    e_a, e_b = [e for e in v.link_edges if e.is_boundary][0:2]

    l_a = e_a.link_loops[0]
    l_b = e_b.link_loops[0]

    # average edge face normal
    no_face = add_nor(l_a.face.normal, l_b.face.normal)

    # average edge direction
    v_a = e_a.other_vert(v)
    v_b = e_b.other_vert(v)

    no_edge = (v_a.co - v.co).normalized() + (v.co - v_b.co).normalized()

    # find the normal
    no = no_edge.cross(no_face).normalized()

    # check are we flipped the right way
    ta = e_a.calc_tangent(l_a) + e_b.calc_tangent(l_b)
    if no.dot(ta) < 0.0:
        no.negate()

    return no


import math


def shell_angle_to_dist(angle):
    return 1.0 if angle < 0.000001 else abs(1.0 / math.cos(angle))


# first make 2 verts per vert
def solid_wire(bm_src, depth=0.01, use_boundary=True, use_even_offset=True):
    bm_dst = bmesh.new()

    bm_src.verts.index_update()

    inset = depth

    verts_neg = []
    verts_pos = []

    is_boundary = False

    if use_boundary:
        verts_boundary = [None] * len(bm_src.verts)

    for v in bm_src.verts:
        co = v.co
        no_scale = v.normal * depth
        verts_neg.append(bm_dst.verts.new(co - no_scale))
        verts_pos.append(bm_dst.verts.new(co + no_scale))

        if use_boundary:
            v.tag = False
            v.select = False

    verts_loop = []

    for f in bm_src.faces:
        for l in f.loops:
            l.index = len(verts_loop)
            in_scale = l.calc_tangent() * inset

            if use_even_offset:
                in_scale *= shell_angle_to_dist((math.pi - l.calc_angle()) * 0.5)

            verts_loop.append(bm_dst.verts.new(l.vert.co + in_scale))

            # boundary
            if use_boundary:
                if l.edge.is_boundary:
                    for v in (l.vert, l.link_loop_next.vert):
                        if not v.tag:
                            is_boundary = True
                            v.tag = True             # don't copy the vert again
                            l.edge.tag = False  # we didn't make a face yet

                            v_boundary_tangent = calc_boundary_tangent(v)

                            in_scale = v_boundary_tangent * inset

                            if use_even_offset:
                                in_scale *= shell_angle_to_dist((math.pi - l.calc_angle()) * 0.5)

                            v_boundary = verts_boundary[v.index] = bm_dst.verts.new(v.co + in_scale)

                            # TODO, make into generic function

    # build faces
    for f in bm_src.faces:
        for l in f.loops:
            l_next = l.link_loop_next
            v_l1 = verts_loop[l.index]
            v_l2 = verts_loop[l_next.index]

            v_src_l1 = l.vert
            v_src_l2 = l_next.vert

            i_1 = v_src_l1.index
            i_2 = v_src_l2.index

            v_neg1 = verts_neg[i_1]
            v_neg2 = verts_neg[i_2]

            v_pos1 = verts_pos[i_1]
            v_pos2 = verts_pos[i_2]

            bm_dst.faces.new((v_l1, v_l2, v_neg2, v_neg1), f)
            bm_dst.faces.new((v_l2, v_l1, v_pos1, v_pos2), f)

            #
            if use_boundary:

                if v_src_l1.tag and v_src_l2.tag:
                    # paranoid check, probably not needed
                    assert(l.edge.is_boundary)

                    # we know we only touch this edge/face once
                    v_b1 = verts_boundary[i_1]
                    v_b2 = verts_boundary[i_2]
                    bm_dst.faces.new((v_b2, v_b1, v_neg1, v_neg2), f)
                    bm_dst.faces.new((v_b1, v_b2, v_pos2, v_pos1), f)

    return bm_dst


def main(context, kw):
    scene = bpy.context.scene
    obact = scene.objects.active
    me = bpy.data.meshes.new(name=obact.name)
    ob = bpy.data.objects.new(me.name, me)
    scene.objects.link(ob)
    # scene.objects.active = ob

    # can work but messes with undo
    '''
    if ob.mode == 'EDIT':
        bm_src = bmesh.from_edit_mesh(obact.data)
    else:
    '''
    if 1:
        bm_src = bmesh.new()
        bm_src.from_mesh(obact.data)

    bm_dst = solid_wire(bm_src,
                        depth=kw["thickness"],
                        use_boundary=kw["use_boundary"],
                        use_even_offset=kw["use_even_offset"])
    bm_src.free()

    bm_dst.to_mesh(me)

    # copy some settings.
    ob.matrix_world = obact.matrix_world
    ob.layers = obact.layers
    scene.objects.active = ob
    ob.select = True
    obact.select = False


# ----------------------------------------------------------------------------
# boiler plate code from here on

from bpy.types import Operator, Panel
from bpy.props import BoolProperty, FloatProperty


class SolidWireFrameOperator(Operator):
    ''''''
    bl_idname = "mesh.solid_wire_frame"
    bl_label = "Solid Wireframe"
    bl_options = {'REGISTER', 'UNDO'}

    thickness = FloatProperty(
            name="Value",
            description="Assignment value",
            default=0.05,
            min=0.0, max=100.0,
            soft_min=0.0, soft_max=1.0,
            )

    use_boundary = BoolProperty(
            description="Add wire to boundary faces",
            default=True,
            )

    use_even_offset = BoolProperty(
            description="Use even calculations",
            default=True,
            )

    def execute(self, context):
        main(context, self.as_keywords())
        return {'FINISHED'}


class VIEW3D_PT_solid_wire(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label = "Solid Wire"

    def draw(self, context):
        self.layout.operator(SolidWireFrameOperator.bl_idname)


'''
def menu_func(self, context):
    self.layout.operator(SolidWireFrameOperator.bl_idname)
'''


def register():
    bpy.utils.register_module(__name__)

    # bpy.types.VIEW3D_MT_edit_mesh_faces.append(menu_func)


def unregister():
    bpy.utils.unregister_module(__name__)

    # bpy.types.VIEW3D_MT_edit_mesh_faces.remove(menu_func)

if __name__ == "__main__":
    register()
