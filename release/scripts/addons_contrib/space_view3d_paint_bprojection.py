bl_info = {
    "name": "BProjection",
    "description": "Help Clone tool",
    "author": "kgeogeo",
    "version": (1, 0),
    "blender": (2, 6, 3),
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/3D_interaction/bprojection",
    "tracker_url":"http://projects.blender.org/tracker/index.php?func=detail&aid=30521&group_id=153&atid=468",
    "category": "Paint"}

import bpy
from bpy.types import Panel, Operator
from bpy.props import IntProperty, FloatProperty, BoolProperty, IntVectorProperty, StringProperty, FloatVectorProperty, CollectionProperty
from bpy_extras import view3d_utils
import math
from math import *
import mathutils
from mathutils import *

BProjection_Empty    = 'Empty for BProjection'
BProjection_Material = 'Material for BProjection'
BProjection_Texture  = 'Texture for BProjection'

# Main function for align the plan to view
def align_to_view(context):
    ob = context.object
    em = bpy.data.objects[BProjection_Empty]       
    rotation = em.custom_rotation
    scale = em.custom_scale
    z = em.custom_location.z
    pos = [em.custom_location.x, em.custom_location.y]
    
    reg = context.area.regions[4]        
    width = reg.width
    height = reg.height 
    
    sd = context.space_data    
    r3d = sd.region_3d     
    r3d.update()
    vr = r3d.view_rotation
    quat = mathutils.Quaternion((0.0, 0.0, 1.0), math.radians(float(rotation)))
    v = Vector((pos[0],pos[1],z))
    v.rotate(vr)

    em = bpy.data.objects[BProjection_Empty]
    img = bpy.data.textures[BProjection_Texture].image
    if img and img.size[1] != 0:
        prop = img.size[0]/img.size[1]
    else: prop = 1    
    
    if em.custom_linkscale:    
        em.scale = Vector((prop*scale[0], scale[0], 1))
    else:
        em.scale = Vector((prop*scale[0], scale[1], 1))
    pos_cur = em.location - sd.cursor_location
    rot_cur1 = em.rotation_euler.to_quaternion()
    em.location = v + ob.location
    em.rotation_euler = Quaternion.to_euler(vr*quat)   
    if em.custom_c3d:
        if em.custom_old_scale != em.custom_scale:
            pos_cur = em.location - sd.cursor_location       
        rot_cur2 = em.rotation_euler.to_quaternion()
        rot_cur1.invert()
        pos_cur.rotate(rot_cur1)
        pos_cur.rotate(rot_cur2)
        v = em.location - pos_cur
        sd.cursor_location =  v

def applyimage(context):        
        img = bpy.data.textures[BProjection_Texture].image
        em = bpy.data.objects[BProjection_Empty]
        ob = context.object
               
        face = ob.data.polygons
        uvdata = ob.data.uv_textures.active.data 
            
        for f,d in zip(face,uvdata):
            if f.select:
                d.image = img
               
        align_to_view(context)
        ob.data.update()

# Function to update the properties
def update_Location(self, context):          
    align_to_view(context)

def find_uv(context):
    obj = context.object
    me = obj.data.vertices
    vg = obj.vertex_groups
    l=[]
    index_uv = 0      
    for face in obj.data.polygons:
        x=len(face.vertices)
        for vertex in face.vertices:
            if len(me[vertex].groups)>0:
                for g in me[vertex].groups:
                    if vg[g.group].name == 'texture plane':
                        x-=1
        
                        
        if x == 0:
            l.append([index_uv,len(face.vertices)])
        index_uv += len(face.vertices)
    return l

# Function to update the scaleUV
def update_UVScale(self, context):
    ob = context.object
    em = bpy.data.objects[BProjection_Empty]
    v = Vector((em.custom_offsetuv[0]/10 + 0.5, em.custom_offsetuv[1]/10 + 0.5))
    l = Vector((0.0,0.0))
    s = em.custom_scaleuv
    os = em.custom_old_scaleuv 
    scale = s - os
    l = find_uv(context)
    for i,j in l:
        for t in range(j):
            d = context.object.data.uv_layers.active.data[i+t]
            vres =  v - d.uv  
            d.uv.x = v.x - vres.x/os[0]*s[0]
            d.uv.y = v.y - vres.y/os[1]*s[1]

    em.custom_old_scaleuv = s  
    
    applyimage(context)

def update_PropUVScale(self, context):
    em = bpy.data.objects[BProjection_Empty]
    if em.custom_linkscaleuv:
        em.custom_scaleuv = [em.custom_propscaleuv,em.custom_propscaleuv]

def update_LinkUVScale(self, context):
    em = bpy.data.objects[BProjection_Empty]
    if em.custom_linkscaleuv:
        em.custom_propscaleuv = em.custom_scaleuv.x
        update_PropUVScale(self, context)
    else:
        update_UVScale(self, context) 
        
# Function to update the offsetUV
def update_UVOffset(self, context):
    ob = context.object
    em = bpy.data.objects[BProjection_Empty]
    o = em.custom_offsetuv
    oo = em.custom_old_offsetuv 
    l = find_uv(context)
    for i,j in l:
        for t in range(j):
            d = context.object.data.uv_layers.active.data[i+t]
            d.uv = [d.uv[0] - oo[0]/10 + o[0]/10, d.uv[1] - oo[1]/10 + o[1]/10]   
    em.custom_old_offsetuv = o
    
    applyimage(context)

# Function to update the flip horizontal
def update_FlipUVX(self, context):
    l = find_uv(context)
    for i,j in l:
        for t in range(j):
            d = context.object.data.uv_layers.active.data[i+t]
            x = d.uv.x
            d.uv.x = 1 - x
    
    applyimage(context)

# Function to update the flip vertical
def update_FlipUVY(self, context):
    l = find_uv(context)
    for i,j in l:
        for t in range(j):
            d = context.object.data.uv_layers.active.data[i+t]
            y = d.uv[1]
            d.uv[1] = 1 - y
    
    applyimage(context)

