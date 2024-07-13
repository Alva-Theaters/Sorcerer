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
import re
import ast
import math
import colorsys
import time
import bmesh
from bpy.types import PropertyGroup
from mathutils import Vector
from bpy.props import *
from bpy.types import NodeSocket, Operator, Menu
from nodeitems_utils import NodeCategory, NodeItem, register_node_categories, unregister_node_categories
from collections import defaultdict
from bpy.app.handlers import persistent
import mathutils
from functools import partial
import inspect
import numpy as np
import logging
from typing import List, Tuple


def SLI_assert_unreachable(*args):
    """This is the preferred error-handling method. It reports traceback, line number, and tells user this is 
    a Sorcerer bug, not a Blender bug, and to report it to Alva Theaters, not Blender. Use on try/excepts 
    and on final else's that should never be reached. Only use try/except on the most downstream functions
    to avoid cascading exceptions and useless line number references. Inspired by the Blender version of this
    in the C++ code."""
    caller_frame = inspect.currentframe().f_back
    caller_file = caller_frame.f_code.co_filename
    caller_line = caller_frame.f_lineno
    message = "Error found at {}:{}\nCode marked as unreachable has been executed. Please report bug to Alva Theaters.".format(caller_file, caller_line)
    print(message)
    

change_requests = []
stored_channels = set()


parameter_mapping = {
    "intensity": "float_intensity",
    "color": "float_vec_color",
    "pan": "float_pan",
    "tilt": "float_tilt",
    "strobe": "float_strobe",
    "zoom": "float_zoom",
    "iris": "float_iris",
    "diffusion": "float_diffusion",
    "edge": "float_edge",
    "gobo_id": "int_gobo_id",
    "gobo_speed": "float_gobo_speed",
    "prism": "int_prism",
    "pan_tilt": "float_vec_pan_tilt_graph"
}


eos_arguments_dict = {
    # Absolute Arguments
    "str_intensity_argument": "# at $ Enter",
    "str_pan_argument": "# Pan at $ Enter",
    "str_tilt_argument": "# Tilt at $ Enter",
    "str_diffusion_argument": "# Diffusion at $ Enter",
    "str_strobe_argument": "# Strobe at $ Enter",
    "str_zoom_argument": "# Zoom at $ Enter",
    "str_iris_argument": "# Iris at $ Enter",
    "str_edge_argument": "# Edge at $ Enter",
    "str_gobo_id_argument": "# Gobo_Select at $ Enter",
    "str_gobo_speed_argument": "# Gobo_Mode 191 Enter, # Gobo_Index/Speed at $ Enter",
    "str_changer_speed_argument": "# Changer_Speed at $ Enter",
    "str_prism_argument": "# Beam_Fx Select $ Enter",
    "str_rgb_argument": "# Red at $1 Enter, # Green at $2 Enter, # Blue at $3 Enter",
    "str_cmy_argument": "# Cyan at $1 Enter, # Magenta at $2 Enter, # Yellow at $3 Enter",
    "str_rgbw_argument": "# Red at $1 Enter, # Green at $2 Enter, # Blue at $3 Enter, # White at $4 Enter",
    "str_rgba_argument": "# Red at $1 Enter, # Green at $2 Enter, # Blue at $3 Enter, # Amber at $4 Enter",
    "str_rgbl_argument": "# Red at $1 Enter, # Green at $2 Enter, # Blue at $3 Enter, # Lime at $4 Enter",
    "str_rgbaw_argument": "# Red at $1 Enter, # Green at $2 Enter, # Blue at $3 Enter, # Amber at $4 Enter, # White at $5 Enter",
    "str_rgbam_argument": "# Red at $1 Enter, # Green at $2 Enter, # Blue at $3 Enter, # Amber at $4 Enter, # Mint at $5 Enter",

    # Raise Arguments
    "str_raise_intensity_argument": "# at + $ Enter",
    "str_raise_pan_argument": "# Pan at + $ Enter",
    "str_raise_tilt_argument": "# Tilt at + $ Enter",
    "str_raise_diffusion_argument": "# Diffusion at + $ Enter",
    "str_raise_strobe_argument": "# Strobe at + $ Enter",
    "str_raise_zoom_argument": "# Zoom at + $ Enter",
    "str_raise_iris_argument": "# Iris at + $ Enter",
    "str_raise_edge_argument": "# Edge at + $ Enter",
    "str_raise_gobo_id_argument": "# Gobo_Select at + $ Enter",
    "str_raise_gobo_speed_argument": "# Gobo_Mode 191 Enter, # Gobo_Index/Speed at + $ Enter",
    "str_raise_changer_speed_argument": "# Changer_Speed at + $ Enter",
    "str_raise_prism_argument": "# Beam_Fx Select + $ Enter",
    "str_raise_rgb_argument": "# Red at + $1 Enter, # Green at + $2 Enter, # Blue at + $3 Enter",
    "str_raise_cmy_argument": "# Cyan at + $1 Enter, # Magenta at + $2 Enter, # Yellow at + $3 Enter",
    "str_raise_rgbw_argument": "# Red at + $1 Enter, # Green at + $2 Enter, # Blue at + $3 Enter, # White at + $4 Enter",
    "str_raise_rgba_argument": "# Red at + $1 Enter, # Green at + $2 Enter, # Blue at + $3 Enter, # Amber at + $4 Enter",
    "str_raise_rgbl_argument": "# Red at + $1 Enter, # Green at + $2 Enter, # Blue at + $3 Enter, # Lime at + $4 Enter",
    "str_raise_rgbaw_argument": "# Red at + $1 Enter, # Green at + $2 Enter, # Blue at + $3 Enter, # Amber at + $4 Enter, # White at + $5 Enter",
    "str_raise_rgbam_argument": "# Red at + $1 Enter, # Green at + $2 Enter, # Blue at + $3 Enter, # Amber at + $4 Enter, # Mint at + $5 Enter",

    # Lower Arguments
    "str_lower_intensity_argument": "# at - $ Enter",
    "str_lower_pan_argument": "# Pan at - $ Enter",
    "str_lower_tilt_argument": "# Tilt at - $ Enter",
    "str_lower_diffusion_argument": "# Diffusion at - $ Enter",
    "str_lower_strobe_argument": "# Strobe at - $ Enter",
    "str_lower_zoom_argument": "# Zoom at - $ Enter",
    "str_lower_iris_argument": "# Iris at - $ Enter",
    "str_lower_edge_argument": "# Edge at - $ Enter",
    "str_lower_gobo_id_argument": "# Gobo_Select at - $ Enter",
    "str_lower_gobo_speed_argument": "# Gobo_Mode 191 Enter, # Gobo_Index/Speed at - $ Enter",
    "str_lower_changer_speed_argument": "# Changer_Speed at - $ Enter",
    "str_lower_prism_argument": "# Beam_Fx Select - $ Enter",
    "str_lower_rgb_argument": "# Red at - $1 Enter, # Green at - $2 Enter, # Blue at - $3 Enter",
    "str_lower_cmy_argument": "# Cyan at - $1 Enter, # Magenta at - $2 Enter, # Yellow at - $3 Enter",
    "str_lower_rgbw_argument": "# Red at - $1 Enter, # Green at - $2 Enter, # Blue at - $3 Enter, # White at - $4 Enter",
    "str_lower_rgba_argument": "# Red at - $1 Enter, # Green at - $2 Enter, # Blue at - $3 Enter, # Amber at - $4 Enter",
    "str_lower_rgbl_argument": "# Red at - $1 Enter, # Green at - $2 Enter, # Blue at - $3 Enter, # Lime at - $4 Enter",
    "str_lower_rgbaw_argument": "# Red at - $1 Enter, # Green at - $2 Enter, # Blue at - $3 Enter, # Amber at - $4 Enter, # White at - $5 Enter",
    "str_lower_rgbam_argument": "# Red at - $1 Enter, # Green at - $2 Enter, # Blue at - $3 Enter, # Amber at - $4 Enter, # Mint at - $5 Enter"
}


def color_profiles(self, context):
    items = [
        ('option_rgb', "RGB", "Red, Green, Blue"),
        ('option_rgba', "RGBA", "Red, Green, Blue, Amber"),
        ('option_rgbw', "RGBW", "Red, Green, Blue, White"),
        ('option_rgbaw', "RGBAW", "Red, Green, Blue, Amber, White"),
        ('option_rgbl', "RGBL", "Red, Green, Blue, Lime"),
        ('option_rgbam', "RGBAM", "Red, Green, Blue, Amber, Mint"),
        ('option_cmy', "CMY", "Cyan, Magenta, Yellow")
    ]
    
    return items


def object_identities(self, context):
    items = [
        ('Fixture', "Fixture", "This controls a single lighting fixture.", 'OUTLINER_OB_LIGHT', 0),
        ('Pan/Tilt Fixture', "Pan/Tilt", "Select this only if you intend to use Blender's pan/tilt gimbals or constraints.", 'ORIENTATION_GIMBAL', 1),
        ('Influencer', "Influencer", "This is a bit like 3D bitmapping. Fixtures inside this object will inherit this object's parameters. Changes are reverted when the object leaves.", 'CUBE', 2),
        ('Brush', "Brush", "Move this object over fixtures for a paint brush effect. Changes persist when the object leaves.", 'BRUSH_DATA', 3),
        ('Stage Object', "Stage Object", "Select the lights on a specific stage object by selecting the stage object, not a light-board group.", 'HOME', 4)
    ]
    
    return items


def scene_groups(self, context):
    items = []

    if context.scene.scene_props.scene_group_data:
        for group in context.scene.scene_props.scene_group_data:
            items.append((group.name, group.name, ""))
            
    return items


def get_sound_sources(self, context):
    items = []
    sequencer = context.scene.sequence_editor

    textual_numbers = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
                       "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty",
                       "twenty_one", "twenty_two", "twenty_three", "twenty_four", "twenty_five", "twenty_six", "twenty_seven", "twenty_eight", "twenty_nine", "thirty",
                       "thirty_one", "thirty_two"]

    if sequencer:
        items.extend([(strip.name, strip.name, "") for strip in sequencer.sequences_all if strip.type == 'SOUND'])
    
    for i in range(33):
        if i == 0:
            i += 1
        input_prop_name = f"input_{textual_numbers[i]}"
        input_display_name = f"Input {i}"
        input_description = f"Corresponds to Input {i} on the audio mixer"
        items.append((input_prop_name, input_display_name, input_description))

    for i in range(17):
        if i == 0:
            i += 1
        input_prop_name = f"bus_{textual_numbers[i]}"
        input_display_name = f"Bus {i}"
        input_description = f"Corresponds to Bus {i} on the audio mixer"
        items.append((input_prop_name, input_display_name, input_description))
        
    return items


def get_speakers(self, context):
    items = []
    textual_numbers = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
                       "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty",
                       "twenty_one", "twenty_two", "twenty_three", "twenty_four", "twenty_five", "twenty_six", "twenty_seven", "twenty_eight", "twenty_nine", "thirty",
                       "thirty_one", "thirty_two"]

    if sequencer:
        items.extend([(strip.name, strip.name, "") for strip in sequencer.sequences_all if strip.type == 'SOUND'])
    
    for i in range(17):
        if i == 0:
            i += 1
        input_prop_name = f"output_{textual_numbers[i]}"
        input_display_name = f"Output {i}"
        input_description = f"Corresponds to Output {i} on the audio mixer"
        items.append((input_prop_name, input_display_name, input_description))
            
    for i in range(7): 
        if i == 0:
            i += 1
        input_prop_name = f"dca_{textual_numbers[i]}"
        input_display_name = f"DCA {i}"
        input_description = f"Corresponds to DCA {i} on the audio mixer"
        items.append((input_prop_name, input_display_name, input_description))
            

# This stores the channel list for each set piece, group controller, strip, etc.
class ChannelListPropertyGroup(PropertyGroup):
    value: IntProperty()
    
    
def correct_argument_because_etc_is_weird(argument):
    return argument.replace(" at - 00 ", " at + 00 ")


def send_osc(address, argument):
    argument = correct_argument_because_etc_is_weird(argument)
    scene = bpy.context.scene.scene_props
    ip_address = scene.str_osc_ip_address
    port = scene.int_osc_port
    #print(argument)
    send_osc_string(address, ip_address, port, argument)


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
    formatted_input = re.sub(r'[()]', '', input_string)
    formatted_input = re.sub(r'(\d)-(\d)', r'\1 - \2', formatted_input)
    tokens = re.split(r'[,\s]+', formatted_input)

    channels = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        
        if token in ("through", "thru", "-", "tthru", "throu", "--", "por") and i > 0 and i < len(tokens) - 1:
            start = int(tokens[i-1])
            end = int(tokens[i+1])
            step = 1 if start < end else -1
            channels.extend(range(start, end + step, step))
            i += 2 
        elif token.isdigit():
            if (i == 0 or tokens[i-1] not in ("through", "thru", "-", "tthru", "throu", "--", "por")) and \
               (i == len(tokens) - 1 or tokens[i+1] not in ("through", "thru", "-", "tthru", "throu", "--", "por")):
                channels.append(int(token))
        i += 1
    
    return channels


def parse_mixer_channels(input_string):
    groups = re.findall(r'\(([^)]+)\)', input_string)
    if not groups:
        groups = [input_string]
        
    all_channels = []

    for group in groups:
        formatted_input = re.sub(r'(\d)-(\d)', r'\1 - \2', group)
        tokens = re.split(r'[,\s]+', formatted_input)
        
        channels = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            if token in ("through", "thru", "-", "tthru", "throu", "--", "por") and i > 0 and i < len(tokens) - 1:
                start = int(tokens[i-1])
                end = int(tokens[i+1])
                step = 1 if start < end else -1
                channels.extend(range(start, end + step, step))
                i += 3  
                continue 
            elif token.isdigit():
                if (i == 0 or tokens[i-1] not in ("through", "thru", "-", "tthru", "throu", "--", "por")) and \
                   (i == len(tokens) - 1 or tokens[i+1] not in ("through", "thru", "-", "tthru", "throu", "--", "por")):
                    channels.append(int(token))
            i += 1
        
        all_channels.append(tuple(channels))

    return all_channels


def get_light_rotation_degrees(light_name):
    """
    Returns the X (tilt) and Y (pan) rotation angles in degrees for a given light object,
    adjusting the range of pan to -270 to 270 degrees.
    
    :param light_name: Name of the light object in the scene.
    :return: Tuple containing the X (tilt) and Y (pan) rotation angles in degrees.
    """
    light_object = bpy.data.objects.get(light_name)

    if light_object and light_object.type == 'MESH':
        # Get the world matrix of the object.
        matrix = light_object.matrix_world

        # Convert the matrix to Euler angles (XYZ rotation order).
        euler = matrix.to_euler('XYZ')

        # Convert radians to degrees
        x_rot_deg = math.degrees(euler.x)  # Tilt
        y_rot_deg = math.degrees(euler.z)  # Pan seems to be on zed euler, not on y as y resolves to super tiny number.

        # Adjust the pan angle to extend the range to -270 to 270 degrees.
        if y_rot_deg > 90:
            y_rot_deg -= 360

        return x_rot_deg, y_rot_deg
    else:
        print("Light object named", light_name,"not found or is not a lamp.")
        return None, None

            
