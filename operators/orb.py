# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Operator
from bpy.props import BoolProperty

from ..utils.event_utils import EventUtils
from ..utils.osc import OSC
from ..orb import invoke_orb


class ORB_OT_base(Operator):
    bl_idname = "alva_orb.modal_base"
    bl_label = ""
    bl_description = "Base class for Orb modals"

    cancel_key = 'ESC'

    def execute(self, context):
        self._cancel = False
        self._generator = self.orb(context, self.orb_idname)

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    def orb(self, context, bl_idname):
        yield from invoke_orb(self, context, bl_idname)

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
                #self.cancel(context)
                return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        OSC.send_osc_lighting("/eos/key/escape", "1")
        OSC.send_osc_lighting("/eos/key/escape", "0")
        OSC.send_osc_lighting("/eos/newcmd", "")
        # Orb.Eos.reset_macro_key()
        # Orb.Eos.restore_snapshot(context.scene)


class ORB_OT_alva_group_patch(ORB_OT_base):
    bl_idname = "alva_orb.group_patch"
    bl_label = "Patch Group"
    bl_description = "Patch group on console"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        self.orb_idname = self.bl_idname
        return super().execute(context)
        

class ORB_OT_sound_strip(ORB_OT_base):
    bl_idname = "alva_orb.sound_strip"
    bl_label = ""
    bl_description = "Orb executes sound on cue"

    def execute(self, context):
        self.orb_idname = "alva_orb.sound_strip"
        return super().execute(context)
    

class ORB_OT_cue_strip(ORB_OT_base):
    bl_idname = "alva_orb.cue_strip"
    bl_label = ""
    bl_description = "Orb will set the cue duration on the board as the strip length of this strip. You must press this every time you change the length of the strip if you want it use the strip length to set cue time"
    
    def execute(self, context):
        self.orb_idname = "alva_orb.cue_strip"
        return super().execute(context)


class ORB_OT_macro_strip(ORB_OT_base):
    bl_idname = "alva_orb.macro_strip"
    bl_label = ""
    bl_description = "Orb generates start frame macro"

    def execute(self, context):
        self.orb_idname = "alva_orb.macro_strip"
        return super().execute(context)


class ORB_OT_flash_strip(ORB_OT_base):
    bl_idname = "alva_orb.flash_strip"
    bl_label = ""
    bl_description = "Orb builds flash macros"

    def execute(self, context):
        self.orb_idname = "alva_orb.flash_strip"
        return super().execute(context)
    
    
class ORB_OT_offset_strip(ORB_OT_base):
    bl_idname = "alva_orb.offset_strip"
    bl_label = ""
    bl_description = "Orb generates offset macro"

    def execute(self, context):
        self.orb_idname = "alva_orb.offset_strip"
        return super().execute(context)
    
    
class ORB_OT_qmeo_make(ORB_OT_base):
    bl_idname = "alva_orb.qmeo_make"
    bl_label = "Make Qmeo"
    bl_description = "Orb will create a qmeo. A qmeo is like a video, only each frame is a lighting cue. Use it to store complex animation data on the lighting console" 

    is_sound: BoolProperty(default=False) # type: ignore

    def execute(self, context):
        self.orb_idname = "alva_orb.qmeo_make"
        return super().execute(context)
    

class ORB_OT_strips_sync(Operator):
    bl_idname = "alva_orb.strips_sync"
    bl_label = "Sync Strips"
    bl_description = "Orb will create timecode events for every Macro, Cue, and Flash strip on the relevant sound strip's event list. Shortcut is Shift+Spacebar"

    @classmethod
    def poll(cls, context):
        relevant_strips = [strip for strip in context.scene.sequence_editor.sequences_all if strip.frame_final_end >= context.scene.frame_start and strip.frame_start <= context.scene.frame_end and (strip.type == 'COLOR' or strip.type == 'SOUND')]
        return len(relevant_strips) >= 1

    def execute(self, context):
        self.orb_idname = "alva_orb.strips_sync"
        return super().execute(context)
    

class ORB_OT_text_block_macro(ORB_OT_base):
    bl_idname = "alva_orb.text_block_macro"
    bl_label = ""
    bl_description = "Orb generates macro from text block"

    def execute(self, context):
        self.orb_idname = "alva_orb.text_block_macro"
        return super().execute(context)


orb_operators = [
    ORB_OT_alva_group_patch,
    ORB_OT_sound_strip,
    ORB_OT_cue_strip,
    ORB_OT_macro_strip,
    ORB_OT_flash_strip,
    ORB_OT_offset_strip,
    ORB_OT_strips_sync,
    ORB_OT_qmeo_make,
    ORB_OT_text_block_macro
]

def register():
    for cls in orb_operators:
        bpy.utils.register_class(cls)
    
def unregister():
    for cls in reversed(orb_operators):
        bpy.utils.unregister_class(cls)