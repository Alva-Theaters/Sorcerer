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
from bpy.app.handlers import persistent
import os
import bpy.utils.previews


preview_collections = {}


stop_updating_color = "No"
auto_cue_prefix = "/eos/newcmd"
animation_string = ""
max_zoom = 1000
min_zoom = -1000
max_iris = 1000
min_iris = -1000


filter_color_strips = partial(filter, bpy.types.ColorSequence.__instancecheck__)


bpy.types.Sequence.start_macro_muted = bpy.props.BoolProperty(
    name="Start Macro Muted",
    description="If true, the start macro is muted",
    default=False
)
bpy.types.Sequence.end_macro_muted = bpy.props.BoolProperty(
    name="End Macro Muted",
    description="If true, the end macro is muted",
    default=False
)


def get_frame_rate(scene):
    fps = scene.render.fps
    fps_base = scene.render.fps_base
    frame_rate = fps / fps_base
    return frame_rate


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


def find_relevant_clock(scene):
    for strip in scene.sequence_editor.sequences:
        if (strip.type == 'SOUND' and 
            not strip.mute and 
            getattr(strip, 'song_timecode_clock_number', 0) != 0 and
            strip.frame_start <= scene.frame_current < strip.frame_final_end):
            return strip


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


def get_light_rotation_degrees(light_name):
    """
    Returns the X (tilt) and Y (pan) rotation angles in degrees for a given light object,
    adjusting the range of pan to -270 to 270 degrees.
    
    :param light_name: Name of the light object in the scene.
    :return: Tuple containing the X (tilt) and Y (pan) rotation angles in degrees.
    """
    
    light_object = bpy.data.objects.get(light_name)

    if light_object and light_object.type == 'LIGHT':
        matrix = light_object.matrix_world
        euler = matrix.to_euler('XYZ')
        x_rot_deg = math.degrees(euler.x)
        y_rot_deg = math.degrees(euler.z)  # Pan seems to be on zed euler, not on y as y resolves to super tiny number

        # Adjust the pan angle to extend the range to -270 to 270 degrees
        if y_rot_deg > 90:
            y_rot_deg -= 360

        return x_rot_deg, y_rot_deg
    else:
        print("It appears as though", light_name,"has left the chat.")
        return None, None


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


# Frame change handler for updating livemap preview.
def frame_change_handler(scene):
    context = bpy.context
    if context.screen:
        if not bpy.context.screen.is_animation_playing:
   
            def set_eos_cue_livemap_preview(context):
                sequence_editor = context.scene.sequence_editor
                current_frame = context.scene.frame_current  # Get the current frame
                if sequence_editor:
                    relevant_strips = [strip for strip in sequence_editor.sequences if getattr(strip, 'eos_cue_number', 0) != 0 and strip.my_settings.motif_type_enum == 'option_eos_cue' and not strip.mute]
                    closest_strip = None
                    for strip in relevant_strips:
                        if strip.frame_start <= current_frame:
                            if closest_strip is None or strip.frame_start > closest_strip.frame_start:
                                closest_strip = strip      
                    if closest_strip:
                        eos_cue_number_selected = closest_strip.eos_cue_number
                        scene.livemap_label = "Livemap Cue: {}".format(eos_cue_number_selected)
                    else:
                        scene.livemap_label = "Livemap Cue: "
                        return 
                else:
                    return None, None
                 
            set_eos_cue_livemap_preview(context)


def fire_start(trigger_prefix, osc_trigger, frame):
    scene = bpy.context.scene.scene_props
    ip_address = scene.str_osc_ip_address
    port = scene.int_osc_port

    send_osc_string(trigger_prefix, ip_address, port, osc_trigger)
    send_osc_string(trigger_prefix, ip_address, port, osc_trigger)
    
    
def fire_offset_start(trigger_prefix, osc_trigger, frame):
    scene = bpy.context.scene.scene_props
    ip_address = scene.str_osc_ip_address
    port = scene.int_osc_port

    send_osc_string(trigger_prefix, ip_address, port, osc_trigger)
    send_osc_string(trigger_prefix, ip_address, port, osc_trigger)


def fire_end(trigger_prefix, osc_trigger_end, frame):
    scene = bpy.context.scene.scene_props
    ip_address = scene.str_osc_ip_address
    port = scene.int_osc_port

    send_osc_string(trigger_prefix, ip_address, port, osc_trigger_end)
    send_osc_string(trigger_prefix, ip_address, port, osc_trigger_end)
    
    
def fire_livemap(live_map_prefix, eos_cue_number_livemap):
    scene = bpy.context.scene.scene_props
    ip_address = scene.str_osc_ip_address
    port = scene.int_osc_port
    
    send_osc_string(live_map_prefix, ip_address, port, eos_cue_number_livemap)
    send_osc_string(live_map_prefix, ip_address, port, eos_cue_number_livemap)


class PlaybackMonitor:
    def __init__(self):
        self.last_frame = -1
        self.is_playing_back = False

    @persistent
    def frame_change_handler(self, scene, depsgraph):
        current_frame = scene.frame_current

        if abs(current_frame - self.last_frame) > 1 and self.last_frame != -1:
            self.on_scrub_detected(current_frame)
            
        self.last_frame = current_frame
        
        # Trigger strips.
        if self.is_playing_back:
            frame = scene.frame_current
            if frame in self.start_mapping:
                for trigger_prefix, osc_trigger in self.start_mapping[frame]:
                    fire_start(trigger_prefix, osc_trigger, frame)
                    
            if frame in self.offset_start_mapping:
                for item in self.offset_start_mapping[frame]:
                    try:
                        trigger_prefix, osc_trigger = item
                        fire_offset_start(trigger_prefix, osc_trigger, frame)
                    except ValueError:
                        print("Error.")
                        
            if frame in self.end_mapping:
                for trigger_prefix, osc_trigger_end in self.end_mapping[frame]:
                    fire_end(trigger_prefix, osc_trigger_end, frame) 

    @persistent
    def on_scrub_detected(self, current_frame):
        scene = bpy.context.scene
        if scene.sync_timecode and self.is_playing_back:
            relevant_sound_strip = None
            current_frame = scene.frame_current
            current_frame = current_frame + scene.timecode_expected_lag

            ## This needs to become a universal function to avoid repeating code.
            for strip in scene.sequence_editor.sequences:
                if (strip.type == 'SOUND' and 
                    not strip.mute and 
                    getattr(strip, 'song_timecode_clock_number', 0) != 0 and
                    strip.frame_start <= current_frame < strip.frame_final_end):
                    relevant_sound_strip = strip
                    break
            
            if relevant_sound_strip != None:
                fps = get_frame_rate(scene)
                timecode = frame_to_timecode(self, current_frame, fps)
                clock = relevant_sound_strip.song_timecode_clock_number
                ip_address = scene.scene_props.str_osc_ip_address
                port = scene.scene_props.int_osc_port
                send_osc_string("/eos/newcmd", ip_address, port, f"Event {clock} / Internal Time {timecode} Enter, Event {clock} / Internal Enable Enter")
               
    @persistent           
    def playback_start_handler(self, scene, depsgraph):
        self.is_playing_back = True
        scene = _context.scene

        # Abort if unarmed
        if not scene.is_armed_osc:
            return
        
        # Go house down.
        if scene.house_down_on_play:
            ip_address = scene.scene_props.str_osc_ip_address
            port = scene.scene_props.int_osc_port
            house_prefix = scene.house_prefix
            house_down_argument = scene.house_down_argument
            send_osc_string(house_prefix, ip_address, port, house_down_argument)
            
        # Get trigger maps
        self.start_mapping = get_trigger_start_map(scene)
        self.offset_start_mapping = get_trigger_offset_start_map(scene)
        self.end_mapping = get_trigger_end_map(scene)
             
        # Go timecode sync.    
        if scene.sync_timecode:
            relevant_sound_strip = None
            current_frame = scene.frame_current
            current_frame = current_frame + scene.timecode_expected_lag
            for strip in scene.sequence_editor.sequences:
                if (strip.type == 'SOUND' and 
                    not strip.mute and 
                    getattr(strip, 'song_timecode_clock_number', 0) != 0 and
                    strip.frame_start <= current_frame < strip.frame_final_end):
                    relevant_sound_strip = strip
                    break
            if relevant_sound_strip != None:
                fps = get_frame_rate(scene)
                timecode = frame_to_timecode(self, current_frame, fps)
                clock = relevant_sound_strip.song_timecode_clock_number
                ip_address = scene.scene_props.str_osc_ip_address
                port = scene.scene_props.int_osc_port
                send_osc_string("/eos/newcmd", ip_address, port, f"Event {clock} / Internal Time {timecode} Enter, Event {clock} / Internal Enable Enter")
                    
        # Go livemap.
        if scene.sequence_editor and scene.is_armed_livemap:
            current_frame = scene.frame_current  
            active_strip = scene.sequence_editor.active_strip
            relevant_strips = [strip for strip in scene.sequence_editor.sequences if getattr(strip, 'eos_cue_number', 0) != 0 and getattr(strip, 'frame_start', 0) != active_strip.frame_start and strip.my_settings.motif_type_enum == 'option_eos_cue' and not strip.mute]
            closest_strip = None
            for strip in relevant_strips:
                if strip.frame_start <= current_frame:
                    if closest_strip is None or strip.frame_start > closest_strip.frame_start:
                        closest_strip = strip
            if closest_strip:
                eos_cue_number_selected = closest_strip.eos_cue_number
                eos_cue_number_livemap = "Go_to_Cue {} Time 1 Enter".format(eos_cue_number_selected)
                live_map_prefix = "/eos/newcmd"
                fire_livemap(live_map_prefix, eos_cue_number_livemap)
                scene.livemap_label = f"Livemap Cue: {eos_cue_number_selected}"
                return 

    @persistent
    def playback_stop_handler(self, scene, depsgraph):
        self.is_playing_back = False
        scene = bpy.context.scene
        
        # Go house up.
        if scene.house_up_on_stop == True:
            ip_address = scene.scene_props.str_osc_ip_address
            port = scene.scene_props.int_osc_port
            house_prefix = scene.house_prefix
            house_up_argument = scene.house_up_argument
            send_osc_string(house_prefix, ip_address, port, house_up_argument)
        
        # End timecode.    
        if scene.sync_timecode:
            relevant_sound_strip = None
            current_frame = scene.frame_current
            for strip in scene.sequence_editor.sequences:
                if (strip.type == 'SOUND' and 
                    not strip.mute and 
                    getattr(strip, 'song_timecode_clock_number', 0) != 0 and
                    strip.frame_start <= current_frame < strip.frame_final_end):
                    relevant_sound_strip = strip
                    break
                
            if relevant_sound_strip != None:
                clock = relevant_sound_strip.song_timecode_clock_number
                ip_address = scene.scene_props.str_osc_ip_address
                port = scene.scene_props.int_osc_port
                send_osc_string("/eos/newcmd", ip_address, port, f"Event {clock} / Internal Disable Enter")

        start_mapping = None
        offset_start_mapping = None
        end_mapping = None

playback_monitor = PlaybackMonitor()


@persistent
def frame_change_handler_animation(scene):
    if not scene.sequence_editor:
        return

    sequences = scene.sequence_editor.sequences_all

    for seq in sequences:
        if isinstance(seq, bpy.types.ColorSequence):
            seq.osc_intensity = seq.osc_intensity
            seq.osc_color = seq.osc_color
            seq.osc_pan = seq.osc_pan
            seq.osc_tilt = seq.osc_tilt
            seq.osc_zoom = seq.osc_zoom
            seq.osc_iris = seq.osc_iris


# Allows real-time updating so you can see what you're doing 
def osc_intensity_update(self, context):
    scene = context.scene
    if context.screen:
        
        if not scene.is_armed_osc:
            return
        
        if not hasattr(self, "my_settings") or self.my_settings.motif_type_enum != 'option_animation':
            return

        if self.intensity_prefix == "":
            return
        
        if '*' in self.intensity_prefix:
            return
        
        if not hasattr(self, "intensity_checker"):
            self.intensity_checker = 1000
            
        if self.intensity_checker == self.osc_intensity:
            return
        
        if self.mute:
            return
        
        if scene.frame_current > self.frame_final_end:
            return
        
        if scene.frame_current < self.frame_start:
            return
        
        intensity_prefix = self.intensity_prefix
        ip_address = context.scene.scene_props.str_osc_ip_address
        port = context.scene.scene_props.int_osc_port
        
        osc_intensity_str = str(self.osc_intensity)
        send_osc_string(intensity_prefix, ip_address, port, osc_intensity_str)
        
        self.intensity_checker = self.osc_intensity

        
def osc_color_update(self, context):
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
        
        red_prefix = self.red_prefix
        green_prefix = self.green_prefix
        blue_prefix = self.blue_prefix
        osc_color = self.osc_color
        red_value = osc_color[0]
        red_value = round(red_value * 100, 1)
        green_value = osc_color[1]
        green_value = round(green_value * 100, 1)
        blue_value = osc_color[2]
        blue_value = round(blue_value * 100, 1)
        ip_address = context.scene.scene_props.str_osc_ip_address
        port = context.scene.scene_props.int_osc_port
        
        osc_red_str = str(red_value)
        send_osc_string(red_prefix, ip_address, port, osc_red_str)
        
        osc_green_str = str(green_value)
        send_osc_string(green_prefix, ip_address, port, osc_green_str)
        
        osc_blue_str = str(blue_value)
        send_osc_string(blue_prefix, ip_address, port, osc_blue_str)
        
        
