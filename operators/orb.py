# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Operator
from bpy.props import BoolProperty

from ..utils.event_utils import EventUtils
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
            frame_rate = EventUtils.get_frame_rate(context.scene)
            if self.is_sound:
                active_strip = context.scene.sequence_editor.active_strip
                start_frame = active_strip.frame_start
                end_frame = active_strip.frame_final_end
            else:
                start_frame = context.scene.frame_start
                end_frame = context.scene.frame_end
            
            self._generator = self.make_qmeo(context.scene, frame_rate, start_frame, end_frame, self.is_sound)
        
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

    def make_qmeo(self, scene, frame_rate, start_frame, end_frame, is_sound):
        yield from Orb.Eos.make_qmeo(scene, frame_rate, start_frame, end_frame, is_sound)

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


class ORB_OT_alva_group_patch(ORB_OT_base_modal_operator):
    bl_idname = "alva_orb.group_patch"
    bl_label = "Patch Group"
    bl_description = "Patch group on console"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        self.strip = 'patch'
        self.enable = True
        return super().execute(context)
        

class ORB_OT_alva_execute_sound_on_cue(ORB_OT_base_modal_operator):
    bl_idname = "alva_orb.execute_on_cue"
    bl_label = ""
    bl_description = "Orb executes sound on cue"

    def execute(self, context):
        self.strip = 'sound'
        self.enable = True
        return super().execute(context)


class ORB_OT_alva_generate_start_frame_macro(ORB_OT_base_modal_operator):
    bl_idname = "alva_orb.generate_start_frame_macro"
    bl_label = ""
    bl_description = "Orb generates start frame macro"

    def execute(self, context):
        self.strip = 'macro'
        self.enable = True
        return super().execute(context)


class ORB_OT_alva_generate_end_frame_macro(ORB_OT_base_modal_operator):
    bl_idname = "alva_orb.generate_end_frame_macro"
    bl_label = ""
    bl_description = "Orb generates end frame macro"

    def execute(self, context):
        self.strip = 'macro'
        self.enable = False
        return super().execute(context)


class ORB_OT_alva_build_flash_macros(ORB_OT_base_modal_operator):
    bl_idname = "alva_orb.generate_flash_macros"
    bl_label = ""
    bl_description = "Orb builds flash macros"

    def execute(self, context):
        self.strip = 'flash'
        self.enable = True
        return super().execute(context)
    
    
class ORB_OT_alva_generate_offset_macro(ORB_OT_base_modal_operator):
    bl_idname = "alva_orb.generate_offset_macro"
    bl_label = ""
    bl_description = "Orb generates offset macro"

    def execute(self, context):
        self.strip = 'offset'
        self.enable=True
        return super().execute(context)
    
    
class ORB_OT_alva_bake_curves_to_cues(ORB_OT_base_modal_operator):
    bl_idname = "alva_orb.render_qmeo"
    bl_label = "Make Qmeo"
    bl_description = "Orb will create a qmeo. A qmeo is like a video, only each frame is a lighting cue. Use it to store complex animation data on the lighting console" 

    is_sound: BoolProperty(default=False) # type: ignore

    def execute(self, context):
        self.strip = 'qmeo'
        self.enable=True
        return super().execute(context)
    

class ORB_OT_alva_render_strips(Operator):
    bl_idname = "alva_orb.render_strips"
    bl_label = "Render Strips"
    bl_description = "Orb will create timecode events for every Macro, Cue, and Flash strip on the relevant sound strip's event list. Shortcut is Shift+Spacebar"

    @classmethod
    def poll(cls, context):
        relevant_strips = [strip for strip in context.scene.sequence_editor.sequences_all if strip.frame_final_end >= context.scene.frame_start and strip.frame_start <= context.scene.frame_end and (strip.type == 'COLOR' or strip.type == 'SOUND')]
        return len(relevant_strips) >= 1

    def invoke(self, context, event):
        return Orb.render_strips(self, context, event)
    

