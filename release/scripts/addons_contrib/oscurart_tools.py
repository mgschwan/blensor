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
    "author": "Oscurart, CodemanX",
    "version": (3,0),
    "blender": (2, 6, 3),
    "location": "View3D > Tools > Oscurart Tools",
    "description": "Tools for objects, render, shapes, and files.",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/3D_interaction/Oscurart_Tools",
    "tracker_url": "",
    "category": "Object"}

import bpy
import math
import sys
import os
import stat
import bmesh
import time
import random

## CREA PANELES EN TOOLS

# VARIABLES DE ENTORNO
bpy.types.Scene.osc_object_tools = bpy.props.BoolProperty(default=False)
bpy.types.Scene.osc_mesh_tools = bpy.props.BoolProperty(default=False)
bpy.types.Scene.osc_shapes_tools = bpy.props.BoolProperty(default=False)
bpy.types.Scene.osc_render_tools = bpy.props.BoolProperty(default=False)
bpy.types.Scene.osc_files_tools = bpy.props.BoolProperty(default=False)
bpy.types.Scene.osc_overrides_tools = bpy.props.BoolProperty(default=False)

# PANEL DE CONTROL
class OscPanelControl(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = "Oscurart Tools"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self,context):
        active_obj = context.active_object
        layout = self.layout

        col = layout.column(align=1)
        col.prop(bpy.context.scene, "osc_object_tools", text="Object", icon="OBJECT_DATAMODE")
        col.prop(bpy.context.scene, "osc_mesh_tools", text="Mesh", icon="EDITMODE_HLT")
        col.prop(bpy.context.scene, "osc_shapes_tools", text="Shapes", icon="SHAPEKEY_DATA")
        col.prop(bpy.context.scene, "osc_render_tools", text="Render", icon="SCENE")
        col.prop(bpy.context.scene, "osc_files_tools", text="Files", icon="IMASEL")
        col.prop(bpy.context.scene, "osc_overrides_tools", text="Overrides", icon="GREASEPENCIL")


# POLLS
class OscPollObject():
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    @classmethod
    def poll(cls, context):
        return context.scene.osc_object_tools


class OscPollMesh():
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    @classmethod
    def poll(cls, context):
        return context.scene.osc_mesh_tools


class OscPollShapes():
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    @classmethod
    def poll(cls, context):
        return context.scene.osc_shapes_tools

class OscPollRender():
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    @classmethod
    def poll(cls, context):
        return context.scene.osc_render_tools

class OscPollFiles():
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    @classmethod
    def poll(cls, context):
        return context.scene.osc_files_tools

class OscPollOverrides():
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    @classmethod
    def poll(cls, context):
        return context.scene.osc_overrides_tools


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
        colrow.operator("objects.relink_objects_between_scenes", icon="LINKED")
        colrow.operator("objects.copy_objects_groups_layers", icon="LINKED")
        colrow = col.row(align=1)
        colrow.prop(bpy.context.scene, "SearchAndSelectOt", text="")
        colrow.operator("object.search_and_select_osc", icon="ZOOM_SELECTED")
        colrow = col.row(align=1)
        colrow.prop(bpy.context.scene, "RenameObjectOt", text="")
        colrow.operator("object.rename_objects_osc", icon="SHORTDISPLAY")
        col.operator("object.duplicate_object_symmetry_osc", icon="OBJECT_DATAMODE", text="Duplicate Symmetry")
        col.operator("object.distribute_osc", icon="OBJECT_DATAMODE", text="Distribute")
        colrow = col.row(align=1)
        colrow.operator("object.modifiers_remove_osc", icon="MODIFIER", text="Remove Modifiers")
        colrow.operator("object.modifiers_apply_osc", icon="MODIFIER", text="Apply Modifiers")


class OscPanelMesh(OscPollMesh, bpy.types.Panel):
    bl_idname = "Oscurart Mesh Tools"
    bl_label = "Mesh Tools"

    def draw(self, context):
        active_obj = context.active_object
        layout = self.layout
        col = layout.column(align=1)
        row = col.row()

        col.operator("mesh.select_side_osc", icon="VERTEXSEL")
        col.operator("mesh.normals_outside_osc", icon="SNAP_NORMAL")
        colrow=col.row(align=1)
        colrow.operator("mesh.resym_save_map", icon="UV_SYNC_SELECT")
        colrow=col.row(align=1)
        colrow.operator("mesh.resym_mesh", icon="UV_SYNC_SELECT", text="Resym Mesh") 
        colrow.operator("mesh.resym_vertex_weights_osc", icon="UV_SYNC_SELECT")     
        colrow=col.row(align=1)
        colrow.operator("mesh.reconst_osc", icon="UV_SYNC_SELECT")        
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

        col.operator("object.shape_key_to_objects_osc", icon="OBJECT_DATAMODE")
        col.operator("mesh.create_lmr_groups_osc", icon="GROUP_VERTEX")
        col.operator("mesh.split_lr_shapes_osc", icon="SHAPEKEY_DATA")
        colrow=col.row()
        colrow.operator("mesh.create_symmetrical_layout_osc", icon="SETTINGS")
        colrow.operator("mesh.create_asymmetrical_layout_osc", icon="SETTINGS")

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
        colrow.operator("render.render_layers_at_time_osc", icon="RENDER_STILL", text="All Scenes")
        colrow.operator("render.render_layers_at_time_osc_cf", icon="RENDER_STILL", text="> Frame")
        colrow = col.row()
        colrow.operator("render.render_current_scene_osc", icon="RENDER_STILL", text="Active Scene")
        colrow.operator("render.render_current_scene_osc_cf", icon="RENDER_STILL", text="> Frame")
        colrow = col.row(align=1)
        colrow.prop(bpy.context.scene, "OscSelScenes", text="")
        colrow.operator("render.render_selected_scenes_osc", icon="RENDER_STILL", text="Selected Scenes")
        colrow.operator("render.render_selected_scenes_osc_cf", icon="RENDER_STILL", text="> Fame")

        colrow = col.row(align=1)
        colrow.prop(bpy.context.scene, "rcPARTS", text="Render Crop Parts")
        colrow.operator("render.render_crop_osc", icon="RENDER_REGION")


class OscPanelFiles(OscPollFiles, bpy.types.Panel):
    bl_idname = "Oscurart Files Tools"
    bl_label = "Files Tools"

    def draw(self, context):
        active_obj = context.active_object
        layout = self.layout
        col = layout.column(align=1)

        colrow = col.row()
        colrow.operator("file.save_incremental_osc", icon="NEW")
        colrow.operator("image.reload_images_osc", icon="IMAGE_COL")
        colrow = col.row(align=1)
        colrow.prop(bpy.context.scene, "oscSearchText", text="")
        colrow.prop(bpy.context.scene, "oscReplaceText", text="")
        col.operator("file.replace_file_path_osc", icon="SHORTDISPLAY")


class OscPanelOverrides(OscPollOverrides, bpy.types.Panel):
    bl_idname = "Oscurart Overrides"
    bl_label = "Overrides Tools"

    def draw(self, context):
        layout = self.layout

        obj = context.object

        col = layout.box().column(align=1)

        colrow = col.row()
        col.operator("render.overrides_set_list", text="Create Override List", icon="GREASEPENCIL")
        col.label(text="Active Scene: " + bpy.context.scene.name)
        col.label(text="Example: [[Group,Material]]")
        col.prop(bpy.context.scene, '["OVERRIDE"]', text="")
        col.operator("render.check_overrides", text="Check List", icon="ZOOM_ALL")       

        boxcol=layout.box().column(align=1)
        boxcol.label(text="Danger Zone")
        boxcolrow=boxcol.row()
        boxcolrow.operator("render.apply_overrides", text="Apply Overrides", icon="ERROR")
        boxcolrow.operator("render.restore_overrides", text="Restore Overrides", icon="ERROR")


    


##---------------------------RELOAD IMAGES------------------

class reloadImages (bpy.types.Operator):
    bl_idname = "image.reload_images_osc"
    bl_label = "Reload Images"
    bl_options = {"REGISTER", "UNDO"}
    def execute(self,context):
        for imgs in bpy.data.images:
            imgs.reload()
        return {'FINISHED'}

##-----------------------------RECONST---------------------------