# Function to update
def update_Rotation(self, context):              
    ob = context.object
    em = bpy.data.objects[BProjection_Empty]
    if em.custom_rotc3d:
        angle = em.custom_rotation - em.custom_old_rotation
        sd = context.space_data
        vr = sd.region_3d.view_rotation.copy()        
        c = sd.cursor_location - ob.location
        e = bpy.data.objects[BProjection_Empty].location - ob.location
        vo = Vector((0.0, 0.0, 1.0))
        vo.rotate(vr)
        quat = mathutils.Quaternion(vo, math.radians(angle))
        v = e-c
        v.rotate(quat)
        vr.invert()
        v.rotate(vr)
        c.rotate(vr)
        em.custom_location = c + v
    else:        
        align_to_view(context)
   
    em.custom_old_rotation = em.custom_rotation

# Function to update scale
def update_Scale(self, context):              
    ob = context.object
    em = bpy.data.objects[BProjection_Empty]
    
    if em.custom_scac3d:
        sd = context.space_data
        r3d =  sd.region_3d
        vr = r3d.view_rotation.copy()
        vr.invert()
        e = em.location - ob.location
        c = sd.cursor_location - ob.location
        ce = e - c
        
        s = em.custom_scale
        os = em.custom_old_scale
        c.rotate(vr)
        ce.rotate(vr)
        
        img = bpy.data.textures[BProjection_Texture].image
        if img and img.size[1] != 0:
            prop = img.size[0]/img.size[1]
        else: prop = 1
        
        v = Vector((s.x*ce.x/os.x, s.y*ce.y/os.y,0.0))
        em.custom_location = c + v
        

    else:          
        align_to_view(context)
            
    
    em.custom_old_scale = em.custom_scale

def update_PropScale(self, context):
    em = bpy.data.objects[BProjection_Empty]
    if em.custom_linkscale:
        em.custom_scale = [em.custom_propscale,em.custom_propscale]
    
def update_LinkScale(self, context):
    em = bpy.data.objects[BProjection_Empty]
    if em.custom_linkscale:
        em.custom_propscale = em.custom_scale.x
        update_PropScale(self, context)
    else:
        update_Scale(self, context) 

def update_activeviewname(self, context):
    em = bpy.data.objects[BProjection_Empty]
    if self.custom_active:
        em.custom_active_view = self.custom_active_view

class custom_props(bpy.types.PropertyGroup):
    custom_location = FloatVectorProperty(name="Location", description="Location of the plan",
                                           default=(0,0,-1.0),
                                           subtype = 'XYZ', size=3)
                                           
    custom_rotation = FloatProperty(name="Rotation", description="Rotate the plane",
                                     min=-180, max=180, default=0)
                                         
    custom_scale = FloatVectorProperty(name="Scales", description="Scale the planes",
                                       subtype = 'XYZ', default=(1.0, 1.0),min = 0.1, size=2)
    custom_propscale = FloatProperty(name="PropScale", description="Scale the Plan",
                                           default=1.0,min = 0.1)
                                                                                    
    custom_linkscale = BoolProperty(name="linkscale", default=True)
   
    # UV properties
    custom_scaleuv = FloatVectorProperty(name="ScaleUV", description="Scale the texture's UV",
                                            default=(1.0,1.0),min = 0.01, subtype = 'XYZ', size=2)
    custom_propscaleuv = FloatProperty(name="PropScaleUV", description="Scale the texture's UV",
                                           default=1.0,min = 0.01) 
    custom_offsetuv = FloatVectorProperty(name="OffsetUV", description="Decal the texture's UV",
                                            default=(0.0,0.0), subtype = 'XYZ', size=2)       
    custom_linkscaleuv = BoolProperty(name="linkscaleUV", default=True)
    custom_flipuvx = BoolProperty(name="flipuvx", default=False)
    custom_flipuvy = BoolProperty(name="flipuvy", default=False)
    
    # other properties
    custom_active= BoolProperty(name="custom_active", default=True)   
    custom_expand = BoolProperty(name="expand", default=False)
    
    custom_active_view = StringProperty(name = "custom_active_view",default = "View",update = update_activeviewname)
    
    custom_image = StringProperty(name = "custom_image",default = "")
    
    custom_index = IntProperty()

# Function to create custom properties
def createcustomprops(context):
    Ob = bpy.types.Object    
    
    # plane properties 
    Ob.custom_location = FloatVectorProperty(name="Location", description="Location of the plan",
                                           default=(5.0,0.0,-1.0),
                                           subtype = 'XYZ', size=3, update = update_Location)
                                           
    Ob.custom_rotation = FloatProperty(name="Rotation", description="Rotate the plane",
                                     min=-180, max=180, default=0,update = update_Rotation)
                                     
    Ob.custom_old_rotation = FloatProperty(name="old_Rotation", description="Old Rotate the plane",
                                         min=-180, max=180, default=0)
                                         
    Ob.custom_scale = FloatVectorProperty(name="Scales", description="Scale the planes",
                                          subtype = 'XYZ', default=(1.0, 1.0),min = 0.1, size=2,update = update_Scale)
    Ob.custom_propscale = FloatProperty(name="PropScale", description="Scale the Plan",
                                           default=1.0,min = 0.1,update = update_PropScale)
    Ob.custom_old_scale = FloatVectorProperty(name="old_Scales", description="Old Scale the planes",
                                          subtype = 'XYZ', default=(1.0, 1.0),min = 0.1, size=2)
                                          
    Ob.custom_linkscale = BoolProperty(name="linkscale", default=True, update = update_LinkScale)
    
                                
    Ob.custom_sub = IntProperty(name="Subdivide", description="Number of subdivision of the plan",
                                     min=0, max=20, default=0)                                
    
    # UV properties
    Ob.custom_scaleuv = FloatVectorProperty(name="ScaleUV", description="Scale the texture's UV",
                                            default=(1.0,1.0),min = 0.01, subtype = 'XYZ', size=2,update = update_UVScale)
    Ob.custom_propscaleuv = FloatProperty(name="PropScaleUV", description="Scale the texture's UV",
                                           default=1.0,min = 0.01,update = update_PropUVScale)    
    Ob.custom_old_scaleuv = FloatVectorProperty(name="old_ScaleUV", description="Scale the texture's UV",
                                                default=(1.0,1.0),min = 0.01, subtype = 'XYZ', size=2)
    Ob.custom_offsetuv = FloatVectorProperty(name="OffsetUV", description="Decal the texture's UV",
                                            default=(0.0,0.0), subtype = 'XYZ', size=2,update = update_UVOffset)    
    Ob.custom_old_offsetuv = FloatVectorProperty(name="old_OffsetUV", description="Decal the texture's UV",
                                                 default=(0.0,0.0), subtype = 'XYZ', size=2)    
    Ob.custom_linkscaleuv = BoolProperty(name="linkscaleUV", default=True, update = update_LinkUVScale)
    Ob.custom_flipuvx = BoolProperty(name="flipuvx", default=False, update = update_FlipUVX)
    Ob.custom_flipuvy = BoolProperty(name="flipuvy", default=False, update = update_FlipUVY)
    
    # other properties    
    Ob.custom_c3d = BoolProperty(name="c3d", default=True)
    Ob.custom_rotc3d = BoolProperty(name="rotc3d", default=False)
    Ob.custom_scac3d = BoolProperty(name="scac3d", default=False)
    Ob.custom_expand = BoolProperty(name="expand", default=True)
    Ob.custom_active_view = StringProperty(name = "custom_active_view",default = "View")
    try:
        Ob.custom_active_object = StringProperty(name = "custom_active_object",default = context.object.name)
    except:
        Ob.custom_active_object = StringProperty(name = "custom_active_object",default = 'debut')    
    Ob.custom_props = CollectionProperty(type = custom_props)

