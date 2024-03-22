# This file is part of Alva Sorcerer.
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
import socket
import time
import re
import json
import ast
import math
from bpy.types import PropertyGroup
from bpy.props import StringProperty
from bpy.types import Operator, Menu
import inspect


# Purpose of this throughout the codebase is to proactively identify possible pre-bugs and to help diagnose bugs.
def sorcerer_assert_unreachable(*args):
    caller_frame = inspect.currentframe().f_back
    caller_file = caller_frame.f_code.co_filename
    caller_line = caller_frame.f_lineno
    message = "Error found at {}:{}\nCode marked as unreachable has been executed. Please report bug to Alva Theaters.".format(caller_file, caller_line)
    print(message)


def send_osc_string(osc_addr, addr, port, string):
    
    def pad(data):
        return data + b"\0" * (4 - (len(data) % 4 or 4))

    if not osc_addr.startswith("/"):
        osc_addr = "/" + osc_addr

    osc_addr = osc_addr.encode() + b"\0"
    string = string.encode() + b"\0"
    tag = ",s".encode()

    message = b"".join(map(pad, (osc_addr, tag, string)))
    try:
        sock.sendto(message, (addr, port))

    except Exception:
        import traceback
        traceback.print_exc()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def get_frame_rate(scene):
    fps = scene.render.fps
    fps_base = scene.render.fps_base
    frame_rate = fps / fps_base
    return frame_rate


def parse_channels(input_string):
    formatted_input = re.sub(r'(\d)-(\d)', r'\1 - \2', input_string)
    tokens = re.split(r'[,\s]+', formatted_input)
    
    channels = []
    
    i = 0
    while i < len(tokens):
        token = tokens[i]
        
        if token in ("through", "thru", "-", "tthru", "throu", "--", "por") and i > 0 and i < len(tokens) - 1:
            start = int(tokens[i-1])
            end = int(tokens[i+1])
            step = 1 if start < end else -1
            channels.extend(range(start, end + step, step))  # Changed to extend for simplicity.
            i += 2  # Skip the next token because we've already processed it.
        elif token.isdigit():
            channels.append(int(token))
        i += 1
    
    return channels


#-------------------------------------------------------------------------------------------------------------------------------------------
'''Begin operators section'''
    
    
class PatchGroupOperator(bpy.types.Operator):
    bl_idname = "array.patch_group_operator"
    bl_label = "Patch Selected Lights as Group"
    bl_description = "Patch group on console"

    def find_addresses(context, starting_universe, starting_address, channel_mode, total_lights):
        address_list = []
        universe = starting_universe
        address = starting_address

        for i in range(total_lights):
            if address + channel_mode - 1 > 512:
                universe += 1
                address = 1
            address_list.append((universe, address))
            address += channel_mode
        return address_list

    def execute(self, context):
        space = context.space_data.edit_tree.nodes
        
        if hasattr(space, "active"):
            active_node = context.space_data.edit_tree.nodes.active
            
            scene = context.scene
            array_modifier = None
            if scene.scene_props.array_modifier_enum in context.active_object.modifiers:
                ip_address = scene.scene_props.str_osc_ip_address
                port = scene.scene_props.int_osc_port
                address = scene.scene_props.str_command_line_address
                
                array_modifier = context.active_object.modifiers[scene.scene_props.array_modifier_enum]
                
                if scene.scene_props.array_curve_enum != "NONE":
                    curve_modifier = context.active_object.modifiers[scene.scene_props.array_curve_enum]
                
                bpy.ops.object.modifier_apply(modifier=array_modifier.name)
                
                if context.object.mode != 'OBJECT':
                    bpy.ops.object.mode_set(mode='OBJECT')
                    
                if scene.scene_props.array_curve_enum != "NONE":   
                    bpy.ops.object.modifier_apply(modifier=curve_modifier.name)
                
                bpy.ops.object.editmode_toggle()
                bpy.ops.mesh.separate(type='LOOSE')
                bpy.ops.object.mode_set(mode='OBJECT')
                for obj in context.selected_objects:
                    if obj.type == 'MESH':
                        context.view_layer.objects.active = obj
                        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')
                
                starting_channel = scene.scene_props.int_array_start_channel
                group_number = scene.scene_props.int_array_group_index
                group_label = scene.scene_props.str_array_group_name
                starting_universe = scene.scene_props.int_array_universe
                start_address = scene.scene_props.int_array_start_address
                channels_to_add = scene.scene_props.int_array_channel_mode
                total_lights = len([chan for chan in bpy.data.objects if chan.select_get()])
                addresses_list = self.find_addresses(starting_universe, start_address, channels_to_add, total_lights)
                
                relevant_channels = []
            
                for i, chan in enumerate([obj for obj in bpy.data.objects if obj.select_get()]):
                    send_osc_string(address, ip_address, port, "Patch Enter")
                    time.sleep(.3)
                    
                    chan.name = str(scene.scene_props.int_array_start_channel)
                    current_universe, current_address = addresses_list[i]
                    #Make sure there wasn't a conflict that automatically changed it to 1.001 or something.
                    if chan.name != str(scene.scene_props.int_array_start_channel):
                        self.report({'ERROR'}, "Object naming is incorrect, must be integer only.")
                    
                    position_x = round(chan.location.x / .3048)
                    position_y = round(chan.location.y / .3048)
                    position_z = round(chan.location.z / .3048)
                    
                    # Rotate by 180 degrees (pi in radians) since cone facing up is the same as a light facing down.
                    orientation_x = round(math.degrees(chan.rotation_euler.x + math.pi))
                    orientation_y = round(math.degrees(chan.rotation_euler.y))
                    orientation_z = round(math.degrees(chan.rotation_euler.z))
                    send_osc_string(address, ip_address, port, f"Chan {chan.name} Type {scene.scene_props.str_array_group_maker} {scene.scene_props.str_array_group_type} Enter, Chan {chan.name} Position {position_x} / {position_y} / {position_z} Enter, Chan {chan.name} Orientation {orientation_x} / {orientation_y} / {orientation_z} Enter, Chan {chan.name} at {str(current_universe)} / {str(current_address)} Enter")
                    channel_number = int(chan.name)
                    relevant_channels.append(channel_number)
                    scene.scene_props.int_array_start_channel += 1
                    time.sleep(.5)
                
                scene.scene_props.int_array_start_channel = int(chan.name) + 1
                scene.scene_props.int_array_start_address = current_address + channels_to_add
                scene.scene_props.int_array_universe = current_universe
                scene.scene_props.int_array_group_index += 1
                
                # Create the group.
                send_osc_string("/eos/key/group", ip_address, port, "1")
                time.sleep(.1)
                send_osc_string("/eos/key/group", ip_address, port, "0")
                time.sleep(.1)
                send_osc_string("/eos/key/group", ip_address, port, "1")
                time.sleep(.1)
                send_osc_string("/eos/key/group", ip_address, port, "0")
                
                time.sleep(1)
                
                send_osc_string("/eos/newcmd", ip_address, port, f"Group {group_number} Enter")
                
                time.sleep(1)
                
                send_osc_string("/eos/newcmd", ip_address, port, f"Group {group_number} Label {group_label}")
                
                time.sleep(1)
                
                send_osc_string("/eos/key/enter", ip_address, port, "1")
                time.sleep(.1)
                send_osc_string("/eos/key/enter", ip_address, port, "0")
                time.sleep(.1)
                send_osc_string("/eos/key/enter", ip_address, port, "1")
                time.sleep(.1)
                send_osc_string("/eos/key/enter", ip_address, port, "0")
                
                time.sleep(1)
                
                argument = "Chan "
                if len(relevant_channels) != 0: 
                    for light in relevant_channels:
                        argument += f"{light} "
                    argument += "Enter Enter"
                    
                send_osc_string("/eos/newcmd", ip_address, port, f"Group {group_number} Enter, Chan {argument}")
                
                time.sleep(1)
                
                send_osc_string(address, ip_address, port, "Patch Enter")
                time.sleep(.3)
                
                send_osc_string("/eos/newcmd", ip_address, port, f"{argument}")
                
                time.sleep(1)
                
                # Select the new lights on the console for highlight visibility.
                send_osc_string(address, ip_address, port, argument)

                bpy.ops.object.editmode_toggle()
                bpy.ops.object.editmode_toggle()
                
                scene.scene_props.array_cone_enum = "NONE"
                scene.scene_props.array_modifier_enum = "NONE"
                scene.scene_props.array_curve_enum = "NONE"
                
                #################################
                # Begin to add controller
                #################################

                # When retrieving the dictionary from the property.
                try:
                    groups_data = eval(scene.scene_props.group_data)
                except (SyntaxError, NameError, TypeError):
                    groups_data = {}

                groups_data[str(group_number)] = {'label': group_label, 'channels': relevant_channels}  # group_number is already a string

                scene.scene_props.group_data = str(groups_data)             
                
                # Begin adding controller.
                tree = context.space_data.edit_tree
                new_controller = tree.nodes.new('group_controller_type')
                new_controller.str_selected_light = str(group_number)

                new_controller.strobe_is_on = scene.scene_props.strobe_is_on
                new_controller.color_is_on = scene.scene_props.color_is_on
                new_controller.pan_tilt_is_on = scene.scene_props.pan_tilt_is_on
                new_controller.diffusion_is_on = scene.scene_props.diffusion_is_on
                new_controller.edge_is_on = scene.scene_props.edge_is_on
                new_controller.iris_is_on = scene.scene_props.iris_is_on
                new_controller.gobo_id_is_on = scene.scene_props.gobo_id_is_on
                new_controller.zoom_is_on = scene.scene_props.zoom_is_on
            
                new_controller.label = new_controller.str_group_label
                        
        return {'FINISHED'}


class RemoveGroupOperator(bpy.types.Operator):
    bl_idname = "group.remove_group"
    bl_label = "Remove Group"
    bl_description = "Remove this group"

    group_id: bpy.props.IntProperty()  

    def execute(self, context):
        scene = context.scene.scene_props
        group_id = str(self.group_id)  

        # Load the existing groups_data.
        try:
            groups_data = eval(scene.group_data)
        except (SyntaxError, NameError, TypeError):
            self.report({'ERROR'}, "Invalid groups data")
            return {'CANCELLED'}

        # Check if the group_id exists in groups_data and remove it.
        if group_id in groups_data:
            del groups_data[group_id]  # Remove the group.
            scene.group_data = str(groups_data)  # Update the scene's group_data.
            self.report({'INFO'}, f"Removed group with ID: {group_id}")
            
        # need to figure out why this is not consistent later.
        else:
            group_id = int(group_id)
            if group_id in groups_data:
                del groups_data[group_id]  # Remove the group.
                scene.group_data = str(groups_data)  # Update the scene's group_data.
                self.report({'INFO'}, f"Removed group with ID: {group_id}")
            
            else: self.report({'ERROR'}, f"Group with ID: {group_id} not found")

        return {'FINISHED'}
    
    
class AddGroupToSceneOperator(bpy.types.Operator):
    bl_idname = "group.add_group_to_scene"
    bl_label = "Add Group to Scene"
    bl_description = "Add this to the dropdown in the Group Controller nodes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene.scene_props
        group_label = scene.str_group_label_to_add
        group_number = str(scene.int_group_number_to_add)  # Convert to string here.
        channels = parse_channels(scene.str_group_channels_to_add)
        
        # Attempt to load the existing group_data or initialize an empty dictionary.
        try:
            groups_data = eval(scene.group_data)
        except (SyntaxError, NameError, TypeError):
            groups_data = {}

        groups_data[group_number] = {'label': group_label, 'channels': channels}  # group_number is already a string.

        scene.group_data = str(groups_data)

        scene.str_group_label_to_add = ""
        scene.int_group_number_to_add += 1

        self.report({'INFO'}, f"Added Group {group_number} with label '{group_label}'")
        
        return {'FINISHED'}
    
      