def osc_pan_update(self, context):
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
        
        pan_prefix = self.pan_prefix
        osc_pan = self.osc_pan
        ip_address = scene.scene_props.str_osc_ip_address
        port = scene.scene_props.int_osc_port

        if self.use_paths:
            sequences = scene.sequence_editor.sequences_all
            light_name = str(self.selected_light)
            
            tilt_value, pan_value = get_light_rotation_degrees(light_name)
            
            if tilt_value == None or pan_value == None:
                return
            
            pan = round(pan_value, 1)
            pan = str(pan)
            
            send_osc_string(pan_prefix, ip_address, port, pan)
        else:
            osc_pan_str = str(osc_pan)
            send_osc_string(pan_prefix, ip_address, port, osc_pan_str)

    
def osc_tilt_update(self, context):
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
        
        tilt_prefix = self.tilt_prefix
        osc_tilt = self.osc_tilt
        ip_address = context.scene.scene_props.str_osc_ip_address
        port = context.scene.scene_props.int_osc_port
        
        if self.use_paths:
            sequences = context.scene.sequence_editor.sequences_all
            light_name = str(self.selected_light)
            
            tilt_value, pan_value = get_light_rotation_degrees(light_name)
            
            if tilt_value == None or pan_value == None:
                return

            tilt = round(tilt_value, 1)
            tilt = str(tilt)
            send_osc_string(tilt_prefix, ip_address, port, tilt)
        else:
            osc_tilt_str = str(osc_tilt)
            send_osc_string(tilt_prefix, ip_address, port, osc_tilt_str)

    
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


class RenderStripsOperator(bpy.types.Operator):
    bl_idname = "seq.render_strips_operator"
    bl_label = "Render Strips"
    bl_description = "Orb will create timecode events for every Macro, Cue, and Flash strip on the relevant sound strip's event list. Shortcut is Shift+Spacebar"

    @classmethod
    def poll(cls, context):
        relevant_strips = [strip for strip in context.scene.sequence_editor.sequences_all if strip.frame_final_end >= context.scene.frame_start and strip.frame_start <= context.scene.frame_end and (strip.type == 'COLOR' or strip.type == 'SOUND')]
        return len(relevant_strips) >= 1

    def invoke(self, context, event):
        all_maps = [
            (get_start_macro_map(context.scene), "Macro"),
            (get_end_macro_map(context.scene), "Macro"),
            (get_start_flash_macro_map(context.scene), "Macro"),
            (get_end_flash_macro_map(context.scene), "Macro"),
            (get_cue_map(context.scene), "Cue")
        ]

        commands = []
        event_strip = find_relevant_clock(context.scene)
        if event_strip == None:
            return {'CANCELLED'}
        event_list = event_strip.song_timecode_clock_number

        i = 1
        for action_map, description in all_maps:
            for frame in action_map:
                actions = action_map[frame]
                for label, index in actions:
                    fps = get_frame_rate(context.scene)
                    timecode = frame_to_timecode(self, frame, fps)
                    argument = f"Event {event_list} / {i} Time {timecode} Show_Control_Action {description} {index} Enter"
                    commands.append(argument)
                    i += 1
                    
        ip_address = context.scene.scene_props.str_osc_ip_address
        port = context.scene.scene_props.int_osc_port
        self.send_osc_command("/eos/key/blind", ip_address, port, "1")
        self.send_osc_command("/eos/key/blind", ip_address, port, "0")
        
        self.send_osc_command("/eos/newcmd", ip_address, port, f"Delete Event {event_list} / Enter Enter")
        self.send_osc_command("/eos/newcmd", ip_address, port, f"Event {event_list} / Enter Enter")
        
        for i in range(0, len(commands), 50):
            batch = commands[i:i+50]
            argument = ", ".join(batch)
            self.send_osc_command("/eos/newcmd", ip_address, port, argument)

        self.send_osc_command("/eos/key/live", ip_address, port, "1")
        self.send_osc_command("/eos/key/live", ip_address, port, "0")
        snapshot = str(context.scene.orb_finish_snapshot)
        self.send_osc_command("/eos/newcmd", ip_address, port, f"Snapshot {snapshot} Enter")
        return{'FINISHED'}

    def send_osc_command(self, address, ip, port, command):
        try:
            send_osc_string(address, ip, port, command)
            time.sleep(0.1)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to send OSC command: {e}")
            return {'CANCELLED'}


# Defines lists of strips with relevant enumerator and checkbox choices.
def filter_eos_cue_strips(sequences):
    return [strip for strip in sequences if strip.type == 'COLOR' and strip.my_settings.motif_type_enum == 'option_eos_cue' and not strip.mute]

def filter_animation_strips(sequences):
    return [strip for strip in sequences if strip.type == 'COLOR' and strip.my_settings.motif_type_enum == 'option_animation' and not strip.mute]

def filter_trigger_strips(sequences):
    return [strip for strip in sequences if strip.type == 'COLOR' and strip.my_settings.motif_type_enum == 'option_trigger' and not strip.mute]

def filter_timecode_learn_strips(sequences):
    return [strip for strip in sequences if strip.type == 'SOUND' and strip.song_timecode_clock_number != 0 and strip.my_learning_checkbox == True and not strip.mute]

def filter_timecode_strips(sequences):
    return [strip for strip in sequences if strip.type == 'SOUND' and strip.song_timecode_clock_number != 0 and strip.my_learning_checkbox == False and not strip.mute]

def filter_eos_macro_strips(sequences):
    return [strip for strip in sequences if strip.type == 'COLOR' and strip.my_settings.motif_type_enum == 'option_eos_macro' and not strip.mute]

def filter_eos_flash_strips(sequences):
    return [strip for strip in sequences if strip.type == 'COLOR' and strip.my_settings.motif_type_enum == 'option_eos_flash' and not strip.mute]


# Starts defining primary mapping functions.
def get_start_macro_map(scene):
    from collections import defaultdict
    mapping = defaultdict(list)
    start_macro_address = "/eos/macro/fire"    
    
    for strip in filter_eos_macro_strips(scene.sequence_editor.sequences):
        if not strip.start_macro_muted:
            data = (strip.name, str(strip.start_frame_macro))
            if data[0] and data[1]:
                mapping[strip.frame_start].append(data)
                        
    return dict(mapping)


def get_end_macro_map(scene):
    from collections import defaultdict
    mapping = defaultdict(list)
    end_macro_address = "/eos/macro/fire"    
    
    for strip in filter_eos_macro_strips(scene.sequence_editor.sequences):
                if not strip.end_macro_muted:
                    data = (strip.name, str(strip.end_frame_macro))
                    if data[0] and data[1]:
                        mapping[strip.frame_final_end].append(data)
                        
    return dict(mapping)


def get_start_flash_macro_map(scene):
    from collections import defaultdict
    mapping = defaultdict(list)
    start_flash_macro_address = "/eos/macro/fire"    
    
    for strip in filter_eos_flash_strips(scene.sequence_editor.sequences):
                data = (strip.name, str(strip.start_flash_macro_number))
                if data[0] and data[1]:
                    mapping[strip.frame_start].append(data)
                    
    return dict(mapping)


def get_end_flash_macro_map(scene):
    from collections import defaultdict
    mapping = defaultdict(list)
    end_flash_macro_address = "/eos/macro/fire"    
    
    for strip in filter_eos_flash_strips(scene.sequence_editor.sequences):
                data = (strip.name, str(strip.end_flash_macro_number))
                bias = strip.flash_bias
                frame_rate = get_frame_rate(scene)
                strip_length_in_frames = strip.frame_final_duration
                bias_in_frames = calculate_bias_offseter(bias, frame_rate, strip_length_in_frames)
                start_frame = strip.frame_start
                end_flash_macro_frame = start_frame + bias_in_frames
                end_flash_macro_frame = int(round(end_flash_macro_frame))
                
                if data[0] and data[1]:
                    mapping[end_flash_macro_frame].append(data)
                    
    return dict(mapping)


def get_trigger_start_map(scene):
    from collections import defaultdict
    mapping = defaultdict(list)

    for strip in filter_trigger_strips(scene.sequence_editor.sequences):
        # In the original Sequencer software, this used a background formatter property as [1].
        data = (strip.trigger_prefix, strip.osc_trigger)
        if data[0] and data[1]:
            mapping[strip.frame_start].append(data)

    return dict(mapping)


def get_trigger_offset_start_map(scene):
    from collections import defaultdict
    mapping = defaultdict(list)

    for strip in filter_trigger_strips(scene.sequence_editor.sequences):
        commands = get_offset_triggers(strip)
        if commands:
            strip_length = strip.frame_final_end - strip.frame_start  # Length of the strip
            num_commands = len(commands)
            step_value = strip_length / num_commands  # Gap between each command
            for index, command in enumerate(commands):
                offset_frame_start = strip.frame_start + int(step_value * index)
                mapping_entry = (strip.trigger_prefix, command)
                mapping[offset_frame_start].append(mapping_entry)

    return dict(mapping)


def get_trigger_end_map(scene):
    from collections import defaultdict
    mapping = defaultdict(list)

    for strip in filter_trigger_strips(scene.sequence_editor.sequences):
        data = (strip.trigger_prefix, strip.osc_trigger_end)
        if data[0] and data[1]:
            mapping[strip.frame_final_end].append(data)

    return dict(mapping)


def get_cue_map(scene):
    from collections import defaultdict
    mapping = defaultdict(list)
    
    for strip in filter_eos_cue_strips(scene.sequence_editor.sequences):
                data = (strip.name, strip.eos_cue_number)
                if strip.eos_cue_number == 0:
                    continue
                elif data[0] and data[1]:
                    mapping[strip.frame_start].append(data)

    return dict(mapping)

        
#Prevents user from setting timecode clock cue number to first cue on sequence to prevent infinite looping.
def timecode_clock_update_safety(self, context):
    sorted_strips = sorted([s for s in context.scene.sequence_editor.sequences_all if s.type == 'COLOR'], key=lambda s: s.frame_start)

    first_eos_cue_strip = None
    
    for strip in sorted_strips:
        if strip.my_settings.motif_type_enum == 'option_eos_cue':
            first_eos_cue_strip = strip
            break

    if first_eos_cue_strip and first_eos_cue_strip.eos_cue_number == self.execute_on_cue_number and self.execute_on_cue_number:
            self.execute_on_cue_number = 0
            print("Cue # for timecode clock cannot be equal to the first cue in the sequence. That will result in infinite looping. The console would go to cue " + str(self.execute_on_cue_number) + " and then the timecode clock would start, and then the timecode clock would immediately call the first cue, thereby starting the timecode clock over again. This would repeat forever without advancing to the next frames.")
            return
            
    
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


def is_linked_updater(self, context):
    active_strip = context.scene.sequence_editor.active_strip
    if active_strip and active_strip.is_linked and active_strip.my_settings.motif_type_enum == "option_animation":
        bpy.ops.wm.show_message('INVOKE_DEFAULT', message="Animation strips will not link as motifs.")


def custom_iris_prefix_updater(self, context):
    active_strip = context.scene.sequence_editor.active_strip
    global animation_string
    
    if active_strip.iris_prefix == animation_string:
        return
    
    animation_prefix_replacements = {
    "r": "/eos/*/param/gobo_index\speed",
    "rotate": "/eos/*/param/gobo_index\speed",
    "rot": "/eos/*/param/gobo_index\speed",
    "rot1": "/eos/*/param/gobo_index\speed",
    "rotate1": "/eos/*/param/gobo_index\speed",
    "r1": "/eos/*/param/gobo_index\speed",
    "rotrate": "/eos/*/param/gobo_index\speed",
    
    "r2": "/eos/*/param/gobo_index\speed_2",
    "rotate2": "/eos/*/param/gobo_index\speed_2",
    "rot2": "/eos/*/param/gobo_index\speed_2",
    "ro2": "/eos/*/param/gobo_index\speed_2",
    "rotte2": "/eos/*/param/gobo_index\speed_2",
    "rt2": "/eos/*/param/gobo_index\speed_2",
    "rotrate2": "/eos/*/param/gobo_index\speed_2",
    
    "s": "/eos/*/param/shutter_strobe",
    "ss": "/eos/*/param/shutter_strobe",
    "shutter": "/eos/*/param/shutter_strobe",
    "st": "/eos/*/param/shutter_strobe",
    "shutterstrbe": "/eos/*/param/shutter_strobe",
    "shutterstrobe": "/eos/*/param/shutter_strobe",
    "shuterstrobe": "/eos/*/param/shutter_strobe",
    
    "x": "/eos/*/param/x_focus",
    "xf": "/eos/*/param/x_focus",
    "xfocus": "/eos/*/param/x_focus",
    
    "y": "/eos/*/param/y_focus",
    "yf": "/eos/*/param/y_focus",
    "yfocus": "/eos/*/param/y_focus",
    
    "z": "/eos/*/param/z_focus",
    "zf": "/eos/*/param/z_focus",
    "zfocus": "/eos/*/param/z_focus",
    
    "e": "/eos/*/param/edge",
    "ed": "/eos/*/param/edge",
    "edge": "/eos/*/param/edge",
    "ege": "/eos/*/param/edge",
    "ede": "/eos/*/param/edge",
    "ee": "/eos/*/param/edge",
    
    "i": "/eos/*",
    "int": "/eos/*",
    "intensity": "/eos/*",
    
    "p": "/eos/*/param/pan",
    "pn": "/eos/*/param/pan",
    "pan": "/eos/*/param/pan",
    
    "t": "/eos/*/param/tilt",
    "tilt": "/eos/*/param/tilt",
    "til": "/eos/*/param/tilt",
    "tit": "/eos/*/param/tilt",
    "tt": "/eos/*/param/tilt",
    
    "iris": "/eos/*/param/iris",
    "is": "/eos/*/param/iris",
    "irs": "/eos/*/param/iris",
    
    "zoom": "/eos/*/param/zoom",
    "zom": "/eos/*/param/zoom",
    "zm": "/eos/*/param/zoom",
}

    animation_string = self.iris_prefix.lower()
    animation_string = animation_string.replace(" ", "")
    words = animation_string.split()
    formatted_words = [animation_prefix_replacements.get(word, word) for word in words]
    animation_string = " ".join(formatted_words)
    active_strip.iris_prefix = str(animation_string)


