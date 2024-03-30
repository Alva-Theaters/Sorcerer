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


'''
=====================================================================
The harmonizer is the most error-prone and sophisticated part of 
Alva Sorcerer. Its job is to harmonize the outputs of multiple
conflicting group controllers on frame change during playback.
It also must update parameters on the console when a value inside
Sorcerer changes. Its behavior may be described by the user as
acting similar to Latest Takes Precedence (LTP) protocol. That
is because Sorcerer does not maintain a background parameter value
for any group or any parameter. All values are defined by the
controllers, or nodes. In conventional control systems for lighting,
and in other contexts, control flows top down. This means that
changes and events are initiated by a function that observes all 
global parameters beneath it. However, in Sorcerer, all changes  
are initiated by individual controllers/nodes. This is because
OSC communication protocol is not designed like DMX protocol. 
It is not capable of adequately communicating thousands of data
points at a time like other protocols can. Therefore, communication
needs must be minimized. Sorcerer minimizes communication needs,
which it calls "change requests", by using a bottom up methodology.
Change requests are initiated when an updater function registered
directly onto each unique property sees that the current value is
not equal to the stored value from the last change. This event 
begins a bottom-up control flow that uses a multitude of universal
update functions to process and format the message, based on OSC
templates provided by the user, effect settings, mixing/mapping
needs, and any other changes that must be made for the desired 
end result on the console. When this happens not during playback, 
the updater is free to send OSC regardless of other properties that
may be trying to change the same parameter on the console. However, 
when this happens during playback, each updater chain is not free
to send its own DMX. Instead, in this context, each updater wishing
to change a parameter appends its various attributes as a change
request to a global list of tuples. The formatting of the variables
inside this list resembles a matrix, consisting of many numbers in
place of strings. This is done to try to minimize memory needs and
processing time, since this is Python. On the frame change pre, all
updaters are called to find changes and resulting needs for change
requests. Any change requests are then added to the global list of
tuples. On the frame change post, once all individual change
requests have been gathered, a different handler processes them. 
It does so using a Highest Takes Precedence (HTP) protocol while in
Non-democratic mode. In Democratic mode, it instead counts votes
using each change request's integer "Influence" value. For example,
an influence value of 7 gives the change request 7 votes in the 
democracy. After all votes are in, the final agreed upon value 
is sent to the console.

As of 3/15/24, the Democratic mode has been disabled since that
part of the harmonizer was causing issues with influencers and 
color. 

When most of the heavy lifting for this system was written, there
were no driver nodes. The harmonizer system needs to be replaced 
with a better harmonizer that does a much better job of handling 
the logic of multiple heirarchies of various drivers. Currently,
there are several inconsistencies with objects and strings being
passed at the same places depending on context. This is undesirable
and easily leads to confusion and poor maintainability. A less dumb
harmonizer passes some sort of "type" value along the chain so that
functions downstream don't have to extrapolate which type of node
or object created the request. Right now, there is a lot of 
extrapolation happening where it shouldn't be. This makes it easy
for downstream functions to receive unexpected arguments. 
=====================================================================
'''


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


change_requests = []
stored_channels = set()


def get_frame_rate(scene):
    fps = scene.render.fps
    fps_base = scene.render.fps_base
    frame_rate = fps / fps_base
    return frame_rate


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


parameter_mapping = {
    1: "intensity",
    2: "pan",
    3: "tilt",
    4: "diffusion",
    5: "strobe",
    6: "zoom",
    7: "iris",
    8: "edge",
    9: "speeed",
    10: "gobo_id",
    11: "misc_effect",
    12: "prism",
    13: "red",
    14: "green",
    15: "blue",
    16: "amber",
    17: "white",
    18: "lime",
    19: "mint",
    20: "cyan",
    21: "magenta",
    22: "yellow"
}
        

'''This thing restores channels the influencer has passed over by reverting that channel 
to the channel parameters in 3D view since we don't really have a good way to guess which group 
controller to use.'''
@persistent
def influencer_deps_updater(scene, depsgraph):
    scene = scene.scene_props
    currently_influenced = set()
    ip_address = scene.str_osc_ip_address
    port = scene.int_osc_port
    address = scene.str_command_line_address
    
    global stored_channels
    
    for obj in bpy.data.objects:
        
        if obj.type == 'MESH' and obj.is_influencer:
            relevant_channels = set(get_lights_inside_mesh(obj))
            relevant_channels_str = ','.join(sorted([item.name for item in relevant_channels]))

            currently_influenced.update(relevant_channels)
            
            if obj.relevant_channels_checker != relevant_channels_str:

                for chan in relevant_channels:
                    effect_type = None
                    
                    universal_updater(chan, bpy.context, 1, round(obj.float_intensity), obj.influence, effect_type)
#                    universal_updater(chan, bpy.context, 2, round(obj.float_pan), obj.influence, effect_type)
#                    universal_updater(chan, bpy.context, 3, round(obj.float_tilt), obj.influence, effect_type)
#                    universal_updater(chan, bpy.context, 4, round(obj.float_diffusion), obj.influence, effect_type)
#                    universal_updater(chan, bpy.context, 6, round(obj.float_zoom), obj.influence, effect_type)
#                    universal_updater(chan, bpy.context, 7, round(obj.float_iris), obj.influence, effect_type)
#                    universal_updater(chan, bpy.context, 8, round(obj.float_edge), obj.influence, effect_type)
#                    universal_updater(chan, bpy.context, 9, round(obj.float_gobo_speed), obj.influence, effect_type)
#                    universal_updater(chan, bpy.context, 10, round(obj.int_gobo_id), obj.influence, effect_type)

                obj.relevant_channels_checker = relevant_channels_str

    
    to_restore = stored_channels - currently_influenced

    for res_chan in to_restore:
        effect_type = None
        universal_updater(res_chan, bpy.context, 1, round(res_chan.float_intensity), res_chan.influence, effect_type)
#        universal_updater(res_chan, bpy.context, 2, round(res_chan.float_pan), res_chan.influence, effect_type)
#        universal_updater(res_chan, bpy.context, 3, round(res_chan.float_tilt), res_chan.influence, effect_type)
#        universal_updater(res_chan, bpy.context, 4, round(res_chan.float_diffusion), res_chan.influence, effect_type)
#        universal_updater(res_chan, bpy.context, 6, round(res_chan.float_zoom), res_chan.influence, effect_type)
#        universal_updater(res_chan, bpy.context, 7, round(res_chan.float_iris), res_chan.influence, effect_type)
#        universal_updater(res_chan, bpy.context, 8, round(res_chan.float_edge), res_chan.influence, effect_type)
#        universal_updater(res_chan, bpy.context, 9, round(res_chan.float_gobo_speed), res_chan.influence, effect_type)
#        universal_updater(res_chan, bpy.context, 10, round(res_chan.int_gobo_id), res_chan.influence, effect_type)

    stored_channels = currently_influenced

    
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
        self.str_group_channels = ', '.join(map(str, channels_list)) 
        
    else:
        self.str_group_id = ""
        self.str_group_label = ""
        self.str_group_channels = ""
        self.label = "INFLUENCER Mixer"
        return 

    if hasattr(self, "parameters_enum"):    
        if self.parameters_enum == 'option_intensity':
            self.label=f"Group {self.str_group_id}: {self.str_group_label} Intensity Mixer"
        elif self.parameters_enum == 'option_color':
            self.label=f"Group {self.str_group_id}: {self.str_group_label} Color Mixer"
        elif self.parameters_enum == 'option_pan_tilt':
            self.label=f"Group {self.str_group_id}: {self.str_group_label} Pan/Tilt Mixer"


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
        self.str_group_channels = ""
        return
    
    if group_id in group_data_dict:
        group_data = group_data_dict[group_id]
        
        self.str_group_id = str(group_id)
        self.str_group_label = group_data.get('label', '')
        channels_list = group_data.get('channels', [])
        self.str_group_channels = ', '.join(map(str, channels_list))
        
    else: 
        group_id = str(group_id)
        if group_id in group_data_dict:
            group_data = group_data_dict[group_id]
            self.str_group_id = str(group_id) 
            self.str_group_label = group_data.get('label', '')  
            channels_list = group_data.get('channels', []) 
            self.str_group_channels = ', '.join(map(str, channels_list)) 
            
        else:
            self.str_group_id = ""
            self.str_group_label = ""
            self.str_group_channels = ""
             
        
def calculate_closeness(rgb_input, target_rgb, sensitivity=1.0):
    diff = sum(abs(input_c - target_c) for input_c, target_c in zip(rgb_input, target_rgb))
    normalized_diff = diff / (300 * sensitivity)
    closeness_score = max(0, min(1, 1 - normalized_diff))
    return closeness_score

        
def rgb_converter(scene, id, red, green, blue):
    return red, green, blue
    
        
def rgba_converter(scene, id, red, green, blue):
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

    
def rgbw_converter(scene, id, red, green, blue):
    white_similarity = min(red, green, blue) / 100
    white_peak = 75 + (25 * white_similarity)  # Peaks at 100 for pure white.

    white = round(white_peak * white_similarity)
    
    return red, green, blue, white


def rgbaw_converter(scene, id, red, green, blue, amber_sensitivity=1.0, white_sensitivity=1.0):
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


def rgbl_converter(scene, id, red, green, blue):
    lime = 0
    
    # Lime peaks at 100 for yellow (100, 100, 0) and white (100, 100, 100).
    if red == 100 and green == 100:
        lime = 100
    # For other combinations, calculate lime based on the lesser of red and green, but only if blue is not dominant.
    elif blue < red and blue < green:
        lime = round((min(red, green) / 100) * 100)
    
    return red, green, blue, lime


def rgbam_converter(scene, id, red, green, blue):
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


def cmy_converter(scene, id, red, green, blue):
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

    
def universal_color_updater(id, color, channel, context):
    scene = context.scene
    red = round(color[0] * 100)
    green = round(color[1] * 100)
    blue = round(color[2] * 100)
    
    # Ensure proper self bpy object is passed if a group controller is
    # is using this as opposed to when a mixer uses this.
    if hasattr(id, "str_group_channels") and id.bl_idname == 'group_controller_type':
        channel = id
    
    if id.color_profile_enum == 'option_rgb':
        universal_updater(channel, context, 13, round(red), id.influence, None)
        universal_updater(channel, context, 14, round(green), id.influence, None)
        universal_updater(channel, context, 15, round(blue), id.influence, None)
    
    elif id.color_profile_enum == 'option_rgba':
        red, green, blue, amber = rgba_converter(scene, id, red, green, blue)
        universal_updater(channel, context, 13, round(red), id.influence, None)
        universal_updater(channel, context, 14, round(green), id.influence, None)
        universal_updater(channel, context, 15, round(blue), id.influence, None)
        universal_updater(channel, context, 16, round(amber), id.influence, None)
                    
    elif id.color_profile_enum == 'option_rgbw':
        red, green, blue, white = rgbw_converter(scene, id, red, green, blue)
        universal_updater(channel, context, 13, round(red), id.influence, None)
        universal_updater(channel, context, 14, round(green), id.influence, None)
        universal_updater(channel, context, 15, round(blue), id.influence, None)
        universal_updater(channel, context, 17, round(white), id.influence, None)
            
    elif id.color_profile_enum == 'option_rgbaw':
        red, green, blue, amber, white = rgbaw_converter(scene, id, red, green, blue, amber_sensitivity=.167, white_sensitivity=.3)
        universal_updater(channel, context, 13, round(red), id.influence, None)
        universal_updater(channel, context, 14, round(green), id.influence, None)
        universal_updater(channel, context, 15, round(blue), id.influence, None)
        universal_updater(channel, context, 16, round(amber), id.influence, None)
        universal_updater(channel, context, 17, round(white), id.influence, None)
        
    elif id.color_profile_enum == 'option_rgbl':
        red, green, blue, lime = rgbl_converter(scene, id, red, green, blue)
        universal_updater(channel, context, 13, round(red), id.influence, None)
        universal_updater(channel, context, 14, round(green), id.influence, None)
        universal_updater(channel, context, 15, round(blue), id.influence, None)
        universal_updater(channel, context, 18, round(lime), id.influence, None)
        
    elif id.color_profile_enum == 'option_cmy':
        cyan, magenta, yellow = cmy_converter(scene, id, red, green, blue)
        universal_updater(channel, context, 20, round(cyan), id.influence, None)
        universal_updater(channel, context, 21, round(magenta), id.influence, None)
        universal_updater(channel, context, 22, round(yellow), id.influence, None)
         
    else:
        red, green, blue, amber, mint = rgbam_converter(scene, id, red, green, blue)
        universal_updater(channel, context, 13, round(red), id.influence, None)
        universal_updater(channel, context, 14, round(green), id.influence, None)
        universal_updater(channel, context, 15, round(blue), id.influence, None)
        universal_updater(channel, context, 16, round(amber), id.influence, None)
        universal_updater(channel, context, 19, round(mint), id.influence, None)
        
        
def apply_no_effect(channels, input_value):
    channel_values = {}

    for index, chan in enumerate(sorted(channels)):
        channel_values[chan] = input_value

    return channel_values
        
        
