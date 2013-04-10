# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See th
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# object_render_wire.py liero, meta-androcto,
# Yorik van Havre, Alejandro Sierra, Howard Trickey
# ***** END GPL LICENCE BLOCK *****

bl_info = {
    "name": "Render Wireframe",
    "author": "Community",
    "description": " WireRender & WireSoild modes",
    "version": (2, 3),
    "blender": (2, 63, 0),
    "location": "Object > Render Wireframe",
    "warning": '',
    'wiki_url': 'http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts',
    'tracker_url': 'https://projects.blender.org/tracker/index.php?'\
                   'func=detail&aid=26997',
    'category': 'Object'}

import bpy, mathutils

cube_faces = [ [0,3,2,1], [5,6,7,4], [0,1,5,4],
               [7,6,2,3], [2,6,5,1], [0,4,7,3] ]
cube_normals = [ mathutils.Vector((0,0,-1)),
                 mathutils.Vector((0,0,1)),
                 mathutils.Vector((0,-1,0)),
                 mathutils.Vector((0,1,0)),
                 mathutils.Vector((1,0,0)),
                 mathutils.Vector((-1,0,0)) ]

def create_cube(me, v, d):
    x = v.co.x
    y = v.co.y
    z = v.co.z
    coords=[ [x-d,y-d,z-d], [x+d,y-d,z-d], [x+d,y+d,z-d], [x-d,y+d,z-d],
         [x-d,y-d,z+d], [x+d,y-d,z+d], [x+d,y+d,z+d], [x-d,y+d,z+d] ]
    for coord in coords:
        me.vertices.add(1)
        me.vertices[-1].co = mathutils.Vector(coord)

def norm_dot(e, k, fnorm, me):
    v = me.vertices[e[1]].co - me.vertices[e[0]].co
    if k == 1:
        v = -v
    v.normalize()
    return v * fnorm

def fill_cube_face(me, index, f):
    return [index + cube_faces[f][i] for i in range(4)]

# Coords of jth point of face f in cube instance i
def cube_face_v(me, f, i, j):
    return me.vertices[i + cube_faces[f][j]].co

def cube_face_center(me, f, i):
    return 0.5 * (cube_face_v(me, f, i, 0) + \
                  cube_face_v(me, f, i, 2))

# Return distance between points on two faces when
# each point is projected onto the plane that goes through
# the face center and is perpendicular to the line
# through the face centers.
def projected_dist(me, i1, i2, f1, f2, j1, j2):
    f1center = cube_face_center(me, f1, i1)
    f2center = cube_face_center(me, f2, i2)
    axis_norm = (f2center - f1center).normalized()
    v1 = cube_face_v(me, f1, i1, j1)
    v2 = cube_face_v(me, f2, i2, j2)
    v1proj = v1 - (axis_norm * (v1 - f1center)) * axis_norm
    v2proj = v2 - (axis_norm * (v2 - f2center)) * axis_norm
    return (v2proj - v1proj).length

def skin_edges(me, i1, i2, f1, f2):
    # Connect verts starting at i1 forming cube face f1
    # to those starting at i2 forming cube face f2.
    # Need to find best alignment to avoid a twist.
    shortest_length = 1e6
    f2_start_index = 0
    for i in range(4):
        x = projected_dist(me, i1, i2, f1, f2, 0, i)
        if x < shortest_length:
            shortest_length = x
            f2_start_index = i
    ans = []
    j = f2_start_index
    for i in range(4):
        fdata = [i1 + cube_faces[f1][i],
                 i2 + cube_faces[f2][j],
                 i2 + cube_faces[f2][(j + 1) % 4],
                 i1 + cube_faces[f1][(i - 1) % 4]]
        if fdata[3] == 0:
            fdata = [fdata[3]] + fdata[0:3]
        ans.extend(fdata)
        j = (j - 1) % 4
    return ans
            

