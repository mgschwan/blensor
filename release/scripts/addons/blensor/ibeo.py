#Ibeo LUX HD specs. According to 
#http://www.ibeo-as.com/images/stories/products/lux_HD/ibeo%20LUX%20HD.pdf
#
# H-FOV: 50° to -60° (2 layers)
#        35° to -50° (4 layers)
#
# V-FOV: 3.2°
# TODO: Multiecho (up to 3 responses per shot)
# Rate; 12.5/25.0/50Hz
# Accuracy: 10cm
# H-Resolution: up to 0.25°
# V-Resolution: 0.8°
# Distance resolution: 4cm
#
#
import math
import sys
import os
import struct 
import ctypes
import time
import random
import bpy
import numpy
from mathutils import Vector, Euler,geometry, Matrix

from blensor import evd
from blensor import mesh_utils

import blensor

parameters = {"angle_resolution":0.25, "rotation_speed":12.5,"max_dist":90,"noise_mu":0.0,"noise_sigma":0.03,
              "start_angle":-50.0,"end_angle":35.0,
              "reflectivity_distance":50,"reflectivity_limit":0.1,"reflectivity_slope":0.005333333}

def addProperties(cType):
    global parameters
    cType.ibeo_angle_resolution = bpy.props.FloatProperty( name = "Scanresolution", default = parameters["angle_resolution"], min = 0.01, max = 3.141, description = "How far(angle) two scan lines are apart" )
    cType.ibeo_rotation_speed = bpy.props.FloatProperty( name = "Rotation speed", default = parameters["rotation_speed"], min = 1, max = 100, description = "Rotation speed in Hertz" )
    cType.ibeo_max_dist = bpy.props.FloatProperty( name = "Scan distance", default = parameters["max_dist"], min = 0, max = 1000, description = "How far the laser can see" )
    cType.ibeo_noise_mu = bpy.props.FloatProperty( name = "Noise mu", default = parameters["noise_mu"], description = "The center of the gaussian noise" )
    cType.ibeo_noise_sigma = bpy.props.FloatProperty( name = "Noise sigma", default = parameters["noise_sigma"], description = "The sigma of the gaussian noise" )
    cType.ibeo_start_angle = bpy.props.FloatProperty( name = "Start angle", default = parameters["start_angle"], description = "The angle at which the scan is started" )
    cType.ibeo_end_angle = bpy.props.FloatProperty( name = "End angle", default = parameters["end_angle"], description = "The angle at which the scan is stopped" )

    cType.ibeo_ref_dist = bpy.props.FloatProperty( name = "Reflectivity Distance", default = parameters["reflectivity_distance"], description = "Objects closer than reflectivity distance are independent of their reflectivity" )
    cType.ibeo_ref_limit = bpy.props.FloatProperty( name = "Reflectivity Limit", default = parameters["reflectivity_limit"], description = "Minimum reflectivity for objects at the reflectivity distance" )
    cType.ibeo_ref_slope = bpy.props.FloatProperty( name = "Reflectivity Slope", default = parameters["reflectivity_slope"], description = "Slope of the reflectivity limit curve" )




def deg2rad(deg):
    return deg*math.pi/180.0

def rad2deg(rad):
    return rad*180.0/math.pi

def tuples_to_list(tuples):
    l = []
    for t in tuples:
        l.extend(t)
    return l

#An Ibeo laser with 4 rays has an aperture angle of 3.2 degrees
#laser_angles =[ (1.6 - 0.8*float(i))*math.pi/180.0 for i in range(4)]
laser_angles =[ deg2rad(1.6), deg2rad(0.8), deg2rad(-0.8), deg2rad(-1.6)]


# The laser noise is initialized with a fixed randomized array to increase
# repoducibility. If the noise should be randomize, call 
# randomize_distance_bias
laser_noise = [0.015798891682948433, 0.030289711937446478, 0.044832263895615468, 
0.022628361223111119]


## If the laser noise has to be truely randomize, call this function prior
## to every scan
def randomize_distance_bias(noise_mu = 0.0, noise_sigma = 0.04):
    for idx in range(len(laser_angles)):
      laser_noise[idx] = random.gauss(noise_mu, noise_sigma)

