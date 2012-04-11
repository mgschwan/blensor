""" An experimental new keymap for Blender.
    Work in progress!
"""
import bpy

###############################################################
# Some configuration variables to toggle various ideas on/off #
###############################################################
DEVELOPER_HOTKEYS = False  # Weird hotkeys that only developers use

WINDOW_TYPE_SWITCHING = False  # Shift-f# hotkeys for switching window types

SUBSURF_RELATIVE = True  # Make subsurf hotkeys work by relative
                         # shifting instead of absolute setting

MAYA_STYLE_MANIPULATORS = False  # Maya-style "QWER" hotkeys for manipulators




###############################
# Custom operators/menus/etc. #
###############################

class ShiftSubsurfLevel(bpy.types.Operator):
    ''' Shifts the subsurf level of the selected objects up or
        down by the given amount.  Has maximum limit, to avoid
        going crazy and running out of RAM.
    '''
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


class SetManipulator(bpy.types.Operator):
    '''Set's the manipulator mode.'''
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
# Work around
bpy.ops.object.mode_set(mode='OBJECT', toggle=False)  # XXX, WHY IS THE KEYMAP DOING THIS? - campbell






######################################################################
######################################################################
############### KEYMAP BEGINS ########################################
######################################################################
######################################################################
wm = bpy.context.window_manager
kc = wm.keyconfigs.new('Blender 2012 (experimental!)')


##############
# Map Window #
##############
km = kc.keymaps.new('Window', space_type='EMPTY', region_type='WINDOW', modal=False)

#------
# Quit
#------
kmi = km.keymap_items.new('wm.quit_blender', 'Q', 'PRESS', ctrl=True)

#----------------------
# Operator search menu
#----------------------
kmi = km.keymap_items.new('wm.search_menu', 'TAB', 'PRESS')

#-----------------
# File management
#-----------------
# Open
kmi = km.keymap_items.new('wm.read_homefile', 'N', 'PRESS', ctrl=True)
kmi = km.keymap_items.new('wm.save_homefile', 'U', 'PRESS', ctrl=True)
kmi = km.keymap_items.new('wm.open_mainfile', 'O', 'PRESS', ctrl=True)
kmi = km.keymap_items.new('wm.link_append', 'O', 'PRESS', ctrl=True, alt=True)

# Save
kmi = km.keymap_items.new('wm.save_mainfile', 'S', 'PRESS', ctrl=True)
kmi = km.keymap_items.new('wm.save_as_mainfile', 'S', 'PRESS', shift=True, ctrl=True)

#------------------
# Window switching
#------------------
if WINDOW_TYPE_SWITCHING:
    kmi = km.keymap_items.new('wm.context_set_enum', 'F2', 'PRESS', shift=True)
    kmi.properties.data_path = 'area.type'
    kmi.properties.value = 'LOGIC_EDITOR'
    kmi = km.keymap_items.new('wm.context_set_enum', 'F3', 'PRESS', shift=True)
    kmi.properties.data_path = 'area.type'
    kmi.properties.value = 'NODE_EDITOR'
    kmi = km.keymap_items.new('wm.context_set_enum', 'F4', 'PRESS', shift=True)
    kmi.properties.data_path = 'area.type'
    kmi.properties.value = 'CONSOLE'
    kmi = km.keymap_items.new('wm.context_set_enum', 'F5', 'PRESS', shift=True)
    kmi.properties.data_path = 'area.type'
    kmi.properties.value = 'VIEW_3D'
    kmi = km.keymap_items.new('wm.context_set_enum', 'F6', 'PRESS', shift=True)
    kmi.properties.data_path = 'area.type'
    kmi.properties.value = 'GRAPH_EDITOR'
    kmi = km.keymap_items.new('wm.context_set_enum', 'F7', 'PRESS', shift=True)
    kmi.properties.data_path = 'area.type'
    kmi.properties.value = 'PROPERTIES'
    kmi = km.keymap_items.new('wm.context_set_enum', 'F8', 'PRESS', shift=True)
    kmi.properties.data_path = 'area.type'
    kmi.properties.value = 'SEQUENCE_EDITOR'
    kmi = km.keymap_items.new('wm.context_set_enum', 'F9', 'PRESS', shift=True)
    kmi.properties.data_path = 'area.type'
    kmi.properties.value = 'OUTLINER'
    kmi = km.keymap_items.new('wm.context_set_enum', 'F10', 'PRESS', shift=True)
    kmi.properties.data_path = 'area.type'
    kmi.properties.value = 'IMAGE_EDITOR'
    kmi = km.keymap_items.new('wm.context_set_enum', 'F11', 'PRESS', shift=True)
    kmi.properties.data_path = 'area.type'
    kmi.properties.value = 'TEXT_EDITOR'
    kmi = km.keymap_items.new('wm.context_set_enum', 'F12', 'PRESS', shift=True)
    kmi.properties.data_path = 'area.type'
    kmi.properties.value = 'DOPESHEET_EDITOR'

