bl_info = {
    "name": "Oscurart Chain and Rope Maker",
    "author": "Oscurart",
    "version": (1,1),
    "blender": (2, 6, 2),
    "api": 3800,
    "location": "Add > Mesh",
    "description": "Create chains and ropes",
    "warning": "",
    "wiki_url": "oscurart.blogspot.com",
    "tracker_url": "",
    "category": "Object"}


import bpy
from .oscurart_rope_maker import * 
from .oscurart_chain_maker import *

def register():
    bpy.utils.register_class(OBJECT_OT_add_object)
    bpy.types.INFO_MT_curve_add.append(oscRopeButton)
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_mesh_add.append(menu_oscChain)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_add_object)
    bpy.types.INFO_MT_curve_add.remove(oscRopeButton)
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_mesh_add.remove(menu_oscChain)    

if __name__ == "__main__":
    register()