def custom_zoom_prefix_updater(self, context):
    active_strip = context.scene.sequence_editor.active_strip
    global animation_string
    
    if active_strip.zoom_prefix == animation_string:
        return
    
    animation_prefix_replacements = {
    "r": "/eos/*/param/gobo_index\speed",
    "rotate": "/eos/*/param/gobo_index\speed",
    "rot": "/eos/*/param/gobo_index\speed",
    "rot1": "/eos/*/param/gobo_index\speed",
    "rotate1": "/eos/*/param/gobo_index\speed",
    "r1": "/eos/*/param/gobo_index\speed",
    "rotrate": "/eos/*/param/gobo_index\speed",
    
    "r2": "/eos/*/param/gobo_index\speed_2",
    "rotate2": "/eos/*/param/gobo_index\speed_2",
    "rot2": "/eos/*/param/gobo_index\speed_2",
    "ro2": "/eos/*/param/gobo_index\speed_2",
    "rotte2": "/eos/*/param/gobo_index\speed_2",
    "rt2": "/eos/*/param/gobo_index\speed_2",
    "rotrate2": "/eos/*/param/gobo_index\speed_2",
    
    "s": "/eos/*/param/shutter_strobe",
    "ss": "/eos/*/param/shutter_strobe",
    "shutter": "/eos/*/param/shutter_strobe",
    "st": "/eos/*/param/shutter_strobe",
    "shutterstrbe": "/eos/*/param/shutter_strobe",
    "shutterstrobe": "/eos/*/param/shutter_strobe",
    "shuterstrobe": "/eos/*/param/shutter_strobe",
    
    "x": "/eos/*/param/x_focus",
    "xf": "/eos/*/param/x_focus",
    "xfocus": "/eos/*/param/x_focus",
    
    "y": "/eos/*/param/y_focus",
    "yf": "/eos/*/param/y_focus",
    "yfocus": "/eos/*/param/y_focus",
    
    "z": "/eos/*/param/z_focus",
    "zf": "/eos/*/param/z_focus",
    "zfocus": "/eos/*/param/z_focus",
    
    "e": "/eos/*/param/edge",
    "ed": "/eos/*/param/edge",
    "edge": "/eos/*/param/edge",
    "ege": "/eos/*/param/edge",
    "ede": "/eos/*/param/edge",
    "ee": "/eos/*/param/edge",
    
    "i": "/eos/*",
    "int": "/eos/*",
    "intensity": "/eos/*",
    
    "p": "/eos/*/param/pan",
    "pn": "/eos/*/param/pan",
    "pan": "/eos/*/param/pan",
    
    "t": "/eos/*/param/tilt",
    "tilt": "/eos/*/param/tilt",
    "til": "/eos/*/param/tilt",
    "tit": "/eos/*/param/tilt",
    "tt": "/eos/*/param/tilt",
    
    "iris": "/eos/*/param/iris",
    "is": "/eos/*/param/iris",
    "irs": "/eos/*/param/iris",
    
    "zoom": "/eos/*/param/zoom",
    "zom": "/eos/*/param/zoom",
    "zm": "/eos/*/param/zoom",
}

    animation_string = self.zoom_prefix.lower()
    animation_string = animation_string.replace(" ", "")
    words = animation_string.split()
    formatted_words = [animation_prefix_replacements.get(word, word) for word in words]
    animation_string = " ".join(formatted_words)
    active_strip.zoom_prefix = str(animation_string)


def flash_input_updater(self, context):
    sequence_editor = context.scene.sequence_editor
    if sequence_editor and sequence_editor.active_strip and sequence_editor.active_strip.type == 'COLOR':

        active_strip = context.scene.sequence_editor.active_strip
        
        space_replacements = {
        "color palete": "colorpalete",
        "c palette": "cpalette",
        "color p": "colorp",
        "c palete": "cpalete",
        "color pallee": "colorpallee",
        "cc palletee": "ccpalletee",
        "colopr pallete": "coloprpallete",
        "color palletee": "colorpalletee",
        "color pallete": "colorpallete",
        
        "beam palete": "beampalete",
        "b palette": "bpalette",
        "beem p": "beemp",
        "baam p": "baamp",
        "beam palatte": "beampalatte",
        "beam palette": "beampalette",
        "bm p": "bmp",
        "bm pallete": "bmpallete",
        "bem pallette": "bempallette",
        "bam p": "bamp",
        
        "focus palete": "focuspalete",
        "f palette": "fpalette",
        "focuss p": "focussp",
        "fcs p": "fcsp",
        "fcs": "fcs",
        "focus palette": "focuspalette",
        "fs p": "fsp",
        "fs pallete": "fspallete",
        "focs pallette": "focspallette",
        "fcus p": "fcusp",
        
        "intensity palete": "intensitypalete",
        "i palette": "ipalette",
        "intsety p": "intsetyp",
        "intensity p": "intensityp",
        "intensity palatte": "intensitypalatte",
        "ntensity palette": "ntensitypalette",
        "i pallete": "ipallete",
        "int pallette": "intpallette",
        "int p": "intp",
    }
             
        replacements = {
            "cp": "Color_Palette",
            "colorpalete": "Color_Palette",
            "color": "Color_Palette",
            "cpalette": "Color_Palette",
            "colorp": "Color_Palette",
            "cpalete": "Color_Palette",
            "c": "Color_Palette",
            "colorpallee": "Color_Palette",
            "ccpalletee": "Color_Palette",
            "coloprpallete": "Color_Palette",
            "colorpalletee": "Color_Palette",
            "colorpallete": "Color_Palette",
            "colorpalette": "Color_Palette",
            
            "b": "Beam_Palette",
            "bp": "Beam_Palette",
            "beampalete": "Beam_Palette",
            "beam": "Beam_Palette",
            "bpalette": "Beam_Palette",
            "beemp": "Beam_Palette",
            "baamp": "Beam_Palette",
            "beampalatte": "Beam_Palette",
            "beampalette": "Beam_Palette",
            "bmp": "Beam_Palette",
            "bmpallete": "Beam_Palette",
            "bempallette": "Beam_Palette",
            "bamp": "Beam_Palette",
            
            "f": "Focus_Palette",
            "bp": "Focus_Palette",
            "focuspalete": "Focus_Palette",
            "focus": "Focus_Palette",
            "fpalette": "Focus_Palette",
            "focussp": "Focus_Palette",
            "fcsp": "Focus_Palette",
            "fcs": "Focus_Palette",
            "focuspalette": "Focus_Palette",
            "fsp": "Focus_Palette",
            "fspallete": "Focus_Palette",
            "focspallette": "Focus_Palette",
            "fcusp": "Focus_Palette",
            
            "i": "Intensity_Palette",
            "ip": "Intensity_Palette",
            "intensitypalete": "Intensity_Palette",
            "intensity": "Intensity_Palette",
            "ipalette": "Intensity_Palette",
            "intsetyp": "Intensity_Palette",
            "intensityp": "Intensity_Palette",
            "intensitypalatte": "Intensity_Palette",
            "ntensitypalette": "Intensity_Palette",
            "ip": "Intensity_Palette",
            "ipallete": "Intensity_Palette",
            "intpallette": "Intensity_Palette",
            "intp": "Intensity_Palette",
            
            "preset": "Preset",
            "p": "Preset",
            "pt": "Preset",
            "prst": "Preset",
            "prset": "Preset",
            "perset": "Preset",
            "prets": "Preset",
            "preseet": "Preset",
            "pst": "Preset",
            "preest": "Preset",
            
            "sub": "Submaster",
            "sb": "Submaster",
            "submaster": "Submaster",
            "s": "Submaster",
            "submastr": "Submaster",
            "submasster": "Submaster",
            "submastwer": "Submaster",
            "subb": "Submaster",

            "full": "at Full",
            "fll": "at Full",
            "fuull": "at Full",
            "fl": "at Full",
            "ful": "at Full",
            "ffl": "at Full",
            
            "out": "0",
            "ot": "0",
            "outt": "0",
            
            "group": "Group",
            "gruop": "Group",
            "grp": "Group",
            "gp": "Group",
            "g": "Group",
            "grup": "Group",
            
            "thr": "thru",
            "through": "thru",
            "throuhg": "thru",
            "tru": "thru",
            "t": "thru"
        }

        # Get the input string and make it lowercase.
        input_string = self.flash_input.lower()

        # Apply space replacements first to combine common multi-word phrases into single tokens.
        for key, value in space_replacements.items():
            input_string = input_string.replace(key, value)

        # Replace hyphen between numbers with 'thru'.
        input_string = re.sub(r'(\d+)\s*-\s*(\d+)', r'\1 thru \2', input_string)
        
        # Replace commas followed by spaces with ' + '.
        input_string = re.sub(r',\s*', ' + ', input_string)
        
        # Insert space between letters and numbers.
        input_string = re.sub(r'(\D)(\d)', r'\1 \2', input_string)
        input_string = re.sub(r'(\d)(\D)', r'\1 \2', input_string)

        words = input_string.split()

        # Apply the main replacements.
        formatted_words = [replacements.get(word, word) for word in words]

        # Handle specific cases like adding "Channel" at the start if needed.
        if formatted_words and formatted_words[0].isdigit():
            formatted_words.insert(0, "Channel")

        # Combine the words back into a single string.
        formatted_command = " ".join(formatted_words)

        # Replace any double "at".
        formatted_command = re.sub(r'\bat at\b', "at", formatted_command)
        
        # Iterate over the words to replace consecutive numbers with 'at' in between.
        new_formatted_words = []
        i = 0
        while i < len(formatted_words):
            new_formatted_words.append(formatted_words[i])
            if (i + 1 < len(formatted_words) and
                    formatted_words[i].isdigit() and
                    formatted_words[i + 1].isdigit()):
                # Check if the next word is 'at' to avoid 'at at'.
                if formatted_words[i + 1] != 'at':
                    new_formatted_words.append("at")
            i += 1

        # Join the modified list back into a string.
        formatted_command = " ".join(new_formatted_words)

        # Replace any occurrence of "at at" with just "at".
        formatted_command = formatted_command.replace("at at", "at")
        
        # If 'at' is not in the command, add 'at Full' to the end.
        if ' at ' not in formatted_command and 'Palette' not in formatted_command and 'Preset' not in formatted_command and not formatted_command.endswith(' at'):
            formatted_command += ' at Full'
        
        final_command = str(formatted_command)

        # Set the background property with the formatted command.
        active_strip.flash_input_background = final_command

        # Assign the formatted command to the background property.
        active_strip.flash_input_background = formatted_command
        
        # Assign the prefix for OSC.
        active_strip.flash_prefix = "eos"
    
    