#-------------
# NDof Device
#-------------
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

#------
# Misc
#------
kmi = km.keymap_items.new('wm.window_fullscreen_toggle', 'F11', 'PRESS', alt=True)

#-----------------------
# Development/debugging
#-----------------------
if DEVELOPER_HOTKEYS:
    kmi = km.keymap_items.new('wm.redraw_timer', 'T', 'PRESS', ctrl=True, alt=True)
    kmi = km.keymap_items.new('wm.debug_menu', 'D', 'PRESS', ctrl=True, alt=True)

#-----
# ???
#-----
kmi = km.keymap_items.new('info.reports_display_update', 'TIMER', 'ANY', any=True)




##################
# 3D View Global #
##################
km = kc.keymaps.new('3D View', space_type='VIEW_3D', region_type='WINDOW', modal=False)

#-----------------
# View navigation
#-----------------
# ???
kmi = km.keymap_items.new('view3d.rotate', 'MOUSEROTATE', 'ANY')
kmi = km.keymap_items.new('view3d.smoothview', 'TIMER1', 'ANY', any=True)

# Perspective/ortho
kmi = km.keymap_items.new('view3d.view_persportho', 'NUMPAD_5', 'PRESS')

# Camera view
kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_0', 'PRESS')
kmi.properties.type = 'CAMERA'

# Basics with mouse
kmi = km.keymap_items.new('view3d.rotate', 'MIDDLEMOUSE', 'PRESS')
kmi = km.keymap_items.new('view3d.move', 'MIDDLEMOUSE', 'PRESS', shift=True)
kmi = km.keymap_items.new('view3d.zoom', 'MIDDLEMOUSE', 'PRESS', ctrl=True)
kmi = km.keymap_items.new('view3d.dolly', 'MIDDLEMOUSE', 'PRESS', shift=True, ctrl=True)

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

# Basics with numpad
kmi = km.keymap_items.new('view3d.view_orbit', 'NUMPAD_8', 'PRESS')
kmi.properties.type = 'ORBITUP'
kmi = km.keymap_items.new('view3d.view_orbit', 'NUMPAD_2', 'PRESS')
kmi.properties.type = 'ORBITDOWN'
kmi = km.keymap_items.new('view3d.view_orbit', 'NUMPAD_4', 'PRESS')
kmi.properties.type = 'ORBITLEFT'
kmi = km.keymap_items.new('view3d.view_orbit', 'NUMPAD_6', 'PRESS')
kmi.properties.type = 'ORBITRIGHT'
kmi = km.keymap_items.new('view3d.view_pan', 'NUMPAD_8', 'PRESS', ctrl=True)
kmi.properties.type = 'PANUP'
kmi = km.keymap_items.new('view3d.view_pan', 'NUMPAD_2', 'PRESS', ctrl=True)
kmi.properties.type = 'PANDOWN'
kmi = km.keymap_items.new('view3d.view_pan', 'NUMPAD_4', 'PRESS', ctrl=True)
kmi.properties.type = 'PANLEFT'
kmi = km.keymap_items.new('view3d.view_pan', 'NUMPAD_6', 'PRESS', ctrl=True)
kmi.properties.type = 'PANRIGHT'
kmi = km.keymap_items.new('view3d.zoom', 'NUMPAD_PLUS', 'PRESS')
kmi.properties.delta = 1
kmi = km.keymap_items.new('view3d.zoom', 'NUMPAD_MINUS', 'PRESS')
kmi.properties.delta = -1

