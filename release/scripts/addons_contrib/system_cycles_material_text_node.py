# system_cycles_material_text_node.py Copyright (C) 5-mar-2012, Silvio Falcinelli 
#
# 
# special thanks to user blenderartists.org cmomoney  
# 
#
# Show Information About the Blend.
# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

bl_info = {
    "name": "Cycles Auto Material Texures Node Editor",
    "author": "Silvio Falcinelli",
    "version": (0,5),
    "blender": (2, 6, 2),
    "api": 44136,
    "location": "Properties > Material > Automatic Node Editor ",
    "description": "automatic cycles texture map",
    "warning": "beta",
    "wiki_url": 'http://www.rendering3d.net/' \
        'scripts/materialedior',
    "tracker_url": "https://projects.blender.org/tracker/index.php?" \
        "func=detail&aid=????",
    "category": "System"}


import bpy
import math
from math import log
from math import pow
from math import exp
import os.path



def AutoNodeOff():
    mats = bpy.data.materials
    for cmat in mats:
        cmat.use_nodes=False
    bpy.context.scene.render.engine='BLENDER_RENDER'


def BakingText(tex,mode):
    print('________________________________________')
    print('INFO start bake texture ' + tex.name)
    bpy.ops.object.mode_set(mode='OBJECT')
    sc=bpy.context.scene
    tmat=''
    img=''
    Robj=bpy.context.active_object
    for n in bpy.data.materials:

        if n.name=='TMP_BAKING':
            tmat=n
   
    if not tmat:
        tmat = bpy.data.materials.new('TMP_BAKING')
        tmat.name="TMP_BAKING"
    
    
    bpy.ops.mesh.primitive_plane_add()
    tm=bpy.context.active_object
    tm.name="TMP_BAKING"
    tm.data.name="TMP_BAKING"
    bpy.ops.object.select_pattern(extend=False, pattern="TMP_BAKING", case_sensitive=False)
    sc.objects.active = tm
    bpy.context.scene.render.engine='BLENDER_RENDER'
    tm.data.materials.append(tmat)
    if len(tmat.texture_slots.items()) == 0:
        tmat.texture_slots.add()
    tmat.texture_slots[0].texture_coords='UV'
    tmat.texture_slots[0].use_map_alpha=True
    tmat.texture_slots[0].texture = tex.texture
    tmat.texture_slots[0].use_map_alpha=True
    tmat.texture_slots[0].use_map_color_diffuse=False
    tmat.use_transparency=True
    tmat.alpha=0
    tmat.use_nodes=False
    tmat.diffuse_color=1,1,1
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.unwrap()

    for n in bpy.data.images:
        if n.name=='TMP_BAKING':
            n.user_clear()
            bpy.data.images.remove(n)


    if mode == "ALPHA" and tex.texture.type=='IMAGE':
        sizeX=tex.texture.image.size[0]
        sizeY=tex.texture.image.size[1]
    else:
        sizeX=600
        sizeY=600
    bpy.ops.image.new(name="TMP_BAKING", width=sizeX, height=sizeY, color=(0.0, 0.0, 0.0, 1.0), alpha=True, uv_test_grid=False, float=False)
    bpy.data.screens['UV Editing'].areas[1].spaces[0].image = bpy.data.images["TMP_BAKING"]
    sc.render.engine='BLENDER_RENDER'
    img = bpy.data.images["TMP_BAKING"]
    img=bpy.data.images.get("TMP_BAKING")
    img.file_format = "JPEG"
    if mode == "ALPHA" and tex.texture.type=='IMAGE':
        img.filepath_raw = tex.texture.image.filepath + "_BAKING.jpg"

    else:
        img.filepath_raw = tex.texture.name + "_PTEXT.jpg"
    
    sc.render.bake_type = 'ALPHA'
    sc.render.use_bake_selected_to_active = True
    sc.render.use_bake_clear = True
    bpy.ops.object.bake_image()
    img.save()
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.delete() 
    bpy.ops.object.select_pattern(extend=False, pattern=Robj.name, case_sensitive=False)           
    sc.objects.active = Robj       
    img.user_clear()
    bpy.data.images.remove(img)
    bpy.data.materials.remove(tmat)

    print('INFO : end Bake ' + img.filepath_raw )
    print('________________________________________')

