import math
import sys
import traceback
import os
import struct 
import ctypes
import time
import random
import bpy
from mathutils import Vector, Euler
import blensor.scan_interface_pure

try:
    import blensorintern
except:
    print ("Warning: This blender version does not have native Blensor support. Some methods may not work")
    blensorintern = None


"""The number of elements per return depends on the version of the blensor
   patch
"""
ELEMENTS_PER_RETURN = 8
SIZEOF_FLOAT = 4

""" rays is an array of vectors that describe the laser direction and also the
         ray origin if the ray_origin field is setp
    max_distance is a float that determines the maximum distance a ray can travel
    keep_render_setup is passed to the blender internal code to keep the renderer
    setup for additional calls
"""
def scan_rays(rays, max_distance, ray_origins=False, keep_render_setup=False, do_shading=True, return_all = False, inv_scan_x = False, inv_scan_y = False, inv_scan_z = False):

    elementsPerRay = 3
    if ray_origins == True:
      elementsPerRay = 6
  
    numberOfRays = int(len(rays)/elementsPerRay)


    rays_buffer = (ctypes.c_float * numberOfRays*elementsPerRay)()
    struct.pack_into("%df"%(numberOfRays*elementsPerRay), rays_buffer, 0, *rays[:numberOfRays*elementsPerRay])

    returns_buffer = (ctypes.c_float * (numberOfRays * ELEMENTS_PER_RETURN))()
   
    print ("Raycount: ", numberOfRays)
    
    returns_buffer_uint = ctypes.cast(returns_buffer, ctypes.POINTER(ctypes.c_uint))

    array_of_returns = []
    if True:
    #try:
      if blensorintern:
          blensorintern.scan(numberOfRays, max_distance, elementsPerRay, keep_render_setup, do_shading,                 
                "%016X"%(ctypes.addressof(rays_buffer)), "%016X"%(ctypes.addressof(returns_buffer)))
      else:
          blensor.scan_interface_pure.scan(numberOfRays, max_distance, elementsPerRay, keep_render_setup, do_shading,                 
                rays, returns_buffer, ELEMENTS_PER_RETURN)


      x_multiplier = -1.0 if inv_scan_x else 1.0
      y_multiplier = -1.0 if inv_scan_y else 1.0
      z_multiplier = -1.0 if inv_scan_z else 1.0

      print ("X: %f Y: %f Z: %f"%(x_multiplier,y_multiplier,z_multiplier))

      for idx in range(numberOfRays):
          if return_all or (returns_buffer[idx*ELEMENTS_PER_RETURN] < max_distance and returns_buffer[idx*ELEMENTS_PER_RETURN]>0.0 ):
              ret = [ float(returns_buffer[e + idx*ELEMENTS_PER_RETURN]) for e in range(4) ]            
              ret[1] = float('NaN')
              ret[2] = float('NaN')
              ret[3] = float('NaN')
              
              if returns_buffer[idx*ELEMENTS_PER_RETURN] > 0.0:
                #The ray may have been reflected and refracted. But the laser
                #does not know that so we need to calculate the point which
                #is the measured distance away from the sensor but without
                #beeing reflected/refracted. We use the original ray direction
                vec = [float(rays[idx*elementsPerRay]), 
                       float(rays[idx*elementsPerRay+1]),
                       float(rays[idx*elementsPerRay+2])]
                veclen = math.sqrt(vec[0]**2+vec[1]**2+vec[2]**2)
                raydistance = float(returns_buffer[idx*ELEMENTS_PER_RETURN])
                vec[0] = x_multiplier * raydistance * vec[0]/veclen
                vec[1] = y_multiplier * raydistance * vec[1]/veclen
                vec[2] = z_multiplier * raydistance * vec[2]/veclen


                ret[1] = vec[0]
                ret[2] = vec[1]
                ret[3] = vec[2]
              ret.append(returns_buffer_uint[idx*ELEMENTS_PER_RETURN+4]) #objectid
              ret.append((returns_buffer[idx*ELEMENTS_PER_RETURN+5],
                          returns_buffer[idx*ELEMENTS_PER_RETURN+6],
                          returns_buffer[idx*ELEMENTS_PER_RETURN+7])) # RGB Value of the material
              ret.append(idx) # Store the index per return as the last element
              array_of_returns.append(ret)
    #except TypeError as e:
    #  exc_type, exc_value, exc_traceback = sys.exc_info()
    #  traceback.print_tb(exc_traceback)
    #finally:
    #  del rays_buffer
    #  del returns_buffer

    return array_of_returns
    