def flash_down_input_updater(self, context):
    sequence_editor = context.scene.sequence_editor
    if sequence_editor and sequence_editor.active_strip and sequence_editor.active_strip.type == 'COLOR':

        active_strip = context.scene.sequence_editor.active_strip
        
        space_replacements = {
        "color palete": "colorpalete",
        "c palette": "cpalette",
        "color p": "colorp",
        "c palete": "cpalete",
        "color pallee": "colorpallee",
        "cc palletee": "ccpalletee",
        "colopr pallete": "coloprpallete",
        "color palletee": "colorpalletee",
        "color pallete": "colorpallete",
        
        "beam palete": "beampalete",
        "b palette": "bpalette",
        "beem p": "beemp",
        "baam p": "baamp",
        "beam palatte": "beampalatte",
        "beam palette": "beampalette",
        "bm p": "bmp",
        "bm pallete": "bmpallete",
        "bem pallette": "bempallette",
        "bam p": "bamp",
        
        "focus palete": "focuspalete",
        "f palette": "fpalette",
        "focuss p": "focussp",
        "fcs p": "fcsp",
        "fcs": "fcs",
        "focus palette": "focuspalette",
        "fs p": "fsp",
        "fs pallete": "fspallete",
        "focs pallette": "focspallette",
        "fcus p": "fcusp",
        
        "intensity palete": "intensitypalete",
        "i palette": "ipalette",
        "intsety p": "intsetyp",
        "intensity p": "intensityp",
        "intensity palatte": "intensitypalatte",
        "ntensity palette": "ntensitypalette",
        "i pallete": "ipallete",
        "int pallette": "intpallette",
        "int p": "intp",
    }
        
        replacements = {
            "cp": "Color_Palette",
            "colorpalete": "Color_Palette",
            "color": "Color_Palette",
            "cpalette": "Color_Palette",
            "colorp": "Color_Palette",
            "cpalete": "Color_Palette",
            "c": "Color_Palette",
            "colorpallee": "Color_Palette",
            "ccpalletee": "Color_Palette",
            "coloprpallete": "Color_Palette",
            "colorpalletee": "Color_Palette",
            "colorpallete": "Color_Palette",
            "colorpalette": "Color_Palette",
            
            "b": "Beam_Palette",
            "bp": "Beam_Palette",
            "beampalete": "Beam_Palette",
            "beam": "Beam_Palette",
            "bpalette": "Beam_Palette",
            "beemp": "Beam_Palette",
            "baamp": "Beam_Palette",
            "beampalatte": "Beam_Palette",
            "beampalette": "Beam_Palette",
            "bmp": "Beam_Palette",
            "bmpallete": "Beam_Palette",
            "bempallette": "Beam_Palette",
            "bamp": "Beam_Palette",
            
            "f": "Focus_Palette",
            "bp": "Focus_Palette",
            "focuspalete": "Focus_Palette",
            "focus": "Focus_Palette",
            "fpalette": "Focus_Palette",
            "focussp": "Focus_Palette",
            "fcsp": "Focus_Palette",
            "fcs": "Focus_Palette",
            "focuspalette": "Focus_Palette",
            "fsp": "Focus_Palette",
            "fspallete": "Focus_Palette",
            "focspallette": "Focus_Palette",
            "fcusp": "Focus_Palette",
            
            "i": "Intensity_Palette",
            "ip": "Intensity_Palette",
            "intensitypalete": "Intensity_Palette",
            "intensity": "Intensity_Palette",
            "ipalette": "Intensity_Palette",
            "intsetyp": "Intensity_Palette",
            "intensityp": "Intensity_Palette",
            "intensitypalatte": "Intensity_Palette",
            "ntensitypalette": "Intensity_Palette",
            "ip": "Intensity_Palette",
            "ipallete": "Intensity_Palette",
            "intpallette": "Intensity_Palette",
            "intp": "Intensity_Palette",
            
            "preset": "Preset",
            "p": "Preset",
            "pt": "Preset",
            "prst": "Preset",
            "prset": "Preset",
            "perset": "Preset",
            "prets": "Preset",
            "preseet": "Preset",
            "pst": "Preset",
            "preest": "Preset",
            
            "sub": "Submaster",
            "sb": "Submaster",
            "submaster": "Submaster",
            "s": "Submaster",
            "submastr": "Submaster",
            "submasster": "Submaster",
            "submastwer": "Submaster",
            "subb": "Submaster",

            "full": "at Full",
            "fll": "at Full",
            "fuull": "at Full",
            "fl": "at Full",
            "ful": "at Full",
            "ffl": "at Full",
            
            "out": "0",
            "ot": "0",
            "outt": "0",
            
            "group": "Group",
            "gruop": "Group",
            "grp": "Group",
            "gp": "Group",
            "g": "Group",
            "grup": "Group",
            
            "thr": "thru",
            "through": "thru",
            "throuhg": "thru",
            "tru": "thru",
            "t": "thru"
        }

        # Get the input string and make it lowercase.
        input_string = self.flash_down_input.lower()

        # Apply space replacements first to combine common multi-word phrases into single tokens.
        for key, value in space_replacements.items():
            input_string = input_string.replace(key, value)

        # Replace hyphen between numbers with 'thru'.
        input_string = re.sub(r'(\d+)\s*-\s*(\d+)', r'\1 thru \2', input_string)
        
        # Replace commas followed by spaces with ' + '.
        input_string = re.sub(r',\s*', ' + ', input_string)
        
        # Insert space between letters and numbers.
        input_string = re.sub(r'(\D)(\d)', r'\1 \2', input_string)
        input_string = re.sub(r'(\d)(\D)', r'\1 \2', input_string)

        # Split the input string into words.
        words = input_string.split()

        # Apply the main replacements.
        formatted_words = [replacements.get(word, word) for word in words]

        # Handle specific cases like adding "Channel" at the start if needed.
        if formatted_words and formatted_words[0].isdigit():
            formatted_words.insert(0, "Channel")

        # Combine the words back into a single string.
        formatted_command = " ".join(formatted_words)

        # Replace any double "at".
        formatted_command = re.sub(r'\bat at\b', "at", formatted_command)
        
        # Iterate over the words to replace consecutive numbers with 'at' in between.
        new_formatted_words = []
        i = 0
        while i < len(formatted_words):
            new_formatted_words.append(formatted_words[i])
            if (i + 1 < len(formatted_words) and
                    formatted_words[i].isdigit() and
                    formatted_words[i + 1].isdigit()):
                # Check if the next word is 'at' to avoid 'at at'.
                if formatted_words[i + 1] != 'at':
                    new_formatted_words.append("at")
            i += 1

        # Join the modified list back into a string.
        formatted_command = " ".join(new_formatted_words)

        # Replace any occurrence of "at at" with just "at".
        formatted_command = formatted_command.replace("at at", "at")
        
        # If 'at' is not in the command, add 'at Full' to the end.
        if ' at ' not in formatted_command and 'Palette' not in formatted_command and 'Preset' not in formatted_command and not formatted_command.endswith(' at'):
            formatted_command += ' at 0'
        
        final_command = str(formatted_command)

        # Set the background property with the formatted command.
        active_strip.flash_down_input_background = final_command

        # Assign the formatted command to the background property.
        active_strip.flash_down_input_background = formatted_command
        
        # Assign the prefix for OSC.
        active_strip.flash_prefix = "eos"
        

def flash_motif_property_updater(self, context):
    active_strip = context.scene.sequence_editor.active_strip
    
    if self != active_strip:
        return
    
    strip = self

    if active_strip and active_strip.type == 'COLOR':
        name  = active_strip.name
        motif_name = active_strip.motif_name

        start_flash = active_strip.start_flash_macro_number
        end_flash = active_strip.end_flash_macro_number
        bias = active_strip.flash_bias
        link_status = active_strip.is_linked
        flash_input = active_strip.flash_input
        flash_down_input = active_strip.flash_down_input

        for strip in filter_color_strips(bpy.context.scene.sequence_editor.sequences_all):
            if strip != active_strip and strip.is_linked and strip.motif_name == motif_name:
                if (
                    strip.start_flash_macro_number == active_strip.start_flash_macro_number and
                    strip.end_flash_macro_number == active_strip.end_flash_macro_number and
                    strip.flash_bias == active_strip.flash_bias and
                    strip.flash_input == active_strip.flash_input and
                    strip.flash_down_input == active_strip.flash_down_input
                ): #why so sad?
                    return

                strip.start_flash_macro_number = start_flash
                strip.end_flash_macro_number = end_flash
                strip.flash_bias = bias
                strip.flash_input = flash_input
                strip.flash_down_input = flash_down_input
                
                if link_status == True:
                    strip.is_linked = True
                else:
                    strip.is_linked = False
                    
                                 
def cue_motif_property_updater(self, context):
    active_strip = context.scene.sequence_editor.active_strip
    
    if self != active_strip:
        return
    
    strip = self

    if active_strip and active_strip.type == 'COLOR':
        name  = active_strip.name
        motif_name = active_strip.motif_name
        eos_cue_number = active_strip.eos_cue_number
        link_status = active_strip.is_linked
        
        for strip in filter_color_strips(bpy.context.scene.sequence_editor.sequences_all):
            if strip != active_strip and strip.is_linked and strip.motif_name == motif_name:
                if strip.eos_cue_number == active_strip.eos_cue_number:
                    return

                strip.eos_cue_number = eos_cue_number
                
                if link_status == True:
                    strip.is_linked = True
                else:
                    strip.is_linked = False
                    
              
def trigger_motif_property_updater(self, context):
    active_strip = context.scene.sequence_editor.active_strip
    
    if self != active_strip:
        return
    
    strip = self

    if active_strip and active_strip.type == 'COLOR':
        name  = active_strip.name
        motif_name = active_strip.motif_name
        color  = active_strip.color
        length = active_strip.frame_final_duration
        enumerator_choice = active_strip.my_settings.motif_type_enum  
        trigger_prefix = active_strip.trigger_prefix
        osc_trigger = active_strip.osc_trigger
        osc_trigger_end = active_strip.osc_trigger_end
        link_status = active_strip.is_linked

        for strip in filter_color_strips(bpy.context.scene.sequence_editor.sequences_all):
            if strip != active_strip and strip.is_linked and strip.motif_name == motif_name:
                if (
                    strip.trigger_prefix == active_strip.trigger_prefix and
                    strip.osc_trigger == active_strip.osc_trigger and
                    strip.osc_trigger_end == active_strip.osc_trigger_end
                ): #why so sad?
                    return

                strip.name = name
                strip.color = color
                strip.frame_final_duration = length
                strip.my_settings.motif_type_enum = enumerator_choice
                strip.trigger_prefix = trigger_prefix
                strip.osc_trigger = osc_trigger
                strip.osc_trigger_end = osc_trigger_end
                
                if link_status == True:
                    strip.is_linked = True
                else:
                    strip.is_linked = False
                    
                                     
def macro_motif_property_updater(self, context):
    active_strip = context.scene.sequence_editor.active_strip
    
    if self != active_strip:
        return
    
    strip = self

    if active_strip and active_strip.type == 'COLOR':
        name  = active_strip.name
        motif_name = active_strip.motif_name
        color  = active_strip.color
        length = active_strip.frame_final_duration
        enumerator_choice = active_strip.my_settings.motif_type_enum
        
        start_frame_macro = active_strip.start_frame_macro
        end_frame_macro = active_strip.end_frame_macro
        friend_list = active_strip.friend_list
        link_status = active_strip.is_linked
        
        for strip in filter_color_strips(bpy.context.scene.sequence_editor.sequences_all):
            if strip != active_strip and strip.is_linked and strip.motif_name == motif_name:
                if (
                    strip.start_frame_macro == active_strip.start_frame_macro and
                    strip.end_frame_macro == active_strip.end_frame_macro and
                    strip.friend_list == active_strip.friend_list
                ): #why so sad?
                    return

                strip.name = name
                strip.color = color
                strip.frame_final_duration = length
                strip.my_settings.motif_type_enum = enumerator_choice
            
                strip.start_frame_macro = start_frame_macro
                strip.end_frame_macro = end_frame_macro
                strip.friend_list = friend_list
                
                if link_status == True:
                    strip.is_linked = True
                else:
                    strip.is_linked = False


def enum_items(self, context):

    items = [
        ('option_eos_macro', "Macro", "Build and fire macros based on strip length", 'REC', 0),
        ('option_eos_cue', "Cue", "Use strip length to define cue duration", 'PLAY', 1),
        ('option_eos_flash', "Flash", "Flash intensity up and down with strip length", 'LIGHT_SUN', 2)
    ]

    if context.scene.animation_enabled:
        items.append(('option_animation', "Animation", "Use keyframes, or inverted cues, to control parameters. Eos does not record this", 'IPO_BEZIER', 3))
        
    if context.scene.triggers_enabled:
        items.append(('option_trigger', "Trigger", "Send discrete trigger at strip's start and/or end frame. Eos does not record this", 'SETTINGS', 4))

    return items


def motif_type_enum_updater(self, context):
    active_strip = context.scene.sequence_editor.active_strip
    motif_type_enum = context.scene.sequence_editor.active_strip.my_settings.motif_type_enum
    
    global stop_updating_color
    if stop_updating_color == "No" and context.scene.is_updating_strip_color:
        
        if motif_type_enum == "option_eos_macro":
            active_strip.color = (1, 0, 0)
        elif motif_type_enum == "option_eos_cue":
            active_strip.color = (0, 0, .5)
        elif motif_type_enum == "option_eos_flash":
            active_strip.color = (1, 1, 0)
        elif motif_type_enum == "option_animation":
            active_strip.color = (0, 1, 0)
        else:
            active_strip.color = (1, 1, 1)


def motif_names_updater(self, context):
    chosen_motif_name = context.scene.my_tool.motif_names_enum
    sequences_all = context.scene.sequence_editor.sequences_all
    
    for strip in sequences_all:
        strip.select = False
    
    for strip in filter_color_strips(sequences_all):
        if strip.motif_name == chosen_motif_name:
            context.scene.sequence_editor.active_strip = strip 
            strip.select = True 
            break
        
    for strip in filter_color_strips(bpy.context.scene.sequence_editor.sequences_all):
        if strip.motif_name == chosen_motif_name:
            strip.select = True
            
        
def color_palette_color_updater(self, context):
    ip_address = context.scene.scene_props.str_osc_ip_address
    port = context.scene.scene_props.int_osc_port
    scene = bpy.context.scene
    
    if scene.preview_color_palette:
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
        
        argument = "Chan 1 thru thru 1000 Red " + str(cp_red) + " Enter"
        send_osc_string(newcmd, ip_address, port, argument)
        
        argument = "Chan 1 thru thru 1000 Green " + str(cp_green) + " Enter"
        send_osc_string(newcmd, ip_address, port, argument)
        
        argument = "Chan 1 thru thru 1000 Amber 0 Enter"
        send_osc_string(newcmd, ip_address, port, argument)
        
        argument = "Chan 1 thru thru 1000 Mint 0 Enter"
        send_osc_string(newcmd, ip_address, port, argument)
        
        if cp_red + cp_green + cp_blue != 300:
            argument = "Chan 1 thru thru 1000 White 0 Enter"
            send_osc_string(newcmd, ip_address, port, argument)
        else: 
            argument = "Chan 1 thru thru 1000 White 100 Enter"
            send_osc_string(newcmd, ip_address, port, argument)
        
        argument = "Chan 1 thru thru 1000 Blue " + str(cp_blue) + " Enter"
        send_osc_string(newcmd, ip_address, port, argument)  
        
                     
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

      
def key_light_updater(self, context):
    scene = context.scene
    if context.screen:
        if self.mute:
            return
        
        groups = parse_builder_groups(scene.key_light_groups)
        key_light = str(self.key_light)
        
        for group in groups:
            address = "/eos/newcmd"
            if len(key_light) == 1:
                argument = str("Group " + str(group) + " at 0" + str(key_light) + " Enter")
            else:
                argument = str("Group " + str(group) + " at " + str(key_light) + " Enter")

            ip_address = context.scene.scene_props.str_osc_ip_address
            port = context.scene.scene_props.int_osc_port
            send_osc_string(address, ip_address, port, argument)
    return
    
    
