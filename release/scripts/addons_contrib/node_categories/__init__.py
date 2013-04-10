#
# Copyright 2011, Blender Foundation.
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

# <pep8 compliant>

bl_info = {
    "name": "Node Categories",
    "author": "Lukas Toenne",
    "blender": (2, 64, 0),
    "location": "Node editor toolbar",
    "description": "Panels for adding nodes, sorted by category",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Nodes/Node_Categories",
    "tracker_url": "",
    "support": "TESTING",
    "category": "Nodes"}

import bpy
from bpy.types import PropertyGroup, Panel, Operator, Menu
from bpy.props import CollectionProperty, PointerProperty, StringProperty, BoolProperty, EnumProperty, IntProperty
from bl_operators.node import NodeAddOperator


# Types

# Get an iterator over all actual node classes
def gen_node_subclasses(base):
    for nodeclass in base.__subclasses__():
        # get_node_type used to distinguish base classes from actual node type classes
        if hasattr(nodeclass, 'get_node_type'):
            yield nodeclass
        # call recursively for subclasses
        for subclass in gen_node_subclasses(nodeclass):
            yield subclass


# Enum items callback to get a list of possible node types from context.
# Used for both the node item and operator properties.
# self argument is unused, can be None
def node_type_items(self, context):
    node_tree = context.space_data.edit_tree

    # XXX In customnodes branch, node will use a poll function to determine possible types in the context tree.
    # For now just use a poll function based on node subclass base
    if node_tree.type == 'SHADER':
        poll = lambda nodeclass: issubclass(nodeclass, bpy.types.ShaderNode) or issubclass(nodeclass, bpy.types.SpecialNode)
    elif node_tree.type == 'COMPOSITING':
        poll = lambda nodeclass: issubclass(nodeclass, bpy.types.CompositorNode) or issubclass(nodeclass, bpy.types.SpecialNode)
    elif node_tree.type == 'TEXTURE':
        poll = lambda nodeclass: issubclass(nodeclass, bpy.types.TextureNode) or issubclass(nodeclass, bpy.types.SpecialNode)

    return [(nc.get_node_type(), nc.bl_rna.name, nc.bl_rna.description) for nc in gen_node_subclasses(bpy.types.Node) if (poll is None) or poll(nc)]


node_class_dict = { nc.get_node_type() : nc for nc in set(gen_node_subclasses(bpy.types.Node)) }


class NodeCategoryItemSetting(PropertyGroup):
    value = StringProperty(name="Value", description="Initial value to assign to the node property")

bpy.utils.register_class(NodeCategoryItemSetting)


class NodeCategoryItem(PropertyGroup):
    def node_type_update(self, context):
        # convenience feature: reset to default label when changing the node type
        # XXX might be better to check if the label has actually been modified?
        self.label = node_class_dict[self.node_type].bl_rna.name

    node_type = EnumProperty(name="Node Type", description="Node type identifier", items=node_type_items, update=node_type_update)
    label = StringProperty(name="Label")

    settings = CollectionProperty(name="Settings", description="Initial settings of the node", type=NodeCategoryItemSetting)

    # internal edit values
    edit = BoolProperty(name="Edit", description="Toggle edit mode of this item", default=False) # only used when general category edit is on

bpy.utils.register_class(NodeCategoryItem)


def node_category_update_name(self, context):
    wm = context.window_manager
    if self.panel_type:
        unregister_node_panel(self)
        register_node_panel(self)

class NodeCategory(PropertyGroup):
    type_items = [
        ("SHADER", "Shader", "Shader node category"),
        ("TEXTURE", "Texture", "Texture node category"),
        ("COMPOSITING", "Compositing", "Compositing node category"),
        ]

    name = StringProperty(name="Name", update=node_category_update_name)
    type = EnumProperty(name="Type", description="Category type used to check visibility", items=type_items)
    items = CollectionProperty(name="Items", description="Node items in this category", type=NodeCategoryItem)

    panel_type = StringProperty(name="Panel Type", description="Identifier of the associated panel type")

bpy.utils.register_class(NodeCategory)


# XXX window manager properties don't seem to be saved and reloaded, using Scene for now ...
#bpy.types.WindowManager.node_categories = CollectionProperty(type=NodeCategory)
#bpy.types.WindowManager.node_categories_edit = BoolProperty(name="Edit Node Categories", default=False)
bpy.types.Scene.node_categories = CollectionProperty(type=NodeCategory)
bpy.types.Scene.node_categories_edit = BoolProperty(name="Edit Node Categories", default=False)



# Panels & Menus

class NodePanel():
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'TOOLS'

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.edit_tree


class NODE_MT_category_add_node_type(Menu):
    '''Select a node type'''
    bl_label = "Node Type"

    def draw(self, context):
        layout = self.layout
        node_tree = context.space_data.edit_tree
        node_types = node_type_items(None, context)

        for nt in node_types:
            identifier = nt[0]
            name = nt[1]

            op = layout.operator("node.category_add_item", text=name)
            op.node_type = identifier
            op.label = name


