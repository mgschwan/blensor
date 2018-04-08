import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
import numpy as np

machineEpsilon = np.finfo(float).eps


# Calculate the minimum reflectivty that will cause a laser return
def blensor_calculate_reflectivity_limit(dist, 
                                         reflectivity_distance,
                                         reflectivity_limit,
                                         reflectivity_slope):
    min_reflectivity = -1.0
    if dist >= reflectivity_distance:
        min_reflectivity = reflectivity_limit + reflectivity_slope * (dist-reflectivity_distance)
    
    return min_reflectivity


"""Raycast scene with individual rays
   Return per hit:
   distance,
   hit_x
   hit_y
   hit_z
   object_id
   R
   G
   B
"""

"""This is the fallback scan interface if native blensor support is not available"""
def scan(numberOfRays, max_distance, elementsPerRay, keep_render_setup, do_shading, rays_buffer, returns_buffer, ELEMENTS_PER_RETURN): 
    if ELEMENTS_PER_RETURN != 8:
        raise Exception("Scan interface incompatible")
    
    # Step 1: Scene to polygons / store face indices and materials
    tris = []
    faces = []
    face_array,obj_array,mat_array = scene_to_mesh()

    for idx,f in enumerate(face_array):
        tris.append(list(f[0]))
        tris.append(list(f[1]))
        tris.append(list(f[2]))
        faces.append([idx*3,idx*3+1,idx*3+2])

    # Step 2: Polygons to BVH tree
    scene_bvh = BVHTree.FromPolygons(tris, faces, all_triangles = True)

    # Step 3: Raycast rays
    scanner = bpy.context.scene.camera
    reflectivity_distance = scanner.ref_dist
    reflectivity_limit = scanner.ref_limit
    reflectivity_slope = scanner.ref_slope

    origin = Vector([0.0,0.0,0.0])
    direction = Vector([0.0,0.0,0.0])

    hit_indices = [-1]*numberOfRays

    for idx in range(numberOfRays):
        direction.x = rays_buffer[idx*elementsPerRay]
        direction.y = rays_buffer[idx*elementsPerRay+1]
        direction.z = rays_buffer[idx*elementsPerRay+2]
        
        if elementsPerRay>=6:
            origin.x = rays_buffer[idx*elementsPerRay+3]
            origin.y = rays_buffer[idx*elementsPerRay+4]
            origin.z = rays_buffer[idx*elementsPerRay+5]
        else:
            origin.x = bpy.context.scene.camera.location.x
            origin.y = bpy.context.scene.camera.location.y
            origin.z = bpy.context.scene.camera.location.z

        direction.rotate (scanner.matrix_world)

        (hit_loc, hit_normal, hit_idx, hit_distance) = scene_bvh.ray_cast(origin,direction,max_distance)

        valid_return = False
        if hit_loc:
            mat = mat_array[hit_idx]

            diffuse_intensity = 1.0
            if mat:
                diffuse_intensity = mat.diffuse_intensity

            #Calculate the required diffuse reflectivity of the material to create a return
            ref_limit = blensor_calculate_reflectivity_limit(hit_distance, reflectivity_distance, reflectivity_limit, reflectivity_slope)

            if diffuse_intensity > ref_limit:
                valid_return = True
                if mat:
                    color = mat.diffuse_color
                    returns_buffer[idx*ELEMENTS_PER_RETURN+5] = color.r
                    returns_buffer[idx*ELEMENTS_PER_RETURN+6] = color.g
                    returns_buffer[idx*ELEMENTS_PER_RETURN+7] = color.b
                else:
                    returns_buffer[idx*ELEMENTS_PER_RETURN+5] = 1.0
                    returns_buffer[idx*ELEMENTS_PER_RETURN+6] = 1.0
                    returns_buffer[idx*ELEMENTS_PER_RETURN+7] = 1.0

                returns_buffer[idx*ELEMENTS_PER_RETURN] = hit_distance
                returns_buffer[idx*ELEMENTS_PER_RETURN+1] = hit_loc.x
                returns_buffer[idx*ELEMENTS_PER_RETURN+2] = hit_loc.y
                returns_buffer[idx*ELEMENTS_PER_RETURN+3] = hit_loc.z

                obj = obj_array[hit_idx]
                name = obj.name
                returns_buffer[idx*ELEMENTS_PER_RETURN+4] = ord(name[0]) + (ord(name[1])<<8) + (ord(name[2])<<16) + (ord(name[3])<<24)  

                hit_indices[idx] = hit_idx

        if not valid_return:
            for r in range(ELEMENTS_PER_RETURN):
                returns_buffer[idx*ELEMENTS_PER_RETURN+r] = 0.0

    # Step 3: Shade rays
    # TODO: Implement material solver
    if do_shading:
        for idx,mat_idx in enumerate(hit_indices):
            if mat_idx >= 0:
                #shade hit point
                pass
            

def scene_to_mesh():
    # TODO: Return materials per face as well
    global_matrix = Matrix() #identity

    scene_faces = []
    scene_obj = []
    scene_materials = []

    idx = 0
    for ob in bpy.data.objects:
        if not ob.hide_render:
            faces = faces_from_mesh(ob,Matrix(), use_mesh_modifiers=True)
            for f in faces:
                scene_faces.append(list(map(list,f[0:3])))
                scene_obj.append(ob)
                scene_materials.append(f[3])
    return scene_faces, scene_obj, scene_materials

def faces_from_mesh(ob, global_matrix, use_mesh_modifiers=False):
    """
    From an object, return a generator over a list of faces.

    Each faces is a list of his vertexes. Each vertex is a tuple of
    his coordinate.

    use_mesh_modifiers
        Apply the preview modifier to the returned liste

    triangulate
        Split the quad into two triangles
    """

    # get the editmode data
    ob.update_from_editmode()

    # get the modifiers
    try:
        mesh = ob.to_mesh(bpy.context.scene, use_mesh_modifiers, "PREVIEW")
    except RuntimeError:
        raise StopIteration

    mat = global_matrix * ob.matrix_world
    mesh.transform(mat)
    if mat.is_negative:
        mesh.flip_normals()
        mesh.calc_tessface()

    def iter_face_index():
        for face in mesh.tessfaces:
            vertices = face.vertices[:]
            material = None
            if face.material_index < len(ob.material_slots):
                material = ob.material_slots[face.material_index].material
            if len(vertices) == 4:
                yield vertices[0], vertices[1], vertices[2],material
                yield vertices[2], vertices[3], vertices[0],material
            else:
                yield vertices[0],vertices[1],vertices[2],material

    vertices = mesh.vertices

    for face in iter_face_index():
        yield [vertices[face[0]].co.copy(), vertices[face[1]].co.copy(), vertices[face[2]].co.copy(), face[3]]

    bpy.data.meshes.remove(mesh)

