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

from ..utils.osc import OSC
from ..updaters.properties_updaters import PropertiesUpdaters


# These are all for the keyboard shortcuts for Cue Switcher
class SCENE_OT_set_preview_index_Base(bpy.types.Operator):
    def set_preview_index(self, context, index):
        scene = context.scene.scene_props
        cue_list = scene.cue_lists[scene.cue_lists_index]
        cue_list.int_preview_index = index
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
        return {'FINISHED'}

class SCENE_OT_set_preview_index_1(SCENE_OT_set_preview_index_Base):
    bl_idname = "wm.set_preview_index_1"
    bl_label = "Set Preview Index to 1"
    
    def execute(self, context):
        return self.set_preview_index(context, 0)

class SCENE_OT_set_preview_index_2(SCENE_OT_set_preview_index_Base):
    bl_idname = "wm.set_preview_index_2"
    bl_label = "Set Preview Index to 2"
    
    def execute(self, context):
        return self.set_preview_index(context, 1)

class SCENE_OT_set_preview_index_3(SCENE_OT_set_preview_index_Base):
    bl_idname = "wm.set_preview_index_3"
    bl_label = "Set Preview Index to 3"
    
    def execute(self, context):
        return self.set_preview_index(context, 2)

class SCENE_OT_set_preview_index_4(SCENE_OT_set_preview_index_Base):
    bl_idname = "wm.set_preview_index_4"
    bl_label = "Set Preview Index to 4"
    
    def execute(self, context):
        return self.set_preview_index(context, 3)

class SCENE_OT_set_preview_index_5(SCENE_OT_set_preview_index_Base):
    bl_idname = "wm.set_preview_index_5"
    bl_label = "Set Preview Index to 5"
    
    def execute(self, context):
        return self.set_preview_index(context, 4)

class SCENE_OT_set_preview_index_6(SCENE_OT_set_preview_index_Base):
    bl_idname = "wm.set_preview_index_6"
    bl_label = "Set Preview Index to 6"
    
    def execute(self, context):
        return self.set_preview_index(context, 5)

class SCENE_OT_set_preview_index_7(SCENE_OT_set_preview_index_Base):
    bl_idname = "wm.set_preview_index_7"
    bl_label = "Set Preview Index to 7"
    
    def execute(self, context):
        return self.set_preview_index(context, 6)

class SCENE_OT_set_preview_index_8(SCENE_OT_set_preview_index_Base):
    bl_idname = "wm.set_preview_index_8"
    bl_label = "Set Preview Index to 8"
    
    def execute(self, context):
        return self.set_preview_index(context, 7)

class SCENE_OT_set_preview_index_9(SCENE_OT_set_preview_index_Base):
    bl_idname = "wm.set_preview_index_9"
    bl_label = "Set Preview Index to 9"
    
    def execute(self, context):
        return self.set_preview_index(context, 8)
    
    
class CutCueOperator(bpy.types.Operator):
    bl_idname = "cue.cut"
    bl_label = "Cut immediately to Preview Cue"

    def execute(self, context):
        scene = context.scene.scene_props
        cue_list = context.scene.cue_lists[scene.cue_lists_index]
        preview_cue = cue_list.cues[cue_list.int_preview_index].int_number
        
        OSC.send_osc_lighting("/eos/newcmd", f"Go_to_Cue {preview_cue} Time 0 Enter")
        
        PropertiesUpdaters.swap_preview_and_program(cue_list)
        return {'FINISHED'}
    
    
class AutoCueOperator(bpy.types.Operator):
    bl_idname = "cue.auto"
    bl_label = "Transition to Preview Cue using Auto Rate time"

    def execute(self, context):
        scene = context.scene.scene_props
        cue_list = context.scene.cue_lists[scene.cue_lists_index]
        preview_cue = cue_list.cues[cue_list.int_preview_index].int_number
        
        OSC.send_osc_lighting("/eos/newcmd", f"Go_to_Cue {cue_list.int_cue_list_number} / {preview_cue} Time {scene.float_auto_time} Enter")
        PropertiesUpdaters.swap_preview_and_program(cue_list)
        return {'FINISHED'}
    
    
