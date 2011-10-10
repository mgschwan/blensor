import math
import sys
import os
import struct 
import ctypes
import time
import random
import bpy
from mathutils import Vector, Euler


"""The number of elements per return depends on the version of the blensor
   patch
"""
ELEMENTS_PER_RETURN = 5



def scan_rays(rays, max_distance):

    rays_buffer = (ctypes.c_float * len(rays))()
    for idx in range(len(rays)):
        struct.pack_into("f",rays_buffer, idx*4, rays[idx])


    returns_buffer = (ctypes.c_float * ((len(rays)//3) * ELEMENTS_PER_RETURN))()
   
    print ("Raycount: ", len(rays)//3)
    rays_low = (ctypes.addressof(rays_buffer)%(2**16))
    rays_high = (ctypes.addressof(rays_buffer)//(2**16))
    returns_low = (ctypes.addressof(returns_buffer)%(2**16))
    returns_high = (ctypes.addressof(returns_buffer)//(2**16))
    
    returns_buffer_uint = ctypes.cast(returns_buffer, ctypes.POINTER(ctypes.c_uint))

    bpy.ops.render.blensor(raycount = len(rays)//3, rays_ptr_low = rays_low, rays_ptr_high = rays_high, returns_ptr_low = returns_low, returns_ptr_high = returns_high , maximum_distance = max_distance)
    

    array_of_returns = []

    for idx in range((len(rays)//3)):
        if returns_buffer[idx*ELEMENTS_PER_RETURN] < max_distance and returns_buffer[idx*ELEMENTS_PER_RETURN]>0.0 :
            #The ray may have been reflecten and refracted. But the laser
            #does not know that so we need to calculate the point which
            #is the measured distance away from the sensor but without
            #beeing reflected/refracted. We use the original ray direction
            vec = [float(rays[idx*3]), 
                   float(rays[idx*3+1]),
                   float(rays[idx*3+2])]
            veclen = math.sqrt(vec[0]**2+vec[1]**2+vec[2]**2)
            raydistance = float(returns_buffer[idx*ELEMENTS_PER_RETURN])
            vec[0] = raydistance * vec[0]/veclen
            vec[1] = raydistance * vec[1]/veclen
            vec[2] = raydistance * vec[2]/veclen


            ret = [ float(returns_buffer[e + idx*ELEMENTS_PER_RETURN]) for e in range(ELEMENTS_PER_RETURN-1) ]            
            ret[1] = vec[0]
            ret[2] = vec[1]
            ret[3] = vec[2]
            ret.append(returns_buffer_uint[idx*ELEMENTS_PER_RETURN+4]) #objectid
            ret.append(idx) # Store the index per return as the last element
            array_of_returns.append(ret)

    return array_of_returns
    

