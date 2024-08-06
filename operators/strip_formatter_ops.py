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
from functools import partial
from bpy.types import Operator
from bpy.utils import register_class, unregister_class


filter_color_strips = partial(filter, bpy.types.ColorSequence.__instancecheck__)


# Select by attribute.
class SEQUENCER_OT_select_by_color(Operator):
    bl_idname = "my.color_trigger"
    bl_label = "Color Trigger"
    
    def execute(self, context):
        select_strips_by_attribute(context, 'color')
        return {'FINISHED'}

class SEQUENCER_OT_select_by_name(Operator):
    bl_idname = "my.strip_name_trigger"
    bl_label = "Strip Name Trigger"
    
    def execute(self, context):
        select_strips_by_attribute(context, 'name')
        return {'FINISHED'}

class SEQUENCER_OT_select_by_channel(Operator):
    bl_idname = "my.channel_trigger"
    bl_label = "Channel Trigger"
    
    def execute(self, context):
        select_strips_by_attribute(context, 'channel')
        return {'FINISHED'}

class SEQUENCER_OT_select_by_start_frame(Operator):
    bl_idname = "my.start_frame_trigger"
    bl_label = "Start Frame Trigger"
    
    def execute(self, context):
        select_strips_by_attribute(context, 'frame_start')
        return {'FINISHED'}

class SEQUENCER_OT_select_by_end_frame(Operator):
    bl_idname = "my.end_frame_trigger"
    bl_label = "End Frame Trigger"
    
    def execute(self, context):
        select_strips_by_attribute(context, 'frame_final_end')
        return {'FINISHED'}

class SEQUENCER_OT_select_by_duration(Operator):
    bl_idname = "my.duration_trigger"
    bl_label = "Duration Trigger"
    
    def execute(self, context):
        select_strips_by_attribute(context, 'frame_final_duration')
        return {'FINISHED'}
    
def select_strips_by_attribute(context, attribute):
    active_strip = context.scene.sequence_editor.active_strip
    sequence_editor = context.scene.sequence_editor
    scene = context.scene
    value = getattr(active_strip, attribute)

    for strip in filter_color_strips(sequence_editor.sequences_all):
        if getattr(strip, attribute) == value:
            strip.select = True
        else:
            if scene.is_filtering_right:
                strip.select = False

# Hotkey hints.    
class SEQUENCER_OT_start_frame_jump(Operator):
    bl_idname = "my.start_frame_jump"
    bl_label = "Jump to Start Frame"
    
    def execute(self, context):
        bpy.context.scene.frame_current = int(bpy.context.scene.sequence_editor.active_strip.frame_start)
        return {'FINISHED'}
    
class SEQUENCER_OT_end_frame_jump(Operator):
    bl_idname = "my.end_frame_jump"
    bl_label = "Jump to End Frame"
    
    def execute(self, context):
        bpy.context.scene.frame_current = int(bpy.context.scene.sequence_editor.active_strip.frame_final_end)
        return {'FINISHED'}

class SEQUENCER_OT_hint_extrude(Operator):
    bl_idname = "my.alva_extrude"
    bl_label = "Extrude Pattern of 2"
    
    def execute(self, context):
        self.report({'INFO'}, 'Type the "E" key while in sequencer to extrude pattern of 2 strips.')
        return {'FINISHED'}

class SEQUENCER_OT_hint_scale(Operator):
    bl_idname = "my.alva_scale"
    bl_label = "Scale Strip(s)"
    
    def execute(self, context):
        self.report({'INFO'}, 'Type the "S" key while in sequencer to scale strips.')
        return {'FINISHED'}
        
class SEQUENCER_OT_hint_grab(Operator):
    bl_idname = "my.alva_grab"
    bl_label = "Grab Strip(s)"
    
    def execute(self, context):
        self.report({'INFO'}, 'Type the "G" key while in sequencer to grab and move strips.')
        return {'FINISHED'}
    
class SEQUENCER_OT_hint_grab_x(Operator):
    bl_idname = "my.alva_grab_x"
    bl_label = "Grab Strip(s) on X"
    
    def execute(self, context):
        self.report({'INFO'}, 'Type the "G" key, then the "X" key while in sequencer to grab and move strips on X axis only.')
        return {'FINISHED'}
        
class SEQUENCER_OT_hint_grab_y(Operator):
    bl_idname = "my.alva_grab_y"
    bl_label = "Grab Strip(s) on Y"
    
    def execute(self, context):
        self.report({'INFO'}, 'Type the "G" key, then the "Y" key while in sequencer to grab and move strips on Y axis only.')
        return {'FINISHED'}
        
class SEQUENCER_OT_hint_cut(Operator):
    bl_idname = "my.cut_operator"
    bl_label = "Cut Strips"
    
    def execute(self, context):
        self.report({'INFO'}, 'Type the "K" key while in sequencer.')
        return {'FINISHED'}

