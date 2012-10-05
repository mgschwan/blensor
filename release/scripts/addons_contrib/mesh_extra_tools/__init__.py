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
# Contributed to by
# meta-androcto #

bl_info = {
    "name": "Extra Tools",
    "author": "various",
    "version": (0, 1),
    "blender": (2, 6, 4),
    "location": "View3D > Toolbar and View3D > Specials (W-key)",
    "description": "Add extra mesh edit tools",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"\
        "Scripts",
    "tracker_url": "https://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=32711",
    "category": "Mesh"}


if "bpy" in locals():
    import imp
    imp.reload(mesh_bump)
    imp.reload(face_inset_fillet)
    imp.reload(mesh_bevel_witold)
    imp.reload(mesh_filletplus)
    imp.reload(mesh_normal_smooth)
    imp.reload(mesh_polyredux)
    imp.reload(mesh_vertex_chamfer)
    imp.reload(mesh_mextrude_plus)
    imp.reload(mesh_bevel_round)

else:
    from . import mesh_bump
    from . import face_inset_fillet
    from . import mesh_bevel_witold
    from . import mesh_filletplus
    from . import mesh_normal_smooth
    from . import mesh_polyredux
    from . import mesh_vertex_chamfer
    from . import mesh_mextrude_plus
    from . import mesh_bevel_round

import bpy


class VIEW3D_MT_edit_mesh_extras(bpy.types.Menu):
    # Define the "Extras" menu
    bl_idname = "VIEW3D_MT_edit_mesh_extras"
    bl_label = "Extra Tools"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("mesh.bump",
            text="Inset Extrude Bump")
        layout.operator("fif.op0_id",
            text="Face Inset Fillet")
        layout.operator("mesh.mbevel",
            text="Edge Bevel")
        layout.operator("f.op0_id",
            text="Edge Fillet Plus")
        layout.operator("normal.smooth",
            text="Normal Smooth")
        layout.operator("object.mextrude",
            text="Multi Extrude")
        layout.operator("mesh.polyredux",
            text="Poly Redux")
        layout.operator("mesh.vertex_chamfer",
            text="Vertex Chamfer")
        layout.operator("mesh.bevel_round",
            text="Bevel Round")


class ExtrasPanel(bpy.types.Panel):
    bl_label = 'Mesh Extra Tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        row = layout.split(0.80)
        row.operator('mesh.bump', text = 'Inset Bump')
        row.operator('help.bump', text = '?')
        row = layout.split(0.80)
        row.operator('fif.op0_id', text = 'Face Inset Fillet')
        row.operator('help.face_inset', text = '?')
        row = layout.split(0.80)
        row.operator('mesh.bevel_round', text = 'Bevel Round')
        row.operator('help.bevelround', text = '?')
        row = layout.split(0.80)
        row.operator('mesh.mbevel', text = 'Edge Bevel')
        row.operator('help.edge_bevel', text = '?')
        row = layout.split(0.80)
        row.operator('f.op0_id', text = 'Edge Fillet plus')
        row.operator('f.op1_id', text = '?')
        row = layout.split(0.80)
        row.operator('normal.smooth', text = 'Normal Smooth')
        row.operator('help.normal_smooth', text = '?')
        row = layout.split(0.80)
        row.operator('mesh.polyredux', text = 'Poly Redux')
        row.operator('help.polyredux', text = '?')
        row = layout.split(0.80)
        row.operator('mesh.vertex_chamfer', text = 'Vertex Chamfer')
        row.operator('help.vertexchamfer', text = '?')
        row = layout.split(0.80)
        row.operator('object.mextrude', text = 'Multi Face Extrude')
        row.operator('help.mextrude', text = '?')


# Multi Extrude Panel

class ExtrudePanel(bpy.types.Panel):
    bl_label = 'Multi Extrude Plus'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        prop = layout.operator("wm.context_set_value", text="Face Select",
            icon='FACESEL')
        prop.value = "(False, False, True)"
        prop.data_path = "tool_settings.mesh_select_mode"
        layout.operator('object.mextrude')
        layout.operator('mesh.bump')
        layout.operator('object.mesh2bones')
# Define "Extras" menu
def menu_func(self, context):
    self.layout.menu("VIEW3D_MT_edit_mesh_extras", icon="PLUGIN")


def register():
    bpy.utils.register_module(__name__)

    # Add "Extras" menu to the "Add Mesh" menu
    bpy.types.VIEW3D_MT_edit_mesh_specials.prepend(menu_func)


def unregister():
    bpy.utils.unregister_module(__name__)

    # Remove "Extras" menu from the "Add Mesh" menu.
    bpy.types.VIEW3D_MT_edit_mesh_specials.remove(menu_func)

if __name__ == "__main__":
    register()
