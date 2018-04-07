# Author: Michael Gschwandtner
# Contact: blensor@zero997.com
import sys
import traceback
from mathutils import Matrix
from math import pi
import types
import bpy


from . import not_implemented_handler
from . import gaussian_error_model
from . import advanced_error_model
from . import blendodyne
from . import depthmap
from . import tof
from . import evd
from . import ibeo
from . import generic_lidar
from . import kinect
from . import exportmotion
from . import mesh_utils
from . import noise
from . import raycast


"""If the blensor module is reloaded, reload all submodules as well
   This will reload all modules at the initial import as well but 
   that should not be a problem
"""
import imp
locals_copy = dict(locals())
for var in locals_copy:
    tmp = locals_copy[var]
    if isinstance(tmp, types.ModuleType) and tmp.__package__ == "blensor":
      print ("Reloading: %s"%(var))
      imp.reload(tmp)



"""A package for simulating various types of range scanners inside blender"""

__version__ = '1.0.18'

__all__ = [
    'blendodyne',
    'depthmap',
    'globals',
    'tof',
    'kinect'
    'ibeo',
    'generic_lidar',
    'exportmotion',
    'mesh_utils',
    'noise'
    ]


class UserInfoException(Exception):
  pass

def setupActiveCamera(context, scanner):
  if context.scene.camera != scanner:
    raise UserInfoException("Must set active object as camera")

################ Blender Addon specific ######################


bl_info = {
    "name": "Sensor Simulation",
    "description": "Simulates various types of range scanners",
    "author": "Michael Gschwandtner",
    "version": (1,0,16),
    "blender": (2, 5, 6),
    "api": 31236,
    "location": "View3D > Properties > Camera",
    "warning": '', # used for warning icon and text in addons panel
    "wiki_url": "http://www.blensor.org",
    "category": "System"}

################  Blender UI specific ########################

def velodyne_layout(obj, layout):
            row = layout.row()
            row.prop(obj, "velodyne_model")
            row = layout.row()
            row.prop(obj, "velodyne_angle_resolution")
            row = layout.row()
            row.prop(obj, "velodyne_rotation_speed")
            row = layout.row()
            row.prop(obj, "velodyne_max_dist")
            row = layout.row()
            col = row.column()
            col.prop(obj, "velodyne_noise_mu")
            col = row.column()
            col.prop(obj, "velodyne_noise_sigma")
            row = layout.row()
            col = row.column()
            col.prop(obj, "velodyne_db_noise_mu")
            col = row.column()
            col.prop(obj, "velodyne_db_noise_sigma")
            row = layout.row()
            row.prop(obj,"velodyne_noise_type")
            row = layout.row()
            col = row.column()
            col.prop(obj, "velodyne_start_angle")
            col = row.column()
            col.prop(obj, "velodyne_end_angle")
            row = layout.row()
            row.operator("blensor.randomize_distance_bias", "Randomize bias")        
            row = layout.row()
            col = row.column()
            col.prop(obj, "velodyne_ref_dist")
            col = row.column()
            col.prop(obj, "velodyne_ref_limit")
            row = layout.row()
            col = row.column()
            col.prop(obj, "velodyne_ref_slope")


def tof_layout(obj, layout):
            row = layout.row()
            col = row.column()
            col.prop(obj, "tof_xres")
            col = row.column()
            col.prop(obj, "tof_yres")
            row = layout.row()
            col = row.column()
            col.prop(obj, "tof_lens_angle_w")
            col = row.column()
            col.prop(obj, "tof_lens_angle_h")
            row = layout.row()
            col = row.column()
            col.prop(obj, "tof_max_dist")
            col = row.column()
            col.prop(obj, "tof_focal_length")
            row = layout.row()
            col = row.column()
            col.prop(obj, "tof_noise_mu")
            col = row.column()
            col.prop(obj, "tof_noise_sigma")
            row = layout.row()
            row.prop(obj, "tof_backfolding")

