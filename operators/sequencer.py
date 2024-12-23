# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Operator
from bpy.props import IntProperty, StringProperty
import time
import os

from ..as_ui.blender_spaces.space_sequencer import draw_strip_media
from ..as_ui.strip_formatter import (
    draw_strip_formatter_color, 
    draw_strip_formatter_sound, 
    draw_strip_formatter_video_audio, 
    draw_strip_formatter_generator
)
from ..as_ui.utils import determine_sequencer_context
from ..utils.event_utils import EventUtils
from ..utils.sequencer_utils import find_available_channel, add_color_strip, analyze_song
from ..utils.osc import OSC
from ..utils.audio_utils import render_volume
from ..maintenance.logging import alva_log

# pyright: reportInvalidTypeForm=false

SCALE_STRIPS_FACTOR = 0.001

'''
DIRECTORY: (exact line numbers will change)
    104. Hotkeys and popup ops
    1224. Macro ops
    1341. Misc. ops
    1893. Orb ops
    2453. Add strip ops
    3310. 3D audio ops
'''

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


# Hotkeys and Popups
class SEQUENCER_OT_alva_scale_strips(Operator):  # TODO Scale type not the most helpful.
    """Scale the length of a single strip or the offsets between multiple selected strips in the VSE"""
    bl_idname = "alva_seq.scale_strips"
    bl_label = "Scale VSE Strips"
    bl_options = {'UNDO'}

    initial_mouse_x = None
    initial_strip_length = None
    initial_offsets = None
    strips_to_scale = None

    def invoke(self, context, event):
        self.initial_mouse_x = event.mouse_x
        # Retrieve and sort the strips by their starting frame.
        self.strips_to_scale = sorted(
            [s for s in context.scene.sequence_editor.sequences if s.select],
            key=lambda s: s.frame_start
        )

        # Check the number of selected strips to set up initial conditions.
        if len(self.strips_to_scale) == 1:
            self.initial_strip_length = self.strips_to_scale[0].frame_final_end - self.strips_to_scale[0].frame_start
        else:
            self.initial_offsets = [self.strips_to_scale[i].frame_start - self.strips_to_scale[i - 1].frame_final_end
                                    for i in range(1, len(self.strips_to_scale))]

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':
            current_mouse_x = event.mouse_x
            delta_x = current_mouse_x - self.initial_mouse_x
            scale_factor = 1 + delta_x * SCALE_STRIPS_FACTOR  # scale factor should start from 1, not 0.

            if len(self.strips_to_scale) == 1:
                new_length = max(1, self.initial_strip_length * scale_factor)
                new_frame_final_end = round(self.strips_to_scale[0].frame_start + new_length)
                self.strips_to_scale[0].frame_final_end = new_frame_final_end

            # Multiple strips selected, adjust offsets.
            elif len(self.strips_to_scale) > 1:
                first_strip_end = round(self.strips_to_scale[0].frame_final_end)

                for i, strip in enumerate(self.strips_to_scale[1:], start=1):
                    original_offset = self.initial_offsets[i - 1]
                    new_offset = self.initial_offsets[i - 1] * scale_factor  # Scale the offset.

                    # Add a gap if the original offset was 0.
                    if original_offset == 0:
                        new_offset = max(new_offset, 1)  # Ensure at least a gap of 1 frame.

                    # Round the resulting frame numbers to the nearest integer.
                    new_frame_start = round(first_strip_end + new_offset)
                    strip.frame_start = new_frame_start
                    first_strip_end = round(strip.frame_final_end)

            return {'RUNNING_MODAL'}

        elif event.type in {'LEFTMOUSE', 'RET'}:
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            # Reset to initial conditions if cancelled.
            if len(self.strips_to_scale) == 1:
                new_frame_final_end = round(self.strips_to_scale[0].frame_start + self.initial_strip_length)
                self.strips_to_scale[0].frame_final_end = new_frame_final_end
            elif len(self.strips_to_scale) > 1:
                first_strip_end = round(self.strips_to_scale[0].frame_final_end)

                for i, strip in enumerate(self.strips_to_scale[1:], start=1):
                    new_frame_start = round(first_strip_end + self.initial_offsets[i - 1])
                    strip.frame_start = new_frame_start
                    first_strip_end = round(strip.frame_final_end)

            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    