# Zoom in/out alternatives
kmi = km.keymap_items.new('view3d.zoom', 'EQUAL', 'PRESS', ctrl=True)
kmi.properties.delta = 1
kmi = km.keymap_items.new('view3d.zoom', 'MINUS', 'PRESS', ctrl=True)
kmi.properties.delta = -1

# Front/Right/Top/Back/Left/Bottom
kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_1', 'PRESS')
kmi.properties.type = 'FRONT'
kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_3', 'PRESS')
kmi.properties.type = 'RIGHT'
kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_7', 'PRESS')
kmi.properties.type = 'TOP'
kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_1', 'PRESS', ctrl=True)
kmi.properties.type = 'BACK'
kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_3', 'PRESS', ctrl=True)
kmi.properties.type = 'LEFT'
kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_7', 'PRESS', ctrl=True)
kmi.properties.type = 'BOTTOM'

# Selection-aligned Front/Right/Top/Back/Left/Bottom
kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_1', 'PRESS', shift=True)
kmi.properties.type = 'FRONT'
kmi.properties.align_active = True
kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_3', 'PRESS', shift=True)
kmi.properties.type = 'RIGHT'
kmi.properties.align_active = True
kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_7', 'PRESS', shift=True)
kmi.properties.type = 'TOP'
kmi.properties.align_active = True
kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_1', 'PRESS', shift=True, ctrl=True)
kmi.properties.type = 'BACK'
kmi.properties.align_active = True
kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_3', 'PRESS', shift=True, ctrl=True)
kmi.properties.type = 'LEFT'
kmi.properties.align_active = True
kmi = km.keymap_items.new('view3d.viewnumpad', 'NUMPAD_7', 'PRESS', shift=True, ctrl=True)
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
kmi = km.keymap_items.new('view3d.fly', 'F', 'PRESS', shift=True)

# Misc
kmi = km.keymap_items.new('view3d.view_selected', 'NUMPAD_PERIOD', 'PRESS')
kmi = km.keymap_items.new('view3d.view_center_cursor', 'NUMPAD_PERIOD', 'PRESS', ctrl=True)
kmi = km.keymap_items.new('view3d.zoom_camera_1_to_1', 'NUMPAD_ENTER', 'PRESS', shift=True)
kmi = km.keymap_items.new('view3d.view_center_camera', 'HOME', 'PRESS')
kmi = km.keymap_items.new('view3d.view_all', 'HOME', 'PRESS')
kmi.properties.center = False
kmi = km.keymap_items.new('view3d.view_all', 'C', 'PRESS', shift=True)
kmi.properties.center = True

#-----------
# Selection
#-----------
# Click select
kmi = km.keymap_items.new('view3d.select', 'SELECTMOUSE', 'PRESS')
kmi.properties.extend = False
kmi.properties.center = False
kmi.properties.enumerate = False
kmi.properties.object = False
kmi = km.keymap_items.new('view3d.select', 'SELECTMOUSE', 'PRESS', shift=True)
kmi.properties.extend = True
kmi.properties.center = False
kmi.properties.enumerate = False
kmi.properties.object = False
kmi = km.keymap_items.new('view3d.select', 'SELECTMOUSE', 'PRESS', ctrl=True)
kmi.properties.extend = False
kmi.properties.center = True
kmi.properties.enumerate = False
kmi.properties.object = True
kmi = km.keymap_items.new('view3d.select', 'SELECTMOUSE', 'PRESS', alt=True)
kmi.properties.extend = False
kmi.properties.center = False
kmi.properties.enumerate = True
kmi.properties.object = False
kmi = km.keymap_items.new('view3d.select', 'SELECTMOUSE', 'PRESS', shift=True, ctrl=True)
kmi.properties.extend = True
kmi.properties.center = True
kmi.properties.enumerate = False
kmi.properties.object = False
kmi = km.keymap_items.new('view3d.select', 'SELECTMOUSE', 'PRESS', ctrl=True, alt=True)
kmi.properties.extend = False
kmi.properties.center = True
kmi.properties.enumerate = True
kmi.properties.object = False
kmi = km.keymap_items.new('view3d.select', 'SELECTMOUSE', 'PRESS', shift=True, alt=True)
kmi.properties.extend = True
kmi.properties.center = False
kmi.properties.enumerate = True
kmi.properties.object = False
kmi = km.keymap_items.new('view3d.select', 'SELECTMOUSE', 'PRESS', shift=True, ctrl=True, alt=True)
kmi.properties.extend = True
kmi.properties.center = True
kmi.properties.enumerate = True
kmi.properties.object = False

