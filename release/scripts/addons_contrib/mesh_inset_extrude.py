bl_info = {
    'name': "Inset Extrude",
    'description': "Inset and Extrude selected polygons, useful modeling tool",
    'author': "Jon Sandstrom",
    'version': (0, 6),
    'blender': (2, 5, 9),
    'location': 'Search for Inset Extrude, map a key to the operator "mesh.inset_extrude", or use the default "I-key"',
    'warning': "Broken",
    'category': 'Mesh',
    'wiki_url': 'http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/Modeling/Inset-Extrude'}

import bpy, bmesh
import bgl
import blf
from math import *
from mathutils import Vector
from bpy.props import FloatProperty, BoolProperty

def find_sel_faces(mesh, individual_faces):
    selected_faces = []
    selected_islands = []
    if individual_faces:
        for face in mesh.polygons:
            if face.select and not face.hide:
                selected_islands.append([face.index])
        return(selected_islands)
    
    for face in mesh.polygons:
        if face.select and not face.hide: selected_faces.append(face.index)
    selected_islands = []
    while len(selected_faces) != 0:
        face = selected_faces[0]
        selected_faces.remove(face)
        active_island = [face]
        active_faces = [face]
        
        while len(active_faces) > 0:
            connected_faces = island_extend(mesh, active_faces, selected_faces)
            active_island.extend(connected_faces)
            active_faces = connected_faces
        selected_islands.append(active_island)    
    
    sel_f  = [] 
    for island in selected_islands:
        sel_f.extend(island) 
    
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.select_less()
    bpy.ops.object.vertex_group_assign(new=True)
    bpy.ops.object.mode_set(mode = 'OBJECT')
    
    return (selected_islands)

def island_extend(mesh, active_faces, selected_faces):
    connected_faces = []
    for face in active_faces:
        cf = []
        for f in selected_faces:
            for edge in mesh.polygons[face].edge_keys:
                if edge in mesh.polygons[f].edge_keys and f not in connected_faces:
                    connected_faces.append(f)
                    cf.append(f)
                    break

        for f in cf: selected_faces.remove(f)
    return(connected_faces)

def find_outer_edge(mesh, island):
    edges = []
    for face in island:
        for edge in mesh.polygons[face].edge_keys: edges.append(edge)
    outer_edges = []
    for edge in edges:
        if edges.count(edge) == 1:
            outer_edges.append(edge)
    return (outer_edges)

def extend_vert_dict(mesh, edges, vert_dict):
    for edge in edges:
        for vert in edge:
            if vert not in vert_dict: 
                vert_dict[vert] = edge_vertex(vert)
                vert_dict[vert].edges.append(edge)
            else:
                vert_dict[vert].edges.append(edge)


class edge_vertex:
    def __init__(self, index):
        self.index = index
        self.faces = []
        self.edges = []

def find_norm_vectors(mesh, vert_dict):
    vertices = list(vert_dict.keys())
    for vert in vertices:
        edge_vectors = []
        for edge in vert_dict[vert].edges:
            if vert == edge[0]:
                vec = mesh.vertices[edge[0]].co.copy() - mesh.vertices[edge[1]].co.copy()
            else:
                vec = mesh.vertices[edge[1]].co.copy() - mesh.vertices[edge[0]].co.copy()
            edge_vectors.append(vec/vec.length)
        vec1 = Vector.cross(edge_vectors[0], edge_vectors[1])
        edges_vec = edge_vectors[1] + edge_vectors[0]
        norm_vec = Vector.cross(vec1, edges_vec)
        if norm_vec.length < 1e-12:           #hackish fix for flat surfaces and straight edges
            norm_vec = edge_vectors[0] 
        
        vert_dict[vert].new_index = len(mesh.vertices) + vertices.index(vert)
        vert_dict[vert].norm_vec = norm_vec
        vert_dict[vert].edge_vec = edge_vectors[0]


def find_edge_faces(mesh, sel_faces, vert_dict):
    edge_faces = []
    for face in sel_faces:
        for vert in mesh.polygons[face].vertices:
            if vert in vert_dict:
                vert_dict[vert].faces.append(mesh.polygons[face].index)
                if face not in edge_faces: edge_faces.append(mesh.polygons[face].index)
    return edge_faces

