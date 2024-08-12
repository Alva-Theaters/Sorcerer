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


import bpy
from bpy.types import Operator
from bpy.props import IntProperty
import time

from ..ui.sequencer_ui import SequencerUI # type: ignore
from ..orb import Orb
from ..utils.utils import Utils # type: ignore
from ..utils.osc import OSC

# Custom icon stuff
import bpy.utils.previews
import os
preview_collections = {}
pcoll = bpy.utils.previews.new()
preview_collections["main"] = pcoll
addon_dir = os.path.dirname(__file__)
pcoll.load("orb", os.path.join(addon_dir, "alva_orb.png"), 'IMAGE')
pcoll = preview_collections["main"]
orb = pcoll["orb"]


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
class SEQUENCER_OT_scale_strips(Operator):  ## Scale type not the most helpful.
    """Scale the length of a single strip or the offsets between multiple selected strips in the VSE"""
    bl_idname = "seq.scale_strips"
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

    
class SEQUENCER_OT_extrude_strips(Operator):  ## New strips must inherit properties. This also must do more than 2.
    '''Extrude patterns of strips like meshes.'''
    bl_idname = "sequencer.vse_extrude_strips"
    bl_label = "Extrude VSE Strips"
    
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
            
            
class SEQUENCER_OT_duplicate_pattern(Operator):
    """Duplicate Selected Pattern"""
    bl_idname = "sequencer.duplicate_pattern"
    bl_label = "Duplicate Pattern"
    bl_options = {'REGISTER', 'UNDO'}

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
            

class SEQUENCER_OT_bump_strip(Operator):
    bl_idname = "sequencer.vse_bump_strip_channel"
    bl_label = "Bump VSE Strip Channel"
    bl_options = {'REGISTER', 'UNDO'}

    direction: IntProperty() # type: ignore # Not importing all bpy.types just for this

    def execute(self, context):
        for strip in context.selected_sequences:
            new_channel = max(1, strip.channel + self.direction)
            strip.channel = new_channel
        return {'FINISHED'}


class SEQUENCER_OT_alva_deselect(Operator):  ## Make this compatible with 3D view too.
    '''The basic, standard Deselect All button Blender refuses to provide.'''
    bl_idname = "sequencer.vse_deselect_all"
    bl_label = "Deselect All"

    def execute(self, context):
        for strip in context.selected_sequences:
            strip.select = False
        return {'FINISHED'}
 
    
snare_state = "snare_complete"
    
class SEQUENCER_OT_new_strip(Operator):
    '''Add color strip on release of Z, when Release is enabled.'''
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
        channel = Utils.find_available_channel(sequence_editor, current_frame, frame_end, channel)
        
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
    
 
class SEQUENCER_OT_new_kick(Operator):
    '''Add color strip on down press of Z key.'''
    bl_idname = "sequencer.vse_new_color_strip_kick"
    bl_label = "New Color Strip"

    def execute(self, context):
        global snare_state
        
        if snare_state == "snare_complete":
            
            current_frame = context.scene.frame_current
            sequence_editor = context.scene.sequence_editor
            
            channel = sequence_editor.active_strip.channel if sequence_editor.active_strip else 1
            frame_end = current_frame + 25
            
            channel = Utils.find_available_channel(sequence_editor, current_frame, frame_end, channel)
            
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
    
    
class SEQUENCER_OT_new_pointer(Operator):
    '''Add color strip on down press of Z key.'''
    bl_idname = "sequencer.vse_new_color_strip_pointer"
    bl_label = "New Color Strip"

    def invoke(self, context, event):
        current_frame = context.scene.frame_current
        sequence_editor = context.scene.sequence_editor

        mouse_x, mouse_y = event.mouse_region_x, event.mouse_region_y
        
        region = context.region
        region_data = context.region_data

        view2d = region.view2d
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

    
class SEQUENCER_OT_bump_universal(Operator):
    direction: IntProperty() # type: ignore

    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        selected_strips = [strip for strip in sequence_editor.sequences_all if strip.select]
        for strip in selected_strips:
            strip.frame_start += self.direction
        return {'FINISHED'}

class SEQUENCER_OT_bump_left(SEQUENCER_OT_bump_universal):
    bl_idname = "sequencer.left_operator"
    bl_label = "Left Operator"
    direction = bpy.props.IntProperty(default=-1)

class SEQUENCER_OT_bump_right(SEQUENCER_OT_bump_universal):
    bl_idname = "sequencer.right_operator"
    bl_label = "Right Operator"
    direction = bpy.props.IntProperty(default=1)

class SEQUENCER_OT_bump_left_long(SEQUENCER_OT_bump_universal):
    bl_idname = "sequencer.left_long_operator"
    bl_label = "Left Long Operator"
    direction = bpy.props.IntProperty(default=-5)

class SEQUENCER_OT_bump_right_long(SEQUENCER_OT_bump_universal):
    bl_idname = "sequencer.right_long_operator"
    bl_label = "Right Long Operator"
    direction = bpy.props.IntProperty(default=5)


class SEQUENCER_OT_select_channel(Operator):
    channel: IntProperty() # type: ignore

    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        for strip in sequence_editor.sequences_all:
            strip.select = (strip.channel == self.channel)
        return {'FINISHED'}

def create_channel_operator(channel):
    return type(
        f"Channel{channel}Operator",
        (SEQUENCER_OT_select_channel,),
        {
            "bl_idname": f"sequencer.channel_{channel}_operator",
            "bl_label": f"Select Channel {channel}",
            "channel": bpy.props.IntProperty(default=channel)
        }
    )


for i in range(1, 21):
    globals()[f"Channel{i}Operator"] = create_channel_operator(i)