def apply_fan_center_effect(channels, input_value):
    num_channels = len(channels)
    max_offset = input_value

    steps = (num_channels - 1) // 2 if num_channels % 2 == 0 else num_channels // 2

    channel_values = {}

    for index, chan in enumerate(sorted(channels)):
        if num_channels % 2 == 0:
            distance_from_center = abs(index - (num_channels / 2 - 0.5))
        else:  # Odd number of channels
            distance_from_center = abs(index - num_channels // 2)

        # Calculate the value based on the distance from the center.
        if distance_from_center <= steps:
            value = (distance_from_center / steps) * max_offset
            # Adjust the sign based on which side of the center the channel is on.
            value = -value if index < num_channels // 2 else value
        else:
            value = 0  # Center channel(s) for even number of channels.

        channel_values[chan] = value

    return channel_values


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
        
                
def universal_mixer_updater(self, parameter, value_one, value_two, value_three):
    is_float_vec = isinstance(value_one, mathutils.Vector) or isinstance(value_one, mathutils.Color)
    
    if not is_float_vec:
        if self.every_other:
            mode = "alternate"
        else:
            mode = None
            
        channel_list = ""
        
        if self.str_group_channels != "":
            channel_list = self.str_group_channels
        else:
            influencer_object_name = self.str_selected_group
            for obj in bpy.data.objects:
                if obj.type == 'MESH' and obj.name == self.str_selected_group:
                    influencer_object = obj
                    channel_list = get_lights_inside_mesh(influencer_object)
                    break
            
        if channel_list == "":   
            return
        
        mixed_list = calculate_mixed_values(channel_list, mode, value_one, value_two, value_three)
        
        effect_type = "mixer"
        
        for channel, calculated_value in mixed_list:
            universal_updater(channel, bpy.context, parameter, round(calculated_value), self.influence, effect_type)
    
    else:
        mode = "alternate" if self.every_other else None

        if hasattr(self, "str_group_channels"):
            channel_list = self.str_group_channels 
        else: channel_list = None
        
        if not channel_list:
            influencer_object_name = self.str_selected_group
            influencer_object = bpy.data.objects.get(influencer_object_name)
            if influencer_object and influencer_object.type == 'MESH':
                channel_list = get_lights_inside_mesh(influencer_object)
            
        if not channel_list:
            return
        
        if isinstance(channel_list, str):
            channel_list = [channel.strip() for channel in channel_list.split(',') if channel.strip().isdigit()]
        elif not all(channel.isdigit() for channel in channel_list):
            print("Invalid channel identifiers found in channel_list.")
            return
    
        final_mixed_colors = []

        for component_index in range(3):
            component_one = value_one[component_index]
            component_two = value_two[component_index] if value_two else None
            component_three = value_three[component_index]

            mixed_component_values = calculate_mixed_values(channel_list, mode, component_one, component_two, component_three)

            for channel_index, (channel, mixed_value) in enumerate(mixed_component_values):
                if component_index == 0:
                    final_mixed_colors.append([mixed_value])
                else:  
                    final_mixed_colors[channel_index].append(mixed_value)

        final_mixed_colors = [tuple(color) for color in final_mixed_colors]
        
        for channel, mixed_color in zip(channel_list, final_mixed_colors):
            universal_color_updater(self, mixed_color, str(channel), bpy.context)

        
def should_mixer_update(self, current_values, stored_values):
    proceed = False
    
    if not self.show_middle:
        proceed = current_values[0] != stored_values[0] or current_values[2] != stored_values[2]
    else:
        proceed = any(curr != stored for curr, stored in zip(current_values, stored_values))
    return proceed


#################
# LOCAL UPDATERS
#################    

############
# INTENSITY
############
def group_intensity_updater(self, context):
    if self.float_intensity != self.float_intensity_checker:
        if self.use_fan_center_intensity:
            effect_type = "fan_center"
        else: effect_type = None
        # 1 = intensity parameter type
        universal_updater(self, context, 1, round(self.float_intensity), self.influence, effect_type)  
        self.float_intensity_checker = self.float_intensity
        
        
def group_driver_intensity_updater(self, context):
    if self.float_intensity != self.float_intensity_checker:
        for output_socket in self.outputs:
            for link in output_socket.links:
              connected_node = link.to_socket.node
              if hasattr(connected_node, "float_intensity_checker"):
                connected_node.float_intensity_checker = .02
                connected_node.float_intensity = self.float_intensity
        
        self.float_intensity_checker = self.float_intensity


def master_intensity_updater(self, context):
    if self.float_intensity != self.float_intensity_checker:
        for output_socket in self.outputs:
            if output_socket.name == "Master Output":
                for link in output_socket.links:
                    group_node = link.to_node
                    if isinstance(group_node, bpy.types.ShaderNodeGroup):
                        target_socket_name = link.to_socket.name
                        group_node_tree = group_node.node_tree
                        for node in group_node_tree.nodes:
                            if node.type == 'GROUP_INPUT':
                                for input_socket in node.outputs:
                                    if input_socket.name == target_socket_name:
                                        for inner_link in input_socket.links:
                                            connected_node = inner_link.to_node
                                            if hasattr(connected_node, 'float_intensity'):
                                                connected_node.float_intensity_checker = .02
                                                connected_node.float_intensity = self.float_intensity
                    
                    elif hasattr(group_node, "float_intensity_checker"):
                      group_node.float_intensity_checker = .02
                      group_node.float_intensity = self.float_intensity
        
        self.float_intensity_checker = self.float_intensity

        
def channel_intensity_updater(self, context):
    if self.float_intensity != self.float_intensity_checker:
        effect_type = None
        
        universal_updater(self, context, 1, round(self.float_intensity), self.influence, effect_type) 
        
        if context.scene.scene_props.channel_controller_is_active:
            for obj in context.selected_objects:
                if hasattr(obj, "float_intensity"):
                    universal_updater(obj.name, context, 1, round(self.float_intensity), self.influence, effect_type)
                      
        self.float_intensity_checker = self.float_intensity
        
        
def mixer_intensity_updater(self, context):
    current_values = [self.float_intensity_one, self.float_intensity_two, self.float_intensity_three]
    stored_values = [self.float_intensity_one_checker, self.float_intensity_two_checker, self.float_intensity_three_checker]
    
    proceed = should_mixer_update(self, current_values, stored_values)

    if proceed: 
        if not self.show_middle:
            float_intensity_two = None
        else: float_intensity_two = self.float_intensity_two
    
        parameter = 1
            
        universal_mixer_updater(self, parameter, self.float_intensity_one, float_intensity_two, self.float_intensity_three)
        
        self.float_intensity_one_checker = self.float_intensity_one
        self.float_intensity_two_checker = self.float_intensity_two
        self.float_intensity_three_checker = self.float_intensity_three
        
        
def mixer_intensity_updater_pointer(self, context):
    if self.show_middle:
        if self.float_intensity_two != self.float_intensity_two_checker or self.float_intensity_three != self.float_intensity_three_checker:
            self.float_intensity_one = self.float_intensity_one
    else:
        if self.float_intensity_three != self.float_intensity_three_checker:
            self.float_intensity_one = self.float_intensity_one
            

def mixer_driver_intensity_updater(self, context):   
    current_values = [self.float_intensity_one, self.float_intensity_two, self.float_intensity_three]
    stored_values = [self.float_intensity_one_checker, self.float_intensity_two_checker, self.float_intensity_three_checker]
    
    proceed = should_mixer_update(self, current_values, stored_values)

    if proceed: 
        for output_socket in self.outputs:
            for link in output_socket.links:
                connected_node = link.to_socket.node
                connected_node.float_intensity_one_checker = .02
                connected_node.float_intensity_one = self.float_intensity_one
                connected_node.float_intensity_two = self.float_intensity_two
                connected_node.float_intensity_three = self.float_intensity_three
        
             
#################
# COLOR
#################  
def group_color_updater(self, context):
    if self.float_vec_color != self.float_vec_color_checker:
        name = self.str_group_id
        color = self.float_vec_color
        universal_color_updater(self, color, name, context)
        self.float_vec_color_checker = self.float_vec_color
        
        
def channel_color_updater(self, context):
    if self.float_vec_color != self.float_vec_color_checker:
        name = self.name
        universal_color_updater(self, self.float_vec_color, name, context)
        
        if context.scene.scene_props.channel_controller_is_active:
            for obj in context.selected_objects:
                if hasattr(obj, "float_vec_color"):
                    universal_color_updater(self, self.float_vec_color, obj.name, context)
                      
        self.float_vec_color_checker = self.float_vec_color
        

def group_driver_color_updater(self, context):
    if self.float_vec_color != self.float_vec_color_checker:
        for output_socket in self.outputs:
            for link in output_socket.links:
              connected_node = link.to_socket.node
              if hasattr(connected_node, "float_intensity_checker"):
                connected_node.float_vec_color = (.05, .05, .05)
                connected_node.float_vec_color = self.float_vec_color
                
                
def master_color_updater(self, context):
    if self.float_vec_color != self.float_vec_color_checker:
        for output_socket in self.outputs:
            if output_socket.name == "Master Output":
                for link in output_socket.links:
                    group_node = link.to_node
                    if isinstance(group_node, bpy.types.ShaderNodeGroup):
                        target_socket_name = link.to_socket.name
                        group_node_tree = group_node.node_tree
                        for node in group_node_tree.nodes:
                            if node.type == 'GROUP_INPUT':
                                for input_socket in node.outputs:
                                    if input_socket.name == target_socket_name:
                                        for inner_link in input_socket.links:
                                            connected_node = inner_link.to_node
                                            if hasattr(connected_node, 'float_vec_color'):
                                                connected_node.float_vec_color_checker = (.05, .05, .05)
                                                connected_node.float_vec_color = self.float_vec_color
        
        self.float_vec_color_checker = self.float_vec_color
        
        
def mixer_color_updater(self, context):
    current_values = [self.float_vec_color_one, self.float_vec_color_two, self.float_vec_color_three]
    stored_values = [self.float_vec_color_one_checker, self.float_vec_color_two_checker, self.float_vec_color_three_checker]

    proceed = should_mixer_update(self, current_values, stored_values)

    if proceed: 
        if not self.show_middle:
            float_vec_color_two = None
        else: float_vec_color_two = self.float_vec_color_two

        parameter = 2

        universal_mixer_updater(self, parameter, self.float_vec_color_one, float_vec_color_two, self.float_vec_color_three)

        self.float_vec_color_one_checker = self.float_vec_color_one
        self.float_vec_color_two_checker = self.float_vec_color_two
        self.float_vec_color_three_checker = self.float_vec_color_three


def mixer_color_updater_pointer(self, context):
    if self.show_middle:
        if self.float_vec_color_two != self.float_vec_color_two_checker or self.float_vec_color_three != self.float_vec_color_three_checker:
            self.float_vec_color_one = self.float_vec_color_one
    else:
        if self.float_vec_color_three != self.float_vec_color_three_checker:
            self.float_vec_color_one = self.float_vec_color_one  
            
            
def mixer_driver_color_updater(self, context):
    current_values = [self.float_vec_color_one, self.float_vec_color_two, self.float_vec_color_three]
    stored_values = [self.float_vec_color_one_checker, self.float_vec_color_two_checker, self.float_vec_color_three_checker]
    
    proceed = should_mixer_update(self, current_values, stored_values)

    if proceed: 
        for output_socket in self.outputs:
            for link in output_socket.links:
                connected_node = link.to_socket.node
                
                connected_node.float_vec_color_one_checker = (.05, .05, .05)
                connected_node.float_vec_color_one = self.float_vec_color_one
                connected_node.float_vec_color_two = self.float_vec_color_two
                connected_node.float_vec_color_three = self.float_vec_color_three


#################
# PAN
#################  
def group_pan_updater(self, context): 
    if self.float_pan != self.float_pan_checker:
        if self.use_fan_center_pan:
            effect_type = "fan_center"
        else: effect_type = None
        
        universal_updater(self, context, 2, round(self.float_pan), self.influence, effect_type)
        self.float_pan_checker = self.float_pan
        
        
def group_driver_pan_updater(self, context):
    if self.float_pan != self.float_pan_checker:
        for output_socket in self.outputs:
            for link in output_socket.links:
              connected_node = link.to_socket.node
              if hasattr(connected_node, "float_intensity_checker"):
                connected_node.float_pan_checker = .05
                connected_node.float_pan = self.float_pan
        
        self.float_pan_checker = self.float_pan
        
        
def master_pan_updater(self, context):
    if self.float_pan != self.float_pan_checker:
        for output_socket in self.outputs:
            if output_socket.name == "Master Output":
                for link in output_socket.links:
                    group_node = link.to_node
                    if isinstance(group_node, bpy.types.ShaderNodeGroup):
                        target_socket_name = link.to_socket.name
                        group_node_tree = group_node.node_tree
                        for node in group_node_tree.nodes:
                            if node.type == 'GROUP_INPUT':
                                for input_socket in node.outputs:
                                    if input_socket.name == target_socket_name:
                                        for inner_link in input_socket.links:
                                            connected_node = inner_link.to_node
                                            if hasattr(connected_node, 'float_pan'):
                                                connected_node.float_pan_checker = .05
                                                connected_node.float_pan = self.float_pan
        
        self.float_pan_checker = self.float_pan
        
        n
def channel_pan_updater(self, context):
    if self.float_pan != self.float_pan_checker:
        effect_type = None
        
        pan_min = context.scene.scene_props.pan_min
        pan_max = context.scene.scene_props.pan_max
        
        # Maps value to send by calculating between value input and min/max inputs
        pan_value = ((self.float_pan / 100.0) * (pan_max - pan_min)) + pan_min
        
        normalized_value = (self.float_pan + 100) / 200
        mapped_value = (normalized_value * (pan_max - pan_min)) + pan_min
        
        universal_updater(self, context, 2, round(mapped_value), self.influence, effect_type)  
        
        if context.scene.scene_props.channel_controller_is_active:
            for obj in context.selected_objects:
                if hasattr(obj, "float_pan"):
                    universal_updater(obj.name, context, 2, round(mapped_value), self.influence, effect_type)
        
        self.float_pan_checker = self.float_pan
        
        
def mixer_pan_updater(self, context):
    current_values = [self.float_pan_one, self.float_pan_two, self.float_pan_three]
    stored_values = [self.float_pan_one_checker, self.float_pan_two_checker, self.float_pan_three_checker]

    proceed = should_mixer_update(self, current_values, stored_values)

    if proceed: 
        if not self.show_middle:
            float_pan_two = None
        else: float_pan_two = self.float_pan_two

        parameter = 2

        universal_mixer_updater(self, parameter, self.float_pan_one, float_pan_two, self.float_pan_three)

        self.float_pan_one_checker = self.float_pan_one
        self.float_pan_two_checker = self.float_pan_two
        self.float_pan_three_checker = self.float_pan_three


def mixer_pan_updater_pointer(self, context):
    if self.show_middle:
        if self.float_pan_two != self.float_pan_two_checker or self.float_pan_three != self.float_pan_three_checker:
            self.float_pan_one = self.float_pan_one
    else:
        if self.float_pan_three != self.float_pan_three_checker:
            self.float_pan_one = self.float_pan_one


def mixer_driver_pan_updater(self, context):
    current_values = [self.float_pan_one, self.float_pan_two, self.float_pan_three]
    stored_values = [self.float_pan_one_checker, self.float_pan_two_checker, self.float_pan_three_checker]
    
    proceed = should_mixer_update(self, current_values, stored_values)

    if proceed: 
        for output_socket in self.outputs:
            for link in output_socket.links:
                connected_node = link.to_socket.node
                
                connected_node.float_pan_one_checker = .05
                connected_node.float_pan_one = self.float_pan_one
                connected_node.float_pan_two = self.float_pan_two
                connected_node.float_pan_three = self.float_pan_three


#################
# TILT
#################  
def group_tilt_updater(self, context):
    if self.float_tilt != self.float_tilt_checker:
        if self.use_fan_center_tilt:
            effect_type = "fan_center"
        else: effect_type = None
        
        universal_updater(self, context, 3, round(self.float_tilt), self.influence, effect_type)
        self.float_tilt_checker = self.float_tilt
        

def group_driver_tilt_updater(self, context):
    if self.float_tilt != self.float_tilt_checker:
        for output_socket in self.outputs:
            for link in output_socket.links:
              connected_node = link.to_socket.node
              if hasattr(connected_node, "float_intensity_checker"):
                connected_node.float_tilt_checker = .05
                connected_node.float_tilt = self.float_tilt
        
        self.float_tilt_checker = self.float_tilt
        
        
def master_tilt_updater(self, context):
    if self.float_tilt != self.float_tilt_checker:
        for output_socket in self.outputs:
            if output_socket.name == "Master Output":
                for link in output_socket.links:
                    group_node = link.to_node
                    if isinstance(group_node, bpy.types.ShaderNodeGroup):
                        target_socket_name = link.to_socket.name
                        group_node_tree = group_node.node_tree
                        for node in group_node_tree.nodes:
                            if node.type == 'GROUP_INPUT':
                                for input_socket in node.outputs:
                                    if input_socket.name == target_socket_name:
                                        for inner_link in input_socket.links:
                                            connected_node = inner_link.to_node
                                            if hasattr(connected_node, 'float_tilt'):
                                                connected_node.float_tilt_checker = .05
                                                connected_node.float_tilt = self.float_tilt
        
        self.float_tilt_checker = self.float_tilt
        
        
def channel_tilt_updater(self, context):
    if self.float_tilt != self.float_tilt_checker:
        effect_type = None
                
        tilt_min = context.scene.scene_props.tilt_min
        tilt_max = context.scene.scene_props.tilt_max
        
        # Maps value to send by calculating between value input and min/max inputs.
        tilt_value = ((self.float_tilt / 100.0) * (tilt_max - tilt_min)) + tilt_min
        
        normalized_value = (self.float_tilt + 100) / 200
        mapped_value = (normalized_value * (tilt_max - tilt_min)) + tilt_min
        
        universal_updater(self, context, 3, round(mapped_value), self.influence, effect_type) 
        
        if context.scene.scene_props.channel_controller_is_active:
            for obj in context.selected_objects:
                if hasattr(obj, "float_tilt"):
                    universal_updater(obj.name, context, 3, round(mapped_value), self.influence, effect_type)
        
        self.float_tilt_checker = self.float_tilt


def mixer_tilt_updater(self, context):
    current_values = [self.float_tilt_one, self.float_tilt_two, self.float_tilt_three]
    stored_values = [self.float_tilt_one_checker, self.float_tilt_two_checker, self.float_tilt_three_checker]
    
    proceed = should_mixer_update(self, current_values, stored_values)

    if proceed: 
        if not self.show_middle:
            float_tilt_two = None
        else: float_tilt_two = self.float_tilt_two
    
        parameter = 3
            
        universal_mixer_updater(self, parameter, self.float_tilt_one, float_tilt_two, self.float_tilt_three)
        
        self.float_tilt_one_checker = self.float_tilt_one
        self.float_tilt_two_checker = self.float_tilt_two
        self.float_tilt_three_checker = self.float_tilt_three


def mixer_tilt_updater_pointer(self, context):
    if self.show_middle:
        if self.float_tilt_two != self.float_tilt_two_checker or self.float_tilt_three != self.float_tilt_three_checker:
            self.float_tilt_one = self.float_tilt_one
    else:
        if self.float_tilt_three != self.float_tilt_three_checker:
            self.float_tilt_one = self.float_tilt_one
            

def mixer_driver_tilt_updater(self, context):
    current_values = [self.float_tilt_one, self.float_tilt_two, self.float_tilt_three]
    stored_values = [self.float_tilt_one_checker, self.float_tilt_two_checker, self.float_tilt_three_checker]
    
    proceed = should_mixer_update(self, current_values, stored_values)

    if proceed: 
        for output_socket in self.outputs:
            for link in output_socket.links:
                connected_node = link.to_socket.node
                
                connected_node.float_tilt_one_checker = .05
                connected_node.float_tilt_one = self.float_tilt_one
                connected_node.float_tilt_two = self.float_tilt_two
                connected_node.float_tilt_three = self.float_tilt_three
                  

#################
# PAN/TILT GRAPH
#################   
'''Uses template color picker as stand-in for pan/tilt square graph controller'''           
def pan_tilt_graph_updater(self, context):
    if self.pan_tilt_graph_checker != self.float_vec_pan_tilt_graph:
        scene = context.scene.scene_props
        effect_type = None
        r, g, b = self.float_vec_pan_tilt_graph[:3]
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        v *= 30
        hue_change = h - self.last_hue
        overdrive_mode = self.overdrive_mode
        
        if self.is_overdriven_left and h < .75:
            overdrive_mode = ""
            self.is_overdriven_left = False
            self.is_approaching_limit = False
            print("Overdriving for left pan")
            
        elif self.is_overdriven_right and h > .25:
            overdrive_mode = ""
            self.is_overdriven_right = False
            self.is_approaching_limit = False
            print("Overdriving for right pan")
            
        if self.is_overdriven_left and h < .85:
            self.is_approaching_limit = True
            
        elif self.is_overdriven_right and h > .15:
            self.is_approaching_limit = True
            
        # Detect a jump in hue value indicating a crossover point.
        if hue_change > 0.5 and not self.is_overdriven_right:  
            overdrive_mode = 'left'
            self.is_overdriven_left = True
        elif hue_change < -0.5 and not self.is_overdriven_left:
            overdrive_mode = 'right'
            self.is_overdriven_right = True

        # Calculate pan based on the direction of the jump.
        if overdrive_mode == 'left':
            overdrive_h = (1 - h) * -1
            pan = (overdrive_h * scene.pan_max * -1) + (scene.pan_max * .5)
        elif overdrive_mode == 'right':
            overdrive_h = h + 1
            pan = (overdrive_h * scene.pan_max * -1) + (scene.pan_max * .5)
        else:
            # Normal operation, map hue to full pan range.
            pan = (h * scene.pan_max * -1) + (scene.pan_max * .5)

        # Calculate tilt based on saturation and value.
        tilt = (s * scene.tilt_max) * v  # Assuming saturation and value map to tilt.

        universal_updater(self, context, 2, round(pan), self.influence, effect_type) 
        universal_updater(self, context, 3, round(tilt), self.influence, effect_type) 
        self.pan_tilt_graph_checker = self.float_vec_pan_tilt_graph

        # Save current hue for next update.
        self.last_hue = h
        self.overdrive_mode = overdrive_mode     
     
        
#################
# DIFFUSION
#################   
def group_diffusion_updater(self, context):
    if self.float_diffusion != self.float_diffusion_checker:
        if self.use_fan_center_diffusion:
            effect_type = "fan_center"
        else: effect_type = None
        
        universal_updater(self, context, 4, round(self.float_diffusion), self.influence, effect_type)
        self.float_diffusion_checker = self.float_diffusion
        
        
def group_driver_diffusion_updater(self, context):
    if self.float_diffusion != self.float_diffusion_checker:
        for output_socket in self.outputs:
            for link in output_socket.links:
              connected_node = link.to_socket.node
              if hasattr(connected_node, "float_intensity_checker"):
                connected_node.float_diffusion_checker = .05
                connected_node.float_diffusion = self.float_diffusion
        
        self.float_diffusion_checker = self.float_diffusion
        
        
def master_diffusion_updater(self, context):
    if self.float_diffusion != self.float_diffusion_checker:
        for output_socket in self.outputs:
            if output_socket.name == "Master Output":
                for link in output_socket.links:
                    group_node = link.to_node
                    if isinstance(group_node, bpy.types.ShaderNodeGroup):
                        target_socket_name = link.to_socket.name
                        group_node_tree = group_node.node_tree
                        for node in group_node_tree.nodes:
                            if node.type == 'GROUP_INPUT':
                                for input_socket in node.outputs:
                                    if input_socket.name == target_socket_name:
                                        for inner_link in input_socket.links:
                                            connected_node = inner_link.to_node
                                            if hasattr(connected_node, 'float_diffusion'):
                                                connected_node.float_diffusion_checker = .05
                                                connected_node.float_diffusion = self.float_diffusion
        
        self.float_diffusion_checker = self.float_diffusion
        
        
def channel_diffusion_updater(self, context):
    if self.float_diffusion != self.float_diffusion_checker:
        effect_type = None
        
        universal_updater(self, context, 4, round(self.float_diffusion), self.influence, effect_type) 
        
        if context.scene.scene_props.channel_controller_is_active:
            for obj in context.selected_objects:
                if hasattr(obj, "float_diffusion"):
                    universal_updater(obj.name, context, 4, round(self.float_diffusion), self.influence, effect_type)
        
        self.float_diffusion_checker = self.float_diffusion
        
        
#################
# STROBE
#################         
def group_strobe_updater(self, context):
    if self.float_strobe != self.float_strobe_checker:
        if self.use_fan_center_strobe:
            effect_type = "fan_center"
        else: effect_type = None
        
        strobe_min = self.strobe_min
        strobe_max = self.strobe_max
        
        # Maps value to send by calculating between value input and min/max inputs
        strobe_value = ((self.float_strobe / 100.0) * (strobe_max - strobe_min)) + strobe_min
        
        universal_updater(self, context, 5, round(strobe_value), self.influence, effect_type)
        self.float_strobe_checker = self.float_strobe
        
        
def group_driver_strobe_updater(self, context):
    if self.float_strobe != self.float_strobe_checker:
        for output_socket in self.outputs:
            for link in output_socket.links:
              connected_node = link.to_socket.node
              if hasattr(connected_node, "float_intensity_checker"):
                connected_node.float_diffusion_checker = .05
                connected_node.float_strobe = self.float_strobe
        
        self.float_strobe_checker = self.float_strobe
        

def master_strobe_updater(self, context):
    if self.float_strobe != self.float_strobe_checker:
        for output_socket in self.outputs:
            if output_socket.name == "Master Output":
                for link in output_socket.links:
                    group_node = link.to_node
                    if isinstance(group_node, bpy.types.ShaderNodeGroup):
                        target_socket_name = link.to_socket.name
                        group_node_tree = group_node.node_tree
                        for node in group_node_tree.nodes:
                            if node.type == 'GROUP_INPUT':
                                for input_socket in node.outputs:
                                    if input_socket.name == target_socket_name:
                                        for inner_link in input_socket.links:
                                            connected_node = inner_link.to_node
                                            if hasattr(connected_node, 'float_strobe'):
                                                connected_node.float_diffusion_checker = .05
                                                connected_node.float_strobe = self.float_strobe
        
        self.float_strobe_checker = self.float_strobe
        

## Currently not usable, so not accessible in UI        
#def channel_strobe_updater(self, context):
#    if self.float_strobe != self.float_strobe_checker:
#        effect_type = None
#        
#        strobe_min = self.strobe_min
#        strobe_max = self.strobe_max
#        
#        # Maps value to send by calculating between value input and min/max inputs
#        strobe_value = ((self.float_strobe / 100.0) * (strobe_max - strobe_min)) + strobe_min
#        
#        universal_updater(self, context, 5, round(strobe_value), self.influence, effect_type)
#        self.float_strobe_checker = self.float_strobe
        
        
#################
# ZOOM
#################         
def group_zoom_updater(self, context):
    if self.float_zoom != self.float_zoom_checker:
        if self.use_fan_center_zoom:
            effect_type = "fan_center"
        else: effect_type = None
        
        zoom_min = self.zoom_min
        zoom_max = self.zoom_max
        
        # Maps value to send by calculating between value input and min/max inputs
        zoom_value = ((self.float_zoom / 100.0) * (zoom_max - zoom_min)) + zoom_min
        
        universal_updater(self, context, 6, round(zoom_value), self.influence, effect_type)
        self.float_zoom_checker = self.float_zoom
        
        
def group_driver_zoom_updater(self, context):
    if self.float_zoom != self.float_zoom_checker:
        for output_socket in self.outputs:
            for link in output_socket.links:
              connected_node = link.to_socket.node
              if hasattr(connected_node, "float_intensity_checker"):
                connected_node.float_zoom_checker = .05
                connected_node.float_zoom = self.float_zoom
        
        self.float_zoom_checker = self.float_zoom
        
        
def master_zoom_updater(self, context):
    if self.float_zoom != self.float_zoom_checker:
        for output_socket in self.outputs:
            if output_socket.name == "Master Output":
                for link in output_socket.links:
                    group_node = link.to_node
                    if isinstance(group_node, bpy.types.ShaderNodeGroup):
                        target_socket_name = link.to_socket.name
                        group_node_tree = group_node.node_tree
                        for node in group_node_tree.nodes:
                            if node.type == 'GROUP_INPUT':
                                for input_socket in node.outputs:
                                    if input_socket.name == target_socket_name:
                                        for inner_link in input_socket.links:
                                            connected_node = inner_link.to_node
                                            if hasattr(connected_node, 'float_zoom'):
                                                connected_node.float_diffusion_checker = .05
                                                connected_node.float_zoom = self.float_zoom
        
        self.float_zoom_checker = self.float_zoom
        
        
def channel_zoom_updater(self, context):
    if self.float_zoom != self.float_zoom_checker:
        effect_type = None
        
        zoom_min = context.scene.scene_props.zoom_min
        zoom_max = context.scene.scene_props.zoom_max
        
        # Maps value to send by calculating between value input and min/max inputs.
        zoom_value = ((self.float_zoom / 100.0) * (zoom_max - zoom_min)) + zoom_min
        
        universal_updater(self, context, 6, round(zoom_value), self.influence, effect_type)
        
        if context.scene.scene_props.channel_controller_is_active:
            for obj in context.selected_objects:
                if hasattr(obj, "float_zoom"):
                    universal_updater(obj.name, context, 6, round(self.float_zoom), self.influence, effect_type)
              
        self.float_zoom_checker = self.float_zoom
        
        
#################
# IRIS
#################         
def group_iris_updater(self, context):
    if self.float_iris != self.float_iris_checker:
        if self.use_fan_center_iris:
            effect_type = "fan_center"
        else: effect_type = None
        
        universal_updater(self, context, 7, round(self.float_iris), self.influence, effect_type)
        self.float_iris_checker = self.float_iris
        
        
def group_driver_iris_updater(self, context):
    if self.float_iris != self.float_iris_checker:
        for output_socket in self.outputs:
            for link in output_socket.links:
              connected_node = link.to_socket.node
              if hasattr(connected_node, "float_intensity_checker"):
                connected_node.float_iris_checker = .05
                connected_node.float_iris = self.float_iris
        
        self.float_iris_checker = self.float_iris
        
        
def master_iris_updater(self, context):
    if self.float_iris != self.float_iris_checker:
        for output_socket in self.outputs:
            if output_socket.name == "Master Output":
                for link in output_socket.links:
                    group_node = link.to_node
                    if isinstance(group_node, bpy.types.ShaderNodeGroup):
                        target_socket_name = link.to_socket.name
                        group_node_tree = group_node.node_tree
                        for node in group_node_tree.nodes:
                            if node.type == 'GROUP_INPUT':
                                for input_socket in node.outputs:
                                    if input_socket.name == target_socket_name:
                                        for inner_link in input_socket.links:
                                            connected_node = inner_link.to_node
                                            if hasattr(connected_node, 'float_iris'):
                                                connected_node.float_diffusion_checker = .05
                                                connected_node.float_iris = self.float_iris
        
        self.float_iris_checker = self.float_iris
        
        
def channel_iris_updater(self, context):
    if self.float_iris != self.float_iris_checker:
        effect_type = None
        
        universal_updater(self, context, 7, round(self.float_iris), self.influence, effect_type)
        
        if context.scene.scene_props.channel_controller_is_active:
            for obj in context.selected_objects:
                if hasattr(obj, "float_iris"):
                    universal_updater(obj.name, context, 7, round(self.float_iris), self.influence, effect_type)

        self.float_iris_checker = self.float_iris
        
        
#################
# EDGE
#################         
def group_edge_updater(self, context):
    if self.float_edge != self.float_edge_checker:
        if self.use_fan_center_edge:
            effect_type = "fan_center"
        else: effect_type = None
        
        universal_updater(self, context, 8, round(self.float_edge), self.influence, effect_type)
        self.float_edge_checker = self.float_edge
        
        
def group_driver_edge_updater(self, context):
    if self.float_edge != self.float_edge_checker:
        for output_socket in self.outputs:
            for link in output_socket.links:
              connected_node = link.to_socket.node
              if hasattr(connected_node, "float_intensity_checker"):
                connected_node.float_edge_checker = .05
                connected_node.float_edge = self.float_edge
        
        self.float_edge_checker = self.float_edge
        
        
def master_edge_updater(self, context):
    if self.float_edge != self.float_edge_checker:
        for output_socket in self.outputs:
            if output_socket.name == "Master Output":
                for link in output_socket.links:
                    group_node = link.to_node
                    if isinstance(group_node, bpy.types.ShaderNodeGroup):
                        target_socket_name = link.to_socket.name
                        group_node_tree = group_node.node_tree
                        for node in group_node_tree.nodes:
                            if node.type == 'GROUP_INPUT':
                                for input_socket in node.outputs:
                                    if input_socket.name == target_socket_name:
                                        for inner_link in input_socket.links:
                                            connected_node = inner_link.to_node
                                            if hasattr(connected_node, 'float_edge'):
                                                connected_node.float_edge_checker = .05
                                                connected_node.float_edge = self.float_edge
        
        self.float_edge_checker = self.float_edge
        
        
def channel_edge_updater(self, context):
    if self.float_edge != self.float_edge_checker:
        effect_type = None
        
        universal_updater(self, context, 8, round(self.float_edge), self.influence, effect_type)
        
        if context.scene.scene_props.channel_controller_is_active:
            for obj in context.selected_objects:
                if hasattr(obj, "float_edge"):
                    universal_updater(obj.name, context, 8, round(self.float_edge), self.influence, effect_type)
        
        self.float_edge_checker = self.float_edge
        
        
#################
# SPEED
#################         
def group_speed_updater(self, context):
    if self.float_gobo_speed != self.float_speed_checker:
        if self.use_fan_center_speed:
            effect_type = "fan_center"
        else: effect_type = None
        
        speed_min = self.speed_min
        speed_max = self.speed_max
        
        # Maps value to send by calculating between value input and min/max inputs
        speed_value = ((self.float_gobo_speed / 100.0) * (speed_max - speed_min)) + speed_min
        
        normalized_value = (self.float_gobo_speed + 100) / 200
        mapped_value = (normalized_value * (speed_max - speed_min)) + speed_min

        universal_updater(self, context, 9, round(mapped_value), self.influence, effect_type)
        self.float_speed_checker = self.float_gobo_speed
        
        
def group_driver_speed_updater(self, context):
    if self.float_gobo_speed != self.float_speed_checker:
        for output_socket in self.outputs:
            for link in output_socket.links:
                connected_node = link.to_socket.node
                if hasattr(connected_node, "float_intensity_checker"):
                  connected_node.float_speed_checker = .05
                  connected_node.float_gobo_speed = self.float_gobo_speed
        
        self.float_speed_checker = self.float_gobo_speed
        
        
def master_speed_updater(self, context):
    if self.float_gobo_speed != self.float_speed_checker:
        for output_socket in self.outputs:
            if output_socket.name == "Master Output":
                for link in output_socket.links:
                    group_node = link.to_node
                    if isinstance(group_node, bpy.types.ShaderNodeGroup):
                        target_socket_name = link.to_socket.name
                        group_node_tree = group_node.node_tree
                        for node in group_node_tree.nodes:
                            if node.type == 'GROUP_INPUT':
                                for input_socket in node.outputs:
                                    if input_socket.name == target_socket_name:
                                        for inner_link in input_socket.links:
                                            connected_node = inner_link.to_node
                                            if hasattr(connected_node, 'float_speed'):
                                                connected_node.float_speed_checker = .05
                                                connected_node.float_speed = self.float_speed
        
        self.float_speed_checker = self.float_gobo_speed
        
        
def channel_speed_updater(self, context):
    if self.float_gobo_speed != self.float_speed_checker:
        effect_type = None
        
        speed_min = context.scene.scene_props.speed_min
        speed_max = context.scene.scene_props.speed_max
        
        # Maps value to send by calculating between value input and min/max inputs
        speed_value = ((self.float_gobo_speed / 100.0) * (speed_max - speed_min)) + speed_min
        
        normalized_value = (self.float_gobo_speed + 100) / 200
        mapped_value = (normalized_value * (speed_max - speed_min)) + speed_min
        
        universal_updater(self, context, 9, round(mapped_value), self.influence, effect_type)
        self.float_speed_checker = self.float_gobo_speed
        

#################
# GOBO ID
#################         
def group_gobo_id_updater(self, context):
    if self.int_gobo_id != self.gobo_id_checker:
        effect_type = None
        
        universal_updater(self, context, 10, round(self.int_gobo_id), self.influence, effect_type)
        self.gobo_id_checker = self.int_gobo_id
        
        
def group_driver_gobo_id_updater(self, context):
    if self.int_gobo_id != self.gobo_id_checker:
        for output_socket in self.outputs:
            for link in output_socket.links:
              connected_node = link.to_socket.node
              if hasattr(connected_node, "float_intensity_checker"):
                connected_node.int_gobo_id_checker = 30
                connected_node.int_gobo_id = self.int_gobo_id
        
        self.gobo_id_checker = self.int_gobo_id
        
        
def master_gobo_id_updater(self, context):
    if self.int_gobo_id != self.gobo_id_checker:
        for output_socket in self.outputs:
            if output_socket.name == "Master Output":
                for link in output_socket.links:
                    group_node = link.to_node
                    if isinstance(group_node, bpy.types.ShaderNodeGroup):
                        target_socket_name = link.to_socket.name
                        group_node_tree = group_node.node_tree
                        for node in group_node_tree.nodes:
                            if node.type == 'GROUP_INPUT':
                                for input_socket in node.outputs:
                                    if input_socket.name == target_socket_name:
                                        for inner_link in input_socket.links:
                                            connected_node = inner_link.to_node
                                            if hasattr(connected_node, 'int_gobo_id'):
                                                connected_node.int_gobo_id_checker = 30
                                                connected_node.int_gobo_id = self.int_gobo_id
        
        self.gobo_id_checker = self.int_gobo_id
        
        
def channel_gobo_id_updater(self, context):
    if self.int_gobo_id != self.gobo_id_checker:
        effect_type = None
        
        universal_updater(self, context, 10, round(self.int_gobo_id), self.influence, effect_type)
        
        if context.scene.scene_props.channel_controller_is_active:
            for obj in context.selected_objects:
                if hasattr(obj, "int_gobo_id"):
                    universal_updater(obj, context, 10, round(self.int_gobo_id), self.influence, effect_type)
        
        self.gobo_id_checker = self.int_gobo_id
        
        
#################
# PRISM
#################         
def group_prism_updater(self, context):
    if self.int_prism != self.prism_checker:
        effect_type = None
        
        universal_updater(self, context, 12, round(self.int_prism), self.influence, effect_type)
        self.prism_checker = self.int_prism
        
        
def group_driver_prism_updater(self, context):
    if self.int_prism != self.prism_checker:
        for output_socket in self.outputs:
            for link in output_socket.links:
              connected_node = link.to_socket.node
              if hasattr(connected_node, "float_intensity_checker"):
                conneted_node.int_prism_checker = 2
                connected_node.int_prism = self.int_prism
        
        self.int_prism_checker = self.int_prism
        
        
def master_prism_updater(self, context):
    if self.int_prism != self.prism_checker:
        for output_socket in self.outputs:
            if output_socket.name == "Master Output":
                for link in output_socket.links:
                    group_node = link.to_node
                    if isinstance(group_node, bpy.types.ShaderNodeGroup):
                        target_socket_name = link.to_socket.name
                        group_node_tree = group_node.node_tree
                        for node in group_node_tree.nodes:
                            if node.type == 'GROUP_INPUT':
                                for input_socket in node.outputs:
                                    if input_socket.name == target_socket_name:
                                        for inner_link in input_socket.links:
                                            connected_node = inner_link.to_node
                                            if hasattr(connected_node, 'int_prism'):
                                                connected_node.int_prism_checker = 2
                                                connected_node.int_prism = self.int_prism
        
        self.int_prism_checker = self.int_prism
        
        
def channel_prism_updater(self, context):
    if self.int_prism != self.prism_checker:
        effect_type = None
        
        universal_updater(self, context, 12, round(self.int_prism), self.influence, effect_type)
        self.prism_checker = self.int_prism
        
        
####################
# UNIVERSAL UPDATER
####################
def universal_updater(self, context, parameter_name, current_value, influence, effect_type):
    scene = context.scene.scene_props
    if scene.nodes_are_armed:
        address = scene.str_command_line_address
        
        if hasattr(self, 'str_group_channels') and self.bl_idname == 'group_controller_type':
            channel_string = self.str_group_channels
            
            # Convert the string to a list of integers and ensure it's sorted.
            channel_list = sorted([int(channel.strip()) for channel in channel_string.split(',') if channel.strip().isdigit()])
            
            # Apply the effect based on the effect_type.
            if effect_type == 'fan_center':
                channel_values = apply_fan_center_effect(channel_list, current_value)
            elif effect_type is None:  # No effect.
                channel_values = {chan: current_value for chan in channel_list}
            elif effect_type == "mixer":
                pass
                
        elif hasattr(self, 'type') and self.type == 'MESH' and self.is_influencer:
            channel_list = get_lights_inside_mesh(self)
            
        elif hasattr(self, 'type') and self.type == 'LIGHT':
            
            pass
    
        arguments = []
        
        enable_syntax = ""
        disable_syntax = ""
        if parameter_name == 5:
            enable_syntax = self.str_enable_strobe_argument
            disable_syntax = self.str_disable_strobe_argument
            
        if parameter_name == 9:
            enable_syntax = self.str_enable_gobo_speed_argument
            disable_syntax = self.str_disable_gobo_speed_argument
            
        if parameter_name == 11:
            enable_syntax = self.str_enable_misc_effect_argument
            disable_syntax = self.str_disable_misc_effect_argument

        if parameter_name == 12:
            enable_syntax = self.str_enable_prism_argument
            disable_syntax = self.str_disable_prism_argument
            
        global change_requests
        
        # This is for the group controllers.
        if hasattr(self, 'str_group_channels') and self.bl_idname == 'group_controller_type':
            for chan, value in channel_values.items():
                chan_argument = construct_argument(self, scene, chan, parameter_name, value, enable_syntax, disable_syntax)
                arguments.append(chan_argument)
                change_requests.append((chan, parameter_name, value, influence, chan_argument))
            argument = ", ".join(arguments)
            
        # This is for the influencers.
        elif hasattr(self, 'type') and self.type == 'MESH' and self.is_influencer:
            for chan in channel_list:
                chan_argument = construct_argument(self, scene, chan.name, parameter_name, current_value, enable_syntax, disable_syntax)
                change_requests.append((str(chan.name), parameter_name, current_value, influence, chan_argument))
                arguments.append(chan_argument)
            argument = ", ".join(arguments)
            
        # This is for the channels' own properties.
        else:
            if not hasattr(self, "name"):
                argument = construct_argument(self, scene, self, parameter_name, current_value, enable_syntax, disable_syntax)
                change_requests.append((str(self), parameter_name, current_value, influence, argument))

            else:
                argument = construct_argument(self, scene, self.name, parameter_name, current_value, enable_syntax, disable_syntax)
                change_requests.append((str(self.name), parameter_name, current_value, influence, argument))
            
        # Send the OSC message now if not playing.
        if not scene.is_playing:
            send_osc_string(address, scene.str_osc_ip_address, scene.int_osc_port, argument)


#################
# CONSTRUCT ARGS
#################   
def construct_argument(self, scene, chan, parameter, value, enable, disable):
    value_rounded = round(value)

    if -10 < value_rounded < 0:
        value_str = "-0" + str(abs(value_rounded))
    elif 0 < value_rounded < 10:
        value_str = "0" + str(value_rounded)
    elif value_rounded == 0:
        value_str = "0"
    else:
        value_str = "{:02}".format(value_rounded) 
        
    if parameter == 1:
        template = scene.str_intensity_argument
        
    elif parameter == 2:
        template = scene.str_pan_argument
        
    elif parameter == 3:
        template = scene.str_tilt_argument
        
    elif parameter == 4:
        template = scene.str_diffusion_argument
        
    elif parameter == 5:
        template = scene.str_strobe_argument
        
    elif parameter == 6:
        template = scene.str_zoom_argument
        
    elif parameter == 7:
        template = scene.str_iris_argument
        
    elif parameter == 8:
        template = scene.str_edge_argument
        
    elif parameter == 9:
        template = self.str_gobo_speed_value_argument
        
    elif parameter == 10:
        template = self.str_gobo_id_argument
        
    elif parameter == 11:
        template = ""
        
    elif parameter == 12:
        template = ""
        
    elif parameter == 13:
        template = scene.str_red_argument
        
    elif parameter == 14:
        template = scene.str_green_argument
        
    elif parameter == 15:
        template = scene.str_blue_argument
        
    elif parameter == 16:
        template = scene.str_amber_argument
        
    elif parameter == 17:
        template = scene.str_white_argument
        
    elif parameter == 18:
        template = scene.str_lime_argument
        
    elif parameter == 19:
        template = scene.str_mint_argument
        
    elif parameter == 20:
        template = scene.str_cyan_argument
        
    elif parameter == 21:
        template = scene.str_magenta_argument
        
    elif parameter == 22:
        template = scene.str_yellow_argument
        
    if parameter == 5 and value == 0 and disable:
        template = scene.str_strobe_argument + ", " + disable
    elif parameter == 5 and value != 0 and enable:
        template = scene.str_strobe_argument + ", " + enable
        
    if parameter == 9 and value == 0 and disable:
        template = self.str_gobo_speed_value_argument + ", " + disable
    elif parameter == 9 and value != 0 and enable:
        template = self.str_gobo_speed_value_argument + ", " + enable
        
    if parameter == 11 and value == 0 and disable:
        template = scene.str_misc_effect_argument + ", " + disable
    elif parameter == 1 and value != 0 and enable:
        template = scene.str_misc_effect_argument + ", " + enable
        
    if parameter == 12 and value == 0 and disable:
        template = scene.str_prism_argument + ", " + disable
    elif parameter == 12 and value != 0 and enable:
        template = scene.str_prism_argument + ", " + enable

    chan_argument = template.replace('$', value_str)
    chan_id = scene.str_channel_template.replace('*', str(chan))
    chan_argument = chan_argument.replace('#', str(chan_id))
    
    return chan_argument


#################
# PUBLISHING
#################   
@persistent
def load_changes_handler(scene):
    if scene.scene_props.nodes_are_armed:
        scene.scene_props.is_playing = True
        
        # Force updates without sending osc, but this will update the change_requests list.
        world = scene.world

        if world is not None and world.node_tree:
            node_tree = world.node_tree

            for controller in node_tree.nodes:
                if controller.bl_idname in ['group_controller_type', 'group_driver_type', 'master_type']:
                    controller.float_intensity = controller.float_intensity
                    controller.float_pan = controller.float_pan
                    controller.float_tilt = controller.float_tilt
                    controller.float_zoom = controller.float_zoom
                    controller.float_iris = controller.float_iris
                    controller.float_edge = controller.float_edge
                    controller.float_diffusion = controller.float_diffusion
                    controller.int_gobo_id = controller.int_gobo_id
                    controller.float_strobe = controller.float_strobe
                    controller.float_gobo_speed = controller.float_gobo_speed
                    controller.int_prism = controller.int_prism
                if controller.bl_idname in ['mixer_type', 'mixer_driver_type']:
                    controller.float_intensity_one = controller.float_intensity_one
                    controller.float_intensity_two = controller.float_intensity_two
                    controller.float_intensity_three = controller.float_intensity_three
                    ## This has a bug, don't have time to fix right now.
                    #controller.float_vec_color_one = controller.float_vec_color_one
                    #controller.float_vec_color_two = controller.float_vec_color_two
                    #controller.float_vec_color_three = controller.float_vec_color_three
                    controller.float_pan_one = controller.float_pan_one
                    controller.float_pan_two = controller.float_pan_two
                    controller.float_pan_three = controller.float_pan_three
                    controller.float_tilt_one = controller.float_tilt_one
                    controller.float_tilt_two = controller.float_tilt_two
                    controller.float_tilt_three = controller.float_tilt_three
            
        for object in bpy.data.objects:
            if object.type == 'MESH':
                object.float_intensity = object.float_intensity
                object.float_pan = object.float_pan
                object.float_tilt = object.float_tilt
                object.float_zoom = object.float_zoom
                object.float_iris = object.float_iris
                object.float_edge = object.float_edge
                object.float_diffusion = object.float_diffusion
                object.int_gobo_id = object.int_gobo_id
                object.float_strobe = object.float_strobe
                object.float_gobo_speed = object.float_gobo_speed
                object.int_prism = object.int_prism
                object.float_vec_pan_tilt_graph = object.float_vec_pan_tilt_graph
        
    
# This function assists with the process of replacing the harmonized.
# value inside preformatted argument strings when in democratic mode.
# This will soon be replaced with much smarter/faster system that doesn't preformat.
def update_argument(argument, original_value, new_value):
    # This assumes that the value is a distinct, identifiable part of the argument
    # and that it appears in the argument in a way that can be uniquely replaced.
    try:
        updated_argument = re.sub(r'\b{}\b'.format(re.escape(str(original_value))), str(new_value), argument, count=1)
        return updated_argument
    except re.error as e:
        print(f"Regex error during argument update: {e}")
        return argument


@persistent
def publish_changes_handler(scene):
    if scene.scene_props.nodes_are_armed:
        scene.scene_props.is_playing = False
        global change_requests

        '''CPVIA stands for channel, parameter, value, influence, and argument'''

        # Ensure consistent channel numbers.
        change_requests = [(int(round(float(c))), p, v, i, a) for c, p, v, i, a in change_requests]
        
        highest_requests = {}
        harmonized_requests = []

        if scene.scene_props.is_not_democratic:
            for c, p, v, i, a in change_requests:
                
                key = (c, p)
                if key not in highest_requests or v > highest_requests[key][2]:
                    highest_requests[key] = (c, p, v, i, a)
            harmonized_requests = list(highest_requests.values())
        else:  # Democratic mode
            votes = defaultdict(lambda: defaultdict(list))
            for c, p, v, i, a in change_requests:
                votes[c][p].append((v, i))
                
            for c, params in votes.items():
                for p, value_influences in params.items():
                    total_influence = sum(influence for _, influence in value_influences)
                    weighted_sum = sum(value * influence for value, influence in value_influences)
                    
                    if total_influence > 0:
                        calculated_value = weighted_sum / total_influence
                        # Assume original_value is available or can be determined.
                        original_value = ...

                        if c != original_value:
                            # Update the argument with the new value.
                            harmonized_argument = update_argument(a, original_value, round(calculated_value))
                            harmonized_requests.append((c, p, round(calculated_value), None, harmonized_argument))
                        else:
                            print(f"Warning: Could not harmonize value in update for channel {c} with value {original_value}. Change request discarded.")

        # Reset change_requests for the next frame.
        change_requests = []
        str_arguments = ""
        counter = 0

        # Construct and send OSC messages.
        for message in harmonized_requests:
            _, _, _, _, a = message
            
    #        formatted_c = f"{c:02d}" if c >= 0 else f"-{-c:02d}"  # Format channel number
    #        argument = f"Chan {formatted_c} {parameter_mapping.get(p, 'Unknown')} at {v} Enter"
    #        
    #        formatted_c = f"{c:02d}" if c >= 0 else f"-{-c:02d}"  # Format channel number
            argument = str(a)
            
            if counter != 0:
                str_arguments += ", "
            str_arguments += argument
            counter += 1

            if counter == 100:
                send_osc_string(scene.scene_props.str_command_line_address, scene.scene_props.str_osc_ip_address, scene.scene_props.int_osc_port, str_arguments)
                
                str_arguments = ""
                counter = 0

        if str_arguments:
            send_osc_string(scene.scene_props.str_command_line_address, scene.scene_props.str_osc_ip_address, scene.scene_props.int_osc_port, str_arguments)


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


class AlvaNodeTree(bpy.types.NodeTree):
    bl_idname = 'AlvaNodeTree'
    bl_label = 'Sorcerer Nodes'
    bl_icon = 'NODETREE'


#class AlvaNodeCategory(NodeCategory):
#    @classmethod
#    def poll(cls, context):
#        return context.space_data.tree_type == 'AlvaNodeTree'
#    
# This is for side enum in built-in add menu.
#alva_node_categories = [
#    AlvaNodeCategory("ALVA_NODES", "Sorcerer Nodes", items=[
#        NodeItem("mixer_type"),
#        NodeItem("mixer_driver_type"),
#        NodeItem("group_controller_type"),
#        NodeItem("group_driver_type"),
#    ]),
#]
    

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
        ]
        return items

    str_group_id: bpy.props.StringProperty(default="1")
    str_group_channels: bpy.props.StringProperty(default="")
    str_group_label: bpy.props.StringProperty(default="")

    influence: bpy.props.IntProperty(default=1, min=1, max=10, description="How many votes this controller has when there are conflicts", options={'ANIMATABLE'})

    float_influence_checker: bpy.props.FloatProperty(default=0, description="How much influence this controller has", options={'ANIMATABLE'})

    parameters_enum: bpy.props.EnumProperty(
        name="Parameter",
        description="Choose a parameter type to mix",
        items=mixer_parameters,
        update=group_info_updater_mixer,
        default=1
    )

    str_selected_group: bpy.props.EnumProperty(
        name="Selected Group",
        description="Choose a group to control. Create these groups with the Patch function on the N tab in node editor, with USITT ASCII import in the same area, or create/modify them in Properties -> World -> SORCERER: Group Channel Blocks (full screen).",
        items=group_objects,
        update=group_info_updater_mixer
    )
    
    float_intensity_one: bpy.props.FloatProperty(default=0, min=0, max=100, update=mixer_intensity_updater)
    float_intensity_one_checker: bpy.props.FloatProperty(default=0)
    float_intensity_two: bpy.props.FloatProperty(default=0, min=0, max=100, update=mixer_intensity_updater_pointer)
    float_intensity_two_checker: bpy.props.FloatProperty(default=0)
    float_intensity_three: bpy.props.FloatProperty(default=0, min=0, max=100, update=mixer_intensity_updater_pointer)
    float_intensity_three_checker: bpy.props.FloatProperty(default=0)
    
    color_profile_enum: bpy.props.EnumProperty(
        name="Color Profile",
        description="Choose a color profile for the group",
        items=color_profiles,
    )
    
    float_vec_color_one: bpy.props.FloatVectorProperty(
        name="",
        subtype='COLOR',
        size=3,
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        description="Color value",
        update=mixer_color_updater
    )
    
    float_vec_color_one_checker: bpy.props.FloatVectorProperty(
        name="",
        subtype='COLOR',
        size=3,
        default=(1.0, 1.0, 1.0),
    )
    
    float_vec_color_two: bpy.props.FloatVectorProperty(
        name="",
        subtype='COLOR',
        size=3,
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        description="Color value",
        update=mixer_color_updater_pointer
    )
    
    float_vec_color_two_checker: bpy.props.FloatVectorProperty(
        name="",
        subtype='COLOR',
        size=3,
        default=(1.0, 1.0, 1.0),
    )
    
    float_vec_color_three: bpy.props.FloatVectorProperty(
        name="",
        subtype='COLOR',
        size=3,
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        description="Color value",
        update=mixer_color_updater_pointer
    )
    
    float_vec_color_three_checker: bpy.props.FloatVectorProperty(
        name="",
        subtype='COLOR',
        size=3,
        default=(1.0, 1.0, 1.0),
    )
    
    float_pan_one: bpy.props.FloatProperty(default=0, min=-315, max=315, update=mixer_pan_updater)
    float_pan_one_checker: bpy.props.FloatProperty(default=0)
    float_pan_two: bpy.props.FloatProperty(default=0, min=-315, max=315, update=mixer_pan_updater_pointer)
    float_pan_two_checker: bpy.props.FloatProperty(default=0)
    float_pan_three: bpy.props.FloatProperty(default=0, min=-315, max=315,update=mixer_pan_updater_pointer)
    float_pan_three_checker: bpy.props.FloatProperty(default=0)
    
    float_tilt_one: bpy.props.FloatProperty(default=0, min=-135, max=135, update=mixer_tilt_updater)
    float_tilt_one_checker: bpy.props.FloatProperty(default=0)
    float_tilt_two: bpy.props.FloatProperty(default=0, min=-135, max=135, update=mixer_tilt_updater_pointer)
    float_tilt_two_checker: bpy.props.FloatProperty(default=0)
    float_tilt_three: bpy.props.FloatProperty(default=0, min=-135, max=135, update=mixer_tilt_updater_pointer)
    float_tilt_three_checker: bpy.props.FloatProperty(default=0)
    
    show_middle: bpy.props.BoolProperty(default=True)
    every_other: bpy.props.BoolProperty(default=False)
    
    collapse_most: bpy.props.BoolProperty(default=False)
    
    def init(self, context):
        self.inputs.new('MixerInputType', "Driver Input")
        self.outputs.new('FlashOutType', "Flash")
        return

    def draw_buttons(self, context, layout):    
        if not self.collapse_most:    
            row = layout.row(align=True)
            op_home = row.operator("node.home_group", icon='HOME', text="Home")
            op_home.node_name = self.name
            op_update = row.operator("node.update_group", icon='FILE_REFRESH', text="Update")
            op_update.node_name = self.name
            
            row = layout.row(align=True)
            row.prop(self, "str_selected_group", text="", icon_only=0, icon='STICKY_UVS_LOC')
            row.prop(self, "parameters_enum", text="")
            if self.parameters_enum == 'option_color':
                row.prop(self, "color_profile_enum", text="")
            
            layout.separator()
        
        if self.parameters_enum == 'option_intensity':
            row = layout.row()
            row.prop(self, "float_intensity_one", text="Intensity 1", slider=True)
            if self.show_middle:
                row.prop(self, "float_intensity_two", text="Intensity 2", slider=True)
            row.prop(self, "float_intensity_three", text="Intensity 3", slider=True)
            
        elif self.parameters_enum == 'option_color':
            row = layout.row()
            row.template_color_picker(self, "float_vec_color_one")
            if self.show_middle:
                row.template_color_picker(self, "float_vec_color_two")
            row.template_color_picker(self, "float_vec_color_three")
            
        elif self.parameters_enum == 'option_pan_tilt':
            row = layout.row()
            row.prop(self, "float_pan_one", text="Pan 1", slider=True)
            if self.show_middle:
                row.prop(self, "float_pan_two", text="Pan 2", slider=True)
            row.prop(self, "float_pan_three", text="Pan 3", slider=True)
            row = layout.row()
            row.prop(self, "float_tilt_one", text="Tilt 1", slider=True)
            if self.show_middle:
                row.prop(self, "float_tilt_two", text="Tilt 2", slider=True)
            row.prop(self, "float_tilt_three", text="Tilt 3", slider=True)  
            
        else: row.label(text="No parameter selected.")         
        
        if not self.collapse_most:
            row = layout.row()
            row.prop(self, "collapse_most", text="", icon='HIDE_OFF', emboss=False)
                        
        if not self.collapse_most:
            if self.parameters_enum != None:
                row.prop(self, "show_middle", text="Show Middle", slider=True)
                
                if not self.show_middle:
                    row.prop(self, "every_other", text="Every Other", slider=True)
    
    
