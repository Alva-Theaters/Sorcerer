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
from bpy.types import UIList


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
                 
            if context.scene.scene_props.expand_toggles:
                row.scale_x = .9
                row.prop(item, "strobe_is_on", text="", icon='OUTLINER_DATA_LIGHTPROBE' if item.strobe_is_on else 'ADD', emboss=False)
                row.prop(item, "color_is_on", text="", icon='COLOR' if item.color_is_on else 'ADD', emboss=False)
                row.prop(item, "pan_tilt_is_on", text="", icon='ORIENTATION_GIMBAL' if item.pan_tilt_is_on else 'ADD', emboss=False)
                row.prop(item, "zoom_is_on", text="", icon='LINCURVE' if item.zoom_is_on else 'ADD', emboss=False)
                row.prop(item, "iris_is_on", text="", icon='RADIOBUT_OFF' if item.iris_is_on else 'ADD', emboss=False)
                row.prop(item, "edge_is_on", text="", icon='SELECT_SET' if item.edge_is_on else 'ADD', emboss=False)
                row.prop(item, "diffusion_is_on", text="", icon='MOD_CLOTH' if item.diffusion_is_on else 'ADD', emboss=False)
                row.prop(item, "gobo_is_on", text="", icon='POINTCLOUD_DATA' if item.gobo_is_on else 'ADD', emboss=False)
                

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