mirror = [Vector([0,0,0]), Vector([0,0,0]), Vector([0,0,0])]
norm_mirror = Vector([0,1,0])
#Create a Triangle that represents the 45° mirror
#rotated around the main axis by <angle>
#The mirror has a side length of 1 meter which is more
#than enough to fit the small square mirror inside this triangle
def createMirror(angle):
    mirror[0].xyz = [0,-1,-1]
    mirror[1].xyz = [-1,1,1]
    mirror[2].xyz = [1,1,1]
    mirror[0].rotate( Matrix.Rotation( angle, 4, norm_mirror) )
    mirror[1].rotate( Matrix.Rotation( angle, 4, norm_mirror)  )
    mirror[2].rotate( Matrix.Rotation( angle, 4, norm_mirror)  )
    n = geometry.normal(mirror[2],mirror[1],mirror[0])
    return [mirror[2],mirror[1],mirror[0],n]


ray_to_mirror = Vector([0.0,0.0,0.0])
rotation_axis = Vector([1.0,0.0,0.0])
reusable_ray = Vector([0.0,0.0,0.0])
#Shoot a ray onto the mirror (like it would be inside the ibeo)
#and calculate the intersection(reflection) point.
#Use the angle between the ray and the normal vector of the mirror
#to calculate the outgoing ray
#Returns the ray, the origin of the ray and the outgoing vertical angle 
#of the ray from the Ibeo scanner
def calculateRay(laserAngle, mirrorAngle, laserMirrorDistance):
    reusable_ray.xyz = [0.0,-1.0,0.0] # A ray pointing down towards the mirror
    reusable_ray.rotate( Matrix.Rotation(laserAngle, 4, rotation_axis) )
    [v1,v2,v3,n] = createMirror(mirrorAngle)
    incomingAngle = n.angle(reusable_ray)%(math.pi/2.0)
    reflectionAxis = n.cross(reusable_ray) # Calculate the axis around which the ray needs
                                           # to be rotated to created the reflection
    ray_to_mirror.xyz = [0.0,laserMirrorDistance,0.0]
    reflectionPoint = geometry.intersect_ray_tri(v1,v2,v3,reusable_ray,ray_to_mirror,False)
    reusable_ray.rotate( Matrix.Rotation(2*incomingAngle, 4,reflectionAxis) )
    return [reusable_ray, reflectionPoint, math.pi/4-incomingAngle]


def scan_advanced(scanner_object, rotation_speed = 25.0, simulation_fps=24, angle_resolution = 0.5, max_distance = 90, evd_file=None,noise_mu=0.0, noise_sigma=0.03, start_angle = -35, end_angle = 50, evd_last_scan=True, add_blender_mesh = False, add_noisy_blender_mesh = False, simulation_time = 0.0,laser_mirror_distance=0.05, world_transformation=Matrix()):
    inv_scan_x = scanner_object.inv_scan_x
    inv_scan_y = scanner_object.inv_scan_y
    inv_scan_z = scanner_object.inv_scan_z   

    start_time = time.time()

    current_time = simulation_time
    delta_rot = angle_resolution*math.pi/180

    evd_storage = evd.evd_file(evd_file)

    xaxis = Vector([1,0,0])
    yaxis = Vector([0,1,0])
    zaxis = Vector([0,0,1])

    rays = []
    ray_info = []

    angles = end_angle-start_angle
    steps_per_rotation = angles/angle_resolution
    time_per_step = (1.0/rotation_speed) / steps_per_rotation

    lines = (end_angle-start_angle)/angle_resolution

    for line in range(int(lines)):
        for laser_idx in range(len(laser_angles)):
            current_angle = start_angle + float(line)*angles/float(lines)
            [ray, origion, laser_angle] = calculateRay(laser_angles[laser_idx], deg2rad(current_angle), laser_mirror_distance) 
            #TODO: Use the origin to cast the ray. Requires changes to the blender patch
            rot_angle = 1e-6 + current_angle + 180.0
            timestamp = ( (rot_angle-180.0)/angle_resolution) * time_per_step 
            rot_angle = rot_angle%360.0
            ray_info.append([deg2rad(rot_angle), laser_angle, timestamp])
            
            rays.extend([ray[0],ray[1],ray[2]])


    returns = blensor.scan_interface.scan_rays(rays, max_distance, inv_scan_x = inv_scan_x, inv_scan_y = inv_scan_y, inv_scan_z = inv_scan_z)

    reusable_vector = Vector([0.0,0.0,0.0,0.0])
    for i in range(len(returns)):
        idx = returns[i][-1]
        reusable_vector.xyzw = [returns[i][1],returns[i][2],returns[i][3],1.0]
        vt = (world_transformation * reusable_vector).xyz
        v = [returns[i][1],returns[i][2],returns[i][3]]

        distance_noise =  laser_noise[idx%len(laser_noise)] + random.gauss(noise_mu, noise_sigma) 
        vector_length = math.sqrt(v[0]**2+v[1]**2+v[2]**2)
        norm_vector = [v[0]/vector_length, v[1]/vector_length, v[2]/vector_length]
        vector_length_noise = vector_length+distance_noise
        reusable_vector.xyzw = [norm_vector[0]*vector_length_noise, norm_vector[1]*vector_length_noise, norm_vector[2]*vector_length_noise,1.0]
        v_noise = (world_transformation * reusable_vector).xyz

        evd_storage.addEntry(timestamp = ray_info[idx][2], yaw =(ray_info[idx][0]+math.pi)%(2*math.pi), pitch=ray_info[idx][1], distance=vector_length, distance_noise=vector_length_noise, x=vt[0], y=vt[1], z=vt[2], x_noise=v_noise[0], y_noise=v_noise[1], z_noise=v_noise[2], object_id=returns[i][4], color=returns[i][5])

    current_angle = start_angle+float(float(int(lines))*angle_resolution)
            
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

    return True, current_angle, scan_time




