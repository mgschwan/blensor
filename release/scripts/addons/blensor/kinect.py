#Range according to http://msdn.microsoft.com/en-us/library/hh405689.aspx
# 800 mm to 4000 mm
# HFOV 57°
# VFOV 43°
# Invalid depth value: 2047
# Focal length in pixels: 580 (4.73mm)
# according to http://www.ros.org/wiki/kinect_calibration/technical
# pixel width/height: 7.8um
# according to http://www.isprs.org/proceedings/XXXVIII/5-W12/Papers/ls2011_submission_40.pdf
#
# This sensor does calculate the paths from both the projector and the camera
# to the object. This gives the characteristical shadows around the objects 
# in the depthmap, without needing to do full stereo processing
#
# It assumes that the displacement between camera/projector is only in the x
# coordinate
#
import math
import sys
import os
import struct 
import ctypes
import time
import random
import bpy
import blensor.globals
import blensor.scan_interface
from blensor import evd
from blensor import mesh_utils


from mathutils import Vector, Euler, Matrix

def deg2rad(deg):
    return deg*math.pi/180.0

def rad2deg(rad):
    return rad*180.0/math.pi

def tuples_to_list(tuples):
    l = []
    for t in tuples:
        l.extend(t)
    return l


parameters = {"max_dist":4,"noise_mu":0.0,"noise_sigma":0.004,  
              "xres": 640, "yres": 480, "flength": 4.73}

def addProperties(cType):
    global parameters
    cType.kinect_max_dist = bpy.props.FloatProperty( name = "Scan distance", default = parameters["max_dist"], min = 0, max = 1000, description = "How far the kinect can see" )
    cType.kinect_noise_mu = bpy.props.FloatProperty( name = "Noise mu", default = parameters["noise_mu"], description = "The center of the gaussian noise" )
    cType.kinect_noise_sigma = bpy.props.FloatProperty( name = "Noise sigma", default = parameters["noise_sigma"], description = "The sigma of the gaussian noise" )
    cType.kinect_xres = bpy.props.IntProperty( name = "X resolution", default = parameters["xres"], description = "Horizontal resolution" )
    cType.kinect_yres = bpy.props.IntProperty( name = "Y resolution", default = parameters["yres"], description = "Vertical resolution" )

    cType.kinect_flength = bpy.props.FloatProperty( name = "Focal length", default = parameters["flength"], description = "Focal length in mm" )