class SEQUENCER_OT_format_strip(Operator):
    '''Pop-up menu for strip formatter, mostly for managing many strips at once'''
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
                alva_context, console_context = SequencerUI.determine_contexts(sequence_editor, active_strip)
            else:
                alva_context = "none_relevant"
                console_context = "none"
                
            column = layout.column(align=True)
            if alva_context == "only_color":
                SequencerUI.draw_strip_formatter_color(self, context, column, scene, sequence_editor, active_strip)

            elif alva_context == "only_sound":
                SequencerUI.draw_strip_formatter_sound(self, context, column, active_strip)
                
            elif alva_context == "one_video_one_audio":
                SequencerUI.draw_strip_formatter_video_audio(self, context, column, active_strip, sequence_editor)
                
            else:
                SequencerUI.draw_strip_formatter_generator(self, context, column, scene)
               
               
class SEQUENCER_OT_strip_media(Operator):
    '''Popup that shows the Lighting panel GUI'''
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
        SequencerUI.draw_strip_media(self, context, scene, bake_panel=False)
    
    
class SEQUENCER_OT_left_five(Operator):
    bl_idname = "my.bump_left_five"
    bl_label = "5"
    bl_description = "They're too late. This bumps selected strips backward by 5 frames. You can also do this by holding Shift and pressing L for left. Pressing L without Shift bumps the strip(s) back by just 1 frame. Hold it down continuously to go fast"
        
    def execute(self, context):
        for strip in context.selected_sequences:
            strip.frame_start -= 5
        return {'FINISHED'}
    

class SEQUENCER_OT_left_one(Operator):
    bl_idname = "my.bump_left_one"
    bl_label = "1"
    bl_description = "They're a smidge late. This bumps selected strips backward by 1 frame. You can also do this by pressing L for left. Pressing L with Shift down bumps the strip(s) back by 5 frames"
    
    def execute(self, context):
        for strip in context.selected_sequences:
            strip.frame_start -= 1
        return {'FINISHED'}
    

class SEQUENCER_OT_up(Operator):
    bl_idname = "my.bump_up"
    bl_label = ""
    bl_description = "This bumps selected strips up 1 channel. Pressing 1-9 selects channels 1-9, pressing 0 selects channel 10, and holding shift down gets you to channel 20. Also, press U to bump up and Shift + U to bump down."
    
    def execute(self, context):
        for strip in context.selected_sequences:
            strip.channel += 1
        return {'FINISHED'}
    

class SEQUENCER_OT_alva_mute(Operator):
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
   
    
class SEQUENCER_OT_bump_down(Operator):
    bl_idname = "my.bump_down"
    bl_label = ""
    bl_description = "This bumps selected strips down 1 channel. Pressing 1-9 selects channels 1-9, pressing 0 selects channel 10, and holding shift down gets you to channel 20. Also, press U to bump up and Shift + U to bump down."
    
    def execute(self, context):
        for strip in context.selected_sequences:
            strip.channel -= 1
        return {'FINISHED'}
    

class SEQUENCER_OT_right_one(Operator):
    bl_idname = "my.bump_right_one"
    bl_label = "1"
    bl_description = "They're a smidge early. This bumps selected strips forward by 1 frame. You can also do this by pressing R for right. Pressing R with Shift down bumps the strip(s) forwward by 5 frames"
    
    def execute(self, context):
        for strip in context.selected_sequences:
            strip.frame_start += 1
        return {'FINISHED'}


class SEQUENCER_OT_right_five(Operator):
    bl_idname = "my.bump_right_five"
    bl_label = "5"
    bl_description = "They're too early. This bumps selected strips forward by 5 frames. You can also do this by holding Shift and pressing R for right. Pressing R without Shift bumps the strip(s) forward by just 1 frame. Hold it down continuously to go fast"
    
    def execute(self, context):
        for strip in context.selected_sequences:
            strip.frame_start += 5
        return {'FINISHED'}
    
    
def bump_timecode(context, time):
    active_strip = context.scene.sequence_editor.active_strip
    event_list = active_strip.int_event_list
    OSC.send_osc_lighting("/eos/newcmd", f"Event {str(event_list)} / 1 Thru 1000000 Time + {str(time)} Enter")

class SEQUENCER_OT_tc_left_five(Operator):
    bl_idname = "my.bump_tc_left_five"
    bl_label = "5"
    bl_description = "They're too late. Bump console's event list events back 5 frames. The event list this is applied to is determined by the Event List field above. This only works for ETC Eos"
    
    def execute(self, context):
        bump_timecode(context, -5)
        return {'FINISHED'}    
    
class SEQUENCER_OT_tc_left_one(Operator):
    bl_idname = "my.bump_tc_left_one"
    bl_label = "1"
    bl_description = "They're a smidge late. Bump console's event list events back 1 frame. The event list this is applied to is determined by the Event List field above. This only works for ETC Eos"
    
    def execute(self, context):
        bump_timecode(context, -1)
        return {'FINISHED'}

class SEQUENCER_OT_tc_right_one(Operator):
    bl_idname = "my.bump_tc_right_one"
    bl_label = "1"
    bl_description = "They're a smidge early. Bump console's event list events forward 1 frame. The event list this is applied to is determined by the Event List field above. This only works for ETC Eos"
    
    def execute(self, context):
        bump_timecode(context, 1)
        return {'FINISHED'}

class SEQUENCER_OT_tc_right_five(Operator):
    bl_idname = "my.bump_tc_right_five"
    bl_label = "5"
    bl_description = "They're too early. Bump console's event list events forward 5 frames. The event list this is applied to is determined by the Event List field above. This only works for ETC Eos"
    
    def execute(self, context):
        bump_timecode(context, 5)
        return {'FINISHED'}
    
    
class SEQUENCER_OT_select_channel(Operator):
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
    