# This Function creates scans over a range of frames

def scan_range(scanner_object, frame_start, frame_end, filename="/tmp/landscape.evd", frame_time = (1.0/24.0), rotation_speed = 25.0, fps = 24, add_blender_mesh=False, add_noisy_blender_mesh=False, angle_resolution = 0.5, max_distance = 90.0, noise_mu = 0.0, noise_sigma= 0.02, laser_mirror_distance = 0.05, start_angle=-35.0, end_angle=50.0, last_frame = True, world_transformation=Matrix()):

    fps = rotation_speed # The Ibeo Module does not yet support an update
                         # rate different to the simulation speed
    start_time = time.time()

    time_per_frame = 1.0 / float(fps)

    try:
        for i in range(frame_start,frame_end):

                bpy.context.scene.frame_current = i

                ok,start_radians,scan_time = scan_advanced(\
                                            scanner_object= scanner_object, \
                                            angle_resolution = angle_resolution,\
                                            start_angle = start_angle, \
                                            end_angle=end_angle, \
                                            evd_file = filename, \
                                            evd_last_scan=False,\
                                            add_blender_mesh=add_blender_mesh, \
                                            add_noisy_blender_mesh=add_noisy_blender_mesh,\
                                            simulation_time = float(i)*frame_time,\
                                            max_distance=max_distance, \
                                            noise_mu = noise_mu, \
                                            noise_sigma=noise_sigma, \
                                            laser_mirror_distance=laser_mirror_distance, \
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








"""
    rays_buffer = (ctypes.c_float * len(rays))()
    for idx in range(len(rays)):
        struct.pack_into("f",rays_buffer, idx*4, rays[idx])


    ELEMENTS_PER_RETURN = 5
    returns_buffer = (ctypes.c_float * ((len(rays)//3) * ELEMENTS_PER_RETURN))()
   
    print ("Raycount: ", len(rays)//3)
    rays_low = (ctypes.addressof(rays_buffer)%(2**16))
    rays_high = (ctypes.addressof(rays_buffer)//(2**16))
    returns_low = (ctypes.addressof(returns_buffer)%(2**16))
    returns_high = (ctypes.addressof(returns_buffer)//(2**16))
    
    returns_buffer_uint = ctypes.cast(returns_buffer, ctypes.POINTER(ctypes.c_uint))

    bpy.ops.render.blensor(raycount = len(rays)//3, rays_ptr_low = rays_low, rays_ptr_high = rays_high, returns_ptr_low = returns_low, returns_ptr_high = returns_high )
"""







