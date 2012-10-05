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
    "name": "Vertex slide for Bmesh",
    "author": "Valter Battioli (ValterVB) and PKHG",
    "version": (2, 0, 0),
    "blender": (2, 6, 2),
    "location": "View3D > Mesh > Vertices (CTRL V-key)",
    "description": "Slide a vertex along an edge or a line",
    "warning": "Work only with Blender 2.62 or higher",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"\
        "Scripts/Modeling/Vertex_Slide2",
    "tracker_url": "http://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=27561",
    "category": "Mesh"}

#***********************************************************************
#ver. 1.0.0: -First version
#ver. 1.0.1: -Now the mouse wheel select in continuos mode the next vertex
#            -Add a marker for the vertex to move
#ver. 1.0.2: -Add check for vertices not selected
#            -Some cleanup
#ver. 1.0.3: -Now the movement is proportional to the mouse movement
#             1/10 of the distance between 2 points for every pixel
#             mouse movement (1/100 with SHIFT)
#ver. 1.0.4: all coordinate as far as possible replaced by vectors
#            view3d_utils are used to define length of an edge on screen!
#            partial simplified logic by PKHG
#ver. 1.0.6: Restore continuous slide, code cleanup
#            Correct the crash with not linked vertex
#ver. 1.0.7: Restore shift, and some code cleanup
#ver. 1.0.8: Restore 2 type of sliding with 2 vertex selected
#ver. 1.0.9: Fix for reverse vector multiplication
#ver. 1.1.0: Delete debug info, some cleanup and add some comments
#ver. 1.1.1: Now UNDO work properly
#ver. 1.1.2: Refactory and some clean of the code.
#            Add edge drawing (from chromoly vertex slide)
#            Add help on screen (from chromooly vertex slide)
#ver. 1.1.3: Now work also with Continuos Grab, some clean on code
#ver. 1.1.4: Remove a lot of mode switching in Invoke. It was too slow 
#            with big mesh.
#ver. 1.1.5: Changed Lay out of the Help and the Key for reverse the 
#            movement. Left/Right arrow rather than Pus/Minus numpad
#ver. 1.1.6: Now the vertex movement is always coherent with Mouse movement
#ver. 2.0.0: Update to Bmesh and remove all mode switching
#ver. 2.0.1: Replaced Conv3DtoScreen2D function with location_3d_to_region_2d
#ver. 2.0.2: Fix crash if there are some duplicate vertices
#***********************************************************************

import bpy
import bmesh
import bgl
import blf
from mathutils import Vector
from bpy_extras.view3d_utils import location_3d_to_region_2d as loc3d2d

# Equation of the line
# Changing t we have a new point coordinate on the line along v0 v1
# With t from 0 to 1  I move from v0 to v1
def NewCoordinate(v0, v1, t):
    return v0 + t * (v1 - v0)
    
#  This class store Vertex data
class Point():
    def __init__(self):
        self.original = self.Vertex()  # Original position
        self.new = self.Vertex()  # New position
        self.t = 0  # Used for move the vertex
        self.x2D = 0  # Screen 2D cooord of the point
        self.y2D = 0  # Screen 2D cooord of the point
        self.selected = False

    class Vertex():
        def __init__(self):
            self.co = None
            self.idx = None
            
