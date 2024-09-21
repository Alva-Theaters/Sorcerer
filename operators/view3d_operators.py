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
import time
import math
from bpy.props import *
from bpy.types import Operator

# pyright: reportInvalidTypeForm=false

from ..cpvia.find import Find 
from ..utils.utils import Utils 
from ..utils.osc import OSC


def apply_patch(item, object):
    properties = [
        "pan_min", "pan_max", "tilt_min", "tilt_max", "zoom_min", "zoom_max", 
        "gobo_speed_min", "gobo_speed_max", "influence_is_on", "intensity_is_on", 
        "pan_tilt_is_on", "color_is_on", "diffusion_is_on", "strobe_is_on", 
        "zoom_is_on", "iris_is_on", "edge_is_on", "gobo_is_on", "prism_is_on", 
        "str_enable_strobe_argument", "str_disable_strobe_argument", 
        "str_enable_gobo_speed_argument", "str_disable_gobo_speed_argument", 
        "str_gobo_id_argument", "str_gobo_speed_value_argument", 
        "str_enable_prism_argument", "str_disable_prism_argument", "color_profile_enum"
    ]

    for prop in properties:
        setattr(object, prop, getattr(item, prop))


#-------------------------------------------------------------------------------------------------------------------------------------------
'''Begin operators section'''
    

class AddChannelToGroupOperator(bpy.types.Operator):
    bl_idname = "patch.add_channel"
    bl_label = "Add Channels"
    bl_description = "Add channel to group"
    
    group_id: StringProperty() 
    
    def execute(self, context):
        # The best part is no part.
        # This is just an automatic updater now. 1 less step for user.
        return {'FINISHED'}
    
    
class ApplyPatchToObjectsOperator(bpy.types.Operator):
    '''Apply to selected objects'''
    bl_idname = "alva_common.patch_to_selected"
    bl_label = "Apply Settings"
    
    group_id: StringProperty()
    
    def execute(self, context):
        item = context.scene.scene_group_data.get(self.group_id)  # Get the object by name
        if item is None:
            self.report({'ERROR'}, "Group not found")
            return {'CANCELLED'}
        
        for obj in context.selected_objects:
            try:
                apply_patch(item, obj)
            except: pass
          
        return {'FINISHED'}
    
    
class RemoveChannelFromGroupOperator(bpy.types.Operator):
    bl_idname = "alva_common.remove_or_highlight_channel"
    bl_label = "Highlight or Remove"
    bl_description = "Highlight or remove channel, depending on selection below"
    
    group_id: StringProperty()
    channel: IntProperty()
    
    def execute(self, context):
        item = context.scene.scene_group_data.get(self.group_id)
        if item is None:
            self.report({'ERROR'}, "Group not found")
            return {'CANCELLED'}
        
        if item.highlight_or_remove_enum == 'option_remove':
            index_to_remove = -1
            for idx, channel in enumerate(item.channels_list):
                if channel.chan == self.channel:
                    index_to_remove = idx
                    break
            
            if index_to_remove != -1:
                item.channels_list.remove(index_to_remove)
            else:
                self.report({'WARNING'}, "Channel not found")
        else:
            scene = context.scene.scene_props

            OSC.send_osc_lighting("/eos/newcmd", f"{self.channel} at + 100 Sneak Time .5 Enter")
            time.sleep(.5)
            OSC.send_osc_lighting("/eos/newcmd", f"{self.channel} at + - 100 Sneak Time 1 Enter")

        Utils.update_all_controller_channel_lists(context)
        
        return {'FINISHED'}
    
    
#-----------------------------------------------------------------------------------------------------------------------------------------------
'''Begin Presets Node operators'''

class BaseColorOperator(Operator):
    bl_idname = "my.base_color_operator"
    bl_label = "Base Color Operator"
    bl_description = "Base Operator for Color Activation"

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
        
        channels = [str(chan.chan) for chan in group.channels_list]
        channels = " + ".join(channels)
        channels = Utils.simplify_channels_expression(channels)
        preset_number = self.color_number + self.index_offset
        argument_template = self.record_preset_argument_template if self.is_recording else self.preset_argument_template
        argument = argument_template.replace('#', str(channels)).replace('$', str(preset_number)).replace('^', self.preset_type)
        
        OSC.send_osc_lighting("/eos/newcmd", argument)
        return {'FINISHED'}
    

class ColorOne(BaseColorOperator):
    bl_idname = "my.color_one"
    bl_label = "Color One"
    bl_description = "Activate Color One"
    color_number = 1

class ColorTwo(BaseColorOperator):
    bl_idname = "my.color_two"
    bl_label = "Color Two"
    bl_description = "Activate Color Two"
    color_number = 2

