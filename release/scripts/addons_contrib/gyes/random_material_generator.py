# -*- coding: UTF-8 -*-
# first we import all the required modules

import bpy ,random , copy 
from bpy.props import *
import textwrap

def h_names(self,contex):
    h_list=list(rm.rm_history)
    h_list.sort()
    names=[]
    for x in h_list:
        names=names+[(x,x,x)]
    return names 

class random_material_class:
    """ this class contains all fuctions and variables concerning generation of random material """
    
    def __init__(self):
        """ several fuctions can be found here . All options for random generation . The History dictionary and several others."""
                   
        # various gui modes (simple, template etc)
        bpy.types.Scene.gui_mode = EnumProperty(attr='mode', name='Mode', items=(
('enable', 'Enable', 'Enable Disable material parameters for randomisation'),
('percentage', 'Percentage' , 'here you define the percentage randomisation for each parameter'),
('help', 'Help', 'Help documentation')), default='enable')

        # Here I define the selective areas that the user can enable or disable for randomisation in simple mode               
                     
        bpy.types.Scene.rdiffuse_shader = BoolProperty(name= "Diffuse Shader" ,description = "Enable/Disable Randomisation for the  Diffuse Shader " , default = True)
        bpy.types.Scene.rdiffuse_color = BoolProperty(name= "Diffuse Color" ,description = "Enable/Disable Randomisation for the Diffuse Color", default = True  )
        bpy.types.Scene.rdiffuse_intensity = BoolProperty(name= "Diffuse Intensity" ,description = "Enable/Disable Randomisation for the Diffuse Intensity" , default = True )    
        bpy.types.Scene.rspecular_color = BoolProperty(name= "Specular Color" ,description = "Enable/Disable Randomisation for the Specular Color" , default = True)
        bpy.types.Scene.rspecular_shader = BoolProperty(name= "Specular Shader" ,description = "Enable/Disable Randomisation for the Specular Shader" , default = True)
        bpy.types.Scene.rspecular_intensity = BoolProperty(name= "Specular Intensity" ,description = "Enable/Disable Randomisation for the Specular Intensity" , default = True)
        bpy.types.Scene.rspecular_hardness = BoolProperty(name= "Specular Hardness" ,description = "Enable/Disable Randomisation for the Specular Hardness" , default = True)
        bpy.types.Scene.rtransparency = BoolProperty(name= "Transparency" ,description = "Use and Randomise Transparency" , default = True)
        bpy.types.Scene.rtexture = BoolProperty(name= "Texture" ,description = "Use and Randomise Textures" , default = True)
        
        # Percentage randomisation
        bpy.types.Scene.general_percentage = IntProperty(name="General percentage", description = " General percentage of randomisation" , min = 0 , max = 100 , default = 100, subtype = 'PERCENTAGE')
        bpy.types.Scene.rdiffuse_shader_percentage =  IntProperty(name="Diffuse shader", description = " Diffuse shader percentage of randomisation" , min = 0 , max = 100 , default = 0, subtype = 'PERCENTAGE')
        bpy.types.Scene.rdiffuse_color_percentage =  IntProperty(name="Diffuse Color", description = " Diffuse Color percentage of randomisation" , min = 0 , max = 100 , default = 0, subtype = 'PERCENTAGE')
        bpy.types.Scene.rdiffuse_intensity_percentage =  IntProperty(name="Diffuse Intensity", description = " Diffuse Intensity percentage of randomisation" , min = 0 , max = 100 , default = 0, subtype = 'PERCENTAGE')
        bpy.types.Scene.rspecular_color_percentage =  IntProperty(name="Specular Color", description = " Specular Color percentage of randomisation" , min = 0 , max = 100 , default = 0 , subtype = 'PERCENTAGE')
        bpy.types.Scene.rspecular_shader_percentage =  IntProperty(name="Specular Shader", description = " Specular Shader percentage of randomisation" , min = 0 , max = 100 , default = 0, subtype = 'PERCENTAGE')
        bpy.types.Scene.rspecular_intensity_percentage =  IntProperty(name="Specular Intensity", description = " Specular Intensity percentage of randomisation" , min = 0 , max = 100 , default = 0, subtype = 'PERCENTAGE')
        bpy.types.Scene.rspecular_hardness_percentage =  IntProperty(name="Specular Hardness", description = " Specular Hardness percentage of randomisation" , min = 0 , max = 100 , default = 0, subtype = 'PERCENTAGE')
        bpy.types.Scene.rtransparency_percentage =  IntProperty(name="Transparency", description = " Transparency percentage of randomisation" , min = 0 , max = 100 , default = 0, subtype = 'PERCENTAGE')
        
        # this is the dictionary that stores history
        bpy.types.Scene.history_index = IntProperty(name= "History Index" ,description = "The Number of Random Material Assigned to the Active MAterial of the Selected Object from the history" , default = 1, min = 1 )
        bpy.types.Scene.filter = StringProperty(name="Filter", description ="Filter text , only if the text matches even partially with the material name will be stored")
        self.rm_history={"slot 01":{1:{}} , "slot 02":{1:{}} , "slot 03":{1:{}} ,"slot 04":{1:{}} ,"slot 05":{1:{}} ,"slot 06":{1:{}} ,
                         "slot 07":{1:{}} ,"slot 08":{1:{}} , "slot 09":{1:{}} , "slot 10":{1:{}} ,"slot 11":{1:{}} ,"slot 12":{1:{}} }
        self.delete_start_index=1
        bpy.types.Scene.h_selected = EnumProperty(attr='name', name='Name :', items=h_names)
        
        
        # the prop that controls the text wrap in help menu
        bpy.types.Scene.text_width = IntProperty(name = "Text Width" , description = "The width above which the text wraps" , default = 20 , max = 180 , min = 1)
        
        # here is where history dictionary is saved with the blend file
        # if the backup is already saved with the blend file it is used 
        # to restory the history dictionary , if not it is created
        
        if hasattr(bpy.context.scene , "historybak")==False:
            bpy.types.Scene.historybak = StringProperty()
            print("Gyes log : created history backup")
            
         # non read only material properties where keyframes can be inserted or removed
        self.animated_properties=["alpha",
        "ambient",
        "darkness",
        "diffuse_color",
        "diffuse_fresnel",
        "diffuse_fresnel_factor",
        "diffuse_intensity",
        "diffuse_ramp_blend",
        "diffuse_ramp_factor",
        "diffuse_ramp_input",
        "diffuse_shader",
        "diffuse_toon_size",
        "diffuse_toon_smooth",
        "emit",
        "invert_z",
        "mirror_color",
        "offset_z",
        "preview_render_type",
        "roughness",
        "shadow_buffer_bias",
        "shadow_cast_alpha",
        "shadow_only_type",
        "shadow_ray_bias",
        "specular_alpha",
        "specular_color",
        "specular_hardness",
        "specular_intensity",
        "specular_ior",
        "specular_ramp_blend",
        "specular_ramp_factor",
        "specular_ramp_input",
        "specular_shader",
        "specular_slope",
        "specular_toon_size",
        "specular_toon_smooth",
        "translucency",
        "transparency_method",
        "type",
        "use_cast_approximate",
        "use_cast_buffer_shadows",
        "use_cast_shadows_only",
        "use_cubic",
        "use_diffuse_ramp",
        "use_face_texture",
        "use_face_texture_alpha",
        "use_full_oversampling",
        "use_light_group_exclusive",
        "use_mist",
        "use_nodes",
        "use_object_color",
        "use_only_shadow",
        "use_ray_shadow_bias",
        "use_raytrace",
        "use_shadeless",
        "use_shadows",
        "use_sky",
        "use_specular_ramp",
        "use_tangent_shading",
        "use_textures",
        "use_transparency",
        "use_transparent_shadows",
        "use_vertex_color_paint"]
            
    
       
    # compute randomisation based on the general or specific percentage chosen
    # if the specific percentage is zero then the general percentage is used
    def compute_percentage(self,min,max,value,percentage):
        range = max-min
        general_percentage = bpy.context.scene.general_percentage
        
        if percentage == 0:
            percentage_random = ( value -((range*(general_percentage/100))/2) )+ (range * (general_percentage / 100) * random.random())
        else:
            percentage_random = ( value - ((range*(percentage/100))/2)) + (range * (percentage / 100) * random.random())
             
        if percentage_random > max:
            percentage_random = max
        if percentage_random < min:
            percentage_random = min
        
        return percentage_random 
    
    #deletes from history an index but without leaving empty spaces, everythings is pushed back    
    def delete_from_history(self):
        h_name = bpy.context.scene.h_selected
        length = len(self.rm_history[h_name])
        index = bpy.context.scene.history_index
        for x in range(index , length):
            if index != length :
                self.rm_history[h_name][x]= self.rm_history[h_name][x+1] 
        del self.rm_history[h_name][length]
        length = len(self.rm_history[h_name]) 
        if index <= length:
            self.activate()
            
        bpy.context.scene.historybak = str(self.rm_history)
    
    # the fuction that randomises the material 
    def random_material(self,active_material,name):
        mat = active_material
        scn = bpy.context.scene
             
        #checks that the user has allowed the randomisation of that specific parameter            
        if scn.rdiffuse_color:
            rand_perc = scn.rdiffuse_color_percentage
            mat.diffuse_color = (self.compute_percentage(0,1,mat.diffuse_color[0],rand_perc),
            self.compute_percentage(0,1,mat.diffuse_color[1],rand_perc),
            self.compute_percentage(0,1,mat.diffuse_color[2],rand_perc))
            
 
        if scn.rdiffuse_shader:
            mat.diffuse_shader = random.choice(['LAMBERT','FRESNEL','TOON','MINNAERT'])
    
        if scn.rdiffuse_intensity:
            mat.diffuse_intensity = self.compute_percentage(0,1, mat.diffuse_intensity , scn.rdiffuse_intensity_percentage) 
    
        if scn.rspecular_color:
            rand_perc = scn.rspecular_color_percentage
            mat.specular_color = (self.compute_percentage(0,1,mat.specular_color[0],rand_perc),
            self.compute_percentage(0,1,mat.specular_color[1],rand_perc),
            self.compute_percentage(0,1,mat.specular_color[2],rand_perc))
    
        if scn.rspecular_shader:
            mat.specular_shader = random.choice(['COOKTORR','WARDISO','TOON','BLINN','PHONG'])
    
        if scn.rspecular_intensity:
            mat.specular_intensity =  self.compute_percentage(0,1, mat.specular_intensity , scn.rspecular_intensity_percentage)
    
        if scn.rspecular_hardness:
            mat.specular_hardness =  round(self.compute_percentage(1,511, mat.specular_hardness, scn.rspecular_shader_percentage))
            
        mat.use_transparency = scn.rtransparency 
        
        if mat.use_transparency == True :
            mat.transparency_method == random.choice(['MASK', 'Z_TRANSPARENCY', 'RAYTRACE'])
            mat.alpha = self.compute_percentage(0,1, mat.alpha, scn.rtransparency_percentage)
  
            if mat.transparency_method == 'MASK' :
                bing =0     # dummy code
                
            if mat.transparency_method == 'Z_TRANSPARENCY' :
                bing =0     # dummy code
                mat.specular_alpha= random.random()
        
        if scn.rtexture :
            bpy.ops.gyes.random_texture()
            
        mat.ambient = self.compute_percentage(0,1, mat.ambient, scn.general_percentage)
        
        # after you finishes randomisation store the random material to history
        self.store_to_history(mat)
          
        return mat

   
    #store active material to history
    def store_to_history(self, mat):
        scn = bpy.context.scene
        history_index = scn.history_index
        h_name = scn.h_selected
        self.rm_history[h_name][history_index]={"name" : mat.name}
        print("Gyes log : mat stored : "+self.rm_history[h_name][history_index]["name"]+" in history name : "+h_name+" in index : "+str(history_index))
        mat.use_fake_user = True
                 
        bpy.context.scene.historybak = str(self.rm_history)
        
    # Activate. Make active material the particular history index the user has chosen
    def activate(self, random_assign = False):
        h_name = bpy.context.scene.h_selected
        for i in bpy.context.selected_objects :
            
            if random_assign == False and ( bpy.context.scene.history_index in rm.rm_history[h_name] ) and rm.rm_history[h_name][bpy.context.scene.history_index] and rm.rm_history[h_name][bpy.context.scene.history_index]["name"]:                
                scn = bpy.context.scene
                mat = i.active_material
                index = scn.history_index
                
                if len(i.material_slots) == 0:
                    print("Gyes log : no slot found creating a new one")
                    i.active_material= bpy.data.materials[self.rm_history[h_name][index]["name"]]
                else:
                    print("Gyes log : found slot assigning material")
                    i.material_slots[i.active_material_index].material= bpy.data.materials[self.rm_history[h_name][index]["name"]]
                
            if random_assign == True and ( bpy.context.scene.history_index in rm.rm_history[h_name] ) and rm.rm_history[h_name][bpy.context.scene.history_index] and rm.rm_history[h_name][bpy.context.scene.history_index]["name"]:
            
                index = round(len(self.rm_history) * random.random())
                
                if index == 0 :
                    index = 1
                    
                scn = bpy.context.scene
                mat = i.active_material
                scn.history_index=index
                
                if len(i.material_slots) == 0:
                    print("Gyes log : no slot found creating a new one")
                    i.active_material= bpy.data.materials[self.rm_history[h_name][index]["name"]]
                else:
                    print("Gyes log : found slot assigning material")
                    i.material_slots[i.active_material_index].material= bpy.data.materials[self.rm_history[h_name][index]["name"]]
              
            
            
                   
    # a nice multi label                        
    def multi_label(self, text, ui,text_width):
        
        for x in range(0,len(text)):
            el = textwrap.wrap(text[x], width = text_width)
            
            for y in range(0,len(el)):
                ui.label(text=el[y])
                
    def draw_gui(self ,context,panel):
        layout = panel.layout
        row = layout.row()
        
        row.prop(context.scene , "gui_mode" )
        
        # check which Gui mode the user has selected (Simple is the default one and display the appropriate gui
        
        if context.scene.gui_mode == 'enable' :
            
            box = layout.box()
            
            box.prop(context.scene,"rdiffuse_shader", toggle = True)
            box.prop(context.scene,"rdiffuse_color", toggle = True)
            box.prop(context.scene,"rdiffuse_intensity", toggle = True)
            box.prop(context.scene,"rspecular_shader", toggle = True)
            box.prop(context.scene,"rspecular_color", toggle = True)
            box.prop(context.scene,"rspecular_intensity", toggle = True)
            box.prop(context.scene,"rspecular_hardness", toggle = True)
            box.prop(context.scene,"rtransparency", toggle = True)
            box.prop(context.scene,"rtexture", toggle = True)
            
            box.prop(context.scene,"general_percentage", slider = True)           
            layout.operator("gyes.random_material")
            
        if context.scene.gui_mode == 'percentage' :
            box = layout.box()
            
            if context.scene.rdiffuse_shader :
                box.prop(context.scene,"rdiffuse_shader_percentage", slider = True)
            else:
                box.label(text="Diffuse Shader is disabled ")
                
            if context.scene.rdiffuse_color :
                box.prop(context.scene,"rdiffuse_color_percentage", slider = True)
            else:
                box.label(text="Diffuse Color is disabled ")
                
            if context.scene.rdiffuse_intensity :
                box.prop(context.scene,"rdiffuse_intensity_percentage", slider = True)
            else:
                box.label(text="Diffuse Intensity is disabled ")
                
            if context.scene.rspecular_shader :
                box.prop(context.scene,"rspecular_shader_percentage", slider = True)
            else:
                box.label(text="Specular Shader is disabled ")
                
            if context.scene.rspecular_color :
                box.prop(context.scene,"rspecular_color_percentage", slider = True)
            else:
                box.label(text="Specular Color is disabled ")
                
            if context.scene.rspecular_intensity :
                box.prop(context.scene,"rspecular_intensity_percentage", slider = True)
            else:
                box.label(text="Specular Intensity is disabled ")
                
            if context.scene.rspecular_hardness :
                box.prop(context.scene,"rspecular_hardness_percentage", slider = True)
            else:
                box.label(text="Specular Hardness is disabled ")
            
            if context.scene.rtransparency :
                box.prop(context.scene,"rtransparency_percentage", slider = True)
            else:
                box.label(text="Transparency is disabled ")
                
            box.prop(context.scene,"general_percentage", slider = True)
            layout.operator("gyes.random_material")
        
                           
        if context.scene.gui_mode== 'help' :
            box = layout.box()
            help_text=["","Copyright 2011 Kilon  ",
            "GYES - RGM",    
            "Random Material  Generator",
            "A tool that generates random materials.",
            "",
            "Simple Mode",
            "--------------------------",
            "In this mode you can do basic randomisation. Choose parameters you want to randomise by turning them on or off with clicking on them. Hit the random button when you are ready. Each time you hit the button the new random material is stored in a history index",
            "",
            "History",
            "--------------------------",
            "History index -> choose index",
            "( < ) -> Previous index (activate)",
            "( > ) -> Next index (activate)",
            "( |< ) -> First history index",
            "( >| ) -> Last history index",
            "Activate -> use this index as active material",
            "Animate -> Insert a keyframe in the current frame for every singly non read only material property",
            "X -> Remove a keyframe in the current frame for every singly non read only material property",
            "R -> works just like activate but instead of using the current selected index use a randomly selected one",
            "Delete -> delete this index",
            "Del start -> start deletion from here",
            "Del end -> end deletion here",
            "Restore -> restores history from the saved blend file",
            "",
            "Percentage",
            "--------------------------",
            "Percentage randomisation means that the parameter is randomised inside a range of percentage of the full range of the value. When a specific percentage is zero, the general percentage is used instead for that area. When a specific percentage is not zero then general percentage is ignored and specific percentage is used instead. If you dont want to randomise that area at all, in Simple Mode use the corresponding button to completely disable that area , the percentage slider will also be disable in the percentage mode. Randomisation takes always the current value as starting point so the next randomisation will use the current randomised value. Randomisation is always 50% of the specific percentage bellow the current value and 50% above . If the percentage exceeed minimum and maximum values of the full range, then it will default to minimum and maximum accordingly. "]
            w=bpy.context.scene.text_width
            box.prop(context.scene,"text_width", slider =True)
            self.multi_label(help_text,box,w) 
                                
        # Display the History Gui for all modes
        h_name=bpy.context.scene.h_selected
        layout.label(text="History (RMG + RTG)")
        history_box= layout.box()
        history_box.prop(context.scene, "h_selected")
        history_box.prop(context.scene, "history_index")
        row = history_box.row()
        row.operator("gyes.first")
        row.operator("gyes.previous")
        row.operator("gyes.next")
        row.operator("gyes.last")
        rm_index = context.scene.history_index
        
        if rm_index in self.rm_history[h_name] and self.rm_history[h_name][rm_index] :
            row = history_box.row()
            a = row.split(percentage = 0.3, align = True)
            a.operator("gyes.activate")
            a.operator("gyes.animate")
            b=a.split(percentage = 0.3, align = True)
            b.operator("gyes.x")
            b.operator("gyes.random_activate")                       
        else:
            
            row = history_box.row()
            a = row.split(percentage = 0.3, align = True)
            a.label(text= "Empty Index ! ")
            a.operator("gyes.animate")
            b=a.split(percentage = 0.3, align = True)
            b.operator("gyes.x")
            b.operator("gyes.random_activate")  
        
        if context.scene.history_index < len(self.rm_history[h_name])+2:
            history_box.operator("gyes.store")
        else:
            history_box.label(text= "Not the first Empty Index")
            
        if rm_index in self.rm_history[h_name] and self.rm_history[h_name][rm_index] :
            history_box.operator("gyes.delete")
            row2 = history_box.row()
            row2.operator("gyes.delete_start")
            row2.operator("gyes.delete_end")
            
        if hasattr(bpy.context.scene,"historybak") and bpy.context.scene.historybak!='':
            history_box.operator("gyes.restore")
        else:
            history_box.label(text="Backup not Found")
        history_box.prop(context.scene,"filter")
        history_box.operator("gyes.import_materials")                            
