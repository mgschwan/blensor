'''
bl_info = {
    "name": "Add 3 Point Lighting Setup",
    "author": "Erich Toven" meta-androcto
    "version": (1, 1),
    "blender": (2, 56, 0),
    "api": 34765,
    "location": "View3D > Add",
    "description": "Adds a new 3 point lighting setup",
    "warning": "Very Alpha!",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Object"}


'''
import bpy, mathutils, math
from math import pi
from bpy.props import FloatVectorProperty
#from add_utils import AddObjectHelper, add_object_data
from mathutils import Vector


class functions():
    def addTrackToConstraint(ob, name, target):
        cns = ob.constraints.new('TRACK_TO')
        cns.name = name
        cns.target = target
        cns.track_axis = 'TRACK_NEGATIVE_Z'
        cns.up_axis = 'UP_Y'
        cns.owner_space = 'LOCAL'
        cns.target_space = 'LOCAL'
        return

class AddSingleSpot(bpy.types.Operator):

    bl_idname = "object.add_single_spot"
    bl_label = "Add Single Spot Setup"
    bl_options = {'REGISTER', 'UNDO'}
 
    def execute(self, context):
   
        ### Add basic 3 point lighting setup ###        
        bpy.ops.object.add(type='EMPTY', view_align=False, enter_editmode=False, location=(0.000000, 0.000000, 0.000000))
        empty1 = bpy.context.object
        
        bpy.ops.object.lamp_add(type='SPOT', view_align=False, location=(0.000000, -10.000000, 10.000000), rotation=(-52.103, 15.548, -169.073))
        lamp1 = bpy.context.object

        ### Configure Lighting Setup ###        
        lamp1.name = 'Single_Spot1'
        
        lamp1.data.energy = 4.0
        lamp1.data.distance = 25.0
        lamp1.data.spot_size = 1.396264
        lamp1.data.spot_blend = 1
        lamp1.data.shadow_method = 'BUFFER_SHADOW'
        lamp1.data.shadow_buffer_type = 'HALFWAY'
        lamp1.data.shadow_filter_type = 'GAUSS'
        lamp1.data.shadow_buffer_soft = 10
        lamp1.data.shadow_buffer_size = 2048
        lamp1.data.shadow_buffer_bias = 0.100
        lamp1.data.shadow_buffer_samples = 8
        lamp1.data.use_auto_clip_start = True
        lamp1.data.use_auto_clip_end = True

        functions.addTrackToConstraint(lamp1,'AutoTrack',empty1)
  
        return {'FINISHED'}

class AddArea3point(bpy.types.Operator):
    bl_idname = "object.add_area_3point"
    bl_label = "add 3 Point Area Setup"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Add 3 Point lights to Scene"  
    def execute(self, context):
        ### Add basic 3 point lighting setup ###      

        bpy.ops.object.lamp_add(type='POINT', view_align=False, location=(-12.848104, 18.574114, 7.496113), rotation=(1.537930, 0.711540, 3.687180))
        lamp1 = bpy.context.object

        bpy.ops.object.lamp_add(type='POINT', view_align=False, location=(-13.168015, -18.672356, 15.276655), rotation=(0.941318, 0.917498, -1.187617))     
        lamp2 = bpy.context.object

        bpy.ops.object.lamp_add(type='POINT', view_align=False, location=(19.430519, -20.502472, 7.496113), rotation=(1.614763, 0.709077, 0.853816))   
        lamp3 = bpy.context.object


        ### Configure Lighting Setup ###        
        lamp1.name = 'Point1'
        lamp2.name = 'Point2'
        lamp3.name = 'Point3'
        
        lamp1.data.energy = 0.75
        lamp1.data.distance = 15.0
        lamp1.data.shadow_method = 'RAY_SHADOW'

       
        lamp2.data.energy = 0.75
        lamp2.data.distance = 16.0
        lamp2.data.shadow_method = 'RAY_SHADOW'

        
        lamp3.data.energy = 0.6
        lamp3.data.distance = 8.0
        lamp3.data.shadow_method = 'RAY_SHADOW'

        return {'FINISHED'}

