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


import re
from collections import defaultdict

from ..utils.event_utils import EventUtils
from ..utils.properties_utils import parse_channels
from ..utils.sequencer_utils import calculate_flash_strip_bias


class StripMapping:
    def get_start_macro_map(scene):
        mapping = defaultdict(list)  
        
        for strip in filter_eos_macro_strips(scene.sequence_editor.sequences):
            data = (strip.name, str(strip.int_start_macro))
            if data[0] and data[1]:
                mapping[strip.frame_start].append(data)
                            
        return dict(mapping)

    def get_end_macro_map(scene):
        mapping = defaultdict(list)

        for strip in filter_eos_macro_strips(scene.sequence_editor.sequences):
            data = (strip.name, str(strip.int_end_macro))
            if data[0] and data[1]:
                mapping[strip.frame_final_end].append(data)
                            
        return dict(mapping)

    def get_start_flash_macro_map(scene):
        mapping = defaultdict(list)  
        
        for strip in filter_eos_flash_strips(scene.sequence_editor.sequences):
            data = (strip.name, str(strip.int_start_macro))
            if data[0] and data[1]:
                mapping[strip.frame_start].append(data)
                        
        return dict(mapping)

    def get_end_flash_macro_map(scene):
        mapping = defaultdict(list)
        
        for strip in filter_eos_flash_strips(scene.sequence_editor.sequences):
            data = (strip.name, str(strip.int_end_macro))
            bias = strip.flash_bias
            frame_rate = EventUtils.get_frame_rate(scene)
            strip_length_in_frames = strip.frame_final_duration
            bias_in_frames = calculate_flash_strip_bias(bias, frame_rate, strip_length_in_frames)
            start_frame = strip.frame_start
            end_flash_macro_frame = start_frame + bias_in_frames
            end_flash_macro_frame = int(round(end_flash_macro_frame))
            
            if data[0] and data[1]:
                mapping[end_flash_macro_frame].append(data)
                        
        return dict(mapping)
        

    def get_trigger_start_map(scene):
        mapping = defaultdict(list)

        for strip in filter_trigger_only_strips(scene.sequence_editor.sequences):
            # In the original Sequencer software, this used a background formatter property as [1].
            data = (strip.trigger_prefix, strip.osc_trigger)
            if data[0] and data[1]:
                mapping[strip.frame_start].append(data)
        return dict(mapping)

    def get_trigger_offset_start_map(scene, active_strip=None):
        mapping = defaultdict(list)
        
        if not active_strip:
            for strip in filter_trigger_strips(scene.sequence_editor.sequences):
                commands = get_offset_triggers(strip)
                if commands:
                    strip_length = strip.frame_final_end - strip.frame_start  # Length of the strip
                    num_commands = len(commands)
                    step_value = strip_length / num_commands  # Gap between each command
                    for index, command in enumerate(commands):
                        offset_frame_start = strip.frame_start + int(step_value * index)
                        mapping_entry = (strip.trigger_prefix, command)
                        mapping[offset_frame_start].append(mapping_entry)

        else:
            strip = active_strip
            commands = get_offset_triggers(strip)
            if commands:
                strip_length = strip.frame_final_end - strip.frame_start  # Length of the strip
                num_commands = len(commands)
                step_value = strip_length / num_commands  # Gap between each command
                for index, command in enumerate(commands):
                    offset_frame_start = strip.frame_start + int(step_value * index)
                    mapping_entry = (strip.trigger_prefix, command)
                    mapping[offset_frame_start].append(mapping_entry)

            return offset_mapping_to_string(mapping, scene)

        return dict(mapping)

    def get_trigger_end_map(scene):
        mapping = defaultdict(list)

        for strip in filter_trigger_only_strips(scene.sequence_editor.sequences):
            data = (strip.trigger_prefix, strip.osc_trigger_end)
            if data[0] and data[1]:
                mapping[strip.frame_final_end].append(data)

        return dict(mapping)

    def get_cue_map(scene):
        mapping = defaultdict(list)
        
        for strip in filter_eos_cue_strips(scene.sequence_editor.sequences):
            data = (strip.name, strip.eos_cue_number)
            if strip.eos_cue_number == 0:
                continue
            elif data[0] and data[1]:
                mapping[strip.frame_start].append(data)

        return dict(mapping)
    
    def get_offset_map(scene):
        mapping = defaultdict(list)   
        
        for strip in filter_trigger_strips(scene.sequence_editor.sequences):
            if strip.use_macro:
                data = (strip.name, str(strip.int_start_macro))
                if data[0] and data[1]:
                    mapping[strip.frame_start].append(data)
                            
        return dict(mapping)


