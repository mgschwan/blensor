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

#
#
#  Authors           : Clemens Barth (Blendphys@root-1.de), ...
#
#  Homepage(Wiki)    : http://development.root-1.de/Atomic_Blender.php
#
#  Start of project              : 2011-12-01 by Clemens Barth
#  First publication in Blender  : 2012-11-03
#  Last modified                 : 2012-11-09
#
#  Acknowledgements 
#  ================
#
#  Blender: ideasman, meta_androcto, truman, kilon, CoDEmanX, dairin0d, PKHG, 
#           Valter, ...
#  Other: Frank Palmino
#

bl_info = {
    "name": "Atomic Blender - Utilities",
    "description": "Utilities for manipulating atom structures",
    "author": "Clemens Barth",
    "version": (0,6),
    "blender": (2,6),
    "location": "Panel: View 3D - Tools",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/"
                "Py/Scripts/Import-Export/PDB",
    "tracker_url": "http://projects.blender.org/tracker/"
                   "index.php?func=detail&aid=33071&group_id=153&atid=467",
    "category": "Import-Export"
}

import bpy
from bpy.types import Operator, Panel
from bpy.props import (StringProperty,
                       EnumProperty,
                       FloatProperty)

from . import io_atomblend_utilities

# -----------------------------------------------------------------------------
#                                                                           GUI

# This is the panel, which can be used to prepare the scene.
# It is loaded after the file has been chosen via the menu 'File -> Import'
class PreparePanel(Panel):
    bl_label       = "Atomic Blender Utilities"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOL_PROPS"

    def draw(self, context):
        layout = self.layout
        scn    = context.scene.atom_blend[0]

        row = layout.row()
        row.label(text="Custom data file")
        box = layout.box()
        row = box.row()
        row.label(text="Custom data file")
        row = box.row()
        col = row.column()
        col.prop(scn, "datafile")
        col.operator("atom_blend.datafile_apply")
        row = box.row()
        row.operator("atom_blend.button_distance")
        row.prop(scn, "distance")
        row = layout.row()
        row.label(text="Choice of atom radii")
        box = layout.box()
        row = box.row()
        row.label(text="All changes concern:")
        row = box.row()
        row.prop(scn, "radius_how")
        row = box.row()
        row.label(text="1. Change type of radii")
        row = box.row()
        row.prop(scn, "radius_type")
        row = box.row()
        row.label(text="2. Change atom radii in pm")
        row = box.row()
        row.prop(scn, "radius_pm_name")
        row = box.row()
        row.prop(scn, "radius_pm")
        row = box.row()
        row.label(text="3. Change atom radii by scale")
        row = box.row()
        col = row.column()
        col.prop(scn, "radius_all")
        col = row.column(align=True)
        col.operator( "atom_blend.radius_all_bigger" )
        col.operator( "atom_blend.radius_all_smaller" )

        layout.separator()
        row = box.row()
        row.active = (bpy.context.mode == 'EDIT_MESH')
        row.operator( "atom_blend.separate_atom" )


