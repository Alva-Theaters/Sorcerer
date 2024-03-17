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
import bpy_extras
import socket
import blf
import threading
import time
import re
import json
import math
from functools import partial
from bpy.types import PropertyGroup
from bpy.props import StringProperty
from _bpy import context as _context


max_zoom = 1000
min_zoom = -1000
max_iris = 1000
min_iris = -1000


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


def osc_zoom_update(self, context):
    scene = context.scene
    if context.screen:
        
        if not context.scene.is_armed_osc:
            return
        
        if not hasattr(self, "my_settings") or self.my_settings.motif_type_enum != 'option_animation':
            return
        
        if self.mute:
            return
        
        if scene.frame_current > self.frame_final_end:
            return
        
        if scene.frame_current < self.frame_start:
            return
        
        zoom_prefix = self.zoom_prefix
        osc_zoom = self.osc_zoom
        ip_address = context.scene.scene_props.str_osc_ip_address
        port = context.scene.scene_props.int_osc_port
        
        osc_zoom_str = str(osc_zoom)
        send_osc_string(zoom_prefix, ip_address, port, osc_zoom_str)
        
        
def osc_iris_update(self, context):
    scene = context.scene
    if context.screen:
        
        if not context.scene.is_armed_osc:
            return
        
        if not hasattr(self, "my_settings") or self.my_settings.motif_type_enum != 'option_animation':
            return
        
        if self.mute:
            return
        
        if scene.frame_current > self.frame_final_end:
            return
        
        if scene.frame_current < self.frame_start:
            return
        
        iris_prefix = self.iris_prefix
        osc_iris = self.osc_iris
        ip_address = context.scene.scene_props.str_osc_ip_address
        port = context.scene.scene_props.int_osc_port
        
        osc_iris_str = str(osc_iris)
        send_osc_string(iris_prefix, ip_address, port, osc_iris_str)
        
        
