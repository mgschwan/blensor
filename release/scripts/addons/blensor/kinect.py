#Range according to http://msdn.microsoft.com/en-us/library/hh405689.aspx
# 800 mm to 4000 mm
# HFOV 57°
# VFOV 43°
# Invalid depth value: 2047
# Focal length in pixels: 580 (4.73mm)
# according to http://www.ros.org/wiki/kinect_calibration/technical
# pixel width/height: 7.8um
# according to http://www.isprs.org/proceedings/XXXVIII/5-W12/Papers/ls2011_submission_40.pdf

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


    for x in range(res_x):
        for y in range(res_y):
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
            rays.extend([final_ray[0],final_ray[1],final_ray[2]])


            """ pitch and yaw are added for completeness, normally they are
                not provided by a ToF Camera but can be derived 
                from the pixel position and the camera parameters.
            """
            yaw = math.atan(physical_x/flength)
            pitch = math.atan(physical_y/flength)

            ray_info.append([yaw, pitch, timestamp])
            

    returns = blensor.scan_interface.scan_rays(rays, max_distance)

    verts = []
    verts_noise = []
    evd_storage = evd.evd_file(evd_file)

    for i in range(len(returns)):
        idx = returns[i][-1]
        distance_noise =  random.gauss(noise_mu, noise_sigma)
        #If everything works substitute the previous line with this
        #distance_noise =  pixel_noise[returns[idx][-1]] + random.gauss(noise_mu, noise_sigma) 

        vt = (world_transformation * Vector((returns[i][1],returns[i][2],returns[i][3],1.0))).xyz
        v = [returns[i][1],returns[i][2],returns[i][3]]
        verts.append ( vt )
        vector_length = math.sqrt(v[0]**2+v[1]**2+v[2]**2)
        norm_vector = [v[0]/vector_length, v[1]/vector_length, v[2]/vector_length]


        vector_length_noise = vector_length+distance_noise

        v_noise = (world_transformation * Vector((norm_vector[0]*vector_length_noise, norm_vector[1]*vector_length_noise, norm_vector[2]*vector_length_noise,1.0))).xyz
        verts_noise.append( v_noise )

        evd_storage.addEntry(timestamp = ray_info[idx][2], yaw =(ray_info[idx][0]+math.pi)%(2*math.pi), pitch=ray_info[idx][1], distance=vector_length, distance_noise=vector_length_noise, x=vt[0], y=vt[1], z=vt[2], x_noise=v_noise[0], y_noise=v_noise[1], z_noise=v_noise[2], object_id=returns[i][4], color=returns[i][5])

    if evd_file:
        evd_storage.appendEvdFile()

    if add_blender_mesh:
        scan_mesh = bpy.data.meshes.new("scan_mesh")
        scan_mesh.vertices.add(len(verts))
        scan_mesh.vertices.foreach_set("co", tuples_to_list(verts))
        scan_mesh.update()
        scan_mesh_object = bpy.data.objects.new("Scan.{0}".format(bpy.context.scene.frame_current), scan_mesh)
        bpy.context.scene.objects.link(scan_mesh_object)
        blensor.show_in_frame(scan_mesh_object, bpy.context.scene.frame_current)

        if world_transformation == Matrix():
            scan_mesh_object.matrix_world = bpy.context.object.matrix_world

    if add_noisy_blender_mesh:
        noise_scan_mesh = bpy.data.meshes.new("noisy_scan_mesh")
        noise_scan_mesh.vertices.add(len(verts_noise))
        noise_scan_mesh.vertices.foreach_set("co", tuples_to_list(verts_noise))
        noise_scan_mesh.update()
        noise_scan_mesh_object = bpy.data.objects.new("NoisyScan.{0}".format(bpy.context.scene.frame_current), noise_scan_mesh)
        bpy.context.scene.objects.link(noise_scan_mesh_object)
        blensor.show_in_frame(noise_scan_mesh_object, bpy.context.scene.frame_current)

        if world_transformation == Matrix():
            noise_scan_mesh_object.matrix_world = bpy.context.object.matrix_world

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