def kinect_layout(obj, layout):
            row = layout.row()
            col = row.column()
            col.prop(obj, "kinect_xres")
            col = row.column()
            col.prop(obj, "kinect_yres")
            row = layout.row()
            row.prop(obj, "kinect_flength")
            row = layout.row()
            row.prop(obj, "kinect_max_dist")
            row = layout.row()
            row.prop(obj, "kinect_min_dist")
            row = layout.row()
            row.prop(obj, "kinect_inlier_distance")
            row = layout.row()
            col = row.column()
            col.prop(obj, "kinect_noise_mu")
            col = row.column()
            col.prop(obj, "kinect_noise_sigma")
            row = layout.row()
            row.prop(obj, "kinect_noise_scale")
            row = layout.row()
            row.prop(obj, "kinect_noise_smooth")
            row = layout.row()
            col = row.column()
            col.prop(obj, "kinect_ref_dist")
            col = row.column()
            col.prop(obj, "kinect_ref_limit")
            row = layout.row()
            col = row.column()
            col.prop(obj, "kinect_ref_slope")



def depthmap_layout(obj, layout):
            row = layout.row()
            row.prop(obj, "depthmap_max_dist")

def ibeo_layout(obj, layout):
            row = layout.row()
            row.prop(obj, "ibeo_angle_resolution")
            row = layout.row()
            row.prop(obj, "ibeo_rotation_speed")
            row = layout.row()
            row.prop(obj, "ibeo_max_dist")
            row = layout.row()
            col = row.column()
            col.prop(obj, "ibeo_noise_mu")
            col = row.column()
            col.prop(obj, "ibeo_noise_sigma")
            row = layout.row()
            col = row.column()
            col.prop(obj, "ibeo_start_angle")
            col = row.column()
            col.prop(obj, "ibeo_end_angle")
            row = layout.row()
            col = row.column()
            col.prop(obj, "ibeo_ref_dist")
            col = row.column()
            col.prop(obj, "ibeo_ref_limit")
            row = layout.row()
            col = row.column()
            col.prop(obj, "ibeo_ref_slope")

def generic_layout(obj, layout):
            row = layout.row()
            row.prop(obj, "generic_angle_resolution")
            row = layout.row()
            row.prop(obj, "generic_laser_angles")
            row = layout.row()
            row.prop(obj, "generic_rotation_speed")
            row = layout.row()
            row.prop(obj, "generic_max_dist")
            row = layout.row()
            col = row.column()
            col.prop(obj, "generic_noise_mu")
            col = row.column()
            col.prop(obj, "generic_noise_sigma")
            row = layout.row()
            row.prop(obj, "generic_advanced_error_model")
            row = layout.row()
            col = row.column()
            col.prop(obj, "generic_start_angle")
            col = row.column()
            col.prop(obj, "generic_end_angle")
            row = layout.row()
            col = row.column()
            col.prop(obj, "generic_ref_dist")
            col = row.column()
            col.prop(obj, "generic_ref_limit")
            row = layout.row()
            col = row.column()
            col.prop(obj, "generic_ref_slope")



            