class AddChannelToGroupOperator(bpy.types.Operator):
    bl_idname = "group.add_channel_to_group"
    bl_label = ""
    bl_description = "Add Channel to Group"
    
    group_id: bpy.props.StringProperty()
    
    def execute(self, context):
        # Deserialize the group data.
        groups_data = eval(context.scene.scene_props.group_data)
        
        # Get the channel to add from the scene property.
        channel_to_add = parse_channels(context.scene.scene_props.add_channel_ids)
        
        # Convert channel to string to match keys in groups_data.
        group_id_str = str(self.group_id)

        if self.group_id in groups_data:
            # Add each specified channel to the group.
            for channel in channel_to_add:
                if channel not in groups_data[self.group_id]['channels']:
                    groups_data[self.group_id]['channels'].append(channel)
                    
            # Trigger the group info updater.
            scene = context.scene
            world = scene.world
            if world is not None and world.node_tree:
                node_tree = world.node_tree
            
                for controller in node_tree.nodes:
                    if controller.bl_idname == 'group_controller_type':
                        controller.str_selected_light = controller.str_selected_light

            # Serialize and update the group data.
            context.scene.scene_props.group_data = str(groups_data)
          
        return {'FINISHED'}
    
    
class RemoveChannelFromGroupOperator(bpy.types.Operator):
    bl_idname = "group.remove_channel_from_group"
    bl_label = "Remove Channel from Group"
    bl_description = "Remove Channel from Group"
    
    group_id: bpy.props.StringProperty()  # Use StringProperty instead of IntProperty.
    channel: bpy.props.IntProperty()
    
    def execute(self, context):
        # Deserialize the group data.
        groups_data = eval(context.scene.scene_props.group_data)
        
        # Convert channel to string to match keys in groups_data.
        group_id_str = str(self.group_id)

        # Check if the group exists and the channel is in that group.
        if group_id_str in groups_data and self.channel in groups_data[group_id_str]['channels']:
            groups_data[group_id_str]['channels'].remove(self.channel)  # Remove the channel.
            context.scene.scene_props.group_data = str(groups_data)  # Update the scene's group_data.
            
            # Trigger the group info updater.
            scene = context.scene
            world = scene.world
            if world is not None and world.node_tree:
                node_tree = world.node_tree
            
                for controller in node_tree.nodes:
                    if controller.bl_idname == 'group_controller_type':
                        controller.str_selected_light = controller.str_selected_light
            self.report({'INFO'}, f"Removed channel {self.channel} from group {group_id_str}")

        else:
            self.report({'ERROR'}, f"Group with ID: {group_id_str} not found or channel {self.channel} not in group")

        return {'FINISHED'}
    
    
#-----------------------------------------------------------------------------------------------------------------------------------------------
'''Begin Presets Node operators'''

## Why is there all this repeated code? Needs to utilize universal functions.
class ColorOne(bpy.types.Operator):
    bl_idname = "my.color_one"
    bl_label = "Color One"
    bl_description = "Activate Color One"
    
    color_argument_template: bpy.props.StringProperty()
    record_color_argument_template: bpy.props.StringProperty()
    preset_argument_template: bpy.props.StringProperty()
    group_id: bpy.props.StringProperty()
    is_recording: bpy.props.BoolProperty()
    
    index_offset: bpy.props.IntProperty(default=0, description="Start button index here")
    
    def execute(self, context):
        if self.is_recording:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.record_color_argument_template.replace('#', str(index))
            argument = argument.replace('$', "1")
            
            send_osc_string(address, ip_address, port, argument)           
           
        else:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.color_argument_template.replace('#', str(index))
            argument = argument.replace('$', "1")
            
            send_osc_string(address, ip_address, port, argument)
            
        return {'FINISHED'}


class ColorTwo(bpy.types.Operator):
    bl_idname = "my.color_two"
    bl_label = "Color Two"
    bl_description = "Activate Color Two"
    
    color_argument_template: bpy.props.StringProperty()
    record_color_argument_template: bpy.props.StringProperty()
    preset_argument_template: bpy.props.StringProperty()
    group_id: bpy.props.StringProperty()
    is_recording: bpy.props.BoolProperty()
    index_offset: bpy.props.IntProperty()
    
    def execute(self, context):
        if self.is_recording:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.record_color_argument_template.replace('#', str(index))
            argument = argument.replace('$', "2")
            
            send_osc_string(address, ip_address, port, argument)           
           
        else:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.color_argument_template.replace('#', str(index))
            argument = argument.replace('$', "2")
            
            send_osc_string(address, ip_address, port, argument)
            
        return {'FINISHED'}
        
    
class ColorThree(bpy.types.Operator):
    bl_idname = "my.color_three"
    bl_label = "Color Three"
    bl_description = "Activate Color Three"
    
    color_argument_template: bpy.props.StringProperty()
    record_color_argument_template: bpy.props.StringProperty()
    preset_argument_template: bpy.props.StringProperty()
    group_id: bpy.props.StringProperty()
    is_recording: bpy.props.BoolProperty()
    index_offset: bpy.props.IntProperty()
    
    def execute(self, context):
        if self.is_recording:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.record_color_argument_template.replace('#', str(index))
            argument = argument.replace('$', "3")
            
            send_osc_string(address, ip_address, port, argument)           
           
        else:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.color_argument_template.replace('#', str(index))
            argument = argument.replace('$', "3")
            
            send_osc_string(address, ip_address, port, argument)
            
        return {'FINISHED'}
        
    
class ColorFour(bpy.types.Operator):
    bl_idname = "my.color_four"
    bl_label = "Color Four"
    bl_description = "Activate Color Four"

    color_argument_template: bpy.props.StringProperty()
    record_color_argument_template: bpy.props.StringProperty()
    preset_argument_template: bpy.props.StringProperty()
    group_id: bpy.props.StringProperty()
    is_recording: bpy.props.BoolProperty()
    index_offset: bpy.props.IntProperty()
    
    def execute(self, context):
        if self.is_recording:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.record_color_argument_template.replace('#', str(index))
            argument = argument.replace('$', "4")
            
            send_osc_string(address, ip_address, port, argument)           
           
        else:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.color_argument_template.replace('#', str(index))
            argument = argument.replace('$', "4")
            
            send_osc_string(address, ip_address, port, argument)
            
        return {'FINISHED'}


class ColorFive(bpy.types.Operator):
    bl_idname = "my.color_five"
    bl_label = "Color Five"
    bl_description = "Activate Color Five"
    
    color_argument_template: bpy.props.StringProperty()
    record_color_argument_template: bpy.props.StringProperty()
    preset_argument_template: bpy.props.StringProperty()
    group_id: bpy.props.StringProperty()
    is_recording: bpy.props.BoolProperty()
    index_offset: bpy.props.IntProperty()
    
    def execute(self, context):
        if self.is_recording:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.record_color_argument_template.replace('#', str(index))
            argument = argument.replace('$', "5")
            
            send_osc_string(address, ip_address, port, argument)           
           
        else:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.color_argument_template.replace('#', str(index))
            argument = argument.replace('$', "5")
            
            send_osc_string(address, ip_address, port, argument)
            
        return {'FINISHED'}


class ColorSix(bpy.types.Operator):
    bl_idname = "my.color_six"
    bl_label = "Color Six"
    bl_description = "Activate Color Six"
    
    color_argument_template: bpy.props.StringProperty()
    record_color_argument_template: bpy.props.StringProperty()
    preset_argument_template: bpy.props.StringProperty()
    group_id: bpy.props.StringProperty()
    is_recording: bpy.props.BoolProperty()
    index_offset: bpy.props.IntProperty()
    
    def execute(self, context):
        if self.is_recording:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.record_color_argument_template.replace('#', str(index))
            argument = argument.replace('$', "6")
            
            send_osc_string(address, ip_address, port, argument)           
           
        else:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.color_argument_template.replace('#', str(index))
            argument = argument.replace('$', "6")
            
            send_osc_string(address, ip_address, port, argument)
            
        return {'FINISHED'}


class ColorSeven(bpy.types.Operator):
    bl_idname = "my.color_seven"
    bl_label = "Color Seven"
    bl_description = "Activate Color Seven"

    color_argument_template: bpy.props.StringProperty()
    record_color_argument_template: bpy.props.StringProperty()
    preset_argument_template: bpy.props.StringProperty()
    group_id: bpy.props.StringProperty()
    is_recording: bpy.props.BoolProperty()
    index_offset: bpy.props.IntProperty()
    
    def execute(self, context):
        if self.is_recording:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.record_color_argument_template.replace('#', str(index))
            argument = argument.replace('$', "7")
            
            send_osc_string(address, ip_address, port, argument)           
           
        else:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.color_argument_template.replace('#', str(index))
            argument = argument.replace('$', "7")
            
            send_osc_string(address, ip_address, port, argument)
            
        return {'FINISHED'}


class ColorEight(bpy.types.Operator):
    bl_idname = "my.color_eight"
    bl_label = "Color Eight"
    bl_description = "Activate Color Eight"
    
    color_argument_template: bpy.props.StringProperty()
    record_color_argument_template: bpy.props.StringProperty()
    preset_argument_template: bpy.props.StringProperty()
    group_id: bpy.props.StringProperty()
    is_recording: bpy.props.BoolProperty()
    index_offset: bpy.props.IntProperty()
    
    def execute(self, context):
        if self.is_recording:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.record_color_argument_template.replace('#', str(index))
            argument = argument.replace('$', "8")
            
            send_osc_string(address, ip_address, port, argument)           
           
        else:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.color_argument_template.replace('#', str(index))
            argument = argument.replace('$', "8")
            
            send_osc_string(address, ip_address, port, argument)
            
        return {'FINISHED'}


class ColorNine(bpy.types.Operator):
    bl_idname = "my.color_nine"
    bl_label = "Color Nine"
    bl_description = "Activate Color Nine"
    
    color_argument_template: bpy.props.StringProperty()
    record_color_argument_template: bpy.props.StringProperty()
    preset_argument_template: bpy.props.StringProperty()
    group_id: bpy.props.StringProperty()
    is_recording: bpy.props.BoolProperty()
    index_offset: bpy.props.IntProperty()
    
    def execute(self, context):
        if self.is_recording:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.record_color_argument_template.replace('#', str(index))
            argument = argument.replace('$', "9")
            
            send_osc_string(address, ip_address, port, argument)           
           
        else:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.color_argument_template.replace('#', str(index))
            argument = argument.replace('$', "9")
            
            send_osc_string(address, ip_address, port, argument)
            
        return {'FINISHED'}


class ColorTen(bpy.types.Operator):
    bl_idname = "my.color_ten"
    bl_label = "Color Ten"
    bl_description = "Activate Color Ten"
    
    color_argument_template: bpy.props.StringProperty()
    record_color_argument_template: bpy.props.StringProperty()
    preset_argument_template: bpy.props.StringProperty()
    group_id: bpy.props.StringProperty()
    is_recording: bpy.props.BoolProperty()
    index_offset: bpy.props.IntProperty()
    
    def execute(self, context):
        if self.is_recording:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.record_color_argument_template.replace('#', str(index))
            argument = argument.replace('$', "10")
            
            send_osc_string(address, ip_address, port, argument)           
           
        else:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.color_argument_template.replace('#', str(index))
            argument = argument.replace('$', "10")
            
            send_osc_string(address, ip_address, port, argument)
            
        return {'FINISHED'}


class ColorEleven(bpy.types.Operator):
    bl_idname = "my.color_eleven"
    bl_label = "Color Eleven"
    bl_description = "Activate Color Eleven"
    
    color_argument_template: bpy.props.StringProperty()
    record_color_argument_template: bpy.props.StringProperty()
    preset_argument_template: bpy.props.StringProperty()
    group_id: bpy.props.StringProperty()
    is_recording: bpy.props.BoolProperty()
    index_offset: bpy.props.IntProperty()
    
    def execute(self, context):
        if self.is_recording:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.record_color_argument_template.replace('#', str(index))
            argument = argument.replace('$', "11")
            
            send_osc_string(address, ip_address, port, argument)           
           
        else:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.color_argument_template.replace('#', str(index))
            argument = argument.replace('$', "11")
            
            send_osc_string(address, ip_address, port, argument)
            
        return {'FINISHED'}