class ORB_OT_alva_sync_cue(Operator):
    bl_idname = "alva_orb.generate_cue"
    bl_label = ""
    bl_description = "Orb will set the cue duration on the board as the strip length of this strip. You must press this every time you change the length of the strip if you want it use the strip length to set cue time"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        
        frame_rate = EventUtils.get_frame_rate(context.scene)
        strip_length_in_seconds_total = int(round(active_strip.frame_final_duration / frame_rate))
        minutes = strip_length_in_seconds_total // 60
        seconds = strip_length_in_seconds_total % 60
        cue_duration = "{:02d}:{:02d}".format(minutes, seconds)
        cue_number = active_strip.eos_cue_number
        
        OSC.press_lighting_key("live")
        OSC.send_osc_lighting("/eos/newcmd", f"Cue {str(cue_number)} Time {cue_duration} Enter")

        props = ["key_light_slow", "rim_light_slow", "fill_light_slow", "texture_light_slow", "band_light_slow",
                 "accent_light_slow", "energy_light_slow", "cyc_light_slow"]
        
        for prop in props:
            discrete_time = str(getattr(active_strip, prop))
            if discrete_time != "0.0":
                param = prop.replace("_slow", "")

                import time

                from ..utils.rna_utils import parse_channels
                from ..utils.cpv_utils import simplify_channels_list

                groups = parse_channels(getattr(context.scene, f"{param}_groups"))
                channels = parse_channels(getattr(context.scene, f"{param}_channels"))
                submasters = parse_channels(getattr(context.scene, f"{param}_submasters"))

                if groups:
                    groups_str = simplify_channels_list(groups)
                    address = "/eos/newcmd"
                    argument = f"Group {groups_str} Time {discrete_time.zfill(2)} Enter"
                    OSC.send_osc_lighting(address, argument)
                    time.sleep(.2)

                if channels:
                    channels_str = simplify_channels_list(channels)
                    address = "/eos/newcmd"
                    argument = f"Chan {channels_str} Time {discrete_time.zfill(2)} Enter"
                    OSC.send_osc_lighting(address, argument)
                    time.sleep(.2)

                if submasters:
                    submasters_str = simplify_channels_list(submasters)
                    address = "/eos/newcmd"
                    argument = f"Sub {submasters_str} Time {discrete_time.zfill(2)} Enter"
                    OSC.send_osc_lighting(address, argument)
                    time.sleep(.2)

        OSC.press_lighting_key("update")
        time.sleep(.1)
        OSC.press_lighting_key("enter")

        active_strip.name = f"Cue {str(cue_number)}"
        self.report({'INFO'}, "Orb complete.")
        
        snapshot = str(context.scene.orb_finish_snapshot)
        OSC.send_osc_lighting("/eos/newcmd", f"Snapshot {snapshot} Enter")
        return {'FINISHED'}
    
    
class ORB_OT_alva_generate_text_macro(ORB_OT_base_modal_operator):
    bl_idname = "alva_orb.generate_text_macro"
    bl_label = ""
    bl_description = "Orb generates macro from text block"

    def execute(self, context):
        self.strip = 'text'
        self.enable = True
        return super().execute(context)
    
    
orb_operators = [
    ORB_OT_alva_group_patch,
    ORB_OT_base_modal_operator,
    ORB_OT_alva_execute_sound_on_cue,
    ORB_OT_alva_generate_start_frame_macro,
    ORB_OT_alva_generate_end_frame_macro,
    ORB_OT_alva_build_flash_macros,
    ORB_OT_alva_generate_offset_macro,
    ORB_OT_alva_bake_curves_to_cues,
    ORB_OT_alva_render_strips,
    ORB_OT_alva_sync_cue,
    ORB_OT_alva_generate_text_macro
]

def register():
    for cls in orb_operators:
        bpy.utils.register_class(cls)
    
def unregister():
    for cls in reversed(orb_operators):
        bpy.utils.unregister_class(cls)