def dispatch_scan(obj, filename=None, output_labels=True): 
            """Save the current frame number to restore it after the scan"""
            frame_current = bpy.context.scene.frame_current

            evd.output_labels = output_labels
            if obj.local_coordinates:
              world_transformation = Matrix()
            else:
              world_transformation = obj.matrix_world #((obj.matrix_world*Matrix.Rotation(-pi/2,4,"X")))
          


            if obj.scan_type == "velodyne":
                obj.ref_dist = obj.velodyne_ref_dist
                obj.ref_limit = obj.velodyne_ref_limit
                obj.ref_slope = obj.velodyne_ref_slope

                blendodyne.scan_advanced(scanner_object=obj,
                  angle_resolution=obj.velodyne_angle_resolution, 
                  max_distance=obj.velodyne_max_dist, start_angle=obj.velodyne_start_angle, 
                  end_angle=obj.velodyne_end_angle, noise_mu = obj.velodyne_noise_mu, 
                  noise_sigma=obj.velodyne_noise_sigma, add_blender_mesh=obj.add_scan_mesh, 
                  add_noisy_blender_mesh=obj.add_noise_scan_mesh, 
                  rotation_speed = obj.velodyne_rotation_speed, evd_file=filename,
                  world_transformation = world_transformation )

            elif obj.scan_type == "ibeo":
                obj.ref_dist = obj.ibeo_ref_dist
                obj.ref_limit = obj.ibeo_ref_limit
                obj.ref_slope = obj.ibeo_ref_slope

                ibeo.scan_advanced(scanner_object = obj, angle_resolution=obj.ibeo_angle_resolution, 
                  max_distance=obj.ibeo_max_dist, start_angle=obj.ibeo_start_angle, 
                  end_angle=obj.ibeo_end_angle, noise_mu = obj.ibeo_noise_mu, 
                  noise_sigma=obj.ibeo_noise_sigma, add_blender_mesh=obj.add_scan_mesh, 
                  add_noisy_blender_mesh=obj.add_noise_scan_mesh, 
                  rotation_speed = obj.ibeo_rotation_speed, evd_file=filename,
                  world_transformation=world_transformation)

            elif obj.scan_type == "generic":
                obj.ref_dist = obj.ibeo_ref_dist
                obj.ref_limit = obj.ibeo_ref_limit
                obj.ref_slope = obj.ibeo_ref_slope

                generic_lidar.scan_advanced( scanner_object = obj, add_blender_mesh=obj.add_scan_mesh, 
                  add_noisy_blender_mesh=obj.add_noise_scan_mesh, 
                  evd_file=filename,
                  world_transformation=world_transformation)

            elif obj.scan_type == "depthmap":
                depthmap.scan_advanced( scanner_object = obj, 
                  max_distance=obj.depthmap_max_dist, 
                  add_blender_mesh=obj.add_scan_mesh, filename=filename,
                  world_transformation=world_transformation)

            elif obj.scan_type == "tof":
                tof.scan_advanced( scanner_object = obj, max_distance=obj.tof_max_dist,
                  add_blender_mesh=obj.add_scan_mesh, add_noisy_blender_mesh=obj.add_noise_scan_mesh, 
                  evd_file=filename, noise_mu=obj.tof_noise_mu, noise_sigma=obj.tof_noise_sigma,
                  backfolding=obj.tof_backfolding, tof_res_x = obj.tof_xres, 
                  lens_angle_w = obj.tof_lens_angle_w, lens_angle_h = obj.tof_lens_angle_h, flength = obj.tof_focal_length, 
                  tof_res_y = obj.tof_yres,world_transformation=world_transformation)

            elif obj.scan_type == "kinect":
                obj.ref_dist = obj.kinect_ref_dist
                obj.ref_limit = obj.kinect_ref_limit
                obj.ref_slope = obj.kinect_ref_slope
                kinect.scan_advanced( scanner_object = obj, evd_file=filename, world_transformation=world_transformation)
            else:
                print ("Scanner not supported ... yet")

            """Restore the frame number"""
            bpy.context.scene.frame_current = frame_current