def defReconst(self, OFFSET, SUBD):

    ##EDIT
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)

    ##SETEO VERTEX MODE
    bpy.context.tool_settings.mesh_select_mode = (True, False, False)

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
        if abs(vertice.co[0]) < OFFSET:
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


class reConst (bpy.types.Operator):
    bl_idname = "mesh.reconst_osc"
    bl_label = "ReConst Mesh"
    bl_options = {"REGISTER", "UNDO"}
    OFFSET=bpy.props.FloatProperty(name="Offset", default=0.001, min=-0, max=0.1)
    SUBD=bpy.props.IntProperty(name="Subdivisions Levels", default=0, min=0, max=4)
    def execute(self,context):
        defReconst(self, self.OFFSET, self.SUBD)
        return {'FINISHED'}

## -----------------------------------SELECT LEFT---------------------
def side (self, nombre, offset):

    bpy.ops.object.mode_set(mode="EDIT", toggle=0)

    OBJECT = bpy.context.active_object
    ODATA = bmesh.from_edit_mesh(OBJECT.data)
    MODE = bpy.context.mode


    ##SETEO VERTEX MODE

    bpy.context.tool_settings.mesh_select_mode = (True, False, False)

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
    bl_options = {"REGISTER", "UNDO"}

    side = bpy.props.BoolProperty(name="Greater than zero", default=False)
    offset = bpy.props.FloatProperty(name="Offset", default=0)
    def execute(self,context):

        side(self, self.side, self.offset)

        return {'FINISHED'}


##-----------------------------------CREATE SHAPES----------------
class CreaShapes(bpy.types.Operator):
    bl_idname = "mesh.split_lr_shapes_osc"
    bl_label = "Split LR Shapes"
    bl_options = {"REGISTER", "UNDO"}
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

        print("OPERACION TERMINADA")
        return {'FINISHED'}


##----------------------------SHAPES LAYOUT-----------------------

class CreaShapesLayout(bpy.types.Operator):
    bl_idname = "mesh.create_symmetrical_layout_osc"
    bl_label = "Symmetrical Layout"
    bl_options = {"REGISTER", "UNDO"}
    def execute(self, context):

        SEL_OBJ= bpy.context.active_object
        LISTA_KEYS = bpy.context.active_object.data.shape_keys.key_blocks[1:]
        
        
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
        
        ## CREO DATA PARA SLIDERS        
        ## creo data para los contenedores
        verticess = [(-1,1,0),(1,1,0),(1,-1,0),(-1,-1,0)]
        edgess = [(0,1),(1,2),(2,3),(3,0)]        
        mesh = bpy.data.meshes.new("%s_data_container" % (SEL_OBJ))
        object = bpy.data.objects.new("GRAPHIC_CONTAINER", mesh)
        bpy.context.scene.objects.link(object)
        mesh.from_pydata(verticess,edgess,[])          
        
        gx = 0
        gy = 0
        
        
        for keyblock in LISTA_KEYS:    
            if keyblock.name[-2:] != "_L":
                if keyblock.name[-2:] != "_R":                     
                    
                    ## OBJETO ACTIVO
                    scn.objects.active = ob
                    eval(EDITMODE)
                      
                    ##CREA HUESOS
                    bone = amt.edit_bones.new(keyblock.name)
                    bone.head = (gx,0,0)
                    bone.tail = (gx,0,1)
                    
                    bonectrl = amt.edit_bones.new(keyblock.name+"_CTRL")
                    bonectrl.head = (gy,0,0)
                    bonectrl.tail = (gy,0,0.2)        
            
                    ##EMPARENTA HUESOS             
                    ## EMPARENTO
                    ob.data.edit_bones[bonectrl.name].parent = ob.data.edit_bones[bone.name]                         
                    bpy.context.scene.objects.active = ob
                    
                    for SIDE in ["L","R"]:
                        ##LE HAGO UNA VARIABLE
                        DR = SEL_OBJ.data.shape_keys.key_blocks[keyblock.name+"_"+SIDE].driver_add("value")
                        if SIDE == "L":
                            DR.driver.expression = "var+var_001"
                        else:
                            DR.driver.expression = "-var+var_001"    
                        VAR1 = DR.driver.variables.new()
                        VAR2 = DR.driver.variables.new()
            
                        VAR1.targets[0].id = ob
                        VAR1.type = 'TRANSFORMS'
                        VAR1.targets[0].bone_target = bonectrl.name      
                        VAR1.targets[0].transform_space = "LOCAL_SPACE"
                        VAR1.targets[0].transform_type = "LOC_X"
                        VAR2.targets[0].id = ob
                        VAR2.type = 'TRANSFORMS'                    
                        VAR2.targets[0].bone_target = bonectrl.name
                        VAR2.targets[0].transform_space = "LOCAL_SPACE"
                        VAR2.targets[0].transform_type = "LOC_Y"         
                    
                    eval(POSEMODE)
                    
                    ## SETEO ICONOS
                    ob.pose.bones[keyblock.name].custom_shape = object            
                    ob.pose.bones[keyblock.name+"_CTRL"].custom_shape = object
                    CNS = ob.pose.bones[keyblock.name+"_CTRL"].constraints.new(type='LIMIT_LOCATION')               
                    CNS.min_x = -1
                    CNS.use_min_x = 1
                    CNS.min_z = 0
                    CNS.use_min_z = 1
                    CNS.min_y = -1
                    CNS.use_min_y = 1    
                    CNS.max_x =  1
                    CNS.use_max_x = 1
                    CNS.max_z =  0
                    CNS.use_max_z = 1
                    CNS.max_y =  1
                    CNS.use_max_y = 1    
                    CNS.owner_space  = "LOCAL"
                    CNS.use_transform_limit = True
                    
                    eval(OBJECTMODE)
                    ## creo tipografias
                    bpy.ops.object.text_add(location=(gx,0,0))
                    gx = gx+2.2
                    gy = gy+2.2            
                    texto = bpy.context.object
        
                    texto.data.body = keyblock.name
                    texto.name = "TEXTO_"+keyblock.name
        
                    texto.rotation_euler[0] = math.pi/2
                    texto.location.x = -1
                    texto.location.z = -1
                    texto.data.size = .2
        
                    CNS = texto.constraints.new(type="COPY_LOCATION")
                    CNS.target = ob
                    CNS.subtarget = ob.pose.bones[keyblock.name].name
                    CNS.use_offset = True
    


        return {'FINISHED'}

##----------------------------CREATE LMR GROUPS-------------------
def createLMRGroups(self, FACTORVG, ADDVG):
    ## SETEO VERTEX MODE EDIT
    bpy.context.window.screen.scene.tool_settings.mesh_select_mode = (True, False, False)

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
    bl_label = "Create Mix groups"
    bl_description = "Create Mix groups"
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
    bl_options = {"REGISTER", "UNDO"}
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
        return {'FINISHED'}



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
            if OBJECT.type=="MESH" or OBJECT.type == "META" or OBJECT.type == "CURVE":
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
                    if OBJECT.type == "MESH" or OBJECT.type == "META" or OBJECT.type == "CURVE":
                        for SLOT in OBJECT.material_slots[:]:
                            SLOT.material=bpy.data.materials[OVERRIDE[1]]
        except:
            pass

        if sys.platform.startswith("w"):
            print("PLATFORM: WINDOWS")
            SCENENAME=(FILEPATH.rsplit("\\")[-1])[:-6]
        else:
            print("PLATFORM:LINUX")
            SCENENAME=(FILEPATH.rsplit("/")[-1])[:-6]

        LAYERLIST=[]
        for layer in SCENE.render.layers:
            if layer.use == 1:
                LAYERLIST.append(layer)

        for layers in LAYERLIST:
            for rl in LAYERLIST:
                rl.use= 0

            print("SCENE: "+CURSC)
            print("LAYER: "+layers.name)
            print("OVERRIDE: "+str(PROPTOLIST))

            SCENE.render.filepath = PATH + "/" + SCENENAME + "/" + CURSC + "/" + layers.name + "/" + SCENENAME + "_" + SCENE.name + "_" + layers.name + "_"
            SCENE.render.layers[layers.name].use = 1
            bpy.ops.render.render(animation=True, write_still=True, layer=layers.name, scene= SCENE.name)

            print("DONE")
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
        return {'FINISHED'}

