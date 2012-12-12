#  ***** BEGIN GPL LICENSE BLOCK *****
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see http://www.gnu.org/licenses/
#  or write to the Free Software Foundation, Inc., 51 Franklin Street,
#  Fifth Floor, Boston, MA 02110-1301, USA.
#
#  The Original Code is Copyright (C) 2012 by Peter Cassetta    ###
#  All rights reserved.
#
#  Contact:                        matlib@peter.cassetta.info   ###
#  Information:  http://peter.cassetta.info/material-library/   ###
#
#  The Original Code is: all of this file.
#
#  Contributor(s): Peter Cassetta.
#
#  ***** END GPL LICENSE BLOCK *****

bl_info = {
    "name": "Online Material Library",
    "author": "Peter Cassetta",
    "version": (0, 5),
    "blender": (2, 6, 3),
    "location": "Properties > Material > Online Material Library",
    "description": "Browse and download materials from online CC0 libraries.",
    "warning": "Beta version",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Material/Online_Material_Library",
    "tracker_url": "http://projects.blender.org/tracker/index.php?func=detail&aid=31802",
    "category": "Material"}

import bpy
from bpy_extras.io_utils import ExportHelper
import os.path
import http.client
import xml.dom.minidom

library = ""
library_data = []
update_data = ["Up-to-date.", ""]

library_enum_items = [("peter.cassetta.info/material-library/release/", "Peter's Library - Release", "Stable library hosted on peter.cassetta.info (Default)"),
                      ("peter.cassetta.info/material-library/testing/", "Peter's Library - Testing", "Continually updated library hosted on peter.cassetta.info (Online only)"),
                      ("bundled", "Bundled Library", "The library bundled with this add-on (Offline only)")]
bpy.types.Scene.mat_lib_library = bpy.props.EnumProperty(name = "Select library:", items = library_enum_items, description = "Choose a library", options = {'SKIP_SAVE'})

working_mode = "none"
mat_lib_host = ""
mat_lib_location = ""
mat_lib_cached_files = -1
if os.path.exists(os.path.join(bpy.context.user_preferences.filepaths.script_directory, "addons", "online_mat_lib", "material-library")):
    mat_lib_folder = os.path.join(bpy.context.user_preferences.filepaths.script_directory, "addons", "online_mat_lib", "material-library")
elif os.path.exists(os.path.join(bpy.utils.script_path_user(), "addons", "online_mat_lib", "material-library")):
    mat_lib_folder = os.path.join(bpy.utils.script_path_user(), "addons", "online_mat_lib", "material-library")
elif os.path.exists(os.path.join(bpy.utils.script_paths()[0], "addons", "online_mat_lib", "material-library")):
    mat_lib_folder = os.path.join(bpy.utils.script_paths()[0], "addons", "online_mat_lib", "material-library")
elif os.path.exists(os.path.join(bpy.utils.script_paths()[0], "addons_contrib", "online_mat_lib", "material-library")):
    mat_lib_folder = os.path.join(bpy.utils.script_paths()[0], "addons_contrib", "online_mat_lib", "material-library")
else:
    print("ONLINE MATERIAL LIBRARY -- MAJOR PROBLEM:"\
    "COULD NOT LOCATE ADD-ON INSTALLATION PATH.")
    mat_lib_folder = "error"

mat_lib_contents = "Please refresh."
mat_lib_category_filenames = []
mat_lib_category_types = []
mat_lib_category_names = []
mat_lib_categories = 0

category_contents = "None"
category_name = ""
category_filename = ""
category_materials = 0

category_type = "none"

sub_category_contents = "None"
sub_category_name = ""
sub_category_filename = ""
sub_category_categories = 0
sub_category_names = []
sub_category_filenames = []

material_names = []
material_filenames = []
material_contributors = []
material_ratings = []
material_fireflies = []
material_speeds = []
material_complexities = []
material_scripts = []
material_images = []

material_file_contents = ""

current_material_number = -1
current_material_cached = False
current_material_previewed = False
material_detail_view = "RENDER"
preview_message = []
node_message = []
save_filename = ""
script_stack = []
osl_scripts = []

bpy.types.Scene.mat_lib_auto_preview = bpy.props.BoolProperty(name = "Auto-download previews", description = "Automatically download material previews in online mode", default = True, options = {'SKIP_SAVE'})
bpy.types.Scene.mat_lib_show_osl_materials = bpy.props.BoolProperty(name = "Show OSL materials", description = "Enable to show materials with OSL shading scripts", default = False, options = {'SKIP_SAVE'})
bpy.types.Scene.mat_lib_show_textured_materials = bpy.props.BoolProperty(name = "Show textured materials", description = "Enable to show materials with image textures", default = True, options = {'SKIP_SAVE'})
bpy.types.Scene.mat_lib_osl_only_trusted = bpy.props.BoolProperty(name = "Use OSL scripts from trusted sources only", description = "Disable to allow downloading OSL scripts from anywhere on the web (Not recommended)", default = True, options = {'SKIP_SAVE'})
bpy.types.Scene.mat_lib_images_only_trusted = bpy.props.BoolProperty(name = "Use image textures from trusted sources only", description = "Disable to allow downloading image textures from anywhere on the web (Not recommended)", default = True, options = {'SKIP_SAVE'})

bpy.types.Scene.mat_lib_bcm_write = bpy.props.StringProperty(name = "Text Datablock", description = "Name of text datablock to write .bcm data to", default="bcm_file", options = {'SKIP_SAVE'})
bpy.types.Scene.mat_lib_bcm_read = bpy.props.StringProperty(name = "Text Datablock", description = "Name of text datablock to read .bcm data from", default="bcm_file", options = {'SKIP_SAVE'})
bpy.types.Scene.mat_lib_bcm_name = bpy.props.StringProperty(name = "Material Name", description = "Specify a name for the new material", default="Untitled", options = {'SKIP_SAVE'})

bpy.types.Scene.mat_lib_bcm_save_location = bpy.props.StringProperty(name = "Save location", description = "Directory to save .bcm files in", default=mat_lib_folder + os.sep + "my-materials" + os.sep, options = {'SKIP_SAVE'}, subtype="DIR_PATH")
bpy.types.Scene.mat_lib_bcm_open_location = bpy.props.StringProperty(name = "Open location", description = "Location of .bcm file to open", default=mat_lib_folder + os.sep + "my-materials" + os.sep + "untitled.bcm", options = {'SKIP_SAVE'})

category_enum_items = [("None0", "None", "No category selected")]
bpy.types.Scene.mat_lib_material_category = bpy.props.EnumProperty(name = "", items = category_enum_items, description = "Choose a category", options = {'SKIP_SAVE'})
prev_category = "None0"

subcategory_enum_items = [("None0", "None", "No Subcategory Selected")]
bpy.types.Scene.mat_lib_material_subcategory = bpy.props.EnumProperty(name = "", items = subcategory_enum_items, description = "Choose a subcategory", options = {'SKIP_SAVE'})

class OnlineMaterialLibraryPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Online Material Library"
    bl_idname = "OnlineMaterialLibraryPanel"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"
    
    def draw(self, context):
        global show_success_message
        global show_success_message_timeout
        global current_material_number
        global mat_lib_contents
        global prev_category
        global save_filename
        
        layout = self.layout
        
        if context.scene.render.engine == "CYCLES":
            #Cycles is enabled!
            row = layout.row()
            
            if category_type is not "info" and category_type is not "settings" and category_type is not "tools":
                if mat_lib_contents == "" or mat_lib_contents == "Please refresh.":
                    if mat_lib_folder == "error":
                        row.label(text="ERROR: Could not find installation path!", icon='ERROR')
                    else:
                        #Material Library Contents variable is empty -- show welcome message
                        row.label(text="Online Material Library Add-on -- Version 0.5", icon='SMOOTH')
                        
                        row = layout.row()
                        rowcol = row.column(align=True)
                        rowcol.alignment = 'EXPAND'
                        rowcol.prop(context.scene, "mat_lib_library", text="")
                        
                        rowcolrow = rowcol.row(align=True)
                        rowcolrow.alignment = 'EXPAND'
                        if "bundled" not in context.scene.mat_lib_library:
                            rowcolrow.operator("material.libraryconnect", text="Connect", icon='WORLD').mode = "online"
                        if "testing" not in context.scene.mat_lib_library:
                            rowcolrow.operator("material.libraryconnect", text="Work Offline", icon='DISK_DRIVE').mode = "offline"
                    
                elif working_mode is not "none":
                    #We have a valid material library
                    row = layout.row(align=True)
                    row.alignment = 'EXPAND'
                    row.prop(bpy.context.scene, "mat_lib_material_category")
                else:
                    #Could not retrive a valid material library
                    row.label(text="Could not retrieve material library.", icon='CANCEL')
                    row = layout.row()
                    row.label(text=str(mat_lib_contents))
                    row = layout.row()
                    row.label(text="..." + str(mat_lib_contents)[-50:])
                    
                    row = layout.row()
                    rowcol = row.column(align=True)
                    rowcol.alignment = 'EXPAND'
                    rowcol.prop(context.scene, "mat_lib_library", text="")
                    
                    rowcolrow = rowcol.row(align=True)
                    rowcolrow.alignment = 'EXPAND'
                    if "bundled" not in context.scene.mat_lib_library:
                        rowcolrow.operator("material.libraryconnect", text="Attempt Reconnect", icon='WORLD').mode = "online"
                    if "testing" not in context.scene.mat_lib_library:
                        rowcolrow.operator("material.libraryconnect", text="Work Offline", icon='DISK_DRIVE').mode = "offline"
            
            #Here we check if the user has changed the category, if so, update.
            if prev_category != bpy.context.scene.mat_lib_material_category:
                prev_category = bpy.context.scene.mat_lib_material_category
                libraryCategoryUpdate()
            
            if category_type == "none":
                #Not browsing category
                if working_mode is not "none":
                    row = layout.row()
                    rowcol = row.column(align=True)
                    rowcol.alignment = 'EXPAND'
                    rowcol.prop(context.scene, "mat_lib_library", text="")
                    
                    rowcolrow = rowcol.row(align=True)
                    rowcolrow.alignment = 'EXPAND'
                    if "bundled" not in context.scene.mat_lib_library:
                        if working_mode == "online":
                            rowcolrow.operator("material.libraryconnect", text="Reconnect", icon='WORLD').mode = "online"
                        else:
                            rowcolrow.operator("material.libraryconnect", text="Connect", icon='WORLD').mode = "online"
                    if "testing" not in context.scene.mat_lib_library:
                        if working_mode == "offline":
                            rowcolrow.operator("material.libraryconnect", text="Reload Library", icon='DISK_DRIVE').mode = "offline"
                        else:
                            rowcolrow.operator("material.libraryconnect", text="Work Offline", icon='DISK_DRIVE').mode = "offline"
                
                row = layout.row(align=True)
                row.alignment = 'EXPAND'
                row.operator("material.libraryinfo", text="Info", icon='INFO')
                row.operator("material.librarytools", text="Tools", icon='MODIFIER')
                row.operator("material.librarysettings", text="Settings", icon='SETTINGS')
                
                if "Up-to-date." not in update_data[0]:
                    row = layout.row()
                    row.label(text=update_data[0])
                    row.operator("wm.url_open", text="Get latest version", icon='WORLD').url = update_data[1]
                    
            elif category_type == "info":
                row.label(text="Add-on Info", icon='INFO')
                row.operator("material.libraryhome", text="", icon='LOOP_BACK')
                
                row = layout.row()
                row.operator("wm.url_open", text="All materials are CC0 - learn more.", emboss=False).url = "http://creativecommons.org/publicdomain/zero/1.0/"
                
                row = layout.row()
                row.operator("wm.url_open", text="Material previews generated with B.M.P.S.", emboss=False).url = "https://svn.blender.org/svnroot/bf-blender/trunk/lib/tests/rendering/cycles/blend_files/bmps.blend"
                row = layout.row()
                row.operator("wm.url_open", text="B.M.P.S. created by Robin \"tuqueque\" Marín", emboss=False).url = "http://blenderartists.org/forum/showthread.php?151903-b.m.p.s.-1.5!"
            
            elif category_type == "settings":
                row.label(text="Library Settings", icon='SETTINGS')
                row.operator("material.libraryhome", text="", icon='LOOP_BACK')
                
                row = layout.row()
                row.prop(bpy.context.scene, "mat_lib_auto_preview")
                row = layout.row()
                row.prop(bpy.context.scene, "mat_lib_osl_only_trusted")
                row = layout.row()
                row.prop(bpy.context.scene, "mat_lib_images_only_trusted")
                
                row = layout.row()
                row.label(text="Cached data for active library:")
                
                row = layout.row()
                if mat_lib_cached_files == 0:
                    row.label(text="No cached files.")
                elif mat_lib_cached_files == -2:
                    row.label(text="The Bundled library contains no cached files.")
                elif mat_lib_cached_files == 1:
                    row.label(text="1 cached file.")
                    row.operator("material.libraryclearcache", text="Clear Cache", icon='CANCEL')
                elif mat_lib_cached_files != -1:
                    row.label(text=str(mat_lib_cached_files) + " cached files.")
                    row.operator("material.libraryclearcache", text="Clear Cache", icon='CANCEL')
                else:
                    row.label(text="Please select a library first.", icon="ERROR")
            
            elif category_type == "tools":
                row.label(text="Material Tools", icon='MODIFIER')
                row.operator("material.libraryhome", text="", icon='LOOP_BACK')
                
                row = layout.row()
                row.label(text="Write material data to text as .bcm:")
                
                row = layout.row(align=True)
                row.alignment = 'EXPAND'
                row.prop(bpy.context.scene, "mat_lib_bcm_write", text="", icon="TEXT")
                row.operator("material.libraryconvert", text="Write to text", icon='MATERIAL_DATA')
                
                row = layout.row()
                row.label(text="Save material(s) as .bcm files:")
                
                row = layout.row()
                col = row.column(align=True)
                col.alignment = 'EXPAND'
                colrow = col.row()
                colrow.prop(context.scene, "mat_lib_bcm_save_location", text="")
                colrow = col.row(align=True)
                colrow.alignment = 'EXPAND'
                colrow.operator("material.libraryconvert", text="Save active", icon='DISK_DRIVE').save_location = context.scene.mat_lib_bcm_save_location
                save_button = colrow.operator("material.libraryconvert", text="Save all materials", icon='DISK_DRIVE')
                save_button.save_location = context.scene.mat_lib_bcm_save_location
                save_button.all_materials = True
                
                row = layout.row()
                row.label(text="Open a local .bcm file:")
                 
                row = layout.row()
                col = row.column(align=True)
                col.alignment = 'EXPAND'
                colrow = col.row()
                colrow.prop(context.scene, "mat_lib_bcm_open_location", text="")
                colrow.operator("buttons.file_browse", text="", icon='FILESEL').relative_path = False
                colrow = col.row(align=True)
                colrow.alignment = 'EXPAND'
                colrow.operator("material.libraryadd", text="Add to materials", icon='ZOOMIN').open_location = context.scene.mat_lib_bcm_open_location
                colrow.operator("material.libraryapply", text="Apply to active", icon='PASTEDOWN').open_location = context.scene.mat_lib_bcm_open_location
                
                row = layout.row()
                row.label(text="Read .bcm data in a text block to a material:")
                 
                row = layout.row()
                col = row.column(align=True)
                col.alignment = 'EXPAND'
                colrow = col.row()
                colrow.prop(context.scene, "mat_lib_bcm_read", text="", icon='TEXT')
                colrow = col.row()
                colrow.prop(context.scene, "mat_lib_bcm_name", text="", icon='MATERIAL')
                colrow = col.row(align=True)
                colrow.alignment = 'EXPAND'
                colrow.operator("material.libraryadd", text="Add to materials", icon='ZOOMIN').text_block = context.scene.mat_lib_bcm_read
                colrow.operator("material.libraryapply", text="Apply to active", icon='PASTEDOWN').text_block = context.scene.mat_lib_bcm_read
                
            elif category_type == "category":
                #Browsing category - show materials
                row = layout.row()
                matwrap = row.box()
                i = 0
                while i < category_materials:
                    if i == current_material_number:
                        matwraprow = matwrap.row()
                        matwrapbox = matwraprow.box()
                        matwrapboxrow = matwrapbox.row()
                        matwrapboxrow.operator("material.libraryviewmaterial", text=material_names[i], icon='MATERIAL', emboss=False).material = i
                        matwrapboxrowcol = matwrapboxrow.column()
                        matwrapboxrowcolrow = matwrapboxrowcol.row()
                        matwrapboxrowcolrow.operator("material.libraryviewmaterial", text="", icon='BLANK1', emboss=False).material = i
                        matwrapboxrowcolrow.operator("material.libraryviewmaterial", text="", icon='BLANK1', emboss=False).material = i
                        matwrapboxrowcol = matwrapboxrow.column()
                        matwrapboxrowcolrow = matwrapboxrowcol.row()
                        matwrapboxrowcolrowsplit = matwrapboxrowcolrow.split(percentage=0.8)
                        matwrapboxrowcolrowsplitrow = matwrapboxrowcolrowsplit.row()
                        
                        #Ratings
                        if material_ratings[i] == 0:
                            matwrapboxrowcolrowsplitrow.operator("material.libraryviewmaterial", text="Unrated", emboss=False).material = i
                        else:
                            e = 0
                            while e < material_ratings[i]:
                                matwrapboxrowcolrowsplitrow.operator("material.libraryviewmaterial", text="", icon='SOLO_ON', emboss=False).material = i
                                e = e + 1
                            
                            if material_ratings[i] is not 5:    
                                e = 0
                                while e < (5 - material_ratings[i]):
                                    matwrapboxrowcolrowsplitrow.operator("material.libraryviewmaterial", text="", icon='SOLO_OFF', emboss=False).material = i
                                    e = e + 1
                    else:
                        matwraprow = matwrap.row()
                        matwrapcol = matwraprow.column()
                        matwrapcolrow = matwrapcol.row()
                        matwrapcolrow.operator("material.libraryviewmaterial", text=material_names[i], icon='MATERIAL', emboss=False).material = i
                        matwrapcolrowcol = matwrapcolrow.column()
                        matwrapcolrowcolrow = matwrapcolrowcol.row()
                        matwrapcolrowcolrow.operator("material.libraryviewmaterial", text="", icon='BLANK1', emboss=False).material = i
                        matwrapcolrowcolrow.operator("material.libraryviewmaterial", text="", icon='BLANK1', emboss=False).material = i
                        matwrapcolrowcol = matwrapcolrow.column()
                        matwrapcolrowcolrow = matwrapcolrowcol.row()
                        matwrapcolrowcolrowsplit = matwrapcolrowcolrow.split(percentage=0.8)
                        matwrapcolrowcolrowsplitrow = matwrapcolrowcolrowsplit.row()
                        
                        #Ratings
                        if material_ratings[i] == 0:
                            matwrapcolrowcolrowsplitrow.operator("material.libraryviewmaterial", text="Unrated", emboss=False).material = i
                        else:
                            e = 0
                            while e < material_ratings[i]:
                                matwrapcolrowcolrowsplitrow.operator("material.libraryviewmaterial", text="", icon='SOLO_ON', emboss=False).material = i
                                e = e + 1
                            
                            if material_ratings[i] is not 5:    
                                e = 0
                                while e < (5 - material_ratings[i]):
                                    matwrapcolrowcolrowsplitrow.operator("material.libraryviewmaterial", text="", icon='SOLO_OFF', emboss=False).material = i
                                    e = e + 1
                    i = i + 1
                
                if current_material_number is not -1:
                    #Display selected material's info
                    row = layout.row()
                    infobox = row.box()
                    inforow = infobox.row()
                    
                    #Material name
                    inforow.label(text=(material_names[current_material_number]))
                    
                    #Preview download button
                    if current_material_previewed == False:
                        preview_button = inforow.operator("material.librarypreview", text="", icon='COLOR', emboss=False)
                        preview_button.name = material_names[current_material_number]
                        preview_button.filename = material_filenames[current_material_number]
                    
                    if library == "release":
                        #Cache indicator/button
                        if current_material_cached:
                            inforow.label(text="", icon="SAVE_COPY")
                        else:
                            inforow.operator("material.librarycache", text="", icon="LONGDISPLAY", emboss=False).filename = material_filenames[current_material_number]
                    
                    #Close button
                    inforow.operator("material.libraryviewmaterial", text="", icon='PANEL_CLOSE').material = -1
                    
                    #inforow = infobox.row()
                    inforowsplit = infobox.split(percentage=0.5)
                    
                    #Display a preview
                    if bpy.data.textures.find("mat_lib_preview_texture") == -1:
                        bpy.data.textures.new("mat_lib_preview_texture", "IMAGE")
                        preview_texture = bpy.data.textures["mat_lib_preview_texture"]
                        inforowcol = inforowsplit.column()
                        
                        if material_contributors[current_material_number] != "Unknown" and material_contributors[current_material_number] != "Anonymous":
                            inforowcolrow = inforowcol.row()
                            inforowcolrow.label(text="By %s." % material_contributors[current_material_number])
                        else:
                            inforowcolrow = inforowcol.row()
                            inforowcolrow.label(text="Author unknown.")
                        inforowcolrow = inforowcol.row()
                        inforowcolrow.template_preview(preview_texture)
                    else:
                        preview_texture = bpy.data.textures['mat_lib_preview_texture']
                        inforowcol = inforowsplit.column()
                        if material_contributors[current_material_number] != "Unknown" and material_contributors[current_material_number] != "Anonymous":
                            inforowcolrow = inforowcol.row()
                            inforowcolrow.label(text="By %s." % material_contributors[current_material_number])
                        else:
                            inforowcolrow = inforowcol.row()
                            inforowcolrow.label(text="Author unknown.")
                        inforowcolrow = inforowcol.row()
                        inforowcolrow.template_preview(preview_texture)
                    
                    inforowcol = inforowsplit.column()
                    inforowcolrow = inforowcol.row()
                    inforowcolcol = inforowcol.column(align=True)
                    inforowcolcol.alignment = 'EXPAND'
                    inforowcolcolrow = inforowcolcol.row()
                    if material_detail_view == 'RENDER':
                        if material_fireflies[current_material_number] == "high":
                            inforowcolcolrow.label(text="Firefly Level: High")
                            inforowcolcolrow.label(text="", icon='PARTICLES')
                        elif material_fireflies[current_material_number] == "medium":
                            inforowcolcolrow.label(text="Firefly Level: Medium")
                            inforowcolcolrow.label(text="", icon='MOD_PARTICLES')
                        else:
                            inforowcolcolrow.label(text="Firefly Level: Low")
                        inforowcolcolrow = inforowcolcol.row()
                            
                        if material_complexities[current_material_number] == "simple":
                            inforowcolcolrow.label(text="Complexity: Simple")
                        elif material_complexities[current_material_number] == "intermediate":
                            inforowcolcolrow.label(text="Complexity: Intermediate")
                        elif material_complexities[current_material_number] == "complex":
                            inforowcolcolrow.label(text="Complexity: Complex")
                        inforowcolcolrow = inforowcolcol.row()
                        
                        if material_speeds[current_material_number] == "slow":
                            inforowcolcolrow.label(text="Render Speed: Slow")
                            inforowcolcolrow.label(text="", icon='PREVIEW_RANGE')
                        elif material_speeds[current_material_number] == "fair":
                            inforowcolcolrow.label(text="Render Speed: Fair")
                            inforowcolcolrow.label(text="", icon='TIME')
                        else:
                            inforowcolcolrow.label(text="Render Speed: Good")
                        inforowcolcolrow = inforowcolcol.row()
                        details = inforowcolcolrow.row(align=True)
                        details.alignment = 'RIGHT'
                        detailshidden = details.row()
                        detailshidden.enabled = False
                        detailshidden.operator("material.librarydetailview", text="", icon='PLAY_REVERSE').mode = "PREVIOUS"
                        details.operator("material.librarydetailview", text="", icon='PLAY').mode = "NEXT"
                    elif material_detail_view == "DATA":
                        if material_scripts[current_material_number] == "0":
                            inforowcolcolrow.label(text="OSL Scripts: 0")
                        else:
                            inforowcolcolrow.label(text="OSL Scripts: %s" % material_scripts[current_material_number])
                            inforowcolcolrow.label(text="", icon='TEXT')
                        inforowcolcolrow = inforowcolcol.row()
                    
                        if material_images[current_material_number] == "0":
                            inforowcolcolrow.label(text="Images: 0")
                        else:
                            inforowcolcolrow.label(text="Images: %s" % material_images[current_material_number])
                            inforowcolcolrow.label(text="", icon='IMAGE_RGB')
                            
                        inforowcolcolrow = inforowcolcol.row()
                        inforowcolcolrow.label(text=" ")
                        
                        inforowcolcolrow = inforowcolcol.row()
                        details = inforowcolcolrow.row(align=True)
                        details.alignment = 'RIGHT'
                        details.operator("material.librarydetailview", text="", icon='PLAY_REVERSE').mode = "PREVIOUS"
                        detailshidden = details.row()
                        detailshidden.enabled = False
                        detailshidden.operator("material.librarydetailview", text="", icon='PLAY').mode = "NEXT"
                        
                    inforowcolcolcol = inforowcolcol.column(align=True)
                    inforowcolcolcol.alignment = 'EXPAND'
                    functions = inforowcolcolcol.row()
                    #Display "Add" button
                    mat_button = functions.operator("material.libraryadd", text="Add to materials", icon='ZOOMIN')
                    mat_button.mat_name = material_names[current_material_number]
                    mat_button.filename = material_filenames[current_material_number]
                    functions = inforowcolcolcol.row()
                    
                    #Display "Apply" button
                    mat_button = functions.operator("material.libraryapply", text="Apply to active", icon='PASTEDOWN')
                    mat_button.mat_name = material_names[current_material_number]
                    mat_button.filename = material_filenames[current_material_number]
                    functions = inforowcolcolcol.row()
                    
                    #Display "Save" button
                    mat_button = functions.operator("material.librarysave", text="Save as...", icon='DISK_DRIVE')
                    mat_button.filepath = mat_lib_folder + os.sep + "my-materials" + os.sep + material_filenames[current_material_number] + ".bcm"
                    mat_button.filename = material_filenames[current_material_number]
                    save_filename = material_filenames[current_material_number]
                
            elif category_type == "subcategory":
                #Browsing subcategory - show materials
                row = layout.row()
                matwrap = row.box()
                i = 0
                while i < category_materials:
                    if (i == current_material_number):
                        matwraprow = matwrap.row()
                        matwrapbox = matwraprow.box()
                        matwrapboxrow = matwrapbox.row()
                        matwrapboxrow.operator("material.libraryviewmaterial", text=material_names[i], icon='MATERIAL', emboss=False).material = i
                        matwrapboxrowcol = matwrapboxrow.column()
                        matwrapboxrowcolrow = matwrapboxrowcol.row()
                        matwrapboxrowcolrow.operator("material.libraryviewmaterial", text="", icon='BLANK1', emboss=False).material = i
                        matwrapboxrowcolrow.operator("material.libraryviewmaterial", text="", icon='BLANK1', emboss=False).material = i
                        matwrapboxrowcol = matwrapboxrow.column()
                        matwrapboxrowcolrow = matwrapboxrowcol.row()
                        matwrapboxrowcolrowsplit = matwrapboxrowcolrow.split(percentage=0.8)
                        matwrapboxrowcolrowsplitrow = matwrapboxrowcolrowsplit.row()
                        
                        #Ratings
                        e = 0
                        while e < material_ratings[i]:
                            matwrapboxrowcolrowsplitrow.operator("material.libraryviewmaterial", text="", icon='SOLO_ON', emboss=False).material = i
                            e = e + 1
                        
                        if material_ratings[i] is not 5:    
                            e = 0
                            while e < (5 - material_ratings[i]):
                                matwrapboxrowcolrowsplitrow.operator("material.libraryviewmaterial", text="", icon='SOLO_OFF', emboss=False).material = i
                                e = e + 1
                    else:
                        matwraprow = matwrap.row()
                        matwrapcol = matwraprow.column()
                        matwrapcolrow = matwrapcol.row()
                        matwrapcolrow.operator("material.libraryviewmaterial", text=material_names[i], icon='MATERIAL', emboss=False).material = i
                        matwrapcolrowcol = matwrapcolrow.column()
                        matwrapcolrowcolrow = matwrapcolrowcol.row()
                        matwrapcolrowcolrow.operator("material.libraryviewmaterial", text="", icon='BLANK1', emboss=False).material = i
                        matwrapcolrowcolrow.operator("material.libraryviewmaterial", text="", icon='BLANK1', emboss=False).material = i
                        matwrapcolrowcol = matwrapcolrow.column()
                        matwrapcolrowcolrow = matwrapcolrowcol.row()
                        matwrapcolrowcolrowsplit = matwrapcolrowcolrow.split(percentage=0.8)
                        matwrapcolrowcolrowsplitrow = matwrapcolrowcolrowsplit.row()
                        
                        #Ratings
                        e = 0
                        while e < material_ratings[i]:
                            matwrapcolrowcolrowsplitrow.operator("material.libraryviewmaterial", text="", icon='SOLO_ON', emboss=False).material = i
                            e = e + 1
                        
                        if material_ratings[i] is not 5:    
                            e = 0
                            while e < (5 - material_ratings[i]):
                                matwrapcolrowcolrowsplitrow.operator("material.libraryviewmaterial", text="", icon='SOLO_OFF', emboss=False).material = i
                                e = e + 1
                    i = i + 1
                    
                if current_material_number is not -1:
                    #Display selected material's info
                    row = layout.row()
                    infobox = row.box()
                    inforow = infobox.row()
                   
                    inforow.label(text=material_names[current_material_number])
                    if bpy.context.scene.mat_lib_auto_preview == False:
                        mat_button = inforow.operator("material.librarypreview", text="", icon='IMAGE_COL')
                        mat_button.name = material_names[current_material_number]
                        mat_button.filename = material_filenames[current_material_number]
                    inforow.operator("material.viewmaterial", text="", icon='PANEL_CLOSE').material = -1
                    
                    inforow = infobox.row()
                    
                    #Display a preview
                    if bpy.data.textures.find("mat_lib_preview_texture") == -1:
                        bpy.data.textures.new("mat_lib_preview_texture", "IMAGE")
                        preview_texture = bpy.data.textures["mat_lib_preview_texture"]
                        inforowcol = inforow.column(align=True)
                        inforowcol.alignment = 'EXPAND'
                        inforowcolrow = inforowcol.row()
                        inforowcolrow.operator("material.librarypreview", text="Preview Material", icon='IMAGE_COL')
                        inforowcolrow = inforowcol.row()
                        inforowcolrow.template_preview(preview_texture)
                    else:
                        preview_texture = bpy.data.textures['mat_lib_preview_texture']
                        inforowcol = inforow.column(align=True)
                        inforowcol.alignment = 'EXPAND'
                        inforowcolrow = inforowcol.row()
                        inforowcolrow.operator("material.librarypreview", text="Preview Material", icon='IMAGE_COL')
                        inforowcolrow = inforowcol.row()
                        inforowcolrow.template_preview(preview_texture)
                    
                    inforowcol = inforow.column()
                    inforowcolrow = inforowcol.row()
                    if bpy.data.materials.find(material_names[current_material_number]) is not -1:
                        inforowcolrow.label(text="Material exists", icon='ERROR')
                    if material_contributors[current_material_number] == "Unknown" or material_contributors[current_material_number] == "Anonymous":
                        inforowcolrow = inforowcol.row()
                    else:
                        inforowcolrow = inforowcol.row()
                        inforowcolrow.label(text="By %s." % material_contributors[current_material_number])
                        inforowcolrow = inforowcol.row()
                    
                    if bpy.data.materials.find(material_names[current_material_number]) is not -1:
                        inforowcolrow.label(text="\"Add\" will overwrite.")
                    inforowcolcol = inforowcol.column(align=True)
                    inforowcolcol.alignment = 'EXPAND'
                    
                    
                    #Display "Add" or "Overwrite" button
                    mat_button = inforowcolcol.operator("material.libraryadd", text="Add to materials", icon='ZOOMIN')
                    mat_button.name = material_names[current_material_number]
                    mat_button.filename = material_filenames[current_material_number]
                    
                    #Display "Paste" button
                    mat_button = inforowcolcol.operator("material.libraryapply", text="Apply to active", icon='PASTEDOWN')
                    mat_button.name = bpy.context.object.active_material.name
                    mat_button.filename = material_filenames[current_material_number]
                    
                    #Display "Save" button
                    mat_button = inforowcolcol.operator("material.librarysave", text="Save to disk", icon='DISK_DRIVE')
                    mat_button.name = bpy.context.object.active_material.name
                    mat_button.filename = material_filenames[current_material_number]
                    save_filename = material_filenames[current_material_number]
        else:
            #Dude, you gotta switch to Cycles to use this.
            row = layout.row()
            row.label(text="Sorry, Cycles only at the moment.",icon='ERROR')

