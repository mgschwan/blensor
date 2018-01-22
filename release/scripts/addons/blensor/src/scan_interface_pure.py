from .octrees import octrees
from .octrees import blob_octrees
import bpy
from mathutils import Matrix
import numpy as np

machineEpsilon = np.finfo(float).eps

def scene_to_mesh():
    global_matrix = Matrix() #identity

    scene_faces = []

    for ob in bpy.data.objects:
        faces = faces_from_mesh(ob,Matrix(), use_mesh_modifiers=True, triangulate=True)
        for f in faces:
            scene_faces.append(list(map(list,f)))
    return scene_faces

def faces_from_mesh(ob, global_matrix, use_mesh_modifiers=False, triangulate=True):
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

    if triangulate:
        # From a list of faces, return the face triangulated if needed.
        def iter_face_index():
            for face in mesh.tessfaces:
                vertices = face.vertices[:]
                if len(vertices) == 4:
                    yield vertices[0], vertices[1], vertices[2]
                    yield vertices[2], vertices[3], vertices[0]
                else:
                    yield vertices
    else:
        def iter_face_index():
            for face in mesh.tessfaces:
                yield face.vertices[:]

    vertices = mesh.vertices

    for indexes in iter_face_index():
        yield [vertices[index].co.copy() for index in indexes]

    bpy.data.meshes.remove(mesh)



def insert_face_into_tree(face, tree):
    """Calculate the center and bounds and insert the triangle into the tree 
       with the given bounds and the center as the index"""
    x = y = z = 0
    minx = maxx = face[0][0]
    miny = maxy = face[0][1]
    minz = maxz = face[0][2]

    for vertex in face:
        x += vertex[0]
        y += vertex[0]
        z += vertex[0]
        minx = min(minx, vertex[0])
        miny = min(miny, vertex[1])
        minz = min(minz, vertex[2])
        maxx = max(maxx, vertex[0])
        maxy = max(maxy, vertex[1])
        maxz = max(maxz, vertex[2])
    x = x/len(face) + len(tree)*machineEpsilon #try to make the triangles unique
    y = y/len(face)    
    z = z/len(face)    
    tree.insert((x,y,z),((minx,maxx),(miny,maxy),(minz,maxz)),face)

def test():
    scene = [[[1.0, 0.9999999403953552, -1.0], [1.0, -1.0, -1.0], [-1.0000001192092896, -0.9999998211860657, -1.0]], [[-1.0000001192092896, -0.9999998211860657, -1.0], [-0.9999996423721313, 1.0000003576278687, -1.0], [1.0, 0.9999999403953552, -1.0]], [[1.0000004768371582, 0.999999463558197, 1.0], [-0.9999999403953552, 1.0, 1.0], [-1.0000003576278687, -0.9999996423721313, 1.0]], [[-1.0000003576278687, -0.9999996423721313, 1.0], [0.9999993443489075, -1.0000005960464478, 1.0], [1.0000004768371582, 0.999999463558197, 1.0]], [[1.0, 0.9999999403953552, -1.0], [1.0000004768371582, 0.999999463558197, 1.0], [0.9999993443489075, -1.0000005960464478, 1.0]], [[0.9999993443489075, -1.0000005960464478, 1.0], [1.0, -1.0, -1.0], [1.0, 0.9999999403953552, -1.0]],
             [[1.0, -1.0, -1.0], [0.9999993443489075, -1.0000005960464478, 1.0], [-1.0000003576278687, -0.9999996423721313, 1.0]], [[-1.0000003576278687, -0.9999996423721313, 1.0], [-1.0000001192092896, -0.9999998211860657, -1.0], [1.0, -1.0, -1.0]], [[-1.0000001192092896, -0.9999998211860657, -1.0], [-1.0000003576278687, -0.9999996423721313, 1.0], [-0.9999999403953552, 1.0, 1.0]], [[-0.9999999403953552, 1.0, 1.0], [-0.9999996423721313, 1.0000003576278687, -1.0], [-1.0000001192092896, -0.9999998211860657, -1.0]], [[1.0000004768371582, 0.999999463558197, 1.0], [1.0, 0.9999999403953552, -1.0], [-0.9999996423721313, 1.0000003576278687, -1.0]], [[-0.9999996423721313, 1.0000003576278687, -1.0], [-0.9999999403953552, 1.0, 1.0], [1.0000004768371582, 0.999999463558197, 1.0]]]

    tree = blob_octrees.BlobOctree(((-100.0,100.0),(-100.0,100.0),(-100.0,100.0)))
    for face in scene:
        insert_face_into_tree(face,tree)