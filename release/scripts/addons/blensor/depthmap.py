#TODO: Support different aspect ratios

import math
import sys
import os
import struct 
import ctypes
import time
import random
import bpy
import blensor.globals
from mathutils import Vector, Euler, Matrix


parameters = {"max_dist":200}

def addProperties(cType):
    global parameters
    cType.depthmap_max_dist = bpy.props.FloatProperty( name = "Scan distance", default = parameters["max_dist"], min = 0, max = 1000, description = "How far the laser can see" )




def deg2rad(deg):
    return deg*math.pi/180.0

def rad2deg(rad):
    return rad*180.0/math.pi

def tuples_to_list(tuples):
    l = []
    for t in tuples:
        l.extend(t)
    return l


def scan_advanced(max_distance = 120, filename=None, add_blender_mesh = False,
    world_transformation=Matrix()):
    start_time = time.time()


    bpy.context.scene.render.resolution_percentage=100
    bpy.context.scene.render.use_antialiasing=False
    width = bpy.context.scene.render.resolution_x
    height = bpy.context.scene.render.resolution_y
    cx = float(bpy.context.scene.render.resolution_x) /2.0
    cy = float(bpy.context.scene.render.resolution_y) /2.0 



    flength = 35 #millimeters
    if bpy.context.scene.camera.data.lens_unit == "MILLIMETERS":
        flength = bpy.context.scene.camera.data.lens
    else:
        print ("Lens unit has to be millimeters")
        return False, 0.0,0.0

    focal_length = flength * blensor.globals.getPixelPerMillimeter(width,height)

    bpy.ops.render.render()

    zbuffer = bpy.data.images["Render Result"].zbuf()
    depthmap = [0.0]*len(zbuffer)

    verts = []

    reusable_vector = Vector([0.0,0.0,0.0,0.0])
    for idx in range( len(zbuffer) ):
            x = float(idx % width)
            y = float(idx // width)
            dx = x - cx
            dy = y - cy

            ddist = math.sqrt(dx**2 + dy**2)
            

            world_ddist = ( ddist * zbuffer[idx] ) / focal_length


            object_distance =  math.sqrt(world_ddist ** 2 + zbuffer[idx] ** 2)
            
            depthmap[idx] = object_distance
            if add_blender_mesh:
                if object_distance < max_distance:
                    Z = -zbuffer[idx] 
                    X = -( Z * dx ) / focal_length
                    Y = -( Z * dy ) / focal_length
                    reusable_vector.xyzw = [X,Y,Z,1.0]
                    vt = (world_transformation * reusable_vector).xyz

                    verts.append(vt[0])                
                    verts.append(vt[1])
                    verts.append(vt[2])


    if filename:
        fh = open(filename, "w")
        fh.buffer.write(struct.pack("ii",width,height))
        for idx in range( width*height ):
            fh.buffer.write(struct.pack("d", depthmap[idx]))
        fh.close()

    if add_blender_mesh:
        scan_mesh = bpy.data.meshes.new("scan_mesh")
        scan_mesh.vertices.add(len(verts)//3)
        scan_mesh.vertices.foreach_set("co", verts)
        scan_mesh.update()
        scan_mesh_object = bpy.data.objects.new("Scan.{0}".format(bpy.context.scene.frame_current), scan_mesh)
        bpy.context.scene.objects.link(scan_mesh_object)
        blensor.show_in_frame(scan_mesh_object, bpy.context.scene.frame_current)

        if world_transformation == Matrix():
            scan_mesh_object.matrix_world = bpy.context.object.matrix_world



    bpy.context.scene.update()

    end_time = time.time()
    scan_time = end_time-start_time
    print ("Elapsed time: %.3f"%(scan_time))

    return True, 0.0, scan_time






# This Function creates scans over a range of frames

def scan_range(frame_start, frame_end, filename="/tmp/depthmap", frame_time = (1.0/24.0), fps = 24, add_blender_mesh=False, max_distance = 120.0, last_frame = True,world_transformation=Matrix()):

    start_time = time.time()

    time_per_frame = 1.0 / float(fps)

    try:
        for i in range(frame_start,frame_end):

            bpy.context.scene.frame_current = i

            ok,start_radians,scan_time = scan_advanced(filename = filename+"%04d.dmap"%i , add_blender_mesh=add_blender_mesh,  max_distance=max_distance,world_transformation=world_transformation)

            if not ok:
                break
    except:
        print ("Scan aborted")

    end_time = time.time()
    print ("Total scan time: %.2f"%(end_time-start_time))



######################################################