class SEQUENCER_OT_alva_extrude_strips(Operator):  # TODO New strips must inherit properties.
    '''Extrude patterns of strips like meshes.'''
    bl_idname = "alva_seq.extrude_strips"
    bl_label = "Extrude VSE Strips"
    bl_options = {'UNDO'}
    
    first_mouse_x = None
    pattern_length = None
    pattern_details = None
    
    active_strip_name = ""
    active_strip_color = (1, 1, 1)
    sensitivity_factor = 2  # Adjust this to scale mouse sensitivity

    @classmethod
    def poll(cls, context):
        return len(context.selected_sequences) > 1

    def invoke(self, context, event):
        # Ensure exactly two color strips are selected.
        selected_color_strips = [s for s in context.selected_sequences if s.type == 'COLOR']

        if len(selected_color_strips) != 2:
            self.report({'ERROR'}, "Exactly two color strips must be selected.")
            return {'CANCELLED'}

        strip1, strip2 = selected_color_strips
        if strip1.color != strip2.color or strip1.frame_final_duration != strip2.frame_final_duration:
            self.report({'ERROR'}, "The selected color strips must have matching color and length.")
            return {'CANCELLED'}

        if context.scene.sequence_editor.active_strip not in selected_color_strips:
            self.report({'ERROR'}, "One of the selected color strips must be active.")
            return {'CANCELLED'}

        active_strip = context.scene.sequence_editor.active_strip
        self.active_strip_name = active_strip.name
        self.active_strip_color = active_strip.color
        self.active_strip_start_frame_macro = active_strip.int_start_macro
        self.active_strip_end_frame_macro = active_strip.int_end_macro
        self.active_strip_trigger_prefix = active_strip.trigger_prefix
        self.active_strip_osc_trigger = active_strip.osc_trigger
        self.active_strip_osc_trigger_end = active_strip.osc_trigger_end
        self.active_strip_friend_list = active_strip.friend_list

        # Sort the pattern details by the start frame of each strip.
        self.pattern_details = sorted([(s.frame_final_start, s.frame_final_end) for s in selected_color_strips], key=lambda x: x[0])

        # Calculate pattern_length as the distance from the end of the first strip to the start of the second strip.
        self.pattern_length = self.pattern_details[1][0] - self.pattern_details[0][1]

        # Store the initial mouse position.
        self.first_mouse_x = event.mouse_x
        self.last_extruded_frame_end = None

        # Add the modal handler and start the modal operation.
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    last_extruded_frame_end = None

    def modal(self, context, event):
        # If there's an active strip, we get its channel for reference.
        if context.scene.sequence_editor.active_strip:
            active_channel = context.scene.sequence_editor.active_strip.channel
        else:
            # If there's no active strip, we report an error and cancel the operation.
            self.report({'ERROR'}, "No active strip")
            return {'CANCELLED'}

        if event.type == 'MOUSEMOVE':
            
            # Calculate the number of pattern duplicates based on the mouse's x position.
            delta = (event.mouse_x - self.first_mouse_x) * self.sensitivity_factor
            num_duplicates = int(delta / self.pattern_length)
            
            alva_log("sequencer_operators", f"num_duplicates: {num_duplicates}")
            alva_log("sequencer_operators", f"last_extruded_frame_end: {self.last_extruded_frame_end}")
            alva_log("sequencer_operators", f"pattern end: {self.pattern_details[-1][1]}")
            alva_log("sequencer_operators", f"pattern length: {self.pattern_length}")

            # Check if we need to create a new strip based on the mouse movement.
            if num_duplicates > 0 and (self.last_extruded_frame_end is None or 
               num_duplicates > (self.last_extruded_frame_end - self.pattern_details[-1][1]) // self.pattern_length):
                
                # Get the end frame of the last strip in the pattern.
                last_frame_end = self.last_extruded_frame_end or self.pattern_details[-1][1]
                # Sort the pattern details by the start frame of each strip.
                self.pattern_details.sort(key=lambda x: x[0])

                # Now calculate space_between using the sorted details.
                space_between = self.pattern_details[1][0] - self.pattern_details[0][1]

                # Calculate new start and end frames for the next strip.
                new_start = last_frame_end + space_between
                new_end = new_start + (self.pattern_details[0][1] - self.pattern_details[0][0])
                
                # Create the next strip and update the last extruded end frame.
                self.create_strip(context, new_start, new_end, active_channel)
                self.last_extruded_frame_end = new_end

        elif event.type in {'LEFTMOUSE', 'RET', 'NUMPAD_ENTER'}:  # Confirm
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:  # Cancel
            # If cancelled, reset the last extruded end frame.
            self.last_extruded_frame_end = None
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}


    def create_strip(self, context, start_frame, end_frame, channel):
        motif_type = bpy.context.scene.sequence_editor.active_strip.my_settings.motif_type_enum
        
        for s in context.scene.sequence_editor.sequences_all:
            if s.channel == channel and (s.frame_final_start <= start_frame < s.frame_final_end or s.frame_final_start < end_frame <= s.frame_final_end):
                return
        
        bpy.ops.sequencer.effect_strip_add(
            frame_start=start_frame,
            frame_end=end_frame,
            channel=channel,
            type='COLOR'
        )
        
        new_strip = context.scene.sequence_editor.active_strip
        
        if new_strip:
            new_strip.name = self.active_strip_name
            new_strip.color = self.active_strip_color
            new_strip.int_start_macro = self.active_strip_start_frame_macro
            new_strip.int_end_macro = self.active_strip_end_frame_macro
            new_strip.trigger_prefix = self.active_strip_trigger_prefix
            new_strip.osc_trigger = self.active_strip_osc_trigger
            new_strip.osc_trigger_end = self.active_strip_osc_trigger_end
            new_strip.friend_list = self.active_strip_friend_list
            
            new_strip.my_settings.motif_type_enum = motif_type
            
            
