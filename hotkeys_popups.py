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
from bpy.types import Operator, Menu
import os
import bpy.utils.previews
import inspect


# Purpose of this throughout the codebase is to proactively identify possible pre-bugs and to help diagnose bugs.
def sorcerer_assert_unreachable(*args):
    caller_frame = inspect.currentframe().f_back
    caller_file = caller_frame.f_code.co_filename
    caller_line = caller_frame.f_lineno
    message = "Error found at {}:{}\nCode marked as unreachable has been executed. Please report bug to Alva Theaters.".format(caller_file, caller_line)
    print(message)


preview_collections = {}


snare_state = "snare_complete"


def find_available_channel(self, sequence_editor, start_frame, end_frame, preferred_channel):
    channels = {strip.channel for strip in sequence_editor.sequences_all
                if strip.frame_final_start < end_frame and strip.frame_final_end > start_frame}
    # Start searching from the preferred channel upwards
    current_channel = preferred_channel
    while current_channel in channels:
        current_channel += 1
    return current_channel
    

class VSEStripScalingOperator(bpy.types.Operator):
    """Scale the length of a single strip or the offsets between multiple selected strips in the VSE"""
    bl_idname = "vse.scale_strips"
    bl_label = "Scale VSE Strips"

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
            scale_factor = 1 + delta_x * 0.003  # scale factor should start from 1, not 0.

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

    
class VSEExtrudeStripsOperator(bpy.types.Operator):
    bl_idname = "sequencer.vse_extrude_strips"
    bl_label = "Extrude VSE Strips"
    
    first_mouse_x = None
    pattern_length = None
    pattern_details = None
    
    active_strip_name = ""
    active_strip_color = (1, 1, 1)  # Default to white, (R, G, B)
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
        self.active_strip_start_frame_macro = active_strip.start_frame_macro
        self.active_strip_end_frame_macro = active_strip.end_frame_macro
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
            
            print("num_duplicates:", num_duplicates)
            print("last_extruded_frame_end:", self.last_extruded_frame_end)
            print("pattern end:", self.pattern_details[-1][1])
            print("pattern length:", self.pattern_length)

            # Check if we need to create a new strip based on the mouse movement.
            if num_duplicates > 0 and (self.last_extruded_frame_end is None or 
               num_duplicates > (self.last_extruded_frame_end - self.pattern_details[-1][1]) // self.pattern_length):
                
                print("through check")
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
            new_strip.start_frame_macro = self.active_strip_start_frame_macro
            new_strip.end_frame_macro = self.active_strip_end_frame_macro
            new_strip.trigger_prefix = self.active_strip_trigger_prefix
            new_strip.osc_trigger = self.active_strip_osc_trigger
            new_strip.osc_trigger_end = self.active_strip_osc_trigger_end
            new_strip.friend_list = self.active_strip_friend_list
            
            new_strip.my_settings.motif_type_enum = motif_type
            

class VSEBumpStripChannelOperator(bpy.types.Operator):
    bl_idname = "sequencer.vse_bump_strip_channel"
    bl_label = "Bump VSE Strip Channel"
    bl_options = {'REGISTER', 'UNDO'}

    direction: bpy.props.IntProperty()

    def execute(self, context):
        for strip in context.selected_sequences:
            new_channel = max(1, strip.channel + self.direction)
            strip.channel = new_channel
        return {'FINISHED'}


class VSEDeselectOperator(bpy.types.Operator):
    bl_idname = "sequencer.vse_deselect_all"
    bl_label = "Deselect All"

    def execute(self, context):
        for strip in context.selected_sequences:
            strip.select = False
        return {'FINISHED'}
    
    
class VSENewColorStripOperator(bpy.types.Operator):
    bl_idname = "sequencer.vse_new_color_strip"
    bl_label = "New Color Strip"

    def execute(self, context):
        global snare_state
        
        current_frame = context.scene.frame_current
        sequence_editor = context.scene.sequence_editor
        
        # Start by trying to place the strip on the same channel as the active strip, or default to 1.
        channel = sequence_editor.active_strip.channel if sequence_editor.active_strip else 1
        frame_end = current_frame + 25
        
        # Find an available channel where the new strip will not overlap.
        channel = find_available_channel(self, sequence_editor, current_frame, frame_end, channel)
        
        # Now create the strip on the available channel.
        if bpy.context.scene.is_armed_release:
            color_strip = sequence_editor.sequences.new_effect(
                    name="New Strip",
                    type='COLOR',
                    channel=channel,
                    frame_start=current_frame,
                    frame_end=frame_end)
            
            color_strip.color = (0, 0, 0)

            # Deselect all other strips and set the new strip as the active one.
            for strip in sequence_editor.sequences_all:
                strip.select = False
            
            color_strip.select = True 
            context.scene.sequence_editor.active_strip = color_strip
            
        snare_state = "snare_complete"
        
        return {'FINISHED'}
    
    
class VSENewColorStripKickOperator(bpy.types.Operator):
    bl_idname = "sequencer.vse_new_color_strip_kick"
    bl_label = "New Color Strip"

    def execute(self, context):
        global snare_state
        
        if snare_state == "snare_complete":
            
            current_frame = context.scene.frame_current
            sequence_editor = context.scene.sequence_editor
            
            channel = sequence_editor.active_strip.channel if sequence_editor.active_strip else 1
            print(f"Channel is {channel}")
            frame_end = current_frame + 25
            
            channel = find_available_channel(self, sequence_editor, current_frame, frame_end, channel)
            
            color_strip = sequence_editor.sequences.new_effect(
                    name="New Strip",
                    type='COLOR',
                    channel=channel,
                    frame_start=current_frame,
                    frame_end=frame_end)
            
            color_strip.color = (1, 1, 1)

            for strip in sequence_editor.sequences_all:
                strip.select = False
            
            color_strip.select = True 
            context.scene.sequence_editor.active_strip = color_strip  # Set active strip
            
            snare_state = "waiting_on_snare"
        return {'FINISHED'}

    
class LeftOperator(bpy.types.Operator):
    bl_idname = "sequencer.left_operator"
    bl_label = "Left Operator"

    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        selected_strips = [strip for strip in sequence_editor.sequences_all if strip.select]
        for strip in selected_strips:
            strip.frame_start -= 1
        return {'FINISHED'}


class RightOperator(bpy.types.Operator):
    bl_idname = "sequencer.right_operator"
    bl_label = "Right Operator"

    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        selected_strips = [strip for strip in sequence_editor.sequences_all if strip.select]
        for strip in selected_strips:
            strip.frame_start += 1
        return {'FINISHED'}
    
    
class LeftLongOperator(bpy.types.Operator):
    bl_idname = "sequencer.left_long_operator"
    bl_label = "Left Long Operator"

    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        selected_strips = [strip for strip in sequence_editor.sequences_all if strip.select]
        for strip in selected_strips:
            strip.frame_start -= 5
        return {'FINISHED'}
    
    
class RightLongOperator(bpy.types.Operator):
    bl_idname = "sequencer.right_long_operator"
    bl_label = "Right Long Operator"

    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        selected_strips = [strip for strip in sequence_editor.sequences_all if strip.select]
        for strip in selected_strips:
            strip.frame_start += 5
        return {'FINISHED'}


class One(bpy.types.Operator):
    bl_idname = "sequencer.one"
    bl_label = "Select Channel One"

    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        for strip in sequence_editor.sequences_all:
            if strip.channel == 1:
                strip.select = True
        return {'FINISHED'}
    
    
class Two(bpy.types.Operator):
    bl_idname = "sequencer.two"
    bl_label = "Select Channel 2"

    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        for strip in sequence_editor.sequences_all:
            if strip.channel == 2:
                strip.select = True
        return {'FINISHED'}
    

class Three(bpy.types.Operator):
    bl_idname = "sequencer.three"
    bl_label = "Select Channel 3"

    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        for strip in sequence_editor.sequences_all:
            if strip.channel == 3:
                strip.select = True
        return {'FINISHED'}
    
    
class Four(bpy.types.Operator):
    bl_idname = "sequencer.four"
    bl_label = "Select Channel 4"

    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        for strip in sequence_editor.sequences_all:
            if strip.channel == 4:
                strip.select = True
        return {'FINISHED'}
    
    
class Five(bpy.types.Operator):
    bl_idname = "sequencer.five"
    bl_label = "Select Channel 5"

    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        for strip in sequence_editor.sequences_all:
            if strip.channel == 5:
                strip.select = True
        return {'FINISHED'}
    
    
    
class Six(bpy.types.Operator):
    bl_idname = "sequencer.six"
    bl_label = "Select Channel 6"

    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        for strip in sequence_editor.sequences_all:
            if strip.channel == 6:
                strip.select = True
        return {'FINISHED'}

    
class Seven(bpy.types.Operator):
    bl_idname = "sequencer.seven"
    bl_label = "Select Channel 7"

    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        for strip in sequence_editor.sequences_all:
            if strip.channel == 7:
                strip.select = True
        return {'FINISHED'}
    
    
class Eight(bpy.types.Operator):
    bl_idname = "sequencer.eight"
    bl_label = "Select Channel 8"

    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        for strip in sequence_editor.sequences_all:
            if strip.channel == 8:
                strip.select = True
        return {'FINISHED'}
    
    
class Nine(bpy.types.Operator):
    bl_idname = "sequencer.nine"
    bl_label = "Select Channel 9"

    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        for strip in sequence_editor.sequences_all:
            if strip.channel == 9:
                strip.select = True
        return {'FINISHED'}
    
    
class Ten(bpy.types.Operator):
    bl_idname = "sequencer.ten"
    bl_label = "Select Channel 10"

    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        for strip in sequence_editor.sequences_all:
            if strip.channel == 10:
                strip.select = True
        return {'FINISHED'}
    
      
class Eleven(bpy.types.Operator):
    bl_idname = "sequencer.eleven"
    bl_label = "Select Channel Eleven"

    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        for strip in sequence_editor.sequences_all:
            if strip.channel == 11:
                strip.select = True
        return {'FINISHED'}
    
    
class Twelve(bpy.types.Operator):
    bl_idname = "sequencer.twelve"
    bl_label = "Select Channel 12"

    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        for strip in sequence_editor.sequences_all:
            if strip.channel == 12:
                strip.select = True
        return {'FINISHED'}
    

class Thirteen(bpy.types.Operator):
    bl_idname = "sequencer.thirteen"
    bl_label = "Select Channel 13"

    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        for strip in sequence_editor.sequences_all:
            if strip.channel == 13:
                strip.select = True
        return {'FINISHED'}
    
    
class Fourteen(bpy.types.Operator):
    bl_idname = "sequencer.fourteen"
    bl_label = "Select Channel 14"

    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        for strip in sequence_editor.sequences_all:
            if strip.channel == 14:
                strip.select = True
        return {'FINISHED'}
    
    
class Fifteen(bpy.types.Operator):
    bl_idname = "sequencer.fifteen"
    bl_label = "Select Channel 15"

    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        for strip in sequence_editor.sequences_all:
            if strip.channel == 15:
                strip.select = True
        return {'FINISHED'}
    
    
class Sixteen(bpy.types.Operator):
    bl_idname = "sequencer.sixteen"
    bl_label = "Select Channel 16"
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        for strip in sequence_editor.sequences_all:
            if strip.channel == 16:
                strip.select = True
        return {'FINISHED'}


class Seventeen(bpy.types.Operator):
    bl_idname = "sequencer.seventeen"
    bl_label = "Select Channel 71"

    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        for strip in sequence_editor.sequences_all:
            if strip.channel == 17:
                strip.select = True
        return {'FINISHED'}
    
      
class Eighteen(bpy.types.Operator):
    bl_idname = "sequencer.eighteen"
    bl_label = "Select Channel 18"

    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        for strip in sequence_editor.sequences_all:
            if strip.channel == 18:
                strip.select = True
        return {'FINISHED'}
       
    
class Nineteen(bpy.types.Operator):
    bl_idname = "sequencer.nineteen"
    bl_label = "Select Channel 19"

    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        for strip in sequence_editor.sequences_all:
            if strip.channel == 19:
                strip.select = True
        return {'FINISHED'}
    
    
class Twenty(bpy.types.Operator):
    bl_idname = "sequencer.twenty"
    bl_label = "Select Channel 20"

    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        for strip in sequence_editor.sequences_all:
            if strip.channel == 20:
                strip.select = True
        return {'FINISHED'}
    
    
def determine_popup_contexts(sequence_editor, active_strip):
    """
    Determines the alva_context and console_context based on the selected strips in the sequence_editor.
    """

    if sequence_editor and active_strip:
        selected_color_strips = []
        selected_sound_strips = []
        selected_video_strips = []
        selected_strips = []
        if active_strip:
            motif_type = active_strip.my_settings.motif_type_enum
            alva_context = "no_selection"
            console_context = "no_motif_type"
        
        for strip in sequence_editor.sequences:
            if strip.select:
                selected_strips.append(strip)
                if strip.type == 'COLOR':
                    selected_color_strips.append(strip)
                elif strip.type == 'SOUND':
                    selected_sound_strips.append(strip)
                elif strip.type == 'MOVIE':
                    selected_video_strips.append(strip)
        
        if selected_strips:
            if len(selected_strips) != len(selected_color_strips) and selected_color_strips:
                alva_context = "incompatible_types"
            elif selected_sound_strips and not selected_color_strips and len(selected_strips) == 1:
                alva_context = "only_sound"
            elif len(selected_sound_strips) == 1 and len(selected_video_strips) == 1 and len(selected_strips) == 2:
                alva_context = "one_video_one_audio"
            elif len(selected_sound_strips) == 1 and len(selected_video_strips) == 1 and len(selected_strips) == 3:
                alva_context = "one_video_one_audio"
            elif not (selected_color_strips or selected_sound_strips):
                alva_context = "none_relevant"
            elif len(selected_strips) == len(selected_color_strips) and selected_color_strips and active_strip.type == 'COLOR':
                alva_context = "only_color"
                
        elif not selected_strips:
            alva_context = "none_relevant"
      
        if alva_context == "only_color":
            if motif_type == "option_eos_macro":
                console_context = "macro"
            elif motif_type == "option_eos_cue":
                console_context = "cue"
            elif motif_type == "option_eos_flash":
                console_context = "flash"
            elif motif_type == "option_animation":
                console_context = "animation"
            elif motif_type == "option_trigger":
                console_context = "trigger"
    else:
        alva_context = "none_relevant"
        console_context = "none"

    return alva_context, console_context


## Must become class-level draw function, avoid repeating large chunks of code.
class ModalStripController(Operator):
    bl_idname = "seq.show_strip_properties"
    bl_label = "Strip Media"
    
    @classmethod
    def poll(cls, context):
        return (context.scene is not None) and (context.scene.sequence_editor is not None) and (context.scene.sequence_editor.active_strip is not None)

    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=300)
    
    def draw(self, context):   
        scene = context.scene
        layout = self.layout   
        
        pcoll = preview_collections["main"]
        orb = pcoll["orb"]
          
        if not hasattr(scene, "sequence_editor") and scene.sequence_editor:
            row = column.row(align=True)
            row.operator("my.add_macro", text="", icon='REC')
            row.operator("my.add_cue", text="", icon='PLAY')
            row.operator("my.add_flash", text="", icon='LIGHT_SUN')
            row.operator("my.add_animation", text="", icon='IPO_BEZIER')
            row.label(text="Welcome to Sorcerer! Press O while in sequencer or add color strip to start.")
            row.label(text="or add color strip to start.")
            column.separator()
            return

        # Check if the sequence editor and active strip exist.
        elif hasattr(scene, "sequence_editor") and scene.sequence_editor:
            sequence_editor = scene.sequence_editor
            if hasattr(sequence_editor, "active_strip") and sequence_editor.active_strip:
                active_strip = sequence_editor.active_strip
                alva_context, console_context = determine_popup_contexts(sequence_editor, active_strip)
            else:
                alva_context = "none_relevant"
                console_context = "none"
            column = layout.column(align=True)

            if alva_context == "incompatible_types":
                column.separator()
                row = column.row(align=True)
                row.prop(scene.my_tool, "motif_names_enum", text="", icon='COLOR', icon_only=True)
                row.prop(active_strip, "name", text="")
                row.operator("my.add_macro", text="", icon='REC')
                row.operator("my.add_cue", text="", icon='PLAY')
                row.operator("my.add_flash", text="", icon='LIGHT_SUN')
                row.operator("my.add_animation", text="", icon='IPO_BEZIER')
                row.operator("my.add_trigger", text="", icon='SETTINGS')
                column.separator()
                row = column.row()
                row.label(text="Non-color strips selected.")
                return
             
            if alva_context == "only_sound":
                row = column.row(align=True)
                row.operator("my.mute_button", icon='HIDE_OFF' if not active_strip.mute else 'HIDE_ON')
                row.prop(active_strip, "name", text="")
                column.separator()
                column.separator()
                box = column.box()  
                row = box.row(align=True)
                row.operator("my.bump_tc_left_five", text="", icon='BACK')
                row.operator("my.bump_tc_left_one", text="", icon='TRIA_LEFT')
                row.operator("my.bump_tc_right_one", text="", icon='TRIA_RIGHT')
                row.operator("my.bump_tc_right_five", text="", icon='FORWARD')
                row.prop(active_strip, "song_timecode_clock_number", text="Event List #")
                row.operator("my.clear_timecode_clock", icon="CANCEL")
                box.separator()     
                row = box.row()
                row.prop(active_strip, "execute_on_cue_number", text='"Enable" Cue #')
                row = box.row()
                row.prop(active_strip, "execute_with_macro_number", text="With Macro #")
                row.operator("my.execute_on_cue_operator", icon_value=orb.icon_id)
                box.separator()
                row = box.row()
                row.prop(active_strip, "disable_on_cue_number", text='"Disable" Cue #')
                row = box.row()
                row.prop(active_strip, "disable_with_macro_number", text="With Macro #")
                row.operator("my.disable_on_cue_operator", icon_value=orb.icon_id)
                box.separator()
                row = box.row()
                row.operator("my.generate_text", icon="TEXT")
                box.separator()
                row = box.row(align=True)
                row.operator("my.bump_left_five", icon='BACK')
                row.operator("my.bump_left_one", icon='BACK')
                row.operator("my.bump_up", icon='TRIA_UP')
                row.operator("my.bump_down", icon='TRIA_DOWN')
                row.operator("my.bump_right_one", icon='FORWARD')
                row.operator("my.bump_right_five", icon='FORWARD')
                return
                
            if alva_context == "one_video_one_audio":
                row = column.row(align=True)
                row.prop(scene.my_tool, "motif_names_enum", text="", icon='COLOR', icon_only=True)
                row.prop(active_strip, "name", text="")
                row.operator("my.add_macro", text="", icon='REC')
                row.operator("my.add_cue", text="", icon='PLAY')
                row.operator("my.add_flash", text="", icon='LIGHT_SUN')
                row.operator("my.add_animation", text="", icon='IPO_BEZIER')
                if scene.triggers_enabled:
                    row.operator("my.add_trigger", text="", icon='SETTINGS')
                column.separator()
                row = column.row()
                row.label(text="Non-color strips selected.")
                return
                    
            if alva_context == "none_relevant":
                row = column.row(align=True)
                row.prop(scene.my_tool, "motif_names_enum", text="", icon='COLOR', icon_only=True)
                if hasattr(sequence_editor, "active_strip") and sequence_editor.active_strip:
                    active_strip = sequence_editor.active_strip
                    if active_strip and active_strip.type == 'COLOR':
                        row.prop(active_strip, "motif_name", text="")
                row.operator("my.add_macro", text="", icon='REC')
                row.operator("my.add_cue", text="", icon='PLAY')
                row.operator("my.add_flash", text="", icon='LIGHT_SUN')
                row.operator("my.add_animation", text="", icon='IPO_BEZIER')
                if scene.triggers_enabled:
                    row.operator("my.add_trigger", text="", icon='SETTINGS')
                    
                column.separator()
                return
            
            ###############
            # COLOR HEADER
            ###############
            if alva_context == "only_color":
                row = column.row(align=True)
                strip_type = active_strip.my_settings.motif_type_enum
                row.prop(scene.my_tool, "motif_names_enum", text="", icon='REC' if strip_type == "option_eos_macro" else 'PLAY' if strip_type == "option_eos_cue" else 'OUTLINER_OB_LIGHT' if strip_type == "option_eos_flash" else 'IPO_BEZIER' if strip_type == "option_animation" else 'SETTINGS', icon_only=True)
                if active_strip.is_linked and not console_context == "animation":
                    row.alert = 1
                row.prop(active_strip, "motif_name", text="")
                row.alert = 0
                row.operator("my.add_macro", text="", icon='REC')
                row.operator("my.add_cue", text="", icon='PLAY')
                row.operator("my.add_flash", text="", icon='LIGHT_SUN')
                row.operator("my.add_animation", text="", icon='IPO_BEZIER')
                if scene.triggers_enabled:
                    row.operator("my.add_trigger", text="", icon='SETTINGS')       
                column.separator()
                column.separator()
                active_strip = context.scene.sequence_editor.active_strip
                box = column.box()  
                row = box.row(align=True)
                row.operator("my.mute_button", icon='HIDE_OFF' if not active_strip.mute else 'HIDE_ON')
                my_settings = active_strip.my_settings
                row.prop(my_settings, "motif_type_enum", expand=True)
                if active_strip.is_linked and console_context != "animation":
                    row.alert = 1
                    row.prop(active_strip, "is_linked", icon='LINKED')
                else:
                    row.alert = 0
                    row.prop(active_strip, "is_linked", icon='UNLINKED')
  
                ###############
                # MACRO STRIPS
                ###############
                if console_context == "macro":
                    box = column.box()
                    row = box.row()
                    row.label(text='* = "Sneak Time " + [Strip length]')
                    row = box.row(align=True)
                    row.operator("my.start_macro_search", icon='VIEWZOOM')
                    row.prop(active_strip, "start_frame_macro", text="Start frame macro #")
                    row.operator("my.start_macro_fire", icon='FILE_REFRESH')
                    row.prop(active_strip, "start_macro_muted", icon='HIDE_OFF' if not active_strip.start_macro_muted else 'HIDE_ON', toggle=True)
                    row = box.row(align=True)
                    row.prop(active_strip, "start_frame_macro_text_gui")
                    row.operator("my.generate_start_frame_macro", icon_value=orb.icon_id)
                    row = box.separator()
                    row = box.row(align=True)
                    row.operator("my.end_macro_search", icon='VIEWZOOM')
                    row.prop(active_strip, "end_frame_macro", text="End frame macro #")
                    row.operator("my.end_macro_fire", icon='FILE_REFRESH')
                    row.prop(active_strip, "end_macro_muted", icon='HIDE_OFF' if not active_strip.end_macro_muted else 'HIDE_ON', toggle=True)
                    row = box.row(align=True)
                    row.prop(active_strip, "end_frame_macro_text_gui")
                    row.operator("my.generate_end_frame_macro", icon_value=orb.icon_id)
                                
                ###############
                # CUE STRIPS
                ###############             
                if console_context == "cue":
                    box = column.box() 
                    row = box.row(align=True)  
                    row.prop(active_strip, "eos_cue_number", text="Cue #")
                    row.operator("my.go_to_cue_out_operator", text="", icon='GHOST_ENABLED')
                    if scene.cue_builder_toggle:
                        row.operator("my.update_builder", text="", icon='FILE_REFRESH')
                    row.operator("my.record_cue", text="", icon='REC')
                    row.operator("my.sync_cue", icon_value=orb.icon_id)
                    box.separator()
                    row = box.row(align=True)
                    row.prop(active_strip, "background_color", text="")
                    row.prop(active_strip, "accent_color", text="")
                    if scene.cue_builder_toggle:
                        row = box.row(align=True)
                        row.operator("my.key_groups", text="", icon='PREFERENCES')
                        row.prop(active_strip, "key_light", text="Key Light", slider=True)
                        if active_strip.key_is_recording:
                            row.alert = 1
                        else:
                            row.alert = 0
                        row.operator("my.focus_one", text="", icon='EVENT_F1')
                        row.operator("my.focus_two", text="", icon='EVENT_F2')
                        row.operator("my.focus_three", text="", icon='EVENT_F3')
                        row.operator("my.focus_four", text="", icon='EVENT_F4')
                        row.prop(active_strip, "key_is_recording", text="", icon='REC')
                        row.alert = 0
                        row = box.row(align=True)
                        row.operator("my.rim_groups", text="", icon='PREFERENCES')
                        row.prop(active_strip, "rim_light", text="Rim Light", slider=True)
                        if active_strip.rim_is_recording:
                            row.alert = 1
                        else:
                            row.alert = 0
                        row.operator("my.focus_rim_one", text="", icon='EVENT_F1')
                        row.operator("my.focus_rim_two", text="", icon='EVENT_F2')
                        row.enabled = 0
                        row.operator("my.focus_rim_three", text="", icon='EVENT_F3')
                        row.enabled = 1
                        row.operator("my.focus_rim_four", text="", icon='EVENT_F4')
                        row.prop(active_strip, "rim_is_recording", text="", icon='REC')
                        row.alert = 0
                        row = box.row(align=True)
                        row.operator("my.fill_groups", text="", icon='PREFERENCES')
                        row.prop(active_strip, "fill_light", text="Fill Light", slider=True)
                        if active_strip.fill_is_recording:
                            row.alert = 1
                        else:
                            row.alert = 0
                        row.operator("my.focus_fill_one", text="", icon='EVENT_F1')
                        row.operator("my.focus_fill_two", text="", icon='EVENT_F2')
                        row.operator("my.focus_fill_three", text="", icon='EVENT_F3')
                        row.operator("my.focus_fill_four", text="", icon='EVENT_F4')
                        row.prop(active_strip, "fill_is_recording", text="", icon='REC')
                        row.alert = 0
                        if scene.using_gels_for_cyc:
                            row = box.row(align=True)
                            row.operator("my.gel_one_groups", text="", icon='PREFERENCES')
                            row.prop(active_strip, "background_light_one", text="Cyc 1", slider=True)
                            row.prop(active_strip, "background_light_two", text="Cyc 2", slider=True)
                            row.prop(active_strip, "background_light_three", text="Cyc 3", slider=True)
                            row.prop(active_strip, "background_light_four", text="Cyc 4", slider=True)
                        else:
                            row = box.row(align=True)
                            row.operator("my.gel_one_groups", text="", icon='PREFERENCES')
                            row.prop(active_strip, "background_light_one", text="Cyclorama", slider=True)
                            if active_strip.cyc_is_recording:
                                row.alert = 1
                            else:
                                row.alert = 0
                            row.operator("my.focus_cyc_one", text="", icon='COLORSET_01_VEC')
                            row.operator("my.focus_cyc_two", text="", icon='COLORSET_02_VEC')
                            row.operator("my.focus_cyc_three", text="", icon='COLORSET_03_VEC')
                            row.operator("my.focus_cyc_four", text="", icon='COLORSET_04_VEC')
                            row.operator("my.focus_cyc_five", text="", icon='COLORSET_05_VEC')
                            row.operator("my.focus_cyc_six", text="", icon='COLORSET_06_VEC')
                            row.operator("my.focus_cyc_seven", text="", icon='COLORSET_07_VEC')
                            row.operator("my.focus_cyc_eight", text="", icon='COLORSET_08_VEC')
                            row.prop(active_strip, "cyc_is_recording", text="", icon='REC')
                            row.alert = 0
                        row = box.row(align=True)
                        row.operator("my.texture_groups", text="", icon='PREFERENCES')
                        row.prop(active_strip, "texture_light", text="Texture", slider=True)
                        if active_strip.texture_is_recording:
                            row.alert = 1
                        else:
                            row.alert = 0
                        row.operator("my.focus_texture_one", text="", icon='COLORSET_01_VEC')
                        row.operator("my.focus_texture_two", text="", icon='COLORSET_02_VEC')
                        row.operator("my.focus_texture_three", text="", icon='COLORSET_03_VEC')
                        row.operator("my.focus_texture_four", text="", icon='COLORSET_04_VEC')
                        row.operator("my.focus_texture_five", text="", icon='COLORSET_05_VEC')
                        row.operator("my.focus_texture_six", text="", icon='COLORSET_06_VEC')
                        row.operator("my.focus_texture_seven", text="", icon='COLORSET_07_VEC')
                        row.operator("my.focus_texture_eight", text="", icon='COLORSET_08_VEC')
                        row.prop(active_strip, "texture_is_recording", text="", icon='REC')
                        row.alert = 0
                        row = box.row(align=True)
                        row.operator("my.band_groups", text="", icon='PREFERENCES')
                        row.prop(active_strip, "band_light", text="Band Light", slider=True)
                        if active_strip.band_is_recording:
                            row.alert = 1
                        else:
                            row.alert = 0
                        row.operator("my.focus_band_one", text="", icon='COLORSET_01_VEC')
                        row.operator("my.focus_band_two", text="", icon='COLORSET_02_VEC')
                        row.operator("my.focus_band_three", text="", icon='COLORSET_03_VEC')
                        row.operator("my.focus_band_four", text="", icon='COLORSET_04_VEC')
                        row.operator("my.focus_band_five", text="", icon='COLORSET_05_VEC')
                        row.operator("my.focus_band_six", text="", icon='COLORSET_06_VEC')
                        row.operator("my.focus_band_seven", text="", icon='COLORSET_07_VEC')
                        row.operator("my.focus_band_eight", text="", icon='COLORSET_08_VEC')
                        row.prop(active_strip, "band_is_recording", text="", icon='REC')
                        row.alert = 0
                        row = box.row(align=True)
                        row.operator("my.accent_groups", text="", icon='PREFERENCES')
                        row.prop(active_strip, "accent_light", text="Accent Light", slider=True)
                        if active_strip.accent_is_recording:
                            row.alert = 1
                        else:
                            row.alert = 0
                        row.operator("my.focus_accent_one", text="", icon='COLORSET_01_VEC')
                        row.operator("my.focus_accent_two", text="", icon='COLORSET_02_VEC')
                        row.operator("my.focus_accent_three", text="", icon='COLORSET_03_VEC')
                        row.operator("my.focus_accent_four", text="", icon='COLORSET_04_VEC')
                        row.operator("my.focus_accent_five", text="", icon='COLORSET_05_VEC')
                        row.operator("my.focus_accent_six", text="", icon='COLORSET_06_VEC')
                        row.operator("my.focus_accent_seven", text="", icon='COLORSET_07_VEC')
                        row.operator("my.focus_accent_eight", text="", icon='COLORSET_08_VEC')
                        row.prop(active_strip, "accent_is_recording", text="", icon='REC')
                        row.alert = 0
                        box.separator()
                        row = box.row(align=True)
                        row.operator("my.energy_groups", text="", icon='PREFERENCES')
                        row.prop(active_strip, "energy_light", text="Energy Intensity", slider=True)
                        row = box.row(align=True)
                        row.operator("my.stop_effect", text="", icon='CANCEL')
                        if active_strip.cue_builder_effect_id == "1":
                            row.alert = 1
                        row.operator("my.focus_energy_one", text="", icon='SHADERFX')
                        row.alert = 0
                        if active_strip.cue_builder_effect_id == "2":
                            row.alert = 1
                        row.operator("my.focus_energy_two", text="", icon='SHADERFX')
                        row.alert = 0
                        if active_strip.cue_builder_effect_id == "3":
                            row.alert = 1
                        row.operator("my.focus_energy_three", text="", icon='SHADERFX')
                        row.alert = 0
                        if active_strip.cue_builder_effect_id == "4":
                            row.alert = 1
                        row.operator("my.focus_energy_four", text="", icon='SHADERFX')
                        row.alert = 0
                        if active_strip.cue_builder_effect_id == "5":
                            row.alert = 1
                        row.operator("my.focus_energy_five", text="", icon='SHADERFX')
                        row.alert = 0
                        if active_strip.cue_builder_effect_id == "6":
                            row.alert = 1
                        row.operator("my.focus_energy_six", text="", icon='SHADERFX')
                        row.alert = 0
                        row.prop(active_strip, "energy_speed", text="Speed", slider=True)
                        row.prop(active_strip, "energy_scale", text="Scale", slider=True)
                        
                ###############
                # FLASH STRIPS
                ###############        
                if console_context == "flash":
                    box = column.box()  
                    row = box.row()
                    row.prop(scene, "examples_panel_toggle", icon="TRIA_DOWN" if scene.examples_panel_toggle else "TRIA_RIGHT", icon_only=True, emboss=False)
                    row.label(text="Examples")
                    if scene.examples_panel_toggle:
                        row = box.row()
                        row.label(text="Type in what feels natural.")
                        row = box.row()
                        row.label(text='"1" becomes "Channel 1 at Full')
                        row = box.row()
                        row.label(text='"g1cp6" becomes "Group 1 Color_Palette 6')
                        row = box.row()
                        row.label(text='"136 45" becomes "Channel 136 at 45')
                        row = box.row()
                        row.label(text='"1 at full", "1 100"  "1 full", "group 14, 15 36"')
                        row = box.row()
                        row.label(text='"1 at color palette 4", "1 cp 4", "group 14-17 ip 2"')
                        row = box.row()
                        row.label(text='"sub 1 full", "submaster 3 75", "sub 1,3,4,7-10 75"')
                    box = column.box()
                    row = box.row()
                    row.prop(active_strip, "flash_using_nodes", text="Use Nodes" if not active_strip.flash_using_nodes else "Using Nodes", slider=True, icon='NODETREE')
                    row = box.row()
                    if active_strip.flash_using_nodes:
                        row.enabled = False
                    row = box.label(text="Flash Up: " + active_strip.flash_input_background)
                    row = box.row()
                    if active_strip.flash_using_nodes:
                        row.enabled = False
                    row.prop(active_strip, "flash_input")
                    row = box.row()
                    if active_strip.flash_using_nodes:
                        row.enabled = False
                    row = box.label(text="Flash Down: " + active_strip.flash_down_input_background)
                    row = box.row()
                    if active_strip.flash_using_nodes:
                        row.enabled = False
                    row.prop(active_strip, "flash_down_input")
                    row = box.separator()
                    row = box.row()
                    row.enabled = True
                    row.operator("my.flash_macro_search", text="", icon='VIEWZOOM')
                    row.prop(active_strip, "start_flash_macro_number", text="M 1")
                    row.prop(active_strip, "end_flash_macro_number", text="M 2")
                    row.prop(active_strip, "flash_bias", text="Bias", slider=True)
                    row.operator("my.build_flash_macros", text="", icon_value=orb.icon_id)
                    row = box.row()
                    if active_strip.flash_bias > 0:
                        row.label(text="Bias: Flash will come in slower and go out faster.")
                    if active_strip.flash_bias < 0:
                        row.label(text="Bias: Flash will come in faster and go out slower.")
                    if active_strip.flash_bias == 0:
                        row.label(text="Bias: Flash will come in and go out at same speed.")
            
                ##################
                # ANIMATION STRIPS
                ##################                       
                if console_context == "animation":
                    box = column.box()
                    box.separator()
                    row = box.row(align=True)
                    row.operator("my.clear_intensity", icon='CANCEL')
                    row.prop(active_strip, "intensity_prefix", text="")
                    col = box.row(align=True)
                    row.prop(active_strip, "osc_intensity", text="Intensity", slider=True)
                    row.operator("my.keyframe_intensity", icon='KEYTYPE_KEYFRAME_VEC')
                    row.operator("my.view_graph", icon='IPO_BEZIER')
                    row = box.separator()
                    row = box.row(align=True)
                    row.operator("my.clear_red", icon='CANCEL')
                    row.prop(active_strip, "red_prefix", text="")
                    row.label(text="")
                    row = box.row(align=True)
                    row.operator("my.clear_green", icon='CANCEL')
                    row.prop(active_strip, "green_prefix", text="")
                    row.prop(active_strip, "osc_color", text="")
                    row.operator("my.keyframe_color", icon='KEYTYPE_KEYFRAME_VEC')
                    row.operator("my.view_graph", icon='IPO_BEZIER')
                    row = box.row(align=True)
                    row.operator("my.clear_blue", icon='CANCEL')
                    row.prop(active_strip, "blue_prefix", text="")
                    row.label(text="")
                    row = box.separator()
                    if not active_strip.use_paths:
                        row = box.row(align=True)
                        row.operator("my.clear_pan", icon='CANCEL')
                        row.prop(active_strip, "use_paths", text="", icon='CURVE_BEZCURVE')
                        row.prop(active_strip, "pan_prefix", text="")
                        row.prop(active_strip, "osc_pan", text="Pan", slider=True)
                        row.operator("my.keyframe_pan", icon='KEYTYPE_KEYFRAME_VEC')
                        row.operator("my.view_graph", icon='IPO_BEZIER')
                        row = box.row(align=True)
                        row.operator("my.clear_tilt", icon='CANCEL')
                        row.prop(active_strip, "use_paths", text="", icon='CURVE_BEZCURVE')
                        row.prop(active_strip, "tilt_prefix", text="")
                        row.prop(active_strip, "osc_tilt", text="Tilt", slider=True)
                        row.operator("my.keyframe_tilt", icon='KEYTYPE_KEYFRAME_VEC')
                        row.operator("my.view_graph", icon='IPO_BEZIER')
                    else:
                        row = box.row(align=True)
                        row.operator("my.clear_pan", icon='CANCEL')
                        row.alert = 1
                        row.prop(active_strip, "use_paths", text="", icon='CURVE_BEZCURVE')
                        row.alert = 0
                        row.prop(active_strip, "pan_prefix", text="")
                        row.operator("my.clear_tilt", icon='CANCEL')
                        row.alert = 1
                        row.prop(active_strip, "use_paths", text="", icon='CURVE_BEZCURVE')
                        row.alert = 0
                        row.prop(active_strip, "tilt_prefix", text="")
                        row = box.row(align=True)
                        row.prop_search(active_strip, "selected_light", bpy.data, "objects", text="", icon='LIGHT_SPOT')
                    row = box.separator()
                    row = box.row(align=True)
                    row.operator("my.clear_zoom", icon='CANCEL')
                    row.prop(active_strip, "zoom_prefix", text="")
                    row = box.row(align=True)
                    row.operator("my.reset_zoom_range", icon='X')
                    row.operator("my.set_min_zoom", icon='REMOVE')
                    row.prop(active_strip, "osc_zoom", text="Custom 1", slider=True)
                    row.operator("my.set_max_zoom", icon='ADD')
                    row.operator("my.keyframe_zoom", icon='KEYTYPE_KEYFRAME_VEC')
                    row.operator("my.view_graph", icon='IPO_BEZIER')
                    row = box.separator()
                    row = box.row(align=True)
                    row.operator("my.clear_iris", icon='CANCEL')
                    row.prop(active_strip, "iris_prefix", text="")
                    row = box.row(align=True)
                    row.operator("my.reset_iris_range", icon='X')
                    row.operator("my.set_min_iris", icon='REMOVE')
                    row.prop(active_strip, "osc_iris", text="Custom 2", slider=True)
                    row.operator("my.set_max_iris", icon='ADD')
                    row.operator("my.keyframe_iris", icon='KEYTYPE_KEYFRAME_VEC')
                    row.operator("my.view_graph", icon='IPO_BEZIER')
                    row = box.separator()
                    row = box.row(align=True)
                    row.operator("my.replace_button", text="Replace * with:")
                    row.prop(scene, "replacement_value", text='', icon='FILE_PARENT')
                    if scene.auto_update_replacement:
                        row.alert = 1
                    row.prop(scene, "auto_update_replacement", text="", icon="LINKED")
                    row.alert = 0
                    row.operator("my.add_strip_operator", text="", icon='ADD')
                    row = box.row(align=True)
                    row.operator("my.record_preset", text="Store Preset", icon='NLA_PUSHDOWN')
                    row.operator("my.load_preset", text="Load Preset", icon='FILE_PARENT')
                    row.alert = 1
                    row.operator("my.osc_help_button", text="Help")
                    row.alert= 0
                    row = box.separator()
                    box = column.box()  
                    row = box.row()
                    row.prop(active_strip, "paths_panel_toggle", icon="TRIA_DOWN" if active_strip.paths_panel_toggle else "TRIA_RIGHT", icon_only=True, emboss=False)
                    row.label(text="Motion Paths Help", icon='CURVE_BEZCURVE')
                    if active_strip.paths_panel_toggle:
                        row = box.row(align=True)
                        row.label(text="Motion paths can allow you to make a mover")
                        row = box.row()
                        row.label(text="draw a unicorn. Use it to track mover motion")
                        row = box.row()
                        row.label(text="to any bezier path. For it to work, you")
                        row = box.row(align=True)
                        row.label(text="must create a light, a path, and an empty")
                        row = box.row()
                        row.label(text="inside 3D view. Set the empty to follow")
                        row = box.row()
                        row.label(text="the path and set the light to track the")
                        row = box.row(align=True)
                        row.label(text="empty. Then use 'Offset' to move the empty")
                        row = box.row()
                        row.label(text="along the path. 'Track To' constraint should")
                        row = box.row()
                        row.label(text="usually be set to -Z for To and Y for Up.")
                        row = box.row(align=True)
                        row.label(text="'Follow Path' constraint should usually be set")
                        row = box.row()
                        row.label(text="to Y for Forward and Z for Up. These settings")
                        row = box.row()
                        row.label(text="may vary. Mess with it until it works. Moderate")
                        row = box.row(align=True)
                        row.label(text="level of basic Blender experience is recommended")
                        row = box.row()
                        row.label(text="to use this feature without pain and swearing.")
                        row = box.row(align=True)
                        row.label(text="Look for Blender tutorials online or ask")
                        row = box.row()
                        row.label(text="Alva Theaters for help if needed.")
                        row = box.row(align=True)
                        row.label(text="Alva Theaters help email: help@alvatheaters.com")
                        row = box.row(align=True)
                        row.label(text="For venting frustration: thisisdumb@alvatheaters.com")
                    box = column.box()  
                    row = box.row()
                    row.prop(scene, "bake_panel_toggle", icon="TRIA_DOWN" if scene.bake_panel_toggle else "TRIA_RIGHT", icon_only=True, emboss=False)
                    row.label(text="Create a Qmeo", icon='FILE_MOVIE')
                    if scene.bake_panel_toggle:
                        row = box.row(align=True)
                        row.operator("my.delete_animation_cue_list_operator", text="", icon='CANCEL')
                        row.prop(active_strip, "animation_cue_list_number", text="Cue List")
                        #row = box.row(align=True)
                        row.operator("my.delete_animation_event_list_operator", text="", icon='CANCEL')
                        #row.operator("my.stop_animation_clock_operator", text="", icon='PAUSE')
                        row.prop(active_strip, "animation_event_list_number", text="Event List")
                        #row = box.row()
                        row.operator("my.bake_fcurves_to_cues_operator", text="", icon_value=orb.icon_id)
                        #row = box.row()
                        row.operator("my.rerecord_cues_operator", text="", icon_value=orb.icon_id)
                        #box.separator()
                        row = box.row()
                        row.prop(active_strip, "execute_animation_on_cue_number", text='"Enable" Cue #')
                        #row = box.row()
                        row.prop(active_strip, "execute_animation_with_macro_number", text="With Macro #")
                        row.operator("my.execute_animation_on_cue_operator", icon_value=orb.icon_id)
                        #box.separator()
                        row = box.row()
                        row.prop(active_strip, "disable_animation_on_cue_number", text='"Disable" Cue #')
                        #row = box.row()
                        row.prop(active_strip, "disable_animation_with_macro_number", text="With Macro #")
                        row.operator("my.disable_animation_on_cue_operator", icon_value=orb.icon_id)
                        box.separator()
                      
                ################
                # TRIGGER STRIPS
                ################                        
                if console_context == "trigger":
                    box = column.box()
                    box.separator()
                    row = box.row()
                    split = row.split(factor=0.25)
                    split.label(text="Address:")
                    split.prop(active_strip, "trigger_prefix", text="")
                    row = box.separator()
                    row = box.row()
                    split = row.split(factor=0.35)
                    split.label(text="Start Argument:")
                    split.prop(active_strip, "osc_trigger", text="")
                    row = box.row()
                    split = row.split(factor=0.35)
                    split.label(text="End Argument:")
                    split.prop(active_strip, "osc_trigger_end", text="")
                    row = box.row()
                    box = column.box()
                    row = box.row()
                    row.label(text='Add offsets. "(1-10), (20-11)" for example.')
                    row = box.row()
                    row.prop(active_strip, "friend_list", text="")
                    
            else:
                print("Alva Context:", alva_context)
                row = column.row()
                row.label(text="No active color strip.")
                return           
                          
            if not scene.bake_panel_toggle and console_context != "animation":
                box.separator()
            row = column.row(align=True)
            row.operator("my.bump_left_five", icon='BACK')
            row.operator("my.bump_left_one", icon='BACK')
            row.operator("my.bump_up", icon='TRIA_UP')
            row.operator("my.bump_down", icon='TRIA_DOWN')
            row.operator("my.bump_right_one", icon='FORWARD')
            row.operator("my.bump_right_five", icon='FORWARD')
            return
        
        