class libraryCategory:
    def __init__(self, title, folder):
        self.title = title
        self.folder = folder
        self.materials = []

class libraryMaterial:
    def __init__(self, name, href, contrib, stars, fireflies, speed, complexity, scripts, images):
        self.name = name
        self.href = href
        self.contrib = contrib
        self.stars = stars
        self.fireflies = fireflies
        self.speed = speed
        self.complexity = complexity
        self.scripts = scripts
        self.images = images

def handleCategories(categories):
    for index, category in enumerate(categories):
        handleCategory(category, index)

def handleCategory(category, index):
    if 'addon' in category.attributes:
        needed_version = float(category.attributes['addon'].value)
        this_version = bl_info["version"][0] + (bl_info["version"][1] / 10.0)
        
        #Check this addon's compatibility with this category
        if needed_version > this_version:
            print('\n\n-Category "' + category.attributes['title'].value + '" not used; its materials are for a newer version of this add-on.')
            return
    
    if 'bl' in category.attributes:
        bl_version = bpy.app.version[0] + (bpy.app.version[1] / 100)
        
        #Check Blender's compatibility with this category
        if category.attributes['bl'].value[-1] == "-":
            #This option is for if Blender's compatiblity
            #with a category started only with a specific
            #version, but has not yet ended; this will
            #look like the following: bl="2.64-"
            bl_lower = float(category.attributes['bl'].value[:-1])
            if bl_lower > bl_version:
                print('\n\n-Category "' + category.attributes['title'].value + '" was not used; its materials are not compatible with this version of Blender.')
                return
            
        elif category.attributes['bl'].value[0] == "-":
            #This option is for if Blender's compatiblity
            #with a category ended at some point, and will
            #look like the following: bl="-2.73"
            bl_upper = float(category.attributes['bl'].value[1:])
            if bl_upper < bl_version:
                print('\n\n-Category "' + category.attributes['title'].value + '" was not used; its materials are not compatible with this version of Blender.')
                return
            
        else:
            #This option is for if Blender's compatiblity
            #with a category started with a certain version,
            #then ended with another; it will look
            #like the following: bl="2.64-2.73"
            bl_lower = float(category.attributes['bl'].value.split('-')[0])
            bl_upper = float(category.attributes['bl'].value.split('-')[1])
            if bl_upper < bl_version:
                print('\n\n-Category "' + category.attributes['title'].value + '" was not used; its materials are not compatible with this version of Blender.')
                return
            elif bl_lower > bl_version:
                print('\n\n-Category "' + category.attributes['title'].value + '" was not used; its materials are not compatible with this version of Blender.')
                return
    
    if library is not "bundled":
        if not os.path.exists(mat_lib_folder + os.sep + mat_lib_host + os.sep + library + os.sep + "cycles" + os.sep + category.attributes['folder'].value):
            print("Folder \"/" + category.attributes['folder'].value + "/\" does not exist; creating now.")
            if library == "composite":
                os.mkdir(mat_lib_folder + os.sep + mat_lib_host + os.sep + "cycles" + os.sep + category.attributes['folder'].value)
            else:
                os.mkdir(mat_lib_folder + os.sep + mat_lib_host + os.sep + library + os.sep + "cycles" + os.sep + category.attributes['folder'].value)
        
        if 'remove' in category.attributes:
            if library == "composite":
                if os.path.exists(mat_lib_folder + os.sep + mat_lib_host + os.sep + "cycles" + os.sep + category.attributes['folder'].value):
                    for the_file in os.listdir(mat_lib_folder + os.sep + mat_lib_host + os.sep + "cycles" + os.sep + category.attributes['folder'].value):
                        file_path = mat_lib_folder + os.sep + mat_lib_host + os.sep + "cycles" + os.sep + category.attributes['folder'].value + os.sep + the_file
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                        elif os.path.isdir(file_path):
                            for sub_file in os.listdir(file_path):
                                if os.path.isfile(file_path + sub_file):
                                    os.remove(file_path + sub_file)
                            os.rmdir(file_path)
                    os.rmdir(mat_lib_folder + os.sep + mat_lib_host + os.sep + "cycles" + os.sep + category.attributes['folder'].value)
            else:
                if os.path.exists(mat_lib_folder + os.sep + mat_lib_host + os.sep + library + os.sep + "cycles" + os.sep + category.attributes['folder'].value):
                    for the_file in os.listdir(mat_lib_folder + os.sep + mat_lib_host + os.sep + library + os.sep + "cycles" + os.sep + category.attributes['folder'].value):
                        file_path = mat_lib_folder + os.sep + mat_lib_host + os.sep + library + os.sep + "cycles" + os.sep + category.attributes['folder'].value + os.sep + the_file
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                        elif os.path.isdir(file_path):
                            for sub_file in os.listdir(file_path):
                                if os.path.isfile(file_path + sub_file):
                                    os.remove(file_path + sub_file)
                            os.rmdir(file_path)
                    os.rmdir(mat_lib_folder + os.sep + mat_lib_host + os.sep + library + os.sep + "cycles" + os.sep + category.attributes['folder'].value)
                return
    
    print ('\n\n-Category "' + category.attributes['title'].value + '"; located in folder "/' + category.attributes['folder'].value + '/".')
    library_data.append(libraryCategory(category.attributes['title'].value, category.attributes['folder'].value))
    handleMaterials(category.getElementsByTagName("material"), index)

def handleMaterials(materials, index):
    for material in materials:
        handleMaterial(material, index)

def handleMaterial(material, index):
    if 'addon' in material.attributes:
        needed_version = float(material.attributes['addon'].value)
        this_version = bl_info["version"][0] + (bl_info["version"][1] / 10.0)
        
        #Check this addon's compatibility with this material
        if needed_version > this_version:
            print('\n  -Material "' + material.attributes['name'].value + '" was not used, and is for a newer version of this add-on.')
            return
    
    if 'bl' in material.attributes:
        bl_version = bpy.app.version[0] + (bpy.app.version[1] / 100)
        
        #Check Blender's compatibility with this material
        if material.attributes['bl'].value[-1] == "-":
            #This option is for if Blender's compatiblity
            #with a material started only with a specific
            #version, but has not yet ended; this will
            #look like the following: bl="2.64-"
            bl_lower = float(material.attributes['bl'].value[:-1])
            if bl_lower > bl_version:
                print('\n  -Material "' + material.attributes['name'].value + '" was not used, and is not compatible with this version of Blender.')
                return
            
        elif material.attributes['bl'].value[0] == "-":
            #This option is for if Blender's compatiblity
            #with a material ended at some point, and will
            #look like the following: bl="-2.73"
            bl_upper = float(material.attributes['bl'].value[1:])
            if bl_upper < bl_version:
                print('\n  -Material "' + material.attributes['name'].value + '" was not used, and is not compatible with this version of Blender.')
                return
            
        else:
            #This option is for if Blender's compatiblity
            #with a material started with a certain version,
            #then ended with another; it will
            #look like the following: bl="2.64-2.73"
            bl_lower = float(material.attributes['bl'].value.split('-')[0])
            bl_upper = float(material.attributes['bl'].value.split('-')[1])
            if bl_upper < bl_version:
                print('\n  -Material "' + material.attributes['name'].value + '" was not used, and is not compatible with this version of Blender.')
                return
            elif bl_lower > bl_version:
                print('\n  -Material "' + material.attributes['name'].value + '" was not used, and is not compatible with this version of Blender.')
                return
    
    if 'by' in material.attributes:
        contributor = material.attributes['by'].value
    else:
        contributor = "Unknown"
    
    if 'stars' in material.attributes:
        stars = material.attributes['stars'].value
    else:
        stars = '0'
    
    if 'fireflies' in material.attributes:
        fireflies = material.attributes['fireflies'].value
    else:
        fireflies = 'low'
    
    if 'speed' in material.attributes:
        speed = material.attributes['speed'].value
    else:
        speed = 'good'
    
    if 'complexity' in material.attributes:
        complexity = material.attributes['complexity'].value
    else:
        complexity = 'simple'
    
    if 'scripts' in material.attributes:
        scripts = material.attributes['scripts'].value
    else:
        scripts = '0'
    
    if 'images' in material.attributes:
        images = material.attributes['images'].value
    else:
        images = '0'
    
    library_data[index].materials.append(
        libraryMaterial(
        material.attributes['name'].value,
        material.attributes['href'].value,
        contributor,
        int(stars),
        fireflies,
        speed,
        complexity,
        scripts,
        images))
    print ('\n  -Material "' + 
        material.attributes['name'].value + 
        '"\n    -Filename: "' + 
        material.attributes['href'].value + 
        '.bcm"\n    -Rating: ' + stars + 
        ' stars\n    -Contributed by "' + 
        contributor + '"')

