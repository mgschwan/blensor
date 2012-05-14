# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Oscurart Tools",
    "author": "Oscurart",
    "version": (2,9),
    "blender": (2, 6, 3),
    "location": "View3D > Tools > Oscurart Tools",
    "description": "Tools for objects, render, shapes, and files.",
    "warning": "",
    "wiki_url": "oscurart.blogspot.com",
    "tracker_url": "",
    "category": "Object"}



import bpy
import math
import sys
import os
import stat
import bmesh

## CREA PANELES EN TOOLS

# VARIABLES DE ENTORNO
bpy.types.Scene.osc_object_tools=bpy.props.BoolProperty(default=False)
bpy.types.Scene.osc_mesh_tools=bpy.props.BoolProperty(default=False)
bpy.types.Scene.osc_shapes_tools=bpy.props.BoolProperty(default=False)
bpy.types.Scene.osc_render_tools=bpy.props.BoolProperty(default=False)
bpy.types.Scene.osc_files_tools=bpy.props.BoolProperty(default=False)
bpy.types.Scene.osc_overrides_tools=bpy.props.BoolProperty(default=False)

# PANEL DE CONTROL
class OscPanelControl(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = "Oscurart Tools"
    def draw(self,context):
        active_obj = context.active_object
        layout = self.layout             
  
        col = layout.column(align=1)         
        col.prop(bpy.context.scene,"osc_object_tools",text="Object",icon="OBJECT_DATAMODE")
        col.prop(bpy.context.scene,"osc_mesh_tools",text="Mesh",icon="EDITMODE_HLT")
        col.prop(bpy.context.scene,"osc_shapes_tools",text="Shapes",icon="SHAPEKEY_DATA")
        col.prop(bpy.context.scene,"osc_render_tools",text="Render",icon="SCENE")
        col.prop(bpy.context.scene,"osc_files_tools",text="Files",icon="IMASEL")
        col.prop(bpy.context.scene,"osc_overrides_tools",text="Overrides",icon="GREASEPENCIL")


# POLLS
class OscPollObject():
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    
    @classmethod
    def poll(cls, context):
        return(context.scene.osc_object_tools == True)
    

class OscPollMesh():
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    
    @classmethod
    def poll(cls, context):
        return(context.scene.osc_mesh_tools == True)    


class OscPollShapes():
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    
    @classmethod
    def poll(cls, context):
        return(context.scene.osc_shapes_tools == True)

class OscPollRender():
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    
    @classmethod
    def poll(cls, context):
        return(context.scene.osc_render_tools == True)
    
class OscPollFiles():
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    
    @classmethod
    def poll(cls, context):
        return(context.scene.osc_files_tools == True)  
    
class OscPollOverrides():
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    
    @classmethod
    def poll(cls, context):
        return(context.scene.osc_overrides_tools == True)       



## PANELES    
class OscPanelObject(OscPollObject, bpy.types.Panel):
    bl_idname = "Oscurart Object Tools"
    bl_label = "Object Tools"
        
    def draw(self, context):
        active_obj = context.active_object
        layout = self.layout        
        col = layout.column(align=1)
        row = col.row()           
        
        colrow = col.row(align=1)  
        colrow.operator("objects.relink_objects_between_scenes",icon="LINKED")     
        colrow.operator("objects.copy_objects_groups_layers",icon="LINKED")      
        col.operator("object.distribute_apply_osc",icon="OBJECT_DATAMODE") 
        colrow = col.row(align=1)
        colrow.prop(bpy.context.scene,"SearchAndSelectOt",text="")
        colrow.operator("object.search_and_select_osc",icon="ZOOM_SELECTED")       
        colrow = col.row(align=1)
        colrow.prop(bpy.context.scene,"RenameObjectOt",text="")
        colrow.operator("object.rename_objects_osc",icon="SHORTDISPLAY")  
        col.operator("object.duplicate_object_symmetry_osc",icon="OBJECT_DATAMODE", text="Duplicate Object Symmetry")      
        colrow = col.row(align=1)
        colrow.operator("object.modifiers_remove_osc",icon="MODIFIER", text="Remove Modifiers")
        colrow.operator("object.modifiers_apply_osc",icon="MODIFIER", text="Apply Modifiers")
        

class OscPanelMesh(OscPollMesh, bpy.types.Panel):
    bl_idname = "Oscurart Mesh Tools"
    bl_label = "Mesh Tools"
        
    def draw(self, context):
        active_obj = context.active_object
        layout = self.layout        
        col = layout.column(align=1)
        row = col.row()           
        
        col.operator("mesh.select_side_osc",icon="VERTEXSEL")  
        col.operator("mesh.normals_outside_osc",icon="SNAP_NORMAL")       
        colrow=col.row(align=1)
        colrow.operator("mesh.resym_osc",icon="UV_SYNC_SELECT") 
        colrow.operator("mesh.resym_vertex_weights_osc",icon="UV_SYNC_SELECT") 
        colrow=col.row(align=1)        
        colrow.operator("file.export_groups_osc", icon='GROUP_VCOL')
        colrow.operator("file.import_groups_osc", icon='GROUP_VCOL')        

        
class OscPanelShapes(OscPollShapes, bpy.types.Panel):
    bl_idname = "Oscurart Shapes Tools"
    bl_label = "Shapes Tools"
        
    def draw(self, context):
        active_obj = context.active_object
        layout = self.layout        
        col = layout.column(align=1)
        row = col.row()           

        col.operator("object.shape_key_to_objects_osc",icon="OBJECT_DATAMODE")
        col.operator("mesh.create_lmr_groups_osc",icon="GROUP_VERTEX")
        col.operator("mesh.split_lr_shapes_osc",icon="SHAPEKEY_DATA")
        colrow=col.row()
        colrow.operator("mesh.create_symmetrical_layout_osc",icon="SETTINGS")         
        colrow.operator("mesh.create_asymmetrical_layout_osc",icon="SETTINGS") 
        
class OscPanelRender(OscPollRender, bpy.types.Panel):
    bl_idname = "Oscurart Render Tools"
    bl_label = "Render Tools"
        
    def draw(self, context):
        active_obj = context.active_object
        layout = self.layout        
        col = layout.column(align=1)
        row = col.row() 

        col.operator("file.create_batch_maker_osc", icon="LINENUMBERS_ON", text="Make Render Batch") 
        colrow = col.row()
        colrow.operator("render.render_layers_at_time_osc",icon="RENDER_STILL", text="All Scenes")  
        colrow.operator("render.render_layers_at_time_osc_cf",icon="RENDER_STILL", text="> Frame")
        colrow = col.row()
        colrow.operator("render.render_current_scene_osc",icon="RENDER_STILL", text="Active Scene")
        colrow.operator("render.render_current_scene_osc_cf",icon="RENDER_STILL", text="> Frame")
        colrow = col.row(align=1) 
        colrow.prop(bpy.context.scene,"OscSelScenes",text="")
        colrow.operator("render.render_selected_scenes_osc",icon="RENDER_STILL", text="Selected Scenes") 
        colrow.operator("render.render_selected_scenes_osc_cf",icon="RENDER_STILL", text="> Fame")       
             
        colrow = col.row(align=1)
        colrow.prop(bpy.context.scene,"rcPARTS",text="Render Crop Parts") 
        colrow.operator("render.render_crop_osc",icon="RENDER_REGION")  


class OscPanelFiles(OscPollFiles, bpy.types.Panel):
    bl_idname = "Oscurart Files Tools"
    bl_label = "Files Tools"
        
    def draw(self, context):
        active_obj = context.active_object
        layout = self.layout        
        col = layout.column(align=1)
      
        colrow = col.row()
        colrow.operator("file.save_incremental_osc",icon="NEW")
        colrow.operator("image.reload_images_osc",icon="IMAGE_COL")  
        colrow = col.row(align=1)
        colrow.prop(bpy.context.scene,"oscSearchText",text="")               
        colrow.prop(bpy.context.scene,"oscReplaceText",text="")         
        col.operator("file.replace_file_path_osc",icon="SHORTDISPLAY") 
        
        
class OscPanelOverrides(OscPollOverrides, bpy.types.Panel):
    bl_idname = "Oscurart Overrides"
    bl_label = "Overrides Tools"
        
    def draw(self, context):
        layout = self.layout

        obj = context.object
        
        col = layout.box().column(align=1)

        colrow = col.row()
        col.operator("render.overrides_set_list", text="Create Override List",icon="GREASEPENCIL")
        col.label(text="Active Scene: " + bpy.context.scene.name)
        col.label(text="Example: [[Group,Material]]")        
        col.prop(bpy.context.scene, '["OVERRIDE"]', text="")
        col.operator("render.check_overrides", text="Check List",icon="ZOOM_ALL")
        
        boxcol=layout.box().column(align=1)
        boxcol.label(text="Danger Zone")
        boxcolrow=boxcol.row()
        boxcolrow.operator("render.apply_overrides", text="Apply Overrides",icon="ERROR")
        boxcolrow.operator("render.restore_overrides", text="Restore Overrides",icon="ERROR")        


        
##---------------------------RELOAD IMAGES------------------

class reloadImages (bpy.types.Operator):
    bl_idname = "image.reload_images_osc"
    bl_label = "Reload Images" 
    bl_options =  {"REGISTER","UNDO"}
    def execute(self,context):
        for imgs in bpy.data.images:
            imgs.reload()
        return{"FINISHED"}

##-----------------------------RESYM---------------------------

def defResym(self, OFFSET, SUBD):
    
    ##EDIT    
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    
    ##SETEO VERTEX MODE        
    bpy.context.tool_settings.mesh_select_mode[0]=1
    bpy.context.tool_settings.mesh_select_mode[1]=0
    bpy.context.tool_settings.mesh_select_mode[2]=0
    
    OBJETO = bpy.context.active_object
    OBDATA = bmesh.from_edit_mesh(OBJETO.data)
    OBDATA.select_flush(False)

    if SUBD > 0:
        USESUB=True
        SUBLEV=SUBD
    else:
        USESUB=False
        SUBLEV=1
    
    ## IGUALO VERTICES CERCANOS A CERO      
    for vertice in OBDATA.verts[:]:
        if abs(vertice.co[0]) < OFFSET  : 
            vertice.co[0] = 0              
            
    ##BORRA IZQUIERDA
    bpy.ops.mesh.select_all(action="DESELECT")
       
    for vertices in OBDATA.verts[:]:
      if vertices.co[0] < 0:
        vertices.select = 1
    
    ## BORRA COMPONENTES
    bpy.ops.mesh.delete()
    ## SUMA MIRROR
    bpy.ops.object.modifier_add(type='MIRROR')    
    ## SELECCIONO TODOS LOS COMPONENTES
    bpy.ops.mesh.select_all(action="SELECT")
    ## CREO UV TEXTURE DEL SIMETRICO
    bpy.ops.mesh.uv_texture_add()
    ## SETEO VARIABLE CON LA CANTIDAD DE UVS, RESTO UNO Y LE DOY UN NOMBRE
    LENUVLISTSIM = len(bpy.data.objects[OBJETO.name].data.uv_textures)
    LENUVLISTSIM = LENUVLISTSIM - 1
    OBJETO.data.uv_textures[LENUVLISTSIM:][0].name = "SYMMETRICAL"
    ## UNWRAP
    bpy.ops.uv.unwrap(method='ANGLE_BASED', fill_holes=True, correct_aspect=False, use_subsurf_data=USESUB, uv_subsurf_level=SUBLEV)
    ## MODO OBJETO
    bpy.ops.object.mode_set(mode="OBJECT", toggle= False) 
    ## APLICO MIRROR
    bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Mirror")
    ## VUELVO A EDIT MODE
    bpy.ops.object.mode_set(mode="EDIT", toggle= False)
    OBDATA = bmesh.from_edit_mesh(OBJETO.data)
    OBDATA.select_flush(0)
    ## CREO UV TEXTURE DEL ASIMETRICO
    bpy.ops.mesh.uv_texture_add()
    ## SETEO VARIABLE CON LA CANTIDAD DE UVS, RESTO UNO Y LE DOY UN NOMBRE
    LENUVLISTASIM = len(OBJETO.data.uv_textures)
    LENUVLISTASIM = LENUVLISTASIM  - 1
    OBJETO.data.uv_textures[LENUVLISTASIM:][0].name = "ASYMMETRICAL"
    ## SETEO UV ACTIVO
    OBJETO.data.uv_textures.active = OBJETO.data.uv_textures["ASYMMETRICAL"]
    ## UNWRAP
    bpy.ops.uv.unwrap(method='ANGLE_BASED', fill_holes=True, correct_aspect=False, use_subsurf_data=USESUB, uv_subsurf_level=SUBLEV)
    

class resym (bpy.types.Operator):
    bl_idname = "mesh.resym_osc"
    bl_label = "ReSym Mesh" 
    bl_options =  {"REGISTER","UNDO"}
    OFFSET=bpy.props.FloatProperty(name="Offset", default=0.001, min=-0, max=0.1)
    SUBD=bpy.props.IntProperty(name="Subdivisions Levels", default=0, min=0, max=4) 
    def execute(self,context):
        defResym(self, self.OFFSET, self.SUBD)
        return{"FINISHED"}     
        
## -----------------------------------SELECT LEFT---------------------
def side (self, nombre, offset): 
    
    bpy.ops.object.mode_set(mode="EDIT", toggle=0)
    
    OBJECT=bpy.context.active_object        
    ODATA = bmesh.from_edit_mesh(OBJECT.data)
    MODE=bpy.context.mode

    
    
    ##SETEO VERTEX MODE
    
    bpy.context.tool_settings.mesh_select_mode[0]=1
    bpy.context.tool_settings.mesh_select_mode[1]=0
    bpy.context.tool_settings.mesh_select_mode[2]=0
    
    ## DESELECCIONA TODO
    for VERTICE in ODATA.verts[:]:
        VERTICE.select = False
    
    if nombre == False:
        ## CONDICION QUE SI EL VERTICE ES MENOR A 0 LO SELECCIONA  
        for VERTICES in ODATA.verts[:]:
            if VERTICES.co[0] < (offset):
                VERTICES.select = 1  
    else:
        ## CONDICION QUE SI EL VERTICE ES MENOR A 0 LO SELECCIONA        
        for VERTICES in ODATA.verts[:]:
            if VERTICES.co[0] > (offset):
                VERTICES.select = 1                              

    ODATA.select_flush(False)
    
    bpy.ops.object.mode_set(mode="EDIT", toggle=0)    


class SelectMenor (bpy.types.Operator):
    bl_idname = "mesh.select_side_osc"
    bl_label = "Select Side" 
    bl_options =  {"REGISTER","UNDO"}
    
    side = bpy.props.BoolProperty(name="Greater than zero", default=False)
    offset = bpy.props.FloatProperty(name="Offset", default=0)
    def execute(self,context):  
        
        side(self, self.side, self.offset)
               
        return{"FINISHED"}        
           
    
    
    

##-----------------------------------CREATE SHAPES----------------       
class CreaShapes(bpy.types.Operator):
    bl_idname = "mesh.split_lr_shapes_osc"
    bl_label = "Split LR Shapes"
    bl_options =  {"REGISTER","UNDO"}
    def execute(self, context):
        ## VARIABLES
        ACTOBJ=bpy.context.active_object
        LENKB=len(ACTOBJ.data.shape_keys.key_blocks)
        
        ## RECORTO NOMBRES
        for SHAPE in ACTOBJ.data.shape_keys.key_blocks:
            if len(SHAPE.name) > 7:
                SHAPE.name=SHAPE.name[:8]
                
        ## DUPLICO SHAPES Y CONECTO GRUPO
        for SHAPE in ACTOBJ.data.shape_keys.key_blocks[1:]:
            SHAPE.value=1
            bpy.ops.object.shape_key_add(from_mix=True)
            ACTOBJ.data.shape_keys.key_blocks[-1].name=SHAPE.name[:8]+"_L"
            ACTOBJ.data.shape_keys.key_blocks[-1].vertex_group="_L"
            bpy.ops.object.shape_key_add(from_mix=True)
            ACTOBJ.data.shape_keys.key_blocks[-1].name=SHAPE.name[:8]+"_R"
            ACTOBJ.data.shape_keys.key_blocks[-1].vertex_group="_R"
            bpy.ops.object.shape_key_clear() 
        
        print ("OPERACION TERMINADA")        
        return{"FINISHED"}
    
    
##----------------------------SHAPES LAYOUT-----------------------

class CreaShapesLayout(bpy.types.Operator):
    bl_idname = "mesh.create_symmetrical_layout_osc"
    bl_label = "Symmetrical Layout"
    bl_options =  {"REGISTER","UNDO"}
    def execute(self, context):
        
  
        SEL_OBJ= bpy.context.active_object
        LISTA_KEYS = bpy.context.active_object.data.shape_keys.key_blocks[:]
        
        ##MODOS
        EDITMODE = "bpy.ops.object.mode_set(mode='EDIT')"
        OBJECTMODE = "bpy.ops.object.mode_set(mode='OBJECT')"
        POSEMODE = "bpy.ops.object.mode_set(mode='POSE')"
        
        ##INDICE DE DRIVERS
        varindex = 0
        
        ##CREA NOMBRES A LA ARMATURE
        amt = bpy.data.armatures.new("ArmatureData")
        ob = bpy.data.objects.new("RIG_LAYOUT_"+SEL_OBJ.name, amt)
        
        ##LINK A LA ESCENA
        scn = bpy.context.scene
        scn.objects.link(ob)
        scn.objects.active = ob
        ob.select = True
        
        
        
        
        
        eval(EDITMODE)
        gx = 0
        gy = 0
        
        
        
        for keyblock in LISTA_KEYS:
            print ("KEYBLOCK EN CREACION DE HUESOS "+keyblock.name)
        
                
            if keyblock.name[-2:] != "_L":
                if keyblock.name[-2:] != "_R":
        
                    ##CREA HUESOS
                
                    bone = amt.edit_bones.new(keyblock.name)
                    bone.head = (gx,0,0)
                    bone.tail = (gx,0,1)
                    gx = gx+2.2
                    bone = amt.edit_bones.new(keyblock.name+"_CTRL")
                    bone.head = (gy,0,0)
                    bone.tail = (gy,0,0.2)
                    gy = gy+2.2     
                  
                    ##SETEA ARMATURE ACTIVA
                    bpy.context.scene.objects.active = bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name]
                    bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].select = 1
                    ##DESELECCIONA (modo edit)
                    eval(EDITMODE)
                    bpy.ops.armature.select_all(action="DESELECT")
                    
                    ##EMPARENTA HUESOS
                
                    ##HUESO ACTIVO
                    eval(OBJECTMODE)
                    bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].data.bones.active = bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].data.bones[keyblock.name] 
                    ##MODO EDIT
                    eval(EDITMODE)       
                    ##DESELECCIONA (modo edit)
                    bpy.ops.armature.select_all(action="DESELECT")    
                    ##MODO OBJECT  
                    eval(OBJECTMODE)    
                    ##SELECCIONA UN HUESO
                    bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].data.bones[keyblock.name+"_CTRL"].select = 1
                    eval(EDITMODE)    
                    ##EMPARENTA
                    bpy.ops.armature.parent_set(type="OFFSET")
                    ##DESELECCIONA (modo edit)
                    bpy.ops.armature.select_all(action="DESELECT")      
                     
                    ##LE HAGO UNA VARIABLE DE PLACEBO
                    keyblock.driver_add("value") 
                    SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.expression = "var+var_001"
                    SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables.new()
                    SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables.new()           
                      
                    
                    varindex = varindex + 1 
        
        
        
        for keyblock in LISTA_KEYS:
            print ("KEYBLOCK SEGUNDA VUELTA :"+keyblock.name)    
            
            if keyblock.name[-2:] == "_L":
                print("igual a L") 
        
                ##CREA DRIVERS Y LOS CONECTA
                keyblock.driver_add("value")
                keyblock.driver_add("value")
                
                SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.expression = "var+var_001"
                SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables.new()
                SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables.new()
                SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables['var'].targets[0].id  = bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name] 
                SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables['var'].targets[0].bone_target   = bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].data.bones[(keyblock.name[:-2])+"_CTRL"].name
                SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables['var'].type = 'TRANSFORMS' 
                SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables['var'].targets[0].transform_space= "LOCAL_SPACE"        
                SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables['var'].targets[0].transform_type= "LOC_X"  
                SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables['var_001'].targets[0].id = bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name]
                SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables['var_001'].targets[0].bone_target   = bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].data.bones[(keyblock.name[:-2])+"_CTRL"].name    
                SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables['var_001'].type = 'TRANSFORMS'            
                SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables['var_001'].targets[0].transform_space= "LOCAL_SPACE"        
                SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables['var_001'].targets[0].transform_type= "LOC_Y"    
                        
                             
                varindex = varindex + 1
            
                
        
          
            if keyblock.name[-2:] == "_R":
                print("igual a R") 
                
                ##CREA DRIVERS Y LOS CONECTA
                keyblock.driver_add("value")
                keyblock.driver_add("value")        
                
                SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.expression = "-var+var_001"
                SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables.new()
                SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables.new()
                SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables['var'].targets[0].id  = bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name] 
                SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables['var'].targets[0].bone_target   = bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].data.bones[(keyblock.name[:-2])+"_CTRL"].name      
                SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables['var'].type = 'TRANSFORMS' 
                SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables['var'].targets[0].transform_space= "LOCAL_SPACE"                 
                SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables['var'].targets[0].transform_type= "LOC_X"  
                SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables['var_001'].targets[0].id = bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name]
                SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables['var_001'].targets[0].bone_target   = bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].data.bones[(keyblock.name[:-2])+"_CTRL"].name    
                SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables['var_001'].type = 'TRANSFORMS'            
                SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables['var_001'].targets[0].transform_space= "LOCAL_SPACE"        
                SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables['var_001'].targets[0].transform_type= "LOC_Y" 
                        
                varindex = varindex + 1       
                
                
                
                
        ## CREO DATA PARA SLIDERS
        
        ## creo data para los contenedores
        verticess = [(-1,1,0),(1,1,0),(1,-1,0),(-1,-1,0)]
        edgess = [(0,1),(1,2),(2,3),(3,0)]
        
        mesh = bpy.data.meshes.new(keyblock.name+"_data_container")
        object = bpy.data.objects.new("GRAPHIC_CONTAINER", mesh)
        bpy.context.scene.objects.link(object)
        mesh.from_pydata(verticess,edgess,[])
        
        ## PONGO LOS LIMITES Y SETEO ICONOS
        for keyblock in LISTA_KEYS:
            print ("KEYBLOCK EN CREACION DE HUESOS "+keyblock.name)
        
                
            if keyblock.name[-2:] != "_L":
                if keyblock.name[-2:] != "_R":
                    ## SETEO ICONOS
                    bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].pose.bones[keyblock.name].custom_shape = bpy.data.objects['GRAPHIC_CONTAINER']
                    bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].pose.bones[keyblock.name+"_CTRL"].custom_shape = bpy.data.objects['GRAPHIC_CONTAINER']
                    ## SETEO CONSTRAINTS
                    eval(OBJECTMODE)
                    bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].data.bones.active = bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].data.bones[keyblock.name+"_CTRL"]
                    ## SUMO CONSTRAINT
                    eval(POSEMODE)
                    bpy.ops.pose.constraint_add(type="LIMIT_LOCATION")
                    
                    bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].pose.bones[keyblock.name+"_CTRL"].constraints['Limit Location'].min_x = -1
                    bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].pose.bones[keyblock.name+"_CTRL"].constraints['Limit Location'].use_min_x = 1
                    bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].pose.bones[keyblock.name+"_CTRL"].constraints['Limit Location'].min_z = 0
                    bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].pose.bones[keyblock.name+"_CTRL"].constraints['Limit Location'].use_min_z = 1
                    bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].pose.bones[keyblock.name+"_CTRL"].constraints['Limit Location'].min_y = -1
                    bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].pose.bones[keyblock.name+"_CTRL"].constraints['Limit Location'].use_min_y = 1
                    
                    bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].pose.bones[keyblock.name+"_CTRL"].constraints['Limit Location'].max_x =  1
                    bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].pose.bones[keyblock.name+"_CTRL"].constraints['Limit Location'].use_max_x = 1
                    bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].pose.bones[keyblock.name+"_CTRL"].constraints['Limit Location'].max_z =  0
                    bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].pose.bones[keyblock.name+"_CTRL"].constraints['Limit Location'].use_max_z = 1
                    bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].pose.bones[keyblock.name+"_CTRL"].constraints['Limit Location'].max_y =  1
                    bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].pose.bones[keyblock.name+"_CTRL"].constraints['Limit Location'].use_max_y = 1
                    
                    bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].pose.bones[keyblock.name+"_CTRL"].constraints['Limit Location'].owner_space  = "LOCAL"
                    
        ## PARA QUE EL TEXTO FUNCIONE PASAMOS A OBJECT MODE
        eval(OBJECTMODE)
        
        ## TEXTOS
        for keyblock in LISTA_KEYS:
            print ("KEYBLOCK EN TEXTOS "+keyblock.name)
        
                
            if keyblock.name[-2:] != "_L":
                if keyblock.name[-2:] != "_R":            
                    ## creo tipografias
                    bpy.ops.object.text_add(location=(0,0,0))
                    bpy.data.objects['Text'].data.body = keyblock.name
                    bpy.data.objects['Text'].name = "TEXTO_"+keyblock.name
                    bpy.data.objects["TEXTO_"+keyblock.name].rotation_euler[0] = math.pi/2
                    bpy.data.objects["TEXTO_"+keyblock.name].location.x = -1
                    bpy.data.objects["TEXTO_"+keyblock.name].location.z = -1
                    bpy.data.objects["TEXTO_"+keyblock.name].data.size = .2
                    ## SETEO OBJETO ACTIVO
                    bpy.context.scene.objects.active = bpy.data.objects["TEXTO_"+keyblock.name]
                    bpy.ops.object.constraint_add(type="COPY_LOCATION")
                    bpy.data.objects["TEXTO_"+keyblock.name].constraints['Copy Location'].target = bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name]
                    bpy.data.objects["TEXTO_"+keyblock.name].constraints['Copy Location'].subtarget = bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].data.bones[keyblock.name].name
                    
                    bpy.ops.object.select_all(action="DESELECT")
                    bpy.data.objects["TEXTO_"+keyblock.name].select = 1 
                    bpy.context.scene.objects.active = bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name]
                    bpy.ops.object.parent_set(type="OBJECT") 
                    
        
        ## EMPARENTA ICONO
        
        bpy.ops.object.select_all(action="DESELECT")
        bpy.data.objects["GRAPHIC_CONTAINER"].select = 1 
        bpy.context.scene.objects.active = bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name]
        bpy.ops.object.parent_set(type="OBJECT")
        
        eval(POSEMODE)  
  
        ## BORRA DRIVERS DE QUE NO SEAN LEFT O RIGHT
        for driver in SEL_OBJ.data.shape_keys.animation_data.drivers:
            if driver.data_path.count("_L") == False and driver.data_path.count("_R") == False :
                SEL_OBJ.data.shape_keys.driver_remove(driver.data_path) 
  
  
  
  
              
        return{"FINISHED"}    
        
