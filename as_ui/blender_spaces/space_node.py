# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from ..utils import find_group_label, get_orb_icon

MIXER_CHOICES_VISIBLE = True


def draw_alva_node_view(self, layout):
    orb = get_orb_icon()

    layout = self.layout
    layout.separator()
    layout.label(text="Alva Sorcerer", icon_value=orb.icon_id)
    layout.prop (bpy.context.scene.scene_props, "view_node_add_lighting", text="Add (Lighting)")
    #layout.prop (bpy.context.scene.scene_props, "view_node_add_audio", text="Add (Audio)")
    layout.prop(bpy.context.scene.scene_props, "view_node_toolbar", text="Toolbar")
    layout.prop(bpy.context.scene.scene_props, "view_node_formatter", text="Formatter")


def draw_alva_node_menu(self, layout):
    orb = get_orb_icon()

    layout = self.layout
    layout.separator()
    layout.label(text="Sorcerer", icon_value=orb.icon_id)

    if bpy.context.scene.scene_props.view_node_add_lighting:
        layout.menu("NODE_MT_alva_lighting_nodes")
        
    if bpy.context.scene.scene_props.view_node_add_audio:
        layout.menu("NODE_MT_alva_general_audio_nodes")
        layout.menu("NODE_MT_alva_inputs_audio_nodes")
        layout.menu("NODE_MT_alva_outputs_audio_nodes")


def draw_node_formatter_group(self, context, active_node):
    layout = self.layout
    column = layout.column()
    
    if active_node.bl_idname == "group_controller_type":
        row = column.row()
        row.prop(active_node, "influence", text="Influence")

        column.separator()


def draw_node_formatter_mixer(self, context, active_node):
    row = self.layout.row(align=True)
    row.prop(active_node, "str_manual_fixture_selection", text="")
    row = self.layout.row(align=True)
    row.prop(active_node, "parameters_enum", text="")
    if active_node.parameters_enum == 'option_color':
        row.prop(active_node, "color_profile_enum", text="")


def draw_node_formatter_footer(self, context, active_node):
    row = self.layout.row()
    if active_node.bl_idname == 'NodeFrame':
        row.prop(active_node, "shrink", slider=True)
        row = self.layout.row()
        row.prop(active_node, "label_size", text="Label size")
        row = self.layout.row()
    row.prop(active_node, "label", text="Label")
    row = self.layout.row()
    row.prop(active_node, "use_custom_color", text="", icon='HIDE_ON' if not active_node.use_custom_color else 'HIDE_OFF')
    row.template_color_picker(active_node, "color", value_slider=True)

def draw_expanded_color(self, context, layout, row):
    row.prop(self, "expand_color", text="Back", icon='SCREEN_BACK', slider=True)
    row.label(text="")

    row = layout.row()
    row.template_color_picker(self, "alva_color", value_slider=False)

def draw_node_header(self, context, active_node=None):
    if not active_node:
        try:
            active_node = context.space_data.edit_tree.nodes.active
        except:
            return
        if not active_node:
            return

    col = self.layout.column()

    if active_node.bl_idname == 'console_buttons_type':
        col = self.layout.column()
        col.prop(active_node, "expand_settings", icon='PREFERENCES', text="", emboss=True)

    col = self.layout.column()
    col.prop(active_node, "label", text="Label")

    col = self.layout.column()
    col.prop(active_node, "use_custom_color", text="", icon='HIDE_ON' if not active_node.use_custom_color else 'HIDE_OFF')
    
    col = self.layout.column()
    col.scale_x = .5
    col.prop(active_node, "color", text="")

    col = self.layout.column()
    col.scale_x = .8
    if hasattr(active_node, "scale"):
        col.prop(active_node, "scale", text="Scale")


def draw_node_mixer(self, context, layout): 
    draw_mixer_settings_row(self, context, layout)
    draw_mixer_header_row(self, layout)
    if MIXER_CHOICES_VISIBLE:
        layout.separator()
        draw_mixer_choices(self, layout)
        layout.separator()
        draw_choice_settings(self, layout)

