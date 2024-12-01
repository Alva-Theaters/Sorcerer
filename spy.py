# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

import time
from typing import Tuple, Union
import mathutils

from .cpv.find import Find
from .utils.osc import OSC
from .utils.event_utils import EventUtils
from .utils.spy_utils import _SorcererPython
from .updaters.properties import PropertiesUpdaters

from .utils.audio_utils import render_volume
from .utils.cpv_utils import color_object_to_tuple_and_scale_up, update_alva_controller, home_alva_controller
from .utils.rna_utils import parse_channels, parse_mixer_channels
from .utils.sequencer_utils import duplicate_active_strip_to_selected, find_available_channel, add_color_strip
from .utils.sequencer_utils import analyze_song, AnalysisResult

'''
This script, spy, is a sort of API here to make it easier for casual users
to interact with Sorcerer functions programmatically. Inspired by Blender's 
bpy API. End users shall access this API from built-in text editor through:

import bpy
from bpy import spy

'''


class SorcererPython(_SorcererPython):
    def make_eos_macros(macro_range: Tuple[int, int], int_range: Tuple[int, int], string: str):
        '''
        spy function for iterative macro generation on ETC Eos using custom ranges/strings.
   
        arguments:
            macro_range: Something like (1, 10) creates macros 1-10.
            int_range: Something like (50, 60) lets you make the macros say something like Go_to_Cue 50, 
                        51, 52...60 with those macros. Use * for this customizable integer in the string.
            string: This is what you want the macro to do. Instances of * in this string will be replaced 
                    with the current custom int. So you would make the string be something like 
                    "Go_to_Cue * Enter"

            returns: Nothing. This creates large quantities of macros on the ETC Eos console via OSC.

        Warning:
            Uses time.sleep, which freezes up Blender while running. Not currently equipped with press ESC to 
            cancel functionality. Terminate Blender via Operating System if you accidentally tell it to make 
            99,999 macros, which it will gladly do otherwise.
        '''
        SorcererPython.press_lighting_key("live")
        for macro, custom_int in zip(range(macro_range[0] - 1, macro_range[1]), range(int_range[0], int_range[1] + 1)):
            if macro > 100000:
                print("Error: Macro indexes on ETC Eos only go up to 99,999.")
                return

            SorcererPython.press_lighting_key("learn")
            SorcererPython.press_lighting_key("macro")
            time.sleep(.1)
            for digit in str(macro+1):
                SorcererPython.press_lighting_key(f"{digit}")
                time.sleep(.1)
            SorcererPython.press_lighting_key("enter")
            time.sleep(.1)

            formatted_string = string.replace("*", str(custom_int))
            SorcererPython.lighting_command(formatted_string)
            time.sleep(.1)
            SorcererPython.press_lighting_key("enter")
            SorcererPython.press_lighting_key("learn")
            time.sleep(.2)
            return
        

    #-----------------------------------------------------------------------------------------------------
    # The code below is just an interface between Text Editor and Sorcerer. This should not contain logic.

    # OSC
    def send_osc_lighting(address: str, argument: str) -> None:
        '''Use lighting console network patch'''
        OSC.send_osc_lighting(address, argument)

    def lighting_command(argument: str) -> None:
        '''Send a command line string to the console'''
        OSC.send_osc_lighting("/eos/newcmd", argument)

    def press_lighting_key(key: str) -> None:
        '''Press button down and up. Pass key name as string. This 
            involves a time.sleep of .1, which freezes UI'''
        OSC.press_lighting_key(key)

    def lighting_key_down(key: str) -> None:
        '''Just presses the button down, but does not hold release'''
        OSC.lighting_key_down(key)

    def lighting_key_up(key: str) -> None:
        '''Just releases the key'''
        OSC.lighting_key_up(key)

    def send_osc_video(address: str, argument: str) -> None:
        '''Use video switcher network patch'''
        OSC.send_osc_video(address, argument)
        
    def send_osc_audio(address: str, argument: str) -> None:
        '''Use audio mixer network patch'''
        OSC.send_osc_audio(address, argument)
        
    def send_osc_string(osc_address_to_send: str, network_address: str, network_port: int, string_to_send: str) -> None:
        '''Use custom network patch'''
        OSC.send_osc_string(osc_address_to_send, network_address, network_port, string_to_send)

        
    # General Utilities
    def get_frame_rate(scene: bpy.types.Scene) -> float:
        '''ALWAYS use this, NOT scene.render.fps. Must divide 
        render.fps by render.base and round for true fps, done 
        here'''
        return EventUtils.get_frame_rate(scene)
        
    def parse_channels(input_string: str) -> list[int]:
        '''Convert user string to list of integers representing channel numbers'''
        return parse_channels(input_string)
        
    def parse_mixer_channels(input_string: str) -> Tuple[list[int], list[int]]:
        '''Used to create concurrent offset groups in mixers'''
        return parse_mixer_channels(input_string)
        
    def swap_preview_and_program(cue_list: int) -> None:
        '''Used for the Live Cue Switcher'''
        PropertiesUpdaters.swap_preview_and_program(cue_list)
        
    def frame_to_timecode(frame: float, fps: int = None) -> str:
        '''Convert current frame to 00:00:00:00, in string'''
        return EventUtils.frame_to_timecode(frame, fps)
    
    def time_to_frame(time: float, frame_rate: float, start_frame: float) -> float:
        '''Convert time of song to frame, considering start frame of song strip'''
        return EventUtils.time_to_frame(time, frame_rate, start_frame)
    
    def add_color_strip(name: str, length: int, channel: int, color: tuple, strip_type: str, frame: float):
        '''Adds a color strip to sequencer.'''
        add_color_strip(name, length, channel, color, strip_type, frame)
    
    def analyze_song(self, context, filepath: str) -> AnalysisResult:
        '''Use AI to analyze song for beats and sections. Returns a data class.'''
        return analyze_song(self, context, filepath)
        
    def find_available_channel(sequence_editor, start_frame: float, end_frame: float, start_channel=1) -> int:
        '''Use this to avoid adding strips on top of each other.'''
        return find_available_channel(sequence_editor, start_frame, end_frame, start_channel)
    
    def duplicate_active_strip_to_selected(context) -> None:
        '''The function used by Copy Various to Selected and others.'''
        duplicate_active_strip_to_selected(context)

    def find_relevant_clock_objects(scene: bpy.types.Scene) -> bpy.types.Sequence:
        '''Find most relevant sound strip with a timecode clock assignment.
            Returns 2 bpy strip objects, the first may be scene'''
        return EventUtils.find_relevant_clock_objects(scene)

    def render_volume(speaker: bpy.types.Speaker, empty: bpy.types.Object, sensitivity: float, object_size: float, int_mixer_channel: int) -> float:
        '''Calculates volume for a 3d-audio-object and speaker pair'''
        render_volume(speaker, empty, sensitivity, object_size, int_mixer_channel)

    def color_object_to_tuple_and_scale_up(color_object: mathutils.Color) -> tuple:
        '''Formats Blender color objects for lighting console use. Returns 
            (r, g, b) tuple of ints scaled to 0-100 scale'''
        return color_object_to_tuple_and_scale_up(color_object)
    
    def update_alva_controller(controller: Union[bpy.types.Object, bpy.types.Node, bpy.types.Sequence]) -> None:
        '''Logic for the Update button on the controllers. Pass controller as bpy object'''
        update_alva_controller(controller)
        
    def home_alva_controller(controller: Union[bpy.types.Object, bpy.types.Node, bpy.types.Sequence]) -> None:
        '''Logic for the Home button on the controllers. Pass controller as bpy object'''
        home_alva_controller(controller)


    # Finders
    def find_controllers(scene: bpy.types.Scene) -> Tuple[list, list]:
        '''Find strips, objects, and nodes in scene relevant to Sorcerer.
        Also returns separate list of just the mixers and motors in the
        scene.'''
        return Find.find_controllers(scene)
        
    def find_strips(scene: bpy.types.Scene) -> list[bpy.types.Sequence]:
        '''Find strips in scene relevant to Sorcerer'''
        return Find.find_strips(scene)
        
    def find_objects(scene: bpy.types.Scene) -> list[bpy.types.Object]:
        '''Find objects in scene relevant to Sorcerer'''
        return Find.find_objects(scene)
        
    def find_nodes(scene: bpy.types.Scene) -> list[bpy.types.Node]:
        '''Find nodes in scene relevant to Sorcerer'''
        return Find.find_nodes(scene)


# Allow direct, easy access from text editor.
bpy.spy = SorcererPython