# Box select
kmi = km.keymap_items.new('view3d.select_border', 'B', 'PRESS')

# Lasso select
kmi = km.keymap_items.new('view3d.select_lasso', 'EVT_TWEAK_A', 'ANY', ctrl=True)
kmi.properties.deselect = False
kmi = km.keymap_items.new('view3d.select_lasso', 'EVT_TWEAK_A', 'ANY', shift=True, ctrl=True)
kmi.properties.deselect = True

# Paint select
kmi = km.keymap_items.new('view3d.select_circle', 'C', 'PRESS')

#-------------
# Manipulator
#-------------
kmi = km.keymap_items.new('view3d.manipulator', 'LEFTMOUSE', 'PRESS', any=True)
kmi.properties.release_confirm = True

if MAYA_STYLE_MANIPULATORS:
    kmi = km.keymap_items.new('view3d.manipulator_set', 'Q', 'PRESS')
    kmi.properties.mode = 'NONE'
    kmi = km.keymap_items.new('view3d.manipulator_set', 'W', 'PRESS')
    kmi.properties.mode = 'TRANSLATE'
    kmi = km.keymap_items.new('view3d.manipulator_set', 'E', 'PRESS')
    kmi.properties.mode = 'ROTATE'
    kmi = km.keymap_items.new('view3d.manipulator_set', 'R', 'PRESS')
    kmi.properties.mode = 'SCALE'
else:
    kmi = km.keymap_items.new('wm.context_toggle', 'SPACE', 'PRESS', ctrl=True)
    kmi.properties.data_path = 'space_data.show_manipulator'

#-----------------------
# Transforms via hotkey
#-----------------------
# Grab, rotate scale
kmi = km.keymap_items.new('transform.translate', 'G', 'PRESS')
kmi = km.keymap_items.new('transform.translate', 'EVT_TWEAK_S', 'ANY')
kmi = km.keymap_items.new('transform.rotate', 'R', 'PRESS')
kmi = km.keymap_items.new('transform.resize', 'S', 'PRESS')

# Mirror, shear, warp, to-sphere
kmi = km.keymap_items.new('transform.mirror', 'M', 'PRESS', ctrl=True)
kmi = km.keymap_items.new('transform.shear', 'S', 'PRESS', shift=True, ctrl=True, alt=True)
kmi = km.keymap_items.new('transform.warp', 'W', 'PRESS', shift=True)
kmi = km.keymap_items.new('transform.tosphere', 'S', 'PRESS', shift=True, alt=True)

#-------------------------
# Transform texture space
#-------------------------
kmi = km.keymap_items.new('transform.translate', 'T', 'PRESS', shift=True)
kmi.properties.texture_space = True
kmi = km.keymap_items.new('transform.resize', 'T', 'PRESS', shift=True, alt=True)
kmi.properties.texture_space = True

#------------------
# Transform spaces
#------------------
kmi = km.keymap_items.new('transform.select_orientation', 'SPACE', 'PRESS', alt=True)
kmi = km.keymap_items.new('transform.create_orientation', 'SPACE', 'PRESS', ctrl=True, alt=True)
kmi.properties.use = True

#----------
# Snapping
#----------
kmi = km.keymap_items.new('wm.context_toggle', 'TAB', 'PRESS', shift=True)
kmi.properties.data_path = 'tool_settings.use_snap'
kmi = km.keymap_items.new('transform.snap_type', 'TAB', 'PRESS', shift=True, ctrl=True)

#---------------
# Snapping Menu
#---------------
kmi = km.keymap_items.new('wm.call_menu', 'S', 'PRESS', shift=True)
kmi.properties.name = 'VIEW3D_MT_snap'

#-----------
# 3d cursor
#-----------
kmi = km.keymap_items.new('view3d.cursor3d', 'ACTIONMOUSE', 'PRESS')