class MixerDriverNode(bpy.types.Node):
    bl_idname = 'mixer_driver_type'
    bl_label = 'Mixer Driver Node'
    bl_icon = 'DECORATE_DRIVER'
    bl_width_default = 150
    
    def mixer_parameters(self, context):
        items = [
            ('option_intensity', "Intensity", "Mix intensities across a group", 'OUTLINER_OB_LIGHT', 1),
            ('option_color', "Color", "Mix colors across a group", 'COLOR', 2),
            ('option_pan_tilt', "Pan/Tilt", "Mix pan/tilt settings across a group", 'ORIENTATION_GIMBAL', 3),
        ]
        return items

    influence: bpy.props.IntProperty(default=1, min=1, max=10, description="How many votes this controller has when there are conflicts", options={'ANIMATABLE'})

    float_influence_checker: bpy.props.FloatProperty(default=0, description="How much influence this controller has", options={'ANIMATABLE'})

    parameters_enum: bpy.props.EnumProperty(
        name="Parameter",
        description="Choose a parameter type to mix",
        items=mixer_parameters,
        update=group_info_updater_mixer,
        default=1
    )
    
    float_intensity_one: bpy.props.FloatProperty(default=0, min=0, max=100, update=mixer_driver_intensity_updater)
    float_intensity_one_checker: bpy.props.FloatProperty(default=0)
    float_intensity_two: bpy.props.FloatProperty(default=0, min=0, max=100, update=mixer_intensity_updater_pointer)
    float_intensity_two_checker: bpy.props.FloatProperty(default=0)
    float_intensity_three: bpy.props.FloatProperty(default=0, min=0, max=100, update=mixer_intensity_updater_pointer)
    float_intensity_three_checker: bpy.props.FloatProperty(default=0)
    
    color_profile_enum: bpy.props.EnumProperty(
        name="Color Profile",
        description="Choose a color profile for the group",
        items=color_profiles,
        default=1
    )
    
    float_vec_color_one: bpy.props.FloatVectorProperty(
        name="",
        subtype='COLOR',
        size=3,
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        description="Color value",
        update=mixer_driver_color_updater
    )
    
    float_vec_color_one_checker: bpy.props.FloatVectorProperty(
        name="",
        subtype='COLOR',
        size=3,
        default=(1.0, 1.0, 1.0),
    )
    
    float_vec_color_two: bpy.props.FloatVectorProperty(
        name="",
        subtype='COLOR',
        size=3,
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        description="Color value",
        update=mixer_color_updater_pointer
    )
    
    float_vec_color_two_checker: bpy.props.FloatVectorProperty(
        name="",
        subtype='COLOR',
        size=3,
        default=(1.0, 1.0, 1.0),
    )
    
    float_vec_color_three: bpy.props.FloatVectorProperty(
        name="",
        subtype='COLOR',
        size=3,
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        description="Color value",
        update=mixer_color_updater_pointer
    )
    
    float_vec_color_three_checker: bpy.props.FloatVectorProperty(
        name="",
        subtype='COLOR',
        size=3,
        default=(1.0, 1.0, 1.0),
    )
    
    float_pan_one: bpy.props.FloatProperty(default=0, min=-315, max=315, update=mixer_driver_pan_updater)
    float_pan_one_checker: bpy.props.FloatProperty(default=0)
    float_pan_two: bpy.props.FloatProperty(default=0, min=-315, max=315, update=mixer_pan_updater_pointer)
    float_pan_two_checker: bpy.props.FloatProperty(default=0)
    float_pan_three: bpy.props.FloatProperty(default=0, min=-315, max=315, update=mixer_pan_updater_pointer)
    float_pan_three_checker: bpy.props.FloatProperty(default=0)
    
    float_tilt_one: bpy.props.FloatProperty(default=0, min=-135, max=135, update=mixer_driver_tilt_updater)
    float_tilt_one_checker: bpy.props.FloatProperty(default=0)
    float_tilt_two: bpy.props.FloatProperty(default=0, min=-135, max=135, update=mixer_tilt_updater_pointer)
    float_tilt_two_checker: bpy.props.FloatProperty(default=0)
    float_tilt_three: bpy.props.FloatProperty(default=0, min=-135, max=135, update=mixer_tilt_updater_pointer)
    float_tilt_three_checker: bpy.props.FloatProperty(default=0)
    
    show_middle: bpy.props.BoolProperty(default=True)
    every_other: bpy.props.BoolProperty(default=False)
    
    collapse_most: BoolProperty(default=False)
    
    def init(self, context):
        self.outputs.new('MixerOutputType', "Driver Output")
        self.outputs.new('FlashOutType', "Flash")
        return
        
    def draw_buttons(self, context, layout):
        if not self.collapse_most:  
            row = layout.row(align=True)      
            op_home = row.operator("node.home_group", icon='HOME', text="Home")
            op_home.node_name = self.name
            op_update = row.operator("node.update_group", icon='FILE_REFRESH', text="Update")
            op_update.node_name = self.name
            
            row = layout.row(align=True)
            row.prop(self, "parameters_enum", text="")
            if self.parameters_enum == 'option_color':
                row.prop(self, "color_profile_enum", text="")
            
            layout.separator()
        
        if self.parameters_enum == 'option_intensity':
            row = layout.row()
            row.prop(self, "float_intensity_one", text="Intensity 1", slider=True)
            if self.show_middle:
                row = layout.row()
                row.prop(self, "float_intensity_two", text="Intensity 2", slider=True)
            row = layout.row()
            row.prop(self, "float_intensity_three", text="Intensity 3", slider=True)
            
        elif self.parameters_enum == 'option_color':
            row = layout.row()
            row.template_color_picker(self, "float_vec_color_one")
            if self.show_middle:
                row.template_color_picker(self, "float_vec_color_two")
            row.template_color_picker(self, "float_vec_color_three")
            
        elif self.parameters_enum == 'option_pan_tilt':
            row = layout.row()
            row.prop(self, "float_pan_one", text="Pan 1", slider=True)
            if self.show_middle:
                row.prop(self, "float_pan_two", text="Pan 2", slider=True)
            row.prop(self, "float_pan_three", text="Pan 3", slider=True)
            
            row = layout.row()
            row.prop(self, "float_tilt_one", text="Tilt 1", slider=True)
            if self.show_middle:
                row.prop(self, "float_tilt_two", text="Tilt 2", slider=True)
            row.prop(self, "float_tilt_three", text="Tilt 3", slider=True)  
            
        else: row.label(text="No parameter selected.")  
        
        if not self.collapse_most:
            row = layout.row()
            row.prop(self, "collapse_most", text="", icon='HIDE_ON' if self.collapse_most else 'HIDE_OFF')
                           
        if not self.collapse_most:
            if self.parameters_enum != None:
                row.prop(self, "show_middle", text="Show Middle", slider=True)
                
                if not self.show_middle:
                    row.prop(self, "every_other", text="Every Other", slider=True)
    

