# This file is part of Alva Sorcerer
# Copyright (C) 2024 Alva Theaters

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


'''
=====================================================================
                      DESIGNED BY ALVA THEATERS
                       FOR THE SOLE PURPOSE OF
                         MAKING PEOPLE HAPPY
=====================================================================
'''


## Double hashtag indicates notes for future development requiring some level of attention


# Custom icon stuff
import bpy.utils.previews
import os

preview_collections = {}
pcoll = bpy.utils.previews.new()
preview_collections["main"] = pcoll

addon_dir = os.path.dirname(__file__)
pcoll.load("orb", os.path.join(addon_dir, "alva_orb.png"), 'IMAGE')


def draw_splash(self, context):
    pcoll = preview_collections["main"]
    orb = pcoll["orb"]

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
    layout = self.layout

    if active_controller:
        if hasattr(active_controller, "str_enable_strobe_argument"):
            if not context.scene.scene_props.expand_strobe:
                split = layout.split(factor=0.5)
                row = split.column()
                row.label(text="Strobe Value", icon='OUTLINER_DATA_LIGHTPROBE')
                row = split.column()
                row.prop(active_controller, "float_strobe", text="", slider=True)

                layout.separator()

            row = layout.row()
            row.prop(active_controller, "strobe_min", text="Strobe Min")
            row.prop(active_controller, "strobe_max", text="Max")

            layout.separator()

            split = layout.split(factor=0.5)
            row = split.column()
            row.label(text="Enable Strobe Argument")
            row = split.column()
            row.prop(active_controller, "str_enable_strobe_argument", text="", icon='OUTLINER_DATA_LIGHTPROBE')
            
            split = layout.split(factor=0.5)
            row = split.column()
            row.label(text="Disable Strobe Argument")
            row = split.column()
            row.prop(active_controller, "str_disable_strobe_argument", text="", icon='PANEL_CLOSE')


def draw_pan_tilt_settings(self, context, active_controller):
    layout = self.layout
    
    if active_controller:
        row = layout.row()
        row.prop(active_controller, "pan_min", text="Pan Min")
        row.prop(active_controller, "pan_max", text="Max")
        
        row = layout.row()
        
        row.prop(active_controller, "tilt_min", text="Tilt Min")
        row.prop(active_controller, "tilt_max", text="Max")
    else:
        layout.label(text="Active controller not found.")


def draw_zoom_settings(self, context, active_controller):
    layout = self.layout
    
    if active_controller:
        row = layout.row()
        row.prop(active_controller, "zoom_min", text="Zoom Min")
        row.prop(active_controller, "zoom_max", text="Max")

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
    
    pcoll = preview_collections["main"]
    orb = pcoll["orb"]

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

    if is_property and prop.identifier == 'float_intensity' and st == 'VIEW_3D':
        if not has_separated:
            self.layout.separator()
        layout.operator("alva_common.driver_add", text="Add Driver", icon_value=orb.icon_id)

    in_viewport = context.area.type == 'VIEW_3D' and context.region.type == 'WINDOW'
    has_selected_object = context.object is not None

    if in_viewport and has_selected_object:
        # Right-clicked in viewport with an object selected
        layout.separator()
        has_separated = True
        layout.label(text="Render Freezing:", icon_value=orb.icon_id)
        layout.prop(context.object, "freezing_mode_enum", text="")

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