#-------------------
# Toggle local view
#-------------------
kmi = km.keymap_items.new('view3d.localview', 'NUMPAD_SLASH', 'PRESS')

#--------
# Layers
#--------
kmi = km.keymap_items.new('view3d.layers', 'ACCENT_GRAVE', 'PRESS')
kmi.properties.nr = 0
kmi = km.keymap_items.new('view3d.layers', 'ONE', 'PRESS', any=True)
kmi.properties.nr = 1
kmi = km.keymap_items.new('view3d.layers', 'TWO', 'PRESS', any=True)
kmi.properties.nr = 2
kmi = km.keymap_items.new('view3d.layers', 'THREE', 'PRESS', any=True)
kmi.properties.nr = 3
kmi = km.keymap_items.new('view3d.layers', 'FOUR', 'PRESS', any=True)
kmi.properties.nr = 4
kmi = km.keymap_items.new('view3d.layers', 'FIVE', 'PRESS', any=True)
kmi.properties.nr = 5
kmi = km.keymap_items.new('view3d.layers', 'SIX', 'PRESS', any=True)
kmi.properties.nr = 6
kmi = km.keymap_items.new('view3d.layers', 'SEVEN', 'PRESS', any=True)
kmi.properties.nr = 7
kmi = km.keymap_items.new('view3d.layers', 'EIGHT', 'PRESS', any=True)
kmi.properties.nr = 8
kmi = km.keymap_items.new('view3d.layers', 'NINE', 'PRESS', any=True)
kmi.properties.nr = 9
kmi = km.keymap_items.new('view3d.layers', 'ZERO', 'PRESS', any=True)
kmi.properties.nr = 10

#------------------
# Viewport drawing
#------------------
kmi = km.keymap_items.new('wm.context_toggle_enum', 'Z', 'PRESS')
kmi.properties.data_path = 'space_data.viewport_shade'
kmi.properties.value_1 = 'SOLID'
kmi.properties.value_2 = 'WIREFRAME'
kmi = km.keymap_items.new('wm.context_toggle_enum', 'Z', 'PRESS', alt=True)
kmi.properties.data_path = 'space_data.viewport_shade'
kmi.properties.value_1 = 'TEXTURED'
kmi.properties.value_2 = 'SOLID'

#-------------
# Pivot point
#-------------
kmi = km.keymap_items.new('wm.context_set_enum', 'COMMA', 'PRESS')
kmi.properties.data_path = 'space_data.pivot_point'
kmi.properties.value = 'BOUNDING_BOX_CENTER'
kmi = km.keymap_items.new('wm.context_set_enum', 'COMMA', 'PRESS', ctrl=True)
kmi.properties.data_path = 'space_data.pivot_point'
kmi.properties.value = 'MEDIAN_POINT'
kmi = km.keymap_items.new('wm.context_toggle', 'COMMA', 'PRESS', alt=True)
kmi.properties.data_path = 'space_data.use_pivot_point_align'
kmi = km.keymap_items.new('wm.context_set_enum', 'PERIOD', 'PRESS')
kmi.properties.data_path = 'space_data.pivot_point'
kmi.properties.value = 'CURSOR'
kmi = km.keymap_items.new('wm.context_set_enum', 'PERIOD', 'PRESS', ctrl=True)
kmi.properties.data_path = 'space_data.pivot_point'
kmi.properties.value = 'INDIVIDUAL_ORIGINS'
kmi = km.keymap_items.new('wm.context_set_enum', 'PERIOD', 'PRESS', alt=True)
kmi.properties.data_path = 'space_data.pivot_point'
kmi.properties.value = 'ACTIVE_ELEMENT'

#------
# Misc
#------
kmi = km.keymap_items.new('view3d.clip_border', 'B', 'PRESS', alt=True)
kmi = km.keymap_items.new('view3d.zoom_border', 'B', 'PRESS', shift=True)
kmi = km.keymap_items.new('view3d.render_border', 'B', 'PRESS', shift=True)
kmi = km.keymap_items.new('view3d.camera_to_view', 'NUMPAD_0', 'PRESS', ctrl=True, alt=True)
kmi = km.keymap_items.new('view3d.object_as_camera', 'NUMPAD_0', 'PRESS', ctrl=True)