def draw_mixer_settings_row(self, context, layout):
    space_type = context.space_data.type
    
    if space_type == 'NODE_EDITOR':
        node_tree = context.space_data.node_tree
        node_name = self.name
        node_tree_name = node_tree.name
    else:
        node_name = ""
        node_tree_name = ""

    if self.show_settings:
        row = layout.row(align=True)
        op_home = row.operator("alva_node.home", icon='HOME', text="")
        op_home.space_type = space_type
        op_home.node_name = node_name
        op_home.node_tree_name = node_tree_name
        
        op_update = row.operator("alva_node.update", icon='FILE_REFRESH', text="")
        op_update.space_type = space_type
        op_update.node_name = node_name
        op_update.node_tree_name = node_tree_name
        
        if self.str_manual_fixture_selection == "":
            row.prop(self, "selected_group_enum", icon='COLLECTION_NEW', icon_only=0, text="")
        row.prop(self, "str_manual_fixture_selection", text="")
        if self.mix_method_enum != "option_pose":
            row.prop(self, "parameters_enum", expand=True, text="")

def draw_mixer_header_row(self, layout):
    row = layout.row(align=True)
    row.prop(self, "show_settings", text="", expand=False, icon='TRIA_DOWN' if self.show_settings else 'TRIA_RIGHT')
    row.prop(self, "mix_method_enum", expand=True, icon_only=True)
    if self.mix_method_enum != "option_pose":
        row.prop(self, "float_offset", text="Offset:")
        if self.mix_method_enum != "option_pattern":
            row.prop(self, "int_subdivisions", text="Subdivisions:")
    if self.parameters_enum == "option_color" or self.mix_method_enum == 'option_pose':
        row.prop(self, "color_profile_enum", text="", icon='COLOR', icon_only=True)

def draw_mixer_choices(self, layout):
    num_columns = self.columns

    flow = layout.grid_flow(row_major=True, columns=num_columns, even_columns=True, even_rows=False, align=True)
    flow.scale_y = self.scale
    
    i = 1
    
    for par in self.parameters:
        if self.mix_method_enum != 'option_pose':
            draw_pose_choice(self, flow, par)
        else:
            i = draw_choice(flow, par, i)

def draw_pose_choice(self, flow, par):
    if self.parameters_enum == 'option_intensity':
        flow.prop(par, "alva_intensity", slider=True)
    elif self.parameters_enum == 'option_color':
        flow.template_color_picker(par, "alva_color")
    elif self.parameters_enum == 'option_pan_tilt':
        box = flow.box()
        row = box.row()
        split = row.split(factor=0.5)
        col = split.column()
        col.prop(par, "alva_pan", text="Pan", slider=True)
        col = split.column()
        col.prop(par, "alva_tilt", text="Tilt", slider=True)
    elif self.parameters_enum == 'option_zoom':
        flow.prop(par, "alva_zoom", slider=True)
    else:
        flow.prop(par, "alva_iris", slider=True)

def draw_choice(flow, par, i):
    box = flow.box()
    row = box.row()
    row.label(text=f"Pose {i}:", icon='POSE_HLT')
    split = box.split(factor=0.5)

    # Left side: existing properties
    col = split.column()
    col.prop(par, "alva_intensity", slider=True)
    col.prop(par, "alva_pan", text="Pan", slider=True)
    col.prop(par, "alva_tilt", text="Tilt", slider=True)
    col.prop(par, "alva_zoom", text="Zoom", slider=True)
    col.prop(par, "alva_iris", text="Iris", slider=True)

    # Right side: alva_color
    col = split.column()
    col.template_color_picker(par, "alva_color")
    
    return i + 1

def draw_choice_settings(self, layout):
    row = layout.row()
    row.operator("alva_node.mixer_add_choice", icon='ADD', text="")
    row.operator("alva_node.mixer_remove_choice", icon='REMOVE', text="")
    row.prop(self, "columns", text="Columns:")
    row.prop(self, "scale", text="Size:")

    layout.separator() 
        