class PanelProperties(bpy.types.PropertyGroup):

    def Callback_radius_type(self, context):
        scn = bpy.context.scene.atom_blend[0]
        io_atomblend_utilities.choose_objects("radius_type", 
                                              scn.radius_how, 
                                              None,
                                              None,
                                              scn.radius_type) 
    def Callback_radius_pm(self, context):
        scn = bpy.context.scene.atom_blend[0]
        io_atomblend_utilities.choose_objects("radius_pm", 
                                              scn.radius_how, 
                                              None,
                                              [scn.radius_pm_name,
                                              scn.radius_pm],
                                              None) 
        
    datafile = StringProperty(
        name = "", description="Path to your custom data file",
        maxlen = 256, default = "", subtype='FILE_PATH')
    XYZ_file = StringProperty(
        name = "Path to file", default="",
        description = "Path of the XYZ file")
    number_atoms = StringProperty(name="",
        default="Number", description = "This output shows "
        "the number of atoms which have been loaded")
    distance = StringProperty(
        name="", default="Distance (A)",
        description="Distance of 2 objects in Angstrom")
    radius_how = EnumProperty(
        name="",
        description="Which objects shall be modified?",
        items=(('ALL_ACTIVE',"all active objects", "in the current layer"),
               ('ALL_IN_LAYER',"all"," in active layer(s)")),
               default='ALL_ACTIVE',)
    radius_type = EnumProperty(
        name="Type",
        description="Which type of atom radii?",
        items=(('0',"predefined", "Use pre-defined radii"),
               ('1',"atomic", "Use atomic radii"),
               ('2',"van der Waals","Use van der Waals radii")),
               default='0',update=Callback_radius_type)
    radius_pm_name = StringProperty(
        name="", default="Atom name",
        description="Put in the name of the atom (e.g. Hydrogen)")
    radius_pm = FloatProperty(
        name="", default=100.0, min=0.0,
        description="Put in the radius of the atom (in pm)",
        update=Callback_radius_pm)
    radius_all = FloatProperty(
        name="Scale", default = 1.05, min=1.0, max=5.0,
        description="Put in the scale factor")



# Button loading a custom data file
class DatafileApply(Operator):
    bl_idname = "atom_blend.datafile_apply"
    bl_label = "Apply"
    bl_description = "Use color and radii values stored in the custom file"

    def execute(self, context):
        scn = bpy.context.scene.atom_blend[0]

        if scn.datafile == "":
            return {'FINISHED'}

        io_atomblend_utilities.custom_datafile(scn.datafile)
        io_atomblend_utilities.custom_datafile_change_atom_props()

        return {'FINISHED'}


# Button for separating a single atom from a structure
class SeparateAtom(Operator):
    bl_idname = "atom_blend.separate_atom"
    bl_label = "Separate atoms"
    bl_description = ("Separate atoms you have selected. "
                      "You have to be in the 'Edit Mode'")

    def execute(self, context):
        scn = bpy.context.scene.atom_blend[0]

        io_atomblend_utilities.separate_atoms(scn)

        return {'FINISHED'}


# Button for measuring the distance of the active objects
class DistanceButton(Operator):
    bl_idname = "atom_blend.button_distance"
    bl_label = "Measure ..."
    bl_description = "Measure the distance between two objects"

    def execute(self, context):
        scn  = bpy.context.scene.atom_blend[0]
        dist = io_atomblend_utilities.distance()

        # Put the distance into the string of the output field.
        scn.distance = dist
        return {'FINISHED'}


# Button for increasing the radii of all atoms
class RadiusAllBiggerButton(Operator):
    bl_idname = "atom_blend.radius_all_bigger"
    bl_label = "Bigger ..."
    bl_description = "Increase the radii of the atoms"

    def execute(self, context):
        scn = bpy.context.scene.atom_blend[0]     
        io_atomblend_utilities.choose_objects("radius_all", 
                                              scn.radius_how, 
                                              scn.radius_all, 
                                              None,
                                              None)        
        return {'FINISHED'}


# Button for decreasing the radii of all atoms
class RadiusAllSmallerButton(Operator):
    bl_idname = "atom_blend.radius_all_smaller"
    bl_label = "Smaller ..."
    bl_description = "Decrease the radii of the atoms"

    def execute(self, context):
        scn = bpy.context.scene.atom_blend[0]
        io_atomblend_utilities.choose_objects("radius_all", 
                                              scn.radius_how, 
                                              1.0/scn.radius_all, 
                                              None,
                                              None)                                     
        return {'FINISHED'}


def register():
    io_atomblend_utilities.read_elements()  
    bpy.utils.register_module(__name__)
    bpy.types.Scene.atom_blend = bpy.props.CollectionProperty(type=
                                                   PanelProperties)
    bpy.context.scene.atom_blend.add()

def unregister():
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":

    register()
