import bpy
from bpy import data as D
from bpy import context as C
from mathutils import *
from math import *

import blensor

"""If the scanner is the default camera it can be accessed for example by bpy.data.objects["Camera"]"""
scanner = bpy.data.objects["Camera"]

"""Move it to a different location"""
scanner.location = (0,0,0)

"""Scan the scene with the Velodyne scanner and save it to the file "/tmp/scan.pcd"
   Note: The data will actually be saved to /tmp/scan00000.pcd and /tmp/scan_noisy00000.pcd
"""
blensor.blendodyne.scan_advanced(scanner, rotation_speed = 10.0, simulation_fps=24, angle_resolution = 0.1728, max_distance = 120, evd_file= "/tmp/scan1.pcd",noise_mu=0.0, noise_sigma=0.03, start_angle = 0.0, end_angle = 360.0, evd_last_scan=True, add_blender_mesh = False, add_noisy_blender_mesh = False)

