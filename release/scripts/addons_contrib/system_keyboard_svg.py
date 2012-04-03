# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
# this script creates Keyboard layout images of the current keyboard configuration.
# the result will be writen to the blender default directory.

# first implementation done by jbakker
# <pep8 compliant>

bl_info = {
    "name": "Keyboard Layout (svg)",
    "author": "Jbakker",
    "version": (0, 1),
    "blender": (2, 6, 0),
    "location": "",
    "description": "Save the hotkeys as a .svg file (search: Keyboard)",
    "warning": "may not work in recent svn",
    "wiki_url": 'http://wiki.blender.org/index.php/Extensions:2.5/Py/' \
        'Scripts/System/keymaps_to_svg',
    "tracker_url": "https://projects.blender.org/tracker/index.php?" \
        "func==detail&aid=21490",
    "category": "System"}

import bpy

keyboard = [
['`', 'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE', 'ZERO', 'MINUS', 'EQUAL', 'BACKSPACE'],
['TAB', 'Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', '[', ']', '\\'],
['CAPSLOCK', 'A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ';', "'", 'ENTER'],
['SHIFT', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', ',', '.', '/', 'SHIFT'],
['CONTROL', 'OSKEY', 'ALT', 'SPACE', 'ALT', 'OSKEY', 'MENUKEY', 'CONTROL']
]

# default dimension of a single key [width, heidgh]
DEFAULT_KEY_DIMENSION = [100, 100]
# alternative dimensions of specufic keys [keyname,[width, height]]
ALTERNATIVE_KEY_DIMENSIONS = {
'BACKSPACE': [250, 100],
'TAB': [175, 100],
'\\': [175, 100],
'CAPSLOCK': [225, 100],
'ENTER': [240, 100],
'SHIFT': [290, 100],
'CONTROL': [225, 100],
'ALT': [100, 100],
'OSKEY': [100, 100],
'MENUKEY': [100, 100],
'SPACE': [690, 100],
}


def createKeyboard(viewtype):
    """
    Creates a keyboard layout (.svg) file of the current configuration for a specific viewtype.
    example of a viewtype is "VIEW_3D".
    """
    for keyconfig in bpy.data.window_managers[0].keyconfigs:
        map = {}
        for keymap in keyconfig.keymaps:
            if keymap.space_type in [viewtype]:
                for key in keymap.keymap_items:
                    if key.map_type == 'KEYBOARD':
                        test = 0
                        pre = []
                        cont = ""
                        if key.ctrl:
                            test = test + 1
                            cont = "C"
                        if key.alt:
                            test = test + 2
                            cont = cont + "A"
                        if key.shift:
                            test = test + 4
                            cont = cont + "S"
                        if key.oskey:
                            test = test + 8
                            cont = cont + "O"
                        if len(cont) > 0:
                            cont = "[" + cont + "] "
                        ktype = key.type
                        if ktype not in map.keys():
                            map[ktype] = []
                        map[ktype].append((test, cont + key.name))

        filename = "keyboard_" + viewtype + ".svg"
        print(filename)
        svgfile = open(filename, "w")
        svgfile.write("""<?xml version="1.0" standalone="no"?>
    <!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
    """)
        svgfile.write("""<svg width="2000" height="800" version="1.1" xmlns="http://www.w3.org/2000/svg">
    """)
        svgfile.write("""<style>
    rect {
        fill:rgb(192,192,192);
        stroke-width:1;
        stroke:rgb(0,0,0);
    }
    text.header {
        font-size:xx-large;
    }
    text.key {
        stroke-width:1;
        stroke:rgb(0,0,0);
    }
    text.action {
        font-size:smaller;
    }
    text.add0 {
        font-size:smaller;
        fill:rgb(0,0,0)
    }
    text.add1 {
        font-size:smaller;
        fill:rgb(255,0,0)
    }
    text.add2 {
        font-size:smaller;
        fill:rgb(0,255,0)
    }
    text.add3 {
       font-size:smaller;
       fill:rgb(128,128,0)
    }
    text.add4 {
        font-size:smaller;
        fill:rgb(0,0,255)
    }
    text.add5 {
        font-size:smaller;
        fill:rgb(128,0,128)
    }
    text.add6 {
        font-size:smaller;
        fill:rgb(0, 128, 128)
    }
    text.add7 {
        font-size:smaller;
        fill:rgb(128,128,128)
    }
    text.add8 {
        font-size:smaller;
        fill:rgb(128,128,128)
    }
    text.add9 {
        font-size:smaller;
        fill:rgb(255,128,128)
    }
    text.add10 {
        font-size:smaller;
        fill:rgb(128,255,128)
    }
    text.add11 {
        font-size:smaller;
        fill:rgb(255,255,128)
    }
    text.add12 {
        font-size:smaller;
        fill:rgb(128,128,255)
    }
    text.add13 {
        font-size:smaller;
        fill:rgb(255,128,255)
    }
    text.add14 {
        font-size:smaller;
        fill:rgb(128,255,255)
    }
    text.add15 {
        font-size:smaller;
        fill:rgb(255,255,128)
    }
    </style>
    """)
        svgfile.write("""<text class="header" x="100" y="24">keyboard layout - """ + viewtype + """</text>
""")

        x = 0
        xgap = 15
        ygap = 15
        y = 32
        for row in keyboard:
            x = 0
            for key in row:
                width = DEFAULT_KEY_DIMENSION[0]
                height = DEFAULT_KEY_DIMENSION[1]
                if key in ALTERNATIVE_KEY_DIMENSIONS.keys():
                    width = ALTERNATIVE_KEY_DIMENSIONS[key][0]
                    height = ALTERNATIVE_KEY_DIMENSIONS[key][1]
                tx = 16
                ty = 16
                svgfile.write("""<rect x=\"""" + str(x) + """\" y=\"""" + str(y) + """\" width=\"""" + str(width) + """\" height=\"""" + str(height) + """\" rx="20" ry="20" />
    """)
                svgfile.write("""<text class="key" x=\"""" + str(x + tx) + """\" y=\"""" + str(y + ty) + """\" width=\"""" + str(width) + """\" height=\"""" + str(height) + """\">
    """)
                svgfile.write(key)
                svgfile.write("</text>")
                ty = ty + 16
                tx = 4
                if key in map.keys():
                    for a in map[key]:
                        svgfile.write("""<text class="add""" + str(a[0]) + """" x=\"""" + str(x + tx) + """\" y=\"""" + str(y + ty) + """\" width=\"""" + str(width) + """\" height=\"""" + str(height) + """\">
    """)
                        svgfile.write(a[1])
                        svgfile.write("</text>")
                        ty = ty + 16
                x = x + width + xgap
            y = y + 100 + ygap
        svgfile.write("""</svg>""")
        svgfile.flush()
        svgfile.close()


class WM_OT_Keyboardlayout(bpy.types.Operator):
    """
        Windows manager operator for keyboard leyout export
    """
    bl_idname = "wm.keyboardlayout"
    bl_label = "Keyboard layout (SGV)"

    def execute(self, context):
        """
        Iterate over all viewtypes to export the keyboard layout.
        """
        for vt in ['VIEW_3D', 'LOGIC_EDITOR', 'NODE_EDITOR', 'CONSOLE', 'GRAPH_EDITOR', 'PROPERTIES', 'SEQUENCE_EDITOR', 'OUTLINER', 'IMAGE_EDITOR', 'TEXT_EDITOR', 'DOPESHEET_EDITOR', 'Window']:
            createKeyboard(vt)
        return {'FINISHED'}


def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
