#view3d_multiselect_menu.py (c) 2011 Sean Olson (liquidApe)
#Original Script by: Mariano Hidalgo (uselessdreamer)
#contributed to by: Crouch, sim88, sam, meta-androcto, and Michael W
#
#Tested with r37702
#
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
    "name": "3D View: Multiselect Menu",
    "author": "Sean Olson (liquidApe)",
    "version": (1, 2),
    "blender": (2, 61, 0),
    "location": "View3D > Mouse > Menu ",
    "warning":"",
    "description": "Added options for multiselect to the ctrl-tab menu",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/3D_interaction/multiselect_Menu",
    "tracker_url": "https://projects.blender.org/tracker/index.php?"
                   "func=detail&aid=22132",
    "category": "3D View"}

import bpy

# multiselect menu
class VIEW3D_MT_Multiselect_Menu(bpy.types.Menu):
    bl_label = "MultiSelect Menu"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.separator()
        prop = layout.operator("wm.context_set_value", text="Vertex Select",
            icon='VERTEXSEL')
        prop.value = "(True, False, False)"
        prop.data_path = "tool_settings.mesh_select_mode"

        prop = layout.operator("wm.context_set_value", text="Edge Select",
            icon='EDGESEL')
        prop.value = "(False, True, False)"
        prop.data_path = "tool_settings.mesh_select_mode"

        prop = layout.operator("wm.context_set_value", text="Face Select",
            icon='FACESEL')
        prop.value = "(False, False, True)"
        prop.data_path = "tool_settings.mesh_select_mode"
        layout.separator()

        prop = layout.operator("wm.context_set_value",
            text="Vertex & Edge Select", icon='EDITMODE_HLT')
        prop.value = "(True, True, False)"
        prop.data_path = "tool_settings.mesh_select_mode"

        prop = layout.operator("wm.context_set_value",
            text="Vertex & Face Select", icon='ORTHO')
        prop.value = "(True, False, True)"
        prop.data_path = "tool_settings.mesh_select_mode"

        prop = layout.operator("wm.context_set_value",
            text="Edge & Face Select", icon='SNAP_FACE')
        prop.value = "(False, True, True)"
        prop.data_path = "tool_settings.mesh_select_mode"
        layout.separator()

        prop = layout.operator("wm.context_set_value",
            text="Vertex & Edge & Face Select", icon='SNAP_VOLUME')
        prop.value = "(True, True, True)"
        prop.data_path = "tool_settings.mesh_select_mode"
        layout.separator()

def register():
    bpy.utils.register_module(__name__)
    
    #add multiselect keybinding
    km = bpy.context.window_manager.keyconfigs.active.keymaps['Mesh']
    kmi = km.keymap_items.new('wm.call_menu', 'TAB', 'PRESS', ctrl=True)
    kmi.properties.name = "VIEW3D_MT_Multiselect_Menu"

    #remove default keybinding
    km = bpy.context.window_manager.keyconfigs.active.keymaps['Mesh']
    for kmi in km.keymap_items:
        if kmi.idname == 'wm.call_menu':
            if kmi.properties.name == "VIEW3D_MT_edit_mesh_select_mode":
                km.keymap_items.remove(kmi)
                break

def unregister():
    bpy.utils.unregister_module(__name__)

    #remove multiselect keybinding
    km = bpy.context.window_manager.keyconfigs.active.keymaps['Mesh']
    for kmi in km.keymap_items:
        if kmi.idname == 'wm.call_menu':
            if kmi.properties.name == "VIEW3D_MT_Multiselect_Menu":
                km.keymap_items.remove(kmi)
                break

    #replace default keymap
    km = bpy.context.window_manager.keyconfigs.active.keymaps['Mesh']
    kmi = km.keymap_items.new('wm.call_menu', 'TAB', 'PRESS', ctrl=True)
    kmi.properties.name = "VIEW3D_MT_edit_mesh_select_mode"

if __name__ == "__main__":
    register()