def manual_fixture_selection_updater(self, context):
    """This creates property group instances based on the manual text input for channels"""
    if self.str_manual_fixture_selection != "":
        channels_list = parse_channels(self.str_manual_fixture_selection)
        self.list_group_channels.clear()
        for chan in channels_list:
            item = self.list_group_channels.add()
            item.value = chan
                
                
def group_profile_updater(self, context):
    profile = bpy.context.scene.scene_props.scene_group_data.get(self.selected_profile_enum)

    # List of properties to update
    properties = [
        "pan_min", "pan_max", "tilt_min", "tilt_max", "zoom_min", "zoom_max", 
        "gobo_speed_min", "gobo_speed_max", "influence_is_on", "intensity_is_on", 
        "pan_tilt_is_on", "color_is_on", "diffusion_is_on", "strobe_is_on", 
        "zoom_is_on", "iris_is_on", "edge_is_on", "gobo_id_is_on", "prism_is_on", 
        "str_enable_strobe_argument", "str_disable_strobe_argument", 
        "str_enable_gobo_speed_argument", "str_disable_gobo_speed_argument", 
        "str_gobo_id_argument", "str_gobo_speed_value_argument", 
        "str_enable_prism_argument", "str_disable_prism_argument", "color_profile_enum"
    ]

    for prop in properties:
        setattr(self, prop, getattr(profile, prop))
        
        
def call_fixtures_updater(self, context):
    bpy.ops.viewport.call_fixtures_operator()
        
        
class RaiseChannels(bpy.types.PropertyGroup):
    chan: PointerProperty(type=bpy.types.Object)
    original_influence: FloatProperty()
    original_influence_color: FloatVectorProperty()
    
        
class InfluencerList(bpy.types.PropertyGroup):
    parameter: StringProperty()
    raise_channels: CollectionProperty(type=RaiseChannels)


###################
# HARMONIZER
###################
class HarmonizerBase:
    INFLUENCER = 'influencer'
    CHANNEL = 'channel'
    GROUP = 'group'
    MIXER = 'mixer'
    PAN_TILT = 'pan_tilt'


change_requests = []


class HarmonizerPublisher(HarmonizerBase):
          
    def format_channel_and_value(self, c, v):
        """
        This function formats the channel and value numbers as string and then formats them
        in a way the console will understand (by adding a 0 in front of numbers 1-9.)
        """
        c = str(c)
        v = int(v)
        
        if v >= 0 and v < 10:
            v = f"0{v}"
        elif v < 0 and v > -10:
            v = f"-0{-v}"
        else:
            v = str(v)

        return c, v
    
    
    def format_channel(self, c):
        c = str(c)

        return c
    

    def format_value(self, v):
        """
        This function formats the channel and value numbers as string and then formats them
        in a way the console will understand (by adding a 0 in front of numbers 1-9.)
        """
        v = int(v)
        
        if v >= 0 and v < 10:
            v = f"0{v}"
        elif v < 0 and v > -10:
            v = f"-0{-v}"
        else:
            v = str(v)
        return v
        
        
    def form_osc(self, c, p, v, i, a):
        """
        This function converts cpvia into (address, argument) tuples.

        Parameters:
        cpvia: channel, parameter, value, influence, argument template.

        Returns:
        messages: A list of (address, argument) tuples.
        """
        address = bpy.context.scene.scene_props.str_command_line_address

        color_profiles = {
            # Absolute Arguments
            "rgb": ["$1", "$2", "$3"],
            "cmy": ["$1", "$2", "$3"],
            "rgbw": ["$1", "$2", "$3", "$4"],
            "rgba": ["$1", "$2", "$3", "$4"],
            "rgbl": ["$1", "$2", "$3", "$4"],
            "rgbaw": ["$1", "$2", "$3", "$4", "$5"],
            "rgbam": ["$1", "$2", "$3", "$4", "$5"],

            # Raise Arguments
            "raise_rgb": ["$1", "$2", "$3"],
            "raise_cmy": ["$1", "$2", "$3"],
            "raise_rgbw": ["$1", "$2", "$3", "$4"],
            "raise_rgba": ["$1", "$2", "$3", "$4"],
            "raise_rgbl": ["$1", "$2", "$3", "$4"],
            "raise_rgbaw": ["$1", "$2", "$3", "$4", "$5"],
            "raise_rgbam": ["$1", "$2", "$3", "$4", "$5"],

            # Lower Arguments
            "lower_rgb": ["$1", "$2", "$3"],
            "lower_cmy": ["$1", "$2", "$3"],
            "lower_rgbw": ["$1", "$2", "$3", "$4"],
            "lower_rgba": ["$1", "$2", "$3", "$4"],
            "lower_rgbl": ["$1", "$2", "$3", "$4"],
            "lower_rgbaw": ["$1", "$2", "$3", "$4", "$5"],
            "lower_rgbam": ["$1", "$2", "$3", "$4", "$5"]
        }

        if p not in color_profiles:
            c, v = self.format_channel_and_value(c, v)
            address = address.replace("#", c).replace("$", v)
            argument = a.replace("#", c).replace("$", v)
        else:
            formatted_values = [self.format_value(val) for val in v]

            c = self.format_channel(c)
            argument = a.replace("#", c)
            
            for i, fv in enumerate(formatted_values):
                argument = argument.replace(color_profiles[p][i], str(fv))

        return address, argument
    
    
    def send_cpvia(self, c, p, v, i, a):
        """
        Decides whether to send osc now (we are not playing back) or later (we are playing back).

        Parameters:
        cpvia: channel, parameter, value, influence, argument template.

        This function does not return a value.
        """
        if bpy.context.scene.scene_props.is_playing or bpy.context.scene.scene_props.in_frame_change:
            global change_requests
            change_requests.append((c, p, v, i, a))  
        else:
            address, argument = self.form_osc(c, p, v, i, a)  # Should return 2 strings
            send_osc(address, argument)
            
            
    def find_objects(self, chan):
        relevant_objects = []
        for obj in bpy.data.objects:
            if obj.int_object_channel_index == chan and chan != 1:
                relevant_objects.append(obj)
                pass
            try:
                number = find_int(obj.name)
                if number == int(chan):
                    relevant_objects.append(obj)
            except:
                pass
        return relevant_objects
            
            
    def send_value_to_three_dee(self, parent, chan, param, val):
        """
        Adds material to relevant objects in 3d scene and sets material as that intensity or color.

        Parameters:
        val: Either float or tuple, depending on intensity or color

        This function does not return a value.
        """
        def find_val_type(val):
            if isinstance(val, (tuple, list)):
                return "color"
            elif isinstance(val, (int, float)):
                return "intensity"
            else:
                raise ValueError("Invalid value type")

        val_type = find_val_type(val)
        objects = self.find_objects(chan)
        
        if not objects:
            return
        
        if val_type == "intensity":
            for obj in objects:
                # Ensure the object has a material slot and create one if it doesn't
                if not hasattr(obj.data, "materials"):
                    continue
                
                if not obj.data.materials:
                    mat = bpy.data.materials.new(name="Intensity_Material")
                    obj.data.materials.append(mat)
                else:
                    mat = obj.data.materials[0]

                # Enable 'Use nodes'
                if not mat.use_nodes:
                    mat.use_nodes = True
                
                nodes = mat.node_tree.nodes
                links = mat.node_tree.links
                
                # Find existing emission node or create a new one
                emission = None
                for node in nodes:
                    if node.type == 'EMISSION':
                        emission = node
                        break
                if not emission:
                    emission = nodes.new(type='ShaderNodeEmission')
                    # Add material output node and link it to emission node
                    output = nodes.new(type='ShaderNodeOutputMaterial')
                    links.new(emission.outputs['Emission'], output.inputs['Surface'])

                # Get the current value
                input = emission.inputs['Strength']
                current_val = input.default_value
                    
                if param == "raise_intensity":
                    val = current_val + val * 0.01
                elif param == "lower_intensity":
                    val = current_val - val * 0.01
                else:
                    val *= 0.01
                    
                if val > 1:
                    val = 1
                elif val < 0:
                    val = 0
                    
                input.default_value = val

        elif val_type == "color":
            for obj in objects:
                if not hasattr(obj.data, "materials"):
                    continue
                
                # Ensure the object has a material slot and create one if it doesn't
                if not obj.data.materials:
                    mat = bpy.data.materials.new(name="Color_Material")
                    obj.data.materials.append(mat)
                else:
                    mat = obj.data.materials[0]

                # Enable 'Use nodes'
                if not mat.use_nodes:
                    mat.use_nodes = True
                
                nodes = mat.node_tree.nodes
                links = mat.node_tree.links

                # Find existing emission node or create a new one
                emission = None
                for node in nodes:
                    if node.type == 'EMISSION':
                        emission = node
                        break
                if not emission:
                    emission = nodes.new(type='ShaderNodeEmission')
                    # Add material output node and link it to emission node
                    output = nodes.new(type='ShaderNodeOutputMaterial')
                    links.new(emission.outputs['Emission'], output.inputs['Surface'])

                # Set the color value
                scaled_val = tuple(component * 0.01 for component in val)
                emission.inputs['Color'].default_value = (*scaled_val, 1)  # Assuming val is an (R, G, B) tuple

        else:
            SLI_assert_unreachable()

        
"""This should house all logic for mapping sliders and other inputs to fixture-appropriate values"""
class HarmonizerMappers(HarmonizerBase):
    """
    Finds the relevant min/max values for a specified parameter p
    
    Arguments:
        parent: The parent object/node/strip
        p: The property type, should be pan, tilt, zoom, gobo_speed, or pan_tilt only
        
    Returns:
        min_value, max_value: 2 integers
    """
    def find_my_min_max(self, parent, chan, type, p):  
        try:
            min_property = f"{p}_min"
            max_property = f"{p}_max"
            min_value = find_my_patch(parent, chan, type, min_property)
            max_value = find_my_patch(parent, chan, type, max_property)
            return min_value, max_value
        except AttributeError as e:
            print(f"Error in find_my_min_max: {e}")
            return None, None

         
    def map_value(self, parent, chan, p, unmapped_value, type):
        min_val, max_val = self.find_my_min_max(parent, chan, type, p)
        if p in ["pan", "tilt", "zoom", "gobo_speed"]:
            if min_val <= 0 and max_val >= 0:
                # Normalizing around zero
                if unmapped_value == 0:
                    mapped_value = 0
                elif unmapped_value > 0:
                    normalized_value = unmapped_value / 100
                    mapped_value = normalized_value * max_val
                else:
                    normalized_value = unmapped_value / 100
                    mapped_value = normalized_value * abs(min_val)
            else:
                # Non-symmetrical range
                range_val = max_val - min_val
                # Map the slider value from -100 to 100 to the min_val to max_val range
                if unmapped_value >= 0:
                    normalized_value = unmapped_value / 100
                    mapped_value = normalized_value * (max_val - min_val) + min_val
                else:
                    normalized_value = (unmapped_value + 100) / 200
                    mapped_value = (normalized_value * (max_val - min_val)) + min_val
            return mapped_value
        else: SLI_assert_unreachable()
    
       
class HarmonizerMixer(HarmonizerBase):
    """This should house all logic for mixing values with the mixers"""
    
    def subdivide_values(self, subdivisions: int, values: List[float]) -> List[float]:
        """Subdivide the values based on the number of subdivisions."""
        if subdivisions > 0:
            for _ in range(subdivisions):
                values += values
        return values

    def sort(self, channels: List[int], values: List[float]) -> Tuple[List[int], List[float]]:
        """Sort channels and values together."""
        sorted_channels_values = sorted(zip(channels, values))
        sorted_channels, sorted_values = zip(*sorted_channels_values)
        return list(sorted_channels), list(sorted_values)

    def subdivide_sort(self, subdivisions: int, sorted_channels: List[int], sorted_values: List[float]) -> Tuple[np.ndarray, List[float]]:
        """Subdivide and sort the channels and values."""
        if subdivisions > 0:
            expanded_values = []
            expanded_channels = []
            for channel, value in zip(sorted_channels, sorted_values):
                for _ in range(subdivisions + 1):
                    expanded_values.append(value)
                    expanded_channels.append(channel)
            sorted_values = expanded_values
            sorted_channels = np.linspace(expanded_channels[0], expanded_channels[-1], len(expanded_values))
        return sorted_channels, sorted_values

    def interpolate(self, sorted_channels: np.ndarray, channels: List[int], offset: float) -> np.ndarray:
        """Interpolate values over the given channels with an offset."""
        min_channel = sorted_channels[0]
        max_channel = sorted_channels[-1]
        channel_range = max_channel - min_channel
        num_interpolation_points = len(channels)
        interpolation_points = np.linspace(min_channel, max_channel, num_interpolation_points, endpoint=False) + offset * channel_range
        interpolation_points = np.mod(interpolation_points - min_channel, channel_range) + min_channel
        return interpolation_points

    def interpolate_color(self, 
                sorted_values: List[Tuple[float, float, float]], interpolation_points: np.ndarray, 
                sorted_channels: np.ndarray) -> List[Tuple[float, float, float]]:
        """Interpolate color values across the channels."""
        reds = [color[0] for color in sorted_values]
        greens = [color[1] for color in sorted_values]
        blues = [color[2] for color in sorted_values]
        mixed_reds = np.interp(interpolation_points, sorted_channels, reds)
        mixed_greens = np.interp(interpolation_points, sorted_channels, greens)
        mixed_blues = np.interp(interpolation_points, sorted_channels, blues)
        mixed_values = [(r * 100, g * 100, b * 100) for r, g, b in zip(mixed_reds, mixed_greens, mixed_blues)]
        return mixed_values

    def patternize(self, sorted_values: List[float], channels: List[int], offset: float) -> List[float]:
        """Create a repeating pattern with an offset."""
        num_values = len(sorted_values)
        mixed_values = [sorted_values[i % num_values] for i in range(len(channels))]
        offset_steps = int(offset * len(channels))
        mixed_values = mixed_values[-offset_steps:] + mixed_values[:-offset_steps]
        return mixed_values

    def mix_values(self, mode, 
                   sorted_channels: np.ndarray, sorted_values: List[float], subdivisions: int, 
                   channels: List[int], param_mode: str, offset: float, parent) -> List[float]:
        """Mix the values based on the mode and parameter settings."""
        if mode == "option_gradient":
            sorted_channels, sorted_values = self.subdivide_sort(subdivisions, sorted_channels, sorted_values)
            if len(sorted_channels) == 1:
                return [sorted_values[0]] * len(channels)
            else:
                interpolation_points = self.interpolate(sorted_channels, channels, offset)
                if param_mode == "color":
                    return self.interpolate_color(sorted_values, interpolation_points, sorted_channels)
                else:
                    return list(np.interp(interpolation_points, sorted_channels, sorted_values))
        elif mode == "option_pattern":
            mixed_values = self.patternize(sorted_values, channels, offset)
            if param_mode == "color":
                mixed_values = [(r * 100, g * 100, b * 100) for r, g, b in mixed_values]
            return mixed_values
        elif mode == "option_pose":
            poses = parent.parameters
            num_poses = len(poses)
            motor_node = self.find_motor_node(parent)
            progress = (motor_node.float_progress * .1)
            
            # Ensure pose_index is within range
            pose_index = int(progress * (num_poses - 1)) % num_poses
            next_pose_index = (pose_index + 1) % num_poses
            blend_factor = (progress * (num_poses - 1)) % 1
            
            mixed_values = {
                'float_intensity': [],
                'float_vec_color': [],
                'float_pan': [],
                'float_tilt': [],
                'float_zoom': [],
                'float_iris': []
            }

            for param in mixed_values.keys():
                value1 = getattr(poses[pose_index], param)
                value2 = getattr(poses[next_pose_index], param)

                if param == 'float_vec_color':
                    mixed_value = tuple(v1 * (1 - blend_factor) + v2 * blend_factor for v1, v2 in zip(value1, value2))
                    mixed_values[param] = [(mixed_value[0] * 100, mixed_value[1] * 100, mixed_value[2] * 100)] * len(channels)
                else:
                    mixed_value = value1 * (1 - blend_factor) + value2 * blend_factor
                    mixed_values[param] = [mixed_value] * len(channels)
            
            if param_mode == 'color':
                return mixed_values['float_vec_color']
            else:
                return mixed_values[f'float_{param_mode}']
        else:
            SLI_assert_unreachable()

    def find_motor_node(self, mixer_node: bpy.types.Node) -> bpy.types.Node:
        """Find the motor node connected to the mixer node."""
        if not mixer_node.inputs:
            return None
        for input_socket in mixer_node.inputs:
            if input_socket.is_linked:
                for link in input_socket.links:
                    if link.from_socket.bl_idname == 'MotorOutputType':
                        connected_node = link.from_node
                        if connected_node.bl_idname == 'motor_type':
                            return connected_node
        return None

    def scale(self, parent: bpy.types.Node, param_mode: str, mixed_values: List[float]) -> List[float]:
        """Scale the mixed values based on the motor node's scale."""
        motor_node = self.find_motor_node(parent)
        if motor_node:
            float_scale = motor_node.float_scale
            if param_mode == "color":
                return [(r * float_scale, g * float_scale, b * float_scale) for r, g, b in mixed_values]
            else:
                return [v * float_scale for v in mixed_values]
        return mixed_values
        
    def mix_my_values(self, parent, param):
        """Receives a bpy object mesh, parent, and returns three lists for channels list (c), parameters list (p), 
           and values list (v)"""
        
        cumulative_c = []
        cumulative_p = []
        cumulative_v = []
        
        if parent.str_manual_fixture_selection == "":
            item = bpy.context.scene.scene_props.scene_group_data.get(parent.selected_group_enum)
            channels_list = item.channels_list
            channels = [item.chan for item in channels_list]
            c, p, v = self.append_mixer_cpv(parent, param, channels)
            cumulative_c.extend(c)
            cumulative_p.extend(p)
            cumulative_v.extend(v)
            return cumulative_c, cumulative_p, cumulative_v
        else:
            channel_tuples = parse_mixer_channels(parent.str_manual_fixture_selection)
            for single_tuple in channel_tuples:
                channels = list(single_tuple)
                c, p, v = self.append_mixer_cpv(parent, param, channels)
                cumulative_c.extend(c)
                cumulative_p.extend(p)
                cumulative_v.extend(v)
            return cumulative_c, cumulative_p, cumulative_v
        
        
    def append_mixer_cpv(self, parent, parameter, channels):
        values_list = parent.parameters
        offset = parent.float_offset * 0.5
        subdivisions = parent.int_subdivisions
        mode = parent.mix_method_enum
        param_mode = parameter
        param = parameter
        if parameter == "color":
            param = "vec_color"
        param = f"float_{param}"
        
        # Establish and then subdivide values list
        values = [getattr(choice, param) for choice in values_list]
        values = self.subdivide_values(subdivisions, values)
        
        # Establish channels list, sort channels and values list, mix values, and then scale values
        sorted_channels, sorted_values = self.sort(channels, values)
        mixed_values = self.mix_values(mode, sorted_channels, sorted_values, subdivisions, channels, param_mode, offset, parent)
        scaled_values = self.scale(parent, param_mode, mixed_values)
        
        # Establish parameters list
        p = [parameter for _ in channels]
        
        # Return c, p, v lists
        return list(channels), p, list(scaled_values)

    