class ModalStripFormatter(Operator):
    bl_idname = "seq.show_strip_formatter"
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
                alva_context, console_context = determine_popup_contexts(sequence_editor, active_strip)
            else:
                alva_context = "none_relevant"
                console_context = "none"
            column = layout.column(align=True)
            
            if alva_context == "only_color":
                row = column.row(align=True)
                if scene.is_filtering_left == True:
                    row.alert = 1
                    row.prop(scene, "is_filtering_left", icon='FILTER')
                    row.alert = 0
                elif scene.is_filtering_left == False:
                    row.alert = 0
                    row.prop(scene, "is_filtering_left", icon='FILTER')
                row.operator("my.select_similar", text="Select Magnetic:") 
                if scene.is_filtering_right == True:
                    row.alert = 1
                    row.prop(scene, "is_filtering_right", icon='FILTER')
                    row.alert = 0
                elif scene.is_filtering_right == False:
                    row.alert = 0
                    row.prop(scene, "is_filtering_right", icon='FILTER')
                row = column.row(align=True)
                row.prop(scene, "color_is_magnetic", text="", icon='SNAP_OFF' if not scene.color_is_magnetic else 'SNAP_ON')
                row.prop(active_strip, "color", text="")
                row.operator("my.copy_color_operator", text="", icon='FILE')
                row.operator("my.color_trigger", text="", icon='RESTRICT_SELECT_OFF')
                row = column.row(align=True)
                row.prop(scene, "strip_name_is_magnetic", text="", icon='SNAP_OFF' if not scene.strip_name_is_magnetic else 'SNAP_ON')
                row.prop(active_strip, "name", text="")  
                row.operator("my.copy_strip_name_operator", text="", icon='FILE')
                row.operator("my.strip_name_trigger", text="", icon='RESTRICT_SELECT_OFF')
                row = column.row(align=True)
                row.prop(scene, "channel_is_magnetic", text="", icon='SNAP_OFF' if not scene.channel_is_magnetic else 'SNAP_ON')
                row.prop(active_strip, "channel", text_ctxt="Channel: ")
                row.operator("my.copy_channel_operator", text="", icon='FILE')
                row.operator("my.channel_trigger", text="", icon='RESTRICT_SELECT_OFF')          
                row = column.row(align=True)
                row.prop(scene, "duration_is_magnetic", text="", icon='SNAP_OFF' if not scene.duration_is_magnetic else 'SNAP_ON')
                row.prop(active_strip, "frame_final_duration", text="Duration")
                row.operator("my.copy_duration_operator", text="", icon='FILE')
                row.operator("my.duration_trigger", text="", icon='RESTRICT_SELECT_OFF')
                row = column.row(align=True)
                row.prop(scene, "start_frame_is_magnetic", text="", icon='SNAP_OFF' if not scene.start_frame_is_magnetic else 'SNAP_ON')
                row.prop(active_strip, "frame_start", text="Start Frame")
                row.operator("my.start_frame_jump", text="", icon='PLAY')
                row.operator("my.copy_start_frame_operator", text="", icon='FILE')
                row.operator("my.start_frame_trigger", text="", icon='RESTRICT_SELECT_OFF')
                row = column.row(align=True)
                row.prop(scene, "end_frame_is_magnetic", text="", icon='SNAP_OFF' if not scene.end_frame_is_magnetic else 'SNAP_ON')
                row.prop(active_strip, "frame_final_end", text="End Frame")
                row.operator("my.end_frame_jump", text="", icon='PLAY')
                row.operator("my.copy_end_frame_operator", text="", icon='FILE')
                row.operator("my.end_frame_trigger", text="", icon='RESTRICT_SELECT_OFF')
                row = column.row(align=True)
                row.operator("my.copy_above_to_selected", text="Copy Various to Selected", icon='FILE')
                column.separator()
                if scene.i_know_the_shortcuts == False:
                    row = column.row(align=True)
                    row.operator("my.alva_extrude", text="Extrude")
                    row = column.row(align=True)
                    row.operator("my.alva_scale", text="Scale")
                    row = column.row(align=True)
                    row.operator("my.alva_grab", text="Grab")
                    row = column.row(align=True)
                    row.operator("my.alva_grab_x", text="Grab X")
                    row.operator("my.alva_grab_y", text="Grab Y")
                    row = column.row(align=True)
                    row.operator("my.cut_operator", text="Cut")
                    row = column.row(align=True)
                    row.operator("my.add_media_operator", text="Add Media")
                    row = column.row(align=True)
                    row.operator("my.assign_to_channel_operator", text="Assign to Channel")
                    row = column.row(align=True)
                    row.operator("my.set_start_frame_operator", text="Set Start Frame")
                    row = column.row(align=True)
                    row.operator("my.set_end_frame_operator", text="Set End Frame")
                row = column.row(align=True)
                row.prop(scene, "i_know_the_shortcuts", text="I know the shortcuts.")
                selected_color_strips = []
                selected_strips = []
                for strip in sequence_editor.sequences:
                    if strip.select:
                        selected_strips.append(strip)
                        if strip.type == 'COLOR':
                            selected_color_strips.append(strip)
                if len(selected_color_strips) > 1:
                    column.separator()
                    column.separator()
                    row = column.row(align=True)
                    row.prop(scene, "offset_value", text="Offset in BPM")
                    row.operator("my.add_offset", text="", icon='CENTER_ONLY')
                    column.separator()

            elif alva_context == "only_sound":
                row = column.row(align=True)
                row.operator("my.mute_button", icon='HIDE_OFF' if not active_strip.mute else 'HIDE_ON')
                row.prop(active_strip, "name", text="")
                row = column.row(align=True)
                row.prop(active_strip, "song_bpm_input", text="Beats per minute (BPM)")
                row = column.row(align=True)
                row.prop(active_strip, "beats_per_measure", text="Beats per measure")
                row = column.row(align=True)
                row.prop(active_strip, "song_bpm_channel", text="Generate on channel")
                row.operator("my.generate_strips", text="", icon='COLOR')
                column.separator()
                row = column.row(align=True)
                row.operator("my.start_end_frame_mapping", icon='PREVIEW_RANGE')
                row = column.row(align=True)
                row.operator("my.time_map", text="Zero Timecode", icon='TIME')
                column.separator()
                row = column.row(align=True)
                row.prop(active_strip, "show_waveform", slider=True)
                row = column.row()
                row.prop(active_strip, "volume", text="Volume")
                
            elif alva_context == "one_video_one_audio":
                selected_sound_strips = []
                selected_video_strips = []
                selected_strips = []
                if sequence_editor:
                    for strip in sequence_editor.sequences:
                        if strip.select:
                            selected_strips.append(strip)
                            if strip.type == 'SOUND':
                                selected_sound_strips.append(strip)
                            elif strip.type == 'MOVIE':
                                selected_video_strips.append(strip)
                selected_sound_strip = selected_sound_strips[0]
                selected_video_strip = selected_video_strips[0]
                row = column.row(align=True)
                row.operator("my.mute_button", icon='HIDE_OFF' if not active_strip.mute else 'HIDE_ON')
                row.prop(active_strip, "name", text="")
                row = column.row(align=True)
                if selected_sound_strip.frame_start != selected_video_strip.frame_start or selected_sound_strip.frame_final_duration != selected_video_strip.frame_final_duration:
                    row.alert = 1
                    row.operator("my.sync_video")
                row = column.row(align=True)
                row.operator("my.start_end_frame_mapping", icon='PREVIEW_RANGE')
                row = column.row(align=True)
                row.operator("my.time_map", icon='TIME')
        
            else:
                row = column.row(align=True)            
                row.prop(scene, "channel_selector", text="Channel")
                row.operator("my.select_channel", text="", icon='RESTRICT_SELECT_OFF')           
                row = column.row(align=True)
                row.prop(scene, "generate_quantity", text="Quantity")
                row = column.row(align=True)
                if scene.generate_quantity > 1:
                    row.prop(scene, "normal_offset", text="Offset by")
                row = column.row(align=True)
                row.operator("my.add_color_strip", icon='COLOR')        
                column.separator()
                return
            
            