##----------------------------CREATE LMR GROUPS-------------------
def createLMRGroups(self, FACTORVG, ADDVG):
    ## SETEO VERTEX MODE EDIT
    bpy.context.window.screen.scene.tool_settings.mesh_select_mode[0] = 1
    bpy.context.window.screen.scene.tool_settings.mesh_select_mode[1] = 0
    bpy.context.window.screen.scene.tool_settings.mesh_select_mode[2] = 0
    
    ## VARIABLES
    ACTOBJ=bpy.context.active_object
    bpy.ops.object.mode_set(mode="EDIT", toggle=False)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode="OBJECT")
    GRUPOS=["_L","_R"]
    MIRRORINDEX=0      
            
    for LADO in GRUPOS:
        if MIRRORINDEX == 0:
            ## SUMO DOS VG
            bpy.ops.object.vertex_group_add()        
            ## ASIGNO TODOS LOS VERTICES AL GRUPO
            bpy.ops.object.mode_set(mode='EDIT', toggle=False)
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.object.vertex_group_assign(new=False)
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='WEIGHT_PAINT', toggle=False)        
            ## SETEO VALORES
            for VERTICE in ACTOBJ.data.vertices:
                VERTICE.groups[-1].weight=(VERTICE.co[0]*FACTORVG)+ADDVG    
            ## RENOMBRO
            ACTOBJ.vertex_groups[-1].name=LADO    
    
        else:
            ## SUMO DOS VG
            bpy.ops.object.vertex_group_add()        
            ## ASIGNO TODOS LOS VERTICES AL GRUPO
            bpy.ops.object.mode_set(mode='EDIT', toggle=False)
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.object.vertex_group_assign(new=False)
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='WEIGHT_PAINT', toggle=False)       
            ## SETEO VALORES
            for VERTICE in ACTOBJ.data.vertices:
                VERTICE.groups[-1].weight=(-VERTICE.co[0]*FACTORVG)+ADDVG         
            ## RENOMBRO
            ACTOBJ.vertex_groups[-1].name=LADO
        ## CAMBIO MIRROR INDEX
        MIRRORINDEX+=1
        
    ## SETEO GRUPO ACTIVO   
    ACTOBJ.vertex_groups.active_index=len(ACTOBJ.vertex_groups)       