def find_offset_vec(mesh, vert_dict):
    for vert in list(vert_dict.keys()):
        for face in vert_dict[vert].faces:
            rel_vec = []         # vertex vectors relative to active vertex
            a = 0       # nr of verts on side 'a' of plane
            b = 0       # on side b
            for v in mesh.polygons[face].vertices:
                if v == vert: continue
                rel_co = mesh.vertices[vert].co.copy() - mesh.vertices[v].co.copy()
                rel_vec = rel_co/rel_co.length
                
                case1 = rel_co - vert_dict[vert].norm_vec 
                case2 = rel_co + vert_dict[vert].norm_vec
                
                if case1.length < case2.length:
                    a += 1
                else:
                    b += 1
            if a > 0 and b > 0:
                middle_face = face
                break
        
        # find offset_vector
        offset_vec_raw = Vector.cross(mesh.polygons[middle_face].normal, vert_dict[vert].norm_vec)
        offset_vec_norm = offset_vec_raw / offset_vec_raw.length
        angle = acos(offset_vec_norm * vert_dict[vert].edge_vec)
        if sin(angle) == 0:
            angle = pi/2
        offset_vec = offset_vec_norm / sin(angle)
        
        if len(vert_dict[vert].faces) == 1:
            face_center = Vector([0, 0, 0])
            for v in mesh.polygons[middle_face].vertices:
                face_center += mesh.vertices[v].co.copy()
            face_center /= len(mesh.polygons[middle_face].vertices)
            
            case1 = (face_center - mesh.vertices[vert].co.copy()) + offset_vec
            case2 = (face_center - mesh.vertices[vert].co.copy()) - offset_vec
            if case1.length < case2.length:
                offset_vec.negate()        
        
        else:
            for edge in mesh.polygons[middle_face].edge_keys:
                test = False
                for face in vert_dict[vert].faces:
                    if face == middle_face: continue
                    if edge in mesh.polygons[face].edge_keys: 
                        test = True
                        break
                if test:
                    if edge[0] == vert:
                        edge_vec = mesh.vertices[edge[1]].co - mesh.vertices[edge[0]].co
                    else:
                        edge_vec = mesh.vertices[edge[0]].co - mesh.vertices[edge[1]].co
                    continue
            case1 = edge_vec + offset_vec
            case2 = edge_vec - offset_vec
            if case1.length < case2.length:
                offset_vec.negate()

        vert_dict[vert].offset_vec = offset_vec

def new_faces(mesh, island_dicts, edge_faces, outer_edges):
    
    faces_new = []
    for island in edge_faces:
        vert_dict = island_dicts[edge_faces.index(island)]
        for face in island:
            f_verts = []
            for vert in mesh.polygons[face].vertices:
                if vert in vert_dict:
                    f_verts.append(vert_dict[vert].new_index)
                else:
                    f_verts.append(vert)
            if len(f_verts) == 3:
                f_verts.append(f_verts[-1])
            faces_new.append(f_verts)
    
    not_selected = 0
    for edge_island in outer_edges:
        vert_dict = island_dicts[outer_edges.index(edge_island)]
        for edge in edge_island:
            f_verts = [edge[0], edge[1], vert_dict[edge[1]].new_index, vert_dict[edge[0]].new_index]
            faces_new.append(f_verts)
            not_selected += 1
        
    
    ef_size = 0
    for i in edge_faces: ef_size += len(i)
    n_faces_old = len(mesh.polygons)
    rim_select = range(n_faces_old - ef_size, (n_faces_old+len(faces_new)) - not_selected - ef_size)
    rim_noSelect = range((n_faces_old - ef_size) + (len(faces_new) - not_selected), n_faces_old - ef_size + len(faces_new))
    mesh.polygons.add(len(faces_new))
    for i in range(len(faces_new)):
        mesh.polygons[n_faces_old + i].vertices = faces_new[i]
    mesh.update(calc_edges = True)
    
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode = 'OBJECT')
    for island in edge_faces:
        for face in island:
            mesh.polygons[face].select = True
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.delete(type='FACE')
    bpy.ops.object.mode_set(mode = 'OBJECT')
    return (rim_select, rim_noSelect, n_faces_old)  # return number of old faces to determine the first new face and compare normals to it
    
    