class ModalSequencerSettings(Operator):
    bl_idname = "seq.show_sequencer_settings"
    bl_label = "Sequencer Settings"
    
    @classmethod
    def poll(cls, context):
        return (context.scene is not None) and (context.scene.sequence_editor is not None)

    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=500)
    
    def draw(self, context):
        if context.scene:
            layout = self.layout
            scene = context.scene
            sequence_editor = context.scene.sequence_editor
            column = layout.column(align=True)
            row = column.row()
            
            if not context.scene.animation_enabled:
                row.label('To enable animation, type, ')
                row = column.row()
                row.label('"I understand that ETC Eos')
                row = column.row()
                row.label('cannot store this data locally')
                row = column.row()
                row.label('and it is not safe to use this bonus') 
                row = column.row()
                row.label('feature during a real show on Eos."')
                row = column.separator()
                row = column.separator()
                row = column.separator()
                row = column.separator()
                row = column.row()
                row.prop(scene, "i_understand_animation", text="")
                row = column.separator()
                row = column.separator()
                row = column.row()
                row.operator("my.enable_animation")
                row = column.separator()
                row = column.separator()
                row = column.separator()
                row = column.separator()
                row = column.separator()
                row = column.separator()
                row = column.separator()
                row = column.separator()
                
            if not context.scene.triggers_enabled:
                row = column.row()
                row.label(text='To enable triggers, type, ')
                row = column.row()
                row.label(text='"I understand this bonus feature is')
                row = column.row()
                row.label(text="unrecordable for Eos. ETC Eos cannot")
                row = column.row()
                row.label(text="store these locally. I should not") 
                row = column.row()
                row.label(text='use this during a real show with Eos."')
                row = column.separator()
                row = column.separator()
                row = column.separator()
                row = column.separator()
                row = column.row()
                row.prop(scene, "i_understand_triggers", text="")
                row = column.separator()
                row = column.separator()
                row = column.row()
                row.operator("my.enable_triggers")
                row = column.separator()
                row = column.separator()
                row = column.separator()
                row = column.separator()
                row = column.separator()
                row = column.separator()
                row = column.separator()
                row = column.separator()
            row = column.row()
            row.prop(context.scene, "is_armed_livemap", slider=True, text="Livemap")
            row = column.separator()
            row = column.separator()
            row = column.row()
            row.prop(context.scene, "sync_timecode", slider=True, text="Sync timecode on console")
            if context.scene.sync_timecode:
                row.prop(context.scene, "timecode_expected_lag", text="Expected lag in frames")
            row = column.separator()
            row = column.separator()
            row = column.row()
            row.prop(context.scene, "is_armed_release", slider=True, text="Add secondary strip on release of O key")    
            row = column.separator()
            row = column.separator()
            row = column.row()
            row.prop(context.scene, "is_armed_turbo", slider=True, text="Orb skips Shift+Update")
            row = column.separator()
            row = column.separator()
            row = column.separator()
            row = column.separator()
            row = column.row()
            row.prop(context.scene, "cue_builder_toggle", slider=True)
            row = column.separator()
            row = column.separator()
            row = column.row()
            row.prop(context.scene, "using_gels_for_cyc", text="Using gels for cyc color", slider=True) 
            row = column.separator()
            row = column.separator()
            row = column.row()
            row.prop(context.scene, "cue_builder_id_offset", text="Cue builder ID offset")
            row = column.separator()
            row = column.separator() 
            row = column.separator()
            row = column.separator()
            row = column.row()
            row.prop(context.scene, "i_know_the_shortcuts", text="I know the keyboard shortcuts",  slider=True)    
            row = column.separator()
            row = column.separator()
            row = column.row()
            row.prop(context.scene, "is_updating_strip_color", text="Update strip color",  slider=True)
            row = column.separator()
            row = column.separator()
            row = column.row()
            row.label(text="Adjust frame rate in a Blender Properties window.")
            row = column.row()
            row.label(text="Frame rate must be a whole number.")
            row = column.separator()
            row = column.separator()
            box = column.box()
            row = box.row()
            row.label(text="Automatically adjust house lights on play/stop:")
            box = column.box()
            row = box.row()
            row.label(text="House Prefix: ")
            row = box.row()
            row.prop(scene, "house_prefix", text="")
            box.separator()
            row = box.row()
            row.prop(scene, "house_down_on_play", text="House Down on Play", slider=True)
            row = box.row()
            row.prop(scene, "house_down_argument", text="")
            box.separator()
            row = box.row()
            row.prop(scene, "house_up_on_stop", text="House Up on Stop", slider=True)
            row = box.row()
            row.prop(scene, "house_up_argument", text="")
            row = column.separator()
            row = column.separator()
            row = column.row()
            if scene.scene_props.school_mode_enabled:
                row.label(text="Disable school mode:", icon='LOCKED')
            else:
                row.label(text="Enable school mode:", icon='UNLOCKED')
            row = column.row()
            row.prop(scene.scene_props, "school_mode_password", text="")
            column.separator()
            column.separator()
            if not scene.scene_props.school_mode_enabled:
                box = column.box()
                row = box.row()
                row.label(text="Lighting Console OSC RX (Receive) Settings:")
                box = column.box()
                row = box.row()
                row.prop(scene.scene_props, "str_osc_ip_address", text="IP Address")
                row = box.row()
                row.label(text="Port:")
                row.prop(scene.scene_props, "int_osc_port", text="")
                
                
