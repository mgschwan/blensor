# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
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

# <pep8-80 compliant>

# This script was developed with financial support from the Foundation for
# Science and Technology of Portugal, under the grant SFRH/BD/66452/2009.


bl_info = {
    'name': "Carnegie Mellon University Mocap Library Browser",
    'author': "Daniel Monteiro Basso <daniel@basso.inf.br>",
    'version': (2012, 6, 1, 1),
    'blender': (2, 6, 3),
    'location': "View3D > Tools",
    'description': "Assistant for using CMU Motion Capture data",
    'warning': '',
    'wiki_url': "http://wiki.blender.org/index.php/Extensions:2.6/Py/"\
                "Scripts/3D_interaction/CMU_Mocap_Library_Browser",
    'tracker_url': "http://projects.blender.org/tracker/index.php?"\
                   "func=detail&aid=29086",
    'category': '3D View'}


import os
import bpy
import bgl
import blf
import math
from . import library


def initialize_subjects():
    """
        Initializes the main object and the subjects (actors) list
    """
    while bpy.data.scenes[0].cmu_mocap_lib.subject_list:
        bpy.data.scenes[0].cmu_mocap_lib.subject_list.remove(0)
    for k, v in library.subjects.items():
        n = bpy.data.scenes[0].cmu_mocap_lib.subject_list.add()
        n.name = "{:d} - {}".format(k, v['desc'])
        n.idx = k


def update_motions(self, context):
    """
        Updates the motions list after a subject is selected
    """
    sidx = -1
    if self.subject_active != -1:
        sidx = self.subject_list[self.subject_active].idx
    while self.motion_list:
        self.motion_list.remove(0)
    if sidx != -1:
        for k, v in library.subjects[sidx]["motions"].items():
            n = self.motion_list.add()
            n.name = "{:d} - {}".format(k, v["desc"])
            n.idx = k
        self.motion_active = -1


