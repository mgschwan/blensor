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
#  Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>


bl_info = {
    "name": "Grease Pencil Retopology",
    "author": "Campbell Barton, Bart Crouch",
    "version": (1, 0, 0),
    "blender": (2, 57, 0),
    "location": "View3D > Properties > Grease Pencil",
    "warning": "",
    "description": "Use Grease Pencil to retopologise a mesh.",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Mesh"}


import bpy


# retopo operator
class Retopo(bpy.types.Operator):
    bl_idname = "mesh.gp_retopo"
    bl_label = "Retopo"
    bl_description = "Convert Grease Pencil drawings to a mesh"
    bl_options = {'REGISTER', 'UNDO'}

    precision = bpy.props.IntProperty(name="Precision",
        description="Lower values result in more removed doubles and "
                    "smoother less precise results",
        default=40,
        min=2,
        soft_max=100)

    @classmethod
    def poll(cls, context):
        return context.object

    def execute(self, context):
        from . import retopo
        scene, gp = retopo.initialise(context)
        if not gp:
            self.report({'WARNING'}, "No grease pencil data found")
            return {'CANCELLED'}

        obj_new = retopo.calculate(gp, self.precision)

        bpy.ops.object.select_all(action='DESELECT')
        scene.objects.active = obj_new
        obj_new.select = True

        # nasty, recalc normals
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        return {'FINISHED'}


# draw function for integration in panels
def panel_func(self, context):
    self.layout.operator("mesh.gp_retopo")


# define classes and panels for registration
classes = [Retopo]
panels = [bpy.types.VIEW3D_PT_tools_objectmode,
    bpy.types.VIEW3D_PT_tools_meshedit,
    bpy.types.VIEW3D_PT_tools_curveedit,
    bpy.types.VIEW3D_PT_tools_surfaceedit,
    bpy.types.VIEW3D_PT_tools_armatureedit,
    bpy.types.VIEW3D_PT_tools_mballedit,
    bpy.types.VIEW3D_PT_tools_latticeedit,
    bpy.types.VIEW3D_PT_tools_posemode]


# registering and menu integration
def register():
    for c in classes:
        bpy.utils.register_class(c)
    for panel in panels:
        panel.append(panel_func)


# unregistering and removing menus
def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    for panel in panels:
        panel.remove(panel_func)


if __name__ == "__main__":
    register()