class GroupControllerNode(bpy.types.Node):
    bl_idname = 'group_controller_type'
    bl_label = 'Group Controller Node'
    bl_icon = 'STICKY_UVS_LOC'
    bl_width_default = 200
    
    # Assigned by group_info_updater on str_selected_light property.
    str_group_id: StringProperty(default="1")
    str_group_channels: StringProperty(default="")
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
    pan_min: bpy.props.IntProperty(default=-270, description="Minimum value for pan")
    pan_max: bpy.props.IntProperty(default=270, description="Maximum value for pan")
    tilt_min: bpy.props.IntProperty(default=-135, description="Minimum value for tilt")
    tilt_max: bpy.props.IntProperty(default=135, description="Maximum value for tilt")
    strobe_min: bpy.props.IntProperty(default=0, description="Minimum value for strobe")
    strobe_max: bpy.props.IntProperty(default=10, description="Maximum value for strobe")
    zoom_min: bpy.props.IntProperty(default=1, description="Minimum value for zoom")
    zoom_max: bpy.props.IntProperty(default=100, description="Maximum value for zoom")   
    iris_min: bpy.props.IntProperty(default=0, description="Minimum value for iris")
    iris_max: bpy.props.IntProperty(default=100, description="Maximum value for iris")  
    edge_min: bpy.props.IntProperty(default=0, description="Minimum value for edge")
    edge_max: bpy.props.IntProperty(default=100, description="Maximum value for edge")  
    speed_min: bpy.props.IntProperty(default=-200, description="Minimum value for speed")
    speed_max: bpy.props.IntProperty(default=200, description="Maximum value for speed")
    changer_speed_min: IntProperty(default=0, description="Minimum value for changer speed")
    changer_speed_max: IntProperty(default=0, description="Maximum value for changer speed")

    # Selected group and color profile enumerators.
    str_selected_light: EnumProperty(
        name="Selected Light",
        description="Choose a group to control. Create these groups with the Patch function on the N tab in node editor, with USITT ASCII import in the same area, or create/modify them in Properties -> World -> SORCERER: Group Channel Blocks (full screen).",
        items=lamp_objects,
        update=group_info_updater
    )
    color_profile_enum: EnumProperty(
        name="Color Profile",
        description="Choose a color profile for the group",
        items=color_profiles,
    )
    
    # User-accessible property definitions.
    influence: IntProperty(default=1, min=1, max=10, description="How many votes this controller has when there are conflicts", options={'ANIMATABLE'})
    float_intensity: FloatProperty(default=0, min=0, max=100, description="Intensity value", options={'ANIMATABLE'}, update=group_intensity_updater)
    float_vec_color: FloatVectorProperty(
        name="",
        subtype='COLOR',
        size=3,
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        description="Color value",
        update=group_color_updater
    )
    float_diffusion: FloatProperty(default=0, min=0, max=100, description="Diffusion value", options={'ANIMATABLE'}, update=group_diffusion_updater)
    float_pan: bpy.props.FloatProperty(default=0, min=-315, max=315, description="Pan value", options={'ANIMATABLE'}, update=group_pan_updater)
    float_tilt: FloatProperty(default=0, min=-135, max=135, description="Tilt value", options={'ANIMATABLE'}, update=group_tilt_updater)
    float_strobe: FloatProperty(default=0, min=0, max=100, description="Strobe value", options={'ANIMATABLE'}, update=group_strobe_updater)
    float_zoom: FloatProperty(default=0, min=0, max=100, description="Zoom value", options={'ANIMATABLE'}, update=group_zoom_updater)
    float_iris: FloatProperty(default=0, min=0, max=100, description="Iris value", options={'ANIMATABLE'}, update=group_iris_updater)
    float_edge: FloatProperty(default=0, min=0, max=100, description="Edge value", options={'ANIMATABLE'}, update=group_edge_updater)
    int_gobo_id: IntProperty(default=1, min=0, max=20, description="Gobo selection", options={'ANIMATABLE'}, update=group_gobo_id_updater)
    float_gobo_speed: FloatProperty(default=0, min=-100, max=100, description="Rotation of individual gobo speed", options={'ANIMATABLE'}, update=group_speed_updater)
    float_disc_speed: FloatProperty(default=0, min=-100, max=100, description="Rotation of gobo disc/wheel speed", options={'ANIMATABLE'})
    int_prism: IntProperty(default=0, min=0, max=1, description="Prism value. 1 is on, 0 is off", options={'ANIMATABLE'}, update=group_prism_updater)
    
    # Checkers for aborting redundant updates from frame_change_pre handler.
    float_influence_checker: FloatProperty(default=0, description="How much influence this controller has", options={'ANIMATABLE'})
    float_intensity_checker: FloatProperty(default=0, min=0, max=100, description="Intensity value", options={'ANIMATABLE'})
    float_vec_color_checker: FloatVectorProperty(name="", subtype='COLOR', size=3, default=(1.0, 1.0, 1.0))
    float_pan_checker: FloatProperty(default=0,)
    float_tilt_checker: FloatProperty(default=0)
    float_diffusion_checker: FloatProperty(default=0)
    float_strobe_checker: FloatProperty(default=0)
    float_zoom_checker: FloatProperty(default=0)
    float_iris_checker: FloatProperty(default=0)
    float_edge_checker: FloatProperty(default=0)
    gobo_id_checker: FloatProperty(default=0)
    float_speed_checker: FloatProperty(default=0)
    prism_checker: FloatProperty(default=0)    
    
    #Fan Center effect booleans.
    use_fan_center_intensity: BoolProperty(default=False, description="Use Fan Center effect")
    use_fan_center_tilt: BoolProperty(default=False, description="Use Fan Center effect")
    use_fan_center_pan: BoolProperty(default=False, description="Use Fan Center effect")
    use_fan_center_diffusion: BoolProperty(default=False, description="Use Fan Center effect")
    use_fan_center_strobe: BoolProperty(default=False, description="Use Fan Center effect")
    use_fan_center_zoom: BoolProperty(default=False, description="Use Fan Center effect")
    use_fan_center_iris: BoolProperty(default=False, description="Use Fan Center effect")
    use_fan_center_edge: BoolProperty(default=False, description="Use Fan Center effect")
    use_fan_center_speed: BoolProperty(default=False, description="Use Fan Center effect")
    
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

        # This was originally added to avoid using depsgraph_update handler to reduce traffic, may be cut from final.