def dispatch_scan_range(obj,filename,frame=0,last_frame=True, time_per_frame=1.0/24.0, output_labels=True):
            evd.output_labels = output_labels
            evd.frame_counter = frame

            if obj.local_coordinates:
              world_transformation = Matrix()
            else:
              world_transformation = obj.matrix_world 

            if obj.scan_type == "velodyne":
                obj.ref_dist = obj.velodyne_ref_dist
                obj.ref_limit = obj.velodyne_ref_limit
                obj.ref_slope = obj.velodyne_ref_slope

                blendodyne.scan_range( scanner_object=obj, 
                  angle_resolution=obj.velodyne_angle_resolution, 
                  max_distance=obj.velodyne_max_dist, noise_mu = obj.velodyne_noise_mu, 
                  noise_sigma=obj.velodyne_noise_sigma,  rotation_speed = obj.velodyne_rotation_speed, 
                  frame_start = frame, frame_end=frame+1, filename=filename, last_frame=last_frame, 
                  frame_time=time_per_frame, world_transformation=world_transformation,
                  add_blender_mesh=obj.add_scan_mesh, add_noisy_blender_mesh=obj.add_noise_scan_mesh)

            elif obj.scan_type == "ibeo":
                ibeo.scan_range(scanner_object = obj, angle_resolution=obj.ibeo_angle_resolution,
                  max_distance=obj.ibeo_max_dist, noise_mu = obj.ibeo_noise_mu, 
                  noise_sigma=obj.ibeo_noise_sigma,  rotation_speed = obj.ibeo_rotation_speed, 
                  frame_start = frame, frame_end=frame+1, filename=filename, last_frame=last_frame,
                  world_transformation=world_transformation,
                  add_blender_mesh=obj.add_scan_mesh, add_noisy_blender_mesh=obj.add_noise_scan_mesh)

            elif obj.scan_type == "generic":
                generic_lidar.scan_range( scanner_object = obj, add_blender_mesh=obj.add_scan_mesh, 
                  frame_start = frame, frame_end=frame+1, filename=filename, last_frame=last_frame, 
                  add_noisy_blender_mesh=obj.add_noise_scan_mesh, 
                  world_transformation=world_transformation)

            elif obj.scan_type == "depthmap":
                depthmap.scan_range( scanner_object = obj,
                  max_distance=obj.depthmap_max_dist,
                  frame_start = frame, frame_end=frame+1, filename=filename,
                  world_transformation=world_transformation,
                  add_blender_mesh=obj.add_scan_mesh)

            elif obj.scan_type == "tof":
                tof.scan_range( scanner_object = obj, max_distance=obj.tof_max_dist, 
                  noise_mu = obj.tof_noise_mu, noise_sigma=obj.tof_noise_sigma,                
                  frame_start = frame, frame_end=frame+1, filename=filename, 
                  last_frame=last_frame,frame_time = time_per_frame,
                  backfolding=obj.tof_backfolding, tof_res_x = obj.tof_xres,
                  tof_res_y = obj.tof_yres, 
                  lens_angle_w = obj.tof_lens_angle_w, lens_angle_h = obj.tof_lens_angle_h, flength = obj.tof_focal_length, 
                  world_transformation=world_transformation,
                  add_blender_mesh=obj.add_scan_mesh, add_noisy_blender_mesh=obj.add_noise_scan_mesh)

            elif obj.scan_type == "kinect":
                kinect.scan_range( scanner_object = obj,
                  frame_start = frame, frame_end=frame+1, filename=filename, 
                  last_frame=last_frame,frame_time = time_per_frame,
                  world_transformation=world_transformation)

            else:
                print ("Scanner not supported ... yet")



class OBJECT_PT_sensor(bpy.types.Panel):
    bl_label = "Sensor Simulation"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"
    last_sensor = None

    def draw(self, context):
        layout = self.layout

        obj = context.object
       
        status = "Please select a camera"
        is_cam = False
        try:
            if obj.type == "CAMERA":
                status = obj.name
                is_cam = True
        except:
            is_cam = False

        row = layout.row()
        row.label(text="Laser scanner simulation", icon='WORLD_DATA')

        row = layout.row()
        row.label(text="Active sensor: " + status)
        row = layout.row()
        row.prop(obj, "name")
        if is_cam:
            row = layout.row()
            row.prop(obj, "scan_type")
            #
            #if obj.scan_type != self.last_sensor:
            #    bpy.ops.blensor.set_default()
            if obj.scan_type == "velodyne":
                velodyne_layout(obj,layout)
            elif obj.scan_type == "tof":
                tof_layout(obj,layout)
            elif obj.scan_type == "kinect":
                kinect_layout(obj,layout)
            elif obj.scan_type == "ibeo":
                ibeo_layout(obj,layout)
            elif obj.scan_type == "generic":
                generic_layout(obj,layout)
            elif obj.scan_type == "depthmap":
                depthmap_layout(obj,layout)

            row = layout.row()
            col = row.column()
            col.prop(obj, "add_scan_mesh")
            col = row.column()
            col.prop(obj, "add_noise_scan_mesh")
            row = layout.row()
            col = row.column()
            col.prop(obj, "save_scan")
            col = row.column()            
            col.prop(obj,"local_coordinates")        
            row = layout.row()
            col = row.column()
            col.prop(obj, "ref_enabled")
            col = row.column()
            col.prop(obj, "show_in_frame")
            row = layout.row()
            row.prop(obj, "store_data_in_mesh")
            row = layout.row()
            col = row.column()
            col.prop(obj, "inv_scan_x")
            col = row.column()
            col.prop(obj, "inv_scan_y")
            col = row.column()
            col.prop(obj, "inv_scan_z")
            row = layout.row()
            col = row.column()
            col.prop(obj, "scan_frame_start")
            col = row.column()
            col.prop(obj, "scan_frame_end")

            row = layout.row()
            row.operator("blensor.scan", "Single scan")        
            row = layout.row()
            row.operator("blensor.scanrange", "Scan range")        
            row = layout.row()
            col = row.column()
            col.operator("blensor.export_motion", "Export motion")
            col = row.column()
            col.operator("blensor.delete_scans", "Delete scans")
            
        
