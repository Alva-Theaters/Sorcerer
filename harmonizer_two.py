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


'''
=====================================================================
This is the third major iteration of the harmonizer. It is not yet
complete. It will replace the entire existing harmonizer.py.
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

# This stores the channel list for each set piece, group controller, strip, etc.
class ChannelListPropertyGroup(PropertyGroup):
    value: IntProperty()


# Purpose of this throughout the codebase is to proactively identify possible pre-bugs and to help diagnose bugs.
def sorcerer_assert_unreachable(*args):
    caller_frame = inspect.currentframe().f_back
    caller_file = caller_frame.f_code.co_filename
    caller_line = caller_frame.f_lineno
    message = "Error found at {}:{}\nCode marked as unreachable has been executed. Please report bug to Alva Theaters.".format(caller_file, caller_line)
    print(message)


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

        
###################
# COLOR CONVERTERS
###################
def calculate_closeness(rgb_input, target_rgb, sensitivity=1.0):
    diff = sum(abs(input_c - target_c) for input_c, target_c in zip(rgb_input, target_rgb))
    normalized_diff = diff / (300 * sensitivity)
    closeness_score = max(0, min(1, 1 - normalized_diff))
    return closeness_score


def rgb_converter(scene, red, green, blue):
    return red, green, blue
    
        
def rgba_converter(scene, red, green, blue):
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

    
def rgbw_converter(scene, red, green, blue):
    white_similarity = min(red, green, blue) / 100
    white_peak = 75 + (25 * white_similarity)  # Peaks at 100 for pure white.

    white = round(white_peak * white_similarity)
    
    return red, green, blue, white


def rgbaw_converter(scene, red, green, blue, amber_sensitivity=1.0, white_sensitivity=1.0):
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


def rgbl_converter(scene, red, green, blue):
    lime = 0
    
    # Lime peaks at 100 for yellow (100, 100, 0) and white (100, 100, 100).
    if red == 100 and green == 100:
        lime = 100
    # For other combinations, calculate lime based on the lesser of red and green, but only if blue is not dominant.
    elif blue < red and blue < green:
        lime = round((min(red, green) / 100) * 100)
    
    return red, green, blue, lime


def rgbam_converter(scene, red, green, blue):
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


def cmy_converter(scene, red, green, blue):
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


###################
# MIXER LOGIC
###################
def interpolate(value_start, value_end, steps):
    return [value_start + x * (value_end - value_start) / (steps - 1) for x in range(steps)]


def calculate_mixed_values(channel_list, mode, value_one, value_two, value_three):
    if isinstance(channel_list, str):
        channel_list = [int(chan.strip()) for chan in channel_list.split(',') if chan.strip().isdigit()]
    
    elif all(isinstance(chan, bpy.types.Object) for chan in channel_list):
        channel_list = sorted(channel_list, key=lambda obj: obj.name)
        channel_list = [obj.name for obj in channel_list]
    else:
        channel_list = sorted(channel_list)
   
    sorted_channels = sorted(channel_list)
    mixed_values = []

    if value_two is None and mode == "alternate":
        # Alternating between value_one and value_three for each channel.
        for counter, chan in enumerate(sorted_channels, start=1):
            chan_value = value_three if counter % 2 == 0 else value_one
            mixed_values.append((chan, chan_value))

    elif value_two is None:
        # Interpolating between value_one and value_three for the channel list.
        num_channels = len(sorted_channels)
        for index, chan in enumerate(sorted_channels):
            ratio = index / (num_channels - 1) if num_channels > 1 else 0
            chan_value = ((1 - ratio) * value_one + ratio * value_three)
            mixed_values.append((chan, chan_value))

    else:
            num_channels = len(sorted_channels)
            mid_index = num_channels // 2

            for index, chan in enumerate(sorted_channels):
                if num_channels % 2 == 1:  # If odd number of channels.
                    if index == mid_index:
                        chan_value = value_two
                    elif index < mid_index:
                        # Interpolate between value_one and value_two.
                        ratio = index / mid_index
                        chan_value = (1 - ratio) * value_one + ratio * value_two
                    else:
                        # Interpolate between value_two and value_three.
                        ratio = (index - mid_index) / mid_index
                        chan_value = (1 - ratio) * value_two + ratio * value_three
                else:  # If even number of channels, treat the two middle indices as value_two.
                    if index == mid_index or index == mid_index - 1:
                        chan_value = value_two
                    elif index < mid_index:
                        # Interpolate between value_one and value_two.
                        ratio = index / (mid_index - 1)
                        chan_value = (1 - ratio) * value_one + ratio * value_two
                    else:
                        # Interpolate between value_two and value_three.
                        ratio = (index - mid_index) / (mid_index - 1)
                        chan_value = (1 - ratio) * value_two + ratio * value_three

                mixed_values.append((chan, chan_value))

    return mixed_values


class HarmonizerBase:
    INFLUENCER = 'influencer'
    CHANNEL = 'channel'
    GROUP = 'group'
    MIXER = 'mixer'
    PAN_TILT = 'pan_tilt'


class HarmonizerPublisher(HarmonizerBase):
    def __init__(self):
        self.change_requests = []
    
    def send_cpvia(self, c, p, v, i, a):
        """
        Decides whether to send osc now (we are not playing back) or later (we are playing back).

        Parameters:
        cpvia: channel, parameter, value, influence, argument template.

        This function does not return a value.
        """
        if c and p and v and i and a:
            self.add_change_request(c, p, v, i, a) if bpy.context.scene.scene_props.is_playing else self.send_osc_now(c, p, v, i, a)
        else: print("Invalid cpvia request found in Sorcerer.")
         
    def add_change_request(self, c, p, v, i, a):
        """
        This function creates a change request that will later be harmonized with against other change requests.

        Parameters:
        cpvia: channel, parameter, value, influence, argument template.

        This function does not return a value. It appends a change request to change_requests.
        """
        if c and p and v and i and a:
            self.change_requests.append(c, p, v, i, a)
        else: print("Invalid cpvia request found in Sorcerer's add_change_request.")
          
    def send_osc_now(self, c, p, v, i, a):
        """
        This function creates a list of (address, argument) tuples, each tuple to be separately passed to the send_osc() function.

        Parameters:
        cpvia: channel, parameter, value, influence, argument template.

        This function does not return a value.
        """
        if c and p and v and i and a:
            try: 
                address, argument = self.form_osc(c, p, v, i, a)  # Should return 2 strings
                if not isinstance(address, str) or not isinstance(argument, str):
                    raise ValueError("Invalid address and argument.")
            except ValueError as e:
                print(f"Error in finding address or argument: {e}")
            except Exception as e:
                print(f"Unexpected error in finding address or argument: {e}")
            send_osc(address, argument)
                # 
        else: print("Invalid cpvia request found in Sorcerer's send_osc_now.")
        
        
    def format_channel_and_value(self, c, v):
        """
        This function formats the channel and value numbers as string and then formats them
        in a way the console will understand (by adding a 0 in front of numbers 1-9.)
        """
        c = str(c[0])
        v = str(int(v[0]))
        if len(v) == 1:
            v = f"0{v}"

        return c, v
        
        
    def form_osc(self, c, p, v, i, a):
        """
        This function converts cpvia into (address, argument) tuples

        Parameters:
        cpvia: channel, parameter, value, influence, argument template.

        Returns:
        messages: A list of (address, argument) tuples.
        """  
        if c and p and v and i and a:
            try:
                address = bpy.context.scene.scene_props.str_command_line_address
                if not address or not isinstance(address, str):
                    raise ValueError("Invalid address template.")
            except ValueError as e:
                print(f"Error in address template: {e}")
            except Exception as e:
                print(f"Unexpected error in address template: {e}")
            c, v = self.format_channel_and_value(c, v)
            address = address.replace("#", c).replace("$", v)
            argument = a.replace("#", c).replace("$", v)
            return address, argument
        else: raise ValueError("Invalid cpvia request found in Sorcerer's form_osc.")
            
            
class HarmonizerFinders(HarmonizerBase): ## This must cater to individual fixtures
    def find_my_argument_template(self, parent, p, type):
        if bpy.context.scene.scene_props.console_type_enum == "option_eos":
            if type not in ["Influencer", "Brush"]:
                return getattr(bpy.context.scene.scene_props, f"str_{p}_argument")
            else:
                return getattr(bpy.context.scene.scene_props, f"str_relative_{p}_argument")
    
    
    def find_my_influence(self, parent):
        return parent.influence
    
    
    def find_my_properties(self, parent, p, type):
        """
        Finds the influence and the argument templates using self.
        
        Returns:
        This function returns influence (i) as an integer and argument (a) as a string.
        """  
        try:
            i = self.find_my_influence(parent)  # Should return an integer.
            if not isinstance(i, int):
                raise ValueError("Influence must be an integer.")
            a = self.find_my_argument_template(parent, p, type)  # Should return a string.
            if not isinstance(a, str):
                raise ValueError("Argument template must be a string.")     
            return i, a
        
        except ValueError as e:
            print(f"Error in finding influence or template: {e}")

        except Exception as e:
            print(f"Unexpected error in finding influence or template: {e}")
            
            
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
        try:
            controller_type = self.find_my_controller_type(parent)  # Should return a string.
            if controller_type is None:
                raise ValueError(f"Could not find controller type of {self.name}'s {p}.")
        except ValueError as e:
            print(f"Error in finding controller type for {p}: {e}")
            return None, None
        except Exception as e:
            print(f"Unexpected error in finding controller type for {p}: {e}")
            return None, None
        
        if controller_type in ["Influencer", "Brush"]:
            try:  # Find channels.
                current_channels = parent.find_influencer_current_channels(parent)  # Should return a list.
                if not isinstance(current_channels, list):
                    raise ValueError(f"Error in finding influencer {parent.name}'s new channels.")
                channels_to_restore, channels_to_add = find_influencer_channels_to_change(parent, current_channels)  # Should return a list
                if not isinstance(channels_to_restore, list) or not isinstance(channels_to_add, list):
                    raise ValueError(f"Error in finding influencer {parent.name}'s channels to restore or add.")
            except ValueError as e:
                print(f"Error in updating {p}: {e}")
                return None, None
            except Exception as e:
                print(f"Unexpected error in updating {p}: {e}")
                return None, None
            try:  # Find intensities.
                add_value = parent.find_my_value(parent, p)  # Should return a list with just one [integer].
                if not isinstance(add_value, list):
                    raise ValueError(f"Error in finding influencer {parent.name}'s new values.")
                restore_values = parent.find_my_restore_values(parent, p)
                if not isinstance(restore_values, list):
                    raise ValueError(f"Error in finding influencer {parent.name}'s restore values.")
            except ValueError as e:
                print(f"Unexpected error in finding {parent.name}'s value: {e}")
            except Exception as e:
                print(f"Error in finding {parent.name}'s value: {e}")
            c = new_channels + channels_to_restore
            v = add_values + restore_values
            return c, v, controller_type
        
        elif controller_type == "Fixture":
            value = self.find_my_value(parent, p, type)
            return [parent.int_object_channel_index], [value], controller_type
        
        elif controller_type in  ["group", "strip", "Set Piece"]:
            try: 
                c, v = self.find_my_group_values(parent, p)  # Should return two lists.
                print(c, v)
                if not isinstance(c, list) or not isinstance(v, list):
                    raise ValueError(f"Error in finding group controller {parent.name}'s values.")
                return c, v, controller_type
            except ValueError as e:
                print(f"Unexpected error in finding group {parent.name}'s values: {e}")
            except Exception as e:
                print(f"Error in finding group {parent.name}'s values: {e}")
        
        elif controller_type == "mixer":
            try: 
                mixing = HarmonizerMixer()
                c, v = mixing.mix_my_values(parent, p)  # Should return two lists.
                if not isinstance(c, list) or not isinstance(v, list):
                    raise ValueError(f"Error in mixing group controller {parent.name}'s values.")
                return c, v, controller_type
            except ValueError as e:
                print(f"Unexpected error in finding mixer {parent.name}'s values: {e}")
            except Exception as e:
                print(f"Error in finding mixer {parent.name}'s values: {e}")
                    
        else: sorcerer_assert_unreachable()
        
        
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
                    value = mapping.map_value(parent, p, unmapped_value)
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
        values = []
        
        attribute_name = parameter_mapping.get(p)
        print(f"ITEMS: {parent.list_group_channels.items()}")
        if attribute_name:  # Find and map value
            new_value = getattr(parent, attribute_name)
            values.append(new_value)
            if p in ["pan", "tilt", "zoom", "gobo_speed", "pan_tilt"]:
                mapping = HarmonizerMappers()
                try: 
                    value = mapping.map_value(parent, p, new_value)
                except AttributeError:
                    print("Error in find_my_value when attempting to call map_value.")
            else: value = new_value
            
        for chan in parent.list_group_channels:
            channels.append(chan.value)
             
        return channels, [value]

        
        
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
    def find_my_min_max(self, parent, p):  
        try:
            min_value = getattr(parent, f"{p}_min")
            max_value = getattr(parent, f"{p}_max")
            return min_value, max_value
        except AttributeError as e:
            print(f"Error in find_my_min_max: {e}")
            return None, None

         
    def map_value(self, parent, p, unmapped_value):
        min_val, max_val = self.find_my_min_max(parent, p)

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
        elif p == "pan_tilt":
            # Insert code for pan/tilt graph mapping here
            return mapped_value
        else:
            raise ValueError("Unknown parameter type")
    
    
"""This should house all logic for mixing values with the mixers"""   
class HarmonizerMixer(HarmonizerBase):
    
    """Recieves a bpy object mesh, parent, and returns two lists for channels list (c) and values list (v)"""    
    def mix_my_values(self, parent, p):
        try:
            channels_list = parent.list_group_channels
        except AttributeError:
            print("list_group_channels attribute not found for mixer.")
            return [], []
        
        try:
            values_list = parent.parameters
        except AttributeError:
            print("parameters attribute not found for mixer.")
            return [], []
        
        channels = [item.value for item in channels_list]
        if p == "color":
            p = "vec_color"
        parameter_name = f"float_{p}"
        
        values = [getattr(choice, parameter_name) for choice in values_list]

        # Ensure channels and values are sorted together by channels
        sorted_channels_values = sorted(zip(channels, values))
        sorted_channels, sorted_values = zip(*sorted_channels_values)
        
        print(f"Input: {sorted_channels}, {sorted_values}")
        
        # Create the mixed values by interpolating between the sorted values for each channel
        if len(sorted_channels) == 1:
            # If there is only one channel, return its value for all channels
            mixed_values = [sorted_values[0]] * len(channels)
        else:
            # Interpolate values across the sorted channels
            interpolation_points = np.linspace(sorted_channels[0], sorted_channels[-1], len(channels))
            mixed_values = np.interp(interpolation_points, sorted_channels, sorted_values)
        
        print(f"Output: {channels}, {mixed_values}")
        
        return list(channels), list(mixed_values)

    

def find_node_by_name(node_name):
    """
    Catches and corrects cases where the parent is a collection property instead of 
    a node, sequencer strip, object, etc. This function returns the bpy object so
    that the rest of the harmonizer can find what it needs.
    
    Parameters: 
        node_name: String that is the name of a bpy object (represented as 
        parent_node_identifier), typically a mixer node
    Returns:
        bpy object that is the mixer node
    """
    for node_tree in bpy.data.node_groups:
        if node_name in node_tree.nodes:
            return node_tree.nodes[node_name]
    for world in bpy.data.worlds:
        if world.node_tree and node_name in world.node_tree.nodes:
            return world.node_tree.nodes[node_name]
    return None
    
    
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
        try:
            parent = find_node_by_name(self.parent_node_identifier)
        except AttributeError:
            print("Error: Could not find mixer node bpy object.")
        return parent
    
    
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
    
    parent = find_parent(self)
    
    try:
        c, v, type = find_function(parent, p)  # Should return 2 lists and a string.
        if not isinstance(c, list) or not isinstance(v, list):
            raise ValueError(f"Channel and value lists are required for {p}.")

        harmonizer_finders = HarmonizerFinders()

        i, a = harmonizer_finders.find_my_properties(parent, p, type)  # Should return an int and string.
        if not isinstance(i, int) or not isinstance(a, str):
            raise ValueError(f"Influence and argument template are required for {p}.")
          
        publisher = HarmonizerPublisher()
          
        if len(c) > 1 and len(v) == 1:  # This is for a group
            for chan in c:
                publisher.send_cpvia([chan], p, v, i, a)
        elif len(c) > 1 and len(v) != 1:  # This is for a mixer
            for chan, value in zip(c, v):
                publisher.send_cpvia([chan], p, [value], i, a)
          
        else:
            publisher.send_cpvia(c, p, v, i, a)  # No return value.

    except ValueError as e:
        print(f"Error in updating {p}: {e}")

    except Exception as e:
        print(f"Unexpected error in updating {p}: {e}")


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
    float_pan: FloatProperty(default=0, min=-315, max=315, description="Pan value", options={'ANIMATABLE'}, update=pan_updater)
    float_tilt: FloatProperty(default=0, min=-135, max=135, description="Tilt value", options={'ANIMATABLE'}, update=tilt_updater)
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
            op.space_type = "node_editor"
    
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
            op.space_type = "node_editor"
            row.prop(self, "float_pan", text="Pan", slider=True)
            row.prop(self, "float_tilt", text="Tilt", slider=True)
        
        if self.zoom_is_on or self.iris_is_on:
            row = layout.row(align=True)
            op = row.operator("my.view_zoom_iris_props", text="", icon='LINCURVE')
            op.space_type = "node_editor"
            
            if self.zoom_is_on:
                row.prop(self, "float_zoom", slider=True, text="Zoom:")
            if self.iris_is_on:
                row.prop(self, "float_iris", slider=True, text="Iris:")
        
        if self.edge_is_on or self.diffusion_is_on:
            row = layout.row(align=True)
            op = row.operator("my.view_edge_diffusion_props", text="", icon='SELECT_SET')
            op.space_type = "node_editor"
            
            if self.edge_is_on:
                row.prop(self, "float_edge", slider=True, text="Edge:")
            if self.diffusion_is_on:
                row.prop(self, "float_diffusion", slider=True, text="Diffusion:")
        
        if self.gobo_id_is_on:
            row = layout.row(align=True)
            op = row.operator("my.view_gobo_props", text="", icon='POINTCLOUD_DATA')
            op.space_type = "node_editor"
            
            row.prop(self, "int_gobo_id", text="Gobo:")
            row.prop(self, "float_gobo_speed", slider=True, text="Speed:")
            row.prop(self, "int_prism", slider=True, text="Prism:")

  
class MixerParameters(bpy.types.PropertyGroup):
    parent_node_identifier: StringProperty()

    float_intensity: FloatProperty(default=0, min=0, max=100, update=intensity_updater, name="")
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
    float_zoom: FloatProperty(default=0, min=-315, max=315, update=zoom_updater, name="")
    float_iris: FloatProperty(default=0, min=-135, max=135, update=iris_updater, name="")
  
    
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
            ('option_gradient', "Gradient", "Mix choices across a group evenly"),
            ('option_pattern', "Pattern", "Create patterns out of choices without mixing"),
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
    )
    mix_method_enum: EnumProperty(
        name="Method",
        description="Choose a mixing method",
        items=mixer_methods,
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

    offset: FloatProperty(name="Offset", description="Move or animate this value for a moving effect")
    columns: IntProperty(name="# of Columns:", min=1, max=8, default=3)
    scale: FloatProperty(name="Size of Choices:", min=1, max=3, default=2)
    
    def init(self, context):
        self.inputs.new('MixerInputType', "Driver Input")
        self.outputs.new('FlashOutType', "Flash")
        node_refs[self.name] = self  # Add this node to the global dictionary
        self.set_parent_node_name()
        return

    def draw_buttons(self, context, layout):  
        row = layout.row(align=True)
        op_home = row.operator("node.home_group", icon='HOME', text="")
        op_home.node_name = self.name
        op_update = row.operator("node.update_group", icon='FILE_REFRESH', text="")
        op_update.node_name = self.name
        if self.str_manual_fixture_selection == "":
            row.prop(self, "str_selected_group", icon='COLLECTION_NEW', icon_only=0, text="")
        row.prop(self, "str_manual_fixture_selection", text="")
        row.prop(self, "parameters_enum", expand=True, text="")
        row = layout.row()
        row.prop(self, "mix_method_enum", expand=True)
        row.prop(self, "offset", text="Offset:")
        layout.separator()
        
        num_columns = self.columns

        flow = layout.grid_flow(row_major=True, columns=num_columns, even_columns=True, even_rows=False, align=True)
        flow.scale_y = self.scale
        
        for par in self.parameters:
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
                
        layout.separator()
        row = layout.row()
        row.operator("node.add_choice", icon='ADD')
        row.operator("node.remove_choice", icon='REMOVE')
        row.prop(self, "columns")
        row.prop(self, "scale")
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