class SEQUENCER_OT_render_strips(Operator):
    bl_idname = "seq.render_strips_operator"
    bl_label = "Render Strips"
    bl_description = "Orb will create timecode events for every Macro, Cue, and Flash strip on the relevant sound strip's event list. Shortcut is Shift+Spacebar"

    @classmethod
    def poll(cls, context):
        relevant_strips = [strip for strip in context.scene.sequence_editor.sequences_all if strip.frame_final_end >= context.scene.frame_start and strip.frame_start <= context.scene.frame_end and (strip.type == 'COLOR' or strip.type == 'SOUND')]
        return len(relevant_strips) >= 1

    def invoke(self, context, event):
        return Orb.render_strips(self, context, event)


class SEQUENCER_OT_select_similar(Operator):
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

        if scene.is_filtering_left == False:
            
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
                                                
        elif scene.is_filtering_left == True:
                            
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


hotkeys_popups = [
    SEQUENCER_OT_scale_strips,
    SEQUENCER_OT_extrude_strips,
    SEQUENCER_OT_duplicate_pattern,
    SEQUENCER_OT_bump_strip,
    SEQUENCER_OT_alva_deselect,
    SEQUENCER_OT_new_strip,
    SEQUENCER_OT_new_kick,
    SEQUENCER_OT_new_pointer,
    SEQUENCER_OT_bump_left,
    SEQUENCER_OT_bump_right,
    SEQUENCER_OT_bump_left_long,
    SEQUENCER_OT_bump_right_long,
    SEQUENCER_OT_select_channel,
    SEQUENCER_OT_render_strips,
    SEQUENCER_OT_format_strip,
    SEQUENCER_OT_strip_media,
    SEQUENCER_OT_left_five,
    SEQUENCER_OT_left_one,
    SEQUENCER_OT_up,
    SEQUENCER_OT_alva_mute,
    SEQUENCER_OT_bump_down,
    SEQUENCER_OT_right_one,
    SEQUENCER_OT_right_five,
    SEQUENCER_OT_tc_left_five,
    SEQUENCER_OT_tc_left_one,
    SEQUENCER_OT_tc_right_one,
    SEQUENCER_OT_tc_right_five,
    SEQUENCER_OT_select_similar
]


# VSE channel select hotkeys.
class SEQUENCER_OT_channel_1(Operator):
    bl_idname = "my.channel_1"
    bl_label = "Channel 1"
    bl_description = "Select all strips in channel 1"
    
    def execute(self, context):
        select_strips_in_channel(context, 1)
        return {'FINISHED'}

class SEQUENCER_OT_channel_2(Operator):
    bl_idname = "my.channel_2"
    bl_label = "Channel 2"
    bl_description = "Select all strips in channel 2"
    
    def execute(self, context):
        select_strips_in_channel(context, 2)
        return {'FINISHED'}

class SEQUENCER_OT_channel_3(Operator):
    bl_idname = "my.channel_3"
    bl_label = "Channel 3"
    bl_description = "Select all strips in channel 3"
    
    def execute(self, context):
        select_strips_in_channel(context, 3)
        return {'FINISHED'}

class SEQUENCER_OT_channel_4(Operator):
    bl_idname = "my.channel_4"
    bl_label = "Channel 4"
    bl_description = "Select all strips in channel 4"
    
    def execute(self, context):
        select_strips_in_channel(context, 4)
        return {'FINISHED'}

class SEQUENCER_OT_channel_5(Operator):
    bl_idname = "my.channel_5"
    bl_label = "Channel 5"
    bl_description = "Select all strips in channel 5"
    
    def execute(self, context):
        select_strips_in_channel(context, 5)
        return {'FINISHED'}

class SEQUENCER_OT_channel_6(Operator):
    bl_idname = "my.channel_6"
    bl_label = "Channel 6"
    bl_description = "Select all strips in channel 6"
    
    def execute(self, context):
        select_strips_in_channel(context, 6)
        return {'FINISHED'}

class SEQUENCER_OT_channel_7(Operator):
    bl_idname = "my.channel_7"
    bl_label = "Channel 7"
    bl_description = "Select all strips in channel 7"
    
    def execute(self, context):
        select_strips_in_channel(context, 7)
        return {'FINISHED'}

class SEQUENCER_OT_channel_8(Operator):
    bl_idname = "my.channel_8"
    bl_label = "Channel 8"
    bl_description = "Select all strips in channel 8"
    
    def execute(self, context):
        select_strips_in_channel(context, 8)
        return {'FINISHED'}

class SEQUENCER_OT_channel_9(Operator):
    bl_idname = "my.channel_9"
    bl_label = "Channel 9"
    bl_description = "Select all strips in channel 9"
    
    def execute(self, context):
        select_strips_in_channel(context, 9)
        return {'FINISHED'}

class SEQUENCER_OT_channel_10(Operator):
    bl_idname = "my.channel_10"
    bl_label = "Channel 10"
    bl_description = "Select all strips in channel 10"
    
    def execute(self, context):
        select_strips_in_channel(context, 10)
        return {'FINISHED'}

class SEQUENCER_OT_channel_11(Operator):
    bl_idname = "my.channel_11"
    bl_label = "Channel 11"
    bl_description = "Select all strips in channel 11"
    
    def execute(self, context):
        select_strips_in_channel(context, 11)
        return {'FINISHED'}

class SEQUENCER_OT_channel_12(Operator):
    bl_idname = "my.channel_12"
    bl_label = "Channel 12"
    bl_description = "Select all strips in channel 12"
    
    def execute(self, context):
        select_strips_in_channel(context, 12)
        return {'FINISHED'}

class SEQUENCER_OT_channel_13(Operator):
    bl_idname = "my.channel_13"
    bl_label = "Channel 13"
    bl_description = "Select all strips in channel 13"
    
    def execute(self, context):
        select_strips_in_channel(context, 13)
        return {'FINISHED'}

