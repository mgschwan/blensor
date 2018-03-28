#Range according to wikipedia
# 700 mm to 6000 mm
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
import numpy
import blensor.globals
import blensor.scan_interface
from blensor import evd
from blensor import mesh_utils
from blensor import kinect_dots

"""Highly experimental. Just a quick hack for alexandru"""
from blensor.noise import PerlinNoise
"""---------"""  


WINDOW_INLIER_DISTANCE = 0.1

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

INVALID_DISPARITY = 99999999.9


parameters = {"max_dist":6.0,"min_dist": 0.7, "noise_mu":0.0,"noise_sigma":0.0,  
              "xres": 640, "yres": 480, "flength": 4.73, "reflectivity_distance":0.0,
              "reflectivity_limit":0.01,"reflectivity_slope":0.16, "noise_scale": 0.25, "noise_smooth":1.5,
              "inlier_distance": 0.05, "vert_fov":43.1845, "horiz_fov":55.6408 }

def addProperties(cType):
    global parameters
    cType.kinect_max_dist = bpy.props.FloatProperty( name = "Scan distance (max)", default = parameters["max_dist"], min = 0, max = 1000, description = "How far the kinect can see" )
    cType.kinect_min_dist = bpy.props.FloatProperty( name = "Scan distance (min)", default = parameters["min_dist"], min = 0, max = 1000, description = "How close the kinect can see" )
    cType.kinect_noise_mu = bpy.props.FloatProperty( name = "Noise mu", default = parameters["noise_mu"], description = "The center of the gaussian noise" )
    cType.kinect_noise_sigma = bpy.props.FloatProperty( name = "Noise sigma", default = parameters["noise_sigma"], description = "The sigma of the gaussian noise" )
    cType.kinect_xres = bpy.props.IntProperty( name = "X resolution", default = parameters["xres"], description = "Horizontal resolution" )
    cType.kinect_yres = bpy.props.IntProperty( name = "Y resolution", default = parameters["yres"], description = "Vertical resolution" )

    cType.kinect_flength = bpy.props.FloatProperty( name = "Focal length", default = parameters["flength"], description = "Focal length in mm" )
    cType.kinect_enable_window = bpy.props.BoolProperty( name = "Enable 9x9", default = False, description = "Valid measurements require a 9x9 window of returns" )

    cType.kinect_ref_dist = bpy.props.FloatProperty( name = "Reflectivity Distance", default = parameters["reflectivity_distance"], description = "Objects closer than reflectivity distance are independent of their reflectivity" )
    cType.kinect_ref_limit = bpy.props.FloatProperty( name = "Reflectivity Limit", default = parameters["reflectivity_limit"], description = "Minimum reflectivity for objects at the reflectivity distance" )
    cType.kinect_ref_slope = bpy.props.FloatProperty( name = "Reflectivity Slope", default = parameters["reflectivity_slope"], description = "Slope of the reflectivity limit curve" )

    cType.kinect_noise_smooth = bpy.props.FloatProperty( name = "Global Noise Smoothness", default = parameters["noise_smooth"], min = 1.0, max = 100.0, description = "Smoothness of the global noise (higher values are smoother" )
    cType.kinect_noise_scale = bpy.props.FloatProperty( name = "Global Noise Scale", default = parameters["noise_scale"], min = 0.0, max = 10.0, description = "Strength of the global noise" )
    cType.kinect_inlier_distance = bpy.props.FloatProperty( name = "Inlier Distance", default = parameters["inlier_distance"], min = 0.0, max = 10.0, description = "Which points are considered valid for the 9x9 window" )


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


"""This checks a 9x9 window around the point in idx if the depth values
   would allow the kinect to do a correct matching. If for example some
   value would be missing, the kinect could not match the image to the
   projector pattern
   #TODO: determine how big the depth-difference can be to still produce a
   valid depth measurement. Note: This has to be verified by a real kinect
"""
    