# Return map: v -> list of length len(node_normals) where
# each element of the list is either None (no assignment)
# or ((v0, v1), 0 or 1) giving an edge and direction that face is assigned to.
def find_assignment(me, edges, vert_edges, node_normals):
    nf = len(node_normals)
    feasible = {}
    for e in edges:
        for k in (0, 1):
            fds = [(f, norm_dot(e, k, node_normals[f], me)) for f in range(nf)]
            feasible[(e, k)] = [fd for fd in fds if fd[1] > 0.01]
    assignment = {}
    for v, ves in vert_edges.items():
        assignment[v] = best_assignment(ves, feasible, nf)
    return assignment

def best_assignment(ves, feasible, nf):
    apartial = [ None ] * nf
    return best_assign_help(ves, feasible, apartial, 0.0)[0]

def best_assign_help(ves, feasible, apartial, sumpartial):
    if len(ves) == 0:
        return (apartial, sumpartial)
    else:
        ek0 = ves[0]
        vesrest = ves[1:]
        feas = feasible[ek0]
        bestsum = 0
        besta = None
        for (f, d) in feas:
            if apartial[f] is None:
                ap = apartial[:]
                ap[f] = ek0
                # sum up d**2 to penalize smaller d's more
                sp = sumpartial + d*d
                (a, s) = best_assign_help(vesrest, feasible, ap, sp)
                if s > bestsum:
                    bestsum = s
                    besta = a
        if besta:
            return (besta, bestsum)
        else:
            # not feasible to assign e0, k0; try to assign rest
            return best_assign_help(vesrest, feasible, apartial, sumpartial)

def assigned_face(e, assignment):
    (v0, v1), dir = e
    a = assignment[v1]
    for j, ee in enumerate(a):
        if e == ee:
            return j
    return -1