class LibraryConnect(bpy.types.Operator):
    '''Connect to the material library'''
    bl_idname = "material.libraryconnect"
    bl_label = "Connect to the material library"
    mode = bpy.props.StringProperty()

    def execute(self, context):
        global library_data
        global library
        global update_data
        
        global mat_lib_contents
        global mat_lib_categories
        global mat_lib_category_names
        global mat_lib_category_types
        global mat_lib_category_filenames
        
        global category_enum_items
        global subcategory_enum_items
        
        global show_success_message
        global show_success_message_timeout
        
        global prev_category
        global mat_lib_host
        global mat_lib_location
        global working_mode
        
        if self.mode == "online":
            mat_lib_host = context.scene.mat_lib_library[:context.scene.mat_lib_library.index("/")]
            mat_lib_location = context.scene.mat_lib_library[(context.scene.mat_lib_library.index(mat_lib_host) + len(mat_lib_host)):]
            print(mat_lib_host)
            print(mat_lib_location)
        elif "bundled" not in context.scene.mat_lib_library:
            mat_lib_host = context.scene.mat_lib_library[:context.scene.mat_lib_library.index("/")]
        
        #Pre-create preview image
        if not os.path.exists(mat_lib_folder + os.sep + "mat_lib_preview_image.jpg"):
            f = open(mat_lib_folder + os.sep + "mat_lib_preview_image.jpg", 'w+b')
            f.close()
        
        if self.mode == "online":
            #Connect and download
            connection = http.client.HTTPConnection(mat_lib_host)
            connection.request("GET", mat_lib_location + "cycles/index.xml")
            
            if "release" in context.scene.mat_lib_library:
                response = connection.getresponse().read()
                
                #Cache the index.xml file for offline use
                library_file = open(os.path.join(mat_lib_folder, mat_lib_host, "release", "cycles", "index.xml"), mode="w+b")
                library_file.write(response)
                library_file.close()
                
                #Create /textures/ folder
                if not os.path.exists(os.path.join(mat_lib_folder, mat_lib_host, "release", "cycles", "textures")):
                    os.mkdir(os.path.join(mat_lib_folder, mat_lib_host, "release", "cycles", "textures"))
                
                #Create /scripts/ folder
                if not os.path.exists(os.path.join(mat_lib_folder, mat_lib_host, "release", "cycles", "scripts")):
                    os.mkdir(os.path.join(mat_lib_folder, mat_lib_host, "release", "cycles", "scripts"))
                library = "release"
            elif "testing" in context.scene.mat_lib_library:
                response = connection.getresponse().read()
                
                #Create /textures/ folder
                if not os.path.exists(os.path.join(mat_lib_folder, mat_lib_host, "testing", "cycles", "textures")):
                    os.mkdir(os.path.join(mat_lib_folder, mat_lib_host, "testing", "cycles", "textures"))
                
                #Create /scripts/ folder
                if not os.path.exists(os.path.join(mat_lib_folder, mat_lib_host, "testing", "cycles", "scripts")):
                    os.mkdir(os.path.join(mat_lib_folder, mat_lib_host, "testing", "cycles", "scripts"))
                library = "testing"
            else:
                response = connection.getresponse().read()
                
                #Cache the index.xml file for offline use
                library_file = open(mat_lib_folder + os.sep + mat_lib_host + os.sep + "cycles" + os.sep + "index.xml", mode="w+b")
                library_file.write(response)
                library_file.close()
                
                #Create /textures/ folder
                if not os.path.exists(os.path.join(mat_lib_folder, mat_lib_host, "cycles", "textures")):
                    os.mkdir(os.path.join(mat_lib_folder, mat_lib_host, "cycles", "textures"))
                
                #Create /scripts/ folder
                if not os.path.exists(os.path.join(mat_lib_folder, mat_lib_host, "cycles", "scripts")):
                    os.mkdir(os.path.join(mat_lib_folder, mat_lib_host, "cycles", "scripts"))
                library = "composite"
                
            #Convert the response to a string
            mat_lib_contents = str(response)
            
            #Check for connection errors
            if "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" not in mat_lib_contents:
                self.report({'ERROR'}, "Error connecting; see console for details.")
                print("Received following response from server:\n" + mat_lib_contents)
                return {'CANCELLED'}
            
            #Format nicely
            mat_lib_contents = mat_lib_contents.replace("b'<?xml version=\"1.0\" encoding=\"UTF-8\"?>",'')
            mat_lib_contents = mat_lib_contents.replace("\\r\\n",'')
            mat_lib_contents = mat_lib_contents.replace("\\t",'')[:-1]
            mat_lib_contents = mat_lib_contents.replace("\\",'')
            
        else:
            if "release" in context.scene.mat_lib_library:
                #Check for cached index.xml file
                if os.path.exists(mat_lib_folder + os.sep + mat_lib_host + os.sep + "release" + os.sep + "cycles" + os.sep + "index.xml"):
                    library_file = open(mat_lib_folder + os.sep + mat_lib_host + os.sep + "release" + os.sep + "cycles" + os.sep + "index.xml", mode="r", encoding="UTF-8")
                    mat_lib_contents = library_file.read()
                    library_file.close()
                else:
                    self.report({'ERROR'}, "No cached library exists!")
                    return {'CANCELLED'}
                
                #Create /textures/ folder
                if not os.path.exists(os.path.join(mat_lib_folder, mat_lib_host, "release", "cycles", "textures")):
                    os.mkdir(os.path.join(mat_lib_folder, mat_lib_host, "release", "cycles", "textures"))
                
                #Create /scripts/ folder
                if not os.path.exists(os.path.join(mat_lib_folder, mat_lib_host, "release", "cycles", "scripts")):
                    os.mkdir(os.path.join(mat_lib_folder, mat_lib_host, "release", "cycles", "scripts"))
                library = "release"
            elif context.scene.mat_lib_library == "bundled":
                #Check for index.xml file
                if os.path.exists(mat_lib_folder + os.sep + "bundled" + os.sep + "cycles" + os.sep + "index.xml"):
                    library_file = open(mat_lib_folder + os.sep + "bundled" + os.sep + "cycles" + os.sep + "index.xml", mode="r", encoding="UTF-8")
                    mat_lib_contents = library_file.read()
                    library_file.close()
                else:
                    self.report({'ERROR'}, "Bundled library does not exist!")
                    return {'CANCELLED'}
                library = "bundled"
            else:
                #Check for cached index.xml file
                if os.path.exists(mat_lib_folder + os.sep + mat_lib_host + os.sep + "cycles" + os.sep + "index.xml"):
                    library_file = open(mat_lib_folder + os.sep + mat_lib_host + os.sep + "cycles" + os.sep + "index.xml", mode="r", encoding="UTF-8")
                    mat_lib_contents = library_file.read()
                    library_file.close()
                else:
                    self.report({'ERROR'}, "No cached library exists!")
                    return {'CANCELLED'}
                
                #Create /textures/ folder
                if not os.path.exists(os.path.join(mat_lib_folder, mat_lib_host, "cycles", "textures")):
                    os.mkdir(os.path.join(mat_lib_folder, mat_lib_host, "cycles", "textures"))
                
                #Create /scripts/ folder
                if not os.path.exists(os.path.join(mat_lib_folder, mat_lib_host, "cycles", "scripts")):
                    os.mkdir(os.path.join(mat_lib_folder, mat_lib_host, "cycles", "scripts"))
                library = "composite"
            
            if '<?xml version="1.0" encoding="UTF-8"?>' not in mat_lib_contents:
                self.report({'ERROR'}, "Cached XML file is invalid!")
                return {'CANCELLED'}
            
            #Format nicely
            mat_lib_contents = mat_lib_contents.replace('<?xml version="1.0" encoding="UTF-8"?>', '')
            mat_lib_contents = mat_lib_contents.replace("\r\n",'')
            mat_lib_contents = mat_lib_contents.replace("\n",'')
            mat_lib_contents = mat_lib_contents.replace("\t",'')
            mat_lib_contents = mat_lib_contents.replace("\\",'')
        
        #Clear important lists
        library_data = []
        mat_lib_category_names = []
        mat_lib_category_types = []
        mat_lib_category_filenames = []
            
        dom = xml.dom.minidom.parseString(mat_lib_contents)
        
        if self.mode == "online":
            if library == "composite":
                rev_file = open(mat_lib_folder + os.sep + mat_lib_host + os.sep + "cycles" + os.sep + "revision_data.ini", mode="r", encoding="UTF-8")
                rev_data = rev_file.read()
                rev_file.close()
            else:
                rev_file = open(mat_lib_folder + os.sep + mat_lib_host + os.sep + library + os.sep + "cycles" + os.sep + "revision_data.ini", mode="r", encoding="UTF-8")
                rev_data = rev_file.read()
                rev_file.close()
            
            if "revision=" in rev_data:
                revision = int(rev_data[9:])
            else:
                revision = -1
                print("The revision_data.ini file is invalid; clearing cache and re-creating.")
            
            if revision is not int(dom.getElementsByTagName("library")[0].attributes['rev'].value):
                bpy.ops.material.libraryclearcache()
            
            if library == "composite":
                rev_file = open(mat_lib_folder + os.sep + mat_lib_host + os.sep + "cycles" + os.sep + "revision_data.ini", mode="w", encoding="UTF-8")
            else:
                rev_file = open(mat_lib_folder + os.sep + mat_lib_host + os.sep + library + os.sep + "cycles" + os.sep + "revision_data.ini", mode="w", encoding="UTF-8")
            rev_file.write("revision=" + dom.getElementsByTagName("library")[0].attributes['rev'].value)
            rev_file.close()
            
            if 'addon' in dom.getElementsByTagName("library")[0].attributes:
                current_version = float(dom.getElementsByTagName("library")[0].attributes['addon'].value)
                this_version = bl_info["version"][0] + (bl_info["version"][1] / 10.0)
                if current_version > this_version:
                    update_data = ["Add-on is outdated.", dom.getElementsByTagName("library")[0].attributes['download'].value]
        
        print ("\n\n---Material Library---")
        categories = dom.getElementsByTagName("category")
        handleCategories(categories)
        
        for cat in library_data:
            #Find category names
            mat_lib_category_names.append(cat.title)
            #Find category types
            #NOTE: Will have to redo this.
            #mat_lib_category_types = safeEval(mat_lib_contents[(mat_lib_contents.index('[types]') + 7):mat_lib_contents.index('[/types]')])
            #Get category filenames
            mat_lib_category_filenames.append(cat.folder)
            
        #Find amount of categories
        mat_lib_categories = len(mat_lib_category_names)
        
        #Set enum items for category dropdown
        category_enum_items = [("None0", "None", "No category selected")]
        
        i = 0
        while i < mat_lib_categories:
            print ("Adding category #%d" % (i + 1))
            category_enum_items.append(((mat_lib_category_names[i] + str(i + 1)), mat_lib_category_names[i], (mat_lib_category_names[i] + " category")))
            i = i + 1
        bpy.types.Scene.mat_lib_material_category = bpy.props.EnumProperty(name = "", items = category_enum_items, description = "Choose a category")
        bpy.context.scene.mat_lib_material_category = "None0";
        
        #No errors - set working mode
        working_mode = self.mode
        
        self.report({'INFO'}, "Retrieved library!")
        
        return {'FINISHED'}

class LibraryInfo(bpy.types.Operator):
    '''Display add-on info'''
    bl_idname = "material.libraryinfo"
    bl_label = "Display add-on info"

    def execute(self, context):
        global category_type
        
        category_type = "info"
        
        return {'FINISHED'}

class LibraryTools(bpy.types.Operator):
    '''Display material tools'''
    bl_idname = "material.librarytools"
    bl_label = "Display material tools"

    def execute(self, context):
        global category_type
        
        category_type = "tools"
        
        return {'FINISHED'}

class LibrarySettings(bpy.types.Operator):
    '''Display add-on settings'''
    bl_idname = "material.librarysettings"
    bl_label = "Display add-on settings"

    def execute(self, context):
        global category_type
        global mat_lib_cached_files
        
        category_type = "settings"
        if library == "":
            return {'FINISHED'}
        elif library == "bundled":
            mat_lib_cached_files = -2
            return {'FINISHED'}
        elif library == "composite":
            cached_data_path = mat_lib_folder + os.sep + mat_lib_host + os.sep + "cycles" + os.sep
        else:
            cached_data_path = mat_lib_folder + os.sep + mat_lib_host + os.sep + library + os.sep + "cycles" + os.sep
        mat_lib_cached_files = 0
        for root, dirs, files in os.walk(cached_data_path):
            for name in files:
                if ".jpg" in name.lower():
                    mat_lib_cached_files += 1
                elif ".png" in name.lower():
                    mat_lib_cached_files += 1
                elif ".osl" in name.lower():
                    mat_lib_cached_files += 1
                elif ".osl" in name.lower():
                    mat_lib_cached_files += 1
                elif ".bcm" in name:
                    mat_lib_cached_files += 1
        
        return {'FINISHED'}

class LibraryHome(bpy.types.Operator):
    '''Go back'''
    bl_idname = "material.libraryhome"
    bl_label = "Go back"

    def execute(self, context):
        global category_type
        
        category_type = "none"
        
        return {'FINISHED'}

def libraryCategoryUpdate():
    print("Updating Material Category.")
    #Check if the category is None
    if bpy.context.scene.mat_lib_material_category != "None0":
        #Selected category is not None; select category.        
        
        global category_contents
        global category_name
        global category_filename
        global category_materials
                
        global material_names
        global material_filenames
        global material_contributors
        global material_ratings
        global material_fireflies
        global material_speeds
        global material_complexities
        global material_scripts
        global material_images
        
        global current_material_number
                
        global category_type
    
        i = 0
        while i < len(category_enum_items):
            if category_enum_items[i][0] == bpy.context.scene.mat_lib_material_category:
                #Set category filename for refresh button
                category_filename = mat_lib_category_filenames[i - 1]
                #Set category name for header
                category_name = mat_lib_category_names[i - 1]
                category_index = i - 1
            i = i + 1
        
        if True:
            current_material_number = -1
            
            material_names = []
            material_filenames = []
            material_contributors = []
            material_ratings = []
            material_fireflies = []
            material_speeds = []
            material_complexities = []
            material_scripts = []
            material_images = []
            
            for mat in library_data[category_index].materials:
                #Get material names
                material_names.append(mat.name)
                #Get material filenames
                material_filenames.append(mat.href)
                #Get material contributors
                material_contributors.append(mat.contrib)
                #Get material ratings
                material_ratings.append(mat.stars)
                #Get material firefly levels
                material_fireflies.append(mat.fireflies)
                #Get material render speeds
                material_speeds.append(mat.speed)
                #Get material complexities
                material_complexities.append(mat.complexity)
                #Get material image textures
                material_images.append(mat.images)
                #Get material OSL scripts
                material_scripts.append(mat.scripts)
            
            #Set amount of materials in selected category
            category_materials = len(material_names)
        
            category_type = "category"
        
        elif "parent" == "parent":
            current_material_number = -1
            #REWRITE, REWRITE...
            #Find category names
            #parent_category_names = safeEval(parent_category_contents[(parent_category_contents.index('[names]') + 7):parent_category_contents.index('[/names]')])
            #
            #Get category filenames
            #parent_category_filenames = safeEval(parent_category_contents[(parent_category_contents.index('[filenames]') + 11):parent_category_contents.index('[/filenames]')])
            #
            #Set parent category name for header
            #parent_category_name = self.name
            #
            #Set parent category filename
            #parent_category_filename = self.filename
            #
            #Set amount of categories in parent category
            #parent_category_categories = len(parent_category_names)
            
            category_type = "parent"
        
        elif "subcategory" == "subcategory":
            current_material_number = -1
            #ANOTHER REWRITE.
            #Get material names
            #material_names = safeEval(category_contents[(category_contents.index("[names]") + 7):category_contents.index("[/names]")])
            #
            #Get material filenames
            #material_filenames = safeEval(category_contents[(category_contents.index("[filenames]") + 11):category_contents.index("[/filenames]")])
            #
            #Get material contributors
            #material_contributors = safeEval(category_contents[(category_contents.index("[contributors]") + 14):category_contents.index("[/contributors]")])
            #
            #Get material ratings
            #material_ratings = safeEval(category_contents[(category_contents.index("[ratings]") + 9):category_contents.index("[/ratings]")])
            #
            #Set category name for header
            #category_name = self.name
            #
            #Set category filename for refresh button
            #category_filename = self.filename
            
            #Set amount of materials in selected category
            #category_materials = len(material_names)
            
            category_type = "subcategory"
        
        else:
            self.report({'ERROR'}, "Invalid category! See console for details.")
            print ("Invalid category!")
            print (category_contents)
    else:
        #Selected category is None
        parent_category_contents = "None"
        category_contents = "None"
        current_material_number = -1
        category_type = "none"

class ViewMaterial(bpy.types.Operator):
    '''View material details'''
    bl_idname = "material.libraryviewmaterial"
    bl_label = "view material details"
    material = bpy.props.IntProperty()
    
    def execute(self, context):
        global current_material_number
        global current_material_cached
        global current_material_previewed
        
        if current_material_number == self.material:
            if current_material_previewed:
                current_material_previewed = True
            else:
                current_material_previewed = False
        else:
            current_material_previewed = False
        
        current_material_number = self.material
        current_material_cached = False
        
        if self.material == -1:
            return {'FINISHED'}
        
        if library == "composite":
            if os.path.exists(mat_lib_folder + os.sep + mat_lib_host + os.sep + "cycles" + os.sep + category_filename + os.sep + material_filenames[self.material] + ".bcm"):
                current_material_cached = True
        elif library != "bundled":
            if os.path.exists(mat_lib_folder + os.sep + mat_lib_host + os.sep + library + os.sep + "cycles" + os.sep + category_filename + os.sep + material_filenames[self.material] + ".bcm"):
                current_material_cached = True
        
        if context.scene.mat_lib_auto_preview == True:
            print("Auto-download previews on.")
            bpy.ops.material.librarypreview(name=material_names[self.material], filename=material_filenames[self.material])
            self.report({preview_message[0]}, preview_message[1])
        elif working_mode == "offline":
            bpy.ops.material.librarypreview(name=material_names[self.material], filename=material_filenames[self.material])
            self.report({preview_message[0]}, preview_message[1])
        elif library == "composite":
            if os.path.exists(mat_lib_folder + os.sep + mat_lib_host + os.sep + "cycles" + os.sep  + category_filename + os.sep + material_filenames[self.material] + ".jpg"):
                bpy.ops.material.librarypreview(name=material_names[self.material], filename=material_filenames[self.material])
                self.report({preview_message[0]}, preview_message[1])
        else:
            if os.path.exists(mat_lib_folder + os.sep + mat_lib_host + os.sep + library + os.sep + "cycles" + os.sep  + category_filename + os.sep + material_filenames[self.material] + ".jpg"):
                bpy.ops.material.librarypreview(name=material_names[self.material], filename=material_filenames[self.material])
                self.report({preview_message[0]}, preview_message[1])
        return {'FINISHED'}

class MaterialDetailView(bpy.types.Operator):
    '''Change detail view'''
    bl_idname = "material.librarydetailview"
    bl_label = "change detail view"
    mode = bpy.props.StringProperty()

    def execute(self, context):
        global material_detail_view
        
        if self.mode == "NEXT":
            if material_detail_view == "RENDER":
                material_detail_view = "DATA"
        else:
            if material_detail_view == "DATA":
                material_detail_view = "RENDER"
        return {'FINISHED'}
            

class LibraryClearCache(bpy.types.Operator):
    '''Delete active library's cached previews and/or materials'''
    bl_idname = "material.libraryclearcache"
    bl_label = "delete cached previews and materials"
    
    def execute(self, context):
        global mat_lib_cached_files
        
        
        if library == "bundled":
            self.report({'ERROR'}, "The bundled library is local only and contains no cached online data.")
            return {'CANCELLED'}
        if library == "composite":
            for root, dirs, files in os.walk(mat_lib_folder + os.sep + mat_lib_host + os.sep + "cycles" + os.sep):
                for name in files:
                    if name[-4:].lower() == ".jpg":
                        print("Deleting \"" + os.path.join(root, name) + "\".")
                        os.remove(os.path.join(root, name))
                    elif name[-4:].lower() == ".png":
                        print("Deleting \"" + os.path.join(root, name) + "\".")
                        os.remove(os.path.join(root, name))
                    elif name[-4:].lower() == ".osl":
                        print("Deleting \"" + os.path.join(root, name) + "\".")
                        os.remove(os.path.join(root, name))
                    elif name[-4:].lower() == ".oso":
                        print("Deleting \"" + os.path.join(root, name) + "\".")
                        os.remove(os.path.join(root, name))
                    elif name[-4:].lower() == ".bcm":
                        print("Deleting \"" + os.path.join(root, name) + "\".")
                        os.remove(os.path.join(root, name))
        else:
            for root, dirs, files in os.walk(mat_lib_folder + os.sep + mat_lib_host + os.sep + library + os.sep + "cycles" + os.sep):
                for name in files:
                    if name[-4:].lower() == ".jpg":
                        print("Deleting \"" + os.path.join(root, name) + "\".")
                        os.remove(os.path.join(root, name))
                    elif name[-4:].lower() == ".png":
                        print("Deleting \"" + os.path.join(root, name) + "\".")
                        os.remove(os.path.join(root, name))
                    elif name[-4:].lower() == ".osl":
                        print("Deleting \"" + os.path.join(root, name) + "\".")
                        os.remove(os.path.join(root, name))
                    elif name[-4:].lower() == ".oso":
                        print("Deleting \"" + os.path.join(root, name) + "\".")
                        os.remove(os.path.join(root, name))
                    elif name[-4:].lower() == ".bcm":
                        print("Deleting \"" + os.path.join(root, name) + "\".")
                        os.remove(os.path.join(root, name))
        
        if library == "":
            return {'FINISHED'}
        elif library == "bundled":
            return {'FINISHED'}
        elif library == "composite":
            cached_data_path = mat_lib_folder + os.sep + mat_lib_host + os.sep + "cycles" + os.sep
        else:
            cached_data_path = mat_lib_folder + os.sep + mat_lib_host + os.sep + library + os.sep + "cycles" + os.sep
        mat_lib_cached_files = 0
        for root, dirs, files in os.walk(cached_data_path):
            for name in files:
                if ".jpg" in name:
                    mat_lib_cached_files += 1
                elif ".bcm" in name:
                    mat_lib_cached_files += 1
        
        self.report({'INFO'}, "Preview cache cleared.")
        return {'FINISHED'}
    