def fast_9x9_window(distances, res_x, res_y, disparity_map, noise_smooth, noise_scale):
  data = distances.reshape(res_y, res_x)
  disp_data = disparity_map.reshape(res_y, res_x)
  disp_data[:] = INVALID_DISPARITY
  
  """Highly experimental. Just a quick hack for alexandru"""
  pnoise = PerlinNoise(size=(res_x,res_y))
  #It is important to reshape it exactly as it was generated (w,h)
  noise_field = (pnoise.getData(scale=32.0)-1.0).reshape((res_x,res_y)) 
  """-------------"""

  
  weights = numpy.array([1.0/float((1.2*x)**2+(1.2*y)**2) if x!=0 or y!=0 else 1.0 for x in range(-4,5) for y in range (-4,5)]).reshape((9,9))

  """We don't want to fill the whole 9x9 region with the current disparity
     this fills too much gaps in the depthmap
  """
  fill_weights = numpy.array([1.0/(1.0+float(x**2+y**2)) if math.sqrt(x**2+y**2)<3.1 else -1.0 for x in range(-4,5) for y in range (-4,5)]).reshape((9,9))
  
  interpolation_map = numpy.zeros((res_y,res_x))
    
  for y in range(min(kinect_dots.mask.shape[0]-9, data.shape[0]-9)):
    for x in range(min(kinect_dots.mask.shape[1]-9,data.shape[1]-9)):
      if kinect_dots.mask[y+4,x+4] and data[y+4,x+4] < INVALID_DISPARITY:
        window = data[y:y+9,x:x+9]
        dot_window = kinect_dots.mask[y:y+9,x:x+9]
        valid_values = window < INVALID_DISPARITY
        valid_dots = valid_values&dot_window
        if numpy.sum(valid_dots) > numpy.sum(dot_window)/1.5:
          mean = numpy.sum(window[valid_values])/numpy.sum(valid_values)
          differences = numpy.abs(window-mean)*weights

          valids = (differences<WINDOW_INLIER_DISTANCE) & valid_dots
            
          pointcount = numpy.sum(weights[valids])
          if numpy.sum(valids) > numpy.sum(dot_window)/1.5:
            accu = window[4,4]
            
            disp_data[y+4,x+4] = round((accu + noise_scale*
                noise_field[numpy.int32((x+4)/noise_smooth),numpy.int32((y+4)/noise_smooth)])*8.0)/8.0
            #round(accu*8.0)/8.0 #Values need to be requantified
            
            interpolation_window = interpolation_map[y:y+9,x:x+9]
            disp_data_window = disp_data[y:y+9,x:x+9]
            substitutes = interpolation_window < fill_weights
            disp_data_window[substitutes] = disp_data[y+4,x+4]
            interpolation_window[substitutes] = fill_weights[substitutes]

