'''# ##### BEGIN GPL LICENSE BLOCK #####
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
    "name": "Rectangle",
    "author": "Carbonic Wolf",
    "version": (1,1),
    "blender": (2, 5, 9),
    "api": 39933,
    "location": "View3D > Add > Curve",
    "description": "Add rectangle",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Add Curve"}
    
 '''   
##------------------------------------------------------------
#### import modules
import bpy
from bpy.props import *
from mathutils import *
from math import *

##------------------------------------------------------------
# calculates the matrix for the new object
# depending on user pref
def align_matrix(context):
    loc = Matrix.Translation(context.scene.cursor_location)
    obj_align = context.user_preferences.edit.object_align
    if (context.space_data.type == 'VIEW_3D'
        and obj_align == 'VIEW'):
        rot = context.space_data.region_3d.view_matrix.rotation_part().invert().resize4x4()
    else:
        rot = Matrix()
    align_matrix = loc * rot
    return align_matrix

##------------------------------------------------------------
#### Curve creation functions
# sets bezierhandles to auto
def setBezierHandles(obj, mode = 'AUTOMATIC'):
    scene = bpy.context.scene
    if obj.type != 'CURVE':
        return
    scene.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT', toggle=True)
    bpy.ops.curve.select_all(action='SELECT')
    bpy.ops.curve.handle_type_set(type=mode)
    bpy.ops.object.mode_set(mode='OBJECT', toggle=True)

##------------------------------------------------------------
#### Curve creation functions

# get array of vertcoordinates acording to splinetype
def vertsToPoints(Verts):
    vertArray = []

    for v in Verts:
        vertArray += v

    return vertArray

# create new CurveObject from vertarray and splineType
def createCurve(vertArray, props, align_matrix):
    # options to vars
    splineType = 'BEZIER'
    name = 'rectangle'

    # create curve
    scene = bpy.context.scene
    newCurve = bpy.data.curves.new(name, type = 'CURVE') # curvedatablock
    newSpline = newCurve.splines.new(type = splineType)  # spline

    # create spline from vertarray
    newSpline.bezier_points.add(int(len(vertArray)*0.33))
    newSpline.bezier_points.foreach_set('co', vertArray)

    # Curve settings
    newCurve.dimensions = '2D'
    newSpline.use_cyclic_u = True
    newSpline.use_endpoint_u = True
    newSpline.order_u = 4

    # create object with newCurve
    new_obj = bpy.data.objects.new(name, newCurve)  # object
    scene.objects.link(new_obj)                     # place in active scene
    new_obj.select = True                           # set as selected
    scene.objects.active = new_obj                  # set as active
    new_obj.matrix_world = align_matrix             # apply matrix

    setBezierHandles(new_obj, 'VECTOR')

    return

########################################################################
#######################  Definitions ###################################
########################################################################

#### rectangle
def rectangle_Curve(rectangle_w=2, rectangle_l=2, rectangle_r=1):
    newPoints = []
    x=rectangle_w/2
    y=rectangle_l/2
    r=rectangle_r/2
    
    if r>0:
       newPoints.append([-x+r,y,0])
       newPoints.append([x-r,y,0])
       newPoints.append([x,y-r,0])
       newPoints.append([x,-y+r,0])
       newPoints.append([x-r,-y,0])
       newPoints.append([-x+r,-y,0])
       newPoints.append([-x,-y+r,0])
       newPoints.append([-x,y-r,0])
    else:
       newPoints.append([-x,y,0])
       newPoints.append([x,y,0])
       newPoints.append([x,-y,0])
       newPoints.append([-x,-y,0])

    return newPoints

##------------------------------------------------------------
# Main Function
def main(context, props, align_matrix):
    # deselect all objects
    bpy.ops.object.select_all(action='DESELECT')

    # get verts
    verts = rectangle_Curve(props.rectangle_w,
                            props.rectangle_l,
                            props.rectangle_r)

    # turn verts into array
    vertArray = vertsToPoints(verts)

    # create object
    createCurve(vertArray, props, align_matrix)

    return

class rectangle(bpy.types.Operator):
    ''''''
    bl_idname = "curve.rectangle"
    bl_label = "Rectangle"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "adds rectangle"

    # align_matrix for the invoke
    align_matrix = Matrix()

    #### Parameters
    rectangle_w = FloatProperty(name="Width",
                default=2,
                min=0, soft_min=0,
                description="Width")
    rectangle_l = FloatProperty(name="Length",
                default=2,
                min=0, soft_min=0,
                description="Length")
    rectangle_r = FloatProperty(name="Rounded",
                default=1,
                min=0, soft_min=0,
                description="Rounded")

    ##### DRAW #####
    def draw(self, context):
        props = self.properties
        layout = self.layout

        # general options        
        col = layout.column()
        #col.prop(props, 'rectangle')
        col.label(text="Rectangle Parameters")

        # Parameters 
        box = layout.box()
        box.prop(props, 'rectangle_w')
        box.prop(props, 'rectangle_l')
        box.prop(props, 'rectangle_r')

    ##### POLL #####
    @classmethod
    def poll(cls, context):
        return context.scene != None

    ##### EXECUTE #####
    def execute(self, context):
        # turn off undo
        undo = bpy.context.user_preferences.edit.use_global_undo
        bpy.context.user_preferences.edit.use_global_undo = False

        props = self.properties
        
        # main function
        main(context, props, self.align_matrix)
        
        # restore pre operator undo state
        bpy.context.user_preferences.edit.use_global_undo = undo

        return {'FINISHED'}

    ##### INVOKE #####
    def invoke(self, context, event):
        # store creation_matrix
        self.align_matrix = align_matrix(context)
        self.execute(context)

        return {'FINISHED'}

################################################################################
##### REGISTER #####

def rectangle_button(self, context):
    self.layout.operator(rectangle.bl_idname, text="Rectangle", icon="PLUGIN")


def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_curve_add.append(rectangle_button)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_curve_add.remove(rectangle_button)

if __name__ == "__main__":
    register()