class LibraryPreview(bpy.types.Operator):
    '''Download preview'''
    bl_idname = "material.librarypreview"
    bl_label = "preview material"
    name = bpy.props.StringProperty()
    filename = bpy.props.StringProperty()
        
    def execute(self, context):
        global parent_category_filename
        global category_filename
        global preview_message
        global library
        global current_material_previewed
        
        #Check for a cached preview
        if library == "bundled":
            image_path = mat_lib_folder + os.sep + "bundled" + os.sep + "cycles" + os.sep  + category_filename + os.sep + self.filename + ".jpg"
        elif library == "composite":
            image_path = mat_lib_folder + os.sep + mat_lib_host + os.sep + "cycles" + os.sep  + category_filename + os.sep + self.filename + ".jpg"
        else:
            image_path = mat_lib_folder + os.sep + mat_lib_host + os.sep + library + os.sep + "cycles" + os.sep  + category_filename + os.sep + self.filename + ".jpg"
        
        if os.path.exists(image_path):
            #Cached preview exists
            cached_image = open(image_path, 'r+b')
            response = cached_image.read()
            cached_image.close()
            f = open(mat_lib_folder + os.sep + "mat_lib_preview_image.jpg", 'w+b')
            f.write(response)
            f.close()
            
        elif working_mode == "online":
            #This preview doesn't exist yet; let's download it.
            connection = http.client.HTTPConnection(mat_lib_host)
            connection.request("GET", mat_lib_location + "cycles/" + category_filename + "/" + self.filename + ".jpg")
            response = connection.getresponse().read()
            f = open(mat_lib_folder + os.sep + "mat_lib_preview_image.jpg", 'w+b')
            f.write(response)
            f.close()
            
            #Cache this preview
            f = open(image_path, 'w+b')
            f.write(response)
            f.close()
            
        else:
            self.report({'WARNING'}, "Preview does not exist; cannot download in offline mode.")
            preview_message = ['WARNING', "Preview does not exist; cannot download in offline mode."]
            return {'CANCELLED'}
        
        #Check if has texture
        if bpy.data.images.find("mat_lib_preview_image.jpg") == -1:
            bpy.ops.image.open(filepath=os.path.join(mat_lib_folder, "mat_lib_preview_image.jpg"))
        
        if "mat_lib_preview_texture" not in bpy.data.textures:
             bpy.data.textures.new("mat_lib_preview_texture", "IMAGE")
        
        if bpy.data.textures["mat_lib_preview_texture"].image != bpy.data.images["mat_lib_preview_image.jpg"]:
            bpy.data.textures["mat_lib_preview_texture"].image = bpy.data.images["mat_lib_preview_image.jpg"]
        
        if bpy.data.images["mat_lib_preview_image.jpg"].filepath != os.path.join(mat_lib_folder, "mat_lib_preview_image.jpg"):
            bpy.data.images["mat_lib_preview_image.jpg"].filepath != os.path.join(mat_lib_folder, "mat_lib_preview_image.jpg")
            
        #Do everything possible to get Blender to reload the preview.
        bpy.data.images["mat_lib_preview_image.jpg"].reload()
        bpy.ops.wm.redraw_timer()
        bpy.data.scenes[bpy.context.scene.name].update()
        bpy.data.scenes[bpy.context.scene.name].frame_set(bpy.data.scenes[bpy.context.scene.name].frame_current)
        
        self.report({'INFO'}, "Preview applied.")
        preview_message = ['INFO', "Preview applied."]
        current_material_previewed = True
        
        return {'FINISHED'}

class AddLibraryMaterial(bpy.types.Operator):
    '''Add material to scene'''
    bl_idname = "material.libraryadd"
    bl_label = "add material to scene"
    mat_name = bpy.props.StringProperty()
    filename = bpy.props.StringProperty()
    open_location = bpy.props.StringProperty()
    text_block = bpy.props.StringProperty()
    
    def execute(self, context):
        global material_file_contents
        global library
        global node_message
        global current_material_cached
        
        if not bpy.context.active_object:
            self.report({'ERROR'}, "No object selected!")
        if self.open_location == "" and self.text_block == "":
            if library == "composite" and os.path.exists(mat_lib_folder + os.sep + mat_lib_host + os.sep + "cycles" + os.sep + category_filename + os.sep + self.filename + ".bcm"):
                bcm_file = open(mat_lib_folder + os.sep + mat_lib_host + os.sep + "cycles" + os.sep + category_filename + os.sep + self.filename + ".bcm", mode="r", encoding="UTF-8")
                material_file_contents = ""
                material_file_contents = bcm_file.read()
                bcm_file.close()
            elif library != "bundled" and os.path.exists(mat_lib_folder + os.sep + mat_lib_host + os.sep + library + os.sep + "cycles" + os.sep + category_filename + os.sep + self.filename + ".bcm"):
                bcm_file = open(mat_lib_folder + os.sep + mat_lib_host + os.sep + library + os.sep + "cycles" + os.sep + category_filename + os.sep + self.filename + ".bcm", mode="r", encoding="UTF-8")
                material_file_contents = ""
                material_file_contents = bcm_file.read()
                bcm_file.close()
            elif library == "bundled" and os.path.exists(mat_lib_folder + os.sep + "bundled" + os.sep + "cycles" + os.sep + category_filename + os.sep + self.filename + ".bcm"):
                bcm_file = open(mat_lib_folder + os.sep + "bundled" + os.sep + "cycles" + os.sep + category_filename + os.sep + self.filename + ".bcm", mode="r", encoding="UTF-8")
                material_file_contents = bcm_file.read()
                bcm_file.close()
            elif working_mode == "online":
                connection = http.client.HTTPConnection(mat_lib_host)
                connection.request("GET", mat_lib_location + "cycles/" + category_filename + "/" + self.filename + ".bcm")
                response = connection.getresponse().read()
                
                #Check file for validitity
                if '<?xml version="1.0" encoding="UTF-8"?>' not in str(response)[2:40]:
                    self.report({'ERROR'}, "Material file is either outdated or invalid.")
                    self.filename = ""
                    return {'CANCELLED'}
                
                #Cache material
                if library == "composite":
                    bcm_file = open(mat_lib_folder + os.sep + mat_lib_host + os.sep + "cycles" + os.sep + category_filename + os.sep + self.filename + ".bcm", mode="w+b")
                    bcm_file.write(response)
                    bcm_file.close()
                else:
                    bcm_file = open(mat_lib_folder + os.sep + mat_lib_host + os.sep + library + os.sep + "cycles" + os.sep + category_filename + os.sep + self.filename + ".bcm", mode="w+b")
                    bcm_file.write(response)
                    bcm_file.close()
                
                material_file_contents = str(response)
            else:
                self.report({'ERROR'}, "Material is not cached; cannot download in offline mode!")
                return {'CANCELLED'}
            print (material_file_contents)
            mat_name = self.mat_name
        elif self.open_location is not "":
            if ".bcm" in self.open_location:
                bcm_file = open(self.open_location, mode="r", encoding="UTF-8")
                material_file_contents = bcm_file.read()
                bcm_file.close()
                
                #Check file for validitity
                if '<?xml version="1.0" encoding="UTF-8"?>' not in material_file_contents:
                    self.open_location = ""
                    self.report({'ERROR'}, "Material file is either outdated or invalid.")
                    return {'CANCELLED'}
                mat_name = ""
                for word in self.open_location.split(os.sep)[-1][:-4].split("_"):
                    if mat_name is not "":
                        mat_name += " "
                    mat_name += word.capitalize()
            else:
                self.report({'ERROR'}, "Not a .bcm file.")
                self.open_location = ""
                return {'CANCELLED'}
        else:
            if self.text_block in bpy.data.texts:
                #Read from a text datablock
                material_file_contents = bpy.data.texts[self.text_block].as_string()
            else:
                self.report({'ERROR'}, "Requested text block does not exist.")
                self.text_block = ""
                return {'CANCELLED'}
                
            #Check file for validitity
            if '<?xml version="1.0" encoding="UTF-8"?>' not in material_file_contents[0:38]:
                self.report({'ERROR'}, "Material data is either outdated or invalid.")
                self.text_block = ""
                return {'CANCELLED'}
            mat_name = ""
            
            separator = ""
            if context.scene.mat_lib_bcm_name is "":
                separator = ""
                if "_" in self.text_block:
                    separator = "_"
                elif "-" in self.text_block:
                    separator = "-"
                elif " " in self.text_block:
                    separator = " "
                    
                if separator is not "":
                    for word in self.text_block.split(separator):
                        if mat_name is not "":
                            mat_name += " "
                        mat_name += word.capitalize()
                else:
                    mat_name = self.text_block
            else:
                mat_name = context.scene.mat_lib_bcm_name
        
        if '<?xml version="1.0" encoding="UTF-8"?>' in material_file_contents[0:40]:
            material_file_contents = material_file_contents[material_file_contents.index("<material"):(material_file_contents.rindex("</material>") + 11)]
        else:
            self.mat_name = ""
            self.filename = ""
            self.text_block = ""
            self.open_location = ""
            self.report({'ERROR'}, "Material file is either invalid or outdated.")
            print(material_file_contents)
            return {'CANCELLED'}
        
        #Create new material
        new_mat = bpy.data.materials.new(mat_name)
        new_mat.use_nodes = True
        new_mat.node_tree.nodes.clear()
        
        #Parse file
        dom = xml.dom.minidom.parseString(material_file_contents)
        
        #Create internal OSL scripts
        scripts = dom.getElementsByTagName("script")
        osl_scripts = []
        for s in scripts:
            osl_datablock = bpy.data.texts.new(name=s.attributes['name'].value)
            osl_text = s.toxml()[s.toxml().index(">"):s.toxml().rindex("<")]
            osl_text = osl_text[1:].replace("<br/>","\n").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", "\"").replace("&amp;", "&")
            osl_datablock.write(osl_text)
            osl_scripts.append(osl_datablock)
        
        #Add nodes
        nodes = dom.getElementsByTagName("node")
        addNodes(nodes, new_mat)
        if node_message:
            self.report({node_message[0]}, node_message[1])
            node_message = []
            self.mat_name = ""
            self.filename = ""
            self.open_location = ""
            self.text_block = ""
            return {'CANCELLED'}
            
        #Create links
        links = dom.getElementsByTagName("link")
        createLinks(links, new_mat)
        
        m = dom.getElementsByTagName("material")[0]
        
        #Set viewport color
        new_mat.diffuse_color = color(m.attributes["view_color"].value)
            
        #Set sample-as-lamp-ness
        if m.attributes["sample_lamp"].value == "True":
            sample_lamp = True
        else:
            sample_lamp = False
        new_mat.cycles.sample_as_light = sample_lamp
        
        self.mat_name = ""
        self.filename = ""
        self.open_location = ""
        self.text_block = ""
        self.report({'INFO'}, "Material added.")
        current_material_cached = True
        
        return {'FINISHED'}

class ApplyLibraryMaterial(bpy.types.Operator):
    '''Apply to active material'''
    bl_idname = "material.libraryapply"
    bl_label = "Apply to active material"
    mat_name = bpy.props.StringProperty()
    filename = bpy.props.StringProperty()
    open_location = bpy.props.StringProperty()
    text_block = bpy.props.StringProperty()
    
    def execute(self, context):
        global material_file_contents
        global library
        global node_message
        global current_material_cached
        global osl_scripts
        
        mat_name = ""
        material_file_contents = ""
        if not bpy.context.active_object:
            self.report({'ERROR'}, "No object selected!")
            return {'CANCELLED'}
        if self.filename is not "":
            if library == "composite" and os.path.exists(mat_lib_folder + os.sep + mat_lib_host + os.sep + "cycles" + os.sep + category_filename + os.sep + self.filename + ".bcm"):
                bcm_file = open(mat_lib_folder + os.sep + mat_lib_host + os.sep + "cycles" + os.sep + category_filename + os.sep + self.filename + ".bcm", mode="r", encoding="UTF-8")
                material_file_contents = bcm_file.read()
                bcm_file.close()
            elif library != "bundled" and os.path.exists(mat_lib_folder + os.sep + mat_lib_host + os.sep + library + os.sep + "cycles" + os.sep + category_filename + os.sep + self.filename + ".bcm"):
                bcm_file = open(mat_lib_folder + os.sep + mat_lib_host + os.sep + library + os.sep + "cycles" + os.sep + category_filename + os.sep + self.filename + ".bcm", mode="r", encoding="UTF-8")
                material_file_contents = bcm_file.read()
                bcm_file.close()
            elif library == "bundled" and os.path.exists(mat_lib_folder + os.sep + "bundled" + os.sep + "cycles" + os.sep + category_filename + os.sep + self.filename + ".bcm"):
                bcm_file = open(mat_lib_folder + os.sep + "bundled" + os.sep + "cycles" + os.sep + category_filename + os.sep + self.filename + ".bcm", mode="r", encoding="UTF-8")
                material_file_contents = bcm_file.read()
                bcm_file.close()
            elif working_mode == "online":
                connection = http.client.HTTPConnection(mat_lib_host)
                connection.request("GET", mat_lib_location + "cycles/" + category_filename + "/" + self.filename + ".bcm")
                response = connection.getresponse().read()
                
                #Check file for validitity
                if '<?xml version="1.0" encoding="UTF-8"?>' not in str(response)[2:40]:
                    self.report({'ERROR'}, "Material file is either outdated or invalid.")
                    self.mat_name = ""
                    self.filename = ""
                    return {'CANCELLED'}
                
                #Cache material
                if library == "composite":
                    bcm_file = open(mat_lib_folder + os.sep + mat_lib_host + os.sep + "cycles" + os.sep + category_filename + os.sep + self.filename + ".bcm", mode="w+b")
                    bcm_file.write(response)
                    bcm_file.close()
                else:
                    bcm_file = open(mat_lib_folder + os.sep + mat_lib_host + os.sep + library + os.sep + "cycles" + os.sep + category_filename + os.sep + self.filename + ".bcm", mode="w+b")
                    bcm_file.write(response)
                    bcm_file.close()
                
                material_file_contents = str(response)
            else:
                self.report({'ERROR'}, "Material is not cached; cannot download in offline mode!")
                self.mat_name = ""
                self.filename = ""
                return {'CANCELLED'}
            mat_name = self.mat_name
        elif self.open_location is not "":
            if ".bcm" in self.open_location:
                material_file_contents = ""
                bcm_file = open(self.open_location, mode="r", encoding="UTF-8")
                material_file_contents = bcm_file.read()
                bcm_file.close()
                
                mat_name = ""
                for word in self.open_location.split(os.sep)[-1][:-4].split("_"):
                    if mat_name is not "":
                        mat_name += " "
                    mat_name += word.capitalize()
            else:
                self.open_location = ""
                self.report({'ERROR'}, "Not a .bcm file.")
                return {'CANCELLED'}
        else:
            if self.text_block in bpy.data.texts:
                #Read from a text datablock
                material_file_contents = ""
                material_file_contents = bpy.data.texts[self.text_block].as_string()
            else:
                self.report({'ERROR'}, "Requested text block does not exist.")
                self.text_block = "";
                return {'CANCELLED'}
            
            if context.scene.mat_lib_bcm_name is "":
                separator = ""
                if "_" in self.text_block:
                    separator = "_"
                elif "-" in self.text_block:
                    separator = "-"
                elif " " in self.text_block:
                    separator = " "
                    
                if separator is not "":
                    for word in self.text_block.split(separator):
                        if mat_name is not "":
                            mat_name += " "
                        mat_name += word.capitalize()
                else:
                    mat_name = self.text_block
            else:
                mat_name = context.scene.mat_lib_bcm_name
        
        
        if context.active_object.active_material:
            context.active_object.active_material.name = mat_name
        else:
            new_material = bpy.data.materials.new(mat_name)
            if len(context.active_object.material_slots.keys()) is 0:
                bpy.ops.object.material_slot_add()
            context.active_object.material_slots[context.active_object.active_material_index].material = new_material
        
        #Prepare material for new nodes
        context.active_object.active_material.use_nodes = True
        context.active_object.active_material.node_tree.nodes.clear()
        
        if '<?xml version="1.0" encoding="UTF-8"?>' in material_file_contents[0:40]:
            material_file_contents = material_file_contents[material_file_contents.index("<material"):(material_file_contents.rindex("</material>") + 11)]
        else:
            self.mat_name = ""
            self.filename = ""
            self.text_block = ""
            self.open_location = ""
            self.report({'ERROR'}, "Material file is either invalid or outdated.")
            print(material_file_contents)
            return {'CANCELLED'}
        
        #Parse file
        dom = xml.dom.minidom.parseString(material_file_contents)
        
        #Create internal OSL scripts
        scripts = dom.getElementsByTagName("script")
        osl_scripts = []
        for s in scripts:
            osl_datablock = bpy.data.texts.new(name=s.attributes['name'].value)
            osl_text = s.toxml()[s.toxml().index(">"):s.toxml().rindex("<")]
            osl_text = osl_text[1:].replace("<br/>","\n").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", "\"").replace("&amp;", "&")
            osl_datablock.write(osl_text)
            osl_scripts.append(osl_datablock)
        
        #Add nodes
        nodes = dom.getElementsByTagName("node")
        addNodes(nodes, context.active_object.active_material)
        if node_message:
            self.report({node_message[0]}, node_message[1])
            node_message = []
            self.mat_name = ""
            self.filename = ""
            self.open_location = ""
            self.text_block = ""
            return {'CANCELLED'}
            
        #Create links
        links = dom.getElementsByTagName("link")
        createLinks(links, context.active_object.active_material)
        
        m = dom.getElementsByTagName("material")[0]
        
        #Set viewport color
        context.active_object.active_material.diffuse_color = color(m.attributes["view_color"].value)
            
        #Set sample-as-lamp-ness
        if boolean(m.attributes["sample_lamp"].value):
            sample_lamp = True
        else:
            sample_lamp = False
        context.active_object.active_material.cycles.sample_as_light = sample_lamp
        
        self.mat_name = ""
        self.filename = ""
        self.open_location = ""
        self.text_block = ""
        self.report({'INFO'}, "Material applied.")
        current_material_cached = True
        
        return {'FINISHED'}