class CreaGrupos(bpy.types.Operator):
    bl_idname = "mesh.create_lmr_groups_osc"
    bl_label = "Create LM groups"
    bl_description = "Create LM groups"
    bl_options = {'REGISTER', 'UNDO'}

    FACTORVG= bpy.props.FloatProperty(name="Factor", default=1, min=0, max=1000)
    ADDVG= bpy.props.FloatProperty(name="Addition", default=.5, min=0, max=1000)
    
    def execute(self, context):

        createLMRGroups(self, self.FACTORVG, self.ADDVG)

        return {'FINISHED'}
    
##------------------------------NORMALS OUTSIDE--------------------    
class normalsOutside(bpy.types.Operator):  
    bl_idname = "mesh.normals_outside_osc"
    bl_label = "Normals Outside"
    bl_options =  {"REGISTER","UNDO"}
    def execute(self, context):
        for OBJETO in bpy.context.selected_objects:
            ## SETEA OBJETO ACTIVO
            bpy.data.scenes[0].objects.active = bpy.data.objects[OBJETO.name]
            ## EDICION
            bpy.ops.object.mode_set(mode='EDIT', toggle=False)
            ## SELECCIONA TODOS LOS COMPONENTES 
            bpy.ops.mesh.select_all(action="SELECT")
            ## EXPULSA NORMALES
            bpy.ops.mesh.normals_make_consistent(inside=False)
            ## EDICION
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        return{"FINISHED"}


##------------------------------DISTRIBUTE---------------------------

 

def distributeDef(self, context, X, Y, Z):    

    ## LISTA DE OBJETOS
    OBJETOS = list(bpy.context.selected_objects)

    if X == True:
        ## LISTA VACIA
        LISTOBJ=[]
        
        ## LISTA DE OBJETOS Y NOMBRES
        for OBJETO in OBJETOS:
            LISTOBJ.append((OBJETO.location[0],OBJETO.name))
        
        ## REORDENO
        LISTOBJ.sort()
        
        ## AVERIGUO MINIMO Y MAXIMO
        MIN = min(LISTOBJ)[0]
        MAX = max(LISTOBJ)[0]
        DIF = (MAX - MIN) / (len(OBJETOS)-1)
        TEMPDIF = 0
        
        print(MIN,MAX,DIF,TEMPDIF)
        
        ## ORDENO
        for OBJETO in LISTOBJ:
            bpy.data.objects[OBJETO[1]].location[0]= MIN+TEMPDIF
            TEMPDIF+=DIF
    

    if Y == True:
        ## LISTA VACIA
        LISTOBJ=[]
        
        ## LISTA DE OBJETOS Y NOMBRES
        for OBJETO in OBJETOS:
            LISTOBJ.append((OBJETO.location[1],OBJETO.name))
        
        ## REORDENO
        LISTOBJ.sort()
        
        ## AVERIGUO MINIMO Y MAXIMO
        MIN = min(LISTOBJ)[0]
        MAX = max(LISTOBJ)[0]
        DIF = (MAX - MIN) / (len(OBJETOS)-1)
        TEMPDIF = 0
        
        print(MIN,MAX,DIF,TEMPDIF)
        
        ## ORDENO
        for OBJETO in LISTOBJ:
            bpy.data.objects[OBJETO[1]].location[1]= MIN+TEMPDIF
            TEMPDIF+=DIF
    
    if Z == True:
        ## LISTA VACIA
        LISTOBJ=[]
        
        ## LISTA DE OBJETOS Y NOMBRES
        for OBJETO in OBJETOS:
            LISTOBJ.append((OBJETO.location[2],OBJETO.name))
        
        ## REORDENO
        LISTOBJ.sort()
        
        ## AVERIGUO MINIMO Y MAXIMO
        MIN = min(LISTOBJ)[0]
        MAX = max(LISTOBJ)[0]
        DIF = (MAX - MIN) / (len(OBJETOS)-1)
        TEMPDIF = 0
        
        print(MIN,MAX,DIF,TEMPDIF)
        
        ## ORDENO
        for OBJETO in LISTOBJ:
            bpy.data.objects[OBJETO[1]].location[2]= MIN+TEMPDIF
            TEMPDIF+=DIF
    



      
class DistributeMinMaxApply (bpy.types.Operator):
    bl_idname = "object.distribute_apply_osc"
    bl_label = "Distribute Objects" 
    bl_options =  {"REGISTER","UNDO"}
        
    X=bpy.props.BoolProperty(default=False, name="X")
    Y=bpy.props.BoolProperty(default=False, name="Y")
    Z=bpy.props.BoolProperty(default=False, name="Z")

    def execute(self, context):

        distributeDef(self, context, self.X, self.Y, self.Z)
        
        return{"FINISHED"}            
          


##--------------------------------RENDER LAYER AT TIME----------------------------


def defRenderAll (FRAMETYPE):
        
    LISTMAT=[]
    SCENES=bpy.data.scenes[:]
    ACTSCENE=bpy.context.scene
    FC=bpy.context.scene.frame_current 
    FS=bpy.context.scene.frame_start
    FE=bpy.context.scene.frame_end

    print("---------------------")
           
    ## GUARDO MATERIALES DE OBJETOS EN GRUPOS
    for OBJECT in bpy.data.objects[:]:
        SLOTLIST=[]
        try:
            if OBJECT.type=="MESH" or OBJECT.type == "META":
                for SLOT in OBJECT.material_slots[:]:
                    SLOTLIST.append(SLOT.material)
               
                LISTMAT.append((OBJECT,SLOTLIST))

        except:
            pass
        
  
    for SCENE in SCENES:
        PROPTOLIST=list(eval(SCENE['OVERRIDE']))
        CURSC= SCENE.name 
        PATH = SCENE.render.filepath
        ENDPATH = PATH
        FILEPATH=bpy.data.filepath
        


        
        # CAMBIO SCENE
        bpy.context.window.screen.scene=SCENE
        
        if FRAMETYPE == True:
            bpy.context.scene.frame_start=FC
            bpy.context.scene.frame_end=FC   
            bpy.context.scene.frame_end=FC 
            bpy.context.scene.frame_start=FC
        

        ## SETEO MATERIALES  DE OVERRIDES
        try:
            for OVERRIDE in PROPTOLIST:
                for OBJECT in bpy.data.groups[OVERRIDE[0]].objects[:]:
                    if OBJECT.type == "MESH" or OBJECT.type == "META":
                        for SLOT in OBJECT.material_slots[:]:
                            SLOT.material=bpy.data.materials[OVERRIDE[1]]             
        except:
            pass
         
        if sys.platform.startswith("w"):
            print ("PLATFORM: WINDOWS")
            SCENENAME=(FILEPATH.rsplit("\\")[-1])[:-6]            
        else:
            print ("PLATFORM:LINUX")    
            SCENENAME=(FILEPATH.rsplit("/")[-1])[:-6]

        LAYERLIST=[]
        for layer in SCENE.render.layers:
            if layer.use == 1:
                LAYERLIST.append(layer)
            
        for layers in LAYERLIST:
            for rl in LAYERLIST:
                rl.use= 0

            print("SCENE: "+CURSC)    
            print ("LAYER: "+layers.name)
            print("OVERRIDE: "+str(PROPTOLIST))            
            
            SCENE.render.filepath = PATH+"/"+SCENENAME+"/"+CURSC+"/"+layers.name+"/"+SCENENAME+"_"+SCENE.name+"_"+layers.name+"_"
            SCENE.render.layers[layers.name].use = 1
            bpy.ops.render.render(animation=True, write_still=True, layer=layers.name, scene= SCENE.name)

            print ("DONE")
            print("---------------------")
        
        ## REESTABLECE LOS LAYERS
        for layer in LAYERLIST:
            layer.use = 1
        
        ## RESTAURA EL PATH FINAL
        SCENE.render.filepath = ENDPATH
       
        #RESTAURO MATERIALES  DE OVERRIDES  
        for OBJECT in LISTMAT:
            SLOTIND=0
            try:
                for SLOT in OBJECT[1]:
                    OBJECT[0].material_slots[SLOTIND].material=SLOT
                    SLOTIND+=1
            except:
                print("OUT OF RANGE")
        # RESTAURO FRAMES
        if FRAMETYPE == True:
            SCENE.frame_start=FS
            SCENE.frame_end=FE
            SCENE.frame_end=FE
            SCENE.frame_start=FS
    # RESTAURO SCENE
    bpy.context.window.screen.scene=ACTSCENE      


class renderAll (bpy.types.Operator):
    bl_idname="render.render_layers_at_time_osc"
    bl_label="Render layers at time"
    
    FRAMETYPE=bpy.props.BoolProperty(default=False)

    
    def execute(self,context):
        defRenderAll(self.FRAMETYPE)
        return{"FINISHED"}

class renderAllCF (bpy.types.Operator):
    bl_idname="render.render_layers_at_time_osc_cf"
    bl_label="Render layers at time Current Frame"
    
    FRAMETYPE=bpy.props.BoolProperty(default=True)

    
    def execute(self,context):
        defRenderAll(self.FRAMETYPE)
        return{"FINISHED"}



##--------------------------------RENDER SELECTED SCENES----------------------------


bpy.types.Scene.OscSelScenes = bpy.props.StringProperty(default="[]")