class renderAllCF (bpy.types.Operator):
    bl_idname="render.render_layers_at_time_osc_cf"
    bl_label="Render layers at time Current Frame"

    FRAMETYPE=bpy.props.BoolProperty(default=True)


    def execute(self,context):
        defRenderAll(self.FRAMETYPE)
        return {'FINISHED'}


##--------------------------------RENDER SELECTED SCENES----------------------------


bpy.types.Scene.OscSelScenes = bpy.props.StringProperty(default="[]")


def defRenderSelected(FRAMETYPE):



    ACTSCENE = bpy.context.scene
    LISTMAT = []
    SCENES = bpy.data.scenes[:]
    SCENELIST = eval(bpy.context.scene.OscSelScenes)
    FC = bpy.context.scene.frame_current
    FS = bpy.context.scene.frame_start
    FE = bpy.context.scene.frame_end
    ## GUARDO MATERIALES DE OBJETOS EN GRUPOS
    for OBJECT in bpy.data.objects[:]:
        SLOTLIST=[]
        try:
            if OBJECT.type == "MESH" or OBJECT.type == "META" or OBJECT.type == "CURVE":
                for SLOT in OBJECT.material_slots[:]:
                    SLOTLIST.append(SLOT.material)

                LISTMAT.append((OBJECT,SLOTLIST))
        except:
            pass


    for SCENE in SCENES:
        if SCENE.name in SCENELIST:
            PROPTOLIST = list(eval(SCENE['OVERRIDE']))
            CURSC = SCENE.name
            PATH = SCENE.render.filepath
            ENDPATH = PATH
            FILEPATH = bpy.data.filepath

            print("---------------------")

            # CAMBIO SCENE
            bpy.context.window.screen.scene = SCENE

            if FRAMETYPE  ==  True:
                bpy.context.scene.frame_start = FC
                bpy.context.scene.frame_end = FC
                bpy.context.scene.frame_end = FC
                bpy.context.scene.frame_start = FC

            ## SETEO MATERIALES  DE OVERRIDES
            try:
                for OVERRIDE in PROPTOLIST:
                    for OBJECT in bpy.data.groups[OVERRIDE[0]].objects[:]:
                        if OBJECT.type == "MESH" or OBJECT.type == "META" or OBJECT.type == "CURVE":
                            for SLOT in OBJECT.material_slots[:]:
                                SLOT.material=bpy.data.materials[OVERRIDE[1]]
            except:
                pass

            if sys.platform.startswith("w"):
                print("PLATFORM: WINDOWS")
                SCENENAME=(FILEPATH.rsplit("\\")[-1])[:-6]
            else:
                print("PLATFORM:LINUX")
                SCENENAME=(FILEPATH.rsplit("/")[-1])[:-6]

            LAYERLIST=[]
            for layer in SCENE.render.layers:
                if layer.use == 1:
                    LAYERLIST.append(layer)

            for layers in LAYERLIST:
                for rl in LAYERLIST:
                    rl.use= 0

                print("SCENE: "+CURSC)
                print("LAYER: "+layers.name)
                print("OVERRIDE: "+str(PROPTOLIST))

                SCENE.render.filepath = PATH + "/" + SCENENAME + "/" + CURSC + "/" + layers.name + "/" + SCENENAME + "_" + SCENE.name + "_" + layers.name + "_"
                SCENE.render.layers[layers.name].use = 1
                bpy.ops.render.render(animation=True, layer=layers.name, write_still=True, scene= SCENE.name)

                print("DONE")
                print("---------------------")

            ## REESTABLECE LOS LAYERS
            for layer in LAYERLIST:
                layer.use = 1

            ## RESTAURA EL PATH FINAL
            SCENE.render.filepath = ENDPATH

            #RESTAURO MATERIALES  DE OVERRIDES
            for OBJECT in LISTMAT:
                SLOTIND = 0
                try:
                    for SLOT in OBJECT[1]:
                        OBJECT[0].material_slots[SLOTIND].material = SLOT
                        SLOTIND += 1
                except:
                    print("OUT OF RANGE")

            # RESTAURO FRAMES
            if FRAMETYPE == True:
                SCENE.frame_start = FS
                SCENE.frame_end = FE
                SCENE.frame_end = FE
                SCENE.frame_start = FS


    # RESTAURO SCENE
    bpy.context.window.screen.scene = ACTSCENE


class renderSelected (bpy.types.Operator):
    bl_idname="render.render_selected_scenes_osc"
    bl_label="Render Selected Scenes"

    FRAMETYPE=bpy.props.BoolProperty(default=False)

    def execute(self,context):
        defRenderSelected(self.FRAMETYPE)
        return {'FINISHED'}

class renderSelectedCF (bpy.types.Operator):
    bl_idname="render.render_selected_scenes_osc_cf"
    bl_label="Render Selected Scenes Curent Frame"

    FRAMETYPE=bpy.props.BoolProperty(default=True)

    def execute(self,context):
        defRenderSelected(self.FRAMETYPE)
        return {'FINISHED'}


##--------------------------------RENDER CURRENT SCENE----------------------------


def defRenderCurrent (FRAMETYPE):
    LISTMAT = []
    SCENE = bpy.context.scene
    FC = bpy.context.scene.frame_current
    FS = bpy.context.scene.frame_start
    FE = bpy.context.scene.frame_end


    print("---------------------")

    ## GUARDO MATERIALES DE OBJETOS EN GRUPOS
    for OBJECT in bpy.data.objects[:]:
        SLOTLIST = []
        try:
            if OBJECT.type == "MESH" or OBJECT.type == "META" or OBJECT.type == "CURVE":
                for SLOT in OBJECT.material_slots[:]:
                    SLOTLIST.append(SLOT.material)
                LISTMAT.append((OBJECT,SLOTLIST))
        except:
            pass


    PROPTOLIST = list(eval(SCENE['OVERRIDE']))
    CURSC = SCENE.name
    PATH = SCENE.render.filepath
    ENDPATH = PATH
    FILEPATH = bpy.data.filepath


    if FRAMETYPE == True:
        bpy.context.scene.frame_start = FC
        bpy.context.scene.frame_end = FC
        bpy.context.scene.frame_end = FC
        bpy.context.scene.frame_start = FC

    ## SETEO MATERIALES  DE OVERRIDES
    try:
        for OVERRIDE in PROPTOLIST:
            for OBJECT in bpy.data.groups[OVERRIDE[0]].objects[:]:
                if OBJECT.type == "MESH" or OBJECT.type == "META" or OBJECT.type == "CURVE":
                    for SLOT in OBJECT.material_slots[:]:
                        SLOT.material = bpy.data.materials[OVERRIDE[1]]
    except:
        pass

    if sys.platform.startswith("w"):
        print("PLATFORM: WINDOWS")
        SCENENAME=(FILEPATH.rsplit("\\")[-1])[:-6]
    else:
        print("PLATFORM:LINUX")
        SCENENAME=(FILEPATH.rsplit("/")[-1])[:-6]

    LAYERLIST=[]
    for layer in SCENE.render.layers:
        if layer.use == 1:
            LAYERLIST.append(layer)

    for layers in LAYERLIST:
        for rl in LAYERLIST:
            rl.use= 0

        print("SCENE: "+CURSC)
        print("LAYER: "+layers.name)
        print("OVERRIDE: "+str(PROPTOLIST))


        SCENE.render.filepath = PATH + "/" + SCENENAME + "/" + CURSC + "/" + layers.name + "/" + SCENENAME + "_" + SCENE.name + "_" + layers.name + "_"
        SCENE.render.layers[layers.name].use = 1
        bpy.ops.render.render(animation=True, layer=layers.name, write_still=1, scene= SCENE.name)

        print("DONE")
        print("---------------------")

    ## REESTABLECE LOS LAYERS
    for layer in LAYERLIST:
        layer.use = 1

    ## RESTAURA EL PATH FINAL
    SCENE.render.filepath = ENDPATH

    #RESTAURO MATERIALES  DE OVERRIDES
    for OBJECT in LISTMAT:
        SLOTIND = 0
        try:
            for SLOT in OBJECT[1]:
                OBJECT[0].material_slots[SLOTIND].material=SLOT
                SLOTIND += 1
        except:
            print("FUERA DE RANGO")

    # RESTAURO FRAMES
    if FRAMETYPE == True:
        SCENE.frame_start = FS
        SCENE.frame_end = FE
        SCENE.frame_end = FE
        SCENE.frame_start = FS


