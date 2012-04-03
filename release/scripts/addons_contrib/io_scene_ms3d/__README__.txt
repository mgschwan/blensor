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

# <pep8 compliant>

###############################################################################
#234567890123456789012345678901234567890123456789012345678901234567890123456789
#--------1---------2---------3---------4---------5---------6---------7---------


# ##### BEGIN COPYRIGHT BLOCK #####
#
# initial script copyright (c)2011 Alexander Nussbaumer
#
# ##### END COPYRIGHT BLOCK #####


files:
__README__.txt
__init__.py
ms3d_export.py
ms3d_import.py
ms3d_spec.py
ms3d_utils.py


description:
__README__.txt      : this file
                    § Blender maintenance

__init__.py         : entry point for blender plugins
                      initialize and registers/unregisters plugin functions
                    § Blender maintenance

ms3d_export.py      : entry point for exporter
                      functions to bring Blender content in a correct way to MilkShape
                    § Blender maintenance
                    § Blender -> MilkShape3D maintenance

ms3d_import.py      : entry point for importer
                      functions to bring MilkShape content in a correct way to Blender
                    § Blender maintenance
                    § MilkShape3D -> Blender maintenance

ms3d_spec.py        : objects and structures that specified a MilkShape3D file
                      base functions to write/read its objects itself
                    § MilkShape maintenance

ms3d_utils.py       : most of the strings used in the addon to have a central point for optional internationalization
                      functions that are used by importer and exporter
                    § Blender maintenance
                    § Blender -> MilkShape3D maintenance
                    § MilkShape3D -> Blender maintenance


known issues:
  importer issues:
    - does not import keyframes

  exporter issues:
    - does only export the first existing material, if more than one material is used per mesh
    - does only export the first existing UV texture coordinates, if more than one UV texture is used per mesh
    - does not export bones
    - does not export joints
    - does not export keyframes
    - does not export comments (will never be supported - blender doesn't have similar stuff)


todo:
- change internal data structure for more performance on searching vertex indices and double vertices
- add support for bones and joints in exporter
- add support for keyframes



changelog:
changed: (0, 3, 8),
mod: changed matrix handling, in account to matrix changes since blender rev.42816; for a while with side-by-side implementation by checking 'bpy.app.build_revision'
del: removed unused option for export FuturePinball animation script (i will make an extra addon future_pinball_tool collection)

changed: (0, 3, 6, "beta (2011-12-13 00:00)"),
mod: exporter use an other logic to reduces the total number of smooth groups
mod: correct "version" and "blender" in __init__.py
fix: division by zero in importer
mod: import armature bones (head-tail to tail-head + additional post process to connect for better auto IK handling)
add: import bones and joints with armature modifier
mod: changed mesh generation (take only used vertices, instead of take all vertices and delete deserted in an extra pass)

changed: (0, 3, 4, "beta (2011-12-09 00:00)"),
fix: exporter forgot to change changed vertex_ex handling in ms3d_exporter.py
add: importer adds ms3d_flags custom properties for some objects
fix: importer corrects the roll of blender bones
add: importer adds ms3d_comment custom properties for modelComment (to a blender empty), groupComments (to its blender meshes), materialComments (to its blender materials) and jointComments (to its blender bones)
add: importer adds raw data ms3d_ambient and ms3d_emissive custom properties to material, because blender does not have an exact similar color definition
fix: ms3d_spec, modelComment, only one comment is allowed and a modelComment does not have an index value
mod: droped most of DEBUG_... code
mod: class __init__(self, ...) default parameter handling
mod: droped some tuple constructions: replaced with regular expression "tuple[(].*[[](.*)[]].*[)]" with "(\1)"

changed: (0, 3, 3, "beta (2011-12-02 00:00)")
add: importer adds additionally smoothingGroups as vertex_groups "ms3d_smoothingGroup{1...32}"
fix: export smoothingGroups start index to 1
mod: some blender like modifications ('ENUM' instead "ENUM" on enum values)
mod: some pep8 like modifications (lay-out)
mod: some pep8 like modifications (moved import in the right order)
mod: some pep8 like modifications ("foo(arg, value = 0)" to "foo(arg, value=0)")
mod: some pep8 like modifications (drop "if (sequence) and (len(sequence) > 0):..." to "if (sequence):...")
mod: bit more specific exception blocks


changed: (0, 3, 3, "beta (2011-12-01 00:00)")
mod: if "name" in somedict: result = somedict["name"]  to  result = somedict.get("name") if result is not None: (comment by campbellbarton)
mod: "tracker_url": "http://projects.blender.org/tracker/index.php?func=detail&aid=29404"


changed: (0, 3, 3, "beta (2011-11-29 00:00)")
mod: reuse existing data (now optional)
fix: reuse existing data (now ignores data if library is not none)
add: import process adds custom_properties with raw data (naming and some others, if expecting lost in translation)


changed: (0, 3, 2, "beta (2011-11-27 00:00)")
mod: mered ms3d_base.py to ms3d_utils.py (and droped ms3d_base.py)
mod: moved exclusive importer stuff to ms3d_import.py (renamed BlenderFromMs3d... to ...)
mod: moved exclusive exporter stuff to ms3d_export.py (renamed Ms3dFromBlender... to ...)
fix: import object namings (keep track possible name collisions of ms3d and blender objects on non empty blender scenes - may have same names, but different content)
add: import to group option

changed: (0, 3, 1, "beta (2011-11-25 00:00)")
dev: import bones (not finished yet)
fix: import a material only once, if it is used many times
fix: export materials (all meshes got the same material)
fix: exception in verbose mode (on older ms3d versions with no extended datablocks)

changed: (0, 3, 0, "beta 3b (2011-11-19 00:00)").
mod: exception raise to pass the exception to the GUI
fix: exception if mesh has no material
add: import diffuse / alpha texture file to material (to material and uv texture)
add: export diffuse / alpha texture file name from material (or diffuse from uv texture, if material does not have one)
mod: metric setup on import (bigger clip end value)

changed: (0, 2, 3, "beta_2a (2011-11-15 00:00)").
add: viewport adjustment for import to metric
mod: import / export scale; (reported by AtmanActive, Sun Nov 13, 2011 9:41 pm)
fix: layer handling; bug (reported by AtmanActive, Sun Nov 13, 2011 9:41 pm)
fix: all faces/vertices are now selected again after import

changed: (0, 2, 201111112130, "beta_2").
add: export smoothing groups (from linked faces)
add: import smoothing groups (as linked faces)
add: import groups (as meshes)
fix: export ms3d_triangle_t.groupIndex
add: mark optional part if not available (all value to "None")
add: draw() for option makeup

20111101
changed: (0, 1, 201111011600).


installation instruction:
  - copy the "io_ms3d" folder to <Blender>/2.60/scripts/addons
  - open blender
  - File | User Preferences | Addons | Import-Export
  - enable "Import-Export: MilkShape3D MS3D format (.ms3d)"

# To support reload properly, try to access a package var, if it's there, reload everything
if ("bpy" in locals()):
    import imp
    #if "ms3d_export" in locals():
    #    imp.reload(ms3d_export)
    #if "ms3d_import" in locals():
    #    imp.reload(ms3d_import)
    #if "ms3d_spec" in locals():
    #    imp.reload(ms3d_spec)
    #if "ms3d_utils" in locals():
    #    imp.reload(ms3d_utils)
    pass

else:
    #from . import ms3d_export
    #from . import ms3d_import
    #from . import ms3d_spec
    #from . import ms3d_utils
    pass