class ColorThree(BaseColorOperator):
    bl_idname = "my.color_three"
    bl_label = "Color Three"
    bl_description = "Activate Color Three"
    color_number = 3

class ColorFour(BaseColorOperator):
    bl_idname = "my.color_four"
    bl_label = "Color Four"
    bl_description = "Activate Color Four"
    color_number = 4

class ColorFive(BaseColorOperator):
    bl_idname = "my.color_five"
    bl_label = "Color Five"
    bl_description = "Activate Color Five"
    color_number = 5

class ColorSix(BaseColorOperator):
    bl_idname = "my.color_six"
    bl_label = "Color Six"
    bl_description = "Activate Color Six"
    color_number = 6

class ColorSeven(BaseColorOperator):
    bl_idname = "my.color_seven"
    bl_label = "Color Seven"
    bl_description = "Activate Color Seven"
    color_number = 7

class ColorEight(BaseColorOperator):
    bl_idname = "my.color_eight"
    bl_label = "Color Eight"
    bl_description = "Activate Color Eight"
    color_number = 8

class ColorNine(BaseColorOperator):
    bl_idname = "my.color_nine"
    bl_label = "Color Nine"
    bl_description = "Activate Color Nine"
    color_number = 9

class ColorTen(BaseColorOperator):
    bl_idname = "my.color_ten"
    bl_label = "Color Ten"
    bl_description = "Activate Color Ten"
    color_number = 10

class ColorEleven(BaseColorOperator):
    bl_idname = "my.color_eleven"
    bl_label = "Color Eleven"
    bl_description = "Activate Color Eleven"
    color_number = 11

class ColorTwelve(BaseColorOperator):
    bl_idname = "my.color_twelve"
    bl_label = "Color Twelve"
    bl_description = "Activate Color Twelve"
    color_number = 12

class ColorThirteen(BaseColorOperator):
    bl_idname = "my.color_thirteen"
    bl_label = "Color Thirteen"
    bl_description = "Activate Color Thirteen"
    color_number = 13

class ColorFourteen(BaseColorOperator):
    bl_idname = "my.color_fourteen"
    bl_label = "Color Fourteen"
    bl_description = "Activate Color Fourteen"
    color_number = 14

class ColorFifteen(BaseColorOperator):
    bl_idname = "my.color_fifteen"
    bl_label = "Color Fifteen"
    bl_description = "Activate Color Fifteen"
    color_number = 15


#-----------------------------------------------------------------------------------------------------------------------------------------------
'''USITT ASCII Parsing Operator'''


class SendUSITTASCIITo3DOperator(bpy.types.Operator):
    bl_idname = "my.send_usitt_ascii_to_3d"
    bl_label = "Import Patch"
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

            # Set capabilities based on group_capabilities.
            if group_number in group_capabilities:
                group_label = group_info['label']
                capabilities = group_capabilities[group_number]

                new_controller.strobe_is_on = 'Strobe' in capabilities or '204' in capabilities
                new_controller.color_is_on = 'Red' in capabilities or '12' in capabilities or '11' in capabilities
                new_controller.pan_tilt_is_on = '2' in capabilities or '3' in capabilities
                new_controller.diffusion_is_on = 'Diffusion' in capabilities or '76' in capabilities
                new_controller.intensity_is_on = 'Intensity' in capabilities or '1' in capabilities
                new_controller.edge_is_on = 'Edge' in capabilities or '78' in capabilities
                new_controller.iris_is_on = 'Iris' in capabilities or '73' in capabilities
                new_controller.gobo_is_on = 'Gobo' in capabilities or '200' in capabilities
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
            
            new_group = context.scene.scene_group_data.add()
            new_group.name = group_label
            
            new_group.strobe_is_on = new_controller.strobe_is_on
            new_group.color_is_on = new_controller.color_is_on
            new_group.color_profile_enum = new_controller.color_profile_enum
            new_group.pan_tilt_is_on = new_controller.pan_tilt_is_on
            new_group.diffusion_is_on = new_controller.diffusion_is_on
            new_group.intensity_is_on = new_controller.intensity_is_on
            new_group.edge_is_on = new_controller.edge_is_on
            new_group.iris_is_on = new_controller.iris_is_on
            new_group.gobo_is_on = new_controller.gobo_is_on
            new_group.zoom_is_on = new_controller.zoom_is_on
            
            for channel in channels:
                new_channel = new_group.channels_list.add()
                new_channel.chan = channel
                
            try:
                new_controller.selected_group_enum = group_label
            except:
                print("An error occured because a group label was invalid.")

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
            light_object.str_maual_fixture_selection = str(channel_number)

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
    
    
class SendUSITTASCIIToSequencer(bpy.types.Operator):
    bl_idname = "my.send_usitt_ascii_to_sequencer"
    bl_label = "Not Enabled"
    bl_description = "Automatically populate strips in Sequencer based on USITT ASCII (event list data) export from the console"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        return {'FINISHED'}
    

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------  
'''Settings and renderer operators'''    
    
    
class DemocraticOperator(bpy.types.Operator):
    bl_idname = "my.democratic_operator"
    bl_label = "Democratic"
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
    bl_label = "Non-democratic"
    bl_description = "This isn't a democracy anymore. When different controllers try to change the same channel parameter, the strongest completely erases everyone else's opinion"

    def execute(self, context):
        if context.scene.scene_props.is_not_democratic:
            return {'FINISHED'}
        else:
            context.scene.scene_props.is_not_democratic = True
            context.scene.scene_props.is_democratic = False
            
        return {'FINISHED'}
    
    