class OBJECT_OT_scan(bpy.types.Operator):
    bl_label = "Run scan" #Button label
    bl_idname = "blensor.scan" #Name used to refer to this operator
    bl_description = "Run a laser scan" # tooltip

    filepath = bpy.props.StringProperty(subtype="FILE_PATH")
    output_labels = bpy.props.BoolProperty(
        name="Write labels",
        description="Include labels for each point",
        default=True)


    def execute(self, context):
        obj = context.object

        try:
          setupActiveCamera(context,obj)
          dispatch_scan(obj, self.filepath, self.output_labels)
        except UserInfoException as e:
            print ("Scan not successful")
            self.report({'WARNING'}, "Scan not successful: "+str(e))

        return {'FINISHED'}
 
    def invoke(self,context,event):
        is_cam = False
        obj = context.object
        try:
            if context.object.type == "CAMERA":
                is_cam = True
        except:
            self.report({'WARNING'}, "Please select a valid camera")
        if is_cam:
            try:
              setupActiveCamera(context,obj)
              if obj.save_scan:
                 context.window_manager.fileselect_add(self)
                 return {'RUNNING_MODAL'}
              else:
                    dispatch_scan(obj)
            except UserInfoException as e:
               print ("Scan not successful")
               self.report({'WARNING'}, "Scan not successful: "+str(e))
                #    exc_type, exc_value, exc_traceback = sys.exc_info()
                #    traceback.print_tb(exc_traceback)
                #    self.report({'WARNING'}, "Scan not successful: "+str(type(e)))
        return{'FINISHED'}

class OBJECT_OT_scanrange(bpy.types.Operator):
    bl_label = "Run range scan" #Button label
    bl_idname = "blensor.scanrange" #Name used to refer to this operator
    bl_description = "Run a laser scan over a series of frames" # tooltip
 
    filepath = bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        obj = context.object
        try:
          setupActiveCamera(context,obj)

          bpy.ops.blensor.scanrange_handler(filepath=self.filepath)
        except UserInfoException as e:
            print ("Scan not successful")
            self.report({'WARNING'}, "Scan not successful: "+str(e))
        return {'FINISHED'}
    def invoke(self,context,event):
        wm = context.window_manager

        is_cam = False
        obj = context.object
        try:
            if context.object.type == "CAMERA":
                is_cam = True
        except:
            self.report({'WARNING'}, "Please select a valid camera: "+str(type(e)))
 
        if is_cam:
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}

        return{'FINISHED'}