def draw_node_formatter(self, context):
    layout = self.layout
    column = layout.column(align=True)
    row = column.row()
    active_node = None 
    active_node = context.space_data.edit_tree.nodes.active

    if active_node and (active_node.bl_idname == "group_controller_type"):
        row.prop(active_node, "strobe_is_on", text="Strobe", slider=True)
        row.prop(active_node, "color_is_on", text="Color", slider=True)
        
        row = column.row()
        row.prop(active_node, "pan_tilt_is_on", text="Pan/Tilt", slider=True)
        
        row = column.row()
        row.prop(active_node, "zoom_is_on", text="Zoom", slider=True)
        row.prop(active_node, "iris_is_on", text="Iris", slider=True)
        
        row = column.row()
        row.prop(active_node, "edge_is_on", text="Edge", slider=True)
        row.prop(active_node, "diffusion_is_on", text="Diffusion", slider=True)
        
        row = column.row()
        row.prop(active_node, "gobo_is_on", text="Gobo", slider=True)
        
        column.separator()
        
        if active_node.bl_idname == "group_controller_type":
            row = column.row()
            row.prop(active_node, "influence", text="Influence")
            
            column.separator()
            
    elif active_node and active_node.bl_idname == "mixer_type":
        row = layout.row(align=True)
        row.prop(active_node, "selected_group_enum", text="")
        row = layout.row(align=True)
        row.prop(active_node, "parameters_enum", text="")
        if active_node.parameters_enum == 'option_color':
            row.prop(active_node, "color_profile_enum", text="")
        
    row = layout.row()
    row.prop(active_node, "label", text="Label")
    row = layout.row()
    row.prop(active_node, "use_custom_color", text="", icon='HIDE_ON' if not active_node.use_custom_color else 'HIDE_OFF')
    row.prop(active_node, "color", text="")
    

def draw_console_node(self, context, layout):
    st = context.space_data.type
    node_tree = context.space_data.node_tree
    node_name = self.name
    node_tree_name = node_tree.name

    num_buttons = len(self.custom_buttons)
    num_columns = self.number_of_columns
    num_rows = (num_buttons + num_columns - 1) // num_columns

    if self.direct_select_types_enum == 'Macro':
        layout.prop(context.scene.scene_props, 'view3d_command_line', text="")

    for row_index in range(num_rows):
        row = layout.row(align=True)
        
        for col_index in range(num_columns):
            button_index = row_index * num_columns + col_index
            if button_index < num_buttons:
                button = self.custom_buttons[button_index]
                colon = ":" if button.button_label != "" else ""

                if not self.expand_settings:
                    row.scale_y = self.scale * 1.5 # Boosting this because the box in other mode boosts it, we want them to stay in same spot between modes
                    op = row.operator("alva_node.direct_select", text=f"{button.constant_index}{colon} {button.button_label}")
                    op.button_index = button_index
                    op.space_type = st
                    op.node_name = node_name
                    op.node_tree_name = node_tree_name

                else:
                    box = row.box()
                    
                    sub_row = box.row(align=True)
                    sub_row.scale_y = self.scale / 2
                    sub_row.operator("alva_node.bump_direct_select_up", icon='TRIA_LEFT', text="").button_index = button_index
                    sub_row.prop(button, "constant_index", text="")
                    sub_row.operator("alva_node.bump_direct_select_down", icon='TRIA_RIGHT', text="").button_index = button_index

                    sub_row = box.row(align=True)
                    sub_row.scale_y = self.scale / 2
                    sub_row.prop(button, "button_label", text="")
                    sub_row.operator("alva_node.remove_direct_select", icon='X', text="")

    if self.expand_settings:
        column = layout.column()
        box = column.box()

        row = box.row()
        row.prop(self, "direct_select_types_enum", expand=True, icon_only=True)
        row.label(text=f" {self.direct_select_types_enum} Buttons")

        box.separator()

        row = box.row()
        row.scale_y = 1.5
        row.scale_x = 2
        row.operator("alva_node.add_direct_select", icon='ADD', text="")
        row.prop(self, "number_of_columns", icon='CENTER_ONLY', text="Columns")
        row.prop(self, "scale", text="Scale")
        row.prop(self, "boost_index", text="Boost #'s by")

        row = box.row()
        row.label(text="Make this go away by pressing the gear icon on the node view header", icon='PREFERENCES')

        
