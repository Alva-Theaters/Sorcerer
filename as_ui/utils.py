# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy.utils.previews
import os

preview_collections = {}


def get_orb_icon():
    global preview_collections
    if "main" not in preview_collections:
        pcoll = bpy.utils.previews.new()
        addon_dir = os.path.dirname(__file__)
        pcoll.load("orb", os.path.join(addon_dir, "alva_orb.png"), 'IMAGE')
        preview_collections["main"] = pcoll
    return preview_collections["main"]["orb"]


def unregister_previews():
    global preview_collections
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()


def determine_sequencer_contexts(sequence_editor, active_strip):
    """Determines the alva_context and console_context based on the selected strips in the sequence_editor."""
    if sequence_editor and active_strip:
        selected_color_strips = []
        selected_sound_strips = []
        selected_video_strips = []
        selected_strips = []
        if active_strip:
            motif_type = active_strip.my_settings.motif_type_enum
            alva_context = "no_selection"
            console_context = "no_motif_type"
        
        for strip in sequence_editor.sequences:
            if strip.select or (active_strip and strip == active_strip):
                selected_strips.append(strip)
                if strip.type == 'COLOR':
                    selected_color_strips.append(strip)
                elif strip.type == 'SOUND':
                    selected_sound_strips.append(strip)
                elif strip.type == 'MOVIE':
                    selected_video_strips.append(strip)
        
        if selected_strips:
            if len(selected_strips) != len(selected_color_strips) and selected_color_strips:
                alva_context = "incompatible_types"
            elif selected_sound_strips and not selected_color_strips and len(selected_strips) == 1:
                alva_context = "only_sound"
            elif len(selected_sound_strips) == 1 and len(selected_video_strips) == 1 and len(selected_strips) == 2:
                alva_context = "one_video_one_audio"
            elif len(selected_sound_strips) == 1 and len(selected_video_strips) == 1 and len(selected_strips) == 3:
                alva_context = "one_video_one_audio"
            elif not (selected_color_strips or selected_sound_strips):
                alva_context = "none_relevant"
            elif len(selected_strips) == len(selected_color_strips) and selected_color_strips and active_strip.type == 'COLOR':
                alva_context = "only_color"
                
        elif not selected_strips:
            alva_context = "none_relevant"
        
        if alva_context == "only_color":
            if motif_type == "option_macro":
                console_context = "macro"
            elif motif_type == "option_cue":
                console_context = "cue"
            elif motif_type == "option_flash":
                console_context = "flash"
            elif motif_type == "option_animation":
                console_context = "animation"
            elif motif_type == "option_offset":
                console_context = "offset"
            elif motif_type == "option_trigger":
                console_context = "trigger"
    else:
        alva_context = "none_relevant"
        console_context = "none"

    return alva_context, console_context


def find_group_label(controller):
    '''Used by Global Node UI draw.'''
    if not controller.is_text_not_group:
        return controller.str_group_label
    else:
        return f"Channels {controller.str_manual_fixture_selection}"