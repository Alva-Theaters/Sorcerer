# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from bpy.types import UIList


class VIEW3D_UL_alva_errors_list(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.row().label(text=item.error_type)


class COMMON_UL_group_data_list(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if item.separator:
                row = layout.row()
                row.label(text="")
                return
            elif item.label:
                box = layout.box()
                row = box.row()
                row.prop(item, "name", text="", emboss=False)
                return
            else:
                row = layout.row(align=True)
                row.prop(item, "name", text="", emboss=False)


class SCENE_UL_preview_cue_list(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            
            scene = context.scene.scene_props
            cue_list = context.scene.cue_lists[scene.cue_lists_index]

            # Check if the t-bar is in transition
            in_transition = 0 < cue_list.int_t_bar < 100

            # Highlight the selected preview cue if the t-bar is in transition
            if index == cue_list.int_preview_index and in_transition:
                row.alert = True

            row.scale_x = .1
            row.label(text=f"{(index + 1)}:")
            row.scale_x = 1
            row.prop(item, "str_label", text="", emboss=False)
            row.alert = False  # Reset alert to default for other items
            row.prop(item, "int_number", text="", emboss=False)

            
class SCENE_UL_program_cue_list(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()

            scene = context.scene.scene_props
            cue_list = context.scene.cue_lists[scene.cue_lists_index]

            # Always highlight the selected program cue
            if index == cue_list.int_program_index:
                row.alert = True

            row.scale_x = .1
            row.label(text=f"{(index + 1)}:")
            row.scale_x = 1
            row.prop(item, "str_label", text="", emboss=False)
            row.alert = False  # Reset alert to default for other items
            row.prop(item, "int_number", text="", emboss=False)


class SCENE_UL_cue_list_list(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            row.prop(item, "name", text="", emboss=False)


class TEXT_UL_macro_list_all(UIList):
    bl_idname = "TEXT_UL_macro_list_all"
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.name)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)
            
         
uilist_classes = [
    VIEW3D_UL_alva_errors_list,
    COMMON_UL_group_data_list,
    SCENE_UL_preview_cue_list,
    SCENE_UL_program_cue_list,
    SCENE_UL_cue_list_list,
    TEXT_UL_macro_list_all
]


def register():
    for cls in uilist_classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(uilist_classes):
        bpy.utils.unregister_class(cls)