class ColorSplitter(HarmonizerBase):
    def calculate_closeness(self, rgb_input, target_rgb, sensitivity=1.0):
        diff = sum(abs(input_c - target_c) for input_c, target_c in zip(rgb_input, target_rgb))
        normalized_diff = diff / (300 * sensitivity)
        closeness_score = max(0, min(1, 1 - normalized_diff))
        return closeness_score


    def rgb_converter(self, red, green, blue):
        return red, green, blue
        
            
    def rgba_converter(self, red, green, blue):
        # Calculate the influence of red and the lack of green on the amber component.
        red_influence = red / 100
        green_deficit = 1 - abs(green - 50) / 50
        amber_similarity = red_influence * green_deficit
        white_similarity = min(red, green, blue) / 100
        
        if amber_similarity > white_similarity:
            amber = round(amber_similarity * 100)
        else:
            amber = round(75 * white_similarity)
            
        return red, green, blue, amber

        
    def rgbw_converter(self, red, green, blue):
        white_similarity = min(red, green, blue) / 100
        white_peak = 75 + (25 * white_similarity)  # Peaks at 100 for pure white.

        white = round(white_peak * white_similarity)
        
        return red, green, blue, white


    def rgbaw_converter(self, red, green, blue):
        amber_sensitivity=1.0
        white_sensitivity=1.0
        
        # Define pure color values for comparison
        pure_colors = {
            'amber': (100, 50, 0),
            'white': (100, 100, 100),
            'red': (100, 0, 0),
            'green': (0, 100, 0),
            'blue': (0, 0, 100)
        }
        
        # Calculate closeness scores for each target color, specifying sensitivity where needed.
        scores = {}
        for color, rgb in pure_colors.items():
            if color == 'amber':
                scores[color] = calculate_closeness((red, green, blue), rgb, amber_sensitivity)
            elif color == 'white':
                scores[color] = calculate_closeness((red, green, blue), rgb, white_sensitivity)
            else:
                scores[color] = calculate_closeness((red, green, blue), rgb)
                
        amber = round(scores['amber'] * 100)
        white = round(scores['white'] * 100)

        return red, green, blue, amber, white


    def rgbl_converter(self, red, green, blue):
        lime = 0
        
        # Lime peaks at 100 for yellow (100, 100, 0) and white (100, 100, 100).
        if red == 100 and green == 100:
            lime = 100
        # For other combinations, calculate lime based on the lesser of red and green, but only if blue is not dominant.
        elif blue < red and blue < green:
            lime = round((min(red, green) / 100) * 100)
        
        return red, green, blue, lime


    def rgbam_converter(self, red, green, blue):
        # Handle exact targets with conditional logic.
        if (red, green, blue) == (0, 0, 0):  # Black
            amber, mint = 0, 0
        elif (red, green, blue) == (100, 0, 0):  # Pure Red
            amber, mint = 0, 0
        elif (red, green, blue) == (0, 100, 0):  # Pure Green
            amber, mint = 0, 0
        elif (red, green, blue) == (0, 0, 100):  # Pure Blue
            amber, mint = 0, 0
        elif (red, green, blue) == (100, 100, 100):  # White
            amber, mint = 100, 100
        elif (red, green, blue) == (58, 100, 14):  # Specific Mint Peak
            amber, mint = 0, 100
        elif (red, green, blue) == (100, 50, 0):  # Specific Amber Peak
            amber, mint = 100, 0
        else:
            proximity_to_white = min(red, green, blue) / 100
            amber = round(100 * proximity_to_white)
            mint = round(100 * proximity_to_white)
            
            # Adjust for proximity to the specific mint peak color.
            if green == 100 and red > 0 and blue > 0:
                mint_peak_proximity = min(red / 58, blue / 14)
                mint = round(100 * mint_peak_proximity)
        
        return red, green, blue, amber, mint


    def cmy_converter(self, red, green, blue):
        # Define a tolerance for near-maximum RGB values to treat them as 1.
        tolerance = 0.01
        red_scaled = red / 100.0
        green_scaled = green / 100.0
        blue_scaled = blue / 100.0

        # Apply the tolerance to treat near-maximum values as 1.
        cyan = int((1 - min(red_scaled + tolerance, 1)) * 100)
        magenta = int((1 - min(green_scaled + tolerance, 1)) * 100)
        yellow = int((1 - min(blue_scaled + tolerance, 1)) * 100)

        return cyan, magenta, yellow

        
    def split_color(self, parent, c, p, v, type):
        """
        Splits the input (r, g, b) tuple for value (v) into tuples like (r, g, b, a, m)
        for the value entries and updates the parameter (p) value for each entry to the 
        color profile (pf) enumerator option found with find_my_patch().
        
        This function prepares the parameters and values for later processing by the 
        find_my_argument() function, ensuring that the correct argument is formed based 
        on the received v tuple. The updated parameter p indirectly reflects the 
        color_profile choice, allowing the publisher to interpret the v tuple correctly.
        
        Parameters:
            parent: The parent controller object.
            c: The channel list.
            p: The parameter, as list
            v: The value list.
            type: The controller type.

        Returns:
            new_p: The updated parameter list.
            new_v: The updated value list.
        """
        new_p = []
        new_v = []
        
        for chan, val in zip(c, v):  # 4chan lol
            pf = find_my_patch(parent, chan, type, "color_profile_enum") # this returns option_rgb, option_rgba, etc.
            profile_converters = {
                # Absolute Arguments
                'rgba': (self.rgba_converter, 4),
                'rgbw': (self.rgbw_converter, 4),
                'rgbaw': (self.rgbaw_converter, 5),
                'rgbl': (self.rgbl_converter, 4),
                'cmy': (self.cmy_converter, 3),
                'rgbam': (self.rgbam_converter, 5),

                # Raise Arguments
                'raise_rgba': (self.rgba_converter, 4),
                'raise_rgbw': (self.rgbw_converter, 4),
                'raise_rgbaw': (self.rgbaw_converter, 5),
                'raise_rgbl': (self.rgbl_converter, 4),
                'raise_cmy': (self.cmy_converter, 3),
                'raise_rgbam': (self.rgbam_converter, 5),

                # Lower Arguments
                'lower_rgba': (self.rgba_converter, 4),
                'lower_rgbw': (self.rgbw_converter, 4),
                'lower_rgbaw': (self.rgbaw_converter, 5),
                'lower_rgbl': (self.rgbl_converter, 4),
                'lower_cmy': (self.cmy_converter, 3),
                'lower_rgbam': (self.rgbam_converter, 5)
            }

            mode = pf.replace("option_", "")
            corrected_key = p[0].replace("color", mode)
            
            publisher = HarmonizerPublisher()
            publisher.send_value_to_three_dee(parent, chan, corrected_key, val)

            if corrected_key in ['rgb', 'raise_rgb', 'lower_rgb']:
                new_p.append(corrected_key)
                new_v.append(val)
                
            elif corrected_key in profile_converters:
                converter, num_values = profile_converters[corrected_key]
                converted_values = converter(*val[:3])
                
                new_p.append(corrected_key)
                new_v.append(converted_values[:num_values])
            else: raise ValueError(f"Unknown color profile: {corrected_key}")

        return new_p, new_v
    
        
number_to_add_if_null = 1
    
    
"""Tries to find an integer inside the string and returns it as an int. 
   Returns 0 if no integer is found."""
def find_int(string):
    match = re.search(r'\d+', string)
    return int(match.group()) if match else number_to_add_if_null
    
    
class HarmonizerFinders(HarmonizerBase): ## This must cater to individual fixtures
    def __init__(self):
        super().__init__()
    
    def find_my_argument_template(self, parent, chan, param, type):
        if bpy.context.scene.scene_props.console_type_enum == "option_eos":
            return eos_arguments_dict.get(f"str_{param}_argument", "Unknown Argument")

    def find_my_controller_type(self, parent):
        """
        Function called by find_my_channels_and_[parameter values] functions to find controller type.

        Parameters:
        parent: The object from which this function is called. Should only be a mesh or known node type.
        
        Returns:
        type: The controller type in string, to be used to determine how to find channel list.
        """    
        if hasattr(parent, "type"):
            if parent.type == 'MESH':
                if hasattr(parent, "object_identities_enum"):
                    return parent.object_identities_enum
                else: SLI_assert_unreachable()
            elif parent.type == 'COLOR':  # Color strip
                return "strip"
            elif parent.type == 'CUSTOM':  
                controller_types = {
                'group_controller_type': "group",
                'mixer_type': "mixer",
                }
                return controller_types.get(parent.bl_idname, None)
        else: 
            SLI_assert_unreachable()
            
            
    def is_torus(self, mesh):
        # Analyze the bounding box dimensions
        bbox = mesh.bound_box
        dims = [Vector(bbox[i]) - Vector(bbox[i + 4]) for i in range(4)]
        dims = [dim.length for dim in dims]

        # Check if the dimensions are roughly equal (more like a sphere/torus) or significantly different (more like a cube)
        threshold = 0.1  # Adjust this threshold as needed
        if all(abs(dims[i] - dims[j]) < threshold for i in range(4) for j in range(i + 1, 4)):
            print("Is torus")
            return True
        print("Is not torus")
        return False
        
    
    def is_inside_mesh(self, obj, mesh_obj):
        #torus = self.is_torus(mesh_obj)
        #torus = False
        
        #if not torus:
        # Transform the object's location into the mesh object's local space.
        obj_loc_local = mesh_obj.matrix_world.inverted() @ obj.location

        # Get the local bounding box corners of the mesh object.
        bbox_corners_local = [Vector(corner) for corner in mesh_obj.bound_box]

        # Calculate the min and max bounding box corners in local space.
        bbox_min = Vector((min(corner.x for corner in bbox_corners_local),
                           min(corner.y for corner in bbox_corners_local),
                           min(corner.z for corner in bbox_corners_local)))
        bbox_max = Vector((max(corner.x for corner in bbox_corners_local),
                           max(corner.y for corner in bbox_corners_local),
                           max(corner.z for corner in bbox_corners_local)))
        inside = all(bbox_min[i] <= obj_loc_local[i] <= bbox_max[i] for i in range(3))

        return inside

        
#        else:
#            depsgraph = bpy.context.evaluated_depsgraph_get()
#            evaluated_obj = mesh_obj.evaluated_get(depsgraph)

#            # Ensure the evaluated object has mesh data
#            if not evaluated_obj or not evaluated_obj.data or not hasattr(evaluated_obj.data, 'polygons'):
#                print(f"Error: Object '{mesh_obj.name}' has no evaluated mesh data.")
#                return False

#            # Transform the object's location into the mesh object's local space
#            obj_loc_local = evaluated_obj.matrix_world.inverted() @ obj.location

#            # Find the closest point on the mesh
#            success, closest, normal, _ = evaluated_obj.closest_point_on_mesh(obj_loc_local)
#            
#            if not success:
#                return False

#            # Determine if the point is inside the mesh
#            direction = closest - obj_loc_local
#            inside = direction.dot(normal) > 0