class SEQUENCER_OT_alva_duplicate_pattern(Operator):
    """Duplicate Selected Pattern"""
    bl_idname = "alva_seq.duplicate_pattern"
    bl_label = "Duplicate Pattern"
    bl_options = {'UNDO'}

    def execute(self, context):
        scene = context.scene
        sequence_editor = scene.sequence_editor
        selected_strips = [strip for strip in sequence_editor.sequences if strip.select]
        
        if len(selected_strips) < 1:
            self.report({'WARNING'}, "No strips selected.")
            return {'CANCELLED'}
        
        # Calculate the length of the selected pattern in frames
        pattern_start_frame = min(strip.frame_start for strip in selected_strips)
        pattern_length = max(strip.frame_final_end for strip in selected_strips) - pattern_start_frame
        
        # Deselect all strips
        for strip in sequence_editor.sequences:
            strip.select = False
        
        # Select the original strips again for duplication
        for strip in selected_strips:
            strip.select = True
        
        # Duplicate the selected strips
        bpy.ops.sequencer.duplicate()
        
        # Identify the new duplicated strips and adjust their positions
        new_strips = []
        for strip in sequence_editor.sequences:
            if strip.select and strip not in selected_strips:
                strip.frame_start += pattern_length
                new_strips.append(strip)
        
        # Ensure only the new duplicated strips remain selected
        for strip in sequence_editor.sequences:
            strip.select = strip in new_strips
        
        self.report({'INFO'}, "Pattern duplicated without overlap.")
        return {'FINISHED'}


class SEQUENCER_OT_alva_deselect(Operator):  # TODO Make this compatible with 3D view too.
    '''The basic, standard Deselect All button Blender refuses to provide.'''
    bl_idname = "alva_common.deselect_all"
    bl_label = "Deselect All"
    bl_options = {'UNDO'}

    def execute(self, context):
        for strip in context.selected_sequences:
            strip.select = False
        return {'FINISHED'}
 
    
snare_state = "snare_complete"
    
class SEQUENCER_OT_alva_new_strip(Operator):
    '''Add color strip on release of Z, when Release is enabled.'''
    bl_idname = 'alva_seq.add_color'
    bl_label = "New Color Strip"
    bl_options = {'UNDO'}

    def execute(self, context):
        global snare_state
        
        current_frame = context.scene.frame_current
        sequence_editor = context.scene.sequence_editor
        
        # Start by trying to place the strip on the same channel as the active strip, or default to 1.
        channel = sequence_editor.active_strip.channel if sequence_editor.active_strip else 1
        frame_end = current_frame + 25
        
        # Find an available channel where the new strip will not overlap.
        channel = find_available_channel(sequence_editor, current_frame, frame_end, channel)
        
        # Now create the strip on the available channel.
        if bpy.context.scene.is_armed_release:
            color_strip = sequence_editor.sequences.new_effect(
                    name="New Strip",
                    type='COLOR',
                    channel=channel,
                    frame_start=current_frame,
                    frame_end=frame_end)
            
            color_strip.color = (0, 0, 0)
            color_strip.my_settings.motif_type_enum = context.scene.add_strip_type_default

            # Deselect all other strips and set the new strip as the active one.
            for strip in sequence_editor.sequences_all:
                strip.select = False
            
            color_strip.select = True 
            context.scene.sequence_editor.active_strip = color_strip
            
        snare_state = "snare_complete"
        
        return {'FINISHED'}
    
 
