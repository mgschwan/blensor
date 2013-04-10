'''# ##### BEGIN GPL LICENSE BLOCK #####
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
    "name": "Scene Lighting Presets",
    "author": "meta-androcto",
    "version": (0,1),
    "blender": (2, 63, 0),
    "location": "View3D > Tool Shelf > Scene Lighting Presets",
    "description": "Creates Scenes with Lighting presets",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/",
    "tracker_url": "",
    "category": "Object"}
'''	
import bpy, mathutils, math
from math import pi
from bpy.props import *
from mathutils import Vector

class add_scene_camera(bpy.types.Operator):
    bl_idname = "camera.add_scene"
    bl_label = "Camera Only"
    bl_description = "Empty scene with Camera"
    bl_register = True
    bl_undo = True
    
    def execute(self, context):
        blend_data = context.blend_data
        ob = bpy.context.active_object
	
# add new scene
        bpy.ops.scene.new(type="NEW")
        scene = bpy.context.scene
        scene.name = "scene_camera"
# render settings
        render = scene.render
        render.resolution_x = 1920
        render.resolution_y = 1080
        render.resolution_percentage = 50
# add new world
        world = bpy.data.worlds.new("Camera_World")
        scene.world = world
        world.use_sky_blend = True
        world.use_sky_paper = True
        world.horizon_color = (0.004393,0.02121,0.050)
        world.zenith_color = (0.03335,0.227,0.359)
        world.light_settings.use_ambient_occlusion = True
        world.light_settings.ao_factor = 0.25
# add camera
        bpy.ops.object.camera_add(location = (7.48113,-6.50764,5.34367), rotation = (1.109319,0.010817,0.814928),)
        cam = bpy.context.active_object.data
        cam.lens = 35
        cam.draw_size = 0.1

        return {"FINISHED"}

#### REGISTER ####
def add_object_button(self, context):
    self.layout.menu("INFO_MT_camera.add_scene", icon="PLUGIN")

def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_add.append(add_object_button)

def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_add.remove(add_object_button)


if __name__ == '__main__':
    register()