#            return inside
    

    def find_influencer_current_channels(self, parent):
        """Receives a bpy object mesh, parent, and returns a set representing channels within that mesh"""
        lights_inside = {obj for obj in bpy.data.objects if obj.type == 'MESH' and not obj.hide_viewport and self.is_inside_mesh(obj, parent)}
        lights_inside = {obj for obj in lights_inside if obj.name != parent.name}
        return lights_inside

        
    def get_list_by_parameter(self, parent, parameter):
        """Receives parent, object, and parameter, string and returns parameter, string."""
        for inf_list in parent.influencer_list:
            if inf_list.parameter == parameter:
                return inf_list
        new_list = parent.influencer_list.add()
        new_list.parameter = parameter
        return new_list
    

    def find_my_restore_values(self, channels_to_restore, p, context):
        restore_values = []
        for chan in channels_to_restore:
            attribute_name = f"prev_{p}"
            if hasattr(chan, attribute_name):
                restore_values.append(getattr(chan, attribute_name))
            else:
                restore_values.append(0 if p != "color" else (0, 0, 0))
        return restore_values
    
    
    def color_object_to_tuple(self, v):
        """
        This function converts an RGB color object into a tuple.
        """
        #print(f"V: {v}")
        if type(v) == mathutils.Color:
            return (v.r * 100, v.g * 100, v.b * 100)
        
        else: 
            r, g, b = v
            return (r * 100, g * 100, b * 100)


    def find_my_value(self, parent, p, type, chan):
        """Recieves a bpy object mesh (parent), and parameter, and returns integers in a [list]
           This is for single fixtures."""
        attribute_name = parameter_mapping.get(p)
        if attribute_name:
            unmapped_value = getattr(parent, attribute_name)
            if p == "color":
                unmapped_value = self.color_object_to_tuple(unmapped_value)
            elif p in ["pan", "tilt", "zoom", "gobo_speed", "pan_tilt"]:
                mapping = HarmonizerMappers()
                try: 
                    value = mapping.map_value(parent, chan, p, unmapped_value, type)
                    return value
                except AttributeError:
                    print("Error in find_my_value when attempting to call map_value.")
                    
            return unmapped_value
        else:
            return None
        
    def find_channels_list(self, parent):
        """Recieves a bpy object and returns list of channels, which are ints,"""
        item = bpy.context.scene.scene_props.scene_group_data.get(parent.selected_group_enum)
        channels_list = []
        
        if parent.str_manual_fixture_selection == "":
            for channel in item.channels_list:
                channels_list.append(channel.chan)
        else:
            for channel in parent.list_group_channels:
                channels_list.append(channel.value)
        return channels_list


    def trigger_downstream_nodes(self, parent, attribute_name, new_value):
        """Receives a bpy object and returns nothing"""
        for output_socket in parent.outputs:
            if output_socket.bl_idname == 'LightingOutputType':
                for link in output_socket.links:
                    connected_node = link.to_socket.node
                    if connected_node.bl_idname == "group_controller_type":
                        setattr(connected_node, attribute_name, new_value)
        

    def find_my_group_values(self, parent, p, type):
        """Recieves a bpy object mesh (parent), parameter, and controller_type, and returns three lists for channels list (c), parameters list, and values list (v)"""
        # Use effects to mix up values inside a group, or simply return a simple value
        c = []
        param = []
        v = []
        
        attribute_name = parameter_mapping.get(p)
        if attribute_name:  # Find and map value
            new_value = getattr(parent, attribute_name)
            
            if p == "color":
                new_value = self.color_object_to_tuple(new_value)
            
            if parent.type == 'CUSTOM':
                self.trigger_downstream_nodes(parent, attribute_name, new_value)
            
            channels_list = []
            channels_list = self.find_channels_list(parent)
            
            mapping = HarmonizerMappers()
            for channel in channels_list:
                c.append(channel)
                param.append(p)
                if p in ["pan", "tilt", "zoom", "gobo_speed", "pan_tilt"]:
                    value_to_add = mapping.map_value(parent, channel, p, new_value, type)
                    v.append(value_to_add)
                else:
                    v.append(new_value)
            return c, param, v
        
        else: SLI_assert_unreachable()
        
        
    """This is where we try to find the channel number of the object."""
    def append_channel(self, channels, chan):
        if not bpy.context.scene.scene_props.use_name_for_id:
            if chan.int_object_channel_index != 0:
                channels.append(chan.int_object_channel_index)
            else:
                try:
                    number = find_int(chan.name)
                    channels.append(number)
                except:
                    SLI_assert_unreachable()
        else:
            try:
                channels.append(find_int(chan.name))
            except:
                if chan.int_object_channel_index != 0:
                    channels.append(chan.int_object_channel_index)
                else: channels.append(self.number_to_add_if_null) 
                
                
    def apply_strength(self, parent, value):
        x = parent.float_object_strength
        r, g, b = value
        return (r * x, g * x, b * x)
    
    
    def invert(self, value):
        r, g, b = value
        return (1 - r, 1 - g, 1 - b)
            
        
    def find_my_influencer_values(self, parent, p, type):
        """Receives a bpy object mesh (parent), parameter, and controller_type, and returns three lists for channels list (c), parameters list, and values list (v)"""
        attribute_name = parameter_mapping.get(p)
        if attribute_name:  # Find and map value
            new_value = getattr(parent, attribute_name)
            new_value_for_raise = new_value
            
            if p == 'color':
                restore_value = getattr(parent, "float_vec_color_restore")
            
            current_channels = self.find_influencer_current_channels(parent)
            mapping = HarmonizerMappers()
            true_parent = bpy.data.objects[parent.name]
            influencer_list = self.get_list_by_parameter(true_parent, p)
            raise_channels = influencer_list.raise_channels
            old_channels = set(chan.chan for chan in raise_channels)
            new_channels = set()
            c = []
            param = []
            v = []
            new_channels = current_channels - old_channels
            
            # Release
            if type == "Influencer":
                for chan in list(raise_channels):
                    if chan.chan not in current_channels:
                        channel = []
                        self.append_channel(channel, chan.chan)
                        c.append(channel[0])
                        param.append(p)
                        if p == "color":
                            if not parent.is_erasing:
                                new_release_value = self.color_object_to_tuple(restore_value)
                            else: new_release_value = self.color_object_to_tuple(new_value)
                            v.append(new_release_value)
                        else: v.append(chan.original_influence * -1)
                    
            raise_channels.clear()
            
            # Raise
            for chan in new_channels:
                # Append Channel
                channel = []
                self.append_channel(channel, chan)
                c.append(channel[0])
                
                # Append Parameter
                if type == "Brush" and p == "color":
                    param.append(f"raise_{p}")
                elif type == "Brush":
                    param.append(f"raise_{p}")
                else: param.append(p)
                
                # Append Value
                if p in ["pan", "tilt", "zoom", "gobo_speed"]:
                    value_to_add = mapping.map_value(parent, channel, p, new_value, type)
                    v.append(value_to_add)
                else:
                    if p == "color":
                        if not parent.is_erasing:
                            new_raise_value = new_value_for_raise
                        else: new_raise_value = restore_value
                        
                        if type == "Brush":
                            #return [], [], []
                            if parent.is_erasing:
                                new_raise_value = (1, 1, 1)
                            new_raise_value = self.invert(new_raise_value)
                        new_raise_value = self.color_object_to_tuple(new_raise_value)  
                        new_raise_value = self.apply_strength(parent, new_raise_value)
                        if type == "Brush" and p == "color":
                            r, g, b = new_raise_value
                            if not parent.red_is_on:
                                r = 100
                            if not parent.green_is_on:
                                g = 100
                            if not parent.blue_is_on:
                                b = 100
                            if r == 0:
                                r = -100 * parent.float_object_strength
                            if g == 0:
                                g = -100 * parent.float_object_strength
                            if b == 0:
                                b = -100 * parent.float_object_strength
                            new_raise_value = (r * -1, g * -1, b * -1)
                        v.append(new_raise_value)
                    else:
                        if type == "Brush":
                            new_value_for_raise *= parent.float_object_strength
                            if parent.is_erasing:
                                v.append(new_value_for_raise * -1)
                            else: v.append(new_value_for_raise)
                        else: v.append(new_value_for_raise)
                
            for chan in current_channels:
                new_channel = raise_channels.add()
                new_channel.chan = chan
                if p != "color":
                    new_channel.original_influence = new_value
                
            return c, param, v
        
        else:
            SLI_assert_unreachable()

        
    def find_my_channels_and_values(self, parent, p):
        """
        Intensity updater function called from universal_updater that returns 2 lists for channels and values,
        as well as the controller type for use when building the osc argument

        Parameters:
        self: The object from which this function is called.
        p: Parameter.
        
        Returns:
        c: Channel list
        v: Values list
        type: Controller type
        """
        controller_type = self.find_my_controller_type(parent)  # Should return a string.
        
        if controller_type in ["Influencer", "Brush"]:
            c, p, v = self.find_my_influencer_values(parent, p, controller_type)
            return c, p, v, controller_type
        
        elif controller_type in ["Fixture", "Pan/Tilt Fixture"]:
            channels = []
            self.append_channel(channels, parent)
            value = self.find_my_value(parent, p, controller_type, channels[0])
            return channels, [p], [value], controller_type
        
        elif controller_type in  ["group", "strip", "Stage Object"]:
            c, p, v = self.find_my_group_values(parent, p, controller_type)
            return c, p, v, controller_type
        
        elif controller_type == "mixer":
            mixing = HarmonizerMixer()
            c, p, v = mixing.mix_my_values(parent, p)
            return c, p, v, controller_type
                    
        else: SLI_assert_unreachable()
    
    
def find_my_patch(parent, chan, type, desired_property):
    """
    [EDIT 6/29/24: This docustring is slightly outdated now after revising the code for 
    new patch system]
    
    This function finds the best patch for a given channel. If the controller type is
    not Fixture or P/T Fixture, then it tries to find an object in the 3D scene that
    represents that channel. If it finds one, it will return that object's desired
    property. If the controller type (type) is Fixture or P/T Fixture, then it will
    use that object's patch. If neither of those 2 options work out, it will give up,
    surrender, and just use the parent controller's patch. 
    
    The goal of this function is to ensure that the user has a way to patch all fixtures
    and expect that Sorcerer will behave more or less like a full-blown console——that is
    to say, things like color profiles, mins and maxes, and other things fade away into
    the background and the user doesn't hardly ever have to worry about it. With this
    function, if the user patches the min/max, color profiles, and abilities and whatnot
    for each fixture, then this function will always use that patch for each individual
    fixture——regardless of what controller is controlling the fixture.
    
    At the same time however, if the user doesn't feel like patching beforehand, they
    can make things happen extremely quickly without ever thinking about patch. That's
    why we have a local patch built into the UI of each controller.
    
    Parameters:
        parent: the parent controller object, a node, object, or color strip
        chan: the channel number as defined by the parent's list_group_channels
        type: the controllertype of parent controller object, can be mixer, group node, stage object, etc.
        desired_property: the patch property that is being requested, in string form
        
    Returns:
        desired_property: The value of the requested property, aka the patch info
    """
    if type not in ["Fixture", "Pan/Tilt Fixture"]:
        second_options = []
        for obj in bpy.data.objects:
            if obj.int_object_channel_index == str(chan):
                return getattr(obj, desired_property)
            else:
                try:
                    option = int(obj.name)
                    if option == chan:
                        second_options.append(obj)
                except: pass
        if len(second_options) > 0:
            return getattr(second_options[0], desired_property)
    return getattr(parent, desired_property)
    
    
def find_parent(self):
    """
    Catches and corrects cases where the self is a collection property instead of 
    a node, sequencer strip, object, etc. This function returns the bpy object so
    that the rest of the harmonizer can find what it needs.
    
    Parameters: 
        self: A bpy object that may be a node, strip, object, or collection property
    Returns:
        parent: A bpy object that may be a node, strip, or object
    """
    if not isinstance(self, bpy.types.PropertyGroup):
        return self
    else:
        # Use the node_tree_pointer directly to get the node tree
        node_tree = self.node_tree_pointer
        if node_tree:
            node = node_tree.nodes.get(self.node_name)
            if node:
                return node
        
        # If not found, look in bpy.data.worlds
        for world in bpy.data.worlds:
            if world.node_tree and world.node_tree == self.node_tree_pointer:
                node = world.node_tree.nodes.get(self.node_name)
                if node:
                    return node
        
        return None
    
    
def universal_updater(self, context, property_name, find_function):
    """
    Universal updater function that contains the common logic for all property updates.

    Parameters:
    self: The instance from which this function is called.
    context: The current context.
    property_name (str): The name of the property to update.
    find_function (function): The function that finds the channels and values for the given property.
    """
    p = property_name  # inherited from the partial
    mode = p
    parent = find_parent(self)
    c, p, v, type = find_function(parent, p)  # Should return 3 lists and a string. find_function() is find_my_channels_and_values()
    
    if mode == "color":
        color_splitter = ColorSplitter()
        p, v = color_splitter.split_color(parent, c, p, v, type)

    finders = HarmonizerFinders()
    i = []
    a = []
    influence = parent.influence
    for chan, param in zip(c, p):
        argument = finders.find_my_argument_template(parent, chan, param, type)
        i.append(influence)
        a.append(argument)
      
    publisher = HarmonizerPublisher()
    for chan, param, val, inf, arg in zip(c, p, v, i, a):
        if param in ["intensity", "raise_intensity", "lower_intensity"]:
            publisher.send_value_to_three_dee(parent, chan, param, val)
        publisher.send_cpvia(chan, param, val, inf, arg)


harmonizer_instance = HarmonizerFinders()

intensity_partial = partial(universal_updater, property_name="intensity", find_function=harmonizer_instance.find_my_channels_and_values)
color_partial = partial(universal_updater, property_name="color", find_function=harmonizer_instance.find_my_channels_and_values)
pan_partial = partial(universal_updater, property_name="pan", find_function=harmonizer_instance.find_my_channels_and_values)
tilt_partial = partial(universal_updater, property_name="tilt", find_function=harmonizer_instance.find_my_channels_and_values)
strobe_partial = partial(universal_updater, property_name="strobe", find_function=harmonizer_instance.find_my_channels_and_values)
zoom_partial = partial(universal_updater, property_name="zoom", find_function=harmonizer_instance.find_my_channels_and_values)
iris_partial = partial(universal_updater, property_name="iris", find_function=harmonizer_instance.find_my_channels_and_values)
diffusion_partial = partial(universal_updater, property_name="diffusion", find_function=harmonizer_instance.find_my_channels_and_values)
edge_partial = partial(universal_updater, property_name="edge", find_function=harmonizer_instance.find_my_channels_and_values)
gobo_id_partial = partial(universal_updater, property_name="gobo_id", find_function=harmonizer_instance.find_my_channels_and_values)
gobo_speed_partial = partial(universal_updater, property_name="gobo_speed", find_function=harmonizer_instance.find_my_channels_and_values)
prism_partial = partial(universal_updater, property_name="prism", find_function=harmonizer_instance.find_my_channels_and_values)

def intensity_updater(self, context):
    return intensity_partial(self, context)
def color_updater(self, context):
    return color_partial(self, context)
def pan_updater(self, context):
    return pan_partial(self, context)
def tilt_updater(self, context):
    return tilt_partial(self, context)
def strobe_updater(self, context):
    return strobe_partial(self, context)
def zoom_updater(self, context):
    return zoom_partial(self, context)
def iris_updater(self, context):
    return iris_partial(self, context)