class OBJECT_OT_scanrange_handler(bpy.types.Operator):
    bl_label = "Scane Range Handler" #Button label
    bl_idname = "blensor.scanrange_handler" #Name used to refer to this operator
    bl_description = "The actual scan part"

    filepath = bpy.props.StringProperty()
    frame = bpy.props.IntProperty()
    _timer = None   

    def modal(self, context, event):
        obj=context.object
        try:
          setupActiveCamera(context,obj)

          if event.type in ('ESC'):
              if self._timer is not None:
                 context.window_manager.event_timer_remove(self._timer)
              print ("ABORT MISSION NOW !!")
              return {'CANCELLED'}

          if event.type in ('TIMER'):
              """We only want to create a scan if we are actually called
                 otherwise every event i.e. MOUSEMOVE will force a scan
                 and totally clog the event handling.
              """
              if self._timer is not None:
                 """We don not want to generate timer events while we are scanning
                 """
                 context.window_manager.event_timer_remove(self._timer)
                 dispatch_scan_range(obj, self.filepath, frame=self.properties.frame, 
                                    last_frame=(self.properties.frame == obj.scan_frame_end),
                                    time_per_frame=1.0/(context.scene.render.fps / 
                                    context.scene.render.fps_base))

              if self.properties.frame >= obj.scan_frame_end:
                  return {'FINISHED'}

              range = float(obj.scan_frame_end-obj.scan_frame_start)
              finished = float(self.properties.frame-obj.scan_frame_start)
              percent = 100.0
              if range > 0:
                  percent = 100.0 * finished/range

              """Inform the user about our progress"""
              self.report({'INFO'}, "Scanned frame: %d ( %.2f %% )"%
                          (self.properties.frame,percent))

              self.properties.frame += 1
              self._timer = context.window_manager.event_timer_add(0.1, context.window)
        except UserInfoException as e:
            print ("Scan not successful")
            self.report({'WARNING'}, "Scan not successful: "+str(e))

        return {'PASS_THROUGH'}
        

    def invoke(self, context, event):
        obj = context.object
        self.properties.frame = obj.scan_frame_start

        """Truncate the file if it exists"""
        fh = open(self.filepath, "w")
        fh.close()

        context.window_manager.modal_handler_add(self)
        """If the user moves the mouse the events are generated faster. Otherwise
           use a timer event to trigger the calls to modal
        """
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
        self._timer = context.window_manager.event_timer_add(0.1, context.window)
        return {'RUNNING_MODAL'}



    def execute(self, context):
        obj = context.object
        self.properties.frame = obj.scan_frame_start

        """Truncate the file if it exists"""
        fh = open(self.filepath, "w")
        fh.close()

        context.window_manager.modal_handler_add(self)
        """If the user moves the mouse the events are generated faster. Otherwise
           use a timer event to trigger the calls to modal
        """
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
        self._timer = context.window_manager.event_timer_add(0.1, context.window)
        return {'RUNNING_MODAL'}
 





class OBJECT_OT_randomize(bpy.types.Operator):
    bl_label = "Randomize bias" #Button label
    bl_idname = "blensor.randomize_distance_bias" #Name used to refer to this operator
    bl_description = "Randomize the distance bias" # tooltip
 

    def invoke(self,context,event):
        wm = context.window_manager

        is_cam = False
        obj = context.object
        try:
            if context.object.type == "CAMERA":
                is_cam = True
        except:
                    self.report({'WARNING'}, "Please select a valid camera: "+str(type(e)))
 
        if is_cam:
            if obj.scan_type == "velodyne":
                blendodyne.randomize_distance_bias(obj, obj.velodyne_db_noise_mu, obj.velodyne_db_noise_sigma )

        return{'FINISHED'}


class OBJECT_OT_delete_scans(bpy.types.Operator):
    bl_label = "Delete scans"
    bl_idname = "blensor.delete_scans"
    bl_description = "Delete all scans from scene"
    
    
    def execute(self, context):
        for o in bpy.context.scene.objects:
            if o.name.find('NoisyScan.') == 0 or o.name.find('Scan.') == 0:
                bpy.context.scene.objects.unlink(o)
        
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_confirm(self, event)        
        



