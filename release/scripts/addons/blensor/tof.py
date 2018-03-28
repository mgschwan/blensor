#INFO: Preliminary TOF support
#TODO: Add different camera models
#TODO: Write the full evd data (noise vector, angles)
#TODO: Add the grayscale image values (of the render image)
#TODO: Add the foldback effect of ToF Cameras. 
#TODO: Add output of depthmap
#TODO: Simulate the sampling (i.e. PMD outputs only 1500 different depth values)
#      See SR4000 user manual for details
#TODO: Implement radial distortion
#INFO: SR4000
#      176x144 pixel
#      Standard FOV: 43.6°(h) 34.6°(v)    Focal Length: 10mm
#      Wide FOV: 69°(h) 56°(v)            Focal Length: 5.8mm
#         pixel_width (mm): 0.0453
#         pixel_height(mm): 0.0430
#      Model 1: unambiguity distance 5m 
#      Absolute accuracy of central pixels +-10mm
#      Repeatability of central pixels (sigma) 4mm
#
#      Model 2: unambiguity distance 10m 
#      Absolute accuracy of central pixels +-15mm
#      Repeatability of central pixels (sigma) 6mm

import math
import sys
import os
import struct 
import ctypes
import time
import random
import bpy
import numpy
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


parameters = {"max_dist":20,"noise_mu":0.0,"noise_sigma":0.004, "backfolding":False, "xres": 176, "yres": 144, "lens_angle_w": 43.6, "lens_angle_h": 34.6, "flength": 10.0}

def addProperties(cType):
    global parameters
    cType.tof_max_dist = bpy.props.FloatProperty( name = "Scan distance", default = parameters["max_dist"], min = 0, max = 1000, description = "How far the laser can see" )
    cType.tof_noise_mu = bpy.props.FloatProperty( name = "Noise mu", default = parameters["noise_mu"], description = "The center of the gaussian noise" )
    cType.tof_noise_sigma = bpy.props.FloatProperty( name = "Noise sigma", default = parameters["noise_sigma"], description = "The sigma of the gaussian noise" )
    cType.tof_backfolding = bpy.props.BoolProperty( name = "Backfolding", default = parameters["backfolding"], description = "Should backfolding be simulated" )
    cType.tof_xres = bpy.props.IntProperty( name = "X resolution", default = parameters["xres"], description = "Horizontal resolution" )
    cType.tof_yres = bpy.props.IntProperty( name = "Y resolution", default = parameters["yres"], description = "Vertical resolution" )
    cType.tof_lens_angle_w = bpy.props.FloatProperty( name = "Horizontal FOV", default = parameters["lens_angle_w"], description = "Horizontal opening angle" )
    cType.tof_lens_angle_h = bpy.props.FloatProperty( name = "Vertical FOV", default = parameters["lens_angle_h"], description = "Vertical opening angle" )
    cType.tof_focal_length = bpy.props.FloatProperty( name = "Focal length", default = parameters["flength"], description = "Focal length" )



