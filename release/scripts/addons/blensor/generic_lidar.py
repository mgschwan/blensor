#Generic LIDAR scanner
#Preconfigured for the Hokuyo UTM-30LX 
#according to http://de.manu-systems.com/UTM-30LX_spec.pdf
#HFOV: 270° (-135 / 135)
#Angular resolution 0.25°
#Max dist 30m
#Speed: 40Hz
#Noise is not yet correctly modified
#TODO: Accuracy based on range
#TODO: Accuracy based on illumination

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
from blensor import advanced_error_model
from blensor import gaussian_error_model


from blensor import evd
from blensor import mesh_utils

import blensor

parameters = {"angle_resolution":0.25, "rotation_speed":40,"max_dist":30,"noise_mu":0.0,"noise_sigma":0.03,
              "start_angle":-135.0,"end_angle":135.0,
              "reflectivity_distance":50,"reflectivity_limit":0.1,"reflectivity_slope":0.005333333,
              "laser_angles":"0.0", "advanced_error_model":""}

def addProperties(cType):
    global parameters
    cType.generic_angle_resolution = bpy.props.FloatProperty( name = "Scanresolution", default = parameters["angle_resolution"], min = 0.01, max = 3.141, description = "How far(angle) two scan lines are apart" )
    cType.generic_rotation_speed = bpy.props.FloatProperty( name = "Rotation speed", default = parameters["rotation_speed"], min = 1, max = 100, description = "Rotation speed in Hertz" )
    cType.generic_max_dist = bpy.props.FloatProperty( name = "Scan distance", default = parameters["max_dist"], min = 0, max = 1000, description = "How far the laser can see" )
    cType.generic_noise_mu = bpy.props.FloatProperty( name = "Noise mu", default = parameters["noise_mu"], description = "The center of the gaussian noise" )
    cType.generic_noise_sigma = bpy.props.FloatProperty( name = "Noise sigma", default = parameters["noise_sigma"], description = "The sigma of the gaussian noise" )
    cType.generic_start_angle = bpy.props.FloatProperty( name = "Start angle", default = parameters["start_angle"], description = "The angle at which the scan is started" )
    cType.generic_end_angle = bpy.props.FloatProperty( name = "End angle", default = parameters["end_angle"], description = "The angle at which the scan is stopped" )

    cType.generic_ref_dist = bpy.props.FloatProperty( name = "Reflectivity Distance", default = parameters["reflectivity_distance"], description = "Objects closer than reflectivity distance are independent of their reflectivity" )
    cType.generic_ref_limit = bpy.props.FloatProperty( name = "Reflectivity Limit", default = parameters["reflectivity_limit"], description = "Minimum reflectivity for objects at the reflectivity distance" )
    cType.generic_ref_slope = bpy.props.FloatProperty( name = "Reflectivity Slope", default = parameters["reflectivity_slope"], description = "Slope of the reflectivity limit curve" )
    cType.generic_laser_angles = bpy.props.StringProperty( name = "Laser angles", default = parameters["laser_angles"], description = "Comma separated list of vertical angles" )
    cType.generic_advanced_error_model = bpy.props.StringProperty( name = "Advanced Error Model", default = parameters["advanced_error_model"], description = "List of (distance, mu, sigma) tuples, leave empty if standard error model is used" )




def deg2rad(deg):
    return deg*math.pi/180.0

def rad2deg(rad):
    return rad*180.0/math.pi

def tuples_to_list(tuples):
    l = []
    for t in tuples:
        l.extend(t)
    return l



laser_noise = [0.015798891682948433] #Preset, can be changed
  

## If the laser noise has to be truely randomize, call this function prior
## to every scan
def randomize_distance_bias(num_lasers, noise_mu = 0.0, noise_sigma = 0.04):
    global laser_noise
    if num_lasers != len(laser_noise):
      laser_noise = [0.0 for i in range(num_lasers)]
      
    for idx in range(num_lasers):
      laser_noise[idx] = random.gauss(noise_mu, noise_sigma)


def angles_from_string(angle_string):
  angles = []
  try:
    angles = [float(val) for val in angle_string.split(",")] 
  except:
    print ("Could not create angle list in generic LIDAR")
  return angles