class renderCurrent (bpy.types.Operator):
    bl_idname="render.render_current_scene_osc"
    bl_label="Render Current Scene"

    FRAMETYPE=bpy.props.BoolProperty(default=False)

    def execute(self,context):

        defRenderCurrent(self.FRAMETYPE)

        return {'FINISHED'}


class renderCurrentCF (bpy.types.Operator):
    bl_idname="render.render_current_scene_osc_cf"
    bl_label="Render Current Scene Current Frame"

    FRAMETYPE=bpy.props.BoolProperty(default=True)

    def execute(self,context):

        defRenderCurrent(self.FRAMETYPE)

        return {'FINISHED'}


##--------------------------RENDER CROP----------------------
## SETEO EL STATUS DEL PANEL PARA EL IF
bpy.types.Scene.RcropStatus = bpy.props.BoolProperty(default=0)

## CREO DATA PARA EL SLIDER
bpy.types.Scene.rcPARTS = bpy.props.IntProperty(default=0, min=2, max=50, step=1)


class renderCrop (bpy.types.Operator):
    bl_idname="render.render_crop_osc"
    bl_label="Render Crop: Render!"
    def execute(self,context):



        ##AVERIGUO EL SISTEMA
        if sys.platform.startswith("w"):    
            print("PLATFORM: WINDOWS")
            VARSYSTEM= "\\"
        else:
            print("PLATFORM:LINUX")
            VARSYSTEM= "/"


        ## NOMBRE DE LA ESCENA
        SCENENAME=(bpy.data.filepath.rsplit(VARSYSTEM)[-1]).rsplit(".")[0]

        ## CREA ARRAY
        PARTES = []
        START = 1
        PARTS = bpy.context.scene.rcPARTS
        PARTS = PARTS+1
        while START < PARTS:
            PARTES.append(START)
            START = START+1
        print(PARTES)


        ##SETEO VARIABLE PARA LA FUNCION DE RENDER
        NUMERODECORTE=1

        ##ESCENA ACTIVA
        SCACT = bpy.context.scene

        ## SETEO CROP
        bpy.data.scenes[SCACT.name].render.use_crop_to_border = 1
        bpy.data.scenes[SCACT.name].render.use_border = 1

        ##A VERIGUO RES EN Y
        RESY = bpy.data.scenes[SCACT.name].render.resolution_y

        ## AVERIGUO EL PATH DE LA ESCENA
        OUTPUTFILEPATH = bpy.data.scenes[SCACT.name].render.filepath
        bpy.context.scene.render.filepath = OUTPUTFILEPATH+bpy.context.scene.name


        ## CUANTAS PARTES HARA
        LENPARTES = len(PARTES)

        ## DIVIDE 1 SOBRE LA CANTIDAD DE PARTES
        DIVISOR = 1/PARTES[LENPARTES-1]

        ## SETEA VARIABLE DEL MARCO MINIMO Y MAXIMO
        CMIN = 0
        CMAX = DIVISOR

        ## REMUEVE EL ULTIMO OBJETO DEL ARRAY PARTES
        PARTESRESTADA = PARTES.pop(LENPARTES-1)

        ## SETEA EL MINIMO Y EL MAXIMO CON LOS VALORES DE ARRIBA
        bpy.data.scenes[SCACT.name].render.border_min_y = CMIN
        bpy.data.scenes[SCACT.name].render.border_max_y = CMAX


        ##SETEA EL OUTPUT PARA LA PRIMERA PARTE
        OUTPUTFILEPATH+bpy.context.scene.name
        bpy.context.scene.render.filepath = OUTPUTFILEPATH + SCENENAME + VARSYSTEM + SCENENAME + "_PART" + str(PARTES[0]) + "_"

        ##RENDER PRIMERA PARTE
        bpy.ops.render.render(animation=True)
        bpy.context.scene.render.filepath

        ##SUMO UN NUMERO AL CORTE
        NUMERODECORTE = NUMERODECORTE + 1


        ## RENDER!
        for PARTE in PARTES:
            ## SUMA A LOS VALORES DEL CROP
            CMIN = CMIN + DIVISOR
            CMAX = CMAX + DIVISOR
            print("EL CROP ES DE " + str(CMIN) + " A " + str(CMAX))
            ## SETEA BORDE
            bpy.data.scenes[SCACT.name].render.border_min_y = CMIN
            bpy.data.scenes[SCACT.name].render.border_max_y = CMAX
            ## SETEA EL OUTPUT
            bpy.context.scene.render.filepath = OUTPUTFILEPATH + SCENENAME + VARSYSTEM + SCENENAME + "_PART" + str(NUMERODECORTE) + "_"
            print("EL OUTPUT DE LA FUNCION ES " + bpy.context.scene.render.filepath)
            ## PRINTEA EL NUMERO DE CORTE
            print(PARTE)
            ## RENDER
            bpy.ops.render.render(animation=True)
            ## SUMO NUMERO DE CORTE
            NUMERODECORTE = NUMERODECORTE + 1


        ## REESTABLEZCO EL FILEPATH
        bpy.context.scene.render.filepath = OUTPUTFILEPATH


        print("RENDER TERMINADO")

        return {'FINISHED'}


##------------------------ SEARCH AND SELECT ------------------------

## SETEO VARIABLE DE ENTORNO
bpy.types.Scene.SearchAndSelectOt = bpy.props.StringProperty(default="Object name initials")


class SearchAndSelectOt(bpy.types.Operator):
    bl_idname = "object.search_and_select_osc"
    bl_label = "Search And Select"
    bl_options = {"REGISTER", "UNDO"}
    def execute(self, context):
        for objeto in bpy.context.scene.objects:
            variableNombre = bpy.context.scene.SearchAndSelectOt
            if objeto.name.startswith(variableNombre) == True :
                objeto.select = 1
                print("Selecciona:" + str(objeto.name))
        return {'FINISHED'}

##-------------------------RENAME OBJECTS----------------------------------

## CREO VARIABLE
bpy.types.Scene.RenameObjectOt = bpy.props.StringProperty(default="Type here")

class renameObjectsOt (bpy.types.Operator):
    bl_idname = "object.rename_objects_osc"
    bl_label = "Rename Objects"
    bl_options = {"REGISTER", "UNDO"}
    def execute(self,context):

        ## LISTA
        listaObj = bpy.context.selected_objects


        for objeto in listaObj:
            print(objeto.name)
            objeto.name = bpy.context.scene.RenameObjectOt
        return {'FINISHED'}


##-------------------------RESYM VG----------------------------------



class resymVertexGroups (bpy.types.Operator):
    bl_idname = "mesh.resym_vertex_weights_osc"
    bl_label = "Resym Vertex Weights"
    bl_options = {"REGISTER", "UNDO"}
    def execute(self,context):

        OBACTIVO = bpy.context.active_object
        VGACTIVO = OBACTIVO.vertex_groups.active.index
        
        bpy.ops.object.mode_set(mode='EDIT')
        BM = bmesh.from_edit_mesh(bpy.context.object.data)  
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_select()
        SELVER=[VERT.index for VERT in BM.verts[:] if VERT.select]
        
        if sys.platform.startswith("w"):
            SYSBAR = "\\"
        else:
             SYSBAR = "/" 
         
        FILEPATH=bpy.data.filepath
        ACTIVEFOLDER=FILEPATH.rpartition(SYSBAR)[0]
        ENTFILEPATH= "%s%s%s_%s_SYM_TEMPLATE.xml" %  (ACTIVEFOLDER, SYSBAR, bpy.context.scene.name, bpy.context.object.name)
        XML=open(ENTFILEPATH ,mode="r")
        
        SYMAP = eval(XML.readlines()[0])
        

        # SUMO LOS VERTICES QUE NO EXISTEN EN EL VG        
        INL = [VERT for VERT in SYMAP if SYMAP[VERT] in SELVER if VERT!= SYMAP[VERT]] 
        bpy.ops.mesh.select_all(action='DESELECT')

        for VERT in INL:
            BM.verts[VERT].select = True
        bpy.ops.object.vertex_group_assign(new=False)    
     

        # PASO A WEIGHT Y SETEO LOS VALORES
        bpy.ops.object.mode_set(mode='WEIGHT_PAINT')        
        for VERT in INL:
            print(VERT)
            i = 0
            for GRA in OBACTIVO.data.vertices[SYMAP[VERT]].groups[:]:
                if GRA.group == VGACTIVO:
                    print (i)
                    EM = i                    
                i+=1  
            a = 0
            for GRA in OBACTIVO.data.vertices[VERT].groups[:]:     
                if GRA.group == VGACTIVO:
                    print (a)
                    REC = a
                a+=1
                    
            OBACTIVO.data.vertices[VERT].groups[REC].weight = OBACTIVO.data.vertices[SYMAP[VERT]].groups[EM].weight  
                

        XML.close()
        SYMAP.clear()  
      

        print("===============(JOB DONE)=============")
        return {'FINISHED'}


