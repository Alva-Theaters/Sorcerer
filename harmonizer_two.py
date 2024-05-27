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
    
    
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(module)s - line %(lineno)d - %(message)s'
)


def sorcerer_assert_unreachable(*args):
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
        ('Set Piece', "Set Piece", "Select the lights on a specific set piece by selecting the set piece, not a light-board group.", 'HOME', 3),
        ('Brush', "Brush", "Move this object over fixtures for a paint brush effect. Changes persist when the object leaves.", 'BRUSH_DATA', 4)
    ]
    
    return items

# This stores the channel list for each set piece, group controller, strip, etc.
class ChannelListPropertyGroup(PropertyGroup):
    value: IntProperty()


def send_osc(address, argument):
    scene = bpy.context.scene.scene_props
    ip_address = scene.str_osc_ip_address
    port = scene.int_osc_port
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


def is_inside_mesh(obj, mesh_obj):
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

def get_lights_inside_mesh(mesh_obj):
    """Get all light objects inside the volume of mesh_obj."""
    lights_inside = [obj for obj in bpy.data.objects if obj.type == 'MESH' and not obj.hide_viewport and is_inside_mesh(obj, mesh_obj)]
    return lights_inside


def lamp_objects(self, context):
    items = []

    if context.scene.scene_props.group_data:
        try:
            group_data = eval(context.scene.scene_props.group_data)
            for group_number, group_info in group_data.items():
                label = "{}: Group {}".format(group_info['label'], group_number)
                items.append((str(group_number), label, label))
        except SyntaxError as e:
            print("Error parsing scene.group_data:", e)

    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.get("is_influencer"):
            label = "INFLUENCER: {}".format(obj.name)
            items.append((obj.name, label, label))
            
    return items


def fixture_profiles(self, context):
    items = []

    if context.scene.scene_props.group_data:
        try:
            group_data = eval(context.scene.scene_props.group_data)
            for group_number, group_info in group_data.items():
                label = "{}: Group {}".format(group_info['label'], group_number)
                items.append((str(group_number), label, label))
        except SyntaxError as e:
            print("Error parsing scene.group_data:", e)

    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.get("is_influencer"):
            label = "INFLUENCER: {}".format(obj.name)
            items.append((obj.name, label, label))
            
    return items


def group_objects(self, context):
    items = []

    if context.scene.scene_props.group_data:
        try:
            group_data = eval(context.scene.scene_props.group_data)
            for group_number, group_info in group_data.items():
                label = "{}: Group {}".format(group_info['label'], group_number)
                items.append((str(group_number), label, label))
        except SyntaxError as e:
            print("Error parsing scene.group_data:", e)

    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.get("is_influencer"):
            label = "INFLUENCER: {}".format(obj.name)
            items.append((obj.name, label, label))
            
    return items


def group_info_updater(self, context):
    scene = context.scene.scene_props
    
    try:
        group_data_dict = ast.literal_eval(scene.group_data)
    except ValueError as e:
        # Handle the case where conversion fails.
        print(f"Error converting scene.group_data to dictionary: {e}")
        return

    try:
        group_id = int(self.str_selected_light)
    except ValueError:
        self.str_group_id = ""
        self.str_group_label = ""
        self.list_group_channels = []
        return
    
    if group_id in group_data_dict:
        group_data = group_data_dict[group_id]
        
        self.str_group_id = str(group_id)
        self.str_group_label = group_data.get('label', '')
        channels_list = group_data.get('channels', []) 
        self.list_group_channels.clear()
        for chan in channels_list:
            item = self.list_group_channels.add()
            item.value = chan
        
    else: 
        group_id = str(group_id)
        if group_id in group_data_dict:
            group_data = group_data_dict[group_id]
            self.str_group_id = str(group_id) 
            channels_list = group_data.get('channels', []) 
            self.list_group_channels.clear()
            for chan in channels_list:
                item = self.list_group_channels.add()
                item.value = chan
            
        else:
            self.str_group_id = ""
            self.str_group_label = ""
            self.list_group_channels = []
            
            