# Function to remove custom properties
def removecustomprops():    
    list_prop = ['custom_location', 'custom_rotation', 'custom_old_rotation', 'custom_scale', 'custom_old_scale', 'custom_c3d',
                 'custom_rotc3d', 'custom_scaleuv', 'custom_flipuvx', 'custom_flipuvy', 'custom_linkscale',
                 'custom_linkscaleuv', 'custom_old_scaleuv', 'custom_offsetuv', 'custom_old_offsetuv', 'custom_scac3d', 'custom_sub',
                 'custom_expand', 'custom_active_view', 'custom_propscaleuv', 'custom_props', 'custom_propscale']
    for prop in list_prop:
        try:
            del bpy.data.objects[BProjection_Empty][prop]
        except:
            pass
        
def clear_props(context):
    em = bpy.data.objects[BProjection_Empty] 
    em.custom_scale = [1,1]
    em.custom_rotation = 0
    em.custom_scaleuv =[1.0,1.0]
    em.custom_offsetuv =[0.0,0.0]
    em.custom_propscaleuv = 1.0
    em.custom_propscale = 1.0
    if em.custom_flipuvx == True:
        em.custom_flipuvx = False
    if em.custom_flipuvy == True:
        em.custom_flipuvy = False

# Oprerator Class to create view            
class CreateView(Operator):
    bl_idname = "object.create_view"
    bl_label = "Create a new view"

    def execute(self, context):              
        ob = context.object
        em = bpy.data.objects[BProjection_Empty]
        new_props = em.custom_props.add()        
        em.custom_active_view = new_props.custom_active_view               
        ob.data.shape_keys.key_blocks[ob.active_shape_key_index].mute = True
        bpy.ops.object.shape_key_add(from_mix = False)
        ob.data.shape_keys.key_blocks[ob.active_shape_key_index].value = 1.0
        new_props.custom_index = len(em.custom_props)-1
        bpy.ops.object.active_view(index = new_props.custom_index)
        return {'FINISHED'}

# Oprerator Class to copy view 
class SaveView(Operator):
    bl_idname = "object.save_view"
    bl_label = "copy the view"
    
    index = IntProperty(default = 0)
    
    def execute(self, context):              
        em = bpy.data.objects[BProjection_Empty]
        prop = em.custom_props[self.index]                            
        prop.custom_rotation =  em.custom_rotation                    
        prop.custom_scale =  em.custom_scale                  
        prop.custom_linkscale =  em.custom_linkscale                                      
        prop.custom_scaleuv = em.custom_scaleuv
        prop.custom_propscale = em.custom_propscale
        prop.custom_offsetuv =  em.custom_offsetuv  
        prop.custom_linkscaleuv = em.custom_linkscaleuv
        prop.custom_propscaleuv = em.custom_propscaleuv
        prop.custom_flipuvx = em.custom_flipuvx
        prop.custom_flipuvy = em.custom_flipuvy
        try:
            prop.custom_image = bpy.data.textures[BProjection_Texture].image.name
        except:
            pass
        
        return {'FINISHED'}

# Oprerator Class to copy view 
class PasteView(Operator):
    bl_idname = "object.paste_view"
    bl_label = "paste the view"
    
    index = IntProperty(default = 0)
    
    def execute(self, context):              
        em = bpy.data.objects[BProjection_Empty]
        tmp_scac3d = em.custom_scac3d
        tmp_rotc3d = em.custom_rotc3d
        em.custom_scac3d = False
        em.custom_rotc3d = False
        prop = em.custom_props[self.index]
        em.custom_linkscale =  prop.custom_linkscale
        em.custom_offsetuv =  prop.custom_offsetuv 
        em.custom_linkscaleuv = prop.custom_linkscaleuv
        em.custom_scaleuv = prop.custom_scaleuv
        em.custom_propscaleuv = prop.custom_propscaleuv       
        em.custom_rotation =  prop.custom_rotation                    
        em.custom_scale =  prop.custom_scale
        em.custom_propscale = prop.custom_propscale                     
        if prop.custom_image != '':
            if bpy.data.textures[BProjection_Texture].image.name != prop.custom_image:
                bpy.data.textures[BProjection_Texture].image = bpy.data.images[prop.custom_image]
                applyimage(context)
        if em.custom_flipuvx != prop.custom_flipuvx:
            em.custom_flipuvx = prop.custom_flipuvx
        if em.custom_flipuvy != prop.custom_flipuvy:
            em.custom_flipuvy = prop.custom_flipuvy
        em.custom_scac3d = tmp_scac3d
        em.custom_rotc3d = tmp_rotc3d        
        return {'FINISHED'}