def create_wired_mesh(me2, me, thick):
    edges = []
    vert_edges = {}
    for be in me.edges:
        if be.select and not be.hide:
            e = (be.key[0], be.key[1])
            edges.append(e)
            for k in (0, 1):
                if e[k] not in vert_edges:
                    vert_edges[e[k]] = []
                vert_edges[e[k]].append((e, k))

    assignment = find_assignment(me, edges, vert_edges, cube_normals)

    # Create the geometry
    n_idx = {}   
    for v in assignment:
        vpos = me.vertices[v]
        index = len(me2.vertices)
        # We need to associate each node with the new geometry
        n_idx[v] = index   
        # Geometry for the nodes, each one a cube
        create_cube(me2, vpos, thick)

    # Skin using the new geometry 
    cfaces = []  
    for k, f in assignment.items():
        # Skin the nodes
        for i in range(len(cube_faces)):
            if f[i] is None:
                cfaces.extend(fill_cube_face(me2, n_idx[k], i))
            else:
                (v0, v1), dir = f[i]
                # only skin between edges in forward direction
                # to avoid making doubles
                if dir == 1:
                    # but first make sure other end actually assigned
                    i2 = assigned_face(((v0, v1), 0), assignment)
                    if i2 == -1:
                        cfaces.extend(fill_cube_face(me2, n_idx[k], i))
                    continue
                i2 = assigned_face(((v0, v1), 1), assignment)
                if i2 != -1:
                    cfaces.extend(skin_edges(me2, n_idx[v0], n_idx[v1], i, i2))
                else:
                    # assignment failed for this edge
                    cfaces.extend(fill_cube_face(me2, n_idx[k], i))

    # adding faces to the mesh
    me2.tessfaces.add(len(cfaces) // 4)
    me2.tessfaces.foreach_set("vertices_raw", cfaces)
    me2.update(calc_edges=True)

# Add built in wireframe
def wire_add(mallas):
    if mallas:
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.scene.objects.active = mallas[0]
        for o in mallas: o.select = True
        bpy.ops.object.duplicate()
        obj, sce = bpy.context.object, bpy.context.scene
        for mod in obj.modifiers: obj.modifiers.remove(mod)
        bpy.ops.object.join()
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.wireframe(thickness=0.005)
        bpy.ops.object.mode_set()
        for mat in obj.material_slots: bpy.ops.object.material_slot_remove()
        if 'wire_object' in sce.objects.keys():
            sce.objects.get('wire_object').data = obj.data
            sce.objects.get('wire_object').matrix_world = mallas[0].matrix_world
            sce.objects.unlink(obj)
        else:
            obj.name = 'wire_object'
        obj.data.materials.append(bpy.data.materials.get('mat_wireobj'))

    return{'FINISHED'}
'''
class VIEW3D_PT_tools_SolidifyWireframe(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "mesh_edit"
    bl_label = "Solidify Wireframe"

    def draw(self, context):
        active_obj = context.active_object
        layout = self.layout
        col = layout.column(align=True)
        col.operator("mesh.solidify_wireframe", text="Solidify")
        col.prop(context.scene, "swThickness")
        col.prop(context.scene, "swSelectNew")
'''
# a class for your operator
class SolidifyWireframe(bpy.types.Operator):
    """Turns the selected edges of a mesh into solid objects"""
    bl_idname = "mesh.solidify_wireframe"
    bl_label = "Solidify Wireframe"
    bl_options = {'REGISTER', 'UNDO'}
    
    def invoke(self, context, event):
        return self.execute(context)

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return ob and ob.type == 'MESH'

    def execute(self, context):
        # Get the active object
        ob_act = context.active_object
        # getting current edit mode
        currMode = ob_act.mode
        # switching to object mode
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        # getting mesh data
        mymesh = ob_act.data
        #getting new mesh
        newmesh = bpy.data.meshes.new(mymesh.name + " wire")
        obj = bpy.data.objects.new(newmesh.name,newmesh)
        obj.location = ob_act.location
        obj.rotation_euler = ob_act.rotation_euler
        obj.scale = ob_act.scale
        context.scene.objects.link(obj)
        create_wired_mesh(newmesh, mymesh, context.scene.swThickness)

        # restoring original editmode if needed
        if context.scene.swSelectNew:
            obj.select = True
            context.scene.objects.active = obj
        else:
            bpy.ops.object.mode_set(mode=currMode)

        # returning after everything is done
        return {'FINISHED'}
		
class WireMaterials(bpy.types.Operator):
    bl_idname = 'scene.wire_render'
    bl_label = 'Apply Materials'
    bl_description = 'Set Up Materials for a Wire Render'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        wm = bpy.context.window_manager
        sce = bpy.context.scene

        if 'mat_clay' not in bpy.data.materials:
            mat = bpy.data.materials.new('mat_clay')
            mat.specular_intensity = 0
        else: mat = bpy.data.materials.get('mat_clay')
        mat.diffuse_color = wm.col_clay
        mat.use_shadeless = wm.shadeless_mat

        if 'mat_wire' not in bpy.data.materials:
            mat = bpy.data.materials.new('mat_wire')
            mat.specular_intensity = 0
            mat.use_transparency = True
            mat.type = 'WIRE'
            mat.offset_z = 0.05
        else: mat = bpy.data.materials.get('mat_wire')
        mat.diffuse_color = wm.col_wire
        mat.use_shadeless = wm.shadeless_mat

        try: bpy.ops.object.mode_set()
        except: pass

        if wm.selected_meshes: objetos = bpy.context.selected_objects
        else: objetos = sce.objects

        mallas = [o for o in objetos if o.type == 'MESH' and o.is_visible(sce) and o.name != 'wire_object']

        for obj in mallas:
            sce.objects.active = obj
            print ('procesando >', obj.name)
            obj.show_wire = wm.wire_view
            for mat in obj.material_slots:
                bpy.ops.object.material_slot_remove()
            obj.data.materials.append(bpy.data.materials.get('mat_wire'))
            obj.data.materials.append(bpy.data.materials.get('mat_clay'))
            obj.material_slots.data.active_material_index = 1
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.object.material_slot_assign()
            bpy.ops.object.mode_set()

        if wm.wire_object:
            if 'mat_wireobj' not in bpy.data.materials:
                mat = bpy.data.materials.new('mat_wireobj')
                mat.specular_intensity = 0
            else: mat = bpy.data.materials.get('mat_wireobj')
            mat.diffuse_color = wm.col_wire
            mat.use_shadeless = wm.shadeless_mat
            wire_add(mallas)

        return{'FINISHED'}

class PanelWMat(bpy.types.Panel):
    bl_label = 'Setup Wire Render'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        wm = bpy.context.window_manager
        active_obj = context.active_object
        layout = self.layout

        column = layout.column(align=True)
        column.prop(wm, 'col_clay')
        column.prop(wm, 'col_wire')
        column = layout.column(align=True)
        column.prop(wm, 'selected_meshes')
        column.prop(wm, 'shadeless_mat')
        column.prop(wm, 'wire_view')
        column.prop(wm, 'wire_object')
        column.separator()
        column.operator('scene.wire_render')
        column.label(text='- - - - - - - - - - - - - - - - - - - - - -')
        col = layout.column(align=True)
        column.label(text='Solid WireFrame')
        layout.operator("mesh.solidify_wireframe", text="Create Mesh Object")
        col.prop(context.scene, "swThickness")
        col.prop(context.scene, "swSelectNew")
bpy.types.WindowManager.selected_meshes = bpy.props.BoolProperty(name='Selected Meshes', default=False, description='Apply materials to Selected Meshes / All Visible Meshes')
bpy.types.WindowManager.shadeless_mat = bpy.props.BoolProperty(name='Shadeless', default=False, description='Generate Shadeless Materials')
bpy.types.WindowManager.col_clay = bpy.props.FloatVectorProperty(name='', description='Clay Color', default=(1.0, 0.9, 0.8), min=0, max=1, step=1, precision=3, subtype='COLOR_GAMMA', size=3)
bpy.types.WindowManager.col_wire = bpy.props.FloatVectorProperty(name='', description='Wire Color', default=(0.1 ,0.0 ,0.0), min=0, max=1, step=1, precision=3, subtype='COLOR_GAMMA', size=3)
bpy.types.WindowManager.wire_view = bpy.props.BoolProperty(name='Viewport Wires', default=False, description='Overlay wires display over solid in Viewports')
bpy.types.WindowManager.wire_object = bpy.props.BoolProperty(name='Create Mesh Object', default=False, description='Add a Wire Object to scene to be able to render wires in Cycles')
bpy.types.Scene.swThickness = bpy.props.FloatProperty(name="Thickness", description="Thickness of the skinned edges", default=0.01)
bpy.types.Scene.swSelectNew = bpy.props.BoolProperty(name="Select wire", description="If checked, the wire object will be selected after creation", default=True)

# Register the operator
def solidifyWireframe_menu_func(self, context):
        self.layout.operator(SolidifyWireframe.bl_idname, text="Solidify Wireframe", icon='PLUGIN')

# Add "Solidify Wireframe" menu to the "Mesh" menu.
def register():
        bpy.utils.register_class(WireMaterials)
        bpy.utils.register_class(PanelWMat)
        bpy.utils.register_module(__name__)
        bpy.types.Scene.swThickness = bpy.props.FloatProperty(name="Thickness",
                                                              description="Thickness of the skinned edges",
                                                              default=0.01)
        bpy.types.Scene.swSelectNew = bpy.props.BoolProperty(name="Select wire",
                                                             description="If checked, the wire object will be selected after creation",
                                                             default=True)
        bpy.types.VIEW3D_MT_edit_mesh_edges.append(solidifyWireframe_menu_func)

# Remove "Solidify Wireframe" menu entry from the "Mesh" menu.
def unregister():
        bpy.utils.unregister_class(WireMaterials)
        bpy.utils.unregister_class(PanelWMat)
        bpy.utils.unregister_module(__name__)
        del bpy.types.Scene.swThickness
        bpy.types.VIEW3D_MT_edit_mesh_edges.remove(solidifyWireframe_menu_func)

if __name__ == "__main__":
        register()