class ColorTwelve(bpy.types.Operator):
    bl_idname = "my.color_twelve"
    bl_label = "Color Twelve"
    bl_description = "Activate Color Twelve"
    
    color_argument_template: bpy.props.StringProperty()
    record_color_argument_template: bpy.props.StringProperty()
    preset_argument_template: bpy.props.StringProperty()
    group_id: bpy.props.StringProperty()
    is_recording: bpy.props.BoolProperty()
    index_offset: bpy.props.IntProperty()
    
    def execute(self, context):
        if self.is_recording:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.record_color_argument_template.replace('#', str(index))
            argument = argument.replace('$', "12")
            
            send_osc_string(address, ip_address, port, argument)           
           
        else:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.color_argument_template.replace('#', str(index))
            argument = argument.replace('$', "12")
            
            send_osc_string(address, ip_address, port, argument)
            
        return {'FINISHED'}


class ColorThirteen(bpy.types.Operator):
    bl_idname = "my.color_thirteen"
    bl_label = "Color Thirteen"
    bl_description = "Activate Color Thirteen"
    
    color_argument_template: bpy.props.StringProperty()
    record_color_argument_template: bpy.props.StringProperty()
    preset_argument_template: bpy.props.StringProperty()
    group_id: bpy.props.StringProperty()
    is_recording: bpy.props.BoolProperty()
    index_offset: bpy.props.IntProperty()
    
    def execute(self, context):
        if self.is_recording:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.record_color_argument_template.replace('#', str(index))
            argument = argument.replace('$', "13")
            
            send_osc_string(address, ip_address, port, argument)           
           
        else:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.color_argument_template.replace('#', str(index))
            argument = argument.replace('$', "13")
            
            send_osc_string(address, ip_address, port, argument)
            
        return {'FINISHED'}


class ColorFourteen(bpy.types.Operator):
    bl_idname = "my.color_fourteen"
    bl_label = "Color Fourteen"
    bl_description = "Activate Color Fourteen"
    
    color_argument_template: bpy.props.StringProperty()
    record_color_argument_template: bpy.props.StringProperty()
    preset_argument_template: bpy.props.StringProperty()
    group_id: bpy.props.StringProperty()
    is_recording: bpy.props.BoolProperty()
    index_offset: bpy.props.IntProperty()
    
    def execute(self, context):
        if self.is_recording:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port
            index = int(self.group_id) + self.index_offset

            argument = self.record_color_argument_template.replace('#', str(index))
            argument = argument.replace('$', "14")
            
            send_osc_string(address, ip_address, port, argument)           
           
        else:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.color_argument_template.replace('#', str(index))
            argument = argument.replace('$', "14")
            
            send_osc_string(address, ip_address, port, argument)
            
        return {'FINISHED'}


class ColorFifteen(bpy.types.Operator):
    bl_idname = "my.color_fifteen"
    bl_label = "Color Fifteen"
    bl_description = "Activate Color Fifteen"
    
    color_argument_template: bpy.props.StringProperty()
    record_color_argument_template: bpy.props.StringProperty()
    preset_argument_template: bpy.props.StringProperty()
    group_id: bpy.props.StringProperty()
    is_recording: bpy.props.BoolProperty()
    index_offset: bpy.props.IntProperty()
    
    def execute(self, context):
        if self.is_recording:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.record_color_argument_template.replace('#', str(index))
            argument = argument.replace('$', "15")
            
            send_osc_string(address, ip_address, port, argument)           
           
        else:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.color_argument_template.replace('#', str(index))
            argument = argument.replace('$', "15")
            
            send_osc_string(address, ip_address, port, argument)
            
        return {'FINISHED'}


class FOne(bpy.types.Operator):
    bl_idname = "my.f_one"
    bl_label = "F One"
    bl_description = "Activate F One"
    
    color_argument_template: bpy.props.StringProperty()
    record_preset_argument_template: bpy.props.StringProperty()
    preset_argument_template: bpy.props.StringProperty()
    group_id: bpy.props.StringProperty()
    is_recording: bpy.props.BoolProperty()
    index_offset: bpy.props.IntProperty()
    
    def execute(self, context):
        if self.is_recording:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.record_preset_argument_template.replace('#', str(index))
            argument = argument.replace('$', "1")
            
            send_osc_string(address, ip_address, port, argument)           
           
        else:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset
            print(self.preset_argument_template)
            argument = self.preset_argument_template.replace('#', str(index))
            argument = argument.replace('$', "1")
            
            send_osc_string(address, ip_address, port, argument)
            
        return {'FINISHED'}


class FTwo(bpy.types.Operator):
    bl_idname = "my.f_two"
    bl_label = "F Two"
    bl_description = "Activate F Two"
    
    color_argument_template: bpy.props.StringProperty()
    record_preset_argument_template: bpy.props.StringProperty()
    preset_argument_template: bpy.props.StringProperty()
    group_id: bpy.props.StringProperty()
    is_recording: bpy.props.BoolProperty()
    index_offset: bpy.props.IntProperty()
    
    def execute(self, context):
        if self.is_recording:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.record_preset_argument_template.replace('#', str(index))
            argument = argument.replace('$', "2")
            
            send_osc_string(address, ip_address, port, argument)           
           
        else:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.preset_argument_template.replace('#', str(index))
            argument = argument.replace('$', "2")
            
            send_osc_string(address, ip_address, port, argument)
            
        return {'FINISHED'}


class FThree(bpy.types.Operator):
    bl_idname = "my.f_three"
    bl_label = "F Three"
    bl_description = "Activate F Three"
    
    color_argument_template: bpy.props.StringProperty()
    record_preset_argument_template: bpy.props.StringProperty()
    preset_argument_template: bpy.props.StringProperty()
    group_id: bpy.props.StringProperty()
    is_recording: bpy.props.BoolProperty()
    index_offset: bpy.props.IntProperty()
    
    def execute(self, context):
        if self.is_recording:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.record_preset_argument_template.replace('#', str(index))
            argument = argument.replace('$', "3")
            
            send_osc_string(address, ip_address, port, argument)           
           
        else:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.preset_argument_template.replace('#', str(index))
            argument = argument.replace('$', "3")
            
            send_osc_string(address, ip_address, port, argument)
            
        return {'FINISHED'}


class FFour(bpy.types.Operator):
    bl_idname = "my.f_four"
    bl_label = "F Four"
    bl_description = "Activate F Four"
    
    color_argument_template: bpy.props.StringProperty()
    record_preset_argument_template: bpy.props.StringProperty()
    preset_argument_template: bpy.props.StringProperty()
    group_id: bpy.props.StringProperty()
    is_recording: bpy.props.BoolProperty()
    index_offset: bpy.props.IntProperty()
    
    def execute(self, context):
        if self.is_recording:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.record_preset_argument_template.replace('#', str(index))
            argument = argument.replace('$', "4")
            
            send_osc_string(address, ip_address, port, argument)           
           
        else:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.preset_argument_template.replace('#', str(index))
            argument = argument.replace('$', "4")
            
            send_osc_string(address, ip_address, port, argument)
            
        return {'FINISHED'}


class FFive(bpy.types.Operator):
    bl_idname = "my.f_five"
    bl_label = "F Five"
    bl_description = "Activate F Five"
    
    color_argument_template: bpy.props.StringProperty()
    record_preset_argument_template: bpy.props.StringProperty()
    preset_argument_template: bpy.props.StringProperty()
    group_id: bpy.props.StringProperty()
    is_recording: bpy.props.BoolProperty()
    index_offset: bpy.props.IntProperty()
    
    def execute(self, context):
        if self.is_recording:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.record_preset_argument_template.replace('#', str(index))
            argument = argument.replace('$', "5")
            
            send_osc_string(address, ip_address, port, argument)           
           
        else:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.preset_argument_template.replace('#', str(index))
            argument = argument.replace('$', "5")
            
            send_osc_string(address, ip_address, port, argument)
            
        return {'FINISHED'}


class FSix(bpy.types.Operator):
    bl_idname = "my.f_six"
    bl_label = "F Six"
    bl_description = "Activate F Six"
    
    color_argument_template: bpy.props.StringProperty()
    record_preset_argument_template: bpy.props.StringProperty()
    preset_argument_template: bpy.props.StringProperty()
    group_id: bpy.props.StringProperty()
    is_recording: bpy.props.BoolProperty()
    index_offset: bpy.props.IntProperty()
    
    def execute(self, context):
        if self.is_recording:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.record_preset_argument_template.replace('#', str(index))
            argument = argument.replace('$', "6")
            
            send_osc_string(address, ip_address, port, argument)           
           
        else:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.preset_argument_template.replace('#', str(index))
            argument = argument.replace('$', "6")
            
            send_osc_string(address, ip_address, port, argument)
            
        return {'FINISHED'}


class FSeven(bpy.types.Operator):
    bl_idname = "my.f_seven"
    bl_label = "F Seven"
    bl_description = "Activate F Seven"
    
    color_argument_template: bpy.props.StringProperty()
    record_preset_argument_template: bpy.props.StringProperty()
    preset_argument_template: bpy.props.StringProperty()
    group_id: bpy.props.StringProperty()
    is_recording: bpy.props.BoolProperty()
    index_offset: bpy.props.IntProperty()
    
    def execute(self, context):
        if self.is_recording:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.record_preset_argument_template.replace('#', str(index))
            argument = argument.replace('$', "7")
            
            send_osc_string(address, ip_address, port, argument)           
           
        else:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.preset_argument_template.replace('#', str(index))
            argument = argument.replace('$', "7")
            
            send_osc_string(address, ip_address, port, argument)
            
        return {'FINISHED'}


class FEight(bpy.types.Operator):
    bl_idname = "my.f_eight"
    bl_label = "F Eight"
    bl_description = "Activate F Eight"
    
    color_argument_template: bpy.props.StringProperty()
    record_preset_argument_template: bpy.props.StringProperty()
    preset_argument_template: bpy.props.StringProperty()
    group_id: bpy.props.StringProperty()
    is_recording: bpy.props.BoolProperty()
    index_offset: bpy.props.IntProperty()
    
    def execute(self, context):
        if self.is_recording:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.record_preset_argument_template.replace('#', str(index))
            argument = argument.replace('$', "8")
            
            send_osc_string(address, ip_address, port, argument)           
           
        else:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.preset_argument_template.replace('#', str(index))
            argument = argument.replace('$', "8")
            
            send_osc_string(address, ip_address, port, argument)
            
        return {'FINISHED'}


class FNine(bpy.types.Operator):
    bl_idname = "my.f_nine"
    bl_label = "F Nine"
    bl_description = "Activate F Nine"
    
    color_argument_template: bpy.props.StringProperty()
    record_preset_argument_template: bpy.props.StringProperty()
    preset_argument_template: bpy.props.StringProperty()
    group_id: bpy.props.StringProperty()
    is_recording: bpy.props.BoolProperty()
    index_offset: bpy.props.IntProperty()
    
    def execute(self, context):
        if self.is_recording:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.record_preset_argument_template.replace('#', str(index))
            argument = argument.replace('$', "9")
            
            send_osc_string(address, ip_address, port, argument)           
           
        else:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.preset_argument_template.replace('#', str(index))
            argument = argument.replace('$', "9")
            
            send_osc_string(address, ip_address, port, argument)
            
        return {'FINISHED'}