# create the instance class for randomisation   
rm =random_material_class()

            
        
# Generate the random material button
class gyes_random_material(bpy.types.Operator):
    
    bl_idname = "gyes.random_material"
    bl_label = "Random Material"
    label = bpy.props.StringProperty()
    bl_description = "Generate the random material"
    
    def execute(self, context):
        for i in context.selected_objects :
            if not i.material_slots:
                print("Gyes log : no material_slot found , creating new with material")
                new_random = bpy.data.materials.new("Random")
                i.active_material=new_random
                rm.random_material(i.active_material,'Random')


            if i.material_slots[0].material:
                print("Gyes log : found an existing material, using this one ")
                rm.random_material(i.active_material,'Random')

            if not i.material_slots[0].material:
                print("Gyes log : no material found , creating new")
                new_random = bpy.data.materials.new("Random")
                i.active_material=new_random
                rm.random_material(i.active_material,'Random')

        return{'FINISHED'}

# Move to the first history index and activate it
class history_first(bpy.types.Operator):
    
    bl_label = "|<"
    bl_idname = "gyes.first"
    bl_description = "Move to the first history index and activate it"
    
    def execute(self, context):
        context.scene.history_index = 1 
        rm.activate()
        
        return{'FINISHED'}

# Move to the previous hisory index and activate it
class history_previous(bpy.types.Operator):
    
    bl_label = "<"
    bl_idname = "gyes.previous"
    bl_description = "Move to the previous history index and activate it"
    
    def execute(self, context):
        if context.scene.history_index > 1 :
            context.scene.history_index = context.scene.history_index -1
            rm_index = context.scene.history_index
            h_name = bpy.context.scene.h_selected
            if rm_index in rm.rm_history[h_name] and rm.rm_history[h_name][rm_index]:
                rm.activate()
        
        return{'FINISHED'}