#######################
# Transform Modal Map #
#######################
km = kc.keymaps.new('Transform Modal Map', space_type='EMPTY', region_type='WINDOW', modal=True)

# Cancel
kmi = km.keymap_items.new_modal('CANCEL', 'ESC', 'PRESS', any=True)

# Confirm
kmi = km.keymap_items.new_modal('CONFIRM', 'LEFTMOUSE', 'PRESS', any=True)
kmi = km.keymap_items.new_modal('CONFIRM', 'RET', 'PRESS', any=True)
kmi = km.keymap_items.new_modal('CONFIRM', 'NUMPAD_ENTER', 'PRESS', any=True)

# Snapping
kmi = km.keymap_items.new_modal('SNAP_TOGGLE', 'TAB', 'PRESS', shift=True)
kmi = km.keymap_items.new_modal('SNAP_INV_ON', 'LEFT_CTRL', 'PRESS', any=True)
kmi = km.keymap_items.new_modal('SNAP_INV_OFF', 'LEFT_CTRL', 'RELEASE', any=True)
kmi = km.keymap_items.new_modal('SNAP_INV_ON', 'RIGHT_CTRL', 'PRESS', any=True)
kmi = km.keymap_items.new_modal('SNAP_INV_OFF', 'RIGHT_CTRL', 'RELEASE', any=True)
kmi = km.keymap_items.new_modal('ADD_SNAP', 'A', 'PRESS')
kmi = km.keymap_items.new_modal('REMOVE_SNAP', 'A', 'PRESS', alt=True)

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
kmi = km.keymap_items.new_modal('AXIS_X', 'X', 'PRESS')
kmi = km.keymap_items.new_modal('AXIS_Y', 'Y', 'PRESS')
kmi = km.keymap_items.new_modal('AXIS_Z', 'Z', 'PRESS')
kmi = km.keymap_items.new_modal('PLANE_X', 'X', 'PRESS', shift=True)
kmi = km.keymap_items.new_modal('PLANE_Y', 'Y', 'PRESS', shift=True)
kmi = km.keymap_items.new_modal('PLANE_Z', 'Z', 'PRESS', shift=True)

# ???
#kmi = km.keymap_items.new_modal('TRANSLATE', 'G', 'PRESS')
#kmi = km.keymap_items.new_modal('ROTATE', 'R', 'PRESS')
#kmi = km.keymap_items.new_modal('RESIZE', 'S', 'PRESS')



####################
# Object Non-modal #
####################
km = kc.keymaps.new('Object Non-modal', space_type='EMPTY', region_type='WINDOW', modal=False)


#-----------------------
# Object mode switching
#-----------------------
kmi = km.keymap_items.new('wm.call_menu', 'SPACE', 'PRESS')
kmi.properties.name = 'OBJECT_MT_mode_switch_menu'



#############
# Mesh Edit #
#############
km = kc.keymaps.new('Mesh', space_type='EMPTY', region_type='WINDOW', modal=False)

#---------------------------------
# Vertex/Edge/Face mode switching
#---------------------------------
kmi = km.keymap_items.new('wm.call_menu', 'TAB', 'PRESS', ctrl=True)
kmi.properties.name = 'VIEW3D_MT_edit_mesh_select_mode'

#-----------
# Selection
#-----------
kmi = km.keymap_items.new('mesh.loop_select', 'SELECTMOUSE', 'PRESS', alt=True)
kmi.properties.extend = False
kmi = km.keymap_items.new('mesh.loop_select', 'SELECTMOUSE', 'PRESS', shift=True, alt=True)
kmi.properties.extend = True
kmi = km.keymap_items.new('mesh.edgering_select', 'SELECTMOUSE', 'PRESS', ctrl=True, alt=True)
kmi.properties.extend = False
kmi = km.keymap_items.new('mesh.edgering_select', 'SELECTMOUSE', 'PRESS', shift=True, ctrl=True, alt=True)
kmi.properties.extend = True
kmi = km.keymap_items.new('mesh.select_shortest_path', 'SELECTMOUSE', 'PRESS', ctrl=True)
kmi = km.keymap_items.new('mesh.select_all', 'A', 'PRESS')
kmi.properties.action = 'TOGGLE'
kmi = km.keymap_items.new('mesh.select_all', 'I', 'PRESS', ctrl=True)
kmi.properties.action = 'INVERT'
kmi = km.keymap_items.new('mesh.select_more', 'NUMPAD_PLUS', 'PRESS', ctrl=True)
kmi = km.keymap_items.new('mesh.select_less', 'NUMPAD_MINUS', 'PRESS', ctrl=True)
kmi = km.keymap_items.new('mesh.select_non_manifold', 'M', 'PRESS', shift=True, ctrl=True, alt=True)
kmi = km.keymap_items.new('mesh.select_linked', 'L', 'PRESS', ctrl=True)
kmi = km.keymap_items.new('mesh.select_linked_pick', 'L', 'PRESS')
kmi.properties.deselect = False
kmi = km.keymap_items.new('mesh.select_linked_pick', 'L', 'PRESS', shift=True)
kmi.properties.deselect = True
kmi = km.keymap_items.new('mesh.faces_select_linked_flat', 'F', 'PRESS', shift=True, ctrl=True, alt=True)
kmi = km.keymap_items.new('mesh.select_similar', 'G', 'PRESS', shift=True)

