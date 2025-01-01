# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Operator
from bpy.props import IntProperty

from ..utils.osc import OSC
from ..updaters.properties import PropertiesUpdaters


class PROPERTIES_OT_alva_take_cue(Operator):
    bl_label = ""
    bl_idname = "alva_cue.take"

    index: IntProperty()  # type: ignore

    def execute(self, context):
        scene = context.scene
        cue_list = scene.cue_lists[scene.scene_props.cue_lists_index]
        cue_list.int_preview_index = (self.index - 1)
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
        return {'FINISHED'}
    
    
class PROPERTIES_OT_alva_cue_cut(Operator):
    bl_idname = "alva_cue.cut"
    bl_label = "Cut immediately to Preview Cue"

    def execute(self, context):
        scene = context.scene.scene_props
        cue_list = context.scene.cue_lists[scene.cue_lists_index]
        preview_cue = cue_list.cues[cue_list.int_preview_index].int_number
        
        OSC.send_osc_lighting("/eos/newcmd", f"Go_to_Cue {preview_cue} Time 0 Enter")
        
        PropertiesUpdaters.swap_preview_and_program(cue_list)
        return {'FINISHED'}
    
    
class PROPERTIES_OT_alva_cue_auto(Operator):
    bl_idname = "alva_cue.auto"
    bl_label = "Transition to Preview Cue using Auto Rate time"

    def execute(self, context):
        scene = context.scene.scene_props
        cue_list = context.scene.cue_lists[scene.cue_lists_index]
        preview_cue = cue_list.cues[cue_list.int_preview_index].int_number
        
        OSC.send_osc_lighting("/eos/newcmd", f"Go_to_Cue {cue_list.int_cue_list_number} / {preview_cue} Time {scene.float_auto_time} Enter")
        PropertiesUpdaters.swap_preview_and_program(cue_list)
        return {'FINISHED'}
    
    
class PROPERTIES_OT_alva_cue_self(Operator):
    bl_idname = "alva_cue.self"
    bl_label = "Transition to Preview Cue using the cue's own predefined fade duration"

    def execute(self, context):
        scene = context.scene.scene_props
        
        cue_list = context.scene.cue_lists[scene.cue_lists_index]
        preview_cue = cue_list.cues[cue_list.int_preview_index].int_number
        
        OSC.send_osc_lighting("/eos/newcmd", f"Go_to_Cue {cue_list.int_cue_list_number} / {preview_cue} Time Enter")
        PropertiesUpdaters.swap_preview_and_program(cue_list)
        return {'FINISHED'}
    
    
class PROPERTIES_OT_alva_cue_blue(Operator):
    bl_idname = "alva_cue.blue"
    bl_label = "Fade to blue-out"

    def execute(self, context):
        scene = context.scene.scene_props
        
        OSC.send_osc_lighting("/eos/newcmd", f"Go_to_Cue {scene.string_blue_cue} Time {scene.float_blue_time} Enter")
        return {'FINISHED'}
    
    
class PROPERTIES_OT_alva_cue_black(Operator):
    bl_idname = "alva_cue.black"
    bl_label = "Fade to black-out"

    def execute(self, context):
        scene = context.scene.scene_props
        
        OSC.send_osc_lighting("/eos/newcmd", f"Go_to_Cue {scene.string_black_cue} Time {scene.float_black_time} Enter")
        return {'FINISHED'}
    
    
class PROPERTIES_OT_alva_cue_restore(Operator):
    bl_idname = "alva_cue.restore"
    bl_label = "Fade to Restore"

    def execute(self, context):
        scene = context.scene.scene_props
        
        OSC.send_osc_lighting("/eos/newcmd", f"Go_to_Cue {scene.string_restore_cue} Time {scene.float_restore_time} Enter")
        return {'FINISHED'}
    
    
class PROPERTIES_OT_alva_add_cue_list(Operator):
    bl_idname = "alva_cue.add_list"
    bl_label = "Add Cue List"

    def execute(self, context):
        scene = context.scene.scene_props
        cue_list = context.scene.cue_lists.add()
        cue_list.int_number = len(context.scene.cue_lists)
        scene.cue_lists_index = len(context.scene.cue_lists) - 1
        cue_list.name = f"Song {(scene.cue_lists_index + 1)}"
        return {'FINISHED'}

class PROPERTIES_OT_alva_remove_cue_list(Operator):
    bl_idname = "alva_cue.remove_list"
    bl_label = "Remove Cue List"

    def execute(self, context):
        scene = context.scene.scene_props
        index = scene.cue_lists_index
        context.scene.cue_lists.remove(index)
        scene.cue_lists_index = max(0, index - 1)
        return {'FINISHED'}

class PROPERTIES_OT_alva_add_cue_to_list(Operator):
    bl_idname = "alva_cue.add_cue"
    bl_label = "Add Cue"

    def execute(self, context):
        scene = context.scene.scene_props
        cue_list = context.scene.cue_lists[scene.cue_lists_index]
        cue = cue_list.cues.add()
        cue.int_number = len(cue_list.cues)
        cue_list.int_preview_index = len(cue_list.cues) - 1
        names = ["Intro", "Verse 1", "Pre-chorus", "Chorus", "Verse 2", "Chorus", "Verse 3", "Bridge", "Chorus", "Final Chorus", "Outro"]
        try:
            cue.str_label = names[cue_list.int_preview_index]
        except: cue.str_label = "Cue"
        return {'FINISHED'}

class PROPERTIES_OT_alva_remove_cue_from_list(Operator):
    bl_idname = "alva_cue.remove_cue"
    bl_label = "Remove Cue"

    def execute(self, context):
        scene = context.scene.scene_props
        cue_list = context.scene.cue_lists[scene.cue_lists_index]
        index = cue_list.int_preview_index
        cue_list.cues.remove(index)
        cue_list.int_preview_index = max(0, index - 1)
        return {'FINISHED'}
    

operator_classes = [
    PROPERTIES_OT_alva_take_cue,
    PROPERTIES_OT_alva_cue_cut,
    PROPERTIES_OT_alva_cue_auto,
    PROPERTIES_OT_alva_cue_blue,
    PROPERTIES_OT_alva_cue_black,
    PROPERTIES_OT_alva_cue_restore,
    PROPERTIES_OT_alva_add_cue_list,
    PROPERTIES_OT_alva_remove_cue_list,
    PROPERTIES_OT_alva_add_cue_to_list,
    PROPERTIES_OT_alva_remove_cue_from_list,
    PROPERTIES_OT_alva_cue_self
]


def register():
    for cls in operator_classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(operator_classes):
        bpy.utils.unregister_class(cls)