def diffusion_updater(self, context):
    return diffusion_partial(self, context)
def edge_updater(self, context):
    return edge_partial(self, context)
def gobo_id_updater(self, context):
    return gobo_id_partial(self, context)
def gobo_speed_updater(self, context):
    return gobo_speed_partial(self, context)
def prism_updater(self, context):
    return prism_partial(self, context)

def mixer_offset_updater(self, context):
    if self.parameters:
        if self.parameters_enum == "option_intensity":
            self.parameters[0].float_intensity = self.parameters[0].float_intensity
        elif self.parameters_enum == "option_color":
            self.parameters[0].float_vec_color = self.parameters[0].float_vec_color
        elif self.parameters_enum == "option_pan_tilt":
            self.parameters[0].float_pan = self.parameters[0].float_pan
            self.parameters[0].float_tilt = self.parameters[0].float_tilt
        elif self.parameters_enum == "option_zoom":
            self.parameters[0].float_zoom = self.parameters[0].float_zoom
        elif self.parameters_enum == "option_iris":
            self.parameters[0].float_iris = self.parameters[0].float_iris
###################
# END HARMONIZER
###################
        

###################
# HANDLERS
###################

DEBOUNCE_INTERVAL = 0.003  # 100 milliseconds

# Initialize the last update time variable
last_update_time = 0

def check_and_trigger_drivers(updated_objects):
    evaluated_to_original = [obj.name for obj in updated_objects]
    
    for obj in bpy.data.objects:
        if obj.object_identities_enum == "Stage Object":
            
            # Iterate through drivers of the object
            if obj.animation_data:
                for driver in obj.animation_data.drivers:
                    data_path = driver.data_path
                    # Attempt to resolve the property path to get the property name
                    try:
                        # Check if the property path is quoted or not
                        if '"' in data_path:
                            # Quoted property
                            prop_name = data_path.split('"')[1]
                        else:
                            # Unquoted property (like float_intensity)
                            prop_name = data_path.split('.')[-1]
                        
                        # Print driver details
                        for var in driver.driver.variables:
                            for target in var.targets:
                                
                                # Check if the driver targets any of the updated objects
                                if target.id.name in evaluated_to_original:
                                    # Trigger the update for this property
                                    trigger_set_piece_update(obj)
                    except IndexError:
                        print(f"Failed to parse data path '{data_path}' for drivers on '{obj.name}'")
                    except Exception as e:
                        print(f"Error processing driver on '{obj.name}': {e}")


@persistent
def depsgraph_update_handler(scene, depsgraph):
#    global last_update_time

#    current_time = time.time()
#    if current_time - last_update_time < DEBOUNCE_INTERVAL:
#        return  # Skip this update if within the debounce interval
#    
#    last_update_time = current_time
    updated_objects = {update.id for update in depsgraph.updates if isinstance(update.id, bpy.types.Object)}
    
    for update in depsgraph.updates:
        # Check if the update is for an object
        if isinstance(update.id, bpy.types.Object):
            obj = update.id
            
            if obj.object_identities_enum in {"Influencer", "Brush"}:
                if update.is_updated_transform:
                    trigger_influencer_brush_update(obj)
            elif obj.object_identities_enum == "Stage Object":
                if update.is_updated_geometry:
                    trigger_set_piece_update(obj)
                    
    check_and_trigger_drivers(updated_objects)


def trigger_influencer_brush_update(obj):
    # Trigger the harmonizer update for each relevant property, skipping those set to 0
    properties = ['float_intensity', 'float_vec_color', 'float_zoom', 'float_iris']
    for prop in properties:
        value = getattr(obj, prop)
        if isinstance(value, float) and value != 0:
            setattr(obj, prop, value)
        elif isinstance(value, mathutils.Color) and any(c != 0 for c in value):
            setattr(obj, prop, value)


def trigger_set_piece_update(obj):
    # Trigger the harmonizer update for each relevant property, skipping those set to 0
    properties = ['float_intensity', 'float_vec_color', 'float_zoom', 'float_iris']
    for prop in properties:
        value = getattr(obj, prop)
        if isinstance(value, float) and value != 0:
            setattr(obj, prop, value)
        elif isinstance(value, (list, tuple)) and any(v != 0 for v in value):
            setattr(obj, prop, value)   


#########################
# SORCERER DEPSGRAPH
#########################
old_graph = []
controllers = []

class AnimationDependencyGraph:  # Because Blender's doesn't care :(
    def __init__(self):
        self.toggles = {
            "intensity_is_on": ["float_intensity"], 
            "pan_tilt_is_on": ["float_pan", "float_tilt"],
            "color_is_on": ["float_vec_color"], 
            "diffusion_is_on": ["float_diffusion"],
            "strobe_is_on": ["float_strobe"],
            "zoom_is_on": ["float_zoom"], 
            "iris_is_on": ["float_iris"], 
            "edge_is_on": ["float_edge"], 
            "gobo_id_is_on": ["int_gobo_id", "float_gobo_speed"],
            "prism_is_on": ["int_prism"]
        }
        
    
    # Find object, strip, and node controllers.
    def find_controllers(self, scene):
        controllers = []
        
        if scene.scene_props.objects_enabled:
            controllers = self.find_objects(scene)
        if scene.scene_props.strips_enabled:
            controllers = self.find_strips(scene, controllers)
        if scene.scene_props.nodes_enabled:
            controllers = self.find_nodes(scene, controllers)
        
        return controllers
    
    def find_objects(self, scene):
        if not scene.scene_props.objects_enabled:
            return []
        
        return [obj for obj in scene.objects]
    
    def find_strips(self, scene, controllers):
        if not scene.scene_props.strips_enabled or not hasattr(scene, "sequence_editor"):
            return controllers
        
        for strip in scene.sequence_editor.sequences_all:
            if strip.type == 'COLOR' and strip.my_settings.motif_type_enum == 'option_animation':
                controllers.append(strip)
                
        return controllers
    
    def find_nodes(self, scene, controllers):
        if not scene.scene_props.nodes_enabled:
            return controllers
        
        node_trees = set()
        
        if bpy.context.scene.world and bpy.context.scene.world.node_tree:
            node_trees.add(bpy.context.scene.world.node_tree)
        for node_tree in bpy.data.node_groups:
            node_trees.add(node_tree)
        for node_tree in node_trees:
            for node in node_tree.nodes:
                controllers.append(node)
                
        return controllers
    
    
    # Find the animated properties inside the controllers.
    def convert_to_props(self, scene, controllers):
        props = []
        
        for controller in controllers:
            if hasattr(controller, 'bl_idname') and controller.bl_idname == 'mixer_type':
                props.extend(self.find_props(controller, controller.parameters))
            else:
                props.extend(self.find_props(controller, controller))
                
        return props
    
    def find_props(self, controller, props_location):
        props = []
            
        for toggle, attributes in self.toggles.items():
            if getattr(props_location, toggle, False):
                for property in attributes:
                    if self.has_keyframes(props_location, property):
                        value = getattr(props_location, property, None)
                        props.append((controller, property, value))
            
        return props
    
    def has_keyframes(self, controller, property):
        if hasattr(controller, "animation_data") and controller.animation_data:
            if hasattr(controller.animation_data, "action") and controller.animation_data.action:
                for fcurve in controller.animation_data.action.fcurves:
                    if fcurve.data_path.endswith(property):
                        return len(fcurve.keyframe_points) > 0

        if isinstance(controller, bpy.types.ColorSequence):
            return True
        
        if hasattr(controller, "bl_idname") and controller.bl_idname in ['group_controller_type', 'mixer_type']:
            node_tree = controller.id_data  # Get the node tree containing the node
            if hasattr(node_tree, "animation_data") and node_tree.animation_data:
                action = node_tree.animation_data.action
                if action:
                    for fcurve in action.fcurves:
                        # Check if the data path corresponds to the node and the property
                        if fcurve.data_path.startswith(controller.path_from_id()) and fcurve.data_path.endswith(property):
                            return len(fcurve.keyframe_points) > 0
        return False
    
    
    # Find properties that actually need to send OSC right now.
    def find_updates(self, old_graph, new_graph):
        old_dict = {(controller, parameter): value for controller, parameter, value in old_graph}
        new_dict = {(controller, parameter): value for controller, parameter, value in new_graph}

        # Only consider updates if there is a corresponding entry in both graphs and the value has changed
        updates = [(controller, parameter, new_value) 
                   for (controller, parameter), new_value in new_dict.items() 
                   if (controller, parameter) in old_dict and old_dict[(controller, parameter)] != new_value]

        return updates
    
    
    def use_harmonizer(self, flag):
        bpy.context.scene.scene_props.in_frame_change = flag
    
    
    # Start the logic to create a CPVIA request for the controller's changed property.
    def fire_updaters(self, updates):    
        for controller, property, value in updates:
            setattr(controller, property, getattr(controller, property))
    
    
# HANDLERS 
@persistent
def frame_change_pre(scene):
    global controllers, old_graph

    depsgraph = AnimationDependencyGraph()
    
    if not scene.scene_props.is_playing or not controllers:
        # Find controllers if not playing or if controllers are not set
        controllers = depsgraph.find_controllers(scene)
    
    current_controllers = controllers
    
    new_graph = depsgraph.convert_to_props(scene, current_controllers)
    updates = depsgraph.find_updates(old_graph, new_graph)
    
    depsgraph.use_harmonizer(True)  # Bind updater to harmonizer.
    depsgraph.fire_updaters(updates)  # Form CPVIA request and add to change_requests.
    depsgraph.use_harmonizer(False)  # Release updater from harmonizer.
    
    old_graph = new_graph
    
    # Clear controllers when not playing
    if not scene.scene_props.is_playing:
        controllers = []
    
    
@persistent
def frame_change_post(scene):
    global change_requests
    
#    print("")
#    print("")
#    print(f"BEGINNING. Democratic mode is {scene.scene_props.is_democratic}. Original input below.")
#    for request in change_requests:
#        print(request)
#    print("")

    no_duplicates = remove_duplicates(change_requests)
    
#    print("no_duplicates below.")
#    for request in no_duplicates:
#        print(request)
#    print("")
    
    if scene.scene_props.is_democratic:
        no_conflicts = democracy(no_duplicates)
    else:
        no_conflicts = highest_takes_precedence(no_duplicates)
        
#    print("no_conflicts below.")
#    for request in no_conflicts:
#        print(request)
#    print("")
        
    simplified = simplify(no_conflicts)

#    print("simplified below.")
    publisher = HarmonizerPublisher()
    for request in simplified:
#        print(request)
        address, argument = publisher.form_osc(*request)  # Should return 2 strings
        send_osc(address, argument)
#    print("")
    
    if not scene.scene_props.is_playing:
        scene.scene_props.in_frame_change = False
        
    # Clear change_requests here.
    change_requests = []
               
            
#########################
# CPVIA HARMONIZER
#########################
def remove_duplicates(change_requests):
    request_dict = {}

    for c, p, v, i, a in change_requests:
        key = (c, p, v)
        if key in request_dict:
            request_dict[key][1] += i  # Collect the eaten request's votes
        else:
            request_dict[key] = [a, i]  # Store argument and influence

    return [(c, p, v, influence, argument) for (c, p, v), (argument, influence) in request_dict.items()]


def democracy(no_duplicates):
    '''Democratic mode where influence (i) is the number of votes one gets when there is a conflict'''
    request_dict = {}

    for c, p, v, i, a in no_duplicates:
        key = (c, p)
        if key not in request_dict:
            request_dict[key] = {'total_influence': 0, 'weighted_sum': 0, 'arguments': a}
        request_dict[key]['total_influence'] += i
        request_dict[key]['weighted_sum'] += v * i

    no_conflicts = []
    for key, value_dict in request_dict.items():
        c, p = key
        total_influence = value_dict['total_influence']
        weighted_sum = value_dict['weighted_sum']
        a = value_dict['arguments']
        v = weighted_sum / total_influence  # Calculate weighted average value
        no_conflicts.append((c, p, v, total_influence, a))
    
    return no_conflicts


def highest_takes_precedence(no_duplicates):
    '''Standard HTP protocol mode'''
    request_dict = {}

    for c, p, v, i, a in no_duplicates:
        key = (c, p)  # Key based on channel and parameter only
        if key in request_dict:
            if v > request_dict[key][2]:  # Compare the value
                request_dict[key] = (c, p, v, i, a)
        else:
            request_dict[key] = (c, p, v, i, a)

    no_conflicts = list(request_dict.values())
    
    return no_conflicts

    
def simplify(no_conflicts):
    ''' Finds any instances where everything but channel number is the same 
        between multiple requests and combines them using "thru" for consecutive numbers.
    '''
    
    simplified_dict = {}

    for c, p, v, i, a in no_conflicts:
        key = (p, v, a)
        if key in simplified_dict:
            simplified_dict[key][0].append(int(c))  # Store channels as integers for easier sorting
        else:
            simplified_dict[key] = ([int(c)], p, v, i, a)

    simplified = []
    for (p, v, a), (channels, p, v, i, a) in simplified_dict.items():
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

        combined_channels_str = " + ".join(combined_channels)
        simplified.append((combined_channels_str, p, v, i, a))

    return simplified
    
    
#bpy.types.Scene.animation_handler = AnimationHandler()


# Ensure the handler is added to the frame change handlers list
bpy.app.handlers.frame_change_pre.clear()
bpy.app.handlers.frame_change_post.clear()
#bpy.app.handlers.animation_playback_pre.clear()
bpy.app.handlers.frame_change_pre.append(frame_change_pre)
bpy.app.handlers.frame_change_post.append(frame_change_post)
#bpy.app.handlers.animation_playback_pre.append(animation_playback_pre)

# Print the handlers in frame_change_pre
print("Handlers in bpy.app.handlers.frame_change_pre:")
for handler in bpy.app.handlers.frame_change_pre:
    print(f" - {handler}")
# scene.scene_props.is_playing is set to True/False in the SEQ Main script

###################
# NODE SOCKETS
###################
class AlvaNodeTree(bpy.types.NodeTree):
    bl_idname = 'AlvaNodeTree'
    bl_label = 'Sorcerer Nodes'
    bl_icon = 'NODETREE'
    

class LightingInputSocket(NodeSocket):
    bl_idname = 'LightingInputType'
    bl_label = 'Lighting Input Socket'

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (.5, 0, 1, 1)  