class SEQUENCER_OT_channel_14(Operator):
    bl_idname = "my.channel_14"
    bl_label = "Channel 14"
    bl_description = "Select all strips in channel 14"
    
    def execute(self, context):
        select_strips_in_channel(context, 14)
        return {'FINISHED'}

class SEQUENCER_OT_channel_15(Operator):
    bl_idname = "my.channel_15"
    bl_label = "Channel 15"
    bl_description = "Select all strips in channel 15"
    
    def execute(self, context):
        select_strips_in_channel(context, 15)
        return {'FINISHED'}

class SEQUENCER_OT_channel_16(Operator):
    bl_idname = "my.channel_16"
    bl_label = "Channel 16"
    bl_description = "Select all strips in channel 16"
    
    def execute(self, context):
        select_strips_in_channel(context, 16)
        return {'FINISHED'}

class SEQUENCER_OT_channel_17(Operator):
    bl_idname = "my.channel_17"
    bl_label = "Channel 17"
    bl_description = "Select all strips in channel 17"
    
    def execute(self, context):
        select_strips_in_channel(context, 17)
        return {'FINISHED'}

class SEQUENCER_OT_channel_18(Operator):
    bl_idname = "my.channel_18"
    bl_label = "Channel 18"
    bl_description = "Select all strips in channel 18"
    
    def execute(self, context):
        select_strips_in_channel(context, 18)
        return {'FINISHED'}

class SEQUENCER_OT_channel_19(Operator):
    bl_idname = "my.channel_19"
    bl_label = "Channel 19"
    bl_description = "Select all strips in channel 19"
    
    def execute(self, context):
        select_strips_in_channel(context, 19)
        return {'FINISHED'}

class SEQUENCER_OT_channel_20(Operator):
    bl_idname = "my.channel_20"
    bl_label = "Channel 20"
    bl_description = "Select all strips in channel 20"
    
    def execute(self, context):
        select_strips_in_channel(context, 20)
        return {'FINISHED'}

def select_strips_in_channel(context, channel):
    sequence_editor = context.scene.sequence_editor
    for strip in sequence_editor.sequences_all:
        strip.select = strip.channel == channel


hotkeys_popups.extend([
    SEQUENCER_OT_channel_1,
    SEQUENCER_OT_channel_2,
    SEQUENCER_OT_channel_3,
    SEQUENCER_OT_channel_4,
    SEQUENCER_OT_channel_5,
    SEQUENCER_OT_channel_6,
    SEQUENCER_OT_channel_7,
    SEQUENCER_OT_channel_8,
    SEQUENCER_OT_channel_9,
    SEQUENCER_OT_channel_10,
    SEQUENCER_OT_channel_11,
    SEQUENCER_OT_channel_12,
    SEQUENCER_OT_channel_13,
    SEQUENCER_OT_channel_14,
    SEQUENCER_OT_channel_15,
    SEQUENCER_OT_channel_16,
    SEQUENCER_OT_channel_17,
    SEQUENCER_OT_channel_18,
    SEQUENCER_OT_channel_19,
    SEQUENCER_OT_channel_20
])
    

####################
# Macro Operators
####################
def find_lowest_unused_macro(sequence_editor):
    selected_macro = 1
    
    for strip in sequence_editor.sequences_all:
        if hasattr(strip, 'start_frame_macro') and strip.start_frame_macro:
            if strip.start_frame_macro >= selected_macro:
                selected_macro += 1

    for strip in sequence_editor.sequences_all:
        if hasattr(strip, 'end_frame_macro') and strip.end_frame_macro:
            if strip.end_frame_macro >= selected_macro:
                selected_macro += 1
                
    return selected_macro

class SEQUENCER_OT_start_macro_search(Operator):
    bl_idname = "my.start_macro_search"
    bl_label = ""
    bl_description = "Use this to find the lowest unused macro number according to the sequencer. Caution: this does not yet poll the console to make sure it won't overwrite a macro that exists on the board itself"
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = sequence_editor.active_strip
        selected_macro = find_lowest_unused_macro(sequence_editor)
        active_strip.start_frame_macro = selected_macro
        return {'FINISHED'} 
    
class SEQUENCER_OT_end_macro_search(Operator):
    bl_idname = "my.end_macro_search"
    bl_label = ""
    bl_description = "Use this to find the lowest unused macro number according to the sequencer. Caution: this does not yet poll the console to make sure it won't overwrite a macro that exists on the board itself"
    
    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = sequence_editor.active_strip
        selected_macro = find_lowest_unused_macro(sequence_editor)
        active_strip.end_frame_macro = selected_macro
        return {'FINISHED'} 
    

class SEQUENCER_OT_fire_start_macro(Operator):
    bl_idname = "my.start_macro_fire"
    bl_label = ""
    bl_description = "Send a test command"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        OSC.send_osc_lighting("/eos/macro/fire", str(active_strip.start_frame_macro))
        return {'FINISHED'} 
    
    
class SEQUENCER_OT_fire_end_macro(Operator):
    bl_idname = "my.end_macro_fire"
    bl_label = ""
    bl_description = "Send a test command"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        OSC.send_osc_lighting("/eos/macro/fire", str(active_strip.end_frame_macro))
        return {'FINISHED'}
    

class SEQUENCER_OT_flash_copy_down(Operator):
    bl_idname = "my.flash_copy_down"
    bl_label = ""
    bl_description = "Paste this text down below"

    def execute(self, context):
        sequence_editor = context.scene.sequence_editor
        active_strip = sequence_editor.active_strip
        
        active_strip.flash_down_input = active_strip.flash_input
        return {'FINISHED'}


class SEQUENCER_OT_flash_macro_search(Operator):
    bl_idname = "my.flash_macro_search"
    bl_label = ""
    bl_description = "Find the lowest unused macro number in the sequencer"

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
    
    
macro_operators = [
    SEQUENCER_OT_start_macro_search,
    SEQUENCER_OT_end_macro_search,
    SEQUENCER_OT_fire_start_macro,
    SEQUENCER_OT_fire_end_macro,
    SEQUENCER_OT_flash_macro_search,
    SEQUENCER_OT_flash_copy_down
]


