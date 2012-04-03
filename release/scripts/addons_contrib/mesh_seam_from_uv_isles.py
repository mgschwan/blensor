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
    "name": "Seam from uv isles",
    "author": "Fredrik Hansson",
    "version": (1,1),
    "blender": (2, 5, 7),
    "location": "UV/Image editor> UVs > Seam from UV isles",
    "description": "Marks seams based on UV isles",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": 'http://wiki.blender.org/index.php/Extensions:2.5/Py/' \
        'Scripts/Modeling/Seams_from_uv_isles',
    "tracker_url": "https://projects.blender.org/tracker/index.php?" \
        "func=detail&aid=22929",
    "category": "Mesh"}

import bpy

def main(context):
    obj = context.active_object
    mesh = obj.data

    if not obj or obj.type != 'MESH':
        print("no active Mesh")
        return
    if not mesh.uv_textures.active:
        print("no active UV Texture")
        return
    bpy.ops.object.mode_set(mode='OBJECT')


    uvtex=mesh.uv_textures.active.data

    wrap_q = [1,2,3,0]
    wrap_t = [1,2,0]
    edge_uvs = {}

    for i,uvface in enumerate(uvtex):
        f=mesh.faces[i]
        f_uv = [(round(uv[0], 6), round(uv[1], 6)) for uv in uvface.uv]
        f_vi = [vertices for vertices in f.vertices]
        for i, key in enumerate(f.edge_keys):
            if len(f.vertices)==3:
                uv1, uv2 = f_uv[i], f_uv[wrap_t[i]]
                vi1, vi2 = f_vi[i], f_vi[wrap_t[i]]
            else: # quad
                uv1, uv2 = f_uv[i], f_uv[wrap_q[i]]
                vi1, vi2 = f_vi[i], f_vi[wrap_q[i]]

            if vi1 > vi2: vi1,uv1,uv2 = vi2,uv2,uv1

            edge_uvs.setdefault(key, []).append((uv1, uv2))

    for ed in mesh.edges:
            if(len(set(edge_uvs[ed.key])) > 1):
                ed.use_seam=1

    bpy.ops.object.mode_set(mode='EDIT')

class UvIsleSeamsOperator(bpy.types.Operator):
    ''''''
    bl_idname = "mesh.seam_from_uv_isles"
    bl_label = "Seams from UV isles"
    bl_options = {'REGISTER', 'UNDO'}

#  def poll(self, context):
#      obj = context.active_object
#       return (obj and obj.type == 'MESH')

    def execute(self, context):
        main(context)
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(UvIsleSeamsOperator.bl_idname)

def register():
    bpy.utils.register_module(__name__)

    bpy.types.IMAGE_MT_uvs.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.IMAGE_MT_uvs.remove(menu_func)

if __name__ == "__main__":
    register()