def scan_advanced(scanner_object, max_distance = 10.0, evd_file=None, add_blender_mesh = False, 
                  add_noisy_blender_mesh = False, tof_res_x = 176, tof_res_y = 144, 
                  lens_angle_w=43.6, lens_angle_h=34.6, flength = 10.0,  evd_last_scan=True, 
                  noise_mu=0.0, noise_sigma=0.004, timestamp = 0.0, backfolding=False,
                  world_transformation=Matrix()):

    inv_scan_x = scanner_object.inv_scan_x
    inv_scan_y = scanner_object.inv_scan_y
    inv_scan_z = scanner_object.inv_scan_z  

    start_time = time.time()


    #10.0mm is currently the distance between the focal point and the sensor
    sensor_width = 2 * math.tan(deg2rad(lens_angle_w/2.0)) * 10.0
    sensor_height = 2 * math.tan(deg2rad(lens_angle_h/2.0)) * 10.0

    if tof_res_x == 0 or tof_res_y == 0:
        raise ValueError("Resolution must be > 0")

    pixel_width = sensor_width / float(tof_res_x)
    pixel_height = sensor_height / float(tof_res_y)


    bpy.context.scene.render.resolution_percentage

    width = bpy.context.scene.render.resolution_x
    height = bpy.context.scene.render.resolution_y
    cx = float(tof_res_x) /2.0
    cy = float(tof_res_y) /2.0 




    evd_buffer = []
    rays = []
    ray_info = []

    ray = Vector([0.0,0.0,0.0])
    for x in range(tof_res_x):
        for y in range(tof_res_y):
            """Calculate a vector that originates at the principal point
               and points to the pixel in the sensor. This vector is then
               scaled to the maximum scanning distance 
            """ 
            physical_x = float(x-cx) * pixel_width
            physical_y = float(y-cy) * pixel_height
            physical_z = -float(flength)
            ray.xyz = [physical_x, physical_y, physical_z]
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
            

    returns = blensor.scan_interface.scan_rays(rays, max_distance, inv_scan_x = inv_scan_x, inv_scan_y = inv_scan_y, inv_scan_z = inv_scan_z)

    evd_storage = evd.evd_file(evd_file, tof_res_x, tof_res_y, max_distance)

    reusable_vector = Vector([0.0,0.0,0.0,0.0])
    for i in range(len(returns)):
        idx = returns[i][-1]
        distance_noise =  random.gauss(noise_mu, noise_sigma)
        #If everything works substitute the previous line with this
        #distance_noise =  pixel_noise[returns[idx][-1]] + random.gauss(noise_mu, noise_sigma) 

        reusable_vector.xyzw = [returns[i][1],returns[i][2],returns[i][3],1.0]
        vt = (world_transformation * reusable_vector).xyz
        v = [returns[i][1],returns[i][2],returns[i][3]]
        vector_length = math.sqrt(v[0]**2+v[1]**2+v[2]**2)
        norm_vector = [v[0]/vector_length, v[1]/vector_length, v[2]/vector_length]


        vector_length_noise = vector_length+distance_noise
        if backfolding:
           #Distances > max_distance/2..max_distance are mapped to 0..max_distance/2
           if vector_length_noise >= max_distance/2.0:
               vector_length_noise = vector_length_noise - max_distance/2.0

        reusable_vector.xyzw = [norm_vector[0]*vector_length_noise, norm_vector[1]*vector_length_noise, norm_vector[2]*vector_length_noise,1.0]
        v_noise = (world_transformation * reusable_vector).xyz
        
        evd_storage.addEntry(timestamp = ray_info[idx][2], yaw =(ray_info[idx][0]+math.pi)%(2*math.pi), pitch=ray_info[idx][1], distance=vector_length, distance_noise=vector_length_noise, x=vt[0], y=vt[1], z=vt[2], x_noise=v_noise[0], y_noise=v_noise[1], z_noise=v_noise[2], object_id=returns[i][4], color=returns[i][5], idx=returns[i][-1])

    if evd_file:
        evd_storage.appendEvdFile()

    if not evd_storage.isEmpty():
        scan_data = numpy.array(evd_storage.buffer)
        additional_data = None
        if scanner_object.store_data_in_mesh:
            additional_data = evd_storage.buffer

        if add_blender_mesh:
            mesh_utils.add_mesh_from_points_tf(scan_data[:,5:8], "Scan", world_transformation, buffer=additional_data)

        if add_noisy_blender_mesh:
            mesh_utils.add_mesh_from_points_tf(scan_data[:,8:11], "NoisyScan", world_transformation, buffer=additional_data) 

        bpy.context.scene.update()

    end_time = time.time()
    scan_time = end_time-start_time
    print ("Elapsed time: %.3f"%(scan_time))


    return True, 0.0, scan_time




# This Function creates scans over a range of frames

def scan_range(scanne_object, frame_start, frame_end, filename="/tmp/tof.evd", frame_time = (1.0/24.0), fps = 24, add_blender_mesh=False, add_noisy_blender_mesh=False, max_distance = 20.0, last_frame = True, noise_mu = 0.0, noise_sigma = 0.0, backfolding=False, tof_res_x = 176, tof_res_y=144, lens_angle_w=43.6, lens_angle_h=34.6, flength = 10.0, world_transformation=Matrix()):



    start_time = time.time()

    time_per_frame = 1.0 / float(fps)

    try:
        for i in range(frame_start,frame_end):

            bpy.context.scene.frame_current = i

            ok,start_radians,scan_time = scan_advanced(scanner_object=scanner_object,
                    evd_file = filename , 
                    add_blender_mesh=add_blender_mesh, 
                    add_noisy_blender_mesh=add_noisy_blender_mesh, 
                    max_distance=max_distance,
                    timestamp = float(i) * frame_time,
                    noise_mu = noise_mu, noise_sigma=noise_sigma, backfolding=backfolding,
                    tof_res_x = tof_res_x, tof_res_y = tof_res_y,
                    lens_angle_w = lens_angle_w, lens_angle_h = lens_angle_h, flength = flength, 
                    world_transformation=world_transformation)

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



