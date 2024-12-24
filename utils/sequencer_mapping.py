# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

from collections import defaultdict

'''
This is the problem: 
    Blender doesn't just tell us when a strip in the sequencer gets hit by the play bar during playback.
    We need to figure that out on our own if we want our custom strips to be able to do stuff. The 
    event_manager.py and Orb scripts need this script to tell them what strips want to do what stuff when.
    
This is the complication:
    All the types of strips we add to the sequencer for lighting purposes are user-extendable. This means 
    users can just add their own Alva Sorcerer strip types that do customizable stuff at customizable times 
    (relative to the location of the strip's start and end frame).

    This means we need to seriously minimize what's hardcoded.

This is what we need to achieve:
    dictionary_of_What_the_strips_in_sequencer_want_to_do_and_When = {
        frame_number: (osc_address, osc_argument),
        frame_number: (osc_address, osc_argument),
        frame_number: (osc_address, osc_argument),
    }

    ...where the key is the When and the tuple item is the What.

This is how we do it:
    1. Figure out what strip type classes are currently registered. This will include the built-in 
        Sorcerer ones and any types the user added with additional addons or scripts (__init__() method).

    2. Iterate over each strip class and...
            Iterate over each relevant strip matched to that class and ...
                Process the start-frame and end-frame of that strip using the current StripClass's methods
                to figure out the When and What. We will append the result to the dictionary.

    3. Return our completed dictionary to whoever wanted it.
'''

VALID_STRIP_TYPE = 'COLOR'

class StripMapper:
    def __init__(self, scene, streaming=False):
        self.streaming = streaming
        self.mapping = defaultdict(list)
        self.sequences = scene.sequence_editor.sequences
        self.strip_classes = self.find_registered_strip_classes()

    def find_registered_strip_classes(self):
        from .spy_utils import REGISTERED_STRIPS
        return list(REGISTERED_STRIPS.values())


    def execute(self):
        for StripClass in self.strip_classes:
            if self.streaming and not StripClass.streaming:
                continue
            for strip in self.filter_strips(StripClass.as_idname):
                self.process_a_side_of_the_strip(StripClass, strip, side="start")
                self.process_a_side_of_the_strip(StripClass, strip, side="end")

        print(f"Mapping: {dict(self.mapping)}")
        return dict(self.mapping)

    def filter_strips(self, strip_type):
        return [strip for strip in self.sequences if strip.type == VALID_STRIP_TYPE and strip.my_settings.motif_type_enum == strip_type and not strip.mute]

    def process_a_side_of_the_strip(self, StripClass, strip, side):
        '''Processes a single side (start or end) of the given strip.'''
        try:
            frame_func = getattr(StripClass, f"get_{side}_frame")
            value_func = getattr(StripClass, f"get_{side}_value")
            form_osc_func = getattr(StripClass, "form_osc")
        except AttributeError:
            return

        if not frame_func or not value_func or not form_osc_func:
            return

        if StripClass.poll and not StripClass.poll(strip):
            return

        frames = frame_func(strip)
        values = value_func(strip)

        frames, values = self.format_frames_and_values(frames, values)

        for frame, value in zip(frames, values):
            data = form_osc_func(strip, value)

            if all(data):
                self.mapping[frame].append(data)

    def format_frames_and_values(self, frames, values):
        if not isinstance(frames, list):
            frames = [frames]
        if not isinstance(values, list):
            values = [values]

        if len(frames) != len(values):
            min_length = min(len(frames), len(values))
            frames = frames[:min_length]
            values = values[:min_length]

        return frames, values

'''
This stuff is from the old Offset Friends thing from Alva Sequencer. 
This code will be useful for reference when Offset Strips are actually built. 
Those strips will reuse the exact same logic, so don't delete.
'''
# import re

# from ..utils.event_utils import EventUtils
# from ..utils.rna_utils import parse_channels
# def get_offset_triggers(strip):
#     concurrent_commands = parse_concurrent_commands(strip.friend_list)
#     if len(concurrent_commands) > 1:
#         command_list = generate_concurrent_command_strings(strip.osc_trigger, concurrent_commands)
#     else:
#         channels = parse_channels(strip.friend_list)
#         command_list = generate_command_strings(strip.osc_trigger, channels)
    
#     return command_list


# def parse_concurrent_commands(input_string):
#     # Split input by parentheses to identify concurrent groups.
#     concurrent_groups = re.findall(r'\(([^)]+)\)', input_string)
#     concurrent_commands = []
    
#     # Parse each group separately.
#     for group in concurrent_groups:
#         channels = parse_channels(group)
#         concurrent_commands.append(channels)

#     # If there are no concurrent groups, treat the entire input as sequential.
#     if not concurrent_commands:
#         concurrent_commands.append(parse_channels(input_string))
    
#     return concurrent_commands


# def generate_concurrent_command_strings(command, concurrent_commands):
#     command_lists = []

#     for channels in concurrent_commands:
#         template = re.sub(r'\b\d+\b', '{}', command, count=1)
#         command_lists.append([template.format(chan) for chan in channels])
    
#     # Generate the concurrent command list.
#     concurrent_command_list = []
#     for commands in zip(*command_lists):
#         concurrent_command_list.append(" ".join(commands))
        
#     return concurrent_command_list


# def generate_command_strings(command, channels):
#     command_list = []

#     for chan in channels:
#         command_string = re.sub(r'\b\d+\b', str(chan), command, count=1)
#         command_list.append(command_string)
#     return command_list


# def offset_mapping_to_string(mapping, scene):
#     try:
#         fps = EventUtils.get_frame_rate(scene)

#         result_list = []
#         initial_offset = list(mapping.keys())[0]

#         for offset, actions in mapping.items():
#             for action in actions:
#                 command, description = action
#                 delay = (offset - initial_offset) / fps
#                 # Remove any variations of "enter" (case insensitive)
#                 clean_description = re.sub(r'\b[eE][nN][tT][rR]?[eE]?[rR]?\b', '', description).strip()
#                 result_list.append(f"{clean_description} Delay {delay:.2f} Enter")
#         return ", ".join(result_list)
    
#     except:
#         print(f"Please add values to Start Frame Offsets field.")


# def get_trigger_offset_start_map(scene, active_strip=None):
#     mapping = defaultdict(list)
    
#     if not active_strip:
#         for strip in filter_trigger_strips(scene.sequence_editor.sequences):
#             commands = get_offset_triggers(strip)
#             if commands:
#                 strip_length = strip.frame_final_end - strip.frame_start  # Length of the strip
#                 num_commands = len(commands)
#                 step_value = strip_length / num_commands  # Gap between each command
#                 for index, command in enumerate(commands):
#                     offset_frame_start = strip.frame_start + int(step_value * index)
#                     mapping_entry = (strip.trigger_prefix, command)
#                     mapping[offset_frame_start].append(mapping_entry)

#     else:
#         strip = active_strip
#         commands = get_offset_triggers(strip)
#         if commands:
#             strip_length = strip.frame_final_end - strip.frame_start  # Length of the strip
#             num_commands = len(commands)
#             step_value = strip_length / num_commands  # Gap between each command
#             for index, command in enumerate(commands):
#                 offset_frame_start = strip.frame_start + int(step_value * index)
#                 mapping_entry = (strip.trigger_prefix, command)
#                 mapping[offset_frame_start].append(mapping_entry)

#         return offset_mapping_to_string(mapping, scene)

#     return dict(mapping)