# Oprerator Class to remove view 
class RemoveView(Operator):
    bl_idname = "object.remove_view"
    bl_label = "Rmeove the view"
    
    index = IntProperty(default = 0)
    
    def execute(self, context):              
        ob = context.object
        em = bpy.data.objects[BProjection_Empty]
        
        ob.active_shape_key_index =  self.index + 1
        bpy.ops.object.shape_key_remove()
        
        if  em.custom_props[self.index].custom_active: 
            if len(em.custom_props) > 0:
                bpy.ops.object.active_view(index = self.index-1)
            if self.index == 0 and len(em.custom_props) > 1:
                bpy.ops.object.active_view(index = 1)            
                
        em.custom_props.remove(self.index)
                
        if len(em.custom_props) == 0:
            clear_props(context)
            
            bpy.ops.object.create_view()            
                 
        i=0
        for item in em.custom_props:
            item.custom_index = i           
            i+=1 

        for item in (item for item in em.custom_props if item.custom_active):
                ob.active_shape_key_index = item.custom_index+1
           
        return {'FINISHED'}

# Oprerator Class to copy view 
class ActiveView(Operator):
    bl_idname = "object.active_view"
    bl_label = "Active the view"
    
    index = IntProperty(default = 0)
    
    def execute(self, context):
        ob = context.object
        em = bpy.data.objects[BProjection_Empty]
        for item in (item for item in em.custom_props if item.custom_active == True):
            bpy.ops.object.save_view(index = item.custom_index)
            item.custom_active = False
        em.custom_props[self.index].custom_active  = True
        em.custom_active_view = em.custom_props[self.index].custom_active_view 
        ob.active_shape_key_index =  self.index + 1
        
        for i in ob.data.shape_keys.key_blocks:
            i.mute = True
        
        ob.data.shape_keys.key_blocks[ob.active_shape_key_index].mute = False
        
        bpy.ops.object.paste_view(index = self.index)         
        
        return {'FINISHED'}

