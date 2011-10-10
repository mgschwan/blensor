# Laser Information
# Velodyne HDL-64E S2
# Wavelength: 905 nm
# Pulselength: 5 nanoseconds
# Angular resolution: 0.09 degree
# Distance accuracy (sigma): 2cm
# Range: 50m (~0.1 reflectivity), 120m (~0.8 reflectivity)


import math
import sys
import os
import struct 
import ctypes
import time
import random
import bpy
from mathutils import Vector, Euler

from blensor import evd
import blensor


parameters = {"angle_resolution":0.1728, "rotation_speed":10,"max_dist":120,"noise_mu":0.0,"noise_sigma":0.01,
              "start_angle":0,"end_angle":360, "distance_bias_noise_mu": 0, "distance_bias_noise_sigma": 0.06,
              "reflectivity_distance":50,"reflectivity_limit":0.1,"reflectivity_slope":0.01}

def addProperties(cType):
    global parameters
    cType.velodyne_angle_resolution = bpy.props.FloatProperty( name = "Scanresolution", default = parameters["angle_resolution"], min = 0.01, max = 3.141, description = "How far(angle) two scan lines are apart" )
    cType.velodyne_rotation_speed = bpy.props.FloatProperty( name = "Rotation speed", default = parameters["rotation_speed"], min = 1, max = 100, description = "Rotation speed in Hertz" )
    cType.velodyne_max_dist = bpy.props.FloatProperty( name = "Scan distance", default = parameters["max_dist"], min = 0, max = 1000, description = "How far the laser can see" )
    cType.velodyne_noise_mu = bpy.props.FloatProperty( name = "Noise mu", default = parameters["noise_mu"], description = "The center of the gaussian noise" )
    cType.velodyne_noise_sigma = bpy.props.FloatProperty( name = "Noise sigma", default = parameters["noise_sigma"], description = "The sigma of the gaussian noise" )
    cType.velodyne_db_noise_mu = bpy.props.FloatProperty( name = "DB Noise mu", default = parameters["distance_bias_noise_mu"], description = "The center of the gaussian noise" )
    cType.velodyne_db_noise_sigma = bpy.props.FloatProperty( name = "DB Noise sigma", default = parameters["distance_bias_noise_sigma"], description = "The sigma of the gaussian noise" )
    cType.velodyne_start_angle = bpy.props.FloatProperty( name = "Start angle", default = parameters["start_angle"], description = "The angle at which the scan is started" )
    cType.velodyne_end_angle = bpy.props.FloatProperty( name = "End angle", default = parameters["end_angle"], description = "The angle at which the scan is stopped" )
 

    cType.velodyne_ref_dist = bpy.props.FloatProperty( name = "Reflectivity Distance", default = parameters["reflectivity_distance"], description = "Objects closer than reflectivity distance are independent of their reflectivity" )
    cType.velodyne_ref_limit = bpy.props.FloatProperty( name = "Reflectivity Limit", default = parameters["reflectivity_limit"], description = "Minimum reflectivity for objects at the reflectivity distance" )
    cType.velodyne_ref_slope = bpy.props.FloatProperty( name = "Reflectivity Slope", default = parameters["reflectivity_slope"], description = "Slope of the reflectivity limit curve" )






def deg2rad(deg):
    return deg*math.pi/180.0

def rad2deg(rad):
    return rad*180.0/math.pi

def tuples_to_list(tuples):
    l = []
    for t in tuples:
        l.extend(t)
    return l