class SEQUENCER_OT_alva_new_kick(Operator):
    '''Add color strip on down press of Z key.'''
    bl_idname = 'alva_seq.add_color_kick'
    bl_label = "New Color Strip"
    bl_options = {'UNDO'}

    def execute(self, context):
        global snare_state
        
        if snare_state == "snare_complete":
            
            current_frame = context.scene.frame_current
            sequence_editor = context.scene.sequence_editor
            
            channel = sequence_editor.active_strip.channel if sequence_editor.active_strip else 1
            frame_end = current_frame + 25
            
            channel = (sequence_editor, current_frame, frame_end, channel)
            
            color_strip = sequence_editor.sequences.new_effect(
                    name="New Strip",
                    type='COLOR',
                    channel=channel,
                    frame_start=current_frame,
                    frame_end=frame_end)
            
            color_strip.color = (1, 1, 0)
            color_strip.my_settings.motif_type_enum = context.scene.add_strip_type_default

            for strip in sequence_editor.sequences_all:
                strip.select = False
            
            color_strip.select = True 
            context.scene.sequence_editor.active_strip = color_strip  # Set active strip
            
            snare_state = "waiting_on_snare"
        return {'FINISHED'}
    
    
class SEQUENCER_OT_alva_new_pointer(Operator):
    '''Add color strip on down press of Z key.'''
    bl_idname = 'alva_seq.add_color_pointer'
    bl_label = "New Color Strip"
    bl_options = {'UNDO'}

    def invoke(self, context, event):
        sequence_editor = context.scene.sequence_editor

        mouse_x, mouse_y = event.mouse_region_x, event.mouse_region_y
        
        region = context.region
        frame_start, channel = region.view2d.region_to_view(mouse_x, mouse_y)
        
        frame_start = int(frame_start)
        channel = int(channel)
        frame_end = frame_start + 25

        color_strip = sequence_editor.sequences.new_effect(
                name="New Strip",
                type='COLOR',
                channel=channel,
                frame_start=frame_start,
                frame_end=frame_end)
        
        color_strip.color = (1, 1, 0)
        color_strip.my_settings.motif_type_enum = context.scene.add_strip_type_default

        for strip in sequence_editor.sequences_all:
            strip.select = False
        
        color_strip.select = True 
        context.scene.sequence_editor.active_strip = color_strip

        return {'FINISHED'}

    
class SEQUENCER_OT_alva_bump_horizontal(Operator):
    bl_idname = "alva_seq.bump_horizontal"
    bl_label = ""
    bl_description = "Bump Horizontally"
    bl_options = {'UNDO'}

    direction: IntProperty() 

    def execute(self, context):
        alva_log("sequencer_operators", f"Running horizontal bump operator.")
        for strip in context.selected_sequences:
            strip.frame_start += self.direction
        return {'FINISHED'}
    

class SEQUENCER_OT_alva_bump_vertical(Operator):
    bl_idname = "alva_seq.bump_vertical"
    bl_label = ""
    bl_description = "Bump Vertically"
    bl_options = {'UNDO'}

    direction: IntProperty()
    
    def execute(self, context):
        alva_log("sequencer_operators", f"Running vertical bump operator.")
        for strip in context.selected_sequences:
            strip.channel += self.direction
        return {'FINISHED'}


class SEQUENCER_OT_alva_format_strip(Operator):
    '''Pop-up menu for strip formatter, mostly for managing many strips at once'''
    bl_idname = "alva_seq.formatter"
    bl_label = "Strip Formatter"
    
    @classmethod
    def poll(cls, context):
        return (context.scene is not None) and (context.scene.sequence_editor is not None) and (context.scene.sequence_editor.active_strip is not None)

    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=200)
        
    def draw(self, context):
        layout = self.layout
        scene = context.scene

        if hasattr(scene, "sequence_editor") and scene.sequence_editor:
            sequence_editor = scene.sequence_editor
            if hasattr(sequence_editor, "active_strip") and sequence_editor.active_strip:
                active_strip = sequence_editor.active_strip
                alva_context = determine_sequencer_context(sequence_editor, active_strip)
            else:
                alva_context = "none_relevant"
                
            column = layout.column(align=True)
            if alva_context == "only_color":
                draw_strip_formatter_color(context, column, scene, active_strip)

            elif alva_context == "only_sound":
                draw_strip_formatter_sound(column, active_strip)
                
            elif alva_context == "one_video_one_audio":
                draw_strip_formatter_video_audio(column, active_strip, sequence_editor)
                
            else:
                draw_strip_formatter_generator(column, scene)
               
               
