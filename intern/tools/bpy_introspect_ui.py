#!/usr/bin/env python3

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

# This script dumps ui definitions as XML.
# useful for finding bad api usage.

# Example usage:
# python intern/tools/bpy_introspect_ui.py

import sys
ModuleType = type(sys)


def module_add(name):
    mod = sys.modules[name] = ModuleType(name)
    return mod


class AttributeBuilder:
    """__slots__ = (
        "_attr", "_attr_list", "_item_set", "_args",
        "active", "operator_context", "enabled", "index", "data"
        )"""

    def _as_py(self):
        data = [self._attr_single, self._args, [child._as_py() for child in self._attr_list]]
        return data

    def _as_xml(self, indent="    "):

        def to_xml_str(value):
            if type(value) == str:
                # quick shoddy clean
                value = value.replace("&", " ")
                value = value.replace("<", " ")
                value = value.replace(">", " ")

                return '"' + value + '"'
            else:
                return '"' + str(value) + '"'

        def dict_to_kw(args, dict_args):
            args_str = ""
            if args:
                # args_str += " ".join([to_xml_str(a) for a in args])
                for i, a in enumerate(args):
                    args_str += "arg" + str(i + 1) + "=" + to_xml_str(a) + " "

            if dict_args:
                args_str += " ".join(["%s=%s" % (key, to_xml_str(value)) for key, value in sorted(dict_args.items())])

            if args_str:
                return " " + args_str

            return ""

        lines = []

        def py_to_xml(item, indent_ctx):
            if item._attr_list:
                lines.append("%s<%s%s>" % (indent_ctx, item._attr_single, dict_to_kw(item._args_tuple, item._args)))
                for child in item._attr_list:
                    # print(child._attr)
                    py_to_xml(child, indent_ctx + indent)
                lines.append("%s</%s>" % (indent_ctx, item._attr_single))
            else:
                lines.append("%s<%s%s/>" % (indent_ctx, item._attr_single, dict_to_kw(item._args_tuple, item._args)))

        py_to_xml(self, indent)

        return "\n".join(lines)

    def __init__(self, attr, attr_single):
        self._attr = attr
        self._attr_single = attr_single
        self._attr_list = []
        self._item_set = []
        self._args = {}
        self._args_tuple = ()

    def __call__(self, *args, **kwargs):
        # print(self._attr, args, kwargs)
        self._args_tuple = args
        self._args = kwargs
        return self

    def __getattr__(self, attr):
        attr_obj = NewAttr(self._attr + "." + attr, attr)
        self._attr_list.append(attr_obj)
        return attr_obj

    # def __setattr__(self, attr, value):
    #     setatte

    def __getitem__(self, item):
        item_obj = NewAttr(self._attr + "[" + repr(item) + "]", item)
        self._item_set.append(item_obj)
        return item_obj

    def __setitem__(self, item, value):
        pass  # TODO?

    def __repr__(self):
        return self._attr

    def __iter__(self):
        return iter([])

    #def __len__(self):
    #    return 0

    def __int__(self):
        return 0

    def __cmp__(self, other):
        return -1

    def __lt__(self, other):
        return -1

    def __gt__(self, other):
        return -1

    def __le__(self, other):
        return -1

    def __add__(self, other):
        return self

    def __sub__(self, other):
        return self

    def __truediv__(self, other):
        return self

    def __floordiv__(self, other):
        return self

    def __round__(self, other):
        return self

    def __float__(self):
        return 0.0

    # Custom functions
    def lower(self):
        return ""

    def upper(self):
        return ""

    def keys(self):
        return []


def NewAttr(attr, attr_single):
    obj = AttributeBuilder(attr, attr_single)
    return obj


class BaseFakeUI():
    def __init__(self):
        self.layout = NewAttr("self.layout", "layout")


class Panel(BaseFakeUI):
    pass


class Header(BaseFakeUI):
    pass


class Menu(BaseFakeUI):
    def draw_preset(self, context):
        pass

    def path_menu(self, a, b, c):
        pass


class Operator(BaseFakeUI):
    pass


class PropertyGroup():
    pass


# setup fake module
def fake_main():
    bpy = module_add("bpy")

    # Registerable Subclasses
    bpy.types = module_add("bpy.types")
    bpy.types.Panel = Panel
    bpy.types.Header = Header
    bpy.types.Menu = Menu
    bpy.types.PropertyGroup = PropertyGroup
    bpy.types.Operator = Operator

    # ID Subclasses
    bpy.types.Armature = type("Armature", (), {})
    bpy.types.Bone = type("Bone", (), {})
    bpy.types.EditBone = type("EditBone", (), {})
    bpy.types.PoseBone = type("PoseBone", (), {})
    bpy.types.Material = type("Material", (), {})
    bpy.types.Lamp = type("Lamp", (), {})
    bpy.types.Camera = type("Camera", (), {})
    bpy.types.Curve = type("Curve", (), {})
    bpy.types.Lattice = type("Lattice", (), {})
    bpy.types.Mesh = type("Mesh", (), {})
    bpy.types.MetaBall = type("MetaBall", (), {})
    bpy.types.Object = type("Object", (), {})
    bpy.types.Speaker = type("Speaker", (), {})
    bpy.types.Texture = type("Texture", (), {})
    bpy.types.ParticleSettings = type("ParticleSettings", (), {})
    bpy.types.World = type("World", (), {})
    bpy.types.Brush = type("Brush", (), {})
    bpy.types.WindowManager = type("WindowManager", (), {})
    bpy.types.Scene = type("Scene", (), {})
    bpy.types.Scene.EnumProperty = NewAttr("bpy.types.Scene.EnumProperty", "EnumProperty")
    bpy.types.Scene.StringProperty = NewAttr("bpy.types.Scene.StringProperty", "StringProperty")

    bpy.props = module_add("bpy.props")
    bpy.props.StringProperty = dict
    bpy.props.BoolProperty = dict
    bpy.props.IntProperty = dict
    bpy.props.EnumProperty = dict