# Move to the next hisory index and activate it
class history_next(bpy.types.Operator):
    
    bl_label = ">"
    bl_idname = "gyes.next"
    bl_description = "Move to the next history index and activate it"
    
    def execute(self, context):
        if context.scene.history_index > 0 :
            context.scene.history_index = context.scene.history_index +1
            rm_index = context.scene.history_index
            h_name = bpy.context.scene.h_selected
            if rm_index in rm.rm_history[h_name] and rm.rm_history[h_name][rm_index]:
                rm.activate()
        
        return{'FINISHED'}
    

# Move to the last hisory index and activate it
class history_last(bpy.types.Operator):
    
    bl_label = ">|"
    bl_idname = "gyes.last"
    bl_description = "Move to the last history index and activate it"
    
    def execute(self, context):
        h_name= bpy.context.scene.h_selected
        index = rm.rm_history[h_name] 
        context.scene.history_index = len(index) 
        rm.activate()
        
        return{'FINISHED'}

# The current history index becomes the active material 
class history_activate(bpy.types.Operator):
    
    bl_label = "Activate"
    bl_idname = "gyes.activate"
    bl_description = "The current history index becomes the active material"
    
    def execute(self, context):
        rm_index = context.scene.history_index
        h_name = bpy.context.scene.h_selected
        if rm.rm_history[h_name][rm_index] != {}:
            rm.activate()
        
        return{'FINISHED'}