def defRenderSelected(FRAMETYPE):    
        
    ACTSCENE=bpy.context.scene
    LISTMAT=[]
    SCENES=bpy.data.scenes[:]
    SCENELIST=list(eval(bpy.context.scene.OscSelScenes))
    FC=bpy.context.scene.frame_current    
    FS=bpy.context.scene.frame_start
    FE=bpy.context.scene.frame_end    
    ## GUARDO MATERIALES DE OBJETOS EN GRUPOS
    for OBJECT in bpy.data.objects[:]:
        SLOTLIST=[]
        try:
            if OBJECT.type=="MESH" or OBJECT.type == "META":
                for SLOT in OBJECT.material_slots[:]:
                    SLOTLIST.append(SLOT.material)
               
                LISTMAT.append((OBJECT,SLOTLIST))
        except:
            pass
        
  
    for SCENE in SCENES:
        if SCENE.name in SCENELIST:
            PROPTOLIST=list(eval(SCENE['OVERRIDE']))
            CURSC= SCENE.name 
            PATH = SCENE.render.filepath
            ENDPATH = PATH
            FILEPATH=bpy.data.filepath

            print("---------------------")

            # CAMBIO SCENE
            bpy.context.window.screen.scene=SCENE
            
            if FRAMETYPE == True:
                bpy.context.scene.frame_start=FC
                bpy.context.scene.frame_end=FC   
                bpy.context.scene.frame_end=FC 
                bpy.context.scene.frame_start=FC
        
            ## SETEO MATERIALES  DE OVERRIDES
            try:
                for OVERRIDE in PROPTOLIST:
                    for OBJECT in bpy.data.groups[OVERRIDE[0]].objects[:]:
                        if OBJECT.type == "MESH" or OBJECT.type == "META":
                            for SLOT in OBJECT.material_slots[:]:
                                SLOT.material=bpy.data.materials[OVERRIDE[1]]             
            except:
                pass
             
            if sys.platform.startswith("w"):
                print ("PLATFORM: WINDOWS")
                SCENENAME=(FILEPATH.rsplit("\\")[-1])[:-6]            
            else:
                print ("PLATFORM:LINUX")    
                SCENENAME=(FILEPATH.rsplit("/")[-1])[:-6]

            LAYERLIST=[]
            for layer in SCENE.render.layers:
                if layer.use == 1:
                    LAYERLIST.append(layer)
                
            for layers in LAYERLIST:
                for rl in LAYERLIST:
                    rl.use= 0
                    
                print("SCENE: "+CURSC)    
                print ("LAYER: "+layers.name)
                print("OVERRIDE: "+str(PROPTOLIST))  
            
                SCENE.render.filepath = PATH+"/"+SCENENAME+"/"+CURSC+"/"+layers.name+"/"+SCENENAME+"_"+SCENE.name+"_"+layers.name+"_"
                SCENE.render.layers[layers.name].use = 1
                bpy.ops.render.render(animation=True, layer=layers.name, write_still=True, scene= SCENE.name)

                print ("DONE")
                print("---------------------")
                
            ## REESTABLECE LOS LAYERS
            for layer in LAYERLIST:
                layer.use = 1
            
            ## RESTAURA EL PATH FINAL
            SCENE.render.filepath = ENDPATH
           
            #RESTAURO MATERIALES  DE OVERRIDES  
            for OBJECT in LISTMAT:
                SLOTIND=0
                try:
                    for SLOT in OBJECT[1]:
                        OBJECT[0].material_slots[SLOTIND].material=SLOT
                        SLOTIND+=1
                except:
                    print("OUT OF RANGE")
                    
            # RESTAURO FRAMES
            if FRAMETYPE == True:
                SCENE.frame_start=FS
                SCENE.frame_end=FE
                SCENE.frame_end=FE
                SCENE.frame_start=FS                    
                    
                    
    # RESTAURO SCENE
    bpy.context.window.screen.scene=ACTSCENE


class renderSelected (bpy.types.Operator):
    bl_idname="render.render_selected_scenes_osc"
    bl_label="Render Selected Scenes"

    FRAMETYPE=bpy.props.BoolProperty(default=False)
 
    def execute(self,context):
        defRenderSelected(self.FRAMETYPE)
        return{"FINISHED"}
    
class renderSelectedCF (bpy.types.Operator):
    bl_idname="render.render_selected_scenes_osc_cf"
    bl_label="Render Selected Scenes Curent Frame"

    FRAMETYPE=bpy.props.BoolProperty(default=True)

    def execute(self,context):
        defRenderSelected(self.FRAMETYPE)
        return{"FINISHED"}



##--------------------------------RENDER CURRENT SCENE----------------------------


def defRenderCurrent (FRAMETYPE):
    LISTMAT=[]
    SCENE=bpy.context.scene
    FC=bpy.context.scene.frame_current    
    FS=bpy.context.scene.frame_start
    FE=bpy.context.scene.frame_end 
    
    print("---------------------")
        
    ## GUARDO MATERIALES DE OBJETOS EN GRUPOS
    for OBJECT in bpy.data.objects[:]:
        SLOTLIST=[]
        try:
            if OBJECT.type=="MESH" or OBJECT.type == "META":
                for SLOT in OBJECT.material_slots[:]:
                    SLOTLIST.append(SLOT.material)               
                LISTMAT.append((OBJECT,SLOTLIST))
        except:
            pass        


    PROPTOLIST=list(eval(SCENE['OVERRIDE']))
    CURSC= SCENE.name 
    PATH = SCENE.render.filepath
    ENDPATH = PATH
    FILEPATH=bpy.data.filepath


    if FRAMETYPE == True:
        bpy.context.scene.frame_start=FC
        bpy.context.scene.frame_end=FC   
        bpy.context.scene.frame_end=FC 
        bpy.context.scene.frame_start=FC  
    
    ## SETEO MATERIALES  DE OVERRIDES
    try:
        for OVERRIDE in PROPTOLIST:
            for OBJECT in bpy.data.groups[OVERRIDE[0]].objects[:]:
                if OBJECT.type == "MESH" or OBJECT.type == "META":
                    for SLOT in OBJECT.material_slots[:]:
                        SLOT.material=bpy.data.materials[OVERRIDE[1]]             
    except:
        pass
     
    if sys.platform.startswith("w"):
        print ("PLATFORM: WINDOWS")
        SCENENAME=(FILEPATH.rsplit("\\")[-1])[:-6]            
    else:
        print ("PLATFORM:LINUX")    
        SCENENAME=(FILEPATH.rsplit("/")[-1])[:-6]

    LAYERLIST=[]
    for layer in SCENE.render.layers:
        if layer.use == 1:
            LAYERLIST.append(layer)
        
    for layers in LAYERLIST:
        for rl in LAYERLIST:
            rl.use= 0

        print("SCENE: "+CURSC)    
        print ("LAYER: "+layers.name)
        print("OVERRIDE: "+str(PROPTOLIST))


        SCENE.render.filepath = PATH+"/"+SCENENAME+"/"+CURSC+"/"+layers.name+"/"+SCENENAME+"_"+SCENE.name+"_"+layers.name+"_"
        SCENE.render.layers[layers.name].use = 1
        bpy.ops.render.render(animation=True, layer=layers.name, write_still=1, scene= SCENE.name)
        
        print ("DONE")
        print("---------------------")
    
    ## REESTABLECE LOS LAYERS
    for layer in LAYERLIST:
        layer.use = 1
    
    ## RESTAURA EL PATH FINAL
    SCENE.render.filepath = ENDPATH
   
    #RESTAURO MATERIALES  DE OVERRIDES  
    for OBJECT in LISTMAT:
        SLOTIND=0
        try:
            for SLOT in OBJECT[1]:
                OBJECT[0].material_slots[SLOTIND].material=SLOT
                SLOTIND+=1
        except:
            print("FUERA DE RANGO")    

    # RESTAURO FRAMES
    if FRAMETYPE == True:
        SCENE.frame_start=FS
        SCENE.frame_end=FE
        SCENE.frame_end=FE
        SCENE.frame_start=FS 


class renderCurrent (bpy.types.Operator):
    bl_idname="render.render_current_scene_osc"
    bl_label="Render Current Scene"

    FRAMETYPE=bpy.props.BoolProperty(default=False)

    def execute(self,context):
        
        defRenderCurrent(self.FRAMETYPE)
        
        return{"FINISHED"}


class renderCurrentCF (bpy.types.Operator):
    bl_idname="render.render_current_scene_osc_cf"
    bl_label="Render Current Scene Current Frame"

    FRAMETYPE=bpy.props.BoolProperty(default=True)

    def execute(self,context):
               
        defRenderCurrent(self.FRAMETYPE)
        
        return{"FINISHED"}

   
##--------------------------RENDER CROP----------------------
## SETEO EL STATUS DEL PANEL PARA EL IF 
bpy.types.Scene.RcropStatus = bpy.props.BoolProperty(default=0)

## CREO DATA PARA EL SLIDER
bpy.types.Scene.rcPARTS = bpy.props.IntProperty(default=0,min=2,max=50,step=1) 


class renderCrop (bpy.types.Operator):
    bl_idname="render.render_crop_osc"
    bl_label="Render Crop: Render!"
    def execute(self,context):

        ##AVERIGUO EL SISTEMA
        if sys.platform.startswith("w"):
            print ("PLATFORM: WINDOWS")
            VARSYSTEM= "\\"          
        else:
            print ("PLATFORM:LINUX")    
            VARSYSTEM= "/"

        
        ## NOMBRE DE LA ESCENA
        SCENENAME=(bpy.data.filepath.rsplit(VARSYSTEM)[-1]).rsplit(".")[0]        
        
        ## CREA ARRAY
        PARTES=[]
        START=1
        PARTS=bpy.context.scene.rcPARTS
        PARTS=PARTS+1
        while START < PARTS:
            PARTES.append(START)
            START=START+1
        print(PARTES)
        

        
        ##SETEO VARIABLE PARA LA FUNCION DE RENDER
        NUMERODECORTE=1
        
        ##ESCENA ACTIVA
        SCACT = bpy.context.scene
        
        ## SETEO CROP
        bpy.data.scenes[SCACT.name].render.use_crop_to_border = 1
        bpy.data.scenes[SCACT.name].render.use_border = 1
        
        ##A VERIGUO RES EN Y
        RESY=bpy.data.scenes[SCACT.name].render.resolution_y
        
        ## AVERIGUO EL PATH DE LA ESCENA
        OUTPUTFILEPATH=bpy.data.scenes[SCACT.name].render.filepath
        bpy.context.scene.render.filepath = OUTPUTFILEPATH+bpy.context.scene.name
        

        
        ## CUANTAS PARTES HARA
        LENPARTES=len(PARTES)
        
        ## DIVIDE 1 SOBRE LA CANTIDAD DE PARTES
        DIVISOR=1/PARTES[LENPARTES-1]
        
        ## SETEA VARIABLE DEL MARCO MINIMO Y MAXIMO
        CMIN=0
        CMAX=DIVISOR
        
        ## REMUEVE EL ULTIMO OBJETO DEL ARRAY PARTES
        PARTESRESTADA = PARTES.pop(LENPARTES-1)
        
        ## SETEA EL MINIMO Y EL MAXIMO CON LOS VALORES DE ARRIBA
        bpy.data.scenes[SCACT.name].render.border_min_y = CMIN
        bpy.data.scenes[SCACT.name].render.border_max_y = CMAX

        
        ##SETEA EL OUTPUT PARA LA PRIMERA PARTE
        OUTPUTFILEPATH+bpy.context.scene.name
        bpy.context.scene.render.filepath = OUTPUTFILEPATH+SCENENAME+VARSYSTEM+SCENENAME+"_PART"+str(PARTES[0])+"_"
        
        ##RENDER PRIMERA PARTE
        bpy.ops.render.render(animation=True)
        bpy.context.scene.render.filepath
        
        ##SUMO UN NUMERO AL CORTE
        NUMERODECORTE = NUMERODECORTE+1      
        
        
        ## RENDER!
        for PARTE in PARTES:
            ## SUMA A LOS VALORES DEL CROP
            CMIN = CMIN + DIVISOR
            CMAX = CMAX + DIVISOR
            print ("EL CROP ES DE "+str(CMIN)+" A "+str(CMAX))
            ## SETEA BORDE
            bpy.data.scenes[SCACT.name].render.border_min_y = CMIN
            bpy.data.scenes[SCACT.name].render.border_max_y = CMAX
            ## SETEA EL OUTPUT
            bpy.context.scene.render.filepath = OUTPUTFILEPATH+SCENENAME+VARSYSTEM+SCENENAME+"_PART"+str(NUMERODECORTE)+"_"
            print ("EL OUTPUT DE LA FUNCION ES " +bpy.context.scene.render.filepath)
            ## PRINTEA EL NUMERO DE CORTE
            print (PARTE)
            ## RENDER
            bpy.ops.render.render(animation=True)
            ## SUMO NUMERO DE CORTE
            NUMERODECORTE = NUMERODECORTE+1    
        
        
        ## REESTABLEZCO EL FILEPATH
        bpy.context.scene.render.filepath = OUTPUTFILEPATH  
        
        
        print ("RENDER TERMINADO")
                
        return{"FINISHED"}


    
##------------------------ SEARCH AND SELECT ------------------------

## SETEO VARIABLE DE ENTORNO
bpy.types.Scene.SearchAndSelectOt = bpy.props.StringProperty(default="Object name initials")


class SearchAndSelectOt(bpy.types.Operator):
    bl_idname = "object.search_and_select_osc"
    bl_label = "Search And Select"
    bl_options =  {"REGISTER","UNDO"}
    def execute(self, context): 
        for objeto in bpy.context.scene.objects:
            variableNombre = bpy.context.scene.SearchAndSelectOt
            if objeto.name.startswith(variableNombre) == True :
                objeto.select = 1
                print("Selecciona:" + str(objeto.name))
        return{"FINISHED"}

##-------------------------RENAME OBJECTS----------------------------------    

## CREO VARIABLE
bpy.types.Scene.RenameObjectOt = bpy.props.StringProperty(default="Type here")

