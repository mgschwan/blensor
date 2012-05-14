# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation, either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#  All rights reserved.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

bl_info = {
    "name": "DirectX X Format",
    "author": "Chris Foster",
    "version": (3, 0, 0),
    "blender": (2, 6, 3),
    "location": "File > Export > DirectX (.x)",
    "description": "Export mesh vertices, UV's, materials, textures, "\
        "vertex colors, armatures, empties, and actions.",
    "warning": "This script is a WIP!",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"\
        "Scripts/Import-Export/DirectX_Exporter",
    "tracker_url": "https://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=22795",
    "category": "Import-Export"}

import bpy
from bpy.props import BoolProperty
from bpy.props import EnumProperty
from bpy.props import StringProperty


class ExportDirectX(bpy.types.Operator):
    '''Export selection to DirectX'''

    bl_idname = "export_scene.x"
    bl_label = "Export DirectX"

    filepath = StringProperty(subtype='FILE_PATH')

    SelectedOnly = BoolProperty(
        name="Export Selected Objects Only",
        description="Export only selected objects",
        default=True)

    ApplyModifiers = BoolProperty(
        name="Apply Modifiers",
        description="Apply object modifiers before export",
        default=False)

    ExportArmatures = BoolProperty(
        name="Export Armatures",
        description="Export the bones armatures",
        default=False)

    ExportTextures = BoolProperty(
        name="Export Textures",
        description="Reference external image files to be used by the model",
        default=True)

    ExportVertexColors = BoolProperty(
        name="Export Vertex Colors",
        description="Export mesh vertex colors, if any",
        default=False)

    IncludeFrameRate = BoolProperty(
        name="Include Frame Rate",
        description="Include the AnimTicksPerSecond template which is "\
            "used by some engines to control animation speed",
        default=False)

    ExportAnimation = EnumProperty(
        name="Animations",
        description="Select the type of animations to export. Only object "\
            "and armature bone animations can be exported. Full Animation "\
            "exports every frame",
        items=(
            ('NONE', "None", ""),
            ('KEYS', "Keyframes Only", ""),
            ('FULL', "Full Animation", "")),
        default='NONE')

    ExportActionsAsSets = BoolProperty(
        name="Export Actions as AnimationSets",
        description="Export each action of each object as a separate "\
            "AnimationSet. Otherwise all current actions are lumped "\
            "together into a single set",
        default=False)

    Verbose = BoolProperty(
        name="Verbose",
        description="Run the exporter in debug mode. Check the console for "\
            "output",
        default=False)

    def execute(self, context):
        self.filepath = bpy.path.ensure_ext(self.filepath, ".x")

        import export_x
        Exporter = export_x.DirectXExporter(self, context)
        Exporter.Export() # XXX CHANGE THIS
        return {'FINISHED'}

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = bpy.path.ensure_ext(bpy.data.filepath, ".x")
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


def menu_func(self, context):
    self.layout.operator(ExportDirectX.bl_idname, text="DirectX (.x)")


def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_file_export.append(menu_func)


def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_file_export.remove(menu_func)


if __name__ == "__main__":
    register()