def fake_helper():

    class PropertyPanel():
        pass

    rna_prop_ui = module_add("rna_prop_ui")
    rna_prop_ui.PropertyPanel = PropertyPanel
    rna_prop_ui.draw = NewAttr("rna_prop_ui.draw", "draw")

    rigify = module_add("rigify")
    rigify.get_submodule_types = lambda: []


def fake_runtime():
    """Only call this before `draw()` functions."""

    # Misc Subclasses
    bpy.types.EffectSequence = type("EffectSequence", (), {})

    # Operator Subclases
    bpy.types.WM_OT_doc_view = type("WM_OT_doc_view", (), {"_prefix": ""})

    bpy.data = module_add("bpy.data")
    bpy.data.scenes = ()
    bpy.data.speakers = ()
    bpy.data.groups = ()
    bpy.data.meshes = ()
    bpy.data.shape_keys = ()
    bpy.data.materials = ()
    bpy.data.lattices = ()
    bpy.data.lamps = ()
    bpy.data.textures = ()
    bpy.data.cameras = ()
    bpy.data.curves = ()
    bpy.data.masks = ()
    bpy.data.metaballs = ()
    bpy.data.movieclips = ()
    bpy.data.armatures = ()
    bpy.data.particles = ()

    bpy.data.file_is_saved = True

    bpy.utils = module_add("bpy.utils")
    bpy.utils.smpte_from_frame = lambda f: ""
    bpy.utils.script_paths = lambda f: ()
    bpy.utils.user_resource = lambda a, b: ()

    bpy.app = module_add("bpy.app")
    bpy.app.debug = False
    bpy.app.version = 2, 55, 1

    bpy.path = module_add("bpy.path")
    bpy.path.display_name = lambda f: ""

    bpy_extras = module_add("bpy_extras")
    bpy_extras.keyconfig_utils = module_add("bpy_extras.keyconfig_utils")
    bpy_extras.keyconfig_utils.KM_HIERARCHY = ()
    bpy_extras.keyconfig_utils.keyconfig_merge = lambda a, b: ()

    addon_utils = module_add("addon_utils")
    addon_utils.modules = lambda f: ()
    addon_utils.module_bl_info = lambda f: None
    addon_utils.addons_fake_modules = {}
    addon_utils.error_duplicates = ()
    addon_utils.error_encoding = ()

fake_main()
fake_helper()
# fake_runtime()  # call after initial import so we can catch
#                 # bad use of modules outside of draw() functions.

import bpy


def module_classes(mod):
    classes = []
    for key, value in mod.__dict__.items():
        try:
            is_subclass = issubclass(value, BaseFakeUI)
        except:
            is_subclass = False

        if is_subclass:
            classes.append(value)

    return classes


def main():

    import os
    BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..")
    BASE_DIR = os.path.normpath(os.path.abspath(BASE_DIR))
    MODULE_DIR = os.path.join(BASE_DIR, "release", "scripts", "startup")

    print("Using base dir: %r" % BASE_DIR)
    print("Using module dir: %r" % MODULE_DIR)

    sys.path.insert(0, MODULE_DIR)

    scripts_dir = os.path.join(MODULE_DIR, "bl_ui")
    for f in sorted(os.listdir(scripts_dir)):
        if f.endswith(".py") and not f.startswith("__init__"):
            # print(f)
            mod = __import__("bl_ui." + f[:-3]).__dict__[f[:-3]]

            classes = module_classes(mod)

            for cls in classes:
                setattr(bpy.types, cls.__name__, cls)

    fake_runtime()

    # print("running...")
    print("<ui>")
    for f in sorted(os.listdir(scripts_dir)):
        if f.endswith(".py") and not f.startswith("__init__"):
            # print(f)
            mod = __import__("bl_ui." + f[:-3]).__dict__[f[:-3]]

            classes = module_classes(mod)

            for cls in classes:
                # want to check if the draw function is directly in the class
                # print("draw")
                if "draw" in cls.__dict__:
                    self = cls()
                    self.draw(NewAttr("context", "context"))
                    # print(self.layout._as_py())
                    self.layout._args['id'] = mod.__name__ + "." + cls.__name__
                    print(self.layout._as_xml())
    print("</ui>")


if __name__ == "__main__":
    main()
