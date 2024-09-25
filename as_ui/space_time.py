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


# Custom icon stuff
import bpy.utils.previews
import os

preview_collections = {}
pcoll = bpy.utils.previews.new()
preview_collections["main"] = pcoll

addon_dir = os.path.dirname(__file__)
pcoll.load("orb", os.path.join(addon_dir, "alva_orb.png"), 'IMAGE')


def draw_alva_time_header(self, context):
    pcoll = preview_collections["main"]
    orb = pcoll["orb"]

    if (hasattr(context.scene, "sync_timecode") and
        hasattr(context.scene, "timecode_expected_lag") and
        context.scene.scene_props.view_alva_time_header and
        context.scene.scene_props.console_type_enum == 'option_eos'):
        scene = context.scene

        sequencer_open = False
        active_strip = False

        for area in context.screen.areas:
            if area.type == 'SEQUENCE_EDITOR':
                sequencer_open = True
                if context.scene.sequence_editor.active_strip and context.scene.sequence_editor.active_strip is not None and context.scene.sequence_editor.active_strip.type == 'SOUND':
                    active_strip = True
                    break

        layout = self.layout

        row = layout.row()
        from ..panels import TIME_PT_alva_flags
        row.popover(
            panel=TIME_PT_alva_flags.bl_idname,
            text="Render Flags",
        )

        row.prop(scene, "sync_timecode", text="", icon='LINKED' if scene.sync_timecode else 'UNLINKED')

        row = layout.row()
        if sequencer_open and active_strip:
            active_strip = context.scene.sequence_editor.active_strip
            icon = 'IPO_BEZIER' if active_strip.type == 'COLOR' else 'SOUND'
            row.label(text="", icon=icon)
            target = active_strip

            row = layout.row(align=True)
            row.scale_x = 0.5
            row.prop(target, "str_start_cue", text="")
            row.prop(target, "str_end_cue", text="")
        else:
            row.label(text="", icon='SCENE_DATA')
            target = scene

            row = layout.row(align=True)
            row.scale_x = 0.75
            row.prop(target, "int_start_macro", text="Macro")

        row = layout.row()
        row.operator("alva_orb.render_qmeo", text="", icon_value=orb.icon_id)


def draw_alva_time_view(self, layout):
    if bpy.context.scene.scene_props.console_type_enum == 'option_eos':
        pcoll = preview_collections["main"]
        orb = pcoll["orb"]

        layout = self.layout
        layout.separator()
        layout.label(text="Alva Sorcerer", icon_value=orb.icon_id)
        layout.prop (bpy.context.scene.scene_props, "view_alva_time_header", text="Header")


def draw_alva_time_playback(self, context):
    if context.scene.scene_props.console_type_enum == 'option_eos':
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        layout.prop(context.scene, "timecode_expected_lag", text="OSC Lag")


def draw_alva_time_flags(self, context):
    scene = context.scene.scene_props
    layout = self.layout

    layout.use_property_split = True
    layout.use_property_decorate = False

    layout.column(heading="Types").prop(scene, "enable_lighting", text="Lighting")
    layout.prop(scene, "enable_video", text="Video")
    layout.prop(scene, "enable_audio", text="Audio")

    layout.separator()

    layout.column(heading="Controllers").prop(scene, "enable_objects", text="Objects")
    layout.prop(scene, "enable_strips", text="Strips")
    layout.prop(scene, "enable_nodes", text="Nodes")

    layout.separator()

    layout.column(heading="Freezing").prop(scene, "enable_seconds", text="Seconds")
    layout.prop(scene, "enable_thirds", text="Thirds")
