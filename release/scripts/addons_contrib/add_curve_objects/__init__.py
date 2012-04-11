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
    "name": "Curve Objects",
    "author": "Multiple Authors",
    "version": (0, 1),
    "blender": (2, 6, 3),
    "location": "View3D > Add > Curve > Curve Objects",
    "description": "Add extra curve object types",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Add Curve"}


if "bpy" in locals():
    import imp
    imp.reload(add_curve_rectangle_259)
    imp.reload(add_curve_spirals)
    imp.reload(cotejrp1_particle_tracer)
    imp.reload(cotejrp1_string_it)
    imp.reload(curve_simplify)
	
else:
    from . import add_curve_rectangle_259
    from . import add_curve_spirals
    from . import cotejrp1_particle_tracer
    from . import cotejrp1_string_it
    from . import curve_simplify

import bpy


class INFO_MT_curve_extras_add(bpy.types.Menu):
    # Define the "Extras" menu
    bl_idname = "INFO_MT_curve_extra_objects_add"
    bl_label = "Curve Objects"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("curve.rectangle",
            text="Rectangle")
        layout.operator("curve.spirals",
            text="Spirals")
        layout.operator("curve.particle_tracer",
            text="Particle Tracer")
        layout.operator("curve.string_it_operator",
            text="String It")
        layout.operator("curve.simplify",
            text="Curve Simplify")

# Register all operators and panels

# Define "Extras" menu
def menu_func(self, context):
    self.layout.menu("INFO_MT_curve_extra_objects_add", icon="PLUGIN")


def register():
    bpy.utils.register_module(__name__)

    # Add "Extras" menu to the "Add Mesh" menu
    bpy.types.INFO_MT_curve_add.append(menu_func)


def unregister():
    bpy.utils.unregister_module(__name__)

    # Remove "Extras" menu from the "Add Mesh" menu.
    bpy.types.INFO_MT_curve_add.remove(menu_func)

if __name__ == "__main__":
    register()