# Defines lists of strips with relevant enumerator and checkbox choices.
def filter_eos_cue_strips(sequences):
    return [strip for strip in sequences if strip.type == 'COLOR' and strip.my_settings.motif_type_enum == 'option_eos_cue' and not strip.mute]

def filter_animation_strips(sequences):
    return [strip for strip in sequences if strip.type == 'COLOR' and strip.my_settings.motif_type_enum == 'option_animation' and not strip.mute]

def filter_trigger_only_strips(sequences):
    return [strip for strip in sequences if strip.type == 'COLOR' and strip.my_settings.motif_type_enum == 'option_trigger' and not strip.use_macro and not strip.mute]

def filter_trigger_strips(sequences):
    return [strip for strip in sequences if strip.type == 'COLOR' and strip.my_settings.motif_type_enum == 'option_trigger' and strip.use_macro and not strip.mute]

def filter_timecode_learn_strips(sequences):
    return [strip for strip in sequences if strip.type == 'SOUND' and strip.int_event_list != 0 and strip.my_learning_checkbox == True and not strip.mute]

def filter_timecode_strips(sequences):
    return [strip for strip in sequences if strip.type == 'SOUND' and strip.int_event_list != 0 and strip.my_learning_checkbox == False and not strip.mute]

def filter_eos_macro_strips(sequences):
    return [strip for strip in sequences if strip.type == 'COLOR' and strip.my_settings.motif_type_enum == 'option_eos_macro' and not strip.mute]

def filter_eos_flash_strips(sequences):
    return [strip for strip in sequences if strip.type == 'COLOR' and strip.my_settings.motif_type_enum == 'option_eos_flash' and not strip.mute]


def get_offset_triggers(strip):
    concurrent_commands = parse_concurrent_commands(strip.friend_list)
    if len(concurrent_commands) > 1:
        command_list = generate_concurrent_command_strings(strip.osc_trigger, concurrent_commands)
    else:
        channels = parse_channels(strip.friend_list)
        command_list = generate_command_strings(strip.osc_trigger, channels)
    
    return command_list


def parse_concurrent_commands(input_string):
    # Split input by parentheses to identify concurrent groups.
    concurrent_groups = re.findall(r'\(([^)]+)\)', input_string)
    concurrent_commands = []
    
    # Parse each group separately.
    for group in concurrent_groups:
        channels = parse_channels(group)
        concurrent_commands.append(channels)

    # If there are no concurrent groups, treat the entire input as sequential.
    if not concurrent_commands:
        concurrent_commands.append(parse_channels(input_string))
    
    return concurrent_commands


def generate_concurrent_command_strings(command, concurrent_commands):
    command_lists = []

    for channels in concurrent_commands:
        template = re.sub(r'\b\d+\b', '{}', command, count=1)
        command_lists.append([template.format(chan) for chan in channels])
    
    # Generate the concurrent command list.
    concurrent_command_list = []
    for commands in zip(*command_lists):
        concurrent_command_list.append(" ".join(commands))
        
    return concurrent_command_list


def generate_command_strings(command, channels):
    command_list = []

    for chan in channels:
        command_string = re.sub(r'\b\d+\b', str(chan), command, count=1)
        command_list.append(command_string)
    return command_list


def offset_mapping_to_string(mapping, scene):
    try:
        fps = EventUtils.get_frame_rate(scene)

        result_list = []
        initial_offset = list(mapping.keys())[0]

        for offset, actions in mapping.items():
            for action in actions:
                command, description = action
                delay = (offset - initial_offset) / fps
                # Remove any variations of "enter" (case insensitive)
                clean_description = re.sub(r'\b[eE][nN][tT][rR]?[eE]?[rR]?\b', '', description).strip()
                result_list.append(f"{clean_description} Delay {delay:.2f} Enter")
        return ", ".join(result_list)
    
    except:
        print(f"Please add values to Start Frame Offsets field.")