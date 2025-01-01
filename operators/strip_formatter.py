# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from functools import partial
from bpy.types import Operator
from bpy.props import StringProperty, IntProperty
from bpy.utils import register_class, unregister_class

from ..utils.sequencer_utils import find_available_channel

filter_color_strips = partial(filter, bpy.types.ColorSequence.__instancecheck__)


class SEQUENCER_OT_alva_select_similar(Operator):
    bl_idname = "alva_sequencer.select_similar"
    bl_label = "Select Similar"
    bl_description = "This selects all strips with the same length and color as the active strip"

    @classmethod
    def poll(cls, context):
            return context.scene.sequence_editor and context.scene.sequence_editor.active_strip

    def execute(self, context):
        sequencer = context.scene.sequence_editor
        active_strip = sequencer.active_strip
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
                                                
        elif scene.is_filtering_left:
                            
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


class SEQUENCER_OT_alva_formatter_select(Operator):
    bl_idname = "alva_sequencer.formatter_select"
    bl_label = "Rapid Select"

    target: StringProperty() # type: ignore

    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        sequence_editor = context.scene.sequence_editor
        scene = context.scene
        value = getattr(active_strip, self.target)

        for strip in filter_color_strips(sequence_editor.sequences_all):
            if getattr(strip, self.target) == value:
                strip.select = True
            else:
                if scene.is_filtering_right:
                    strip.select = False

        return {'FINISHED'}


class SEQUENCER_OT_alva_frame_jump(Operator):
    bl_idname = "alva_sequencer.frame_jump"
    bl_label = "Jump to Start Frame"

    direction: IntProperty() # type: ignore
    
    def execute(self, context):
        if self.direction == 1:
            frame_target = bpy.context.scene.sequence_editor.active_strip.frame_start
        else:
            frame_target = bpy.context.scene.sequence_editor.active_strip.frame_final_end
        bpy.context.scene.frame_current = int(frame_target)
        return {'FINISHED'}


class SEQUENCER_OT_alva_hotkey_hint(Operator):
    '''Press for hotkey hint'''
    bl_idname = "alva_sequencer.hotkey_hint"
    bl_label = "Hotkey Hint"

    message: StringProperty() # type: ignore
    
    def execute(self, context):
        self.report({'INFO'}, self.message)
        return {'FINISHED'}
    
  
class SEQUENCER_OT_alva_copy_strip_attribute(Operator):
    '''Copy this attribute of active strip to selected strips'''
    bl_idname = "alva_sequencer.copy_attribute"
    bl_label = "Copy Attribute"

    target: StringProperty() # type: ignore

    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip

        if not active_strip and active_strip.type == 'COLOR':
            return {'CANCELLED'}
        
        value = getattr(active_strip, self.target)
        if self.target == 'color':
            global stop_updating_color
            stop_updating_color = "Yes"

            for strip in filter_color_strips(context.selected_sequences):
                if strip != active_strip:
                    strip.color = value
                        
            stop_updating_color = "No"

        else:
            for strip in filter_color_strips(context.selected_sequences):
                if strip != active_strip:
                    setattr(strip, self.target, value)

        return {'FINISHED'}  


class SEQUENCER_OT_alva_set_timecode(Operator):
    bl_idname = "alva_sequencer.set_timecode"
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
    

class SEQUENCER_OT_alva_start_end_mapping(Operator):
    bl_idname = "alva_sequencer.start_end_frame_mapping"
    bl_label = "Set Range"
    bl_description = "Make sequencer's start and end frame match the selected clip's start and end frame"
        
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        context.scene.frame_start = int(active_strip.frame_start)
        context.scene.frame_end = int(active_strip.frame_final_duration + active_strip.frame_start)
        bpy.ops.sequencer.view_selected()
        return {'FINISHED'}
    

class SEQUENCER_OT_alva_sync_video_to_audio(Operator):
    bl_idname = "alva_sequencer.sync_video"
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
     

formatter_operators = [
    SEQUENCER_OT_alva_select_similar,
    SEQUENCER_OT_alva_formatter_select,
    SEQUENCER_OT_alva_frame_jump,
    SEQUENCER_OT_alva_hotkey_hint,
    SEQUENCER_OT_alva_copy_strip_attribute,
    SEQUENCER_OT_alva_set_timecode,
    SEQUENCER_OT_alva_start_end_mapping,
    SEQUENCER_OT_alva_sync_video_to_audio
]


def register():
    for cls in formatter_operators:
        register_class(cls)
    
    
def unregister():
    for cls in reversed(formatter_operators):
        unregister_class(cls)