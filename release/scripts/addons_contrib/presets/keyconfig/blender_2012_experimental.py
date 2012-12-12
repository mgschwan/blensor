""" An experimental new keymap for Blender.
    Work in progress!
"""
import bpy

######################
# Misc configuration
######################
DEVELOPER_HOTKEYS = False  # Weird hotkeys that only developers use
MAYA_STYLE_MANIPULATORS = False  # Maya-style "QWER" hotkeys for manipulators
SUBSURF_RELATIVE = True  # Make subsurf hotkeys work by relative
                         # shifting instead of absolute setting
# Left mouse-button select
bpy.context.user_preferences.inputs.select_mouse = 'LEFT'

# Basic transform keys
TRANSLATE_KEY = 'F'
ROTATE_KEY = 'D'
SCALE_KEY = 'S'

# Specials Menu Key
SPECIALS_MENU_KEY = 'Q'


################################
# Helper functions and classes
################################
class SetManipulator(bpy.types.Operator):
    """Set's the manipulator mode"""
    bl_idname = "view3d.manipulator_set"
    bl_label = "Set Manipulator"
    mode = bpy.props.EnumProperty(items=[("NONE", "None", ""),
                                         ("TRANSLATE", "Translate", ""),
                                         ("ROTATE", "Rotate", ""),
                                         ("SCALE", "Scale", "")],
                                         default="NONE")

    def execute(self, context):
        if self.mode == "NONE":
            context.space_data.show_manipulator = False
        elif self.mode == "TRANSLATE":
            context.space_data.show_manipulator = True
            context.space_data.use_manipulator_translate = True
            context.space_data.use_manipulator_rotate = False
            context.space_data.use_manipulator_scale = False
        elif self.mode == "ROTATE":
            context.space_data.show_manipulator = True
            context.space_data.use_manipulator_translate = False
            context.space_data.use_manipulator_rotate = True
            context.space_data.use_manipulator_scale = False
        elif self.mode == "SCALE":
            context.space_data.show_manipulator = True
            context.space_data.use_manipulator_translate = False
            context.space_data.use_manipulator_rotate = False
            context.space_data.use_manipulator_scale = True

        return {'FINISHED'}
bpy.utils.register_class(SetManipulator)


class ModeSwitchMenu(bpy.types.Menu):
    """ A menu for switching between object modes.
    """
    bl_idname = "OBJECT_MT_mode_switch_menu"
    bl_label = "Switch Mode"

    def draw(self, context):
        layout = self.layout
        layout.operator_enum("object.mode_set", "mode")
bpy.utils.register_class(ModeSwitchMenu)


# Temporary work around: Blender does not properly limit the mode switch menu
# items until the first mode switch (e.g. mesh objects will show pose mode as
# an option).
# TODO: file a bug report for this behavior.
bpy.ops.object.mode_set(mode='OBJECT', toggle=False)


