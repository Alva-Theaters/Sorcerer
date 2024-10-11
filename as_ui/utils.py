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
            if motif_type == "option_eos_macro":
                console_context = "macro"
            elif motif_type == "option_eos_cue":
                console_context = "cue"
            elif motif_type == "option_eos_flash":
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