def find_shortest_edge(mesh, edge_faces, vert_dict, outer_edges):
    # finds the shortest edge that is connected to the outer rim
    # will be used for scaling the sensitivity of the interface
    shortest_edge = -1
    if len(edge_faces) == 1:
        for edge in mesh.polygons[edge_faces[0]].edge_keys:
            edgeco = mesh.vertices[edge[0]].co - mesh.vertices[edge[1]].co
            if shortest_edge < 0 or edgeco.length < shortest_edge:
                shortest_edge = edgeco.length
    for face in edge_faces:        
        for edge in mesh.polygons[face].edge_keys:
            if (edge not in outer_edges) and (edge[0] in vert_dict or edge[1] in vert_dict):
                edgeco = mesh.vertices[edge[0]].co - mesh.vertices[edge[1]].co
                if shortest_edge < 0 or edgeco.length < shortest_edge:
                    shortest_edge = edgeco.length
    return(shortest_edge)

def find_displace_vecs(mesh, sel_faces, vert_dict):
    area = 0
    inside_verts = {}
    for face in sel_faces:
        for vert in mesh.polygons[face].vertices:
            if vert in inside_verts:
                inside_verts[vert].append(mesh.polygons[face].normal)
            else:
                inside_verts[vert] = [mesh.polygons[face].normal]
        area += mesh.polygons[face].area
    displace_vecs = {}
    for vert in list(inside_verts.keys()):
        vec_norm = Vector([0,0,0])
        for normal in inside_verts[vert]:
            vec_norm += normal
        vec_norm /= len(inside_verts[vert])
        dot = vec_norm * inside_verts[vert][0]
        if dot > 1: dot = 1
        angle = acos(dot)
        vec = vec_norm / sin(pi/2 - angle)
        if vert in vert_dict:
            displace_vecs[vert] = vec
        else:
            displace_vecs[vert] = [mesh.vertices[vert].co.copy(), vec]

    return(displace_vecs, area)

def select_faces(mesh, rim_select, rim_noSelect, edge_faces, n_faces_old, ref_normal, use_smooth):
    all = []
    all.extend(rim_select)
    all.extend(rim_noSelect)
    for face in all:
        face = bpy.context.object.data.polygons.active = True
        mesh.polygons[face].use_smooth = use_smooth
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.normals_make_consistent()
    bpy.ops.object.mode_set(mode = 'OBJECT')
    
    bpy.ops.object.mode_set(mode = 'EDIT')
    ef_size = 0
    for i in edge_faces: ef_size += len(i)
    if mesh.polygons[n_faces_old - ef_size].normal * ref_normal < 0.9:
        bpy.ops.mesh.flip_normals()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_remove()
    bpy.ops.object.mode_set(mode = 'OBJECT')
    for face in rim_select:
        bpy.context.object.data.polygons.active = True

def run_inset_extrude(mesh, individual_faces):
    sel_faces = find_sel_faces(mesh, individual_faces)
    outer_edges = []
    island_dicts = []
    shortest_edge = None
    area = -1
    disp_islands = []
    n_faces_old = 0
    edge_faces_islands = []
    for island in sel_faces:
        out_edges = find_outer_edge(mesh, island)
        outer_edges.append(out_edges)
        vert_dict = {}
        
        extend_vert_dict(mesh, out_edges, vert_dict)
        find_norm_vectors(mesh, vert_dict)
        
        edge_faces = find_edge_faces(mesh, island, vert_dict)
        edge_faces_islands.append(edge_faces)
        ref_normal = mesh.polygons[edge_faces[0]].normal.copy()
        use_smooth = mesh.polygons[edge_faces[0]].use_smooth
        find_offset_vec(mesh, vert_dict)
        
        short_edge = find_shortest_edge(mesh, edge_faces, vert_dict, out_edges)
        if shortest_edge == None or shortest_edge > short_edge:
            shortest_edge = short_edge
        
        disp_vecs, ar = find_displace_vecs(mesh, island, vert_dict)
        if area < 0 or ar < area:
            area = ar 
        disp_islands.append(disp_vecs)
        
        island_dicts.append(vert_dict)
        
        mesh.vertices.add(len(vert_dict.keys()))
        offset_verts(mesh, vert_dict, 0.03)

    
    rim_select, rim_noSelect, n_f_old = new_faces(mesh, island_dicts, edge_faces_islands, outer_edges)
    
    select_faces(mesh, rim_select, rim_noSelect, edge_faces_islands, n_faces_old, ref_normal, use_smooth)
    return([island_dicts, disp_islands, shortest_edge, area])