##------------------------ SHAPES LAYOUT SYMMETRICA ------------------------


class CreateLayoutAsymmetrical(bpy.types.Operator):
    bl_idname = "mesh.create_asymmetrical_layout_osc"
    bl_label = "Asymmetrical Layout"
    bl_options = {"REGISTER", "UNDO"}
    def execute(self, context):

        SEL_OBJ= bpy.context.active_object
        LISTA_KEYS = bpy.context.active_object.data.shape_keys.key_blocks[1:]
        
        ##MODOS
        EDITMODE = "bpy.ops.object.mode_set(mode='EDIT')"
        OBJECTMODE = "bpy.ops.object.mode_set(mode='OBJECT')"
        POSEMODE = "bpy.ops.object.mode_set(mode='POSE')"
        
        ##CREA NOMBRES A LA ARMATURE
        amtas = bpy.data.armatures.new("ArmatureData")
        obas = bpy.data.objects.new("RIG_LAYOUT_"+SEL_OBJ.name, amtas)
        
        ##LINK A LA ESCENA
        scn = bpy.context.scene
        scn.objects.link(obas)
        scn.objects.active = obas
        obas.select = True
        
        ## CREO DATA PARA SLIDERS            
        ## creo data para los contenedores
        verticess = [(-.1,1,0),(.1,1,0),(.1,0,0),(-.1,0,0)]
        edgess = [(0,1),(1,2),(2,3),(3,0)]            
        mesh = bpy.data.meshes.new("%s_data_container" % (SEL_OBJ))
        object = bpy.data.objects.new("GRAPHIC_CONTAINER_AS", mesh)
        bpy.context.scene.objects.link(object)
        mesh.from_pydata(verticess,edgess,[])
        
        eval(EDITMODE)
        gx = 0
        gy = 0        
        
        for keyblock in LISTA_KEYS:        
            if keyblock.name[-2:] != "_L":
                if keyblock.name[-2:] != "_R":
                    ## OBJETO ACTIVO
                    scn.objects.active = obas
                    eval(EDITMODE)
        
                    ##CREA HUESOS        
                    bone = amtas.edit_bones.new(keyblock.name)
                    bone.head = (gx,0,0)
                    bone.tail = (gx,0,1)
                    
                    bonectrl = amtas.edit_bones.new(keyblock.name+"_CTRL")
                    bonectrl.head = (gy,0,0)
                    bonectrl.tail = (gy,0,0.2)
        
                    ##EMPARENTA HUESOS
                    ## EMPARENTO
                    obas.data.edit_bones[bonectrl.name].parent = obas.data.edit_bones[bone.name]                         
                    bpy.context.scene.objects.active = obas
                    
                    ##DESELECCIONA (modo edit)
                    bpy.ops.armature.select_all(action="DESELECT")
        
                    ##CREA DRIVERS Y LOS CONECTA
                    DR1 = keyblock.driver_add("value")
                    DR1.driver.expression = "var"
                    VAR2 = DR1.driver.variables.new()     
                    VAR2.targets[0].id = obas
                    VAR2.targets[0].bone_target = bonectrl.name
                    VAR2.type = 'TRANSFORMS'
                    VAR2.targets[0].transform_space = "LOCAL_SPACE"
                    VAR2.targets[0].transform_type = "LOC_Y"       
                    
                    eval(POSEMODE)
                    
                    ## SETEO ICONOS
                    obas.pose.bones[keyblock.name].custom_shape = object
                    obas.pose.bones[keyblock.name+"_CTRL"].custom_shape = object
                    
                    ## SETEO CONSTRAINTS
        
                    bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].data.bones.active = bpy.data.objects["RIG_LAYOUT_"+SEL_OBJ.name].data.bones[keyblock.name+"_CTRL"]
                    ## SUMO CONSTRAINT
                    eval(POSEMODE)
                    CNS = obas.pose.bones[keyblock.name+"_CTRL"].constraints.new(type='LIMIT_LOCATION')                        
                    CNS.min_x = 0
                    CNS.use_min_x = 1
                    CNS.min_z = 0
                    CNS.use_min_z = 1
                    CNS.min_y = 0
                    CNS.use_min_y = 1
                    
                    CNS.max_x =  0
                    CNS.use_max_x = 1
                    CNS.max_z =  0
                    CNS.use_max_z = 1
                    CNS.max_y =  1
                    CNS.use_max_y = 1
                    
                    CNS.owner_space  = "LOCAL"
                    CNS.use_transform_limit = True        
        
                    ## PARA QUE EL TEXTO FUNCIONE PASAMOS A OBJECT MODE
                    eval(OBJECTMODE)
        
                    ## TEXTOS
                    ## creo tipografias
                    bpy.ops.object.text_add(location=(0,0,0))
                    gx = gx+2.2
                    gy = gy+2.2
                    texto = bpy.context.object
                    texto.data.body = keyblock.name
                    texto.name = "TEXTO_"+keyblock.name
        
                    texto.rotation_euler[0] = math.pi/2
                    texto.location.x = -.15
                    texto.location.z = -.15
                    texto.data.size = .2
                    
                    CNS = texto.constraints.new(type="COPY_LOCATION")
                    CNS.target = obas
                    CNS.subtarget = obas.pose.bones[keyblock.name].name
                    CNS.use_offset = True  
                              
        

        return {'FINISHED'}


##------------------------ SAVE INCREMENTAL ------------------------

class saveIncremental(bpy.types.Operator):
    bl_idname = "file.save_incremental_osc"
    bl_label = "Save Incremental File"
    bl_options = {"REGISTER", "UNDO"}
    def execute(self, context):

        # SI POSEE _V        
        filepath = bpy.data.filepath
        
        if filepath.count("_v"):
            strnum = filepath.rpartition("_v")[-1].rpartition(".blend")[0]
            intnum = int(strnum)
            modnum = strnum.replace(str(intnum),str(intnum+1))    
            output = filepath.replace(strnum,modnum)
            bpy.ops.wm.save_as_mainfile(filepath=output)   
             
        else:
            output = filepath.rpartition(".blend")[0]+"_v01"
            bpy.ops.wm.save_as_mainfile(filepath=output)         
        
        return {'FINISHED'}

##------------------------ REPLACE FILE PATHS ------------------------

bpy.types.Scene.oscSearchText = bpy.props.StringProperty(default="Search Text")
bpy.types.Scene.oscReplaceText = bpy.props.StringProperty(default="Replace Text")

class replaceFilePath(bpy.types.Operator):
    bl_idname = "file.replace_file_path_osc"
    bl_label = "Replace File Path"
    bl_options = {"REGISTER", "UNDO"}
    def execute(self, context):
        TEXTSEARCH = bpy.context.scene.oscSearchText
        TEXTREPLACE = bpy.context.scene.oscReplaceText

        for image in bpy.data.images:
            image.filepath = image.filepath.replace(TEXTSEARCH,TEXTREPLACE)

        return {'FINISHED'}


##------------------------ DUPLICATE OBJECTS SYMMETRY ------------------------

def duplicateSymmetrical (self, disconect):
    for objeto in bpy.context.selected_objects:

        OBSEL = objeto

        #DESELECT AND SELECT OBJETO
        bpy.ops.object.select_all(action='DESELECT')
        objeto.select = 1
        bpy.context.scene.objects.active = objeto

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
    bl_options = {"REGISTER", "UNDO"}

    desconecta = bpy.props.BoolProperty(name="Keep Connection", default=True)

    def execute(self,context):

        duplicateSymmetrical(self, self.desconecta)

        return {'FINISHED'}


##---------------------------BATCH MAKER------------------


