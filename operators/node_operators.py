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


import bpy
from bpy.types import Operator
from bpy.props import StringProperty, IntProperty

# pyright: reportInvalidTypeForm=false

from ..as_ui.space_node import draw_node_formatter_footer, draw_node_formatter_group, draw_node_formatter_mixer
from ..cpvia.find import Find
from ..utils.osc import OSC


class NODE_OT_node_formatter(Operator):
    bl_idname = "nodes.show_node_formatter"
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
        layout = self.layout
        scene = context.scene
        column = layout.column(align=True)
        
        space = context.space_data.edit_tree.nodes
        active_node = None

        if hasattr(context.space_data, 'edit_tree') and context.space_data.edit_tree is not None:
            active_node = context.space_data.edit_tree.nodes.active

            if active_node and (active_node.bl_idname == "group_controller_type" or active_node.bl_idname == "group_driver_type" or active_node.bl_idname == "master_type"):
                draw_node_formatter_group(self, context, active_node)
                    
            elif active_node and active_node.bl_idname == "mixer_type" or active_node.bl_idname == "mixer_driver_type":
                draw_node_formatter_mixer(self, context, active_node)

            draw_node_formatter_footer(self, context, active_node)
            
            
class NODE_OT_keyframe_mixer(bpy.types.Operator):
    '''Keyframe mixer properties, since I key doesn't work here'''
    bl_idname = 'nodes.keyframe_mixer'
    bl_label = "Keyframe mixer"
    
    space_type: bpy.props.StringProperty() # type: ignore
    node_name: bpy.props.StringProperty() # type: ignore
    node_tree_name: bpy.props.StringProperty() # type: ignore
    
    def execute(self, context):
        finders = Find
        active_controller = finders.find_controller_by_space_type(context, self.space_type, self.node_name, self.node_tree_name)
        if not active_controller:
            return {'CANCELLED'}
        
        try:
            parameters = active_controller.parameters
            print("SUCCESS")
        except Exception as e:
            self.report({'INFO'}, "Please contact Alva Theaters.")
            print(f"Error: {str(e)}")
            return {'CANCELLED'}
        
        # Assuming `parameters` is a collection, we will access properties directly by name.
        if active_controller.parameters_enum == 'option_intensity':
            data_path = 'parameters["float_intensity"]'
            value = parameters.get("float_intensity")
            
        elif active_controller.parameters_enum == 'option_color':
            data_path = 'parameters["float_vec_color"]'
            value = parameters.get("float_vec_color")
            
        elif active_controller.parameters_enum == 'option_pan_tilt':
            data_path = 'parameters["float_pan"]'
            value = parameters.get("float_pan")
            
        elif active_controller.parameters_enum == 'option_zoom':
            data_path = 'parameters["float_zoom"]'
            value = parameters.get("float_zoom")
            
        elif active_controller.parameters_enum == 'option_iris':
            data_path = 'parameters["float_iris"]'
            value = parameters.get("float_iris")
        
        print(f"Attempting to keyframe: {data_path} with value: {value}")
        
        try:
            # Attempting to use keyframe_insert with the correct path
            active_controller.keyframe_insert(data_path=data_path, frame=bpy.context.scene.frame_current)
        except Exception as e:
            print(f"Failed to keyframe: {str(e)}")
            self.report({'ERROR'}, f"Failed to keyframe: {str(e)}")
            for prop_name in parameters.keys():
                print(f"Property name: {prop_name}")
                print(f"Value: {parameters[prop_name]}")
            return {'CANCELLED'}
    
        return {'FINISHED'}

        
class AddCustomButton(bpy.types.Operator):
    '''Add custom button'''
    bl_idname = "node.add_custom_button"
    bl_label = "Add Custom Button"

    def execute(self, context):
        node = context.node
        new_button = node.custom_buttons.add()
        new_button.button_label = ""
        new_button.constant_index = len(node.custom_buttons)
        return {'FINISHED'}


class RemoveCustomButton(bpy.types.Operator):
    '''Move the custom button's position in the stack vertically'''
    bl_idname = "node.remove_custom_button"
    bl_label = "Remove Custom Button"

    button_index: IntProperty()

    def execute(self, context):
        node = context.node

        if node.custom_buttons and 0 <= self.button_index < len(node.custom_buttons):
            node.custom_buttons.remove(self.button_index)
        else:
            self.report({'WARNING'}, "Invalid button index or no buttons to remove.")
        return {'FINISHED'}  
    
    