def group_info_updater_mixer(self, context):
    scene = context.scene.scene_props
    
    try:
        group_data_dict = ast.literal_eval(scene.group_data)
    except ValueError as e:
        print(f"Error converting scene.group_data to dictionary: {e}")
        return

    group_id_str = str(self.str_selected_group)

    if group_id_str in group_data_dict:
        group_data = group_data_dict[group_id_str]
        
        self.str_group_id = group_id_str 
        self.str_group_label = group_data.get('label', '')
        channels_list = group_data.get('channels', [])
        self.list_group_channels.clear()
        for chan in channels_list:
            item = self.list_group_channels.add()
            item.value = chan
        
    else:
        self.str_group_id = ""
        self.str_group_label = ""
        self.list_group_channels = ""
        self.label = "INFLUENCER Mixer"
        return 

    if hasattr(self, "parameters_enum"):    
        if self.parameters_enum == 'option_intensity':
            self.label=f"Group {self.str_group_id}: {self.str_group_label} Intensity Mixer"
        elif self.parameters_enum == 'option_color':
            self.label=f"Group {self.str_group_id}: {self.str_group_label} Color Mixer"
        elif self.parameters_enum == 'option_pan_tilt':
            self.label=f"Group {self.str_group_id}: {self.str_group_label} Pan/Tilt Mixer"
            
            
def manual_fixture_selection_updater(self, context):
    if self.str_manual_fixture_selection != "":
            channels_list = parse_channels(self.str_manual_fixture_selection)
            self.list_group_channels.clear()
            for chan in channels_list:
                item = self.list_group_channels.add()
                item.value = chan


###################
# HARMONIZER
###################
class HarmonizerBase:
    INFLUENCER = 'influencer'
    CHANNEL = 'channel'
    GROUP = 'group'
    MIXER = 'mixer'
    PAN_TILT = 'pan_tilt'


class HarmonizerPublisher(HarmonizerBase):
    def __init__(self):
        self.change_requests = []
          
        
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
        v = str(int(v))
        if len(v) == 1:
            v = f"0{v}"
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
            "option_rgb": ["$1", "$2", "$3"],
            "option_cmy": ["$1", "$2", "$3"],
            "option_rgbw": ["$1", "$2", "$3", "$4"],
            "option_rgba": ["$1", "$2", "$3", "$4"],
            "option_rgbl": ["$1", "$2", "$3", "$4"],
            "option_rgbaw": ["$1", "$2", "$3", "$4", "$5"],
            "option_rgbam": ["$1", "$2", "$3", "$4", "$5"]
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
        if bpy.context.scene.scene_props.is_playing:
            self.change_requests.append(c, p, v, i, a)  
        else:
            address, argument = self.form_osc(c, p, v, i, a)  # Should return 2 strings
            send_osc(address, argument)
        
        
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
            print(parent.pan_max)
            return min_value, max_value
        except AttributeError as e:
            print(f"Error in find_my_min_max: {e}")
            return None, None

         
    def map_value(self, parent, chan, p, unmapped_value, type):
        min_val, max_val = self.find_my_min_max(parent, chan, type, p)
        print(f"Input min/max: {min_val, max_val}")
        print(f"Unmapped value: {unmapped_value}")
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
                print(f"Mapped value 1: {mapped_value}")
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
                print(f"Mapped value 2: {mapped_value}")
            return mapped_value
        else: sorcerer_assert_unreachable()
    
       
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
            progress = motor_node.float_progress
            
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
            sorcerer_assert_unreachable()

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
        
    def mix_my_values(self, parent, p):
        """Recieves a bpy object mesh, parent, and returns three lists for channels list (c), parameters list, 
           and values list (v)"""
        # Define variables
        channels_list = parent.list_group_channels
        values_list = parent.parameters
        channels = [item.value for item in channels_list]
        offset = parent.float_offset * 0.5
        subdivisions = parent.int_subdivisions
        mode = parent.mix_method_enum
        param_mode = p
        if p == "color":
            p = "vec_color"
        parameter_name = f"float_{p}"
        
        # Establish and then subdivide values list
        values = [getattr(choice, parameter_name) for choice in values_list]
        values = self.subdivide_values(subdivisions, values)
        
        # Establish channels list, sort channels and values list, mix values, and then scale values
        sorted_channels, sorted_values = self.sort(channels, values)
        mixed_values = self.mix_values(mode, sorted_channels, sorted_values, subdivisions, channels, param_mode, offset, parent)
        scaled_values = self.scale(parent, param_mode, mixed_values)
        
        # Establish parameters list
        p = [p for _ in channels]
        
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

        
    def split_color(self, parent, c, v, type):
        """
        Splits the input (r, g, b) tuple for value (v) into tuples like (r, g, b, a, m)
        for the value entries and updates the parameter (p) value for each entry to the 
        color profile (pf) enumerator option found with find_my_patch().
        
        This function prepares the parameters and values for later processing by the 
        find_my_argument() function, ensuring that the correct argument is formed based 
        on the received v tuple. The updated parameter p reflects the color_profile choice,
        allowing the publisher to interpret the v tuple correctly.
        
        Parameters:
            parent: The parent controller object.
            c: The channel list.
            v: The value list.
            type: The controller type.

        Returns:
            new_p: The updated parameter list.
            new_v: The updated value list.
        """
        new_p = []
        new_v = []
        
        for chan, val in zip(c, v):  # 4chan lol
            pf = find_my_patch(parent, chan, type, "color_profile_enum")
            profile_converters = {
                'option_rgba': (self.rgba_converter, 4),
                'option_rgbw': (self.rgbw_converter, 4),
                'option_rgbaw': (self.rgbaw_converter, 5),
                'option_rgbl': (self.rgbl_converter, 4),
                'option_cmy': (self.cmy_converter, 3),
                'option_rgbam': (self.rgbam_converter, 5),
            }

            if pf == 'option_rgb':
                new_p.append(pf)
                new_v.append(val)
            elif pf in profile_converters:
                converter, num_values = profile_converters[pf]
                converted_values = converter(*val[:3])
                
                new_p.append(pf)
                new_v.append(converted_values[:num_values])
            else: raise ValueError(f"Unknown color profile: {pf}")

        return new_p, new_v
    
    