def defoscBatchMaker(TYPE):
    # REVISO SISTEMA
    if sys.platform.startswith("w"):
        print("PLATFORM: WINDOWS")
        SYSBAR = "\\"
        EXTSYS = ".bat"
        QUOTES = '"'
    else:
        print("PLATFORM:LINUX")
        SYSBAR = "/"
        EXTSYS = ".sh"
        QUOTES = ''

    # CREO VARIABLES
    FILENAME = bpy.data.filepath.rpartition(SYSBAR)[-1].rpartition(".")[0]
    BINDIR = bpy.app[4]
    SHFILE = bpy.data.filepath.rpartition(SYSBAR)[0] + SYSBAR + FILENAME + EXTSYS
    FILEBATCH = open(SHFILE,"w")

    # SI ES LINUX LE DOY PERMISOS CHMOD
    if EXTSYS == ".sh":
        try:
            os.chmod(SHFILE, stat.S_IRWXU)
        except:
            print("** Oscurart Batch maker can not modify the permissions.")    

    # DEFINO ARCHIVO DE BATCH
    FILEBATCH.writelines("%s%s%s -b %s -x 1 -o %s -P %s%s.py  -s %s -e %s -a" % (QUOTES,BINDIR,QUOTES,bpy.data.filepath,bpy.context.scene.render.filepath,bpy.data.filepath.rpartition(SYSBAR)[0]+SYSBAR,TYPE,str(bpy.context.scene.frame_start),str(bpy.context.scene.frame_end)) )
    FILEBATCH.close()  


    # DEFINO LOS ARCHIVOS DE SCRIPT
    
    RLATFILE =  "%s%sosRlat.py" % (bpy.data.filepath.rpartition(SYSBAR)[0] , SYSBAR )
    if not os.path.isfile(RLATFILE):
        FILESC = open(RLATFILE,"w")        
        if EXTSYS == ".sh":
            try:
                os.chmod(RLATFILE, stat.S_IRWXU)  
            except:
                print("** Oscurart Batch maker can not modify the permissions.")                             
        FILESC.writelines("import bpy \nbpy.ops.render.render_layers_at_time_osc()\nbpy.ops.wm.quit_blender()")
        FILESC.close()
    else:
        print("The All Python files Skips: Already exist!")   
         
    RSLATFILE = "%s%sosRSlat.py" % (bpy.data.filepath.rpartition(SYSBAR)[0] , SYSBAR)    
    if not os.path.isfile(RSLATFILE):          
        FILESSC = open(RSLATFILE,"w")          
        if EXTSYS == ".sh":
            try:
                os.chmod(RSLATFILE, stat.S_IRWXU)   
            except:
                print("** Oscurart Batch maker can not modify the permissions.")                            
        FILESSC.writelines("import bpy \nbpy.ops.render.render_selected_scenes_osc()\nbpy.ops.wm.quit_blender()")
        FILESSC.close()
    else:
        print("The Selected Python files Skips: Already exist!")          

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
        return {'FINISHED'}


##---------------------------REMOVE MODIFIERS Y APPLY MODIFIERS------------------

class oscRemModifiers (bpy.types.Operator):
    bl_idname = "object.modifiers_remove_osc"
    bl_label = "Remove modifiers"
    bl_options = {"REGISTER", "UNDO"}
    def execute(self,context):
        for objeto in bpy.context.selected_objects:
            for modificador in objeto.modifiers:
                print(modificador.type)
                bpy.context.scene.objects.active=objeto
                bpy.ops.object.modifier_remove(modifier=modificador.name)
        return {'FINISHED'}

class oscApplyModifiers (bpy.types.Operator):
    bl_idname = "object.modifiers_apply_osc"
    bl_label = "Apply modifiers"
    bl_options = {"REGISTER", "UNDO"}
    def execute(self,context):
        for objeto in bpy.context.selected_objects:
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.scene.objects.active=objeto
            objeto.select = True
            if objeto.data.users >= 2:
                bpy.ops.object.make_single_user(type='SELECTED_OBJECTS', object=True, obdata=True, material=False, texture=False, animation=False)
            for modificador in objeto.modifiers:
                try:
                    bpy.ops.object.modifier_apply(apply_as="DATA", modifier=modificador.name)
                except:
                    bpy.ops.object.modifier_remove(modifier=modificador.name) 
                    print("* Modifier %s skipping apply" % (modificador.name))   

        return {'FINISHED'}


##---------------------------SHAPES TO OBJECTS------------------

class ShapeToObjects (bpy.types.Operator):
    bl_idname = "object.shape_key_to_objects_osc"
    bl_label = "Shapes To Objects"
    bl_options = {"REGISTER", "UNDO"}
    def execute(self,context):
        OBJACT=bpy.context.active_object
        for SHAPE in OBJACT.data.shape_keys.key_blocks[:]:
            print(SHAPE.name)
            bpy.ops.object.shape_key_clear()
            SHAPE.value=1
            mesh=OBJACT.to_mesh(bpy.context.scene, True, 'PREVIEW')
            object=bpy.data.objects.new(SHAPE.name, mesh)
            bpy.context.scene.objects.link(object)
        return {'FINISHED'}


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
    bl_options = {"REGISTER", "UNDO"}
    def execute(self,context):
        for scene in bpy.data.scenes[:]:
            try:
                scene['OVERRIDE']
            except:
                scene['OVERRIDE']="[]"
        return {'FINISHED'}


###------------------------IMPORT EXPORT GROUPS--------------------

class OscExportVG (bpy.types.Operator):
    bl_idname = "file.export_groups_osc"
    bl_label = "Export Groups"
    bl_options = {"REGISTER", "UNDO"}
    def execute(self,context):

        OBSEL=bpy.context.active_object

        if os.sys.platform.count("win"):
            print("WINDOWS")
            BAR = "\\"
        else:
            print("LINUX")
            BAR = "/"
        # VARIABLES
        FILEPATH = bpy.data.filepath
        FILE = open(FILEPATH.rpartition(BAR)[0] + BAR+OBSEL.name + ".xml", mode = "w")
        VERTLIST = []

        LENVER = len(OBSEL.data.vertices)

        for VG in OBSEL.vertex_groups:
            BONELIST = []
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
        FILEPATH = bpy.data.filepath
        FILE = open(FILEPATH.rpartition(BAR)[0] + BAR + OBSEL.name + "_DATA.xml", mode = "w")

        DATAVER = []

        for VERT in OBSEL.data.vertices[:]:
            TEMP = 0
            VGTEMP = 0
            LISTVGTEMP = []

            for GROUP in VERT.groups[:]:
                LISTVGTEMP.append((GROUP.group,VGTEMP))
                VGTEMP += 1

            LISTVGTEMP=sorted(LISTVGTEMP)
            for GROUP in VERT.groups[:]:
                DATAVER.append((VERT.index,TEMP,VERT.groups[LISTVGTEMP[TEMP][1]].weight))
                TEMP += 1


        ## GUARDO Y CIERRO
        FILE.writelines(str(DATAVER))
        FILE.close()

        return {'FINISHED'}

class OscImportVG (bpy.types.Operator):
    bl_idname = "file.import_groups_osc"
    bl_label = "Import Groups"
    bl_options = {"REGISTER", "UNDO"}
    def execute(self,context):

        OBSEL = bpy.context.active_object
        # AVERIGUO EL SISTEMA
        if os.sys.platform.count("win"):
            print("WINDOWS")
            BAR = "\\"
        else:
            print("LINUX")
            BAR = "/"
        # VARIABLES
        FILEPATH = bpy.data.filepath
        FILE = open(FILEPATH.rpartition(BAR)[0] + BAR + OBSEL.name + ".xml", mode="r")
        VERTLIST = FILE.readlines(0)
        VERTLIST = eval(VERTLIST[0])
        VERTLISTR = VERTLIST[:-1]
        GROUPLIST = VERTLIST[-1:]
        VGINDEX = 0

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
        FILEPATH = bpy.data.filepath
        FILE = open(FILEPATH.rpartition(BAR)[0]+BAR+OBSEL.name+"_DATA.xml", mode="r")
        DATAPVER = FILE.readlines(0)
        DATAPVER = eval(DATAPVER[0])

        # PASO A MODO OBJECT
        bpy.ops.object.mode_set(mode='OBJECT')

        #for VERT in DATAPVER:
        for VERT in DATAPVER:
            OBSEL.data.vertices[VERT[0]].groups[VERT[1]].weight = VERT[2]

        # CIERRO
        FILE.close()


        # PASO A MODO PINTURA DE PESO
        bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
        return {'FINISHED'}


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
    bl_options = {"REGISTER", "UNDO"}


    def execute (self, context):
        relinkObjects(self)
        return {'FINISHED'}


