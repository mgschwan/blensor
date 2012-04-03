# ***** BEGIN GPL LICENSE BLOCK *****
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
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****

# ----------------------------------------------------------------------------#    

'''
todo:
- add file selection for single and multiple files

changelog:
    "version": (1,1,4),
        filename will be used as texture name (still limited by stringlength)


    "version": (1,1,3),
    fixed operator and registration
    added tracker and wiki url\
    
version": (1,1,2)
    replaced image.new() with image.load()
    changed addon category
    removed some unused/old code    
    
version":1.11:
    added type arg to texture.new() [L48]
    cleared default filename
''' 

# ----------------------------------------------------------------------------#    

import bpy
import os
from bpy.props import *

#addon description
bl_info = {
    "name": "import BrushSet",
    "author": "Daniel Grauer",
    "version": (1, 1, 5),
    "blender": (2, 5, 6),
    "category": "Import-Export",
    "location": "File > Import > BrushSet",
    "description": "imports all image files from a folder",
    "warning": '', # used for warning icon and text in addons panel
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/Import-Export/BrushSet",
    "tracker_url": "http://projects.blender.org/tracker/index.php?func=detail&aid=25702&group_id=153&atid=467",
    }

print(" ")
print("*------------------------------------------------------------------------------*")
print("*                          initializing BrushSet import                        *")
print("*------------------------------------------------------------------------------*")
print(" ")

#extension filter (alternative use mimetypes)
ext_list = ['jpg',
            'bmp',
            'iris',
            'png',
            'jpeg',
            'targa',
            'tga'];

def LoadBrushSet(filepath, filename):
    for file in os.listdir(filepath):
        path = (filepath + file)
        #get folder name
        (f1, f2) = os.path.split(filepath)
        (f3, foldername) = os.path.split(f1)
        
        texturename = foldername         # file        "texture"    foldername
        
        #filter ext_list
        if file.split('.')[-1].lower() in ext_list: 
            #create new texture
            texture = bpy.data.textures.new(texturename, 'IMAGE')    #watch it, string limit 21 ?!

            #create new image
            image = bpy.data.images.load(path)
            image.source = "FILE"
            image.filepath = path
            bpy.data.textures[texture.name].image = image
            
            print("imported: " + file)
    print("Brush Set imported!")  

# ----------------------------------------------------------------------------#    

class BrushSetImporter(bpy.types.Operator):
    '''Load Brush Set'''
    bl_idname = "import_image.brushset"
    bl_label = "Import BrushSet"

    filename = StringProperty(name="File Name", description="filepath", default="", maxlen=1024, options={'ANIMATABLE'}, subtype='NONE')
    filepath = StringProperty(name="File Name", description="filepath", default="", maxlen=1024, options={'ANIMATABLE'}, subtype='NONE')
    
    def execute(self, context):
        LoadBrushSet(self.properties.filepath, self.properties.filename)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

# ----------------------------------------------------------------------------#    

def menu_func(self, context):
    #clear the default name for import
    default_name = "" 

    self.layout.operator(BrushSetImporter.bl_idname, text="Brush Set").filename = default_name

# ----------------------------------------------------------------------------#    

def register():    
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_import.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_import.remove(menu_func)

if __name__ == "__main__":
    register()

print(" ")
print("*------------------------------------------------------------------------------*")
print(" ")