def draw_motor_node(self, context, layout):
    row = layout.row()
    row.prop(self, "transmission_enum", expand=True)
    if self.transmission_enum != 'option_keyframe':
        row = layout.row()
        row.template_color_picker(self, "motor", value_slider = False)
    row = layout.row()
    if self.transmission_enum == 'option_keyframe':
        row.enabled = True
    else: row.enabled = False
    row.prop(self, "float_progress")
    row = layout.row()
    if self.transmission_enum == 'option_keyframe':
        row.enabled = True
    else: row.enabled = False
    row.prop(self, "float_scale")
    layout.separator()
    
    
def draw_pan_tilt_node(self, context, layout):
    column = layout.column(align=True)
    
    row = column.row(align=True)  
    
    channel_string = str(self.pan_tilt_channel)
    active_object = None
    
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.str_manual_fixture_selection == channel_string:
            active_object = obj
            break
    
    if active_object:
        #row.prop(active_object, "pan_is_inverted", text="", icon='SORT_DESC')
        row.prop(self, "pan_tilt_channel", text="Channel")
        column.separator()
        column.separator()
        
        row = column.row()
        
        if active_object:
            row.template_color_picker(active_object, "float_vec_pan_tilt_graph", value_slider = True)
            #row.prop(active_object, "float_vec_pan_tilt_graph", text="") # For debugging

            if active_object.is_overdriven_left:
                row = column.row()
                row.alert = 1
                row.scale_x = .55
                row.label(text="")
                row.scale_x = 1
                row.label(text="|")
                row.alert = 0
                row = column.row()
                row.alert = 1
                row.label(text = "Extending for left-pan")
                row.alert = 0
                
                if active_object.is_approaching_limit:
                    row = column.row()
                    row.alert = 1
                    row.label(text = "Will soon pan-around!")
                    row.alert = 0
                
            if active_object.is_overdriven_right:
                row = column.row()
                row.alert = 1
                row.scale_x = .55
                row.label(text="")
                row.scale_x = 1
                row.label(text="|")
                row.alert = 0
                row = column.row()
                row.alert = 1
                row.label(text = "Extending for right-pan")
                row.alert = 0
                
                if active_object.is_approaching_limit:
                    row = column.row()
                    row.alert = 1
                    row.label(text = "Will soon pan-around!")
                    row.alert = 0
                    
    else: 
        row.label(text="No light selected.")
        row.prop(self, "pan_tilt_channel", text="Channel:")
        
        