class NODE_MT_category_add_setting(Menu):
    '''Select a node setting'''
    bl_label = "Node Setting"

    def draw(self, context):
        layout = self.layout

        for prop in bpy.types.Node.bl_rna.properties:
            if prop.is_hidden or prop.is_readonly:
                continue

            op = layout.operator("node.category_add_setting", text=prop.name)
            op.setting = prop.identifier

        layout.separator()

        layout.operator("node.category_add_setting", text="Custom ...")
        # op.setting is undefined, so the operator opens a popup to get it


def gen_valid_identifier(seq):
    # get an iterator
    itr = iter(seq)
    # pull characters until we get a legal one for first in identifer
    for ch in itr:
        if ch == '_' or ch.isalpha():
            yield ch
            break
    # pull remaining characters and yield legal ones for identifier
    for ch in itr:
        if ch == '_' or ch.isalpha() or ch.isdigit():
            yield ch


def get_unique_identifier(prefix, name):
    base = prefix + ''.join(gen_valid_identifier(name))

    identifier = base
    index = 1
    while hasattr(bpy.types, identifier):
        identifier = base + str(index)
        index += 1

    return identifier


def register_node_panel(_category):
    identifier = get_unique_identifier("NODE_PT_category_", _category.name)

    @classmethod
    def panel_poll(cls, context):
        space = context.space_data
        category = context.scene.node_categories[cls.category]
        return space.tree_type == category.type

    def panel_draw_header(self, context):
        layout = self.layout
        category = context.scene.node_categories[self.category]
        edit = context.scene.node_categories_edit

        if edit:
            row = layout.row()
            row.prop(category, "name", text="")
            op = row.operator("node.remove_category", text="", icon='X')
            op.category_name = self.category

    def panel_draw(self, context):
        layout = self.layout
        category = context.scene.node_categories[self.category]
        edit = context.scene.node_categories_edit

        layout.context_pointer_set("node_category", category)

        if edit:
            for index, item in enumerate(category.items):
                layout.context_pointer_set("node_category_item", item)

                if item.edit:
                    row = layout.row(align=True)
                    row.prop(item, "edit", icon='TRIA_DOWN', text="", icon_only=True, toggle=True)

                    box = row.box()

                    sub = box.row(align=True)
                    sub.prop(item, "label", text="")
                    op = sub.operator("node.category_remove_item", text="", icon='X')
                    op.index = index

                    box.prop_menu_enum(item, "node_type", text="Node: "+node_class_dict[item.node_type].bl_rna.name, icon='NODE')

                    for setting_index, setting in enumerate(item.settings):
                        row = box.row(align=True)
                        row.label(text=setting.name + " = ")
                        row.prop(setting, "value", text="")

                        op = row.operator("node.category_remove_setting", text="", icon='X')
                        op.index = setting_index

                    box.menu("NODE_MT_category_add_setting", text="Add Setting", icon='ZOOMIN')
                else:
                    row = layout.row(align=True)
                    row.prop(item, "edit", icon='TRIA_RIGHT', text="", icon_only=True, toggle=True)
                    row.label(text=item.label)

            layout.menu("NODE_MT_category_add_node_type", text="Add Node", icon='ZOOMIN')
        else:
            for item in category.items:
                layout.context_pointer_set("node_category_item", item)

                row = layout.row(align=True)
                row.operator("node.category_add_node", text=item.label)

    panel_class_dict = {
        'category' : ''.join(_category.name), # careful here! category can be removed, needs a deep string copy!
        'bl_idname' : identifier,
        'bl_label' : ''.join(_category.name),
        'poll' : panel_poll,
        'draw_header' : panel_draw_header,
        'draw' : panel_draw,
        }
    panel_class = type(identifier, (NodePanel, Panel), panel_class_dict)

    _category.panel_type = identifier
    bpy.utils.register_class(panel_class)

def register_all_node_panels(context):
    categories = context.scene.node_categories
    for cat in categories:
        register_node_panel(cat)


def unregister_node_panel(category):
    panel_type_identifier = getattr(category, "panel_type", None)
    if panel_type_identifier:
        panel_type = getattr(bpy.types, panel_type_identifier, None)
        if panel_type:
            bpy.utils.unregister_class(panel_type)
        category.panel_type = ""

def unregister_all_node_panels(context):
    categories = context.scene.node_categories
    for cat in categories:
        unregister_node_panel(cat)


class NODE_PT_categories(NodePanel, Panel):
    bl_label = "Categories"
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        edit = scene.node_categories_edit

        layout.prop(scene, "node_categories_edit", text="Edit", toggle=True)
        if edit:
            layout.operator("node.add_category", text="Add Category")


# Operators

class NodeOperator():
    @classmethod
    def poll(cls, context):
        space = context.space_data
        # needs active node editor and a tree
        return (space.type == 'NODE_EDITOR' and space.edit_tree)


