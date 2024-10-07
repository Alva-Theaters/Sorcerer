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
import math
import mathutils
import re
import time
from bpy.types import Scene, Object

try:
    import allin1 # type: ignore
except:
    print(f"Could not import allin1.")
    
from ..assets.dictionaries import Dictionaries 
from ..utils.osc import OSC


DEFAULT_EXECUTOR_INDEX = 1


class Segment:
    def __init__(self, start, end, label):
        self.start = start
        self.end = end
        self.label = label

    def __repr__(self):
        return f"Segment(start={self.start}, end={self.end}, label='{self.label}')"

class AnalysisResult:
    def __init__(self, path, bpm, beats, beat_positions, downbeats, segments):
        self.path = path
        self.bpm = bpm
        self.beats = beats
        self.beat_positions = beat_positions
        self.downbeats = downbeats
        self.segments = segments

    def __repr__(self):
        return (f"AnalysisResult(path='{self.path}', bpm={self.bpm}, beats={self.beats}, "
                f"beat_positions={self.beat_positions}, downbeats={self.downbeats}, segments={self.segments})")


class Utils:
    def register_properties(cls, properties, register=True):
        if register:
            for prop_name, prop_value in properties:
                setattr(cls, prop_name, prop_value)
        else:
            for prop_name, _ in reversed(properties):
                delattr(cls, prop_name)
                

    def find_subclass_by_name(base_class, subclass_name):
        """
        Find a subclass of base_class with the given subclass_name.
        This is for when we run Sorcerer from the built-in text editor
        and need to register properties using PropertyGroup subclasses
        registered from another script, in this case, property_groups.py.
        
        Args:
            base_class (class): The base class to search for subclasses.
            subclass_name (str): The name of the subclass to find.
        
        Returns:
            class: The found subclass.
        """
        for subclass in base_class.__subclasses__():
            if subclass.__name__ == subclass_name:
                return subclass
        assert False, f"{subclass_name} not registered"
        

    def get_frame_rate(scene):
        return round((scene.render.fps / scene.render.fps_base), 2)


    def parse_channels(input_string, remove=False):
        try:
            input_string = input_string.replace("do not want", "not").replace("don't want", "not").replace(".", "").replace("!", "").replace("?", "")
            input_string = input_string.lower()

            formatted_input = re.sub(r'[()]', '', input_string)
            
            # Ensure consistent spacing around the dash for cases like '1-10', '1 -10'
            formatted_input = re.sub(r'(\d)\s*-\s*(\d)', r'\1 - \2', formatted_input)
            
            # Split by commas and whitespace
            tokens = re.split(r'[,\s]+', formatted_input)
            
            versions_of_through = (
                "through", "thru", "-", "tthru", "throu", "--", "por", "thr", 
                "to", "until", "up to", "till", "over"
            )
            versions_of_not = (
                "not", "minus", "except", "excluding", "casting", "aside", 
                "without", "leave", "omit", "remove", "other", "than", "delete",
                "deleting", "take"
            )
            versions_of_add = (
                "add", "adding", "including", "include", 
                "save", "preserve", "plus", "with", "addition", "+", "want",
                "do"
            )

            channels = []
            exclusions = []
            additions = []
            i = 0
            exclude_mode = False
            add_mode = False
            
            while i < len(tokens):
                token = tokens[i]
                
                if token in versions_of_add:
                    exclude_mode = False
                elif token in ["keep", "keeping"]:
                    exclude_mode = False
                    add_mode = True
                elif token in versions_of_not:
                    exclude_mode = True
                    add_mode = False
                elif token in versions_of_through and i > 0 and i < len(tokens) - 1:
                    start = int(tokens[i-1])
                    end = int(tokens[i+1])
                    step = 1 if start < end else -1
                    range_list = list(range(start, end + step, step))
                    if exclude_mode:
                        exclusions.extend(range_list)
                    elif add_mode:
                        additions.extend(range_list)
                    else:
                        channels.extend(range_list)
                    i += 1  # Skip the end token of the range
                elif token.isdigit():
                    num = int(token)
                    if exclude_mode:
                        exclusions.append(num)
                    elif add_mode:
                        additions.append(num)
                    else:
                        channels.append(num)
                i += 1
            
            channels = [ch for ch in channels if ch not in exclusions]
            channels.extend(additions)
            
            channels = list(set(channels))
            channels.sort()
            
            if not remove:
                return channels
            else:
                return channels, exclusions
        
        except Exception as e:
            print(f"An error has occured within parse_channels: {e}")
            return None

    def parse_mixer_channels(input_string):
        try:
            groups = re.findall(r'\(([^)]+)\)', input_string)
            if not groups:
                groups = [input_string]
                
            all_channels = []

            for group in groups:
                channels = Utils.parse_channels(group)
                all_channels.append(tuple(channels))

            return all_channels
        except Exception as e:
            print(f"An error has occured within parse_channels: {e}")
            return None


    def update_all_controller_channel_lists(context):
        from ..cpvia.find import Find

        controllers, mixers_and_motors = Find.find_controllers(context.scene)

        for controller in controllers:
            if hasattr(controller, "str_manual_fixture_selection"):
                controller.str_manual_fixture_selection = controller.str_manual_fixture_selection


    def get_loc_rot(obj, use_matrix=False):
        x_pos, y_pos, z_pos, x_rot_rad, y_rot_rad, z_rot_rad  = Utils.get_original_loc_rot(obj, use_matrix)

        # Convert meters to feet.
        position_x = round(x_pos / .3048, 2)
        position_y = round(y_pos / .3048, 2)
        position_z = round(z_pos / .3048, 2)

        # Round and rotate x by 180 degrees (pi in radians) since cone facing up is the same as a light facing down.
        orientation_x = round(math.degrees(x_rot_rad + math.pi), 2)
        orientation_y = round(math.degrees(y_rot_rad), 2)
        orientation_z = 0  # Prevent modifiers from messing up pan/tilt. ## Add option to enable in the future.

        return position_x, position_y, position_z, orientation_x, orientation_y, orientation_z
    
    
    def get_original_loc_rot(obj, use_matrix=False):
        if use_matrix:
            depsgraph = bpy.context.evaluated_depsgraph_get()
            eval_obj = obj.evaluated_get(depsgraph)
            matrix = eval_obj.matrix_world
            
            euler = matrix.to_euler('XYZ')

            # Convert radians to degrees for rotation
            x_rot_rad = euler.x  # Tilt
            y_rot_rad = euler.z  # Pan seems to be on zed euler, not on y as y resolves to super tiny number.
            z_rot_rad = euler.y  # Roll

            position = matrix.translation
            x_pos = position.x
            y_pos = position.y
            z_pos = position.z

        else:
            x_pos = obj.location.x
            y_pos = obj.location.y
            z_pos = obj.location.z
            x_rot_rad = obj.rotation_euler.x
            y_rot_rad = obj.rotation_euler.y
            z_rot_rad = obj.rotation_euler.z

        return x_pos, y_pos, z_pos, x_rot_rad, y_rot_rad, z_rot_rad 


                
    def try_parse_int(value):
        try:
            return int(value)
        except ValueError:
            return None
                
    def swap_preview_and_program(cue_list):
        if not cue_list.is_progressive:
            temp = cue_list.int_preview_index
            cue_list.int_preview_index = cue_list.int_program_index
            cue_list.int_program_index = temp
            
        else:
            cue_list.int_program_index = (cue_list.int_preview_index)
            cue_list.int_preview_index = (cue_list.int_program_index + 1)
                        
    def frame_to_timecode(frame, fps=None):
        context = bpy.context
        """Convert frame number to timecode format."""
        if fps is None:
            fps = context.scene.render.fps_base * context.scene.render.fps
        hours = int(frame // (fps * 3600))
        frame %= fps * 3600
        minutes = int(frame // (fps * 60))
        frame %= fps * 60
        seconds = int(frame // fps)
        frames = int(round(frame % fps))
        return "{:02}:{:02}:{:02}:{:02}".format(hours, minutes, seconds, frames)

    def time_to_frame(time, frame_rate, start_frame):
        return int(time * frame_rate) + start_frame

    def add_color_strip(name, length, channel, color, strip_type, frame):
        scene = bpy.context.scene
        strip = scene.sequence_editor.sequences.new_effect(
            name=name,
            type='COLOR',
            channel=channel,
            frame_start=int(frame),
            frame_end=int(frame + length)
        )
        strip.color = color
        strip.my_settings.motif_type_enum = strip_type
        
    def analyze_song(self, filepath):
        try:
            return allin1.analyze(filepath)
        except:
            print("allin1 not found or failed. Returning hardcoded dummy class.")

            return AnalysisResult(
                path=filepath, 
                bpm=100,
                beats=[
                    0.33, 0.75, 1.14, 1.55, 1.97, 2.38, 2.79, 3.21, 3.62, 4.03, 4.44, 4.86, 5.27, 5.68, 6.10, 6.51, 6.92, 7.33,
                    7.75, 8.16, 8.57, 8.98, 9.40, 9.81, 10.22, 10.63, 11.05, 11.46, 11.87, 12.29, 12.70, 13.11, 13.53, 13.94,
                    14.35, 14.76, 15.18, 15.59, 16.00, 16.41, 16.83, 17.24, 17.65, 18.06, 18.48, 18.89, 19.30, 19.71, 20.13,
                    20.54, 20.95, 21.36, 21.78, 22.19, 22.60, 23.01, 23.43, 23.84, 24.25, 24.66, 25.08, 25.49, 25.90, 26.31,
                    26.73, 27.14, 27.55, 27.96, 28.38, 28.79, 29.20, 29.61, 30.03, 30.44, 30.85, 31.26, 31.68, 32.09, 32.50,
                    32.91, 33.33, 33.74, 34.15, 34.56, 34.98, 35.39, 35.80, 36.21, 36.63, 37.04, 37.45, 37.86, 38.28, 38.69,
                    39.10, 39.51, 39.93, 40.34, 40.75, 41.16, 41.58, 41.99, 42.40, 42.81, 43.23, 43.64, 44.05, 44.46, 44.88,
                    45.29, 45.70, 46.11, 46.53, 46.94, 47.35, 47.76, 48.18, 48.59, 49.00, 49.41, 49.83, 50.24, 50.65, 51.06,
                    51.48, 51.89, 52.30, 52.71, 53.13, 53.54, 53.95, 54.36, 54.78, 55.19, 55.60, 56.01, 56.43, 56.84, 57.25,
                    57.66, 58.08, 58.49, 58.90, 59.31, 59.73, 60.14, 60.55, 60.96, 61.38, 61.79, 62.20, 62.61, 63.03, 63.44,
                    63.85, 64.26, 64.68, 65.09, 65.50, 65.91, 66.33, 66.74, 67.15, 67.56, 67.98, 68.39, 68.80, 69.21, 69.63,
                    70.04, 70.45, 70.86, 71.28, 71.69, 72.10, 72.51, 72.93, 73.34, 73.75, 74.16, 74.58, 74.99, 75.40, 75.81,
                    76.23, 76.64, 77.05, 77.46, 77.88, 78.29, 78.70, 79.11, 79.53, 79.94, 80.35, 80.76, 81.18, 81.59, 82.00,
                    82.41, 82.83, 83.24, 83.65, 84.06, 84.48, 84.89, 85.30, 85.71, 86.13, 86.54, 86.95, 87.36, 87.78, 88.19,
                    88.60, 89.01, 89.43, 89.84, 90.25, 90.66, 91.08, 91.49, 91.90, 92.31, 92.73, 93.14, 93.55, 93.96, 94.38,
                    94.79, 95.20, 95.61, 96.03, 96.44, 96.85, 97.26, 97.68, 98.09, 98.50, 98.91, 99.33, 99.74, 100.15, 100.56,
                    100.98, 101.39, 101.80, 102.21, 102.63, 103.04, 103.45, 103.86, 104.28, 104.69, 105.10, 105.51, 105.93
                ],
                beat_positions=[
                    1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4,
                    1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4,
                    1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4,
                    1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4,
                    1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4,
                    1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4,
                    1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4,
                    1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4
                ],
                downbeats=[
                    0.33, 1.94, 3.53, 5.12, 6.71, 8.30, 9.90, 11.49, 13.08, 14.67, 16.26, 17.86, 19.45, 21.04, 22.63, 24.22, 25.82,
                    27.41, 29.00, 30.59, 32.18, 33.78, 35.37, 36.96, 38.55, 40.14, 41.74, 43.33, 44.92, 46.51, 48.10, 49.70, 51.29,
                    52.88, 54.47, 56.06, 57.66, 59.25, 60.84, 62.43, 64.02, 65.62, 67.21, 68.80, 70.39, 71.98, 73.58, 75.17, 76.76,
                    78.35, 79.94, 81.54, 83.13, 84.72, 86.31, 87.90, 89.50, 91.09, 92.68, 94.27, 95.86, 97.46, 99.05, 100.64, 102.23,
                    103.82, 105.42, 107.01, 108.60, 110.19, 111.78, 113.38, 114.97, 116.56, 118.15, 119.74, 121.34, 122.93, 124.52,
                    126.11, 127.70, 129.30, 130.89, 132.48, 134.07, 135.66, 137.26, 138.85, 140.44, 142.03, 143.62, 145.22, 146.81,
                    148.40, 149.99, 151.58, 153.18, 154.67
                ],
                segments=[
                    Segment(start=0.0, end=0.33, label='start'), 
                    Segment(start=0.33, end=13.13, label='intro'), 
                    Segment(start=13.13, end=37.53, label='chorus'), 
                    Segment(start=37.53, end=51.53, label='verse'), 
                    Segment(start=51.53, end=64.34, label='verse'), 
                    Segment(start=64.34, end=89.93, label='chorus'), 
                    Segment(start=89.93, end=105.93, label='bridge'), 
                    Segment(start=105.93, end=134.74, label='chorus'), 
                    Segment(start=134.74, end=153.95, label='chorus'), 
                    Segment(start=153.95, end=154.67, label='end'),
                ]
        )

    def find_available_channel(sequence_editor, start_frame, end_frame, start_channel=1):
        current_channel = start_channel

        while True:
            is_occupied = any(
                strip.channel == current_channel and not (strip.frame_final_end < start_frame or strip.frame_start > end_frame)
                for strip in sequence_editor.sequences
            )
            if not is_occupied:
                return current_channel
            current_channel += 1

    def duplicate_active_strip_to_selected(context):
        sequence_editor = context.scene.sequence_editor
        active_strip = sequence_editor.active_strip

        if not active_strip or active_strip.type != 'COLOR':
            return False, "No active color strip found."

        selected_strips = [strip for strip in sequence_editor.sequences if strip.select and strip != active_strip and strip.type == 'COLOR']
        
        if not selected_strips:
            return False, "No other selected color strips found."

        original_names = [strip.name for strip in selected_strips]
        original_start_frames = [strip.frame_start for strip in selected_strips]
        original_channels = [strip.channel for strip in selected_strips]

        new_strips = []
        
        for strip in selected_strips:
            sequence_editor.sequences.remove(strip)

        for original_start_frame, original_channel in zip(original_start_frames, original_channels):
            bpy.ops.sequencer.select_all(action='DESELECT')
            active_strip.select = True

            bpy.ops.sequencer.duplicate()

            duplicated_strip = next(strip for strip in sequence_editor.sequences if strip.select and strip != active_strip and strip not in new_strips)

            duplicated_strip.channel = original_channel - 1  # I don't know why this need - 1, but it goes up a channel for no reason otherwise.
            duplicated_strip.frame_start = original_start_frame
            
            new_strips.append(duplicated_strip)

            active_strip.select = False

        for new_strip, original_name in zip(new_strips, original_names):
            new_strip.name = original_name

        for strip in new_strips:
            strip.select = True

        return True, "Strips replaced with duplicates of the active strip successfully."
            
    # "auto_cue" aka Livemap
    def get_auto_cue_string(self):
        frame_rate = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base
        strip_length_in_seconds = round(self.frame_final_duration / frame_rate, 2)
        return "Go_to_Cue " + str(self.eos_cue_number) + " Time Enter"

    def get_motif_name_items(self, context):
        unique_names = set() 
        sequences = context.scene.sequence_editor.sequences_all
        for seq in sequences:
            if hasattr(seq, 'motif_name'):  
                unique_names.add(seq.motif_name)
        items = [(name, name, "") for name in sorted(unique_names)]
        return items
            
    # For flash end macro.
    def calculate_bias_offseter(bias, frame_rate, strip_length_in_frames):
        if bias == 0:
            return strip_length_in_frames / 2
        elif bias < 0:
            proportion_of_first_half = (49 + bias) / 49
            return round(strip_length_in_frames * proportion_of_first_half * 0.5)
        else:
            proportion_of_second_half = bias / 49
            return round(strip_length_in_frames * (0.5 + proportion_of_second_half * 0.5))

    def render_volume(speaker, empty, sensitivity, object_size, int_mixer_channel):
        '''Basically a crude form of the Dolby Atmos Renderer'''
        distance = (speaker.location - empty.location).length
        adjusted_distance = max(distance - object_size, 0)
        final_distance = adjusted_distance + sensitivity
        final_distance = max(final_distance, 1e-6)
        base_volume = 1.0
        volume = base_volume / final_distance
        volume = max(0, min(volume, 1))
        
        if bpy.context.screen:
            for area in bpy.context.screen.areas:
                if area.type == 'SEQUENCE_EDITOR':
                    area.tag_redraw()
                
        if bpy.context.scene.str_audio_ip_address != "":
            address = bpy.context.scene.audio_osc_address.format("#", str(int_mixer_channel))
            address = address.format("$", round(volume))
            argument = bpy.context.scene.audio_osc_argument.format("#", str(int_mixer_channel))
            argument = argument.format("$", round(volume))
            OSC.send_osc_lighting(address, argument)
        return volume


    def color_object_to_tuple_and_scale_up(v):
        if type(v) == mathutils.Color:
            return (v.r * 100, v.g * 100, v.b * 100)

        else: 
            r, g, b = v
            return (r * 100, g * 100, b * 100)
        

    def find_group_label(controller):
        if not controller.is_text_not_group:
            return controller.str_group_label
        else:
            return f"Channels {controller.str_manual_fixture_selection}"
        
        
    def update_nodes(connected_nodes):
        for node in connected_nodes:
            Utils.update_alva_controller(node)


    def update_alva_controller(controller):
        from ..properties.common_properties import CommonProperties 
        props = CommonProperties

        # Redirect to mixer node's PropertyGroup if controller is a mixer node
        if hasattr(controller, "bl_idname") and controller.bl_idname == 'mixer_type':
            for choice in controller.parameters:
                for prop_name, _ in props.common_parameters:
                    setattr(choice, prop_name, getattr(choice, prop_name))

        else:
            for prop_name, _ in props.common_parameters + props.common_parameters_extended:
                setattr(controller, prop_name, getattr(controller, prop_name))


    def home_alva_controller(controller):
        from ..properties.common_properties import CommonProperties 
        props = CommonProperties

        # Redirect to mixer node's PropertyGroup if controller is a mixer node
        if hasattr(controller, "bl_idname") and controller.bl_idname == 'mixer_type':
            controller.float_offset = 0
            controller.int_subdivisions = 0

            for choice in controller.parameters:
                for prop_name, prop in props.common_parameters:
                    try:
                        current_value = getattr(choice, prop_name)
                        if prop_name == "float_iris":
                            setattr(choice, prop_name, 100)
                        elif prop_name == "float_vec_color":
                            setattr(choice, prop_name, tuple(1.0 for _ in current_value))
                        elif prop_name in ["float_intensity", "float_pan", "float_tilt", "float_zoom"]:
                            setattr(choice, prop_name, 0)
                    except AttributeError:
                        print(f"Attribute {prop_name} not found in controller, skipping.")

        else:
            for prop_name, prop in props.common_parameters + props.common_parameters_extended:
                try:
                    current_value = getattr(controller, prop_name)
                    if prop_name == "float_iris":
                        setattr(controller, prop_name, 100)
                    elif prop_name == "float_vec_color":
                        setattr(controller, prop_name, tuple(1.0 for _ in current_value))
                    elif prop_name in [
                        "float_intensity", "float_pan", "float_tilt", "float_zoom", "float_strobe", 
                        "float_edge", "float_diffusion", "float_gobo_speed", "int_gobo_id", "int_prism"]:
                        setattr(controller, prop_name, 0)
                except AttributeError:
                    print(f"Attribute {prop_name} not found in controller, skipping.")
        

    def find_addresses(starting_universe, starting_address, channel_mode, total_lights):
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
    

    def simplify_channels_list(channels):
        channels.sort()
        combined_channels = []
        start = channels[0]
        end = channels[0]

        for c in channels[1:]:
            if c == end + 1:
                end = c
            else:
                if start == end:
                    combined_channels.append(str(start))
                else:
                    combined_channels.append(f"{start} Thru {end}")
                start = end = c

        if start == end:
            combined_channels.append(str(start))
        else:
            combined_channels.append(f"{start} Thru {end}")

        return " + ".join(combined_channels)


    #-------------------------------------------------------------------------------------------------------------------------------------------
    '''Text editor macros'''
    #-------------------------------------------------------------------------------------------------------------------------------------------
    def tokenize_macro_line(input_line):
        scene = bpy.context.scene
        if scene.add_underscores:
            try:
                input_line = Utils.add_underscores_to_keywords(input_line)
            except Exception as e:
                print(f"An error occurred while adding underscores to keywords: {e}")
                return None

        try:
            tokens = Utils.tokenize(input_line)
        except Exception as e:
            print(f"An error occurred while tokenizing macro string: {e}")
            return None

        if tokens is None:
            return None

        osc_keys = Dictionaries.osc_keys # Already lowercase
        results = []

        for token in tokens:
            token_lower = token.lower()  # Convert token to lowercase for comparison

            if token == '/':
                token = '\\'

            if token_lower in osc_keys:
                key_address = f"/eos/key/{token}"
                results.append((key_address, "1"))
                results.append((key_address, "0"))
            else:
                results.append(("/eos/newcmd", str(token)))
                
        # Check if the last token is "enter" and add it if it's not
        if tokens[-1].lower() != "enter" and scene.add_enter:
            results.append(("/eos/key/Enter", "1"))
            results.append(("/eos/key/Enter", "0"))
                
        return results

    def add_underscores_to_keywords(input_string):
        osc_keys = Dictionaries.osc_keys
        macro_buttons = Dictionaries.macro_buttons

        keywords_list = set(osc_keys + macro_buttons)
        
        for keyword in keywords_list:
            if not keyword:
                continue

            if "\\" in keyword:
                continue

            keyword_no_underscore = keyword.replace("_", " ")
            
            try:
                pattern = re.compile(re.escape(keyword_no_underscore), re.IGNORECASE)
                input_string = pattern.sub(keyword, input_string)
            except re.error as e:
                print(f"Error with keyword '{keyword_no_underscore}': {e}")
        
        return input_string
        
    def tokenize(input_string):
        replacements = ["{", "}", "[", "]", "<", ">"]
        clean_string = input_string
        for item in replacements:
            clean_string = clean_string.replace(item, "")
        
        tokens = re.findall(r'\d|[^\d\s]+', clean_string)
        return tokens


    #-------------------------------------------------------------------------------------------------------------------------------------------
    '''Find executor'''
    #-------------------------------------------------------------------------------------------------------------------------------------------
    def find_executor(scene: Scene, object: Object, executor_type: str) -> int:
        try:
            existing_prop = getattr(object, f"int_{executor_type}")
        except:
            print("An error occured in find_executor because of an invalid object or incorrect registration.")

        if existing_prop != 0 and (object.name == object.str_parent_name or isinstance(object, bpy.types.Scene)): # Middle check filters duplicates
            if isinstance(object, bpy.types.Scene) and executor_type not in ["start_macro", "end_macro"]:
                pass # We need to find a new one for Scene's event list and cue list
            else:
                return existing_prop # Don't find a new one, use the old one

        new_index = Utils.find_new_executor(scene, executor_type)

        return Utils.add_new_index(scene, new_index, object, executor_type)

    def find_new_executor(scene, executor_type):
        executor_map = {
            'event_list': 'event_list',
            'cue_list': 'cue_list',
            'start_macro': 'macro',
            'end_macro': 'macro',
            'start_preset': 'preset',
            'end_preset': 'preset',
        }

        base_name = executor_map[executor_type]
        
        range_min = getattr(scene, f"orb_{base_name}s_start")
        range_max = getattr(scene, f"orb_{base_name}s_end")

        index_range = list(range(range_min, range_max + 1))

        if executor_type in executor_map:
            return Utils.find_unused_index(scene, index_range, executor_map[executor_type])
        else:
            print(f"An error occurred within find_new_executor with argument {executor_type}. Returning default index")
            return DEFAULT_EXECUTOR_INDEX

    def get_all_executor_strip_names(scene):
        return [strip.name for strip in scene.sequence_editor.sequences if (strip.type == 'COLOR' or strip.type =='SOUND')]

    def find_unused_index(scene, range, base_attribute):
        strips = Utils.get_all_executor_strips(scene)
        used_indices = set()

        start_attr = f"int_start_{base_attribute}"
        end_attr = f"int_end_{base_attribute}"
        attr = f"int_{base_attribute}"

        for strip in strips:
            if hasattr(strip, start_attr):
                used_indices.add(getattr(strip, start_attr))
            if hasattr(strip, end_attr):
                used_indices.add(getattr(strip, end_attr))
            if hasattr(strip, attr):
                used_indices.add(getattr(strip, attr))

        for index in range:
            if index not in used_indices:
                return index

        return None
    
    def get_all_executor_strips(scene):
        strips = [strip for strip in scene.sequence_editor.sequences if (strip.type == 'COLOR' or strip.type =='SOUND')]
        strips.append(scene)
        return strips
    
    def add_new_index(scene, new_index, object, executor_type):
        try:
            setattr(object, f"int_{executor_type}", new_index)
        except:
            print("An error occured while trying to set property to new index.")
        return new_index 

    #-------------------------------------------------------------------------------------------------------------------------------------------
    '''Spy's make Eos macros'''
    #-------------------------------------------------------------------------------------------------------------------------------------------
    def make_eos_macro(macro_range, int_range, string):
        from ..spy import SorcererPython as spy

        spy.osc.press_lighting_key("live")
        for macro, custom_int in zip(range(macro_range[0] - 1, macro_range[1]), range(int_range[0], int_range[1] + 1)):
            if macro < 100000:
                spy.osc.press_lighting_key("learn")
                spy.osc.press_lighting_key("macro")
                time.sleep(.1)
                for digit in str(macro+1):
                    spy.osc.press_lighting_key(f"{digit}")
                    time.sleep(.1)
                spy.osc.press_lighting_key("enter")
                time.sleep(.1)

                formatted_string = string.replace("*", str(custom_int))
                spy.osc.lighting_command(formatted_string)
                time.sleep(.1)
                spy.osc.press_lighting_key("enter")
                spy.osc.press_lighting_key("learn")
                time.sleep(.2)
            else:
                print("Error: Macro indexes on ETC Eos only go up to 99,999.")
                return
            

def is_rendered_mode():
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D' and space.shading.type == 'RENDERED':
                        return True
    return False