class CacheLibraryMaterial(bpy.types.Operator):
    '''Cache material to disk'''
    bl_idname = "material.librarycache"
    bl_label = "cache material to disk"
    filename = bpy.props.StringProperty()
    
    def execute(self, context):
        global material_file_contents
        global current_material_cached
        
        if working_mode == "online":
            connection = http.client.HTTPConnection(mat_lib_host)
            connection.request("GET", mat_lib_location + "cycles/" + category_filename + "/" + self.filename + ".bcm")
            response = connection.getresponse().read()
        else:
            self.report({'ERROR'}, "Cannot cache material in offline mode.")
            return {'CANCELLED'}
        
        material_file_contents = str(response)
        if '<?xml version="1.0" encoding="UTF-8"?>' in material_file_contents[2:40]:
            material_file_contents = material_file_contents[material_file_contents.index("<material"):(material_file_contents.rindex("</material>") + 11)]
        else:
            self.report({'ERROR'}, "Invalid material file.")
            print(material_file_contents)
            return {'CANCELLED'}
        
        #Parse file
        dom = xml.dom.minidom.parseString(material_file_contents)
        
        #Create external OSL scripts and cache image textures
        nodes = dom.getElementsByTagName("node")
        for node in nodes:
            node_data = node.attributes
            if node_data['type'].value == "TEX_IMAGE":
                if node_data['image'].value:
                    if "file://" in node_data['image'].value:
                        self.report({'ERROR'}, "Cannot cache image texture located at %s." % node_data['image'].value)
                    elif "http://" in node_data['image'].value:
                        self.report({'ERROR'}, "Cannot cache image texture hosted at %s." % node_data['image'].value)
                    else:
                        ext = "." + node_data['image'].value.split(".")[-1]
                        image_name = node_data['image'].value[:-4]
                        
                        if ext.lower() != ".jpg" and ext.lower() != ".png":
                            node_message = ['ERROR', "The image file referenced by this image texture node is not .jpg or .png; not downloading."]
                            return
                            
                        if library == "composite" and os.path.exists(os.path.join(mat_lib_folder, mat_lib_host, "cycles", "textures", image_name + ext)):
                            image_filepath = os.path.join(mat_lib_folder, mat_lib_host, "cycles", "textures", image_name + ext)
                        elif library != "bundled" and os.path.exists(os.path.join(mat_lib_folder, mat_lib_host, library, "cycles", "textures", image_name + ext)):
                            image_filepath = os.path.join(mat_lib_folder, mat_lib_host, library, "cycles", "textures", image_name + ext)
                        elif library == "bundled" and os.path.exists(os.path.join(mat_lib_folder, "bundled", "cycles", "textures", image_name + ext)):
                            image_filepath = os.path.join(mat_lib_folder, "bundled", "cycles", "textures", image_name + ext)
                        elif working_mode == "online":
                            connection = http.client.HTTPConnection(mat_lib_host)
                            connection.request("GET", mat_lib_location + "cycles/textures/" + image_name + ext)
                            response = connection.getresponse().read()
                            
                            #Cache image texture
                            if library == "composite":
                                image_filepath = os.path.join(mat_lib_folder, mat_lib_host, "cycles", "textures", image_name + ext)
                                image_file = open(image_filepath, mode="w+b")
                                image_file.write(response)
                                image_file.close()
                            else:
                                image_filepath = os.path.join(mat_lib_folder, mat_lib_host, library, "cycles", "textures", image_name + ext)
                                image_file = open(image_filepath, mode="w+b")
                                image_file.write(response)
                                image_file.close()
                        else:
                            node_message = ['ERROR', "The image texture, \"%s\", is not cached; cannot download in offline mode." % (image_name + ext)]
                            image_filepath = ""
            elif node_data['type'].value == "SCRIPT":
                if node_data['script'].value:
                    if "file://" in node_data['script'].value:
                        self.report({'ERROR'}, "Cannot cache OSL script located at %s." % node_data['script'].value)
                    elif "http://" in node_data['script'].value:
                        self.report({'ERROR'}, "Cannot cache OSL script hosted at %s." % node_data['script'].value)
                    else:
                        ext = "." + node_data['script'].value.split(".")[-1]
                        script_name = node_data['script'].value[:-4]
                        
                        if ext.lower() != ".osl" and ext.lower() != ".oso":
                            node_message = ['ERROR', "The OSL script file referenced by this script node is not .osl or .oso; not downloading."]
                            return
                            
                        if library == "composite" and os.path.exists(os.path.join(mat_lib_folder, mat_lib_host, "cycles", "scripts", script_name + ext)):
                            script_filepath = os.path.join(mat_lib_folder, mat_lib_host, "cycles", "scripts", script_name + ext)
                        elif library != "bundled" and os.path.exists(os.path.join(mat_lib_folder, mat_lib_host, library, "cycles", "scripts", script_name + ext)):
                            script_filepath = os.path.join(mat_lib_folder, mat_lib_host, library, "cycles", "scripts", script_name + ext)
                        elif library == "bundled" and os.path.exists(os.path.join(mat_lib_folder, "bundled", "cycles", "scripts", script_name + ext)):
                            script_filepath = os.path.join(mat_lib_folder, "bundled", "cycles", "scripts", script_name + ext)
                        elif working_mode == "online":
                            connection = http.client.HTTPConnection(mat_lib_host)
                            connection.request("GET", mat_lib_location + "cycles/scripts/" + script_name + ext)
                            response = connection.getresponse().read()
                            
                            #Cache image texture
                            if library == "composite":
                                script_filepath = os.path.join(mat_lib_folder, mat_lib_host, "cycles", "scripts", script_name + ext)
                                script_file = open(script_filepath, mode="w+b")
                                script_file.write(response)
                                script_file.close()
                            else:
                                script_filepath = os.path.join(mat_lib_folder, mat_lib_host, library, "cycles", "scripts", script_name + ext)
                                script_file = open(script_filepath, mode="w+b")
                                script_file.write(response)
                                script_file.close()
                        else:
                            node_message = ['ERROR', "The OSL script, \"%s\", is not cached; cannot download in offline mode." % (script_name + ext)]
                            script_filepath = ""
                    
        
        if library == "composite":
            bcm_file = open(mat_lib_folder + os.sep + mat_lib_host + os.sep + "cycles" + os.sep + category_filename + os.sep + self.filename + ".bcm", mode="w+b")
            bcm_file.write(response)
            bcm_file.close()
        elif library != "bundled":
            bcm_file = open(mat_lib_folder + os.sep + mat_lib_host + os.sep + library + os.sep + "cycles" + os.sep + category_filename + os.sep + self.filename + ".bcm", mode="w+b")
            bcm_file.write(response)
            bcm_file.close()
        else:
            self.report({'ERROR'}, "Cannot cache materials from this library.")
            return {'CANCELLED'}
            
        current_material_cached = True
        self.report({'INFO'}, "Material cached.")
        return {'FINISHED'}

class SaveLibraryMaterial(bpy.types.Operator, ExportHelper):
    '''Save material to disk'''
    bl_idname = "material.librarysave"
    bl_label = "Save material to disk"
    filepath = bpy.props.StringProperty()
    filename = bpy.props.StringProperty()
    
    #ExportHelper uses this
    filename_ext = ".bcm"

    filter_glob = bpy.props.StringProperty(
            default="*.bcm",
            options={'HIDDEN'},
            )
    
    def execute(self, context):
        global material_file_contents
        global save_filename
        global current_material_cached
        
        if library == "composite" and os.path.exists(mat_lib_folder + os.sep + mat_lib_host + os.sep + "cycles" + os.sep + category_filename + os.sep + save_filename):
            bcm_file = open(mat_lib_folder + os.sep + mat_lib_host + os.sep + "cycles" + os.sep + category_filename + os.sep + self.filename, mode="r+b")
            response = bcm_file.read()
            bcm_file.close()
        elif library != "bundled" and os.path.exists(mat_lib_folder + os.sep + mat_lib_host + os.sep + library + os.sep + "cycles" + os.sep + category_filename + os.sep + save_filename):
            bcm_file = open(mat_lib_folder + os.sep + mat_lib_host + os.sep + library + os.sep + "cycles" + os.sep + category_filename + os.sep + self.filename, mode="r+b")
            response = bcm_file.read()
            bcm_file.close()
        elif library == "bundled" and os.path.exists(mat_lib_folder + os.sep + "bundled" + os.sep + "cycles" + os.sep + category_filename + os.sep + save_filename):
            bcm_file = open(mat_lib_folder + os.sep + "bundled" + os.sep + "cycles" + os.sep + category_filename + os.sep + self.filename, mode="r+b")
            response = bcm_file.read()
            bcm_file.close()
        elif working_mode == "online":
            connection = http.client.HTTPConnection(mat_lib_host)
            connection.request("GET", mat_lib_location + "cycles/" + category_filename + "/" + self.filename)
            response = connection.getresponse().read()
            
            #Cache material
            if library == "composite":
                bcm_file = open(mat_lib_folder + os.sep + mat_lib_host + os.sep + "cycles" + os.sep + category_filename + os.sep + self.filename, mode="w+b")
                bcm_file.write(response)
                bcm_file.close()
            else:
                bcm_file = open(mat_lib_folder + os.sep + mat_lib_host + os.sep + library + os.sep + "cycles" + os.sep + category_filename + os.sep + self.filename, mode="w+b")
                bcm_file.write(response)
                bcm_file.close()
        else:
            self.report({'ERROR'}, "Material is not cached; cannot download in offline mode.")
            return {'FINISHED'}
        
        material_file_contents = str(response)
        
        bcm_file = open(self.filepath, mode="w+b")
        bcm_file.write(response)
        bcm_file.close()
        
        if '<?xml version="1.0" encoding="UTF-8"?>' in material_file_contents[0:40]:
            material_file_contents = material_file_contents[material_file_contents.index("<material"):(material_file_contents.rindex("</material>") + 11)]
        else:
            self.report({'ERROR'}, "Invalid material file.")
            print(material_file_contents)
            return {'CANCELLED'}
        
        #Parse file
        dom = xml.dom.minidom.parseString(material_file_contents)
        
        bcm_file = open(self.filepath, mode="r", encoding="UTF-8")
        material_file_contents = bcm_file.read()
        bcm_file.close()
        
        #Create external OSL scripts and cache image textures
        nodes = dom.getElementsByTagName("node")
        for node in nodes:
            node_data = node.attributes
            if node_data['type'].value == "TEX_IMAGE":
                if node_data['image'].value:
                    node_attributes = (
                        node_data['image'].value,
                        node_data['source'].value,
                        node_data['color_space'].value,
                        node_data['projection'].value,
                        node_data['loc'].value)
                    original_xml = ("<node type=\"TEX_IMAGE\" image=\"%s\" source=\"%s\" color_space=\"%s\" projection=\"%s\" loc=\"%s\" />" % node_attributes)
                    if "file://" in node_data['image'].value:
                        if os.path.exists(node_data['image'].value[7:]):
                            image_file = open(node_data['image'].value[7:], mode="r+b")
                            image_data = image_file.read()
                            image_file.close()
                            copied_image = open(self.filepath[:-len(self.filename)] + node_data['image'].value.split(os.sep)[-1], mode="w+b")
                            copied_image.write(image_data)
                            copied_image.close()
                            image_location = ("file://" + self.filepath[:-len(self.filename)] + node_data['image'].value.split(os.sep)[-1])
                        else:
                            image_location = ""
                    elif "http://" in node_data['image'].value:
                        self.report({'ERROR'}, "Cannot save image texture hosted at %s." % node_data['image'].value)
                        image_location = ""
                    else:
                        ext = "." + node_data['image'].value.split(".")[-1]
                        image_name = node_data['image'].value[:-4]
                        
                        if ext.lower() != ".jpg" and ext.lower() != ".png":
                            node_message = ['ERROR', "The image file referenced by this image texture node is not .jpg or .png; not downloading."]
                            return
                            
                        if library == "composite" and os.path.exists(os.path.join(mat_lib_folder, mat_lib_host, "cycles", "textures", image_name + ext)):
                            image_filepath = os.path.join(mat_lib_folder, mat_lib_host, "cycles", "textures", image_name + ext)
                        elif library != "bundled" and os.path.exists(os.path.join(mat_lib_folder, mat_lib_host, library, "cycles", "textures", image_name + ext)):
                            image_filepath = os.path.join(mat_lib_folder, mat_lib_host, library, "cycles", "textures", image_name + ext)
                        elif library == "bundled" and os.path.exists(os.path.join(mat_lib_folder, "bundled", "cycles", "textures", image_name + ext)):
                            image_filepath = os.path.join(mat_lib_folder, "bundled", "cycles", "textures", image_name + ext)
                        elif working_mode == "online":
                            connection = http.client.HTTPConnection(mat_lib_host)
                            connection.request("GET", mat_lib_location + "cycles/textures/" + image_name + ext)
                            response = connection.getresponse().read()
                            
                            #Cache image texture
                            if library == "composite":
                                image_filepath = os.path.join(mat_lib_folder, mat_lib_host, "cycles", "textures", image_name + ext)
                                image_file = open(image_filepath, mode="w+b")
                                image_file.write(response)
                                image_file.close()
                            else:
                                image_filepath = os.path.join(mat_lib_folder, mat_lib_host, library, "cycles", "textures", image_name + ext)
                                image_file = open(image_filepath, mode="w+b")
                                image_file.write(response)
                                image_file.close()
                        else:
                            node_message = ['ERROR', "The image texture, \"%s\", is not cached; cannot download in offline mode." % (image_name + ext)]
                            image_filepath = ""
                        image_location = ("file://" + self.filepath[:-len(self.filename)] + node_data['image'].value)
                        
                        if image_filepath:
                            print(image_filepath)
                            image_file = open(image_filepath, mode="r+b")
                            image_data = image_file.read()
                            image_file.close()
                            saved_image = open(self.filepath[:-len(self.filename)] + node_data['image'].value, mode="w+b")
                            saved_image.write(image_data)
                            saved_image.close()
                
                    updated_xml = original_xml.replace(node_data['image'].value, image_location)
                    material_file_contents = material_file_contents.replace(original_xml, updated_xml)
            elif node_data['type'].value == "SCRIPT":
                if node_data['script'].value:
                    node_attributes = (
                        node_data['mode'].value,
                        node_data['script'].value,
                        node_data['loc'].value)
                    original_xml = ("<node type=\"SCRIPT\" mode=\"%s\" script=\"%s\" loc=\"%s\" />" % node_attributes)
                    if "file://" in node_data['script'].value:
                        if os.path.exists(node_data['script'].value[7:]):
                            script_file = open(node_data['script'].value[7:], mode="r+b")
                            script_data = script_file.read()
                            script_file.close()
                            copied_script = open(self.filepath[:-len(self.filename)] + node_data['script'].value.split(os.sep)[-1], mode="w+b")
                            copied_script.write(script_data)
                            copied_script.close()
                            script_location = ("file://" + self.filepath[:-len(self.filename)] + node_data['script'].value.split(os.sep)[-1])
                        else:
                            script_location = ""
                    elif "http://" in node_data['script'].value:
                        self.report({'ERROR'}, "Cannot save OSL script hosted at %s." % node_data['script'].value)
                        script_location = ""
                    else:
                        ext = "." + node_data['script'].value.split(".")[-1]
                        script_name = node_data['script'].value[:-4]
                        
                        if ext.lower() != ".osl" and ext.lower() != ".oso":
                            node_message = ['ERROR', "The OSL script file referenced by this script node is not .osl or .oso; not downloading."]
                            return
                            
                        if library == "composite" and os.path.exists(os.path.join(mat_lib_folder, mat_lib_host, "cycles", "scripts", script_name + ext)):
                            script_filepath = os.path.join(mat_lib_folder, mat_lib_host, "cycles", "scripts", script_name + ext)
                        elif library != "bundled" and os.path.exists(os.path.join(mat_lib_folder, mat_lib_host, library, "cycles", "scripts", script_name + ext)):
                            script_filepath = os.path.join(mat_lib_folder, mat_lib_host, library, "cycles", "scripts", script_name + ext)
                        elif library == "bundled" and os.path.exists(os.path.join(mat_lib_folder, "bundled", "cycles", "scripts", script_name + ext)):
                            script_filepath = os.path.join(mat_lib_folder, "bundled", "cycles", "scripts", script_name + ext)
                        elif working_mode == "online":
                            connection = http.client.HTTPConnection(mat_lib_host)
                            connection.request("GET", mat_lib_location + "cycles/scripts/" + script_name + ext)
                            response = connection.getresponse().read()
                            
                            #Cache OSL script
                            if library == "composite":
                                script_filepath = os.path.join(mat_lib_folder, mat_lib_host, "cycles", "scripts", script_name + ext)
                                script_file = open(script_filepath, mode="w+b")
                                script_file.write(response)
                                script_file.close()
                            else:
                                script_filepath = os.path.join(mat_lib_folder, mat_lib_host, library, "cycles", "scripts", script_name + ext)
                                script_file = open(script_filepath, mode="w+b")
                                script_file.write(response)
                                script_file.close()
                        else:
                            node_message = ['ERROR', "The OSL script, \"%s\", is not cached; cannot download in offline mode." % (script_name + ext)]
                            script_filepath = ""
                        
                        if script_filepath:
                            print(script_filepath)
                            script_file = open(script_filepath, mode="r+b")
                            script_data = script_file.read()
                            script_file.close()
                            saved_script = open(self.filepath[:-len(self.filename)] + node_data['script'].value, mode="w+b")
                            saved_script.write(script_data)
                            saved_script.close()
                    
                    updated_xml = original_xml.replace(node_data['script'].value, script_location)
                    material_file_contents = material_file_contents.replace(original_xml, updated_xml)
        
        bcm_file = open(self.filepath, mode="w", encoding="UTF-8")
        bcm_file.write(material_file_contents)
        bcm_file.close()
        
        self.report({'INFO'}, "Material saved.")
        current_material_cached = True
        
        return {'FINISHED'}

def createLinks(links, mat):
    node_tree = mat.node_tree
    for dom_link in links:
        link = {
    "to": int(dom_link.attributes['to'].value),
    "input": int(dom_link.attributes['input'].value),
    "from": int(dom_link.attributes['from'].value),
    "output": int(dom_link.attributes['output'].value)}
        node_tree.links.new(
    node_tree.nodes[link["to"]].inputs[link["input"]],
    node_tree.nodes[link["from"]].outputs[link["output"]])