#        active_influencer = bpy.data.objects.get(self.str_selected_light)
#        if active_influencer is not None and active_influencer.select_get() and active_influencer.type == 'MESH':
#            if active_influencer.is_influencer:
#                row = layout.row()
#                row.label(text="Influencer Location:")
#                row = layout.row(align=True)
#                row.prop(self, "influencer_x_location", toggle=True, text="X")
#                row = layout.row(align=True)
#                row.prop(self, "influencer_y_location", toggle=True, text="Y")
#                row = layout.row(align=True)
#                row.prop(self, "influencer_z_location", toggle=True, text="Z")
#                layout.separator()
#                layout.separator()

        row = layout.row(align=True)
        ## Use of row.alert logic here is probably redundant per existing Blender UI rules.
        if not self.str_selected_light:
            row.alert = 1
        row.prop(self, "str_selected_light", text="", icon_only=True, icon='LIGHT')
        row.alert = 0
        
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
            op.node_name = self.name
    
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
            op.node_name = self.name
            ## Need to switch to the blue color, not the red.
            if self.use_fan_center_pan:
                row.alert = 1
            row.prop(self, "use_fan_center_pan", text="", icon='PARTICLES')
            row.alert = 0
            row.prop(self, "float_pan", text="Pan", slider=True)
            if self.use_fan_center_tilt:
                row.alert = 1
            row.prop(self, "use_fan_center_tilt", text="", icon='PARTICLES')
            row.alert = 0
            row.prop(self, "float_tilt", text="Tilt", slider=True)
        
        if self.zoom_is_on or self.iris_is_on:
            row = layout.row(align=True)
            op = row.operator("my.view_zoom_iris_props", text="", icon='LINCURVE')
            op.node_name = self.name
            
            if self.zoom_is_on:
                if self.use_fan_center_zoom:
                    row.alert = 1
                row.prop(self, "use_fan_center_zoom", text="", icon='PARTICLES')
                row.alert = 0
                row.prop(self, "float_zoom", slider=True, text="Zoom:")
            if self.iris_is_on:
                if self.use_fan_center_iris:
                    row.alert = 1
                row.prop(self, "use_fan_center_iris", text="", icon='PARTICLES')
                row.alert = 0
                row.prop(self, "float_iris", slider=True, text="Iris:")
        
        if self.edge_is_on or self.diffusion_is_on:
            row = layout.row(align=True)
            op = row.operator("my.view_edge_diffusion_props", text="", icon='SELECT_SET')
            op.node_name = self.name
            
            if self.edge_is_on:
                if self.use_fan_center_zoom:
                    row.alert = 1
                row.prop(self, "use_fan_center_edge", text="", icon='PARTICLES')
                row.alert = 0
                row.prop(self, "float_edge", slider=True, text="Edge:")
            if self.diffusion_is_on:
                if self.use_fan_center_diffusion:
                    row.alert = 1
                row.prop(self, "use_fan_center_diffusion", text="", icon='PARTICLES')
                row.alert = 0
                row.prop(self, "float_diffusion", slider=True, text="Diffusion:")
        
        if self.gobo_id_is_on:
            row = layout.row(align=True)
            op = row.operator("my.view_gobo_props", text="", icon='POINTCLOUD_DATA')
            op.node_name = self.name
            
            row.prop(self, "int_gobo_id", text="Gobo:")
            row.prop(self, "float_gobo_speed", slider=True, text="Speed:")
            row.prop(self, "int_prism", slider=True, text="Prism:")
            