class FTen(bpy.types.Operator):
    bl_idname = "my.f_ten"
    bl_label = "F Ten"
    bl_description = "Activate F Ten"
    
    color_argument_template: bpy.props.StringProperty()
    record_preset_argument_template: bpy.props.StringProperty()
    preset_argument_template: bpy.props.StringProperty()
    group_id: bpy.props.StringProperty()
    is_recording: bpy.props.BoolProperty()
    index_offset: bpy.props.IntProperty()
    
    def execute(self, context):
        if self.is_recording:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.record_preset_argument_template.replace('#', str(index))
            argument = argument.replace('$', "10")
            
            send_osc_string(address, ip_address, port, argument)           
           
        else:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.preset_argument_template.replace('#', str(index))
            argument = argument.replace('$', "10")
            
            send_osc_string(address, ip_address, port, argument)
            
        return {'FINISHED'}


class FEleven(bpy.types.Operator):
    bl_idname = "my.f_eleven"
    bl_label = "F Eleven"
    bl_description = "Activate F Eleven"
    
    color_argument_template: bpy.props.StringProperty()
    record_preset_argument_template: bpy.props.StringProperty()
    preset_argument_template: bpy.props.StringProperty()
    group_id: bpy.props.StringProperty()
    is_recording: bpy.props.BoolProperty()
    index_offset: bpy.props.IntProperty()
    
    def execute(self, context):
        if self.is_recording:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.record_preset_argument_template.replace('#', str(index))
            argument = argument.replace('$', "11")
            
            send_osc_string(address, ip_address, port, argument)           
           
        else:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.preset_argument_template.replace('#', str(index))
            argument = argument.replace('$', "11")
            
            send_osc_string(address, ip_address, port, argument)
            
        return {'FINISHED'}


class FTwelve(bpy.types.Operator):
    bl_idname = "my.f_twelve"
    bl_label = "F Twelve"
    bl_description = "Activate F Twelve"
    
    color_argument_template: bpy.props.StringProperty()
    record_preset_argument_template: bpy.props.StringProperty()
    preset_argument_template: bpy.props.StringProperty()
    group_id: bpy.props.StringProperty()
    is_recording: bpy.props.BoolProperty()
    index_offset: bpy.props.IntProperty()
    
    def execute(self, context):
        if self.is_recording:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.record_preset_argument_template.replace('#', str(index))
            argument = argument.replace('$', "12")
            
            send_osc_string(address, ip_address, port, argument)           
           
        else:
            scene = context.scene.scene_props
            address = scene.str_command_line_address
            ip_address = scene.str_osc_ip_address
            port = scene.int_osc_port

            index = int(self.group_id) + self.index_offset

            argument = self.preset_argument_template.replace('#', str(index))
            argument = argument.replace('$', "12")
            
            send_osc_string(address, ip_address, port, argument)
            
        return {'FINISHED'}


#-----------------------------------------------------------------------------------------------------------------------------------------------
'''USITT ASCII Parsing Operator'''


class SendUSITTASCIITo3DOperator(bpy.types.Operator):
    bl_idname = "my.send_usitt_ascii_to_3d"
    bl_label = ""
    bl_description = "Automatically populate fixtures in Blender based on USITT ASCII export from the console"
    bl_options = {'REGISTER', 'UNDO'}
    
    def is_too_close(self, new_pos, existing_positions, threshold):
        for pos in existing_positions:
            if abs(new_pos[0] - pos[0]) < threshold and abs(new_pos[1] - pos[1]) < threshold:
                return True
        return False

    def get_active_text_block(self, context):
        if context.space_data.type == 'TEXT_EDITOR':
            return context.space_data.text
        return None

    def parse_ascii_for_channel_positions(self, ascii_data):
        channel_positions = []  # List to store channel numbers and their positions.
        channel_orientations = []  # List to store channel numbers and their orientations.

        current_channel = None
        current_position = None
        current_orientation = None

        for line in ascii_data.lines:
            trimmed_line = line.body.strip()

            if trimmed_line.startswith('$Patch'):
                parts = trimmed_line.split()
                if len(parts) >= 2:
                    current_channel = int(parts[1])

            elif trimmed_line.startswith('$$Position') and current_channel is not None:
                position_data = trimmed_line.split()[1:]
                try:
                    current_position = tuple(map(float, position_data))
                except ValueError:
                    current_position = None

            elif trimmed_line.startswith('$$Orientation') and current_channel is not None:
                orientation_data = trimmed_line.split()[1:]
                try:
                    current_orientation = tuple(map(float, orientation_data))
                except ValueError:
                    current_orientation = None

            if current_channel and current_position and current_orientation:
                channel_positions.append((current_channel, current_position))
                channel_orientations.append((current_channel, current_orientation))
                current_channel = None
                current_position = None
                current_orientation = None

        return channel_positions, channel_orientations

    def parse_groups_data(self, ascii_data):
        groups_data = {}

        current_group = None
        current_label = ""
        current_channels = []

        # Loop through each line in the ASCII data.
        for line in ascii_data.lines:
            trimmed_line = line.body.strip()

            # Check for the start of a new group.
            if trimmed_line.startswith('$Group'):
                # If there's an existing group, save it before starting a new one.
                if current_group is not None:
                    groups_data[str(current_group)] = {'label': current_label, 'channels': current_channels}
                # Reset for the new group.
                parts = trimmed_line.split()
                current_group = str(parts[1]) if len(parts) > 1 else None
                current_label = ""
                current_channels = []

            # Check for group label.
            elif trimmed_line.startswith('Text') and current_group is not None:
                label_parts = trimmed_line.split(maxsplit=1)
                current_label = label_parts[1].strip() if len(label_parts) > 1 else ""

            # Check for channel list.
            elif trimmed_line.startswith('$$ChanList') and current_group is not None:
                # Extend the current channel list with new values.
                channel_list_parts = trimmed_line.split()[1:]
                current_channels.extend(int(ch.strip()) for ch in channel_list_parts if ch.strip().isdigit())

        # Save the last group if the file ends after channel list.
        if current_group is not None:
            groups_data[str(current_group)] = {'label': current_label, 'channels': current_channels}

        return groups_data
    
    def parse_fixture_personalities(self, ascii_data):
        fixture_personalities = {}
        current_personality = None
        current_capabilities = set()

        for line in ascii_data.lines:
            trimmed_line = line.body.strip()

            if trimmed_line.startswith('$Personality'):
                if current_personality is not None:
                    fixture_personalities[current_personality] = current_capabilities
                parts = trimmed_line.split()
                current_personality = parts[1] if len(parts) > 1 else None
                current_capabilities = set()

            elif trimmed_line.startswith('$$PersChan') and current_personality is not None:
                parts = trimmed_line.split()
                parameter_id = parts[1]
        
                if parameter_id in ['204', '12', '2', '3', '1', '9', '10', '11', '76', '78', '79', '200', '73', '48', '51', '18241', '20675', 'Gobo', 'Zoom', 'Strobe', 'Pan', 'Tilt', 'Edge', 'Diffusion', 'Iris', 'Red']: 
                    current_capabilities.add(parameter_id)            

        if current_personality is not None:
            fixture_personalities[current_personality] = current_capabilities
        
        return fixture_personalities

    def parse_patch_data(self, ascii_data):
        channel_to_personality = {}  

        for line in ascii_data.lines: 
            line_content = line.body.strip() 
            if line_content.startswith('$Patch'):
                parts = line_content.split()  
                if len(parts) >= 3:
                    channel_number = int(parts[1])  
                    personality_code = int(parts[2]) 
                    channel_to_personality[channel_number] = personality_code

        return channel_to_personality
    
    '''EXECUTE'''
    def execute(self, context):
        scene = bpy.context.scene.scene_props

        # Get the name of the selected text block from the scene property.
        selected_text_block_name = scene.selected_text_block_name

        # Use the selected text block name to get the actual text block data.
        ascii_data = bpy.data.texts.get(selected_text_block_name)

        if ascii_data is None:
            self.report({'ERROR'}, "Selected text block not found.")
            return {'CANCELLED'}

        # Parse the ASCII file to find the group data and personalities.
        groups_data = self.parse_groups_data(ascii_data)
        scene.group_data = str(groups_data)

        fixture_personalities = self.parse_fixture_personalities(ascii_data)
        channel_to_personality = self.parse_patch_data(ascii_data)  # Parse patch data to get channel-to-personality mapping.

        # For each group, determine the capabilities of its fixtures based on the personalities assigned to each channel.
        group_capabilities = {}  # Key: Group number, Value: Set of capabilities.
        
        for group_number, group_info in groups_data.items():
            capabilities = set()

            for channel in group_info['channels']:
                # Use channel_to_personality mapping to find the personality code for the channel.
                personality_code = channel_to_personality.get(channel)
                
                if personality_code:
                    # Convert personality_code to string for lookup.
                    personality_code_str = str(personality_code)
                    # Use the personality code to find the capabilities.
                    capabilities.update(fixture_personalities.get(personality_code_str, set()))

            # Convert group_number to string before using it as a key.
            group_capabilities[group_number] = capabilities

        # Scale factor for node positioning based on ascii positions.
        scale_factor_x = 20
        scale_factor_y = 20
        
        # Grid parameters for when there is no ascii position data.
        grid_start_x = 0  
        grid_start_y = 0 
        grid_cell_width = 2  
        grid_cell_height = 2  
        grid_columns = 4  

        current_column = 0
        current_row = 0
        
        # This is the scale factor for ensuring a million nodes aren't squashed onto each other.
        position_threshold = 30  

        existing_positions = []
        
        # Go ahead and get the locations and orientations ready.
        channel_positions, channel_orientations = self.parse_ascii_for_channel_positions(ascii_data)
        
        # Create a controller for each imported group.
        for group_number, group_info in groups_data.items():
            tree = context.space_data.edit_tree
            new_controller = tree.nodes.new('group_controller_type')
            new_controller.str_selected_light = str(group_number)

            # Set capabilities based on group_capabilities.
            if group_number in group_capabilities:
                capabilities = group_capabilities[group_number]

                new_controller.strobe_is_on = 'Strobe' in capabilities or '204' in capabilities
                new_controller.color_is_on = 'Red' in capabilities or '12' in capabilities
                new_controller.pan_tilt_is_on = '2' in capabilities or '3' in capabilities
                new_controller.diffusion_is_on = 'Diffusion' in capabilities or '76' in capabilities
                new_controller.intensity_is_on = 'Intensity' in capabilities or '1' in capabilities
                new_controller.edge_is_on = 'Edge' in capabilities or '78' in capabilities
                new_controller.iris_is_on = 'Iris' in capabilities or '73' in capabilities
                new_controller.gobo_id_is_on = 'Gobo' in capabilities or '200' in capabilities
                new_controller.zoom_is_on = 'Zoom' in capabilities or '79' in capabilities                
                
                # Initialize flags.
                finished = False
                white_present = False

                # Check for Lime capability.
                if 'Lime' in capabilities or '20675' in capabilities:
                    new_controller.color_profile_enum = 'option_rgbl'
                    finished = True
                
                # If not finished, check for Lime capability.    
                elif '9' in capabilities or '10' in capabilities or '11' in capabilities:
                    new_controller.color_profile_enum = 'option_cmy'
                    finished = True

                # If not finished, check for Mint capability.
                elif 'Mint' in capabilities or '18241' in capabilities:
                    new_controller.color_profile_enum = 'option_rgbam'
                    finished = True

                # If not finished, check for White capability.
                elif 'White' in capabilities or '51' in capabilities:
                    new_controller.color_profile_enum = 'option_rgbw'
                    white_present = True  # Note that White is present, but do not finish yet.

                # If not finished and White is not present, check for Amber capability.
                if not finished and not white_present:
                    if 'Amber' in capabilities or '48' in capabilities:
                        new_controller.color_profile_enum = 'option_rgba'
                    else:
                        new_controller.color_profile_enum = 'option_rgb'  # Default to RGB if no Amber.
                
                if not finished:
                    # If White is present and Amber is also present, set to RGBAW.
                    if white_present and 'Amber' in capabilities or '48' in capabilities:
                        new_controller.color_profile_enum = 'option_rgbaw'
                   
                    
                new_controller.label = new_controller.str_group_label
                
