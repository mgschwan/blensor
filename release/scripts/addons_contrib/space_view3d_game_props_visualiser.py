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

# <pep8 compliant>


bl_info = {
    'name': 'Game Property Visualizer',
    'author': 'Bartius Crouch/Vilem Novak',
    'version': (2,5),
    'blender': (2, 5, 3),
    'location': 'View3D > Properties panel > Display tab',
    'description': 'Display the game properties next to selected objects '\
        'in the 3d-view',
    'warning': 'Script is returning errors',
    'wiki_url': 'http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/3D_interaction/Game_Property_Visualiser',
    'tracker_url': 'http://projects.blender.org/tracker/?func=detail&aid=22607&group_id=153&atid=468',
    'category': '3D View'}

"""
Displays game properties next to selected objects(under name)

How to use:
    just toggle the button 'Visualize game props' in the right side panel
"""

import bgl
import blf
import bpy
import mathutils


# calculate locations and store them as ID property in the mesh
def calc_callback(self, context):
    # polling
    if context.mode == 'EDIT_MESH':
        return
    
    # get screen information
    mid_x = context.region.width/2.0
    mid_y = context.region.height/2.0
    width = context.region.width
    height = context.region.height
    
    # get matrices
    view_mat = context.space_data.region_3d.perspective_matrix

    ob_mat = context.active_object.matrix_world
    total_mat = view_mat*ob_mat
    
    # calculate location info
    texts = []
    
    # uncomment 2 lines below, to enable live updating of the selection
    #ob=context.active_object
    for ob in context.selected_objects:
        locs = []
        ob_mat = ob.matrix_world
        total_mat = view_mat*ob_mat
 
        for p in ob.game.properties:
            # d = {'data':p.name+':'+str(p.value)}
            # print (d)
            locs.append([ mathutils.Vector([0,0,0]).resize_4d()])
    
    
        for loc in locs:
    
            vec = loc[0]*total_mat # order is important
            # dehomogenise
            vec = mathutils.Vector((vec[0]/vec[3],vec[1]/vec[3],vec[2]/vec[3]))
            x = int(mid_x + vec[0]*width/2.0)
            y = int(mid_y + vec[1]*height/2.0)
            texts+=[x, y]
        

    # store as ID property in mesh
    #print (texts)
    context.scene['GamePropsVisualizer'] = texts


# draw in 3d-view
def draw_callback(self, context):
    # polling
    if context.mode == 'EDIT_MESH':
        return
    # retrieving ID property data
    try:
        #print(context.scene['GamePropsVisualizer'])
        texts = context.scene['GamePropsVisualizer']
        
    except:
        return
    if not texts:
        return
    
    # draw
    i=0

    blf.size(0, 12, 72)
   
        
    bgl.glColor3f(1.0,1.0,1.0)
    for ob in bpy.context.selected_objects:
        for pi,p in enumerate(ob.game.properties):
            blf.position(0, texts[i], texts[i+1]-(pi+1)*14, 0)
            if p.type=='FLOAT':
                t=p.name+':  '+ str('%g'% p.value)
            else:    
                t=p.name+':  '+ str(p.value)
            blf.draw(0, t)
            i+=2


# operator
class GamePropertyVisualizer(bpy.types.Operator):
    bl_idname = "view3d.game_props_visualizer"
    bl_label = "Game Properties Visualizer"
    bl_description = "Toggle the visualization of game properties"
    
    @classmethod
    def poll(cls, context):
        return context.mode!='EDIT_MESH'
    
    def modal(self, context, event):
        context.area.tag_redraw()

        # removal of callbacks when operator is called again
        #print(context.scene.display_game_properties)
        if context.scene.display_game_properties == -1:
           # print('deinit2')

            context.scene.display_game_properties = 0
            context.region.callback_remove(self.handle1)
            context.region.callback_remove(self.handle2)
            context.scene.display_game_properties = 0
            
            return {'FINISHED'}
        
        return {'PASS_THROUGH'}
    
    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            print(context.scene.display_game_properties)
            if context.scene.display_game_properties == 0 or context.scene.display_game_properties == -1:
                print('init')
                # operator is called for the first time, start everything
                context.scene.display_game_properties = 1
                self.handle1 = context.region.callback_add(calc_callback,
                    (self, context), 'POST_VIEW')
                self.handle2 = context.region.callback_add(draw_callback,
                    (self, context), 'POST_PIXEL')

                context.window_manager.modal_handler_add(self)
                return {'RUNNING_MODAL'}
            else:
                # operator is called again, stop displaying
                context.scene.display_game_properties = -1
                #print(dir(self))
                #
                return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, can't run operator")
            return {'CANCELLED'}


# defining the panel
def menu_func(self, context):
    col = self.layout.column(align=True)
    col.operator(GamePropertyVisualizer.bl_idname, text="Visualize game props")
    self.layout.separator()


def register():
    bpy.types.Scene.display_game_properties = bpy.props.IntProperty(name='Visualize Game Poperties')
    bpy.types.VIEW3D_PT_view3d_display.prepend(menu_func)

def unregister():
    del bpy.types.Scene.display_game_properties
    bpy.types.VIEW3D_PT_view3d_display.remove(menu_func)

if __name__ == "__main__":
    register()