class GroupDriverNode(bpy.types.Node):
    bl_idname = 'group_driver_type'
    bl_label = 'Group Driver Node'
    bl_icon = 'DECORATE_DRIVER'
    bl_width_default = 200

    # Parameters
    float_intensity: bpy.props.FloatProperty(default=0, min=0, max=100, description="Intensity value", options={'ANIMATABLE'}, update=group_driver_intensity_updater)
    float_vec_color: bpy.props.FloatVectorProperty(
        name="",
        subtype='COLOR',
        size=3,
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        description="Color value",
        update=group_driver_color_updater
    )
    float_diffusion: bpy.props.FloatProperty(default=0, min=0, max=100, description="Diffusion value", options={'ANIMATABLE'}, update=group_driver_diffusion_updater)
    float_diffusion_checker: bpy.props.FloatProperty(default=0, min=0, max=100, description="Diffusion value", options={'ANIMATABLE'})
    float_pan: bpy.props.FloatProperty(default=0, min=-315, max=315, description="Pan value", options={'ANIMATABLE'}, update=group_driver_pan_updater)
    float_tilt: bpy.props.FloatProperty(default=0, min=-135, max=135, description="Tilt value", options={'ANIMATABLE'}, update=group_driver_tilt_updater)
    float_strobe: bpy.props.FloatProperty(default=0, min=0, max=100, description="Strobe value", options={'ANIMATABLE'}, update=group_driver_strobe_updater)
    float_zoom: bpy.props.FloatProperty(default=0, min=0, max=100, description="Zoom value", options={'ANIMATABLE'}, update=group_driver_zoom_updater)
    float_iris: bpy.props.FloatProperty(default=0, min=0, max=100, description="Iris value", options={'ANIMATABLE'}, update=group_driver_iris_updater)
    float_edge: bpy.props.FloatProperty(default=0, min=0, max=100, description="Edge value", options={'ANIMATABLE'}, update=group_driver_edge_updater)
    int_gobo_id: bpy.props.IntProperty(default=1, min=0, max=20, description="Gobo selection", options={'ANIMATABLE'}, update=group_driver_gobo_id_updater)
    float_gobo_speed: bpy.props.FloatProperty(default=0, min=-100, max=100, description="Rotation of individual gobo speed", options={'ANIMATABLE'}, update=group_driver_speed_updater)
    int_prism: bpy.props.IntProperty(default=0, min=0, max=1, description="Prism value. 1 is on, 0 is off", options={'ANIMATABLE'}, update=group_driver_prism_updater)
     
    # Checkers.   
    float_intensity_checker: bpy.props.FloatProperty(default=0, min=0, max=100, description="Intensity value", options={'ANIMATABLE'})
    float_pan_checker: bpy.props.FloatProperty(default=0,)
    float_tilt_checker: bpy.props.FloatProperty(default=0)
    float_vec_color_checker: bpy.props.FloatVectorProperty(name="", subtype='COLOR', size=3, default=(1.0, 1.0, 1.0))
    float_diffusion_checker: bpy.props.FloatProperty(default=0)
    float_strobe_checker: bpy.props.FloatProperty(default=0)
    float_zoom_checker: bpy.props.FloatProperty(default=0)
    float_iris_checker: bpy.props.FloatProperty(default=0)
    float_edge_checker: bpy.props.FloatProperty(default=0)
    gobo_id_checker: bpy.props.FloatProperty(default=0)
    float_speed_checker: bpy.props.FloatProperty(default=0)
    misc_effect_checker: bpy.props.FloatProperty(default=0)
    prism_checker: bpy.props.FloatProperty(default=0)
    
    # View toggles.
    pan_tilt_is_on: bpy.props.BoolProperty(default=False, description="Pan/Tilt is enabled when checked")
    color_is_on: bpy.props.BoolProperty(default=False, description="Color is enabled when checked")
    diffusion_is_on: bpy.props.BoolProperty(default=False, description="Diffusion is enabled when checked")
    strobe_is_on: bpy.props.BoolProperty(default=False, description="Strobe is enabled when checked")
    zoom_is_on: bpy.props.BoolProperty(default=False, description="Zoom is enabled when checked")
    iris_is_on: bpy.props.BoolProperty(default=False, description="Iris is enabled when checked")
    edge_is_on: bpy.props.BoolProperty(default=False, description="Edge is enabled when checked")
    gobo_id_is_on: bpy.props.BoolProperty(default=False, description="Gobo ID is enabled when checked")

    def init(self, context):
        self.outputs.new('FlashOutType', "Flash")
        self.outputs.new('GroupOutputType', "Driver Output")
        self.inputs.new('MasterInputType', "Master Input")
        self.inputs.new('MasterInputType', "Master Input")
        self.inputs.new('MasterInputType', "Master Input")

    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        op_home = row.operator("node.home_group", icon='HOME', text="Home")
        op_home.node_name = self.name
        op_update = row.operator("node.update_group", icon='FILE_REFRESH', text="Update")
        op_update.node_name = self.name
        if self.color_is_on:
            row.prop(self, "float_vec_color", text="")
        column = layout.column()
        row = column.row()
        row.prop(self, "float_intensity", slider=True, text="Intensity:")
        if self.strobe_is_on:
            row = column.row()
            row.prop(self, "float_strobe", slider=True, text="Strobe:")
        if self.pan_tilt_is_on:
            row = column.row()
            row.prop(self, "float_pan", slider=True, text="Pan:")
            row = column.row()
            row.prop(self, "float_tilt", slider=True, text="Tilt:")
        if self.zoom_is_on:
            row = column.row()
            row.prop(self, "float_zoom", slider=True, text="Zoom:")
        if self.iris_is_on:
            row = column.row()
            row.prop(self, "float_iris", slider=True, text="Iris:")
        if self.edge_is_on:
            row = column.row()
            row.prop(self, "float_edge", slider=True, text="Edge:")
        if self.diffusion_is_on:
            row = column.row()
            row.prop(self, "float_diffusion", slider=True, text="Diffusion:")
        if self.gobo_id_is_on:
            row = column.row()
            row.prop(self, "int_gobo_id", slider=True, text="Gobo:")
            row = column.row()
            row.prop(self, "float_gobo_speed", slider=True, text="Gobo Speed:")
            row = column.row()
            row.prop(self, "int_prism", slider=True, text="Prism:")
            column.separator()
        
        