# A random history index becomes the active material 
class history_random_activate(bpy.types.Operator):
    
    bl_label = "R"
    bl_idname = "gyes.random_activate"
    bl_description = "A random history index becomes the active material"
    
    def execute(self, context):
        rm_index = context.scene.history_index
        h_name = bpy.context.scene.h_selected
        if rm.rm_history[h_name][rm_index] != {}:
            rm.activate(random_assign = True)
        
        return{'FINISHED'}


# It stores current active material to the selected history index
class store_to_history(bpy.types.Operator):
    
    bl_label = "Store"
    bl_idname = "gyes.store"
    bl_description = " It stores current active material to the selected history index"
    
    def execute(self, context):
        mat = context.selected_objects[0].active_material
        rm.store_to_history(mat)
                 
        return{'FINISHED'}

# Delete selected history index from history
class delete_from_history(bpy.types.Operator):
    
    bl_label = "Delete"
    bl_idname = "gyes.delete"
    bl_description = "Delete selected history index from history"
    
    def execute(self, context):
        rm.delete_from_history()
        
        return{'FINISHED'}
               
# Start deletion from this index
class delete_from_history_start(bpy.types.Operator):
    
    bl_label = "Del Start"
    bl_idname = "gyes.delete_start"
    bl_description = "Start deletion from this index"
    
    def execute(self, context):
        rm_index = context.scene.history_index
        rm.delete_start_index = rm_index
        
        return{'FINISHED'}   