## ------------------------------------ COPY GROUPS AND LAYERS--------------------------------------


def CopyObjectGroupsAndLayers (self):

    OBSEL=bpy.selection_osc[:]
    GLOBALLAYERS=list(OBSEL[-1].layers[:])
    ACTSCENE=bpy.context.scene
    GROUPS=OBSEL[-1].users_group
    ACTOBJ=OBSEL[-1]
    
    for OBJECT in OBSEL[:-1]:
        for scene in bpy.data.scenes[:]:
            
            # CAMBIO ESCENA EN EL UI
            bpy.context.window.screen.scene=scene

            # SI EL OBJETO ACTIVO ESTA EN LA ESCENA
            if ACTOBJ in bpy.context.scene.objects[:] and OBJECT in bpy.context.scene.objects[:]:
                scene.objects[OBJECT.name].layers = ACTOBJ.layers
            elif ACTOBJ not in bpy.context.scene.objects[:] and OBJECT in bpy.context.scene.objects[:]: 
                scene.objects[OBJECT.name].layers = list(GLOBALLAYERS)                  
                
        # REMUEVO DE TODO GRUPO
        for GROUP in bpy.data.groups[:]:
            if GROUP in OBJECT.users_group[:]:
                GROUP.objects.unlink(OBJECT)
                
        # INCLUYO OBJETO EN GRUPOS    
        for GROUP in GROUPS:
            GROUP.objects.link(OBJECT)            
 
    bpy.context.window.screen.scene = ACTSCENE

class OscCopyObjectGAL (bpy.types.Operator):
    bl_idname = "objects.copy_objects_groups_layers"
    bl_label = "Copy Groups And Layers"
    bl_options = {"REGISTER", "UNDO"}


    def execute (self, context):
        CopyObjectGroupsAndLayers (self)
        return {'FINISHED'}


## ------------------------------------ APPLY AND RESTORE OVERRIDES --------------------------------------

def DefOscApplyOverrides(self):
    LISTMAT = []
    PROPTOLIST = list(eval(bpy.context.scene['OVERRIDE']))
    # REVISO SISTEMA
    if sys.platform.startswith("w"):
        print("PLATFORM: WINDOWS")
        SYSBAR = "\\"
    else:
        print("PLATFORM:LINUX")
        SYSBAR = "/"
    FILEPATH=bpy.data.filepath
    ACTIVEFOLDER=FILEPATH.rpartition(SYSBAR)[0]
    ENTFILEPATH= "%s%s%s_OVERRIDE.xml" %  (ACTIVEFOLDER, SYSBAR, bpy.context.scene.name)
    XML=open(ENTFILEPATH ,mode="w")
    ## GUARDO MATERIALES DE OBJETOS EN GRUPOS
    
    LISTMAT = { OBJ : [SLOT.material for SLOT in OBJ.material_slots[:]] for OBJ in bpy.data.objects[:] if OBJ.type == "MESH" or OBJ.type == "META" or OBJ.type == "CURVE" }
    
    
    for OVERRIDE in PROPTOLIST:
        for OBJECT in bpy.data.groups[OVERRIDE[0]].objects[:]:
            if OBJECT.type == "MESH" or OBJECT.type == "META" or OBJECT.type == "CURVE": 
                if len(OBJECT.material_slots) > 0:                   
                    for SLOT in OBJECT.material_slots[:]:
                        SLOT.material = bpy.data.materials[OVERRIDE[1]]                    
                else:
                    print ("* %s have not Material Slots" % (OBJECT.name))         
    

    XML.writelines(str(LISTMAT))
    XML.close()    
    
    
def DefOscRestoreOverrides(self):    
    # REVISO SISTEMA
    if sys.platform.startswith("w"):
        #print("PLATFORM: WINDOWS")
        SYSBAR="\\"
    else:
        #print("PLATFORM:LINUX")
        SYSBAR="/"

    FILEPATH = bpy.data.filepath
    ACTIVEFOLDER = FILEPATH.rpartition(SYSBAR)[0]
    ENTFILEPATH = "%s%s%s_OVERRIDE.xml" %  (ACTIVEFOLDER, SYSBAR, bpy.context.scene.name)
    XML = open(ENTFILEPATH, mode="r")
    RXML = XML.readlines(0)

    LISTMAT = dict(eval(RXML[0]))

    # RESTAURO MATERIALES  DE OVERRIDES
    
    for OBJ in LISTMAT:            
        if OBJ.type == "MESH" or OBJ.type == "META" or OBJ.type == "CURVE":
            SLOTIND = 0
            for SLOT in LISTMAT[OBJ]:
                OBJ.material_slots[SLOTIND].material = SLOT  
                SLOTIND += 1     
        
    # CIERRO
    XML.close()

    
## HAND OPERATOR    
class OscApplyOverrides(bpy.types.Operator):
    bl_idname = "render.apply_overrides"
    bl_label = "Apply Overrides in this Scene"
    bl_options = {"REGISTER", "UNDO"}


    def execute (self, context):
        DefOscApplyOverrides(self)
        return {'FINISHED'}

class OscRestoreOverrides(bpy.types.Operator):
    bl_idname = "render.restore_overrides"
    bl_label = "Restore Overrides in this Scene"
    bl_options = {"REGISTER", "UNDO"}


    def execute (self, context):
        DefOscRestoreOverrides(self)        
        return {'FINISHED'}






## ------------------------------------ CHECK OVERRIDES --------------------------------------

class OscCheckOverrides (bpy.types.Operator):
    bl_idname = "render.check_overrides"
    bl_label = "Check Overrides"
    bl_options = {"REGISTER", "UNDO"}


    def execute (self, context):
        GROUPI = False
        GLOBAL = 0
        GLOBALERROR = 0

        print("==== STARTING CHECKING ====")
        print("")

        for SCENE in bpy.data.scenes[:]:
            MATLIST = []
            MATI = False

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
                    GROUPI = True
                    GLOBALERROR += 1
                # REVISO OVERRIDES EN GRUPOS
                if OVERRIDE[1] in MATLIST:
                    pass
                else:
                    print("** %s material are in conflict." % (OVERRIDE[1]))
                    MATI = True
                    GLOBALERROR += 1

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
    if bpy.context.mode == "OBJECT":
        obj = bpy.context.object
        sel = len(bpy.context.selected_objects)

        if sel == 0:
            bpy.selection_osc=[]
        else:
            if sel == 1:
                bpy.selection_osc=[]
                bpy.selection_osc.append(obj)
            elif sel > len(bpy.selection_osc):
                for sobj in bpy.context.selected_objects:
                    if (sobj in bpy.selection_osc) == False:
                        bpy.selection_osc.append(sobj)

            elif sel < len(bpy.selection_osc):
                for it in bpy.selection_osc:
                    if (it in bpy.context.selected_objects) == False:
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


## ------------------------------------ RESYM MESH--------------------------------------


def reSymSave (self):
    
    bpy.ops.object.mode_set(mode='EDIT')
    
    BM = bmesh.from_edit_mesh(bpy.context.object.data)   
     
    L = {VERT.index : [VERT.co[0],VERT.co[1],VERT.co[2]] for VERT in BM.verts[:] if VERT.co[0] < 0.0001}
    R = {VERT.index : [-VERT.co[0],VERT.co[1],VERT.co[2]]  for VERT in BM.verts[:] if VERT.co[0] > -0.0001}
    
    SYMAP = {VERTL : VERTR for VERTR in R for VERTL in L if R[VERTR] == L[VERTL] }            
    
    if sys.platform.startswith("w"):
        SYSBAR = "\\"
    else:
         SYSBAR = "/"   
    
    FILEPATH=bpy.data.filepath
    ACTIVEFOLDER=FILEPATH.rpartition(SYSBAR)[0]
    ENTFILEPATH= "%s%s%s_%s_SYM_TEMPLATE.xml" %  (ACTIVEFOLDER, SYSBAR, bpy.context.scene.name, bpy.context.object.name)
    XML=open(ENTFILEPATH ,mode="w")
    
    XML.writelines(str(SYMAP))
    XML.close()
    SYMAP.clear()