class renameObjectsOt (bpy.types.Operator):
    bl_idname = "object.rename_objects_osc"
    bl_label = "Rename Objects" 
    bl_options =  {"REGISTER","UNDO"}
    def execute(self,context):

        ## LISTA
        listaObj = bpy.context.selected_objects
        
        
        
        for objeto in listaObj:
            print (objeto.name)
            objeto.name = bpy.context.scene.RenameObjectOt
        return{"FINISHED"}



##-------------------------RESYM VG---------------------------------- 




class resymVertexGroups (bpy.types.Operator):
    bl_idname = "mesh.resym_vertex_weights_osc"
    bl_label = "Resym Vertex Weights" 
    bl_options =  {"REGISTER","UNDO"}
    def execute(self,context):
        
        OBACTIVO=bpy.context.active_object
        VGACTIVO=OBACTIVO.vertex_groups.active.index
        MENORESACERO=[]
        MAYORESACERO=[]
        MENORESACEROYSG=[]
        
        
        ## LISTA DE LOS VERTICES QUE ESTAN EN GRUPOS
        VERTICESENGRUPOS=[0]
        for vertice in OBACTIVO.data.vertices:
            if len(vertice.groups.items()) > 0:
                VERTICESENGRUPOS.append(vertice.index)  
                
                
                
        ## VERTICES MENORES A CERO
        for verticeindex in VERTICESENGRUPOS:
            for indices in OBACTIVO.data.vertices[verticeindex].groups:
                if indices.group == VGACTIVO:     
                    if bpy.context.active_object.data.vertices[verticeindex].co[0] < 0:
                        MENORESACERO.append(bpy.context.active_object.data.vertices[verticeindex].index)
                        
        ## VERTICES MENORES A CERO Y SIN GRUPO
        for vertice in OBACTIVO.data.vertices:
            if vertice.co[0] < 0:
                MENORESACEROYSG.append(vertice.index)               
                
        
        ## VERTICES MAYORES A CERO
        for verticeindex in VERTICESENGRUPOS:
            for indices in OBACTIVO.data.vertices[verticeindex].groups:
                if indices.group == VGACTIVO:     
                    if bpy.context.active_object.data.vertices[verticeindex].co[0] > 0:
                        MAYORESACERO.append(bpy.context.active_object.data.vertices[verticeindex].index)
        
        ## TE MUESTRA LAS LISTAS
        print("-------------VERTICES EN GRUPOS-----------")        
        print (VERTICESENGRUPOS)
        print("-------------MENORES A CERO-----------")
        print (MENORESACERO)
        print("-------------MENORES A CERO SIN GRUPO-----------")
        print (MENORESACEROYSG)
        print("-------------MAYORES A CERO-----------")
        print (MAYORESACERO)
        
        
        ## SETEA WORK INDEX      
        for vertices in MAYORESACERO:
            for indices in OBACTIVO.data.vertices[vertices].groups:
                if indices.group == VGACTIVO: 
                    WORKINDEX = indices.group  
        
        ## DESELECCIONO COMPONENTES
        bpy.ops.object.mode_set(mode="EDIT",toggle=0)
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.mode_set(mode="OBJECT",toggle=0)
        
        
        ## SETEO GRUPO
        for verticemenor in MENORESACEROYSG:
            for verticemayor in MAYORESACERO:
                if OBACTIVO.data.vertices[verticemenor].co[0] == -OBACTIVO.data.vertices[verticemayor].co[0]:
                    if OBACTIVO.data.vertices[verticemenor].co[1] == OBACTIVO.data.vertices[verticemayor].co[1]:   
                        if OBACTIVO.data.vertices[verticemenor].co[2] == OBACTIVO.data.vertices[verticemayor].co[2]: 
                            OBACTIVO.data.vertices[verticemenor].select = 1    
        
        ## ASSIGNO AL GRUPO
        bpy.ops.object.mode_set(mode="EDIT",toggle=0)
        bpy.ops.object.vertex_group_assign(new=False)
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.mode_set(mode="OBJECT",toggle=0)
        
        ## MODO PINTURA
        bpy.ops.object.mode_set(mode="WEIGHT_PAINT",toggle=0)
        
        
        ##--------->> VUELVO A CREAR GRUPOS YA QUE LOS INDICES CAMBIARON
        MENORESACERO=[]
        MAYORESACERO=[]
        
        
        ## LISTA DE LOS VERTICES QUE ESTAN EN GRUPOS
        VERTICESENGRUPOS=[0]
        for vertice in OBACTIVO.data.vertices:
            if len(vertice.groups.items()) > 0:
                VERTICESENGRUPOS.append(vertice.index)  
                
                
                
        ## VERTICES MENORES A CERO
        for verticeindex in VERTICESENGRUPOS:
            for indices in OBACTIVO.data.vertices[verticeindex].groups:
                if indices.group == VGACTIVO:     
                    if bpy.context.active_object.data.vertices[verticeindex].co[0] < 0:
                        MENORESACERO.append(bpy.context.active_object.data.vertices[verticeindex].index)
        
        
        
        
        ## VERTICES MAYORES A CERO
        for verticeindex in VERTICESENGRUPOS:
            for indices in OBACTIVO.data.vertices[verticeindex].groups:
                if indices.group == VGACTIVO:     
                    if bpy.context.active_object.data.vertices[verticeindex].co[0] > 0:
                        MAYORESACERO.append(bpy.context.active_object.data.vertices[verticeindex].index)
        
        
        ## SETEO WEIGHT     
        for verticemenor in MENORESACERO:
            for verticemayor in MAYORESACERO:
                if OBACTIVO.data.vertices[verticemenor].co[0] == -OBACTIVO.data.vertices[verticemayor].co[0]:
                    if OBACTIVO.data.vertices[verticemenor].co[1] == OBACTIVO.data.vertices[verticemayor].co[1]:   
                        if OBACTIVO.data.vertices[verticemenor].co[2] == OBACTIVO.data.vertices[verticemayor].co[2]: 
                            VARINMAY = 0
                            VARINMEN = 0
                            while  OBACTIVO.data.vertices[verticemayor].groups[VARINMAY].group != VGACTIVO:
                                VARINMAY = VARINMAY+1
                            while  OBACTIVO.data.vertices[verticemenor].groups[VARINMEN].group != VGACTIVO:
                                VARINMEN = VARINMEN+1
                            ##print("Varinmay: "+str(VARINMAY)+" .Varinmen "+str(VARINMEN))  
                            OBACTIVO.data.vertices[verticemenor].groups[VARINMEN].weight = OBACTIVO.data.vertices[verticemayor].groups[VARINMAY].weight
                            
        
                          
        print("===============(TERMINADO)=============")       
        return{"FINISHED"}



##------------------------ SHAPES LAYOUT SYMMETRICA ------------------------



class CreateLayoutAsymmetrical(bpy.types.Operator):
    bl_idname = "mesh.create_asymmetrical_layout_osc"
    bl_label = "Asymmetrical Layout"
    bl_options =  {"REGISTER","UNDO"}
    def execute(self, context): 
                
        SEL_OBJ= bpy.context.active_object
        LISTA_KEYS = bpy.context.active_object.data.shape_keys.key_blocks
        
        ##MODOS
        EDITMODE = "bpy.ops.object.mode_set(mode='EDIT')"
        OBJECTMODE = "bpy.ops.object.mode_set(mode='OBJECT')"
        POSEMODE = "bpy.ops.object.mode_set(mode='POSE')"
        
        ##INDICE DE DRIVERS
        varindex = 0
        
        ##CREA NOMBRES A LA ARMATURE
        amtas = bpy.data.armatures.new("ArmatureData")
        obas = bpy.data.objects.new("RIG_LAYOUT_"+SEL_OBJ.name, amtas)
        
        ##LINK A LA ESCENA
        scn = bpy.context.scene
        scn.objects.link(obas)
        scn.objects.active = obas
        obas.select = True
        
        
        
        
        
        eval(EDITMODE)
        gx = 0
        gy = 0
        
        
        
        for keyblock in LISTA_KEYS:
            print ("KEYBLOCK EN CREACION DE HUESOS "+keyblock.name)
        
                
            if keyblock.name[-2:] != "_L":
                if keyblock.name[-2:] != "_R":
        
                    ##CREA HUESOS
                
                    bone = amtas.edit_bones.new(keyblock.name)
                    bone.head = (gx,0,0)
                    bone.tail = (gx,0,1)
                    gx = gx+2.2
                    bone = amtas.edit_bones.new(keyblock.name+"_CTRL")
                    bone.head = (gy,0,0)
                    bone.tail = (gy,0,0.2)
                    gy = gy+2.2     
                  
                    ##SETEA ARMATURE ACTIVA
                    bpy.context.scene.objects.active = bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name]
                    bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].select = 1
                    ##DESELECCIONA (modo edit)
                    eval(EDITMODE)
                    bpy.ops.armature.select_all(action="DESELECT")
                    
                    ##EMPARENTA HUESOS
                
                    ##HUESO ACTIVO
                    eval(OBJECTMODE)
                    bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].data.bones.active = bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].data.bones[keyblock.name] 
                    ##MODO EDIT
                    eval(EDITMODE)       
                    ##DESELECCIONA (modo edit)
                    bpy.ops.armature.select_all(action="DESELECT")    
                    ##MODO OBJECT  
                    eval(OBJECTMODE)    
                    ##SELECCIONA UN HUESO
                    bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].data.bones[keyblock.name+"_CTRL"].select = 1
                    eval(EDITMODE)    
                    ##EMPARENTA
                    bpy.ops.armature.parent_set(type="OFFSET")
                    ##DESELECCIONA (modo edit)
                    bpy.ops.armature.select_all(action="DESELECT")      
                     
                    ##CREA DRIVERS Y LOS CONECTA
                    keyblock.driver_add("value")
                    keyblock.driver_add("value")        
                    
                    SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.expression = "-var+var_001"
                    SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables.new()
                    SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables.new()
                    SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables['var'].targets[0].id  = bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name] 
                    SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables['var'].targets[0].bone_target   = bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].data.bones[(keyblock.name)+"_CTRL"].name      
                    SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables['var'].type = 'TRANSFORMS' 
                    SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables['var'].targets[0].transform_space= "LOCAL_SPACE"                 
                    SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables['var'].targets[0].transform_type= "LOC_X"  
                    SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables['var_001'].targets[0].id = bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name]
                    SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables['var_001'].targets[0].bone_target   = bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].data.bones[(keyblock.name)+"_CTRL"].name    
                    SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables['var_001'].type = 'TRANSFORMS'            
                    SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables['var_001'].targets[0].transform_space= "LOCAL_SPACE"        
                    SEL_OBJ.data.shape_keys.animation_data.drivers[varindex].driver.variables['var_001'].targets[0].transform_type= "LOC_Y" 
                          
                    
                    varindex = varindex + 1 
        
        
        
             
                
                
                
                
        ## CREO DATA PARA SLIDERS
        
        ## creo data para los contenedores
        verticess = [(-.1,1,0),(.1,1,0),(.1,0,0),(-.1,0,0)]
        edgess = [(0,1),(1,2),(2,3),(3,0)]
        
        mesh = bpy.data.meshes.new(keyblock.name+"_data_container")
        object = bpy.data.objects.new("GRAPHIC_CONTAINER_AS", mesh)
        bpy.context.scene.objects.link(object)
        mesh.from_pydata(verticess,edgess,[])
        
        ## PONGO LOS LIMITES Y SETEO ICONOS
        for keyblock in LISTA_KEYS:
            print ("KEYBLOCK EN CREACION DE HUESOS "+keyblock.name)
            ## SETEO ICONOS
            bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].pose.bones[keyblock.name].custom_shape = bpy.data.objects['GRAPHIC_CONTAINER_AS']
            bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].pose.bones[keyblock.name+"_CTRL"].custom_shape = bpy.data.objects['GRAPHIC_CONTAINER_AS']
            ## SETEO CONSTRAINTS
            eval(OBJECTMODE)
            bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].data.bones.active = bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].data.bones[keyblock.name+"_CTRL"]
            ## SUMO CONSTRAINT
            eval(POSEMODE)
            bpy.ops.pose.constraint_add(type="LIMIT_LOCATION")
            
            bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].pose.bones[keyblock.name+"_CTRL"].constraints['Limit Location'].min_x = 0
            bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].pose.bones[keyblock.name+"_CTRL"].constraints['Limit Location'].use_min_x = 1
            bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].pose.bones[keyblock.name+"_CTRL"].constraints['Limit Location'].min_z = 0
            bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].pose.bones[keyblock.name+"_CTRL"].constraints['Limit Location'].use_min_z = 1
            bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].pose.bones[keyblock.name+"_CTRL"].constraints['Limit Location'].min_y = 0
            bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].pose.bones[keyblock.name+"_CTRL"].constraints['Limit Location'].use_min_y = 1
            
            bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].pose.bones[keyblock.name+"_CTRL"].constraints['Limit Location'].max_x =  0
            bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].pose.bones[keyblock.name+"_CTRL"].constraints['Limit Location'].use_max_x = 1
            bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].pose.bones[keyblock.name+"_CTRL"].constraints['Limit Location'].max_z =  0
            bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].pose.bones[keyblock.name+"_CTRL"].constraints['Limit Location'].use_max_z = 1
            bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].pose.bones[keyblock.name+"_CTRL"].constraints['Limit Location'].max_y =  1
            bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].pose.bones[keyblock.name+"_CTRL"].constraints['Limit Location'].use_max_y = 1
            
            bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].pose.bones[keyblock.name+"_CTRL"].constraints['Limit Location'].owner_space  = "LOCAL"
                    
        ## PARA QUE EL TEXTO FUNCIONE PASAMOS A OBJECT MODE
        eval(OBJECTMODE)
        
        ## TEXTOS
        for keyblock in LISTA_KEYS:
            print ("KEYBLOCK EN TEXTOS "+keyblock.name)            
            ## creo tipografias
            bpy.ops.object.text_add(location=(0,0,0))
            bpy.data.objects['Text'].data.body = keyblock.name
            bpy.data.objects['Text'].name = "TEXTO_"+keyblock.name
            bpy.data.objects["TEXTO_"+keyblock.name].rotation_euler[0] = math.pi/2
            bpy.data.objects["TEXTO_"+keyblock.name].location.x = -1
            bpy.data.objects["TEXTO_"+keyblock.name].location.z = -1
            bpy.data.objects["TEXTO_"+keyblock.name].data.size = .2
            ## SETEO OBJETO ACTIVO
            bpy.context.scene.objects.active = bpy.data.objects["TEXTO_"+keyblock.name]
            bpy.ops.object.constraint_add(type="COPY_LOCATION")
            bpy.data.objects["TEXTO_"+keyblock.name].constraints['Copy Location'].target = bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name]
            bpy.data.objects["TEXTO_"+keyblock.name].constraints['Copy Location'].subtarget = bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].data.bones[keyblock.name].name
            
            bpy.ops.object.select_all(action="DESELECT")
            bpy.data.objects["TEXTO_"+keyblock.name].select = 1 
            bpy.context.scene.objects.active = bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name]
            bpy.ops.object.parent_set(type="OBJECT") 
            
        
        ## EMPARENTA ICONO
        
        bpy.ops.object.select_all(action="DESELECT")
        bpy.data.objects["GRAPHIC_CONTAINER_AS"].select = 1 
        bpy.context.scene.objects.active = bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name]
        bpy.ops.object.parent_set(type="OBJECT")
        
        eval(POSEMODE)  
                  
        

        return{"FINISHED"}