def AutoNode():
    
    mats = bpy.data.materials
    sc = bpy.context.scene

    for cmat in mats:

        cmat.use_nodes=True
        TreeNodes=cmat.node_tree
        links = TreeNodes.links
    
        shader=''
        shmix=''
        shtsl=''
        Add_Emission=''
        Add_Translucent=''
        Mix_Alpha=''        
        sT=False
        lock=True
        
        for n in TreeNodes.nodes:
            if n.type == 'OUTPUT_MATERIAL':
                if n.label == 'Lock':
                    lock=False

                    
        if lock:        
            for n in TreeNodes.nodes:
                TreeNodes.nodes.remove(n)
        
     
    
            if not shader :
                shader = TreeNodes.nodes.new('BSDF_DIFFUSE')    
                shader.location = 0,470
                 
                shout = TreeNodes.nodes.new('OUTPUT_MATERIAL')
                shout.location = 200,400          
                links.new(shader.outputs[0],shout.inputs[0])
                
            textures = cmat.texture_slots
            sM=True
    
            for tex in textures:
                if tex:
                    if tex.use:
                        if tex.use_map_alpha:
                            sM=False
                            
                            if sc.EXTRACT_ALPHA:
                                
                                if tex.texture.type =='IMAGE' and tex.texture.use_alpha: 
                                    
                                    if not os.path.exists(bpy.path.abspath(tex.texture.image.filepath + "_BAKING.jpg")) or sc.EXTRACT_OW:

                                        BakingText(tex,'ALPHA')
                                else:
                                    if not tex.texture.type =='IMAGE': 
                                    
                                        if not os.path.exists(bpy.path.abspath(tex.texture.name + "_PTEXT.jpg")) or sc.EXTRACT_OW:
    
                                            BakingText(tex,'PTEXT')                                             
                                    
                            



    
            if  cmat.use_transparency and cmat.raytrace_transparency.ior == 1 and not cmat.raytrace_mirror.use  and sM:
                if not shader.type == 'BSDF_TRANSPARENT':
                    print("INFO:  Make TRANSPARENT shader node " + cmat.name)
                    TreeNodes.nodes.remove(shader)
                    shader = TreeNodes.nodes.new('BSDF_TRANSPARENT')    
                    shader.location = 0,470
                    links.new(shader.outputs[0],shout.inputs[0]) 
    
    
    
            if not cmat.raytrace_mirror.use and not cmat.use_transparency:
                if not shader.type == 'BSDF_DIFFUSE':
                    print("INFO:  Make DIFFUSE shader node" + cmat.name)
                    TreeNodes.nodes.remove(shader)
                    shader = TreeNodes.nodes.new('BSDF_DIFFUSE')    
                    shader.location = 0,470
                    links.new(shader.outputs[0],shout.inputs[0]) 
                    
                    
    
            if cmat.raytrace_mirror.use and cmat.raytrace_mirror.reflect_factor>0.001 and cmat.use_transparency:
                if not shader.type == 'BSDF_GLASS':
                    print("INFO:  Make GLASS shader node" + cmat.name)
                    TreeNodes.nodes.remove(shader)
                    shader = TreeNodes.nodes.new('BSDF_GLASS')  
                    shader.location = 0,470
                    links.new(shader.outputs[0],shout.inputs[0]) 
    
    
    
    
            if cmat.raytrace_mirror.use and not cmat.use_transparency and cmat.raytrace_mirror.reflect_factor>0.001 :
                if not shader.type == 'BSDF_GLOSSY':
                    print("INFO:  Make MIRROR shader node" + cmat.name)
                    TreeNodes.nodes.remove(shader)
                    shader = TreeNodes.nodes.new('BSDF_GLOSSY') 
                    shader.location = 0,520
                    links.new(shader.outputs[0],shout.inputs[0]) 
                    
                    
                            
            if cmat.emit > 0.001 :
                if not shader.type == 'EMISSION' and not cmat.raytrace_mirror.reflect_factor>0.001 and not cmat.use_transparency:
                    print("INFO:  Mix EMISSION shader node" + cmat.name)
                    TreeNodes.nodes.remove(shader)
                    shader = TreeNodes.nodes.new('EMISSION')    
                    shader.location = 0,450
                    links.new(shader.outputs[0],shout.inputs[0])               
                       
                else:
                    if not Add_Emission:
                        print("INFO:  Add EMISSION shader node" + cmat.name)
                        shout.location = 550,330
                        Add_Emission = TreeNodes.nodes.new('ADD_SHADER')
                        Add_Emission.location = 370,490
                        
                        shem = TreeNodes.nodes.new('EMISSION')
                        shem.location = 180,380  
                        
                        links.new(Add_Emission.outputs[0],shout.inputs[0]) 
                        links.new(shem.outputs[0],Add_Emission.inputs[1])
                        links.new(shader.outputs[0],Add_Emission.inputs[0])
                        
                        shem.inputs['Color'].default_value=cmat.diffuse_color.r,cmat.diffuse_color.g,cmat.diffuse_color.b,1
                        shem.inputs['Strength'].default_value=cmat.emit
    
                                   
    
    
            if cmat.translucency > 0.001 : 
                print("INFO:  Add BSDF_TRANSLUCENT shader node" + cmat.name)
                shout.location = 770,330
                Add_Translucent = TreeNodes.nodes.new('ADD_SHADER')
                Add_Translucent.location = 580,490
                        
                shtsl = TreeNodes.nodes.new('BSDF_TRANSLUCENT')
                shtsl.location = 400,350     
                        
                links.new(Add_Translucent.outputs[0],shout.inputs[0]) 
                links.new(shtsl.outputs[0],Add_Translucent.inputs[1])
    
                
                if Add_Emission:
                    links.new(Add_Emission.outputs[0],Add_Translucent.inputs[0])
     
                    pass
                else:
    
                    links.new(shader.outputs[0],Add_Translucent.inputs[0]) 
                    pass               
                shtsl.inputs['Color'].default_value=cmat.translucency, cmat.translucency,cmat.translucency,1                             
          
                       


            shader.inputs['Color'].default_value=cmat.diffuse_color.r,cmat.diffuse_color.g,cmat.diffuse_color.b,1
            
            if shader.type=='BSDF_DIFFUSE':
                shader.inputs['Roughness'].default_value=cmat.specular_intensity    
                       
            if shader.type=='BSDF_GLOSSY':
                shader.inputs['Roughness'].default_value=1-cmat.raytrace_mirror.gloss_factor  
                
                
            if shader.type=='BSDF_GLASS':
                shader.inputs['Roughness'].default_value=1-cmat.raytrace_mirror.gloss_factor                   
                shader.inputs['IOR'].default_value=cmat.raytrace_transparency.ior
                
                
            if shader.type=='EMISSION':
                shader.inputs['Strength'].default_value=cmat.emit              
              
                      
                                  
            textures = cmat.texture_slots
            for tex in textures:
                sT=False   
                pText=''            
                if tex:
                    if tex.use:
                        if tex.texture.type=='IMAGE':
                            img = tex.texture.image
                            shtext = TreeNodes.nodes.new('TEX_IMAGE')
                            shtext.location = -200,400 
                            shtext.image=img
                            sT=True
    

               
                            
  
                        if not tex.texture.type=='IMAGE':                           
                            if sc.EXTRACT_PTEX:
                                print('INFO : Extract Procedural Texture  ' )
                                
                                if not os.path.exists(bpy.path.abspath(tex.texture.name + "_PTEXT.jpg")) or sc.EXTRACT_OW:
                                    BakingText(tex,'PTEX')    
                                                     
                                img=bpy.data.images.load(tex.texture.name + "_PTEXT.jpg")
                                shtext = TreeNodes.nodes.new('TEX_IMAGE')
                                shtext.location = -200,400 
                                shtext.image=img                                
                                sT=True
                                                                     

                if sT:
                        if tex.use_map_color_diffuse :
                            links.new(shtext.outputs[0],shader.inputs[0]) 
                            
                                                
                        if tex.use_map_emit:                            
                            if not Add_Emission:
                                print("INFO:  Mix EMISSION + Texure shader node " + cmat.name)
                                
                                intensity=0.5+(tex.emit_factor / 2)
                                
                                shout.location = 550,330
                                Add_Emission = TreeNodes.nodes.new('ADD_SHADER')
                                Add_Emission.name="Add_Emission"
                                Add_Emission.location = 370,490
                                
                                shem = TreeNodes.nodes.new('EMISSION')
                                shem.location = 180,380  
                                
                                links.new(Add_Emission.outputs[0],shout.inputs[0]) 
                                links.new(shem.outputs[0],Add_Emission.inputs[1])
                                links.new(shader.outputs[0],Add_Emission.inputs[0])
                                
                                shem.inputs['Color'].default_value=cmat.diffuse_color.r,cmat.diffuse_color.g,cmat.diffuse_color.b,1
                                shem.inputs['Strength'].default_value=intensity * 2

                            links.new(shtext.outputs[0],shem.inputs[0]) 


                        if tex.use_map_mirror:   
                            links.new(shader.inputs[0],shtext.outputs[0]) 


                        if tex.use_map_translucency:
                            if not Add_Translucent:   
                                print("INFO:  Add Translucency + Texure shader node " + cmat.name)
                                
                                intensity=0.5+(tex.emit_factor / 2)
                                
                                shout.location = 550,330
                                Add_Translucent = TreeNodes.nodes.new('ADD_SHADER')
                                Add_Translucent.name="Add_Translucent"
                                Add_Translucent.location = 370,290
                                
                                shtsl = TreeNodes.nodes.new('BSDF_TRANSLUCENT')
                                shtsl.location = 180,240     
                                
                                links.new(shtsl.outputs[0],Add_Translucent.inputs[1])
                                
                                if Add_Emission:
                                    links.new(Add_Translucent.outputs[0],shout.inputs[0]) 
                                    links.new(Add_Emission.outputs[0],Add_Translucent.inputs[0]) 
                                    pass
                                else:
                                    links.new(Add_Translucent.outputs[0],shout.inputs[0]) 
                                    links.new(shader.outputs[0],Add_Translucent.inputs[0])
                                                            
                            links.new(shtext.outputs[0],shtsl.inputs[0]) 
                            

                        if tex.use_map_alpha:
                            if not Mix_Alpha:   
                                print("INFO:  Mix Alpha + Texure shader node " + cmat.name)

                                shout.location = 750,330
                                Mix_Alpha = TreeNodes.nodes.new('MIX_SHADER')
                                Mix_Alpha.name="Add_Alpha"
                                Mix_Alpha.location = 570,290
                                sMask = TreeNodes.nodes.new('BSDF_TRANSPARENT') 
                                sMask.location = 250,180                                
                                tMask = TreeNodes.nodes.new('TEX_IMAGE')
                                tMask.location = -200,250

                                if tex.texture.type=='IMAGE':
                                    if tex.texture.use_alpha:
                                        imask=bpy.data.images.load(img.filepath+"_BAKING.jpg")       
                                    else:  
                                        imask=bpy.data.images.load(img.filepath)   
                                else:
                                    imask=bpy.data.images.load(img.name)         
                                      

                                tMask.image = imask
                                links.new(Mix_Alpha.inputs[0],tMask.outputs[0])
                                links.new(shout.inputs[0],Mix_Alpha.outputs[0])
                                links.new(sMask.outputs[0],Mix_Alpha.inputs[1])
                                
                                if not Add_Emission and not Add_Translucent:
                                    links.new(Mix_Alpha.inputs[2],shader.outputs[0])
                                
                                if Add_Emission and not Add_Translucent:
                                    links.new(Mix_Alpha.inputs[2],Add_Emission.outputs[0])  
                                
                                if Add_Translucent:
                                    links.new(Mix_Alpha.inputs[2],Add_Translucent.outputs[0])                                    
                                    
                                    
                            
                        if tex.use_map_normal:
                            t = TreeNodes.nodes.new('RGBTOBW')
                            t.location = -0,300 
                            links.new(t.outputs[0],shout.inputs[2]) 
                            links.new(shtext.outputs[0],t.inputs[0])    
    bpy.context.scene.render.engine='CYCLES'                                                      
                                                     
 