def offset_verts(mesh, vert_dict, offset):
    verts = list(vert_dict.keys())
    for vert in verts:
        new_co = mesh.vertices[vert].co.copy() + vert_dict[vert].offset_vec * offset
        mesh.vertices[vert_dict[vert].new_index].co = new_co

def displace_verts(mesh, vert_dict, displace_vecs, displace):
    for vert in list(displace_vecs.keys()):
        if vert in vert_dict:
            mesh.vertices[vert_dict[vert].new_index].co += displace_vecs[vert] * displace
        else:
            mesh.vertices[vert].co = displace_vecs[vert][0] + displace_vecs[vert][1] * displace



def draw_UI(self, context):
    # creates all lines and appends them to a list, then draws these to the UI
    font_id = 0
    lines = []
    
    if self.switch:
        blf.position(font_id, self.initial_mouse_region[0]+5, self.current_mouse_region[1]+8, 0)
        blf.size(font_id, 20, 38)
        blf.draw(font_id, str(round(self.offset, 3)))
        
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glColor4f(1.0, 1.0, 1.0, 0.2)
        bgl.glLineWidth(2)
        
        length = 0
        while length < abs(self.current_mouse_region[0] - self.initial_mouse_region[0])-10:
            
            if self.current_mouse_region[0] - self.initial_mouse_region[0] >= 0:
                lines.append([(self.initial_mouse_region[0]+length+4, self.current_mouse_region[1]),
                              (self.initial_mouse_region[0]+length+10, self.current_mouse_region[1])])
                
            else:
                lines.append([(self.initial_mouse_region[0]-length-4, self.current_mouse_region[1]),
                              (self.initial_mouse_region[0]-length-10, self.current_mouse_region[1])])
            length +=10
            
        lines.append([(self.initial_mouse_region[0]+1, self.current_mouse_region[1]+15),
                  (self.initial_mouse_region[0]+1, self.current_mouse_region[1]-8)])
        
    else:
        blf.position(font_id, self.current_mouse_region[0]+5, self.initial_mouse_region[1]+8, 0)
        blf.size(font_id, 20, 38)
        blf.draw(font_id, str(round(self.displace, 3)))
        
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glColor4f(1.0, 1.0, 1.0, 0.2)
        bgl.glLineWidth(2)
        
        length = 0
        while length < abs(self.current_mouse_region[1] - self.initial_mouse_region[1])-10:
            
            if self.current_mouse_region[1] - self.initial_mouse_region[1] >= 0:
                lines.append([(self.current_mouse_region[0], self.initial_mouse_region[1]+length+4),
                              (self.current_mouse_region[0], self.initial_mouse_region[1]+length+10)])
                
            else:
                lines.append([(self.current_mouse_region[0], self.initial_mouse_region[1]-length-4),
                              (self.current_mouse_region[0], self.initial_mouse_region[1]-length-10)])
            length +=10
        
        lines.append([(self.current_mouse_region[0]+15, self.initial_mouse_region[1]+1),
                  (self.current_mouse_region[0]-8, self.initial_mouse_region[1]+1)])
    
    
    # draw lines
    for i in lines:
        bgl.glBegin(bgl.GL_LINE_STRIP)
        for x, y in i:
            bgl.glVertex2i(x, y)
        bgl.glEnd()
 
    # restore opengl defaults
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
    