class SEQUENCER_OT_hint_add_media(Operator):
    bl_idname = "my.add_media_operator"
    bl_label = "Add Media"
    
    def execute(self, context):
        self.report({'INFO'}, 'Right-click twice inside the sequencer to add strips such as sound and video.')
        return {'FINISHED'}
        
class SEQUENCER_OT_hint_assign_to_channel(Operator):
    bl_idname = "my.assign_to_channel_operator"
    bl_label = "Assign to Channel"
    
    def execute(self, context):
        self.report({'INFO'}, 'Type the "C" key while in sequencer, then channel number, then "Enter" key.')
        return {'FINISHED'}    
    
class SEQUENCER_OT_hint_set_start_frame(Operator):
    bl_idname = "my.set_start_frame_operator"
    bl_label = "Set Start Frame"
    
    def execute(self, context):
        self.report({'INFO'}, 'Type the "S" key while in Timeline window.')
        return {'FINISHED'}
        
class SEQUENCER_OT_hint_set_end_frame(Operator):
    bl_idname = "my.set_end_frame_operator"
    bl_label = "Set End Frame"
    
    def execute(self, context):
        self.report({'INFO'}, 'Type the "E" key while in Timeline window.')
        return {'FINISHED'}
    
  
# Copy attribute to selected.  
class SEQUENCER_OT_copy_color(Operator):
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

class SEQUENCER_OT_copy_name(Operator):
    bl_idname = "my.copy_strip_name_operator"
    bl_label = "Copy strip name to Selected"
    bl_description = "Copy strip name to selected strips"

    def execute(self, context):
        copy_attribute_to_selected(context, 'name')
        return {'FINISHED'}

class SEQUENCER_OT_copy_channel(Operator):
    bl_idname = "my.copy_channel_operator"
    bl_label = "Copy channel to Selected"
    bl_description = "Copy channel to selected strips"

    def execute(self, context):
        copy_attribute_to_selected(context, 'channel')
        return {'FINISHED'}

class SEQUENCER_OT_copy_duration(Operator):
    bl_idname = "my.copy_duration_operator"
    bl_label = "Copy duration to Selected"
    bl_description = "Copy duration to selected strips"

    def execute(self, context):
        copy_attribute_to_selected(context, 'frame_final_duration')
        return {'FINISHED'}

class SEQUENCER_OT_copy_start_frame(Operator):
    bl_idname = "my.copy_start_frame_operator"
    bl_label = "Copy start frame to Selected"
    bl_description = "Copy start frame to selected strips"

    def execute(self, context):
        copy_attribute_to_selected(context, 'frame_start')
        return {'FINISHED'}

class SEQUENCER_OT_copy_end_frame(Operator):
    bl_idname = "my.copy_end_frame_operator"
    bl_label = "Copy end frame to Selected"
    bl_description = "Copy end frame to selected strips"

    def execute(self, context):
        copy_attribute_to_selected(context, 'frame_final_end')
        return {'FINISHED'}
    
def copy_attribute_to_selected(context, attribute):
    active_strip = context.scene.sequence_editor.active_strip
    if active_strip and active_strip.type == 'COLOR':
        value = getattr(active_strip, attribute)
        for strip in filter_color_strips(context.selected_sequences):
            if strip != active_strip:
                setattr(strip, attribute, value)
     

formatter_operators = [
    SEQUENCER_OT_select_by_color,
    SEQUENCER_OT_select_by_name,
    SEQUENCER_OT_select_by_channel,
    SEQUENCER_OT_select_by_start_frame,
    SEQUENCER_OT_select_by_end_frame,
    SEQUENCER_OT_select_by_duration,
    SEQUENCER_OT_start_frame_jump,
    SEQUENCER_OT_end_frame_jump,
    SEQUENCER_OT_hint_extrude,
    SEQUENCER_OT_hint_scale,
    SEQUENCER_OT_hint_grab,
    SEQUENCER_OT_hint_grab_x,
    SEQUENCER_OT_hint_grab_y,
    SEQUENCER_OT_hint_cut,
    SEQUENCER_OT_hint_add_media,
    SEQUENCER_OT_hint_assign_to_channel,
    SEQUENCER_OT_hint_set_start_frame,
    SEQUENCER_OT_hint_set_end_frame,
    SEQUENCER_OT_copy_color,
    SEQUENCER_OT_copy_name,
    SEQUENCER_OT_copy_channel,
    SEQUENCER_OT_copy_duration,
    SEQUENCER_OT_copy_start_frame,
    SEQUENCER_OT_copy_end_frame,
]


def register():
    for cls in formatter_operators:
        register_class(cls)
    
    
def unregister():
    for cls in reversed(formatter_operators):
        unregister_class(cls)