class mllock(bpy.types.Operator):
    bl_idname = "ml.lock"
    bl_label = "Lock"
    bl_description = "Safe to overwrite of mssive BL conversion"
    bl_register = True
    bl_undo = True
    @classmethod
    def poll(cls, context):
        return True
    def execute(self, context):
        cmat=bpy.context.selected_objects[0].active_material
        TreeNodes=cmat.node_tree
        links = TreeNodes.links
        for n in TreeNodes.nodes:
            if n.type == 'OUTPUT_MATERIAL':
                if n.label == 'Lock':
                    n.label=''
                else:
                    n.label='Lock'     




        return {'FINISHED'}
 
 
class mlrefresh(bpy.types.Operator):
    bl_idname = "ml.refresh"
    bl_label = "Refresh"
    bl_description = "Refresh"
    bl_register = True
    bl_undo = True
    @classmethod
    def poll(cls, context):
        return True
    def execute(self, context):
        AutoNode()
        return {'FINISHED'}


class mlrestore(bpy.types.Operator):
    bl_idname = "ml.restore"
    bl_label = "Restore"
    bl_description = "Restore"
    bl_register = True
    bl_undo = True
    @classmethod
    def poll(cls, context):
        return True
    def execute(self, context):
        AutoNodeOff()
        return {'FINISHED'}