class HarmonizerFinders(HarmonizerBase): ## This must cater to individual fixtures
    def find_my_argument_template(self, parent, chan, param, type):
        if bpy.context.scene.scene_props.console_type_enum == "option_eos":
            if type not in ["Influencer", "Brush"]:
                color_templates = {
                    "option_rgb": "# Red at $1 Enter, # Green at $2 Enter, # Blue at $3 Enter",
                    "option_cmy": "# Cyan at $1 Enter, # Magenta at $2 Enter, # Yellow at $3 Enter",
                    "option_rgbw": "# Red at $1 Enter, # Green at $2 Enter, # Blue at $3 Enter, # White at $4 Enter",
                    "option_rgba": "# Red at $1 Enter, # Green at $2 Enter, # Blue at $3 Enter, # Amber at $4 Enter",
                    "option_rgbl": "# Red at $1 Enter, # Green at $2 Enter, # Blue at $3 Enter, # Lime at $4 Enter",
                    "option_rgbaw": "# Red at $1 Enter, # Green at $2 Enter, # Blue at $3 Enter, # Amber at $4 Enter, # White at $5 Enter",
                    "option_rgbam": "# Red at $1 Enter, # Green at $2 Enter, # Blue at $3 Enter, # Amber at $4 Enter, # Mint at $5 Enter"
                }
                if param in color_templates:
                    return color_templates[param]

                else:
                    return getattr(bpy.context.scene.scene_props, f"str_{param}_argument")
            else:
                return getattr(bpy.context.scene.scene_props, f"str_relative_{p}_argument")
            
            
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
                else: sorcerer_assert_unreachable()
            elif parent.type == 'COLOR':  # Color strip
                return "strip"
            elif parent.type == 'CUSTOM':  
                controller_types = {
                'group_controller_type': "group",
                'mixer_type': "mixer",
                }
                return controller_types.get(parent.bl_idname, None)
        else: 
            sorcerer_assert_unreachable()
        
        
    """Recieves a bpy object mesh, parent, and returns a list representing channels within that mesh"""
    def find_influencer_current_channels(parent):
        # Use the get_lights_within_mesh function in the library to get channels, then add them to its captured_set().
        return current_channels
        
        
    """Recieves a bpy object mesh (parent), and returns two lists representing channels that used to be 
       within that mesh but just left, as well as new additions."""   
    def find_influencer_channels_to_change(parent, current_channels, context):
        # Compare current channels with the object's captured_set()
        return channels_to_restore, channels_to_add
        
        
    """Recieves a bpy object mesh (parent), and parameter, and returns a list of restore values"""
    def find_my_restore_values(channels_to_restore, p, context):
        # Use the background property registered on the objects to restore.
        return restore_values
    
    
    def color_object_to_tuple(self, v):
        """
        This function converts an RGB color object into a tuple.
        """
        return (v.r * 100, v.g * 100, v.b * 100)


    """Recieves a bpy object mesh (parent), and parameter, and returns integers in a [list]
       This is for single fixtures."""
    def find_my_value(self, parent, p, type):
        # Use effects to mix up values inside a group, or simply return a single integer
        attribute_name = parameter_mapping.get(p)
        if attribute_name:
            unmapped_value = getattr(parent, attribute_name)
            if p in ["pan", "tilt", "zoom", "gobo_speed", "pan_tilt"]:
                mapping = HarmonizerMappers()
                try: 
                    value = mapping.map_value(parent, p, unmapped_value, type)
                    return value
                except AttributeError:
                    print("Error in find_my_value when attempting to call map_value.")
            return unmapped_value
        else:
            return None


    """Recieves a bpy object mesh (parent), and parameter, and returns two lists for channels list (c) and values list (v)"""
    def find_my_group_values(self, parent, p):
        # Use effects to mix up values inside a group, or simply return a simple value
        channels = []
        parameters = []
        values = []
        
        attribute_name = parameter_mapping.get(p)
        if attribute_name:  # Find and map value
            new_value = getattr(parent, attribute_name)
            
            if p == "color":
                new_value = self.color_object_to_tuple(new_value)
            
            mapping = HarmonizerMappers()
            for chan in parent.list_group_channels:
                channels.append(chan.value)
                parameters.append(p)
                if p in ["pan", "tilt", "zoom", "gobo_speed", "pan_tilt"]:
                    value_to_add = mapping.map_value(parent, chan, p, new_value, type)
                    values.append(value_to_add)
                else:
                    values.append(new_value)
            return channels, parameters, values
        
        else: sorcerer_assert_unreachable()
    
        
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
            current_channels = parent.find_influencer_current_channels(parent)  # Should return a list.
            channels_to_restore, channels_to_add = find_influencer_channels_to_change(parent, current_channels)  # Should return a list
            add_value = parent.find_my_value(parent, p)  # Should return a list with just one [integer].
            restore_values = parent.find_my_restore_values(parent, p)
            c = new_channels + channels_to_restore
            v = add_values + restore_values
            return c, p, v, controller_type
        
        elif controller_type == "Fixture":
            value = self.find_my_value(parent, p, type)
            return [parent.int_object_channel_index], [p], [value], controller_type
        
        elif controller_type in  ["group", "strip", "Set Piece"]:
            c, p, v = self.find_my_group_values(parent, p)
            return c, p, v, controller_type
        
        elif controller_type == "mixer":
            mixing = HarmonizerMixer()
            c, p, v = mixing.mix_my_values(parent, p)
            return c, p, v, controller_type
                    
        else: sorcerer_assert_unreachable()
    
    