laser_angles =[-7.1143909000 ,-6.8259001000 ,0.3328709900 ,0.6607859700 ,
-6.4908152000 ,-6.0973902000 ,-8.5282297000 ,-8.1613369000 ,-5.8425112000 ,
-5.4713659000 ,-7.8512449000 ,-7.5291781000 ,-3.0490510000 ,-2.7686839000 ,
-5.0532770000 ,-4.7975101000 ,-2.3829660000 ,-2.1140020000 ,-4.4367881000 ,
-4.0757122000 ,-1.7279370000 ,-1.4470620000 ,-3.7842851000 ,-3.4226439000 ,
1.0237820000 ,1.3398750000 ,-0.9904980100 ,-0.6977589700 ,1.6909920000 ,
1.9717960000 ,-0.3464250000 ,-0.0419129990 ,-22.6174770000 ,-22.2171250000 ,
-11.3515270000 ,-10.7762110000 ,-21.7437740000 ,-21.1960530000 ,-24.8932860000 ,
-24.2637140000 ,-20.6647490000 ,-20.0160450000 ,-23.7457070000 ,-23.0651020000 ,
-16.4140130000 ,-16.0144540000 ,-19.4244710000 ,-19.1009100000 ,-15.4937170000 ,
-15.0140580000 ,-18.6500020000 ,-18.1543940000 ,-14.4663670000 ,-13.8276510000 ,
-17.5921270000 ,-16.9942110000 ,-10.3347680000 ,-9.8352394000 ,-13.2298120000 ,
-12.8963990000 ,-9.3798056000 ,-8.8888798000 ,-12.3722690000 ,-11.9693750000]

# The laser noise is initialized with a fixed randomized array to increase
# repoducibility. If the noise should be randomize, call 
# randomize_distance_bias
laser_noise = [0.023188431056485468, 0.018160539830319688, 
               -0.082857233607375583, -0.064524698320918547, 
               -0.093271246114693618, 0.043527643100361682,
                0.02964170651252759, 0.022130151884228375, 
                0.057142456134798118, -0.0022902380317122851, 
                0.0067235936679492184, -0.036271973173879445, 
                0.017223035592365758, -0.077567037832670549, 
               -0.045212530018321921, -0.071407355488847954, 
               -0.044010545427414234, -0.13100196824243787, 
                0.06562213285464942, 0.072876545417746588, 
                0.02948486101287804, -0.0549980634164711, 
                0.0017215074797752329, 0.011024793340907989, 
               -0.031627028532767984, -0.0015734962901194415, 
               -0.036013321659115423, 0.10758083132777119, 
               -0.08155406184051478, 0.042643613869132221, 
               -0.0084507159317202072, -0.13509680354593059, 
               -0.011626407663142539, -0.016650248443238872, 
               -0.089390919093335297, 0.058944202109090765, 
               -0.0017922326055001933, 0.17981608947109032, 
               -0.08508532554265108, 0.073143736372048768, 
               -0.048115410987441362, -0.042704861239692658, 
                0.035086496817459518, 0.064943607611183743, 
                0.010321640735410247, -0.088027285788537329, 
                0.064927912617182712, -0.0063073544055394313, 
                0.0094236036091259051, -0.012188267349634907, 
               -0.030570059320519608, -0.022883795755219431, 
               -0.01536736072143652, 0.091570972465821771, 
               -0.09083766812058082, 0.14380982060713934, 
                0.01373428104250375, -0.014464880110123654, 
               -0.031761209027541266, -0.01571113598069827, 
               -0.14107381715154735, -0.064936750764770235, 
                0.034911820770082327, 0.065682492298063416]


# If the laser noise has to be truely randomize, call this function prior
# to every scan
def randomize_distance_bias(noise_mu = 0.0, noise_sigma = 0.04):
    laser_noise = [random.gauss(noise_mu, noise_sigma)  for i in range(len(laser_angles)) ]




def scan_advanced(rotation_speed = 10.0, simulation_fps=24, angle_resolution = 0.1728, max_distance = 120, evd_file=None,noise_mu=0.0, noise_sigma=0.03, start_angle = 0.0, end_angle = 360.0, evd_last_scan=True, add_blender_mesh = False, add_noisy_blender_mesh = False, simulation_time = 0.0):
    start_time = time.time()

    current_time = simulation_time
    delta_rot = angle_resolution*math.pi/180

    evd_storage = evd.evd_file(evd_file)

    xaxis = Vector([1,0,0])
    yaxis = Vector([0,1,0])
    zaxis = Vector([0,0,1])

    rays = []
    ray_info = []

    steps_per_rotation = 360.0/angle_resolution
    time_per_step = (1.0/rotation_speed) / steps_per_rotation
    angles = end_angle-start_angle

    lines = (end_angle-start_angle)/angle_resolution
    for line in range(int(lines)):
        for laser_idx in range(len(laser_angles)):
            ray = Vector([0,0,max_distance])
            rot_angle = 1e-6 + start_angle+float(line)*angle_resolution + 180.0
            timestamp = ( (rot_angle-180.0)/angle_resolution) * time_per_step 
            rot_angle = rot_angle%360.0
            ray_info.append([deg2rad(rot_angle), deg2rad(laser_angles[laser_idx]), timestamp])
            
            rotator = Euler( [deg2rad(-laser_angles[laser_idx]), deg2rad(rot_angle), 0.0] )
            ray.rotate( rotator )
            rays.extend([ray[0],ray[1],ray[2]])

    returns = blensor.scan_interface.scan_rays(rays, max_distance)
    verts = []
    verts_noise = []