def reSymMesh (self):
    
    bpy.ops.object.mode_set(mode='EDIT')
    
    BM = bmesh.from_edit_mesh(bpy.context.object.data)
    
    if sys.platform.startswith("w"):
        SYSBAR = "\\"
    else:
         SYSBAR = "/" 
    
    FILEPATH=bpy.data.filepath
    ACTIVEFOLDER=FILEPATH.rpartition(SYSBAR)[0]
    ENTFILEPATH= "%s%s%s_%s_SYM_TEMPLATE.xml" %  (ACTIVEFOLDER, SYSBAR, bpy.context.scene.name, bpy.context.object.name)
    XML=open(ENTFILEPATH ,mode="r")
    
    SYMAP = eval(XML.readlines()[0])
    
    for VERT in SYMAP:
        if VERT == SYMAP[VERT]:
            BM.verts[VERT].co[0] = 0
            BM.verts[VERT].co[1] = BM.verts[SYMAP[VERT]].co[1]
            BM.verts[VERT].co[2] = BM.verts[SYMAP[VERT]].co[2]            
        else:    
            BM.verts[VERT].co[0] = -BM.verts[SYMAP[VERT]].co[0]
            BM.verts[VERT].co[1] = BM.verts[SYMAP[VERT]].co[1]
            BM.verts[VERT].co[2] = BM.verts[SYMAP[VERT]].co[2]
    
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')
    
    XML.close()
    SYMAP.clear()


class OscResymSave (bpy.types.Operator):
    bl_idname = "mesh.resym_save_map"
    bl_label = "Resym save XML Map"
    bl_options = {"REGISTER", "UNDO"}


    def execute (self, context):
        reSymSave(self)
        return {'FINISHED'}

class OscResymMesh (bpy.types.Operator):
    bl_idname = "mesh.resym_mesh"
    bl_label = "Resym save Apply XML"
    bl_options = {"REGISTER", "UNDO"}


    def execute (self, context):
        reSymMesh(self)
        return {'FINISHED'}
    
##=============== DISTRIBUTE ======================    


def ObjectDistributeOscurart (self, X, Y, Z):
    if len(bpy.selection_osc[:]) > 1:
        # VARIABLES
        dif = bpy.selection_osc[-1].location-bpy.selection_osc[0].location
        chunkglobal = dif/(len(bpy.selection_osc[:])-1)
        chunkx = 0
        chunky = 0
        chunkz = 0
        deltafst = bpy.selection_osc[0].location
        
        #ORDENA
        for OBJECT in bpy.selection_osc[:]:          
            if X:  OBJECT.location.x=deltafst[0]+chunkx
            if Y:  OBJECT.location[1]=deltafst[1]+chunky
            if Z:  OBJECT.location.z=deltafst[2]+chunkz
            chunkx+=chunkglobal[0]
            chunky+=chunkglobal[1]
            chunkz+=chunkglobal[2]
    else:  
        self.report({'ERROR'}, "Selection is only 1!")      
    
class DialogDistributeOsc(bpy.types.Operator):
    bl_idname = "object.distribute_osc"
    bl_label = "Distribute Objects"       
    Boolx = bpy.props.BoolProperty(name="X")
    Booly = bpy.props.BoolProperty(name="Y")
    Boolz = bpy.props.BoolProperty(name="Z")
    
    def execute(self, context):
        ObjectDistributeOscurart(self, self.Boolx,self.Booly,self.Boolz)
        return {'FINISHED'}
    def invoke(self, context, event):
        self.Boolx = True
        self.Booly = True
        self.Boolz = True        
        return context.window_manager.invoke_props_dialog(self)
    
##--------------------------------- OVERRIDES PANEL ---------------------------------- 
   
class OscOverridesGUI(bpy.types.Panel):
    bl_label = "Oscurart Material Overrides"
    bl_idname = "Oscurart Overrides List"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    def draw(self,context):
        
        layout = self.layout
        col = layout.column(align=1)
        colrow = col.row(align=1)
        colrow.operator("render.overrides_add_slot", icon = "ZOOMIN") 
        colrow.operator("render.overrides_remove_slot", icon = "ZOOMOUT")         
        col.operator("render.overrides_transfer", icon = "SHORTDISPLAY") 
        i = 0
        for m in bpy.context.scene.ovlist:
            colrow = col.row(align=1)
            colrow.prop_search(m, "grooverride", bpy.data, "groups", text= "")  
            colrow.prop_search(m, "matoverride", bpy.data, "materials", text= "")
            if i != len(bpy.context.scene.ovlist)-1:
                pa = colrow.operator("ovlist.move_down", text="", icon="TRIA_DOWN")
                pa.index = i                
            if i > 0:
                p = colrow.operator("ovlist.move_up", text="", icon="TRIA_UP")
                p.index = i
            pb = colrow.operator("ovlist.kill", text="", icon="X")            
            pb.index = i
            i+=1
 
class OscOverridesUp (bpy.types.Operator): 
    bl_idname = 'ovlist.move_up'
    bl_label = 'Move Override up'
    bl_options = {'INTERNAL'}
   
    index = bpy.props.IntProperty(min=0)
   
    @classmethod
    def poll(self,context):
        return len(context.scene.ovlist) 
    def execute(self,context):
        ovlist = context.scene.ovlist
        ovlist.move(self.index,self.index-1) 

        return {'FINISHED'}   

class OscOverridesDown (bpy.types.Operator): 
    bl_idname = 'ovlist.move_down'
    bl_label = 'Move Override down'
    bl_options = {'INTERNAL'}
   
    index = bpy.props.IntProperty(min=0)
   
    @classmethod
    def poll(self,context):
        return len(context.scene.ovlist) 
    def execute(self,context):
        ovlist = context.scene.ovlist
        ovlist.move(self.index,self.index+1) 
        return {'FINISHED'}              

class OscOverridesKill (bpy.types.Operator): 
    bl_idname = 'ovlist.kill'
    bl_label = 'Kill Override'
    bl_options = {'INTERNAL'}
   
    index = bpy.props.IntProperty(min=0)
   
    @classmethod
    def poll(self,context):
        return len(context.scene.ovlist) 
    def execute(self,context):
        ovlist = context.scene.ovlist  
        ovlist.remove(self.index)  
        return {'FINISHED'}              


class OscOverridesProp(bpy.types.PropertyGroup):
    matoverride = bpy.props.StringProperty() 
    grooverride = bpy.props.StringProperty()        
        
bpy.utils.register_class(OscOverridesGUI)
bpy.utils.register_class(OscOverridesProp)
bpy.types.Scene.ovlist = bpy.props.CollectionProperty(type=OscOverridesProp)        


class OscTransferOverrides (bpy.types.Operator):    
    """Tooltip"""
    bl_idname = "render.overrides_transfer"
    bl_label = "Transfer Overrides"

    def execute(self, context):
        # CREO LISTA
        OSCOV = [[OVERRIDE.grooverride,OVERRIDE.matoverride]for OVERRIDE in bpy.context.scene.ovlist[:] if OVERRIDE.matoverride != "" if OVERRIDE.grooverride != ""]

        bpy.context.scene["OVERRIDE"] = str(OSCOV)
        return {'FINISHED'}   
    
class OscAddOverridesSlot (bpy.types.Operator):    
    """Tooltip"""
    bl_idname = "render.overrides_add_slot"
    bl_label = "Add Override Slot"

    def execute(self, context):
        prop = bpy.context.scene.ovlist.add()
        prop.matoverride = ""
        prop.grooverride = ""
        return {'FINISHED'}      

class OscRemoveOverridesSlot (bpy.types.Operator):    
    """Tooltip"""
    bl_idname = "render.overrides_remove_slot"
    bl_label = "Remove Override Slot"

    def execute(self, context):
        bpy.context.scene.ovlist.remove(len(bpy.context.scene.ovlist)-1)
        return {'FINISHED'} 
    
bpy.utils.register_class(OscTransferOverrides)
bpy.utils.register_class(OscAddOverridesSlot)
bpy.utils.register_class(OscRemoveOverridesSlot)
 
##======================================================================================FIN DE SCRIPTS


def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