######################
# More operators
######################
class SEQUENCER_OT_analyze_song(Operator):
    bl_idname = "seq.analyze_song"
    bl_label = "Analyze Song (AI)"
    bl_description = "Use AI to automatically generate strips"
        
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
            result = Utils.analyze_song(self, filepath)
            
            scene = context.scene
            frame_rate = Utils.get_frame_rate(scene)
            start_frame = active_sequence.frame_start
            
            beats = [Utils.time_to_frame(beat, frame_rate, start_frame) for beat in result.beats]
            downbeats = [Utils.time_to_frame(downbeat, frame_rate, start_frame) for downbeat in result.downbeats]
            cues = [Utils.time_to_frame(segment.start, frame_rate, start_frame) for segment in result.segments]
            beat_positions = result.beat_positions  # Extract beat positions

            corrected_cues = remove_overlapping_cues(cues)

            for i, beat in enumerate(beats):
                color = color_codes[(beat_positions[i] % len(color_codes))-1]
                Utils.add_color_strip(name="Beat", length=4, channel=(active_strip.channel + 3), color=color, strip_type='option_eos_flash', frame=beat-2)
            for downbeat in downbeats:
                Utils.add_color_strip(name="Down Beat", length=12, channel=(active_strip.channel + 2), color=(1, 1, 0), strip_type='option_eos_flash', frame=downbeat-6)
            for cue in corrected_cues:
                Utils.add_color_strip(name="Cue", length=64, channel=(active_strip.channel + 1), color=(0, 0, 1), strip_type='option_eos_cue', frame=cue-32)
            
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "No active sound strip found")
            return {'CANCELLED'}
        
        
class SEQUENCER_OT_add_offset(Operator):
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


class SEQUENCER_OT_start_end_mapping(Operator):
    bl_idname = "my.start_end_frame_mapping"
    bl_label = "Set Range"
    bl_description = "Make sequencer's start and end frame match the selected clip's start and end frame"
        
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        context.scene.frame_start = int(active_strip.frame_start)
        context.scene.frame_end = int(active_strip.frame_final_duration + active_strip.frame_start)
        bpy.ops.sequencer.view_selected()
        return {'FINISHED'}
    

class SEQUENCER_OT_map_time(Operator):
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


class SEQUENCER_OT_generate_strips(Operator):
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


class SEQUENCER_OT_add_color_strip(Operator):
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
    

class SEQUENCER_OT_zero_clock(Operator):
    bl_idname = "my.clock_zero"
    bl_label = ""
    bl_description = "Set timecode clock to zero"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        event_list_number = str(active_strip.int_event_list)
        OSC.send_osc_lighting("/eos/newcmd", f"Event {event_list_number} / Internal Disable Time Enter")
        return {'FINISHED'}
    
    
class SEQUENCER_OT_delete_events(Operator):
    bl_idname = "my.clear_timecode_clock"
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


class SEQUENCER_OT_sync_video_to_audio(Operator):
    bl_idname = "my.sync_video"
    bl_label = "Sync Video to Audio Speed"
    bl_description = "Synchronizes start and end frame of a video and also remaps the timing if the frame rate of the sequencer does not match that of the video"
        
    def execute(self, context):
        selected_sound_strip = [strip for strip in context.scene.sequence_editor.sequences if strip.select and strip.type == 'SOUND']
        selected_video_strip = [strip for strip in context.scene.sequence_editor.sequences if strip.select and strip.type == 'MOVIE']
        
        video_strip = selected_video_strip[0]
        sound_strip = selected_sound_strip[0]
        
        channel = Utils.find_available_channel(context.scene.sequence_editor, video_strip.frame_start, video_strip.frame_final_end, video_strip.channel + 1)

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
        

class SEQUENCER_OT_sync_cue(Operator):
    bl_idname = "my.sync_cue"
    bl_label = ""
    bl_description = "Orb will set the cue duration on the board as the strip length of this strip. You must press this every time you change the length of the strip if you want it use the strip length to set cue time"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        
        frame_rate = Utils.get_frame_rate(context.scene)
        strip_length_in_seconds_total = int(round(active_strip.frame_final_duration / frame_rate))
        minutes = strip_length_in_seconds_total // 60
        seconds = strip_length_in_seconds_total % 60
        cue_duration = "{:02d}:{:02d}".format(minutes, seconds)
        cue_number = active_strip.eos_cue_number
        
        OSC.send_osc_lighting("/eos/key/live", "1")
        OSC.send_osc_lighting("/eos/newcmd", f"Cue {str(cue_number)} Time {cue_duration} Enter")
        active_strip.name = f"Cue {str(cue_number)}"
        self.report({'INFO'}, "Orb complete.")
        
        snapshot = str(context.scene.orb_finish_snapshot)
        OSC.send_osc_lighting("/eos/newcmd", f"Snapshot {snapshot} Enter")
        return {'FINISHED'}
    

class SEQUENCER_OT_command_line(Operator):
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
        
        
class TOOL_OT_duplicate_strip_to_above(Operator):
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

            ## This used to increase the animation channel number as well.

            else:
                self.report({'WARNING'}, "Please select exactly one strip.")
                return {'CANCELLED'}
        else:
            self.report({'WARNING'}, "Sequence editor is not active or available.")
            return {'CANCELLED'}

        return {'FINISHED'}
    
    
## This button needs to be completely redone.
class SEQUENCER_OT_generate_color_palette(Operator):
    bl_idname = "my.color_palette_operator"
    bl_label = ""
    bl_description = "Record color palette for all channels on console"
    
    def execute(self, context):
        return {'FINISHED'}