def addNodes(nodes, mat):
    global node_message
    global osl_scripts
    
    for dom_node in nodes:
        node_type = dom_node.attributes['type'].value
        loc = dom_node.attributes['loc'].value
        node_location = [int(loc[:loc.index(",")]), int(loc[(loc.index(",") + 1):])]
        node_tree = mat.node_tree
        node_data = dom_node.attributes
        
        #Below here checks the type of the node and adds the correct type
        
        #INPUT TYPES
        #This is totally crafty, but some of these nodes actually
        # store their values as their output's default value!
        if node_type == "ATTRIBUTE":
            print ("ATTRIBUTE")
            node = node_tree.nodes.new(node_type)
            node.attribute_name = node_data['attribute'].value
        
        elif node_type == "CAMERA":
            print ("CAMERA")
            node = node_tree.nodes.new(node_type)
        
        elif node_type == "FRESNEL":
            print ("FRESNEL")
            node = node_tree.nodes.new(node_type)
            node.inputs['IOR'].default_value = float(node_data['ior'].value)
                
        elif node_type == "LAYER_WEIGHT":
            print ("LAYER_WEIGHT")
            node = node_tree.nodes.new(node_type)
            node.inputs['Blend'].default_value = float(node_data['blend'].value)
                
        elif node_type == "LIGHT_PATH":
            print ("LIGHT_PATH")
            node = node_tree.nodes.new(node_type)
        
        elif node_type == "NEW_GEOMETRY":
            print ("NEW_GEOMETRY")
            node = node_tree.nodes.new(node_type)
        
        elif node_type == "OBJECT_INFO":
            if bpy.app.version[0] + (bpy.app.version[1] / 100.0) < 2.64:
                node_message = ['ERROR', """The material file contains the node \"%s\".
This node is not available in the Blender version you are currently using.
You may need a newer version of Blender for this material to work properly.""" % node_type]
                return
            print ("OBJECT_INFO")
            node = node_tree.nodes.new(node_type)
        
        elif node_type == "PARTICLE_INFO":
            if bpy.app.version[0] + (bpy.app.version[1] / 100.0) < 2.64:
                node_message = ['ERROR', """The material file contains the node \"%s\".
This node is not available in the Blender version you are currently using.
You may need a newer version of Blender for this material to work properly.""" % node_type]
                return
            print ("PARTICLE_INFO")
            node = node_tree.nodes.new(node_type)
        
        elif node_type == "RGB":
            print ("RGB")
            node = node_tree.nodes.new(node_type)
            node.outputs['Color'].default_value = color(node_data['color'].value)
        
        elif node_type == "TANGENT":
            print ("TANGENT")
            if bpy.app.version[0] + (bpy.app.version[1] / 100.0) < 2.65:
                node_message = ['ERROR', """The material file contains the node \"%s\".
This node is not available in the Blender version you are currently using.
You may need a newer version of Blender for this material to work properly.""" % node_type]
                return
            node = node_tree.nodes.new(node_type)
            node.direction_type = node_data['direction'].value
            node.axis = node_data['axis'].value
        
        elif node_type == "TEX_COORD":
            print ("TEX_COORD")
            node = node_tree.nodes.new(node_type)
            if bpy.app.version[0] + (bpy.app.version[1] / 100.0) > 2.64 and "dupli" in node_data:
                node.from_dupli = boolean(node_data['dupli'].value)
        
        elif node_type == "VALUE":
            print ("VALUE")
            node = node_tree.nodes.new(node_type)
            node.outputs['Value'].default_value = float(node_data['value'].value)
            
            #OUTPUT TYPES
        elif node_type == "OUTPUT_LAMP":
            print ("OUTPUT_LAMP")
            node = node_tree.nodes.new(node_type)
        
        elif node_type == "OUTPUT_MATERIAL":
            print ("OUTPUT_MATERIAL")
            node = node_tree.nodes.new(node_type)
        
        elif node_type == "OUTPUT_WORLD":
            print ("OUTPUT_WORLD")
            node = node_tree.nodes.new(node_type)
        
            #SHADER TYPES
        elif node_type == "ADD_SHADER":
            print ("ADD_SHADER")
            node = node_tree.nodes.new(node_type)
            
        elif node_type == "AMBIENT_OCCLUSION":
            print ("AMBIENT_OCCLUSION")
            if bpy.app.version[0] + (bpy.app.version[1] / 100.0) < 2.65:
                node_message = ['ERROR', """The material file contains the node \"%s\".
This node is not available in the Blender version you are currently using.
You may need a newer version of Blender for this material to work properly.""" % node_type]
                return
            node = node_tree.nodes.new(node_type)
            node.inputs['Color'].default_value = color(node_data['color'].value)
        
        elif node_type == "BACKGROUND":
            print ("BACKGROUND")
            node = node_tree.nodes.new(node_type)
            node.inputs['Color'].default_value = color(node_data['color'].value)
            node.inputs['Strength'].default_value = float(node_data['strength'].value)
            
        elif node_type == "BSDF_ANISOTROPIC":
            print ("BSDF_ANISOTROPIC")
            if bpy.app.version[0] + (bpy.app.version[1] / 100.0) < 2.65:
                node_message = ['ERROR', """The material file contains the node \"%s\".
This node is not available in the Blender version you are currently using.
You may need a newer version of Blender for this material to work properly.""" % node_type]
                return
            node = node_tree.nodes.new(node_type)
            node.inputs['Color'].default_value = color(node_data['color'].value)
            node.inputs['Roughness'].default_value = float(node_data['roughness'].value)
            node.inputs['Anisotropy'].default_value = float(node_data['anisotropy'].value)
            node.inputs['Rotation'].default_value = float(node_data['rotation'].value)
            
        elif node_type == "BSDF_DIFFUSE":
            print ("BSDF_DIFFUSE")
            node = node_tree.nodes.new(node_type)
            node.inputs['Color'].default_value = color(node_data['color'].value)
            node.inputs['Roughness'].default_value = float(node_data['roughness'].value)
        
        elif node_type == "BSDF_GLASS":
            print ("BSDF_GLASS")
            node = node_tree.nodes.new(node_type)
            node.distribution = node_data['distribution'].value
            node.inputs['Color'].default_value = color(node_data['color'].value)
            node.inputs['Roughness'].default_value = float(node_data['roughness'].value)
            node.inputs['IOR'].default_value = float(node_data['ior'].value)
            
        elif node_type == "BSDF_GLOSSY":
            print ("BSDF_GLOSSY")
            node = node_tree.nodes.new(node_type)
            node.distribution = node_data['distribution'].value
            node.inputs['Color'].default_value = color(node_data['color'].value)
            node.inputs['Roughness'].default_value = float(node_data['roughness'].value)
        
        elif node_type == "BSDF_REFRACTION":
            print ("BSDF_REFRACTION")
            if bpy.app.version[0] + (bpy.app.version[1] / 100.0) < 2.65:
                node_message = ['ERROR', """The material file contains the node \"%s\".
This node is not available in the Blender version you are currently using.
You may need a newer version of Blender for this material to work properly.""" % node_type]
                return
            node = node_tree.nodes.new(node_type)
            node.distribution = node_data['distribution'].value
            node.inputs['Color'].default_value = color(node_data['color'].value)
            node.inputs['Roughness'].default_value = float(node_data['roughness'].value)
            node.inputs['IOR'].default_value = float(node_data['ior'].value)
        
        elif node_type == "BSDF_TRANSLUCENT":
            print ("BSDF_TRANSLUCENT")
            node = node_tree.nodes.new(node_type)
            node.inputs['Color'].default_value = color(node_data['color'].value)
        
        elif node_type == "BSDF_TRANSPARENT":
            print ("BSDF_TRANSPARENT")
            node = node_tree.nodes.new(node_type)
            node.inputs['Color'].default_value = color(node_data['color'].value)
        
        elif node_type == "BSDF_VELVET":
            print ("BSDF_VELVET")
            node = node_tree.nodes.new(node_type)
            node.inputs['Color'].default_value = color(node_data['color'].value)
            node.inputs['Sigma'].default_value = float(node_data['sigma'].value)
        
        elif node_type == "EMISSION":
            print ("EMISSION")
            node = node_tree.nodes.new(node_type)
            node.inputs['Color'].default_value = color(node_data['color'].value)
            node.inputs['Strength'].default_value = float(node_data['strength'].value)
        
        elif node_type == "HOLDOUT":
            print ("HOLDOUT")
            node = node_tree.nodes.new(node_type)
        
        elif node_type == "MIX_SHADER":
            print ("MIX_SHADER")
            node = node_tree.nodes.new(node_type)
            node.inputs['Fac'].default_value = float(node_data['fac'].value)
        
            #TEXTURE TYPES
        elif node_type == "TEX_BRICK":
            print ("TEX_BRICK")
            if bpy.app.version[0] + (bpy.app.version[1] / 100.0) < 2.64:
                node_message = ['ERROR', """The material file contains the node \"%s\".
This node is not available in the Blender version you are currently using.
You may need a newer version of Blender for this material to work properly.""" % node_type]
                return
            node = node_tree.nodes.new(node_type)
            node.offset = float(node_data['offset'].value)
            node.offset_frequency = float(node_data['offset_freq'].value)
            node.squash = float(node_data['squash'].value)
            node.squash_frequency = float(node_data['squash_freq'].value)
            node.inputs['Color1'].default_value = color(node_data['color1'].value)
            node.inputs['Color2'].default_value = color(node_data['color2'].value)
            node.inputs['Mortar'].default_value = color(node_data['mortar'].value)
            node.inputs['Scale'].default_value = float(node_data['scale'].value)
            node.inputs['Mortar Size'].default_value = float(node_data['mortar_size'].value)
            node.inputs['Bias'].default_value = float(node_data['bias'].value)
            node.inputs['Brick Width'].default_value = float(node_data['width'].value)
            node.inputs['Row Height'].default_value = float(node_data['height'].value)
            
        elif node_type == "TEX_CHECKER":
            print ("TEX_CHECKER")
            node = node_tree.nodes.new(node_type)
            node.inputs['Color1'].default_value = color(node_data['color1'].value)
            node.inputs['Color2'].default_value = color(node_data['color2'].value)
            node.inputs['Scale'].default_value = float(node_data['scale'].value)
            
        elif node_type == "TEX_ENVIRONMENT":
            print ("TEX_ENVIRONMENT")
            if bpy.app.version[0] + (bpy.app.version[1] / 100.0) < 2.64:
                node_message = ['ERROR', """The material file contains the node \"%s\".
This node is not available in the Blender version you are currently using.
You may need a newer version of Blender for this material to work properly.""" % node_type]
                return
            node = node_tree.nodes.new(node_type)
            node.color_space = node_data['color_space'].value
            node.projection = node_data['projection'].value
            if 'image' in node_data:
                if "file://" in node_data['image'].value:
                    image_filepath = node_data['image'].value[7:]
                    image_name = node_data['image'].value.split(os.sep)[-1]
                    image_datablock = bpy.data.images.new(name=image_name, width=4, height=4)
                    image_datablock.source = node_data['source'].value
                    image_datablock.filepath = image_filepath
                    node.image = image_datablock
                    if node_data['source'].value == 'MOVIE' or node_data['source'].value == 'SEQUENCE':
                        node.image_user.frame_duration = int(node_data['frame_duration'].value)
                        node.image_user.frame_start = int(node_data['frame_start'].value)
                        node.image_user.frame_offset = int(node_data['frame_offset'].value)
                        node.image_user.use_cyclic = boolean(node_data['cyclic'].value)
                        node.image_user.use_auto_refresh = boolean(node_data['auto_refresh'].value)
                elif "http://" in node_data['image'].value and bpy.context.scene.mat_lib_images_only_trusted == False:
                    ext = "." + node_data['image'].value.split(".")[-1]
                    image_name = node_data['image'].value.split("/")[-1][:-4]
                    image_host = node_data['image'].value[7:].split("/")[0]
                    image_location = node_data['image'].value[(7 + len(image_host)):]
                    
                    if ext.lower() != ".jpg" and ext.lower() != ".png":
                        node_message = ['ERROR', "The image file referenced by this image texture node is not .jpg or .png; not downloading."]
                        return
                    
                    connection = http.client.HTTPConnection(image_host)
                    connection.request("GET", image_location)
                    response = connection.getresponse().read()
                    #Save image texture
                    image_filepath = os.path.join(mat_lib_folder, "my-materials", image_name + ext)
                    image_file = open(image_filepath, mode="w+b")
                    image_file.write(response)
                    image_file.close()
                    image_datablock = bpy.data.images.new(name=(image_name + ext), width=4, height=4)
                    image_datablock.source = node_data['source'].value
                    image_datablock.filepath = image_filepath
                    node.image = image_datablock
                    if node_data['source'].value == 'MOVIE' or node_data['source'].value == 'SEQUENCE':
                        node.image_user.frame_duration = int(node_data['frame_duration'].value)
                        node.image_user.frame_start = int(node_data['frame_start'].value)
                        node.image_user.frame_offset = int(node_data['frame_offset'].value)
                        node.image_user.use_cyclic = boolean(node_data['cyclic'].value)
                        node.image_user.use_auto_refresh = boolean(node_data['auto_refresh'].value)
                else:
                    ext = "." + node_data['image'].value.split(".")[-1]
                    image_name = node_data['image'].value[:-4]
                    
                    if ext.lower() != ".jpg" and ext.lower() != ".png":
                        node_message = ['ERROR', "The image file referenced by this image texture node is not .jpg or .png; not downloading."]
                        return
                        
                    if library == "composite" and os.path.exists(os.path.join(mat_lib_folder, mat_lib_host, "cycles", "textures", image_name + ext)):
                        image_filepath = os.path.join(mat_lib_folder, mat_lib_host, "cycles", "textures", image_name + ext)
                    elif library != "bundled" and os.path.exists(os.path.join(mat_lib_folder, mat_lib_host, library, "cycles", "textures", image_name + ext)):
                        image_filepath = os.path.join(mat_lib_folder, mat_lib_host, library, "cycles", "textures", image_name + ext)
                    elif library == "bundled" and os.path.exists(os.path.join(mat_lib_folder, "bundled", "cycles", "textures", image_name + ext)):
                        image_filepath = os.path.join(mat_lib_folder, "bundled", "cycles", "textures", image_name + ext)
                    elif working_mode == "online":
                        connection = http.client.HTTPConnection(mat_lib_host)
                        connection.request("GET", mat_lib_location + "cycles/textures/" + image_name + ext)
                        response = connection.getresponse().read()
                        
                        #Cache image texture
                        if library == "composite":
                            image_filepath = os.path.join(mat_lib_folder, mat_lib_host, "cycles", "textures", image_name + ext)
                            image_file = open(image_filepath, mode="w+b")
                            image_file.write(response)
                            image_file.close()
                        else:
                            image_filepath = os.path.join(mat_lib_folder, mat_lib_host, library, "cycles", "textures", image_name + ext)
                            image_file = open(image_filepath, mode="w+b")
                            image_file.write(response)
                            image_file.close()
                    else:
                        node_message = ['ERROR', "The image texture, \"%s\", is not cached; cannot download in offline mode." % (image_name + ext)]
                        image_filepath = ""
                    if image_filepath != "":
                        image_datablock = bpy.data.images.new(name=(image_name + ext), width=4, height=4)
                        image_datablock.source = node_data['source'].value
                        image_datablock.filepath = image_filepath
                        node.image = image_datablock
                        if node_data['source'].value == 'MOVIE' or node_data['source'].value == 'SEQUENCE':
                            node.image_user.frame_duration = int(node_data['frame_duration'].value)
                            node.image_user.frame_start = int(node_data['frame_start'].value)
                            node.image_user.frame_offset = int(node_data['frame_offset'].value)
                            node.image_user.use_cyclic = boolean(node_data['cyclic'].value)
                            node.image_user.use_auto_refresh = boolean(node_data['auto_refresh'].value)
            
        elif node_type == "TEX_GRADIENT":
            print ("TEX_GRADIENT")
            node = node_tree.nodes.new(node_type)
            node.gradient_type = node_data['gradient'].value
        
        elif node_type == "TEX_IMAGE":
            print ("TEX_IMAGE")
            node = node_tree.nodes.new(node_type)
            node.color_space = node_data['color_space'].value
            if bpy.app.version[0] + (bpy.app.version[1] / 100.0) > 2.63 and "projection" in node_data:
                node.projection = node_data['projection'].value
            if 'image' in node_data:
                if "file://" in node_data['image'].value:
                    image_filepath = node_data['image'].value[7:]
                    image_name = node_data['image'].value.split(os.sep)[-1]
                    image_datablock = bpy.data.images.new(name=image_name, width=4, height=4)
                    image_datablock.source = node_data['source'].value
                    image_datablock.filepath = image_filepath
                    node.image = image_datablock
                    if node_data['source'].value == 'MOVIE' or node_data['source'].value == 'SEQUENCE':
                        node.image_user.frame_duration = int(node_data['frame_duration'].value)
                        node.image_user.frame_start = int(node_data['frame_start'].value)
                        node.image_user.frame_offset = int(node_data['frame_offset'].value)
                        node.image_user.use_cyclic = boolean(node_data['cyclic'].value)
                        node.image_user.use_auto_refresh = boolean(node_data['auto_refresh'].value)
                elif "http://" in node_data['image'].value and bpy.context.scene.mat_lib_images_only_trusted == False:
                    ext = "." + node_data['image'].value.split(".")[-1]
                    image_name = node_data['image'].value.split("/")[-1][:-4]
                    image_host = node_data['image'].value[7:].split("/")[0]
                    image_location = node_data['image'].value[(7 + len(image_host)):]
                    
                    if ext.lower() != ".jpg" and ext.lower() != ".png":
                        node_message = ['ERROR', "The image file referenced by this image texture node is not .jpg or .png; not downloading."]
                        return
                    
                    connection = http.client.HTTPConnection(image_host)
                    connection.request("GET", image_location)
                    response = connection.getresponse().read()
                    #Save image texture
                    image_filepath = os.path.join(mat_lib_folder, "my-materials", image_name + ext)
                    image_file = open(image_filepath, mode="w+b")
                    image_file.write(response)
                    image_file.close()
                    image_datablock = bpy.data.images.new(name=(image_name + ext), width=4, height=4)
                    image_datablock.source = node_data['source'].value
                    image_datablock.filepath = image_filepath
                    node.image = image_datablock
                    if node_data['source'].value == 'MOVIE' or node_data['source'].value == 'SEQUENCE':
                        node.image_user.frame_duration = int(node_data['frame_duration'].value)
                        node.image_user.frame_start = int(node_data['frame_start'].value)
                        node.image_user.frame_offset = int(node_data['frame_offset'].value)
                        node.image_user.use_cyclic = boolean(node_data['cyclic'].value)
                        node.image_user.use_auto_refresh = boolean(node_data['auto_refresh'].value)
                else:
                    ext = "." + node_data['image'].value.split(".")[-1]
                    image_name = node_data['image'].value[:-4]
                    
                    if ext.lower() != ".jpg" and ext.lower() != ".png":
                        node_message = ['ERROR', "The image file referenced by this image texture node is not .jpg or .png; not downloading."]
                        return
                        
                    if library == "composite" and os.path.exists(os.path.join(mat_lib_folder, mat_lib_host, "cycles", "textures", image_name + ext)):
                        image_filepath = os.path.join(mat_lib_folder, mat_lib_host, "cycles", "textures", image_name + ext)
                    elif library != "bundled" and os.path.exists(os.path.join(mat_lib_folder, mat_lib_host, library, "cycles", "textures", image_name + ext)):
                        image_filepath = os.path.join(mat_lib_folder, mat_lib_host, library, "cycles", "textures", image_name + ext)
                    elif library == "bundled" and os.path.exists(os.path.join(mat_lib_folder, "bundled", "cycles", "textures", image_name + ext)):
                        image_filepath = os.path.join(mat_lib_folder, "bundled", "cycles", "textures", image_name + ext)
                    elif working_mode == "online":
                        connection = http.client.HTTPConnection(mat_lib_host)
                        connection.request("GET", mat_lib_location + "cycles/textures/" + image_name + ext)
                        response = connection.getresponse().read()
                        
                        #Cache image texture
                        if library == "composite":
                            image_filepath = os.path.join(mat_lib_folder, mat_lib_host, "cycles", "textures", image_name + ext)
                            image_file = open(image_filepath, mode="w+b")
                            image_file.write(response)
                            image_file.close()
                        else:
                            image_filepath = os.path.join(mat_lib_folder, mat_lib_host, library, "cycles", "textures", image_name + ext)
                            image_file = open(image_filepath, mode="w+b")
                            image_file.write(response)
                            image_file.close()
                    else:
                        node_message = ['ERROR', "The image texture, \"%s\", is not cached; cannot download in offline mode." % (image_name + ext)]
                        image_filepath = ""
                    if image_filepath != "":
                        image_datablock = bpy.data.images.new(name=(image_name + ext), width=4, height=4)
                        image_datablock.source = node_data['source'].value
                        image_datablock.filepath = image_filepath
                        node.image = image_datablock
                        if node_data['source'].value == 'MOVIE' or node_data['source'].value == 'SEQUENCE':
                            node.image_user.frame_duration = int(node_data['frame_duration'].value)
                            node.image_user.frame_start = int(node_data['frame_start'].value)
                            node.image_user.frame_offset = int(node_data['frame_offset'].value)
                            node.image_user.use_cyclic = boolean(node_data['cyclic'].value)
                            node.image_user.use_auto_refresh = boolean(node_data['auto_refresh'].value)
                
        elif node_type == "TEX_MAGIC":
            print ("TEX_MAGIC")
            node = node_tree.nodes.new(node_type)
            node.turbulence_depth = int(node_data['depth'].value)
            node.inputs['Scale'].default_value = float(node_data['scale'].value)
            node.inputs['Distortion'].default_value = float(node_data['distortion'].value)
        
        elif node_type == "TEX_MUSGRAVE":
            print ("TEX_MUSGRAVE")
            node = node_tree.nodes.new(node_type)
            node.musgrave_type = node_data['musgrave'].value
            node.inputs['Scale'].default_value = float(node_data['scale'].value)
            node.inputs['Detail'].default_value = float(node_data['detail'].value)
            node.inputs['Dimension'].default_value = float(node_data['dimension'].value)
            node.inputs['Lacunarity'].default_value = float(node_data['lacunarity'].value)
            node.inputs['Offset'].default_value = float(node_data['offset'].value)
            node.inputs['Gain'].default_value = float(node_data['gain'].value)
        
        elif node_type == "TEX_NOISE":
            print ("TEX_NOISE")
            node = node_tree.nodes.new(node_type)
            node.inputs['Scale'].default_value = float(node_data['scale'].value)
            node.inputs['Detail'].default_value = float(node_data['detail'].value)
            node.inputs['Distortion'].default_value = float(node_data['distortion'].value)
                        
        elif node_type == "TEX_SKY":
            print ("TEX_SKY")
            node = node_tree.nodes.new(node_type)
            node.sun_direction = vector(node_data['sun_direction'].value)
            node.turbidity = float(node_data['turbidity'].value)
        
        elif node_type == "TEX_VORONOI":
            print ("TEX_VORONOI")
            node = node_tree.nodes.new(node_type)
            node.coloring = node_data['coloring'].value
            node.inputs['Scale'].default_value = float(node_data['scale'].value)
        
        elif node_type == "TEX_WAVE":
            print ("TEX_WAVE")
            node = node_tree.nodes.new(node_type)
            node.wave_type = node_data['wave'].value
            node.inputs['Scale'].default_value = float(node_data['scale'].value)
            node.inputs['Distortion'].default_value = float(node_data['distortion'].value)
            node.inputs['Detail'].default_value = float(node_data['detail'].value)
            node.inputs['Detail Scale'].default_value = float(node_data['detail_scale'].value)
        
            #COLOR TYPES
        elif node_type == "BRIGHTCONTRAST":
            print ("BRIGHTCONTRAST")
            node = node_tree.nodes.new(node_type)
            node.inputs['Color'].default_value = color(node_data['color'].value)
            node.inputs['Bright'].default_value = float(node_data['bright'].value)
            node.inputs['Contrast'].default_value = float(node_data['contrast'].value)
        
        elif node_type == "GAMMA":
            print ("GAMMA")
            node = node_tree.nodes.new(node_type)
            node.inputs['Color'].default_value = color(node_data['color'].value)
            node.inputs['Gamma'].default_value = float(node_data['gamma'].value)
        
        elif node_type == "HUE_SAT":
            print ("HUE_SAT")
            node = node_tree.nodes.new(node_type)
            node.inputs['Hue'].default_value = float(node_data['hue'].value)
            node.inputs['Saturation'].default_value = float(node_data['saturation'].value)
            node.inputs['Value'].default_value = float(node_data['value'].value)
            node.inputs['Fac'].default_value = float(node_data['fac'].value)
            node.inputs['Color'].default_value = color(node_data['color'].value)
            
        elif node_type == "INVERT":
            print ("INVERT")
            node = node_tree.nodes.new(node_type)
            node.inputs['Fac'].default_value = float(node_data['fac'].value)
            node.inputs['Color'].default_value = color(node_data['color'].value)
        
        elif node_type == "LIGHT_FALLOFF":
            if bpy.app.version[0] + (bpy.app.version[1] / 100.0) < 2.64:
                node_message = ['ERROR', """The material file contains the node \"%s\".
This node is not available in the Blender version you are currently using.
You may need a newer version of Blender for this material to work properly.""" % node_type]
                return
            print ("LIGHT_FALLOFF")
            node = node_tree.nodes.new(node_type)
            node.inputs['Strength'].default_value = float(node_data['strength'].value)
            node.inputs['Smooth'].default_value = float(node_data['smooth'].value)
        
        elif node_type == "MIX_RGB":
            print ("MIX_RGB")
            node = node_tree.nodes.new(node_type)
            node.blend_type = node_data['blend_type'].value
            if bpy.app.version[0] + (bpy.app.version[1] / 100.0) > 2.63 and "clamp" in node_data:
                node.use_clamp = boolean(node_data['clamp'].value)
            node.inputs['Fac'].default_value = float(node_data['fac'].value)
            node.inputs['Color1'].default_value = color(node_data['color1'].value)
            node.inputs['Color2'].default_value = color(node_data['color2'].value)
        
            #VECTOR TYPES
        elif node_type == "BUMP":
            print ("BUMP")
            if bpy.app.version[0] + (bpy.app.version[1] / 100.0) < 2.65:
                node_message = ['ERROR', """The material file contains the node \"%s\".
This node is not available in the Blender version you are currently using.
You may need a newer version of Blender for this material to work properly.""" % node_type]
                return
            node = node_tree.nodes.new(node_type)
            node.inputs["Strength"].default_value = float(node_data['strength'].value)
            
        elif node_type == "MAPPING":
            print ("MAPPING")
            node = node_tree.nodes.new(node_type)
            node.translation = vector(node_data['translation'].value)
            node.rotation = vector(node_data['rotation'].value)
            node.scale = vector(node_data['scale'].value)
            if boolean(node_data['use_min'].value):
                node.use_min = True
                node.min = vector(node_data['min'].value)
            if boolean(node_data['use_max'].value):
                node.use_max = True
                node.max = vector(node_data['max'].value)
            node.inputs['Vector'].default_value = vector(node_data['vector'].value)
        
        elif node_type == "NORMAL":
            print ("NORMAL")
            node = node_tree.nodes.new(node_type)
            node.outputs['Normal'].default_value = vector(node_data['vector_output'].value)
            node.inputs['Normal'].default_value = vector(node_data['vector_input'].value)
            
        elif node_type == "NORMAL_MAP":
            print ("NORMAL_MAP")
            if bpy.app.version[0] + (bpy.app.version[1] / 100.0) < 2.65:
                node_message = ['ERROR', """The material file contains the node \"%s\".
This node is not available in the Blender version you are currently using.
You may need a newer version of Blender for this material to work properly.""" % node_type]
                return
            node = node_tree.nodes.new(node_type)
            node.space = node_data['space'].value
            node.uv_map = node_data['uv_map'].value
            node.inputs["Strength"].default_value = float(node_data['strength'].value)
            node.inputs['Color'].default_value = color(node_data['color'].value)
            
            #CONVERTOR TYPES
        elif node_type == "COMBRGB":
            print ("COMBRGB")
            node = node_tree.nodes.new(node_type)
            node.inputs['R'].default_value = float(node_data['red'].value)
            node.inputs['G'].default_value = float(node_data['green'].value)
            node.inputs['B'].default_value = float(node_data['blue'].value)
        
        elif node_type == "MATH":
            print ("MATH")
            node = node_tree.nodes.new(node_type)
            node.operation = node_data['operation'].value
            if bpy.app.version[0] + (bpy.app.version[1] / 100.0) > 2.63 and "clamp" in node_data:
                node.use_clamp = boolean(node_data['clamp'].value)
            node.inputs[0].default_value = float(node_data['value1'].value)
            node.inputs[1].default_value = float(node_data['value2'].value)
        
        elif node_type == "RGBTOBW":
            print ("RGBTOBW")
            node = node_tree.nodes.new(node_type)
            node.inputs['Color'].default_value = color(node_data['color'].value)
        
        elif node_type == "SEPRGB":
            print ("SEPRGB")
            node = node_tree.nodes.new(node_type)
            node.inputs['Image'].default_value = color(node_data['image'].value)
        
        elif node_type == "VALTORGB":
            print ("VALTORGB")
            node = node_tree.nodes.new(node_type)
            node.color_ramp.interpolation = node_data['interpolation'].value
            node.inputs['Fac'].default_value = float(node_data['fac'].value)
            
            #Delete the first stop which comes with the ramp by default
            node.color_ramp.elements.remove(node.color_ramp.elements[0])
            
            # The first stop will be "stop1", so set i to 1
            i = 1
            while i <= int(node_data['stops'].value):
                #Each color stop element is formatted like this:
                #            stop1="0.35|rgba(1, 0.5, 0.8, 0.5)"
                #The "|" separates the stop's position and color.
                element_data = node_data[("stop" + str(i))].value.split('|')
                if i == 1:
                    element = node.color_ramp.elements[0]
                    element.position = float(element_data[0])
                else:
                    element = node.color_ramp.elements.new(float(element_data[0]))
                element.color = color(element_data[1])
                i = i + 1
            
        elif node_type == "VECT_MATH":
            print ("VECT_MATH")
            node = node_tree.nodes.new(node_type)
            node.operation = node_data['operation'].value
            node.inputs[0].default_value = vector(node_data['vector1'].value)
            node.inputs[1].default_value = vector(node_data['vector2'].value)
            
            #MISCELLANEOUS NODE TYPES
        elif node_type == "FRAME":
            #Don't attempt to add frame nodes in builds previous
            #to rev51926, as Blender's nodes.new() operator was
            #unable to add FRAME nodes. Was fixed with rev51926.
            if int(bpy.app.build_revision.decode()) > 51925:
                print("FRAME")
                node = node_tree.nodes.new(node_type)
        
        elif node_type == "REROUTE":
            if bpy.app.version[0] + (bpy.app.version[1] / 100.0) < 2.64:
                node_message = ['ERROR', """The material file contains the node \"%s\".
This node is not available in the Blender version you are currently using.
You may need a newer version of Blender for this material to work properly.""" % node_type]
                return
            print ("REROUTE")
            node = node_tree.nodes.new(node_type)
        
        elif node_type == "SCRIPT":
            if bpy.app.version[0] + (bpy.app.version[1] / 100.0) < 2.65:
                node_message = ['ERROR', """The material file contains an OSL script node.
This node is not available in the Blender version you are currently using.
You may need a newer version of Blender for this material to work properly."""]
                return
            print ("SCRIPT")
            node = node_tree.nodes.new(node_type)
            node.mode = node_data['mode'].value
            if node_data['mode'].value == 'EXTERNAL':
                if 'script' in node_data:
                    if "file://" in node_data['script'].value:
                        node.filepath = node_data['script'].value[7:]
                    elif "http://" in node_data['script'].value and bpy.context.scene.mat_lib_osl_only_trusted == False:
                        ext = "." + node_data['script'].value.split(".")[-1]
                        script_name = node_data['script'].value.split("/")[-1][:-4]
                        osl_host = node_data['script'].value[7:].split("/")[0]
                        script_location = node_data['script'].value[(7 + len(osl_host)):]
                        
                        if ext.lower() != ".osl" and ext.lower() != ".oso":
                            node_message = ['ERROR', "The OSL script file referenced by this script node is not .osl or .oso; not downloading."]
                            return
                        
                        connection = http.client.HTTPConnection(osl_host)
                        connection.request("GET", script_location + script_name + ext)
                        response = connection.getresponse().read()
                        #Save OSL script
                        osl_filepath = os.path.join(mat_lib_folder, "my-materials", script_name + ext)
                        osl_file = open(osl_filepath, mode="w+b")
                        osl_file.write(response)
                        osl_file.close()
                        node.filepath = osl_filepath
                        
                    else:
                        ext = "." + node_data['script'].value.split(".")[-1]
                        script_name = node_data['script'].value[:-4]
                        
                        if ext.lower() != ".osl" and ext.lower() != ".oso":
                            node_message = ['ERROR', "The OSL script file referenced by this script node is not .osl or .oso; not downloading."]
                            return
                        
                        if library == "composite" and os.path.exists(os.path.join(mat_lib_folder, mat_lib_host, "cycles", "scripts", script_name + ext)):
                            osl_filepath = os.path.join(mat_lib_folder, mat_lib_host, "cycles", "scripts", script_name + ext)
                        elif library != "bundled" and os.path.exists(os.path.join(mat_lib_folder, mat_lib_host, library, "cycles", "scripts", script_name + ext)):
                            osl_filepath = os.path.join(mat_lib_folder, mat_lib_host, library, "cycles", "scripts", script_name + ext)
                        elif library == "bundled" and os.path.exists(os.path.join(mat_lib_folder, "bundled", "cycles", "scripts", script_name + ext)):
                            osl_filepath = os.path.join(mat_lib_folder, "bundled", "cycles", "scripts", script_name + ext)
                        elif working_mode == "online":
                            connection = http.client.HTTPConnection(mat_lib_host)
                            connection.request("GET", mat_lib_location + "cycles/scripts/" + script_name + ext)
                            response = connection.getresponse().read()
                            
                            #Cache OSL script
                            if library == "composite":
                                osl_filepath = os.path.join(mat_lib_folder, mat_lib_host, "cycles", "scripts", script_name + ext)
                                osl_file = open(osl_filepath, mode="w+b")
                                osl_file.write(response)
                                osl_file.close()
                            else:
                                osl_filepath = os.path.join(mat_lib_folder, mat_lib_host, library, "cycles", "scripts", script_name + ext)
                                osl_file = open(osl_filepath, mode="w+b")
                                osl_file.write(response)
                                osl_file.close()
                        else:
                            node_message = ['ERROR', "The OSL script, \"%s\", is not cached; cannot download in offline mode." % (script_name + ext)]
                            osl_filepath = ""
                        node.filepath = osl_filepath
            else:
                if 'script' in node_data:
                    node.script = osl_scripts[int(node_data['script'].value)]
            if node.inputs:
                for input in node.inputs:
                    if input.name.lower() in node_data:
                        if input.type == 'RGBA':
                            input.default_value = color(node_data[input.name.lower()].value)
                        elif input.type == 'VECTOR':
                            input.default_value = vector(node_data[input.name.lower()].value)
                        elif input.type == 'VALUE':
                            input.default_value = float(node_data[input.name.lower()].value)
                        elif input.type == 'INT':
                            input.default_value = int(node_data[input.name.lower()].value)
                        elif input.type == 'BOOL':
                            input.default_value = boolean(node_data[input.name.lower()].value)
                        else:
                            input.default_value = str(node_data[input.name.lower()].value)
                    else:
                        node_message = ['WARNING', "There was no value specified for input \"%s\", leaving at default." % input.name]
                
        else:
            node_message = ['ERROR', """The material file contains the node name \"%s\", which is not known.
The material file may contain an error, or you may need to check for updates to this add-on.""" % node_type]
            return
        node.location = node_location
        
        #Give the node a custom label
        if 'label' in node_data:
            node.label = node_data['label'].value
        
        #Give the node a custom color
        if bpy.app.version[0] + (bpy.app.version[1] / 100.0) > 2.63:
            if 'custom_color' in node_data:
                node.use_custom_color = True
                node.color = color(node_data['custom_color'].value)
        
        #Collapse node if needed
        if 'hide' in node_data:
            node.hide = boolean(node_data['hide'].value)