class ToggleObjectMuteOperator(bpy.types.Operator):
    bl_idname = "object.toggle_object_mute_operator"
    bl_label = "Mute OSC"
    bl_description = "Disable object's OSC output"

    space_type: StringProperty() 
    node_name: StringProperty() 
    node_tree_name: StringProperty() 

    def execute(self, context):
        finders = Find
        active_controller = finders.find_controller_by_space_type(context, self.space_type, self.node_name, self.node_tree_name)
        active_controller.mute = not active_controller.mute
        return {'FINISHED'}
    
    
class PullFixtureSelectionOperator(bpy.types.Operator):
    bl_idname = "object.pull_selection_operator"
    bl_label = "Pull Fixtures"
    bl_description = "Pull current selection from 3D view"

    def execute(self, context):
        channels = [obj.str_manual_fixture_selection for obj in context.selected_objects]
        new_list = ", ".join(channels)
        active_object = context.active_object
        active_object.str_manual_fixture_selection = new_list
        return {'FINISHED'}
    
    
class AddLightingModifierOperator(bpy.types.Operator):
    bl_idname = "viewport.lighting_modifier_add"
    bl_label = "Add Lighting Modifier"
    bl_description = "Control all fixtures at once using photo-editing principles like layering"
    
    type: bpy.props.EnumProperty(
        name="Lighting Modifiers",
        description="Change all fixtures at once using photo-editing principles",
        items = [
            ('option_brightness_contrast', "Brightness/Contrast", "Adjust overall brightness and contrast of entire rig's intensity values"),
            ('option_saturation', "Saturation", "Adjust overall saturation of entire rig"),
            ('option_hue', "Hue", "Adjust the saturation of individual hues across the entire rig"),
            ('option_curves', "Curves", "Adjust overall brightness and contrast of entire rig's intensity values")
        ]
    )

    def execute(self, context):
        scene = context.scene
        modifier = scene.lighting_modifiers.add()
        modifier.name = self.type.replace('option_', '').replace('_', '/').title()
        modifier.type = self.type
        scene.active_modifier_index = len(scene.lighting_modifiers) - 1

        return {'FINISHED'}


class RemoveLightingModifierOperator(bpy.types.Operator):
    '''Remove selected modifier'''
    bl_idname = "viewport.lighting_modifier_remove"
    bl_label = "Remove Lighting Modifier"

    name: StringProperty()

    def execute(self, context):
        scene = context.scene
        index = scene.lighting_modifiers.find(self.name)
        if index != -1:
            scene.lighting_modifiers.remove(index)
            scene.active_modifier_index = min(max(0, scene.active_modifier_index - 1), len(scene.lighting_modifiers) - 1)
        return {'FINISHED'}


class MoveLightingModifierOperator(bpy.types.Operator):
    '''Bump modifiers position in the stack vertically'''
    bl_idname = "viewport.lighting_modifier_move"
    bl_label = "Move Lighting Modifier"

    name: StringProperty()
    direction: EnumProperty(
        items=(
            ('UP', 'Up', ''),
            ('DOWN', 'Down', '')
        )
    )

    def execute(self, context):
        scene = context.scene
        index = scene.lighting_modifiers.find(self.name)
        if index == -1:
            return {'CANCELLED'}
        new_index = index + (-1 if self.direction == 'UP' else 1)
        if new_index < 0 or new_index >= len(scene.lighting_modifiers):
            return {'CANCELLED'}
        scene.lighting_modifiers.move(index, new_index)
        scene.active_modifier_index = new_index
        return {'FINISHED'}
    
    
class CallFixturesOperator(bpy.types.Operator):
    bl_idname = "viewport.call_fixtures_operator"
    bl_label = "Summon Movers"
    bl_description = "You're supposed to type in a command line command in the space to the left and then fire that command by pressing this button. Use this feature to call any relevant moving lights to focus on this set piece"

    def execute(self, context):
        scene = context.scene.scene_props
        active_object = context.active_object
        string = active_object.str_call_fixtures_command
        
        if not string.endswith(" Enter"):
            string = f"{string} Enter"
        
        OSC.send_osc_lighting("/eos/newcmd", string)
        return {'FINISHED'}
    
    
