# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy.utils.previews
import os

from ..utils.spy_utils import REGISTERED_STRIPS, REGISTERED_PARAMETERS, REGISTERED_LIGHTING_CONSOLES

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


def determine_sequencer_context(sequence_editor, active_strip):
    """Determines the alva_context based on the selected strips in the sequence_editor."""
    if not (sequence_editor and active_strip):
        return "none_relevant"
    
    if not active_strip:
        return "no_selection"
    
    all, colors, sounds, videos = count_selected_strips(sequence_editor, active_strip)
    
    if len(all) == len(colors) and colors and active_strip.type == 'COLOR':  # Most common first.
        return "only_color"
    elif sounds and len(all) == 1:
        return "only_sound"
    elif len(sounds) == 1 and len(videos) == 1 and (len(all) == 2 or len(all) == 3):  # Include speed strips.
        return "one_video_one_audio"
    elif not (colors or sounds):
        return "none_relevant"
    return "incompatible_types"


def count_selected_strips(sequence_editor, active_strip):
    colors = []
    sounds = []
    videos = []
    all = []
    for strip in sequence_editor.sequences:
        if strip.select or (active_strip and strip == active_strip):
            all.append(strip)
            if strip.type == 'COLOR':
                colors.append(strip)
            elif strip.type == 'SOUND':
                sounds.append(strip)
            elif strip.type == 'MOVIE':
                videos.append(strip)

    return all, colors, sounds, videos
    

def find_extendables_class(class_type, id='', all=False):
    class_type_to_list = {
        'strips': REGISTERED_STRIPS,
        'parameters': REGISTERED_PARAMETERS,
        'lighting_consoles': REGISTERED_LIGHTING_CONSOLES
    }
    class_list = class_type_to_list[class_type]

    if all:
        return class_list
    
    try:
        return class_list[id]
    except KeyError:
        return None


def find_group_label(controller):
    '''Used by Global Node UI draw.'''
    if not controller.is_text_not_group:
        return controller.str_group_label
    else:
        return f"Channels {controller.str_manual_fixture_selection}"