class SEQUENCER_OT_alva_strip_media(Operator):
    '''Popup that shows the Lighting panel GUI'''
    bl_idname = "alva_seq.properties"
    bl_label = "Strip Media"
    
    @classmethod
    def poll(cls, context):
        return (context.scene is not None) and (context.scene.sequence_editor is not None) and (context.scene.sequence_editor.active_strip is not None)

    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=320)
    
    def draw(self, context):
        scene = context.scene
        draw_strip_media(self, context, scene)
    

class SEQUENCER_OT_alva_mute(Operator):
    bl_idname = "alva_seq.mute"
    bl_label = ""   
    bl_description = "This mutes the selected strip(s). Muted strips will not contribute to OSC messaging to the console. You can also do this with H to mute and Alt-H to unmute, or command + H to unmute on Mac"
    bl_options = {'UNDO'}

    def execute(self, context):
        selected_strips = [strip for strip in context.scene.sequence_editor.sequences if strip.select]
        for strip in selected_strips:
            if strip.mute:
                strip.mute = False 
            else:
                strip.mute = True
        return {'FINISHED'}
    
    
def bump_timecode(context, time):
    active_strip = context.scene.sequence_editor.active_strip
    event_list = active_strip.int_event_list
    OSC.send_osc_lighting("/eos/newcmd", f"Event {str(event_list)} / 1 Thru 1000000 Time + {str(time)} Enter")

class SEQUENCER_OT_alva_tc_left_five(Operator):
    bl_idname = "alva_seq.tc_left_five"
    bl_label = "5"
    bl_description = "They're too late. Bump console's event list events back 5 frames. The event list this is applied to is determined by the Event List field above. This only works for ETC Eos"

    def execute(self, context):
        bump_timecode(context, -5)
        return {'FINISHED'}    
    
class SEQUENCER_OT_alva_tc_left_one(Operator):
    bl_idname = "alva_seq.tc_left_one"
    bl_label = "1"
    bl_description = "They're a smidge late. Bump console's event list events back 1 frame. The event list this is applied to is determined by the Event List field above. This only works for ETC Eos"
    
    def execute(self, context):
        bump_timecode(context, -1)
        return {'FINISHED'}

class SEQUENCER_OT_alva_tc_right_one(Operator):
    bl_idname = "alva_seq.tc_right_one"
    bl_label = "1"
    bl_description = "They're a smidge early. Bump console's event list events forward 1 frame. The event list this is applied to is determined by the Event List field above. This only works for ETC Eos"
    
    def execute(self, context):
        bump_timecode(context, 1)
        return {'FINISHED'}

class SEQUENCER_OT_alva_tc_right_five(Operator):
    bl_idname = "alva_seq.tc_right_five"
    bl_label = "5"
    bl_description = "They're too early. Bump console's event list events forward 5 frames. The event list this is applied to is determined by the Event List field above. This only works for ETC Eos"
    
    def execute(self, context):
        bump_timecode(context, 5)
        return {'FINISHED'}
    
    
class SEQUENCER_OT_alva_select_channel(Operator):
    bl_idname = "alva_seq.select_channel"
    bl_label = "Select Channel"
    bl_description = "Select all strips on channel above. Pressing 1-9 selects channels 1-9, pressing 0 selects channel 10, and holding shift gets you to channel 20. Press D to deselect all and A to toggle selection of all. B for box select"
    bl_options = {'UNDO'}

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


