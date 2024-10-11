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
    
from ..assets.dictionaries import Dictionaries 
from ..utils.osc import OSC


DEFAULT_EXECUTOR_INDEX = 1


class Utils:

    # properties_utils.py
    def register_properties(cls, properties, register=True):
        if register:
            for prop_name, prop_value in properties:
                setattr(cls, prop_name, prop_value)
        else:
            for prop_name, _ in reversed(properties):
                delattr(cls, prop_name)


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


    # event_utils.py
    def get_frame_rate(scene):
        return round((scene.render.fps / scene.render.fps_base), 2)
    

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
    

    def get_loc_rot(obj, use_matrix=False):
        x_pos, y_pos, z_pos, x_rot_rad, y_rot_rad, z_rot_rad  = Utils.get_original_loc_rot(obj, use_matrix)

        # Convert meters to feet.
        position_x = round(x_pos / .3048, 2)
        position_y = round(y_pos / .3048, 2)
        position_z = round(z_pos / .3048, 2)

        # Round and rotate x by 180 degrees (pi in radians) since cone facing up is the same as a light facing down.
        orientation_x = round(math.degrees(x_rot_rad + math.pi), 2)
        orientation_y = round(math.degrees(y_rot_rad), 2)
        orientation_z = round(math.degrees(z_rot_rad), 2)

        return position_x, position_y, position_z, orientation_x, orientation_y, orientation_z
    
    
    def get_original_loc_rot(obj, use_matrix=False):
        if use_matrix:
            depsgraph = bpy.context.evaluated_depsgraph_get()
            eval_obj = obj.evaluated_get(depsgraph)
            
            bpy.context.view_layer.update()
            
            matrix = eval_obj.matrix_world
            euler = matrix.to_euler('XYZ')

            # Convert radians to degrees for rotation
            x_rot_rad = euler.x
            y_rot_rad = euler.y
            z_rot_rad = euler.z

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


    # orb_utils.py
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


    # properties_utils.py
    def swap_preview_and_program(cue_list):
        if not cue_list.is_progressive:
            temp = cue_list.int_preview_index
            cue_list.int_preview_index = cue_list.int_program_index
            cue_list.int_program_index = temp
            
        else:
            cue_list.int_program_index = (cue_list.int_preview_index)
            cue_list.int_preview_index = (cue_list.int_program_index + 1)


    # audio_utils.py
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


    # cpvia_utils.py
    def color_object_to_tuple_and_scale_up(v):
        if type(v) == mathutils.Color:
            return (v.r * 100, v.g * 100, v.b * 100)

        else: 
            r, g, b = v
            return (r * 100, g * 100, b * 100)
        
        
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
            

# event_utils.py
def is_rendered_mode():
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D' and space.shading.type == 'RENDERED':
                        return True
    return False