class AddBasic3Point(bpy.types.Operator):

    bl_idname = "object.add_basic_3point"
    bl_label = "Add 3 Point Spot Setup"
    bl_options = {'REGISTER', 'UNDO'}
 
    def execute(self, context):
   
        ### Add basic 3 point lighting setup ###        
        bpy.ops.object.add(type='EMPTY', view_align=False, enter_editmode=False, location=(0.000000, -3.817210, 8.279530), rotation=(0, 0, 0))
        empty1 = bpy.context.object
        
        bpy.ops.object.lamp_add(type='SPOT', view_align=False, location=(19.430519, -20.502472, 7.496113), rotation=(1.614763, 0.709077, 0.853816))
        lamp1 = bpy.context.object

        bpy.ops.object.lamp_add(type='SPOT', view_align=False, location=(-12.848104, 18.574114, 7.496113), rotation=(1.537930, 1.537930, 3.687180))
        lamp2 = bpy.context.object
                
        bpy.ops.object.lamp_add(type='SPOT', view_align=False, location=(-13.168015, -18.672356, 15.276655), rotation=(0.941318, 0.917498, -1.187617))
        lamp3 = bpy.context.object

        ### Configure Lighting Setup ###        
        lamp1.name = 'Spot1'
        lamp2.name = 'Spot2'
        lamp3.name = 'Key'
        
        lamp1.data.energy = 4.0
        lamp1.data.distance = 25.0
        lamp1.data.spot_size = 1.396264
        lamp1.data.spot_blend = 1
        lamp1.data.shadow_method = 'BUFFER_SHADOW'
        lamp1.data.shadow_buffer_type = 'HALFWAY'
        lamp1.data.shadow_filter_type = 'GAUSS'
        lamp1.data.shadow_buffer_soft = 10
        lamp1.data.shadow_buffer_size = 2048
        lamp1.data.shadow_buffer_bias = 0.100
        lamp1.data.shadow_buffer_samples = 8
        lamp1.data.use_auto_clip_start = True
        lamp1.data.use_auto_clip_end = True
        
        
        lamp2.data.energy = 2.0
        lamp2.data.distance = 25.0
        lamp2.data.spot_size = 1.047198
        lamp2.data.spot_blend = 1
        lamp2.data.shadow_method = 'BUFFER_SHADOW'
        lamp2.data.shadow_buffer_type = 'HALFWAY'
        lamp2.data.shadow_filter_type = 'GAUSS'
        lamp2.data.shadow_buffer_soft = 5
        lamp2.data.shadow_buffer_size = 2048
        lamp2.data.shadow_buffer_bias = 0.100
        lamp2.data.shadow_buffer_samples = 16
        lamp2.data.use_auto_clip_start = True
        lamp2.data.use_auto_clip_end = True

        lamp3.data.energy = 2.0
        lamp3.data.distance = 30.0
        lamp3.data.spot_size = 1.570797
        lamp3.data.spot_blend = 1
        lamp3.data.shadow_method = 'BUFFER_SHADOW'
        lamp3.data.shadow_buffer_type = 'HALFWAY'
        lamp3.data.shadow_filter_type = 'GAUSS'
        lamp3.data.shadow_buffer_soft = 20
        lamp3.data.shadow_buffer_size = 2048
        lamp3.data.shadow_buffer_bias = 1
        lamp3.data.shadow_buffer_samples = 16
        lamp3.data.use_auto_clip_start = True
        lamp3.data.use_auto_clip_end = True

        functions.addTrackToConstraint(lamp3,'AutoTrack',empty1)
  
        return {'FINISHED'}
class AddBasic2Point(bpy.types.Operator):

    bl_idname = "object.add_basic_2point"
    bl_label = "Add 2 Point Setup"
    bl_options = {'REGISTER', 'UNDO'}
 
    def execute(self, context):
   
# add point lamp
        bpy.ops.object.lamp_add(type="POINT", location = (4.07625,1.00545,5.90386), rotation =(0.650328,0.055217,1.866391))
        lamp1 = bpy.context.active_object.data
        lamp1.name = "Point_Right"
        lamp1.energy = 1.0
        lamp1.distance = 30.0
        lamp1.shadow_method = "RAY_SHADOW"
        lamp1.use_sphere = True        
# add point lamp2
        bpy.ops.object.lamp_add(type="POINT", location = (-0.57101,-4.24586,5.53674), rotation =(1.571,0,0.785))
        lamp2 = bpy.context.active_object.data
        lamp2.name = "Point_Left"
        lamp2.energy = 1.0
        lamp2.distance = 30.0
        lamp2.shadow_method = "RAY_SHADOW"
  
        return {'FINISHED'}
       
class INFO_MT_add_3pointsetup(bpy.types.Menu):
    bl_idname = "INFO_MT_lighting.add"
    bl_label = "Lighting Setups"
    bl_description = "Add 3 point light sets to Scene"  
    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("object.add_single_spot",
            text="Add Single Spot")
        layout.operator("object.add_basic_3point",
            text="Add 3 Point Spot Setup")
        layout.operator("object.add_basic_2point",
            text="Add 2 Point Setup")
        layout.operator("object.add_area_3point",
            text="Add 3 Point Setup")

#import space_info    


#### REGISTER ####
def menu_func(self, context):
    self.layout.menu("INFO_MT_lighting.add", icon="PLUGIN")

def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_add.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_add.remove(menu_func)


if __name__ == '__main__':
    register()