class MasterNode(bpy.types.Node):
    bl_idname = 'master_type'
    bl_label = 'Master Node'
    bl_icon = 'DECORATE_DRIVER'
    bl_width_default = 200

    # Parameters
    float_intensity: bpy.props.FloatProperty(default=0, min=0, max=100, description="Intensity value", options={'ANIMATABLE'}, update=master_intensity_updater)
    float_vec_color: bpy.props.FloatVectorProperty(
        name="",
        subtype='COLOR',
        size=3,
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        description="Color value",
        update=master_color_updater
    )
    float_diffusion: bpy.props.FloatProperty(default=0, min=0, max=100, description="Diffusion value", options={'ANIMATABLE'}, update=master_diffusion_updater)
    float_diffusion_checker: bpy.props.FloatProperty(default=0, min=0, max=100, description="Diffusion value", options={'ANIMATABLE'})
    float_pan: bpy.props.FloatProperty(default=0, min=-315, max=315, description="Pan value", options={'ANIMATABLE'}, update=master_pan_updater)
    float_tilt: bpy.props.FloatProperty(default=0, min=-135, max=135, description="Tilt value", options={'ANIMATABLE'}, update=master_tilt_updater)
    float_strobe: bpy.props.FloatProperty(default=0, min=0, max=100, description="Strobe value", options={'ANIMATABLE'}, update=master_strobe_updater)
    float_zoom: bpy.props.FloatProperty(default=0, min=0, max=100, description="Zoom value", options={'ANIMATABLE'}, update=master_zoom_updater)
    float_iris: bpy.props.FloatProperty(default=0, min=0, max=100, description="Iris value", options={'ANIMATABLE'}, update=master_iris_updater)
    float_edge: bpy.props.FloatProperty(default=0, min=0, max=100, description="Edge value", options={'ANIMATABLE'}, update=master_edge_updater)
    int_gobo_id: bpy.props.IntProperty(default=1, min=0, max=20, description="Gobo selection", options={'ANIMATABLE'}, update=master_gobo_id_updater)
    float_gobo_speed: bpy.props.FloatProperty(default=0, min=-100, max=100, description="Rotation of individual gobo speed", options={'ANIMATABLE'}, update=master_speed_updater)
    int_prism: bpy.props.IntProperty(default=0, min=0, max=1, description="Prism value. 1 is on, 0 is off", options={'ANIMATABLE'}, update=master_prism_updater)
     
    # Checkers.   
    float_intensity_checker: bpy.props.FloatProperty(default=0, min=0, max=100, description="Intensity value", options={'ANIMATABLE'})
    float_pan_checker: bpy.props.FloatProperty(default=0,)
    float_tilt_checker: bpy.props.FloatProperty(default=0)
    float_vec_color_checker: bpy.props.FloatVectorProperty(name="", subtype='COLOR', size=3, default=(1.0, 1.0, 1.0))
    float_diffusion_checker: bpy.props.FloatProperty(default=0)
    float_strobe_checker: bpy.props.FloatProperty(default=0)
    float_zoom_checker: bpy.props.FloatProperty(default=0)
    float_iris_checker: bpy.props.FloatProperty(default=0)
    float_edge_checker: bpy.props.FloatProperty(default=0)
    gobo_id_checker: bpy.props.FloatProperty(default=0)
    float_speed_checker: bpy.props.FloatProperty(default=0)
    misc_effect_checker: bpy.props.FloatProperty(default=0)
    prism_checker: bpy.props.FloatProperty(default=0)
    
    # View toggles.
    pan_tilt_is_on: bpy.props.BoolProperty(default=False, description="Pan/Tilt is enabled when checked")
    color_is_on: bpy.props.BoolProperty(default=False, description="Color is enabled when checked")
    diffusion_is_on: bpy.props.BoolProperty(default=False, description="Diffusion is enabled when checked")
    strobe_is_on: bpy.props.BoolProperty(default=False, description="Strobe is enabled when checked")
    zoom_is_on: bpy.props.BoolProperty(default=False, description="Zoom is enabled when checked")
    iris_is_on: bpy.props.BoolProperty(default=False, description="Iris is enabled when checked")
    edge_is_on: bpy.props.BoolProperty(default=False, description="Edge is enabled when checked")
    gobo_id_is_on: bpy.props.BoolProperty(default=False, description="Gobo ID is enabled when checked")

    def init(self, context):
        self.outputs.new('MasterOutputType', "Master Output")

    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        op_home = row.operator("node.home_group", icon='HOME', text="Home")
        op_home.node_name = self.name
        op_update = row.operator("node.update_group", icon='FILE_REFRESH', text="Update")
        op_update.node_name = self.name
        if self.color_is_on:
            row.prop(self, "float_vec_color", text="")
        column = layout.column()
        row = column.row()
        row.prop(self, "float_intensity", slider=True, text="Intensity:")
        if self.strobe_is_on:
            row = column.row()
            row.prop(self, "float_strobe", slider=True, text="Strobe:")
        if self.pan_tilt_is_on:
            row = column.row()
            row.prop(self, "float_pan", slider=True, text="Pan:")
            row = column.row()
            row.prop(self, "float_tilt", slider=True, text="Tilt:")
        if self.zoom_is_on:
            row = column.row()
            row.prop(self, "float_zoom", slider=True, text="Zoom:")
        if self.iris_is_on:
            row = column.row()
            row.prop(self, "float_iris", slider=True, text="Iris:")
        if self.edge_is_on:
            row = column.row()
            row.prop(self, "float_edge", slider=True, text="Edge:")
        if self.diffusion_is_on:
            row = column.row()
            row.prop(self, "float_diffusion", slider=True, text="Diffusion:")
        if self.gobo_id_is_on:
            row = column.row()
            row.prop(self, "int_gobo_id", slider=True, text="Gobo:")
            row = column.row()
            row.prop(self, "float_gobo_speed", slider=True, text="Gobo Speed:")
            row = column.row()
            row.prop(self, "int_prism", slider=True, text="Prism:")
            column.separator()


