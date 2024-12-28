# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Operator
from bpy.props import StringProperty

from ..utils.event_utils import EventUtils
from ..utils.osc import OSC
from ..orb import invoke_orb


class ORB_OT_sync(Operator):
    bl_idname = "alva_orb.orb"
    bl_label = ""
    bl_description = "Sync Sorcerer data onto the console"
    bl_options = {'REGISTER', 'UNDO'}

    as_id: StringProperty() # type: ignore
    cancel_key = 'ESC'

    def execute(self, context):
        self._cancel = False
        self._generator = self.orb(context)

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    def orb(self, context):
        yield from invoke_orb(self, context, self.as_id)

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


def register():
    bpy.utils.register_class(ORB_OT_sync)
    
def unregister():
    bpy.utils.unregister_class(ORB_OT_sync)