#                # Set pan/tilt min and max if able.
#                if group_number in channel_pan_tilt_range:
#                    pan_range = channel_pan_tilt_range[group_number]['pan_range']
#                    tilt_range = channel_pan_tilt_range[group_number]['tilt_range']
#                    
#                    if pan_range != (None, None):
#                        new_controller.pan_min = pan_range[0]
#                        new_controller.pan_max = pan_range[1]
#                    
#                    if tilt_range != (None, None):
#                        new_controller.tilt_min = tilt_range[0]
#                        new_controller.tilt_max = tilt_range[1]
                
            # Calculate the average position of the channels in the group.
            channels = group_info.get('channels', [])
            positions = [pos for chan, pos in channel_positions if chan in channels]
            orientations = [orient for chan, orient in channel_orientations if chan in channels]

            if positions:
                avg_x = sum(pos[0] for pos in positions) / len(positions)
                avg_y = sum(pos[1] for pos in positions) / len(positions)
                new_pos = (avg_x * scale_factor_x, avg_y * scale_factor_y)
                
                # Check if the new position is too close to any existing position.
                while self.is_too_close(new_pos, existing_positions, position_threshold):
                    # Adjust the position slightly to avoid overlap.
                    new_pos = (new_pos[0] + position_threshold, new_pos[1])
                    
                new_controller.location = new_pos
                existing_positions.append(new_pos)

                # Use the orientation of the first light for the node, if available.
                if orientations:
                    first_orientation = orientations[0]
                    # Convert orientation from degrees to radians.
                    orientation_radians = tuple(math.radians(o) for o in first_orientation)
                    new_controller.rotation_euler = orientation_radians
            else:
                # Calculate grid position if it doesn't have ascii position info.
                grid_x = grid_start_x + (current_column * grid_cell_width)
                grid_y = grid_start_y - (current_row * grid_cell_height)  

                new_controller.location = (grid_x, grid_y)

                current_column += 1
                if current_column >= grid_columns:
                    current_column = 0
                    current_row += 1
            
            if tree:
                tree.update_tag()
                
            bpy.ops.node.view_selected()
        
        # Now, create, position, and orient Blender lights based on ascii data.
        for channel_number, position in channel_positions:
            bpy.ops.mesh.primitive_cone_add(location=position)
            light_object = bpy.context.active_object
            light_object.name = str(channel_number)

            # Find the orientation for the current channel.
            orientation = next((orient for chan, orient in channel_orientations if chan == channel_number), None)
            if orientation:
                # Add π radians (180 degrees) to the x-component to correct for the cone's upward facing direction.
                orientation_radians = (math.radians(orientation[0]) + math.pi, math.radians(orientation[1]), math.radians(orientation[2]))
                light_object.rotation_euler = orientation_radians
                
        if not channel_positions:
            self.report({'ERROR'}, "Position data not found.")
            return {'CANCELLED'}

        return {'FINISHED'}
    

#-----------------------------------------------------------------------------------------------------------------------------------------------------------
'''Keyframe buttons for pop-up channel controller'''
        
    
class KeyframeChannelIntensityOperator(bpy.types.Operator):
    bl_idname = "my.keyframe_channel_intensity_operator"
    bl_label = ""
    bl_description = "Keyframe"

    def execute(self, context):
        obj = context.object
        frame = context.scene.frame_current
        obj.keyframe_insert(data_path="float_intensity", frame=frame)
        
        return {'FINISHED'}
        
    
class KeyframeChannelColorOperator(bpy.types.Operator):
    bl_idname = "my.keyframe_channel_color_operator"
    bl_label = ""
    bl_description = "Keyframe"

    def execute(self, context):
        obj = context.object
        frame = context.scene.frame_current
        obj.keyframe_insert(data_path="float_vec_color", frame=frame)
        
        return {'FINISHED'}    
    
    
class KeyframeChannelSpeedOperator(bpy.types.Operator):
    bl_idname = "my.keyframe_channel_speed_operator"
    bl_label = ""
    bl_description = "Keyframe"

    def execute(self, context):
        obj = context.object
        frame = context.scene.frame_current
        obj.keyframe_insert(data_path="float_gobo_speed", frame=frame)
        
        return {'FINISHED'}    
    
    
class KeyframeChannelDiffusionOperator(bpy.types.Operator):
    bl_idname = "my.keyframe_channel_diffusion_operator"
    bl_label = ""
    bl_description = "Keyframe"

    def execute(self, context):
        obj = context.object
        frame = context.scene.frame_current
        obj.keyframe_insert(data_path="float_diffusion", frame=frame)
        
        return {'FINISHED'}
       
    
class KeyframeChannelIrisOperator(bpy.types.Operator):
    bl_idname = "my.keyframe_channel_iris_operator"
    bl_label = ""
    bl_description = "Keyframe"

    def execute(self, context):
        obj = context.object
        frame = context.scene.frame_current
        obj.keyframe_insert(data_path="float_iris", frame=frame)
        
        return {'FINISHED'}
        
    
class KeyframeChannelGoboOperator(bpy.types.Operator):
    bl_idname = "my.keyframe_channel_gobo_operator"
    bl_label = ""
    bl_description = "Keyframe"

    def execute(self, context):
        obj = context.object
        frame = context.scene.frame_current
        obj.keyframe_insert(data_path="int_gobo_id", frame=frame)
        
        return {'FINISHED'}
        
    
class KeyframeChannelZoomOperator(bpy.types.Operator):
    bl_idname = "my.keyframe_channel_zoom_operator"
    bl_label = ""
    bl_description = "Keyframe"

    def execute(self, context):
        obj = context.object
        frame = context.scene.frame_current
        obj.keyframe_insert(data_path="float_zoom", frame=frame)
        
        return {'FINISHED'}    
    
    
class KeyframeChannelEdgeOperator(bpy.types.Operator):
    bl_idname = "my.keyframe_channel_edge_operator"
    bl_label = ""
    bl_description = "Keyframe"

    def execute(self, context):
        obj = context.object
        frame = context.scene.frame_current
        obj.keyframe_insert(data_path="float_edge", frame=frame)
        
        return {'FINISHED'}
        
    
class KeyframeChannelPanOperator(bpy.types.Operator):
    bl_idname = "my.keyframe_channel_pan_operator"
    bl_label = ""
    bl_description = "Keyframe"

    def execute(self, context):
        obj = context.object
        frame = context.scene.frame_current
        obj.keyframe_insert(data_path="float_pan", frame=frame)
        
        return {'FINISHED'}    
    
    
class KeyframeChannelTiltOperator(bpy.types.Operator):
    bl_idname = "my.keyframe_channel_tilt_operator"
    bl_label = ""
    bl_description = "Keyframe"

    def execute(self, context):
        obj = context.object
        frame = context.scene.frame_current
        obj.keyframe_insert(data_path="float_tilt", frame=frame)
        
        return {'FINISHED'}


#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------  
'''Settings and renderer operators'''    
    
    
class DemocraticOperator(bpy.types.Operator):
    bl_idname = "my.democratic_operator"
    bl_label = ""
    bl_description = "This is a democracy. When different controllers try to change the same channel parameter, their Influence parameter gives them votes in a weighted average"

    def execute(self, context):
        if context.scene.scene_props.is_democratic:
            
            return {'FINISHED'}
        else:
            context.scene.scene_props.is_democratic = True
            context.scene.scene_props.is_not_democratic = False
            
        return {'FINISHED'}   
    
    
class NonDemocraticOperator(bpy.types.Operator):
    bl_idname = "my.non_democratic_operator"
    bl_label = ""
    bl_description = "This isn't a democracy anymore. When different controllers try to change the same channel parameter, the strongest completely erases everyone else's opinion"

    def execute(self, context):
        if context.scene.scene_props.is_not_democratic:
            return {'FINISHED'}
        else:
            context.scene.scene_props.is_not_democratic = True
            context.scene.scene_props.is_democratic = False
            
        return {'FINISHED'}
       
    
