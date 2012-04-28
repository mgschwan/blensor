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

################################################################################
# Repeats extrusion + rotation + scale for one or more faces                   #

################################################################################

bl_info = {
    "name": "MExtrude",
    "author": "liero",
    "version": (1, 2, 8),
    "blender": (2, 6, 2),
    "location": "View3D > Tool Shelf",
    "description": "Repeat extrusions from faces to create organic shapes",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts",
    "tracker_url": "http://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=28570",
    "category": "Mesh"}

import bpy, random
from random import gauss
from math import radians
from mathutils import Euler
from bpy.props import FloatProperty, IntProperty

def vloc(self, r):
    random.seed(self.ran + r)
    return self.off * (1 + random.gauss(0, self.var1 / 3))

def vrot(self,r):
    random.seed(self.ran+r)
    return Euler((radians(self.rotx) + random.gauss(0, self.var2 / 3), \
        radians(self.roty) + random.gauss(0, self.var2 / 3), \
        radians(self.rotz) + random.gauss(0,self.var2 / 3)), 'XYZ')

def vsca(self, r):
    random.seed(self.ran + r)
    return [self.sca * (1 + random.gauss(0, self.var3 / 3))] * 3

class MExtrude(bpy.types.Operator):
    bl_idname = 'object.mextrude'
    bl_label = 'MExtrude'
    bl_description = 'Multi Extrude'
    bl_options = {'REGISTER', 'UNDO'}

    off = FloatProperty(name='Offset', min=-2, soft_min=0.001, \
        soft_max=2, max=5, default=.5, description='Translation')
    rotx = FloatProperty(name='Rot X', min=-85, soft_min=-30, \
        soft_max=30, max=85, default=0, description='X rotation')
    roty = FloatProperty(name='Rot Y', min=-85, soft_min=-30, \
        soft_max=30, max=85, default=0, description='Y rotation')
    rotz = FloatProperty(name='Rot Z', min=-85, soft_min=-30, \
        soft_max=30, max=85, default=-0, description='Z rotation')
    sca = FloatProperty(name='Scale', min=0.1, soft_min=0.5, \
        soft_max=1.2, max =2, default=.9, description='Scaling')
    var1 = FloatProperty(name='Offset Var', min=-5, soft_min=-1, \
        soft_max=1, max=5, default=0, description='Offset variation')
    var2 = FloatProperty(name='Rotation Var', min=-5, soft_min=-1, \
        soft_max=1, max=5, default=0, description='Rotation variation')
    var3 = FloatProperty(name='Scale Noise', min=-5, soft_min=-1, \
        soft_max=1, max=5, default=0, description='Scaling noise')
    num = IntProperty(name='Repeat', min=1, max=50, soft_max=100, \
        default=5, description='Repetitions')
    ran = IntProperty(name='Seed', min=-9999, max=9999, default=0, \
        description='Seed to feed random values')

    @classmethod
    def poll(cls, context):
        return (context.object and context.object.type == 'MESH')

    def draw(self, context):
        layout = self.layout
        column = layout.column(align=True)
        column.label(text='Transformations:')
        column.prop(self, 'off', slider=True)
        column.prop(self, 'rotx', slider=True)
        column.prop(self, 'roty', slider=True)
        column.prop(self, 'rotz', slider=True)
        column.prop(self, 'sca', slider=True)
        column = layout.column(align=True)
        column.label(text='Variation settings:')
        column.prop(self, 'var1', slider=True)
        column.prop(self, 'var2', slider=True)
        column.prop(self, 'var3', slider=True)
        column.prop(self, 'ran')
        column = layout.column(align=False)
        column.prop(self, 'num')

    def execute(self, context):
        obj = bpy.context.object
        data, om, msv =  obj.data, obj.mode, []
        msm = bpy.context.tool_settings.mesh_select_mode
        bpy.context.tool_settings.mesh_select_mode = [False, False, True]

        # disable modifiers
        for i in range(len(obj.modifiers)):
            msv.append(obj.modifiers[i].show_viewport)
            obj.modifiers[i].show_viewport = False

        # isolate selection
        bpy.ops.object.mode_set()
        bpy.ops.object.mode_set(mode='EDIT')
        total = data.total_face_sel
        try: bpy.ops.mesh.select_inverse()
        except: bpy.ops.mesh.select_all(action='INVERT')
        bpy.ops.object.vertex_group_assign(new=True)
        bpy.ops.mesh.hide()

        # faces loop
        for i in range(total):
            bpy.ops.object.editmode_toggle()
            # is bmesh..?
            try:
                faces = data.polygons
            except:
                faces = data.faces
            for f in faces:
                if not f.hide:
                    f.select = True
                    break
            norm = f.normal.copy()
            rot, loc = vrot(self, i), vloc(self, i)
            norm.rotate(obj.matrix_world.to_quaternion())
            bpy.ops.object.editmode_toggle()

            # extrude loop
            for a in range(self.num):
                norm.rotate(rot)
                r2q = rot.to_quaternion()
                bpy.ops.mesh.extrude_faces_move()
                bpy.ops.transform.translate(value = norm * loc)
                bpy.ops.transform.rotate(value = [r2q.angle], axis = r2q.axis)
                bpy.ops.transform.resize(value = vsca(self, i + a))
            bpy.ops.object.vertex_group_remove_from()
            bpy.ops.mesh.hide()

        # keep just last faces selected
        bpy.ops.mesh.reveal()
        bpy.ops.object.vertex_group_deselect()
        bpy.ops.object.vertex_group_remove()
        bpy.ops.object.mode_set()


        # restore user settings
        for i in range(len(obj.modifiers)): 
            obj.modifiers[i].show_viewport = msv[i]
        bpy.context.tool_settings.mesh_select_mode = msm
        bpy.ops.object.mode_set(mode=om)
        if not total:
            self.report({'INFO'}, 'Select one or more faces...')
        return{'FINISHED'}

class BotonME(bpy.types.Panel):
    bl_label = 'Multi Extrude'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    def draw(self, context):
        layout = self.layout
        layout.operator('object.mextrude')

def register():
    bpy.utils.register_class(MExtrude)
    bpy.utils.register_class(BotonME)

def unregister():
    bpy.utils.unregister_class(MExtrude)
    bpy.utils.unregister_class(BotonME)

if __name__ == '__main__':
    register()