class OBJECT_OT_exportmotion(bpy.types.Operator):
    bl_label = "Export motion data" #Button label
    bl_idname = "blensor.export_motion" #Name used to refer to this operator
    bl_description = "Export the position and motion parameters of all objects"

    
    filepath = bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        bpy.ops.blensor.export_handler(filepath=self.filepath)
        return {'FINISHED'}    
 
    def invoke(self,context,event):
        print ("INVOKE")
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class OBJECT_OT_exporthandler(bpy.types.Operator):
    bl_label = "Export Handler" #Button label
    bl_idname = "blensor.export_handler" #Name used to refer to this operator
    bl_description = "The actual export part"

    filepath = bpy.props.StringProperty()
    last_frame = bpy.props.IntProperty()
    _timer = None   

    def modal(self, context, event):
        if event.type in ('ESC'):
            if self._timer is not None:
               context.window_manager.event_timer_remove(self._timer)
            return {'CANCELLED'}
        if event.type in ('TIMER'):
            try:
                exportmotion.export(filename=self.filepath, 
                                            fps=bpy.context.scene.render.fps / 
                                            bpy.context.scene.render.fps_base,
                                            frame = self.properties.last_frame,
                                            append = self.properties.last_frame !=
                                                     bpy.context.scene.frame_start)
            except:
                print ("Export not successful")
                self.report({'WARNING'}, "Export not successful: "+str(type(e)))
                if self._timer is not None:
                    context.window_manager.event_timer_remove(self._timer)
                return {'FINISHED'}

            if self.properties.last_frame >= bpy.context.scene.frame_end:
                if self._timer is not None:
                    context.window_manager.event_timer_remove(self._timer)
                return {'FINISHED'}

            self.properties.last_frame += 1

        return {'PASS_THROUGH'}
        

    def invoke(self, context, event):
        print ("EXECUTE")
        self.properties.last_frame = bpy.context.scene.frame_start
        print ("Start Modal handler")
        context.window_manager.modal_handler_add(self)
        """If the user moves the mouse the events are generated faster. Otherwise
           use a timer event to trigger the calls to modal
        """
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
        self._timer = context.window_manager.event_timer_add(0.01, context.window)
        print ("Modal handler started")
        return {'RUNNING_MODAL'}



    def execute(self, context):
        print ("EXECUTE")
        self.properties.last_frame = bpy.context.scene.frame_start
        print ("Start Modal handler")
        context.window_manager.modal_handler_add(self)
        """If the user moves the mouse the events are generated faster. Otherwise
           use a timer event to trigger the calls to modal
        """
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
        self._timer = context.window_manager.event_timer_add(0.01, context.window)
        print ("Modal handler started")
        return {'RUNNING_MODAL'}
 





laser_types=[("velodyne", "Velodyne HDL", "Rotating infrared laser"),("ibeo","Ibeo LUX","Line laser with 4 rays"),("tof","TOF Camera","Time of Flight camera"),("kinect","Kinect","Primesense technology"),("generic","Generic LIDAR","Generic LIDAR sensor"),("depthmap","Depthmap","Plain Depthmap")]


######################################################

def show_in_frame(obj, frame):
    """ Make obj only appear in the specified frame """
    # Clear existing animation data
    obj.animation_data_clear()
    # Turn off display in previous frame
    obj.hide = True
    obj.keyframe_insert('hide', frame=frame - 1)
    obj.hide_render = True
    obj.keyframe_insert('hide_render', frame=frame - 1)
    # Turn on display in desired frame
    obj.hide = False
    obj.keyframe_insert('hide', frame=frame)
    obj.hide_render = False
    obj.keyframe_insert('hide_render', frame=frame)
    # Turn off display in following frame
    obj.hide = True
    obj.keyframe_insert('hide', frame=frame + 1)
    obj.hide_render = True
    obj.keyframe_insert('hide_render', frame=frame + 1)


########################################################

 
class NativeWarningMessageBox(bpy.types.Operator):
    bl_idname = "message.nativewarningmessagebox"
    bl_label = ""
 
    def execute(self, context):
        return {'FINISHED'}
 
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width = 600)

    def draw(self, context):
        self.layout.label("Warning: The functionality you are trying to use is not available in this blender version")
        self.layout.label("This blender version does not have native Blensor support.")
        self.layout.label()
 


########################################################


def info():
	return str("Not for standalone use")


class GenericFloatCollection(bpy.types.PropertyGroup):
    val = bpy.props.FloatProperty(name="value")