# End deletion here and delete all selected indices
class delete_from_history_end(bpy.types.Operator):
    
    bl_label = "Del End"
    bl_idname = "gyes.delete_end"
    bl_description = "End deletion here and delete all selected indices"
    
    def execute(self, context):
        delete_end_index = context.scene.history_index
        context.scene.history_index = rm.delete_start_index
        for x in range ( rm.delete_start_index , delete_end_index):
            rm.delete_from_history()
        
        return{'FINISHED'} 
    
# End deletion here and delete all selected indices
class restore_history(bpy.types.Operator):
    
    bl_label = "Restore"
    bl_idname = "gyes.restore"
    bl_description = "Restore history"
    
    def execute(self, context):
        
        s=""
        s = bpy.context.scene.historybak
       
        rm.rm_history=eval(s)
        
        print("Gyes log : restored history dictionary") 
        
        return{'FINISHED'} 
    
# Animate inserts a keyframe for every randomised material parameter except nodes
class animate(bpy.types.Operator):
    
    bl_label = "Animate"
    bl_idname = "gyes.animate"
    bl_description = "Animate inserts a keyframe for every non read only material parameter"
    
    def execute(self, context):
        framen = bpy.context.scene.frame_current
        for i in range(0,len(bpy.context.selected_objects)):
            mat = bpy.context.selected_objects[i].active_material
                        
            for y in range(0,len(rm.animated_properties)):
                mat.keyframe_insert(data_path = rm.animated_properties[y], frame = framen)
        
        return{'FINISHED'}
 