hotkeys_popups = [
    SEQUENCER_OT_alva_scale_strips,
    SEQUENCER_OT_alva_extrude_strips,
    SEQUENCER_OT_alva_duplicate_pattern,
    SEQUENCER_OT_alva_deselect,
    SEQUENCER_OT_alva_new_strip,
    SEQUENCER_OT_alva_new_kick,
    SEQUENCER_OT_alva_new_pointer,
    SEQUENCER_OT_alva_bump_horizontal,
    SEQUENCER_OT_alva_bump_vertical,
    SEQUENCER_OT_alva_format_strip,
    SEQUENCER_OT_alva_strip_media,
    SEQUENCER_OT_alva_mute,
    SEQUENCER_OT_alva_tc_left_five,
    SEQUENCER_OT_alva_tc_left_one,
    SEQUENCER_OT_alva_tc_right_one,
    SEQUENCER_OT_alva_tc_right_five,
    SEQUENCER_OT_alva_select_channel
]
    

class SEQUENCER_OT_alva_fire_start_macro(Operator):
    bl_idname = "alva_seq.start_macro_fire"
    bl_label = ""
    bl_description = "Send a test command"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        OSC.send_osc_lighting("/eos/macro/fire", str(active_strip.start_frame_macro))
        return {'FINISHED'} 
    
    
class SEQUENCER_OT_alva_fire_end_macro(Operator):
    bl_idname = "alva_seq.end_macro_fire"
    bl_label = ""
    bl_description = "Send a test command"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        OSC.send_osc_lighting("/eos/macro/fire", str(active_strip.end_frame_macro))
        return {'FINISHED'}
    

class SEQUENCER_OT_alva_flash_copy_down(Operator):
    bl_idname = "alva_seq.flash_copy_down"
    bl_label = ""
    bl_description = "Paste this text down below"
    bl_options = {'UNDO'}

    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = sequence_editor.active_strip
        
        active_strip.flash_down_input = active_strip.flash_input
        return {'FINISHED'}
    
    
macro_operators = [
    SEQUENCER_OT_alva_fire_start_macro,
    SEQUENCER_OT_alva_fire_end_macro,
    SEQUENCER_OT_alva_flash_copy_down
]


class SEQUENCER_OT_alva_analyze_song(Operator):
    bl_idname = "alva_seq.analyze_song"
    bl_label = "Analyze Song (AI)"
    bl_description = "Use AI to automatically generate strips"
    bl_options = {'UNDO'}
        
    def execute(self, context):
        def remove_overlapping_cues(cues, min_distance=64):
            """Remove cues that are too close to each other to prevent overlap."""
            corrected_cues = []
            last_cue = None
            for cue in sorted(cues):
                if last_cue is None or (cue - last_cue) >= min_distance:
                    corrected_cues.append(cue)
                    last_cue = cue
            return corrected_cues
        
        active_sequence = context.scene.sequence_editor.active_strip
        if active_sequence and active_sequence.type == 'SOUND':
            active_strip = context.scene.sequence_editor.active_strip
            filepath = bpy.path.abspath(active_sequence.sound.filepath)
            result = analyze_song(self, filepath)
            
            scene = context.scene
            frame_rate = EventUtils.get_frame_rate(scene)
            start_frame = active_sequence.frame_start
            
            beats = [EventUtils.time_to_frame(beat, frame_rate, start_frame) for beat in result.beats]
            downbeats = [EventUtils.time_to_frame(downbeat, frame_rate, start_frame) for downbeat in result.downbeats]
            cues = [EventUtils.time_to_frame(segment.start, frame_rate, start_frame) for segment in result.segments]
            beat_positions = result.beat_positions  # Extract beat positions

            corrected_cues = remove_overlapping_cues(cues)

            for i, beat in enumerate(beats):
                color = color_codes[(beat_positions[i] % len(color_codes))-1]
                add_color_strip(name="Beat", length=4, channel=(active_strip.channel + 3), color=color, strip_type='option_flash', frame=beat-2)
            for downbeat in downbeats:
                add_color_strip(name="Down Beat", length=12, channel=(active_strip.channel + 2), color=(1, 1, 0), strip_type='option_flash', frame=downbeat-6)
            for cue in corrected_cues:
                add_color_strip(name="Cue", length=64, channel=(active_strip.channel + 1), color=(0, 0, 1), strip_type='option_cue', frame=cue-32)
            
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "No active sound strip found")
            return {'CANCELLED'}
        
        
class SEQUENCER_OT_alva_add_offset(Operator):
    bl_idname = "alva_seq.offset"
    bl_label = "Offset"
    bl_description = "Offset selected strips by the BPM to the left"
    bl_options = {'UNDO'}
        
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