#----------------------
# Proportional editing
#----------------------
kmi = km.keymap_items.new('wm.context_toggle_enum', 'O', 'PRESS')
kmi.properties.data_path = 'tool_settings.proportional_edit'
kmi.properties.value_1 = 'DISABLED'
kmi.properties.value_2 = 'ENABLED'
kmi = km.keymap_items.new('wm.context_cycle_enum', 'O', 'PRESS', shift=True)
kmi.properties.data_path = 'tool_settings.proportional_edit_falloff'
kmi = km.keymap_items.new('wm.context_toggle_enum', 'O', 'PRESS', alt=True)
kmi.properties.data_path = 'tool_settings.proportional_edit'
kmi.properties.value_1 = 'DISABLED'
kmi.properties.value_2 = 'CONNECTED'

#--------
# Hiding
#--------
kmi = km.keymap_items.new('mesh.hide', 'H', 'PRESS')
kmi.properties.unselected = False
kmi = km.keymap_items.new('mesh.hide', 'H', 'PRESS', shift=True)
kmi.properties.unselected = True
kmi = km.keymap_items.new('mesh.reveal', 'H', 'PRESS', alt=True)

#--------
# Create
#--------
kmi = km.keymap_items.new('mesh.loopcut_slide', 'R', 'PRESS', ctrl=True)
kmi = km.keymap_items.new('mesh.knifetool', 'K', 'PRESS')
kmi = km.keymap_items.new('view3d.edit_mesh_extrude_move_normal', 'E', 'PRESS')
kmi = km.keymap_items.new('wm.call_menu', 'E', 'PRESS', alt=True)
kmi.properties.name = 'VIEW3D_MT_edit_mesh_extrude'
kmi = km.keymap_items.new('mesh.edge_face_add', 'F', 'PRESS')
kmi = km.keymap_items.new('mesh.vert_connect', 'J', 'PRESS')
kmi = km.keymap_items.new('mesh.spin', 'R', 'PRESS', alt=True)
kmi = km.keymap_items.new('mesh.fill', 'F', 'PRESS', alt=True)
kmi = km.keymap_items.new('mesh.beautify_fill', 'F', 'PRESS', shift=True, alt=True)
kmi = km.keymap_items.new('mesh.duplicate_move', 'D', 'PRESS', shift=True)
kmi = km.keymap_items.new('wm.call_menu', 'A', 'PRESS', shift=True)
kmi.properties.name = 'INFO_MT_mesh_add'
kmi = km.keymap_items.new('mesh.dupli_extrude_cursor', 'ACTIONMOUSE', 'CLICK', ctrl=True)
kmi.properties.rotate_source = True
kmi = km.keymap_items.new('mesh.dupli_extrude_cursor', 'ACTIONMOUSE', 'CLICK', shift=True, ctrl=True)
kmi.properties.rotate_source = False

#--------
# Delete
#--------
kmi = km.keymap_items.new('wm.call_menu', 'X', 'PRESS')
kmi.properties.name = 'VIEW3D_MT_edit_mesh_delete'
kmi = km.keymap_items.new('wm.call_menu', 'DEL', 'PRESS')
kmi.properties.name = 'VIEW3D_MT_edit_mesh_delete'