class NODE_OT_add_category(NodeOperator, Operator):
    '''Create a new node category'''
    bl_idname = "node.add_category"
    bl_label = "Add Node Category"
    bl_options = {'UNDO'}

    category_name = StringProperty(name="Category Name", description="Name of the new node category")

    def execute(self, context):
        categories = context.scene.node_categories

        # cancel if name is already registered
        if self.category_name in categories.keys():
            self.report({'ERROR'}, "Node category "+self.category_name+" is already registered")
            return {'CANCELLED'}

        cat = categories.add()
        cat.name = self.category_name
        cat.type = context.space_data.tree_type
        register_node_panel(cat)

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "category_name", text="Name")


class NODE_OT_remove_category(NodeOperator, Operator):
    '''Remove a node category'''
    bl_idname = "node.remove_category"
    bl_label = "Remove Node Category"
    bl_options = {'UNDO'}

    category_name = StringProperty(name="Category Name", description="Name of the node category")

    def execute(self, context):
        categories = context.scene.node_categories

        # cancel if name is not registered
        if not self.category_name in categories.keys():
            self.report({'ERROR'}, "Node category "+self.category_name+" is not registered")
            return {'CANCELLED'}

        cat = categories[self.category_name]
        
        unregister_node_panel(cat)
        categories.remove(categories.values().index(cat))

        return {'FINISHED'}


class NODE_OT_category_add_item(NodeOperator, Operator):
    '''Add a node item in a category'''
    bl_idname = "node.category_add_item"
    bl_label = "Add Item"
    bl_options = {'UNDO'}

    node_type = EnumProperty(name="Node Type", description="Node type identifier", items=node_type_items)
    label = StringProperty(name="Label")

    def execute(self, context):
        category = context.node_category

        item = category.items.add()
        item.node_type = self.node_type
        item.label = self.label

        return {'FINISHED'}


class NODE_OT_category_remove_item(NodeOperator, Operator):
    '''Remove a node item from a category'''
    bl_idname = "node.category_remove_item"
    bl_label = "Remove Item"
    bl_options = {'UNDO'}

    index = IntProperty(name="Index", description="Index of the category item to remove")

    def execute(self, context):
        category = context.node_category
        category.items.remove(self.index)
        return {'FINISHED'}


class NODE_OT_category_add_setting(NodeOperator, Operator):
    '''Define an initial node setting'''
    bl_idname = "node.category_add_setting"
    bl_label = "Add Setting"
    bl_options = {'UNDO', 'REGISTER'}

    setting = StringProperty(name="Setting", description="Name of the node setting")

    def execute(self, context):
        # set in the invoke function below as a workaround
        item = self.item

        if self.setting in [setting.name for setting in item.settings]:
            self.report({'ERROR'}, "Node setting "+self.setting+" already defined")
            return {'CANCELLED'}

        setting = item.settings.add()
        setting.name = self.setting

        return {'FINISHED'}

    def invoke(self, context, event):
        # XXX workaround for popup invoke: context loses the item pointer during popup,
        # setting this as a py object in the invoke function is a workaround
        self.item = context.node_category_item

        if self.properties.is_property_set("setting"):
            return self.execute(context)
        else:
            wm = context.window_manager
            return wm.invoke_props_popup(self, event)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "setting", text="Name")


class NODE_OT_category_remove_setting(NodeOperator, Operator):
    '''Remove a node setting'''
    bl_idname = "node.category_remove_setting"
    bl_label = "Remove Setting"
    bl_options = {'UNDO'}

    index = IntProperty(name="Index", description="Index of the category item setting to remove")

    def execute(self, context):
        item = context.node_category_item
        item.settings.remove(self.index)
        return {'FINISHED'}


# Node Add operator that uses category item settings for additional initialization
class NODE_OT_category_add_node(NodeAddOperator, Operator):
    '''Add a node to the active tree and initialize from settings'''
    bl_idname = "node.category_add_node"
    bl_label = "Add Node"

    def execute(self, context):
        item = context.node_category_item

        node = self.create_node(context, item.node_type)

        for setting in item.settings:
            print("SETTING: ", setting.name, " = ", setting.value)

            # XXX catch exceptions here?
            value = eval(setting.value)
                
            try:
                setattr(node, setting.name, value)
            except AttributeError as e:
                self.report({'ERROR_INVALID_INPUT'}, "Node has no attribute "+setting.name)
                print (str(e))
                # Continue despite invalid attribute

        return {'FINISHED'}

    def invoke(self, context, event):
        self.store_mouse_cursor(context, event)
        self.execute(context)
        return bpy.ops.transform.translate('INVOKE_DEFAULT')


def register():
    register_all_node_panels(bpy.context)
    bpy.utils.register_module(__name__)


def unregister():
    unregister_all_node_panels(bpy.context)
    bpy.utils.unregister_module(__name__)