class ModalNodeSettings(Operator):
    bl_idname = "nodes.show_node_settings"
    bl_label = "Node Settings"
    
    @classmethod
    def poll(cls, context):
        return (context.scene is not None)

    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=500)
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene.scene_props
        column = layout.column(align=True)
        print(scene.school_mode_enabled)
        
        if not scene.school_mode_enabled:
#            row = column.row()
#            row.label(text="Harmonizer Settings:")
#            
#            row = column.row()
#            if scene.is_democratic:
#                row.alert = 1
#            row.operator("my.democratic_operator", text="Democratic", icon='HEART')
#            row.alert = 0
#            if scene.is_not_democratic:
#                row.alert = 1
#            row.operator("my.non_democratic_operator", text="Non-democratic", icon='ORPHAN_DATA')
#            row.alert = 0
#            
#            column.separator()
#            column.separator()
            
            box = column.box()
            row = box.row()
            row.label(text="Lighting Console OSC RX (Receive) Settings:")
            box = column.box()
            row = box.row()
            row.prop(scene, "str_osc_ip_address", text="IP Address")
            row = box.row()
            row.label(text="Port:")
            row.prop(scene, "int_osc_port", text="")
            
            column.separator()
            
            row = column.row()
            row.prop(scene, "bool_eos_console_mode", text="Eos Console Mode", toggle=False)
            row.label(text="")
            
            column.separator()
        
        row = column.row()
        if scene.school_mode_enabled:
            row.label(text="Disable school mode:", icon='LOCKED')
        else:
            row.label(text="Enable school mode:", icon='UNLOCKED')
            
        row = column.row()
        row.prop(scene, "school_mode_password", text="")
        column.separator()
        
        if not scene.school_mode_enabled: 
            column.separator()
            layout.separator()
            
            box = column.box()  
            row = box.row()

            row.prop(scene, "expand_prefixes_is_on", icon="TRIA_DOWN" if scene.expand_prefixes_is_on else "TRIA_RIGHT", icon_only=True, emboss=False)

            row.label(text="OSC Syntax Templates")      
            
            if scene.expand_prefixes_is_on:
                box = column.box()

                row = box.row()
                row.label(text="Command Line Address:")
                row = box.row()
                row.prop(scene, "str_command_line_address", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Channel Template:")
                row = box.row()
                row.prop(scene, "str_channel_template", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Group Template:")
                row = box.row()
                row.prop(scene, "str_group_template", text = "")
                
                box.separator()
                box.separator()
                box.separator()
                
                row = box.row()
                row.label(text="Intensity Argument:", icon='OUTLINER_OB_LIGHT')
                row = box.row()
                row.prop(scene, "str_intensity_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Strobe Argument:", icon='OUTLINER_OB_LIGHTPROBE')
                row = box.row()
                row.prop(scene, "str_strobe_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Pan Argument:", icon='ORIENTATION_GIMBAL')
                row = box.row()
                row.prop(scene, "str_pan_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Tilt Argument:", icon='ORIENTATION_GIMBAL')
                row = box.row()
                row.prop(scene, "str_tilt_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Red Argument:", icon='COLORSET_01_VEC')
                row = box.row()
                row.prop(scene, "str_red_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Blue Argument:", icon='COLORSET_04_VEC')
                row = box.row()
                row.prop(scene, "str_blue_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Green Argument:", icon='COLORSET_03_VEC')
                row = box.row()
                row.prop(scene, "str_green_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Amber Argument:", icon='COLORSET_02_VEC')
                row = box.row()
                row.prop(scene, "str_amber_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="White Argument:", icon='COLORSET_13_VEC')
                row = box.row()
                row.prop(scene, "str_white_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Mint Argument:", icon='COLORSET_07_VEC')
                row = box.row()
                row.prop(scene, "str_mint_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Lime Argument:", icon='COLORSET_12_VEC')
                row = box.row()
                row.prop(scene, "str_lime_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Zoom Argument:", icon='LINCURVE')
                row = box.row()
                row.prop(scene, "str_zoom_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Iris Argument:", icon='MESH_CIRCLE')
                row = box.row()
                row.prop(scene, "str_iris_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Edge Argument:", icon='SELECT_SET')
                row = box.row()
                row.prop(scene, "str_edge_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Diffusion Argument:", icon='MOD_CLOTH')
                row = box.row()
                row.prop(scene, "str_diffusion_argument", text = "")
                
                
class ModalNodeFormatter(Operator):
    bl_idname = "nodes.show_node_formatter"
    bl_label = "Node Formatter"
    
    @classmethod
    def poll(cls, context):
        return (context.scene is not None)

    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=300)
                
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        column = layout.column(align=True)
        row = column.row()
        space = context.space_data.edit_tree.nodes
        active_node = None 

        if hasattr(context.space_data, 'edit_tree') and context.space_data.edit_tree is not None:
            active_node = context.space_data.edit_tree.nodes.active

            if active_node and (active_node.bl_idname == "group_controller_type" or active_node.bl_idname == "group_driver_type" or active_node.bl_idname == "master_type"):
                row.prop(active_node, "strobe_is_on", text="Strobe", slider=True)
                row.prop(active_node, "color_is_on", text="Color", slider=True)
                
                row = column.row()
                row.prop(active_node, "pan_tilt_is_on", text="Pan/Tilt", slider=True)
                
                row = column.row()
                row.prop(active_node, "zoom_is_on", text="Zoom", slider=True)
                row.prop(active_node, "iris_is_on", text="Iris", slider=True)
                
                row = column.row()
                row.prop(active_node, "edge_is_on", text="Edge", slider=True)
                row.prop(active_node, "diffusion_is_on", text="Diffusion", slider=True)
                
                row = column.row()
                row.prop(active_node, "gobo_id_is_on", text="Gobo", slider=True)
                
                column.separator()
                
                if active_node.bl_idname == "group_controller_type":
                    row = column.row()
                    row.prop(active_node, "influence", text="Influence")
                    
                    column.separator()
                    
            elif active_node and active_node.bl_idname == "mixer_type" or active_node.bl_idname == "mixer_driver_type":
                row = layout.row(align=True)
                row.prop(active_node, "str_selected_group", text="")
                row = layout.row(align=True)
                row.prop(active_node, "parameters_enum", text="")
                if active_node.parameters_enum == 'option_color':
                    row.prop(active_node, "color_profile_enum", text="")
  
                if active_node.parameters_enum != None:
                    row = layout.row()
                    row.prop(active_node, "show_middle", text="Show Middle", slider=True)
                    
                    if not active_node.show_middle:
                        row.prop(active_node, "every_other", text="Every Other", slider=True)
                        
                row = layout.row()
                row.prop(active_node, "collapse_most", text="Collapse most")
            
        row = layout.row()
        row.prop(active_node, "label", text="Label")
        row = layout.row()
        row.prop(active_node, "use_custom_color", text="", icon='HIDE_ON' if not active_node.use_custom_color else 'HIDE_OFF')
        row.prop(active_node, "color", text="")
        
        
addon_keymaps = []


def register():
    bpy.utils.register_class(VSEStripScalingOperator)
    bpy.utils.register_class(VSEExtrudeStripsOperator)
    bpy.utils.register_class(VSEBumpStripChannelOperator)
    bpy.utils.register_class(VSEDeselectOperator)
    bpy.utils.register_class(VSENewColorStripOperator)
    bpy.utils.register_class(VSENewColorStripKickOperator)
    bpy.utils.register_class(RightOperator)
    bpy.utils.register_class(LeftOperator)
    bpy.utils.register_class(RightLongOperator)
    bpy.utils.register_class(LeftLongOperator)
    bpy.utils.register_class(One)
    bpy.utils.register_class(Two)
    bpy.utils.register_class(Three)
    bpy.utils.register_class(Four)
    bpy.utils.register_class(Five)
    bpy.utils.register_class(Six)
    bpy.utils.register_class(Seven)
    bpy.utils.register_class(Eight)
    bpy.utils.register_class(Nine)
    bpy.utils.register_class(Ten)
    bpy.utils.register_class(Eleven)
    bpy.utils.register_class(Twelve)
    bpy.utils.register_class(Thirteen)
    bpy.utils.register_class(Fourteen)
    bpy.utils.register_class(Fifteen)
    bpy.utils.register_class(Sixteen)
    bpy.utils.register_class(Seventeen)
    bpy.utils.register_class(Eighteen)
    bpy.utils.register_class(Nineteen)
    bpy.utils.register_class(Twenty)
    bpy.utils.register_class(ModalStripController)
    bpy.utils.register_class(ModalStripFormatter)
    bpy.utils.register_class(ModalSequencerSettings)
    bpy.utils.register_class(ModalNodeSettings)
    bpy.utils.register_class(ModalNodeFormatter)
    
    # Define the hotkeys
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='Sequencer', space_type='SEQUENCE_EDITOR')
    
    # Hotkey for the scaling operator
    km.keymap_items.new(VSEStripScalingOperator.bl_idname, type='S', value='PRESS')
    # Hotkey for the extrude operator
    km.keymap_items.new(VSEExtrudeStripsOperator.bl_idname, type='E', value='PRESS')
    
    # Bump up
    kmi = km.keymap_items.new('sequencer.vse_bump_strip_channel', type='U', value='PRESS')
    kmi.properties.direction = 1
    # Bump down with shift
    kmi_shift = km.keymap_items.new('sequencer.vse_bump_strip_channel', type='U', value='PRESS', shift=True)
    kmi_shift.properties.direction = -1
    
    # Deselect all
    kmi_shift = km.keymap_items.new('sequencer.vse_deselect_all', type='D', value='PRESS')
    
    # Add color strip
    kmi_shift = km.keymap_items.new('sequencer.vse_new_color_strip', type='O', value='RELEASE')
    kmi_shift = km.keymap_items.new('sequencer.vse_new_color_strip_kick', type='O', value='PRESS')
    
    kmi_shift = km.keymap_items.new('sequencer.left_operator', type='L', value='PRESS')
    kmi_shift = km.keymap_items.new('sequencer.right_operator', type='R', value='PRESS')
    
    kmi_shift = km.keymap_items.new('sequencer.left_long_operator', type='L', value='PRESS', shift=True)
    kmi_shift = km.keymap_items.new('sequencer.right_long_operator', type='R', value='PRESS', shift=True)
    
    kmi_shift = km.keymap_items.new('sequencer.one', type='ONE', value='PRESS')
    kmi_shift = km.keymap_items.new('sequencer.two', type='TWO', value='PRESS')
    kmi_shift = km.keymap_items.new('sequencer.three', type='THREE', value='PRESS')
    kmi_shift = km.keymap_items.new('sequencer.four', type='FOUR', value='PRESS')
    kmi_shift = km.keymap_items.new('sequencer.five', type='FIVE', value='PRESS')
    kmi_shift = km.keymap_items.new('sequencer.six', type='SIX', value='PRESS')
    kmi_shift = km.keymap_items.new('sequencer.seven', type='SEVEN', value='PRESS')
    kmi_shift = km.keymap_items.new('sequencer.eight', type='EIGHT', value='PRESS')
    kmi_shift = km.keymap_items.new('sequencer.nine', type='NINE', value='PRESS')
    kmi_shift = km.keymap_items.new('sequencer.ten', type='ZERO', value='PRESS')
    
    kmi_shift = km.keymap_items.new('sequencer.eleven', type='ONE', value='PRESS', shift=True)
    kmi_shift = km.keymap_items.new('sequencer.twelve', type='TWO', value='PRESS', shift=True)
    kmi_shift = km.keymap_items.new('sequencer.thirteen', type='THREE', value='PRESS', shift=True)
    kmi_shift = km.keymap_items.new('sequencer.fourteen', type='FOUR', value='PRESS', shift=True)
    kmi_shift = km.keymap_items.new('sequencer.fifteen', type='FIVE', value='PRESS', shift=True)
    kmi_shift = km.keymap_items.new('sequencer.sixteen', type='SIX', value='PRESS', shift=True)
    kmi_shift = km.keymap_items.new('sequencer.seventeen', type='SEVEN', value='PRESS', shift=True)
    kmi_shift = km.keymap_items.new('sequencer.eighteen', type='EIGHT', value='PRESS', shift=True)
    kmi_shift = km.keymap_items.new('sequencer.nineteen', type='NINE', value='PRESS', shift=True)
    kmi_shift = km.keymap_items.new('sequencer.twenty', type='ZERO', value='PRESS', shift=True)
    
    wm = bpy.context.window_manager
    if wm.keyconfigs.addon:
        # Keymap for Sequencer
        km = wm.keyconfigs.addon.keymaps.new(name='Sequencer', space_type='SEQUENCE_EDITOR')
        kmi1 = km.keymap_items.new("seq.show_strip_properties", 'M', 'PRESS')
        kmi2 = km.keymap_items.new("seq.show_strip_formatter", 'F', 'PRESS')
        addon_keymaps.append((km, kmi1))
        addon_keymaps.append((km, kmi2))

    node_editor_keyconfig = bpy.context.window_manager.keyconfigs.addon
    if node_editor_keyconfig:  # Ensure the addon keyconfig exists
        node_editor_km = node_editor_keyconfig.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')

        # Add a new keymap item
        node_editor_kmi = node_editor_km.keymap_items.new("nodes.show_node_formatter", type='F', value='PRESS')
        node_editor_kmi.active = True

        # Store keymap for unregistering
        global custom_node_editor_keymaps
        custom_node_editor_keymaps = []
        custom_node_editor_keymaps.append((node_editor_km, node_editor_kmi))
        
    # Custom icon stuff
    pcoll = bpy.utils.previews.new()
    preview_collections["main"] = pcoll
    addon_dir = os.path.dirname(__file__)
    pcoll.load("orb", os.path.join(addon_dir, "alva_orb.png"), 'IMAGE')
    
    
def unregister():
    bpy.utils.unregister_class(ModalNodeFormatter)
    bpy.utils.unregister_class(ModalNodeSettings)
    bpy.utils.unregister_class(ModalSequencerSettings)
    bpy.utils.unregister_class(ModalStripFormatter)
    bpy.utils.unregister_class(ModalStripController)
    bpy.utils.unregister_class(Twenty)
    bpy.utils.unregister_class(Nineteen)
    bpy.utils.unregister_class(Eighteen)
    bpy.utils.unregister_class(Seventeen)
    bpy.utils.unregister_class(Sixteen)
    bpy.utils.unregister_class(Fifteen)
    bpy.utils.unregister_class(Fourteen)
    bpy.utils.unregister_class(Thirteen)
    bpy.utils.unregister_class(Twelve)
    bpy.utils.unregister_class(Eleven)
    bpy.utils.unregister_class(Ten)
    bpy.utils.unregister_class(Nine)
    bpy.utils.unregister_class(Eight)
    bpy.utils.unregister_class(Seven)
    bpy.utils.unregister_class(Six)
    bpy.utils.unregister_class(Five)
    bpy.utils.unregister_class(Four)
    bpy.utils.unregister_class(Three)
    bpy.utils.unregister_class(Two)
    bpy.utils.unregister_class(One)
    bpy.utils.unregister_class(LeftLongOperator)
    bpy.utils.unregister_class(RightLongOperator)
    bpy.utils.unregister_class(LeftOperator)
    bpy.utils.unregister_class(RightOperator)
    bpy.utils.unregister_class(VSENewColorStripKickOperator)
    bpy.utils.unregister_class(VSENewColorStripOperator)
    bpy.utils.unregister_class(VSEDeselectOperator)
    bpy.utils.unregister_class(VSEBumpStripChannelOperator)
    bpy.utils.unregister_class(VSEExtrudeStripsOperator)
    bpy.utils.unregister_class(VSEStripScalingOperator)

    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.get('Sequencer')
    if km:
        for kmi in km.keymap_items:
            km.keymap_items.remove(kmi)
        wm.keyconfigs.addon.keymaps.remove(km)

    for km, kmi in custom_node_editor_keymaps:
        km.keymap_items.remove(kmi)
    custom_node_editor_keymaps.clear()

    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()


# For development purposes only.
if __name__ == "__main__":
    register()