def start_macro_update(self, context):
    active_strip = context.scene.sequence_editor.active_strip
    ip_address = context.scene.scene_props.str_osc_ip_address
    port = context.scene.scene_props.int_osc_port
    
    self.start_frame_macro_text = self.start_frame_macro_text_gui
    
    frame_rate = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base
    strip_length_in_seconds_total = active_strip.frame_final_duration / frame_rate
    
    # Convert total seconds to minutes and fractional seconds format.
    minutes = int(strip_length_in_seconds_total // 60)
    seconds = strip_length_in_seconds_total % 60
    duration = "{:02d}:{:04.1f}".format(minutes, seconds)  
    
    formatted_command = update_macro_command(self.start_frame_macro_text, duration)
    self.start_frame_macro_text = formatted_command

  
def end_macro_update(self, context):
    active_strip = context.scene.sequence_editor.active_strip
    ip_address = context.scene.scene_props.str_osc_ip_address
    port = context.scene.scene_props.int_osc_port
    
    self.end_frame_macro_text = self.end_frame_macro_text_gui
    
    frame_rate = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base
    strip_length_in_seconds_total = active_strip.frame_final_duration / frame_rate
    
    # Convert total seconds to minutes and fractional seconds format.
    minutes = int(strip_length_in_seconds_total // 60)
    seconds = strip_length_in_seconds_total % 60
    duration = "{:02d}:{:04.1f}".format(minutes, seconds)  
    
    formatted_command = update_macro_command(self.end_frame_macro_text, duration)
    self.end_frame_macro_text = formatted_command
    
    
def update_macro_command(command, duration):
    if '*' in command:
        command = command.replace('*', 'Sneak Time ' + str(duration))

    commands_to_replace = [
        'go to cue',
        'stop effect',
        'go to cue 0',
        'intensity palette',
        'color palette',
        'focus palette',
        'beam palette'
    ]

    for cmd in commands_to_replace:
        if cmd in command:
            command = command.replace(cmd, cmd.replace(' ', '_'))

    if not command.strip().endswith('Enter'):
        command += ' Enter'

    return command 


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


def get_frame_rate(scene):
    fps = scene.render.fps
    fps_base = scene.render.fps_base
    frame_rate = fps / fps_base
    return frame_rate


filter_color_strips = partial(filter, bpy.types.ColorSequence.__instancecheck__)


def parse_builder_groups(input_text):
    # This function takes a string input that contains numbers separated by commas, spaces, or dashes
    # and returns a list of numbers. For range inputs like "1-3", it will return [1, 2, 3].
    
    # Split the input by commas and spaces to handle all types of input.
    parts = input_text.replace(',', ' ').split()
    result = []

    for part in parts:
        # Check if we have a range (indicated by a dash).
        if '-' in part:
            # Split the range into start and end, then generate the numbers in between.
            start, end = map(int, part.split('-'))
            result.extend(range(start, end + 1))
        else:
            # It's a single number, so add it to the result.
            result.append(int(part))

    return result


def replacement_value_updater(self, context):
    ''' This needs to 1: clear all prefix fields. 2: press the "my.load_preset()" button. 3: press the "my.replace_button()", and finally, 4: update the strip name to reflect self. '''   
    
    if bpy.context.scene.auto_update_replacement:
        active_strip = context.scene.sequence_editor.active_strip  
    
        active_strip.intensity_prefix =  ""
        active_strip.red_prefix =  ""
        active_strip.green_prefix =  ""
        active_strip.blue_prefix =  ""
        active_strip.pan_prefix =  ""
        active_strip.tilt_prefix =  ""
        active_strip.zoom_prefix =  ""
        active_strip.iris_prefix =  ""
        
        bpy.ops.my.load_preset()
        bpy.ops.my.replace_button()
        
        active_strip.name = self.replacement_value


class EnableAnimationOperator(bpy.types.Operator):
    bl_idname = "my.enable_animation"
    bl_label = "Enable Animation"
    bl_description = "This adds Animation to the Motif Type options. Animation lets you use keyframes to control paramters, which are like inverted cues. They change behavior before, not behavior after. They are snapshots in time, not requests to start going to a look"
    
    def execute(self, context):
        if bpy.context.scene.i_understand_animation == "I understand that ETC Eos cannot store this data locally and it is not safe to use this bonus feature during a real show on Eos.":
            context.scene.animation_enabled = True
            self.report({'INFO'}, "Animation enabled.")
        else:
            self.report({'ERROR'}, "Try again.")
        return {'FINISHED'}    
    

class EnableTriggersOperator(bpy.types.Operator):
    bl_idname = "my.enable_triggers"
    bl_label = "Enable Triggers"
    bl_description = "This adds Triggers to the Motif Type options. Triggers is useful if you are using a console other than ETC Eos or if you want to do offset effects"

    def execute(self, context):
        if bpy.context.scene.i_understand_triggers == "I understand this bonus feature is unrecordable for Eos. ETC Eos cannot store these locally. I should not use this during a real show with Eos.":
            context.scene.triggers_enabled = True
            self.report({'INFO'}, "Triggers enabled.")
        else:
            self.report({'ERROR'}, "Try again.")
        return {'FINISHED'}  
    

class SelectSimilarOperator(bpy.types.Operator):
    bl_idname = "my.select_similar"
    bl_label = "Select Similar"
    bl_description = "This selects all strips with the same length and color as the active strip"

    @classmethod
    def poll(cls, context):
            return context.scene.sequence_editor and context.scene.sequence_editor.active_strip

    def execute(self, context):
        sequencer = context.scene.sequence_editor
        active_strip = sequencer.active_strip
        strip_type = active_strip.my_settings.motif_type_enum
        scene = bpy.context.scene

        active_strip_color = active_strip.color
        active_strip_strip_name = active_strip.name
        active_strip_channel = active_strip.channel
        active_strip_duration = active_strip.frame_final_duration
        active_strip_frame_start = active_strip.frame_start
        active_strip_frame_end = active_strip.frame_final_end
        
        def is_color_similar(color1, color2, tolerance=0.0001):
            return all(abs(c1 - c2) < tolerance for c1, c2 in zip(color1, color2))

        if scene.is_filtering_left == True:
            
            for strip in sequencer.sequences_all:
                if strip.type == 'COLOR':
                    if scene.color_is_magnetic and hasattr(strip, 'color'):
                        if strip.color == active_strip_color:
                            strip.select = True
                        else:
                            strip.select = False
                    
                if scene.strip_name_is_magnetic:
                    if strip.name == active_strip_strip_name:
                        strip.select = True
                    else:
                        strip.select = False
                    
                if scene.channel_is_magnetic:
                    if strip.channel == active_strip_channel:
                        strip.select = True
                    else:
                        strip.select = False
                        
                if scene.duration_is_magnetic:
                    if strip.frame_final_duration == active_strip_duration:
                        strip.select = True
                    else:
                        strip.select = False
                    
                if scene.start_frame_is_magnetic:
                    if strip.frame_start == active_strip_frame_start:
                        strip.select = True
                    else:
                        strip.select = False
                    
                if scene.end_frame_is_magnetic:
                    if strip.frame_final_end == active_strip_frame_end:
                        strip.select = True
                    else:
                        strip.select = False
                                                
        if scene.is_filtering_left == False:
                            
                for strip in sequencer.sequences_all:
                    if scene.color_is_magnetic:
                        if strip.type == 'COLOR':
                            if strip.color == active_strip_color:
                                strip.select = True
                        
                    if scene.strip_name_is_magnetic:
                        if strip.name == active_strip_strip_name:
                            strip.select = True
                        
                    if scene.channel_is_magnetic:
                        if strip.channel == active_strip_channel:
                            strip.select = True
                            
                    if scene.duration_is_magnetic:
                        if strip.frame_final_duration == active_strip_duration:
                            strip.select = True
                        
                    if scene.start_frame_is_magnetic:
                        if strip.frame_start == active_strip_frame_start:
                            strip.select = True
                        
                    if scene.end_frame_is_magnetic:
                        if strip.frame_final_end == active_strip_frame_end:
                            strip.select = True
                            
                for strip in sequencer.sequences_all:           
                    if scene.color_is_magnetic:
                        if strip.type == 'COLOR':
                            if strip.color != active_strip_color:
                                strip.select = False
                        
                    if scene.strip_name_is_magnetic:
                        if strip.name != active_strip_strip_name:
                            strip.select = False
                        
                    if scene.channel_is_magnetic:
                        if strip.channel != active_strip_channel:
                            strip.select = False
                            
                    if scene.duration_is_magnetic:
                        if strip.frame_final_duration != active_strip_duration:
                            strip.select = False
                        
                    if scene.start_frame_is_magnetic:
                        if strip.frame_start != active_strip_frame_start:
                            strip.select = False
                        
                    if scene.end_frame_is_magnetic:
                        if strip.frame_final_end != active_strip_frame_end:
                            strip.select = False

        return {'FINISHED'}


class BumpLeftFiveOperator(bpy.types.Operator):
    bl_idname = "my.bump_left_five"
    bl_label = "5"
    bl_description = "They're too late. This bumps selected strips backward by 5 frames. You can also do this by holding Shift and pressing L for left. Pressing L without Shift bumps the strip(s) back by just 1 frame. Hold it down continuously to go fast"
        
    def execute(self, context):
        for strip in context.selected_sequences:
            strip.frame_start -= 5
        return {'FINISHED'}
    

class BumpLeftOneOperator(bpy.types.Operator):
    bl_idname = "my.bump_left_one"
    bl_label = "1"
    bl_description = "They're a smidge late. This bumps selected strips backward by 1 frame. You can also do this by pressing L for left. Pressing L with Shift down bumps the strip(s) back by 5 frames"
    
    def execute(self, context):
        for strip in context.selected_sequences:
            strip.frame_start -= 1
        return {'FINISHED'}
    

class BumpUpOperator(bpy.types.Operator):
    bl_idname = "my.bump_up"
    bl_label = ""
    bl_description = "This bumps selected strips up 1 channel. Pressing 1-9 selects channels 1-9, pressing 0 selects channel 10, and holding shift down gets you to channel 20. Also, press U to bump up and Shift + U to bump down."
    
    def execute(self, context):
        for strip in context.selected_sequences:
            strip.channel += 1
        return {'FINISHED'}
    

class MuteOperator(bpy.types.Operator):
    bl_idname = "my.mute_button"
    bl_label = ""   
    bl_description = "This mutes the selected strip(s). Muted strips will not contribute to OSC messaging to the console. You can also do this with H to mute and Alt-H to unmute, or command + H to unmute on Mac"
    
    def execute(self, context):
        selected_strips = [strip for strip in context.scene.sequence_editor.sequences if strip.select]
        for strip in selected_strips:
            if strip.mute == True:
                strip.mute = False 
            else:
                strip.mute = True
        return {'FINISHED'}
   
    
class BumpDownOperator(bpy.types.Operator):
    bl_idname = "my.bump_down"
    bl_label = ""
    bl_description = "This bumps selected strips down 1 channel. Pressing 1-9 selects channels 1-9, pressing 0 selects channel 10, and holding shift down gets you to channel 20. Also, press U to bump up and Shift + U to bump down."
    
    def execute(self, context):
        for strip in context.selected_sequences:
            strip.channel -= 1
        return {'FINISHED'}
    

class BumpRightOneOperator(bpy.types.Operator):
    bl_idname = "my.bump_right_one"
    bl_label = "1"
    bl_description = "They're a smidge early. This bumps selected strips forward by 1 frame. You can also do this by pressing R for right. Pressing R with Shift down bumps the strip(s) forwward by 5 frames"
    
    def execute(self, context):
        for strip in context.selected_sequences:
            strip.frame_start += 1
        return {'FINISHED'}


class BumpRightFiveOperator(bpy.types.Operator):
    bl_idname = "my.bump_right_five"
    bl_label = "5"
    bl_description = "They're too early. This bumps selected strips forward by 5 frames. You can also do this by holding Shift and pressing R for right. Pressing R without Shift bumps the strip(s) forward by just 1 frame. Hold it down continuously to go fast"
    
    def execute(self, context):
        for strip in context.selected_sequences:
            strip.frame_start += 5
        return {'FINISHED'}
    

class BumpTCLeftFiveOperator(bpy.types.Operator):
    bl_idname = "my.bump_tc_left_five"
    bl_label = "5"
    bl_description = "They're too late. Bump console's event list events back 5 frames. The event list this is applied to is determined by the Event List field above. This only works for ETC Eos"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        ip_address = context.scene.scene_props.str_osc_ip_address
        port = context.scene.scene_props.int_osc_port
        event_list = active_strip.song_timecode_clock_number
        address = "/eos/newcmd"
        argument = "Event " + str(event_list) + " / 1 Thru 1000000 Time - 5 Enter"
        send_osc_string(address, ip_address, port, argument)
        return {'FINISHED'}    
    

class BumpTCLeftOneOperator(bpy.types.Operator):
    bl_idname = "my.bump_tc_left_one"
    bl_label = "1"
    bl_description = "They're a smidge late. Bump console's event list events back 1 frame. The event list this is applied to is determined by the Event List field above. This only works for ETC Eos"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        ip_address = context.scene.scene_props.str_osc_ip_address
        port = context.scene.scene_props.int_osc_port
        event_list = active_strip.song_timecode_clock_number
        address = "/eos/newcmd"
        argument = "Event " + str(event_list) + " / 1 Thru 1000000 Time - 1 Enter"
        send_osc_string(address, ip_address, port, argument)
        return {'FINISHED'}


class BumpTCRightOneOperator(bpy.types.Operator):
    bl_idname = "my.bump_tc_right_one"
    bl_label = "1"
    bl_description = "They're a smidge early. Bump console's event list events forward 1 frame. The event list this is applied to is determined by the Event List field above. This only works for ETC Eos"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        ip_address = context.scene.scene_props.str_osc_ip_address
        port = context.scene.scene_props.int_osc_port
        event_list = active_strip.song_timecode_clock_number        
        address = "/eos/newcmd"
        argument = "Event " + str(event_list) + " / 1 Thru 1000000 Time + 1 Enter"        
        send_osc_string(address, ip_address, port, argument)
        return {'FINISHED'}


class BumpTCRightFiveOperator(bpy.types.Operator):
    bl_idname = "my.bump_tc_right_five"
    bl_label = "5"
    bl_description = "They're too early. Bump console's event list events forward 5 frames. The event list this is applied to is determined by the Event List field above. This only works for ETC Eos"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        ip_address = context.scene.scene_props.str_osc_ip_address
        port = context.scene.scene_props.int_osc_port
        event_list = active_strip.song_timecode_clock_number
        address = "/eos/newcmd"
        argument = "Event " + str(event_list) + " / 1 Thru 1000000 Time + 5 Enter"
        send_osc_string(address, ip_address, port, argument)
        return {'FINISHED'}
    
    
class SelectChannelOperator(bpy.types.Operator):
    bl_idname = "my.select_channel"
    bl_label = "Select Channel"
    bl_description = "Select all strips on channel above. Pressing 1-9 selects channels 1-9, pressing 0 selects channel 10, and holding shift gets you to channel 20. Press D to deselect all and A to toggle selection of all. B for box select"
    
    def execute(self, context):
        relevant_channel = context.scene.channel_selector
        earliest_strip = None
        for strip in bpy.context.scene.sequence_editor.sequences_all:
            if strip.channel == relevant_channel:
                strip.select = True
                if not earliest_strip or strip.frame_start < earliest_strip.frame_start:
                    earliest_strip = strip
        if earliest_strip:
            context.scene.sequence_editor.active_strip = earliest_strip
        return {'FINISHED'}


class StartMacroSearchOperator(bpy.types.Operator):
    bl_idname = "my.start_macro_search"
    bl_label = ""
    bl_description = "Use this to find the lowest unused macro number according to the sequencer. Caution: this does not yet poll the console to make sure it won't overwrite a macro that exists on the board itself"
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = context.scene.sequence_editor.active_strip
        selected_macro = 1
        
        for strip in sequence_editor.sequences_all:
            if hasattr(strip, 'start_frame_macro'):
                if strip.start_frame_macro:  
                    if strip.start_frame_macro >= selected_macro:
                        selected_macro += 1
                               
        for strip in sequence_editor.sequences_all:
            if hasattr(strip, 'end_frame_macro'):
                if strip.end_frame_macro:  
                    if strip.end_frame_macro >= selected_macro:
                        selected_macro += 1
                    
        active_strip.start_frame_macro = selected_macro
        return {'FINISHED'} 
    

class EndMacroSearchOperator(bpy.types.Operator):
    bl_idname = "my.end_macro_search"
    bl_label = ""
    bl_description = "Use this to find the lowest unused macro number according to the sequencer. Caution: this does not yet poll the console to make sure it won't overwrite a macro that exists on the board itself"
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = context.scene.sequence_editor.active_strip
        
        selected_macro = 1
        
        for strip in sequence_editor.sequences_all:
            if hasattr(strip, 'start_frame_macro'):
                if strip.start_frame_macro:  
                    if strip.start_frame_macro >= selected_macro:
                        selected_macro += 1
                    
        for strip in sequence_editor.sequences_all:
            if hasattr(strip, 'end_frame_macro'):
                if strip.end_frame_macro:  
                    if strip.end_frame_macro >= selected_macro:
                        selected_macro += 1
                    
        active_strip.end_frame_macro = selected_macro
        return {'FINISHED'} 


class FlashMacroSearchOperator(bpy.types.Operator):
    bl_idname = "my.flash_macro_search"
    bl_label = ""
    bl_description = "Find the lowest unused macro number in the sequencer."

    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = sequence_editor.active_strip

        used_macros = set()
        macro_attributes = ['start_frame_macro', 'end_frame_macro', 'start_flash_macro_number', 'end_flash_macro_number']
        for strip in sequence_editor.sequences_all:
            for attr in macro_attributes:
                macro_number = getattr(strip, attr, None)
                if macro_number:
                    used_macros.add(macro_number)

        selected_macro = 1
        while selected_macro in used_macros:
            selected_macro += 1

        active_strip.start_flash_macro_number = selected_macro
        selected_macro += 1
        while selected_macro in used_macros:  
            selected_macro += 1
        active_strip.end_flash_macro_number = selected_macro
        return {'FINISHED'}


class StartMacroOperator(bpy.types.Operator):
    bl_idname = "my.start_macro_fire"
    bl_label = ""
    bl_description = "Send a test command"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        ip_address = context.scene.scene_props.str_osc_ip_address
        port = context.scene.scene_props.int_osc_port
        address = "/eos/macro/fire"
        argument = str(active_strip.start_frame_macro)
        send_osc_string(address, ip_address, port, argument)
        return {'FINISHED'} 
    
    
class EndMacroOperator(bpy.types.Operator):
    bl_idname = "my.end_macro_fire"
    bl_label = ""
    bl_description = "Send a test command"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        ip_address = context.scene.scene_props.str_osc_ip_address
        port = context.scene.scene_props.int_osc_port
        address = "/eos/macro/fire"
        argument = str(active_strip.end_frame_macro)
        send_osc_string(address, ip_address, port, argument)
        return {'FINISHED'}


class AddOffsetOperator(bpy.types.Operator):
    bl_idname = "my.add_offset"
    bl_label = "Offset"
    bl_description = "Offset selected strips by the BPM to the left"
        
    def execute(self, context):
        offset_value = context.scene.offset_value
        sequence_editor = context.scene.sequence_editor
        active_strip = context.scene.sequence_editor.active_strip
        channel = active_strip.channel

        if sequence_editor:
            selected_strips = sorted([strip for strip in sequence_editor.sequences if strip.select], key=lambda s: s.frame_start)
            frame_rate = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base
            offset_value_converted = frame_rate * (60 / offset_value)  # Convert BPM to frames
            initial_offset = selected_strips[0].frame_start if selected_strips else 0
            cumulative_offset = 0

            for strip in selected_strips:
                strip.frame_start = initial_offset + cumulative_offset
                #strip.channel = find_available_channel(sequence_editor, strip.frame_start, strip.frame_final_end)
                strip.channel = channel
                cumulative_offset += offset_value_converted

        return {'FINISHED'}


class StartEndFrameMappingOperator(bpy.types.Operator):
    bl_idname = "my.start_end_frame_mapping"
    bl_label = "Set Range"
    bl_description = "Make sequencer's start and end frame match the selected clip's start and end frame"
        
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        context.scene.frame_start = int(active_strip.frame_start)
        context.scene.frame_end = int(active_strip.frame_final_duration + active_strip.frame_start)
        bpy.ops.sequencer.view_selected()
        return {'FINISHED'}
    

class MapTimeOperator(bpy.types.Operator):
    bl_idname = "my.time_map"
    bl_label = "Set Timecode"
    bl_description = "Drag all strips uniformly so that active strip's start frame is on frame 1 of the sequencer. Commonly used to synchronize with the console's timecode"
        
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip

        if active_strip is None:
            self.report({'ERROR'}, "No active strip selected.")
            return {'CANCELLED'}

        offset = 1 - active_strip.frame_start
        sorted_strips = sorted(context.scene.sequence_editor.sequences_all, key=lambda s: s.frame_start)

        for strip in sorted_strips:
            if not strip.type == 'SPEED':
                strip.frame_start += offset

        return {'FINISHED'}


# List of colors to cycle through.
color_codes = [
    (1, 0, 0),  # Red
    (0, 1, 0),  # Green
    (0, 0, 1),  # Blue
    (1, 1, 0),  # Yellow
    (1, 0, 1),  # Magenta
    (0, 1, 1),  # Cyan
    (1, 1, 1),  # White
    (1, 0, 0),  # Dark red
    (0, .5, 0),  # Dark Green
    (0, 0, .5),  # Dark Blue
    (.5, .5, 0),  # Dark Yellow
    (.5, 0, .5),  # Dark Magenta
    (0, .5, .5),  # Dark Cyan
    (.5, .5, .5),  # Grey
    (1, .5, .5),  # Light red
    (.5, 1, .5),  # Light green
]


class GenerateStripsOperator(bpy.types.Operator):
    bl_idname = "my.generate_strips"
    bl_label = "Generate Strips On-Beat"
    bl_description = "Generate color-coded strips on each beat as specified above"
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = sequence_editor.active_strip

        try:
            song_bpm_input = active_strip.song_bpm_input
            song_bpm_channel = active_strip.song_bpm_channel
            beats_per_measure = active_strip.beats_per_measure
            
        except AttributeError:
            self.report({'ERROR'}, "BPM input, channel, or beats per measure property not found on the active strip!")
            return {'CANCELLED'}

        if song_bpm_input <= 0:
            self.report({'ERROR'}, "Invalid BPM!")
            return {'CANCELLED'}

        frames_per_second = context.scene.render.fps_base * context.scene.render.fps
        frame_start = active_strip.frame_start
        frame_end = active_strip.frame_final_end
        frames_per_beat = round((60 / song_bpm_input) * frames_per_second)

        beat_count = 0
        for frame in range(int(frame_start), int(frame_end), frames_per_beat):

            color_strip = sequence_editor.sequences.new_effect(
                name="Color Strip",
                type='COLOR',
                channel=song_bpm_channel,
                frame_start=frame,
                frame_end=frame + frames_per_beat - 1)  # Subtracting 1 to avoid overlap

            # Assign color based on the beat count
            color_strip.color = color_codes[beat_count % len(color_codes)]
            
            # Increment the beat count and reset if it reaches beats per measure
            beat_count = (beat_count + 1) % beats_per_measure

        return {'FINISHED'}


class AddColorStripOperator(bpy.types.Operator):
    bl_idname = "my.add_color_strip"
    bl_label = "Add Strip(s)"
    bl_description = "Generate 1 or more color strips. If multiple, offset them by frames with the Offset by field. Also, press O as in Oscar to add strips even during playback. Go to Settings to enable adding a second strip upon release for kick/snare"
    
    def execute(self, context):
        scene = context.scene
        start_frame = scene.frame_current
        channel = scene.channel_selector
        color = (1, 1, 1)  # Default color is white. Change values for different colors (R, G, B, A)
        offset = 0

        if not scene.sequence_editor:
            scene.sequence_editor_create()

        if scene.generate_quantity == 1:
            bpy.ops.sequencer.effect_strip_add(
                frame_start=start_frame,
                frame_end=start_frame + offset + scene.normal_offset,
                channel=channel,
                type='COLOR',
                color=color
            )
        else:
            for i in range(scene.generate_quantity):
                offset = i * scene.normal_offset
                bpy.ops.sequencer.effect_strip_add(
                    frame_start=start_frame + offset,
                    frame_end=start_frame + offset + scene.normal_offset,
                    channel=channel,
                    type='COLOR',
                    color=color
                )

        return {'FINISHED'}
    

class ClockZeroOperator(bpy.types.Operator):
    bl_idname = "my.clock_zero"
    bl_label = ""
    bl_description = "Set timecode clock to zero"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        ip_address = context.scene.scene_props.str_osc_ip_address
        port = context.scene.scene_props.int_osc_port
        event_list_number = str(active_strip.song_timecode_clock_number)
        address = "/eos/newcmd"
        argument = "Event " + event_list_number + " / Internal Disable Time Enter"
        send_osc_string(address, ip_address, port, argument)
        return {'FINISHED'}
    
    
class ClearTimecodeClockOperator(bpy.types.Operator):
    bl_idname = "my.clear_timecode_clock"
    bl_label = ""
    bl_description = "Deletes all timecode events in the event list associated with the timecode clock. Command must be manually confirmed on the console"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip

        if active_strip and active_strip.type == 'SOUND':
            ip_address = context.scene.scene_props.str_osc_ip_address
            port = context.scene.scene_props.int_osc_port
            
            tab_address = "/eos/key/tab"
            one_address = "/eos/key/1"
            cmd_address = "/eos/newcmd"
            
            enter_argument = "Enter"
            funky_enter_argument = "11 Enter"
            
            event_list_number = active_strip.song_timecode_clock_number
            final_argument = "Delete Event " + str(event_list_number) + " / 1 thru 9999 Enter"
        
            send_osc_string(tab_address, ip_address, port, funky_enter_argument)
            send_osc_string(one_address, ip_address, port, enter_argument)
            send_osc_string(one_address, ip_address, port, enter_argument)
            send_osc_string(tab_address, ip_address, port, enter_argument)
            time.sleep(.1)
            send_osc_string(cmd_address, ip_address, port, final_argument)
            
        return {'FINISHED'}


# All of this button needs to be completely redone.
class ExecuteOnCueOperator(bpy.types.Operator):
    bl_idname = "my.execute_on_cue_operator"
    bl_label = ""
    bl_description = "Orb deletes the macro (on the console), recreates the macro, sets the macro to enable the correct timecode clock, sets the macro to foreground mode, goes to Live mode, and instructs the cue execute the macro"
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = context.scene.sequence_editor.active_strip
        ip_address = context.scene.scene_props.str_osc_ip_address
        port = context.scene.scene_props.int_osc_port
        scene = bpy.context.scene
        
        argument_one = "1"
        argument_off = "0"
        
        if not scene.is_armed_turbo:
            address_one = "/eos/key/shift"
            address_two = "/eos/key/update"
            argument_two = "1"
            send_osc_string(address_one, ip_address, port, argument_one)
            send_osc_string(address_two, ip_address, port, argument_two)
            send_osc_string(address_one, ip_address, port, argument_off)
            time.sleep(2)
        
        address_three = "/eos/key/macro"
        argument_three = "11 Enter"
        
        send_osc_string(address_three, ip_address, port, argument_three)  
        send_osc_string(address_three, ip_address, port, argument_three)  
        
        time.sleep(.5)    
        
        address_four = "/eos/newcmd"
        argument_four = "Delete " + str(active_strip.execute_with_macro_number) + " Enter Enter"
        
        send_osc_string(address_four, ip_address, port, argument_four)
        
        time.sleep(.5)
        
        address_four_half = "/eos/newcmd"
        argument_four_half = str(active_strip.execute_with_macro_number) + " Enter"
        
        send_osc_string(address_four_half, ip_address, port, argument_four_half)
        
        time.sleep(.5)
        
        address_five = "/eos/softkey/6"
        argument_five = "1"
        
        send_osc_string(address_five, ip_address, port, argument_five)
        
        time.sleep(.1)
        
        address_six = "/eos/key/event"
        argument_six = "1"
        
        send_osc_string(address_six, ip_address, port, argument_six)
        
        
        event_list_number = str(active_strip.song_timecode_clock_number)
        down = "1"
        for digit in event_list_number:
            key = "/eos/key/" + digit
            send_osc_string(key, ip_address, port, down)
            time.sleep(.5)

        address_seven = "/eos/key/\\"
        argument_seven = "1"
        
        address_eight = "/eos/key/internal"
        argument_eight = "1"
        
        address_time = "/eos/key/time"
        argument_time = "1"
        
        address_nine = "/eos/key/enable"
        argument_nine = "1"
        
        address_ten = "/eos/key/enter"
        argument_ten = "1"              
        
        address_twelve = "/eos/key/select"
        argument_twelve = "1"
        
        address_twelve_half = "/eos/softkey/3"
        argument_twelve_half = "1"
        
        time.sleep(.5)
        send_osc_string(address_seven, ip_address, port, argument_seven)
        time.sleep(.5)
        send_osc_string(address_eight, ip_address, port, argument_eight)
        time.sleep(.5)
        send_osc_string(address_time, ip_address, port, argument_time)
        time.sleep(.5)
        send_osc_string(address_ten, ip_address, port, argument_ten)        
        
        #Event
        time.sleep(.5)
        send_osc_string(address_six, ip_address, port, argument_six)        
        
        event_list_number = str(active_strip.song_timecode_clock_number)
        down = "1"
        for digit in event_list_number:
            key = "/eos/key/" + digit
            send_osc_string(key, ip_address, port, down)
            time.sleep(.5)
                
        time.sleep(.5)
        send_osc_string(address_seven, ip_address, port, argument_seven)
        
        time.sleep(.5)
        send_osc_string(address_eight, ip_address, port, argument_eight)
        
        time.sleep(.5)
        send_osc_string(address_nine, ip_address, port, argument_nine)
        
        time.sleep(.5)
        send_osc_string(address_ten, ip_address, port, argument_ten)       
        
        time.sleep(.5)
        send_osc_string(address_twelve, ip_address, port, argument_twelve)
        time.sleep(.5)
        send_osc_string(address_twelve_half, ip_address, port, argument_twelve_half)
        time.sleep(.5)
        send_osc_string(address_ten, ip_address, port, argument_ten)
        time.sleep(.5)        
        
        address_thirteen = "/eos/key/live"
        argument_thirteen = "1"
        
        send_osc_string(address_thirteen, ip_address, port, argument_thirteen)
        
        time.sleep(.5)

        address_fourteen = "/eos/newcmd"
        argument_fourteen = "Cue " + str(active_strip.execute_on_cue_number) + " Execute Macro " + str(active_strip.execute_with_macro_number) + "Enter Enter"
        
        send_osc_string(address_fourteen, ip_address, port, argument_fourteen)
        
        #resets stupid macro key
        send_osc_string(address_three, ip_address, port, argument_off) 
        
        snapshot = str(context.scene.orb_finish_snapshot)
        send_osc_string("/eos/newcmd", ip_address, port, f"Snapshot {snapshot} Enter")
        
        self.report({'INFO'}, "Orb complete.")

        return {'FINISHED'}
    
    
## All of this button needs to be completely redone.
class DisableOnCueOperator(bpy.types.Operator):
    bl_idname = "my.disable_on_cue_operator"
    bl_label = ""
    bl_description = "Orb deletes the macro (on the console), recreates the macro, sets the macro to disable the correct timecode clock, sets the macro to foreground mode, goes to Live mode, and instructs the cue execute the macro"
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = context.scene.sequence_editor.active_strip
        ip_address = context.scene.scene_props.str_osc_ip_address
        port = context.scene.scene_props.int_osc_port
        scene = bpy.context.scene
        
        argument_one = "1"
        argument_off = "0"
        
        if not scene.is_armed_turbo:
            address_one = "/eos/key/shift"
            
            
            address_two = "/eos/key/update"
            argument_two = "1"
        
            send_osc_string(address_one, ip_address, port, argument_one)
            send_osc_string(address_two, ip_address, port, argument_two)
            send_osc_string(address_one, ip_address, port, argument_off)
            
            time.sleep(2)
        
        address_three = "/eos/key/macro"
        argument_three = "11 Enter"
        
        send_osc_string(address_three, ip_address, port, argument_three)  
        send_osc_string(address_three, ip_address, port, argument_three)  
        
        time.sleep(.5)    
        
        address_four = "/eos/newcmd"
        argument_four = "Delete " + str(active_strip.disable_with_macro_number) + " Enter Enter"
        
        send_osc_string(address_four, ip_address, port, argument_four)
        
        time.sleep(.5)
        
        address_four_half = "/eos/newcmd"
        argument_four_half = str(active_strip.disable_with_macro_number) + " Enter"
        
        send_osc_string(address_four_half, ip_address, port, argument_four_half)
        
        time.sleep(.5)
        
        address_five = "/eos/softkey/6"
        argument_five = "1"
        
        send_osc_string(address_five, ip_address, port, argument_five)
        
        time.sleep(.1)
        
        address_six = "/eos/key/event"
        argument_six = "1"
        
        send_osc_string(address_six, ip_address, port, argument_six)
        
        
        event_list_number = str(active_strip.song_timecode_clock_number)
        down = "1"
        for digit in event_list_number:
            key = "/eos/key/" + digit
            send_osc_string(key, ip_address, port, down)
            time.sleep(.5)

        address_seven = "/eos/key/\\"
        argument_seven = "1"
        
        address_eight = "/eos/key/internal"
        argument_eight = "1"
        
        address_time = "/eos/key/time"
        argument_time = "1"
        
        address_nine = "/eos/key/disable"
        argument_nine = "1"
        
        address_ten = "/eos/key/enter"
        argument_ten = "1"        
        
        address_twelve = "/eos/key/select"
        argument_twelve = "1"
        
        address_twelve_half = "/eos/softkey/3"
        argument_twelve_half = "1"
        
        time.sleep(.5)
        send_osc_string(address_seven, ip_address, port, argument_seven)
        time.sleep(.5)
        send_osc_string(address_eight, ip_address, port, argument_eight)
        time.sleep(.5)
        send_osc_string(address_time, ip_address, port, argument_time)
        time.sleep(.5)
        send_osc_string(address_ten, ip_address, port, argument_ten)        
        
        #Event
        time.sleep(.5)
        send_osc_string(address_six, ip_address, port, argument_six)
               
        event_list_number = str(active_strip.song_timecode_clock_number)
        down = "1"
        for digit in event_list_number:
            key = "/eos/key/" + digit
            send_osc_string(key, ip_address, port, down)
            time.sleep(.5)        
        
        time.sleep(.5)
        send_osc_string(address_seven, ip_address, port, argument_seven)
        
        time.sleep(.5)
        send_osc_string(address_eight, ip_address, port, argument_eight)
        
        time.sleep(.5)
        send_osc_string(address_nine, ip_address, port, argument_nine)
        
        time.sleep(.5)
        send_osc_string(address_ten, ip_address, port, argument_ten)       
        
        time.sleep(.5)
        send_osc_string(address_twelve, ip_address, port, argument_twelve)
        time.sleep(.5)
        send_osc_string(address_twelve_half, ip_address, port, argument_twelve_half)
        time.sleep(.5)
        send_osc_string(address_ten, ip_address, port, argument_ten)
        time.sleep(.5)
                
        address_thirteen = "/eos/key/live"
        argument_thirteen = "1"
        
        send_osc_string(address_thirteen, ip_address, port, argument_thirteen)
        
        time.sleep(.5)

        address_fourteen = "/eos/newcmd"
        argument_fourteen = "Cue " + str(active_strip.disable_on_cue_number) + " Execute Macro " + str(active_strip.disable_with_macro_number) + "Enter Enter"
        
        send_osc_string(address_fourteen, ip_address, port, argument_fourteen)
        
        #resets stupid macro key
        send_osc_string(address_three, ip_address, port, argument_off) 
        
        snapshot = str(context.scene.orb_finish_snapshot)
        send_osc_string("/eos/newcmd", ip_address, port, f"Snapshot {snapshot} Enter")
        
        self.report({'INFO'}, "Orb complete.")

        return {'FINISHED'}
    
    
## All of this button needs to be redone.
class ExecuteAnimationOnCueOperator(bpy.types.Operator):
    bl_idname = "my.execute_animation_on_cue_operator"
    bl_label = ""
    bl_description = "Orb deletes the macro (on the console), recreates the macro, sets the macro to enable the correct timecode clock, sets the macro to foreground mode, goes to Live mode, and instructs the cue execute the macro"
    
    def frame_to_timecode(self, frame, fps=None):
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
        
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = context.scene.sequence_editor.active_strip
        ip_address = context.scene.scene_props.str_osc_ip_address
        port = context.scene.scene_props.int_osc_port
        scene = bpy.context.scene
        start_frame_in_timecode = self.frame_to_timecode(active_strip.frame_start)
        
        argument_one = "1"
        argument_off = "0"
        
        if not scene.is_armed_turbo:
            address_one = "/eos/key/shift"
     
            address_two = "/eos/key/update"
            argument_two = "1"
        
            send_osc_string(address_one, ip_address, port, argument_one)
            send_osc_string(address_two, ip_address, port, argument_two)
            send_osc_string(address_one, ip_address, port, argument_off)
            
            time.sleep(2)
        
        address_three = "/eos/key/macro"
        argument_three = "11 Enter"
        
        send_osc_string(address_three, ip_address, port, argument_three)  
        send_osc_string(address_three, ip_address, port, argument_three)  
        
        time.sleep(.5)    
        
        address_four = "/eos/newcmd"
        argument_four = "Delete " + str(active_strip.execute_animation_with_macro_number) + " Enter Enter"
        
        send_osc_string(address_four, ip_address, port, argument_four)
        
        time.sleep(.5)
        
        address_four_half = "/eos/newcmd"
        argument_four_half = str(active_strip.execute_animation_with_macro_number) + " Enter"
        
        send_osc_string(address_four_half, ip_address, port, argument_four_half)
        
        time.sleep(.5)
        
        address_five = "/eos/softkey/6"
        argument_five = "1"
        
        send_osc_string(address_five, ip_address, port, argument_five)
        
        time.sleep(.1)
        
        address_six = "/eos/key/event"
        argument_six = "1"
        
        send_osc_string(address_six, ip_address, port, argument_six)
                
        event_list_number = str(active_strip.animation_event_list_number)
        down = "1"
        for digit in event_list_number:
            key = "/eos/key/" + digit
            send_osc_string(key, ip_address, port, down)
            time.sleep(.5)

        address_seven = "/eos/key/\\"
        argument_seven = "1"
        
        address_eight = "/eos/key/internal"
        argument_eight = "1"
        
        address_time = "/eos/key/time"
        argument_time = "1"
        
        address_nine = "/eos/key/enable"
        argument_nine = "1"
        
        address_ten = "/eos/key/enter"
        argument_ten = "1"        
        
        address_twelve = "/eos/key/select"
        argument_twelve = "1"
        
        address_twelve_half = "/eos/softkey/3"
        argument_twelve_half = "1"
        
        time.sleep(.5)
        send_osc_string(address_seven, ip_address, port, argument_seven)
        time.sleep(.5)
        send_osc_string(address_eight, ip_address, port, argument_eight)
        time.sleep(.5)
        send_osc_string(address_time, ip_address, port, argument_time)
        time.sleep(.5)
        
        down = "1"
        for digit in start_frame_in_timecode:
            key = "/eos/key/" + digit
            send_osc_string(key, ip_address, port, down)
            time.sleep(.2)
            
        time.sleep(.5)
        send_osc_string(address_ten, ip_address, port, argument_ten)
                
        #Event
        time.sleep(.5)
        send_osc_string(address_six, ip_address, port, argument_six)        
        
        event_list_number = str(active_strip.animation_event_list_number)
        down = "1"
        for digit in event_list_number:
            key = "/eos/key/" + digit
            send_osc_string(key, ip_address, port, down)
            time.sleep(.5)        
        
        time.sleep(.5)
        send_osc_string(address_seven, ip_address, port, argument_seven)
        
        time.sleep(.5)
        send_osc_string(address_eight, ip_address, port, argument_eight)
        
        time.sleep(.5)
        send_osc_string(address_nine, ip_address, port, argument_nine)
        
        time.sleep(.5)
        send_osc_string(address_ten, ip_address, port, argument_ten)       
        
        time.sleep(.5)
        send_osc_string(address_twelve, ip_address, port, argument_twelve)
        time.sleep(.5)
        send_osc_string(address_twelve_half, ip_address, port, argument_twelve_half)
        time.sleep(.5)
        send_osc_string(address_ten, ip_address, port, argument_ten)
        time.sleep(.5)
               
        address_thirteen = "/eos/key/live"
        argument_thirteen = "1"
        
        send_osc_string(address_thirteen, ip_address, port, argument_thirteen)
        
        time.sleep(.5)

        address_fourteen = "/eos/newcmd"
        argument_fourteen = "Cue 1 / " + str(active_strip.execute_animation_on_cue_number) + " Execute Macro " + str(active_strip.execute_animation_with_macro_number) + "Enter Enter"
        
        send_osc_string(address_fourteen, ip_address, port, argument_fourteen)
        
        #resets stupid macro key
        send_osc_string(address_three, ip_address, port, argument_off) 
        
        snapshot = str(context.scene.orb_finish_snapshot)
        send_osc_string("/eos/newcmd", ip_address, port, f"Snapshot {snapshot} Enter")
        
        self.report({'INFO'}, "Orb complete.")

        return {'FINISHED'}
    
    
## All of this button needs to be completely redone.
class DisableAnimationOnCueOperator(bpy.types.Operator):
    bl_idname = "my.disable_animation_on_cue_operator"
    bl_label = ""
    bl_description = "Orb deletes the macro (on the console), recreates the macro, sets the macro to disable the correct timecode clock, sets the macro to foreground mode, goes to Live mode, and instructs the cue execute the macro"
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = context.scene.sequence_editor.active_strip
        ip_address = context.scene.scene_props.str_osc_ip_address
        port = context.scene.scene_props.int_osc_port
        scene = bpy.context.scene
        
        argument_one = "1"
        argument_off = "0"
        
        if not scene.is_armed_turbo:
            address_one = "/eos/key/shift"
            
            
            address_two = "/eos/key/update"
            argument_two = "1"
        
            send_osc_string(address_one, ip_address, port, argument_one)
            send_osc_string(address_two, ip_address, port, argument_two)
            send_osc_string(address_one, ip_address, port, argument_off)
            
            time.sleep(2)
        
        address_three = "/eos/key/macro"
        argument_three = "11 Enter"
        
        send_osc_string(address_three, ip_address, port, argument_three)  
        send_osc_string(address_three, ip_address, port, argument_three)  
        
        time.sleep(.5)    
        
        address_four = "/eos/newcmd"
        argument_four = "Delete " + str(active_strip.disable_animation_with_macro_number) + " Enter Enter"
        
        send_osc_string(address_four, ip_address, port, argument_four)
        
        time.sleep(.5)
        
        address_four_half = "/eos/newcmd"
        argument_four_half = str(active_strip.disable_animation_with_macro_number) + " Enter"
        
        send_osc_string(address_four_half, ip_address, port, argument_four_half)
        
        time.sleep(.5)
        
        address_five = "/eos/softkey/6"
        argument_five = "1"
        
        send_osc_string(address_five, ip_address, port, argument_five)
        
        time.sleep(.1)
        
        address_six = "/eos/key/event"
        argument_six = "1"
        
        send_osc_string(address_six, ip_address, port, argument_six)
        
        
        event_list_number = str(active_strip.animation_event_list_number)
        down = "1"
        for digit in event_list_number:
            key = "/eos/key/" + digit
            send_osc_string(key, ip_address, port, down)
            time.sleep(.5)


        address_seven = "/eos/key/\\"
        argument_seven = "1"
        
        address_eight = "/eos/key/internal"
        argument_eight = "1"
        
        address_time = "/eos/key/time"
        argument_time = "1"
        
        address_nine = "/eos/key/disable"
        argument_nine = "1"
        
        address_ten = "/eos/key/enter"
        argument_ten = "1"

        address_twelve = "/eos/key/select"
        argument_twelve = "1"
        
        address_twelve_half = "/eos/softkey/3"
        argument_twelve_half = "1"
        
        time.sleep(.5)
        send_osc_string(address_seven, ip_address, port, argument_seven)
        time.sleep(.5)
        send_osc_string(address_eight, ip_address, port, argument_eight)
        time.sleep(.5)
        send_osc_string(address_time, ip_address, port, argument_time)
        time.sleep(.5)
        send_osc_string(address_ten, ip_address, port, argument_ten)
               
        #Event
        time.sleep(.5)
        send_osc_string(address_six, ip_address, port, argument_six)
                
        event_list_number = str(active_strip.animation_event_list_number)
        down = "1"
        for digit in event_list_number:
            key = "/eos/key/" + digit
            send_osc_string(key, ip_address, port, down)
            time.sleep(.5)
                
        time.sleep(.5)
        send_osc_string(address_seven, ip_address, port, argument_seven)
        
        time.sleep(.5)
        send_osc_string(address_eight, ip_address, port, argument_eight)
        
        time.sleep(.5)
        send_osc_string(address_nine, ip_address, port, argument_nine)
        
        time.sleep(.5)
        send_osc_string(address_ten, ip_address, port, argument_ten)       
        
        time.sleep(.5)
        send_osc_string(address_twelve, ip_address, port, argument_twelve)
        time.sleep(.5)
        send_osc_string(address_twelve_half, ip_address, port, argument_twelve_half)
        time.sleep(.5)
        send_osc_string(address_ten, ip_address, port, argument_ten)
        time.sleep(.5)
                
        address_thirteen = "/eos/key/live"
        argument_thirteen = "1"
        
        send_osc_string(address_thirteen, ip_address, port, argument_thirteen)
        
        time.sleep(.5)

        address_fourteen = "/eos/newcmd"
        argument_fourteen = "Cue 1 / " + str(active_strip.disable_animation_on_cue_number) + " Execute Macro " + str(active_strip.disable_animation_with_macro_number) + "Enter Enter"
        
        send_osc_string(address_fourteen, ip_address, port, argument_fourteen)
        
        #resets stupid macro key
        send_osc_string(address_three, ip_address, port, argument_off) 
        
        active_strip.my_settings.motif_type_enum = "option_eos_macro"
        active_strip.start_frame_macro = active_strip.execute_animation_with_macro_number
        active_strip.end_frame_macro = active_strip.disable_animation_with_macro_number
        
        snapshot = str(context.scene.orb_finish_snapshot)
        send_osc_string("/eos/newcmd", ip_address, port, f"Snapshot {snapshot} Enter")
        
        self.report({'INFO'}, "Orb complete.")

        return {'FINISHED'}
    

## All of this button needs to be completely redone.
class GenerateStartFrameMacroOperator(bpy.types.Operator):
    bl_idname = "my.generate_start_frame_macro"
    bl_label = ""
    bl_description = 'Orb creates the macro on the console. In the background, any * signs will be replaced with "Sneak Time [strip length]". "Enter" is added to end if missing. Missing underscores are added to some keys'
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = context.scene.sequence_editor.active_strip
        ip_address = context.scene.scene_props.str_osc_ip_address
        port = context.scene.scene_props.int_osc_port
        scene = bpy.context.scene
        
        start_macro_update(active_strip, context)
        
        argument_one = "1"
        argument_off = "0"
        
        if not scene.is_armed_turbo:
            address_one = "/eos/key/shift"
            
            
            address_two = "/eos/key/update"
            argument_two = "1"
        
            send_osc_string(address_one, ip_address, port, argument_one)
            send_osc_string(address_two, ip_address, port, argument_two)
            send_osc_string(address_one, ip_address, port, argument_off)
            
            time.sleep(2)
        
        address_three = "/eos/key/macro"
        argument_three = "1"
        
        address_six = "/eos/key/learn"
        argument_six = "Enter"
        
        send_osc_string(address_six, ip_address, port, argument_six)
        
        time.sleep(.5)
        
        address_seven = "/eos/key/macro"
        argument_seven = "1"
        
        send_osc_string(address_seven, ip_address, port, argument_seven)
        
        time.sleep(.5)
        
        
        macro_number = str(active_strip.start_frame_macro)
        down = "1"
        for digit in macro_number:
            key = "/eos/key/" + digit
            send_osc_string(key, ip_address, port, down)
            time.sleep(.5)
            
        address_eight = "/eos/key/enter"
        argument_eight = "1"
        
        send_osc_string(address_eight, ip_address, port, argument_eight)
        
        time.sleep(.5)
        
        send_osc_string(address_eight, ip_address, port, argument_eight)
        
        time.sleep(.5)
        
        address_nine = "/eos/newcmd"
        argument_nine = active_strip.start_frame_macro_text
        
        send_osc_string(address_nine, ip_address, port, argument_nine)
        
        time.sleep(.5)
        
        send_osc_string(address_six, ip_address, port, argument_six)
        
        #resets stupid macro key
        send_osc_string(address_three, ip_address, port, argument_off) 
        
        snapshot = str(context.scene.orb_finish_snapshot)
        send_osc_string("/eos/newcmd", ip_address, port, f"Snapshot {snapshot} Enter")
        
        self.report({'INFO'}, "Orb complete.")
        
        return {'FINISHED'}
    
    
## All of this button needs to be completely redone.
class GenerateEndFrameMacroOperator(bpy.types.Operator):
    bl_idname = "my.generate_end_frame_macro"
    bl_label = ""
    bl_description = 'Orb creates the macro on the console. In the background, any * signs will be replaced with "Sneak Time [strip length]". "Enter" is added to end if missing. Missing underscores are added to some keys'
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = context.scene.sequence_editor.active_strip
        ip_address = context.scene.scene_props.str_osc_ip_address
        port = context.scene.scene_props.int_osc_port
        scene = bpy.context.scene
        
        end_macro_update(active_strip, context)
        
        argument_one = "1"
        argument_off = "0"
        
        if not scene.is_armed_turbo:
            address_one = "/eos/key/shift"
            
            
            address_two = "/eos/key/update"
            argument_two = "1"
        
            send_osc_string(address_one, ip_address, port, argument_one)
            send_osc_string(address_two, ip_address, port, argument_two)
            send_osc_string(address_one, ip_address, port, argument_off)
            
            time.sleep(2)
        
        address_three = "/eos/key/macro"
        argument_three = "1"
        
        address_six = "/eos/key/learn"
        argument_six = "Enter"
        
        send_osc_string(address_six, ip_address, port, argument_six)
        
        time.sleep(.5)
        
        address_seven = "/eos/key/macro"
        argument_seven = "1"
        
        send_osc_string(address_seven, ip_address, port, argument_seven)
        
        time.sleep(.5)
        
        
        macro_number = str(active_strip.end_frame_macro)
        down = "1"
        for digit in macro_number:
            key = "/eos/key/" + digit
            send_osc_string(key, ip_address, port, down)
            time.sleep(.5)
            
        
        address_eight = "/eos/key/enter"
        argument_eight = "1"
        
        send_osc_string(address_eight, ip_address, port, argument_eight)
        
        time.sleep(.5)
        
        send_osc_string(address_eight, ip_address, port, argument_eight)
        
        time.sleep(.5)
        
        address_nine = "/eos/newcmd"
        argument_nine = active_strip.end_frame_macro_text
        
        send_osc_string(address_nine, ip_address, port, argument_nine)
        
        time.sleep(.5)
        
        send_osc_string(address_six, ip_address, port, argument_six)
        
        #resets stupid macro key
        send_osc_string(address_three, ip_address, port, argument_off) 
        
        snapshot = str(context.scene.orb_finish_snapshot)
        send_osc_string("/eos/newcmd", ip_address, port, f"Snapshot {snapshot} Enter")
        
        self.report({'INFO'}, "Orb complete.")
        
        return {'FINISHED'}

    
def calculate_biased_start_length(bias, frame_rate, strip_length_in_frames):
    # Normalize bias to a 0-1 scale
    normalized_bias = (bias + 49) / 98  # This will give 0 for -49 and 1 for 49
    
    # Calculate minimum and maximum start_length in seconds
    min_start_length = 1 / frame_rate  # 1 frame
    max_start_length = (strip_length_in_frames - 1) / frame_rate  # Entire duration minus 1 frame
    
    # Interpolate between min and max based on normalized bias
    biased_start_length = (min_start_length * (1 - normalized_bias)) + (max_start_length * normalized_bias)
    
    # Round to 1 decimal place
    biased_start_length_rounded = round(biased_start_length, 1)
    
    return biased_start_length_rounded
    
    
# This button may be okay, not as dumb as the others
class BuildFlashMacrosOperator(bpy.types.Operator):
    bl_idname = "my.build_flash_macros"
    bl_label = ""
    bl_description = 'Orb builds the macros needed for the flash functionality'
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = context.scene.sequence_editor.active_strip
        ip_address = context.scene.scene_props.str_osc_ip_address
        port = context.scene.scene_props.int_osc_port
        
        shift = "/eos/key/shift" # requires up command to set boolean back to False
        update = "/eos/key/update"
        live = "/eos/key/live"
        macro = "/eos/key/macro" # requires up command to reset
        enter = "/eos/key/enter"
        learn = "/eos/key/learn" # Seems to need "enter" command instead of 1 or 0
        new_cmd = "/eos/newcmd"

        down = "1"
        up = "0"
        enter_arg = "Enter"
        
        if bpy.context.scene.is_armed_turbo == False:
            # Update console in cases this does something bad, so user can exit out reload file to restore
            send_osc_string(shift, ip_address, port, down)
            send_osc_string(update, ip_address, port, down)
            send_osc_string(update, ip_address, port, up)
            send_osc_string(shift, ip_address, port, up)
            
            time.sleep(2)
        
        # Learn M 1
        send_osc_string(live, ip_address, port, down)
        send_osc_string(live, ip_address, port, up)
        time.sleep(.5)
        send_osc_string(learn, ip_address, port, enter_arg)
        time.sleep(.5)
        send_osc_string(macro, ip_address, port, down)
        send_osc_string(macro, ip_address, port, up)
        time.sleep(.5)
        
        macro_number = str(active_strip.start_flash_macro_number)
        for digit in macro_number:
            key = "/eos/key/" + digit
            send_osc_string(key, ip_address, port, down)
            send_osc_string(key, ip_address, port, up)
            time.sleep(.5)
            
        send_osc_string(enter, ip_address, port, down)
        send_osc_string(enter, ip_address, port, up)
        
        time.sleep(.5)
        
        send_osc_string(enter, ip_address, port, down)
        send_osc_string(enter, ip_address, port, up)
        
        time.sleep(.5)
        
        scene = bpy.context.scene
        frame_rate = get_frame_rate(scene)
        strip_length_in_frames = active_strip.frame_final_duration
        strip_length_in_seconds = strip_length_in_frames / frame_rate
        bias = active_strip.flash_bias
        
        start_length = calculate_biased_start_length(bias, frame_rate, strip_length_in_frames)
        end_length = strip_length_in_seconds - start_length
        end_length = round(end_length, 1)

        m1 = str(active_strip.flash_input_background) + " Sneak Time " + str(start_length) + " Enter "
        
        send_osc_string(new_cmd, ip_address, port, m1)
        time.sleep(.5)
        send_osc_string(enter, ip_address, port, down)
        send_osc_string(enter, ip_address, port, up)
        send_osc_string(learn, ip_address, port, enter_arg)
                
        # Learn M 2
        send_osc_string(learn, ip_address, port, enter_arg)
        time.sleep(.5)
        send_osc_string(macro, ip_address, port, down)
        send_osc_string(macro, ip_address, port, up)
        time.sleep(.5)
        
        macro_number = str(active_strip.end_flash_macro_number)
        for digit in macro_number:
            key = "/eos/key/" + digit
            send_osc_string(key, ip_address, port, down)
            send_osc_string(key, ip_address, port, up)
            time.sleep(.5)
            
        send_osc_string(enter, ip_address, port, down)
        send_osc_string(enter, ip_address, port, up)
        
        time.sleep(.5)
        
        send_osc_string(enter, ip_address, port, down)
        send_osc_string(enter, ip_address, port, up)
        
        time.sleep(.5)
        
        scene = bpy.context.scene
        frame_rate = get_frame_rate(scene)
        strip_length_in_frames = active_strip.frame_final_duration
        strip_length_in_seconds = strip_length_in_frames / frame_rate
        bias = active_strip.flash_bias
        
        start_length = calculate_biased_start_length(bias, frame_rate, strip_length_in_frames)
        end_length = strip_length_in_seconds - start_length
        end_length = round(end_length, 1)

        m1 = str(active_strip.flash_input_background) + " Sneak Time " + str(start_length) + " Enter "
        m2 = str(active_strip.flash_down_input_background) + " Sneak Time " + str(end_length) + " Enter"
        send_osc_string(new_cmd, ip_address, port, m2)
        time.sleep(.5)
        send_osc_string(enter, ip_address, port, down)
        send_osc_string(enter, ip_address, port, up)
        send_osc_string(learn, ip_address, port, enter_arg)
        
        snapshot = str(context.scene.orb_finish_snapshot)
        send_osc_string("/eos/newcmd", ip_address, port, f"Snapshot {snapshot} Enter")
        
        self.report({'INFO'}, "Orb complete.")

        return {'FINISHED'}


intensity_preset = "/eos/*"
red_preset = "/eos/*/param/red"
green_preset = "/eos/*/param/green"
blue_preset = "/eos/*/param/blue"
pan_preset = "/eos/*/param/pan"
tilt_preset = "/eos/*/param/tilt"
zoom_preset = "/eos/*/param/zoom"
iris_preset = "/eos/*/param/iris"


class SetMaxZoomOperator(bpy.types.Operator):
    bl_idname = "my.set_max_zoom"
    bl_label = ""
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = sequence_editor.active_strip
        
        global max_zoom
        global min_zoom
        
        max_zoom = active_strip.osc_zoom
        
        bpy.types.ColorSequence.osc_zoom  = bpy.props.FloatProperty(name="Zoom:", min=min_zoom, max=max_zoom, options={'ANIMATABLE'}, update=osc_zoom_update, default=10)
        return {'FINISHED'}
    
    
class SetMinZoomOperator(bpy.types.Operator):
    bl_idname = "my.set_min_zoom"
    bl_label = ""
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = sequence_editor.active_strip
        
        global max_zoom
        global min_zoom
        
        min_zoom = active_strip.osc_zoom
        bpy.types.ColorSequence.osc_zoom  = bpy.props.FloatProperty(name="Zoom:", min=min_zoom, max=max_zoom, options={'ANIMATABLE'}, update=osc_zoom_update, default=10)
        return {'FINISHED'}
    
    
class SetMaxIrisOperator(bpy.types.Operator):
    bl_idname = "my.set_max_iris"
    bl_label = ""
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = sequence_editor.active_strip
        
        global max_iris
        global min_iris
        
        max_iris = active_strip.osc_iris
        bpy.types.ColorSequence.osc_iris  = bpy.props.FloatProperty(name="Custom 2:", min=min_iris, max=max_iris, options={'ANIMATABLE'}, update=osc_iris_update, default=10)
        return {'FINISHED'}
    

class SetMinIrisOperator(bpy.types.Operator):
    bl_idname = "my.set_min_iris"
    bl_label = ""
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = sequence_editor.active_strip
        
        global max_iris
        global min_iris
        
        min_iris = active_strip.osc_iris
        bpy.types.ColorSequence.osc_iris  = bpy.props.FloatProperty(name="Custom 2:", min=min_iris, max=max_iris, options={'ANIMATABLE'}, update=osc_iris_update, default=10)
        return {'FINISHED'}
    

class ResetZoomRangeOperator(bpy.types.Operator):
    bl_idname = "my.reset_zoom_range"
    bl_label = ""
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = sequence_editor.active_strip
        
        global max_zoom
        global min_zoom
        
        max_zoom = 1000
        min_zoom = -1000
        
        bpy.types.ColorSequence.osc_zoom  = bpy.props.FloatProperty(name="Custom 2:", min=min_zoom, max=max_zoom, options={'ANIMATABLE'}, update=osc_zoom_update, default=10)
        return {'FINISHED'}
    
    
class ResetIrisRangeOperator(bpy.types.Operator):
    bl_idname = "my.reset_iris_range"
    bl_label = ""
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = sequence_editor.active_strip
        
        global max_iris
        global min_iris
        
        max_iris = 1000
        min_iris = -1000
        
        bpy.types.ColorSequence.osc_iris  = bpy.props.FloatProperty(name="Custom 2:", min=min_iris, max=max_iris, options={'ANIMATABLE'}, update=osc_iris_update, default=10)
        return {'FINISHED'}


class ClearIntensityOperator(bpy.types.Operator):
    bl_idname = "my.clear_intensity"
    bl_label = ""
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = sequence_editor.active_strip
        active_strip.intensity_prefix = ""
        return {'FINISHED'}
    

class ClearRedOperator(bpy.types.Operator):
    bl_idname = "my.clear_red"
    bl_label = ""
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = sequence_editor.active_strip
        active_strip.red_prefix = ""
        return {'FINISHED'}
    

class ClearGreenOperator(bpy.types.Operator):
    bl_idname = "my.clear_green"
    bl_label = ""
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = sequence_editor.active_strip
        active_strip.green_prefix = ""
        return {'FINISHED'}
    
    
class ClearBlueOperator(bpy.types.Operator):
    bl_idname = "my.clear_blue"
    bl_label = ""
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = sequence_editor.active_strip
        active_strip.blue_prefix = ""
        return {'FINISHED'}
    
    
class ClearPanOperator(bpy.types.Operator):
    bl_idname = "my.clear_pan"
    bl_label = ""
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = sequence_editor.active_strip
        active_strip.pan_prefix = ""
        return {'FINISHED'}
    
    
class ClearTiltOperator(bpy.types.Operator):
    bl_idname = "my.clear_tilt"
    bl_label = ""
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = sequence_editor.active_strip
        active_strip.tilt_prefix = ""
        return {'FINISHED'}
    
    
class ClearZoomOperator(bpy.types.Operator):
    bl_idname = "my.clear_zoom"
    bl_label = ""
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = sequence_editor.active_strip
        active_strip.zoom_prefix = ""
        return {'FINISHED'}
    
    
class ClearIrisOperator(bpy.types.Operator):
    bl_idname = "my.clear_iris"
    bl_label = ""
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = sequence_editor.active_strip
        active_strip.iris_prefix = ""
        return {'FINISHED'}
    
    
class ClearIntensityDataOperator(bpy.types.Operator):
    bl_idname = "my.clear_intensity_data"
    bl_label = ""
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = sequence_editor.active_strip
        return {'FINISHED'}


class ClearPanDataOperator(bpy.types.Operator):
    bl_idname = "my.clear_pan_data"
    bl_label = ""
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = sequence_editor.active_strip
        active_strip.pan_prefix = ""
        return {'FINISHED'}
    
    
class ClearTiltDataOperator(bpy.types.Operator):
    bl_idname = "my.clear_tilt_data"
    bl_label = ""
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = sequence_editor.active_strip
        active_strip.tilt_prefix = ""
        return {'FINISHED'}
    
    
class ClearZoomDataOperator(bpy.types.Operator):
    bl_idname = "my.clear_zoom_data"
    bl_label = ""
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = sequence_editor.active_strip
        active_strip.zoom_prefix = ""
        return {'FINISHED'}
    

class ClearIrisDataOperator(bpy.types.Operator):
    bl_idname = "my.clear_iris_data"
    bl_label = ""
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = sequence_editor.active_strip
        active_strip.iris_prefix = ""
        return {'FINISHED'}
    
    
class ViewGraphOperator(bpy.types.Operator):
    bl_idname = "my.view_graph"
    bl_label = ""
    bl_description = "Before clicking this, open up a Blender graph editor elsewhere. Then, pressing this button will automatically zoom that viewer to the selected keyframes. Graphs gives you access to f-curves, aka the candy store you didn't know existed"
    
    def execute(self, context):
        graph_editor = None
        for area in bpy.context.screen.areas:
            if area.type == 'GRAPH_EDITOR':
                graph_editor = area
                break
                
        if graph_editor:
            for region in graph_editor.regions:
                if region.type == 'WINDOW':
                    override = {
                        'area': graph_editor,
                        'region': region,
                        'screen': context.screen,
                        'scene': context.scene,
                    }
                    bpy.ops.graph.view_selected(override)
                    return {'FINISHED'}
        else:
            self.report({'ERROR'}, "No graph editor found. Please open a graph editor window.")
            return {'CANCELLED'}
        
        return {'FINISHED'}
    
    
class KeyframeIntensityOperator(bpy.types.Operator):
    bl_idname = "my.keyframe_intensity"
    bl_label = ""
    bl_description = "A keyframe is like an inverted cue. It affects behavior before, not after like a cue. A keyframe is proactive while a cue is reactive. Adding a keyframe locks the parameter to that value at that exact time"
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = sequence_editor.active_strip

        if hasattr(active_strip, "osc_intensity"):  
            active_strip.keyframe_insert(data_path="osc_intensity", frame=bpy.context.scene.frame_current)
        else:
            self.report({'ERROR'}, "Active strip does not have 'osc_intensity' property.")
            
        return {'FINISHED'}
    
    
class KeyframeColorOperator(bpy.types.Operator):
    bl_idname = "my.keyframe_color"
    bl_label = ""
    bl_description = "A keyframe is better than a cue with a curve on it because with this, you can make a mover draw a unicorn in 2 minutes (once Paths support is added)"
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = sequence_editor.active_strip

        if hasattr(active_strip, "osc_color"):  
            active_strip.keyframe_insert(data_path="osc_color", frame=bpy.context.scene.frame_current)
        else:
            self.report({'ERROR'}, "Active strip does not have 'osc_color' property.")
            
        return {'FINISHED'}
    
    
class KeyframePanOperator(bpy.types.Operator):
    bl_idname = "my.keyframe_pan"
    bl_label = ""
    bl_description = "If you want to design the best football play on earth, do you want to design it with a call sheet (cue list), or do you want to design it by stopping time and manually animating the movements of each individual player (keyframes)?"
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = sequence_editor.active_strip

        if hasattr(active_strip, "osc_pan"):  
            active_strip.keyframe_insert(data_path="osc_pan", frame=bpy.context.scene.frame_current)
        else:
            self.report({'ERROR'}, "Active strip does not have 'osc_pan' property.")
            
        return {'FINISHED'}
    
    
class KeyframeTiltOperator(bpy.types.Operator):
    bl_idname = "my.keyframe_tilt"
    bl_label = ""
    bl_description = "Keyframes are useful for creating extremely specific motion paths. They can be used to create dynamic light designs with zero repetition. This means natural, organic, non-repeating movement without any technicals"
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = sequence_editor.active_strip

        if hasattr(active_strip, "osc_tilt"):  
            active_strip.keyframe_insert(data_path="osc_tilt", frame=bpy.context.scene.frame_current)
        else:
            self.report({'ERROR'}, "Active strip does not have 'osc_tilt' property.")
            
        return {'FINISHED'}
    
    
class KeyframeZoomOperator(bpy.types.Operator):
    bl_idname = "my.keyframe_zoom"
    bl_label = ""
    bl_description = "Here's a secret: this doesn't have to control zoom. It says zoom, but it can just as easily control gobo rotatation speed or strobe speed if you change the prefix. Just so you know. This will be made smarter in the next version"
    
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = sequence_editor.active_strip

        if hasattr(active_strip, "osc_zoom"):  
            active_strip.keyframe_insert(data_path="osc_zoom", frame=bpy.context.scene.frame_current)
        else:
            self.report({'ERROR'}, "Active strip does not have 'osc_zoom' property.")
            
        return {'FINISHED'}
    

class KeyframeIrisOperator(bpy.types.Operator):
    bl_idname = "my.keyframe_iris"
    bl_label = ""
    bl_description = "Here's a secret: this doesn't have to control iris. It says iris, but it can just as easily control gobo rotatation speed or strobe speed if you change the prefix. Just so you know. This will be made smarter in the next version"
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = sequence_editor.active_strip

        if hasattr(active_strip, "osc_iris"):  
            active_strip.keyframe_insert(data_path="osc_iris", frame=bpy.context.scene.frame_current)
        else:
            self.report({'ERROR'}, "Active strip does not have 'osc_iris' property.")

        return {'FINISHED'}
    
    
class LoadPresetOperator(bpy.types.Operator):
    bl_idname = "my.load_preset"
    bl_label = "Load"
    bl_description = "Recall stored values from the aether"
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        selected_strips = [strip for strip in sequence_editor.sequences if strip.select]
        
        global intensity_preset, red_preset, green_preset, blue_preset, pan_preset, tilt_preset, zoom_preset, iris_preset
        
        for strip in selected_strips:
            if not strip.intensity_prefix:
                strip.intensity_prefix = intensity_preset
            if not strip.red_prefix:
                strip.red_prefix = red_preset
            if not strip.green_prefix:
                strip.green_prefix = green_preset
            if not strip.blue_prefix:
                strip.blue_prefix = blue_preset
            if not strip.pan_prefix:
                strip.pan_prefix = pan_preset
            if not strip.tilt_prefix:
                strip.tilt_prefix = tilt_preset
            if not strip.zoom_prefix:
                strip.zoom_prefix = zoom_preset
            if not strip.iris_prefix:
                strip.iris_prefix = iris_preset
        
        return {'FINISHED'}
    

class RecordPresetOperator(bpy.types.Operator):
    bl_idname = "my.record_preset"
    bl_label = "Record"
    bl_description = "Store these values into the aether"
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = context.scene.sequence_editor.active_strip
        
        global intensity_preset, pan_preset, tilt_preset, zoom_preset, iris_preset
        
        intensity_preset = active_strip.intensity_prefix
        red_preset = active_strip.red_prefix
        green_preset = active_strip.green_prefix
        blue_preset = active_strip.blue_prefix
        pan_preset = active_strip.pan_prefix
        tilt_preset = active_strip.tilt_prefix
        zoom_preset = active_strip.zoom_prefix
        iris_preset = active_strip.iris_prefix
        
        return{'FINISHED'}
    
    
zoom_temp_preset = ""
iris_temp_preset = ""
    
    
class ReplaceOperator(bpy.types.Operator):
    bl_idname = "my.replace_button"
    bl_label = "Replace"
    bl_description = "Type an asterisk (*) anywhere in the prefixes boxes and then press this button to replace all those asterisks with the stuff to the right"
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = sequence_editor.active_strip
        replacement_value = context.scene.replacement_value
        selected_strips = [strip for strip in sequence_editor.sequences if strip.select]
        
        global intensity_preset, pan_preset, tilt_preset, zoom_temp_preset, iris_temp_preset
        
        for strip in selected_strips:
            if not strip.intensity_prefix == "":
                strip.intensity_prefix = intensity_preset
            if not strip.red_prefix == "":
                strip.red_prefix = red_preset
            if not strip.green_prefix == "":
                strip.green_prefix = green_preset
            if not strip.blue_prefix == "":
                strip.blue_prefix = blue_preset
            if not strip.pan_prefix == "":
                strip.pan_prefix = pan_preset
            if not strip.tilt_prefix == "":
                strip.tilt_prefix = tilt_preset
            if not strip.zoom_prefix == "":
                zoom_temp_preset = strip.zoom_prefix
            if not strip.iris_prefix == "":
                iris_temp_preset = strip.iris_prefix
                
        if not strip.zoom_prefix == "":
            zoom_temp_preset = strip.zoom_prefix
        if not strip.iris_prefix == "":
            iris_temp_preset = strip.iris_prefix

        for strip in selected_strips:
            strip.intensity_prefix = str(strip.intensity_prefix.replace("*", replacement_value))
            strip.red_prefix = str(strip.red_prefix.replace("*", replacement_value))
            strip.green_prefix = str(strip.green_prefix.replace("*", replacement_value))
            strip.blue_prefix = str(strip.blue_prefix.replace("*", replacement_value))
            strip.pan_prefix = str(strip.pan_prefix.replace("*", replacement_value))
            strip.tilt_prefix = str(strip.tilt_prefix.replace("*", replacement_value))
            strip.zoom_prefix = str(strip.zoom_prefix.replace("*", replacement_value))
            strip.iris_prefix = str(strip.iris_prefix.replace("*", replacement_value))

        return {'FINISHED'}
    
## Why does this still do nothing???
#class OSCHelpOperator(bpy.types.Operator):
#    bl_idname = "my.osc_help_button"
#    bl_label = "Help: What do I Put?"
#    
#    _timer = None

#    def modal(self, context, event):
#        if event.type in {'RIGHTMOUSE', 'ESC'}:
#            self.cancel(context)
#            return {'CANCELLED'}

#        if not context.area or context.area.type != 'TEXT_EDITOR':
#            self.cancel(context)
#            return {'CANCELLED'}

#        return {'PASS_THROUGH'}

#    def invoke(self, context, event):
#        # Create a new text block with the help information
#        text_block = bpy.data.texts.new("OSC_Help")
#        text_block.write("Here is some helpful text about OSC...\n")
#        text_block.write("More information here...\n")
#        text_block.write("Copy this text or follow this link: www.yourlinkhere.com")

#        # Change the current area type to the text editor and set the text block
#        context.area.type = 'TEXT_EDITOR'
#        context.space_data.text = text_block

#        self._timer = context.window_manager.event_timer_add(0.1, window=context.window)
#        context.window_manager.modal_handler_add(self)
#        return {'RUNNING_MODAL'}

#    def cancel(self, context):
#        context.window_manager.event_timer_remove(self._timer)


class SyncVideoOperator(bpy.types.Operator):
    bl_idname = "my.sync_video"
    bl_label = "Sync Video to Audio Speed"
    bl_description = "Synchronizes start and end frame of a video and also remaps the timing if the frame rate of the sequencer does not match that of the video"
        
    def execute(self, context):
        selected_sound_strip = [strip for strip in context.scene.sequence_editor.sequences if strip.select and strip.type == 'SOUND']
        selected_video_strip = [strip for strip in context.scene.sequence_editor.sequences if strip.select and strip.type == 'MOVIE']
        
        video_strip = selected_video_strip[0]
        sound_strip = selected_sound_strip[0]
        
        channel = find_available_channel(context.scene.sequence_editor, video_strip.frame_start, video_strip.frame_final_end, video_strip.channel + 1)

        if video_strip.frame_final_duration != sound_strip.frame_final_duration: 
            speed_strip = context.scene.sequence_editor.sequences.new_effect(
                    name="Speed Control",
                    type='SPEED',
                    seq1=video_strip,
                    channel=channel,
                    frame_start=video_strip.frame_start,
                    frame_end=video_strip.frame_final_end
            )
        
        video_strip.frame_start = sound_strip.frame_start
        video_strip.frame_final_duration = sound_strip.frame_final_duration
        return{'FINISHED'}
        

class SyncCueOperator(bpy.types.Operator):
    bl_idname = "my.sync_cue"
    bl_label = ""
    bl_description = "Orb will set the cue duration on the board as the strip length of this strip. You must press this every time you change the length of the strip if you want it use the strip length to set cue time"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        ip_address = context.scene.scene_props.str_osc_ip_address
        port = context.scene.scene_props.int_osc_port
        
        frame_rate = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base
        strip_length_in_seconds_total = int(round(active_strip.frame_final_duration / frame_rate))
        minutes = strip_length_in_seconds_total // 60
        seconds = strip_length_in_seconds_total % 60
        cue_duration = "{:02d}:{:02d}".format(minutes, seconds)
        address = "/eos/key/live"
        argument = "1"
        cue_number = active_strip.eos_cue_number
        address_two = "/eos/newcmd"
        argument_two = "Cue " + str(cue_number) + " Time " + cue_duration + " Enter"
        send_osc_string(address, ip_address, port, argument)
        send_osc_string(address_two, ip_address, port, argument_two)
        active_strip.name = "Cue " + str(cue_number)
        self.report({'INFO'}, "Orb complete.")
        
        snapshot = str(context.scene.orb_finish_snapshot)
        send_osc_string("/eos/newcmd", ip_address, port, f"Snapshot {snapshot} Enter")
        
        return {'FINISHED'}


class StartMacroEyeballOperator(bpy.types.Operator):
    bl_idname = "sequencer.start_macro_eyeball_toggle"
    bl_label = "Toggle Macro Mute"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        active_strip.macro_muted = not active_strip.macro_muted
        return {'FINISHED'}
    

class EndMacroEyeballOperator(bpy.types.Operator):
    bl_idname = "sequencer.end_macro_eyeball_toggle"
    bl_label = "Toggle Macro Mute"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        active_strip.macro_muted = not active_strip.macro_muted
        return {'FINISHED'}
    

class ShowWaveformOperator(bpy.types.Operator):
    bl_idname = "my.waveform_operator"
    bl_label = "Draw Waveform"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        name = active_strip.name
        if bpy.context.scene.sequence_editor.sequences_all[name].show_waveform == False:
            bpy.context.scene.sequence_editor.sequences_all[name].show_waveform = True
        if bpy.context.scene.sequence_editor.sequences_all[name].show_waveform == True:
            bpy.context.scene.sequence_editor.sequences_all[name].show_waveform = False
        return {'FINISHED'}


class ColorTriggerOperator(bpy.types.Operator):
    bl_idname = "my.color_trigger"
    bl_label = "Color Trigger"
    
    def execute(self, context):
        active_strip = bpy.context.scene.sequence_editor.active_strip
        sequence_editor = bpy.context.scene.sequence_editor
        color = active_strip.color
        scene = bpy.context.scene
        
        for strip in filter_color_strips(sequence_editor.sequences_all):
            if strip.color == color:
                strip.select = True
            else:
                if scene.is_filtering_right == True:
                    strip.select = False
        
        return {'FINISHED'}
    

class StripNameTriggerOperator(bpy.types.Operator):
    bl_idname = "my.strip_name_trigger"
    bl_label = "Strip Name Trigger"
    
    def execute(self, context):
        active_strip = bpy.context.scene.sequence_editor.active_strip
        sequence_editor = bpy.context.scene.sequence_editor
        name = active_strip.name
        scene = bpy.context.scene
        
        for strip in filter_color_strips(sequence_editor.sequences_all):
            if strip.name == name:
                strip.select = True
            else:
                if scene.is_filtering_right == True:
                    strip.select = False
        return {'FINISHED'}
    

class ChannelTriggerOperator(bpy.types.Operator):
    bl_idname = "my.channel_trigger"
    bl_label = "Channel Trigger"
    
    def execute(self, context):
        active_strip = bpy.context.scene.sequence_editor.active_strip
        sequence_editor = bpy.context.scene.sequence_editor
        channel = active_strip.channel
        scene = bpy.context.scene
        
        for strip in filter_color_strips(sequence_editor.sequences_all):
            if strip.channel == channel:
                strip.select = True
            else:
                if scene.is_filtering_right == True:
                    strip.select = False
        return {'FINISHED'}
    

class StartFrameTriggerOperator(bpy.types.Operator):
    bl_idname = "my.start_frame_trigger"
    bl_label = "Start Frame Trigger"
    
    def execute(self, context):
        active_strip = bpy.context.scene.sequence_editor.active_strip
        sequence_editor = bpy.context.scene.sequence_editor
        frame_start = active_strip.frame_start
        scene = bpy.context.scene
        
        for strip in filter_color_strips(sequence_editor.sequences_all):
            if strip.frame_start == frame_start:
                strip.select = True
            else:
                if scene.is_filtering_right == True:
                    strip.select = False
        return {'FINISHED'}
    
    
class EndFrameTriggerOperator(bpy.types.Operator):
    bl_idname = "my.end_frame_trigger"
    bl_label = "End Frame Trigger"
    
    def execute(self, context):
        active_strip = bpy.context.scene.sequence_editor.active_strip
        sequence_editor = bpy.context.scene.sequence_editor
        frame_final_end = active_strip.frame_final_end
        scene = bpy.context.scene
        
        for strip in filter_color_strips(sequence_editor.sequences_all):
            if strip.frame_final_end == frame_final_end:
                strip.select = True
            else:
                if scene.is_filtering_right == True:
                    strip.select = False
        return {'FINISHED'}
    

class DurationTriggerOperator(bpy.types.Operator):
    bl_idname = "my.duration_trigger"
    bl_label = "Duration Trigger"
    
    def execute(self, context):
        active_strip = bpy.context.scene.sequence_editor.active_strip
        sequence_editor = bpy.context.scene.sequence_editor
        frame_final_duration = active_strip.frame_final_duration
        scene = bpy.context.scene
        
        for strip in filter_color_strips(sequence_editor.sequences_all):
            if strip.frame_final_duration == frame_final_duration:
                strip.select = True
            else:
                if scene.is_filtering_right == True:
                    strip.select = False
        return {'FINISHED'}
    
    
class StartFrameJumpOperator(bpy.types.Operator):
    bl_idname = "my.start_frame_jump"
    bl_label = "Jump to Start Frame"
    
    def execute(self, context):
        bpy.context.scene.frame_current = int(bpy.context.scene.sequence_editor.active_strip.frame_start)
        return {'FINISHED'}
    
    
class EndFrameJumpOperator(bpy.types.Operator):
    bl_idname = "my.end_frame_jump"
    bl_label = "Jump to End Frame"
    
    def execute(self, context):
        bpy.context.scene.frame_current = int(bpy.context.scene.sequence_editor.active_strip.frame_final_end)
        return {'FINISHED'}


class ExtrudeOperator(bpy.types.Operator):
    bl_idname = "my.alva_extrude"
    bl_label = "Extrude Pattern of 2"
    
    def execute(self, context):
        self.report({'INFO'}, 'Type the "E" key while in sequencer to extrude pattern of 2 strips.')
        return {'FINISHED'}


class ScaleOperator(bpy.types.Operator):
    bl_idname = "my.alva_scale"
    bl_label = "Scale Strip(s)"
    
    def execute(self, context):
        self.report({'INFO'}, 'Type the "S" key while in sequencer to scale strips.')
        return {'FINISHED'}
    
    
class GrabOperator(bpy.types.Operator):
    bl_idname = "my.alva_grab"
    bl_label = "Grab Strip(s)"
    
    def execute(self, context):
        self.report({'INFO'}, 'Type the "G" key while in sequencer to grab and move strips.')
        return {'FINISHED'}
    

class GrabXOperator(bpy.types.Operator):
    bl_idname = "my.alva_grab_x"
    bl_label = "Grab Strip(s) on X"
    
    def execute(self, context):
        self.report({'INFO'}, 'Type the "G" key, then the "X" key while in sequencer to grab and move strips on X axis only.')
        return {'FINISHED'}
    
    
class GrabYOperator(bpy.types.Operator):
    bl_idname = "my.alva_grab_y"
    bl_label = "Grab Strip(s) on Y"
    
    def execute(self, context):
        self.report({'INFO'}, 'Type the "G" key, then the "Y" key while in sequencer to grab and move strips on Y axis only.')
        return {'FINISHED'}
    
    
class CutOperator(bpy.types.Operator):
    bl_idname = "my.cut_operator"
    bl_label = "Cut Strips"
    
    def execute(self, context):
        self.report({'INFO'}, 'Type the "K" key while in sequencer.')
        return {'FINISHED'}


class AddMediaOperator(bpy.types.Operator):
    bl_idname = "my.add_media_operator"
    bl_label = "Add Media"
    
    def execute(self, context):
        self.report({'INFO'}, 'Right-click twice inside the sequencer to add strips such as sound and video.')
        return {'FINISHED'}
    
    
class AssignToChannelOperator(bpy.types.Operator):
    bl_idname = "my.assign_to_channel_operator"
    bl_label = "Assign to Channel"
    
    def execute(self, context):
        self.report({'INFO'}, 'Type the "C" key while in sequencer, then channel number, then "Enter" key.')
        return {'FINISHED'}
    
    
class SetStartFrameOperator(bpy.types.Operator):
    bl_idname = "my.set_start_frame_operator"
    bl_label = "Set Start Frame"
    
    def execute(self, context):
        self.report({'INFO'}, 'Type the "S" key while in Timeline window.')
        return {'FINISHED'}
    
    
class SetEndFrameOperator(bpy.types.Operator):
    bl_idname = "my.set_end_frame_operator"
    bl_label = "Set End Frame"
    
    def execute(self, context):
        self.report({'INFO'}, 'Type the "E" key while in Timeline window.')
        return {'FINISHED'}
    
    
class CopyColorOperator(bpy.types.Operator):
    bl_idname = "my.copy_color_operator"
    bl_label = "Copy color to Selected"
    bl_description = "Copy color to selected strips"

    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip

        if active_strip and active_strip.type == 'COLOR':
            global stop_updating_color
            stop_updating_color = "Yes"
            
            color = active_strip.color

            for strip in filter_color_strips(context.selected_sequences):
                if strip != active_strip:
                    strip.color = color
                        
        stop_updating_color = "No"
                    
        return {'FINISHED'}
    

class CopyStripNameOperator(bpy.types.Operator):
    bl_idname = "my.copy_strip_name_operator"
    bl_label = "Copy strip name to Selected"
    bl_description = "Copy strip name to selected strips"

    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip

        if active_strip and active_strip.type == 'COLOR':
            name = active_strip.name

            for strip in filter_color_strips(context.selected_sequences):
                if strip != active_strip:
                    strip.name = name     
        return {'FINISHED'}
    
    
class CopyChannelOperator(bpy.types.Operator):
    bl_idname = "my.copy_channel_operator"
    bl_label = "Copy channel to Selected"
    bl_description = "Copy channel to selected strips"

    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip

        if active_strip and active_strip.type == 'COLOR':
            channel = active_strip.channel

            for strip in filter_color_strips(context.selected_sequences):
                if strip != active_strip:
                    strip.channel = channel    
        return {'FINISHED'}
    
    
class CopyDurationOperator(bpy.types.Operator):
    bl_idname = "my.copy_duration_operator"
    bl_label = "Copy duration to Selected"
    bl_description = "Copy duration to selected strips"

    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip

        if active_strip and active_strip.type == 'COLOR':
            duration = active_strip.frame_final_duration

            for strip in filter_color_strips(context.selected_sequences):
                if strip != active_strip:
                    strip.frame_final_duration = duration
        return {'FINISHED'}
    
    
class CopyStartFrameOperator(bpy.types.Operator):
    bl_idname = "my.copy_start_frame_operator"
    bl_label = "Copy start frame to Selected"
    bl_description = "Copy start frame to selected strips"

    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip

        if active_strip and active_strip.type == 'COLOR':
            start_frame = active_strip.frame_start

            for strip in filter_color_strips(context.selected_sequences):
                if strip != active_strip:
                    strip.frame_start = start_frame
        return {'FINISHED'}
    
    
class CopyEndFrameOperator(bpy.types.Operator):
    bl_idname = "my.copy_end_frame_operator"
    bl_label = "Copy end frame to Selected"
    bl_description = "Copy end frame to selected strips"

    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip

        if active_strip and active_strip.type == 'COLOR':
            end_frame = active_strip.frame_final_end

            for strip in filter_color_strips(context.selected_sequences):
                if strip != active_strip:
                    strip.frame_final_end = end_frame
        return {'FINISHED'}
    
    
class CopyAboveToSelectedOperator(bpy.types.Operator):
    bl_idname = "my.copy_above_to_selected"
    bl_label = "Copy to Selected"
    bl_description = "Copy some properties of the active strip to all the other selected strips"

    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip

        if active_strip and active_strip.type == 'COLOR':
            global stop_updating_color
            stop_updating_color = "Yes"
            
            name  = active_strip.name
            motif_name = active_strip.motif_name
            color  = active_strip.color
            length = active_strip.frame_final_duration
            enumerator_choice = active_strip.my_settings.motif_type_enum

            intensity_prefix = active_strip.intensity_prefix
            pan_prefix = active_strip.pan_prefix
            tilt_prefix = active_strip.tilt_prefix
            zoom_prefix = active_strip.zoom_prefix
            iris_prefix = active_strip.iris_prefix
            trigger_prefix = active_strip.trigger_prefix
            osc_trigger = active_strip.osc_trigger
            osc_trigger_end = active_strip.osc_trigger_end
            eos_cue_number = active_strip.eos_cue_number
            start_frame_macro = active_strip.start_frame_macro
            end_frame_macro = active_strip.end_frame_macro
            friend_list = active_strip.friend_list
            start_flash = active_strip.start_flash_macro_number
            end_flash = active_strip.end_flash_macro_number
            bias = active_strip.flash_bias
            link_status = active_strip.is_linked
            flash_input = active_strip.flash_input
            flash_down_input = active_strip.flash_down_input

            for strip in filter_color_strips(context.selected_sequences):
                if strip != active_strip:
                    strip.name = name
                    strip.motif_name = motif_name
                    strip.color = color
                    strip.frame_final_duration = length
                    strip.my_settings.motif_type_enum = enumerator_choice

                    strip.intensity_prefix = intensity_prefix
                    strip.pan_prefix = pan_prefix
                    strip.tilt_prefix = tilt_prefix
                    strip.zoom_prefix = zoom_prefix
                    strip.iris_prefix = iris_prefix
                    strip.trigger_prefix = trigger_prefix
                    strip.osc_trigger = osc_trigger
                    strip.osc_trigger_end = osc_trigger_end
                    strip.eos_cue_number = eos_cue_number
                    strip.start_frame_macro = start_frame_macro
                    strip.end_frame_macro = end_frame_macro
                    strip.friend_list = friend_list
                    strip.start_flash_macro_number = start_flash
                    strip.end_flash_macro_number = end_flash
                    strip.flash_bias = bias
                    strip.flash_input = flash_input
                    strip.flash_down_input = flash_down_input
                    
                    if link_status == True:
                        strip.is_linked = True
                    else:
                        strip.is_linked = False
                        
        stop_updating_color = "No"
                    
        return {'FINISHED'}
     

def create_motif_strip(context, motif_type_enum):
    def find_available_channel(sequence_editor, start_frame, end_frame, preferred_channel):
        channels = {strip.channel for strip in sequence_editor.sequences_all
                    if strip.frame_final_start < end_frame and strip.frame_final_end > start_frame}
        current_channel = preferred_channel
        while current_channel in channels:
            current_channel += 1
        return current_channel

    current_frame = context.scene.frame_current
    sequence_editor = context.scene.sequence_editor
    channel = sequence_editor.active_strip.channel if sequence_editor.active_strip else 1
    frame_end = current_frame + 25

    channel = find_available_channel(sequence_editor, current_frame, frame_end, channel)

    color_strip = sequence_editor.sequences.new_effect(
        name="New Strip",
        type='COLOR',
        channel=channel,
        frame_start=current_frame,
        frame_end=frame_end)
    if motif_type_enum == "option_eos_macro":
        color_strip.color = (1, 0, 0)
    elif motif_type_enum == "option_eos_cue":
        color_strip.color = (0, 0, .5)
    elif motif_type_enum == "option_eos_flash":
        color_strip.color = (1, 1, 0)
    elif motif_type_enum == "option_animation":
        color_strip.color = (0, 1, 0)
    else:
        color_strip.color = (1, 1, 1)
    for strip in sequence_editor.sequences_all:
        strip.select = False

    color_strip.select = True
    context.scene.sequence_editor.active_strip = color_strip
    color_strip.my_settings.motif_type_enum = motif_type_enum

    return {'FINISHED'}


class AddMacroOperator(bpy.types.Operator):
    bl_idname = "my.add_macro"
    bl_label = "Macro"
    bl_description = "Add macro strip. Type in macro syntax you know letter by letter and type * for strip length"
    
    def execute(self, context):
        return create_motif_strip(context, "option_eos_macro")
        
        
class AddCueOperator(bpy.types.Operator):
    bl_idname = "my.add_cue"
    bl_label = "Cue"
    bl_description = "Add cue strip. Strip length will become the cues fade in time"
    
    def execute(self, context):
        return create_motif_strip(context, "option_eos_cue")
    
    
class AddFlashOperator(bpy.types.Operator):
    bl_idname = "my.add_flash"
    bl_label = "Flash"
    bl_description = "Add flash strip. Flash strips are really fast for making lights flash up then down with no effort"
    
    def execute(self, context):
        return create_motif_strip(context, "option_eos_flash")
    
    
class AddAnimationOperator(bpy.types.Operator):
    bl_idname = "my.add_animation"
    bl_label = "Animation"
    bl_description = "Add animation strip. Use Blender's sophisticated animation tools such as Graph Editor, Dope Sheet, Motion Tracking, and NLA Editor to create effects that are impossible to create anywhere else. Then, output a qmeo deliverable to the console for local playback"
    
    def execute(self, context):
        return create_motif_strip(context, "option_animation")
    
    
class AddTriggerOperator(bpy.types.Operator):
    bl_idname = "my.add_trigger"
    bl_label = "Trigger"
    bl_description = "Add trigger strip. Use this to send arbitrary OSC strings on start and end frame with fully custom address/argument. Or, experiment with creating advanced offset effects with plain english"
    
    def execute(self, context):
        return create_motif_strip(context, "option_trigger")
    
    
class RemoveMotifOperator(bpy.types.Operator):
    bl_idname = "my.remove_motif"
    bl_label = ""
    bl_description = "Remove Motif"
    
    def execute(self, context):
        # Why does this do nothing?
        return {'FINISHED'}
    

class PlayOperator(bpy.types.Operator):
    bl_idname = "my.play_operator"
    bl_label = ""
    bl_description = "Hits play on the sequencer"
    
    def execute(self, context):
        bpy.ops.screen.animation_play()
        return {'FINISHED'}
    

class StopOperator(bpy.types.Operator):
    bl_idname = "my.stop_operator"
    bl_label = ""
    bl_description = "Hits stop on the sequencer and resets to the original frame from before, which you would use if you're refining a specific area repeatedly and don't want to manually scrib backward every time"
    
    def execute(self, context):
        bpy.ops.screen.animation_cancel(restore_frame=True)
        return {'FINISHED'}
    
    
class DeleteOperator(bpy.types.Operator):
    bl_idname = "my.delete_operator"
    bl_label = "Delete"
    bl_description = "No confirmation will be asked for"
    
    def execute(self, context):
        bpy.ops.sequencer.delete()
        return {'FINISHED'}


class SaveOperator(bpy.types.Operator):
    bl_idname = "my.save_operator"
    bl_label = "Save"
    bl_description = "Saves both the Blender file and the console file"
    
    def execute(self, context):
        bpy.ops.wm.save_mainfile()
        ip_address = context.scene.scene_props.str_osc_ip_address
        port = context.scene.scene_props.int_osc_port
        send_osc_string("/eos/key/shift", ip_address, port, "1")
        send_osc_string("/eos/key/update", ip_address, port, "1")
        send_osc_string("/eos/key/shift", ip_address, port, "0")
        return {'FINISHED'}
    
    
class AddStripOperator(bpy.types.Operator):
    bl_idname = "my.add_strip_operator"
    bl_label = "Add Strip"
    bl_description = "Adds a duplicate strip above current strip"
    
    def execute(self, context):
        scene = context.scene

        if hasattr(scene, "sequence_editor") and scene.sequence_editor:
            sequences = scene.sequence_editor.sequences_all
            selected_sequences = [seq for seq in sequences if seq.select]
            if len(selected_sequences) == 1:
                active_strip = selected_sequences[0]
                bpy.ops.sequencer.duplicate()
                sequences = scene.sequence_editor.sequences_all
                duplicated_strips = [seq for seq in sequences if seq.select and seq != active_strip]
                for new_strip in duplicated_strips:
                    new_strip.channel = max(seq.channel for seq in sequences) + 1
                    
                replacement_value = scene.replacement_value
                if replacement_value:
                    parts = replacement_value.split('/')
                    if len(parts) == 2 and parts[1].isdigit():
                        incremented_value = int(parts[1]) + 1
                        scene.replacement_value = parts[0] + '/' + str(incremented_value)
                        replacement_value_updater(scene, context)
            else:
                self.report({'WARNING'}, "Please select exactly one strip.")
                return {'CANCELLED'}
        else:
            self.report({'WARNING'}, "Sequence editor is not active or available.")
            return {'CANCELLED'}

        return {'FINISHED'}
  
    
class ScriptingOperator(bpy.types.Operator):
    bl_idname = "my.scripting_operator"
    bl_label = "3D View"
    
    def execute(self, context):
        bpy.context.window.screen = bpy.data.screens['Default'] # Toggled to 3D view after development wrapped up
        return {'FINISHED'}
    

class SequencerOperator(bpy.types.Operator):
    bl_idname = "my.sequencer_operator"
    bl_label = "Video Editor"
    
    def execute(self, context):
        bpy.context.window.screen = bpy.data.screens['Video Editing']
        return {'FINISHED'}
    

class GoToCueOutOperator(bpy.types.Operator):
    bl_idname = "my.go_to_cue_out_operator"
    bl_label = "Ghost out"
    bl_description = "Presses Go_to Cue Out on the console"
    
    def execute(self, context):
        ip_address = context.scene.scene_props.str_osc_ip_address
        port = context.scene.scene_props.int_osc_port
        send_osc_string("/eos/newcmd", ip_address, port, "Go_to_Cue Out Enter")
        return {'FINISHED'}
    
    
class DisplaysOperator(bpy.types.Operator):
    bl_idname = "my.displays_operator"
    bl_label = "Displays"
    bl_description = "Presses Displays on the console"
    
    def execute(self, context):
        ip_address = context.scene.scene_props.str_osc_ip_address
        port = context.scene.scene_props.int_osc_port
        send_osc_string("/eos/key/displays", ip_address, port, "1")
        send_osc_string("/eos/key/displays", ip_address, port, "0")
        return {'FINISHED'}
    
    
class AboutOperator(bpy.types.Operator):
    bl_idname = "my.about_operator"
    bl_label = "About"
    bl_description = "Presses About on the console"
    
    def execute(self, context):
        ip_address = context.scene.scene_props.str_osc_ip_address
        port = context.scene.scene_props.int_osc_port
        send_osc_string("/eos/key/about", ip_address, port, "0")
        # How come this button appears to be the only button that responds to a 0 for a trigger event and not 1?
        # Edit: probably because this older code doesn't use 1 then 0 for press down and then release.
        return {'FINISHED'}
    

# Inop.
class RecordOperator(bpy.types.Operator):
    bl_idname = "my.record_operator"
    bl_label = "Record"
    bl_description = ""
    
    def execute(self, context):
        ip_address = context.scene.scene_props.str_osc_ip_address
        port = context.scene.scene_props.int_osc_port
        address = "/eos/key/record"
        argument = "1"
        send_osc_string(address, ip_address, port, argument)
        #This one and many others behave as expected after reading the documentation
        return {'FINISHED'}


class DisableAllClocksOperator(bpy.types.Operator):
    bl_idname = "my.disable_all_clocks_operator"
    bl_label = "Disable All Clocks"
    bl_description = "Disables all timecode clocks in ETC Eos"
    
    def execute(self, context):
        ip_address = context.scene.scene_props.str_osc_ip_address
        port = context.scene.scene_props.int_osc_port
        clock_number = 1
        
        while clock_number <= 100:
            send_osc_string("/eos/newcmd", ip_address, port, f"Event {str(clock_number)} / Internal Disable Enter")
            clock_number += 1
            
        return {'FINISHED'}
    
    
## This button needs to be completely redone.
class ColorPaletteOperator(bpy.types.Operator):
    bl_idname = "my.color_palette_operator"
    bl_label = ""
    bl_description = "Record color palette for all channels on console"
    
    def execute(self, context):
        
        ip_address = context.scene.scene_props.str_osc_ip_address
        port = context.scene.scene_props.int_osc_port
        scene = bpy.context.scene
        cp_number = scene.color_palette_number
        cp_red = scene.color_palette_color[0]
        cp_green = scene.color_palette_color[1]
        cp_blue = scene.color_palette_color[2]
        cp_label = scene.color_palette_name
        newcmd = "/eos/newcmd"
        live = "/eos/key/live"
        enter = "/eos/key/enter"
        down = "1"
        up = "0"
        
        cp_red = round(cp_red * 100, 1)
        cp_green = round(cp_green * 100, 1)
        cp_blue = round(cp_blue * 100, 1)
        
        send_osc_string(live, ip_address, port, down)
        send_osc_string(live, ip_address, port, up)
        
        time.sleep(.3)
        
        argument = "Chan 1 thru thru 1000 Red " + str(cp_red) + " Enter"
        send_osc_string(newcmd, ip_address, port, argument)
        
        time.sleep(.3)
        
        argument = "Chan 1 thru thru 1000 Green " + str(cp_green) + " Enter"
        send_osc_string(newcmd, ip_address, port, argument)
        
        time.sleep(.3)
        
        argument = "Chan 1 thru thru 1000 Blue " + str(cp_blue) + " Enter"
        send_osc_string(newcmd, ip_address, port, argument)
        
        time.sleep(.3)
        
        argument = "Chan 1 thru thru 1000 Amber 0 Enter"
        send_osc_string(newcmd, ip_address, port, argument)
        
        time.sleep(.3)
        
        argument = "Chan 1 thru thru 1000 Mint 0 Enter"
        send_osc_string(newcmd, ip_address, port, argument)
        
        time.sleep(.3)
        
        if cp_red + cp_green + cp_blue != 300:
            argument = "Chan 1 thru thru 1000 White 0 Enter"
            send_osc_string(newcmd, ip_address, port, argument)
        else: 
            argument = "Chan 1 thru thru 1000 White 100 Enter"
            send_osc_string(newcmd, ip_address, port, argument)
        
        time.sleep(.3)
        
        argument = "Chan 1 thru thru 1000 Record Color_Palette " + str(cp_number) + " Enter Enter"
        send_osc_string(newcmd, ip_address, port, argument)
        
        time.sleep(.3)
        
        argument = "Color_Palette " + str(cp_number) + " Label " + str(cp_label)
        send_osc_string(newcmd, ip_address, port, argument)
        
        time.sleep(.3)
        
        send_osc_string(enter, ip_address, port, down)
        send_osc_string(enter, ip_address, port, up)
        
        self.report({'INFO'}, "Orb complete.")
        
        if scene.reset_color_palette:
            scene.color_palette_number += 1
            scene.color_palette_name = ""
            
        snapshot = str(context.scene.orb_finish_snapshot)
        send_osc_string("/eos/newcmd", ip_address, port, f"Snapshot {snapshot} Enter")
        
        return {'FINISHED'}


class DeleteAnimationCueListOperator(bpy.types.Operator):
    bl_idname = "my.delete_animation_cue_list_operator"
    bl_label = ""
    bl_description = "Delete cue list"
    
    def execute(self, context):
        scene = bpy.context.scene
        context = bpy.context
        active_strip = context.scene.sequence_editor.active_strip
        ip_address = bpy.context.scene.scene_props.str_osc_ip_address
        port = bpy.context.scene.scene_props.int_osc_port
        cue_list = active_strip.animation_cue_list_number
        address = "/eos/key/live"
        down = "1"
        up = "0"
        send_osc_string(address, ip_address, port, down)
        send_osc_string(address, ip_address, port, up)
        
        time.sleep(.2)
        
        address = "/eos/newcmd"
        argument = "Delete Cue " + str(cue_list) + " / Enter"
        send_osc_string(address, ip_address, port, argument)
        return {'FINISHED'}
        
        
class DeleteAnimationEventListOperator(bpy.types.Operator):
    bl_idname = "my.delete_animation_event_list_operator"
    bl_label = ""
    bl_description = "Delete event list"
    
    def execute(self, context):
        scene = bpy.context.scene
        context = bpy.context
        active_strip = context.scene.sequence_editor.active_strip 
        ip_address = bpy.context.scene.scene_props.str_osc_ip_address
        port = bpy.context.scene.scene_props.int_osc_port
        event_list = active_strip.animation_event_list_number
        address = "/eos/key/live"
        down = "1"
        up = "0"
        send_osc_string(address, ip_address, port, down)
        send_osc_string(address, ip_address, port, up)
        
        time.sleep(.2)
        
        address = "/eos/newcmd"
        argument = "Delete Event " + str(event_list) + " / Enter"
        send_osc_string(address, ip_address, port, argument)
        return {'FINISHED'}
    
    
class StopAnimationClockOperator(bpy.types.Operator):
    bl_idname = "my.stop_animation_clock_operator"
    bl_label = ""
    bl_description = "Stop animation clock"
    
    def execute(self, context):
        scene = bpy.context.scene
        context = bpy.context
        active_strip = context.scene.sequence_editor.active_strip
        ip_address = bpy.context.scene.scene_props.str_osc_ip_address
        port = bpy.context.scene.scene_props.int_osc_port
        cue_list = active_strip.animation_cue_list_number
        address = "/eos/newcmd"
        argument = "Event " + str(active_strip.animation_event_list_number) + " / Internal Disable Enter"
        send_osc_string(address, ip_address, port, argument)
        return {'FINISHED'}


class BakeFCurvesToCuesOperator(bpy.types.Operator):
    bl_idname = "my.bake_fcurves_to_cues_operator"
    bl_label = "Bake F-curves To Cues"
    bl_description = "Orb will create a qmeo. A qmeo is like a video, only each frame is a lighting cue. Use it to store complex animation data on the lighting console" 

    def frame_to_timecode(self, frame, fps=None):
        """Convert frame number to timecode format."""
        scene = bpy.context.scene
        context = bpy.context
        active_strip = context.scene.sequence_editor.active_strip
        frame_rate = get_frame_rate(scene)
        start_frame = active_strip.frame_start
        end_frame = active_strip.frame_final_end  
        ip_address = bpy.context.scene.scene_props.str_osc_ip_address
        port = bpy.context.scene.scene_props.int_osc_port
        current_frame_number = scene.frame_current
        cue_duration = 1 / frame_rate
        cue_duration = round(cue_duration, 2)
        event_list_number = active_strip.animation_event_list_number
        fps = frame_rate
        
        hours = int(frame // (fps * 3600))
        minutes = int((frame % (fps * 3600)) // (fps * 60))
        seconds = int((frame % (fps * 60)) // fps)
        frames = int(frame % fps)  # No rounding needed for non-drop frame

        return "{:02}:{:02}:{:02}:{:02}".format(hours, minutes, seconds, frames)
    
    def execute(self, context):
        scene = context.scene
        active_strip = context.scene.sequence_editor.active_strip
        frame_rate = get_frame_rate(scene)
        start_frame = active_strip.frame_start
        end_frame = active_strip.frame_final_end  
        ip_address = scene.scene_props.str_osc_ip_address
        port = scene.scene_props.int_osc_port
        current_frame_number = scene.frame_current
        cue_duration = 1 / frame_rate
        cue_duration = round(cue_duration, 2)
        event_list_number = active_strip.animation_event_list_number
        
        newcmd = "/eos/newcmd"
        softkey_2 = "/eos/softkey/2"
        zero = "/eos/key/0"
        enter = "/eos/key/enter"
        go = "/eos/key/go"
        event = "/eos/key/event"
        
        down = "1"
        up = "0"

        # Create a sorted list of frames
        start_frame = int(start_frame)
        end_frame = int(end_frame)
        frames = list(range(start_frame, end_frame))

        # Iterate through the frames and perform operations
        for frame in frames:
            context.scene.frame_set(frame)
            depsgraph = context.evaluated_depsgraph_get()  # Get the dependency graph
            context.view_layer.update()
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
            
            current_frame_number = scene.frame_current
            
            # Record cue
            argument = "Record " + str(active_strip.animation_cue_list_number) + " / " + str(current_frame_number) + " Enter Enter"
            send_osc_string(newcmd, ip_address, port, argument)
            time.sleep(.1)
        
        time.sleep(.5)
            
        # Enter and execute command to set duration for all new cues
        argument = "Cue " + str(active_strip.animation_cue_list_number) + " / " + str(start_frame) + " thru " + str(end_frame) + " Time " + str(cue_duration) + " Enter "
        send_osc_string(newcmd, ip_address, port, argument)
        
        time.sleep(.5)
        
        # Set up timecode clock to fire the cues
        argument = "Event " + str(event_list_number) + " / " + str(start_frame) + " thru " + str(end_frame) + " Enter"
        send_osc_string(newcmd, ip_address, port, argument)
        
        time.sleep(.3)
        
        # Create all events to help with organization
        argument = "Event " + str(active_strip.animation_event_list_number) + " / " + str(start_frame) + " thru " + str(end_frame) + " Enter"
        send_osc_string(newcmd, ip_address, port, argument)
        
        time.sleep(.3)
        
        for frame in frames:         
            # Record all cues
            bpy.context.scene.frame_set(frame)
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
            
            time.sleep(.1)
            current_frame_number = scene.frame_current
            
            timecode = self.frame_to_timecode(frame)
            
            argument = "Event " + str(active_strip.animation_event_list_number) + " / " + str(current_frame_number) + " Time " + str(timecode) + " Show_Control_Action Cue " + str(frame) + " Enter"
            send_osc_string(newcmd, ip_address, port, argument)
            
            time.sleep(.3)
            
        snapshot = str(context.scene.orb_finish_snapshot)
        send_osc_string("/eos/newcmd", ip_address, port, f"Snapshot {snapshot} Enter")
            
        self.report({'INFO'}, "Orb complete.")
        
        return {'FINISHED'}
 
 
class RerecordCuesOperator(bpy.types.Operator):
    bl_idname = "my.rerecord_cues_operator"
    bl_label = "Re-record Cues"
    bl_description = "Orb will re-record the cues. Use this instead of the left button if you already used that button, updated the animation without changing its length, and just want to re-record the existing cues. This is far shorter" 
    
    def execute(self, context):
        scene = context.scene
        active_strip = scene.sequence_editor.active_strip
        frame_rate = get_frame_rate(scene)
        start_frame = active_strip.frame_start
        end_frame = active_strip.frame_final_end  
        ip_address = scene.scene_props.str_osc_ip_address
        port = scene.scene_props.int_osc_port
        current_frame_number = scene.frame_current
        cue_duration = 1 / frame_rate
        cue_duration = round(cue_duration, 2)
        event_list_number = active_strip.animation_event_list_number
        
        newcmd = "/eos/newcmd"
        softkey_2 = "/eos/softkey/2"
        zero = "/eos/key/0"
        enter = "/eos/key/enter"
        go = "/eos/key/go"
        event = "/eos/key/event"
        
        down = "1"
        up = "0"

        # Create a sorted list of frames
        start_frame = int(start_frame)
        end_frame = int(end_frame)
        frames = list(range(start_frame, end_frame))

        # Iterate through the frames and perform operations
        for frame in frames:
            scene.frame_set(frame)
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

            current_frame_number = scene.frame_current
            
            # Record all cues
            argument = "Record " + str(active_strip.animation_cue_list_number) + " / " + str(current_frame_number) + " Enter Enter"
            send_osc_string(newcmd, ip_address, port, argument)
            time.sleep(1.2)
        
        time.sleep(.5)
            
        # Enter and execute command to set duration for all new cues
        argument = "Cue " + str(active_strip.animation_cue_list_number) + " / " + str(start_frame) + " thru " + str(end_frame) + " Time " + str(cue_duration) + " Enter "
        send_osc_string(newcmd, ip_address, port, argument)
        
        snapshot = str(context.scene.orb_finish_snapshot)
        send_osc_string("/eos/newcmd", ip_address, port, f"Snapshot {snapshot} Enter")

        self.report({'INFO'}, "Orb complete.")
        
        return {'FINISHED'}
 
 
class GenerateTextOperator(bpy.types.Operator):
    bl_idname = "my.generate_text"
    bl_label = "CIA > Import > USITT ASCII"
    bl_description = "Save event list into a .txt file for USITT ASCII import into Eos. Then, save as .esf3d console file. Then open up the main show file and merge the Show Control from the newly created .esf3d console file"
    
    def frame_to_timecode(self, frame, fps=None):
        context = bpy.context
        scene = context.scene
        """Convert frame number to timecode format."""
        if fps is None:
            fps = get_frame_rate(scene)
        hours = int(frame // (fps * 3600))
        frame %= fps * 3600
        minutes = int(frame // (fps * 60))
        frame %= fps * 60
        seconds = int(frame // fps)
        frames = int(round(frame % fps))
        return "{:02}:{:02}:{:02}:{:02}".format(hours, minutes, seconds, frames)

    
    def execute(self, context):
        scene = context.scene
        song_timecode_clock_number = context.scene.sequence_editor.active_strip.song_timecode_clock_number
        seq_start = context.scene.frame_start
        seq_end = context.scene.frame_end
        active_strip = context.scene.sequence_editor.active_strip
        frames_per_second = get_frame_rate(scene)
        
        #Determines if song strip starts at frame 1 and if not, by what positive or negative amount
        if active_strip.frame_start > 1:
            slide_factor = active_strip.frame_start - 1
        elif active_strip.frame_start < 1:
            slide_factor = 1 - active_strip.frame_start
        else:
            slide_factor = 0
            
        text_block = bpy.data.texts.new(name="Generated Show File.txt")
        
        text_block.write("""Ident 3:0
Manufacturer ETC
Console Eos
$$Format 3.20
$$Software Version 3.2.2 Build 25  Fixture Library 3.2.0.75, 26.Apr.2023
 
 
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
! Show Control Event Lists
! A Show Control event list may be one of the following types:
!     SMPTE Time Code, MIDI Time Code, Real Time Clock, Analog, Network
! 
! SMPTE/MIDI Time Code Event List
! Time stamp format is hh:mm:ss:ff (h=hour, m=minute, s=second, f=frame)
! $SCList:      List number, List type (1=MIDI, 2=SMPTE)
!               All following time code messages are in this time code list
! 
!     $$FirstFrame, $$LastFrame, $$FramesPerSecond(24, 25 or 30)
!                   (first frame and last frame are used for running the events
!                   on an internal clock or with an internal clock backup)
!     $$Source      Source device id, default=1
!     $$Internal    Internal Clock enabled
!     $$External    External Clock enabled
!     $$Silent      Silent Mode enabled
! 
! Individual Time Code Events
!   $TimeCode time stamp
!     $$SCData:   Type (E=Empty, C=Cue, M=Macro, S=Submaster),
!                   if Cue then cuelist/name
!                   if Sub then mode Off/On/Bump or F=Subfader
!                   if Macro then macro number


""")

        text_block.write("$SCList " + str(active_strip.song_timecode_clock_number) + " 2\n")
        text_block.write("$$FirstFrame  00:00:00:00\n")
        text_block.write("$$LastFrame  23:59:59:00\n")
        text_block.write("$$FramesPerSecond " + str(frames_per_second) + "\n")
        text_block.write("\n")
        text_block.write("\n")
        text_block.write("\n")
        text_block.write("\n")

        for strip in context.scene.sequence_editor.sequences:
            if strip.type == "COLOR" and strip.my_settings.motif_type_enum == 'option_eos_cue' and seq_start <= strip.frame_start <= seq_end and not strip.mute:
                eos_cue_number = strip.eos_cue_number
                strip_name = strip.name
                start_frame = strip.frame_start - slide_factor
                if eos_cue_number:         
                    text_block.write("$Timecode  " + self.frame_to_timecode(start_frame) + "\n")
                    text_block.write("Text " + strip_name + "\n")
                    text_block.write("$$SCData C 1/" + str(eos_cue_number) + "\n")
                    text_block.write("\n")
                    text_block.write("\n")

            # Check if it's a color strip and lies within sequencer's start and end frame and is a macro strip
            if strip.type == "COLOR" and strip.my_settings.motif_type_enum == 'option_eos_macro' and seq_start <= strip.frame_start <= seq_end and not strip.mute:
                start_macro_number = strip.start_frame_macro
                end_macro_number = strip.end_frame_macro
                strip_name = strip.name
                start_frame = strip.frame_start - slide_factor
                end_frame = strip.frame_final_end - slide_factor
                if start_macro_number != 0 and not strip.start_macro_muted:         
                    text_block.write("$Timecode  " + self.frame_to_timecode(start_frame) + "\n")
                    text_block.write("Text " + strip_name + " (Start Macro)" + "\n")
                    text_block.write("$$SCData M " + str(start_macro_number) + "\n")  
                    text_block.write("\n")
                    text_block.write("\n")
                if end_macro_number != 0 and not strip.end_macro_muted:         
                    text_block.write("$Timecode  " + self.frame_to_timecode(end_frame) + "\n")
                    text_block.write("Text " + strip_name + " (End Macro)" + "\n")
                    text_block.write("$$SCData M " + str(end_macro_number) + "\n")    
                    text_block.write("\n")
                    text_block.write("\n")
                    
            if strip.type == "COLOR" and strip.my_settings.motif_type_enum == 'option_eos_flash' and seq_start <= strip.frame_start <= seq_end and not strip.mute:
                start_flash_macro_number = strip.start_flash_macro_number
                end_flash_macro_number = strip.end_flash_macro_number
                strip_name = strip.name
                start_frame = strip.frame_start - slide_factor
                end_frame = strip.frame_final_end
                bias = strip.flash_bias
                frame_rate = get_frame_rate(scene)
                strip_length_in_frames = strip.frame_final_duration
                bias_in_frames = calculate_bias_offseter(bias, frame_rate, strip_length_in_frames)
                start_frame = strip.frame_start - slide_factor
                end_flash_macro_frame = start_frame + bias_in_frames
                end_flash_macro_frame = int(round(end_flash_macro_frame))
                end_frame = end_flash_macro_frame

                # If only the start flash macro is provided
                if start_flash_macro_number != 0:         
                    text_block.write("$Timecode  " + self.frame_to_timecode(start_frame) + "\n")
                    text_block.write("Text " + strip_name + " (Flash Up)" + "\n")
                    text_block.write("$$SCData M " + str(start_flash_macro_number) + "\n")  
                    text_block.write("\n")
                    text_block.write("\n")
                if end_flash_macro_number != 0:         
                    text_block.write("$Timecode  " + self.frame_to_timecode(end_frame) + "\n")
                    text_block.write("Text " + strip_name + " (Flash Down)" + "\n")
                    text_block.write("$$SCData M " + str(end_flash_macro_number) + "\n")    
                    text_block.write("\n")
                    text_block.write("\n")
                    
        for area in bpy.context.screen.areas:
            if area.type == 'SEQUENCE_EDITOR':
                area.type = 'TEXT_EDITOR'
                break
            
        bpy.context.space_data.text = text_block

        self.report({'INFO'}, "ASCII created successfully!")
        
        return {'FINISHED'}
    
    
def get_motif_name_items(self, context):
    unique_names = set()

    sequences = context.scene.sequence_editor.sequences_all
    for seq in sequences:
        if hasattr(seq, 'motif_name'):
            unique_names.add(seq.motif_name)
    items = [(name, name, "") for name in sorted(unique_names)]
    return items
    
    
class ImportUsittAsciiOperator(bpy.types.Operator):
    bl_idname = "my.import_usitt_ascii_operator"
    bl_label = "Import USITT ASCII"
    
    def execute(self, context):
        for area in bpy.context.screen.areas:
            if area.type == 'SEQUENCE_EDITOR':
                area.type = 'TEXT_EDITOR'
                break
        
        return {'FINISHED'}
    
    
class UpdateBuilderOperator(bpy.types.Operator):
    bl_idname = "my.update_builder"
    bl_label = "Update builder"
    bl_description = "Send all builder settings to console."
    
    def execute(self, context):
        scene = context.scene
        active_strip = scene.sequence_editor.active_strip
        
        active_strip.key_light = active_strip.key_light
        active_strip.rim_light = active_strip.rim_light
        active_strip.fill_light = active_strip.fill_light
        active_strip.background_light_one = active_strip.background_light_one
        active_strip.background_light_two = active_strip.background_light_two
        active_strip.background_light_three = active_strip.background_light_three
        active_strip.background_light_four = active_strip.background_light_four
        active_strip.texture_light = active_strip.texture_light
        active_strip.band_light = active_strip.band_light
        active_strip.accent_light = active_strip.accent_light
        active_strip.energy_light = active_strip.energy_light
        active_strip.energy_speed = active_strip.energy_speed
        active_strip.energy_scale = active_strip.energy_scale
        
        return {'FINISHED'}
    
    
class RecordCueOperator(bpy.types.Operator):
    bl_idname = "my.record_cue"
    bl_label = "Record cue"
    bl_description = "Record the cue on the console as is."
    
    def execute(self, context):
        scene = context.scene
        active_strip = scene.sequence_editor.active_strip
        address = "/eos/newcmd"
        argument = "Record Cue " + active_strip.eos_cue_number + " Enter"
        ip_address = scene.scene_props.str_osc_ip_address
        port = scene.scene_props.int_osc_port
        send_osc_string(address, ip_address, port, argument)
        return {'FINISHED'}
    
    
def send_cue_builder_group_command(id, group_type, recording, context):
    scene = context.scene
    active_strip = scene.sequence_editor.active_strip
    groups = parse_builder_groups(getattr(scene, "{}_light_groups".format(group_type)))

    if not recording:
        command_suffix = "Preset " + str(id + scene.cue_builder_id_offset) + " Enter"
    else:
        command_suffix = "Record Preset " + str(id + scene.cue_builder_id_offset) + " Enter Enter"

    address = "/eos/newcmd"
    argument_parts = ["Group " + str(group) + " " + command_suffix for group in groups]
    argument = " + ".join(argument_parts)
    ip_address = scene.scene_props.str_osc_ip_address
    port = scene.scene_props.int_osc_port
    send_osc_string(address, ip_address, port, argument)
    
    
class FocusOneOperator(bpy.types.Operator):
    bl_idname = "my.focus_one"
    bl_label = "Focus Palette 1"
    bl_description = "Set to Preset 1, possibly for general look."
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(1, 'key', active_strip.key_is_recording, context)
        return {'FINISHED'}
    
    
class FocusTwoOperator(bpy.types.Operator):
    bl_idname = "my.focus_two"
    bl_label = "Focus Palette 2"
    bl_description = "Set to Preset 2, possibly for side lighting."
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(2, 'key', active_strip.key_is_recording, context)
        return {'FINISHED'}
    
    
class FocusThreeOperator(bpy.types.Operator):
    bl_idname = "my.focus_three"
    bl_label = "Focus Palette 3"
    bl_description = "Set to Preset 3, possibly for paramount lighting."
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(3, 'key', active_strip.key_is_recording, context)
        return {'FINISHED'}
    
    
class FocusFourOperator(bpy.types.Operator):
    bl_idname = "my.focus_four"
    bl_label = "Focus Palette 4"
    bl_description = "Set to Preset 4, possibly for McCandless lighting."
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(4, 'key', active_strip.key_is_recording, context)
        return {'FINISHED'}
    
    
class FocusRimOneOperator(bpy.types.Operator):
    bl_idname = "my.focus_rim_one"
    bl_label = "Focus Palette 1"
    bl_description = "Set to Preset 1, possibly for wide wash"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(1, 'rim', active_strip.rim_is_recording, context)
        return {'FINISHED'}
    
    
class FocusRimTwoOperator(bpy.types.Operator):
    bl_idname = "my.focus_rim_two"
    bl_label = "Focus Palette 2"
    bl_description = "Set to Preset 2, SR wash"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(2, 'rim', active_strip.rim_is_recording, context)
        return {'FINISHED'}
    
    
class FocusRimThreeOperator(bpy.types.Operator):
    bl_idname = "my.focus_rim_three"
    bl_label = "Focus Palette 3"
    bl_description = "Set to Preset 3, possibly for SL wash"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(3, 'rim', active_strip.rim_is_recording, context)
        return {'FINISHED'}
    
    
class FocusRimFourOperator(bpy.types.Operator):
    bl_idname = "my.focus_rim_four"
    bl_label = "Focus Palette 4"
    bl_description = "Set to Preset 4, possibly for CS"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(4, 'rim', active_strip.rim_is_recording, context)
        return {'FINISHED'}
    
    
class FocusFillOneOperator(bpy.types.Operator):
    bl_idname = "my.focus_fill_one"
    bl_label = "Focus Palette 1"
    bl_description = "Set to focus palette one"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(1, 'fill', active_strip.fill_is_recording, context)
        return {'FINISHED'}
    
    
class FocusFillTwoOperator(bpy.types.Operator):
    bl_idname = "my.focus_fill_two"
    bl_label = "Focus Palette 2"
    bl_description = "Set to focus palette two"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(2, 'fill', active_strip.fill_is_recording, context)
        return {'FINISHED'}
    
    
class FocusFillThreeOperator(bpy.types.Operator):
    bl_idname = "my.focus_fill_three"
    bl_label = "Focus Palette 3"
    bl_description = "Set to focus palette three"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(3, 'fill', active_strip.fill_is_recording, context)
        return {'FINISHED'}
    
    
class FocusFillFourOperator(bpy.types.Operator):
    bl_idname = "my.focus_fill_four"
    bl_label = "Focus Palette 4"
    bl_description = "Set to focus palette four"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(4, 'fill', active_strip.fill_is_recording, context)
        return {'FINISHED'}
    
    
class FocusTextureOneOperator(bpy.types.Operator):
    bl_idname = "my.focus_texture_one"
    bl_label = "Focus Palette 1"
    bl_description = "Set to Preset 1"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(1, 'texture', active_strip.texture_is_recording, context)
        return {'FINISHED'}
    
    
class FocusTextureTwoOperator(bpy.types.Operator):
    bl_idname = "my.focus_texture_two"
    bl_label = "Preset 2"
    bl_description = "Set to Preset 2"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(2, 'texture', active_strip.texture_is_recording, context)
        return {'FINISHED'}
    
    
class FocusTextureThreeOperator(bpy.types.Operator):
    bl_idname = "my.focus_texture_three"
    bl_label = "Preset 3"
    bl_description = "Set to Preset 3"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(3, 'texture', active_strip.texture_is_recording, context)
        return {'FINISHED'}
    
    
class FocusTextureFourOperator(bpy.types.Operator):
    bl_idname = "my.focus_texture_four"
    bl_label = "Preset 4"
    bl_description = "Set to Preset 4"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(4, 'texture', active_strip.texture_is_recording, context)
        return {'FINISHED'}
    
    
class FocusTextureFiveOperator(bpy.types.Operator):
    bl_idname = "my.focus_texture_five"
    bl_label = "Focus Palette 5"
    bl_description = "Set to Preset 5"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(5, 'texture', active_strip.texture_is_recording, context)
        return {'FINISHED'}
    
    
class FocusTextureSixOperator(bpy.types.Operator):
    bl_idname = "my.focus_texture_six"
    bl_label = "Preset 6"
    bl_description = "Set to Preset 6"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(6, 'texture', active_strip.texture_is_recording, context)
        return {'FINISHED'}
    
    
class FocusTextureSevenOperator(bpy.types.Operator):
    bl_idname = "my.focus_texture_seven"
    bl_label = "Preset 7"
    bl_description = "Set to Preset 7"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(7, 'texture', active_strip.texture_is_recording, context)
        return {'FINISHED'}
    
    
class FocusTextureEightOperator(bpy.types.Operator):
    bl_idname = "my.focus_texture_eight"
    bl_label = "Preset 8"
    bl_description = "Set to Preset 8"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(8, 'texture', active_strip.texture_is_recording, context)
        return {'FINISHED'}
    
    
class FocusBandOneOperator(bpy.types.Operator):
    bl_idname = "my.focus_band_one"
    bl_label = "Focus Palette 1"
    bl_description = "Set to focus palette one"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(1, 'band', active_strip.band_is_recording, context)
        return {'FINISHED'}
    
    
class FocusBandTwoOperator(bpy.types.Operator):
    bl_idname = "my.focus_band_two"
    bl_label = "Focus Palette 2"
    bl_description = "Set to focus palette two"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(2, 'band', active_strip.band_is_recording, context)
        return {'FINISHED'}
    
    
class FocusBandThreeOperator(bpy.types.Operator):
    bl_idname = "my.focus_band_three"
    bl_label = "Focus Palette 3"
    bl_description = "Set to focus palette three"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(3, 'band', active_strip.band_is_recording, context)
        return {'FINISHED'}
    
    
class FocusBandFourOperator(bpy.types.Operator):
    bl_idname = "my.focus_band_four"
    bl_label = "Focus Palette 4"
    bl_description = "Set to focus palette four"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(4, 'band', active_strip.band_is_recording, context)
        return {'FINISHED'}
    
    
class FocusBandFiveOperator(bpy.types.Operator):
    bl_idname = "my.focus_band_five"
    bl_label = "Preset 5"
    bl_description = "Set to Preset 5"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(5, 'band', active_strip.band_is_recording, context)
        return {'FINISHED'}
    
    
class FocusBandSixOperator(bpy.types.Operator):
    bl_idname = "my.focus_band_six"
    bl_label = "Preset 6"
    bl_description = "Set to Preset 6"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(6, 'band', active_strip.band_is_recording, context)
        return {'FINISHED'}
    
    
class FocusBandSevenOperator(bpy.types.Operator):
    bl_idname = "my.focus_band_seven"
    bl_label = "Preset 7"
    bl_description = "Set to Preset 7"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(7, 'band', active_strip.band_is_recording, context)
        return {'FINISHED'}
    
    
class FocusBandEightOperator(bpy.types.Operator):
    bl_idname = "my.focus_band_eight"
    bl_label = "Preset 8"
    bl_description = "Set to Preset 8"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(8, 'band', active_strip.band_is_recording, context)
        return {'FINISHED'}
    
    
class FocusAccentOneOperator(bpy.types.Operator):
    bl_idname = "my.focus_accent_one"
    bl_label = "Focus Palette 1"
    bl_description = "Set to focus palette one"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(1, 'accent', active_strip.accent_is_recording, context)
        return {'FINISHED'}
    
    
class FocusAccentTwoOperator(bpy.types.Operator):
    bl_idname = "my.focus_accent_two"
    bl_label = "Focus Palette 2"
    bl_description = "Set to focus palette two"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(2, 'accent', active_strip.accent_is_recording, context)
        return {'FINISHED'}
    
    
class FocusAccentThreeOperator(bpy.types.Operator):
    bl_idname = "my.focus_accent_three"
    bl_label = "Focus Palette 3"
    bl_description = "Set to focus palette three"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(3, 'accent', active_strip.accent_is_recording, context)
        return {'FINISHED'}
    
    
class FocusAccentFourOperator(bpy.types.Operator):
    bl_idname = "my.focus_accent_four"
    bl_label = "Focus Palette 4"
    bl_description = "Set to focus palette four"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(4, 'accent', active_strip.accent_is_recording, context)
        return {'FINISHED'}
    
    
class FocusAccentFiveOperator(bpy.types.Operator):
    bl_idname = "my.focus_accent_five"
    bl_label = "Focus Palette 5"
    bl_description = "Set to Preset 5"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(5, 'accent', active_strip.accent_is_recording, context)
        return {'FINISHED'}
    
    
class FocusAccentSixOperator(bpy.types.Operator):
    bl_idname = "my.focus_accent_six"
    bl_label = "Preset 6"
    bl_description = "Set to Preset 6"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(6, 'accent', active_strip.accent_is_recording, context)
        return {'FINISHED'}
    
    
class FocusAccentSevenOperator(bpy.types.Operator):
    bl_idname = "my.focus_accent_seven"
    bl_label = "Preset 7"
    bl_description = "Set to Preset 7"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(7, 'accent', active_strip.accent_is_recording, context)
        return {'FINISHED'}
    
    
class FocusAccentEightOperator(bpy.types.Operator):
    bl_idname = "my.focus_accent_eight"
    bl_label = "Preset 8"
    bl_description = "Set to Preset 8"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(8, 'accent', active_strip.accent_is_recording, context)
        return {'FINISHED'}
    
    
class FocusCycOneOperator(bpy.types.Operator):
    bl_idname = "my.focus_cyc_one"
    bl_label = "Focus Palette 1"
    bl_description = "Set to focus palette one"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(1, 'cyc', active_strip.cyc_is_recording, context)
        return {'FINISHED'}
    
    
class FocusCycTwoOperator(bpy.types.Operator):
    bl_idname = "my.focus_cyc_two"
    bl_label = "Focus Palette 2"
    bl_description = "Set to focus palette two"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(2, 'cyc', active_strip.cyc_is_recording, context)
        return {'FINISHED'}
    
    
class FocusCycThreeOperator(bpy.types.Operator):
    bl_idname = "my.focus_cyc_three"
    bl_label = "Focus Palette 3"
    bl_description = "Set to focus palette three"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(3, 'cyc', active_strip.cyc_is_recording, context)
        return {'FINISHED'}
    
    
class FocusCycFourOperator(bpy.types.Operator):
    bl_idname = "my.focus_cyc_four"
    bl_label = "Focus Palette 4"
    bl_description = "Set to focus palette four"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(4, 'cyc', active_strip.cyc_is_recording, context)
        return {'FINISHED'}
    
    
class FocusCycFiveOperator(bpy.types.Operator):
    bl_idname = "my.focus_cyc_five"
    bl_label = "Focus Palette 5"
    bl_description = "Set to Preset 5"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(5, 'cyc', active_strip.cyc_is_recording, context)
        return {'FINISHED'}
    
    
class FocusCycSixOperator(bpy.types.Operator):
    bl_idname = "my.focus_cyc_six"
    bl_label = "Preset 6"
    bl_description = "Set to Preset 6"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(6, 'cyc', active_strip.cyc_is_recording, context)
        return {'FINISHED'}
    
    
class FocusCycSevenOperator(bpy.types.Operator):
    bl_idname = "my.focus_cyc_seven"
    bl_label = "Preset 7"
    bl_description = "Set to Preset 7"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(7, 'cyc', active_strip.cyc_is_recording, context)
        return {'FINISHED'}
    
    
class FocusCycEightOperator(bpy.types.Operator):
    bl_idname = "my.focus_cyc_eight"
    bl_label = "Preset 8"
    bl_description = "Set to Preset 8"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(8, 'cyc', active_strip.cyc_is_recording, context)
        return {'FINISHED'} 
    
    
class FocusEnergyOneOperator(bpy.types.Operator):
    bl_idname = "my.focus_energy_one"
    bl_label = "Focus Palette 1"
    bl_description = "Set to Effect 1"
    
    def execute(self, context):
        scene = context.scene
        active_strip = scene.sequence_editor.active_strip
        
        if context.screen:
            groups = parse_builder_groups(scene.energy_light_groups)
            active_strip.cue_builder_effect_id = "1"
            
            for group in groups:
                address = "/eos/newcmd"
                argument = str("Group " + str(group) + " Effect " + str(1 + scene.cue_builder_id_offset) + " Enter")
                ip_address = context.scene.scene_props.str_osc_ip_address
                port = context.scene.scene_props.int_osc_port
                send_osc_string(address, ip_address, port, argument)
        return {'FINISHED'}
    
    
class FocusEnergyTwoOperator(bpy.types.Operator):
    bl_idname = "my.focus_energy_two"
    bl_label = "Focus Palette 2"
    bl_description = "Set to Effect 2"
    
    def execute(self, context):
        scene = context.scene
        active_strip = scene.sequence_editor.active_strip
        
        if context.screen:
            groups = parse_builder_groups(scene.energy_light_groups)
            active_strip.cue_builder_effect_id = "2"
            
            for group in groups:
                address = "/eos/newcmd"
                argument = str("Group " + str(group) + " Effect " + str(2 + scene.cue_builder_id_offset) + " Enter")
                ip_address = context.scene.scene_props.str_osc_ip_address
                port = context.scene.scene_props.int_osc_port
                send_osc_string(address, ip_address, port, argument)
        return {'FINISHED'}
    
    
class FocusEnergyThreeOperator(bpy.types.Operator):
    bl_idname = "my.focus_energy_three"
    bl_label = "Focus Palette 3"
    bl_description = "Set to Effect 3"
    
    def execute(self, context):
        scene = context.scene
        active_strip = scene.sequence_editor.active_strip
        
        if context.screen:
            groups = parse_builder_groups(scene.energy_light_groups)
            active_strip.cue_builder_effect_id = "3"
            
            for group in groups:
                address = "/eos/newcmd"
                argument = str("Group " + str(group) + " Effect " + str(3 + scene.cue_builder_id_offset) + " Enter")
                ip_address = context.scene.scene_props.str_osc_ip_address
                port = context.scene.scene_props.int_osc_port
                send_osc_string(address, ip_address, port, argument)
        return {'FINISHED'}
    
    
class FocusEnergyFourOperator(bpy.types.Operator):
    bl_idname = "my.focus_energy_four"
    bl_label = "Focus Palette 4"
    bl_description = "Set to Effect 4"
    
    def execute(self, context):
        scene = context.scene
        active_strip = scene.sequence_editor.active_strip
        
        if context.screen:
            groups = parse_builder_groups(scene.energy_light_groups)
            active_strip.cue_builder_effect_id = "4"
            
            for group in groups:
                address = "/eos/newcmd"
                argument = str("Group " + str(group) + " Effect " + str(4 + scene.cue_builder_id_offset) + " Enter")
                ip_address = context.scene.scene_props.str_osc_ip_address
                port = context.scene.scene_props.int_osc_port
                send_osc_string(address, ip_address, port, argument)
        return {'FINISHED'}
    

class FocusEnergyFiveOperator(bpy.types.Operator):
    bl_idname = "my.focus_energy_five"
    bl_label = "Focus Palette 5"
    bl_description = "Set to Effect 5"
    
    def execute(self, context):
        scene = context.scene
        active_strip = scene.sequence_editor.active_strip
        
        if context.screen:
            groups = parse_builder_groups(scene.energy_light_groups)
            active_strip.cue_builder_effect_id = "5"
            
            for group in groups:
                address = "/eos/newcmd"
                argument = str("Group " + str(group) + " Effect " + str(5 + scene.cue_builder_id_offset) + " Enter")
                ip_address = context.scene.scene_props.str_osc_ip_address
                port = context.scene.scene_props.int_osc_port
                send_osc_string(address, ip_address, port, argument)
        return {'FINISHED'}
    
    
class FocusEnergySixOperator(bpy.types.Operator):
    bl_idname = "my.focus_energy_six"
    bl_label = "Preset 6"
    bl_description = "Set to Effect 6"
    
    def execute(self, context):
        scene = context.scene
        active_strip = scene.sequence_editor.active_strip
        
        if context.screen:
            groups = parse_builder_groups(scene.energy_light_groups)
            active_strip.cue_builder_effect_id = "6"
            
            for group in groups:
                address = "/eos/newcmd"
                argument = str("Group " + str(group) + " Effect " + str(6 + scene.cue_builder_id_offset) + " Enter")
                ip_address = context.scene.scene_props.str_osc_ip_address
                port = context.scene.scene_props.int_osc_port
                send_osc_string(address, ip_address, port, argument)
        return {'FINISHED'}
    
    
class StopEffectOperator(bpy.types.Operator):
    bl_idname = "my.stop_effect"
    bl_label = "Stop Effect"
    bl_description = "Stop effect"
    
    def execute(self, context):
        scene = context.scene
        active_strip = scene.sequence_editor.active_strip
        
        if context.screen:
            groups = parse_builder_groups(scene.energy_light_groups)
            active_strip.cue_builder_effect_id = ""
            
            for group in groups:
                address = "/eos/newcmd"
                argument = str("Group " + str(group) + " Effect Enter")
                ip_address = context.scene.scene_props.str_osc_ip_address
                port = context.scene.scene_props.int_osc_port
                send_osc_string(address, ip_address, port, argument)
        return {'FINISHED'}
    
    
class BakeAudioOperator(bpy.types.Operator):
    bl_idname = "seq.bake_audio_operator"
    bl_label = "Bake Audio"
    bl_description = "Bake spatial information to volume keyframes so it will show up after mixdown. Then, import them into audio-activated Qlab and play them all at the same time through a multi-output USB audio interface connected to the sound mixer"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        sequences = scene.sequence_editor.sequences_all
        active_strip = scene.sequence_editor.active_strip
        correct_frame_start = active_strip.frame_start
        correct_frame_end = active_strip.frame_final_duration
        matching_strips = [strip for strip in sequences if strip.type == 'SOUND' and strip.audio_type_enum == "option_speaker" and strip.frame_start == correct_frame_start and strip.frame_final_duration == correct_frame_end]
        
        for frame in range(scene.frame_start, scene.frame_end + 1):
            scene.frame_set(frame)
            for strip in matching_strips:
                strip.volume = strip.dummy_volume
                strip.keyframe_insert(data_path="volume", frame=frame)
        
        self.report({'INFO'}, "Bake complete.")
        
        return {'FINISHED'}
    
    
class SoloTrackOperator(bpy.types.Operator):
    bl_idname = "seq.solo_track_operator"
    bl_label = "Solo Track"
    bl_description = "Mute all other participating tracks and keep this unmuted"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        sequences = scene.sequence_editor.sequences_all
        active_strip = scene.sequence_editor.active_strip
        correct_frame_start = active_strip.frame_start
        correct_frame_end = active_strip.frame_final_duration
        matching_strips = [strip for strip in sequences if strip.type == 'SOUND' and strip.audio_type_enum == "option_speaker" and strip.frame_start == correct_frame_start and strip.frame_final_duration == correct_frame_end]
        
        true_frame_start = active_strip.frame_start + active_strip.frame_offset_start
        true_frame_end = active_strip.frame_final_end - active_strip.frame_offset_end

        # Set the scene's start and end frames to match the true start and end of the active strip
        scene.frame_start = int(true_frame_start)
        scene.frame_end = int(true_frame_end)
        
        for strip in matching_strips:
            strip.mute = True
                
        active_strip.mute = False
        
        self.report({'INFO'}, "Bake complete.")
        
        return {'FINISHED'}
    
    
class ExportAudioOperator(bpy.types.Operator):
    bl_idname = "seq.export_audio_operator"
    bl_label = "Export Channel"
    bl_description = "Export an audio file for this speaker channel to Qlab"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        bpy.ops.sound.mixdown('INVOKE_DEFAULT')
        return {'FINISHED'}
    
    
class KeyGroupsOperator(bpy.types.Operator):
    bl_idname = "my.key_groups"
    bl_label = "Console Groups"
    bl_description = "Set groups for key light"
    
    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        self.layout.prop(context.scene, "key_light_groups", text="")

        
class RimGroupsOperator(bpy.types.Operator):
    bl_idname = "my.rim_groups"
    bl_label = "Console Groups"
    bl_description = "Set groups for rim light"
    
    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        self.layout.prop(context.scene, "rim_light_groups", text="")
        
        
class FillGroupsOperator(bpy.types.Operator):
    bl_idname = "my.fill_groups"
    bl_label = "Console Groups"
    bl_description = "Set groups for fill light"
    
    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        self.layout.prop(context.scene, "fill_light_groups", text="")
        
        
class TextureGroupsOperator(bpy.types.Operator):
    bl_idname = "my.texture_groups"
    bl_label = "Console Groups"
    bl_description = "Set groups for texture light"
    
    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        self.layout.prop(context.scene, "texture_light_groups", text="")
        
        
class BandGroupsOperator(bpy.types.Operator):
    bl_idname = "my.band_groups"
    bl_label = "Console Groups"
    bl_description = "Set groups for band light"
    
    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        self.layout.prop(context.scene, "band_light_groups", text="")
        
        
class AccentGroupsOperator(bpy.types.Operator):
    bl_idname = "my.accent_groups"
    bl_label = "Accent Groups"
    bl_description = "Set groups for accent light"
    
    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        self.layout.prop(context.scene, "accent_light_groups", text="")
        
        
class EnergyGroupsOperator(bpy.types.Operator):
    bl_idname = "my.energy_groups"
    bl_label = "Energy Groups"
    bl_description = "Set groups for energy light"
    
    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        self.layout.prop(context.scene, "energy_light_groups", text="")
        
        
class GelOneGroupsOperator(bpy.types.Operator):
    bl_idname = "my.gel_one_groups"
    bl_label = "Console Groups"
    bl_description = "Set groups for gel 1 light"
    
    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        scene = context.scene
        if not scene.using_gels_for_cyc:
            return context.window_manager.invoke_props_dialog(self, width=400)
        else:
            return context.window_manager.invoke_props_dialog(self, width=600)

    def draw(self, context):
        scene = context.scene
        if not scene.using_gels_for_cyc:  
            self.layout.prop(context.scene, "cyc_light_groups", text="")
        else:
            self.layout.prop(context.scene, "cyc_light_groups", text="Gel 1")
            self.layout.prop(context.scene, "cyc_two_light_groups", text="Gel 2")
            self.layout.prop(context.scene, "cyc_three_light_groups", text="Gel 3")
            self.layout.prop(context.scene, "cyc_four_light_groups", text="Gel 4")
            

## What on earth is this here for??? 
class WM_OT_ShowMessage(bpy.types.Operator):
    bl_idname = "wm.show_message"
    bl_label = "Message"

    message:  bpy.props.StringProperty()

    def execute(self, context):
        self.report({'INFO'}, self.message)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=500)
    
    def draw(self, context):
        self.layout.label(text=self.message)
            
            
classes = (
    EnableAnimationOperator,
    EnableTriggersOperator,
    BumpLeftFiveOperator,
    BumpLeftOneOperator,
    BumpUpOperator,
    BumpDownOperator,
    BumpRightOneOperator,
    BumpRightFiveOperator,
    BumpTCLeftFiveOperator,
    BumpTCLeftOneOperator,
    BumpTCRightOneOperator,
    BumpTCRightFiveOperator,
    AddOffsetOperator,
    CopyAboveToSelectedOperator,
    CopyColorOperator,
    CopyStripNameOperator,
    CopyChannelOperator,
    CopyDurationOperator,
    CopyStartFrameOperator,
    CopyEndFrameOperator,
    SelectSimilarOperator,
    StartEndFrameMappingOperator,
    MapTimeOperator,
    SyncVideoOperator,
    MuteOperator,
    ClearIntensityOperator,
    ClearRedOperator,
    ClearGreenOperator,
    ClearBlueOperator,
    ClearPanOperator,
    ClearTiltOperator,
    ClearZoomOperator,
    ClearIrisOperator,
    RecordPresetOperator,
    LoadPresetOperator,
    SetMaxZoomOperator,
    SetMinZoomOperator,
    SetMaxIrisOperator,
    SetMinIrisOperator,
    ResetZoomRangeOperator,
    ResetIrisRangeOperator,
    ViewGraphOperator,
    ClearIntensityDataOperator,
    ClearPanDataOperator,
    ClearTiltDataOperator,
    ClearZoomDataOperator,
    ClearIrisDataOperator,
    KeyframeIntensityOperator,
    KeyframeColorOperator,
    KeyframePanOperator,
    KeyframeTiltOperator,
    KeyframeZoomOperator,
    KeyframeIrisOperator,
    ReplaceOperator,
    GenerateStripsOperator,
    AddColorStripOperator,
    ClockZeroOperator,
    ClearTimecodeClockOperator,
    SyncCueOperator,
    ExecuteOnCueOperator,
    DisableOnCueOperator,
    ExecuteAnimationOnCueOperator,
    DisableAnimationOnCueOperator,
    StartMacroSearchOperator,
    EndMacroSearchOperator,
    StartMacroOperator,
    EndMacroOperator,
    StartMacroEyeballOperator,
    EndMacroEyeballOperator,
    GenerateStartFrameMacroOperator,
    GenerateEndFrameMacroOperator,
    BuildFlashMacrosOperator,
    FlashMacroSearchOperator,
    SelectChannelOperator,
    PlayOperator,
    StopOperator,
    DeleteOperator,
    SaveOperator,
    AddStripOperator,
    ScriptingOperator,
    SequencerOperator,
    GoToCueOutOperator,
    DisplaysOperator,
    AboutOperator,
    GenerateTextOperator,
    ImportUsittAsciiOperator,
    RecordOperator,
    ColorTriggerOperator,
    StripNameTriggerOperator,
    ChannelTriggerOperator,
    StartFrameTriggerOperator,
    EndFrameTriggerOperator,
    DurationTriggerOperator,
    StartFrameJumpOperator,
    EndFrameJumpOperator,
    ExtrudeOperator,
    ScaleOperator,
    GrabOperator,
    GrabXOperator,
    GrabYOperator,
    ShowWaveformOperator,
    AddMacroOperator,
    AddCueOperator,
    AddFlashOperator,
    AddAnimationOperator,
    AddTriggerOperator,
    RemoveMotifOperator,
    CutOperator,
    AddMediaOperator,
    AssignToChannelOperator,
    SetStartFrameOperator,
    SetEndFrameOperator,
    WM_OT_ShowMessage,
    BakeFCurvesToCuesOperator,
    DisableAllClocksOperator,
    RerecordCuesOperator,
    ColorPaletteOperator,
    DeleteAnimationCueListOperator,
    DeleteAnimationEventListOperator,
    StopAnimationClockOperator,
    FocusOneOperator,
    FocusTwoOperator,
    FocusThreeOperator,
    FocusFourOperator,
    FocusRimOneOperator,
    FocusRimTwoOperator,
    FocusRimThreeOperator,
    FocusRimFourOperator,
    FocusFillOneOperator,
    FocusFillTwoOperator,
    FocusFillThreeOperator,
    FocusFillFourOperator,
    FocusTextureOneOperator,
    FocusTextureTwoOperator,
    FocusTextureThreeOperator,
    FocusTextureFourOperator,
    FocusTextureFiveOperator,
    FocusTextureSixOperator,
    FocusTextureSevenOperator,
    FocusTextureEightOperator,
    FocusBandOneOperator,
    FocusBandTwoOperator,
    FocusBandThreeOperator,
    FocusBandFourOperator,
    FocusBandFiveOperator,
    FocusBandSixOperator,
    FocusBandSevenOperator,
    FocusBandEightOperator,
    FocusAccentOneOperator,
    FocusAccentTwoOperator,
    FocusAccentThreeOperator,
    FocusAccentFourOperator,
    FocusAccentFiveOperator,
    FocusAccentSixOperator,
    FocusAccentSevenOperator,
    FocusAccentEightOperator,
    FocusCycOneOperator,
    FocusCycTwoOperator,
    FocusCycThreeOperator,
    FocusCycFourOperator,
    FocusCycFiveOperator,
    FocusCycSixOperator,
    FocusCycSevenOperator,
    FocusCycEightOperator,
    FocusEnergyOneOperator,
    FocusEnergyTwoOperator,
    FocusEnergyThreeOperator,
    FocusEnergyFourOperator,
    FocusEnergyFiveOperator,
    FocusEnergySixOperator,
    UpdateBuilderOperator,
    RecordCueOperator,
    KeyGroupsOperator,
    RimGroupsOperator,
    FillGroupsOperator,
    TextureGroupsOperator,
    BandGroupsOperator,
    AccentGroupsOperator,
    EnergyGroupsOperator,
    GelOneGroupsOperator,
    StopEffectOperator,
    BakeAudioOperator,
    SoloTrackOperator,
    ExportAudioOperator
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    # Shift+G keymap for Ghost Out
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Window', space_type='EMPTY')
        kmi = km.keymap_items.new(GoToCueOutOperator.bl_idname, 'G', 'PRESS', shift=True)
        
        
def unregister():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps['Window']
        for kmi in km.keymap_items:
            if kmi.idname == GoToCueOutOperator.bl_idname:
                km.keymap_items.remove(kmi)
                break
            
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        

# For development purposes only.   
if __name__ == "__main__":
    register()