"""Register the blender addon"""
def register():
    global laser_types
    bpy.utils.register_class(GenericFloatCollection)
    bpy.utils.register_class(OBJECT_OT_scanrange)
    bpy.utils.register_class(OBJECT_OT_randomize)
    bpy.utils.register_class(OBJECT_OT_delete_scans)
    bpy.utils.register_class(OBJECT_OT_scan)
    bpy.utils.register_class(OBJECT_PT_sensor)
    bpy.utils.register_class(OBJECT_OT_exportmotion)
    bpy.utils.register_class(OBJECT_OT_exporthandler)
    bpy.utils.register_class(OBJECT_OT_scanrange_handler)
    bpy.utils.register_class(NativeWarningMessageBox)

    cType = bpy.types.Object
       

    ## Common Properties

    cType.add_scan_mesh = bpy.props.BoolProperty( name = "Add scan", default = True, description = "Should the scan be added as an object" )
    cType.add_noise_scan_mesh = bpy.props.BoolProperty( name = "Add noisy scan", default = False, description = "Should the noisy scan be added as an object" )

    cType.save_scan = bpy.props.BoolProperty( name = "Save to File", default = False, description = "Should the scan be saved to file" )
    cType.local_coordinates = bpy.props.BoolProperty( name = "Sensor coordinates", default = True, description = "Should the points be saved sensor coordinates" )


    cType.scan_frame_start = bpy.props.IntProperty( name = "Start frame", default = 1, min = 0, description = "First frame to be scanned" )
    cType.scan_frame_end = bpy.props.IntProperty( name = "End frame", default = 250, min = 0, description = "Last frame to be scanned" )

    cType.store_data_in_mesh = bpy.props.BoolProperty( name = "Store data in mesh", default = True, description = "Add scan data to the Blender mesh, for later export (high memory usage!)" )

    cType.inv_scan_x = bpy.props.BoolProperty( name = "Inv X", default = False, description = "Invert the X coordinate" )
    cType.inv_scan_y = bpy.props.BoolProperty( name = "Inv Y", default = False, description = "Invert the X coordinate" )
    cType.inv_scan_z = bpy.props.BoolProperty( name = "Inv Z", default = False, description = "Invert the X coordinate" )




    cType.scan_type = bpy.props.EnumProperty( items=laser_types, name = "Scanner type", description = "Which scanner to use" )

    cType.ref_enabled = bpy.props.BoolProperty( name = "Enable reflection", default = False, description = "Should the respect reflective surfaces" )
    cType.show_in_frame = bpy.props.BoolProperty( name = "Show in frame", default = True, description = "Show the scanned result only in the frame it was scanned" )

    cType.ref_dist = bpy.props.FloatProperty( name = "Reflectivity Distance", default = 100.0, description = "Objects closer than reflectivity distance are independent of their reflectivity" )
    cType.ref_limit = bpy.props.FloatProperty( name = "Reflectivity Limit", default = -1.0, description = "Minimum reflectivity for objects at the reflectivity distance" )
    cType.ref_slope = bpy.props.FloatProperty( name = "Reflectivity Slope", default = 0.5, description = "Slope of the reflectivity limit curve" )




    ## Add the sensor specific properties

    blendodyne.addProperties(cType)
    ibeo.addProperties(cType)
    tof.addProperties(cType)
    kinect.addProperties(cType)
    generic_lidar.addProperties(cType)
    depthmap.addProperties(cType)
"""Unregister the blender addon"""
def unregister():
    bpy.utils.unregister_class(OBJECT_OT_exportmotion)
    bpy.utils.unregister_class(OBJECT_PT_sensor)
    bpy.utils.unregister_class(OBJECT_OT_scan)
    bpy.utils.unregister_class(OBJECT_OT_delete_scans)
    bpy.utils.unregister_class(OBJECT_OT_randomize)
    bpy.utils.unregister_class(OBJECT_OT_scanrange)
    bpy.utils.unregister_class(OBJECT_OT_exporthandler)
    bpy.utils.unregister_class(OBJECT_OT_scanrange_handler)
    bpy.utils.unregister_class(GenericFloatCollection)
    bpy.utils.unregister_class(NativeWarningMessageBox)


