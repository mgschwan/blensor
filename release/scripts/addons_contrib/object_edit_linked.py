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
    "name": "Edit Linked Library",
    "author": "Jason van Gumster (Fweeb)",
    "version": (0, 7, 1),
    "blender": (2, 6, 0),
    "location": "View3D > Toolshelf > Edit Linked Library",
    "description": "Allows editing of objects linked from a .blend library.",
    "wiki_url": "http://wiki.blender.org/index.php?title=Extensions:2.5/Py/Scripts/Object/Edit_Linked_Library",
    "tracker_url": "http://projects.blender.org/tracker/index.php?func=detail&aid=29630&group_id=153&atid=467",
    "category": "Object"}
    

import bpy
from bpy.app.handlers import persistent

settings = {
    "original_file": "",
    "linked_file": "",
    "linked_objects": [],
    }

@persistent
def linked_file_check(context):
    if settings["linked_file"] != "":
        if settings["linked_file"] in {bpy.data.filepath, bpy.path.abspath(bpy.data.filepath)}:
            print("Editing a linked library.")
            bpy.ops.object.select_all(action = 'DESELECT')
            for ob_name in settings["linked_objects"]:
                bpy.data.objects[ob_name].select = True
            if len(settings["linked_objects"]) == 1:
                bpy.context.scene.objects.active = bpy.data.objects[settings["linked_objects"][0]]
        else:
            # For some reason, the linked editing session ended (failed to find a file or opened a different file before returning to the originating .blend)
            settings["original_file"] = ""
            settings["linked_file"] = ""



class EditLinked(bpy.types.Operator):
    '''Edit Linked Library'''
    bl_idname = "object.edit_linked"
    bl_label = "Edit Linked Library"

    autosave = bpy.props.BoolProperty(name = "Autosave", description = "Automatically save the current file before opening the linked library", default = True)

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        #print(bpy.context.active_object.library)
        target = context.active_object

        if target.dupli_group and target.dupli_group.library:
            targetpath = target.dupli_group.library.filepath
            settings["linked_objects"].extend([ob.name for ob in target.dupli_group.objects])
        elif target.library:
            targetpath = target.library.filepath
            settings["linked_objects"].append(target.name)

        if targetpath:
            print(target.name + " is linked to " + targetpath)

            if self.properties.autosave == True:
                bpy.ops.wm.save_mainfile()

            settings["original_file"] = bpy.data.filepath

            # XXX: need to test for proxied rigs
            settings["linked_file"] = bpy.path.abspath(targetpath)

            bpy.ops.wm.open_mainfile(filepath=settings["linked_file"])
            print("Opened linked file!")
        else:
            self.report({'WARNING'}, target.name + " is not linked")
            print(target.name + " is not linked")

        return {'FINISHED'}


class ReturnToOriginal(bpy.types.Operator):
    '''Return to the original file after editing the linked library .blend'''
    bl_idname = "wm.return_to_original"
    bl_label = "Return to Original File"

    autosave = bpy.props.BoolProperty(name = "Autosave", description = "Automatically save the current file before opening original file", default = True)

    @classmethod
    def poll(cls, context):
        # Probably the wrong context to check for here...
        return context.active_object is not None
    
    def execute(self, context):
        if self.properties.autosave == True:
            bpy.ops.wm.save_mainfile()
        bpy.ops.wm.open_mainfile(filepath=settings["original_file"])
        settings["original_file"] = ""
        settings["linked_objects"] = []
        print("Back to the original!")
        return {'FINISHED'}


# UI
# TODO: Add operators to the File menu? Hide the entire panel for non-linked objects?
class PanelLinkedEdit(bpy.types.Panel):
    bl_label = "Edit Linked Library"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"


    def draw(self, context):
        kc = bpy.context.window_manager.keyconfigs.addon
        km = kc.keymaps["3D View"]
        kmi_edit = km.keymap_items["object.edit_linked"]
        kmi_return = km.keymap_items["wm.return_to_original"]

        if settings["original_file"] == "" and ((context.active_object.dupli_group and context.active_object.dupli_group.library is not None) or context.active_object.library is not None):
            kmi_edit.active = True
            kmi_return.active = False
            self.layout.operator("object.edit_linked").autosave = context.scene.edit_linked_autosave
            self.layout.prop(context.scene, "edit_linked_autosave")
        elif settings["original_file"] != "":
            kmi_edit.active = False
            kmi_return.active = True
            self.layout.operator("wm.return_to_original").autosave = context.scene.edit_linked_autosave
            self.layout.prop(context.scene, "edit_linked_autosave")
        else:
            kmi_edit.active = False
            kmi_return.active = False
            self.layout.label(text = "Active object is not linked")


def register():
    bpy.app.handlers.load_post.append(linked_file_check)
    bpy.utils.register_class(EditLinked)
    bpy.utils.register_class(ReturnToOriginal)
    bpy.utils.register_class(PanelLinkedEdit)

    # Is there a better place to store this property?
    bpy.types.Scene.edit_linked_autosave = bpy.props.BoolProperty(name = "Autosave", description = "Automatically save the current file before opening a linked file", default = True)

    # Keymapping (deactivated by default; activated when a library object is selected)
    kc = bpy.context.window_manager.keyconfigs.addon
    km = kc.keymaps.new(name = "3D View", space_type='VIEW_3D')
    kmi = km.keymap_items.new("object.edit_linked", 'NUMPAD_SLASH', 'PRESS', shift = True)
    kmi.active = False
    kmi = km.keymap_items.new("wm.return_to_original", 'NUMPAD_SLASH', 'PRESS', shift = True)
    kmi.active = False


def unregister():
    bpy.utils.unregister_class(EditLinked)
    bpy.utils.unregister_class(ReturnToOriginal)
    bpy.utils.unregister_class(PanelLinkedEdit)
    bpy.app.handlers.load_post.remove(linked_file_check)

    del bpy.types.Scene.edit_linked_autosave

    kc = bpy.context.window_manager.keyconfigs.addon
    km = kc.keymaps["3D View"]
    km.keymap_items.remove(km.keymap_items["object.edit_linked"])
    km.keymap_items.remove(km.keymap_items["wm.return_to_original"])


if __name__ == "__main__":
    register()