def boolean(string):
    if string == "True":
        boolean = True
    elif string == "False":
        boolean = False
    elif string == "true":
        boolean = True
    elif string == "false":
        boolean = False
    else:
        print('Error converting string to a boolean')
        return
    return boolean

def color(string):
    if "rgba" in string:
        colors = string[5:-1].replace(" ", "").split(",")
        r = float(colors[0])
        g = float(colors[1])
        b = float(colors[2])
        a = float(colors[3])
        color = [r,g,b,a]
    elif "rgb" in string:
        colors = string[4:-1].replace(" ", "").split(",")
        r = float(colors[0])
        g = float(colors[1])
        b = float(colors[2])
        color = [r,g,b]
    else:
        print('Error converting string to a color')
        return
    return color

def vector(string):
    import mathutils
    if "Vector" in string:
        vectors = string[7:-1].replace(" ", "").split(",")
        x = float(vectors[0])
        y = float(vectors[1])
        z = float(vectors[2])
        vector = mathutils.Vector((x, y, z))
    else:
        print('Error converting string to a vector')
        return
    return vector

class MaterialConvert(bpy.types.Operator):
    '''Convert material(s) to the .bcm format'''
    bl_idname = "material.libraryconvert"
    bl_label = "Convert Cycles Material to .bcm"
    save_location = bpy.props.StringProperty()
    all_materials = bpy.props.BoolProperty()

    def execute(self, context):
        global material_file_contents
        global script_stack
        
        if self.all_materials:
            #For all_materials, access the materials with an index
            mat = 0
            loop_length = len(bpy.data.materials)
        else:
            if not context.active_object:
                if not context.active_object.get("active_material"):
                    self.save_location = ""
                    self.all_materials = False
                    self.report({'ERROR'}, "No material selected!")
                    return {'CANCELLED'}
                self.save_location = ""
                self.all_materials = False
                self.report({'ERROR'}, "No object selected!")
                return {'CANCELLED'}
            #For single materials, access the materials with a name
            mat = context.active_object.active_material.name
            loop_length = 1
        
        if self.save_location is "":
            if context.scene.mat_lib_bcm_write is not "":
                txt = context.scene.mat_lib_bcm_write
            else:
                txt = "bcm_file"
            
            if txt not in bpy.data.texts:
                bpy.data.texts.new(txt)
        
        j = 0
        while j < loop_length:
            if self.save_location is not "":
                if self.all_materials:
                    filename = bpy.data.materials[mat].name.replace("(", "")
                else:
                    filename = mat.replace("(", "")
                filename = filename.replace(")", "")
                filename = filename.replace("!", "")
                filename = filename.replace("@", "")
                filename = filename.replace("#", "")
                filename = filename.replace("$", "")
                filename = filename.replace("%", "")
                filename = filename.replace("&", "")
                filename = filename.replace("*", "")
                filename = filename.replace("/", "")
                filename = filename.replace("|", "")
                filename = filename.replace("\\", "")
                filename = filename.replace("'", "")
                filename = filename.replace("\"", "")
                filename = filename.replace("?", "")
                filename = filename.replace(";", "")
                filename = filename.replace(":", "")
                filename = filename.replace("[", "")
                filename = filename.replace("]", "")
                filename = filename.replace("{", "")
                filename = filename.replace("}", "")
                filename = filename.replace("`", "")
                filename = filename.replace("~", "")
                filename = filename.replace("+", "")
                filename = filename.replace("=", "")
                filename = filename.replace(".", "")
                filename = filename.replace(",", "")
                filename = filename.replace("<", "")
                filename = filename.replace(">", "")
                filename = filename.replace(" ", "_")
                filename = filename.replace("-", "_")
                filename = filename.lower()
        
            material_file_contents = ""
            write('<?xml version="1.0" encoding="UTF-8"?>')
            
            red = smallFloat(bpy.data.materials[mat].diffuse_color.r)
            green = smallFloat(bpy.data.materials[mat].diffuse_color.g)
            blue = smallFloat(bpy.data.materials[mat].diffuse_color.b)
            write("\n<material view_color=\"%s\"" % ("rgb(" + red + ", " + green + ", " + blue + ")"))
            
            write(" sample_lamp=\"" + str(bpy.data.materials[mat].cycles.sample_as_light) + "\">")
            write("\n\t<nodes>")
            
            group_warning = False
            frame_warning = False
            for node in bpy.data.materials[mat].node_tree.nodes:
                if "NodeGroup" in str(node.items):
                    node_type = "GROUP"
                    group_warning = True
                    
                elif node.type == 'FRAME' and int(bpy.app.build_revision.decode()) < 51926:
                    #Don't attempt to write frame nodes in builds previous
                    #to rev51926, as Blender's nodes.new() operator was
                    #unable to add FRAME nodes. Was fixed with rev51926.
                    frame_warning = True
                    print("Skipping frame node; this Blender version will not support adding it back."\
                        "\nFrame nodes are not supported on builds prior to rev51926.")
                else:
                    node_type = node.type
                    #Write node opening bracket
                    write("\n\t\t<node ")
                    
                    #Write node type
                    write("type=\"%s\"" % node_type)
                
                    #Write node custom color
                    if bpy.app.version[0] + (bpy.app.version[1] / 100.0) > 2.63:
                        if node.use_custom_color:
                            r = smallFloat(node.color.r)
                            g = smallFloat(node.color.g)
                            b = smallFloat(node.color.b)
                            write(" custom_color=\"%s\"" % ("rgb(" + r + ", " + g + ", " + b + ")"))
                    
                    #Write node label
                    if node.label:
                        write(" label=\"%s\"" % node.label)
                    
                    #Write node hidden-ness
                    if node.hide:
                        write(" hide=\"True\"")
                        
                    #Write node data
                    writeNodeData(node)
                    
                    #Write node closing bracket
                    write(" />")
            
            write("\n\t</nodes>")
            
            write("\n\t<links>")
            writeNodeLinks(bpy.data.materials[mat].node_tree)
            write("\n\t</links>")
            if script_stack:
                write("\n\t<scripts>")
                i = 0
                while i < len(script_stack):
                    write("\n\t\t<script name=\"%s\" id=\"%s\">\n" % (script_stack[i], str(i)))
                    first_line = True
                    for l in bpy.data.texts[script_stack[i]].lines:
                        if first_line == True:
                            write(l.body.replace("<", "lt;").replace(">", "gt;"))
                            first_line = False
                        else:
                            write("<br />" + l.body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;"))
                    write("\n\t\t</script>")
                    i += 1
                write("\n\t</scripts>")
                script_stack = []
            write("\n</material>")
            
            if self.save_location == "":
                if group_warning:
                    self.report({'ERROR'}, "Material \"" + mat + "\" contains a group node (not supported). Please un-group the nodes and try again.")
                else:
                    bpy.data.texts[txt].clear()
                    bpy.data.texts[txt].write(material_file_contents)
                    if not self.all_materials:
                        if frame_warning:
                            self.report({'WARNING'}, "Material \"" + mat + "\" contains a frame node, which was skipped; see console for details.")
                        else:
                            self.report({'INFO'}, "Material \"" + mat + "\" written to Text \"" + txt + "\" as .bcm")
            else:
                if group_warning:
                    self.report({'ERROR'}, "Material \"" + mat + "\" contains a group node (not supported). Please un-group the nodes and try again.")
                else:
                    print(context.scene.mat_lib_bcm_save_location + filename + ".bcm")
                    bcm_file = open(context.scene.mat_lib_bcm_save_location + filename + ".bcm", mode="w", encoding="UTF-8")
                    bcm_file.write(material_file_contents)
                    bcm_file.close()
                    if not self.all_materials:
                        if frame_warning:
                            self.report({'WARNING'}, "Material \"" + mat + "\" contains a frame node which was skipped; see console for details.")
                            self.report({'WARNING'}, "Material \"" + mat + "\" contains a frame node which was skipped; see console for details.")
                        else:
                            self.report({'INFO'}, "Material \"" + mat + "\" saved to \"" + filename + ".bcm\"")
            j += 1
            if self.all_materials:
                mat += 1
        if self.all_materials and not group_warning and not frame_warning:
            self.report({'INFO'}, "All materials successfully saved!")
        
        self.save_location = ""
        self.all_materials = False
        return {'FINISHED'}

def writeNodeData(node):
    global material_file_contents
    global script_stack
    
    I = node.inputs
    O = node.outputs
    
    if "NodeGroup" in str(node.items):
        node_type = "GROUP"
    else:
        node_type = node.type
        
    if node_type == "GROUP":
        print("GROUP NODE!")
        write("ERROR: GROUP NODES NOT YET SUPPORTED.")
        
        #INPUT TYPES
    elif node_type == "ATTRIBUTE":
        print("ATTRIBUTE")
        write(" attribute=\"%s\"" % node.attribute_name)
    
    elif node_type == "CAMERA":
        print("CAMERA")
        
    elif node_type == "FRESNEL":
        print("FRESNEL")
        write(" ior=\"%s\"" % smallFloat(I['IOR'].default_value))
    
    elif node_type == "LAYER_WEIGHT":
        print("LAYER_WEIGHT")
        write(" blend=\"%s\"" % smallFloat(I['Blend'].default_value))
    
    elif node_type == "LIGHT_PATH":
        print("LIGHT_PATH")
    
    elif node_type == "NEW_GEOMETRY":
        print("NEW_GEOMETRY")
    
    elif node_type == "OBJECT_INFO":
        print("OBJECT_INFO")
    
    elif node_type == "PARTICLE_INFO":
        print("PARTICLE_INFO")
    
    elif node_type == "RGB":
        print("RGB")
        write(" color=\"%s\"" % rgba(O['Color'].default_value))
    
    elif node_type == "TANGENT":
        print("TANGENT")
        write(" direction=\"%s\"" % node.direction_type)
        write(" axis=\"%s\"" % node.axis)
    
    elif node_type == "TEX_COORD":
        print("TEX_COORD")
        if bpy.app.version[0] + (bpy.app.version[1] / 100.0) > 2.64:
            write(" dupli=\"%s\"" % node.from_dupli)
        else:
            write(" dupli=\"False\"")
    
    elif node_type == "VALUE":
        print("VALUE")
        write(" value=\"%s\"" % smallFloat(O['Value'].default_value))
        
        #OUTPUT TYPES
    elif node_type == "OUTPUT_LAMP":
        print("OUTPUT_LAMP")
    
    elif node_type == "OUTPUT_MATERIAL":
        print("OUTPUT_MATERIAL")
    
    elif node_type == "OUTPUT_WORLD":
        print("OUTPUT_WORLD")
    
        #SHADER TYPES
    elif node_type == "ADD_SHADER":
        print("ADD_SHADER")
    
    elif node_type == "AMBIENT_OCCLUSION":
        print("AMBIENT_OCCLUSION")
        write(" color=\"%s\"" % rgba(I['Color'].default_value))
    
    elif node_type == "BACKGROUND":
        print("BACKGROUND")
        write(" color=\"%s\"" % rgba(I['Color'].default_value))
        write(" strength=\"%s\"" % smallFloat(I['Strength'].default_value))
    
    elif node_type == "BSDF_ANISOTROPIC":
        print("BSDF_ANISOTROPIC")
        write(" color=\"%s\"" % rgba(I['Color'].default_value))
        write(" roughness=\"%s\"" % smallFloat(I['Roughness'].default_value))
        write(" anisotropy=\"%s\"" % smallFloat(I['Anisotropy'].default_value))
        write(" rotation=\"%s\"" % smallFloat(I['Rotation'].default_value))
    
    elif node_type == "BSDF_DIFFUSE":
        print("BSDF_DIFFUSE")
        write(" color=\"%s\"" % rgba(I['Color'].default_value))
        write(" roughness=\"%s\"" % smallFloat(I['Roughness'].default_value))
    
    elif node_type == "BSDF_GLASS":
        print("BSDF_GLASS")
        write(" distribution=\"%s\"" % node.distribution)
        write(" color=\"%s\"" % rgba(I['Color'].default_value))
        write(" roughness=\"%s\"" % smallFloat(I['Roughness'].default_value))
        write(" ior=\"%s\"" % smallFloat(I['IOR'].default_value))
    
    elif node_type == "BSDF_GLOSSY":
        print("BSDF_GLOSSY")
        write(" distribution=\"%s\"" % node.distribution)
        write(" color=\"%s\"" % rgba(I['Color'].default_value))
        write(" roughness=\"%s\"" % smallFloat(I['Roughness'].default_value))
    
    elif node_type == "BSDF_REFRACTION":
        print("BSDF_REFRACTION")
        write(" distribution=\"%s\"" % node.distribution)
        write(" color=\"%s\"" % rgba(I['Color'].default_value))
        write(" roughness=\"%s\"" % smallFloat(I['Roughness'].default_value))
        write(" ior=\"%s\"" % smallFloat(I['IOR'].default_value))
    
    elif node_type == "BSDF_TRANSLUCENT":
        print("BSDF_TRANSLUCENT")
        write(" color=\"%s\"" % rgba(I['Color'].default_value))
    
    elif node_type == "BSDF_TRANSPARENT":
        print("BSDF_TRANSPARENT")
        write(" color=\"%s\"" % rgba(I['Color'].default_value))
    
    elif node_type == "BSDF_VELVET":
        print("BSDF_VELVET")
        write(" color=\"%s\"" % rgba(I['Color'].default_value))
        write(" sigma=\"%s\"" % smallFloat(I['Sigma'].default_value))
    
    elif node_type == "EMISSION":
        print("EMISSION")
        write(" color=\"%s\"" % rgba(I['Color'].default_value))
        write(" strength=\"%s\"" % smallFloat(I['Strength'].default_value))
    
    elif node_type == "HOLDOUT":
        print("HOLDOUT")
    
    elif node_type == "MIX_SHADER":
        print("MIX_SHADER")
        write(" fac=\"%s\"" % smallFloat(I['Fac'].default_value))
        
        #TEXTURE TYPES
    elif node_type == "TEX_BRICK":
        print ("TEX_BRICK")
        write(" offset=\"%s\"" % smallFloat(node.offset))
        write(" offset_freq=\"%s\"" % str(node.offset_frequency))
        write(" squash=\"%s\"" % smallFloat(node.squash))
        write(" squash_freq=\"%s\"" % str(node.squash_frequency))
        write(" color1=\"%s\"" % rgba(I['Color1'].default_value))
        write(" color2=\"%s\"" % rgba(I['Color2'].default_value))
        write(" mortar=\"%s\"" % rgba(I['Mortar'].default_value))
        write(" scale=\"%s\"" % smallFloat(I['Scale'].default_value))
        write(" mortar_size=\"%s\"" % smallFloat(I['Mortar Size'].default_value))
        write(" bias=\"%s\"" % smallFloat(I['Bias'].default_value))
        write(" width=\"%s\"" % smallFloat(I['Brick Width'].default_value))
        write(" height=\"%s\"" % smallFloat(I['Row Height'].default_value))
            
    elif node_type == "TEX_CHECKER":
        print("TEX_CHECKER")
        write(" color1=\"%s\"" % rgba(I['Color1'].default_value))
        write(" color2=\"%s\"" % rgba(I['Color2'].default_value))
        write(" scale=\"%s\"" % smallFloat(I['Scale'].default_value))
    
    elif node_type == "TEX_ENVIRONMENT":
        print("TEX_ENVIRONMENT")
        if node.image:
            write(" image=\"file://%s\"" % os.path.realpath(bpy.path.abspath(node.image.filepath)))
            write(" source=\"%s\"" % node.image.source)
            if node.image.source == "SEQUENCE" or node.image.source == "MOVIE":
                write(" frame_duration=\"%s\"" % str(node.image_user.frame_duration))
                write(" frame_start=\"%s\"" % str(node.image_user.frame_start))
                write(" frame_offset=\"%s\"" % str(node.image_user.frame_offset))
                write(" cyclic=\"%s\"" % str(node.image_user.use_cyclic))
                write(" auto_refresh=\"%s\"" % str(node.image_user.use_auto_refresh))
        else:
            write(" image=\"\"")
        write(" color_space=\"%s\"" % node.color_space)
        write(" projection=\"%s\"" % node.projection)
    
    elif node_type == "TEX_GRADIENT":
        print("TEX_GRADIENT")
        write(" gradient=\"%s\"" % node.gradient_type)
    
    elif node_type == "TEX_IMAGE":
        print("TEX_IMAGE")
        if node.image:
            write(" image=\"file://%s\"" % os.path.realpath(bpy.path.abspath(node.image.filepath)))
            write(" source=\"%s\"" % node.image.source)
            if node.image.source == "SEQUENCE" or node.image.source == "MOVIE":
                write(" frame_duration=\"%s\"" % str(node.image_user.frame_duration))
                write(" frame_start=\"%s\"" % str(node.image_user.frame_start))
                write(" frame_offset=\"%s\"" % str(node.image_user.frame_offset))
                write(" cyclic=\"%s\"" % str(node.image_user.use_cyclic))
                write(" auto_refresh=\"%s\"" % str(node.image_user.use_auto_refresh))
        else:
            write(" image=\"\"")
        write(" color_space=\"%s\"" % node.color_space)
        if bpy.app.version[0] + (bpy.app.version[1] / 100.0) > 2.63:
            write(" projection=\"%s\"" % node.projection)
            if node.projection == "BOX":
                write(" blend=\"%s\"" % smallFloat(node.projection_blend))
        else:
            write(" projection=\"FLAT\"")
    
    elif node_type == "TEX_MAGIC":
        print("TEX_MAGIC")
        write(" depth=\"%s\"" % str(node.turbulence_depth))
        write(" scale=\"%s\"" % smallFloat(I['Scale'].default_value))
        write(" distortion=\"%s\"" % smallFloat(I['Distortion'].default_value))
    
    elif node_type == "TEX_MUSGRAVE":
        print("TEX_MUSGRAVE")
        write(" musgrave=\"%s\"" % node.musgrave_type)
        write(" scale=\"%s\"" % smallFloat(I['Scale'].default_value))
        write(" detail=\"%s\"" % smallFloat(I['Detail'].default_value))
        write(" dimension=\"%s\"" % smallFloat(I['Dimension'].default_value))
        write(" lacunarity=\"%s\"" % smallFloat(I['Lacunarity'].default_value))
        write(" offset=\"%s\"" % smallFloat(I['Offset'].default_value))
        write(" gain=\"%s\"" % smallFloat(I['Gain'].default_value))
    
    elif node_type == "TEX_NOISE":
        print("TEX_NOISE")
        write(" scale=\"%s\"" % smallFloat(I['Scale'].default_value))
        write(" detail=\"%s\"" % smallFloat(I['Detail'].default_value))
        write(" distortion=\"%s\"" % smallFloat(I['Distortion'].default_value))
    
    elif node_type == "TEX_SKY":
        print("TEX_SKY")
        write(" sun_direction=\"%s\"" % smallVector(node.sun_direction))
        write(" turbidity=\"%s\"" % smallFloat(node.turbidity))
    
    elif node_type == "TEX_VORONOI":
        print("TEX_VORONOI")
        write(" coloring=\"%s\"" % node.coloring)
        write(" scale=\"%s\"" % smallFloat(I['Scale'].default_value))
    
    elif node_type == "TEX_WAVE":
        print("TEX_WAVE")
        write(" wave=\"%s\"" % node.wave_type)
        write(" scale=\"%s\"" % smallFloat(I['Scale'].default_value))
        write(" distortion=\"%s\"" % smallFloat(I['Distortion'].default_value))
        write(" detail=\"%s\"" % smallFloat(I['Detail'].default_value))
        write(" detail_scale=\"%s\"" % smallFloat(I['Detail Scale'].default_value))
    
        #COLOR TYPES
    elif node_type == "BRIGHTCONTRAST":
        print("BRIGHTCONTRAST")
        write(" color=\"%s\"" % rgba(I['Color'].default_value))
        write(" bright=\"%s\"" % smallFloat(I['Bright'].default_value))
        write(" contrast=\"%s\"" % smallFloat(I['Contrast'].default_value))
    
    elif node_type == "GAMMA":
        print("GAMMA")
        write(" color=\"%s\"" % rgba(I['Color'].default_value))
        write(" gamma=\"%s\"" % smallFloat(I['Gamma'].default_value))
    
    elif node_type == "HUE_SAT":
        print("HUE_SAT")
        write(" hue=\"%s\"" % smallFloat(I['Hue'].default_value))
        write(" saturation=\"%s\"" % smallFloat(I['Saturation'].default_value))
        write(" value=\"%s\"" % smallFloat(I['Value'].default_value))
        write(" fac=\"%s\"" % smallFloat(I['Fac'].default_value))
        write(" color=\"%s\"" % rgba(I['Color'].default_value))
    
    elif node_type == "LIGHT_FALLOFF":
        print("LIGHT_FALLOFF")
        write(" strength=\"%s\"" % smallFloat(I['Strength'].default_value))
        write(" smooth=\"%s\"" % smallFloat(I['Smooth'].default_value))
    
    elif node_type == "MIX_RGB":
        print("MIX_RGB")
        write(" blend_type=\"%s\"" % node.blend_type)
        if bpy.app.version[0] + (bpy.app.version[1] / 100.0) > 2.63:
            write(" use_clamp=\"%s\"" % str(node.use_clamp))
        write(" fac=\"%s\"" % smallFloat(I['Fac'].default_value))
        write(" color1=\"%s\"" % rgba(I[1].default_value))
        write(" color2=\"%s\"" % rgba(I[2].default_value))
    
    elif node_type == "INVERT":
        print("INVERT")
        write(" fac=\"%s\"" % smallFloat(I['Fac'].default_value))
        write(" color=\"%s\"" % rgba(I['Color'].default_value))
        
        #VECTOR TYPES
    elif node_type == "BUMP":
        print("BUMP")
        write(" strength=\"%s\"" % smallFloat(I['Strength'].default_value))
        
    elif node_type == "MAPPING":
        print("MAPPING")
        write(" translation=\"%s\"" % smallVector(node.translation))
        write(" rotation=\"%s\"" % smallVector(node.rotation))
        write(" scale=\"%s\"" % smallVector(node.scale))
        
        write(" use_min=\"%s\"" % str(node.use_min))
        if node.use_min:
            write(" min=\"%s\"" % smallVector(node.min))
        
        write(" use_max=\"%s\"" % str(node.use_max))
        if node.use_max:
            write(" max=\"%s\"" % smallVector(node.max))
        
        vec = I[0].default_value
        write(" vector=\"%s\"" % smallVector(I['Vector'].default_value))
    
    elif node_type == "NORMAL":
        print("NORMAL")
        write(" vector_output=\"%s\"" % smallVector(O['Normal'].default_value))
        write(" vector_input=\"%s\"" % smallVector(I['Normal'].default_value))
        
    elif node_type == "NORMAL_MAP":
        print("NORMAL_MAP")
        write(" space=\"%s\"" % node.space)
        write(" uv_map=\"%s\"" % node.uv_map)
        write(" strength=\"%s\"" % smallFloat(I['Strength'].default_value))
        write(" color=\"%s\"" % rgba(I['Color'].default_value))
        
        #CONVERTER TYPES
    elif node_type == "COMBRGB":
        print("COMBRGB")
        write(" red=\"%s\"" % smallFloat(I['R'].default_value))
        write(" green=\"%s\"" % smallFloat(I['G'].default_value))
        write(" blue=\"%s\"" % smallFloat(I['B'].default_value))
    
    elif node_type == "MATH":
        print("MATH")
        write(" operation=\"%s\"" % node.operation)
        if bpy.app.version[0] + (bpy.app.version[1] / 100.0) > 2.63:
            write(" use_clamp=\"%s\"" % str(node.use_clamp))
        write(" value1=\"%s\"" % smallFloat(I[0].default_value))
        write(" value2=\"%s\"" % smallFloat(I[1].default_value))
        
    elif node_type == "RGBTOBW":
        print ("RGBTOBW")
        write(" color=\"%s\"" % rgba(I['Color'].default_value))
    
    elif node_type == "SEPRGB":
        print("SEPRGB")
        write(" image=\"%s\"" % rgba(I['Image'].default_value))
    
    elif node_type == "VALTORGB":
        print("VALTORGB")
        write(" interpolation=\"%s\"" % str(node.color_ramp.interpolation))
        write(" fac=\"%s\"" % smallFloat(I['Fac'].default_value))
        write(" stops=\"%s\"" % str(len(node.color_ramp.elements)))
        
        k = 1
        while k <= len(node.color_ramp.elements):
            write(" stop%s=\"%s\"" % 
            (str(k), 
             (smallFloat(node.color_ramp.elements[k-1].position) +
             "|" + 
             rgba(node.color_ramp.elements[k-1].color))
            ))
            k += 1
    
    elif node_type == "VECT_MATH":
        print("VECT_MATH")
        write(" operation=\"%s\"" % node.operation)
        write(" vector1=\"%s\"" % smallVector(I[0].default_value))
        write(" vector2=\"%s\"" % smallVector(I[1].default_value))
        
        #MISCELLANEOUS NODE TYPES
    elif node_type == "FRAME":
        print("FRAME")
    
    elif node_type == "REROUTE":
        print("REROUTE")
    
    elif node_type == "SCRIPT":
        print("SCRIPT")
        write(" mode=\"%s\"" % node.mode)
        if node.mode == 'EXTERNAL':
            if node.filepath:
                write(" script=\"file://%s\"" % os.path.realpath(bpy.path.abspath(node.filepath)))
        else:
            if node.script:
                write(" script=\"%s\"" % len(script_stack))
                script_stack.append(node.script.name)
        if node.inputs:
            for input in node.inputs:
                if input.type == 'RGBA':
                    input_value = rgba(input.default_value)
                elif input.type == 'VECTOR':
                    input_value = smallVector(input.default_value)
                elif input.type == 'VALUE':
                    input_value = smallFloat(input.default_value)
                elif input.type == 'INT':
                    input_value = str(input.default_value)
                elif input.type == 'BOOL':
                    input_value = str(input.default_value)
                else:
                    input_value = str(input.default_value)
                
                write(" %s=\"%s\"" % (input.name.lower(), input_value))
    else:
        write(" ERROR: UNKNOWN NODE TYPE. ")
        return
    writeLocation(node)
    
def rgba(color):
    red = smallFloat(color[0])
    green = smallFloat(color[1])
    blue = smallFloat(color[2])
    alpha = smallFloat(color[3])
    return ("rgba(" + red + ", " + green + ", " + blue + ", " + alpha + ")")

def smallFloat(float):
    if len(str(float)) < (6 + str(float).index(".")):
        return str(float)
    else:
        return str(float)[:(6 + str(float).index("."))]

def smallVector(vector):
    return "Vector(" + smallFloat(vector[0]) + ", " + smallFloat(vector[1]) + ", " + smallFloat(vector[2]) + ")"

def write (string):
    global material_file_contents
    material_file_contents += string

def writeLocation(node):
    global material_file_contents
    #X location
    x = str(int(node.location.x))
    #Y location
    y = str(int(node.location.y))
    
    material_file_contents += (" loc=\"" + x + ", " + y + "\"")
    
def writeNodeLinks(node_tree):
    global material_file_contents
    
    #Loop through the links
    i = 0
    while i < len(node_tree.links):
        material_file_contents += ("\n\t\t<link ")
        
        to_node_name = node_tree.links[i].to_node.name
        #Loop through nodes to check name
        e = 0
        while e < len(node_tree.nodes):
            #Write the index if name matches
            if to_node_name == node_tree.nodes[e].name:
                material_file_contents += "to=\"%d\"" % e
                #Set input socket's name
                to_socket = node_tree.links[i].to_socket.path_from_id()
                material_file_contents += (" input=\"%s\"" % to_socket[(to_socket.index("inputs[") + 7):-1])
                e = len(node_tree.nodes)
            e = e + 1
            
        
        from_node_name = node_tree.links[i].from_node.name
        #Loop through nodes to check name
        e = 0
        while e < len(node_tree.nodes):
            #Write the index if name matches
            if from_node_name == node_tree.nodes[e].name:
                material_file_contents += " from=\"%d\"" % e
                #Set input socket's name
                from_socket = node_tree.links[i].from_socket.path_from_id()
                material_file_contents += (" output=\"%s\"" % from_socket[(from_socket.index("outputs[") + 8):-1])
                e = len(node_tree.nodes)
            e = e + 1
        material_file_contents += (" />")
        i = i + 1


def register():
    bpy.utils.register_class(OnlineMaterialLibraryPanel)
    bpy.utils.register_class(LibraryConnect)
    bpy.utils.register_class(LibraryInfo)
    bpy.utils.register_class(LibrarySettings)
    bpy.utils.register_class(LibraryTools)
    bpy.utils.register_class(LibraryHome)
    bpy.utils.register_class(ViewMaterial)
    bpy.utils.register_class(MaterialDetailView)
    bpy.utils.register_class(LibraryClearCache)
    bpy.utils.register_class(LibraryPreview)
    bpy.utils.register_class(AddLibraryMaterial)
    bpy.utils.register_class(ApplyLibraryMaterial)
    bpy.utils.register_class(CacheLibraryMaterial)
    bpy.utils.register_class(SaveLibraryMaterial)
    bpy.utils.register_class(MaterialConvert)


def unregister():
    bpy.utils.unregister_class(OnlineMaterialLibraryPanel)
    bpy.utils.unregister_class(LibraryConnect)
    bpy.utils.unregister_class(LibraryInfo)
    bpy.utils.unregister_class(LibrarySettings)
    bpy.utils.unregister_class(LibraryTools)
    bpy.utils.unregister_class(LibraryHome)
    bpy.utils.unregister_class(ViewMaterial)
    bpy.utils.unregister_class(MaterialDetailView)
    bpy.utils.unregister_class(LibraryClearCache)
    bpy.utils.unregister_class(LibraryPreview)
    bpy.utils.unregister_class(AddLibraryMaterial)
    bpy.utils.unregister_class(ApplyLibraryMaterial)
    bpy.utils.unregister_class(CacheLibraryMaterial)
    bpy.utils.unregister_class(SaveLibraryMaterial)
    bpy.utils.unregister_class(MaterialConvert)

if __name__ == "__main__":
    register()