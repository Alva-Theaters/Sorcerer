# This file is part of Alva ..
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
This script, spy, is a sort of API here to make it easier for casual users
to interact with Sorcerer functions programmatically. Inspired by Blender's 
bpy API. End users shall access this API from built-in text editor through:

import bpy
from bpy import spy

'''


import bpy

from .utils.osc import OSC
from .utils.utils import Utils
from .cpvia.find import Find
from .cpvia.mix import Mixer
from .cpvia.influencers import Influencers
from .assets.sli import SLI


class SorcererPython:
    class osc:
        def send_osc_lighting(address, argument):
            '''Use lighting console network patch'''
            OSC.send_osc_lighting(address, argument)

        def lighting_command(argument):
            '''Send a command line string to the console'''
            OSC.send_osc_lighting("/eos/newcmd", argument)

        def press_lighting_key(key):
            '''Press button down and up. Pass key name as string. This 
               involves a time.sleep of .1, which freezes UI'''
            OSC.press_lighting_key(key)

        def lighting_key_down(key):
            '''Just presses the button down, but does not hold release'''
            OSC.lighting_key_down(key)

        def lighting_key_up(key):
            '''Just releases the key'''
            OSC.lighting_key_up(key)

        def send_osc_video(address, argument):
            '''Use video switcher network patch'''
            OSC.send_osc_video(address, argument)
          
        def send_osc_audio(address, argument):
            '''Use audio mixer network patch'''
            OSC.send_osc_audio(address, argument)
            
        def send_osc_string(osc_addr, addr, port, string):
            '''Use custom network patch'''
            OSC.send_osc_string(osc_addr, addr, port, string)
        
    class utils:
        def get_frame_rate(scene):
            '''ALWAYS use this, NOT scene.render.fps. Must divide 
               render.fps by render.base and round for true fps, done 
               here'''
            return Utils.get_frame_rate(scene)
            
        def parse_channels(input_string):
            '''Convert user string to list of integers representing channel numbers'''
            return Utils.parse_channels(input_string)
            
        def parse_mixer_channels(input_string):
            '''Convert user string to list of tuples, the tuples containing integers 
               that represent channel numbers. Used to create concurrent offset groups
               in mixers'''
            return Utils.parse_mixer_channels(input_string)
            
        def get_light_rotation_degrees(light_name):
            '''Find true rotation after modifiers/constraints, Returns x_rotation_degrees,
               y_rotation_degreees. Pass to it the object name as string'''
            return Utils.get_light_rotation_degrees(light_name)
            
        def try_parse_int(value):
            '''Use this to avoid runtime errors converting to int. Returns int or none.
               This is just a try/except for int()'''
            return Utils.try_parse_int(value)
            
        def swap_preview_and_program(cue_list):
            '''Used for the ALVA M/E Switcher'''
            Utils.swap_preview_and_program(cue_list)
            
        def frame_to_timecode(frame, fps=None):
            '''Convert current frame to 00:00:00:00, in string'''
            return Utils.frame_to_timecode(frame, fps=None)
        
        def time_to_frame(time, frame_rate, start_frame):
            '''Convert time of song to frame, considering start frame of song strip'''
            return Utils.time_to_frame(time, frame_rate, start_frame)
        
        def add_color_strip(name, length, channel, color, strip_type, frame):
            Utils.add_color_strip(name, length, channel, color, strip_type, frame)
        
        def analyze_song(self, context, filepath):
            '''Use AI to analyze song for beats and sections'''
            return Utils.analyze_song(self, context, filepath)
            
        def find_available_channel(sequence_editor, start_frame, end_frame, start_channel=1):
            '''Use this to avoid adding strips on top of each other'''
            return Utils.find_available_channel(sequence_editor, start_frame, end_frame, start_channel=1)
        
        def duplicate_active_strip_to_selected(context):
            '''The function used by Copy Various to Selected and others'''
            Utils.duplicate_active_strip_to_selected(context)

        def find_relevant_clock_strip(scene):
            '''Find most relevant sound strip with a timecode clock assignment.
               Returns a bpy strip object'''
            return Utils.find_relevant_clock_strip(scene)
            
        def calculate_bias_offseter(bias, frame_rate, strip_length_in_frames):
            '''Used by Flash strip background logic to apply bias to flash down
               timing, Returns a float'''
            return Utils.calculate_bias_offseter(bias, frame_rate, strip_length_in_frames)

        def render_volume(speaker, empty, sensitivity, object_size, int_mixer_channel):
            '''Calculates volume for a 3d-audio-object and speaker pair'''
            Utils.render_volume(speaker, empty, sensitivity, object_size, int_mixer_channel)

        def color_object_to_tuple_and_scale_up(v):
            '''Formats Blender color objects for lighting console use. Returns 
               (r, g, b) tuple of ints scaled to 0-100 scale'''
            return Utils.color_object_to_tuple_and_scale_up(v)
        
        def update_alva_controller(controller):
            '''Logic for the Update button on the controllers. Pass controller
               as bpy object'''
            Utils.update_alva_controller(controller)
            
        def home_alva_controller(controller):
            '''Logic for the Home button on the controllers. Pass controller
               as bpy object'''
            Utils.home_alva_controller(controller)

    class find:
        def is_inside_mesh(obj, mesh_obj):
            '''Returns true if obj is inside mesh_obj. Doesn't work well
               for shapes much more complicated than cubes'''
            return Find.is_inside_mesh(obj, mesh_obj)
            
        def invert_color(self, value):
            '''Used for influencer calculations'''
            return Influencers.invert_color(self, value)
                
        def find_int(string):
            """Tries to find an integer inside the string and returns it 
               as an int. Returns 1 if no integer is found."""
            return Find.find_int(string)
            
        def mix_my_values(parent, param):
            '''Used by Alva's cpvia_generator for mixer nodes'''
            return Mixer.mix_my_values(parent, param)
            
        def split_color(parent, c, p, v, type):
            '''Used across Sorcerer for converting Blender's RGB space 
               to correct color space for the fixture'''
            return Mixer.split_color(parent, c, p, v, type)

        def find_my_patch(parent, chan, type, desired_property):
            '''This function finds the best patch for a given channel.'''
            return Find.find_my_patch(parent, chan, type, desired_property)
            
        def find_parent(self, object):
            '''Catches and corrects cases where the self is a collection 
            property instead of a node, sequencer strip, object, etc.'''
            return Find.find_parent(self, object)  
            
        def find_controllers(self, scene):
            '''Find strips, objects, and nodes in scene relevant to Sorcerer'''
            return Find.find_controllers(self, scene)
            
        def find_strips(self, scene):
            '''Find strips in scene relevant to Sorcerer'''
            return Find.find_strips(self, scene)
            
        def find_objects(self, scene):
            '''Find objects in scene relevant to Sorcerer'''
            return Find.find_objects(self, scene)
            
        def find_nodes(self, scene):
            '''Find nodes in scene relevant to Sorcerer'''
            return Find.find_nodes(self, scene)
    

bpy.spy = SorcererPython
