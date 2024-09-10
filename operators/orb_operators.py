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

## Double hashtag indicates notes for future development requiring some level of attention

import bpy
from bpy.types import Operator

from ..utils.utils import Utils # type: ignore
from ..utils.osc import OSC
from ..orb import Orb


class ORB_OT_base_modal_operator(Operator):
    bl_idname = "alva_orb.modal_base"
    bl_label = ""
    bl_description = "Base class for Orb modals"

    cancel_key = 'ESC'

    def execute(self, context):
        self._cancel = False
        if self.strip == 'qmeo':
            frame_rate = Utils.get_frame_rate(context.scene)
            scene = context.scene
            if hasattr(scene.sequence_editor, "active_strip") and scene.sequence_editor.active_strip is not None and scene.sequence_editor.active_strip.type == 'SOUND':
                active_strip = context.scene.sequence_editor.active_strip
                start_frame = active_strip.frame_start
                end_frame = active_strip.frame_final_end
            else:
                start_frame = context.scene.frame_start
                end_frame = context.scene.frame_end
            
            self._generator = self.make_qmeo(context.scene, frame_rate, start_frame, end_frame)
        
        elif self.strip == 'patch':
            self._generator = self.patch_group(context)
        
        else:
            self._generator = self.initiate_orb(context, strip=self.strip, enable=self.enable)

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
                    try:
                        func()
                    except Exception as e:
                        print(f"An unknown error occured with Orb: {e}")
                if msg:
                    self.report({'INFO'}, msg)
            except StopIteration:
                self.report({'INFO'}, "Operation completed")
                self.cancel(context)
                return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def initiate_orb(self, context, strip='sound', enable=True):
        yield from Orb.initiate_orb(self, context, strip=strip, enable=enable)

    def make_qmeo(self, scene, frame_rate, start_frame, end_frame):
        yield from Orb.Eos.make_qmeo(scene, frame_rate, start_frame, end_frame)

    def patch_group(self, context):
        yield from Orb.Eos.patch_group(self, context)

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        OSC.send_osc_lighting("/eos/key/escape", "1")
        OSC.send_osc_lighting("/eos/key/escape", "0")
        OSC.send_osc_lighting("/eos/newcmd", "")
        Orb.Eos.reset_macro_key()
        Orb.Eos.restore_snapshot(context.scene)


class VIEW3D_OT_alva_group_patch(ORB_OT_base_modal_operator):
    bl_idname = "alva_orb.group_patch"
    bl_label = "Patch Group"
    bl_description = "Patch group on console"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        self.strip = 'patch'
        self.enable = True
        return super().execute(context)
        

class SEQUENCER_OT_execute_sound_on_cue(ORB_OT_base_modal_operator):
    bl_idname = "my.execute_on_cue_operator"
    bl_label = ""
    bl_description = "Orb executes sound on cue"

    def execute(self, context):
        self.strip = 'sound'
        self.enable = True
        return super().execute(context)


class SEQUENCER_OT_disable_sound_on_cue(ORB_OT_base_modal_operator):
    bl_idname = "my.disable_on_cue_operator"
    bl_label = ""
    bl_description = "Orb disables sound on cue"

    def execute(self, context):
        self.strip = 'sound'
        self.enable = False
        return super().execute(context)


class SEQUENCER_OT_execute_animation_on_cue(ORB_OT_base_modal_operator):
    bl_idname = "my.execute_animation_on_cue_operator"
    bl_label = ""
    bl_description = "Orb executes animation on cue"

    def execute(self, context):
        self.strip = 'animation'
        self.enable = True
        return super().execute(context)


class SEQUENCER_OT_disable_animation_on_cue(ORB_OT_base_modal_operator):
    bl_idname = "my.disable_animation_on_cue_operator"
    bl_label = ""
    bl_description = "Orb disables animation on cue"

    def execute(self, context):
        self.strip = 'animation'
        self.enable = False
        return super().execute(context)


class SEQUENCER_OT_generate_start_frame_macro(ORB_OT_base_modal_operator):
    bl_idname = "my.generate_start_frame_macro"
    bl_label = ""
    bl_description = "Orb generates start frame macro"

    def execute(self, context):
        self.strip = 'macro'
        self.enable = True
        return super().execute(context)


class SEQUENCER_OT_generate_end_frame_macro(ORB_OT_base_modal_operator):
    bl_idname = "my.generate_end_frame_macro"
    bl_label = ""
    bl_description = "Orb generates end frame macro"

    def execute(self, context):
        self.strip = 'macro'
        self.enable = False
        return super().execute(context)


class SEQUENCER_OT_build_flash_macros(ORB_OT_base_modal_operator):
    bl_idname = "my.build_flash_macros"
    bl_label = ""
    bl_description = "Orb builds flash macros"

    def execute(self, context):
        self.strip = 'flash'
        self.enable = True
        return super().execute(context)
    
    
class SEQUENCER_OT_generate_offset_macro(ORB_OT_base_modal_operator):
    bl_idname = "my.generate_offset_macro"
    bl_label = ""
    bl_description = "Orb generates offset macro"

    def execute(self, context):
        self.strip = 'offset'
        self.enable=True
        return super().execute(context)
    
    
class SEQUENCER_OT_bake_curves_to_cues(ORB_OT_base_modal_operator):
    bl_idname = "alva_orb.render_qmeo"
    bl_label = "Make Qmeo"
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
    
    
class TEXT_OT_generate_text_macro(ORB_OT_base_modal_operator):
    bl_idname = "text.generate_text_macro"
    bl_label = ""
    bl_description = "Orb generates macro from text block"

    def execute(self, context):
        self.strip = 'text'
        self.enable = True
        return super().execute(context)
    
    
orb_operators = [
    VIEW3D_OT_alva_group_patch,
    ORB_OT_base_modal_operator,
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

def register():
    for cls in orb_operators:
        bpy.utils.register_class(cls)
    
def unregister():
    for cls in reversed(orb_operators):
        bpy.utils.unregister_class(cls)