# Draw Class to show the panel
class BProjection(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "BProjection"

    @classmethod
    def poll(cls, context):
        return (context.image_paint_object or context.sculpt_object)

    def draw(self, context):
        layout = self.layout        
        if  BProjection_Empty in [ob.name for ob in bpy.data.objects]:
            tex = bpy.data.textures[BProjection_Texture]

            ob = context.object
            em = bpy.data.objects[BProjection_Empty]
            if ob == bpy.data.objects[em.custom_active_object]:            
                col = layout.column(align =True)
                col.operator("object.removebprojectionplane", text="Remove BProjection plane")           

            try:
                matBProjection = bpy.data.materials[BProjection_Material]
            except:
                matBProjection = None
            
            box = layout.box()

            row = box.row()
            if not em.custom_expand:
                row.prop(em, "custom_expand", text  = "", icon="TRIA_RIGHT", emboss=False)
                row.label(text= 'Paint Object: '+ ob.name)
            else:
                row.prop(em, "custom_expand", text = "" , icon="TRIA_DOWN", emboss=False)                
                row.label(text= 'Paint Object: '+ ob.name)
                
                if ob == bpy.data.objects[em.custom_active_object]:
                    col = box.column(align =True)
                    col.template_ID(tex, "image", open="image.open")
                    row  = box.row(align=True)
                    row.operator('object.applyimage', text="Apply image", icon = 'FILE_TICK')
                    row.prop(em, "custom_c3d",text="", icon='CURSOR')
                    row  = box.row(align =True)
                    row.label(text="Location:")
                    row  = box.row(align =True)
                    row.prop(em,'custom_location', text='')
                    row  = box.row(align =True)            
                    row.prop(em,'custom_rotation')
                    row.prop(em,'custom_rotc3d',text="",icon='MANIPUL')            
                    row  = box.row(align =True)
                    row.label(text="Scale:")
                    row  = box.row(align =True) 
                    if em.custom_linkscale :
                        row.prop(em, "custom_propscale",text="")
                        row.prop(em, "custom_linkscale",text="",icon='LINKED')
                    else: 
                        row.prop(em,'custom_scale',text='')
                        row.prop(em, "custom_linkscale",text="",icon='UNLINKED')
                    row.prop(em,'custom_scac3d',text="",icon='MANIPUL')                            
                    row  = box.row(align =True)
                    row.label(text="UV's Offset:")
                    row  = box.row(align =True)
                    row.prop(em,'custom_offsetuv',text='')
                    row.prop(em, "custom_flipuvx",text="",icon='ARROW_LEFTRIGHT')   
                    row.prop(em, "custom_flipuvy",text="",icon='FULLSCREEN_ENTER') 
                    row  = box.row(align =True)
                    row.label(text="UV's Scale:")
                    row  = box.row(align =True)                            
                    if em.custom_linkscaleuv:
                        row.prop(em,'custom_propscaleuv',text='')
                        row.prop(em, "custom_linkscaleuv",text="",icon='LINKED')
                    else: 
                        row.prop(em,'custom_scaleuv',text='')
                        row.prop(em, "custom_linkscaleuv",text="",icon='UNLINKED')            
                    
                    if matBProjection:
                        row = box.column(align =True)
                        row.prop(matBProjection,'alpha', slider = True)
                        row = box.column(align =True)
    
                if ob == bpy.data.objects[em.custom_active_object]:    
                    for item in em.custom_props:
                        box = layout.box()
                        row = box.row()
                        if item.custom_active:
                            row.operator("object.active_view",text = "", icon='RADIOBUT_ON', emboss = False).index = item.custom_index 
                        else:
                            row.operator("object.active_view",text = "", icon='RADIOBUT_OFF', emboss = False).index = item.custom_index 
                        row.prop(item, "custom_active_view", text="")        
                        row.operator('object.remove_view', text="", icon = 'PANEL_CLOSE', emboss = False).index = item.custom_index
                    row = layout.row()
                    row.operator('object.create_view', text="Create View", icon = 'RENDER_STILL') 
                else:
                    col = box.column(align =True)
                    col.operator("object.change_object", text="Change Object")       

        else:
            ob = context.object
            col = layout.column(align = True)
            
            if ob.active_material is None:
                col.label(text="Add a material first!", icon="ERROR")
            elif ob.data.uv_textures.active is None:
                col.label(text="Create UVMap first!!", icon="ERROR")
            else:
                col.operator("object.addbprojectionplane", text="Add BProjection plane")
                col = layout.column(align = True)
                col.prop(ob, "custom_sub",text="Subdivision level")
                   

# Oprerator Class to apply the image to the plane             
class ApplyImage(Operator):
    bl_idname = "object.applyimage"
    bl_label = "Apply image"

    def execute(self, context):        
        applyimage(context)
        
        return {'FINISHED'}

# Oprerator Class to make the 4 or 6 point and scale the plan
class IntuitiveScale(Operator):
    bl_idname = "object.intuitivescale"
    bl_label = "Draw lines"

    def invoke(self, context, event):
        ob = context.object
        em = bpy.data.objects[BProjection_Empty]
        x = event.mouse_region_x
        y = event.mouse_region_y                
        if len(ob.grease_pencil.layers.active.frames) == 0: 
            bpy.ops.gpencil.draw(mode='DRAW', stroke=[{"name":"", "pen_flip":False,
                                                       "is_start":True, "location":(0, 0, 0),
                                                       "mouse":(x,y), "pressure":1, "time":0}])
        else:
            if em.custom_linkscale:
                nb_point = 4
            else:
                nb_point = 6
                   
            if len(ob.grease_pencil.layers.active.frames[0].strokes) < nb_point:
                bpy.ops.gpencil.draw(mode='DRAW', stroke=[{"name":"", "pen_flip":False,
                                                           "is_start":True, "location":(0, 0, 0),
                                                           "mouse":(x,y), "pressure":1, "time":0}])
                                                           
            if len(ob.grease_pencil.layers.active.frames[0].strokes) == nb_point:
                s = ob.grease_pencil.layers.active.frames[0]
                v1 = s.strokes[1].points[0].co - s.strokes[0].points[0].co
                if not em.custom_linkscale:
                    v2 = s.strokes[4].points[0].co - s.strokes[3].points[0].co
                else:
                    v2 = s.strokes[3].points[0].co - s.strokes[2].points[0].co
                propx = v1.x/v2.x                
                em.custom_scale[0] *= abs(propx)
                
                if not em.custom_linkscale:
                    v1 = s.strokes[2].points[0].co - s.strokes[0].points[0].co
                    v2 = s.strokes[5].points[0].co - s.strokes[3].points[0].co
                    propy = v1.y/v2.y
                    em.custom_scale[1] *= abs(propy)
                bpy.ops.gpencil.active_frame_delete()
        
        return {'FINISHED'}

# Oprerator Class to configure all wath is needed
class AddBProjectionPlane(Operator):
    bl_idname = "object.addbprojectionplane"
    bl_label = "Configure"
    
    def creatematerial(self, context):        
        if 'Material for BProjection' not in [mat.name for mat in bpy.data.materials]:            
            bpy.data.textures.new(name='Texture for BProjection',type='IMAGE')
    
            bpy.data.materials.new(name='Material for BProjection')
            
            matBProjection = bpy.data.materials['Material for BProjection']
            matBProjection.texture_slots.add()
            matBProjection.use_shadeless = True
            matBProjection.use_transparency = True
            matBProjection.active_texture = bpy.data.textures['Texture for BProjection']
        
            index = matBProjection.active_texture_index
            matBProjection.texture_slots[index].texture_coords = 'UV'
        
        ob = context.object 
        old_index = ob.active_material_index
        bpy.ops.object.material_slot_add()
        index = ob.active_material_index
        ob.material_slots[index].material = bpy.data.materials['Material for BProjection']
        bpy.ops.object.material_slot_assign()
        ob.active_material_index = old_index
        ob.data.update()
            
    def execute(self, context):    
        if  BProjection_Empty not in [ob.name for ob in bpy.data.objects]:                
            
            cm = bpy.context.object.mode
            '''tmp = context.object
            for ob in (ob for ob in bpy.data.objects if ob.type == 'MESH' and ob.hide == False and context.scene in ob.users_scene):
                context.scene.objects.active = ob
                bpy.ops.object.mode_set(mode = cm, toggle=False) 
            
            context.scene.objects.active = tmp'''
            bpy.ops.object.mode_set(mode = 'OBJECT', toggle=False)
            
            context.space_data.show_relationship_lines = False
            
            ob = context.object
        
            bpy.ops.object.add()
            em = context.object
            em.name = BProjection_Empty
                        
            context.scene.objects.active = ob
            ob.select = True
    
            bpy.ops.object.editmode_toggle()
    
            bpy.ops.mesh.primitive_plane_add()
            bpy.ops.object.vertex_group_assign(new = True)
            ob.vertex_groups.active.name = 'texture plane'   
            bpy.ops.uv.unwrap()
            
            bpy.ops.mesh.select_all(action='DESELECT')                                
            bpy.ops.object.vertex_group_select()
            
            bpy.ops.object.editmode_toggle()
            for i in range(4):
                ob.data.edges[len(ob.data.edges)-1-i].crease = 1
            bpy.ops.object.editmode_toggle()
            
            em.custom_sub = ob.custom_sub
            if em.custom_sub > 0:
                bpy.ops.mesh.subdivide(number_cuts = em.custom_sub)
    
            em.select = True
            bpy.ops.object.hook_add_selob()
            em.select = False
            em.hide = True   
                     
            self.creatematerial(context)
  
          
            bpy.ops.gpencil.data_add()
            ob.grease_pencil.draw_mode = 'VIEW'
            bpy.ops.gpencil.layer_add()
            ob.grease_pencil.layers.active.color = [1.0,0,0]
            
            bpy.ops.object.editmode_toggle()
            
            bpy.ops.object.shape_key_add(from_mix = False)
            
            bpy.ops.object.create_view()
            # ----------------------------------------------
            # XXX, this isnt future proof, DON'T USE INDEX's - campbell                    
            km = bpy.data.window_managers['WinMan'].keyconfigs['Blender'].keymaps['3D View']
            km.keymap_items[3-1].idname = 'view3d.rotate_view3d'
            km.keymap_items[19-1].idname = 'view3d.zoom_view3d'
            km.keymap_items[19-1].properties.delta = 1.0
            km.keymap_items[20-1].idname = 'view3d.zoom_view3d'
            km.keymap_items[20-1].properties.delta = -1.0
            km.keymap_items[4-1].idname = 'view3d.pan_view3d'
            km.keymap_items[28-1].idname = 'view3d.preset_view3d'
            km.keymap_items[28-1].properties.view = 'FRONT'
            km.keymap_items[30-1].idname = 'view3d.preset_view3d'
            km.keymap_items[30-1].properties.view = 'RIGHT'            
            km.keymap_items[34-1].idname = 'view3d.preset_view3d'
            km.keymap_items[34-1].properties.view = 'TOP'
            km.keymap_items[36-1].idname = 'view3d.preset_view3d'
            km.keymap_items[36-1].properties.view = 'BACK'
            km.keymap_items[37-1].idname = 'view3d.preset_view3d'
            km.keymap_items[37-1].properties.view = 'LEFT'            
            km.keymap_items[38-1].idname = 'view3d.preset_view3d'
            km.keymap_items[38-1].properties.view = 'BOTTOM'                                   
            km = context.window_manager.keyconfigs.default.keymaps['Image Paint']
            kmi = km.keymap_items.new("object.intuitivescale", 'LEFTMOUSE', 'PRESS', shift=True)
                        
            align_to_view(context)
            
            context.space_data.cursor_location = em.location
            
            bpy.ops.object.mode_set(mode = cm, toggle=False)
            bpy.data.objects[BProjection_Empty].custom_active_object = context.object.name
            
        return {'FINISHED'}

# Oprerator Class to remove what is no more needed    
class RemoveBProjectionPlane(Operator):
    bl_idname = "object.removebprojectionplane"
    bl_label = "Configure"

    def removematerial(self, context):
        ob = context.object 
        i = 0

        for ms in ob.material_slots:
            if ms.name == BProjection_Material:
                index = i
            i+=1
                
        ob.active_material_index = index
        bpy.ops.object.material_slot_remove()
    
    def execute(self, context):
        try:               
            cm = bpy.context.object.mode
            bpy.ops.object.mode_set(mode = 'OBJECT', toggle=False)
            
            context.space_data.show_relationship_lines = True
            
            bpy.ops.object.modifier_remove(modifier="Hook-Empty for BProjection")
            
            self.removematerial(context)

            ob = context.object
    
            bpy.ops.object.editmode_toggle()
    
            bpy.ops.mesh.reveal()
                                   
            bpy.ops.mesh.select_all(action='DESELECT')                    
            
            ob.vertex_groups.active_index = ob.vertex_groups['texture plane'].index
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.delete()
            bpy.ops.object.vertex_group_remove()
    
            bpy.ops.object.editmode_toggle()
   
            ob.select = False
                
            em = bpy.data.objects[BProjection_Empty]
            context.scene.objects.active = em
            em.hide = False
            em.select = True
            bpy.ops.object.delete()
    
            context.scene.objects.active = ob
            ob.select = True
            
            km = bpy.data.window_managers['WinMan'].keyconfigs['Blender'].keymaps['3D View']
            # ----------------------------------------------
            # XXX, this isnt future proof, DON'T USE INDEX's - campbell
            km.keymap_items[3-1].idname = 'view3d.rotate'
            km.keymap_items[19-1].idname = 'view3d.zoom'
            km.keymap_items[19-1].properties.delta = 1.0
            km.keymap_items[20-1].idname = 'view3d.zoom'
            km.keymap_items[20-1].properties.delta = -1.0
            km.keymap_items[4-1].idname = 'view3d.move'
            km.keymap_items[28-1].idname = 'view3d.viewnumpad'
            km.keymap_items[28-1].properties.type = 'FRONT'
            km.keymap_items[30-1].idname = 'view3d.viewnumpad'
            km.keymap_items[30-1].properties.type = 'RIGHT'            
            km.keymap_items[34-1].idname = 'view3d.viewnumpad'
            km.keymap_items[34-1].properties.type = 'TOP'
            km.keymap_items[36-1].idname = 'view3d.viewnumpad'
            km.keymap_items[36-1].properties.type = 'BACK'
            km.keymap_items[37-1].idname = 'view3d.viewnumpad'
            km.keymap_items[37-1].properties.type = 'LEFT'            
            km.keymap_items[38-1].idname = 'view3d.viewnumpad'
            km.keymap_items[38-1].properties.type = 'BOTTOM'            
            
            km = context.window_manager.keyconfigs.default.keymaps['Image Paint']
            #to do
            for kmi in (kmi for kmi in km.keymap_items if kmi.idname in {"object.intuitivescale", }):
                    km.keymap_items.remove(kmi)
            
            '''tmp = context.object
            for ob in (ob for ob in bpy.data.objects if ob.type == 'MESH' and ob.hide == False and context.scene in ob.users_scene):
                context.scene.objects.active = ob
                bpy.ops.object.mode_set(mode = 'OBJECT', toggle=False) 
            
            context.scene.objects.active = tmp'''
            ob = context.object           
            
            
            for i in ob.data.shape_keys.key_blocks:
                bpy.ops.object.shape_key_remove()
            bpy.ops.object.shape_key_remove()
               
            bpy.ops.object.mode_set(mode = cm, toggle=False)
            removecustomprops()
                    
        except:
            nothing = 0
        
        return {'FINISHED'}

# Oprerator Class to remove what is no more needed    
class ChangeObject(Operator):
    bl_idname = "object.change_object"
    bl_label = "Change Object"

    def removematerial(self, context):
        ob = context.object 
        i = 0

        for ms in ob.material_slots:
            if ms.name == BProjection_Material:
                index = i
            i+=1
                
        ob.active_material_index = index
        bpy.ops.object.material_slot_remove()
    
    def execute(self, context):
            new_ob = context.object
            em = bpy.data.objects[BProjection_Empty]              
            context.scene.objects.active = bpy.data.objects[em.custom_active_object]
            ob = context.object
            if ob != new_ob:
                cm = bpy.context.object.mode
                bpy.ops.object.mode_set(mode = 'OBJECT', toggle=False)
                
                bpy.ops.object.modifier_remove(modifier="Hook-Empty for BProjection") 
    
                ob = context.object
        
                bpy.ops.object.editmode_toggle()
        
                bpy.ops.mesh.reveal()
                                       
                bpy.ops.mesh.select_all(action='DESELECT')                               
                ob.vertex_groups.active_index = ob.vertex_groups['texture plane'].index
                bpy.ops.object.vertex_group_select()
                lo_b = [ob for ob in bpy.data.objects if ob.type == 'MESH']
                bpy.ops.mesh.separate(type='SELECTED')
                lo_a = [ob for ob in bpy.data.objects if ob.type == 'MESH']
                bpy.ops.object.vertex_group_remove()
                
                for i in lo_b:
                    lo_a.remove(i)
                bplane = lo_a[0]
                
                bpy.ops.object.editmode_toggle()
                
                self.removematerial(context)
                
                bpy.ops.object.mode_set(mode = cm, toggle=False)
                
                shape_index = ob.active_shape_key_index
                
                for i in ob.data.shape_keys.key_blocks:
                    bpy.ops.object.shape_key_remove()
                bpy.ops.object.shape_key_remove()
                
                ob.select = False
                
                bplane.select = True            
                context.scene.objects.active = bplane
                for ms in (ms for ms in bplane.material_slots if ms.name != BProjection_Material):
                    bplane.active_material = ms.material
                    bpy.ops.object.material_slot_remove()
                
                for gs in (gs for gs in bplane.vertex_groups if gs.name != 'texture plane'):
                    bplane.vertex_groups.active_index = gs.index
                    bpy.ops.object.vertex_group_remove()
              
                context.scene.objects.active = new_ob
                cm = new_ob.mode
                bpy.ops.object.mode_set(mode = 'OBJECT', toggle=False) 
                bpy.ops.object.join()
    
                em.hide = False
                em.select = True
                new_ob.select = False
                bpy.ops.object.location_clear()
                bpy.ops.object.rotation_clear()
                bpy.ops.object.scale_clear()
                context.scene.objects.active = new_ob
                bpy.ops.object.editmode_toggle()            
                bpy.ops.object.hook_add_selob()
                bpy.ops.object.editmode_toggle()
                em.hide = True
                em.select = False
                new_ob.select = True
                em.custom_active_object = new_ob.name
                tmp = em.custom_c3d
                em.custom_c3d = False
                bpy.ops.object.active_view(index = shape_index-1)
                bpy.ops.object.mode_set(mode = cm, toggle=False)
                        
                sd = context.space_data
                r3d = sd.region_3d 
                vr = r3d.view_rotation.copy()
                vr.invert()
                ob_loc = ob.location.copy()            
                new_ob_loc = new_ob.location.copy() 
                ob_loc.rotate(vr)
                new_ob_loc.rotate(vr)
                em.custom_location += Vector((ob_loc.x - new_ob_loc.x, ob_loc.y - new_ob_loc.y, 0.0))
                em.custom_c3d = tmp
                    
            return {'FINISHED'}

# Oprerator Class to rotate the view3D
class RotateView3D(Operator):
    bl_idname = "view3d.rotate_view3d"
    bl_label = "Rotate the View3D"
    
    first_mouse = Vector((0,0))

    pan = Vector((0,0))

    key = ['']
 
    first_time = True
    tmp_level = -1

    def vect_sphere(self, context, mx, my):
        width = context.area.regions[4].width
        height = context.area.regions[4].height
           
        if width >= height:
            ratio = height/width
        
            x = 2*mx/width
            y = 2*ratio*my/height
            
            x = x - 1
            y = y - ratio
        else:
            ratio = width/height
        
            x = 2*ratio*mx/width
            y = 2*my/height
 
            x = x - ratio
            y = y - 1
        
        z2 = 1 - x * x - y * y
        if z2 > 0:
            z= sqrt(z2)
        else : z=0
            
        p = Vector((x, y, z))
        p.normalize()
        return p
    
    def tracball(self, context, mx, my, origine):
        sd = context.space_data
        ob = context.object
        em = bpy.data.objects[BProjection_Empty]
            
        vr_b = sd.region_3d.view_rotation.copy()
        vr_b.invert()
        pos_init = sd.region_3d.view_location - origine
        sd.region_3d.view_location = origine
        
        v1 = self.vect_sphere(context, self.first_mouse.x, self.first_mouse.y)
        v2 = self.vect_sphere(context, mx, my)
                        
        axis = Vector.cross(v1,v2);
        angle = Vector.angle(v1,v2);
            
        q =  Quaternion(axis,-2*angle)
                        
        sd.region_3d.view_rotation *=q
        sd.region_3d.update()
        
        vr_a = sd.region_3d.view_rotation.copy()                           
        pos_init.rotate(vr_a*vr_b)            
        sd.region_3d.view_location =  pos_init + origine
        
        self.first_mouse = Vector((mx, my))
                
    def modal(self, context, event):                                
        ob = context.object
        em = bpy.data.objects['Empty for BProjection'] 
        reg = context.area.regions[4]        
        if event.value == 'PRESS':
            self.pan = Vector((event.mouse_region_x, event.mouse_region_y))
                    
            self.key = [event.type]

        if event.value == 'RELEASE':
            self.key = [''] 

        if event.type == 'MOUSEMOVE':                        
            
            if '' in self.key:
                self.tracball(context, event.mouse_region_x, event.mouse_region_y,ob.location)
                align_to_view(context)
                if self.first_time:
                    rot_ang = context.user_preferences.view.rotation_angle            
                    context.user_preferences.view.rotation_angle = 0
                    bpy.ops.view3d.view_orbit(type='ORBITLEFT')
                    context.user_preferences.view.rotation_angle = rot_ang   
                    bpy.ops.view3d.view_persportho()         
                    bpy.ops.view3d.view_persportho()
                    self.first_time = False
          
            deltax = event.mouse_region_x - round(self.pan.x)
            deltay = event.mouse_region_y - round(self.pan.y)          

            if 'G' in self.key:       
                sd = context.space_data              
                l =  sd.region_3d
                vr = l.view_rotation.copy()
                vr.invert()
                
                v_init = Vector((0.0,0.0,1.0))
                
                pos = [-deltax,-deltay]
                v = view3d_utils.region_2d_to_location_3d(context.region, l, pos, v_init)
                pos = [0,0]
                vbl = view3d_utils.region_2d_to_location_3d(context.region, l, pos, v_init)        
                loc = vbl - v            
                loc.rotate(vr)
                em.custom_location += loc              
                                   
            if 'S' in self.key:                
                s = em.custom_scale
                if em.custom_linkscale:
                    em.custom_propscale += deltax/20
                else:
                    em.custom_scale = [s[0] + deltax/20, s[1] + deltay/20]
                                          
            if 'Z' in self.key:                
                em.custom_location.z+=deltax/10
                      
            if 'R' in self.key:
                em.custom_rotation+=deltax
                    
            if 'U' in self.key:
                suv = em.custom_scaleuv
                if em.custom_linkscaleuv:    
                    em.custom_propscaleuv += deltax/50
                else:
                    em.custom_scaleuv= [suv[0] + deltax/50 , suv[1] + deltay/50]               

            if 'Y' in self.key:       
                ouv = em.custom_offsetuv
                em.custom_offsetuv = [ouv[0] - deltax/50,ouv[1] - deltay/50] 

            self.pan = Vector((event.mouse_region_x, event.mouse_region_y))
            self.first_mouse = Vector((event.mouse_region_x, self.first_mouse.y))
                        
        elif event.type == 'MIDDLEMOUSE'and event.value == 'RELEASE':
            if self.tmp_level > -1:
                for sub in context.object.modifiers:
                    if sub.type in ['SUBSURF','MULTIRES']:
                        sub.levels = self.tmp_level   
            
            return {'FINISHED'}
        
        if 'C' in self.key:
            clear_props(context)
        
        if 'O' in self.key:
            bpy.ops.object.change_object()            
        return {'RUNNING_MODAL'}
    
    def execute(self, context):        
        align_to_view(context)  
        
        return{'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        self.first_mouse = Vector((event.mouse_region_x,event.mouse_region_y))
        self.first_time = True
        for sub in context.object.modifiers:
            if sub.type in ['SUBSURF', 'MULTIRES']:
                self.tmp_level = sub.levels
                sub.levels = 0
        return {'RUNNING_MODAL'}

# Oprerator Class to pan the view3D
class PanView3D(bpy.types.Operator):
    bl_idname = "view3d.pan_view3d"
    bl_label = "Pan View3D"
    
    first_mouse = Vector((0,0))
    tmp_level = -1

    def modal(self, context, event):
        ob = context.object
        em = bpy.data.objects[BProjection_Empty]
        width = context.area.regions[4].width
        height = context.area.regions[4].height

        deltax = event.mouse_region_x - self.first_mouse.x
        deltay = event.mouse_region_y - self.first_mouse.y                
        
        sd = context.space_data              
        r3d =  sd.region_3d
        vr = r3d.view_rotation.copy()
        vr.invert()
        
        v_init = Vector((0.0,0.0,1.0))
        
        pos = [deltax,deltay]
        v = view3d_utils.region_2d_to_location_3d(context.region, r3d, pos, v_init)
        pos = [0,0]
        vbl = view3d_utils.region_2d_to_location_3d(context.region, r3d, pos, v_init)        
        loc = vbl - v       
        sd.region_3d.view_location += loc         
        loc.rotate(vr)
        em.custom_location += loc

        self.first_mouse.x = event.mouse_region_x
        self.first_mouse.y = event.mouse_region_y

        if event.type == 'MIDDLEMOUSE'and event.value == 'RELEASE':
            if self.tmp_level > -1:
                for sub in context.object.modifiers:
                    if sub.type in ['SUBSURF','MULTIRES']:
                        sub.levels = self.tmp_level
            return {'FINISHED'}
        
        return {'RUNNING_MODAL'}
                
    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        self.first_mouse.x = event.mouse_region_x
        self.first_mouse.y = event.mouse_region_y   
        for sub in context.object.modifiers:
            if sub.type in ['SUBSURF', 'MULTIRES']:
                self.tmp_level = sub.levels
                sub.levels = 0  
                      
        return {'RUNNING_MODAL'}

    def execute(self, context):        
        align_to_view(context)  
        
        return{'FINISHED'}

# Oprerator Class to zoom the view3D
class ZoomView3D(Operator):
    bl_idname = "view3d.zoom_view3d"
    bl_label = "Zoom View3D"

    delta = FloatProperty(
        name="delta",
        description="Delta",
        min=-1.0, max=1,
        default=1.0)

    def invoke(self, context, event):                   
        ob = context.object
        em = bpy.data.objects[BProjection_Empty]
        sd = context.space_data

        width = context.area.regions[4].width
        height = context.area.regions[4].height              
                    
        r3d =  sd.region_3d
        v_init = Vector((0.0,0.0,1.0))

        pos = [width,height]
        vtr_b = view3d_utils.region_2d_to_location_3d(context.region, r3d, pos, v_init)
        pos = [0,0]
        vbl_b = view3d_utils.region_2d_to_location_3d(context.region, r3d, pos, v_init)
        len_b = vtr_b - vbl_b
       
        bpy.ops.view3d.zoom(delta = self.delta)
        r3d.update()

        pos = [width,height]
        vtr_a = view3d_utils.region_2d_to_location_3d(context.region, r3d, pos, v_init)
        pos = [0,0]
        vbl_a = view3d_utils.region_2d_to_location_3d(context.region, r3d, pos, v_init) 
        len_a = vtr_a - vbl_a
        
        fac = len_a.length/len_b.length
        r3d.view_location -= ob.location
        r3d.view_location *= fac
        r3d.view_location += ob.location
        vres = Vector((em.custom_location.x*fac,em.custom_location.y*fac,em.custom_location.z))
        em.custom_location = vres
        
        
        align_to_view(context)
        
        return {'FINISHED'}

    def execute(self, context):        
        align_to_view(context)
        
        return{'FINISHED'}

# Oprerator Class to use numpad shortcut
class PresetView3D(Operator):
    bl_idname = "view3d.preset_view3d"
    bl_label = "Preset View3D"

    view = StringProperty(name="View", description="Select the view", default='TOP')
    def invoke(self, context, event):                   
        ob = context.object
        em = bpy.data.objects[BProjection_Empty]
        origine = ob.location
        sd = context.space_data

        vr_b = sd.region_3d.view_rotation.copy()
        vr_b.invert()
        pos_init = sd.region_3d.view_location - origine
        sd.region_3d.view_location = origine

        tmp = context.user_preferences.view.smooth_view
        context.user_preferences.view.smooth_view = 0
        bpy.ops.view3d.viewnumpad(type=self.view)
        align_to_view(context)        
        context.user_preferences.view.smooth_view = tmp

        vr_a = sd.region_3d.view_rotation.copy()                           
        pos_init.rotate(vr_a*vr_b)            
        sd.region_3d.view_location =  pos_init + origine              
                    
        return {'FINISHED'}

def register():
    bpy.utils.register_module(__name__)
    createcustomprops(bpy.context)

def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