class LightingOutputSocket(NodeSocket):
    bl_idname = 'LightingOutputType'
    bl_label = 'Lighting Output Socket'

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (.5, 0, 1, 1)  
    
    
class FlashOutSocket(NodeSocket):
    bl_idname = 'FlashOutType'
    bl_label = 'Flash Output Socket'

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (1, 1, 0, 1) 
    
    
class MotorInputSocket(NodeSocket):
    bl_idname = 'MotorInputType'
    bl_label = 'Motor Input Socket'

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (.5, .5, .5, .5) 
    
    
class MotorOutputSocket(NodeSocket):
    bl_idname = 'MotorOutputType'
    bl_label = 'Motor Output Socket'

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (.5, .5, .5, .5) 
    
    
###################
# NODES
###################
class GroupControllerNode(bpy.types.Node):
    bl_idname = 'group_controller_type'
    bl_label = 'Group Controller Node'
    bl_icon = 'STICKY_UVS_LOC'
    bl_width_default = 300

    # Assigned by group_info_updater on selected_group_enum property.
    str_group_id: StringProperty(default="1")
    list_group_channels: CollectionProperty(type=ChannelListPropertyGroup)
    str_group_label: StringProperty(default="")
    
    # OSC argument templates for properties specific to the fixture type, not scene. For example, strobe, not intensity.
    str_enable_strobe_argument: StringProperty(default="# Strobe_Mode 127 Enter", description="Add # for group ID")
    str_disable_strobe_argument: StringProperty(default="# Strobe_Mode 76 Enter", description="Add # for group ID")
    str_enable_gobo_speed_argument: StringProperty(default="# Gobo_Mode 191 Enter", description="Add # for group ID")
    str_disable_gobo_speed_argument: StringProperty(default="# Gobo_Mode 63 Enter", description="Add # for group ID")
    str_gobo_id_argument: StringProperty(default="# Gobo_Select $ Enter", description="Add # for group ID and $ for value")
    str_gobo_speed_value_argument: StringProperty(default="# Gobo_Index/Speed at $ Enter", description="Add $ for animation data and # for fixture/group ID")
    str_enable_misc_effect_argument: StringProperty(default="# Gobo_Wheel_Mode 213 Enter", description="Add # for group ID")
    str_disable_misc_effect_argument: StringProperty(default="# Gobo_Wheel_Mode 213 Enter", description="Add # for group ID")
    str_enable_prism_argument: StringProperty(default="# Beam_Fx_Select 02 Enter", description="Add # for group ID")
    str_disable_prism_argument: StringProperty(default="# Beam_Fx_Select 01 Enter", description="Add # for group ID")
    
    # Min/max values mapped from 0-100 scale inside the harmonizer since we cannot live-update prop min/maxes. 
    # This provides user full use of the slider at all times.
    pan_min: IntProperty(default=-270, description="Minimum value for pan")
    pan_max: IntProperty(default=270, description="Maximum value for pan")
    tilt_min: IntProperty(default=-135, description="Minimum value for tilt")
    tilt_max: IntProperty(default=135, description="Maximum value for tilt")
    zoom_min: IntProperty(default=1, description="Minimum value for zoom")
    zoom_max: IntProperty(default=100, description="Maximum value for zoom")     
    gobo_speed_min: IntProperty(default=-200, description="Minimum value for speed")
    gobo_speed_max: IntProperty(default=200, description="Maximum value for speed")

    # Selected group and color profile enumerators.
    selected_group_enum: EnumProperty(
        name="Selected Light",
        description="Choose a group to control. Create these groups with the Patch function on the N tab in node editor, with USITT ASCII import in the same area, or create/modify them in Properties -> World -> SORCERER: Group Channel Blocks (full screen).",
        items=scene_groups
    )
    str_manual_fixture_selection: StringProperty(
        name="Selected Lights",
        description="Instead of the group selector to the left, simply type in what you wish to control here",
        update=manual_fixture_selection_updater
    )
    color_profile_enum: EnumProperty(
        name="Color Profile",
        description="Choose a color profile for the group",
        items=color_profiles,
    )
    
    # User-accessible property definitions.
    influence: IntProperty(default=1, min=1, max=10, description="How many votes this controller has when there are conflicts", options={'ANIMATABLE'})
    float_intensity: FloatProperty(default=0, min=0, max=100, description="Intensity value", options={'ANIMATABLE'}, update=intensity_updater)
    float_vec_color: FloatVectorProperty(
        name="",
        subtype='COLOR',
        size=3,
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        description="Color value",
        update=color_updater
    )
    float_diffusion: FloatProperty(default=0, min=0, max=100, description="Diffusion value", options={'ANIMATABLE'}, update=diffusion_updater)
    float_pan: FloatProperty(default=0, min=-100, max=100, description="Pan value", options={'ANIMATABLE'}, update=pan_updater)
    float_tilt: FloatProperty(default=0, min=-100, max=100, description="Tilt value", options={'ANIMATABLE'}, update=tilt_updater)
    float_strobe: FloatProperty(default=0, min=0, max=100, description="Strobe value", options={'ANIMATABLE'}, update=strobe_updater)
    float_zoom: FloatProperty(default=0, min=0, max=100, description="Zoom value", options={'ANIMATABLE'}, update=zoom_updater)
    float_iris: FloatProperty(default=0, min=0, max=100, description="Iris value", options={'ANIMATABLE'}, update=iris_updater)
    float_edge: FloatProperty(default=0, min=0, max=100, description="Edge value", options={'ANIMATABLE'}, update=edge_updater)
    int_gobo_id: IntProperty(default=1, min=0, max=20, description="Gobo selection", options={'ANIMATABLE'}, update=gobo_id_updater)
    float_gobo_speed: FloatProperty(default=0, min=-100, max=100, description="Rotation of individual gobo speed", options={'ANIMATABLE'}, update=gobo_speed_updater)
    int_prism: IntProperty(default=0, min=0, max=1, description="Prism value. 1 is on, 0 is off", options={'ANIMATABLE'}, update=prism_updater)
    # Toggles for turning off visibility to unneeded parameters.
    influence_is_on: BoolProperty(default=False, description="Influence is enabled when checked")
    intensity_is_on: BoolProperty(default=True, description="Intensity is enabled when checked")
    pan_tilt_is_on: BoolProperty(default=False, description="Pan/Tilt is enabled when checked")    
    color_is_on: BoolProperty(default=False, description="Color is enabled when checked")
    diffusion_is_on: BoolProperty(default=False, description="Diffusion is enabled when checked")
    strobe_is_on: BoolProperty(default=False, description="Strobe is enabled when checked")
    zoom_is_on: BoolProperty(default=False, description="Zoom is enabled when checked")
    iris_is_on: BoolProperty(default=False, description="Iris is enabled when checked")
    edge_is_on: BoolProperty(default=False, description="Edge is enabled when checked")
    gobo_id_is_on: BoolProperty(default=False, description="Gobo ID is enabled when checked")
    prism_is_on: BoolProperty(default=False, description="Prism is enabled when checked")

    def init(self, context):
        group_input = self.inputs.new('LightingInputType', "Lighting Input")
        group_input.link_limit = 10
        self.outputs.new('LightingOutputType', "Lighting Output")
        self.outputs.new('FlashOutType', "Flash")

        # Assign node group pointer
        self.node_group_pointer = self.id_data
        return

    def draw_buttons(self, context, layout):
        if self.influence_is_on:
            row = layout.row(align=True)
            row.prop(self, "influence", slider=True, text="Influence:")
            layout.separator()

        row = layout.row(align=True)
        if self.str_manual_fixture_selection == "":
            if not self.selected_group_enum:
                row.alert = 1
            row.prop(self, "selected_group_enum", text="", icon_only=False, icon='LIGHT')
            row.alert = 0
        row.prop(self, "str_manual_fixture_selection", text="")
        
        row = layout.row(align=True)
        # Must send identity info to some operators since buttons can be pressed on non-active nodes.
        op_home = row.operator("node.home_group", icon='HOME', text="")
        op_home.node_name = self.name
        op_update = row.operator("node.update_group", icon='FILE_REFRESH', text="")
        op_update.node_name = self.name
        
        row.prop(self, "float_intensity", slider=True, text="Intensity:")
        
        # All strobe controls on a button/popup to avoid putting it on its own row.
        if self.strobe_is_on:
            row_one = row.column(align=True)
            row_one.scale_x = 1
            op = row_one.operator("my.view_strobe_props", icon='OUTLINER_OB_LIGHTPROBE', text="")
            op.space_type = self.name
            op.node_group_name = self.id_data.name
    
        if self.color_is_on:
            sub = row.column(align=True)
            sub.scale_x = 0.3
            sub.prop(self, "float_vec_color", text="")
            sub_two = row.column(align=True)
            # Do not allow students/volunteers to mess up the color profile setting.
            if not context.scene.scene_props.school_mode_enabled:
                sub_two.scale_x = 0.8
                sub_two.prop(self, "color_profile_enum", text="", icon='COLOR', icon_only=True)

        if self.pan_tilt_is_on:
            row = layout.row(align=True)
            op = row.operator("my.view_pan_tilt_props", icon='ORIENTATION_GIMBAL', text="")
            op.space_type = self.name
            op.node_group_name = self.id_data.name
            row.prop(self, "float_pan", text="Pan", slider=True)
            row.prop(self, "float_tilt", text="Tilt", slider=True)
        
        if self.zoom_is_on or self.iris_is_on:
            row = layout.row(align=True)
            op = row.operator("my.view_zoom_iris_props", text="", icon='LINCURVE')
            op.space_type = self.name
            op.node_group_name = self.id_data.name
            
            if self.zoom_is_on:
                row.prop(self, "float_zoom", slider=True, text="Zoom:")
            if self.iris_is_on:
                row.prop(self, "float_iris", slider=True, text="Iris:")
        
        if self.edge_is_on or self.diffusion_is_on:
            row = layout.row(align=True)
            op = row.operator("my.view_edge_diffusion_props", text="", icon='SELECT_SET')
            op.space_type = self.name
            op.node_group_name = self.id_data.name
            
            if self.edge_is_on:
                row.prop(self, "float_edge", slider=True, text="Edge:")
            if self.diffusion_is_on:
                row.prop(self, "float_diffusion", slider=True, text="Diffusion:")
        
        if self.gobo_id_is_on:
            row = layout.row(align=True)
            op = row.operator("my.view_gobo_props", text="", icon='POINTCLOUD_DATA')
            op.space_type = self.name
            op.node_group_name = self.id_data.name
            
            row.prop(self, "int_gobo_id", text="Gobo:")
            row.prop(self, "float_gobo_speed", slider=True, text="Speed:")
            row.prop(self, "int_prism", slider=True, text="Prism:")


def mixer_update_handler(scene):
    for node_tree in bpy.data.node_groups:
        for node in node_tree.nodes:
            if isinstance(node, MixerNode):
                node.update_node_name()
                
    for world in bpy.data.worlds:
        if world.node_tree:
            for node in world.node_tree.nodes:
                if isinstance(node, MixerNode):
                    node.update_node_name()

  
class MixerParameters(bpy.types.PropertyGroup):
    node_tree_pointer: bpy.props.PointerProperty(
        name="Node Tree Pointer",
        type=bpy.types.NodeTree,
        description="Pointer to the node tree"
    )
    node_name: bpy.props.StringProperty(
        name="Node Name",
        description="Name of the node"
    )

    float_intensity: FloatProperty(default=0, min=0, max=100, update=intensity_updater, name="Intensity:")
    float_vec_color: FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        size=3,
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        description="Color value",
        update=color_updater
    )
    float_pan: FloatProperty(default=0, min=-315, max=315, update=pan_updater, name="Pan:")
    float_tilt: FloatProperty(default=0, min=-135, max=135, update=tilt_updater, name="Tilt:")
    float_zoom: FloatProperty(default=10, min=1, max=100, update=zoom_updater, name="Zoom:")
    float_iris: FloatProperty(default=100, min=0, max=100, update=iris_updater, name="Iris:")
  
    
class MixerNode(bpy.types.Node):
    bl_idname = 'mixer_type'
    bl_label = 'Mixer Node'
    bl_icon = 'OPTIONS'
    bl_width_default = 400
    
    def mixer_parameters(self, context):
        items = [
            ('option_intensity', "Intensity", "Mix intensities across a group", 'OUTLINER_OB_LIGHT', 1),
            ('option_color', "Color", "Mix colors across a group", 'COLOR', 2),
            ('option_pan_tilt', "Pan/Tilt", "Mix pan/tilt settings across a group", 'ORIENTATION_GIMBAL', 3),
            ('option_zoom', "Zoom", "Mix zoom settings across a group", 'LINCURVE', 4),
            ('option_iris', "Iris", "Mix iris settings across a group", 'RADIOBUT_OFF', 5)
        ]
        return items
    
    def mixer_methods(self, context):
        items = [
            ('option_gradient', "Gradient", "Mix choices across a group evenly", 'SMOOTHCURVE', 1),
            ('option_pattern', "Pattern", "Create patterns out of choices without mixing", 'IPO_CONSTANT', 2),
            ('option_pose', "Pose", "Create poses to oscillate between", 'POSE_HLT', 3),
        ]
        return items

    parameters: CollectionProperty(type=MixerParameters)
    
    str_group_id: StringProperty(default="1")
    list_group_channels: CollectionProperty(type=ChannelListPropertyGroup)
    str_group_label: StringProperty(default="")
    
    collapse_most: BoolProperty(default=False)

    parameters_enum: EnumProperty(
        name="Parameter",
        description="Choose a parameter type to mix",
        items=mixer_parameters,
        default=1
    )
    color_profile_enum: EnumProperty(
        name="Color Profile",
        description="Choose a color profile for the group",
        items=color_profiles,
        update=mixer_offset_updater
    )
    mix_method_enum: EnumProperty(
        name="Method",
        description="Choose a mixing method",
        items=mixer_methods,
        default=1
    )
    selected_group_enum: EnumProperty(
        name="Selected Group",
        description="Choose a group to control. Create these groups with the Patch function on the N tab in node editor, with USITT ASCII import in the same area, or create/modify them in Properties -> World -> SORCERER: Group Channel Blocks (full screen).",
        items=scene_groups
    )
    str_manual_fixture_selection: StringProperty(
        name="Selected Lights",
        description="Instead of the group selector to the left, simply type in what you wish to control here",
        update=manual_fixture_selection_updater
    )
    influence: IntProperty(default=1, min=1, max=10, description="How many votes this controller has when there are conflicts", options={'ANIMATABLE'})

    show_settings: BoolProperty(default=True, name="Show Settings", description="Expand/collapse group/parameter row and UI controller row")
    float_offset: FloatProperty(name="Offset", description="Move or animate this value for a moving effect", update=mixer_offset_updater)
    int_subdivisions: IntProperty(name="Subdivisions", description="Subdivide the mix into multiple sections", update=mixer_offset_updater, min=0, max=32)
    columns: IntProperty(name="# of Columns:", min=1, max=8, default=3)
    scale: FloatProperty(name="Size of Choices:", min=1, max=3, default=2)
    
    def init(self, context):
        self.inputs.new('MotorInputType', "Motor Input")
        self.outputs.new('FlashOutType', "Flash")
        node_refs[self.name] = self  # Add this node to the global dictionary
        self.update_node_name()
        return
    
    def update_node_name(self):
        """Update the node name to ensure uniqueness."""
        if not self.name.startswith("MixerNode_"):
            self.name = "MixerNode_" + self.name

        # Update names in parameters
        for param in self.parameters:
            param.node_tree_pointer = self.id_data
            param.node_name = self.name

    def draw_buttons(self, context, layout):  
        if self.show_settings:
            row = layout.row(align=True)
            op_home = row.operator("node.home_group", icon='HOME', text="")
            op_home.node_name = self.name
            op_update = row.operator("node.update_group", icon='FILE_REFRESH', text="")
            op_update.node_name = self.name
            if self.str_manual_fixture_selection == "":
                row.prop(self, "selected_group_enum", icon='COLLECTION_NEW', icon_only=0, text="")
            row.prop(self, "str_manual_fixture_selection", text="")
            if self.mix_method_enum != "option_pose":
                row.prop(self, "parameters_enum", expand=True, text="")
        
        row = layout.row(align=True)
        row.prop(self, "show_settings", text="", expand=False, icon='TRIA_DOWN' if self.show_settings else 'TRIA_RIGHT')
        row.prop(self, "mix_method_enum", expand=True, icon_only=True)
        if self.mix_method_enum != "option_pose":
            row.prop(self, "float_offset", text="Offset:")
            if self.mix_method_enum != "option_pattern":
                row.prop(self, "int_subdivisions", text="Subdivisions:")
        if self.parameters_enum in ["option_color", "option_pose"]:
            row.prop(self, "color_profile_enum", text="", icon='COLOR', icon_only=True)
        layout.separator()
        
        num_columns = self.columns

        flow = layout.grid_flow(row_major=True, columns=num_columns, even_columns=True, even_rows=False, align=True)
        flow.scale_y = self.scale
        
        i = 1
        
        for par in self.parameters:
            if self.mix_method_enum != 'option_pose':
                if self.parameters_enum == 'option_intensity':
                    flow.prop(par, "float_intensity", slider=True)
                elif self.parameters_enum == 'option_color':
                    flow.template_color_picker(par, "float_vec_color")
                elif self.parameters_enum == 'option_pan_tilt':
                    box = flow.box()
                    row = box.row()
                    split = row.split(factor=0.5)
                    col = split.column()
                    col.prop(par, "float_pan", text="Pan", slider=True)
                    col = split.column()
                    col.prop(par, "float_tilt", text="Tilt", slider=True)
                elif self.parameters_enum == 'option_zoom':
                    flow.prop(par, "float_zoom", slider=True)
                else:
                    flow.prop(par, "float_iris", slider=True)
            
            else:
                box = flow.box()
                row = box.row()
                row.label(text=f"Pose {i}:", icon='POSE_HLT')
                split = box.split(factor=0.5)

                # Left side: existing properties
                col = split.column()
                col.prop(par, "float_intensity")
                col.prop(par, "float_pan", text="Pan", slider=True)
                col.prop(par, "float_tilt", text="Tilt", slider=True)
                col.prop(par, "float_zoom")
                col.prop(par, "float_iris")

                # Right side: float_vec_color
                col = split.column()
                col.template_color_picker(par, "float_vec_color")
                
                i += 1
                
        layout.separator()
        if self.show_settings:
            row = layout.row()
            row.operator("node.add_choice", icon='ADD', text="")
            row.operator("node.remove_choice", icon='REMOVE', text="")
            row.prop(self, "columns", text="Columns:")
            row.prop(self, "scale", text="Size:")
            layout.separator() 


