#!/usr/bin/env python3.2

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
# ***** END GPL LICENSE BLOCK *****

# <pep8 compliant>

# This script dumps rna into xml.
# useful for finding bugs in RNA api.

# Example usage
# blender some.blend --background -noaudio --python intern/tools/dump_rna2xml.py

import os
import bpy
import rna_xml


def main():
    filename = os.path.splitext(bpy.data.filepath)[0] + ".xml"

    file = open(filename, 'w')

    if 0:
        # blend file
        rna_xml.rna2xml(file.write,
                        root_rna=bpy.data,
                        root_rna_skip={"window_managers"})
    else:
        # theme. just another test
        rna_xml.rna2xml(file.write,
                        root_rna=bpy.context.user_preferences.themes[0],
                        method='ATTR')

        file.close()

    # read back to ensure this is valid!
    from xml.dom.minidom import parse
    xml_nodes = parse(filename)
    print("Written:", filename)

    # test reading back theme
    if 1:
        theme = xml_nodes.getElementsByTagName("Theme")[0]
        rna_xml.xml2rna(theme,
                        root_rna=bpy.context.user_preferences.themes[0],)

if __name__ == "__main__":
    main()