def find_my_patch(parent, chan, type, desired_property):
    """
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
        type: the controllertype of parent controller object, can be mixer, group node, set piece, etc.
        desired_property: the patch property that is being requested, in string form
        
    Returns:
        desired_property: The value of the requested property
    """
    if type not in ["Fixture", "Pan/Tilt Fixture"]:
        for obj in bpy.data.objects:
            if obj.int_fixture_index == chan:
                return getattr(obj, desired_property)
            
    else: return getattr(chan, desired_property)
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
        p, v = color_splitter.split_color(parent, c, v, type)

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
pan_tilt_partial = partial(universal_updater, property_name="pan_tilt", find_function=harmonizer_instance.find_my_channels_and_values)

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
def pan_tilt_updater(self, context):
    return pan_tilt_partial(self, context)

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
# NODE SOCKETS
###################
class AlvaNodeTree(bpy.types.NodeTree):
    bl_idname = 'AlvaNodeTree'
    bl_label = 'Sorcerer Nodes'
    bl_icon = 'NODETREE'
    

class MixerInputSocket(NodeSocket):
    bl_idname = 'MixerInputType'
    bl_label = 'Mixer Input Socket'

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (.5, 0, 1, 1)  


class MixerOutputSocket(NodeSocket):
    bl_idname = 'MixerOutputType'
    bl_label = 'Mixer Input Socket'

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (.5, 0, 1, 1)  
   
    
class GroupOutputSocket(NodeSocket):
    bl_idname = 'GroupOutputType'
    bl_label = 'Group Output Socket'

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (1, 0, 1, 1)  
    
    
class GroupInputSocket(NodeSocket):
    bl_idname = 'GroupInputType'
    bl_label = 'Group Input Socket'

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (1, 0, 1, 1) 
    
    
class MasterInputSocket(NodeSocket):
    bl_idname = 'MasterInputType'
    bl_label = 'Master Input Socket'

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (1, 1, 1, 1) 
    
    
class MasterOutputSocket(NodeSocket):
    bl_idname = 'MasterOutputType'
    bl_label = 'Master Output Socket'

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (1, 1, 1, 1)
    
    
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

    # Assigned by group_info_updater on str_selected_light property.
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
    speed_min: IntProperty(default=-200, description="Minimum value for speed")
    speed_max: IntProperty(default=200, description="Maximum value for speed")

    # Selected group and color profile enumerators.
    str_selected_light: EnumProperty(
        name="Selected Light",
        description="Choose a group to control. Create these groups with the Patch function on the N tab in node editor, with USITT ASCII import in the same area, or create/modify them in Properties -> World -> SORCERER: Group Channel Blocks (full screen).",
        items=lamp_objects,
        update=group_info_updater
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
    intensity_is_on: BoolProperty(default=False, description="Intensity is enabled when checked")
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
        self.inputs.new('GroupInputType', "Driver Input")
        self.inputs.new('GroupInputType', "Driver Input")
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
            if not self.str_selected_light:
                row.alert = 1
            row.prop(self, "str_selected_light", text="", icon_only=False, icon='LIGHT')
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
        update=group_info_updater_mixer,
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
    str_selected_group: EnumProperty(
        name="Selected Group",
        description="Choose a group to control. Create these groups with the Patch function on the N tab in node editor, with USITT ASCII import in the same area, or create/modify them in Properties -> World -> SORCERER: Group Channel Blocks (full screen).",
        items=group_objects,
        update=group_info_updater_mixer
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
        self.inputs.new('MixerInputType', "Driver Input")
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
                row.prop(self, "str_selected_group", icon='COLLECTION_NEW', icon_only=0, text="")
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
    MixerInputSocket,
    MixerOutputSocket,
    MasterOutputSocket,
    MasterInputSocket,
    GroupInputSocket,
    MotorInputSocket,
    MotorOutputSocket,
    GroupOutputSocket,
    FlashOutSocket,
    AlvaNodeTree,    
    GroupControllerNode,
    MixerParameters,
    MixerNode,
    LightingModifier
)

    
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    ##################################################################################
    '''Registering the object props directly on object to preserve self-association'''
    ##################################################################################
        
    bpy.types.Object.relevant_channels_checker = StringProperty(default="")
    
    
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
        description="Choose a color profile for the group",
        items=color_profiles,
    )
    bpy.types.Object.object_identities_enum = EnumProperty(
        name="Identity",
        description="Choose an identity for the object",
        items=object_identities,
    )
    
    # Assigned by group_info_updater on str_selected_light property.
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
        description="Color value",
        update=color_updater
    )
    bpy.types.Object.float_vec_pan_tilt_graph = FloatVectorProperty(
        name="",
        subtype='COLOR',
        size=3,
        default=(.2, .2, .2),
        min=0.0,
        max=.2,
        update=pan_tilt_updater
    )
    bpy.types.Object.pan_tilt_graph_checker = FloatVectorProperty(
        name="",
        subtype='COLOR',
        size=3,
        default=(.2, .2, .2),
        min=0.0,
        max=.2
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
    bpy.types.Object.intensity_is_on = BoolProperty(default=False, description="Intensity is enabled when checked")
    bpy.types.Object.pan_tilt_is_on = BoolProperty(default=False, description="Pan/Tilt is enabled when checked")    
    bpy.types.Object.color_is_on = BoolProperty(default=False, description="Color is enabled when checked")
    bpy.types.Object.diffusion_is_on = BoolProperty(default=False, description="Diffusion is enabled when checked")
    bpy.types.Object.strobe_is_on = BoolProperty(default=False, description="Strobe is enabled when checked")
    bpy.types.Object.zoom_is_on = BoolProperty(default=False, description="Zoom is enabled when checked")
    bpy.types.Object.iris_is_on = BoolProperty(default=False, description="Iris is enabled when checked")
    bpy.types.Object.edge_is_on = BoolProperty(default=False, description="Edge is enabled when checked")
    bpy.types.Object.gobo_id_is_on = BoolProperty(default=False, description="Gobo ID is enabled when checked")
    bpy.types.Object.prism_is_on = BoolProperty(default=False, description="Prism is enabled when checked")

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
        description="Command line text to focus moving fixtures onto set piece"
    )
    bpy.types.Object.str_selected_light = EnumProperty(
        name="Selected Group",
        description="Choose a group to control. Create these groups with the Patch function on the N tab in node editor, with USITT ASCII import in the same area, or create/modify them in Properties -> World -> SORCERER: Group Channel Blocks (full screen)",
        items=lamp_objects,
        update=group_info_updater
    )
    bpy.types.Object.str_selected_profile = EnumProperty(
        name="Profile to Apply",
        description="Choose a fixture profile to apply to this fixture and any other selected fixtures. Build profiles in Blender's Properties viewport under World",
        items=fixture_profiles
    )
    bpy.types.Object.float_object_strength = FloatProperty(default=1, min=0, max=1)
    
    # For animation strips in sequencer
    bpy.types.ColorSequence.str_manual_fixture_selection = StringProperty(
        name="Selected Lights",
        description="Instead of the group selector to the left, simply type in what you wish to control here",
        update=manual_fixture_selection_updater
    )
    bpy.types.ColorSequence.str_selected_light = EnumProperty(
        name="Selected Group",
        description="Choose a group to control. Create these groups with the Patch function on the N tab in node editor, with USITT ASCII import in the same area, or create/modify them in Properties -> World -> SORCERER: Group Channel Blocks (full screen)",
        items=lamp_objects,
        update=group_info_updater
    )
    bpy.types.ColorSequence.color_profile_enum = EnumProperty(
        name="Color Profile",
        description="Choose a color profile for the group",
        items=color_profiles,
    )

    # Assigned by group_info_updater on str_selected_light property.
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
    bpy.types.ColorSequence.speed_min = IntProperty(
        default=-200, 
        description="Minimum value for speed"
    )
    bpy.types.ColorSequence.speed_max = IntProperty(
        default=200, 
        description="Maximum value for speed"
    )
    
    bpy.types.ColorSequence.influence_is_on = BoolProperty(default=False, description="Influence is enabled when checked")
    bpy.types.ColorSequence.intensity_is_on = BoolProperty(default=False, description="Intensity is enabled when checked")
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

#    bpy.app.handlers.depsgraph_update_pre.append(influencer_deps_updater)
#    bpy.app.handlers.frame_change_pre.append(influencer_deps_updater)

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
#    if influencer_deps_updater in bpy.app.handlers.frame_change_pre:
#        bpy.app.handlers.frame_change_pre.remove(influencer_deps_updater)
#    if influencer_deps_updater in bpy.app.handlers.depsgraph_update_pre:
#        bpy.app.handlers.depsgraph_update_pre.remove(influencer_deps_updater)

    bpy.app.handlers.depsgraph_update_post.remove(update_handler)

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

    del bpy.types.ColorSequence.str_selected_light
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