class BumpUpCustomButton(bpy.types.Operator):
    '''Move the custom button's position in the stack vertically'''
    bl_idname = "node.bump_up_custom_button"
    bl_label = "Move Button Up"

    button_index: IntProperty()

    def execute(self, context):
        node = context.node

        if 0 < self.button_index < len(node.custom_buttons):
            node.custom_buttons.move(self.button_index, self.button_index - 1)
        else:
            self.report({'WARNING'}, "Cannot move the first button up or invalid index.")

        return {'FINISHED'}


class BumpDownCustomButton(bpy.types.Operator):
    bl_idname = "node.bump_down_custom_button"
    bl_label = "Move Button Down"

    button_index: IntProperty()

    def execute(self, context):
        node = context.node

        if 0 <= self.button_index < len(node.custom_buttons) - 1:
            node.custom_buttons.move(self.button_index, self.button_index + 1)
        else:
            self.report({'WARNING'}, "Cannot move the last button down or invalid index.")

        return {'FINISHED'}

    
class CustomButton(bpy.types.Operator):
    '''Make a custom console button'''
    bl_idname = "node.custom_button"
    bl_label = "Custom Button"

    button_index: IntProperty()

    space_type: bpy.props.StringProperty() # type: ignore
    node_name: bpy.props.StringProperty() # type: ignore
    node_tree_name: bpy.props.StringProperty() # type: ignore

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


class RecordEffectPresetOperator(bpy.types.Operator):
    bl_idname = "node.record_effect_preset_operator"
    bl_label = "Record"
    bl_description = "Orb will record the node's group into the preset above onto the console using the argument template below"

    node_tree_name: StringProperty()
    node_name: StringProperty()
    
    def execute(self, context):
        active_node = Find.find_node_by_tree(self.node_name, self.node_tree_name)
        if not active_node:
            self.report({'ERROR'}, f"Node '{self.node_name}' not found in '{self.node_tree_name}'.")
            return {'CANCELLED'}
              
        finders = Find
        up_channels_list, down_channels_list = finders.find_flash_node_channels(self, update_nodes=True)
        up_channels_str, down_channels_str = finders.join_flash_channels(up_channels_list, down_channels_list)
        
        preset_number = active_node.int_start_preset
        OSC.send_osc_lighting("/eos/newcmd", "Group {str(up_channels_list)} Record Preset {str(preset_number)} Enter Enter")
        
        preset_number = active_node.int_end_preset
        OSC.send_osc_lighting("/eos/newcmd", "Group {str(down_channels_list)} Record Preset {str(preset_number)} Enter Enter")
        
        return {'FINISHED'}
    
    
