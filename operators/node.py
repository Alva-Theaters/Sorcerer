# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Operator
from bpy.props import IntProperty, StringProperty, BoolProperty

from ..as_ui.blender_spaces.space_node import draw_node_formatter_footer, draw_node_formatter_group, draw_node_formatter_mixer
from ..utils.cpv_utils import simplify_channels_list
from ..cpv.find import Find
from ..utils.osc import OSC

# pyright: reportInvalidTypeForm=false


class NODE_OT_alva_node_formatter(Operator):
    bl_idname = "alva_node.formatter"
    bl_label = "Node Formatter"
    
    @classmethod
    def poll(cls, context):
        return (context.scene is not None)

    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=300)
                
    def draw(self, context):
        active_node = None

        if hasattr(context.space_data, 'edit_tree') and context.space_data.edit_tree is not None:
            active_node = context.space_data.edit_tree.nodes.active

            if active_node and (active_node.bl_idname == "group_controller_type" or active_node.bl_idname == "group_driver_type" or active_node.bl_idname == "master_type"):
                draw_node_formatter_group(self, context, active_node)
                    
            elif active_node and active_node.bl_idname == "mixer_type" or active_node.bl_idname == "mixer_driver_type":
                draw_node_formatter_mixer(self, context, active_node)

            draw_node_formatter_footer(self, context, active_node)

        
class NODE_OT_add_direct_select(bpy.types.Operator):
    '''Add direct select'''
    bl_idname = "alva_node.add_direct_select"
    bl_label = "Add Direct Select"

    def execute(self, context):
        node = context.node
        new_button = node.custom_buttons.add()
        new_button.button_label = ""
        new_button.constant_index = len(node.custom_buttons)
        return {'FINISHED'}


class NODE_OT_remove_direct_select(bpy.types.Operator):
    '''Remove direct select'''
    bl_idname = "alva_node.remove_direct_select"
    bl_label = "Remove Direct Select"

    button_index: IntProperty()

    def execute(self, context):
        node = context.node

        if node.custom_buttons and 0 <= self.button_index < len(node.custom_buttons):
            node.custom_buttons.remove(self.button_index)
        else:
            self.report({'WARNING'}, "Invalid button index or no buttons to remove.")
        return {'FINISHED'}  
    
    
class NODE_OT_alva_bump_direct_select_up(Operator):
    '''Move the direct select's position in the stack vertically'''
    bl_idname = "alva_node.bump_direct_select_up"
    bl_label = "Move Button Up"

    button_index: IntProperty()

    def execute(self, context):
        node = context.node

        if 0 < self.button_index < len(node.custom_buttons):
            node.custom_buttons.move(self.button_index, self.button_index - 1)
        else:
            self.report({'WARNING'}, "Cannot move the first button up or invalid index.")

        return {'FINISHED'}


class NODE_OT_alva_bump_direct_select_down(Operator):
    bl_idname = "alva_node.bump_direct_select_down"
    bl_label = "Move Button Down"

    button_index: IntProperty()

    def execute(self, context):
        node = context.node

        if 0 <= self.button_index < len(node.custom_buttons) - 1:
            node.custom_buttons.move(self.button_index, self.button_index + 1)
        else:
            self.report({'WARNING'}, "Cannot move the last button down or invalid index.")

        return {'FINISHED'}

    
class NODE_OT_alva_direct_select(Operator):
    '''Direct select button'''
    bl_idname = "alva_node.direct_select"
    bl_label = "Direct Select"

    button_index: IntProperty()

    space_type: bpy.props.StringProperty() 
    node_name: bpy.props.StringProperty() 
    node_tree_name: bpy.props.StringProperty() 

    def execute(self, context):
        finders = Find
        node = finders.find_controller_by_space_type(context, self.space_type, self.node_name, self.node_tree_name)
        if not node:
            return {'CANCELLED'}
        
        this_button = node.custom_buttons[self.button_index]
        argument = node.direct_select_types_enum.replace(" ", "_")

        if argument == "Macro":
            this_button.button_address = "/eos/macro/fire"
            this_button.button_argument = str(this_button.constant_index)
        else:
            this_button.button_address = "/eos/cmd"
            this_button.button_argument = f"{argument} {this_button.constant_index}"

        OSC.send_osc_lighting(this_button.button_address, this_button.button_argument)
        return {'FINISHED'}
    

class NODE_OT_alva_mixer_add_choice(Operator):
    bl_idname = "alva_node.mixer_add_choice"
    bl_label = "Add Choice"
    bl_description = "Add a new choice"

    def execute(self, context):
        node = context.node
        choice = node.parameters.add()
        node.active_modifier_index = len(node.parameters) - 1
        choice.node_tree_name = node.id_data.name
        choice.node_name = node.name
        return {'FINISHED'}
    

class NODE_OT_alva_mixer_remove_choice(Operator):
    bl_idname = "alva_node.mixer_remove_choice"
    bl_label = "Remove Choice"
    bl_description = "Remove the last choice"

    def execute(self, context):
        node = context.node
        if node.parameters:
            index = len(node.parameters) - 1
            node.parameters.remove(index)
            node.active_modifier_index = max(0, len(node.parameters) - 1)
        return {'FINISHED'}
    

class NODE_OT_alva_color_grid_button(Operator):
    bl_idname = "alva_node.color_preset"
    bl_label = "Color Preset"
    bl_description = "Activate Color Palette or Preset"

    record_preset_argument_template: StringProperty(default="Chan # Record ^ $ Enter")
    preset_argument_template: StringProperty(default="Chan # ^ $ Enter")
    index_offset: IntProperty()
    is_recording: BoolProperty()
    color_number: IntProperty()
    group_name: StringProperty()
    preset_type: StringProperty()

    def execute(self, context):
        for grp in context.scene.scene_group_data:
            if grp.name == self.group_name:
                group = grp
        if not group:
            self.report({'INFO'}, "Cannot find group.")
            return {'CANCELLED'}
        
        channels = [chan.chan for chan in group.channels_list]
        channels_str = simplify_channels_list(channels)
        preset_number = self.color_number + self.index_offset
        argument_template = self.record_preset_argument_template if self.is_recording else self.preset_argument_template
        argument = argument_template.replace('#', channels_str).replace('$', str(preset_number)).replace('^', self.preset_type)
        
        OSC.send_osc_lighting("/eos/newcmd", argument)
        return {'FINISHED'}
    

operators = [
    NODE_OT_alva_node_formatter,
    NODE_OT_remove_direct_select,
    NODE_OT_alva_direct_select,
    NODE_OT_alva_bump_direct_select_up,
    NODE_OT_alva_bump_direct_select_down,
    NODE_OT_add_direct_select,
    NODE_OT_alva_mixer_add_choice,
    NODE_OT_alva_mixer_remove_choice,
    NODE_OT_alva_color_grid_button
]


def register():
    for cls in operators:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(operators):
        bpy.utils.unregister_class(cls)