class SEQUENCER_OT_delete_qmeo_cues(Operator):
    bl_idname = "my.delete_animation_cue_list_operator"
    bl_label = ""
    bl_description = "Delete qmeo cues"
    
    def execute(self, context):
        scene = bpy.context.scene
        context = bpy.context
        active_strip = context.scene.sequence_editor.active_strip
        cue_list = active_strip.int_cue_list
        
        OSC.send_osc_lighting("/eos/key/live", "1")
        OSC.send_osc_lighting("/eos/key/live", "0")
        time.sleep(.2)
        
        # Must confirm on console.
        OSC.send_osc_lighting("/eos/newcmd", f"Delete Cue {str(cue_list)} / Enter")
        return {'FINISHED'}
        
        
class SEQUENCER_OT_delete_qmeo_events(Operator):
    bl_idname = "my.delete_animation_event_list_operator"
    bl_label = ""
    bl_description = "Delete qmeo events"
    
    def execute(self, context):
        scene = bpy.context.scene
        context = bpy.context
        active_strip = context.scene.sequence_editor.active_strip 
        event_list = active_strip.animation_event_list_number
        
        OSC.send_osc_lighting("/eos/key/live", "1")
        OSC.send_osc_lighting("/eos/key/live", "0")
        time.sleep(.2)
        
        # Must confirm on console.
        OSC.send_osc_lighting("/eos/newcmd", f"Delete Event {str(event_list)} / Enter")
        return {'FINISHED'}
    
    
class SEQUENCER_OT_stop_single_clock(Operator):
    bl_idname = "my.stop_animation_clock_operator"
    bl_label = ""
    bl_description = "Stop animation clock"
    
    def execute(self, context):
        scene = bpy.context.scene
        active_strip = context.scene.sequence_editor.active_strip
        cue_list = active_strip.int_cue_list
        
        OSC.send_osc_lighting("/eos/newcmd", f"Event {str(active_strip.animation_event_list_number)} / Internal Disable Enter")
        return {'FINISHED'}

 
class SEQUENCER_OT_generate_text(Operator):
    bl_idname = "my.generate_text"
    bl_label = "CIA > Import > USITT ASCII"
    bl_description = "Save event list into a .txt file for USITT ASCII import into Eos. Then, save as .esf3d console file. Then open up the main show file and merge the Show Control from the newly created .esf3d console file"
    
    def execute(self, context):
        scene = context.scene
        int_event_list = context.scene.sequence_editor.active_strip.int_event_list
        seq_start = context.scene.frame_start
        seq_end = context.scene.frame_end
        active_strip = context.scene.sequence_editor.active_strip
        frames_per_second = Utils.get_frame_rate(scene)
        
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

        text_block.write("$SCList " + str(active_strip.int_event_list) + " 2\n")
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
                    text_block.write("$Timecode  " + Utils.frame_to_timecode(start_frame) + "\n")
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
                    text_block.write("$Timecode  " + Utils.frame_to_timecode(start_frame) + "\n")
                    text_block.write("Text " + strip_name + " (Start Macro)" + "\n")
                    text_block.write("$$SCData M " + str(start_macro_number) + "\n")  
                    text_block.write("\n")
                    text_block.write("\n")
                if end_macro_number != 0 and not strip.end_macro_muted:         
                    text_block.write("$Timecode  " + Utils.frame_to_timecode(end_frame) + "\n")
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
                frame_rate = Utils.get_frame_rate(scene)
                strip_length_in_frames = strip.frame_final_duration
                bias_in_frames = Utils.calculate_bias_offseter(bias, frame_rate, strip_length_in_frames)
                start_frame = strip.frame_start - slide_factor
                end_flash_macro_frame = start_frame + bias_in_frames
                end_flash_macro_frame = int(round(end_flash_macro_frame))
                end_frame = end_flash_macro_frame

                # If only the start flash macro is provided
                if start_flash_macro_number != 0:         
                    text_block.write("$Timecode  " + Utils.frame_to_timecode(start_frame) + "\n")
                    text_block.write("Text " + strip_name + " (Flash Up)" + "\n")
                    text_block.write("$$SCData M " + str(start_flash_macro_number) + "\n")  
                    text_block.write("\n")
                    text_block.write("\n")
                if end_flash_macro_number != 0:         
                    text_block.write("$Timecode  " + Utils.frame_to_timecode(end_frame) + "\n")
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
    
    
misc_operators = [
    SEQUENCER_OT_analyze_song,
    SEQUENCER_OT_add_offset,
    SEQUENCER_OT_start_end_mapping,
    SEQUENCER_OT_map_time,
    SEQUENCER_OT_generate_strips,
    SEQUENCER_OT_add_color_strip,
    SEQUENCER_OT_zero_clock,
    SEQUENCER_OT_delete_events,
    SEQUENCER_OT_delete_qmeo_cues,
    SEQUENCER_OT_sync_video_to_audio,
    SEQUENCER_OT_sync_cue,
    SEQUENCER_OT_command_line,
    TOOL_OT_duplicate_strip_to_above,
    SEQUENCER_OT_generate_color_palette,
    SEQUENCER_OT_delete_qmeo_events,
    SEQUENCER_OT_stop_single_clock,
    SEQUENCER_OT_generate_text
]