class RecordDownEffectPresetOperator(bpy.types.Operator):  ## I'm pretty sure this was excommunicated?
    bl_idname = "node.record_down_effect_preset_operator"
    bl_label = "Record"
    bl_description = "Orb will record the node's group into the preset above onto the console using the argument template below"

    node_tree_name: StringProperty()  # Property to hold the node tree name
    node_name: StringProperty()  # Property to hold the node name

    def execute(self, context):
        node_tree = bpy.data.node_groups.get(self.node_tree_name)
        if not node_tree:
            for world in bpy.data.worlds:
                if world.node_tree and world.node_tree.name == self.node_tree_name:
                    node_tree = world.node_tree
                    if not node_tree:
                        self.report({'ERROR'}, f"Node tree '{self.node_tree_name}' not found.")
                        return {'CANCELLED'}

        active_node = node_tree.nodes.get(self.node_name)
        if not active_node:
            self.report({'ERROR'}, f"Node '{self.node_name}' not found in '{self.node_tree_name}'.")
            return {'CANCELLED'}
        
        if active_node:
            finders = Find()
            groups_list = []
            for input_socket in active_node.inputs:
                if input_socket.bl_idname == 'FlashDownType':
                    for link in input_socket.links:
                        connected_node = link.from_socket.node
                        if connected_node.bl_idname == "group_controller_type":
                            groups_list.append(finders.find_channels_list(connected_node))
                        elif connected_node.bl_idname == "group_driver_type":
                            for output_socket in connected_node.outputs:
                                if output_socket.bl_idname == 'GroupOutputType':
                                    for link in output_socket.links:
                                        driven_node = link.to_socket.node
                                        if driven_node.bl_idname == "group_controller_type":
                                            groups_list.append(finders.find_channels_list(driven_node))    
                        elif connected_node.bl_idname == "mixer_driver_type":
                            for output_socket in connected_node.outputs:
                                if output_socket.bl_idname == 'MixerOutputType':
                                    for link in output_socket.links:
                                        driven_node = link.to_socket.node
                                        if driven_node.bl_idname == "mixer_type":
                                            groups_list.append(finders.find_channels_list(driven_node))
                        elif connected_node.bl_idname == 'ShaderNodeGroup':
                            group_node_tree = connected_node.node_tree
                            for node in group_node_tree.nodes:
                                if node.type == 'GROUP_OUTPUT':
                                    for socket in node.inputs:
                                        if socket.name == "Flash":
                                            for inner_link in socket.links:
                                                interior_connected_node = inner_link.from_node
                                                if interior_connected_node.bl_idname == 'group_controller_type':
                                                    groups_list.append(finders.find_channels_list(interior_connected_node))
                                                elif interior_connected_node.bl_idname == "group_driver_type":
                                                    for output_socket in interior_connected_node.outputs:
                                                        if output_socket.bl_idname == 'GroupOutputType':
                                                            for link in output_socket.links:
                                                                driven_node = link.to_socket.node
                                                                if driven_node.bl_idname == "group_controller_type":
                                                                    groups_list.append(finders.find_channels_list(driven_node))
                                                    
        scene = context.scene
        node = context.active_node
        group_numbers = ' + Group '.join(groups_list)
        preset_number = active_node.int_end_preset
        argument_template = scene.scene_props.str_preset_assignment_argument
          
        argument = argument_template.replace("#", str(group_numbers))
        argument = argument.replace("$", str(preset_number))
          
        OSC.send_osc_lighting("/eos/newcmd", argument)
          
        for node_tree in bpy.data.node_groups:
            if node_tree.bl_idname == 'AlvaNodeTree':
                for node in node_tree.nodes:
                    if node.bl_idname == "flash_type" and node.flash_motif_names_enum != "":
                        node.flash_motif_names_enum = node.flash_motif_names_enum
            if node_tree.bl_idname == 'ShaderNodeTree':
                for node in world.node_tree.nodes:
                    if node.bl_idname == "flash_type" and node.flash_motif_names_enum != "":
                        node.flash_motif_names_enum = node.flash_motif_names_enum
                          
        snapshot = str(context.scene.orb_finish_snapshot)
        OSC.send_osc_lighting("/eos/newcmd", f"Snapshot {snapshot} Enter")
                          
        return {'FINISHED'}
    
    
def find_node_by_name(node_name):
    for node_tree in bpy.data.node_groups:
        if node_name in node_tree.nodes:
            return node_tree.nodes[node_name]
    for world in bpy.data.worlds:
        if world.node_tree and node_name in world.node_tree.nodes:
            return world.node_tree.nodes[node_name]
    return None
    
    
class FlashPresetSearchOperator(bpy.types.Operator):
    bl_idname = "node.flash_preset_search_operator"
    bl_label = "Search"
    bl_description = "Search for unused preset. Warning: does not poll the console."

    node_name: StringProperty(default="")
    node_group_name: StringProperty(default="")

    def execute(self, context):
        used_presets = set()

        for node_tree in bpy.data.node_groups:
            if node_tree.bl_idname == 'AlvaNodeTree' or node_tree.bl_idname == 'ShaderNodeTree':
                for node in node_tree.nodes:
                    if node.bl_idname == "flash_type":
                        used_presets.add(node.int_start_preset)
                        used_presets.add(node.int_end_preset)
        for world in bpy.data.worlds:
            if world.use_nodes:
                for node in world.node_tree.nodes:
                    if node.bl_idname == "flash_type":
                        used_presets.add(node.int_start_preset)
                        used_presets.add(node.int_end_preset)
                        
        result_one = 1
        result_two = 2 

        while result_one in used_presets or result_two in used_presets:
            result_one += 1
            result_two = result_one + 1

        active_node = find_node_by_name(self.node_name)
        
        if active_node and active_node.bl_idname == "flash_type":
            active_node.int_start_preset = result_one
            active_node.int_end_preset = result_two
        else:
            self.report({'WARNING'}, "Active node is not a valid 'flash_type' node.")

        return {'FINISHED'}
    

operators = [
    NODE_OT_node_formatter,
    NODE_OT_keyframe_mixer,
    RemoveCustomButton,
    CustomButton,
    BumpUpCustomButton,
    BumpDownCustomButton,
    AddCustomButton,
    RecordEffectPresetOperator,
    RecordDownEffectPresetOperator,
    FlashPresetSearchOperator
]


def register():
    for cls in operators:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(operators):
        bpy.utils.unregister_class(cls)