def scan_advanced(scanner_object, evd_file=None, 
                  evd_last_scan=True, 
                  timestamp = 0.0,
                  world_transformation=Matrix()):


    # threshold for comparing projector and camera rays
    thresh = 0.01

    inv_scan_x = scanner_object.inv_scan_x
    inv_scan_y = scanner_object.inv_scan_y
    inv_scan_z = scanner_object.inv_scan_z 

    x_multiplier = -1.0 if inv_scan_x else 1.0
    y_multiplier = -1.0 if inv_scan_y else 1.0
    z_multiplier = -1.0 if inv_scan_z else 1.0

    start_time = time.time()

    max_distance = scanner_object.kinect_max_dist
    min_distance = scanner_object.kinect_min_dist
    add_blender_mesh = scanner_object.add_scan_mesh
    add_noisy_blender_mesh = scanner_object.add_noise_scan_mesh
    noise_mu = scanner_object.kinect_noise_mu
    noise_sigma = scanner_object.kinect_noise_sigma                
    noise_scale = scanner_object.kinect_noise_scale
    noise_smooth = scanner_object.kinect_noise_smooth                
    res_x = scanner_object.kinect_xres 
    res_y = scanner_object.kinect_yres
    flength = scanner_object.kinect_flength
    WINDOW_INLIER_DISTANCE = scanner_object.kinect_inlier_distance


    if res_x < 1 or res_y < 1:
        raise ValueError("Resolution must be > 0")

        


    pixel_width = max(0.0001, (
        math.tan((parameters["horiz_fov"]/2.0)*math.pi/180.0)*flength)/max(1.0,res_x/2.0))   #default:0.0078
    pixel_height = max(0.0001, (
        math.tan((parameters["vert_fov"]/2.0)*math.pi/180.0)*flength)/max(1.0,res_y/2.0))   #default:0.0078
    print ("%f,%f"%(pixel_width,pixel_height))
    cx = float(res_x) /2.0
    cy = float(res_y) /2.0 

    evd_buffer = []

    rays = [0.0]*res_y*res_x*6
    ray_info = [[0.0,0.0,0.0]]*res_y*res_x

    baseline = Vector([0.075,0.0,0.0]) #Kinect has a baseline of 7.5 centimeters


    
    rayidx=0
    ray = Vector([0.0,0.0,0.0])
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

            #ray = Vector([physical_x, physical_y, physical_z])
            ray.xyz=[physical_x, physical_y, physical_z]
            ray.normalize()
            final_ray = max_distance*ray
            rays[rayidx*6] = final_ray[0]
            rays[rayidx*6+1] = final_ray[1]
            rays[rayidx*6+2] = final_ray[2]
            rays[rayidx*6+3] = baseline.x
            rays[rayidx*6+4] = baseline.y
            rays[rayidx*6+5] = baseline.z

            """ pitch and yaw are added for completeness, normally they are
                not provided by a ToF Camera but can be derived 
                from the pixel position and the camera parameters.
            """
            yaw = math.atan(physical_x/flength)
            pitch = math.atan(physical_y/flength)
            ray_info[rayidx][0] = yaw
            ray_info[rayidx][1] = pitch
            ray_info[rayidx][2] = timestamp

            rayidx += 1

    """ Max distance is increased because the kinect is limited by 4m
        _normal distance_ to the imaging plane, We don't need shading in the
        first pass. 
        #TODO: the shading requirements might change when transmission
        is implemented (the rays might pass through glass)
    """
    returns = blensor.scan_interface.scan_rays(rays, 2.0*max_distance, True,True,True,True)

    camera_rays = []
    projector_ray_index = -1 * numpy.ones(len(returns), dtype=numpy.uint32)

    kinect_image = numpy.zeros((res_x*res_y,16))
    kinect_image[:,3:11] = float('NaN')
    kinect_image[:,11] = -1.0
    """Calculate the rays from the camera to the hit points of the projector rays"""
    for i in range(len(returns)):
        idx = returns[i][-1]
        kinect_image[idx,12:15] = returns[i][5]

        if returns[i][0] < max_distance:
          camera_rays.extend([returns[i][1]+baseline.x, returns[i][2]+baseline.y, 
                            returns[i][3]+baseline.z])
          projector_ray_index[i] = idx


    camera_returns = blensor.scan_interface.scan_rays(camera_rays, 2*max_distance, False,False,False)
    
    evd_storage = evd.evd_file(evd_file, res_x, res_y, max_distance)

    all_quantized_disparities = numpy.empty(res_x*res_y)
    all_quantized_disparities[:] = INVALID_DISPARITY
    
    disparity_weight = numpy.empty(res_x*res_y)
    disparity_weight[:] = INVALID_DISPARITY

    all_quantized_disp_mat = all_quantized_disparities.reshape(res_y,res_x)
    disp_weight_mat = disparity_weight.reshape(res_y,res_x)

    weights = numpy.array([1.0/float((1.2*x)**2+(1.2*y)**2) if x!=0 or y!=0 else 1.0 for x in range(-4,5) for y in range (-4,5)]).reshape((9,9))
    
    """Build a quantized disparity map"""
    for i in range(len(camera_returns)):
        idx = camera_returns[i][-1] 
        projector_idx = projector_ray_index[idx] # Get the index of the original ray

        if (abs(camera_rays[idx*3]-camera_returns[i][1]) < thresh and
            abs(camera_rays[idx*3+1]-camera_returns[i][2]) < thresh and
            abs(camera_rays[idx*3+2]-camera_returns[i][3]) < thresh and
            abs(camera_returns[i][3]) <= max_distance and
            abs(camera_returns[i][3]) >= min_distance):
            """The ray hit the projected ray, so this is a valid measurement"""
            projector_point = get_uv_from_idx(projector_idx, res_x,res_y)

            camera_x = get_pixel_from_world(camera_rays[idx*3],camera_rays[idx*3+2],
                                   flength/pixel_width) + random.gauss(noise_mu, noise_sigma)

            camera_y = get_pixel_from_world(camera_rays[idx*3+1],camera_rays[idx*3+2],
                                   flength/pixel_width)

            """ Kinect calculates the disparity with an accuracy of 1/8 pixel"""

            camera_x_quantized = round(camera_x*8.0)/8.0
            
            #I don't know if this accurately represents the kinect 
            camera_y_quantized = round(camera_y*8.0)/8.0 

            disparity_quantized = camera_x_quantized + projector_point[0]
            if projector_idx >= 0: 
              all_quantized_disparities[projector_idx] = disparity_quantized
        
    processed_disparities = numpy.empty(res_x*res_y)
    fast_9x9_window(all_quantized_disparities, res_x, res_y, processed_disparities, noise_smooth, noise_scale)
    
    """We reuse the vector objects to spare us the object creation every
       time
    """
    v = Vector([0.0,0.0,0.0])
    vn = Vector([0.0,0.0,0.0])
    """Check if the rays of the camera meet with the rays of the projector and
       add them as valid returns if they do"""
    image_idx = 0
    
    
    for i in range(len(camera_returns)):
        idx = camera_returns[i][-1] 
        projector_idx = projector_ray_index[idx] # Get the index of the original ray
        camera_x,camera_y = get_uv_from_idx(projector_idx, res_x,res_y)

        if projector_idx >= 0:
          disparity_quantized = processed_disparities[projector_idx] 
        else:
          disparity_quantized = INVALID_DISPARITY
        
        if disparity_quantized < INVALID_DISPARITY and disparity_quantized != 0.0:
            disparity_quantized = -disparity_quantized
            Z_quantized = (flength*(baseline.x))/(disparity_quantized*pixel_width)
            X_quantized = baseline.x+Z_quantized*camera_x*pixel_width/flength
            Y_quantized = baseline.y+Z_quantized*camera_y*pixel_width/flength
            Z_quantized = -(Z_quantized+baseline.z)
            
            v.xyz=[x_multiplier*(returns[idx][1]+baseline.x),\
                   y_multiplier*(returns[idx][2]+baseline.y),\
                   z_multiplier*(returns[idx][3]+baseline.z)]
            vector_length = math.sqrt(v[0]**2+v[1]**2+v[2]**2)

            vt = (world_transformation * v.to_4d()).xyz

            vn.xyz = [x_multiplier*X_quantized,y_multiplier*Y_quantized,z_multiplier*Z_quantized]
            vector_length_noise = vn.magnitude
            
            #TODO@mgschwan: prevent object creation here too
            v_noise = (world_transformation * vn.to_4d()).xyz 
             
            kinect_image[projector_idx] = [ray_info[projector_idx][2], 
               0.0, 0.0, -returns[idx][3], -Z_quantized, vt[0], 
               vt[1], vt[2], v_noise[0], v_noise[1], v_noise[2], 
               returns[idx][4], returns[idx][5][0], returns[idx][5][1],
               returns[idx][5][2],projector_idx]
            image_idx += 1
        else:
          """Occlusion"""
          pass

    for e in kinect_image:
      evd_storage.addEntry(timestamp = e[0], yaw = e[1], pitch=e[2], 
        distance=e[3], distance_noise=e[4], x=e[5], y=e[6], z=e[7], 
        x_noise=e[8], y_noise=e[9], z_noise=e[10], object_id=e[11], 
        color=[e[12],e[13],e[14]], idx=e[15])
        

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



