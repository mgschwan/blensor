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
 # Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 #
 # Contributor(s): Campbell Barton
 #
 # #**** END GPL LICENSE BLOCK #****

# <pep8 compliant>

"""
This script runs inside blender and compiles all scripts into pyc files which
blender uses as modules.

./blender.bin --background -noaudio --python source/tools/compile_scripts.py
"""


def main():
    try:
        import bpy
    except ImportError:
        print("Run this script from within blender")
        return

    import os
    import compileall

    compile_paths = []

    print("compiling blender/python scripts")

    # check for portable python install
    path_user = bpy.utils.resource_path('USER')
    path_local = bpy.utils.resource_path('LOCAL')
    if bpy.path.is_subdir(os.__file__, path_user):
        print("  found local python:", path_user)
        compile_paths.append(os.path.join(path_user, "python", "lib"))
    elif bpy.path.is_subdir(os.__file__, path_local):
        print("  found user python:", path_user)
        compile_paths.append(os.path.join(path_local, "python", "lib"))
    else:
        print("  found system python - skipping compile")

    # blender script dirs
    scripts = os.path.normpath(os.path.join(bpy.__file__, "..", "..", ".."))
    print("  found `bpy` scripts:", scripts)
    compile_paths.extend((os.path.join(scripts, "startup"),
                          os.path.join(scripts, "modules"),
                          os.path.join(scripts, "addons"),
                          ))

    print("  compiling paths...")
    for fp in compile_paths:
        print("  %r" % fp)

    for fp in compile_paths:
        compileall.compile_dir(fp, force=True)


if __name__ == '__main__':
    main()
