from mathutils import Vector
from .. import bel

def write(me, uvs, matimage = False) :
    uvs, nest = bel.nested(uvs)
    newuvs = []
    append = newuvs.append
    for uvi, uvlist in enumerate(uvs) :

        uv = me.uv_textures.new()
        uv.name = 'UV%s'%uvi
        
        for uvfi, uvface in enumerate(uvlist) :
            #uv.data[uvfi].use_twoside = True # 2.60 changes mat ways
            mslotid = me.faces[uvfi].material_index
            #mat = mesh.materials[mslotid]
            if matimage :
                if matimage[mslotid] :
                    img = matimage[mslotid]
                    uv.data[uvfi].image=img
                    #uv.data[uvfi].use_image = True
            
            uv.data[uvfi].uv1 = Vector((uvface[0],uvface[1]))
            uv.data[uvfi].uv2 = Vector((uvface[2],uvface[3]))
            uv.data[uvfi].uv3 = Vector((uvface[4],uvface[5]))
            if len(uvface) == 8 :
                uv.data[uvfi].uv4 = Vector((uvface[6],uvface[7]))
        append(uv)
    if nest : return newuvs
    else : return newuvs[0]


# face are squared or rectangular, 
# any orientation
# vert order width then height 01 and 23 = x 12 and 03 = y
# normal default when face has been built
def row(vertices,faces,normals=True) :
    uvs = []
    append = uvs.append
    for face in faces :
        v0 = vertices[face[0]]
        v1 = vertices[face[1]]
        v2 = vertices[face[-1]]
        #print(v0,v1)
        lx = (v1 - v0).length
        ly = (v2 - v0).length
        # init uv
        if len(uvs) == 0 :
            x = 0
            y = 0
        elif normals :
            x = uvs[-1][2]
            y = uvs[-1][3]
        else :
            x = uvs[-1][0]
            y = uvs[-1][1]
        if normals : append([x,y,x+lx,y,x+lx,y+ly,x,y+ly])
        else : append([x+lx,y,x,y,x,y+ly,x+lx,y+ly])
    return uvs

## convert UV given as verts location to blender format
# eg : [ [v0x,v0y] , [vnx , vny] ... ] -> [ [ v1x,v1y,v0x,v0y,v4x,v4y] ... ]
# this format is found in directx files
'''
def asVertsLocation(verts2d, faces) :
    uv = []
    for f in faces :
        uvface = []
        for vi in f :
            uvface.extend(verts2d[vi])
        uv.append(uvface)
    return uv
'''
def asVertsLocation(verts2d, idFaces) :
    coFaces = []
    uvBlender = []
    conv0 = coFaces.extend
    conv1 = uvBlender.extend
    for f in idFaces : conv0([verts2d[vi] for vi in f])
    for f in coFaces : conv1(f)
    return uvBlender