def scan_advanced(scanner_object, simulation_fps=24, evd_file=None,noise_mu=0.0, evd_last_scan=True, add_blender_mesh = False, add_noisy_blender_mesh = False, simulation_time = 0.0,laser_mirror_distance=0.05, world_transformation=Matrix()):
    
    
    angle_resolution=scanner_object.generic_angle_resolution
    max_distance=scanner_object.generic_max_dist
    start_angle=scanner_object.generic_start_angle
    end_angle=scanner_object.generic_end_angle
    noise_mu = scanner_object.generic_noise_mu
    noise_sigma=scanner_object.generic_noise_sigma
    laser_angles = scanner_object.generic_laser_angles
    rotation_speed = scanner_object.generic_rotation_speed

    inv_scan_x = scanner_object.inv_scan_x
    inv_scan_y = scanner_object.inv_scan_y
    inv_scan_z = scanner_object.inv_scan_z    

    """Standard Error model is a Gaussian Distribution"""
    model = gaussian_error_model.GaussianErrorModel(noise_mu, noise_sigma)
    if scanner_object.generic_advanced_error_model:
      """Advanced error model is a list of distance,mu,sigma tuples"""
      model = advanced_error_model.AdvancedErrorModel(scanner_object.generic_advanced_error_model)


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

    laser_angles = angles_from_string(laser_angles)


    rays = []
    ray_info = []

    #Bad code???
    #steps_per_rotation = 360.0/angle_resolution
    #time_per_step = (1.0 / rotation_speed) / steps_per_rotation
    #angles = end_angle-start_angle
  
    lines = (end_angle-start_angle)/angle_resolution
    ray = Vector([0.0,0.0,0.0])
    for line in range(int(lines)):
        for laser_idx in range(len(laser_angles)):
            ray.xyz = [0,0,max_distance]
            rot_angle = 1e-6 + start_angle+float(line)*angle_resolution + 180.0
            timestamp = ( (rot_angle-180.0)/angle_resolution) * time_per_step 
            rot_angle = rot_angle%360.0
            ray_info.append([deg2rad(rot_angle), deg2rad(laser_angles[laser_idx]), timestamp])
            
            rotator = Euler( [deg2rad(-laser_angles[laser_idx]), deg2rad(rot_angle), 0.0] )
            ray.rotate( rotator )
            rays.extend([ray[0],ray[1],ray[2]])


    returns = blensor.scan_interface.scan_rays(rays, max_distance, inv_scan_x = inv_scan_x, inv_scan_y = inv_scan_y, inv_scan_z = inv_scan_z)

    reusable_vector = Vector([0.0,0.0,0.0,0.0])
    if len(laser_angles) != len(laser_noise):
      randomize_distance_bias(len(laser_angles), noise_mu,noise_sigma)
      
    for i in range(len(returns)):
        idx = returns[i][-1]
        reusable_vector.xyzw = [returns[i][1],returns[i][2],returns[i][3],1.0]
        vt = (world_transformation * reusable_vector).xyz
        v = [returns[i][1],returns[i][2],returns[i][3]]

        vector_length = math.sqrt(v[0]**2+v[1]**2+v[2]**2)
        distance_noise =  laser_noise[idx%len(laser_noise)] + model.drawErrorFromModel(vector_length) 
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

def scan_range(scanner_object, frame_start, frame_end, filename="/tmp/landscape.evd", frame_time = (1.0/24.0),  fps = 24, add_blender_mesh=False, add_noisy_blender_mesh=False, last_frame = True, world_transformation=Matrix()):


    angle_resolution=scanner_object.generic_angle_resolution
    max_distance=scanner_object.generic_max_dist
    start_angle=scanner_object.generic_start_angle
    end_angle=scanner_object.generic_end_angle
    noise_mu = scanner_object.generic_noise_mu
    noise_sigma=scanner_object.generic_noise_sigma
    laser_angles = scanner_object.generic_laser_angles
    rotation_speed = scanner_object.generic_rotation_speed

    fps = rotation_speed # Todo this module does not yet support an update
                         # rate different to the simulation speed
    start_time = time.time()

    time_per_frame = 1.0 / float(fps)

    try:
        for i in range(frame_start,frame_end):

                bpy.context.scene.frame_current = i

                ok,start_radians,scan_time = scan_advanced(scanner_object=scanner_object, evd_file = filename, evd_last_scan=False,add_blender_mesh=add_blender_mesh, add_noisy_blender_mesh=add_noisy_blender_mesh, simulation_time = float(i)*frame_time,  world_transformation=world_transformation)

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