""" Calculates the Image coordinates on the sensor for a given ray
    This function assumes that the rays are generated like
    for y in range(res_y):
      for x in range(res_x):
"""
def get_uv_from_idx(idx, res_x, res_y):
  return ((idx%res_x)-res_x/2,(idx//res_x)-res_y/2)

""" Calculate the pixel coordinate from the world coordinates the focal length
    and the width of a pixel.
    X,Z are in meters, flength is in pixel
"""
def get_pixel_from_world(X,Z,flength_px):
  return (flength_px*X/Z)


def scan_advanced(scanner_object, evd_file=None, 
                  evd_last_scan=True, 
                  timestamp = 0.0,
                  world_transformation=Matrix()):

    max_distance = scanner_object.kinect_max_dist
    add_blender_mesh = scanner_object.add_scan_mesh
    add_noisy_blender_mesh = scanner_object.add_noise_scan_mesh
    noise_mu = scanner_object.kinect_noise_mu
    noise_sigma = scanner_object.kinect_noise_sigma                
    res_x = scanner_object.kinect_xres 
    res_y = scanner_object.kinect_yres
    flength = scanner_object.kinect_flength


    start_time = time.time()



    if res_x < 1 or res_y < 1:
        raise ValueError("Resolution must be > 0")

    pixel_width = 0.0078
    pixel_height = 0.0078

    bpy.context.scene.render.resolution_percentage

    cx = float(res_x) /2.0
    cy = float(res_y) /2.0 




    evd_buffer = []
    rays = []
    ray_info = []

    baseline = Vector([0.075,0.0,0.0]) #Kinect has a baseline of 7.5 centimeters

    """Calculate the rays from the projector"""
    for y in range(res_y):
        for x in range(res_x):
            """Calculate a vector that originates at the principal point
               and points to the pixel in the sensor. This vector is then
               scaled to the maximum scanning distance 
            """ 

            physical_x = float(x-cx) * pixel_width
            physical_y = float(y-cy) * pixel_height
            physical_z = -float(flength)

            ray = Vector([physical_x, physical_y, physical_z])
            ray.normalize()
            final_ray = max_distance*ray
            rays.extend([final_ray[0],final_ray[1],final_ray[2], baseline.x,baseline.y,baseline.z]) #ray+baseline


            """ pitch and yaw are added for completeness, normally they are
                not provided by a ToF Camera but can be derived 
                from the pixel position and the camera parameters.
            """
            yaw = math.atan(physical_x/flength)
            pitch = math.atan(physical_y/flength)

            ray_info.append([yaw, pitch, timestamp])
            

    """ Max distance is increased because the kinect is limited by 4m
        _normal distance_ to the imaging plane
    """
    returns = blensor.scan_interface.scan_rays(rays, 2.0*max_distance, True)

    camera_rays = []
    projector_ray_index = [] #Stores the index to the rays array for the camera ray


    """Calculate the rays from the camera to the hit points of the projector rays"""
    for i in range(len(returns)):
        idx = returns[i][-1]
        camera_rays.extend([returns[i][1]+baseline.x, returns[i][2]+baseline.y, 
                            returns[i][3]+baseline.z])
        projector_ray_index.append(idx)


    camera_returns = blensor.scan_interface.scan_rays(camera_rays, 2*max_distance, False)

    verts = []
    verts_noise = []
    evd_storage = evd.evd_file(evd_file)


    """Check if the rays of the camera meet with the rays of the projector and
       add them as valid returns if they do"""
    for i in range(len(camera_returns)):
        idx = camera_returns[i][-1] 
        projector_idx = projector_ray_index[idx] # Get the index of the original ray

        if abs(camera_rays[idx*3]-camera_returns[i][1]) < 0.01 and abs(camera_rays[idx*3+1]-camera_returns[i][2]) < 0.01 and  abs(camera_rays[idx*3+2]-camera_returns[i][3]) < 0.01 and camera_returns[i][3] <= max_distance :
            """The ray hit the projected ray, so this is a valid measurement"""



            projector_point = get_uv_from_idx(projector_idx, res_x,res_y)
            camera_x = get_pixel_from_world(camera_rays[idx*3],camera_rays[idx*3+2],
                                   flength/pixel_width)
            camera_y = get_pixel_from_world(camera_rays[idx*3+1],camera_rays[idx*3+2],
                                   flength/pixel_width)

            """ Kinect calculates the disparity with an accuracy of 1/8 pixel"""

            camera_x_quantized = float(int(camera_x*8.0))/8.0
            camera_y_quantized = float(int(camera_y*8.0))/8.0 #I don't know if this accurately represents the kinect 

            disparity_quantized = camera_x_quantized + projector_point[0]

            Z_quantized = (flength*(baseline.x))/(disparity_quantized*pixel_width)
            X_quantized = Z_quantized*camera_x_quantized*pixel_width/flength
            Y_quantized = Z_quantized*camera_y_quantized*pixel_width/flength

            v = Vector([camera_returns[i][1],camera_returns[i][2],camera_returns[i][3]])
            vector_length = math.sqrt(v[0]**2+v[1]**2+v[2]**2)

            vt = (world_transformation * v.to_4d()).xyz
            verts.append ( vt )

            vn = Vector([X_quantized,Y_quantized,Z_quantized])
            vector_length_noise = vn.magnitude

            v_noise = (world_transformation * vn.to_4d()).xyz
            verts_noise.append( v_noise )

            evd_storage.addEntry(timestamp = ray_info[projector_idx][2], yaw = 0.0, pitch=0.0, distance=vector_length, distance_noise=vector_length_noise, x=vt[0], y=vt[1], z=vt[2], x_noise=v_noise[0], y_noise=v_noise[1], z_noise=v_noise[2], object_id=camera_returns[i][4], color=camera_returns[i][5])
        else:
          """Occlusion"""
          pass


    if evd_file:
        evd_storage.appendEvdFile()

    if add_blender_mesh:
        mesh_utils.add_mesh_from_points_tf(verts, "Scan", world_transformation)

    if add_noisy_blender_mesh:
        mesh_utils.add_mesh_from_points_tf(verts_noise, "NoisyScan", world_transformation)


    bpy.context.scene.update()

    end_time = time.time()
    scan_time = end_time-start_time
    print ("Elapsed time: %.3f"%(scan_time))


    return True, 0.0, scan_time




# This Function creates scans over a range of frames

def scan_range(scanner_object, frame_start, frame_end, filename="/tmp/kinect.evd", frame_time = (1.0/24.0), fps = 24, last_frame = True,world_transformation=Matrix()):



    start_time = time.time()

    time_per_frame = 1.0 / float(fps)

    try:
        for i in range(frame_start,frame_end):

            bpy.context.scene.frame_current = i

            ok,start_radians,scan_time = scan_advanced(scanner_object=scanner_object, evd_file = filename , 
                    timestamp = float(i) * frame_time, world_transformation=world_transformation)

            if not ok:
                break
    except:
        print ("Scan aborted")

    if last_frame:
        evd_file = open(filename,"a")
        evd_file.buffer.write(struct.pack("i",-1))
        evd_file.close()

    end_time = time.time()
    print ("Total scan time: %.2f"%(end_time-start_time))


######################################################