# Remove Animation
class x(bpy.types.Operator):
    
    bl_label = "X"
    bl_idname = "gyes.x"
    bl_description = "Reverse Animate by deleting every keyframe inserted by animate for every non read only material parameter"
    
    def execute(self, context):
        framen = bpy.context.scene.frame_current
        for i in range(0,len(bpy.context.selected_objects)):
            mat = bpy.context.selected_objects[i].active_material
            
            for y in range(0,len(rm.animated_properties)):
                mat.keyframe_delete(data_path = rm.animated_properties[y], frame = framen)
        
        return{'FINISHED'}

# Move to the first history index and activate it
class import_materials(bpy.types.Operator):
    
    bl_label = "Import"
    bl_idname = "gyes.import_materials"
    bl_description = "Import all materials matching filter in the active history"
    
    def execute(self, context):
        filter = bpy.context.scene.filter
        h_name = bpy.context.scene.h_selected
        bpy.context.scene.history_index = len(rm.rm_history[h_name])+1
        for mat in bpy.data.materials:
            if filter in mat.name:
                rm.store_to_history(mat)
                bpy.context.scene.history_index = bpy.context.scene.history_index+1
                    
                
                
        
        return{'FINISHED'}





#registration is necessary for the script to appear in the GUI
def register():
    bpy.utils.register_class(gyes_panel)
    bpy.utils.register_class(gyes_random_material)
    bpy.utils.register_class(history_previous)
    bpy.utils.register_class(history_next)
    bpy.utils.register_class(history_activate)
    bpy.utils.register_class(history_random_activate)
    bpy.utils.register_class(store_to_history)
    bpy.utils.register_class(delete_from_history)
    bpy.utils.register_class(delete_from_history_start)
    bpy.utils.register_class(delete_from_history_end)
    bpy.utils.register_class(history_first)
    bpy.utils.register_class(history_last)
    bpy.utils.register_class(restore_history)
    bpy.utils.register_class(animate)
    bpy.utils.register_class(x)
    bpy.utils.register_class(import_materials)
def unregister():
    bpy.utils.unregister_class(gyes_panel)
    bpy.utils.unregister_class(gyes_random_material)
    bpy.utils.unregister_class(history_previous)
    bpy.utils.unregister_class(history_next)
    bpy.utils.unregister_class(history_activate)
    bpy.utils.unregister_class(history_random_activate)
    bpy.utils.unregister_class(store_to_history)
    bpy.utils.unregister_class(delete_from_history)
    bpy.utils.unregister_class(delete_from_history_start)
    bpy.utils.unregister_class(delete_from_history_end)
    bpy.utils.unregister_class(history_first)
    bpy.utils.unregister_class(history_last)
    bpy.utils.unregister_class(restore_history)
    bpy.utils.unregister_class(animate)
    bpy.utils.unregister_class(x)
    bpy.utils.unregister_class(import_materials)
if __name__ == '__main__':
    register()
