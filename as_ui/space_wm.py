# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

from .utils import get_orb_icon


def draw_splash(self, context):
    orb = get_orb_icon()

    from .. import bl_info, as_info
    version = bl_info["version"]
    primary = version[0]
    if len(version) > 1:
        secondary = version[1]
    else: secondary = 0

    if len(version) > 2:
        tertiary = version[2]
    else: tertiary = 0

    version = f"v{primary}.{secondary}.{tertiary}"
    restrictions = as_info["restrictions_url"]

    layout = self.layout
    box = layout.box()

    row = box.row()
    row.scale_y = 3
    row.label(text=f"Alva Sorcerer {version}", icon_value=orb.icon_id)
    row = box.row()
    row.label(text="Today I'm just a baby, but one day I'll grow big and strong!")
    box.separator()

    if as_info["alpha"]:
        row = box.row()
        row.alert = 1
        row.label(text="Warning: Many features do not work in this alpha version.")
        row.alert = 0
    elif as_info["beta"]:
        row = box.row()
        row.label(text="Warning: Some features may not work in this beta version.")
    
    row = box.row()
    if restrictions != "":
        row.operator("wm.url_open", text="See Restrictions").url = restrictions
    row.operator("wm.url_open", text="Support").url = "https://sorcerer.alvatheaters.com/support"


def draw_strobe_settings(self, context, active_controller):
    ac = active_controller

    layout = self.layout
    layout.use_property_split = True
    layout.use_property_decorate = False

    if ac and hasattr(ac, "str_enable_strobe_argument"):
        if not context.scene.scene_props.expand_strobe:
            layout.use_property_decorate = True
            layout.prop(ac, "float_strobe")
            layout.use_property_decorate = False
            layout.separator()

        layout.prop(ac, "strobe_min", text="Strobe Min")
        layout.prop(ac, "strobe_max", text="Max")

        layout.separator()
        layout.prop(ac, "str_enable_strobe_argument", text="Enable Argument")
        layout.prop(ac, "str_disable_strobe_argument", text="Disable")

    else:
        layout.label(text="Active controller not found.")


def draw_pan_tilt_settings(self, context, active_controller):
    ac = active_controller

    layout = self.layout
    layout.use_property_split = True
    layout.use_property_decorate = False
    
    if ac:
        layout.prop(ac, "pan_min", text="Pan Min")
        layout.prop(ac, "pan_max", text="Max")
        
        layout.separator()
        
        layout.prop(ac, "tilt_min", text="Tilt Min")
        layout.prop(ac, "tilt_max", text="Max")
    else:
        layout.label(text="Active controller not found.")


def draw_zoom_settings(self, context, active_controller):
    ac = active_controller

    layout = self.layout
    layout.use_property_split = True
    layout.use_property_decorate = False
    
    if active_controller:
        layout.prop(ac, "zoom_min", text="Zoom Min")
        layout.prop(ac, "zoom_max", text="Max")

    else:
        layout.label(text="Active controller not found.")


def draw_edge_diffusion_settings(self, context, active_controller):   
    layout = self.layout
    
    if active_controller:
        row = layout.row()
        row.label(text="Nothing to adjust here.")
    else:
        layout.label(text="Active controller not found.")

 
def draw_gobo_settings(self, context, active_controller):
    layout = self.layout

    if active_controller:
        split = layout.split(factor=.5)
        row = split.column()
        row.label(text="Gobo ID Argument")
        row = split.column()
        row.prop(active_controller, "str_gobo_id_argument", text="", icon='POINTCLOUD_DATA')
        
        layout.separator()
        
        split = layout.split(factor=.5)
        row = split.column()
        row.label(text="Gobo Speed Value Argument")
        row = split.column()
        row.prop(active_controller, "str_gobo_speed_value_argument", text="", icon='CON_ROTLIKE')
        split = layout.split(factor=.5)
        row = split.column()
        row.label(text="Enable Gobo Speed Argument")
        row = split.column()
        row.prop(active_controller, "str_enable_gobo_speed_argument", text="", icon='CHECKBOX_HLT')
        split_two = layout.split(factor=.51, align=True)
        row_two = split_two.column()
        row_two.label(text="")
        row_two = split_two.column(align=True)
        row_two.prop(active_controller, "gobo_speed_min", text="Min")
        row_two = split_two.column(align=True)
        row_two.prop(active_controller, "gobo_speed_max", text="Max")
        
        layout.separator()
        
        split = layout.split(factor=.5)
        row = split.column()
        row.label(text="Enable Prism Argument")
        row = split.column()
        row.prop(active_controller, "str_enable_prism_argument", text="", icon='TRIA_UP')
        
        split = layout.split(factor=.5)
        row = split.column()
        row.label(text="Disable Prism Argument")
        row = split.column()
        row.prop(active_controller, "str_disable_prism_argument", text="", icon='PANEL_CLOSE')
        
    else:
        layout.label(text="Active controller not found.")


def draw_alva_right_click(self, context):
    is_property = False
    try:
        prop = context.button_prop
        is_property = True
    except:
        pass

    if is_property and prop.identifier not in ['float_vec_color', 'float_intensity']:
        return
    
    orb = get_orb_icon()

    st = context.space_data.type
    layout = self.layout
    has_separated = False

    if is_property and prop.identifier == 'float_vec_color':
        if st == 'NODE_EDITOR':
            node_tree = context.space_data.node_tree
            node_name = context.active_node.name
            node_tree_name = node_tree.name
        else:
            node_name = ""
            node_tree_name = ""

        self.layout.separator()
        has_separated = True
        op = self.layout.operator("alva_common.white_balance", icon_value=orb.icon_id, text="Set White Balance")
        op.space_type = st
        op.node_name = node_name
        op.node_tree_name = node_tree_name
        if st == 'VIEW_3D' and context.active_object and context.active_object.type == 'MESH':
            self.layout.prop(context.active_object, "color_profile_enum", text="")

    if is_property and prop.identifier == 'float_intensity' and st == 'VIEW_3D':
        if not has_separated:
            self.layout.separator()
        layout.operator("alva_object.driver_add", text="Add Driver", icon_value=orb.icon_id)

    in_viewport = context.area.type == 'VIEW_3D' and context.region.type == 'WINDOW'
    has_selected_object = context.object is not None

    if in_viewport and has_selected_object:
        # Right-clicked in viewport with an object selected
        layout.separator()
        has_separated = True
        layout.label(text="Render Freezing:", icon_value=orb.icon_id)
        layout.prop(context.object, "freezing_mode_enum", text="")
        if len(context.object.list_group_channels) == 1:
            layout.separator()
            layout.prop(context.object, "int_alva_sem", icon='NONE')

    in_sequencer = context.area.type == 'SEQUENCE_EDITOR'
    has_selected_strip = hasattr(context.scene.sequence_editor, "active_strip") and context.scene.sequence_editor.active_strip is not None

    if in_sequencer and has_selected_strip:
        active_strip = context.scene.sequence_editor.active_strip
        if active_strip.my_settings.motif_type_enum == 'option_animation':
            layout.separator()
            has_separated = True
            layout.label(text="Render Freezing:", icon_value=orb.icon_id)
            layout.prop(active_strip, "freezing_mode_enum", text="")

    in_node_editor = (st == 'NODE_EDITOR')
    has_selected_node = hasattr(context, "active_node") and context.active_node is not None

    if in_node_editor and has_selected_node and hasattr(context.active_node, "expand_color"):
        layout.prop(context.active_node, "expand_color", text="Expand Color")
