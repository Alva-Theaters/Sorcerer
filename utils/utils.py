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
import mathutils
from ..utils.osc import OSC


class Utils:
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