class BakeAnimationOperator(bpy.types.Operator):
    bl_idname = "my.bake_animation_operator"
    bl_label = ""
    bl_description = "This allows you to create qmeos on the lighting console, or lighting videos made up of moving cues, not moving pictures. Use the syntax templates to programmatically bake Sorcerer's animation data onto console cues to be fired from an event list"
  
    def frame_to_timecode(self, frame, fps=None):
        """Convert frame number to timecode format."""
        scene = bpy.context.scene
        context = bpy.context
        
        frame_rate = get_frame_rate(scene)
        start_frame = scene.frame_start
        end_frame = scene.frame_end 

        fps = frame_rate
        
        hours = int(frame // (fps * 3600))
        minutes = int((frame % (fps * 3600)) // (fps * 60))
        seconds = int((frame % (fps * 60)) // fps)
        frames = int(frame % fps)  # No rounding needed for non-drop frame.

        return "{:02}:{:02}:{:02}:{:02}".format(hours, minutes, seconds, frames)
      
    def execute(self, context):
        scene = bpy.context.scene
        
        frame_rate = get_frame_rate(scene)
        start_frame = scene.frame_start
        end_frame = scene.frame_end 
        
        scene.scene_props.is_baking = True
        scene.scene_props.str_bake_info = "Making a Qmeo! Escape to Cancel."
         
        ip_address = context.scene.scene_props.str_osc_ip_address
        port = context.scene.scene_props.int_osc_port
        current_frame_number = scene.frame_current
        cue_duration = 1 / frame_rate
        cue_duration = round(cue_duration, 2)
        
        address = scene.scene_props.str_command_line_address
        frames = list(range(start_frame, end_frame))

        cue_duration = round(1 / frame_rate, 2)
        
        percentage_remaining = 100 / len(frames)
        percentage_steps = percentage_remaining
        
        rounded_remaining = round(percentage_remaining)
        
        scene.scene_props.str_bake_info = "Making a Qmeo! Escape to Cancel. " + str(rounded_remaining) + "% Complete"
        
        # Create all events to help with organization.
        argument = scene.scene_props.str_create_all_events.replace("#", str(end_frame))

        send_osc_string(address, ip_address, port, argument)
        
        time.sleep(.3)

        message_list = []

        # Iterate through the frames and perform operations.
        for frame in frames:
            if frame == 0:
                continue 
            bpy.context.scene.frame_set(frame)
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
            
            current_frame_number = scene.frame_current
            
            # Record cue      
            cue_argument = scene.scene_props.str_record_cue.replace("#", str(current_frame_number))
            cue_argument = cue_argument.replace("$", str(cue_duration))
            
            timecode = self.frame_to_timecode(frame)
            
            event_argument = scene.scene_props.str_setup_event.replace("#", str(frame))
            event_argument = event_argument.replace("$", str(timecode))
            
            complete_argument = str(cue_argument) + ", " + str(event_argument)
            
            send_osc_string(address, ip_address, port, complete_argument)
            
            percentage_remaining += percentage_steps
            rounded_remaining = round(percentage_remaining)
            scene.scene_props.str_bake_info = "Making a Qmeo! Escape to Cancel. " + str(rounded_remaining) + "% Complete"
            time.sleep(.1)
        
        time.sleep(.5)
        
        snapshot = str(context.scene.orb_finish_snapshot)
        send_osc_string("/eos/newcmd", ip_address, port, f"Snapshot {snapshot} Enter")
            
        # Restore everything
        scene.scene_props.str_bake_info = "Create Qmeo"
        self.report({'INFO'}, "Orb complete.")
        scene.scene_props.is_baking = False
        
        return {'FINISHED'}
    

class JustCuesOperator(bpy.types.Operator):
    bl_idname = "my.just_cues_operator"
    bl_label = ""
    bl_description = "Use this to only re-record the cues without needing to recreate the event list"

    def execute(self, context):
        scene = bpy.context.scene
        
        scene.scene_props.is_cue_baking = True
        scene.scene_props.str_cue_bake_info = "Making a Qmeo! Escape to Cancel."
        
        frame_rate = get_frame_rate(scene)
        start_frame = scene.frame_start
        end_frame = scene.frame_end  
        ip_address = context.scene.scene_props.str_osc_ip_address
        port = context.scene.scene_props.int_osc_port
        current_frame_number = scene.frame_current
        cue_duration = 1 / frame_rate
        cue_duration = round(cue_duration, 2)
        
        address = scene.scene_props.str_command_line_address

        # Create a sorted list of frames.
        frames = list(range(start_frame, end_frame))
        
        cue_duration = round(1 / frame_rate, 2)
        
        percentage_remaining = 100 / len(frames)
        percentage_steps = percentage_remaining
        
        rounded_remaining = round(percentage_remaining)
        
        scene.scene_props.str_cue_bake_info = "Making a Qmeo! Escape to Cancel. " + str(rounded_remaining) + "% Complete"

        # Iterate through the frames and perform operations.
        for frame in frames:
            bpy.context.scene.frame_set(frame)
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
            
            current_frame_number = scene.frame_current
            
            # Record cue.
            argument = scene.scene_props.str_record_cue.replace("#", str(current_frame_number))
            argument = argument.replace("$", str(cue_duration))
            
            send_osc_string(address, ip_address, port, argument)
            
            percentage_remaining += percentage_steps
            rounded_remaining = round(percentage_remaining)
            scene.scene_props.str_cue_bake_info = "Making a Qmeo! Escape to Cancel. " + str(rounded_remaining) + "% Complete"
            time.sleep(.1)
            
        scene.scene_props.str_cue_bake_info = "Just Cues"
        scene.scene_props.is_cue_baking = False
        
        snapshot = str(context.scene.orb_finish_snapshot)
        send_osc_string("/eos/newcmd", ip_address, port, f"Snapshot {snapshot} Enter")
        
        self.report({'INFO'}, "Orb complete.")

        return {'FINISHED'}
    

class JustEventsOperator(bpy.types.Operator):
    bl_idname = "my.just_events_operator"
    bl_label = ""
    bl_description = "Use this to only re-record the cues without needing to recreate the event list"

    def frame_to_timecode(self, frame, fps=None):
        """Convert frame number to timecode format."""
        scene = bpy.context.scene
        context = bpy.context
        
        frame_rate = get_frame_rate(scene)
        start_frame = scene.frame_start
        end_frame = scene.frame_end 

        fps = frame_rate
        
        hours = int(frame // (fps * 3600))
        minutes = int((frame % (fps * 3600)) // (fps * 60))
        seconds = int((frame % (fps * 60)) // fps)
        frames = int(frame % fps)  # No rounding needed for non-drop frame.

        return "{:02}:{:02}:{:02}:{:02}".format(hours, minutes, seconds, frames)    
    
    def execute(self, context):
        scene = bpy.context.scene
        
        frame_rate = get_frame_rate(scene)
        start_frame = scene.frame_start
        end_frame = scene.frame_end 
        
        scene.scene_props.is_event_baking = True
        scene.scene_props.str_event_bake_info = "Making a Qmeo! Escape to Cancel."
         
        ip_address = context.scene.scene_props.str_osc_ip_address
        port = context.scene.scene_props.int_osc_port
        current_frame_number = scene.frame_current
        cue_duration = 1 / frame_rate
        cue_duration = round(cue_duration, 2)
        
        address = scene.scene_props.str_command_line_address

        # Create a sorted list of frames.
        frames = list(range(start_frame, end_frame))
        
        percentage_remaining = 100 / len(frames)
        percentage_steps = percentage_remaining
        
        rounded_remaining = round(percentage_remaining)
        
        scene.scene_props.str_event_bake_info = "Making a Qmeo! Escape to Cancel. " + str(rounded_remaining) + "% Complete"
              
        # Create all events to help with organization.
        argument = scene.scene_props.str_create_all_events.replace("#", str(end_frame))

        send_osc_string(address, ip_address, port, argument)
        time.sleep(.3)
            
        # Create all events to help with organization.
        argument = scene.scene_props.str_create_all_events.replace("#", str(end_frame))

        send_osc_string(address, ip_address, port, argument)
        time.sleep(.3)
        
        message_list = []
        
        # Set up all timecode events.
        for frame in frames:     
            if frame == 0:
                continue  
            
            current_frame_number = scene.frame_current
            
            timecode = self.frame_to_timecode(frame)
            
            argument = scene.scene_props.str_setup_event.replace("#", str(frame))
            argument = argument.replace("$", str(timecode))
    
            message_list.append(argument)
            
        str_arguments = ""
        counter = 0
        
        for message in message_list:
            
            if counter != 0:
                str_arguments += ", "
            str_arguments += message
            counter += 1
            
            # Fails between 130 and 150. Setting to 75 for now in case other consoles have far longer syntax.
            if counter == 75:
                bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
                send_osc_string(address, ip_address, port, str_arguments)
                time.sleep(.1)
                str_arguments = ""
              
                counter = 0

        if str_arguments:
            send_osc_string(address, ip_address, port, str_arguments)
            
        scene.scene_props.str_event_bake_info = "Just Events"
        
        scene.scene_props.is_event_baking = False
        
        snapshot = str(context.scene.orb_finish_snapshot)
        send_osc_string("/eos/newcmd", ip_address, port, f"Snapshot {snapshot} Enter")
        
        self.report({'INFO'}, "Orb complete.")

        return {'FINISHED'}
       
    
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------    
'''Other node operators'''    
    
        
class AddCustomButton(bpy.types.Operator):
    bl_idname = "node.add_custom_button"
    bl_label = "Add Custom Button"

    def execute(self, context):
        node = context.node
        node.custom_buttons.add()
        
        return {'FINISHED'}    
    

class RemoveCustomButton(bpy.types.Operator):
    bl_idname = "node.remove_custom_button"
    bl_label = "Remove Custom Button"

    button_index: bpy.props.IntProperty()

    def execute(self, context):
        node = context.node

        if node.custom_buttons and 0 <= self.button_index < len(node.custom_buttons):
            node.custom_buttons.remove(self.button_index)
        else:
            self.report({'WARNING'}, "Invalid button index or no buttons to remove.")
            
        return {'FINISHED'}  
    
    
class BumpUpCustomButton(bpy.types.Operator):
    bl_idname = "node.bump_up_custom_button"
    bl_label = "Move Button Up"

    button_index: bpy.props.IntProperty()

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

    button_index: bpy.props.IntProperty()

    def execute(self, context):
        node = context.node

        if 0 <= self.button_index < len(node.custom_buttons) - 1:
            node.custom_buttons.move(self.button_index, self.button_index + 1)
        else:
            self.report({'WARNING'}, "Cannot move the last button down or invalid index.")

        return {'FINISHED'}
        
    
class HomeGroupButton(bpy.types.Operator):
    bl_idname = "node.home_group"
    bl_label = "Home Group"

    node_name: bpy.props.StringProperty()

    def execute(self, context):
        node_tree = context.scene.world.node_tree

        if context.space_data.path:
            group_node = context.space_data.path[-1].node_tree
            if group_node:
                node_tree = group_node

        node = node_tree.nodes.get(self.node_name)
        
        if node and (node.bl_idname == 'group_controller_type' or node.bl_idname == 'group_driver_type' or node.bl_idname == 'master_type'):
            node.float_intensity = 0
            if node.strobe_is_on:
                node.float_strobe = 0
            if node.color_is_on:
                node.float_vec_color = (1, 1, 1)
            if node.pan_tilt_is_on:
                node.float_pan = 0
                node.float_tilt = 0
            if node.zoom_is_on:
                node.float_zoom = 0
            if node.iris_is_on:
                node.float_iris = 100
            if node.edge_is_on:
                node.float_edge = 0
            if node.diffusion_is_on:
                node.float_diffusion = 0
            if node.gobo_id_is_on:
                node.int_gobo_id = 1
                node.float_gobo_speed = 0
                node.int_prism = 0
        elif node.bl_idname == 'mixer_type' or node.bl_idname == 'mixer_driver_type':
            if node.parameters_enum == 'option_intensity':
                node.float_intensity_one_checker = .05
                node.float_intensity_one = 0
            elif node.parameters_enum == 'option_color':
                node.float_vec_color_one_checker = (.05, .05, .05)
                node.float_vec_color_one = (1, 1, 1)
                node.float_vec_color_two_checker = (.05, .05, .05)
                node.float_vec_color_two = (1, 1, 1)
                node.float_vec_color_three_checker = (.05, .05, .05)
                node.float_vec_color_three = (1, 1, 1)
            elif node.parameters_enum == 'option_pan_tilt':
                node.float_pan_one_checker = .05
                node.float_pan_one = 0
            else: sorcerer_assert_unreachable()
        else: sorcerer_assert_unreachable()
                        
        return {'FINISHED'}
        
    
class HomeChannelButton(bpy.types.Operator):
    bl_idname = "node.home_channel"
    bl_label = "Home Channel"

    node_name: bpy.props.StringProperty()

    def execute(self, context):
        node = context.node
        button = node.custom_buttons[self.button_index]

        scene = context.scene.scene_props
        
        ip_address = scene.str_osc_ip_address
        port = scene.int_osc_port
        address = button.button_address
        argument = button.button_argument
        
        send_osc_string(address, ip_address, port, argument)

        return {'FINISHED'}   
    
    
class UpdateGroupButton(bpy.types.Operator):
    bl_idname = "node.update_group"
    bl_label = "Update Group"

    node_name: bpy.props.StringProperty()

    def execute(self, context):
        node_tree = context.scene.world.node_tree

        if context.space_data.path:
            group_node = context.space_data.path[-1].node_tree
            if group_node:
                node_tree = group_node

        node = node_tree.nodes.get(self.node_name)
        
        if node and (node.bl_idname == 'group_controller_type' or node.bl_idname == 'group_driver_type' or node.bl_idname == 'master_type'):
            node.float_intensity_checker = .05
            print(node.float_intensity_checker)
            node.float_intensity = node.float_intensity
            if node.strobe_is_on:
                node.float_strobe_checker = .05
                node.float_strobe = node.float_strobe
            if node.color_is_on:
                node.float_vec_color_checker = (.05, .05, .05)
                node.float_vec_color = node.float_vec_color
            if node.pan_tilt_is_on:
                node.float_pan_checker = -500
                node.float_pan = node.float_pan
                node.float_tilt_checker = -500
                node.float_tilt = node.float_tilt
            if node.zoom_is_on:
                node.float_zoom_checker = .05
                node.float_zoom = node.float_zoom
            if node.iris_is_on:
                node.float_iris_checker = .05
                node.float_iris = node.float_iris
            if node.edge_is_on:
                node.float_edge_checker = .05
                node.float_edge = node.float_edge
            if node.diffusion_is_on:
                node.float_diffusion_checker = .05
                node.float_diffusion = node.float_diffusion
            if node.gobo_id_is_on:
                node.gobo_id_checker = 30
                node.int_gobo_id = node.int_gobo_id
                node.float_speed_checker = -1000
                node.float_gobo_speed = node.float_gobo_speed
                node.int_prism_checker = 2
                node.int_prism = node.int_prism
        elif node.bl_idname == 'mixer_type' or node.bl_idname == 'mixer_driver_type':
            if node.parameters_enum == 'option_intensity':
                node.float_intensity_one_checker = .05
                node.float_intensity_one = node.float_intensity_one
            elif node.parameters_enum == 'option_color':
                node.float_vec_color_one_checker = (.05, .05, .05)
                node.float_vec_color_one = node.float_vec_color_one
            elif node.parameters_enum == 'option_pan_tilt':
                node.float_vec_color_one_checker = (.05, .05, .05)
                node.float_vec_color_one = node.float_vec_color_one
            else: sorcerer_assert_unreachable()
        else: sorcerer_assert_unreachable()
                
        return {'FINISHED'}
       
    
class UpdateChannelButton(bpy.types.Operator):
    bl_idname = "node.update_channel"
    bl_label = "Update Channel"

    node_name: bpy.props.StringProperty()

    def execute(self, context):
        node = context.node
        button = node.custom_buttons[self.button_index]

        scene = context.scene.scene_props
        
        ip_address = scene. str_osc_ip_address
        port = scene.int_osc_port
        address = button.button_address
        argument = button.button_argument
        
        send_osc_string(address, ip_address, port, argument)

        return {'FINISHED'}
    
    
class AddConsoleButtonsNode(bpy.types.Operator):
    bl_idname = "node.add_console_buttons_node"
    bl_label = "Add Console Buttons"
    bl_description="Adjust all intensities of group controller nodes on this level"

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('console_buttons_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'} 
          
        
class AddOvenNode(bpy.types.Operator):
    bl_idname = "node.add_oven_node"
    bl_label = "Add Oven"
    bl_description="Create qmeos to store complex animation data directly on the console. Qmeos are like videos, but each frame is a lighting cue"

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('oven_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
        
    
class AddSettingsNode(bpy.types.Operator):
    bl_idname = "node.add_settings_node"
    bl_label = "Add Settings"
    bl_description="Sorcerer node settings"

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('settings_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
        
    
class AddIntensitiesNode(bpy.types.Operator):
    bl_idname = "node.add_intensities_node"
    bl_label = "Add Intensities"
    bl_description="Adjust all intensities of group controller nodes on this level"

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('intensities_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        self.execute(context)
        bpy.ops.node.translate_attach_remove_on_cancel('INVOKE_DEFAULT', node='NEW')
        return {'FINISHED'}
        
    
class AddPresetsNode(bpy.types.Operator):
    bl_idname = "node.add_presets_node"
    bl_label = "Add Presets"
    bl_description="Record and recall console presets"

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('presets_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
        
    
class AddColorsNode(bpy.types.Operator):
    bl_idname = "node.add_colors_node"
    bl_label = "Add Colors"
    bl_description="Adjust all colors of group controller nodes on this level"

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('colors_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
    
    
class AddStrobesNode(bpy.types.Operator):
    bl_idname = "node.add_strobes_node"
    bl_label = "Add Strobes"
    bl_description="Adjust all strobes of group controller nodes on this level"

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('strobes_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
        
    
class AddZoomsNode(bpy.types.Operator):
    bl_idname = "node.add_zooms_node"
    bl_label = "Add Zooms"
    bl_description="Adjust all zooms of group controller nodes on this level"

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('zooms_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}    
    
    
class AddEdgesNode(bpy.types.Operator):
    bl_idname = "node.add_edges_node"
    bl_label = "Add Edges"
    bl_description="Adjust all edges of group controller nodes on this level"

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('edges_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
    
        
class AddPanTiltNode(bpy.types.Operator):
    bl_idname = "node.add_pan_tilt_node"
    bl_label = "Add Pan/Tilt controller for FOH-hung mover"
    bl_description="Intuitive pan/tilt controller only for FOH, forward-facing fixtures"

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('pan_tilt_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}    
    

class AddGroupControllerNode(bpy.types.Operator):
    bl_idname = "node.add_group_controller_node"
    bl_label = "Control a group defined in Properties"
    bl_description="Control a group defined in Properties"

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('group_controller_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
        

class AddMixerNode(bpy.types.Operator):
    bl_idname = "node.add_mixer_node"
    bl_label = "Mix 3 different parameter choices across a group"
    bl_description="Mix 3 different parameter choices accross a group"

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('mixer_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
    
    
class AddMixerDriverNode(bpy.types.Operator):
    bl_idname = "node.add_mixer_driver_node"
    bl_label = "Mix 3 different parameter choices across multiple groups"
    bl_description="Mix 3 different parameter choices across multiple groups"

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('mixer_driver_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
    
    
class AddMasterNode(bpy.types.Operator):
    bl_idname = "node.add_master_node"
    bl_label = "Commandeer collapsed Node Groups"
    bl_description="Commandeer collapsed Node Groups"

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('master_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
    
    
class AddGroupDriverNode(bpy.types.Operator):
    bl_idname = "node.add_group_driver_node"
    bl_label = "Control multiple groups at once"
    bl_description="Control multiple groups at once"

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('group_driver_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
    

class AddFlashNode(bpy.types.Operator):
    bl_idname = "node.add_flash_node"
    bl_label = "Connect to flash strips in the sequencer"
    bl_description="Autofill the Flash Up and Flash Down fields of flash strips in Sequencer with node settings and noodle links. Intended primarily for pose-based choreography"

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('flash_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
    
    
class KeyframeStrobePopupOperator(bpy.types.Operator):
    bl_idname = "popup.keyframe_strobe_popup_operator"
    bl_label = "Keyframe Strobe"
    bl_description = "Keyframe the strobe property of a node"

    node_name: bpy.props.StringProperty()

    def execute(self, context):
        world = context.scene.world
        if world and world.node_tree:
            node = world.node_tree.nodes.get(self.node_name)
            if node:
                frame = context.scene.frame_current
                node.keyframe_insert(data_path="float_strobe", frame=frame)
                print(self.node_name)
                return {'FINISHED'}
            else:
                self.report({'WARNING'}, "Node not found.")
                return {'CANCELLED'}
        else:
            self.report({'WARNING'}, "World or node tree not found.")
            
            return {'CANCELLED'}
        
    
class ViewStrobeProps(bpy.types.Operator):
    bl_idname = "my.view_strobe_props"
    bl_label = "View Strobe Properties"
    
    node_name: bpy.props.StringProperty()  
    
    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        node = None
        world = context.scene.world
        if world and world.node_tree:
            node = world.node_tree.nodes.get(self.node_name)
        if node:
            return context.window_manager.invoke_props_dialog(self, width=400)
        else:
            self.report({'WARNING'}, "Node not found.")
            
            return {'CANCELLED'}

    def draw(self, context):
        layout = self.layout
        column = layout.row()
        world = context.scene.world
        
        if world and world.node_tree:
            node = world.node_tree.nodes.get(self.node_name)
            if node:
                split = layout.split(factor=.5)
                row = split.column()
                row.label(text="Strobe Value", icon='OUTLINER_DATA_LIGHTPROBE')
                row = split.column()
                row.prop(node, "float_strobe", text="",slider=True)
                op = row.operator("popup.keyframe_strobe_popup_operator", text="Keyframe", icon='KEYTYPE_KEYFRAME_VEC')
                op.node_name = self.node_name
                
                layout.separator()
                
                if hasattr(node, "str_enable_strobe_argument"):
                    split = layout.split(factor=.5)
                    row = split.column()
                    row.label(text="Enable Strobe Argument")
                    row = split.column()
                    row.prop(node, "str_enable_strobe_argument", text="", icon='OUTLINER_DATA_LIGHTPROBE')
                    
                    split = layout.split(factor=.5)
                    row = split.column()
                    row.label(text="Disable Strobe Argument")
                    row = split.column()
                    row.prop(node, "str_disable_strobe_argument", text="", icon='PANEL_CLOSE')


class ViewPanTiltProps(bpy.types.Operator):
    bl_idname = "my.view_pan_tilt_props"
    bl_label = "Pan/Tilt Properties"
    bl_description = "Access pan and tilt min and max settings"

    node_name: bpy.props.StringProperty()

    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        node = None
        world = context.scene.world
        if world and world.node_tree:
            node = world.node_tree.nodes.get(self.node_name)
        if node:
            return context.window_manager.invoke_props_dialog(self, width=200)
        else:
            self.report({'WARNING'}, "Node not found.")
            return {'CANCELLED'}

    def draw(self, context):
        layout = self.layout
        column = layout.row()
        row = layout.row(align=True)
        world = context.scene.world
        
        if not context.scene.scene_props.school_mode_enabled:
            if world and world.node_tree:
                node = world.node_tree.nodes.get(self.node_name)
                if node:
                    row.prop(node, "pan_min", text="Pan Min:")
                    row.prop(node, "pan_max", text="Max:")
                    
                    row = layout.row(align=True)
                    
                    row.prop(node, "tilt_min", text="Tilt Min:")
                    row.prop(node, "tilt_max", text="Max:")
                else:
                    layout.label(text="Node not found.")
                    
        else:
            row.label(text="Unauthorized request.")
       
    
class ViewZoomIrisProps(bpy.types.Operator):
    bl_idname = "my.view_zoom_iris_props"
    bl_label = "Zoom Properties"
    bl_description = "Access zoom min and max settings"

    node_name: bpy.props.StringProperty()

    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        node = None
        world = context.scene.world
        if world and world.node_tree:
            node = world.node_tree.nodes.get(self.node_name)
        if node:
            return context.window_manager.invoke_props_dialog(self, width=200)
        else:
            self.report({'WARNING'}, "Node not found.")
            return {'CANCELLED'}

    def draw(self, context):
        layout = self.layout
        column = layout.row()
        row = layout.row(align=True)
        world = context.scene.world
        
        if not context.scene.scene_props.school_mode_enabled:
        
            if world and world.node_tree:
                node = world.node_tree.nodes.get(self.node_name)
                if node:
                    row.prop(node, "zoom_min", text="Zoom Min:")
                    row.prop(node, "zoom_max", text="Max:")

                else:
                    layout.label(text="Node not found.")
                    
        else:
            row.label(text="Unauthorized request.")
        

class ViewEdgeDiffusionProps(bpy.types.Operator):
    bl_idname = "my.view_edge_diffusion_props"
    bl_label = "Edge/Diffusion Properties"

    node_name: bpy.props.StringProperty()

    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        node = None
        world = context.scene.world
        if world and world.node_tree:
            node = world.node_tree.nodes.get(self.node_name)
        if node:
            return context.window_manager.invoke_props_dialog(self, width=200)
        else:
            self.report({'WARNING'}, "Node not found.")
            return {'CANCELLED'}

    def draw(self, context):
        layout = self.layout
        column = layout.row()
        row = layout.row(align=True)
        world = context.scene.world
        
        if world and world.node_tree:
            node = world.node_tree.nodes.get(self.node_name)
            if node:
                row.label(text="Nothing to adjust here.")
            else:
                layout.label(text="Node not found.")
    
       
class ViewGoboProps(bpy.types.Operator):
    bl_idname = "my.view_gobo_props"
    bl_label = "View Gobo Properties"
    bl_description = "Access gobo-related settings"

    node_name: bpy.props.StringProperty()

    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        node = None
        world = context.scene.world
        if world and world.node_tree:
            node = world.node_tree.nodes.get(self.node_name)
        if node:
            return context.window_manager.invoke_props_dialog(self, width=400)
        else:
            self.report({'WARNING'}, "Node not found.")
            return {'CANCELLED'}

    def draw(self, context):
        layout = self.layout
        column = layout.row()
        world = context.scene.world
        
        if not context.scene.scene_props.school_mode_enabled:
        
            if world and world.node_tree:
                node = world.node_tree.nodes.get(self.node_name)
                if node:
                    split = layout.split(factor=.5)
                    row = split.column()
                    row.label(text="Gobo ID Argument")
                    row = split.column()
                    row.prop(node, "str_gobo_id_argument", text="", icon='POINTCLOUD_DATA')
                    
                    layout.separator()
                    
                    split = layout.split(factor=.5)
                    row = split.column()
                    row.label(text="Gobo Speed Value Argument")
                    row = split.column()
                    row.prop(node, "str_gobo_speed_value_argument", text="", icon='CON_ROTLIKE')
                    split = layout.split(factor=.5)
                    row = split.column()
                    row.label(text="Enable Gobo Speed Argument")
                    row = split.column()
                    row.prop(node, "str_enable_gobo_speed_argument", text="", icon='CHECKBOX_HLT')
                    split_two = layout.split(factor=.51, align=True)
                    row_two = split_two.column()
                    row_two.label(text="")
                    row_two = split_two.column(align=True)
                    row_two.prop(node, "speed_min", text="Min")
                    row_two = split_two.column(align=True)
                    row_two.prop(node, "speed_max", text="Max")
                    
                    split = layout.split(factor=.5)
                    row = split.column()
                    row.label(text="Disable Gobo Speed Argument")
                    row = split.column()
                    row.prop(node, "str_disable_gobo_speed_argument", text="", icon='CHECKBOX_DEHLT')
                    
                    layout.separator()
                    
                    split = layout.split(factor=.5)
                    row = split.column()
                    row.label(text="Enable Prism Argument")
                    row = split.column()
                    row.prop(node, "str_enable_prism_argument", text="", icon='TRIA_UP')
                    
                    split = layout.split(factor=.5)
                    row = split.column()
                    row.label(text="Disable Prism Argument")
                    row = split.column()
                    row.prop(node, "str_disable_prism_argument", text="", icon='PANEL_CLOSE')
                    
                else:
                    layout.label(text="Node not found.")
                    
        else:
            row = column.row()
            row.label(text="Unauthorized request.")
        
    
class CustomButton(bpy.types.Operator):
    bl_idname = "node.custom_button"
    bl_label = "Custom Button"

    button_index: bpy.props.IntProperty()

    def execute(self, context):
        node = context.node
        button = node.custom_buttons[self.button_index]

        scene = context.scene
        
        ip_address = scene.scene_props.str_osc_ip_address
        port = scene.scene_props.int_osc_port
        address = button.button_address
        argument = button.button_argument
        
        send_osc_string(address, ip_address, port, argument)

        return {'FINISHED'}
    
    
class RecordEffectPresetOperator(bpy.types.Operator):
    bl_idname = "node.record_effect_preset_operator"
    bl_label = "Record"
    bl_description = "Orb will record the node's group into the preset above onto the console using the argument template below"

    node_tree_name: bpy.props.StringProperty()  # Property to hold the node tree name
    node_name: bpy.props.StringProperty()  # Property to hold the node name

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
            groups_list = []
            for input_socket in active_node.inputs:
                if input_socket.bl_idname == 'FlashUpType':
                    for link in input_socket.links:
                        connected_node = link.from_socket.node
                        if connected_node.bl_idname == "group_controller_type":
                            groups_list.append(connected_node.str_selected_light)
                        elif connected_node.bl_idname == "group_driver_type":
                            for output_socket in connected_node.outputs:
                                if output_socket.bl_idname == 'GroupOutputType':
                                    for link in output_socket.links:
                                        driven_node = link.to_socket.node
                                        if driven_node.bl_idname == "group_controller_type":
                                            groups_list.append(driven_node.str_selected_light)
                        elif connected_node.bl_idname == "mixer_type":
                            down_groups_list.append(connected_node.str_selected_light)               
                        elif connected_node.bl_idname == "mixer_driver_type":
                            for output_socket in connected_node.outputs:
                                if output_socket.bl_idname == 'MixerOutputType':
                                    for link in output_socket.links:
                                        driven_node = link.to_socket.node
                                        if driven_node.bl_idname == "mixer_type":
                                            groups_list.append(driven_node.str_selected_group)
                        elif connected_node.bl_idname == 'ShaderNodeGroup':
                            group_node_tree = connected_node.node_tree
                            for node in group_node_tree.nodes:
                                if node.type == 'GROUP_OUTPUT':
                                    for socket in node.inputs:
                                        if socket.name == "Flash":
                                            for inner_link in socket.links:
                                                interior_connected_node = inner_link.from_node
                                                if interior_connected_node.bl_idname == 'group_controller_type':
                                                    groups_list.append(interior_connected_node.str_selected_light)
                                                elif interior_connected_node.bl_idname == "group_driver_type":
                                                    for output_socket in interior_connected_node.outputs:
                                                        if output_socket.bl_idname == 'GroupOutputType':
                                                            for link in output_socket.links:
                                                                driven_node = link.to_socket.node
                                                                if driven_node.bl_idname == "group_controller_type":
                                                                    groups_list.append(driven_node.str_selected_light)
                                                    
        scene = context.scene
        node = context.active_node
        group_numbers = ' + Group '.join(groups_list)
        preset_number = active_node.int_up_preset_assignment
        argument_template = scene.scene_props.str_preset_assignment_argument
          
        argument = argument_template.replace("#", str(group_numbers))
        argument = argument.replace("$", str(preset_number))
        ip_address = scene.scene_props.str_osc_ip_address
        port = scene.scene_props.int_osc_port
        address = scene.scene_props.str_command_line_address
          
        send_osc_string(address, ip_address, port, argument)
          
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
        send_osc_string("/eos/newcmd", ip_address, port, f"Snapshot {snapshot} Enter")
                          
        return {'FINISHED'}
    
    
class RecordDownEffectPresetOperator(bpy.types.Operator):
    bl_idname = "node.record_down_effect_preset_operator"
    bl_label = "Record"
    bl_description = "Orb will record the node's group into the preset above onto the console using the argument template below"

    node_tree_name: bpy.props.StringProperty()  # Property to hold the node tree name
    node_name: bpy.props.StringProperty()  # Property to hold the node name

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
            groups_list = []
            for input_socket in active_node.inputs:
                if input_socket.bl_idname == 'FlashDownType':
                    for link in input_socket.links:
                        connected_node = link.from_socket.node
                        if connected_node.bl_idname == "group_controller_type":
                            groups_list.append(connected_node.str_selected_light)
                        elif connected_node.bl_idname == "group_driver_type":
                            for output_socket in connected_node.outputs:
                                if output_socket.bl_idname == 'GroupOutputType':
                                    for link in output_socket.links:
                                        driven_node = link.to_socket.node
                                        if driven_node.bl_idname == "group_controller_type":
                                            groups_list.append(driven_node.str_selected_light)
                        elif connected_node.bl_idname == "mixer_type":
                            down_groups_list.append(connected_node.str_selected_light)               
                        elif connected_node.bl_idname == "mixer_driver_type":
                            for output_socket in connected_node.outputs:
                                if output_socket.bl_idname == 'MixerOutputType':
                                    for link in output_socket.links:
                                        driven_node = link.to_socket.node
                                        if driven_node.bl_idname == "mixer_type":
                                            groups_list.append(driven_node.str_selected_group)
                        elif connected_node.bl_idname == 'ShaderNodeGroup':
                            group_node_tree = connected_node.node_tree
                            for node in group_node_tree.nodes:
                                if node.type == 'GROUP_OUTPUT':
                                    for socket in node.inputs:
                                        if socket.name == "Flash":
                                            for inner_link in socket.links:
                                                interior_connected_node = inner_link.from_node
                                                if interior_connected_node.bl_idname == 'group_controller_type':
                                                    groups_list.append(interior_connected_node.str_selected_light)
                                                elif interior_connected_node.bl_idname == "group_driver_type":
                                                    for output_socket in interior_connected_node.outputs:
                                                        if output_socket.bl_idname == 'GroupOutputType':
                                                            for link in output_socket.links:
                                                                driven_node = link.to_socket.node
                                                                if driven_node.bl_idname == "group_controller_type":
                                                                    groups_list.append(driven_node.str_selected_light)
                                                    
        scene = context.scene
        node = context.active_node
        group_numbers = ' + Group '.join(groups_list)
        preset_number = active_node.int_down_preset_assignment
        argument_template = scene.scene_props.str_preset_assignment_argument
          
        argument = argument_template.replace("#", str(group_numbers))
        argument = argument.replace("$", str(preset_number))
        ip_address = scene.scene_props.str_osc_ip_address
        port = scene.scene_props.int_osc_port
        address = scene.scene_props.str_command_line_address
          
        send_osc_string(address, ip_address, port, argument)
          
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
        send_osc_string("/eos/newcmd", ip_address, port, f"Snapshot {snapshot} Enter")
                          
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
    bl_label = ""
    bl_description = "Search for unused preset. Warning: does not poll the console."

    node_name: StringProperty(default="")
    node_group_name: StringProperty(default="")

    def execute(self, context):
        used_presets = set()

        for node_tree in bpy.data.node_groups:
            if node_tree.bl_idname == 'AlvaNodeTree' or node_tree.bl_idname == 'ShaderNodeTree':
                for node in node_tree.nodes:
                    if node.bl_idname == "flash_type":
                        used_presets.add(node.int_up_preset_assignment)
                        used_presets.add(node.int_down_preset_assignment)
        for world in bpy.data.worlds:
            if world.use_nodes:
                for node in world.node_tree.nodes:
                    if node.bl_idname == "flash_type":
                        used_presets.add(node.int_up_preset_assignment)
                        used_presets.add(node.int_down_preset_assignment)
                        
        result_one = 1
        result_two = 2 

        while result_one in used_presets or result_two in used_presets:
            result_one += 1
            result_two = result_one + 1

        active_node = find_node_by_name(self.node_name)
        
        if active_node and active_node.bl_idname == "flash_type":
            active_node.int_up_preset_assignment = result_one
            active_node.int_down_preset_assignment = result_two
        else:
            print(active_node)
            self.report({'WARNING'}, "Active node is not a valid 'flash_type' node.")

        return {'FINISHED'}
    
    
classes = (
    PatchGroupOperator,
    AddChannelToGroupOperator,
    RemoveChannelFromGroupOperator,
    RemoveGroupOperator,
    AddGroupToSceneOperator,
    ColorOne,
    ColorTwo,
    ColorThree,
    ColorFour,
    ColorFive,
    ColorSix,
    ColorSeven,
    ColorEight,
    ColorNine,
    ColorTen,
    ColorEleven,
    ColorTwelve,
    ColorThirteen,
    ColorFourteen,
    ColorFifteen,
    FOne,
    FTwo,
    FThree,
    FFour,
    FFive,
    FSix,
    FSeven,
    FEight,
    FNine,
    FTen,
    FEleven,
    FTwelve,
    SendUSITTASCIITo3DOperator,
    KeyframeChannelIntensityOperator,
    KeyframeChannelSpeedOperator,
    KeyframeChannelDiffusionOperator,
    KeyframeChannelIrisOperator,
    KeyframeChannelGoboOperator,
    KeyframeChannelZoomOperator,
    KeyframeChannelEdgeOperator,
    KeyframeChannelPanOperator,
    KeyframeChannelColorOperator,
    KeyframeChannelTiltOperator,
    DemocraticOperator,
    NonDemocraticOperator,
    BakeAnimationOperator,
    JustCuesOperator,
    JustEventsOperator,
    RemoveCustomButton,
    AddConsoleButtonsNode,
    CustomButton,
    BumpUpCustomButton,
    BumpDownCustomButton,
    AddCustomButton,
    HomeGroupButton,
    HomeChannelButton,
    UpdateGroupButton,
    UpdateChannelButton,
    AddOvenNode,
    AddSettingsNode,
    AddIntensitiesNode,
    AddPresetsNode,
    AddColorsNode,
    AddStrobesNode,
    AddZoomsNode,
    AddEdgesNode,
    AddPanTiltNode,
    AddMixerNode,
    AddMixerDriverNode,
    AddGroupDriverNode,
    AddMasterNode,
    AddGroupControllerNode,
    AddFlashNode,
    KeyframeStrobePopupOperator,
    ViewStrobeProps,
    ViewPanTiltProps,
    ViewZoomIrisProps,
    ViewEdgeDiffusionProps,
    ViewGoboProps,
    RecordEffectPresetOperator,
    RecordDownEffectPresetOperator,
    FlashPresetSearchOperator,
)


def register():
    
    for cls in classes:
        bpy.utils.register_class(cls)
            
        
def unregister():

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
               

# For development purposes only. 
if __name__ == "__main__":
    register()
