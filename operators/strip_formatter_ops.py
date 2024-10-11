# This file is part of Alva Sorcerer
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


import bpy
from functools import partial
from bpy.types import Operator
from bpy.props import StringProperty, IntProperty
from bpy.utils import register_class, unregister_class


filter_color_strips = partial(filter, bpy.types.ColorSequence.__instancecheck__)


class SEQUENCER_OT_alva_formatter_select(Operator):
    bl_idname = "alva_seq.formatter_select"
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
    bl_idname = "alva_seq.frame_jump"
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
    bl_idname = "alva_seq.hotkey_hint"
    bl_label = "Hotkey Hint"

    message: StringProperty() # type: ignore
    
    def execute(self, context):
        self.report({'INFO'}, self.message)
        return {'FINISHED'}
    
  
class SEQUENCER_OT_alva_copy_strip_attribute(Operator):
    '''Copy this attribute of active strip to selected strips'''
    bl_idname = "alva_seq.copy_attribute"
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
     

formatter_operators = [
    SEQUENCER_OT_alva_formatter_select,
    SEQUENCER_OT_alva_frame_jump,
    SEQUENCER_OT_alva_hotkey_hint,
    SEQUENCER_OT_alva_copy_strip_attribute,
]


def register():
    for cls in formatter_operators:
        register_class(cls)
    
    
def unregister():
    for cls in reversed(formatter_operators):
        unregister_class(cls)