def initialize():
    
    global_undo = bpy.context.user_preferences.edit.use_global_undo
    bpy.context.user_preferences.edit.use_global_undo = False
    bpy.context.tool_settings.mesh_select_mode = [False, False, True]
    bpy.ops.object.mode_set(mode = 'OBJECT')
    mesh = bpy.context.active_object.data
    vert_dict, displace_vecs, shortest_edge, area = run_inset_extrude(mesh, False)
    bpy.ops.object.mode_set(mode = 'EDIT')
    return ([global_undo, mesh, vert_dict, displace_vecs, shortest_edge, area])

def terminate(global_undo):
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.user_preferences.edit.use_global_undo = global_undo

class MESH_OT_inset_extrude(bpy.types.Operator):
    bl_idname = "mesh.inset_extrude"
    bl_label = "Inset Extrude"
    bl_options = {'REGISTER', 'UNDO'}
    
    displace = FloatProperty(name='Extrude', 
                description='displacement from original surface',
                default=0.0, min=-100, max=100)
    offset = FloatProperty(name='Inset', 
                description='inset from selcetion border',
                default=0.0, min=-100, max=100)
    individual_faces = BoolProperty(name='Individual Faces', 
                default=False)
    switch = True
    multiplier = 1
    shift_value = 0
    ctrl = False
    run_modal = False
    key_input = ''
    
    def draw(self, context):
        layout = self.layout
        col_top = layout.column(align = True)
        row = col_top.row(align = True)
        col_left = row.column(align = True)
        col_left.prop(self, 'offset')
        col_left.prop(self, 'displace')
#        col_left.prop(self, 'individual_faces')
    
    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')
        if not self.run_modal:
            run_inset_extrude(self.mesh, self.individual_faces)
        for vert_dict in self.island_dicts:
            offset_verts(self.mesh, vert_dict, self.offset)
            displace_verts(self.mesh, vert_dict, self.disp_islands[self.island_dicts.index(vert_dict)], self.displace)
        bpy.ops.object.mode_set(mode='EDIT')
        return{'FINISHED'}
    
    def modal(self, context, event):
        v3d = context.space_data
        context.area.tag_redraw()
        
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self.switch = not self.switch
            self.shift_value = 0
            self.initial_mouse = Vector((event.mouse_x, event.mouse_y, 0.0))
            self.initial_mouse_region = [event.mouse_region_x, event.mouse_region_y]
            