classes = (
    GroupControllerNode,
    MixerNode,
    MixerInputSocket,
    MixerDriverNode,
    MixerOutputSocket,
    GroupDriverNode,
    MasterNode,
    MasterOutputSocket,
    MasterInputSocket,
    GroupInputSocket,
    GroupOutputSocket,
    FlashOutSocket,
    AlvaNodeTree
)

    
def register():
    
    ##################################################################################
    '''Registering the object props directly on object to preserve self-association'''
    ##################################################################################
        
    bpy.types.Object.relevant_channels_checker = bpy.props.StringProperty(default="")
    
    
    bpy.types.Object.str_enable_strobe_argument = bpy.props.StringProperty(
        default="# Strobe_Mode 127 Enter", description="Add # for group ID")
        
    bpy.types.Object.str_disable_strobe_argument = bpy.props.StringProperty(
        default="# Strobe_Mode 76 Enter", description="Add # for group ID")


    bpy.types.Object.str_enable_gobo_speed_argument = bpy.props.StringProperty(
        default="", description="Add # for group ID")
        
    bpy.types.Object.str_disable_gobo_speed_argument = bpy.props.StringProperty(
        default="", description="Add # for group ID")
        

    bpy.types.Object.str_gobo_id_argument = bpy.props.StringProperty(
        default="# Gobo_Select $ Enter", description="Add # for group ID and $ for value")


    bpy.types.Object.str_enable_prism_argument = bpy.props.StringProperty(
        default="# Beam_Fx_Select 02 Enter", description="Add # for group ID")
        
    bpy.types.Object.str_disable_prism_argument = bpy.props.StringProperty(
        default="# Beam_Fx_Select 01 Enter", description="Add # for group ID")






    #---------------------------------------------------------------------------------------
    '''OBECT FLOATS/INTS'''        
        
        
            
    bpy.types.Object.float_intensity_checker = bpy.props.FloatProperty(default=0)
    bpy.types.Object.float_vec_color_checker = bpy.props.FloatVectorProperty(default=(0, 0, 0))
    bpy.types.Object.float_pan_checker = bpy.props.FloatProperty(default=0)
    bpy.types.Object.float_tilt_checker = bpy.props.FloatProperty(default=0)
    bpy.types.Object.float_strobe_checker = bpy.props.FloatProperty(default=0)
    bpy.types.Object.float_zoom_checker = bpy.props.FloatProperty(default=0)
    bpy.types.Object.float_iris_checker = bpy.props.FloatProperty(default=0)
    bpy.types.Object.float_diffusion_checker = bpy.props.FloatProperty(default=0)
    bpy.types.Object.gobo_id_checker = bpy.props.FloatProperty(default=0)
    bpy.types.Object.float_speed_checker = bpy.props.FloatProperty(default=0)
    bpy.types.Object.float_edge_checker = bpy.props.FloatProperty(default=0)
    bpy.types.Object.misc_effect_checker = bpy.props.FloatProperty(default=0)
    bpy.types.Object.prism_checker = bpy.props.FloatProperty(default=0)
    bpy.types.Object.float_influence_checker = bpy.props.FloatProperty(
        default=1, description="")
    bpy.types.Object.color_profile_enum = EnumProperty(
        name="Color Profile",
        description="Choose a color profile for the group",
        items=color_profiles,
    )
    bpy.types.Object.float_intensity = bpy.props.FloatProperty(
        name="Intensity",
        default=0.0,
        min=0.0,
        max=100.0,
        description="Intensity value",
        options={'ANIMATABLE'},
        update=channel_intensity_updater
    )
    bpy.types.Object.float_vec_color = bpy.props.FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        size=3,
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        description="Color value",
        update=channel_color_updater
    )
    bpy.types.Object.float_vec_pan_tilt_graph = bpy.props.FloatVectorProperty(
        name="",
        subtype='COLOR',
        size=3,
        default=(.2, .2, .2),
        min=0.0,
        max=.2,
        update=pan_tilt_graph_updater
    )
    bpy.types.Object.pan_tilt_graph_checker = bpy.props.FloatVectorProperty(
        name="",
        subtype='COLOR',
        size=3,
        default=(.2, .2, .2),
        min=0.0,
        max=.2
    )
    bpy.types.Object.float_pan = bpy.props.FloatProperty(
        name="Pan",
        default=0.0,
        min=-270,
        max=270.0,
        description="Pan value",
        options={'ANIMATABLE'},
        update=channel_pan_updater
    )
    bpy.types.Object.float_tilt = bpy.props.FloatProperty(
        name="Tilt",
        default=0.0,
        min=-135.0,
        max=135.0,
        description="Tilt value",
        options={'ANIMATABLE'},
        update=channel_tilt_updater
    )
    bpy.types.Object.float_diffusion = bpy.props.FloatProperty(
        name="Diffusion",
        default=0.0,
        min=0,
        max=100.0,
        description="Diffusion value",
        options={'ANIMATABLE'},
        update=channel_diffusion_updater
    )
    bpy.types.Object.float_strobe = bpy.props.FloatProperty(
        name="Shutter Strobe",
        default=0.0,
        min=0.0,
        max=100.0,
        description="Shutter strobe value",
        options={'ANIMATABLE'},
        #update=channel_strobe_updater
    )
    bpy.types.Object.float_zoom = bpy.props.FloatProperty(
        name="Zoom",
        default=0.0,
        min=0.0,
        max=100.0,
        description="Zoom value",
        options={'ANIMATABLE'},
        update=channel_zoom_updater
    )
    bpy.types.Object.float_iris = bpy.props.FloatProperty(
        name="Iris",
        default=0.0,
        min=0.0,
        max=100.0,
        description="Iris value",
        options={'ANIMATABLE'},
        update=channel_iris_updater
    )
    bpy.types.Object.float_edge = bpy.props.FloatProperty(
        name="Edge",
        default=0.0,
        min=0.0,
        max=100.0,
        description="Edge value",
        options={'ANIMATABLE'},
        update=channel_edge_updater
    )
    bpy.types.Object.int_gobo_id = bpy.props.IntProperty(
        name="Gobo Selection",
        default=1,
        min=0,
        max=20,
        description="Gobo selection",
        options={'ANIMATABLE'},
        update=channel_gobo_id_updater
    )
    bpy.types.Object.float_gobo_speed = bpy.props.FloatProperty(
        name="Gobo Speed",
        default=0.0,
        min=-300.0,
        max=300.0,
        description="Rotation of individual gobo speed",
        options={'ANIMATABLE'},
        update=channel_speed_updater
    )
    bpy.types.Object.int_prism = bpy.props.IntProperty(
        name="Prism",
        default=0,
        min=0,
        max=1,
        description="Prism value. 1 is on, 0 is off",
        options={'ANIMATABLE'},
        update=channel_prism_updater
    )
    bpy.types.Object.int_misc_effect = bpy.props.IntProperty(
        name="Miscellaneous Effect",
        default=0,
        min=0,
        max=10,
        description="Miscellaneous effect value",
        options={'ANIMATABLE'}
    )
    
    




    #--------------------------------------------------------------------------------------------
    '''VARIOUS OBJECT TYPES'''
    
    
    
    bpy.types.Object.influence = bpy.props.IntProperty(
        default=1, description="How many votes this controller gets when there are conflicts", min=1, max=10)
        
    bpy.types.Object.int_intro = bpy.props.IntProperty(
        default=25, description="How many frames it takes for influencer to fully activate on a channel", min=0, max=500)
        
    bpy.types.Object.int_outro = bpy.props.IntProperty(
        default=25, description="How many frames it takes for influencer to fully deactivate off a channel", min=0, max=500)  
    
    
    bpy.types.Object.is_influencer = bpy.props.BoolProperty(
        default=False, description="")

    bpy.types.Object.pan_is_inverted = bpy.props.BoolProperty(default=True, description="Light is hung facing forward, for example, in FOH.")
    bpy.types.Object.last_hue = bpy.props.FloatProperty(default=0)
    bpy.types.Object.overdrive_mode = bpy.props.StringProperty(default="")
    bpy.types.Object.is_overdriven_left = bpy.props.BoolProperty(default=False)
    bpy.types.Object.is_overdriven_right = bpy.props.BoolProperty(default=False)
    bpy.types.Object.is_approaching_limit = bpy.props.BoolProperty(default=False)

    
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.app.handlers.depsgraph_update_pre.append(influencer_deps_updater)
    bpy.app.handlers.frame_change_pre.append(influencer_deps_updater)
    
    bpy.app.handlers.frame_change_pre.append(load_changes_handler)
    bpy.app.handlers.frame_change_post.append(publish_changes_handler)

    
def unregister():
    # Handlers
    if publish_changes_handler in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.remove(publish_changes_handler)
    if load_changes_handler in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.remove(load_changes_handler)
    if influencer_deps_updater in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.remove(influencer_deps_updater)
    if influencer_deps_updater in bpy.app.handlers.depsgraph_update_pre:
        bpy.app.handlers.depsgraph_update_pre.remove(influencer_deps_updater)

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