#################
# Orb Operators
#################
class SEQUENCER_OT_base_modal_operator(Operator):
    bl_idname = "my.base_modal_operator"
    bl_label = ""
    bl_description = "Base class for modal operators"

    cancel_key = 'ESC'

    def execute(self, context):
        self._cancel = False
        if self.strip != 'qmeo':
            self._generator = self.generate_macros_to_cues(context, strip=self.strip, enable=self.enable)
        else:
            frame_rate = Utils.get_frame_rate(context.scene)
            if hasattr(context.scene.sequence_editor, "active_strip") and context.scene.sequence_editor.active_strip is not None:
                active_strip = context.scene.sequence_editor.active_strip
                start_frame = active_strip.frame_start
                end_frame = active_strip.frame_final_end
                cue_list = active_strip.int_cue_list
            else:
                start_frame = context.scene.frame_start
                end_frame = context.scene.frame_end
                cue_list = context.scene.int_cue_list
            
            self._generator = self.make_qmeo(context.scene, frame_rate, start_frame, end_frame, cue_list)

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == self.cancel_key and event.value == 'PRESS':
            self._cancel = True
            self.cancel(context)
            self.report({'INFO'}, "Operation cancelled")
            return {'CANCELLED'}

        if event.type == 'TIMER':
            try:
                func, msg = next(self._generator)
                if func:
                    func()
                if msg:
                    self.report({'INFO'}, msg)
            except StopIteration:
                self.report({'INFO'}, "Operation completed")
                self.cancel(context)
                return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def generate_macros_to_cues(self, context, strip='sound', enable=True):
        yield from Orb.generate_macros_to_cues(self, context, strip=strip, enable=enable)

    def make_qmeo(self, scene, frame_rate, start_frame, end_frame, cue_list):
        yield from Orb.Eos.make_qmeo(scene, frame_rate, start_frame, end_frame, cue_list)

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        OSC.send_osc_lighting("/eos/key/escape", "1")
        OSC.send_osc_lighting("/eos/key/escape", "0")
        OSC.send_osc_lighting("/eos/newcmd", "")
        Orb.Eos.reset_macro_key()
        Orb.Eos.restore_snapshot(context.scene)
        

class SEQUENCER_OT_execute_sound_on_cue(SEQUENCER_OT_base_modal_operator):
    bl_idname = "my.execute_on_cue_operator"
    bl_label = ""
    bl_description = "Orb executes sound on cue"

    def execute(self, context):
        self.strip = 'sound'
        self.enable = True
        return super().execute(context)


class SEQUENCER_OT_disable_sound_on_cue(SEQUENCER_OT_base_modal_operator):
    bl_idname = "my.disable_on_cue_operator"
    bl_label = ""
    bl_description = "Orb disables sound on cue"

    def execute(self, context):
        self.strip = 'sound'
        self.enable = False
        return super().execute(context)


class SEQUENCER_OT_execute_animation_on_cue(SEQUENCER_OT_base_modal_operator):
    bl_idname = "my.execute_animation_on_cue_operator"
    bl_label = ""
    bl_description = "Orb executes animation on cue"

    def execute(self, context):
        self.strip = 'animation'
        self.enable = True
        return super().execute(context)


class SEQUENCER_OT_disable_animation_on_cue(SEQUENCER_OT_base_modal_operator):
    bl_idname = "my.disable_animation_on_cue_operator"
    bl_label = ""
    bl_description = "Orb disables animation on cue"

    def execute(self, context):
        self.strip = 'animation'
        self.enable = False
        return super().execute(context)


class SEQUENCER_OT_generate_start_frame_macro(SEQUENCER_OT_base_modal_operator):
    bl_idname = "my.generate_start_frame_macro"
    bl_label = ""
    bl_description = "Orb generates start frame macro"

    def execute(self, context):
        self.strip = 'macro'
        self.enable = True
        return super().execute(context)


class SEQUENCER_OT_generate_end_frame_macro(SEQUENCER_OT_base_modal_operator):
    bl_idname = "my.generate_end_frame_macro"
    bl_label = ""
    bl_description = "Orb generates end frame macro"

    def execute(self, context):
        self.strip = 'macro'
        self.enable = False
        return super().execute(context)


class SEQUENCER_OT_build_flash_macros(SEQUENCER_OT_base_modal_operator):
    bl_idname = "my.build_flash_macros"
    bl_label = ""
    bl_description = "Orb builds flash macros"

    def execute(self, context):
        self.strip = 'flash'
        self.enable = True
        return super().execute(context)
    
    
class SEQUENCER_OT_generate_offset_macro(SEQUENCER_OT_base_modal_operator):
    bl_idname = "my.generate_offset_macro"
    bl_label = ""
    bl_description = "Orb generates offset macro"

    def execute(self, context):
        self.strip = 'offset'
        self.enable=True
        return super().execute(context)
    
    
class SEQUENCER_OT_bake_curves_to_cues(SEQUENCER_OT_base_modal_operator):
    bl_idname = "my.bake_fcurves_to_cues_operator"
    bl_label = "Bake F-curves To Cues"
    bl_description = "Orb will create a qmeo. A qmeo is like a video, only each frame is a lighting cue. Use it to store complex animation data on the lighting console" 

    def execute(self, context):
        self.strip = 'qmeo'
        self.enable=True
        return super().execute(context)
 
 
class SEQUENCER_OT_only_cues(Operator):
    bl_idname = "my.rerecord_cues_operator"
    bl_label = "Re-record Cues"
    bl_description = "Orb will re-record the cues. Use this instead of the left button if you already used that button, updated the animation without changing its length, and just want to re-record the existing cues. This is far shorter" 
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        frame_rate = Utils.get_frame_rate(context.scene)
        start_frame = active_strip.frame_start
        end_frame = active_strip.frame_final_end
        cue_list = active_strip.int_cue_list
        
        Orb.Eos.make_qmeo(context.scene, frame_rate, start_frame, end_frame, cue_list, None)
        return {'FINISHED'}
    
    
class TEXT_OT_generate_text_macro(SEQUENCER_OT_base_modal_operator):
    bl_idname = "text.generate_text_macro"
    bl_label = ""
    bl_description = "Orb generates macro from text block"

    def execute(self, context):
        self.strip = 'text'
        self.enable = True
        return super().execute(context)
    
    