def rim_light_updater(self, context):
    scene = context.scene
    if context.screen:
        if self.mute:
            return
        
        groups = parse_builder_groups(scene.rim_light_groups)
        rim_light = str(self.rim_light)
        
        for group in groups:
            address = "/eos/newcmd"
            if len(rim_light) == 1:
                argument = str("Group " + str(group) + " at 0" + str(rim_light) + " Enter")
            else:
                argument = str("Group " + str(group) + " at " + str(rim_light) + " Enter")
 
            ip_address = context.scene.scene_props.str_osc_ip_address
            port = context.scene.scene_props.int_osc_port
            send_osc_string(address, ip_address, port, argument)
    return
    
    
def fill_light_updater(self, context):
    scene = context.scene
    if context.screen:
        if self.mute:
            return
        
        groups = parse_builder_groups(scene.fill_light_groups)
        fill_light = str(self.fill_light)
        
        for group in groups:
            address = "/eos/newcmd"
            if len(fill_light) == 1:
                argument = str("Group " + str(group) + " at 0" + str(fill_light) + " Enter")
            else:
                argument = str("Group " + str(group) + " at " + str(fill_light) + " Enter")

            
            ip_address = context.scene.scene_props.str_osc_ip_address
            port = context.scene.scene_props.int_osc_port
        
            send_osc_string(address, ip_address, port, argument)
    return
    
    
def texture_light_updater(self, context):
    scene = context.scene
    if context.screen:
        if self.mute:
            return
        
        groups = parse_builder_groups(scene.texture_light_groups)
        texture_light = str(self.texture_light)
        
        for group in groups:
            address = "/eos/newcmd"
            if len(texture_light) == 1:
                argument = str("Group " + str(group) + " at 0" + str(texture_light) + " Enter")
            else:
                argument = str("Group " + str(group) + " at " + str(texture_light) + " Enter")
           
            ip_address = context.scene.scene_props.str_osc_ip_address
            port = context.scene.scene_props.int_osc_port
            send_osc_string(address, ip_address, port, argument)
    return
    
        
def band_light_updater(self, context):
    scene = context.scene
    if context.screen:      
        if self.mute:
            return
        
        groups = parse_builder_groups(scene.band_light_groups)
        band_light = str(self.band_light)
        
        for group in groups:
            address = "/eos/newcmd"
            if len(band_light) == 1:
                argument = str("Group " + str(group) + " at 0" + str(band_light) + " Enter")
            else:
                argument = str("Group " + str(group) + " at " + str(band_light) + " Enter")
            
            ip_address = context.scene.scene_props.str_osc_ip_address
            port = context.scene.scene_props.int_osc_port       
            send_osc_string(address, ip_address, port, argument)
    return
        
    
def accent_light_updater(self, context):
    scene = context.scene
    if context.screen:       
        if self.mute:
            return
        
        groups = parse_builder_groups(scene.accent_light_groups)
        accent_light = str(self.accent_light)
        
        for group in groups:
            address = "/eos/newcmd"
            if len(accent_light) == 1:
                argument = str("Group " + str(group) + " at 0" + str(accent_light) + " Enter")
            else:
                argument = str("Group " + str(group) + " at " + str(accent_light) + " Enter")
           
            ip_address = context.scene.scene_props.str_osc_ip_address
            port = context.scene.scene_props.int_osc_port        
            send_osc_string(address, ip_address, port, argument)
    return
        
    
def energy_light_updater(self, context):
    scene = context.scene
    if context.screen:       
        if self.mute:
            return
        
        groups = parse_builder_groups(scene.energy_light_groups)
        energy_light = str(self.energy_light)
        
        for group in groups:
            address = "/eos/newcmd"
            if len(energy_light) == 1:
                argument = str("Group " + str(group) + " at 0" + str(energy_light) + " Enter")
            else:
                argument = str("Group " + str(group) + " at " + str(energy_light) + " Enter")
            
            ip_address = context.scene.scene_props.str_osc_ip_address
            port = context.scene.scene_props.int_osc_port        
            send_osc_string(address, ip_address, port, argument)
    return


def energy_speed_updater(self, context):
    scene = context.scene
    if context.screen:       
        if self.mute:
            return
        
        energy_speed = str(self.energy_speed)
        address = "/eos/newcmd"
        
        if len(energy_speed) == 1:
            argument = str("Effect " + str(self.cue_builder_effect_id) + " Rate 0" + energy_speed + " Enter")
        else:
            argument = str("Effect " + str(self.cue_builder_effect_id) + " Rate " + energy_speed + " Enter")

        ip_address = context.scene.scene_props.str_osc_ip_address
        port = context.scene.scene_props.int_osc_port    
        send_osc_string(address, ip_address, port, argument)
    return


def energy_scale_updater(self, context):
    scene = context.scene
    if context.screen:        
        if self.mute:
            return
        
        energy_scale = str(self.energy_scale)
        address = "/eos/newcmd"
        
        if len(energy_scale) == 1:
            argument = str("Effect " + str(self.cue_builder_effect_id) + " Scale 0" + energy_scale + " Enter")
        else:
            argument = str("Effect " + str(self.cue_builder_effect_id) + " Scale " + energy_scale + " Enter")

        
        ip_address = context.scene.scene_props.str_osc_ip_address
        port = context.scene.scene_props.int_osc_port    
        send_osc_string(address, ip_address, port, argument)       
    return
    
     
def background_light_updater(self, context):
    scene = context.scene
    if context.screen:        
        if self.mute:
            return
        
        groups = parse_builder_groups(scene.cyc_light_groups)
        background_light = str(self.background_light_one)
        
        for group in groups:
            address = "/eos/newcmd"
            if len(background_light) == 1:
                argument = str("Group " + str(group) + " at 0" + str(background_light) + " Enter")
            else:
                argument = str("Group " + str(group) + " at " + str(background_light) + " Enter")
            
            ip_address = context.scene.scene_props.str_osc_ip_address
            port = context.scene.scene_props.int_osc_port        
            send_osc_string(address, ip_address, port, argument)
    return


def background_two_light_updater(self, context):
    scene = context.scene
    if context.screen:    
        if self.mute:
            return
        
        groups = parse_builder_groups(scene.cyc_two_light_groups)
        background_two_light = str(self.background_light_two)
        
        for group in groups:
            address = "/eos/newcmd"
            if len(background_two_light) == 1:
                argument = str("Group " + str(group) + " at 0" + str(background_two_light) + " Enter")
            else:
                argument = str("Group " + str(group) + " at " + str(background_two_light) + " Enter")
            
            ip_address = context.scene.scene_props.str_osc_ip_address
            port = context.scene.scene_props.int_osc_port        
            send_osc_string(address, ip_address, port, argument)
    return
       
    
def background_three_light_updater(self, context):
    scene = context.scene
    if context.screen:        
        if self.mute:
            return
        
        groups = parse_builder_groups(scene.cyc_three_light_groups)
        background_three_light = str(self.background_light_three)
        
        for group in groups:
            address = "/eos/newcmd"
            if len(background_three_light) == 1:
                argument = str("Group " + str(group) + " at 0" + str(background_three_light) + " Enter")
            else:
                argument = str("Group " + str(group) + " at " + str(background_three_light) + " Enter")
            
            ip_address = context.scene.scene_props.str_osc_ip_address
            port = context.scene.scene_props.int_osc_port        
            send_osc_string(address, ip_address, port, argument)
    return
        

def background_four_light_updater(self, context):
    scene = context.scene
    if context.screen:       
        if self.mute:
            return
        
        groups = parse_builder_groups(scene.cyc_four_light_groups)
        background_four_light = str(self.background_light_four)
        
        for group in groups:
            address = "/eos/newcmd"
            if len(background_four_light) == 1:
                argument = str("Group " + str(group) + " at 0" + str(background_four_light) + " Enter")
            else:
                argument = str("Group " + str(group) + " at " + str(background_four_light) + " Enter")
            
            ip_address = context.scene.scene_props.str_osc_ip_address
            port = context.scene.scene_props.int_osc_port        
            send_osc_string(address, ip_address, port, argument)
    return


# This function remains mostly unchanged but now also returns the step to help with the concurrent commands.
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


# New function to parse and group concurrent commands.
def parse_concurrent_commands(input_string):
    # Split input by parentheses to identify concurrent groups.
    concurrent_groups = re.findall(r'\(([^)]+)\)', input_string)
    concurrent_commands = []
    
    # Parse each group separately.
    for group in concurrent_groups:
        channels = parse_channels(group)
        concurrent_commands.append(channels)
    
    # If there are no concurrent groups, treat the entire input as sequential.
    if not concurrent_commands:
        concurrent_commands.append(parse_channels(input_string))
    
    return concurrent_commands


# Generate command strings for concurrent commands.
def generate_concurrent_command_strings(command, concurrent_commands):
    command_lists = []
    for channels in concurrent_commands:
        template = re.sub(r'\b\d+\b', '{}', command, count=1)
        command_lists.append([template.format(chan) for chan in channels])
    
    # Generate the concurrent command list.
    concurrent_command_list = []
    for commands in zip(*command_lists):
        concurrent_command_list.append(" ".join(commands))
        
    return concurrent_command_list


# This function is updated to handle concurrent commands.
def get_offset_triggers(strip):
    # Detect and parse concurrent commands.
    concurrent_commands = parse_concurrent_commands(strip.friend_list)
    # Check if we have concurrent commands.
    if len(concurrent_commands) > 1 or any(isinstance(i, list) for i in concurrent_commands):
        command_list = generate_concurrent_command_strings(strip.osc_trigger, concurrent_commands)
    else:  # Fallback to original behavior for sequential commands.
        channels = parse_channels(strip.friend_list)
        command_list = generate_command_strings(strip.osc_trigger, channels)
    
    return command_list


class SimpleCommandLine(bpy.types.Operator):
    bl_idname = "sequencer.simple_command_line"
    bl_label = "Simple Command Line"

    def modal(self, context, event):
        scene = context.scene

        if event.type == 'RET':
            self.execute_command(context)
            scene.command_line_label = "Cmd Line: "
            context.area.tag_redraw()
            return {'FINISHED'}
        elif event.type == 'ESC':
            scene.command_line_label = "Cmd Line: "
            return {'CANCELLED'}
        elif event.ascii.isdigit():
            scene.command_line_label += event.ascii
            context.area.tag_redraw()
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        context.scene.command_line_label = "Cmd Line: @ Channel "
        context.window_manager.modal_handler_add(self)
        context.area.tag_redraw()
        return {'RUNNING_MODAL'}

    def execute_command(self, context):
        # Process the command without the need for "=".
        command = context.scene.command_line_label.split("@ Channel ")[-1]
        try:
            channel = int(command)
            # Execute the command: in this case, set the channel for selected strips.
            selected_strips = [strip for strip in context.scene.sequence_editor.sequences_all if strip.select]
            for strip in selected_strips:
                strip.channel = channel
        except ValueError:
            self.report({'ERROR'}, "Invalid channel number")

        # Reset the command line label after command execution.
        context.scene.command_line_label = "Cmd Line: "


def draw_cmd_line_func(self, context):
    layout = self.layout
    scene = context.scene
    # Always draw the command line label.
    layout.label(text=scene.command_line_label)


class MySettings(bpy.types.PropertyGroup):
    motif_type_enum:  bpy.props.EnumProperty(
        items=enum_items,
        name="Motif Types",
        description="Choose motif type",
        update=motif_type_enum_updater,
        default=1
    )
    
    
class MyMotifs(bpy.types.PropertyGroup):
    motif_names_enum: bpy.props.EnumProperty(
        name="",
        description="List of unique motif names",
        items=get_motif_name_items,
        update=motif_names_updater
    )
        

def draw_func(self, context):
    pcoll = preview_collections["main"]
    orb = pcoll["orb"]
   
    scene = _context.scene
    layout = self.layout
    row = layout.row()
    row.operator("seq.show_sequencer_settings", text="", icon_value=orb.icon_id, emboss=False)
    row.label(text=scene.livemap_label)
    row = layout.row()
    row.alert = context.scene.is_armed_osc
    row.prop(context.scene, "is_armed_osc", toggle=True) 
    
    
def get_audio_object_items(self, context):

    items = [
        ('option_object', "Strip represents a 3D audio object", "This will produce sound and move throughout the scene", 'MESH_CUBE', 1),
        ('option_speaker', "Strip represents a speaker", "This represents a physical speaker at the the theater", 'SPEAKER', 2),
    ]
    return items


def empty_objects_poll(self, object):
    return object.type == 'EMPTY'


def speaker_objects_poll(self, object):
    return object.type == 'SPEAKER'


class AudioObjectSettings(bpy.types.PropertyGroup):
    audio_type_enum:  bpy.props.EnumProperty(
        items=get_audio_object_items,
        name="Audio Types",
        description="Choose what the strip should do",
        default=1
    )
    
    
def render_volume(speaker, empty, sensitivity, object_size, int_mixer_channel):
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
        ip_address = bpy.context.scene.str_audio_ip_address
        port = bpy.context.scene.int_audio_port
        send_osc_string(address, ip_address, port, argument)
    return volume