class ListItem(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty()
    idx = bpy.props.IntProperty()


class CMUMocapLib(bpy.types.PropertyGroup):
    local_storage = bpy.props.StringProperty(
        name="Local Storage",
        subtype='DIR_PATH',
        description="Location to store downloaded resources",
        default="~/cmu_mocap_lib")
    follow_structure = bpy.props.BoolProperty(
        name="Follow Library Folder Structure",
        description="Store resources in subfolders of the local storage",
        default=True)
    automatically_import = bpy.props.BoolProperty(
        name="Automatically Import after Download",
        description="Import the resource after the download is finished",
        default=True)
    subject_list = bpy.props.CollectionProperty(
        name="subjects", type=ListItem)
    subject_active = bpy.props.IntProperty(
        name="subject_idx", default=-1, update=update_motions)
    subject_import_name = bpy.props.StringProperty(
        name="Armature Name",
        description="Identifier of the imported subject's armature",
        default="Skeleton")
    motion_list = bpy.props.CollectionProperty(name="motions", type=ListItem)
    motion_active = bpy.props.IntProperty(name="motion_idx", default=-1)
    frame_skip = bpy.props.IntProperty(name="Fps Divisor", default=4,
    # usually the sample rate is 120, so the default 4 gives you 30fps
                          description="Frame supersampling factor", min=1)
    cloud_scale = bpy.props.FloatProperty(name="Marker Cloud Scale",
                          description="Scale the marker cloud by this value",
                          default=1., min=0.0001, max=1000000.0,
                          soft_min=0.001, soft_max=100.0)


def draw_callback(self, context):
    mid = int(360 * self.recv / self.fsize)
    cx = 200
    cy = 30
    blf.position(0, 230, 23, 0)
    blf.size(0, 20, 72)
    blf.draw(0, "{0:2d}% of {1}".format(
        100 * self.recv // self.fsize, self.hfsize))

    bgl.glEnable(bgl.GL_BLEND)
    bgl.glColor4f(.7, .7, .7, 0.8)
    bgl.glBegin(bgl.GL_TRIANGLE_FAN)
    bgl.glVertex2i(cx, cy)
    for i in range(mid):
        x = cx + 20 * math.sin(math.radians(float(i)))
        y = cy + 20 * math.cos(math.radians(float(i)))
        bgl.glVertex2f(x, y)
    bgl.glEnd()

    bgl.glColor4f(.0, .0, .0, 0.6)
    bgl.glBegin(bgl.GL_TRIANGLE_FAN)
    bgl.glVertex2i(cx, cy)
    for i in range(mid, 360):
        x = cx + 20 * math.sin(math.radians(float(i)))
        y = cy + 20 * math.cos(math.radians(float(i)))
        bgl.glVertex2f(x, y)
    bgl.glEnd()

    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)


class CMUMocapDownloadImport(bpy.types.Operator):
    bl_idname = "mocap.download_import"
    bl_label = "Download and Import a file"

    remote_file = bpy.props.StringProperty(
        name="Remote File",
        description="Location from where to download the file data")
    local_file = bpy.props.StringProperty(
        name="Local File",
        description="Destination where to save the file data")
    do_import = bpy.props.BoolProperty(
        name="Manual Import",
        description="Import the resource non-automatically",
        default=False)

    timer = None
    fout = None
    src = None
    fsize = 0
    recv = 0
    cloud_scale = 1

    def modal(self, context, event):
        context.area.tag_redraw()
        if event.type == 'ESC':
            self.fout.close()
            os.unlink(self.local_file)
            return self.cancel(context)
        if event.type == 'TIMER':
            to_read = min(self.fsize - self.recv, 100 * 2 ** 10)
            data = self.src.read(to_read)
            self.fout.write(data)
            self.recv += to_read
            if self.fsize == self.recv:
                self.fout.close()
                return self.cancel(context)
        return {'PASS_THROUGH'}

    def cancel(self, context):
        context.window_manager.event_timer_remove(self.timer)
        context.region.callback_remove(self.handle)
        if os.path.exists(self.local_file):
            self.import_or_open()
        return {'CANCELLED'}

    def execute(self, context):
        cml = bpy.data.scenes[0].cmu_mocap_lib
        if not os.path.exists(self.local_file):
            try:
                os.makedirs(os.path.split(self.local_file)[0])
            except:
                pass
            from urllib.request import urlopen
            self.src = urlopen(self.remote_file)
            info = self.src.info()
            self.fsize = int(info["Content-Length"])
            m = int(math.log10(self.fsize) // 3)
            self.hfsize = "{:.1f}{}".format(
                self.fsize * math.pow(10, -m * 3),
                ['b', 'Kb', 'Mb', 'Gb', 'Tb', 'Eb', 'Pb'][m])  # :-p
            self.fout = open(self.local_file, 'wb')
            self.recv = 0
            self.handle = context.region.\
                callback_add(draw_callback, (self, context), 'POST_PIXEL')
            self.timer = context.window_manager.\
                event_timer_add(0.001, context.window)
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.import_or_open()
        return {'FINISHED'}

    def import_or_open(self):
        cml = bpy.data.scenes[0].cmu_mocap_lib
        if cml.automatically_import or self.do_import:
            if self.local_file.endswith("mpg"):
                bpy.ops.wm.path_open(filepath=self.local_file)
            elif self.local_file.endswith("asf"):
                try:
                    bpy.ops.import_anim.asf(
                        filepath=self.local_file,
                        from_inches=True,
                        use_rot_x=True, use_rot_z=True,
                        armature_name=cml.subject_import_name)
                except AttributeError:
                    self.report({'ERROR'}, "To use this feature "
                        "please enable the Acclaim ASF/AMC Importer addon.")
            elif self.local_file.endswith("amc"):
                ob = bpy.context.active_object
                if not ob or ob.type != 'ARMATURE' or \
                    'source_file_path' not in ob:
                    self.report({'ERROR'}, "Please select a CMU Armature.")
                    return
                try:
                    bpy.ops.import_anim.amc(
                        filepath=self.local_file,
                        frame_skip=cml.frame_skip)
                except AttributeError:
                    self.report({'ERROR'}, "To use this feature please "
                        "enable the Acclaim ASF/AMC Importer addon.")
            elif self.local_file.endswith("c3d"):
                try:
                    bpy.ops.import_anim.c3d(
                        filepath=self.local_file,
                        from_inches=False,
                        auto_scale=True,
                        scale=cml.cloud_scale,
                        show_names=False,
                        frame_skip=cml.frame_skip)
                except AttributeError:
                    self.report({'ERROR'}, "To use this feature "
                        "please enable the C3D Importer addon.")



class CMUMocapConfig(bpy.types.Panel):
    bl_idname = "object.cmu_mocap_config"
    bl_label = "CMU Mocap Browser Configuration"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        if not bpy:
            return
        cml = bpy.data.scenes[0].cmu_mocap_lib
        layout = self.layout
        layout.operator("wm.url_open",
            text="Carnegie Mellon University Mocap Library",
            icon='URL').url = 'http://mocap.cs.cmu.edu/'
        layout.prop(cml, "local_storage")
        layout.prop(cml, "follow_structure")
        layout.prop(cml, "automatically_import")


class CMUMocapSubjectBrowser(bpy.types.Panel):
    bl_idname = "object.cmu_mocap_subject_browser"
    bl_label = "CMU Mocap Subject Browser"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        if not bpy:
            return
        layout = self.layout
        cml = bpy.data.scenes[0].cmu_mocap_lib
        # spare space... layout.label("Subjects")
        layout.template_list(cml, "subject_list", cml, "subject_active")
        layout.prop(cml, "subject_import_name")
        if cml.subject_active != -1:
            sidx = cml.subject_list[cml.subject_active].idx
            remote_fname = library.skeleton_url.format(sidx)
            tid = "{0:02d}".format(sidx)
            local_path = os.path.expanduser(cml.local_storage)
            if cml.follow_structure:
                local_path = os.path.join(local_path, tid)
            local_fname = os.path.join(local_path, tid + ".asf")
            do_import = False
            if os.path.exists(local_fname):
                label = "Import Selected"
                do_import = True
            elif cml.automatically_import:
                label = "Download and Import Selected"
            else:
                label = "Download Selected"

            props = layout.operator("mocap.download_import",
                                    text=label, icon='ARMATURE_DATA')
            props.remote_file = remote_fname
            props.local_file = local_fname
            props.do_import = do_import


class CMUMocapMotionBrowser(bpy.types.Panel):
    bl_idname = "object.cmu_mocap_motion_browser"
    bl_label = "CMU Mocap Motion Browser"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        if not bpy:
            return
        layout = self.layout
        cml = bpy.data.scenes[0].cmu_mocap_lib
        # spare space... layout.label("Motions for selected subject")
        layout.template_list(cml, "motion_list", cml, "motion_active")
        if cml.motion_active == -1:
            return
        sidx = cml.subject_list[cml.subject_active].idx
        midx = cml.motion_list[cml.motion_active].idx
        motion = library.subjects[sidx]['motions'][midx]
        fps = motion['fps']
        ifps = fps // cml.frame_skip
        # layout.label("Original capture frame rate: {0:d} fps.".format(fps))
        # layout.label("Importing frame rate: {0:d} fps.".format(ifps))
        row = layout.row()
        row.column().label("Original: {0:d} fps.".format(fps))
        row.column().label("Importing: {0:d} fps.".format(ifps))
        layout.prop(cml, "frame_skip")
        layout.prop(cml, "cloud_scale")
        remote_fname = library.motion_url.format(sidx, midx)
        tid = "{0:02d}".format(sidx)
        local_path = os.path.expanduser(cml.local_storage)
        if cml.follow_structure:
            local_path = os.path.join(local_path, tid)
        for target, icon, ext in (
                ('Motion Data', 'POSE_DATA', 'amc'),
                ('Marker Cloud', 'EMPTY_DATA', 'c3d'),
                ('Movie', 'FILE_MOVIE', 'mpg')):
            action = "Import" if ext != 'mpg' else "Open"
            fname = "{0:02d}_{1:02d}.{2}".format(sidx, midx, ext)
            local_fname = os.path.join(local_path, fname)
            do_import = False
            if os.path.exists(local_fname):
                label = "{0} {1}".format(action, target)
                do_import = True
            elif cml.automatically_import:
                label = "Download and {0} {1}".format(action, target)
            else:
                label = "Download {0}".format(target)
            row = layout.row()
            props = row.operator("mocap.download_import", text=label, icon=icon)
            props.remote_file = remote_fname + ext
            props.local_file = local_fname
            props.do_import = do_import
            row.active = ext in motion['files']


def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.cmu_mocap_lib = bpy.props.PointerProperty(type=CMUMocapLib)
    initialize_subjects()


def unregister():
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