##------------------------ SHAPES LAYOUT SYMMETRICA ------------------------

class saveIncremental(bpy.types.Operator):
    bl_idname = "file.save_incremental_osc"
    bl_label = "Save Incremental File"
    bl_options =  {"REGISTER","UNDO"}
    def execute(self, context):     
        ##SETEO VARIABLES
        filepath=bpy.data.filepath
        
        ##SI LA RUTA CONTIENE _V
        if filepath.count("_v") == 0:
            print("La escena no tiene numero")
            stpath=filepath.rsplit(".blend")
            incrementalValue=1
            print("El output es: "+ stpath[0]+"_v0"+str(incrementalValue)+".blend")
            output=stpath[0]+"_v0"+str(incrementalValue)+".blend"
            bpy.ops.wm.save_as_mainfile(filepath=output)  
            
            
        else:    
            sfilepath=filepath.split("_v")[0]
            idfilepath=(filepath.split("_v")[1])[:-6]
            stpath=sfilepath+"_v"
            incrementalValue=int(idfilepath)    
            
            if len(idfilepath) > 1 :
                if idfilepath[0] == "0":
                    print("El primer valor es cero")
                    incrementalValue+=1
                    print("El output es: "+ sfilepath+"_v0"+str(incrementalValue)+".blend")
                    output=sfilepath+"_v0"+str(incrementalValue)+".blend"
                    bpy.ops.wm.save_as_mainfile(filepath=output)
                else:
                    print("El primer valor no es cero")
                    incrementalValue+=1
                    print("El output es: "+ sfilepath+"_v"+str(incrementalValue)+".blend")  
                    output=sfilepath+"_v0"+str(incrementalValue)+".blend"
                    bpy.ops.wm.save_as_mainfile(filepath=output)              
            
            if len(idfilepath) <= 1 :
                print("No tiene primer valor")  
                incrementalValue+=1
                print("El output es: "+ sfilepath+"_v0"+str(incrementalValue)+".blend")  
                output=sfilepath+"_v0"+str(incrementalValue)+".blend"
                bpy.ops.wm.save_as_mainfile(filepath=output)      
        return{"FINISHED"}  
    
##------------------------ REPLACE FILE PATHS ------------------------ 

bpy.types.Scene.oscSearchText = bpy.props.StringProperty(default="Search Text")
bpy.types.Scene.oscReplaceText = bpy.props.StringProperty(default="Replace Text")

class replaceFilePath(bpy.types.Operator):
    bl_idname = "file.replace_file_path_osc"
    bl_label = "Replace File Path"
    bl_options =  {"REGISTER","UNDO"}
    def execute(self, context):    
        TEXTSEARCH=bpy.context.scene.oscSearchText
        TEXTREPLACE=bpy.context.scene.oscReplaceText
        
        for image in bpy.data.images:
            if image.filepath != '':
                if image.filepath.count(TEXTSEARCH) == 2:
                    FILEPATH=image.filepath
                    FOLDER=FILEPATH.partition(TEXTSEARCH)[0]+TEXTREPLACE
                    PREFIX=FILEPATH.partition(TEXTSEARCH)[-1].partition(TEXTSEARCH)[0]+TEXTREPLACE+FILEPATH.partition(TEXTSEARCH)[-1].partition(TEXTSEARCH)[2]        
                    print("Reemplazo el path de: "+image.name)
                    image.filepath=FOLDER+PREFIX   

                if image.filepath.count(TEXTSEARCH) == 1:
                    FILEPATH=image.filepath
                    FOLDER=FILEPATH.partition(TEXTSEARCH)[0]+TEXTREPLACE+FILEPATH.partition(TEXTSEARCH)[-1]
                        
                    print("Reemplazo el path de: "+image.name)
                    image.filepath= FOLDER

                     
        return{"FINISHED"}



##------------------------ DUPLICATE OBJECTS SYMMETRY ------------------------ 

def duplicateSymmetrical (self, disconect):
    for objeto in bpy.context.selected_objects:
                
        OBSEL=objeto 
        
        #DESELECT AND SELECT OBJETO
        bpy.ops.object.select_all(action='DESELECT') 
        objeto.select = 1   
        bpy.context.scene.objects.active=objeto
        
        #DUPLICA
        bpy.ops.object.duplicate(linked=1)
        
        #OBJETO ACTIVO
        OBDUP=bpy.context.active_object 
           
        print(OBDUP)
        
        #SUMA DRIVER
        OBDUP.driver_add("location")
        
        ## LOCATIONS
        
        #EXPRESION
        OBDUP.animation_data.drivers[0].driver.expression = "-var"
        #CREA VARIABLE
        OBDUP.animation_data.drivers[0].driver.variables.new()
        #MODIFICO VARIABLE
        OBDUP.animation_data.drivers[0].driver.variables[0].type = "TRANSFORMS"
        OBDUP.animation_data.drivers[0].driver.variables[0].targets[0].id = objeto
        OBDUP.animation_data.drivers[0].driver.variables[0].targets[0].transform_type = 'LOC_X'
        
        #EXPRESION
        OBDUP.animation_data.drivers[1].driver.expression = "var"
        #CREA VARIABLE
        OBDUP.animation_data.drivers[1].driver.variables.new()
        #MODIFICO VARIABLE
        OBDUP.animation_data.drivers[1].driver.variables[0].type = "TRANSFORMS"
        OBDUP.animation_data.drivers[1].driver.variables[0].targets[0].id = objeto
        OBDUP.animation_data.drivers[1].driver.variables[0].targets[0].transform_type = 'LOC_Y'
        
        #EXPRESION
        OBDUP.animation_data.drivers[2].driver.expression = "var"
        #CREA VARIABLE
        OBDUP.animation_data.drivers[2].driver.variables.new()
        #MODIFICO VARIABLE
        OBDUP.animation_data.drivers[2].driver.variables[0].type = "TRANSFORMS"
        OBDUP.animation_data.drivers[2].driver.variables[0].targets[0].id = objeto
        OBDUP.animation_data.drivers[2].driver.variables[0].targets[0].transform_type = 'LOC_Z'
        
        ## SCALE
        OBDUP.driver_add("scale")
        
        
        #EXPRESION
        OBDUP.animation_data.drivers[3].driver.expression = "-var"
        #CREA VARIABLE
        OBDUP.animation_data.drivers[3].driver.variables.new()
        #MODIFICO VARIABLE
        OBDUP.animation_data.drivers[3].driver.variables[0].type = "TRANSFORMS"
        OBDUP.animation_data.drivers[3].driver.variables[0].targets[0].id = objeto
        OBDUP.animation_data.drivers[3].driver.variables[0].targets[0].transform_type = 'SCALE_X'
                        
        #EXPRESION
        OBDUP.animation_data.drivers[4].driver.expression = "var"
        #CREA VARIABLE
        OBDUP.animation_data.drivers[4].driver.variables.new()
        #MODIFICO VARIABLE
        OBDUP.animation_data.drivers[4].driver.variables[0].type = "TRANSFORMS"
        OBDUP.animation_data.drivers[4].driver.variables[0].targets[0].id = objeto
        OBDUP.animation_data.drivers[4].driver.variables[0].targets[0].transform_type = 'SCALE_Y'
                        
                        
        #EXPRESION
        OBDUP.animation_data.drivers[5].driver.expression = "var"
        #CREA VARIABLE
        OBDUP.animation_data.drivers[5].driver.variables.new()
        #MODIFICO VARIABLE
        OBDUP.animation_data.drivers[5].driver.variables[0].type = "TRANSFORMS"
        OBDUP.animation_data.drivers[5].driver.variables[0].targets[0].id = objeto
        OBDUP.animation_data.drivers[5].driver.variables[0].targets[0].transform_type = 'SCALE_Z'
                                                                                                      

        ## ROTATION
        OBDUP.driver_add("rotation_euler")
        
        
        #EXPRESION
        OBDUP.animation_data.drivers[6].driver.expression = "var"
        #CREA VARIABLE
        OBDUP.animation_data.drivers[6].driver.variables.new()
        #MODIFICO VARIABLE
        OBDUP.animation_data.drivers[6].driver.variables[0].type = "TRANSFORMS"
        OBDUP.animation_data.drivers[6].driver.variables[0].targets[0].id = objeto
        OBDUP.animation_data.drivers[6].driver.variables[0].targets[0].transform_type = 'ROT_X'
                        
        #EXPRESION
        OBDUP.animation_data.drivers[7].driver.expression = "-var"
        #CREA VARIABLE
        OBDUP.animation_data.drivers[7].driver.variables.new()
        #MODIFICO VARIABLE
        OBDUP.animation_data.drivers[7].driver.variables[0].type = "TRANSFORMS"
        OBDUP.animation_data.drivers[7].driver.variables[0].targets[0].id = objeto
        OBDUP.animation_data.drivers[7].driver.variables[0].targets[0].transform_type = 'ROT_Y'
                        
                        
        #EXPRESION
        OBDUP.animation_data.drivers[8].driver.expression = "-var"
        #CREA VARIABLE
        OBDUP.animation_data.drivers[8].driver.variables.new()
        #MODIFICO VARIABLE
        OBDUP.animation_data.drivers[8].driver.variables[0].type = "TRANSFORMS"
        OBDUP.animation_data.drivers[8].driver.variables[0].targets[0].id = objeto
        OBDUP.animation_data.drivers[8].driver.variables[0].targets[0].transform_type = 'ROT_Z'               

        if disconect != True:
            bpy.ops.object.make_single_user(obdata=True, object=True) 
            bpy.context.active_object.driver_remove("location") 
            bpy.context.active_object.driver_remove("rotation_euler") 
            bpy.context.active_object.driver_remove("scale")     


class oscDuplicateSymmetricalOp (bpy.types.Operator):
    bl_idname = "object.duplicate_object_symmetry_osc"
    bl_label = "Oscurart Duplicate Symmetrical"  
    bl_options =  {"REGISTER","UNDO"}
    
    desconecta = bpy.props.BoolProperty(name="Keep Connection", default=True)
    
    def execute(self,context):
        
        duplicateSymmetrical(self, self.desconecta)  
                      
        return{"FINISHED"}  
        

##---------------------------BATCH MAKER------------------