@persistent
def render_audio_objects(scene):
    if not hasattr(scene, "sequence_editor") or not scene.sequence_editor:
        return

    audio_objects = {}
    for strip in scene.sequence_editor.sequences_all:
        if strip.type == 'SOUND' and strip.audio_type_enum == "option_object" and strip.audio_object_activated:
            audio_objects[strip.sound.filepath] = (strip.selected_empty, strip.audio_object_size)

    for strip in scene.sequence_editor.sequences_all:
        if strip.type == 'SOUND' and strip.audio_type_enum == "option_speaker":
            if strip.sound.filepath in audio_objects:
                empty, object_size = audio_objects[strip.sound.filepath]
                speaker = strip.selected_speaker
                if speaker and empty:
                    sensitivity = getattr(strip, 'speaker_sensitivity', 1)
                    strip.dummy_volume = render_volume(speaker, empty, sensitivity, object_size, strip.int_mixer_channel)


# Output socket setup and send_osc_string function (For OSC output).
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


def register(): 
    # Custom icon stuff
    pcoll = bpy.utils.previews.new()
    preview_collections["main"] = pcoll
    addon_dir = os.path.dirname(__file__)
    pcoll.load("orb", os.path.join(addon_dir, "alva_orb.png"), 'IMAGE')
    bpy.types.Scene.livemap_label = bpy.props.StringProperty(name="Livemap Label", default="Livemap Cue:")
    
    bpy.utils.register_class(MySettings)
    bpy.utils.register_class(RenderStripsOperator)
    bpy.types.Sequence.my_settings = bpy.props.PointerProperty(type=MySettings)
    
    bpy.utils.register_class(MyMotifs)
    if not hasattr(bpy.types.Scene, "my_tool"):
        bpy.types.Scene.my_tool = bpy.props.PointerProperty(type=MyMotifs)
    
    bpy.types.Scene.animation_enabled = bpy.props.BoolProperty(default=True)
    bpy.types.Scene.triggers_enabled = bpy.props.BoolProperty(default=False)
    bpy.types.ColorSequence.animation_cue_list_number = bpy.props.IntProperty(default=10, min=2, max=99999)
    bpy.types.ColorSequence.animation_event_list_number = bpy.props.IntProperty(default=10, min=2, max=99999)
    
    bpy.types.Scene.i_know_the_shortcuts = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.house_down_on_play = bpy.props.BoolProperty(default=False, description="Automatically dip the house lights during playback")
    bpy.types.Scene.house_prefix = bpy.props.StringProperty(default="/eos/newcmd", description="OSC Address/Prefix for the following 2 arguments")
    bpy.types.Scene.house_down_argument = bpy.props.StringProperty(default="500 at 1 Enter", description="Argument needed to lower house lights on playback")
    bpy.types.Scene.house_up_on_stop = bpy.props.BoolProperty(default=False, description="Automatically raise the house lights for safety when sequencer stops playing")
    bpy.types.Scene.house_up_argument = bpy.props.StringProperty(default="500 at 75 Enter", description="Argument needed to raise house lights on stop")
    bpy.types.Scene.sync_timecode = bpy.props.BoolProperty(default=True, description="Sync console's timecode clock with Sorcerer on play/stop/scrub based on top-most active sound strip's event list number")
    bpy.types.Scene.timecode_expected_lag = bpy.props.IntProperty(default=0, min=0, max=100, description="Expected lag in frames")
    bpy.types.Scene.orb_finish_snapshot = bpy.props.IntProperty(default=1, min=1, max=9999, description="Snapshot that Orb should set when done")

    bpy.types.Scene.color_palette_color = bpy.props.FloatVectorProperty(
    name="Color Palette Color",
    subtype='COLOR',
    default=(1.0, 1.0, 1.0),
    min=0.0,
    max=1.0,
    description="Color for setting all channels to and then recording color palette",
    update=color_palette_color_updater
    )
    
    bpy.types.Scene.preview_color_palette = bpy.props.BoolProperty(default=False, description="Link channels 1-1,000 to this color as you adjust it here")
    bpy.types.Scene.reset_color_palette = bpy.props.BoolProperty(default=False, description="Automatically advance number and clear out name when Orb is done")
    bpy.types.Scene.color_palette_number = bpy.props.IntProperty(name="", min=1, max=9999, default=10, description="This is the number of the color palette to record")
    bpy.types.Scene.color_palette_name = bpy.props.StringProperty(name="", default="Auto Color Palette 1", description="This can name the color palette to record")
    
    bpy.types.SoundSequence.song_timecode_clock_number = bpy.props.IntProperty(name="", min=0, max=99, description="This should be the number of the event list you have created on the console for this song")
    bpy.types.SoundSequence.execute_on_cue_number = bpy.props.IntProperty(name="", min=0, max=10000, update=timecode_clock_update_safety, description="Specifies which cue will start (or enable) the timecode clock. Can't be the same as first cue in Blender sequence or that will create loop")
    bpy.types.SoundSequence.execute_with_macro_number = bpy.props.IntProperty(name="", min=0, max=100000, description="Specifies which macro number to build to use to start the timecode clock on the console")
    bpy.types.SoundSequence.disable_on_cue_number = bpy.props.IntProperty(name="", min=0, max=10000, update=timecode_clock_update_safety, description="Specifies which cue will stop (or disable) the timecode clock")
    bpy.types.SoundSequence.disable_with_macro_number = bpy.props.IntProperty(name="", min=0, max=100000, description="Specifies which macro number to build to use to start the timecode clock on the console")
    bpy.types.ColorSequence.execute_animation_on_cue_number = bpy.props.IntProperty(name="", min=0, max=10000, description="Specifies which cue will start (or enable) the timecode clock")
    bpy.types.ColorSequence.execute_animation_with_macro_number = bpy.props.IntProperty(name="", min=0, max=100000, description="Specifies which macro number to build to use to start the timecode clock on the console")
    bpy.types.ColorSequence.disable_animation_on_cue_number = bpy.props.IntProperty(name="", min=0, max=10000, update=timecode_clock_update_safety, description="Specifies which cue will stop (or disable) the timecode clock")
    bpy.types.ColorSequence.disable_animation_with_macro_number = bpy.props.IntProperty(name="", min=0, max=100000, description="Specifies which macro number to build to use to start the timecode clock on the console")
    
    bpy.types.Scene.addressing_panel_toggle = bpy.props.BoolProperty(
        name="Destination Panel", 
        description="Set the IP address and port for your lighting console here", 
        default = True
    )    
    bpy.types.Scene.examples_panel_toggle = bpy.props.BoolProperty(
        name="Examples", 
        description="See examples of what you can input", 
        default = False
    ) 
    bpy.types.Scene.bake_panel_toggle = bpy.props.BoolProperty(
        name="Oven", 
        description="Use this to store animation data locally on the console", 
        default = False
    ) 
    bpy.types.ColorSequence.paths_panel_toggle = bpy.props.BoolProperty(
        name="Paths", 
        description="Use this to map pan/tilt to paths in 3D View", 
        default = False
    ) 
    bpy.types.ColorSequence.use_paths = bpy.props.BoolProperty(
        name="Use Paths", 
        description="Use this to map pan/tilt to paths in 3D View", 
        default = False
    ) 
    bpy.types.Scene.selected_curve = bpy.props.StringProperty()
    bpy.types.ColorSequence.selected_light = bpy.props.StringProperty()
    bpy.types.Scene.selected_constraint = bpy.props.StringProperty()
    
    bpy.types.ColorSequence.friend_list = bpy.props.StringProperty(default="", description='Use this to create an offset effect timed by strip length. Type something like "1 thru 5" in this box and something like "1 at full enter" as the Strip Start Argument to make the offset friends join in. Beware: this feature is not stable')
    bpy.types.Scene.replacement_value = bpy.props.StringProperty(default="group/1", update=replacement_value_updater)
    bpy.types.Scene.auto_update_replacement = bpy.props.BoolProperty(default=False, description="When user updates this value, automatically update prefixes and strip name as well")
    bpy.types.Scene.offset_value = bpy.props.IntProperty(name="", min=-100000, max=10000)
    bpy.types.SoundSequence.song_bpm_input = bpy.props.IntProperty(name="", min=1, max=250, description='Use this to determine what strips will be generated and where')
    bpy.types.SoundSequence.song_bpm_channel = bpy.props.IntProperty(name="", min=1, max=32, description='Use this to choose which channel to place the new strips on')
    bpy.types.SoundSequence.beats_per_measure = bpy.props.IntProperty(name="", min=1, max=16, description='Use this to determine how many beats are in each measure. In a time signature like 3/4, this would be the top number 3')
    
    bpy.types.ColorSequence.motif_name = bpy.props.StringProperty(default="", description="Use this to link cues together that should act as one. They must have the same name here and have the link button turned on so that it is red for them to automatically update each other. Not everything will necessarily be updated.")
    bpy.types.ColorSequence.strip_length_proxy = bpy.props.IntProperty(name="", min=-9999, max=1000000)
        
    bpy.types.Scene.prefix_panel_toggle = bpy.props.BoolProperty(
        name="Animation Prefixes Panel", 
        description="Set the OSC prefixes for your lighting console here. For example, an ETC Eos family console OSC prefix to set the intensity of Group 1 is: /eos/group/1", 
        default = True
    )   
    
    bpy.types.ColorSequence.intensity_prefix = bpy.props.StringProperty(name="Intensity Prefix:", default="/eos/*", description='Type in the prefix, aka address, needed by your console to control intensity. For ETC Eos, it is "/eos/chan/1" to control intensity on channel 1. The second half of the OSC message is the argument, represented to the right. If your console does not want the value to be in the argument by itself, contact Alva Theaters',)
    bpy.types.ColorSequence.red_prefix = bpy.props.StringProperty(name="Red Prefix:", default="/eos/*/param/red", description='Type in the prefix, aka address, needed by your console to control red value. For ETC Eos, it is "/eos/chan/1/param/red" to control red on channel 1. The second half of the OSC message is the argument, represented to the right. If your console does not want the value to be in the argument by itself, contact Alva Theaters',)
    bpy.types.ColorSequence.green_prefix = bpy.props.StringProperty(name="Green Prefix:", default="/eos/*/param/green", description='Type in the prefix, aka address, needed by your console to control green value. For ETC Eos, it is "/eos/chan/1/param/green" to control green on channel 1. The second half of the OSC message is the argument, represented to the right. If your console does not want the value to be in the argument by itself, contact Alva Theaters',)
    bpy.types.ColorSequence.blue_prefix = bpy.props.StringProperty(name="Blue Prefix:", default="/eos/*/param/blue", description='Type in the prefix, aka address, needed by your console to control blue value. For ETC Eos, it is "/eos/chan/1/param/blue" to control blue on channel 1. The second half of the OSC message is the argument, represented to the right. If your console does not want the value to be in the argument by itself, contact Alva Theaters',)
    bpy.types.ColorSequence.pan_prefix = bpy.props.StringProperty(name="Pan Prefix:", default="/eos/*/param/pan", description='Type in the prefix, aka address, needed by your console to control pan. For ETC Eos, it is "/eos/chan/1/param/pan" to control intensity on channel 1. The second half of the OSC message is the argument, represented to the right. If your console does not want the value to be in the argument by itself, contact Alva Theaters')
    bpy.types.ColorSequence.tilt_prefix = bpy.props.StringProperty(name="Tilt Prefix:", default="/eos/*/param/tilt", description='Type in the prefix, aka address, needed by your console to control tilt. For ETC Eos, it is "/eos/chan/1/param/tilt" to control tilt on channel 1. The second half of the OSC message is the argument, represented to the right. If your console does not want the value to be in the argument by itself, contact Alva Theaters')
    bpy.types.ColorSequence.zoom_prefix = bpy.props.StringProperty(name="Zoom Prefix:", default="/eos/*/param/zoom", description='If using ETC Eos, type in r for "Rotate", z for "Zoom", st for "Shutter Strobe", r2 for "Rotate wheel 2", and many more variations', update=custom_zoom_prefix_updater)
    bpy.types.ColorSequence.iris_prefix = bpy.props.StringProperty(name="Iris Prefix:", default="/eos/*/param/iris", description='If using ETC Eos, type in r for "Rotate", z for "Zoom", st for "Shutter Strobe", r2 for "Rotate wheel 2", and many more variations', update=custom_iris_prefix_updater)
    bpy.types.ColorSequence.flash_input = bpy.props.StringProperty(name="", description="Type in what feels natural as a request for a flash up. It IS the software's job to read your mind", update=flash_input_updater)
    
    bpy.types.ColorSequence.flash_down_input = bpy.props.StringProperty(name="", description="Type in the second half of the flash, which tells Sorcerer what to do to flash back down", update=flash_down_input_updater)
    bpy.types.ColorSequence.flash_input_background = bpy.props.StringProperty(name="",)
    bpy.types.ColorSequence.flash_down_input_background = bpy.props.StringProperty(name="",)
    bpy.types.ColorSequence.start_flash_macro_number = bpy.props.IntProperty(name="", min=0, max=99999, description="This is the macro number on the console that Alva will use to fire the beginning of the flash", update=flash_motif_property_updater)
    bpy.types.ColorSequence.end_flash_macro_number = bpy.props.IntProperty(name="", min=0, max=99999, description="This is the macro number on the console that Alva will use to fire the end of the flash", update=flash_motif_property_updater)
    bpy.types.ColorSequence.frame_middle = bpy.props.IntProperty(name="", min=-100000, max=100000, default=0)
    bpy.types.ColorSequence.flash_bias = bpy.props.IntProperty(name="", min=-49, max=49, default=0, description="This allows you to make the flash start with a rapid fade up and then fade down slowly and vise-versa", update=flash_motif_property_updater)
    bpy.types.ColorSequence.flash_prefix = bpy.props.StringProperty(name="", default="")
    bpy.types.ColorSequence.start_flash = bpy.props.StringProperty(name="", default="")
    bpy.types.ColorSequence.end_flash = bpy.props.StringProperty(name="", default="")
    
    bpy.types.ColorSequence.trigger_prefix = bpy.props.StringProperty(name="", default="/eos/newcmd", description="Prefix, aka address, is the first half of an OSC message. The top three fields here will definitely work on any console brand/type that has an OSC input library", update=trigger_motif_property_updater)
    bpy.types.ColorSequence.osc_trigger = bpy.props.StringProperty(name="", description="This argument will be fired with the above prefix when frame 1 of the strip comes up in the sequencer. The top three fields here will definitely work on any console brand/type that has an OSC input library", update=trigger_motif_property_updater)
    bpy.types.ColorSequence.osc_trigger_end = bpy.props.StringProperty(name="", description="This argument will be fired with the above prefix when the final frame of the strip comes up in the sequencer. The top three fields here will definitely work on any console brand/type that has an OSC input library", update=trigger_motif_property_updater)
    bpy.types.ColorSequence.eos_cue_number = bpy.props.StringProperty(name="", update=cue_motif_property_updater, description="This argument will be fired with the above prefix when frame 1 of the strip comes up in the sequencer. The top three fields here will definitely work on any console brand/type that has an OSC input library")
    
    bpy.types.ColorSequence.osc_auto_cue = bpy.props.StringProperty(get=get_auto_cue_string)
    
    bpy.types.ColorSequence.start_frame_macro = bpy.props.IntProperty(name="", min=0, max=99999, update=macro_motif_property_updater)
    bpy.types.ColorSequence.start_frame_macro_text = bpy.props.StringProperty(name="")
    bpy.types.ColorSequence.start_frame_macro_text_gui = bpy.props.StringProperty(name="", update=start_macro_update)
    bpy.types.ColorSequence.end_frame_macro = bpy.props.IntProperty(name="", min=0, max=99999, update=macro_motif_property_updater)
    bpy.types.ColorSequence.end_frame_macro_text = bpy.props.StringProperty(name="")
    bpy.types.ColorSequence.end_frame_macro_text_gui = bpy.props.StringProperty(name="", update=end_macro_update)
    bpy.types.ColorSequence.start_macro_muted = bpy.props.BoolProperty(name="", description="Toggle mute/unmute for the start macro", default=False)
    bpy.types.ColorSequence.end_macro_muted = bpy.props.BoolProperty(name="", description="Toggle mute/unmute for the end macro", default=False)
    
    bpy.types.ColorSequence.osc_intensity  = bpy.props.FloatProperty(name="Intensity", min=0, max=100, options={'ANIMATABLE'}, update=osc_intensity_update, description="")
    bpy.types.ColorSequence.intensity_checker = bpy.props.FloatProperty(name="", min=-10000, max=10000, default=10000)
    bpy.types.ColorSequence.osc_color = bpy.props.FloatVectorProperty(
    name="Color",
    subtype='COLOR',
    default=(1.0, 1.0, 1.0),
    min=0.0,
    max=1.0,
    options={'ANIMATABLE'},
    update=osc_color_update
)
    bpy.types.ColorSequence.osc_pan  = bpy.props.FloatProperty(name="Pan:", min=-360, max=360, options={'ANIMATABLE'}, update=osc_pan_update)
    bpy.types.ColorSequence.osc_tilt  = bpy.props.FloatProperty(name="Tilt:", min=-360, max=360, options={'ANIMATABLE'}, update=osc_tilt_update)
    bpy.types.ColorSequence.osc_zoom  = bpy.props.FloatProperty(name="Zoom:", min=1, max=max_zoom, options={'ANIMATABLE'}, update=osc_zoom_update, default=10)
    bpy.types.ColorSequence.osc_iris  = bpy.props.FloatProperty(name="Iris:", min=1, max=100, options={'ANIMATABLE'}, update=osc_iris_update, default=100)
 
    bpy.types.Scene.osc_receive_port = bpy.props.IntProperty(min=0, max=65535)
    bpy.types.Scene.channel_selector = bpy.props.IntProperty(min=0, max=32, description="Enter the channel number you wish to select. Or, in the sequencer, just type the number of the channel you want. 0 for 10, and hold down shift to get up to 20. Only works up to channel 20")
    bpy.types.Scene.generate_quantity = bpy.props.IntProperty(min=1, max=10000, default=1, description="Enter in how many strips you want")
    bpy.types.Scene.normal_offset = bpy.props.IntProperty(min=0, max=10000, default=25, description="Enter in the desired offset in frames. A large offset number will result in long strips. Once created, you can do offsets using BPM instead. If you want to generate using BPM, select the sound file and do it there")
    bpy.types.Scene.i_understand_animation = bpy.props.StringProperty(default="")
    bpy.types.Scene.i_understand_triggers = bpy.props.StringProperty(default="") 
 
    bpy.types.Scene.color_is_magnetic = bpy.props.BoolProperty(name="", description="Select Magnetic button will only select other strips if they share Active Strip's color", default=False)
    bpy.types.Scene.strip_name_is_magnetic = bpy.props.BoolProperty(name="", description="Select Magnetic button will only select other strips if they share Active Strip's strip name", default=False)
    bpy.types.Scene.channel_is_magnetic = bpy.props.BoolProperty(name="", description="Select Magnetic button will only select other strips if they share Active Strip's channel", default=False)
    bpy.types.Scene.duration_is_magnetic = bpy.props.BoolProperty(name="", description="Select Magnetic button will only select other strips if they share Active Strip's duration", default=False)
    bpy.types.Scene.start_frame_is_magnetic = bpy.props.BoolProperty(name="", description="Select Magnetic button will only select other strips if they share Active Strip's start frame", default=False)
    bpy.types.Scene.end_frame_is_magnetic = bpy.props.BoolProperty(name="", description="Select Magnetic button will only select other strips if they share Active Strip's end frame", default=False)
    bpy.types.Scene.is_filtering_left = bpy.props.BoolProperty(name="", description="Select Magnetic button will only select other strips if they are an exact match for the magnetic properties. If this is disabled, any strip matching as little as 1 magnetic property will be selected", default=False)
    bpy.types.Scene.is_filtering_right = bpy.props.BoolProperty(name="", description="The quick-select buttons below will deselect strips that don't match the button if this is enabled. If this is disabled, the quick-select button will only add to selections without ever deselecting anything", default=False)

    bpy.types.Scene.is_armed_osc = bpy.props.BoolProperty(
        default=True, name="Arm Strips", description="Arm strips to stream data on playback")
    bpy.types.Scene.is_armed_livemap = bpy.props.BoolProperty(
        default=True, name="Arm Livemap", description="Arm livemap to automatically jump to correct cue on playback from middle")
    bpy.types.Scene.is_armed_release = bpy.props.BoolProperty(
        default=False, name="Arm Add Extra Strip on Release of O", description="Arm this to add a second strip when O as in Oscar key is released. This is to activate kick and snare with a single finger")
    bpy.types.Scene.is_armed_turbo = bpy.props.BoolProperty(
        default=False, name="Orb Skips Shift+Update", description="Arm this to skip the safety step where build buttons save the console file prior to messing with stuff on the console")
    bpy.types.ColorSequence.is_linked = bpy.props.BoolProperty(
        default=False, name="", description="Link this to make it so that this strip will automatically stay in sync with all other strips sharing the same motif name above", update=is_linked_updater)

    # Cue builder stuff
    bpy.types.Scene.key_light_groups = bpy.props.StringProperty(name="Key Light Groups")
    bpy.types.Scene.rim_light_groups = bpy.props.StringProperty(name="Rim Light Groups")
    bpy.types.Scene.fill_light_groups = bpy.props.StringProperty(name="Fill Light Groups")
    bpy.types.Scene.texture_light_groups = bpy.props.StringProperty(name="Texture Light Groups")
    bpy.types.Scene.band_light_groups = bpy.props.StringProperty(name="Band Light Groups")
    bpy.types.Scene.accent_light_groups = bpy.props.StringProperty(name="Accent Light Groups")
    bpy.types.Scene.energy_light_groups = bpy.props.StringProperty(name="Accent Light Groups")
    bpy.types.Scene.cyc_light_groups = bpy.props.StringProperty(name="Background Light 1 Groups")
    bpy.types.Scene.cyc_two_light_groups = bpy.props.StringProperty(name="Background Light 1 Groups")
    bpy.types.Scene.cyc_three_light_groups = bpy.props.StringProperty(name="Background Light 1 Groups")
    bpy.types.Scene.cyc_four_light_groups = bpy.props.StringProperty(name="Background Light 1 Groups")   
    bpy.types.ColorSequence.key_light = bpy.props.IntProperty(name="Key Light", min=0, max=100, update=key_light_updater, description="White, nuetral, primary light for primary performers")
    bpy.types.ColorSequence.rim_light = bpy.props.IntProperty(name="Rim Light", min=0, max=100,  update=rim_light_updater, description="White or warm light coming from upstage to create definition between foreground and background")
    bpy.types.ColorSequence.fill_light = bpy.props.IntProperty(name="Fill Light", min=0, max=100,  update=fill_light_updater, description="White, nuetral light to balance edges between key and rim lights")
    bpy.types.ColorSequence.texture_light = bpy.props.IntProperty(name="Texture Light", min=0, max=100,  update=texture_light_updater, description="Faint light with gobo to create texture on surfaces without interfering with key light")
    bpy.types.ColorSequence.band_light = bpy.props.IntProperty(name="Band Light", min=0, max=100,  update=band_light_updater, description="Strongly saturated light for the band to create mood")
    bpy.types.ColorSequence.accent_light = bpy.props.IntProperty(name="Accent Light", min=0, max=100,  update=accent_light_updater, description="Color scheme typically should have only 1-2 colors, this being one of them")
    bpy.types.ColorSequence.energy_light = bpy.props.IntProperty(name="Energy Light", min=0, max=100,  update=energy_light_updater, description="Intensity of lights on energy effect")
    bpy.types.ColorSequence.energy_speed = bpy.props.IntProperty(name="Energy Speed", min=0, max=500, update=energy_speed_updater, description="Speed of energy effect")
    bpy.types.ColorSequence.energy_scale = bpy.props.IntProperty(name="Energy Scale", min=0, max=500, update=energy_scale_updater, description="Scale of energy effect")
    bpy.types.ColorSequence.background_light_one = bpy.props.IntProperty(name="Background Light 1", min=0, max=100,  update=background_light_updater, description="Background light intensity, typically for cyclorama or uplights. Change the colors on console, not here")
    bpy.types.ColorSequence.background_light_two = bpy.props.IntProperty(name="Background Light 2", min=0, max=100,  update=background_two_light_updater, description="Use these additional slots if you're controlling backdrop color by varying intensity of multiple channels with different color gels")
    bpy.types.ColorSequence.background_light_three = bpy.props.IntProperty(name="Background Light 3", min=0, max=100,  update=background_three_light_updater, description="Use these additional slots if you're controlling backdrop color by varying intensity of multiple channels with different color gels")
    bpy.types.ColorSequence.background_light_four = bpy.props.IntProperty(name="Background Light 4", min=0, max=100,  update=background_four_light_updater, description="Use these additional slots if you're controlling backdrop color by varying intensity of multiple channels with different color gels")
    bpy.types.ColorSequence.band_color = bpy.props.FloatVectorProperty(name="Band Color", subtype='COLOR', size=3, min=0.0, max=1.0, default=(1.0, 1.0, 1.0), description="Dummy, reference color only. Does not control console parameters")
    bpy.types.ColorSequence.accent_color = bpy.props.FloatVectorProperty(name="Accent Color", subtype='COLOR', size=3, min=0.0, max=1.0, default=(1.0, 1.0, 1.0), description="Dummy, reference color only. Does not control console parameters")
    bpy.types.ColorSequence.background_color = bpy.props.FloatVectorProperty(name="Background Color", subtype='COLOR', size=3, min=0.0, max=1.0, default=(1.0, 1.0, 1.0), description="Dummy, reference color only. Does not control console parameters")
    bpy.types.ColorSequence.cue_builder_effect_id = bpy.props.StringProperty(name="")
    bpy.types.Scene.cue_builder_id_offset = bpy.props.IntProperty(name="", description="Set this to 100 (or any integer) to make the cue builder buttons start at Preset 100/Effect 100, or similar")

    bpy.types.ColorSequence.flash_using_nodes = bpy.props.BoolProperty(
        name="Use Nodes", 
        description="Auto-fill Flash Up and Flash Down fields with nodes", 
        default = False
    )
    bpy.types.Scene.cue_builder_toggle = bpy.props.BoolProperty(
        name="Cue Builder Panel", 
        description="Build cues inside Alva so you don't have to constantly switch back and forth between Alva and the console.", 
        default = True
    ) 
    bpy.types.Scene.builder_settings_toggle = bpy.props.BoolProperty(
        name="Builder Settings Panel", 
        description="Select which groups are in key, rim, fill, band, accent, and background light categories.", 
        default = False
    ) 
    bpy.types.ColorSequence.key_is_recording = bpy.props.BoolProperty(
        name="", 
        description="Record presets when pose buttons are red", 
        default = False
    ) 
    bpy.types.ColorSequence.rim_is_recording = bpy.props.BoolProperty(
        name="", 
        description="Record presets when pose buttons are red", 
        default = False
    ) 
    bpy.types.ColorSequence.fill_is_recording = bpy.props.BoolProperty(
        name="", 
        description="Record presets when pose buttons are red", 
        default = False
    ) 
    bpy.types.ColorSequence.texture_is_recording = bpy.props.BoolProperty(
        name="", 
        description="Record presets when pose buttons are red", 
        default = False
    ) 
    bpy.types.ColorSequence.band_is_recording = bpy.props.BoolProperty(
        name="", 
        description="Record presets when pose buttons are red", 
        default = False
    ) 
    bpy.types.ColorSequence.accent_is_recording = bpy.props.BoolProperty(
        name="", 
        description="Record presets when pose buttons are red", 
        default = False
    ) 
    bpy.types.ColorSequence.cyc_is_recording = bpy.props.BoolProperty(
        name="", 
        description="Record presets when pose buttons are red", 
        default = False
    ) 
    bpy.types.Scene.using_gels_for_cyc = bpy.props.BoolProperty(
        name="", 
        description="Mix backdrop color by mixing intensities of 4 channels gelled differently", 
        default = True
    ) 
    bpy.types.Scene.is_updating_strip_color = bpy.props.BoolProperty(
        name="", 
        description="When checked,changing the strip lighting effect type, the color of the strip changes to match the effect type.", 
        default = True
    ) 
    
    # 3D sound stuff.
    bpy.types.SoundSequence.audio_type_enum = bpy.props.EnumProperty(
        items=get_audio_object_items,
        name="Audio Types",
        description="Choose what the strip should do",
        default=1
    )
    bpy.types.SoundSequence.selected_empty = bpy.props.PointerProperty(
        type=bpy.types.Object,
        poll=empty_objects_poll,
        name="Selected Empty",
        description='You are supposed to link this audio object strip to an "empty" object over in 3D view'
    )
    bpy.types.SoundSequence.selected_speaker = bpy.props.PointerProperty(
        type=bpy.types.Object,
        poll=speaker_objects_poll,
        name="Selected Speaker",
        description='You are supposed to link this speaker strip to a "speaker" object over in 3D view'
    )
    bpy.types.SoundSequence.speaker_sensitivity = bpy.props.FloatProperty(name="Sensitivity", description="Sensitivity of speaker", default=.5, min=0, max=1)
    bpy.types.SoundSequence.audio_object_activated = bpy.props.BoolProperty(default=False, name="Activate Audio Object", description="Activate renderer for this audio object. Leaving this on when not needed may introduce lag")
    bpy.types.SoundSequence.dummy_volume = bpy.props.FloatProperty(default=0, name="Dummy Volume", min=0, max=1)
    bpy.types.SoundSequence.audio_object_size = bpy.props.FloatProperty(default=1, name="Dummy Volume", min=0, max=20)
    bpy.types.SoundSequence.int_mixer_channel = bpy.props.IntProperty(default=1, name="Channel/fader number on mixer", min=1, max=9999, description='This is for the OSC real-time monitor below. This is talking about the fader on the audio mixer. It will be replace "#" in the OSC templates below')

    bpy.types.Scene.audio_osc_address = bpy.props.StringProperty(default="", description="Type # for channel/fader/ouput number and $ for value, to be autofilled in background by Sorcerer. Use this for realtime feedback during design, then bake/export to Qlab. Set up the mixer as if these are IEM's")
    bpy.types.Scene.audio_osc_argument = bpy.props.StringProperty(default="", description="Type # for channel/fader/ouput number and $ for value, to be autofilled in background by Sorcerer. Use this for realtime feedback during design, then bake/export to Qlab. Set up the mixer as if these are IEM's")
    bpy.types.Scene.str_audio_ip_address = bpy.props.StringProperty(default="", description="IP address of audio mixer. Leave blank to deactivate background process")
    bpy.types.Scene.int_audio_port = bpy.props.IntProperty(default=10023, description="Port where audio mixer expects to recieve UDP messages")

    bpy.app.handlers.depsgraph_update_pre.append(render_audio_objects)
    bpy.app.handlers.frame_change_pre.append(render_audio_objects)

    #Adds Arm Strips button to header/footer.
    bpy.types.SEQUENCER_HT_header.append(draw_func)

    #Adds Livemap Cue label to header/footer.
    bpy.types.Scene.livemap_label = bpy.props.StringProperty(name="Livemap Label", default="Livemap Cue:")
    
    bpy.app.handlers.frame_change_pre.append(playback_monitor.frame_change_handler)
    bpy.app.handlers.animation_playback_pre.append(playback_monitor.playback_start_handler)
    bpy.app.handlers.animation_playback_post.append(playback_monitor.playback_stop_handler)
    bpy.app.handlers.frame_change_pre.append(frame_change_handler_animation)
    bpy.app.handlers.frame_change_pre.append(frame_change_handler)
    
    #Command line stuff.
    bpy.utils.register_class(SimpleCommandLine)
    bpy.types.SEQUENCER_HT_header.append(draw_cmd_line_func)
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='Sequencer', space_type='SEQUENCE_EDITOR')
    kmi = km.keymap_items.new(SimpleCommandLine.bl_idname, 'C', 'PRESS')
    kmi = km.keymap_items.new(RenderStripsOperator.bl_idname, 'SPACE', 'PRESS', shift=True)
    bpy.types.Scene.command_line_label = bpy.props.StringProperty(default="Cmd Line: ")
    

