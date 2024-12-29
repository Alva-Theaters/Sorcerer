# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.props import StringProperty
from bpy.types import Operator
import math
import os

from ..assets.dictionaries import Dictionaries

LICENSE_HEADER_NUM_LINES = 4


class TEXT_OT_alva_populate_macros(Operator):
    bl_idname = "alva_text.populate_macros"
    bl_label = "Populate"
    bl_description = "Populate macro buttons"

    filter_group: StringProperty()   # type: ignore

    def execute(self, context):
        scene = context.scene
        scene.macro_buttons.clear()

        groups = {
            "All": Dictionaries.macro_buttons,
            "Basic Operations": Dictionaries.basic_operations,
            "Numbers": Dictionaries.numbers,
            "Letters": Dictionaries.letters,
            "Console Buttons": Dictionaries.console_buttons,
            "Control": Dictionaries.control,
            "Network": Dictionaries.network,
            "Attributes": Dictionaries.attributes,
            "Effects": Dictionaries.effects,
            "Time and Date": Dictionaries.time_and_date,
            "Miscellaneous": Dictionaries.miscellaneous,
            "Timecode": Dictionaries.timecode,
        }

        if self.filter_group in groups:
            for name in groups[self.filter_group]:
                item = scene.macro_buttons.add()
                item.name = name

        return {'FINISHED'}
    

class TEXT_OT_alva_send_text_to_3d(Operator):
    bl_idname = "alva_text.text_to_3d"
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
    

class TEXT_OT_alva_template_add(Operator):
    bl_idname = 'alva_text.template_add'
    bl_label = "Template"

    template_type: StringProperty() # type: ignore

    def execute(self, context):
        if self.template_type == 'lighting_console':
            text_block_name = "lighting_console.py"
            file_path = os.path.join(os.path.dirname(__file__), '..', 'extendables', 'python_templates', 'lighting_console.py')
        elif self.template_type == 'strip':
            text_block_name = "custom_strip.py"
            file_path = os.path.join(os.path.dirname(__file__), '..', 'extendables', 'python_templates', 'custom_strip.py')
        else:
            self.report({'ERROR'}, "Unknown template type")
            return {'CANCELLED'}

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()[LICENSE_HEADER_NUM_LINES:]
                content = ''.join(lines)
        except FileNotFoundError:
            self.report({'ERROR'}, f"File {file_path} not found")
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error reading {file_path}: {str(e)}")
            return {'CANCELLED'}

        new_text_block = bpy.data.texts.new(name=text_block_name)
        new_text_block.from_string(content)
        context.space_data.text = new_text_block
        context.area.tag_redraw()
        bpy.ops.text.move(type='FILE_TOP')
        bpy.ops.text.move(type='LINE_BEGIN')

        return {'FINISHED'}
    

operator_classes = [
    TEXT_OT_alva_populate_macros,
    TEXT_OT_alva_send_text_to_3d,
    TEXT_OT_alva_template_add
]


def register():
    for cls in operator_classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(operator_classes):
        bpy.utils.unregister_class(cls)