def draw_global_node(self, context, layout):
    scene = context.scene
    world = scene.world
    node_tree = world.node_tree
    
    layout.prop(self, "parameters_enum", expand=True)

    if world is not None and world.node_tree:
        flow = layout.grid_flow(row_major=True, columns=self.columns, even_columns=True, even_rows=False, align=True)
        flow.scale_y = self.scale
        
        for con in node_tree.nodes:
            if con.bl_idname == 'group_controller_type':
                group_label = find_group_label(con)
                if not self.parameters_enum in ['option_color', 'option_compound']:
                    col = layout.column()
                    row = col.row()
                    row.scale_y = self.scale
                
                if self.parameters_enum == 'option_compound':
                    box = flow.box()
                    row = box.row()
                    row.label(text=f"{group_label} Compound:")
                    split = box.split(factor=0.5)
                    
                    # Left side: existing properties
                    col = split.column()
                    col.prop(con, "alva_intensity", text="Intensity:", slider=True)
                    col.prop(con, "alva_pan", text="Pan:", slider=True)
                    col.prop(con, "alva_tilt", text="Tilt:", slider=True)
                    col.prop(con, "alva_zoom", text="Zoom:", slider=True)
                    col.prop(con, "alva_iris", text="Iris:", slider=True)

                    # Right side: alva_color
                    col = split.column()
                    col.template_color_picker(con, "alva_color")
                            
                elif self.parameters_enum == 'option_intensity':
                    row.prop(con, "alva_intensity", text=f"{group_label}'s Intensity:", slider=True)
                elif self.parameters_enum == 'option_color':
                    box = flow.box()
                    row = box.row()
                    row.label(text=f"{group_label}'s Color:")
                    row = box.row()
                    row.scale_y = self.scale
                    row.template_color_picker(con, "alva_color")
                elif self.parameters_enum == 'option_pan_tilt':
                    row.prop(con, "alva_pan", text=f"{group_label}'s Pan:", slider=True)  
                    row = col.row()
                    row.scale_y = self.scale
                    row.prop(con, "alva_tilt", text=f"{group_label}'s Tilt:", slider=True)
                    row.separator()                      
                elif self.parameters_enum == 'option_zoom':
                    row.prop(con, "alva_zoom", text=f"{group_label}'s Zoom:", slider=True)
                elif self.parameters_enum == 'option_iris':
                    row.prop(con, "alva_iris", text=f"{group_label}'s Iris:", slider=True)
        if self.parameters_enum in ['option_color', 'option_compound']:
            col = layout.column()
            row = col.row()
            row.prop(self, "columns")
            row.prop(self, "scale")
        else:
            layout.separator()
            layout.prop(self, "scale")
        layout.separator()
        
        
def create_presets_operator(row, op_idname, icon, **kwargs):
    op = row.operator(op_idname, text="", icon=icon)
    for key, value in kwargs.items():
        setattr(op, key, value)
        
        
def draw_presets_node(self, context, layout):
    scene = context.scene

    column = layout.column()
    row = column.row()
    row.prop(self, "preset_types_enum", expand=True)
    row.prop(self, "index_offset", icon='ADD', text="Index Offset")
    row.prop(self, "show_settings", icon='PREFERENCES', text="")

    column = layout.column(align=True)

    if len(scene.scene_group_data) == 0:
        column.label(text="Make groups in 3D View side panel to get started.")
        return

    for group in scene.scene_group_data:
        if not group.show_in_presets_node and not self.show_settings:
            continue
        
        group_label = group.name
        box = column.box()
        row = box.row(align=True)
        row.label(text=group_label)

        row.prop(self, "is_recording", text="", icon='REC')

        if self.is_recording:
            row.alert = 1

        color_ops = [
            ("my.color_one", 'COLORSET_01_VEC'),
            ("my.color_two", 'COLORSET_02_VEC'),
            ("my.color_three", 'COLORSET_03_VEC'),
            ("my.color_four", 'COLORSET_04_VEC'),
            ("my.color_five", 'COLORSET_05_VEC'),
            ("my.color_six", 'COLORSET_06_VEC'),
            ("my.color_seven", 'COLORSET_07_VEC'),
            ("my.color_eight", 'COLORSET_08_VEC'),
            ("my.color_nine", 'COLORSET_09_VEC'),
            ("my.color_ten", 'COLORSET_11_VEC'),
            ("my.color_eleven", 'COLORSET_12_VEC'),
            ("my.color_twelve", 'COLORSET_13_VEC'),
            ("my.color_thirteen", 'COLORSET_14_VEC'),
            ("my.color_fourteen", 'COLORSET_15_VEC')
        ]

        i = 1
        for op_idname, icon in color_ops:
            create_presets_operator(row, op_idname, icon,
                            is_recording=self.is_recording,
                            index_offset = self.index_offset,
                            color_number = i,
                            group_name=group.name,
                            preset_type=self.preset_types_enum)
            i += 1

        if self.show_settings:
            row.prop(group, "show_in_presets_node", text="", icon='HIDE_OFF' if group.show_in_presets_node else 'HIDE_ON')
        row.alert = 0