#    for idx in range((len(rays)//3)):
    for i in range(len(returns)):
        idx = returns[i][-1]
        v = [returns[i][1],returns[i][2],returns[i][3]]
        verts.append ( v )

        distance_noise =  laser_noise[idx%len(laser_noise)] + random.gauss(noise_mu, noise_sigma) 
        vector_length = math.sqrt(v[0]**2+v[1]**2+v[2]**2)
        norm_vector = [v[0]/vector_length, v[1]/vector_length, v[2]/vector_length]
        vector_length_noise = vector_length+distance_noise
        v_noise = [ norm_vector[0]*vector_length_noise, norm_vector[1]*vector_length_noise, norm_vector[2]*vector_length_noise ]
        verts_noise.append( v_noise )

        evd_storage.addEntry(timestamp = ray_info[idx][2], yaw =(ray_info[idx][0]+math.pi)%(2*math.pi), pitch=ray_info[idx][1], distance=vector_length, distance_noise=vector_length_noise, x=v[0], y=v[1], z=v[2], x_noise=v_noise[0], y_noise=v_noise[1], z_noise=v_noise[2], object_id=returns[i][4])


    current_angle = start_angle+float(float(int(lines))*angle_resolution)
            
    if evd_file:
        evd_storage.appendEvdFile()

    if add_blender_mesh:
        scan_mesh = bpy.data.meshes.new("scan_mesh")
        scan_mesh.vertices.add(len(verts))
        scan_mesh.vertices.foreach_set("co", tuples_to_list(verts))
        scan_mesh.update()
        scan_mesh_object = bpy.data.objects.new("scan", scan_mesh)
        bpy.context.scene.objects.link(scan_mesh_object)

    if add_noisy_blender_mesh:
        noise_scan_mesh = bpy.data.meshes.new("noisy_scan_mesh")
        noise_scan_mesh.vertices.add(len(verts_noise))
        noise_scan_mesh.vertices.foreach_set("co", tuples_to_list(verts_noise))
        noise_scan_mesh.update()
        noise_scan_mesh_object = bpy.data.objects.new("noisy_scan", noise_scan_mesh)
        bpy.context.scene.objects.link(noise_scan_mesh_object)

    bpy.context.scene.update()

    end_time = time.time()
    scan_time = end_time-start_time
    print ("Elapsed time: %.3f"%(scan_time))

    return True, current_angle, scan_time




# This Function creates scans over a range of frames

def scan_range(frame_start, frame_end, filename="/tmp/landscape.evd", frame_time = (1.0/24.0), rotation_speed = 10.0, fps = 24, add_blender_mesh=False, add_noisy_blender_mesh=False, angle_resolution = 0.1728, max_distance = 120.0, noise_mu = 0.0, noise_sigma= 0.02,last_frame = True):
    start_time = time.time()

    time_per_frame = 1.0 / float(fps)
    angle_per_second = 360.0 * rotation_speed
    angle_per_frame = angle_per_second * time_per_frame


    try:
        for i in range(frame_start,frame_end):
                bpy.context.scene.frame_current = i

                ok,start_radians,scan_time = scan_advanced(angle_resolution = angle_resolution, start_angle = float(i)*angle_per_frame, end_angle=float(i+1)*angle_per_frame, evd_file = filename, evd_last_scan=False,add_blender_mesh=add_blender_mesh, add_noisy_blender_mesh=add_noisy_blender_mesh, simulation_time = float(i)*frame_time, max_distance=max_distance, noise_mu = noise_mu, noise_sigma=noise_sigma)

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