def defoscBatchMaker(TYPE):
    # REVISO SISTEMA
    if sys.platform.startswith("w"):
        print ("PLATFORM: WINDOWS")
        SYSBAR="\\" 
        EXTSYS=".bat" 
        QUOTES='"'          
    else:
        print ("PLATFORM:LINUX")    
        SYSBAR="/"
        EXTSYS=".sh"
        QUOTES=''
    
    print(TYPE)
    
    # CREO VARIABLES
    FILENAME=bpy.data.filepath.rpartition(SYSBAR)[-1].rpartition(".")[0]
    BINDIR=bpy.app[4]
    SHFILE= bpy.data.filepath.rpartition(SYSBAR)[0]+SYSBAR+FILENAME+EXTSYS
    FILEBATCH=open(SHFILE,"w")
    FILESC=open(bpy.data.filepath.rpartition(SYSBAR)[0]+SYSBAR+"osRlat.py","w")
    FILESSC=open(bpy.data.filepath.rpartition(SYSBAR)[0]+SYSBAR+"osRSlat.py","w")

    
    # DEFINO ARCHIVO DE BATCH
    FILEBATCH.writelines("%s%s%s -b %s -x 1 -o %s -P %s%s.py  -s %s -e %s -a" % (QUOTES,BINDIR,QUOTES,bpy.data.filepath,bpy.context.scene.render.filepath,bpy.data.filepath.rpartition(SYSBAR)[0]+SYSBAR,TYPE,str(bpy.context.scene.frame_start),str(bpy.context.scene.frame_end)) )
    FILEBATCH.close()        
    
    # SI ES LINUX LE DOY PERMISOS CHMOD
    if EXTSYS == ".sh":
        os.chmod(SHFILE, stat.S_IRWXU)
        
    
    
    # DEFINO LOS ARCHIVOS DE SCRIPT
    FILESC.writelines("import bpy \nbpy.ops.render.render_layers_at_time_osc()\nbpy.ops.wm.quit_blender()" )
    FILESC.close()    
    FILESSC.writelines("import bpy \nbpy.ops.render.render_selected_scenes_osc()\nbpy.ops.wm.quit_blender()" )
    FILESSC.close() 

class oscBatchMaker (bpy.types.Operator):
    bl_idname = "file.create_batch_maker_osc"
    bl_label = "Make render batch" 
    bl_options = {'REGISTER', 'UNDO'}
        

    type = bpy.props.EnumProperty(
            name="Render Mode",
            description="Select Render Mode.",
            items=(('osRlat', "All Scenes", "Render All Layers At Time"),
                   ('osRSlat', "Selected Scenes", "Render Only The Selected Scenes")),
            default='osRlat',
            )
   
    
    def execute(self,context):
        defoscBatchMaker(self.type)
        return{"FINISHED"}


##---------------------------REMOVE MODIFIERS Y APPLY MODIFIERS------------------

class oscRemModifiers (bpy.types.Operator):
    bl_idname = "object.modifiers_remove_osc"
    bl_label = "Remove modifiers" 
    bl_options =  {"REGISTER","UNDO"}
    def execute(self,context):
        for objeto in bpy.context.selected_objects:
            for modificador in objeto.modifiers:
                print(modificador.type)
                bpy.context.scene.objects.active=objeto
                bpy.ops.object.modifier_remove(modifier=modificador.name)
        return{"FINISHED"}

class oscApplyModifiers (bpy.types.Operator):
    bl_idname = "object.modifiers_apply_osc"
    bl_label = "Apply modifiers" 
    bl_options =  {"REGISTER","UNDO"}
    def execute(self,context):
        for objeto in bpy.context.selected_objects:
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.scene.objects.active=objeto
            objeto.select=True            
            bpy.ops.object.make_single_user(type='SELECTED_OBJECTS', object=True, obdata=True, material=False, texture=False, animation=False)
            for modificador in objeto.modifiers:
                print(modificador.type)
                # SUBSURF
                if modificador.type == 'SUBSURF':
                    if modificador.levels > 0:
                        bpy.ops.object.modifier_apply(apply_as="DATA",modifier=modificador.name)
                    else:
                        bpy.ops.object.modifier_remove(modifier=modificador.name)          
                # MESH DEFORM
                if modificador.type == 'MESH_DEFORM':
                    if modificador.object != None:
                        bpy.ops.object.modifier_apply(apply_as="DATA",modifier=modificador.name)
                    else:
                        bpy.ops.object.modifier_remove(modifier=modificador.name)      
                # ARRAY 
                if modificador.type == 'ARRAY':
                    bpy.ops.object.modifier_apply(apply_as="DATA",modifier=modificador.name)
                # BEVEL 
                if modificador.type == 'BEVEL':
                    bpy.ops.object.modifier_apply(apply_as="DATA",modifier=modificador.name) 
                # BOOLEAN
                if modificador.type == 'BOOLEAN':
                    if modificador.object != None:
                        bpy.ops.object.modifier_apply(apply_as="DATA",modifier=modificador.name)
                    else:
                        bpy.ops.object.modifier_remove(modifier=modificador.name)                      
                # BUILD
                if modificador.type == 'BUILD':
                    bpy.ops.object.modifier_apply(apply_as="DATA",modifier=modificador.name)            
                # DECIMATE
                if modificador.type == 'DECIMATE':
                    bpy.ops.object.modifier_apply(apply_as="DATA",modifier=modificador.name) 
                # EDGE SPLIT
                if modificador.type == 'EDGE_SPLIT':
                    bpy.ops.object.modifier_apply(apply_as="DATA",modifier=modificador.name)             
                # MASK
                if modificador.type == 'MASK':
                    bpy.ops.object.modifier_apply(apply_as="DATA",modifier=modificador.name)              
                # MIRROR
                if modificador.type == 'MIRROR':
                    bpy.ops.object.modifier_apply(apply_as="DATA",modifier=modificador.name) 
                # MULTIRESOLUTION
                if modificador.type == 'MULTIRES':
                    bpy.ops.object.modifier_apply(apply_as="DATA",modifier=modificador.name)
                # SCREW
                if modificador.type == 'SCREW':
                    bpy.ops.object.modifier_apply(apply_as="DATA",modifier=modificador.name)
                # SOLIDIFY
                if modificador.type == 'SOLIDIFY':
                    bpy.ops.object.modifier_apply(apply_as="DATA",modifier=modificador.name)     
                # UV_PROJECT
                if modificador.type == 'UV_PROJECT':
                    bpy.ops.object.modifier_apply(apply_as="DATA",modifier=modificador.name)              
                # ARMATURE
                if modificador.type == 'ARMATURE':
                    if modificador.object != None:
                        bpy.ops.object.modifier_apply(apply_as="DATA",modifier=modificador.name)
                    else:
                        bpy.ops.object.modifier_remove(modifier=modificador.name) 
                # CAST
                if modificador.type == 'CAST':
                    bpy.ops.object.modifier_apply(apply_as="DATA",modifier=modificador.name) 
                # CURVE
                if modificador.type == 'CURVE':
                    if modificador.object != None:
                        bpy.ops.object.modifier_apply(apply_as="DATA",modifier=modificador.name)
                    else:
                        bpy.ops.object.modifier_remove(modifier=modificador.name)                              
                # DISPLACE
                if modificador.type == 'DISPLACE':
                    if modificador.texture != None:
                        bpy.ops.object.modifier_apply(apply_as="DATA",modifier=modificador.name)
                    else:
                        bpy.ops.object.modifier_remove(modifier=modificador.name)                  
                # HOOK
                if modificador.type == 'HOOK':
                    if modificador.object != None:
                        bpy.ops.object.modifier_apply(apply_as="DATA",modifier=modificador.name)
                    else:
                        bpy.ops.object.modifier_remove(modifier=modificador.name)                   
                # LATTICE
                if modificador.type == 'LATTICE':
                    if modificador.object != None:
                        bpy.ops.object.modifier_apply(apply_as="DATA",modifier=modificador.name)
                    else:
                        bpy.ops.object.modifier_remove(modifier=modificador.name)                
                # SHRINK WRAP
                if modificador.type == 'SHRINKWRAP':
                    if modificador.target != None:
                        bpy.ops.object.modifier_apply(apply_as="DATA",modifier=modificador.name)
                    else:
                        bpy.ops.object.modifier_remove(modifier=modificador.name)                  
                # SIMPLE DEFORM
                if modificador.type == 'SIMPLE_DEFORM':
                    bpy.ops.object.modifier_apply(apply_as="DATA",modifier=modificador.name)                
                # SMOOTH
                if modificador.type == 'SMOOTH':
                    bpy.ops.object.modifier_apply(apply_as="DATA",modifier=modificador.name)                  
                # WARP
                if modificador.type == 'WARP':
                    if modificador.object_from != None:
                        if modificador.object_to != None:
                            bpy.ops.object.modifier_apply(apply_as="DATA",modifier=modificador.name)
                    else:
                        bpy.ops.object.modifier_remove(modifier=modificador.name)                 
                # WAVE
                if modificador.type == 'WAVE':
                    bpy.ops.object.modifier_apply(apply_as="DATA",modifier=modificador.name) 
        return{"FINISHED"}


        
##---------------------------SHAPES TO OBJECTS------------------

class ShapeToObjects (bpy.types.Operator):
    bl_idname = "object.shape_key_to_objects_osc"
    bl_label = "Shapes To Objects" 
    bl_options =  {"REGISTER","UNDO"}
    def execute(self,context):
        OBJACT=bpy.context.active_object    
        for SHAPE in OBJACT.data.shape_keys.key_blocks[:]:
            print(SHAPE.name)
            bpy.ops.object.shape_key_clear()
            SHAPE.value=1
            mesh=OBJACT.to_mesh(bpy.context.scene, True, 'PREVIEW')
            object=bpy.data.objects.new(SHAPE.name, mesh)
            bpy.context.scene.objects.link(object)
        return{"FINISHED"}
    
    

##--------------------------OVERRIDES-----------------------------

## PARA ESCENAS NUEVAS

for scene in bpy.data.scenes[:]:
    try:
        scene['OVERRIDE']
    except:
        scene['OVERRIDE']="[]"



class OverridesOp (bpy.types.Operator):
    bl_idname = "render.overrides_set_list"
    bl_label = "Overrides set list" 
    bl_options =  {"REGISTER","UNDO"}
    def execute(self,context):
        for scene in bpy.data.scenes[:]:
            try:
                scene['OVERRIDE']
            except:
                scene['OVERRIDE']="[]"
        return{"FINISHED"}        


###------------------------IMPORT EXPORT GROUPS--------------------

class OscExportVG (bpy.types.Operator):
    bl_idname = "file.export_groups_osc"
    bl_label = "Export Groups" 
    bl_options =  {"REGISTER","UNDO"}
    def execute(self,context):

        OBSEL=bpy.context.active_object
        
        if os.sys.platform.count("win"):
            print("WINDOWS")
            BAR = "\\"
        else:
            print("LINUX")
            BAR = "/"  
        # VARIABLES
        FILEPATH=bpy.data.filepath        
        FILE=open(FILEPATH.rpartition(BAR)[0]+BAR+OBSEL.name+".xml", mode="w")
        VERTLIST=[]

        LENVER=len(OBSEL.data.vertices)        
        
        for VG in OBSEL.vertex_groups:
            BONELIST=[]
            for VERTICE in range(0,LENVER):
                try:
                    BONELIST.append((VERTICE,VG.weight(VERTICE),VG.name,))
                except:
                    pass
            VERTLIST.append(BONELIST)
        
        ## CREO LA LISTA CON LOS NOMBRES DE LOS GRUPOS
        NAMEGROUPLIST=[]
        for VG in OBSEL.vertex_groups:
            NAMEGROUPLIST.append(VG.name)
        
        ## AGREGO LOS NOMBRES A LA LISTA
        VERTLIST.append(NAMEGROUPLIST)
        
        ## GUARDO Y CIERRO
        FILE.writelines(str(VERTLIST))
        FILE.close()
        
        ## ---- CREO OTRO ARCHIVO PARA LA DATA ----
        # VARIABLES
        FILEPATH=bpy.data.filepath        
        FILE=open(FILEPATH.rpartition(BAR)[0]+BAR+OBSEL.name+"_DATA.xml", mode="w")        
        
        DATAVER=[]
        
        for VERT in OBSEL.data.vertices[:]:
            TEMP=0
            VGTEMP=0
            LISTVGTEMP=[]            
            
            for GROUP in VERT.groups[:]:
                LISTVGTEMP.append((GROUP.group,VGTEMP))
                VGTEMP+=1
            
            LISTVGTEMP=sorted(LISTVGTEMP)
            for GROUP in VERT.groups[:]:
                DATAVER.append((VERT.index,TEMP,VERT.groups[LISTVGTEMP[TEMP][1]].weight))
                TEMP+=1

        
        ## GUARDO Y CIERRO
        FILE.writelines(str(DATAVER))
        FILE.close()        
        
        return{"FINISHED"}
        