#----------
# Separate
#----------
kmi = km.keymap_items.new('mesh.rip_move', 'V', 'PRESS')
kmi = km.keymap_items.new('mesh.split', 'Y', 'PRESS')
kmi = km.keymap_items.new('mesh.separate', 'P', 'PRESS')

#-------
# Merge
#-------
kmi = km.keymap_items.new('mesh.merge', 'M', 'PRESS', alt=True)

#-----------
# Transform
#-----------
kmi = km.keymap_items.new('transform.shrink_fatten', 'S', 'PRESS', alt=True)
kmi = km.keymap_items.new('transform.edge_crease', 'E', 'PRESS', shift=True)
kmi = km.keymap_items.new('mesh.quads_convert_to_tris', 'T', 'PRESS', ctrl=True)
kmi = km.keymap_items.new('mesh.quads_convert_to_tris', 'T', 'PRESS', shift=True, ctrl=True)
kmi.properties.use_beauty = False
kmi = km.keymap_items.new('mesh.tris_convert_to_quads', 'J', 'PRESS', alt=True)

#------------
# Tool Menus
#------------
kmi = km.keymap_items.new('wm.call_menu', 'W', 'PRESS')
kmi.properties.name = 'VIEW3D_MT_edit_mesh_specials'
kmi = km.keymap_items.new('wm.call_menu', 'F', 'PRESS', ctrl=True)
kmi.properties.name = 'VIEW3D_MT_edit_mesh_faces'
kmi = km.keymap_items.new('wm.call_menu', 'E', 'PRESS', ctrl=True)
kmi.properties.name = 'VIEW3D_MT_edit_mesh_edges'
kmi = km.keymap_items.new('wm.call_menu', 'V', 'PRESS', ctrl=True)
kmi.properties.name = 'VIEW3D_MT_edit_mesh_vertices'

#------
# UV's
#------
kmi = km.keymap_items.new('wm.call_menu', 'U', 'PRESS')
kmi.properties.name = 'VIEW3D_MT_uv_map'

#-------------------
# Calculate normals
#-------------------
kmi = km.keymap_items.new('mesh.normals_make_consistent', 'N', 'PRESS', ctrl=True)
kmi.properties.inside = False
kmi = km.keymap_items.new('mesh.normals_make_consistent', 'N', 'PRESS', shift=True, ctrl=True)
kmi.properties.inside = True

#-------------------
# Subsurf shortcuts
#-------------------

if SUBSURF_RELATIVE:
    kmi = km.keymap_items.new('object.shift_subsurf_level', 'EQUAL', 'CLICK')
    kmi.properties.delta = 1
    kmi.properties.max = 4
    kmi = km.keymap_items.new('object.shift_subsurf_level', 'MINUS', 'CLICK')
    kmi.properties.delta = -1
    kmi.properties.min = 0
else:
    kmi = km.keymap_items.new('object.subdivision_set', 'ZERO', 'PRESS', ctrl=True)
    kmi.properties.level = 0
    kmi = km.keymap_items.new('object.subdivision_set', 'ONE', 'PRESS', ctrl=True)
    kmi.properties.level = 1
    kmi = km.keymap_items.new('object.subdivision_set', 'TWO', 'PRESS', ctrl=True)
    kmi.properties.level = 2
    kmi = km.keymap_items.new('object.subdivision_set', 'THREE', 'PRESS', ctrl=True)
    kmi.properties.level = 3
    kmi = km.keymap_items.new('object.subdivision_set', 'FOUR', 'PRESS', ctrl=True)
    kmi.properties.level = 4
    kmi = km.keymap_items.new('object.subdivision_set', 'FIVE', 'PRESS', ctrl=True)
    kmi.properties.level = 5

#---------
# Rigging
#---------
kmi = km.keymap_items.new('object.vertex_parent_set', 'P', 'PRESS', ctrl=True)
kmi = km.keymap_items.new('wm.call_menu', 'H', 'PRESS', ctrl=True)
kmi.properties.name = 'VIEW3D_MT_hook'
kmi = km.keymap_items.new('wm.call_menu', 'G', 'PRESS', ctrl=True)
kmi.properties.name = 'VIEW3D_MT_vertex_group'