class BVertexSlideOperator(bpy.types.Operator):
    bl_idname = "vertex.slide"
    bl_label = "Vertex Slide"
    bl_options = {'REGISTER', 'UNDO', 'GRAB_POINTER', 'BLOCKING', 'INTERNAL'}

    Vertex1 = Point()  # First selected vertex data
    LinkedVertices1 = []  # List of index of linked verts of Vertex1
    Vertex2 = Point()  # Second selected vertex data
    LinkedVertices2 = []  # List of index of linked verts of Vertex2
    ActiveVertex = None  # Index of vertex to be moved
    tmpMouse_x = 0
    tmpMouse = Vector((0, 0))
    Direction = 1.0  # Used for direction and precision of the movement
    FirstVertexMove = True  # If true move the first vertex
    VertLinkedIdx = 0  # Index of LinkedVertices1. Used only for 1 vertex select case
    LeftAltPress = False  # Flag to know if ALT is hold on
    LeftShiftPress = False  # Flag to know if SHIFT is hold on
    obj = None  # Object
    mesh = None  # Mesh
    bm = None  # BMesh

    # OpenGL Function to draw on the screen help and pointer *
    def draw_callback_px(self, context):
        x, y = loc3d2d(context.region, context.space_data.region_3d, self.bm.verts[self.ActiveVertex].co)

        # Draw an * at the active vertex
        blf.position(0, x, y, 0)
        blf.size(0, 26, 72)
        blf.draw(0, "*")

        #Draw Help
        yPos=30
        blf.size(0, 11, context.user_preferences.system.dpi)
        txtHelp1 = "{SHIFT}:Precision"
        txtHelp2 = "{WHEEL}:Change the vertex/edge"
        txtHelp3 = "{ALT}:Continuos slide"
        txtHelp4 = "{LEFT ARROW}:Reverse the movement"
        txtHelp5 = "{RIGHT ARROW}:Restore the movement"
        blf.position(0, 70, yPos, 0)
        blf.draw(0, txtHelp5)
        yPos += (int(blf.dimensions(0, txtHelp4)[1]*2))
        blf.position(0 , 70, yPos, 0)
        blf.draw(0, txtHelp4)
        yPos += (int(blf.dimensions(0, txtHelp3)[1]*2))
        blf.position(0 , 70, yPos, 0)
        blf.draw(0, txtHelp3)
        yPos += (int(blf.dimensions(0, txtHelp2)[1]*2))
        blf.position(0 , 70, yPos, 0)
        blf.draw(0, txtHelp2)
        yPos += (int(blf.dimensions(0, txtHelp1)[1]*2))
        blf.position(0 , 70, yPos, 0)
        blf.draw(0, txtHelp1)

        # Draw edge
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glColor4f(1.0, 0.1, 0.8, 1.0)
        bgl.glBegin(bgl.GL_LINES)
        for p in self.LinkedVertices1:
            bgl.glVertex2f(self.Vertex1.x2D, self.Vertex1.y2D)
            bgl.glVertex2f(p.x2D, p.y2D)
        for p in self.LinkedVertices2:
            bgl.glVertex2f(self.Vertex2.x2D, self.Vertex2.y2D)
            bgl.glVertex2f(p.x2D, p.y2D)
        bgl.glEnd()

    # Compute the screen distance of two vertices
    def ScreenDistance(self, vertex_zero_co, vertex_one_co):
        matw = bpy.context.active_object.matrix_world
        V0 = matw * vertex_zero_co
        res0 = loc3d2d(bpy.context.region, bpy.context.space_data.region_3d, V0)
        V1 = matw * vertex_one_co
        res1 = loc3d2d(bpy.context.region, bpy.context.space_data.region_3d, V1)
        result = (res0 - res1).length
        return result

    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':
            Vertices = self.bm.verts
            # Calculate the temp t value. Stored in td
            tmpMouse = Vector((event.mouse_x, event.mouse_y))
            t_diff = (tmpMouse - self.tmpMouse).length
            self.tmpMouse = tmpMouse
            if self.Vertex2.original.idx is not None: # 2 vertex selected
                td = t_diff * self.Direction / self.ScreenDistance(self.Vertex1.original.co,
                                                                   self.Vertex2.original.co)
            else:  # 1 vertex selected
                td = t_diff * self.Direction / self.ScreenDistance(self.Vertex1.original.co,
                                                                   self.LinkedVertices1[self.VertLinkedIdx].original.co)
            if event.mouse_x < self.tmpMouse_x:
                td = -td

            if self.Vertex2.original.idx is not None: # 2 vertex selected
                # Calculate the t valuse
                if self.FirstVertexMove:
                    self.Vertex1.t = self.Vertex1.t + td
                else:
                    self.Vertex2.t = self.Vertex2.t + td
                # Move the vertex
                Vertices[self.Vertex1.original.idx].co = NewCoordinate(self.Vertex1.original.co,
                                                                       self.Vertex2.original.co,
                                                                       self.Vertex1.t)
                Vertices[self.Vertex2.original.idx].co = NewCoordinate(self.Vertex2.original.co,
                                                                       self.Vertex1.original.co,
                                                                       self.Vertex2.t)
            else:  # 1 vertex selected
                if self.LeftAltPress:  # Continuous slide
                    # Calculate the t valuse
                    self.Vertex2.t = self.Vertex2.t + td
                    # Move the vertex
                    Vertices[self.Vertex1.original.idx].co = NewCoordinate(self.Vertex2.original.co,
                                                                           self.LinkedVertices1[self.VertLinkedIdx].original.co,
                                                                           self.Vertex2.t)
                else:
                    # Calculate the t valuse
                    self.LinkedVertices1[self.VertLinkedIdx].t = self.LinkedVertices1[self.VertLinkedIdx].t + td
                    # Move the vertex
                    Vertices[self.Vertex1.original.idx].co = NewCoordinate(self.Vertex1.original.co,
                                                                           self.LinkedVertices1[self.VertLinkedIdx].original.co,
                                                                           self.LinkedVertices1[self.VertLinkedIdx].t)
                self.ActiveVertex = self.Vertex1.original.idx
            self.tmpMouse_x = event.mouse_x
            context.area.tag_redraw()

        elif event.type == 'LEFT_SHIFT':  # Hold left SHIFT for precision
            self.LeftShiftPress = not self.LeftShiftPress
            if self.LeftShiftPress:
                self.Direction *= 0.1
            else:
                if self.Direction < 0:
                    self.Direction = -1
                else:
                    self.Direction = 1

        elif event.type == 'LEFT_ALT':  # Hold ALT to use continuous slide
            self.LeftAltPress = not self.LeftAltPress
            if self.LeftAltPress and self.Vertex2.original.idx is None:
                vert = self.bm.verts[self.Vertex1.original.idx]
                self.Vertex2.original.co = Vector((vert.co.x, vert.co.y, vert.co.z))
                self.Vertex2.t = 0

        elif event.type == 'LEFT_ARROW':  # Reverse direction
            if self.Direction < 0.0:
                self.Direction = - self.Direction

        elif event.type == 'RIGHT_ARROW':  # Restore direction
            if self.Direction > 0.0:
                self.Direction = - self.Direction

        elif event.type == 'WHEELDOWNMOUSE':  # Change the vertex to be moved
            if self.Vertex2.original.idx is None:
                if self.LeftAltPress:
                    vert=self.bm.verts[self.Vertex1.original.idx]
                    self.Vertex2.original.co = Vector((vert.co.x, vert.co.y, vert.co.z))
                    self.Vertex2.t = 0
                self.VertLinkedIdx = self.VertLinkedIdx + 1
                if self.VertLinkedIdx > len(self.LinkedVertices1) - 1:
                    self.VertLinkedIdx = 0
                bpy.ops.mesh.select_all(action='DESELECT')
                self.bm.verts[self.Vertex1.original.idx].select = True
                self.bm.verts[self.LinkedVertices1[self.VertLinkedIdx].original.idx].select = True
            else:
                self.FirstVertexMove = not self.FirstVertexMove
                if self.LeftAltPress == False:
                    self.Vertex1.t = 0
                    self.Vertex2.t = 0
                if self.FirstVertexMove:
                    self.ActiveVertex = self.Vertex1.original.idx
                else:
                    self.ActiveVertex = self.Vertex2.original.idx
            # Keep Vertex movement coherent with Mouse movement
            if self.Vertex2.original.idx is not None:
                if self.FirstVertexMove: 
                    tmpX1, tmpY1 = loc3d2d(context.region, context.space_data.region_3d, self.Vertex1.original.co)
                    tmpX2, tmpY2 = loc3d2d(context.region, context.space_data.region_3d, self.Vertex2.original.co)
                    if ((tmpX1 > tmpX2 and self.Direction >= 0) or (tmpX2 > tmpX1 and self.Direction >= 0)):
                        self.Direction = -self.Direction
                else:
                    tmpX1, tmpY1 = loc3d2d(context.region, context.space_data.region_3d, self.Vertex2.original.co)
                    tmpX2, tmpY2 = loc3d2d(context.region, context.space_data.region_3d, self.Vertex1.original.co)
                    if (tmpX1 < tmpX2 and self.Direction < 0) or (tmpX2 < tmpX1 and self.Direction >= 0):
                        self.Direction = -self.Direction
            else:
                tmpX1, tmpY1 = loc3d2d(context.region, context.space_data.region_3d, self.Vertex1.original.co)
                tmpX2, tmpY2 = loc3d2d(context.region, context.space_data.region_3d, self.LinkedVertices1[self.VertLinkedIdx].original.co)
                if ((tmpX1 > tmpX2 and self.Direction >= 0) or (tmpX2 > tmpX1 and self.Direction < 0)):
                    self.Direction = -self.Direction
            context.area.tag_redraw()

        elif event.type == 'WHEELUPMOUSE':  # Change the vertex to be moved
            if self.Vertex2.original.idx is None:
                if self.LeftAltPress:
                    vert = self.bm.verts[self.Vertex1.original.idx]
                    self.Vertex2.original.co = Vector((vert.co.x, vert.co.y, vert.co.z))
                    self.Vertex2.t = 0
                self.VertLinkedIdx = self.VertLinkedIdx - 1
                if self.VertLinkedIdx < 0:
                    self.VertLinkedIdx = len(self.LinkedVertices1) - 1
                bpy.ops.mesh.select_all(action='DESELECT')
                self.bm.verts[self.Vertex1.original.idx].select = True
                self.bm.verts[self.LinkedVertices1[self.VertLinkedIdx].original.idx].select = True
            else:
                self.FirstVertexMove = not self.FirstVertexMove
                if self.LeftAltPress == False:
                    self.Vertex1.t = 0
                    self.Vertex2.t = 0
                if self.FirstVertexMove:
                    self.ActiveVertex = self.Vertex1.original.idx
                else:
                    self.ActiveVertex = self.Vertex2.original.idx
            # Keep Vertex movement coherent with Mouse movement
            if self.Vertex2.original.idx is not None:
                if self.FirstVertexMove: 
                    tmpX1, tmpY1 = loc3d2d(context.region, context.space_data.region_3d, self.Vertex1.original.co)
                    tmpX2, tmpY2 = loc3d2d(context.region, context.space_data.region_3d, self.Vertex2.original.co)
                    if ((tmpX1 > tmpX2 and self.Direction >= 0) or (tmpX2 > tmpX1 and self.Direction >= 0)):
                        self.Direction = -self.Direction
                else:
                    tmpX1, tmpY1 = loc3d2d(context.region, context.space_data.region_3d, self.Vertex2.original.co)
                    tmpX2, tmpY2 = loc3d2d(context.region, context.space_data.region_3d, self.Vertex1.original.co)
                    if (tmpX1 < tmpX2 and self.Direction < 0) or (tmpX2 < tmpX1 and self.Direction >= 0):
                        self.Direction = -self.Direction
            else:
                tmpX1, tmpY1 = loc3d2d(context.region, context.space_data.region_3d, self.Vertex1.original.co)
                tmpX2, tmpY2 = loc3d2d(context.region, context.space_data.region_3d, self.LinkedVertices1[self.VertLinkedIdx].original.co)
                if ((tmpX1 > tmpX2 and self.Direction >= 0) or (tmpX2 > tmpX1 and self.Direction < 0)):
                    self.Direction = -self.Direction
            context.area.tag_redraw()

        elif event.type == 'LEFTMOUSE':  # Confirm and exit
            Vertices = self.bm.verts
            bpy.ops.mesh.select_all(action='DESELECT')
            Vertices[self.Vertex1.original.idx].select = True
            if self.Vertex2.original.idx is not None:
                Vertices[self.Vertex2.original.idx].select = True
            context.region.callback_remove(self._handle)
            context.area.tag_redraw()
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:  # Restore and exit
            Vertices = self.bm.verts
            bpy.ops.mesh.select_all(action='DESELECT')
            Vertices[self.Vertex1.original.idx].co = self.Vertex1.original.co
            Vertices[self.Vertex1.original.idx].select = True
            if self.Vertex2.original.idx is not None:
                Vertices[self.Vertex2.original.idx].co = self.Vertex2.original.co
                Vertices[self.Vertex2.original.idx].select = True
            context.region.callback_remove(self._handle)
            context.area.tag_redraw()
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.active_object == None or context.active_object.type != "MESH":
            self.report({'WARNING'}, "Not any active object or not an mesh object:")
            return {'CANCELLED'}

        if context.active_object.mode != 'EDIT':
            self.report({'WARNING'}, "Mesh isn't in Edit Mode")
            return {'CANCELLED'}
        
        self.obj = bpy.context.object
        self.mesh = self.obj.data
        self.bm = bmesh.from_edit_mesh(self.mesh)

        Count=0
        Selected=False
        SelectedVertices = []  # Index of selected vertices
        for i, v in enumerate(self.bm.verts):
            if v.select and v.is_valid:
                SelectedVertices.append(v.index)
                Selected = True
                Count += 1 
                if (Count > 2):  # More than 2 vertices selected
                    Selected = False
                    break

        if Selected == False:
            self.report({'WARNING'}, "0 or more then 2 vertices selected, could not start")
            return {'CANCELLED'}

        self.tmpMouse[0], self.tmpMouse[1] = (event.mouse_x, event.mouse_y)
        self.tmpMouse_x = self.tmpMouse[0]

        self.Vertex1 = Point()
        self.Vertex2 = Point()
        self.LinkedVertices1 = []
        self.LinkedVertices2 = []

        # Store selected vertices data. To move in the first Loop
        self.Vertex1.original.idx = SelectedVertices[0]
        self.Vertex1.original.co = self.bm.verts[SelectedVertices[0]].co.copy()
        self.Vertex1.new = self.Vertex1.original
        x, y = loc3d2d(context.region, context.space_data.region_3d, self.bm.verts[SelectedVertices[0]].co)  # For draw edge
        self.Vertex1.x2D = x
        self.Vertex1.y2D = y
        if len(SelectedVertices) == 2:
            self.Vertex2.original.idx = SelectedVertices[1]
            self.Vertex2.original.co = self.bm.verts[SelectedVertices[1]].co.copy()
            self.Vertex2.new = self.Vertex2.original
            x, y = loc3d2d(context.region, context.space_data.region_3d, self.bm.verts[SelectedVertices[1]].co)  # For draw edge
            self.Vertex2.x2D = x
            self.Vertex2.y2D = y

        if len(SelectedVertices) == 2:
            self.bm.verts[self.Vertex2.original.idx].select = False  # Unselect the second selected vertex

        # Store linked vertices data, except the selected vertices
        for i, vert in enumerate(self.bm.verts[self.Vertex1.original.idx].link_edges):
            self.LinkedVertices1.append(Point())
            self.LinkedVertices1[-1].original.idx = vert.other_vert(self.bm.verts[self.Vertex1.original.idx]).index   #e_0.other_vert(v_0).index
            self.LinkedVertices1[-1].original.co = vert.other_vert(self.bm.verts[self.Vertex1.original.idx]).co.copy()
            self.LinkedVertices1[-1].new = self.LinkedVertices1[-1].original
            x, y = loc3d2d(context.region, context.space_data.region_3d, vert.other_vert(self.bm.verts[self.Vertex1.original.idx]).co)  # For draw edge
            self.LinkedVertices1[-1].x2D = x
            self.LinkedVertices1[-1].y2D = y
        if len(SelectedVertices) == 2:
            for i, vert in enumerate(self.bm.verts[self.Vertex2.original.idx].link_edges):
                self.LinkedVertices2.append(Point())
                self.LinkedVertices2[-1].original.idx = vert.other_vert(self.bm.verts[self.Vertex2.original.idx]).index
                self.LinkedVertices2[-1].original.co = vert.other_vert(self.bm.verts[self.Vertex2.original.idx]).co.copy()
                self.LinkedVertices2[-1].new = self.LinkedVertices1[-1].original
                x, y = loc3d2d(context.region, context.space_data.region_3d, vert.other_vert(self.bm.verts[self.Vertex2.original.idx]).co)  # For draw edge
                self.LinkedVertices2[-1].x2D = x
                self.LinkedVertices2[-1].y2D = y

        # Check for no linked vertex. Can be happen also with a mix of Select Mode
        # Need only with 1 vertex selected
        if len(SelectedVertices) == 1 and len(self.LinkedVertices1) == 0:
            self.report({'WARNING'}, "Isolated vertex or mixed Select Mode!")
            return {'CANCELLED'}
        # Check for duplicate vertices. If some linked vertice have the same coords of selected vertice
        # we have the error "division by 0
        if self.Vertex1.original.co == self.Vertex2.original.co:
            self.report({'WARNING'}, "At least one duplicate vertex")
            return {'CANCELLED'}
            
        self.bm.verts[self.Vertex1.original.idx].select = True  # Select the first selected vertex
        if len(SelectedVertices) == 2:
            self.bm.verts[self.Vertex2.original.idx].select = True  # Select the second selected vertex
        else:
            self.bm.verts[self.LinkedVertices1[0].original.idx].select = True  # Select the first linked vertex
        self.ActiveVertex = self.Vertex1.original.idx

        # Keep Vertex movement coherent with Mouse movement
        tmpX1, tmpY1 = loc3d2d(context.region, context.space_data.region_3d, self.Vertex1.original.co)
        if len(SelectedVertices) == 2:
            tmpX2, tmpY2 = loc3d2d(context.region, context.space_data.region_3d, self.Vertex2.original.co)
        else:
            tmpX2, tmpY2 = loc3d2d(context.region, context.space_data.region_3d, self.LinkedVertices1[0].original.co)
        if tmpX2 - tmpX1 < 0:
            self.Direction = -self.Direction

        context.area.tag_redraw()  # Force the redraw of the 3D View

        # Add the region OpenGL drawing callback
        # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
        self._handle = context.region.callback_add(self.__class__.draw_callback_px, (self, context), 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

def menu_func(self, context):
    self.layout.operator_context = "INVOKE_DEFAULT"
    self.layout.operator(BVertexSlideOperator.bl_idname, text="Vertex Slide Bmesh")


def register():
    bpy.utils.register_module(__name__)
    bpy.types.VIEW3D_MT_edit_mesh_vertices.prepend(menu_func)


def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.VIEW3D_MT_edit_mesh_vertices.remove(menu_func)


if __name__ == "__main__":
    register()