class SEQUENCER_OT_alva_generate_strips(Operator):
    bl_idname = "alva_seq.generate_on_song"
    bl_label = "Generate Strips On-Beat"
    bl_description = "Generate color-coded strips on each beat as specified above"
    bl_options = {'UNDO'}
    
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


class SEQUENCER_OT_alva_add_color_strip(Operator):
    bl_idname = "alva_seq.generate"
    bl_label = "Add Strip(s)"
    bl_description = "Generate 1 or more color strips. If multiple, offset them by frames with the Offset by field. Also, press O as in Oscar to add strips even during playback. Go to Settings to enable adding a second strip upon release for kick/snare"
    bl_options = {'UNDO'}

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
    
    
class SEQUENCER_OT_alva_delete_events(Operator):
    bl_idname = "alva_seq.clear_tc_clock"
    bl_label = ""
    bl_description = "Deletes all timecode events in the event list associated with the timecode clock. Command must be manually confirmed on the console"

    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip

        if active_strip and active_strip.type == 'SOUND':
            event_list_number = active_strip.int_event_list
            OSC.send_osc_lighting("/eos/key/tab", "11 Enter")
            OSC.send_osc_lighting("/eos/key/1", "Enter")
            OSC.send_osc_lighting("/eos/key/1", "Enter")
            OSC.send_osc_lighting("/eos/key/tab", "Enter")
            time.sleep(.1)
            OSC.send_osc_lighting("/eos/newcmd", f"Delete Event {str(event_list_number)} / 1 thru 9999 Enter")

        return {'FINISHED'}
    

class SEQUENCER_OT_alva_command_line(Operator):
    bl_idname = "alva_seq.command_line"
    bl_label = "Simple Command Line"
    bl_options = {'UNDO'}

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
        
        
class TOOL_OT_alva_duplicate_strip_to_above(Operator):
    bl_idname = "alva_seq.duplicate"
    bl_label = "Add Strip"
    bl_description = "Adds a duplicate strip above current strip"
    bl_options = {'UNDO'}
    
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

                if active_strip.my_settings.motif_type_enum == 'option_animation' and len(active_strip.list_group_channels) == 1:
                    new_strip.str_manual_fixture_selection = str(active_strip.list_group_channels[0].chan + 1)

            else:
                self.report({'WARNING'}, "Please select exactly one strip.")
                return {'CANCELLED'}
        else:
            self.report({'WARNING'}, "Sequence editor is not active or available.")
            return {'CANCELLED'}

        return {'FINISHED'}
    

class SEQUENCER_OT_alva_add(Operator):
    bl_idname = 'alva_seq.add'
    bl_label = "Add"
    bl_description = "Add color strip"
    bl_options = {'UNDO'}
    
    Option: StringProperty()
    
    def execute(self, context):
        motif_type_enum = self.Option
        current_frame = context.scene.frame_current
        sequence_editor = context.scene.sequence_editor
        channel = sequence_editor.active_strip.channel if sequence_editor.active_strip else 1
        frame_end = current_frame + 25

        my_channel = find_available_channel(sequence_editor, current_frame, frame_end, channel)

        color_strip = sequence_editor.sequences.new_effect(
            name="New Strip",
            type='COLOR',
            channel=my_channel,
            frame_start=current_frame,
            frame_end=frame_end)
        if motif_type_enum == "option_macro":
            color_strip.color = (1, 0, 0)
        elif motif_type_enum == "option_cue":
            color_strip.color = (0, 0, .5)
        elif motif_type_enum == "option_flash":
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
    

class SEQUENCER_OT_alva_refresh_audio_object_selection(Operator):
    bl_idname = "alva_seq.refresh_audio_object_selection"
    bl_label = ""
    bl_description = "Refresh after making changes to speaker routing"

    def execute(self, context):
        strip = context.scene.sequence_editor.active_strip
        strip.selected_stage_object = strip.selected_stage_object
        return {'FINISHED'}
    
 
