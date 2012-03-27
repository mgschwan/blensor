import math
import sys
import os
import struct 
import ctypes
import time
import random
import bpy
from mathutils import Vector, Euler, Matrix

from blensor import evd
import blensor


def tuples_to_list(tuples):
    l = []
    for t in tuples:
        l.extend(t)
    return l


# Creates and adds a mesh_object from a set of points or from a flattened 
# list
def add_mesh_from_points(points, name="mesh"):
    flattened = points

    if len(points) > 0:
        if type(points[0]) == type([]) or type(points[0]) == type(()):
            flattened = tuples_to_list(points)            

    mesh = bpy.data.meshes.new(name+"_mesh")
    mesh.vertices.add(len(flattened)//3)
    mesh.vertices.foreach_set("co",flattened)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.objects.link(obj)

"""Add a mesh from points or from a flattened list and transform it according to
   world_transformation, or according to the transformation of the camera
"""
def add_mesh_from_points_tf(points, name="Scan", world_transformation = Matrix()):
    mesh = bpy.data.meshes.new(name+"_mesh")
    mesh.vertices.add(len(points))
    mesh.vertices.foreach_set("co", tuples_to_list(points))
    mesh.update()
    mesh_object = bpy.data.objects.new("{0}.{1}".format(name,bpy.context.scene.frame_current), mesh)
    bpy.context.scene.objects.link(mesh_object)
    blensor.show_in_frame(mesh_object, bpy.context.scene.frame_current)
    
    if world_transformation == Matrix():
       mesh_object.matrix_world = bpy.context.object.matrix_world



