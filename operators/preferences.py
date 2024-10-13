# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Operator


class PREFERENCES_OT_alva_set_context_to_scene(Operator):
    '''Sets active_strip to nothing so you can see the settings for the global Scene instead'''
    bl_idname = "alva_pref.context_to_scene"
    bl_label = "Show Scene properties"

    def execute(self, context):
        if context.scene.sequence_editor:
            context.scene.sequence_editor.active_strip = None
        return {'FINISHED'}
    

class PREFERENCES_OT_alva_democratic(Operator):
    bl_idname = "alva_pref.democratic"
    bl_label = "Democratic"
    bl_description = "This is a democracy. When different controllers try to change the same channel parameter, their Influence parameter gives them votes in a weighted average"

    def execute(self, context):
        if context.scene.scene_props.is_democratic:
            
            return {'FINISHED'}
        else:
            context.scene.scene_props.is_democratic = True
            context.scene.scene_props.is_not_democratic = False
            
        return {'FINISHED'}   
    
    
class PREFERENCES_OT_alva_nondemocratic(Operator):
    bl_idname = "alva_pref.nondemocratic"
    bl_label = "Non-democratic"
    bl_description = "This isn't a democracy anymore. When different controllers try to change the same channel parameter, the strongest completely erases everyone else's opinion"

    def execute(self, context):
        if context.scene.scene_props.is_not_democratic:
            return {'FINISHED'}
        else:
            context.scene.scene_props.is_not_democratic = True
            context.scene.scene_props.is_democratic = False
            
        return {'FINISHED'}
    

class PREFERENCES_OT_alva_save_dtp(Operator):
    bl_idname = "alva_pref.save_dtp"
    bl_label = "Save as .dtp"
    bl_description = "Save a Digital Theatre Package (.dtp) to upload to the core"
    
    def execute(self, context):
        return {'FINISHED'}
    

preferences_operators = [
    PREFERENCES_OT_alva_set_context_to_scene,
    PREFERENCES_OT_alva_democratic,
    PREFERENCES_OT_alva_nondemocratic,
    PREFERENCES_OT_alva_save_dtp
]

def register():
    for cls in preferences_operators:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(preferences_operators):
        bpy.utils.unregister_class(cls)