class LightingModifier(bpy.types.PropertyGroup):
    name: StringProperty(name="Name", default="Lighting Modifier")
    show_expanded: BoolProperty(name="Show Expanded", default=True)
    mute: BoolProperty(name="Mute", default=False)
    type: EnumProperty(
        name="Type",
        description="Type of lighting modifier",
        items = [
            ('option_brightness_contrast', "Brightness/Contrast", "Adjust overall brightness and contrast of the entire rig's intensity values"),
            ('option_saturation', "Saturation", "Adjust overall saturation of entire rig"),
            ('option_hue', "Hue", "Adjust the saturation of individual hues across the entire rig"),
            ('option_curves', "Curves", "Adjust overall brightness and contrast of entire rig's intensity values")
        ]
    )
    brightness: IntProperty(name="Brightness", default=0, min = -100, max = 100, description="Adjust overall brightness of the entire rig's intensity values")
    contrast: IntProperty(name="Contrast", default=0, min = -100, max = 100, description="Adjust the difference between the brightest lights and the darkest lights")
    saturation: IntProperty(name="Saturation", default=0, min = -100, max = 100, description="Adjust overall saturation of the entire rig")
    
    highlights: IntProperty(name="Highlights", default=0, min = -100, max = 100, description="")
    shadows: IntProperty(name="Shadows", default=0, min = -100, max = 100, description="")
    whites: IntProperty(name="Whites", default=0, min = -100, max = 100, description="")
    blacks: IntProperty(name="Blacks", default=0, min = -100, max = 100, description="")
    
    reds: IntProperty(name="Reds", default=0, min = -100, max = 100, description="")
    greens: IntProperty(name="Greens", default=0, min = -100, max = 100, description="")
    blues: IntProperty(name="Blues", default=0, min = -100, max = 100, description="")