class OscImportVG (bpy.types.Operator):
    bl_idname = "file.import_groups_osc"
    bl_label = "Import Groups" 
    bl_options =  {"REGISTER","UNDO"}
    def execute(self,context):

        OBSEL=bpy.context.active_object
	# AVERIGUO EL SISTEMA
        if os.sys.platform.count("win"):
            print("WINDOWS")
            BAR = "\\"
        else:
            print("LINUX")
            BAR = "/" 
        # VARIABLES 
        FILEPATH=bpy.data.filepath
        FILE=open(FILEPATH.rpartition(BAR)[0]+BAR+OBSEL.name+".xml", mode="r")
        VERTLIST=FILE.readlines(0)
        VERTLIST=eval(VERTLIST[0])
        VERTLISTR=VERTLIST[:-1]
        GROUPLIST=VERTLIST[-1:]
        VGINDEX=0      
        
        ## MODO OBJECT
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        
        for GROUP in GROUPLIST[0]:
            #CREO GRUPO
            bpy.ops.object.vertex_group_add()
            #CAMBIO NOMBRE
            OBSEL.vertex_groups[-1].name=GROUP 
         
             
       
        
        for VG in OBSEL.vertex_groups[:]:            
            # SETEO VG
            bpy.ops.object.vertex_group_set_active(group=VG.name)            
            # EDIT    
            bpy.ops.object.mode_set(mode='EDIT')               
            # DESELECT
            bpy.ops.mesh.select_all(action='DESELECT')                          
            # OBJECT   
            bpy.ops.object.mode_set(mode='OBJECT')              
            # SELECCIONO LOS VERTICES             
            for VERTI in VERTLISTR[VG.index]:
                OBSEL.data.vertices[VERTI[0]].select=1                   
            ## SETEO EL VALOR DEL PESO
            bpy.context.tool_settings.vertex_group_weight=1                                  
            # EDIT    
            bpy.ops.object.mode_set(mode='EDIT')         
            ## ASIGNO
            bpy.ops.object.vertex_group_assign(new=False)

        # CIERRO
        FILE.close()
        
        
        ## ----------- LEVANTO DATA ----
        # VARIABLES 
        FILEPATH=bpy.data.filepath
        FILE=open(FILEPATH.rpartition(BAR)[0]+BAR+OBSEL.name+"_DATA.xml", mode="r")
        DATAPVER=FILE.readlines(0)
        DATAPVER=eval(DATAPVER[0])
        
        # PASO A MODO OBJECT      
        bpy.ops.object.mode_set(mode='OBJECT')        
        
        #for VERT in DATAPVER:
        for VERT in DATAPVER:
            OBSEL.data.vertices[VERT[0]].groups[VERT[1]].weight=VERT[2]       
        
        # CIERRO
        FILE.close()
        
   
        # PASO A MODO PINTURA DE PESO       
        bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
        return{"FINISHED"}


## ------------------------------------ RELINK OBJECTS--------------------------------------   


def relinkObjects (self):  
    
    LISTSCENE=[]
    
    for SCENE in bpy.data.scenes[:]:
        if bpy.selection_osc[-1] in SCENE.objects[:]:
            LISTSCENE.append(SCENE)    

    OBJECTS = bpy.selection_osc[:-1]
    
    ## REMUEVO ESCENA ACTIVA
    LISTSCENE.remove(bpy.context.scene)
    
    ## DESELECT
    bpy.ops.object.select_all(action='DESELECT')
    
    ## SELECT
    for OBJETO in OBJECTS:
        if OBJETO.users != len(bpy.data.scenes):
            print(OBJETO.name)
            OBJETO.select = True
        
    ## LINK
    for SCENE in LISTSCENE:
        bpy.ops.object.make_links_scene(scene=SCENE.name)           
    

class OscRelinkObjectsBetween (bpy.types.Operator):
    bl_idname = "objects.relink_objects_between_scenes"
    bl_label = "Relink Objects Between Scenes" 
    bl_options =  {"REGISTER","UNDO"}  
    
   
      
    def execute (self, context):
        relinkObjects(self)        
        return {'FINISHED'}
    


## ------------------------------------ COPY GROUPS AND LAYERS--------------------------------------   


def CopyObjectGroupsAndLayers (self): 
              
    OBSEL=bpy.selection_osc[:]
    GLOBALLAYERS=str(OBSEL[-1].layers[:])
    ACTSCENE=bpy.context.scene
    GROUPS=OBSEL[-1].users_group
    ERROR=False    
    
    for OBJECT in OBSEL[:-1]:
        for scene in bpy.data.scenes[:]:
            try:
                ISINLAYER=False
                bpy.context.window.screen.scene=scene
                
                if OBSEL[-1] in bpy.context.scene.objects[:]:
                    scene.objects[OBJECT.name].layers=OBSEL[-1].layers
                else:
                    scene.objects[OBJECT.name].layers=list(eval(GLOBALLAYERS))
                    ISINLAYER=True
                    
                
                scene.objects.active=OBJECT
                
                for GROUP in GROUPS:
                    bpy.ops.object.group_link(group=GROUP.name)      
                
                if ISINLAYER == False:                          
                    print("-- %s was successfully copied in %s" % (OBJECT.name,scene.name))
                else:
                    print("++ %s copy data from %s in %s" % (OBJECT.name,ACTSCENE.name,scene.name))    
            except:
                print ("** %s was not copied in %s" % (OBJECT.name,scene.name))  
                ERROR = True 
    bpy.context.window.screen.scene=ACTSCENE 
    
    if ERROR == False:
        self.report({'INFO'}, "All Objects were Successfully Copied")
    else:
        self.report({'WARNING'}, "Some Objects Could not be Copied")    
           

class OscCopyObjectGAL (bpy.types.Operator):
    bl_idname = "objects.copy_objects_groups_layers"
    bl_label = "Copy Groups And Layers" 
    bl_options =  {"REGISTER","UNDO"}  
   
      
    def execute (self, context):
        CopyObjectGroupsAndLayers (self)        
        return {'FINISHED'}
    
    
## ------------------------------------ APPLY AND RESTORE OVERRIDES --------------------------------------   

   

class OscApplyOverrides(bpy.types.Operator):
    bl_idname = "render.apply_overrides"
    bl_label = "Apply Overrides in this Scene" 
    bl_options =  {"REGISTER","UNDO"}  
   
      
    def execute (self, context):
        LISTMAT=[]
        PROPTOLIST=list(eval(bpy.context.scene['OVERRIDE']))        
        # REVISO SISTEMA
        if sys.platform.startswith("w"):
            print ("PLATFORM: WINDOWS")
            SYSBAR="\\"           
        else:
            print ("PLATFORM:LINUX")    
            SYSBAR="/"        
        FILEPATH=bpy.data.filepath
        ACTIVEFOLDER=FILEPATH.rpartition(SYSBAR)[0]
        ENTFILEPATH= "%s%s%s_OVERRIDE.xml" %  (ACTIVEFOLDER,SYSBAR,bpy.context.scene.name)
        XML=open(ENTFILEPATH ,mode="w")        
        ## GUARDO MATERIALES DE OBJETOS EN GRUPOS
        for OBJECT in bpy.data.objects[:]:
            SLOTLIST=[]
            try:
                if OBJECT.type=="MESH" or OBJECT.type == "META":
                    for SLOT in OBJECT.material_slots[:]:
                        SLOTLIST.append(SLOT.material)                   
                    LISTMAT.append((OBJECT,SLOTLIST))        
            except:
                pass        
        try:
            for OVERRIDE in PROPTOLIST:
                for OBJECT in bpy.data.groups[OVERRIDE[0]].objects[:]:
                    if OBJECT.type == "MESH" or OBJECT.type == "META":
                        for SLOT in OBJECT.material_slots[:]:
                            SLOT.material=bpy.data.materials[OVERRIDE[1]]             
        except:
            pass
        
        XML.writelines(str(LISTMAT))
        XML.close()       
        return {'FINISHED'}   
    
class OscRestoreOverrides(bpy.types.Operator):
    bl_idname = "render.restore_overrides"
    bl_label = "Restore Overrides in this Scene" 
    bl_options =  {"REGISTER","UNDO"}  
   
      
    def execute (self, context):
        # REVISO SISTEMA
        if sys.platform.startswith("w"):
            print ("PLATFORM: WINDOWS")
            SYSBAR="\\"           
        else:
            print ("PLATFORM:LINUX")    
            SYSBAR="/"   
        
        FILEPATH=bpy.data.filepath
        ACTIVEFOLDER=FILEPATH.rpartition(SYSBAR)[0]
        ENTFILEPATH= "%s%s%s_OVERRIDE.xml" %  (ACTIVEFOLDER,SYSBAR,bpy.context.scene.name)
        XML=open(ENTFILEPATH,mode="r")
        RXML=XML.readlines(0)
        
        LISTMAT=list(eval(RXML[0]))     
        
        # RESTAURO MATERIALES  DE OVERRIDES  
        for OBJECT in LISTMAT:
            SLOTIND=0
            try:
                for SLOT in OBJECT[1]:
                    OBJECT[0].material_slots[SLOTIND].material=SLOT
                    SLOTIND+=1
            except:
                print("OUT OF RANGE")
        # CIERRO
        XML.close()
       
        return {'FINISHED'}     
    
    
## ------------------------------------ CHECK OVERRIDES --------------------------------------   

class OscCheckOverrides (bpy.types.Operator):
    bl_idname = "render.check_overrides"
    bl_label = "Check Overrides" 
    bl_options =  {"REGISTER","UNDO"}  
   
      
    def execute (self, context):
        GROUPI=False
        GLOBAL=0
        GLOBALERROR=0
        
        print("==== STARTING CHECKING ====")
        print("")
        
        for SCENE in bpy.data.scenes[:]:            
            MATLIST=[]
            MATI=False       
                 
            for MATERIAL in bpy.data.materials[:]:
                MATLIST.append(MATERIAL.name)
                
            GROUPLIST=[]
            for GROUP in bpy.data.groups[:]:
                if GROUP.users > 0:
                    GROUPLIST.append(GROUP.name)
                
            print("   %s Scene is checking" % (SCENE.name))
            
            for OVERRIDE in list(eval(SCENE['OVERRIDE'])):
                # REVISO OVERRIDES EN GRUPOS
                if OVERRIDE[0] in GROUPLIST:
                    pass
                else:                    
                    print("** %s group are in conflict." % (OVERRIDE[0]))
                    GROUPI=True
                    GLOBALERROR+=1
                # REVISO OVERRIDES EN GRUPOS    
                if OVERRIDE[1] in MATLIST:
                    pass
                else:                 
                    print("** %s material are in conflict." % (OVERRIDE[1]))
                    MATI=True
                    GLOBALERROR+=1
            
            if MATI is False:
                print("-- Materials are ok.") 
            else:    
                GLOBAL+=1
            if GROUPI is False:
                print("-- Groups are ok.")   
            else:    
                GLOBAL+=1
      
        if GLOBAL < 1:     
            self.report({'INFO'}, "Materials And Groups are Ok")     
        if GLOBALERROR > 0:
            self.report({'WARNING'}, "Override Error: Look in the Console")    
        print("")

        return {'FINISHED'}
          

## ------------------------------------ SELECTION -------------------------------------- 
bpy.selection_osc=[]

def select_osc():
    if bpy.context.mode=="OBJECT":
        obj = bpy.context.object
        sel = len(bpy.context.selected_objects)
	

        if sel==0:
            bpy.selection_osc=[]
        else:
            if sel==1:
                bpy.selection_osc=[]
                bpy.selection_osc.append(obj)
            elif sel>len(bpy.selection_osc):
                for sobj in bpy.context.selected_objects:
                    if (sobj in bpy.selection_osc)==False:
                        bpy.selection_osc.append(sobj)

            elif sel<len(bpy.selection_osc):
                for it in bpy.selection_osc:
                    if (it in bpy.context.selected_objects)==False:
                        bpy.selection_osc.remove(it)

class OscSelection(bpy.types.Header):
    bl_label = "Selection Osc"
    bl_space_type = "VIEW_3D"

    def __init__(self):
        select_osc()

    def draw(self, context):
        """
        layout = self.layout
        row = layout.row()
        row.label("Sels: "+str(len(bpy.selection_osc))) 
        """
        
##======================================================================================FIN DE SCRIPTS    
    
    
def register():
    pass

def unregister():
    pass

if __name__ == "__main__":
    register()



## REGISTRA CLASSES
bpy.utils.register_class(OscPanelControl)
bpy.utils.register_class(OscPanelObject)
bpy.utils.register_class(OscPanelMesh)
bpy.utils.register_class(OscPanelShapes)
bpy.utils.register_class(OscPanelRender)
bpy.utils.register_class(OscPanelFiles)
bpy.utils.register_class(OscPanelOverrides)
bpy.utils.register_class(SelectMenor)
bpy.utils.register_class(CreaGrupos)
bpy.utils.register_class(CreaShapes)
bpy.utils.register_class(normalsOutside)
bpy.utils.register_class(resym)
bpy.utils.register_class(reloadImages)
bpy.utils.register_class(renderAll)
bpy.utils.register_class(renderAllCF)
bpy.utils.register_class(renderCrop)
bpy.utils.register_class(SearchAndSelectOt)
bpy.utils.register_class(CreaShapesLayout)
bpy.utils.register_class(renameObjectsOt)
bpy.utils.register_class(resymVertexGroups)
bpy.utils.register_class(CreateLayoutAsymmetrical)
bpy.utils.register_class(DistributeMinMaxApply)
bpy.utils.register_class(saveIncremental)
bpy.utils.register_class(replaceFilePath)
bpy.utils.register_class(oscDuplicateSymmetricalOp)
bpy.utils.register_class(oscBatchMaker)
bpy.utils.register_class(oscRemModifiers)
bpy.utils.register_class(oscApplyModifiers)
bpy.utils.register_class(ShapeToObjects)
bpy.utils.register_class(OverridesOp)
bpy.utils.register_class(OscExportVG )
bpy.utils.register_class(OscImportVG )
bpy.utils.register_class(renderCurrent)
bpy.utils.register_class(renderCurrentCF)
bpy.utils.register_class(renderSelected)
bpy.utils.register_class(renderSelectedCF)
bpy.utils.register_class(OscRelinkObjectsBetween)
bpy.utils.register_class(OscCopyObjectGAL) 
bpy.utils.register_class(OscApplyOverrides)
bpy.utils.register_class(OscRestoreOverrides)
bpy.utils.register_class(OscCheckOverrides)
bpy.utils.register_class(OscSelection)