class SEQUENCER_OT_alva_bake_audio(Operator):
    bl_idname = "alva_seq.export_audio"
    bl_label = "May Take > 1 Hour"
    bl_description = "Create separate audio files for external playback, with 3D mixing built into the files. Route each sound file to the correct speaker inside a group cue. WARNING: Can take a very long time to complete"
    bl_options = {'UNDO'}

    filepath: StringProperty(
        name="File Path",
        description="Filepath for exporting the audio",
        default="",
        maxlen=1024,
        subtype='FILE_PATH'
    )

    REDRAW_INTERVAL = 100  # UI redraws must be limited because they slow the program considerably

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        '''
        This operator is responsible for creating a folder hierarchy that allows any many-channel
        audio player to play back 3D audio. A "many-channel audio player" is a software, like 
        Qlab, that can play back more than 2 tracks simultaneously while sending each track to 
        a different speaker. 

        The folder hierarchy created by this operator includes the files for all 3D audio objects
        in the scene. 

        1. Mute all other track other than the current one so they don't bleed
        2. Create main folder for entire scene based on user-specified directory (invoke method)
        3. Create a subfolder to contain all the speaker tracks for current sound strip
        4. Bake volume keyframes for entire scene for that speaker/sound_strip pair
        5. Mixdown that file with its volume keyframes in a vacuum
        6. Go back to Step 4 for the next speaker until all speakers are done
        7. Go back to Step 3 for the next sound strip until all the sound strips are done
        '''
        scene = context.scene
        sounds = [strip for strip in context.sequences if strip.type == 'SOUND']
        for strip in sounds:
            if strip.selected_stage_object is None:
                continue

            self.mute_others(sounds, strip)
            main_folder_path = self.make_main_folder()
            subfolder_path = self.make_subfolder(main_folder_path, strip)
            sound_object = bpy.data.objects[strip.selected_stage_object.name]
            speaker_lists = [sl for sl in sound_object.speaker_list if sl.name == strip.name]
            
            for speaker_list in speaker_lists:
                for speaker in speaker_list.speakers:
                    self.bake_keyframes(strip, scene, speaker, sound_object)
                    self.create_sound_file_in_subfolder(subfolder_path, speaker)

        self.report({'INFO'}, "Folders created")
        return {'FINISHED'}

    def mute_others(self, sounds, strip):
        for other_strip in sounds:
            if other_strip != strip:
                other_strip.mute = True
        strip.mute = False

    def make_main_folder(self):
        base_directory = os.path.dirname(self.filepath)
        main_folder_path = os.path.join(base_directory, "Sound Scene")
        if not os.path.exists(main_folder_path):
            os.makedirs(main_folder_path)
        return main_folder_path

    def make_subfolder(self, main_folder_path, strip):
        subfolder_path = os.path.join(main_folder_path, strip.name)
        if not os.path.exists(subfolder_path):
            os.makedirs(subfolder_path)
        return subfolder_path

    def render_frame(self, scene, frame, strip, speaker, sound_object):
        scene.frame_set(frame)
        strip.volume = render_volume(speaker.speaker_pointer, sound_object, strip.int_sound_cue)
        strip.keyframe_insert(data_path="volume", frame=frame)
        self.update_ui(frame)

    def update_ui(self, frame):
        if frame % self.REDRAW_INTERVAL == 0:
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

    def bake_keyframes(self, strip, scene, speaker, sound_object):
        for frame in range(int(strip.frame_start), int(strip.frame_final_end)):
            self.render_frame(scene, frame, strip, speaker, sound_object)

    def create_sound_file_in_subfolder(self, subfolder_path, speaker):
        output_path = os.path.join(subfolder_path, f"{speaker.speaker_number}.wav")
        bpy.ops.sound.mixdown(filepath=output_path, 
                            container='WAV', 
                            codec='PCM', 
                            format='F32', 
                            split_channels=False)


misc_operators = [
    SEQUENCER_OT_alva_analyze_song,
    SEQUENCER_OT_alva_add_offset,
    SEQUENCER_OT_alva_generate_strips,
    SEQUENCER_OT_alva_add_color_strip,
    SEQUENCER_OT_alva_delete_events,
    SEQUENCER_OT_alva_command_line,
    TOOL_OT_alva_duplicate_strip_to_above,
    SEQUENCER_OT_alva_add,
    SEQUENCER_OT_alva_refresh_audio_object_selection,
    SEQUENCER_OT_alva_bake_audio
]


def register():
    for cls in hotkeys_popups:
        bpy.utils.register_class(cls)
    for cls in macro_operators:
        bpy.utils.register_class(cls)
    for cls in misc_operators:
        bpy.utils.register_class(cls)
    
    
def unregister():
    for cls in reversed(hotkeys_popups):
        bpy.utils.unregister_class(cls)
    for cls in reversed(macro_operators):
        bpy.utils.unregister_class(cls)
    for cls in reversed(misc_operators):
        bpy.utils.unregister_class(cls)