orb_operators = [
    SEQUENCER_OT_base_modal_operator,
    SEQUENCER_OT_execute_sound_on_cue,
    SEQUENCER_OT_disable_sound_on_cue,
    SEQUENCER_OT_execute_animation_on_cue,
    SEQUENCER_OT_disable_animation_on_cue,
    SEQUENCER_OT_generate_start_frame_macro,
    SEQUENCER_OT_generate_end_frame_macro,
    SEQUENCER_OT_build_flash_macros,
    SEQUENCER_OT_generate_offset_macro,
    SEQUENCER_OT_bake_curves_to_cues,
    SEQUENCER_OT_only_cues,
    TEXT_OT_generate_text_macro
]
   

######################
# Add Strip Operators
######################
class SEQUENCER_OT_add_macro(Operator):
    bl_idname = "my.add_macro"
    bl_label = "Macro"
    bl_description = "Add macro strip. Type in macro syntax you know letter by letter and type * for strip length"
    
    def execute(self, context):
        return create_motif_strip(context, "option_eos_macro")
        
class SEQUENCER_OT_add_cue(Operator):
    bl_idname = "my.add_cue"
    bl_label = "Cue"
    bl_description = "Add cue strip. Strip length will become the cues fade in time"
    
    def execute(self, context):
        return create_motif_strip(context, "option_eos_cue")
        
class SEQUENCER_OT_add_flash(Operator):
    bl_idname = "my.add_flash"
    bl_label = "Flash"
    bl_description = "Add flash strip. Flash strips are really fast for making lights flash up then down with no effort"
    
    def execute(self, context):
        return create_motif_strip(context, "option_eos_flash")
        
class SEQUENCER_OT_add_animation(Operator):
    bl_idname = "my.add_animation"
    bl_label = "Animation"
    bl_description = "Add animation strip. Use Blender's sophisticated animation tools such as Graph Editor, Dope Sheet, Motion Tracking, and NLA Editor to create effects that are impossible to create anywhere else. Then, output a qmeo deliverable to the console for local playback"
    
    def execute(self, context):
        return create_motif_strip(context, "option_animation")

class SEQUENCER_OT_add_offset_strip(Operator):
    bl_idname = "my.add_offset_strip"
    bl_label = "Offset"
    bl_description = "Add offset strip. Use this to rapidly create wipes, chases, choreography, and other offsetted effects"
    
    def execute(self, context):
        return create_motif_strip(context, "option_offset")
        
class SEQUENCER_OT_add_trigger(Operator):
    bl_idname = "my.add_trigger"
    bl_label = "Trigger"
    bl_description = "Add trigger strip. Use this to send arbitrary OSC strings on start and end frame with fully custom address/argument. Or, experiment with creating advanced offset effects with plain english"
    
    def execute(self, context):
        return create_motif_strip(context, "option_trigger")
    
def create_motif_strip(context, motif_type_enum):
    current_frame = context.scene.frame_current
    sequence_editor = context.scene.sequence_editor
    channel = sequence_editor.active_strip.channel if sequence_editor.active_strip else 1
    frame_end = current_frame + 25

    my_channel = Utils.find_available_channel(sequence_editor, current_frame, frame_end, channel)
    print(f"Channel is {my_channel}")

    color_strip = sequence_editor.sequences.new_effect(
        name="New Strip",
        type='COLOR',
        channel=my_channel,
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


add_strip_operators = [
    SEQUENCER_OT_add_macro,
    SEQUENCER_OT_add_cue,
    SEQUENCER_OT_add_flash,
    SEQUENCER_OT_add_animation,
    SEQUENCER_OT_add_offset_strip,
    SEQUENCER_OT_add_trigger
]
    

#####################
# 3D Audio Operators 
#####################   
class SEQUENCER_OT_bake_audio(Operator):
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
    
class SEQUENCER_OT_solo_track(Operator):
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
    
class SEQUENCER_OT_export_audio(Operator):
    bl_idname = "seq.export_audio_operator"
    bl_label = "Export Channel"
    bl_description = "Export an audio file for this speaker channel to Qlab"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        bpy.ops.sound.mixdown('INVOKE_DEFAULT')
        return {'FINISHED'}
    
class SEQUENCER_OT_render_all_objects(Operator):
    bl_idname = "seq.render_all_audio_objects_operator"
    bl_label = "Render all Audio Objects to Files"
    bl_description = "Export audio files for all audio objects for Qlab"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        return {'FINISHED'}
    
class COMMON_OT_save_dtp(Operator):
    bl_idname = "main.save_dtp_operator"
    bl_label = "Save as .dtp"
    bl_description = "Save a Digital Theatre Package (.dtp) to upload to the core"
    
    def execute(self, context):
        return {'FINISHED'}
    
    
three_dee_audio_operators = [
    SEQUENCER_OT_bake_audio,
    SEQUENCER_OT_solo_track,
    SEQUENCER_OT_export_audio,
    SEQUENCER_OT_render_all_objects,
    COMMON_OT_save_dtp
]


def register():
    for cls in hotkeys_popups:
        bpy.utils.register_class(cls)
    for cls in macro_operators:
        bpy.utils.register_class(cls)
    for cls in misc_operators:
        bpy.utils.register_class(cls)
    for cls in orb_operators:
        bpy.utils.register_class(cls)
    for cls in add_strip_operators:
        bpy.utils.register_class(cls)
    for cls in three_dee_audio_operators:
        bpy.utils.register_class(cls)
    
def unregister():
    for cls in reversed(hotkeys_popups):
        bpy.utils.unregister_class(cls)
    for cls in reversed(macro_operators):
        bpy.utils.unregister_class(cls)
    for cls in reversed(misc_operators):
        bpy.utils.unregister_class(cls)
    for cls in reversed(orb_operators):
        bpy.utils.unregister_class(cls)
    for cls in reversed(add_strip_operators):
        bpy.utils.unregister_class(cls)
    for cls in reversed(three_dee_audio_operators):
        bpy.utils.unregister_class(cls)