class SelfCueOperator(bpy.types.Operator):
    bl_idname = "cue.self"
    bl_label = "Transition to Preview Cue using the cue's own predefined fade duration"

    def execute(self, context):
        scene = context.scene.scene_props
        
        cue_list = context.scene.cue_lists[scene.cue_lists_index]
        preview_cue = cue_list.cues[cue_list.int_preview_index].int_number
        
        OSC.send_osc_lighting("/eos/newcmd", f"Go_to_Cue {cue_list.int_cue_list_number} / {preview_cue} Time Enter")
        PropertiesUpdaters.swap_preview_and_program(cue_list)
        return {'FINISHED'}
    
    
class BlueOperator(bpy.types.Operator):
    bl_idname = "cue.blue"
    bl_label = "Fade to blue-out"

    def execute(self, context):
        scene = context.scene.scene_props
        
        OSC.send_osc_lighting("/eos/newcmd", f"Go_to_Cue {scene.string_blue_cue} Time {scene.float_blue_time} Enter")
        return {'FINISHED'}
    
    
class BlackOperator(bpy.types.Operator):
    bl_idname = "cue.black"
    bl_label = "Fade to black-out"

    def execute(self, context):
        scene = context.scene.scene_props
        
        OSC.send_osc_lighting("/eos/newcmd", f"Go_to_Cue {scene.string_black_cue} Time {scene.float_black_time} Enter")
        return {'FINISHED'}
    
    
class RestoreOperator(bpy.types.Operator):
    bl_idname = "cue.restore"
    bl_label = "Fade to Restore"

    def execute(self, context):
        scene = context.scene.scene_props
        
        OSC.send_osc_lighting("/eos/newcmd", f"Go_to_Cue {scene.string_restore_cue} Time {scene.float_restore_time} Enter")
        return {'FINISHED'}
    
    
class AddCueListOperator(bpy.types.Operator):
    bl_idname = "cue_list.add_list"
    bl_label = "Add Cue List"

    def execute(self, context):
        scene = context.scene.scene_props
        cue_list = context.scene.cue_lists.add()
        cue_list.int_number = len(context.scene.cue_lists)
        scene.cue_lists_index = len(context.scene.cue_lists) - 1
        cue_list.name = f"Song {(scene.cue_lists_index + 1)}"
        return {'FINISHED'}

class RemoveCueListOperator(bpy.types.Operator):
    bl_idname = "cue_list.remove_list"
    bl_label = "Remove Cue List"

    def execute(self, context):
        scene = context.scene.scene_props
        index = scene.cue_lists_index
        context.scene.cue_lists.remove(index)
        scene.cue_lists_index = max(0, index - 1)
        return {'FINISHED'}

class AddCueToListOperator(bpy.types.Operator):
    bl_idname = "cue.add_cue"
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

class RemoveCueFromListOperator(bpy.types.Operator):
    bl_idname = "cue.remove_cue"
    bl_label = "Remove Cue"

    def execute(self, context):
        scene = context.scene.scene_props
        cue_list = context.scene.cue_lists[scene.cue_lists_index]
        index = cue_list.int_preview_index
        cue_list.cues.remove(index)
        cue_list.int_preview_index = max(0, index - 1)
        return {'FINISHED'}
    
    
operator_classes = [
    SCENE_OT_set_preview_index_1,
    SCENE_OT_set_preview_index_2,
    SCENE_OT_set_preview_index_3,
    SCENE_OT_set_preview_index_4,
    SCENE_OT_set_preview_index_5,
    SCENE_OT_set_preview_index_6,
    SCENE_OT_set_preview_index_7,
    SCENE_OT_set_preview_index_8,
    SCENE_OT_set_preview_index_9,
    CutCueOperator,
    AutoCueOperator,
    BlueOperator,
    BlackOperator,
    RestoreOperator,
    AddCueListOperator,
    RemoveCueListOperator,
    AddCueToListOperator,
    RemoveCueFromListOperator,
    SelfCueOperator
]


def register():
    for cls in operator_classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(operator_classes):
        bpy.utils.unregister_class(cls)