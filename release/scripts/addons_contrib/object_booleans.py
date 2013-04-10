bl_info = {
    "name": "Boolean Operators",
    "location": "View3D > Toolbar",
    "description": "Add Boolean Tools for running boolean operations on two selected objects.",
    "author": "Jonathan Williamson",
    "version": (0,4),
    "blender": (2, 6, 6),
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/3D_interaction/booleanoperators",
    "tracker_url": "http://projects.blender.org/tracker/index.php?func=detail&aid=34502&group_id=153&atid=467",
    "category": "3D View",
    }

import bpy

###------ Create Boolean Operators -------###
   
class boolean(bpy.types.Operator):
    """Boolean the currently selected objects"""
    bl_idname = "mesh.boolean"
    bl_label = "Boolean Operator"
    bl_options = {'REGISTER', 'UNDO'}     
            
    modOp = bpy.props.StringProperty()
            
    def execute(self, context):
 
        scene = bpy.context.scene
         
        modName = "Bool"
    
        activeObj = context.active_object
        selected = context.selected_objects

        if selected:
            if len(selected) > 1:
                if len(selected) == 2:
                    for ob in selected:
                        if ob != activeObj:
                            nonActive = ob
    
                    bpy.ops.object.modifier_add(type="BOOLEAN")   
                    
                    for mod in activeObj.modifiers:
                        if mod.type == 'BOOLEAN':
                            mod.operation = self.modOp
                            mod.object = nonActive
                            mod.name = modName
                    
                    bpy.ops.object.modifier_apply(apply_as='DATA', modifier=modName)
                    scene.objects.active = nonActive 
                    activeObj.select = False
                    bpy.ops.object.delete(use_global=False)
                    activeObj.select = True
                    scene.objects.active = activeObj
                else:
                    self.report({'INFO'}, "Select only 2 objects at a time")
            else:
                self.report({'INFO'}, "Only 1 object selected")
        else:
            self.report({'INFO'}, "No objects selected")
                
        return {"FINISHED"}     


###------- Create the Boolean Menu --------###          

class booleanMenu(bpy.types.Menu):
    bl_label = "Boolean Tools"
    bl_idname = "object.boolean_menu"
       
    def draw(self, context):
        layout = self.layout
        
        union = layout.operator("mesh.boolean", "Union")
        union.modOp = 'UNION'
        
        intersect = layout.operator("mesh.boolean", "Intersect")
        intersect.modOp = 'INTERSECT'
        
        difference = layout.operator("mesh.boolean", "Difference")
        difference.modOp = 'DIFFERENCE'


###------- Create the Boolean Toolbar --------###          

class booleanToolbar(bpy.types.Panel):
    bl_label = "Boolean Tools"
    bl_idname = "object.boolean_toolbar"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = 'objectmode'
    
    def draw(self, context):
        layout = self.layout
        
        col = layout.column(align=True)
        
        col.label(text="Operation:", icon="MOD_BOOLEAN")
        
        row = col.row()
        union = row.operator("mesh.boolean", "Union")
        union.modOp = 'UNION'
        
        intersect = row.operator("mesh.boolean", "Intersect")
        intersect.modOp = 'INTERSECT'
        
        difference = row.operator("mesh.boolean", "Difference")
        difference.modOp = 'DIFFERENCE'
    
###------- Define the Hotkeys and Register Operators ---------###

addon_keymaps = []
    
            
def register():
    bpy.utils.register_class(boolean)
    bpy.utils.register_class(booleanMenu)
    bpy.utils.register_class(booleanToolbar)
    
    wm = bpy.context.window_manager
    
    # create the boolean menu hotkey
    km = wm.keyconfigs.addon.keymaps.new(name='Object Mode', space_type='EMPTY')
    kmi = km.keymap_items.new('wm.call_menu', 'B', 'PRESS', ctrl=True, shift=True)
    kmi.properties.name = 'object.boolean_menu'

    addon_keymaps.append(km)
    
def unregister():
    bpy.utils.unregister_class(boolean)
    bpy.utils.unregister_class(booleanMenu)
    bpy.utils.unregister_class(booleanToolbar)
    
    
    # remove keymaps when add-on is deactivated
    wm = bpy.context.window_manager
    for km in addon_keymaps:
        wm.keyconfigs.addon.keymaps.remove(km)
    del addon_keymaps[:]
    
if __name__ == "__main__":
    register()