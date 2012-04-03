import bpy
import numpy
from mathutils import Matrix


"""A package for simulating various types of range scanners inside blender"""

__version__ = '1.0.0'

__all__ = [
    'blendodyne',
    'depthmap',
    'globals',
    'tof',
    'kinect'
    'ibeo',
    'exportmotion',
    'mesh_utils'
    ]



################ Blender Addon specific ######################


bl_info = {
    "name": "Vertex Align",
    "description": "Aligns two objects by matching vertices",
    "author": "Michael Gschwandtner",
    "version": (1,0),
    "blender": (2, 6, 0),
    "api": 31236,
    "location": "View3D > Properties > Object",
    "warning": 'Requires numpy', # used for warning icon and text in addons panel
    "wiki_url": "http://www.blensor.org",
    "category": "3D View"}



class AlignVertexItem(bpy.types.PropertyGroup):
    index = bpy.props.IntProperty(name="Test Prop", default=0)

def getTransformationMatrix(object, referenceobject):

    o1 = object
    o2 = referenceobject

    verts_o1 = []
    verts_o2 = []
    for idx in o1.align_vertice_indices:
        v = object.matrix_world*object.data.vertices[idx.index].co.to_4d()
        verts_o1.append( v.to_3d()/v[3] )

    for idx in o2.align_vertice_indices:
        v = referenceobject.matrix_world*referenceobject.data.vertices[idx.index].co.to_4d()
        verts_o2.append( v.to_3d()/v[3] )
        
    if len(verts_o2) != len(verts_o1):
        raise Exception ("Invalid number of vertices")    

    A=numpy.zeros((len(verts_o1),12))
    b=numpy.zeros((len(verts_o2),1))
        
    for i in range(len(verts_o1)):
     A[i*3][0]=verts_o1[i].x
     A[i*3][1]=verts_o1[i].y
     A[i*3][2]=verts_o1[i].z
     A[i*3][3]=1
     A[i*3+1][4]=verts_o1[i].x
     A[i*3+1][5]=verts_o1[i].y
     A[i*3+1][6]=verts_o1[i].z
     A[i*3+1][7]=1
     A[i*3+2][8]=verts_o1[i].x
     A[i*3+2][9]=verts_o1[i].y
     A[i*3+2][10]=verts_o1[i].z
     A[i*3+2][11]=1
     b[i*3]   = verts_o2[i].x
     b[i*3+1] = verts_o2[i].y
     b[i*3+2] = verts_o2[i].z

    m = numpy.linalg.lstsq(A,b)[0]
    m = m.reshape((3,4))

    mat = Matrix()
    for row in range(3):
      for col in range(4):
        mat[col][row] = m[row][col]
    return mat

def getSelectedVertex(object):
    vert = -1
    for idx in range(len(object.data.vertices)):
        if object.data.vertices[idx].select:
           """Bail out if more than one vertex is selected"""
           if vert != -1:
              vert = -1
              break
           vert = idx
    return vert

def isIndexInside(index, coll):
    ret = False
    for c in coll:
        if c.index == index:
           ret = True
           break
    return ret

class MeshAlignPanel(bpy.types.Panel):
    bl_label = "Align Meshes"
    bl_idname = "OBJECT_PT_alignmesh"
    bl_space_type = "PROPERTIES"
    bl_region_type = "OBJECT"
    bl_context = "object"

    def draw(self, context):
        layout = self.layout

        obj = context.object

        row = layout.row()
        row.label(text="Align meshes", icon='WORLD_DATA')
        row = layout.row()
        row.operator("meshalign.addvertexbutton")
        row = layout.row()
        row.label(text="%d vertices selected"%(len(obj.align_vertice_indices)))
        row.operator("meshalign.clearvertexbutton")
        row = layout.row()
        row.prop(obj, "align_target_object")
        row = layout.row()
        row.operator("meshalign.button")


class OBJECT_OT_AlignButton(bpy.types.Operator):
    bl_idname = "meshalign.button"
    bl_label = "Align"
    
    def execute(self, context):
        obj = context.object
        reference_obj = bpy.data.objects[obj.align_target_object]

        mat = getTransformationMatrix(obj, reference_obj)
        print (str(mat))
        obj.matrix_world= mat * obj.matrix_world
        return {'FINISHED'}

class OBJECT_OT_AddVertexButton(bpy.types.Operator):
    bl_idname = "meshalign.addvertexbutton"
    bl_label = "Add vertex"
    
    def execute(self, context):
        obj = context.object
        bpy.ops.object.mode_set(mode='OBJECT') 
        vert = getSelectedVertex(obj)
        bpy.ops.object.mode_set(mode='EDIT') 
        print (str(vert))
        if vert==-1:
            self.report({'WARNING'}, "Please select exactly ONE vertex")
        elif isIndexInside(vert, obj.align_vertice_indices):
            self.report({'WARNING'}, "Vertex already selected")
        else:
            v = obj.align_vertice_indices.add()
            v.index = vert
        return {'FINISHED'}

class OBJECT_OT_ClearVertexButton(bpy.types.Operator):
    bl_idname = "meshalign.clearvertexbutton"
    bl_label = "Clear selection"
    
    def execute(self, context):
        obj = context.object
        while len(obj.align_vertice_indices) > 0:
            obj.align_vertice_indices.remove(0)

        return {'FINISHED'}



def register():
    bpy.utils.register_class(AlignVertexItem)
    bpy.types.Object.align_target_object = bpy.props.StringProperty( name = "Target object", default = "", description = "The object to be aligned to" )
    bpy.types.Object.align_vertice_indices = bpy.props.CollectionProperty(type=AlignVertexItem)
    bpy.utils.register_class(OBJECT_OT_AlignButton)
    bpy.utils.register_class(OBJECT_OT_AddVertexButton)
    bpy.utils.register_class(OBJECT_OT_ClearVertexButton)
    bpy.utils.register_class(MeshAlignPanel)




def unregister():
    bpy.utils.unregister_class(MeshAlignPanel)
    bpy.utils.unregister_class(OBJECT_OT_AlignButton)
    bpy.utils.unregister_class(OBJECT_OT_AddVertexButton)

if __name__ == "__main__":
    register()
