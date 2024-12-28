# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from ..utils import get_orb_icon


def draw_alva_time_header(self, context):
    orb = get_orb_icon()

    if (hasattr(context.scene, "sync_timecode") and
        hasattr(context.scene, "timecode_expected_lag") and
        context.scene.scene_props.view_alva_time_header and
        context.scene.scene_props.console_type_enum == 'option_eos'):
        scene = context.scene
        is_sound = is_qmeo_parent_a_sound_strip(context)

        layout = self.layout
        row = layout.row()
        from ...panels import TIME_PT_alva_flags
        row.popover(
            panel=TIME_PT_alva_flags.bl_idname,
            text="Render Flags",
        )

        row.prop(scene, "sync_timecode", text="", icon='LINKED' if scene.sync_timecode else 'UNLINKED')
        row = layout.row()
        is_strip = False
        if is_sound:
            active_strip = context.scene.sequence_editor.active_strip
            row.label(text="", icon='SOUND')
            target = active_strip
            is_strip = True

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
        row.operator("alva_orb.orb", text="", icon_value=orb.icon_id).as_orb_id = 'timeline'


def is_qmeo_parent_a_sound_strip(context):
    scene = context.scene
    is_sound = False
    sequencer_open = False
    active_strip = False

    for area in context.screen.areas:
        if area.type == 'SEQUENCE_EDITOR':
            sequencer_open = True
            if context.scene.sequence_editor.active_strip and context.scene.sequence_editor.active_strip is not None and context.scene.sequence_editor.active_strip.type == 'SOUND':
                active_strip = True
                break

    if sequencer_open and active_strip and scene.sequence_editor.active_strip.type == 'SOUND':
        is_sound = True

    return is_sound


def draw_alva_time_view(self, layout):
    if bpy.context.scene.scene_props.console_type_enum == 'option_eos':
        orb = get_orb_icon()

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