from bpy.props import *
sc = bpy.types.Scene
sc.EXTRACT_ALPHA= BoolProperty(attr="EXTRACT_ALPHA",default= False)
sc.EXTRACT_PTEX= BoolProperty(attr="EXTRACT_PTEX",default= False)
sc.EXTRACT_OW= BoolProperty(attr="Overwrite",default= False)

class OBJECT_PT_scenemassive(bpy.types.Panel):
    bl_label = "Automatic Massive Material Nodes"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"
    

    def draw(self, context):
        sc = context.scene
        t=''
        lock=''
        try:
            cmat=bpy.context.selected_objects[0].active_material
            t="Material : " + cmat.name
            
            
            TreeNodes=cmat.node_tree
            links = TreeNodes.links
        
      
            lock=False
            
            for n in TreeNodes.nodes:
                if n.type == 'OUTPUT_MATERIAL':
                    if n.label == 'Lock':
                        lock=True          
            
            
        except:
            pass    
        
        ob_cols = []
        db_cols = []
        layout = self.layout
        row = layout.row()
        row.prop(sc,"EXTRACT_ALPHA",text='Extract Alpha Texture  (slow)',icon='FORCE_TEXTURE')
        row = layout.row()
        row.prop(sc,"EXTRACT_PTEX",text='Extract Procedural Texture (slow)',icon='FORCE_TEXTURE')        
        row = layout.row()
        row.prop(sc,"EXTRACT_OW",text='Extract Texture Overwrite') 
        row = layout.row()
        row = layout.row()
        l_row = layout.row()
        ob_cols.append(l_row.column())
        layout.separator()
        row = ob_cols[0].row() 
        row.operator("ml.refresh", text='BLENDER > CYCLES', icon='TEXTURE')
        layout.separator()
        row = ob_cols[0].row() 
        row.operator("ml.restore", text='BLENDER Mode  (Node Off)', icon='MATERIAL')        
        layout.separator()
        row = ob_cols[0].row() 
        layout.separator()
        layout.separator()
        row = ob_cols[0].row() 
        layout.separator()
        row = ob_cols[0].row() 



        if t:
            row.label(text=t)
            row.label(text='', icon='MATERIAL')
            if lock:
                row.operator("ml.lock", text="Lock" )
            else:
                row.operator("ml.lock", text="UnLock" ) 
            
        layout.separator()
        row = ob_cols[0].row() 
        layout.separator()          
        row = ob_cols[0].row() 
        layout.separator()
        row = ob_cols[0].row() 
        row.label(text="Ver 0,4 beta  blender 2.62 - 2.63    Silvio Falcinelli")
        layout.separator()
        row = ob_cols[0].row() 
        row.label(text="wwww.rendering3d.net")


 
def register():
    bpy.utils.register_module(__name__)
    pass

def unregister():
    bpy.utils.unregister_module(__name__)

    pass

if __name__ == "__main__":
    register()