###################
# REGISTRATION
###################
classes = (
    ChannelListPropertyGroup,
    LightingInputSocket,
    LightingOutputSocket,
    MotorInputSocket,
    MotorOutputSocket,
    FlashOutSocket,
    AlvaNodeTree,    
    GroupControllerNode,
    MixerParameters,
    MixerNode,
    LightingModifier,
    RaiseChannels,
    InfluencerList
)

    
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    ##################################################################################
    '''Registering the object props directly on object to preserve self-association'''
    ##################################################################################
        
    bpy.types.Object.relevant_channels_checker = StringProperty(default="")
    
    bpy.types.Object.int_speaker_number = IntProperty(name="Speaker Number", description="Number of speaker in Qlab or on sound mixer. You're seeing this here because you selected a Speaker object, and speaker objects represent real, physical speakers in your theater for the purpose of spatial audio. To pan microphones left or right, you don't use an encoder, you just move the microphone or sound object closer to the left or right inside 3D view", default=0)
    bpy.types.Object.sound_source_enum = EnumProperty(items=get_sound_sources, name="Select either a sound strip in the sequencer or a microphone in Audio Patch")
    
    bpy.types.Object.str_enable_strobe_argument = StringProperty(
        default="# Strobe_Mode 127 Enter", description="Add # for group ID")
        
    bpy.types.Object.str_disable_strobe_argument = StringProperty(
        default="# Strobe_Mode 76 Enter", description="Add # for group ID")


    bpy.types.Object.str_enable_gobo_speed_argument = StringProperty(
        default="", description="Add # for group ID")
        
    bpy.types.Object.str_disable_gobo_speed_argument = StringProperty(
        default="", description="Add # for group ID")
        

    bpy.types.Object.str_gobo_id_argument = StringProperty(
        default="# Gobo_Select $ Enter", description="Add # for group ID and $ for value")


    bpy.types.Object.str_enable_prism_argument = StringProperty(
        default="# Beam_Fx_Select 02 Enter", description="Add # for group ID")
        
    bpy.types.Object.str_disable_prism_argument = StringProperty(
        default="# Beam_Fx_Select 01 Enter", description="Add # for group ID")

    bpy.types.Object.str_gobo_speed_value_argument = StringProperty(
        default="# Gobo_Index/Speed at $ Enter", description="Add $ for animation data and # for fixture/group ID")




    #---------------------------------------------------------------------------------------
    '''OBECT FLOATS/INTS'''        
        
    bpy.types.Object.int_object_channel_index = IntProperty(default=1) ## This needs to be added to the UI
            
    bpy.types.Object.float_intensity_checker = FloatProperty(default=0)
    bpy.types.Object.float_vec_color_checker = FloatVectorProperty(default=(0, 0, 0))
    bpy.types.Object.float_pan_checker = FloatProperty(default=0)
    bpy.types.Object.float_tilt_checker = FloatProperty(default=0)
    bpy.types.Object.float_strobe_checker = FloatProperty(default=0)
    bpy.types.Object.float_zoom_checker = FloatProperty(default=0)
    bpy.types.Object.float_iris_checker = FloatProperty(default=0)
    bpy.types.Object.float_diffusion_checker = FloatProperty(default=0)
    bpy.types.Object.gobo_id_checker = FloatProperty(default=0)
    bpy.types.Object.float_speed_checker = FloatProperty(default=0)
    bpy.types.Object.float_edge_checker = FloatProperty(default=0)
    bpy.types.Object.misc_effect_checker = FloatProperty(default=0)
    bpy.types.Object.prism_checker = FloatProperty(default=0)
    bpy.types.Object.float_influence_checker = FloatProperty(
        default=1, description="")
    bpy.types.Object.color_profile_enum = EnumProperty(
        name="Color Profile",
        description="Choose a color profile for the mesh based on the patch in the lighting console",
        items=color_profiles,
    )
    bpy.types.Object.object_identities_enum = EnumProperty(
        name="Mesh Identity",
        description="In Sorcerer, meshes can represent and control individual lighting fixtures, microphones, stage objects, brushes, and 3D bitmapping objects. Select what you want your mesh to do here",
        items=object_identities,
    )
    
    # Assigned by group_info_updater on selected_group_enum property.
    bpy.types.Object.str_group_id = StringProperty(default="1")
    bpy.types.Object.list_group_channels = CollectionProperty(type=ChannelListPropertyGroup)
    bpy.types.Object.str_group_label = StringProperty(default="")
    
    bpy.types.Object.float_intensity = FloatProperty(
        name="Intensity",
        default=0.0,
        min=0.0,
        max=100.0,
        description="Intensity value",
        options={'ANIMATABLE'},
        update=intensity_updater
    )
    bpy.types.Object.float_vec_color = FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        size=3,
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        description='Color value. If your fixture is not an RGB fixture, but CMY, RGBA, or something like that, Sorcerer will automatically translate RGB to the correct color profile. The best way to tell Sorcerer which color profile is here on the object controller, to the right of this field. To make changes to many at a time, use the magic "Profile to Apply" feature on the top left of this box, or the "Apply Patch to Objects in Scene" button at the end of the group patch below this panel',
        update=color_updater
    )
    bpy.types.Object.float_vec_color_restore = FloatVectorProperty(
        name="Color (restore)",
        subtype='COLOR',
        size=3,
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        description="Why are there 2 colors for this one? Because remotely making relative changes to color doesn't work well. Influencers use relative changes for everything but color for this reason. This second color picker picks the color the influencer will restore channels to after passing over"
    )
    bpy.types.Object.float_volume = FloatProperty(
        name="Volume",
        default=0.0,
        min=0.0,
        max=100.0,
        description="Volume of microphone",
        options={'ANIMATABLE'}
    )
    bpy.types.Object.float_pan = FloatProperty(
        name="Pan",
        default=0.0,
        min=-100,
        max=100,
        description="Pan value",
        options={'ANIMATABLE'},
        update=pan_updater
    )
    bpy.types.Object.float_tilt = FloatProperty(
        name="Tilt",
        default=0.0,
        min=-100,
        max=100,
        description="Tilt value",
        options={'ANIMATABLE'},
        update=tilt_updater
    )
    bpy.types.Object.float_diffusion = FloatProperty(
        name="Diffusion",
        default=0.0,
        min=0,
        max=100.0,
        description="Diffusion value",
        options={'ANIMATABLE'},
        update=diffusion_updater
    )
    bpy.types.Object.float_strobe = FloatProperty(
        name="Shutter Strobe",
        default=0.0,
        min=0.0,
        max=100.0,
        description="Shutter strobe value",
        options={'ANIMATABLE'},
        update=strobe_updater
    )
    bpy.types.Object.float_zoom = FloatProperty(
        name="Zoom",
        default=0.0,
        min=0.0,
        max=100.0,
        description="Zoom value",
        options={'ANIMATABLE'},
        update=zoom_updater
    )
    bpy.types.Object.float_iris = FloatProperty(
        name="Iris",
        default=0.0,
        min=0.0,
        max=100.0,
        description="Iris value",
        options={'ANIMATABLE'},
        update=iris_updater
    )
    bpy.types.Object.float_edge = FloatProperty(
        name="Edge",
        default=0.0,
        min=0.0,
        max=100.0,
        description="Edge value",
        options={'ANIMATABLE'},
        update=edge_updater
    )
    bpy.types.Object.int_gobo_id = IntProperty(
        name="Gobo Selection",
        default=1,
        min=0,
        max=20,
        description="Gobo selection",
        options={'ANIMATABLE'},
        update=gobo_id_updater
    )
    bpy.types.Object.float_gobo_speed = FloatProperty(
        name="Gobo Speed",
        default=0.0,
        min=-300.0,
        max=300.0,
        description="Rotation of individual gobo speed",
        options={'ANIMATABLE'},
        update=gobo_speed_updater
    )
    bpy.types.Object.int_prism = IntProperty(
        name="Prism",
        default=0,
        min=0,
        max=1,
        description="Prism value. 1 is on, 0 is off",
        options={'ANIMATABLE'},
        update=prism_updater
    )
    
    bpy.types.Object.pan_min = IntProperty(
        default=-270, 
        description="Minimum value for pan"
    )
    bpy.types.Object.pan_max = IntProperty(
        default=270, 
        description="Maximum value for pan"
    )
    bpy.types.Object.tilt_min = IntProperty(
        default=-135, 
        description="Minimum value for tilt"
    )
    bpy.types.Object.tilt_max = IntProperty(
        default=135, 
        description="Maximum value for tilt"
    )
    bpy.types.Object.zoom_min = IntProperty(
        default=1, 
        description="Minimum value for zoom"
    )
    bpy.types.Object.zoom_max = IntProperty(
        default=100, 
        description="Maximum value for zoom"
    )
    bpy.types.Object.gobo_speed_min = IntProperty(
        default=-200, 
        description="Minimum value for speed"
    )
    bpy.types.Object.gobo_speed_max = IntProperty(
        default=200, 
        description="Maximum value for speed"
    )
    
    




    #--------------------------------------------------------------------------------------------
    '''VARIOUS OBJECT TYPES'''
    
    bpy.types.Object.influence = IntProperty(
        default=1, description="How many votes this controller gets when there are conflicts", min=1, max=10)
        
    bpy.types.Object.int_intro = IntProperty(
        default=25, description="How many frames it takes for influencer to fully activate on a channel", min=0, max=500)
        
    bpy.types.Object.int_outro = IntProperty(
        default=25, description="How many frames it takes for influencer to fully deactivate off a channel", min=0, max=500)  

    bpy.types.Object.pan_is_inverted = BoolProperty(default=True, description="Light is hung facing forward, for example, in FOH.")
    bpy.types.Object.last_hue = FloatProperty(default=0)
    bpy.types.Object.overdrive_mode = StringProperty(default="")
    bpy.types.Object.is_overdriven_left = BoolProperty(default=False)
    bpy.types.Object.is_overdriven_right = BoolProperty(default=False)
    bpy.types.Object.is_approaching_limit = BoolProperty(default=False)
    
    bpy.types.Object.influence_is_on = BoolProperty(default=False, description="Influence is enabled when checked")
    bpy.types.Object.audio_is_on = BoolProperty(default=False, description="Audio is enabled when checked")
    bpy.types.Object.mic_is_linked = BoolProperty(default=False, description="Microphone volume is linked to Intensity when red")
    bpy.types.Object.intensity_is_on = BoolProperty(default=True, description="Intensity is enabled when checked")
    bpy.types.Object.pan_tilt_is_on = BoolProperty(default=False, description="Pan/Tilt is enabled when checked")    
    bpy.types.Object.color_is_on = BoolProperty(default=False, description="Color is enabled when checked")
    bpy.types.Object.diffusion_is_on = BoolProperty(default=False, description="Diffusion is enabled when checked")
    bpy.types.Object.strobe_is_on = BoolProperty(default=False, description="Strobe is enabled when checked")
    bpy.types.Object.zoom_is_on = BoolProperty(default=False, description="Zoom is enabled when checked")
    bpy.types.Object.iris_is_on = BoolProperty(default=False, description="Iris is enabled when checked")
    bpy.types.Object.edge_is_on = BoolProperty(default=False, description="Edge is enabled when checked")
    bpy.types.Object.gobo_id_is_on = BoolProperty(default=False, description="Gobo ID is enabled when checked")
    bpy.types.Object.prism_is_on = BoolProperty(default=False, description="Prism is enabled when checked")
    
    bpy.types.Object.is_erasing = BoolProperty(name="Eraser", description="Erase instead of add")
    bpy.types.Object.influencer_list = CollectionProperty(type=InfluencerList)

    bpy.types.Object.int_fixture_index = IntProperty(default=0)
    bpy.types.Object.fixture_index_is_locked = BoolProperty(default=True)
    bpy.types.Object.mute = BoolProperty(default=False, description="Mute this object's OSC output")
    bpy.types.Object.str_manual_fixture_selection = StringProperty(
        name="Selected Light",
        description="Instead of the group selector to the left, simply type in what you wish to control here",
        update=manual_fixture_selection_updater
    )
    bpy.types.Object.str_call_fixtures_command = StringProperty(
        name="Call Fixtures Command",
        description="Command line text to focus moving fixtures onto stage object",
        update=call_fixtures_updater
    )
    bpy.types.Object.selected_group_enum = EnumProperty(
        name="Selected Group",
        description="Choose a group to control. Create these groups with the Patch function on the N tab in node editor, with USITT ASCII import in the same area, or create/modify them in Properties -> World -> SORCERER: Group Channel Blocks (full screen)",
        items=scene_groups
    )
    bpy.types.Object.selected_profile_enum = EnumProperty(
        name="Profile to Apply",
        description="Choose a fixture profile to apply to this fixture and any other selected fixtures. Build profiles in Blender's Properties viewport under World",
        items=scene_groups,
        update=group_profile_updater
    )
    bpy.types.Object.float_object_strength = FloatProperty(default=1, min=0, max=1)
    bpy.types.Object.red_is_on = BoolProperty(default=True, description="Disable or enable red output. Useful for trying to paint secondary colors")
    bpy.types.Object.green_is_on = BoolProperty(default=True, description="Disable or enable green output. Useful for trying to paint secondary colors")
    bpy.types.Object.blue_is_on = BoolProperty(default=True, description="Disable or enable blue output. Useful for trying to paint secondary colors")
    
    # For animation strips in sequencer
    bpy.types.ColorSequence.str_manual_fixture_selection = StringProperty(
        name="Selected Lights",
        description="Instead of the group selector to the left, simply type in what you wish to control here",
        update=manual_fixture_selection_updater
    )
    bpy.types.ColorSequence.selected_group_enum = EnumProperty(
        name="Selected Group",
        description="Choose a group to control. Create these groups with the Patch function on the N tab in node editor, with USITT ASCII import in the same area, or create/modify them in Properties -> World -> SORCERER: Group Channel Blocks (full screen)",
        items=scene_groups
    )
    bpy.types.ColorSequence.color_profile_enum = EnumProperty(
        name="Color Profile",
        description="Choose a color profile for the group",
        items=color_profiles,
    )

    # Assigned by group_info_updater on selected_group_enum property.
    bpy.types.ColorSequence.str_group_id =  StringProperty(default="1")
    bpy.types.ColorSequence.list_group_channels = CollectionProperty(type=ChannelListPropertyGroup)
    bpy.types.ColorSequence.str_group_label = StringProperty(default="")
    
    bpy.types.ColorSequence.influence = IntProperty(default=1, min=1, max=10, description="How many votes this controller has when there are conflicts", options={'ANIMATABLE'})
    bpy.types.ColorSequence.float_intensity = FloatProperty(default=0, min=0, max=100, description="Intensity value", options={'ANIMATABLE'}, update=intensity_updater)
    bpy.types.ColorSequence.float_vec_color = FloatVectorProperty(
        name="",
        subtype='COLOR',
        size=3,
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        description="Color value",
        update=color_updater
    )
    bpy.types.ColorSequence.float_diffusion = FloatProperty(default=0, min=0, max=100, description="Diffusion value", options={'ANIMATABLE'}, update=diffusion_updater)
    bpy.types.ColorSequence.float_pan = FloatProperty(default=0, min=-315, max=315, description="Pan value", options={'ANIMATABLE'}, update=pan_updater)
    bpy.types.ColorSequence.float_tilt = FloatProperty(default=0, min=-135, max=135, description="Tilt value", options={'ANIMATABLE'}, update=tilt_updater)
    bpy.types.ColorSequence.float_strobe = FloatProperty(default=0, min=0, max=100, description="Strobe value", options={'ANIMATABLE'}, update=strobe_updater)
    bpy.types.ColorSequence.float_zoom = FloatProperty(default=0, min=0, max=100, description="Zoom value", options={'ANIMATABLE'}, update=zoom_updater)
    bpy.types.ColorSequence.float_iris = FloatProperty(default=0, min=0, max=100, description="Iris value", options={'ANIMATABLE'}, update=iris_updater)
    bpy.types.ColorSequence.float_edge = FloatProperty(default=0, min=0, max=100, description="Edge value", options={'ANIMATABLE'}, update=edge_updater)
    bpy.types.ColorSequence.int_gobo_id = IntProperty(default=1, min=0, max=20, description="Gobo selection", options={'ANIMATABLE'}, update=gobo_id_updater)
    bpy.types.ColorSequence.float_gobo_speed = FloatProperty(default=0, min=-100, max=100, description="Rotation of individual gobo speed", options={'ANIMATABLE'}, update=gobo_speed_updater)
    bpy.types.ColorSequence.int_prism = IntProperty(default=0, min=0, max=1, description="Prism value. 1 is on, 0 is off", options={'ANIMATABLE'}, update=prism_updater)
    
    bpy.types.ColorSequence.pan_min = IntProperty(
        default=-270, 
        description="Minimum value for pan"
    )
    bpy.types.ColorSequence.pan_max = IntProperty(
        default=270, 
        description="Maximum value for pan"
    )
    bpy.types.ColorSequence.tilt_min = IntProperty(
        default=-135, 
        description="Minimum value for tilt"
    )
    bpy.types.ColorSequence.tilt_max = IntProperty(
        default=135, 
        description="Maximum value for tilt"
    )
    bpy.types.ColorSequence.zoom_min = IntProperty(
        default=1, 
        description="Minimum value for zoom"
    )
    bpy.types.ColorSequence.zoom_max = IntProperty(
        default=100, 
        description="Maximum value for zoom"
    )
    bpy.types.ColorSequence.gobo_speed_min = IntProperty(
        default=-200, 
        description="Minimum value for speed"
    )
    bpy.types.ColorSequence.gobo_speed_max = IntProperty(
        default=200, 
        description="Maximum value for speed"
    )
    
    bpy.types.ColorSequence.influence_is_on = BoolProperty(default=False, description="Influence is enabled when checked")
    bpy.types.ColorSequence.intensity_is_on = BoolProperty(default=True, description="Intensity is enabled when checked")
    bpy.types.ColorSequence.pan_tilt_is_on = BoolProperty(default=False, description="Pan/Tilt is enabled when checked")    
    bpy.types.ColorSequence.color_is_on = BoolProperty(default=False, description="Color is enabled when checked")
    bpy.types.ColorSequence.diffusion_is_on = BoolProperty(default=False, description="Diffusion is enabled when checked")
    bpy.types.ColorSequence.strobe_is_on = BoolProperty(default=False, description="Strobe is enabled when checked")
    bpy.types.ColorSequence.zoom_is_on = BoolProperty(default=False, description="Zoom is enabled when checked")
    bpy.types.ColorSequence.iris_is_on = BoolProperty(default=False, description="Iris is enabled when checked")
    bpy.types.ColorSequence.edge_is_on = BoolProperty(default=False, description="Edge is enabled when checked")
    bpy.types.ColorSequence.gobo_id_is_on = BoolProperty(default=False, description="Gobo ID is enabled when checked")
    bpy.types.ColorSequence.prism_is_on = BoolProperty(default=False, description="Prism is enabled when checked")
    
    bpy.types.ColorSequence.float_flash_intensity_up = FloatProperty(default=0, min=0, max=100, description="Intensity value", update=intensity_updater)
    bpy.types.ColorSequence.float_vec_flash_color_up = FloatVectorProperty(
        name="",
        subtype='COLOR',
        size=3,
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        description="Color value",
        update=color_updater
    )    
    bpy.types.ColorSequence.float_flash_pan_up = FloatProperty(default=0, min=-315, max=315, description="Pan value", update=pan_updater)
    bpy.types.ColorSequence.float_flash_tilt_up = FloatProperty(default=0, min=-135, max=135, description="Tilt value", update=tilt_updater)
    bpy.types.ColorSequence.float_flash_strobe_up = FloatProperty(default=0, min=0, max=100, description="Strobe value", update=strobe_updater)
    bpy.types.ColorSequence.float_flash_zoom_up = FloatProperty(default=0, min=0, max=100, description="Zoom value", update=zoom_updater)
    bpy.types.ColorSequence.float_flash_iris_up = FloatProperty(default=0, min=0, max=100, description="Iris value", update=iris_updater)
    bpy.types.ColorSequence.int_flash_gobo_id_up = IntProperty(default=1, min=0, max=20, description="Gobo selection", update=gobo_id_updater)
    
    bpy.types.ColorSequence.float_flash_intensity_down = FloatProperty(default=0, min=0, max=100, description="Intensity value", update=intensity_updater)
    bpy.types.ColorSequence.float_vec_flash_color_down = FloatVectorProperty(
        name="",
        subtype='COLOR',
        size=3,
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        description="Color value",
        update=color_updater
    )    
    bpy.types.ColorSequence.float_flash_pan_down = FloatProperty(default=0, min=-315, max=315, description="Pan value", update=pan_updater)
    bpy.types.ColorSequence.float_flash_tilt_down = FloatProperty(default=0, min=-135, max=135, description="Tilt value", update=tilt_updater)
    bpy.types.ColorSequence.float_flash_strobe_down = FloatProperty(default=0, min=0, max=100, description="Strobe value", update=strobe_updater)
    bpy.types.ColorSequence.float_flash_zoom_down = FloatProperty(default=0, min=0, max=100, description="Zoom value", update=zoom_updater)
    bpy.types.ColorSequence.float_flash_iris_down = FloatProperty(default=0, min=0, max=100, description="Iris value", update=iris_updater)
    bpy.types.ColorSequence.int_flash_gobo_id_down = IntProperty(default=1, min=0, max=20, description="Gobo selection", update=gobo_id_updater)
        
    bpy.types.Scene.lighting_modifiers = CollectionProperty(type=LightingModifier)
    bpy.types.Scene.active_modifier_index = IntProperty(default=-1)

    if depsgraph_update_handler not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(depsgraph_update_handler)

    # Commenting this out until harmonizer is replaced with harmonizer_two per spam issue
    #bpy.app.handlers.frame_change_pre.append(load_changes_handler)
    #bpy.app.handlers.frame_change_post.append(publish_changes_handler)
        
    bpy.app.handlers.depsgraph_update_post.append(mixer_update_handler)

    
def unregister():
    # Handlers
#    if publish_changes_handler in bpy.app.handlers.frame_change_post:
#        bpy.app.handlers.frame_change_post.remove(publish_changes_handler)
#    if load_changes_handler in bpy.app.handlers.frame_change_pre:
#        bpy.app.handlers.frame_change_pre.remove(load_changes_handler)

    bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update_handler)
    bpy.app.handlers.depsgraph_update_post.remove(mixer_update_handler)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    # Object
    del bpy.types.Object.int_misc_effect
    del bpy.types.Object.int_prism
    del bpy.types.Object.float_gobo_speed
    del bpy.types.Object.int_gobo_id
    del bpy.types.Object.float_edge
    del bpy.types.Object.float_iris
    del bpy.types.Object.float_zoom
    del bpy.types.Object.float_strobe
    del bpy.types.Object.float_diffusion
    del bpy.types.Object.float_tilt
    del bpy.types.Object.float_pan
    del bpy.types.Object.pan_tilt_graph_checker
    del bpy.types.Object.float_vec_pan_tilt_graph
    del bpy.types.Object.float_vec_color
    del bpy.types.Object.float_intensity
    del bpy.types.Object.float_influence_checker
    del bpy.types.Object.prism_checker
    del bpy.types.Object.misc_effect_checker
    del bpy.types.Object.float_speed_checker
    del bpy.types.Object.gobo_id_checker
    del bpy.types.Object.float_diffusion_checker
    del bpy.types.Object.float_iris_checker
    del bpy.types.Object.float_zoom_checker
    del bpy.types.Object.float_strobe_checker
    del bpy.types.Object.float_tilt_checker
    del bpy.types.Object.float_pan_checker
    del bpy.types.Object.float_intensity_checker
    del bpy.types.Object.str_disable_prism_argument
    del bpy.types.Object.str_enable_prism_argument
    del bpy.types.Object.str_gobo_id_argument
    del bpy.types.Object.str_disable_gobo_speed_argument
    del bpy.types.Object.str_enable_gobo_speed_argument
    del bpy.types.Object.str_disable_strobe_argument
    del bpy.types.Object.str_enable_strobe_argument
    del bpy.types.Object.relevant_channels_checker

    del bpy.types.ColorSequence.selected_group_enum
    del bpy.types.ColorSequence.influence
    del bpy.types.ColorSequence.float_intensity
    del bpy.types.ColorSequence.float_vec_color
    del bpy.types.ColorSequence.float_diffusion
    del bpy.types.ColorSequence.float_pan
    del bpy.types.ColorSequence.float_tilt
    del bpy.types.ColorSequence.float_strobe
    del bpy.types.ColorSequence.float_zoom
    del bpy.types.ColorSequence.float_iris
    del bpy.types.ColorSequence.float_edge
    del bpy.types.ColorSequence.int_gobo_id
    del bpy.types.ColorSequence.float_gobo_speed
    del bpy.types.ColorSequence.int_prism
    del bpy.types.ColorSequence.influence_is_on
    del bpy.types.ColorSequence.intensity_is_on
    del bpy.types.ColorSequence.pan_tilt_is_on
    del bpy.types.ColorSequence.color_is_on
    del bpy.types.ColorSequence.diffusion_is_on
    del bpy.types.ColorSequence.strobe_is_on
    del bpy.types.ColorSequence.zoom_is_on
    del bpy.types.ColorSequence.iris_is_on
    del bpy.types.ColorSequence.edge_is_on
    del bpy.types.ColorSequence.gobo_id_is_on
    del bpy.types.ColorSequence.prism_is_on
    del bpy.types.ColorSequence.osc_color
    del bpy.types.ColorSequence.osc_intensity
    del bpy.types.Object.is_approaching_limit
    del bpy.types.Object.is_overdriven_right
    del bpy.types.Object.is_overdriven_left
    del bpy.types.Object.overdrive_mode
    del bpy.types.Object.last_hue
    del bpy.types.Object.pan_is_inverted
    del bpy.types.Object.is_influencer
    del bpy.types.Object.int_outro
    del bpy.types.Object.int_intro
    del bpy.types.Object.influence


# For development purposes only
if __name__ == "__main__":
    register()