class ObjectDeleteNoConfirm(bpy.types.Operator):
    """Delete selected objects without the confirmation popup"""
    bl_idname = "object.delete_no_confirm"
    bl_label = "Delete Objects No Confirm"
    bl_options = {'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        bpy.ops.object.delete()

        return {'FINISHED'}
bpy.utils.register_class(ObjectDeleteNoConfirm)


class ShiftSubsurfLevel(bpy.types.Operator):
    """Shift the subsurf level of the selected objects up or """ \
    """down by the given amount (has maximum limit, to avoid """ \
    """going crazy and running out of RAM)"""
    bl_idname = "object.shift_subsurf_level"
    bl_label = "Shift Subsurf Level"

    delta = bpy.props.IntProperty(name="Delta", description="Amount to increase/decrease the subsurf level.", default=1)
    min = bpy.props.IntProperty(name="Minimum", description="The lowest subsurf level to shift to.", default=0)
    max = bpy.props.IntProperty(name="Maximum", description="The highest subsurf level to shift to.", default=4)

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        for obj in context.selected_objects:
            # Find the last subsurf modifier in the stack
            m = None
            for mod in obj.modifiers:
                if mod.type == "SUBSURF":
                    m = mod

            # Add a subsurf modifier if necessary
            if not m and self.delta > 0:
                m = obj.modifiers.new(name="Subsurf", type='SUBSURF')
                m.levels = 0

            # Adjust it's subsurf level
            if m:
                if self.delta > 0:
                    if (m.levels + self.delta) <= self.max:
                        m.levels += self.delta
                elif self.delta < 0:
                    if (m.levels + self.delta) >= self.min:
                        m.levels += self.delta
        return {'FINISHED'}
bpy.utils.register_class(ShiftSubsurfLevel)


class SetEditMeshSelectMode(bpy.types.Operator):
    """Set edit mesh select mode (vert, edge, face)"""
    bl_idname = "view3d.set_edit_mesh_select_mode"
    bl_label = "Set Edit Mesh Select Mode"
    mode = bpy.props.EnumProperty(items=[("VERT", "Vertex", ""),
                                         ("EDGE", "Edge", ""),
                                         ("FACE", "Face", "")],
                                         default="VERT")
    toggle = bpy.props.BoolProperty(name="Toggle", default=False)
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None
    
    def execute(self, context):
        if self.mode == "VERT":
            mode = 0
        elif self.mode == "EDGE":
            mode = 1
        else:  # self.mode == "FACE"
            mode = 2
        
        select_mode = context.tool_settings.mesh_select_mode
        if self.toggle:
            select_mode[mode] = [True, False][select_mode[mode]]
        else:
            select_mode[mode] = True
            for i in range(0,3):
                if i != mode:
                    select_mode[i] = False
            
        return {'FINISHED'}
bpy.utils.register_class(SetEditMeshSelectMode)


class MeshDeleteContextual(bpy.types.Operator):
    """ Deletes mesh elements based on context instead
        of forcing the user to select from a menu what
        it should delete.
    """
    bl_idname = "mesh.delete_contextual"
    bl_label = "Mesh Delete Contextual"
    bl_options = {'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return (context.active_object is not None) and (context.mode == "EDIT_MESH")
    
    def execute(self, context):
        select_mode = context.tool_settings.mesh_select_mode
        
        if select_mode[0]:
            bpy.ops.mesh.delete(type='VERT')
        elif select_mode[1] and not select_mode[2]:
            bpy.ops.mesh.delete(type='EDGE')
        elif select_mode[2] and not select_mode[1]:
            bpy.ops.mesh.delete(type='FACE')
        else:
            bpy.ops.mesh.delete(type='VERT')
            
        return {'FINISHED'}
bpy.utils.register_class(MeshDeleteContextual)

###########
# Keymaps
###########

def clear_keymap(kc):
    """ Clears all the keymaps, so we can start from scratch, building
        things back up again one-by-one.
    """
    # Map Window
    km = kc.keymaps.new('Window', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Screen
    km = kc.keymaps.new('Screen', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Editing this part of the keymap seems
    # to cause problems, so leaving alone.
    # Map Screen Editing
    #km = kc.keymaps.new('Screen Editing', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map View2D
    km = kc.keymaps.new('View2D', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Frames
    km = kc.keymaps.new('Frames', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Header
    km = kc.keymaps.new('Header', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map View2D Buttons List
    km = kc.keymaps.new('View2D Buttons List', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Property Editor
    km = kc.keymaps.new('Property Editor', space_type='PROPERTIES', region_type='WINDOW', modal=False)

    # Map Markers
    km = kc.keymaps.new('Markers', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Animation
    km = kc.keymaps.new('Animation', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Timeline
    km = kc.keymaps.new('Timeline', space_type='TIMELINE', region_type='WINDOW', modal=False)

    # Map Outliner
    km = kc.keymaps.new('Outliner', space_type='OUTLINER', region_type='WINDOW', modal=False)

    # Map 3D View Generic
    km = kc.keymaps.new('3D View Generic', space_type='VIEW_3D', region_type='WINDOW', modal=False)

    # Map Grease Pencil
    km = kc.keymaps.new('Grease Pencil', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Face Mask
    km = kc.keymaps.new('Face Mask', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Pose
    km = kc.keymaps.new('Pose', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Object Mode
    km = kc.keymaps.new('Object Mode', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Image Paint
    km = kc.keymaps.new('Image Paint', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Vertex Paint
    km = kc.keymaps.new('Vertex Paint', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Weight Paint
    km = kc.keymaps.new('Weight Paint', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Sculpt
    km = kc.keymaps.new('Sculpt', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Mesh
    km = kc.keymaps.new('Mesh', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Curve
    km = kc.keymaps.new('Curve', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Armature
    km = kc.keymaps.new('Armature', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Metaball
    km = kc.keymaps.new('Metaball', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Lattice
    km = kc.keymaps.new('Lattice', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Particle
    km = kc.keymaps.new('Particle', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Font
    km = kc.keymaps.new('Font', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Object Non-modal
    km = kc.keymaps.new('Object Non-modal', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map 3D View
    km = kc.keymaps.new('3D View', space_type='VIEW_3D', region_type='WINDOW', modal=False)

    # Map View3D Gesture Circle
    km = kc.keymaps.new('View3D Gesture Circle', space_type='EMPTY', region_type='WINDOW', modal=True)

    # Map Gesture Border
    km = kc.keymaps.new('Gesture Border', space_type='EMPTY', region_type='WINDOW', modal=True)

    # Map Standard Modal Map
    km = kc.keymaps.new('Standard Modal Map', space_type='EMPTY', region_type='WINDOW', modal=True)

    # Map Animation Channels
    km = kc.keymaps.new('Animation Channels', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map UV Editor
    km = kc.keymaps.new('UV Editor', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map Transform Modal Map
    km = kc.keymaps.new('Transform Modal Map', space_type='EMPTY', region_type='WINDOW', modal=True)

    # Map UV Sculpt
    km = kc.keymaps.new('UV Sculpt', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Map View3D Fly Modal
    km = kc.keymaps.new('View3D Fly Modal', space_type='EMPTY', region_type='WINDOW', modal=True)

    # Map View3D Rotate Modal
    km = kc.keymaps.new('View3D Rotate Modal', space_type='EMPTY', region_type='WINDOW', modal=True)

    # Map View3D Move Modal
    km = kc.keymaps.new('View3D Move Modal', space_type='EMPTY', region_type='WINDOW', modal=True)

    # Map View3D Zoom Modal
    km = kc.keymaps.new('View3D Zoom Modal', space_type='EMPTY', region_type='WINDOW', modal=True)

    # Map Graph Editor Generic
    km = kc.keymaps.new('Graph Editor Generic', space_type='GRAPH_EDITOR', region_type='WINDOW', modal=False)

    # Map Graph Editor
    km = kc.keymaps.new('Graph Editor', space_type='GRAPH_EDITOR', region_type='WINDOW', modal=False)

    # Map Image Generic
    km = kc.keymaps.new('Image Generic', space_type='IMAGE_EDITOR', region_type='WINDOW', modal=False)

    # Map Image
    km = kc.keymaps.new('Image', space_type='IMAGE_EDITOR', region_type='WINDOW', modal=False)

    # Map Node Generic
    km = kc.keymaps.new('Node Generic', space_type='NODE_EDITOR', region_type='WINDOW', modal=False)

    # Map Node Editor
    km = kc.keymaps.new('Node Editor', space_type='NODE_EDITOR', region_type='WINDOW', modal=False)

    # Map File Browser
    km = kc.keymaps.new('File Browser', space_type='FILE_BROWSER', region_type='WINDOW', modal=False)

    # Map File Browser Main
    km = kc.keymaps.new('File Browser Main', space_type='FILE_BROWSER', region_type='WINDOW', modal=False)

    # Map File Browser Buttons
    km = kc.keymaps.new('File Browser Buttons', space_type='FILE_BROWSER', region_type='WINDOW', modal=False)

    # Map Dopesheet
    km = kc.keymaps.new('Dopesheet', space_type='DOPESHEET_EDITOR', region_type='WINDOW', modal=False)

    # Map NLA Generic
    km = kc.keymaps.new('NLA Generic', space_type='NLA_EDITOR', region_type='WINDOW', modal=False)

    # Map NLA Channels
    km = kc.keymaps.new('NLA Channels', space_type='NLA_EDITOR', region_type='WINDOW', modal=False)

    # Map NLA Editor
    km = kc.keymaps.new('NLA Editor', space_type='NLA_EDITOR', region_type='WINDOW', modal=False)

    # Map Text
    km = kc.keymaps.new('Text', space_type='TEXT_EDITOR', region_type='WINDOW', modal=False)

    # Map Sequencer
    km = kc.keymaps.new('Sequencer', space_type='SEQUENCE_EDITOR', region_type='WINDOW', modal=False)

    # Map Logic Editor
    km = kc.keymaps.new('Logic Editor', space_type='LOGIC_EDITOR', region_type='WINDOW', modal=False)

    # Map Console
    km = kc.keymaps.new('Console', space_type='CONSOLE', region_type='WINDOW', modal=False)

    # Map Clip
    km = kc.keymaps.new('Clip', space_type='CLIP_EDITOR', region_type='WINDOW', modal=False)

    # Map Clip Editor
    km = kc.keymaps.new('Clip Editor', space_type='CLIP_EDITOR', region_type='WINDOW', modal=False)

    # Map Clip Graph Editor
    km = kc.keymaps.new('Clip Graph Editor', space_type='CLIP_EDITOR', region_type='WINDOW', modal=False)





def MapAdd_Window(kc):
    """ Window Map
    """
    km = kc.keymaps.new('Window', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Quit
    kmi = km.keymap_items.new('wm.quit_blender', 'Q', 'PRESS', ctrl=True)

    # Operator search menu
    kmi = km.keymap_items.new('wm.search_menu', 'TAB', 'CLICK')

    # Open
    kmi = km.keymap_items.new('wm.open_mainfile', 'O', 'CLICK', ctrl=True)
    kmi = km.keymap_items.new('wm.link_append', 'O', 'CLICK', ctrl=True, alt=True)
    kmi = km.keymap_items.new('wm.link_append', 'O', 'CLICK', ctrl=True, shift=True)
    kmi.properties.link = False
    kmi = km.keymap_items.new('wm.read_homefile', 'N', 'CLICK', ctrl=True)

    # Save
    kmi = km.keymap_items.new('wm.save_mainfile', 'S', 'CLICK', ctrl=True)
    kmi = km.keymap_items.new('wm.save_as_mainfile', 'S', 'CLICK', shift=True, ctrl=True)
    kmi = km.keymap_items.new('wm.save_homefile', 'U', 'CLICK', ctrl=True)

    # NDof Device
    kmi = km.keymap_items.new('wm.call_menu', 'NDOF_BUTTON_MENU', 'PRESS')
    kmi.properties.name = 'USERPREF_MT_ndof_settings'
    kmi = km.keymap_items.new('wm.ndof_sensitivity_change', 'NDOF_BUTTON_PLUS', 'PRESS')
    kmi.properties.decrease = False
    kmi.properties.fast = False
    kmi = km.keymap_items.new('wm.ndof_sensitivity_change', 'NDOF_BUTTON_MINUS', 'PRESS')
    kmi.properties.decrease = True
    kmi.properties.fast = False
    kmi = km.keymap_items.new('wm.ndof_sensitivity_change', 'NDOF_BUTTON_PLUS', 'PRESS', shift=True)
    kmi.properties.decrease = False
    kmi.properties.fast = True
    kmi = km.keymap_items.new('wm.ndof_sensitivity_change', 'NDOF_BUTTON_MINUS', 'PRESS', shift=True)
    kmi.properties.decrease = True
    kmi.properties.fast = True

    # Misc
    kmi = km.keymap_items.new('wm.window_fullscreen_toggle', 'F11', 'CLICK', alt=True)

    # Development/debugging
    if DEVELOPER_HOTKEYS:
        kmi = km.keymap_items.new('wm.redraw_timer', 'T', 'CLICK', ctrl=True, alt=True)
        kmi = km.keymap_items.new('wm.debug_menu', 'D', 'CLICK', ctrl=True, alt=True)

    # ???
    kmi = km.keymap_items.new('info.reports_display_update', 'TIMER', 'ANY', any=True)


def MapAdd_Screen(kc):
    """ Screen Map
    """
    km = kc.keymaps.new('Screen', space_type='EMPTY', region_type='WINDOW', modal=False)

    kmi = km.keymap_items.new('screen.animation_step', 'TIMER0', 'ANY', any=True)
    kmi = km.keymap_items.new('screen.screen_set', 'RIGHT_ARROW', 'PRESS', ctrl=True)
    kmi.properties.delta = 1
    kmi = km.keymap_items.new('screen.screen_set', 'LEFT_ARROW', 'PRESS', ctrl=True)
    kmi.properties.delta = -1
    kmi = km.keymap_items.new('screen.screen_full_area', 'UP_ARROW', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('screen.screen_full_area', 'DOWN_ARROW', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('screen.screen_full_area', 'SPACE', 'PRESS', shift=True)
    kmi = km.keymap_items.new('screen.screenshot', 'F3', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('screen.screencast', 'F3', 'PRESS', alt=True)
    kmi = km.keymap_items.new('screen.region_quadview', 'Q', 'PRESS', ctrl=True, alt=True)
    kmi = km.keymap_items.new('screen.repeat_history', 'F3', 'PRESS')
    kmi = km.keymap_items.new('screen.repeat_last', 'R', 'PRESS', shift=True)
    kmi = km.keymap_items.new('screen.region_flip', 'F5', 'PRESS')
    kmi = km.keymap_items.new('screen.redo_last', 'F6', 'PRESS')
    kmi = km.keymap_items.new('script.reload', 'F8', 'PRESS')
    kmi = km.keymap_items.new('file.execute', 'RET', 'PRESS')
    kmi = km.keymap_items.new('file.execute', 'NUMPAD_ENTER', 'PRESS')
    kmi = km.keymap_items.new('file.cancel', 'ESC', 'PRESS')
    kmi = km.keymap_items.new('ed.undo', 'Z', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('ed.redo', 'Z', 'PRESS', shift=True, ctrl=True)
    kmi = km.keymap_items.new('ed.undo_history', 'Z', 'PRESS', ctrl=True, alt=True)
    kmi = km.keymap_items.new('render.render', 'F12', 'PRESS')
    kmi = km.keymap_items.new('render.render', 'F12', 'PRESS', ctrl=True)
    kmi.properties.animation = True
    kmi = km.keymap_items.new('render.view_cancel', 'ESC', 'PRESS')
    kmi = km.keymap_items.new('render.view_show', 'F11', 'PRESS')
    kmi = km.keymap_items.new('render.play_rendered_anim', 'F11', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('screen.userpref_show', 'U', 'PRESS', ctrl=True, alt=True)

    # Editing this seems to cause problems.
    # TODO: file bug report
    # Screen Editing
    #km = kc.keymaps.new('Screen Editing', space_type='EMPTY', region_type='WINDOW', modal=False)
    #
    #kmi = km.keymap_items.new('screen.actionzone', 'LEFTMOUSE', 'PRESS')
    #kmi.properties.modifier = 0
    #kmi = km.keymap_items.new('screen.actionzone', 'LEFTMOUSE', 'PRESS', shift=True)
    #kmi.properties.modifier = 1
    #kmi = km.keymap_items.new('screen.actionzone', 'LEFTMOUSE', 'PRESS', ctrl=True)
    #kmi.properties.modifier = 2
    #kmi = km.keymap_items.new('screen.area_split', 'NONE', 'ANY')
    #kmi = km.keymap_items.new('screen.area_join', 'NONE', 'ANY')
    #kmi = km.keymap_items.new('screen.area_dupli', 'NONE', 'ANY', shift=True)
    #kmi = km.keymap_items.new('screen.area_swap', 'NONE', 'ANY', ctrl=True)
    #kmi = km.keymap_items.new('screen.region_scale', 'NONE', 'ANY')
    #kmi = km.keymap_items.new('screen.area_move', 'LEFTMOUSE', 'PRESS')
    #kmi = km.keymap_items.new('screen.area_options', 'RIGHTMOUSE', 'PRESS')


def MapAdd_View2D(kc):
    """ View 2D Map
    """
    km = kc.keymaps.new('View2D', space_type='EMPTY', region_type='WINDOW', modal=False)

    kmi = km.keymap_items.new('view2d.scroller_activate', 'LEFTMOUSE', 'PRESS')
    kmi = km.keymap_items.new('view2d.scroller_activate', 'MIDDLEMOUSE', 'PRESS')
    kmi = km.keymap_items.new('view2d.pan', 'MIDDLEMOUSE', 'PRESS')
    kmi = km.keymap_items.new('view2d.pan', 'MIDDLEMOUSE', 'PRESS', shift=True)
    kmi = km.keymap_items.new('view2d.pan', 'TRACKPADPAN', 'ANY')
    kmi = km.keymap_items.new('view2d.scroll_right', 'WHEELDOWNMOUSE', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('view2d.scroll_left', 'WHEELUPMOUSE', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('view2d.scroll_down', 'WHEELDOWNMOUSE', 'PRESS', shift=True)
    kmi = km.keymap_items.new('view2d.scroll_up', 'WHEELUPMOUSE', 'PRESS', shift=True)
    kmi = km.keymap_items.new('view2d.zoom_out', 'WHEELOUTMOUSE', 'PRESS')
    kmi = km.keymap_items.new('view2d.zoom_in', 'WHEELINMOUSE', 'PRESS')
    kmi = km.keymap_items.new('view2d.zoom_out', 'NUMPAD_MINUS', 'PRESS')
    kmi = km.keymap_items.new('view2d.zoom_in', 'NUMPAD_PLUS', 'PRESS')
    kmi = km.keymap_items.new('view2d.scroll_down', 'WHEELDOWNMOUSE', 'PRESS')
    kmi = km.keymap_items.new('view2d.scroll_up', 'WHEELUPMOUSE', 'PRESS')
    kmi = km.keymap_items.new('view2d.scroll_right', 'WHEELDOWNMOUSE', 'PRESS')
    kmi = km.keymap_items.new('view2d.scroll_left', 'WHEELUPMOUSE', 'PRESS')
    kmi = km.keymap_items.new('view2d.zoom', 'MIDDLEMOUSE', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('view2d.zoom', 'TRACKPADZOOM', 'ANY')
    kmi = km.keymap_items.new('view2d.zoom_border', 'B', 'PRESS', shift=True)

    # View2D Buttons List
    km = kc.keymaps.new('View2D Buttons List', space_type='EMPTY', region_type='WINDOW', modal=False)

    kmi = km.keymap_items.new('view2d.scroller_activate', 'LEFTMOUSE', 'PRESS')
    kmi = km.keymap_items.new('view2d.scroller_activate', 'MIDDLEMOUSE', 'PRESS')
    kmi = km.keymap_items.new('view2d.pan', 'MIDDLEMOUSE', 'PRESS')
    kmi = km.keymap_items.new('view2d.pan', 'TRACKPADPAN', 'ANY')
    kmi = km.keymap_items.new('view2d.scroll_down', 'WHEELDOWNMOUSE', 'PRESS')
    kmi = km.keymap_items.new('view2d.scroll_up', 'WHEELUPMOUSE', 'PRESS')
    kmi = km.keymap_items.new('view2d.scroll_down', 'PAGE_DOWN', 'PRESS')
    kmi.properties.page = True
    kmi = km.keymap_items.new('view2d.scroll_up', 'PAGE_UP', 'PRESS')
    kmi.properties.page = True
    kmi = km.keymap_items.new('view2d.zoom', 'MIDDLEMOUSE', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('view2d.zoom', 'TRACKPADZOOM', 'ANY')
    kmi = km.keymap_items.new('view2d.zoom_out', 'NUMPAD_MINUS', 'PRESS')
    kmi = km.keymap_items.new('view2d.zoom_in', 'NUMPAD_PLUS', 'PRESS')
    kmi = km.keymap_items.new('view2d.reset', 'HOME', 'PRESS')


def MapAdd_View3D_Global(kc):
    """ View 3D Global Map
    """
    km = kc.keymaps.new('3D View', space_type='VIEW_3D', region_type='WINDOW', modal=False)

    #-----------------
    # View navigation
    #-----------------

    # ???
    kmi = km.keymap_items.new('view3d.rotate', 'MOUSEROTATE', 'ANY')
    kmi = km.keymap_items.new('view3d.smoothview', 'TIMER1', 'ANY', any=True)

    

    # Basics with mouse
    kmi = km.keymap_items.new('view3d.rotate', 'MIDDLEMOUSE', 'PRESS')
    kmi = km.keymap_items.new('view3d.move', 'MIDDLEMOUSE', 'PRESS', shift=True)
    kmi = km.keymap_items.new('view3d.zoom', 'MIDDLEMOUSE', 'PRESS', ctrl=True)
    #kmi = km.keymap_items.new('view3d.dolly', 'MIDDLEMOUSE', 'PRESS', shift=True, ctrl=True)

    # Basics with mouse wheel
    kmi = km.keymap_items.new('view3d.zoom', 'WHEELINMOUSE', 'PRESS')
    kmi.properties.delta = 1
    kmi = km.keymap_items.new('view3d.zoom', 'WHEELOUTMOUSE', 'PRESS')
    kmi.properties.delta = -1
    kmi = km.keymap_items.new('view3d.view_pan', 'WHEELUPMOUSE', 'PRESS', ctrl=True)
    kmi.properties.type = 'PANRIGHT'
    kmi = km.keymap_items.new('view3d.view_pan', 'WHEELDOWNMOUSE', 'PRESS', ctrl=True)
    kmi.properties.type = 'PANLEFT'
    kmi = km.keymap_items.new('view3d.view_pan', 'WHEELUPMOUSE', 'PRESS', shift=True)
    kmi.properties.type = 'PANUP'
    kmi = km.keymap_items.new('view3d.view_pan', 'WHEELDOWNMOUSE', 'PRESS', shift=True)
    kmi.properties.type = 'PANDOWN'
    kmi = km.keymap_items.new('view3d.view_orbit', 'WHEELUPMOUSE', 'PRESS', ctrl=True, alt=True)
    kmi.properties.type = 'ORBITLEFT'
    kmi = km.keymap_items.new('view3d.view_orbit', 'WHEELDOWNMOUSE', 'PRESS', ctrl=True, alt=True)
    kmi.properties.type = 'ORBITRIGHT'
    kmi = km.keymap_items.new('view3d.view_orbit', 'WHEELUPMOUSE', 'PRESS', shift=True, alt=True)
    kmi.properties.type = 'ORBITUP'
    kmi = km.keymap_items.new('view3d.view_orbit', 'WHEELDOWNMOUSE', 'PRESS', shift=True, alt=True)
    kmi.properties.type = 'ORBITDOWN'

    # Basics with trackpad
    kmi = km.keymap_items.new('view3d.rotate', 'TRACKPADPAN', 'ANY', alt=True)
    kmi = km.keymap_items.new('view3d.move', 'TRACKPADPAN', 'ANY')
    kmi = km.keymap_items.new('view3d.zoom', 'TRACKPADZOOM', 'ANY')
    
    # Perspective/ortho
    kmi = km.keymap_items.new('view3d.view_persportho', 'NUMPAD_5', 'CLICK')

    # Camera view
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_0', 'CLICK')
    kmi.properties.type = 'CAMERA'
    
    # Basics with numpad
    kmi = km.keymap_items.new('view3d.view_orbit', 'NUMPAD_8', 'CLICK')
    kmi.properties.type = 'ORBITUP'
    kmi = km.keymap_items.new('view3d.view_orbit', 'NUMPAD_2', 'CLICK')
    kmi.properties.type = 'ORBITDOWN'
    kmi = km.keymap_items.new('view3d.view_orbit', 'NUMPAD_4', 'CLICK')
    kmi.properties.type = 'ORBITLEFT'
    kmi = km.keymap_items.new('view3d.view_orbit', 'NUMPAD_6', 'CLICK')
    kmi.properties.type = 'ORBITRIGHT'
    kmi = km.keymap_items.new('view3d.view_pan', 'NUMPAD_8', 'CLICK', ctrl=True)
    kmi.properties.type = 'PANUP'
    kmi = km.keymap_items.new('view3d.view_pan', 'NUMPAD_2', 'CLICK', ctrl=True)
    kmi.properties.type = 'PANDOWN'
    kmi = km.keymap_items.new('view3d.view_pan', 'NUMPAD_4', 'CLICK', ctrl=True)
    kmi.properties.type = 'PANLEFT'
    kmi = km.keymap_items.new('view3d.view_pan', 'NUMPAD_6', 'CLICK', ctrl=True)
    kmi.properties.type = 'PANRIGHT'
    kmi = km.keymap_items.new('view3d.zoom', 'NUMPAD_PLUS', 'CLICK')
    kmi.properties.delta = 1
    kmi = km.keymap_items.new('view3d.zoom', 'NUMPAD_MINUS', 'CLICK')
    kmi.properties.delta = -1

    # Zoom in/out alternatives
    kmi = km.keymap_items.new('view3d.zoom', 'EQUAL', 'CLICK', ctrl=True)
    kmi.properties.delta = 1
    kmi = km.keymap_items.new('view3d.zoom', 'MINUS', 'CLICK', ctrl=True)
    kmi.properties.delta = -1

    # Front/Right/Top/Back/Left/Bottom
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_1', 'CLICK')
    kmi.properties.type = 'FRONT'
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_3', 'CLICK')
    kmi.properties.type = 'RIGHT'
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_7', 'CLICK')
    kmi.properties.type = 'TOP'
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_1', 'CLICK', ctrl=True)
    kmi.properties.type = 'BACK'
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_3', 'CLICK', ctrl=True)
    kmi.properties.type = 'LEFT'
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_7', 'CLICK', ctrl=True)
    kmi.properties.type = 'BOTTOM'

    kmi = km.keymap_items.new('view3d.viewnumpad', 'MIDDLEMOUSE', 'CLICK', alt=True)
    kmi.properties.type = 'FRONT'
    kmi = km.keymap_items.new('view3d.viewnumpad', 'EVT_TWEAK_M', 'EAST', alt=True)
    kmi.properties.type = 'RIGHT'
    kmi = km.keymap_items.new('view3d.viewnumpad', 'EVT_TWEAK_M', 'NORTH', alt=True)
    kmi.properties.type = 'TOP'
    kmi = km.keymap_items.new('view3d.viewnumpad', 'MIDDLEMOUSE', 'DOUBLE_CLICK', alt=True)
    kmi.properties.type = 'BACK'
    kmi = km.keymap_items.new('view3d.viewnumpad', 'EVT_TWEAK_M', 'WEST', alt=True)
    kmi.properties.type = 'LEFT'
    kmi = km.keymap_items.new('view3d.viewnumpad', 'EVT_TWEAK_M', 'SOUTH', alt=True)
    kmi.properties.type = 'BOTTOM'

    # Selection-aligned Front/Right/Top/Back/Left/Bottom
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_1', 'CLICK', shift=True)
    kmi.properties.type = 'FRONT'
    kmi.properties.align_active = True
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_3', 'CLICK', shift=True)
    kmi.properties.type = 'RIGHT'
    kmi.properties.align_active = True
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_7', 'CLICK', shift=True)
    kmi.properties.type = 'TOP'
    kmi.properties.align_active = True
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_1', 'CLICK', shift=True, ctrl=True)
    kmi.properties.type = 'BACK'
    kmi.properties.align_active = True
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_3', 'CLICK', shift=True, ctrl=True)
    kmi.properties.type = 'LEFT'
    kmi.properties.align_active = True
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_7', 'CLICK', shift=True, ctrl=True)
    kmi.properties.type = 'BOTTOM'
    kmi.properties.align_active = True

    # NDOF Device
    kmi = km.keymap_items.new('view3d.ndof_orbit', 'NDOF_BUTTON_MENU', 'ANY')
    kmi = km.keymap_items.new('view3d.ndof_pan', 'NDOF_BUTTON_MENU', 'ANY', shift=True)
    kmi = km.keymap_items.new('view3d.view_selected', 'NDOF_BUTTON_FIT', 'PRESS')
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NDOF_BUTTON_FRONT', 'PRESS')
    kmi.properties.type = 'FRONT'
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NDOF_BUTTON_BACK', 'PRESS')
    kmi.properties.type = 'BACK'
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NDOF_BUTTON_LEFT', 'PRESS')
    kmi.properties.type = 'LEFT'
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NDOF_BUTTON_RIGHT', 'PRESS')
    kmi.properties.type = 'RIGHT'
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NDOF_BUTTON_TOP', 'PRESS')
    kmi.properties.type = 'TOP'
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NDOF_BUTTON_BOTTOM', 'PRESS')
    kmi.properties.type = 'BOTTOM'
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NDOF_BUTTON_FRONT', 'PRESS', shift=True)
    kmi.properties.type = 'FRONT'
    kmi.properties.align_active = True
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NDOF_BUTTON_RIGHT', 'PRESS', shift=True)
    kmi.properties.type = 'RIGHT'
    kmi.properties.align_active = True
    kmi = km.keymap_items.new('view3d.viewnumpad', 'NDOF_BUTTON_TOP', 'PRESS', shift=True)
    kmi.properties.type = 'TOP'
    kmi.properties.align_active = True

    # Fly mode
    #kmi = km.keymap_items.new('view3d.fly', 'F', 'CLICK', shift=True)

    # Misc
    kmi = km.keymap_items.new('view3d.view_selected', 'NUMPAD_PERIOD', 'CLICK')
    kmi = km.keymap_items.new('view3d.view_center_cursor', 'NUMPAD_PERIOD', 'CLICK', ctrl=True)
    kmi = km.keymap_items.new('view3d.zoom_camera_1_to_1', 'NUMPAD_ENTER', 'CLICK', shift=True)
    kmi = km.keymap_items.new('view3d.view_center_camera', 'HOME', 'CLICK')
    kmi = km.keymap_items.new('view3d.view_all', 'HOME', 'CLICK')
    kmi.properties.center = False
    kmi = km.keymap_items.new('view3d.view_all', 'C', 'CLICK', shift=True)
    kmi.properties.center = True

    #-------------
    # Manipulator
    #-------------
    
    kmi = km.keymap_items.new('view3d.manipulator', 'EVT_TWEAK_L', 'ANY', any=True)
    kmi.properties.release_confirm = True

    if MAYA_STYLE_MANIPULATORS:
        kmi = km.keymap_items.new('view3d.manipulator_set', 'Q', 'CLICK')
        kmi.properties.mode = 'NONE'
        kmi = km.keymap_items.new('view3d.manipulator_set', TRANSLATE_KEY, 'CLICK')
        kmi.properties.mode = 'TRANSLATE'
        kmi = km.keymap_items.new('view3d.manipulator_set', ROTATE_KEY, 'CLICK')
        kmi.properties.mode = 'ROTATE'
        kmi = km.keymap_items.new('view3d.manipulator_set', SCALE_KEY, 'CLICK')
        kmi.properties.mode = 'SCALE'
    else:
        kmi = km.keymap_items.new('wm.context_toggle', 'SPACE', 'CLICK', ctrl=True)
        kmi.properties.data_path = 'space_data.show_manipulator'

    #-----------
    # Selection
    #-----------
    
    # Click select
    kmi = km.keymap_items.new('view3d.select', 'SELECTMOUSE', 'CLICK') # Replace
    kmi.properties.extend = False
    kmi.properties.deselect = False
    kmi.properties.toggle = False
    kmi.properties.center = False
    kmi.properties.enumerate = False
    kmi.properties.object = False
    kmi = km.keymap_items.new('view3d.select', 'SELECTMOUSE', 'CLICK', shift=True) # Extend
    kmi.properties.extend = True
    kmi.properties.deselect = False
    kmi.properties.toggle = False
    kmi.properties.center = False
    kmi.properties.enumerate = False
    kmi.properties.object = False
    kmi = km.keymap_items.new('view3d.select', 'SELECTMOUSE', 'CLICK', ctrl=True) # Deselect
    kmi.properties.extend = False
    kmi.properties.deselect = True
    kmi.properties.toggle = False
    kmi.properties.center = False
    kmi.properties.enumerate = False
    kmi.properties.object = False
    
    # Enumerate select
    kmi = km.keymap_items.new('view3d.select', 'SELECTMOUSE', 'CLICK', alt=True) # Replace
    kmi.properties.extend = False
    kmi.properties.center = False
    kmi.properties.enumerate = True
    kmi.properties.object = False
    kmi = km.keymap_items.new('view3d.select', 'SELECTMOUSE', 'CLICK', shift=True, alt=True) # Extend
    kmi.properties.extend = True
    kmi.properties.center = False
    kmi.properties.enumerate = True
    kmi.properties.object = False
    kmi = km.keymap_items.new('view3d.select', 'SELECTMOUSE', 'CLICK', ctrl=True, alt=True) # Center (TODO: deselect)
    kmi.properties.extend = False
    kmi.properties.center = True
    kmi.properties.enumerate = True
    kmi.properties.object = False

    # Border select
    kmi = km.keymap_items.new('view3d.select_border', 'EVT_TWEAK_L', 'ANY') # Replace
    kmi.properties.extend = False
    kmi = km.keymap_items.new('view3d.select_border', 'EVT_TWEAK_L', 'ANY', shift=True) # Extend
    kmi.properties.extend = True
    kmi = km.keymap_items.new('view3d.select_border', 'EVT_TWEAK_L', 'ANY', ctrl=True) # Deselect (handled in modal)
    kmi.properties.extend = False

    # Lasso select
    kmi = km.keymap_items.new('view3d.select_lasso', 'EVT_TWEAK_L', 'ANY', alt=True) # Replace
    kmi.properties.extend = False
    kmi.properties.deselect = False
    kmi = km.keymap_items.new('view3d.select_lasso', 'EVT_TWEAK_L', 'ANY', alt=True, shift=True) # Extend
    kmi.properties.extend = True
    kmi.properties.deselect = False
    kmi = km.keymap_items.new('view3d.select_lasso', 'EVT_TWEAK_L', 'ANY', alt=True, ctrl=True) # Deselect
    kmi.properties.extend = False
    kmi.properties.deselect = True

    # Paint select
    #kmi = km.keymap_items.new('view3d.select_circle', 'C', 'CLICK')

    #-----------------------
    # Transforms via hotkey
    #-----------------------
    
    # Grab, rotate scale
    kmi = km.keymap_items.new('transform.translate', TRANSLATE_KEY, 'PRESS')
    #kmi = km.keymap_items.new('transform.translate', 'EVT_TWEAK_S', 'ANY')
    kmi = km.keymap_items.new('transform.rotate', ROTATE_KEY, 'PRESS')
    kmi = km.keymap_items.new('transform.resize', SCALE_KEY, 'PRESS')

    # Mirror, shear, warp, to-sphere
    #kmi = km.keymap_items.new('transform.mirror', 'M', 'CLICK', ctrl=True)
    #kmi = km.keymap_items.new('transform.shear', 'S', 'CLICK', shift=True, ctrl=True, alt=True)
    #kmi = km.keymap_items.new('transform.warp', 'W', 'CLICK', shift=True)
    #kmi = km.keymap_items.new('transform.tosphere', 'S', 'CLICK', shift=True, alt=True)

    #-------------------------
    # Transform texture space
    #-------------------------
    kmi = km.keymap_items.new('transform.translate', 'T', 'CLICK', shift=True)
    kmi.properties.texture_space = True
    kmi = km.keymap_items.new('transform.resize', 'T', 'CLICK', shift=True, alt=True)
    kmi.properties.texture_space = True

    #------------------
    # Transform spaces
    #------------------
    kmi = km.keymap_items.new('transform.select_orientation', 'SPACE', 'CLICK', alt=True)
    kmi = km.keymap_items.new('transform.create_orientation', 'SPACE', 'CLICK', ctrl=True, alt=True)
    kmi.properties.use = True

    #----------
    # Snapping
    #----------
    kmi = km.keymap_items.new('wm.context_toggle', 'TAB', 'CLICK', shift=True)
    kmi.properties.data_path = 'tool_settings.use_snap'
    kmi = km.keymap_items.new('transform.snap_type', 'TAB', 'CLICK', shift=True, ctrl=True)

    #---------------
    # Snapping Menu
    #---------------
    kmi = km.keymap_items.new('wm.call_menu', 'S', 'CLICK', shift=True)
    kmi.properties.name = 'VIEW3D_MT_snap'

    #-----------
    # 3d cursor
    #-----------
    kmi = km.keymap_items.new('view3d.cursor3d', 'ACTIONMOUSE', 'CLICK')

    #-------------------
    # Toggle local view
    #-------------------
    kmi = km.keymap_items.new('view3d.localview', 'NUMPAD_SLASH', 'CLICK')

    #--------
    # Layers
    #--------
    """
    kmi = km.keymap_items.new('view3d.layers', 'ACCENT_GRAVE', 'CLICK')
    kmi.properties.nr = 0
    kmi = km.keymap_items.new('view3d.layers', 'ONE', 'CLICK', any=True)
    kmi.properties.nr = 1
    kmi = km.keymap_items.new('view3d.layers', 'TWO', 'CLICK', any=True)
    kmi.properties.nr = 2
    kmi = km.keymap_items.new('view3d.layers', 'THREE', 'CLICK', any=True)
    kmi.properties.nr = 3
    kmi = km.keymap_items.new('view3d.layers', 'FOUR', 'CLICK', any=True)
    kmi.properties.nr = 4
    kmi = km.keymap_items.new('view3d.layers', 'FIVE', 'CLICK', any=True)
    kmi.properties.nr = 5
    kmi = km.keymap_items.new('view3d.layers', 'SIX', 'CLICK', any=True)
    kmi.properties.nr = 6
    kmi = km.keymap_items.new('view3d.layers', 'SEVEN', 'CLICK', any=True)
    kmi.properties.nr = 7
    kmi = km.keymap_items.new('view3d.layers', 'EIGHT', 'CLICK', any=True)
    kmi.properties.nr = 8
    kmi = km.keymap_items.new('view3d.layers', 'NINE', 'CLICK', any=True)
    kmi.properties.nr = 9
    kmi = km.keymap_items.new('view3d.layers', 'ZERO', 'CLICK', any=True)
    kmi.properties.nr = 10
    """

    #------------------
    # Viewport drawing
    #------------------
    kmi = km.keymap_items.new('wm.context_toggle_enum', 'Z', 'PRESS')
    kmi.properties.data_path = 'space_data.viewport_shade'
    kmi.properties.value_1 = 'SOLID'
    kmi.properties.value_2 = 'WIREFRAME'
    
    kmi = km.keymap_items.new('wm.context_menu_enum', 'Z', 'PRESS', alt=True)
    kmi.properties.data_path = 'space_data.viewport_shade'
    
    #-------------
    # Pivot point
    #-------------
    kmi = km.keymap_items.new('wm.context_set_enum', 'COMMA', 'CLICK')
    kmi.properties.data_path = 'space_data.pivot_point'
    kmi.properties.value = 'BOUNDING_BOX_CENTER'
    kmi = km.keymap_items.new('wm.context_set_enum', 'COMMA', 'CLICK', ctrl=True)
    kmi.properties.data_path = 'space_data.pivot_point'
    kmi.properties.value = 'MEDIAN_POINT'
    kmi = km.keymap_items.new('wm.context_toggle', 'COMMA', 'CLICK', alt=True)
    kmi.properties.data_path = 'space_data.use_pivot_point_align'
    kmi = km.keymap_items.new('wm.context_set_enum', 'PERIOD', 'CLICK')
    kmi.properties.data_path = 'space_data.pivot_point'
    kmi.properties.value = 'CURSOR'
    kmi = km.keymap_items.new('wm.context_set_enum', 'PERIOD', 'CLICK', ctrl=True)
    kmi.properties.data_path = 'space_data.pivot_point'
    kmi.properties.value = 'INDIVIDUAL_ORIGINS'
    kmi = km.keymap_items.new('wm.context_set_enum', 'PERIOD', 'CLICK', alt=True)
    kmi.properties.data_path = 'space_data.pivot_point'
    kmi.properties.value = 'ACTIVE_ELEMENT'

    #------
    # Misc
    #------
    kmi = km.keymap_items.new('view3d.clip_border', 'B', 'CLICK', alt=True)
    kmi = km.keymap_items.new('view3d.zoom_border', 'B', 'CLICK', shift=True)
    kmi = km.keymap_items.new('view3d.render_border', 'B', 'CLICK', shift=True)
    kmi = km.keymap_items.new('view3d.camera_to_view', 'NUMPAD_0', 'CLICK', ctrl=True, alt=True)
    kmi = km.keymap_items.new('view3d.object_as_camera', 'NUMPAD_0', 'CLICK', ctrl=True)
    

def MapAdd_View3D_Object_Nonmodal(kc):
    """ Object Non-modal Map
        This essentially applies globally within the 3d view.  But technically
        only when objects are involved (but when are they not...?).
    """
    km = kc.keymaps.new('Object Non-modal', space_type='EMPTY', region_type='WINDOW', modal=False)
    
    # Mode switching
    kmi = km.keymap_items.new('wm.call_menu', 'SPACE', 'PRESS')
    kmi.properties.name = 'OBJECT_MT_mode_switch_menu'


def MapAdd_View3D_ObjectMode(kc):
    """ Object Mode Map
    """
    km = kc.keymaps.new('Object Mode', space_type='EMPTY', region_type='WINDOW', modal=False)

    # Delete
    kmi = km.keymap_items.new('object.delete_no_confirm', 'X', 'CLICK')
    kmi = km.keymap_items.new('object.delete_no_confirm', 'DEL', 'CLICK')

    # Proportional editing
    kmi = km.keymap_items.new('wm.context_toggle', 'O', 'PRESS')
    kmi.properties.data_path = 'tool_settings.use_proportional_edit_objects'
    kmi = km.keymap_items.new('wm.context_cycle_enum', 'O', 'PRESS', shift=True)
    kmi.properties.data_path = 'tool_settings.proportional_edit_falloff'
    
    # Game engine start
    kmi = km.keymap_items.new('view3d.game_start', 'P', 'PRESS')
    
    # Selection
    kmi = km.keymap_items.new('object.select_all', 'A', 'PRESS')
    kmi.properties.action = 'TOGGLE'
    kmi = km.keymap_items.new('object.select_all', 'I', 'PRESS', ctrl=True)
    kmi.properties.action = 'INVERT'
    kmi = km.keymap_items.new('object.select_linked', 'L', 'PRESS', shift=True)
    kmi = km.keymap_items.new('object.select_grouped', 'G', 'PRESS', shift=True)
    kmi = km.keymap_items.new('object.select_mirror', 'M', 'PRESS', shift=True, ctrl=True)
    kmi = km.keymap_items.new('object.select_hierarchy', 'LEFT_BRACKET', 'PRESS')
    kmi.properties.direction = 'PARENT'
    kmi.properties.extend = False
    kmi = km.keymap_items.new('object.select_hierarchy', 'LEFT_BRACKET', 'PRESS', shift=True)
    kmi.properties.direction = 'PARENT'
    kmi.properties.extend = True
    kmi = km.keymap_items.new('object.select_hierarchy', 'RIGHT_BRACKET', 'PRESS')
    kmi.properties.direction = 'CHILD'
    kmi.properties.extend = False
    kmi = km.keymap_items.new('object.select_hierarchy', 'RIGHT_BRACKET', 'PRESS', shift=True)
    kmi.properties.direction = 'CHILD'
    kmi.properties.extend = True
    
    # Parenting
    kmi = km.keymap_items.new('object.parent_set', 'P', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('object.parent_no_inverse_set', 'P', 'PRESS', shift=True, ctrl=True)
    kmi = km.keymap_items.new('object.parent_clear', 'P', 'PRESS', alt=True)

    # Constraints
    kmi = km.keymap_items.new('object.constraint_add_with_targets', 'C', 'PRESS', shift=True, ctrl=True)
    kmi = km.keymap_items.new('object.constraints_clear', 'C', 'PRESS', ctrl=True, alt=True)
    
    # Transforms
    kmi = km.keymap_items.new('object.location_clear', TRANSLATE_KEY, 'PRESS', alt=True)
    kmi = km.keymap_items.new('object.rotation_clear', ROTATE_KEY, 'PRESS', alt=True)
    kmi = km.keymap_items.new('object.scale_clear', SCALE_KEY, 'PRESS', alt=True)
    kmi = km.keymap_items.new('object.origin_clear', 'O', 'PRESS', alt=True)
    
    # Hiding
    kmi = km.keymap_items.new('object.hide_view_set', 'H', 'PRESS') # Hide selected
    kmi.properties.unselected = False
    kmi = km.keymap_items.new('object.hide_view_set', 'H', 'PRESS', shift=True) # Hide unselected
    kmi.properties.unselected = True
    kmi = km.keymap_items.new('object.hide_view_clear', 'H', 'PRESS', alt=True) # Unhide
    
    #kmi = km.keymap_items.new('object.hide_render_set', 'H', 'PRESS', ctrl=True)
    #kmi = km.keymap_items.new('object.hide_render_clear', 'H', 'PRESS', ctrl=True, alt=True)
    
    
    # Layer management
    kmi = km.keymap_items.new('object.move_to_layer', 'M', 'PRESS')

    # Add menus
    kmi = km.keymap_items.new('wm.call_menu', 'A', 'PRESS', shift=True)
    kmi.properties.name = 'INFO_MT_add'
    kmi = km.keymap_items.new('wm.call_menu', 'L', 'PRESS', ctrl=True)
    kmi.properties.name = 'VIEW3D_MT_make_links'
    
    # Duplication
    kmi = km.keymap_items.new('object.duplicate_move', 'D', 'PRESS', shift=True)
    kmi = km.keymap_items.new('object.duplicate_move_linked', 'D', 'PRESS', alt=True)
    kmi = km.keymap_items.new('object.duplicates_make_real', 'A', 'PRESS', shift=True, ctrl=True)
    kmi = km.keymap_items.new('wm.call_menu', 'U', 'PRESS')
    kmi.properties.name = 'VIEW3D_MT_make_single_user'
    
    # Apply menu
    kmi = km.keymap_items.new('wm.call_menu', 'A', 'PRESS', ctrl=True)
    kmi.properties.name = 'VIEW3D_MT_object_apply'
    
    # Groups
    kmi = km.keymap_items.new('group.create', 'G', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('group.objects_remove', 'G', 'PRESS', ctrl=True, alt=True)
    kmi = km.keymap_items.new('group.objects_add_active', 'G', 'PRESS', shift=True, ctrl=True)
    kmi = km.keymap_items.new('group.objects_remove_active', 'G', 'PRESS', shift=True, alt=True)

    # Make proxy
    kmi = km.keymap_items.new('object.proxy_make', 'P', 'PRESS', ctrl=True, alt=True)
    
    # Keyframe insertion
    kmi = km.keymap_items.new('anim.keyframe_insert_menu', 'I', 'PRESS')
    kmi = km.keymap_items.new('anim.keyframe_delete_v3d', 'I', 'PRESS', alt=True)
    kmi = km.keymap_items.new('anim.keying_set_active_set', 'I', 'PRESS', shift=True, ctrl=True, alt=True)
    
    # Misc
    kmi = km.keymap_items.new('object.join', 'J', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('object.convert', 'C', 'PRESS', alt=True)
    kmi = km.keymap_items.new('object.make_local', 'L', 'PRESS')
    kmi = km.keymap_items.new('wm.call_menu', SPECIALS_MENU_KEY, 'PRESS')
    kmi.properties.name = 'VIEW3D_MT_object_specials'
    
    # Subdivision surface shortcuts
    #kmi = km.keymap_items.new('object.subdivision_set', 'ZERO', 'PRESS', ctrl=True)
    #kmi.properties.level = 0
    #kmi = km.keymap_items.new('object.subdivision_set', 'ONE', 'PRESS', ctrl=True)
    #kmi.properties.level = 1
    #kmi = km.keymap_items.new('object.subdivision_set', 'TWO', 'PRESS', ctrl=True)
    #kmi.properties.level = 2
    #kmi = km.keymap_items.new('object.subdivision_set', 'THREE', 'PRESS', ctrl=True)
    #kmi.properties.level = 3
    #kmi = km.keymap_items.new('object.subdivision_set', 'FOUR', 'PRESS', ctrl=True)
    #kmi.properties.level = 4
    #kmi = km.keymap_items.new('object.subdivision_set', 'FIVE', 'PRESS', ctrl=True)
    #kmi.properties.level = 5


def MapAdd_View3D_MeshEditMode(kc):
    """ Mesh Edit Mode Map
    """
    km = kc.keymaps.new('Mesh', space_type='EMPTY', region_type='WINDOW', modal=False)

    #---------------------------------
    # Vertex/Edge/Face mode switching
    #---------------------------------
    kmi = km.keymap_items.new('view3d.set_edit_mesh_select_mode', 'ONE', 'PRESS')
    kmi.properties.mode = 'VERT'
    kmi.properties.toggle = False
    kmi = km.keymap_items.new('view3d.set_edit_mesh_select_mode', 'TWO', 'PRESS')
    kmi.properties.mode = 'EDGE'
    kmi.properties.toggle = False
    kmi = km.keymap_items.new('view3d.set_edit_mesh_select_mode', 'THREE', 'PRESS')
    kmi.properties.mode = 'FACE'
    kmi.properties.toggle = False

    kmi = km.keymap_items.new('view3d.set_edit_mesh_select_mode', 'ONE', 'PRESS', shift=True)
    kmi.properties.mode = 'VERT'
    kmi.properties.toggle = True
    kmi = km.keymap_items.new('view3d.set_edit_mesh_select_mode', 'TWO', 'PRESS', shift=True)
    kmi.properties.mode = 'EDGE'
    kmi.properties.toggle = True
    kmi = km.keymap_items.new('view3d.set_edit_mesh_select_mode', 'THREE', 'PRESS', shift=True)
    kmi.properties.mode = 'FACE'
    kmi.properties.toggle = True

    #-----------
    # Selection
    #-----------
    
    # Shortest path
    kmi = km.keymap_items.new('mesh.select_shortest_path', 'LEFTMOUSE', 'CLICK', alt=True) # Replace
    # TODO: add, remove
    
    # Edge loop
    kmi = km.keymap_items.new('mesh.loop_select', 'LEFTMOUSE', 'DOUBLE_CLICK') # Replace
    kmi.properties.extend = False
    kmi.properties.deselect = False
    kmi = km.keymap_items.new('mesh.loop_select', 'LEFTMOUSE', 'DOUBLE_CLICK', shift=True) # Add
    kmi.properties.extend = True
    kmi.properties.deselect = False
    kmi = km.keymap_items.new('mesh.loop_select', 'LEFTMOUSE', 'DOUBLE_CLICK', ctrl=True) # Remove
    kmi.properties.extend = False
    kmi.properties.deselect = True
    
    # Edge ring
    kmi = km.keymap_items.new('mesh.edgering_select', 'LEFTMOUSE', 'DOUBLE_CLICK', alt=True) # Replace
    kmi.properties.extend = False
    kmi.properties.deselect = False
    kmi = km.keymap_items.new('mesh.edgering_select', 'LEFTMOUSE', 'DOUBLE_CLICK', alt=True, shift=True) # Add
    kmi.properties.extend = True
    kmi.properties.deselect = False
    kmi = km.keymap_items.new('mesh.edgering_select', 'LEFTMOUSE', 'DOUBLE_CLICK', alt=True, ctrl=True) # Remove
    kmi.properties.extend = False
    kmi.properties.deselect = True
    
    kmi = km.keymap_items.new('mesh.select_all', 'A', 'PRESS')
    kmi.properties.action = 'TOGGLE'
    kmi = km.keymap_items.new('mesh.select_all', 'I', 'CLICK', ctrl=True)
    kmi.properties.action = 'INVERT'
    kmi = km.keymap_items.new('mesh.select_more', 'NUMPAD_PLUS', 'CLICK', ctrl=True)
    kmi = km.keymap_items.new('mesh.select_less', 'NUMPAD_MINUS', 'CLICK', ctrl=True)
    kmi = km.keymap_items.new('mesh.select_non_manifold', 'M', 'CLICK', shift=True, ctrl=True, alt=True)
    kmi = km.keymap_items.new('mesh.select_linked', 'L', 'CLICK', ctrl=True)
    kmi = km.keymap_items.new('mesh.select_linked_pick', 'L', 'CLICK')
    kmi.properties.deselect = False
    kmi = km.keymap_items.new('mesh.select_linked_pick', 'L', 'CLICK', shift=True)
    kmi.properties.deselect = True
    kmi = km.keymap_items.new('mesh.faces_select_linked_flat', 'F', 'CLICK', shift=True, ctrl=True, alt=True)
    kmi = km.keymap_items.new('mesh.select_similar', 'G', 'CLICK', shift=True)

    # Proportional editing
    kmi = km.keymap_items.new('wm.context_toggle_enum', 'O', 'CLICK')
    kmi.properties.data_path = 'tool_settings.proportional_edit'
    kmi.properties.value_1 = 'DISABLED'
    kmi.properties.value_2 = 'ENABLED'
    kmi = km.keymap_items.new('wm.context_cycle_enum', 'O', 'CLICK', shift=True)
    kmi.properties.data_path = 'tool_settings.proportional_edit_falloff'
    kmi = km.keymap_items.new('wm.context_toggle_enum', 'O', 'CLICK', alt=True)
    kmi.properties.data_path = 'tool_settings.proportional_edit'
    kmi.properties.value_1 = 'DISABLED'
    kmi.properties.value_2 = 'CONNECTED'

    # Hiding
    kmi = km.keymap_items.new('mesh.hide', 'H', 'CLICK')
    kmi.properties.unselected = False
    kmi = km.keymap_items.new('mesh.hide', 'H', 'CLICK', shift=True)
    kmi.properties.unselected = True
    kmi = km.keymap_items.new('mesh.reveal', 'H', 'CLICK', alt=True)

    #-----------------
    # Create Geometry
    #-----------------
    
    # Add Primitive
    kmi = km.keymap_items.new('wm.call_menu', 'A', 'PRESS', shift=True)
    kmi.properties.name = 'INFO_MT_mesh_add'
    
    # Add edge and face / vertex connect
    kmi = km.keymap_items.new('mesh.edge_face_add', 'C', 'CLICK')
    kmi = kmi = km.keymap_items.new('mesh.vert_connect', 'C', 'CLICK', shift=True)
    
    kmi = km.keymap_items.new('mesh.fill', 'C', 'CLICK', alt=True)
    kmi = km.keymap_items.new('mesh.beautify_fill', 'C', 'CLICK', alt=True, shift=True)
    
    # Subdivide
    kmi = km.keymap_items.new('mesh.subdivide', 'W', 'CLICK')
    
    # Loop cut
    kmi = km.keymap_items.new('mesh.loopcut_slide', 'T', 'CLICK')
    
    # Knife
    kmi = km.keymap_items.new('mesh.knife_tool', 'K', 'CLICK')
    
    # Extrude
    kmi = km.keymap_items.new('view3d.edit_mesh_extrude_move_normal', 'E', 'CLICK')
    kmi = km.keymap_items.new('wm.call_menu', 'E', 'CLICK', alt=True)
    kmi.properties.name = 'VIEW3D_MT_edit_mesh_extrude'
    
    kmi = km.keymap_items.new('mesh.dupli_extrude_cursor', 'ACTIONMOUSE', 'CLICK', ctrl=True)
    kmi.properties.rotate_source = True
    kmi = km.keymap_items.new('mesh.dupli_extrude_cursor', 'ACTIONMOUSE', 'CLICK', shift=True, ctrl=True)
    kmi.properties.rotate_source = False
    
    # Inset/Outset
    kmi = km.keymap_items.new('mesh.inset', 'I', 'CLICK')
    kmi.properties.use_outset = False
    kmi = km.keymap_items.new('mesh.inset', 'I', 'CLICK', shift=True)
    kmi.properties.use_outset = True
    
    # Bevel
    kmi = km.keymap_items.new('mesh.bevel', 'B', 'CLICK')

    # Duplicate
    kmi = km.keymap_items.new('mesh.duplicate_move', 'D', 'CLICK', shift=True)
    
    # Rip
    kmi = km.keymap_items.new('mesh.rip_move', 'R', 'CLICK')
    
    # Split / Separate
    kmi = km.keymap_items.new('mesh.split', 'Y', 'CLICK')
    kmi = km.keymap_items.new('mesh.separate', 'Y', 'CLICK', shift=True)
    

    #-----------------
    # Remove Geometry
    #-----------------

    # Delete/Dissolve
    kmi = km.keymap_items.new('mesh.delete_contextual', 'X', 'CLICK')
    kmi = km.keymap_items.new('mesh.delete_contextual', 'DEL', 'CLICK')
    
    kmi = km.keymap_items.new('mesh.dissolve', 'X', 'CLICK', shift=True)
    kmi.properties.use_verts = True
    kmi = km.keymap_items.new('mesh.dissolve', 'DEL', 'CLICK', shift=True)
    kmi.properties.use_verts = True
    
    kmi = km.keymap_items.new('wm.call_menu', 'X', 'CLICK', alt=True)
    kmi.properties.name = 'VIEW3D_MT_edit_mesh_delete'
    kmi = km.keymap_items.new('wm.call_menu', 'DEL', 'CLICK', alt=True)
    kmi.properties.name = 'VIEW3D_MT_edit_mesh_delete'

    # Merge/collapse
    kmi = km.keymap_items.new('mesh.edge_collapse', 'M', 'CLICK')
    kmi = km.keymap_items.new('mesh.merge', 'M', 'CLICK', alt=True)
    
    #-----------------
    # Deform Geometry
    #-----------------
    
    # Smooth
    kmi = km.keymap_items.new('mesh.vertices_smooth', 'W', 'PRESS', shift=True)
    
    # Shrink / Fatten
    kmi = km.keymap_items.new('transform.shrink_fatten', 'S', 'CLICK', alt=True)
    
    #------
    # Misc
    #------
    
    # Vert/edge properties
    #kmi = km.keymap_items.new('transform.edge_crease', 'E', 'CLICK', shift=True)
    
    # Tri/quad conversion
    #kmi = km.keymap_items.new('mesh.quads_convert_to_tris', 'T', 'CLICK', ctrl=True)
    #kmi = km.keymap_items.new('mesh.quads_convert_to_tris', 'T', 'CLICK', shift=True, ctrl=True)
    #kmi.properties.use_beauty = False
    #kmi = km.keymap_items.new('mesh.tris_convert_to_quads', 'J', 'CLICK', alt=True)

    # Tool Menus
    kmi = km.keymap_items.new('wm.call_menu', SPECIALS_MENU_KEY, 'CLICK')
    kmi.properties.name = 'VIEW3D_MT_edit_mesh_specials'
    kmi = km.keymap_items.new('wm.call_menu', 'ONE', 'CLICK', alt=True)
    kmi.properties.name = 'VIEW3D_MT_edit_mesh_vertices'
    kmi = km.keymap_items.new('wm.call_menu', 'TWO', 'CLICK', alt=True)
    kmi.properties.name = 'VIEW3D_MT_edit_mesh_edges'
    kmi = km.keymap_items.new('wm.call_menu', 'THREE', 'CLICK', alt=True)
    kmi.properties.name = 'VIEW3D_MT_edit_mesh_faces'

    # UV's
    kmi = km.keymap_items.new('wm.call_menu', 'U', 'CLICK')
    kmi.properties.name = 'VIEW3D_MT_uv_map'

    # Calculate normals
    kmi = km.keymap_items.new('mesh.normals_make_consistent', 'N', 'CLICK', ctrl=True)
    kmi.properties.inside = False
    kmi = km.keymap_items.new('mesh.normals_make_consistent', 'N', 'CLICK', shift=True, ctrl=True)
    kmi.properties.inside = True

    # Subsurf shortcuts
    if SUBSURF_RELATIVE:
        kmi = km.keymap_items.new('object.shift_subsurf_level', 'EQUAL', 'PRESS')
        kmi.properties.delta = 1
        kmi.properties.max = 4
        kmi = km.keymap_items.new('object.shift_subsurf_level', 'MINUS', 'PRESS')
        kmi.properties.delta = -1
        kmi.properties.min = 0
    else:
        kmi = km.keymap_items.new('object.subdivision_set', 'ZERO', 'CLICK', ctrl=True)
        kmi.properties.level = 0
        kmi = km.keymap_items.new('object.subdivision_set', 'ONE', 'CLICK', ctrl=True)
        kmi.properties.level = 1
        kmi = km.keymap_items.new('object.subdivision_set', 'TWO', 'CLICK', ctrl=True)
        kmi.properties.level = 2
        kmi = km.keymap_items.new('object.subdivision_set', 'THREE', 'CLICK', ctrl=True)
        kmi.properties.level = 3
        kmi = km.keymap_items.new('object.subdivision_set', 'FOUR', 'CLICK', ctrl=True)
        kmi.properties.level = 4
        kmi = km.keymap_items.new('object.subdivision_set', 'FIVE', 'CLICK', ctrl=True)
        kmi.properties.level = 5

    # Rigging
    kmi = km.keymap_items.new('object.vertex_parent_set', 'P', 'CLICK', ctrl=True)
    kmi = km.keymap_items.new('wm.call_menu', 'H', 'CLICK', ctrl=True)
    kmi.properties.name = 'VIEW3D_MT_hook'
    kmi = km.keymap_items.new('wm.call_menu', 'G', 'CLICK', ctrl=True)
    kmi.properties.name = 'VIEW3D_MT_vertex_group'


def MapAdd_ModalStandard(kc):
    """ Standard Modal Map
        Super basic modal stuff that applies globally in Blender.
    """
    km = kc.keymaps.new('Standard Modal Map', space_type='EMPTY', region_type='WINDOW', modal=True)

    kmi = km.keymap_items.new_modal('CANCEL', 'ESC', 'PRESS', any=True)
    kmi = km.keymap_items.new_modal('APPLY', 'LEFTMOUSE', 'ANY', any=True)
    kmi = km.keymap_items.new_modal('APPLY', 'RET', 'PRESS', any=True)
    kmi = km.keymap_items.new_modal('APPLY', 'NUMPAD_ENTER', 'PRESS', any=True)
    kmi = km.keymap_items.new_modal('STEP10', 'LEFT_CTRL', 'PRESS', any=True)
    kmi = km.keymap_items.new_modal('STEP10_OFF', 'LEFT_CTRL', 'RELEASE', any=True)


def MapAdd_ModalTransform(kc):
    """ Transform Modal Map
        Keys for when the user is in a transform mode, such as grab/rotate/scale.
    """
    km = kc.keymaps.new('Transform Modal Map', space_type='EMPTY', region_type='WINDOW', modal=True)

    # Cancel
    kmi = km.keymap_items.new_modal('CANCEL', 'ESC', 'PRESS', any=True)

    # Confirm
    kmi = km.keymap_items.new_modal('CONFIRM', 'LEFTMOUSE', 'PRESS', any=True)
    kmi = km.keymap_items.new_modal('CONFIRM', 'RET', 'CLICK', any=True)
    kmi = km.keymap_items.new_modal('CONFIRM', 'NUMPAD_ENTER', 'CLICK', any=True)

    # Snapping
    kmi = km.keymap_items.new_modal('SNAP_TOGGLE', 'TAB', 'PRESS', shift=True)
    kmi = km.keymap_items.new_modal('SNAP_INV_ON', 'LEFT_CTRL', 'PRESS', any=True)
    kmi = km.keymap_items.new_modal('SNAP_INV_OFF', 'LEFT_CTRL', 'RELEASE', any=True)
    kmi = km.keymap_items.new_modal('SNAP_INV_ON', 'RIGHT_CTRL', 'PRESS', any=True)
    kmi = km.keymap_items.new_modal('SNAP_INV_OFF', 'RIGHT_CTRL', 'RELEASE', any=True)
    kmi = km.keymap_items.new_modal('ADD_SNAP', 'A', 'CLICK')
    kmi = km.keymap_items.new_modal('REMOVE_SNAP', 'A', 'CLICK', alt=True)

    # Proportional edit adjusting
    kmi = km.keymap_items.new_modal('PROPORTIONAL_SIZE_UP', 'PAGE_UP', 'PRESS')
    kmi = km.keymap_items.new_modal('PROPORTIONAL_SIZE_DOWN', 'PAGE_DOWN', 'PRESS')
    kmi = km.keymap_items.new_modal('PROPORTIONAL_SIZE_UP', 'WHEELDOWNMOUSE', 'PRESS')
    kmi = km.keymap_items.new_modal('PROPORTIONAL_SIZE_DOWN', 'WHEELUPMOUSE', 'PRESS')

    # Auto-ik adjusting
    kmi = km.keymap_items.new_modal('AUTOIK_CHAIN_LEN_UP', 'PAGE_UP', 'PRESS', shift=True)
    kmi = km.keymap_items.new_modal('AUTOIK_CHAIN_LEN_DOWN', 'PAGE_DOWN', 'PRESS', shift=True)
    kmi = km.keymap_items.new_modal('AUTOIK_CHAIN_LEN_UP', 'WHEELDOWNMOUSE', 'PRESS', shift=True)
    kmi = km.keymap_items.new_modal('AUTOIK_CHAIN_LEN_DOWN', 'WHEELUPMOUSE', 'PRESS', shift=True)

    # Constraining to axes
    kmi = km.keymap_items.new_modal('AXIS_X', 'X', 'CLICK')
    kmi = km.keymap_items.new_modal('AXIS_Y', 'Y', 'CLICK')
    kmi = km.keymap_items.new_modal('AXIS_Z', 'Z', 'CLICK')
    kmi = km.keymap_items.new_modal('PLANE_X', 'X', 'CLICK', shift=True)
    kmi = km.keymap_items.new_modal('PLANE_Y', 'Y', 'CLICK', shift=True)
    kmi = km.keymap_items.new_modal('PLANE_Z', 'Z', 'CLICK', shift=True)

    # Overrides ("No, really, actually translate") and trackball rotate
    kmi = km.keymap_items.new_modal('TRANSLATE', TRANSLATE_KEY, 'PRESS')
    kmi = km.keymap_items.new_modal('ROTATE', ROTATE_KEY, 'PRESS')
    kmi = km.keymap_items.new_modal('RESIZE', SCALE_KEY, 'PRESS')


def MapAdd_ModalBorderSelect(kc):
    """ Border Select Modal Map
        Determines behavior when in border select tool.
    """
    km = kc.keymaps.new('Gesture Border', space_type='EMPTY', region_type='WINDOW', modal=True)

    kmi = km.keymap_items.new_modal('CANCEL', 'ESC', 'PRESS', any=True)

    kmi = km.keymap_items.new_modal('BEGIN', 'LEFTMOUSE', 'PRESS')
    kmi = km.keymap_items.new_modal('SELECT', 'LEFTMOUSE', 'RELEASE')
    kmi = km.keymap_items.new_modal('SELECT', 'LEFTMOUSE', 'RELEASE', shift=True)
    kmi = km.keymap_items.new_modal('DESELECT', 'LEFTMOUSE', 'RELEASE', ctrl=True)







def MapAdd_FileBrowserGlobal(kc):
    # Map File Browser
    km = kc.keymaps.new('File Browser', space_type='FILE_BROWSER', region_type='WINDOW', modal=False)

    kmi = km.keymap_items.new('file.bookmark_toggle', 'N', 'PRESS')
    kmi = km.keymap_items.new('file.parent', 'P', 'PRESS')
    kmi = km.keymap_items.new('file.bookmark_add', 'B', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('file.hidedot', 'H', 'PRESS')
    kmi = km.keymap_items.new('file.previous', 'BACK_SPACE', 'PRESS')
    kmi = km.keymap_items.new('file.next', 'BACK_SPACE', 'PRESS', shift=True)
    kmi = km.keymap_items.new('file.directory_new', 'I', 'PRESS')
    kmi = km.keymap_items.new('file.delete', 'X', 'PRESS')
    kmi = km.keymap_items.new('file.delete', 'DEL', 'PRESS')
    kmi = km.keymap_items.new('file.smoothscroll', 'TIMER1', 'ANY', any=True)

def MapAdd_FileBrowserMain(kc):
    # Map File Browser Main
    km = kc.keymaps.new('File Browser Main', space_type='FILE_BROWSER', region_type='WINDOW', modal=False)

    kmi = km.keymap_items.new('file.execute', 'LEFTMOUSE', 'DOUBLE_CLICK')
    kmi.properties.need_active = True
    kmi = km.keymap_items.new('file.select', 'LEFTMOUSE', 'CLICK')
    kmi = km.keymap_items.new('file.select', 'LEFTMOUSE', 'CLICK', shift=True)
    kmi.properties.extend = True
    kmi = km.keymap_items.new('file.select', 'LEFTMOUSE', 'CLICK', alt=True)
    kmi.properties.extend = True
    kmi.properties.fill = True
    kmi = km.keymap_items.new('file.select_all_toggle', 'A', 'PRESS')
    kmi = km.keymap_items.new('file.refresh', 'NUMPAD_PERIOD', 'PRESS')
    kmi = km.keymap_items.new('file.select_border', 'B', 'PRESS')
    kmi = km.keymap_items.new('file.select_border', 'EVT_TWEAK_L', 'ANY')
    kmi = km.keymap_items.new('file.rename', 'LEFTMOUSE', 'PRESS', ctrl=True)
    kmi = km.keymap_items.new('file.highlight', 'MOUSEMOVE', 'ANY', any=True)
    kmi = km.keymap_items.new('file.filenum', 'NUMPAD_PLUS', 'PRESS')
    kmi.properties.increment = 1
    kmi = km.keymap_items.new('file.filenum', 'NUMPAD_PLUS', 'PRESS', shift=True)
    kmi.properties.increment = 10
    kmi = km.keymap_items.new('file.filenum', 'NUMPAD_PLUS', 'PRESS', ctrl=True)
    kmi.properties.increment = 100
    kmi = km.keymap_items.new('file.filenum', 'NUMPAD_MINUS', 'PRESS')
    kmi.properties.increment = -1
    kmi = km.keymap_items.new('file.filenum', 'NUMPAD_MINUS', 'PRESS', shift=True)
    kmi.properties.increment = -10
    kmi = km.keymap_items.new('file.filenum', 'NUMPAD_MINUS', 'PRESS', ctrl=True)
    kmi.properties.increment = -100

def MapAdd_FileBrowserButtons(kc):
    # Map File Browser Buttons
    km = kc.keymaps.new('File Browser Buttons', space_type='FILE_BROWSER', region_type='WINDOW', modal=False)

    kmi = km.keymap_items.new('file.filenum', 'NUMPAD_PLUS', 'PRESS')
    kmi.properties.increment = 1
    kmi = km.keymap_items.new('file.filenum', 'NUMPAD_PLUS', 'PRESS', shift=True)
    kmi.properties.increment = 10
    kmi = km.keymap_items.new('file.filenum', 'NUMPAD_PLUS', 'PRESS', ctrl=True)
    kmi.properties.increment = 100
    kmi = km.keymap_items.new('file.filenum', 'NUMPAD_MINUS', 'PRESS')
    kmi.properties.increment = -1
    kmi = km.keymap_items.new('file.filenum', 'NUMPAD_MINUS', 'PRESS', shift=True)
    kmi.properties.increment = -10
    kmi = km.keymap_items.new('file.filenum', 'NUMPAD_MINUS', 'PRESS', ctrl=True)
    kmi.properties.increment = -100









wm = bpy.context.window_manager
kc = wm.keyconfigs.new('Blender 2012 (experimental!)')

clear_keymap(kc)

MapAdd_Window(kc)
MapAdd_Screen(kc)

MapAdd_View2D(kc)

MapAdd_View3D_Global(kc)
MapAdd_View3D_Object_Nonmodal(kc)
MapAdd_View3D_ObjectMode(kc)
MapAdd_View3D_MeshEditMode(kc)

MapAdd_ModalStandard(kc)
MapAdd_ModalTransform(kc)
MapAdd_ModalBorderSelect(kc)

MapAdd_FileBrowserGlobal(kc)
MapAdd_FileBrowserMain(kc)
MapAdd_FileBrowserButtons(kc)