def unregister():
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps['Sequencer']
    wm.keyconfigs.addon.keymaps.remove(km)
    bpy.utils.unregister_class(SimpleCommandLine)
    bpy.app.handlers.frame_change_pre.remove(frame_change_handler)
    bpy.app.handlers.frame_change_pre.remove(frame_change_handler_animation)
    bpy.app.handlers.animation_playback_post.remove(playback_monitor.playback_stop_handler)
    bpy.app.handlers.animation_playback_pre.remove(playback_monitor.playback_start_handler)
    bpy.app.handlers.frame_change_pre.remove(playback_monitor.frame_change_handler)
    bpy.app.handlers.depsgraph_update_pre.remove(render_audio_objects)
    bpy.app.handlers.frame_change_pre.remove(render_audio_objects)
    bpy.utils.unregister_class(MySettings)
    bpy.utils.unregister_class(RenderStripsOperator)
    bpy.utils.unregister_class(MyMotifs)
    del bpy.types.Scene.cue_builder_id_offset
    del bpy.types.ColorSequence.cue_builder_effect_id
    del bpy.types.ColorSequence.background_color
    del bpy.types.ColorSequence.accent_color
    del bpy.types.ColorSequence.band_color
    del bpy.types.ColorSequence.background_light_four
    del bpy.types.ColorSequence.background_light_three
    del bpy.types.ColorSequence.background_light_two
    del bpy.types.ColorSequence.background_light_one
    del bpy.types.ColorSequence.energy_scale
    del bpy.types.ColorSequence.energy_speed
    del bpy.types.ColorSequence.energy_light
    del bpy.types.ColorSequence.accent_light
    del bpy.types.ColorSequence.band_light
    del bpy.types.ColorSequence.texture_light
    del bpy.types.ColorSequence.fill_light
    del bpy.types.ColorSequence.rim_light
    del bpy.types.ColorSequence.key_light
    del bpy.types.Scene.cyc_four_light_groups
    del bpy.types.Scene.cyc_three_light_groups
    del bpy.types.Scene.cyc_two_light_groups
    del bpy.types.Scene.cyc_light_groups
    del bpy.types.Scene.energy_light_groups
    del bpy.types.Scene.accent_light_groups
    del bpy.types.Scene.band_light_groups
    del bpy.types.Scene.texture_light_groups
    del bpy.types.Scene.fill_light_groups
    del bpy.types.Scene.rim_light_groups
    del bpy.types.Scene.key_light_groups
    del bpy.types.Scene.is_armed_turbo
    del bpy.types.Scene.is_armed_release
    del bpy.types.Scene.is_armed_livemap
    del bpy.types.Scene.is_armed_osc
    del bpy.types.Scene.is_filtering_right
    del bpy.types.Scene.is_filtering_left
    del bpy.types.Scene.end_frame_is_magnetic
    del bpy.types.Scene.start_frame_is_magnetic
    del bpy.types.Scene.duration_is_magnetic
    del bpy.types.Scene.channel_is_magnetic
    del bpy.types.Scene.strip_name_is_magnetic
    del bpy.types.Scene.color_is_magnetic
    del bpy.types.Scene.i_understand_triggers
    del bpy.types.Scene.i_understand_animation
    del bpy.types.Scene.normal_offset
    del bpy.types.Scene.generate_quantity
    del bpy.types.Scene.channel_selector
    del bpy.types.Scene.osc_receive_port
    del bpy.types.ColorSequence.osc_iris
    del bpy.types.ColorSequence.osc_zoom
    del bpy.types.ColorSequence.osc_tilt
    del bpy.types.ColorSequence.osc_pan
    del bpy.types.ColorSequence.osc_color
    del bpy.types.ColorSequence.intensity_checker
    del bpy.types.ColorSequence.osc_intensity
    del bpy.types.ColorSequence.end_macro_muted
    del bpy.types.ColorSequence.start_macro_muted
    del bpy.types.ColorSequence.end_frame_macro_text_gui
    del bpy.types.ColorSequence.end_frame_macro_text
    del bpy.types.ColorSequence.end_frame_macro
    del bpy.types.ColorSequence.start_frame_macro_text_gui
    del bpy.types.ColorSequence.start_frame_macro_text
    del bpy.types.ColorSequence.start_frame_macro
    del bpy.types.ColorSequence.osc_auto_cue
    del bpy.types.ColorSequence.eos_cue_number
    del bpy.types.ColorSequence.osc_trigger_end
    del bpy.types.ColorSequence.osc_trigger
    del bpy.types.ColorSequence.trigger_prefix
    del bpy.types.ColorSequence.end_flash
    del bpy.types.ColorSequence.start_flash
    del bpy.types.ColorSequence.flash_prefix
    del bpy.types.ColorSequence.flash_bias
    del bpy.types.ColorSequence.frame_middle
    del bpy.types.ColorSequence.end_flash_macro_number
    del bpy.types.ColorSequence.start_flash_macro_number
    del bpy.types.ColorSequence.frame_middle
    del bpy.types.ColorSequence.end_flash_macro_number
    del bpy.types.ColorSequence.start_flash_macro_number
    del bpy.types.ColorSequence.flash_down_input_background
    del bpy.types.ColorSequence.flash_input_background
    del bpy.types.ColorSequence.flash_down_input
    del bpy.types.ColorSequence.flash_input_background
    del bpy.types.ColorSequence.flash_input
    del bpy.types.ColorSequence.iris_prefix
    del bpy.types.ColorSequence.zoom_prefix
    del bpy.types.ColorSequence.tilt_prefix
    del bpy.types.ColorSequence.pan_prefix
    del bpy.types.ColorSequence.blue_prefix
    del bpy.types.ColorSequence.green_prefix
    del bpy.types.ColorSequence.red_prefix
    del bpy.types.ColorSequence.intensity_prefix
    del bpy.types.Scene.prefix_panel_toggle
    del bpy.types.ColorSequence.strip_length_proxy
    del bpy.types.ColorSequence.motif_name
    del bpy.types.SoundSequence.beats_per_measure
    del bpy.types.SoundSequence.song_bpm_channel
    del bpy.types.SoundSequence.song_bpm_input
    del bpy.types.Scene.offset_value
    del bpy.types.Scene.auto_update_replacement
    del bpy.types.Scene.replacement_value
    del bpy.types.ColorSequence.friend_list
    del bpy.types.Scene.selected_constraint
    del bpy.types.ColorSequence.selected_light
    del bpy.types.Scene.selected_curve
    del bpy.types.ColorSequence.use_paths
    del bpy.types.ColorSequence.paths_panel_toggle
    del bpy.types.Scene.bake_panel_toggle
    del bpy.types.Scene.examples_panel_toggle
    del bpy.types.Scene.addressing_panel_toggle
    del bpy.types.ColorSequence.disable_animation_with_macro_number
    del bpy.types.ColorSequence.disable_animation_on_cue_number
    del bpy.types.ColorSequence.execute_animation_with_macro_number
    del bpy.types.ColorSequence.execute_animation_on_cue_number
    del bpy.types.SoundSequence.disable_with_macro_number
    del bpy.types.SoundSequence.disable_on_cue_number
    del bpy.types.SoundSequence.execute_with_macro_number
    del bpy.types.SoundSequence.execute_on_cue_number
    del bpy.types.SoundSequence.song_timecode_clock_number
    del bpy.types.Scene.color_palette_name
    del bpy.types.Scene.color_palette_number
    del bpy.types.Scene.reset_color_palette
    del bpy.types.Scene.preview_color_palette
    del bpy.types.Scene.color_palette_color
    del bpy.types.Scene.orb_finish_snapshot
    del bpy.types.Scene.timecode_expected_lag
    del bpy.types.Scene.sync_timecode
    del bpy.types.Scene.house_up_argument
    del bpy.types.Scene.house_up_on_stop
    del bpy.types.Scene.house_down_argument
    del bpy.types.Scene.house_prefix
    del bpy.types.Scene.house_down_on_play
    del bpy.types.Scene.i_know_the_shortcuts
    del bpy.types.ColorSequence.animation_event_list_number
    del bpy.types.ColorSequence.animation_cue_list_number
    del bpy.types.Scene.triggers_enabled
    del bpy.types.Scene.animation_enabled
    del bpy.types.Scene.my_tool
    bpy.utils.unregister_class(MyMotifs)
    del bpy.types.Sequence.my_settings
    bpy.utils.unregister_class(RenderStripsOperator)
    del bpy.types.Scene.livemap_label
    bpy.utils.previews.remove(preview_collections["main"])


# For development purposes only.
if __name__ == "__main__":
    register()