#        elif event.type == 'I' and event.value == 'PRESS':
#            self.individual_faces = not self.individual_faces
#            self.island_dicts, self.disp_islands, self.shortest_edge, self.area = run_inset_extrude(self.mesh, self.individual_faces)
        
        elif event.type == 'MOUSEMOVE':
            current_mouse = Vector((event.mouse_x, event.mouse_y, 0.0))
            offset_vector = (self.initial_mouse - current_mouse)
            self.current_mouse_region = [event.mouse_region_x, event.mouse_region_y]
                
            if self.switch:
                self.offset = - offset_vector[0] * self.shortest_edge * 0.0015 * self.multiplier + self.shift_value
            else:
                self.displace = - offset_vector[1] * 0.002 * self.multiplier * sqrt(self.area) + self.shift_value
            
            if self.ctrl:
                if self.multiplier!=1:
                    self.offset = round(self.offset, 2)
                    self.displace = round(self.displace, 2)
                else:
                    self.offset = round(self.offset, 1)
                    self.displace = round(self.displace, 1)
            
            self.execute(context)
            return {'RUNNING_MODAL'}
            
        elif event.type =='LEFT_SHIFT' or event.type == 'RIGHT_SHIFT':
            if event.value == 'PRESS':
                self.multiplier = 0.1
                if self.switch:
                    self.shift_value = self.offset * 0.9
                else:
                    self.shift_value = self.displace * 0.9
            if event.value == 'RELEASE':
                self.multiplier = 1
                self.shift_value = 0
            return {'RUNNING_MODAL'}
        
        elif event.type =='LEFT_CTRL' or event.type == 'RIGHT_CTRL':
            if event.value == 'PRESS': self.ctrl = True
            if event.value == 'RELEASE': self.ctrl = False
            return {'RUNNING_MODAL'}
        
        elif event.type in list(self.key_dict.keys()) and event.value == 'PRESS':
            if event.type == 'NUMPAD_ENTER':
                context.area.header_text_set()
                if self.switch:
                    self.key_input = ''
                    self.shift_value = 0
                    self.initial_mouse = Vector((event.mouse_x, event.mouse_y, 0.0))
                    self.initial_mouse_region = [event.mouse_region_x, event.mouse_region_y]
                    self.switch = not self.switch
                    return {'RUNNING_MODAL'}
                else:
                    terminate(self.global_undo)
                    context.region.callback_remove(self._handle) 
                    self.run_modal = False
                    return {'FINISHED'}
            else:
                if event.type == 'BACK_SPACE':
                    self.key_input = self.key_input[:-1]
                    if len(self.key_input) == 0:
                        self.key_input = ''
                        context.area.header_text_set(self.key_input)
                        return{'RUNNING_MODAL'}
                else:
                    self.key_input += self.key_dict[event.type]
                    if self.key_dict[event.type] in ['+', '-', '*', '/']:
                        context.area.header_text_set(self.key_input)    
                        return {'RUNNING_MODAL'}
                context.area.header_text_set(self.key_input)
                try:
                    if self.switch:
                        self.offset = eval(self.key_input)
                    else:
                        self.displace = eval(self.key_input)
                except SyntaxError:
                    return {'RUNNING_MODAL'}
                self.execute(context)
                return {'RUNNING_MODAL'}
        
        
        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            context.area.header_text_set()
            terminate(self.global_undo)
            context.region.callback_remove(self._handle) 
            self.run_modal = False
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            context.area.header_text_set()
            context.region.callback_remove(self._handle)
            self.run_modal = False
            return {'CANCELLED'}
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        initial_selection_mode = [bool for bool in bpy.context.tool_settings.mesh_select_mode]
        self.global_undo, self.mesh, self.island_dicts, self.disp_islands, self.shortest_edge, self.area = initialize()
        bpy.context.tool_settings.mesh_select_mode = initial_selection_mode
        self.displace = 0
        self.run_modal = True
        
        self.key_dict = {
                        'NUMPAD_0':'0', 'NUMPAD_1':'1', 'NUMPAD_2':'2', 
                        'NUMPAD_3':'3', 'NUMPAD_4':'4', 'NUMPAD_5':'5', 
                        'NUMPAD_6':'6', 'NUMPAD_7':'7', 'NUMPAD_8':'8', 
                        'NUMPAD_9':'9', 'NUMPAD_PERIOD':'.', 'NUMPAD_SLASH':'/', 
                        'NUMPAD_ASTERIX':'*', 'NUMPAD_MINUS':'-', 'NUMPAD_ENTER':None, 
                        'NUMPAD_PLUS':'+', 'ONE':'1', 'TWO':'2', 'THREE':'3', 
                        'FOUR':'4', 'FIVE':'5', 'SIX':'6', 'SEVEN':'7', 
                        'EIGHT':'8', 'NINE':'9', 'ZERO':'0', 'PERIOD':'.', 'BACK_SPACE':None
                        }
        
        if context.space_data.type == 'VIEW_3D':
            v3d = context.space_data

            context.window_manager.modal_handler_add(self)
            self.current_mouse_region = [event.mouse_region_x, event.mouse_region_y]
            self.initial_mouse = Vector((event.mouse_x, event.mouse_y, 0.0))
            self.initial_mouse_region = [event.mouse_region_x, event.mouse_region_y]
            self._handle = context.region.callback_add(draw_UI, (self, context), 'POST_PIXEL')
            
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Active space must be a View3d")
            return {'CANCELLED'}

def register():
    bpy.utils.register_module(__name__)

    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
    kmi = km.keymap_items.new('mesh.inset_extrude', 'I', 'PRESS')
 #   kmi.properties.name = "MESH_OT_inset_extrude"
	

def unregister():
    bpy.utils.unregister_module(__name__)

    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps['3D View']
    for kmi in km.keymap_items:
        if kmi.idname == 'mesh.inset_extrude':
#            if kmi.properties.name == "MESH_OT_inset_extrude":
            km.keymap_items.remove(kmi)
            break
if __name__ == "__main__":
    register()