class AddChoiceOperator(bpy.types.Operator):
    bl_idname = "node.add_choice"
    bl_label = "Add Choice"
    bl_description = "Add a new choice"

    def execute(self, context):
        node = context.node
        choice = node.parameters.add()
        node.active_modifier_index = len(node.parameters) - 1
        choice.node_tree_pointer = node.id_data
        choice.node_name = node.name
        return {'FINISHED'}
    
    
class RemoveChoiceOperator(bpy.types.Operator):
    bl_idname = "node.remove_choice"
    bl_label = "Remove Choice"
    bl_description = "Remove the last choice"

    def execute(self, context):
        node = context.node
        if node.parameters:
            index = len(node.parameters) - 1
            node.parameters.remove(index)
            node.active_modifier_index = max(0, len(node.parameters) - 1)
        return {'FINISHED'}
    
    
class AddGroupOperator(bpy.types.Operator):
    bl_idname = "patch.add_group_item"
    bl_label = "Add a new group"

    def execute(self, context):
        scene = context.scene
        new_item = scene.scene_group_data.add()
        new_item.name = "New Group"
        scene.scene_props.group_data_index = len(scene.scene_group_data) - 1
        return {'FINISHED'}
    

class RemoveGroupOperator(bpy.types.Operator):
    bl_idname = "patch.remove_group_item"
    bl_label = "Remove the selected group"

    def execute(self, context):
        scene = context.scene
        index = scene.scene_props.group_data_index

        scene.scene_group_data.remove(index)

        if index > 0:
            scene.scene_props.group_data_index = index - 1
        else:
            scene.scene_props.group_data_index = 0
        return {'FINISHED'}


class BumpGroupOperator(bpy.types.Operator):
    bl_idname = "patch.bump_group_item"
    bl_label = "Bump Group Up or Down"
    
    direction: bpy.props.IntProperty()

    def execute(self, context):
        scene = context.scene
        index = scene.scene_props.group_data_index
        
        if self.direction == 1 and index < len(scene.scene_group_data) - 1:
            scene.scene_group_data.move(index, index + 1)
            scene.scene_props.group_data_index += 1
        elif self.direction == -1 and index > 0:
            scene.scene_group_data.move(index, index - 1)
            scene.scene_props.group_data_index -= 1
        else:
            self.report({'WARNING'}, "Cannot move further in this direction")
        
        return {'FINISHED'}


class VIEW3D_OT_object_controller(Operator):
    bl_idname = "alva_view3d.object_controller"
    bl_label = "Object Controller"
    
    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        width = 180
        return context.window_manager.invoke_popup(self, width=width)

    @classmethod
    def poll(cls, context):
        return (hasattr(context, "scene") and
                hasattr(context, "active_object"))

    def draw(self, context):
        active_object = context.active_object
        from ..as_ui.space_common import draw_parameters_mini, draw_play_bar
        from ..as_ui.space_view3d import draw_speaker
        
        if active_object.type == 'MESH':
            draw_parameters_mini(self, context, self.layout, active_object, use_slider=True)
            self.layout.separator()
            draw_play_bar(self, context, self.layout)
        
        # if active_object.type == 'SPEAKER':
        #     draw_speaker(self, context, active_object)


class VIEW3D_OT_alva_set_context_to_scene(bpy.types.Operator):
    '''Sets active_strip to nothing so you can see the settings for the global Scene instead'''
    bl_idname = "view3d.alva_set_context_to_scene"
    bl_label = "Show Scene properties"

    def execute(self, context):
        if context.scene.sequence_editor:
            context.scene.sequence_editor.active_strip = None
        return {'FINISHED'}

    
classes = (
    AddChannelToGroupOperator,
    RemoveChannelFromGroupOperator,
    ApplyPatchToObjectsOperator,
    BaseColorOperator,
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
    SendUSITTASCIITo3DOperator,
    SendUSITTASCIIToSequencer,
    DemocraticOperator,
    NonDemocraticOperator,
    ToggleObjectMuteOperator,
    PullFixtureSelectionOperator,
    AddLightingModifierOperator,
    RemoveLightingModifierOperator,
    MoveLightingModifierOperator,
    CallFixturesOperator,
    AddChoiceOperator,
    RemoveChoiceOperator,
    AddGroupOperator,
    RemoveGroupOperator,
    BumpGroupOperator,
    VIEW3D_OT_object_controller,
    VIEW3D_OT_alva_set_context_to_scene
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
            
        
def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)