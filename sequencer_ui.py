# This file is part of Alva Sorcerer.
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
import socket
import os
import bpy.utils.previews


preview_collections = {}


def determine_contexts(sequence_editor, active_strip):
    """
    Determines the alva_context and console_context based on the selected strips in the sequence_editor.
    """

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
            if strip.select:
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
            elif motif_type == "option_trigger":
                console_context = "trigger"
    else:
        alva_context = "none_relevant"
        console_context = "none"

    return alva_context, console_context


class AlvaConsolePanel(bpy.types.Panel):
    bl_label = "Lighting"
    bl_idname = "ALVA_PT_console_panel"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Alva Sorcerer'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        pcoll = preview_collections["main"]
        orb = pcoll["orb"]
        
        if not hasattr(scene, "sequence_editor") and scene.sequence_editor:
            row = column.row(align=True)
            row.operator("my.add_macro", text="", icon='REC')
            row.operator("my.add_cue", text="", icon='PLAY')
            row.operator("my.add_flash", text="", icon='LIGHT_SUN')
            row.operator("my.add_animation", text="", icon='IPO_BEZIER')
            row.label(text="Welcome to Sorcerer! Press O while in sequencer or add color strip to start.")
            row.label(text="or add color strip to start.")
            column.separator()
            return

        # Check if the sequence editor and active strip exist
        elif hasattr(scene, "sequence_editor") and scene.sequence_editor:
            sequence_editor = scene.sequence_editor
            if hasattr(sequence_editor, "active_strip") and sequence_editor.active_strip:
                active_strip = sequence_editor.active_strip
                alva_context, console_context = determine_contexts(sequence_editor, active_strip)
            else:
                alva_context = "none_relevant"
                console_context = "none"
            column = layout.column(align=True)

            if alva_context == "incompatible_types":
                column.separator()
                row = column.row(align=True)
                row.prop(scene.my_tool, "motif_names_enum", text="", icon='COLOR', icon_only=True)
                row.prop(active_strip, "name", text="")
                row.operator("my.add_macro", text="", icon='REC')
                row.operator("my.add_cue", text="", icon='PLAY')
                row.operator("my.add_flash", text="", icon='LIGHT_SUN')
                row.operator("my.add_animation", text="", icon='IPO_BEZIER')
                if scene.triggers_enabled:
                    row.operator("my.add_trigger", text="", icon='SETTINGS')
                column.separator()
                row = column.row()
                row.label(text="Non-color strips selected.")
                return
             
            if alva_context == "only_sound":
                row = column.row(align=True)
                row.operator("my.mute_button", icon='HIDE_OFF' if not active_strip.mute else 'HIDE_ON')
                row.prop(active_strip, "name", text="")
                column.separator()
                column.separator()
                box = column.box()  
                row = box.row(align=True)
                row.operator("my.bump_tc_left_five", text="", icon='BACK')
                row.operator("my.bump_tc_left_one", text="", icon='TRIA_LEFT')
                row.operator("my.bump_tc_right_one", text="", icon='TRIA_RIGHT')
                row.operator("my.bump_tc_right_five", text="", icon='FORWARD')
                row.prop(active_strip, "song_timecode_clock_number", text="Event List #")
                row.operator("my.clear_timecode_clock", icon="CANCEL")
                box.separator()     
                row = box.row()
                row.prop(active_strip, "execute_on_cue_number", text='"Enable" Cue #')
                row = box.row()
                row.prop(active_strip, "execute_with_macro_number", text="With Macro #")
                row.operator("my.execute_on_cue_operator", icon_value=orb.icon_id)
                box.separator()
                row = box.row()
                row.prop(active_strip, "disable_on_cue_number", text='"Disable" Cue #')
                row = box.row()
                row.prop(active_strip, "disable_with_macro_number", text="With Macro #")
                row.operator("my.disable_on_cue_operator", icon_value=orb.icon_id)
                box.separator()
                column.separator()
                row = box.row()
                row.operator("my.generate_text", icon="TEXT")
                box.separator()
                row = box.row(align=True)
                row.operator("my.bump_left_five", icon='BACK')
                row.operator("my.bump_left_one", icon='BACK')
                row.operator("my.bump_up", icon='TRIA_UP')
                row.operator("my.bump_down", icon='TRIA_DOWN')
                row.operator("my.bump_right_one", icon='FORWARD')
                row.operator("my.bump_right_five", icon='FORWARD')
                return
                
            if alva_context == "one_video_one_audio":
                row = column.row(align=True)
                row.prop(scene.my_tool, "motif_names_enum", text="", icon='COLOR', icon_only=True)
                row.prop(active_strip, "name", text="")
                row.operator("my.add_macro", text="", icon='REC')
                row.operator("my.add_cue", text="", icon='PLAY')
                row.operator("my.add_flash", text="", icon='LIGHT_SUN')
                row.operator("my.add_animation", text="", icon='IPO_BEZIER')
                if scene.triggers_enabled:
                    row.operator("my.add_trigger", text="", icon='SETTINGS')
                column.separator()
                row = column.row()
                row.label(text="Non-color strips selected.")
                return
                    
            if alva_context == "none_relevant":
                row = column.row(align=True)
                row.prop(scene.my_tool, "motif_names_enum", text="", icon='COLOR', icon_only=True)
                if hasattr(sequence_editor, "active_strip") and sequence_editor.active_strip:
                    active_strip = sequence_editor.active_strip
                    if active_strip and active_strip.type == 'COLOR':
                        row.prop(active_strip, "motif_name", text="")
                row.operator("my.add_macro", text="", icon='REC')
                row.operator("my.add_cue", text="", icon='PLAY')
                row.operator("my.add_flash", text="", icon='LIGHT_SUN')
                row.operator("my.add_animation", text="", icon='IPO_BEZIER')
                if scene.triggers_enabled:
                    row.operator("my.add_trigger", text="", icon='SETTINGS')
                    
                column.separator()
                return
            
            ###############
            # COLOR HEADER
            ###############
            if alva_context == "only_color":
                row = column.row(align=True)
                strip_type = active_strip.my_settings.motif_type_enum
                row.prop(scene.my_tool, "motif_names_enum", text="", icon='REC' if strip_type == "option_eos_macro" else 'PLAY' if strip_type == "option_eos_cue" else 'OUTLINER_OB_LIGHT' if strip_type == "option_eos_flash" else 'IPO_BEZIER' if strip_type == "option_animation" else 'SETTINGS', icon_only=True)
                if active_strip.is_linked and not console_context == "animation":
                    row.alert = 1
                row.prop(active_strip, "motif_name", text="")
                row.alert = 0
                row.operator("my.add_macro", text="", icon='REC')
                row.operator("my.add_cue", text="", icon='PLAY')
                row.operator("my.add_flash", text="", icon='LIGHT_SUN')
                row.operator("my.add_animation", text="", icon='IPO_BEZIER')
                if scene.triggers_enabled:
                    row.operator("my.add_trigger", text="", icon='SETTINGS')       
                column.separator()
                column.separator()
                active_strip = context.scene.sequence_editor.active_strip
                box = column.box()  
                row = box.row(align=True)
                row.operator("my.mute_button", icon='HIDE_OFF' if not active_strip.mute else 'HIDE_ON')
                my_settings = active_strip.my_settings
                row.prop(my_settings, "motif_type_enum", expand=True)
                if active_strip.is_linked and console_context != "animation":
                    row.alert = 1
                    row.prop(active_strip, "is_linked", icon='LINKED')
                else:
                    row.alert = 0
                    row.prop(active_strip, "is_linked", icon='UNLINKED')
  
                ###############
                # MACRO STRIPS
                ###############
                if console_context == "macro":
                    box = column.box()
                    row = box.row()
                    row.label(text='* = "Sneak Time " + [Strip length]')
                    row = box.row(align=True)
                    row.operator("my.start_macro_search", icon='VIEWZOOM')
                    row.prop(active_strip, "start_frame_macro", text="Start frame macro #")
                    row.operator("my.start_macro_fire", icon='FILE_REFRESH')
                    row.prop(active_strip, "start_macro_muted", icon='HIDE_OFF' if not active_strip.start_macro_muted else 'HIDE_ON', toggle=True)
                    row = box.row(align=True)
                    row.prop(active_strip, "start_frame_macro_text_gui")
                    row.operator("my.generate_start_frame_macro", icon_value=orb.icon_id)
                    row = box.separator()
                    row = box.row(align=True)
                    row.operator("my.end_macro_search", icon='VIEWZOOM')
                    row.prop(active_strip, "end_frame_macro", text="End frame macro #")
                    row.operator("my.end_macro_fire", icon='FILE_REFRESH')
                    row.prop(active_strip, "end_macro_muted", icon='HIDE_OFF' if not active_strip.end_macro_muted else 'HIDE_ON', toggle=True)
                    row = box.row(align=True)
                    row.prop(active_strip, "end_frame_macro_text_gui")
                    row.operator("my.generate_end_frame_macro", icon_value=orb.icon_id)
                
                                
                ###############
                # CUE STRIPS
                ###############             
                if console_context == "cue":
                    box = column.box() 
                    row = box.row(align=True)  
                    row.prop(active_strip, "eos_cue_number", text="Cue #")
                    row.operator("my.go_to_cue_out_operator", text="", icon='GHOST_ENABLED')
                    if scene.cue_builder_toggle:
                        row.operator("my.update_builder", text="", icon='FILE_REFRESH')
                    row.operator("my.record_cue", text="", icon='REC')
                    row.operator("my.sync_cue", icon_value=orb.icon_id)
                    box.separator()
                    row = box.row(align=True)
                    row.prop(active_strip, "background_color", text="")
                    row.prop(active_strip, "accent_color", text="")
                    if scene.cue_builder_toggle:
                        row = box.row(align=True)
                        row.operator("my.key_groups", text="", icon='PREFERENCES')
                        row.prop(active_strip, "key_light", text="Key Light", slider=True)
                        if active_strip.key_is_recording:
                            row.alert = 1
                        else:
                            row.alert = 0
                        row.operator("my.focus_one", text="", icon='EVENT_F1')
                        row.operator("my.focus_two", text="", icon='EVENT_F2')
                        row.operator("my.focus_three", text="", icon='EVENT_F3')
                        row.operator("my.focus_four", text="", icon='EVENT_F4')
                        row.prop(active_strip, "key_is_recording", text="", icon='REC')
                        row.alert = 0
                        row = box.row(align=True)
                        row.operator("my.rim_groups", text="", icon='PREFERENCES')
                        row.prop(active_strip, "rim_light", text="Rim Light", slider=True)
                        if active_strip.rim_is_recording:
                            row.alert = 1
                        else:
                            row.alert = 0
                        row.operator("my.focus_rim_one", text="", icon='EVENT_F1')
                        row.operator("my.focus_rim_two", text="", icon='EVENT_F2')
                        row.enabled = 0
                        row.operator("my.focus_rim_three", text="", icon='EVENT_F3')
                        row.enabled = 1
                        row.operator("my.focus_rim_four", text="", icon='EVENT_F4')
                        row.prop(active_strip, "rim_is_recording", text="", icon='REC')
                        row.alert = 0
                        row = box.row(align=True)
                        row.operator("my.fill_groups", text="", icon='PREFERENCES')
                        row.prop(active_strip, "fill_light", text="Fill Light", slider=True)
                        if active_strip.fill_is_recording:
                            row.alert = 1
                        else:
                            row.alert = 0
                        row.operator("my.focus_fill_one", text="", icon='EVENT_F1')
                        row.operator("my.focus_fill_two", text="", icon='EVENT_F2')
                        row.operator("my.focus_fill_three", text="", icon='EVENT_F3')
                        row.operator("my.focus_fill_four", text="", icon='EVENT_F4')
                        row.prop(active_strip, "fill_is_recording", text="", icon='REC')
                        row.alert = 0
                        if scene.using_gels_for_cyc:
                            row = box.row(align=True)
                            row.operator("my.gel_one_groups", text="", icon='PREFERENCES')
                            row.prop(active_strip, "background_light_one", text="Cyc 1", slider=True)
                            row.prop(active_strip, "background_light_two", text="Cyc 2", slider=True)
                            row.prop(active_strip, "background_light_three", text="Cyc 3", slider=True)
                            row.prop(active_strip, "background_light_four", text="Cyc 4", slider=True)
                        else:
                            row = box.row(align=True)
                            row.operator("my.gel_one_groups", text="", icon='PREFERENCES')
                            row.prop(active_strip, "background_light_one", text="Cyclorama", slider=True)
                            if active_strip.cyc_is_recording:
                                row.alert = 1
                            else:
                                row.alert = 0
                            row.operator("my.focus_cyc_one", text="", icon='COLORSET_01_VEC')
                            row.operator("my.focus_cyc_two", text="", icon='COLORSET_02_VEC')
                            row.operator("my.focus_cyc_three", text="", icon='COLORSET_03_VEC')
                            row.operator("my.focus_cyc_four", text="", icon='COLORSET_04_VEC')
                            row.operator("my.focus_cyc_five", text="", icon='COLORSET_05_VEC')
                            row.operator("my.focus_cyc_six", text="", icon='COLORSET_06_VEC')
                            row.operator("my.focus_cyc_seven", text="", icon='COLORSET_07_VEC')
                            row.operator("my.focus_cyc_eight", text="", icon='COLORSET_08_VEC')
                            row.prop(active_strip, "cyc_is_recording", text="", icon='REC')
                            row.alert = 0
                        row = box.row(align=True)
                        row.operator("my.texture_groups", text="", icon='PREFERENCES')
                        row.prop(active_strip, "texture_light", text="Texture", slider=True)
                        if active_strip.texture_is_recording:
                            row.alert = 1
                        else:
                            row.alert = 0
                        row.operator("my.focus_texture_one", text="", icon='COLORSET_01_VEC')
                        row.operator("my.focus_texture_two", text="", icon='COLORSET_02_VEC')
                        row.operator("my.focus_texture_three", text="", icon='COLORSET_03_VEC')
                        row.operator("my.focus_texture_four", text="", icon='COLORSET_04_VEC')
                        row.operator("my.focus_texture_five", text="", icon='COLORSET_05_VEC')
                        row.operator("my.focus_texture_six", text="", icon='COLORSET_06_VEC')
                        row.operator("my.focus_texture_seven", text="", icon='COLORSET_07_VEC')
                        row.operator("my.focus_texture_eight", text="", icon='COLORSET_08_VEC')
                        row.prop(active_strip, "texture_is_recording", text="", icon='REC')
                        row.alert = 0
                        row = box.row(align=True)
                        row.operator("my.band_groups", text="", icon='PREFERENCES')
                        row.prop(active_strip, "band_light", text="Band Light", slider=True)
                        if active_strip.band_is_recording:
                            row.alert = 1
                        else:
                            row.alert = 0
                        row.operator("my.focus_band_one", text="", icon='COLORSET_01_VEC')
                        row.operator("my.focus_band_two", text="", icon='COLORSET_02_VEC')
                        row.operator("my.focus_band_three", text="", icon='COLORSET_03_VEC')
                        row.operator("my.focus_band_four", text="", icon='COLORSET_04_VEC')
                        row.operator("my.focus_band_five", text="", icon='COLORSET_05_VEC')
                        row.operator("my.focus_band_six", text="", icon='COLORSET_06_VEC')
                        row.operator("my.focus_band_seven", text="", icon='COLORSET_07_VEC')
                        row.operator("my.focus_band_eight", text="", icon='COLORSET_08_VEC')
                        row.prop(active_strip, "band_is_recording", text="", icon='REC')
                        row.alert = 0
                        row = box.row(align=True)
                        row.operator("my.accent_groups", text="", icon='PREFERENCES')
                        row.prop(active_strip, "accent_light", text="Accent Light", slider=True)
                        if active_strip.accent_is_recording:
                            row.alert = 1
                        else:
                            row.alert = 0
                        row.operator("my.focus_accent_one", text="", icon='COLORSET_01_VEC')
                        row.operator("my.focus_accent_two", text="", icon='COLORSET_02_VEC')
                        row.operator("my.focus_accent_three", text="", icon='COLORSET_03_VEC')
                        row.operator("my.focus_accent_four", text="", icon='COLORSET_04_VEC')
                        row.operator("my.focus_accent_five", text="", icon='COLORSET_05_VEC')
                        row.operator("my.focus_accent_six", text="", icon='COLORSET_06_VEC')
                        row.operator("my.focus_accent_seven", text="", icon='COLORSET_07_VEC')
                        row.operator("my.focus_accent_eight", text="", icon='COLORSET_08_VEC')
                        row.prop(active_strip, "accent_is_recording", text="", icon='REC')
                        row.alert = 0
                        box.separator()
                        row = box.row(align=True)
                        row.operator("my.energy_groups", text="", icon='PREFERENCES')
                        row.prop(active_strip, "energy_light", text="Energy Intensity", slider=True)
                        row = box.row(align=True)
                        row.operator("my.stop_effect", text="", icon='CANCEL')
                        if active_strip.cue_builder_effect_id == "1":
                            row.alert = 1
                        row.operator("my.focus_energy_one", text="", icon='SHADERFX')
                        row.alert = 0
                        if active_strip.cue_builder_effect_id == "2":
                            row.alert = 1
                        row.operator("my.focus_energy_two", text="", icon='SHADERFX')
                        row.alert = 0
                        if active_strip.cue_builder_effect_id == "3":
                            row.alert = 1
                        row.operator("my.focus_energy_three", text="", icon='SHADERFX')
                        row.alert = 0
                        if active_strip.cue_builder_effect_id == "4":
                            row.alert = 1
                        row.operator("my.focus_energy_four", text="", icon='SHADERFX')
                        row.alert = 0
                        if active_strip.cue_builder_effect_id == "5":
                            row.alert = 1
                        row.operator("my.focus_energy_five", text="", icon='SHADERFX')
                        row.alert = 0
                        if active_strip.cue_builder_effect_id == "6":
                            row.alert = 1
                        row.operator("my.focus_energy_six", text="", icon='SHADERFX')
                        row.alert = 0
                        row.prop(active_strip, "energy_speed", text="Speed", slider=True)
                        row.prop(active_strip, "energy_scale", text="Scale", slider=True)
                        
                ###############
                # FLASH STRIPS
                ###############        
                if console_context == "flash":
                    box = column.box()  
                    row = box.row()
                    row.prop(scene, "examples_panel_toggle", icon="TRIA_DOWN" if scene.examples_panel_toggle else "TRIA_RIGHT", icon_only=True, emboss=False)
                    row.label(text="Examples")
                    if scene.examples_panel_toggle:
                        row = box.row()
                        row.label(text="Type in what feels natural.")
                        row = box.row()
                        row.label(text='"1" becomes "Channel 1 at Full')
                        row = box.row()
                        row.label(text='"g1cp6" becomes "Group 1 Color_Palette 6')
                        row = box.row()
                        row.label(text='"136 45" becomes "Channel 136 at 45')
                        row = box.row()
                        row.label(text='"1 at full", "1 100"  "1 full", "group 14, 15 36"')
                        row = box.row()
                        row.label(text='"1 at color palette 4", "1 cp 4", "group 14-17 ip 2"')
                        row = box.row()
                        row.label(text='"sub 1 full", "submaster 3 75", "sub 1,3,4,7-10 75"')
                    box = column.box()
                    row = box.row()
                    row.prop(active_strip, "flash_using_nodes", text="Use Nodes" if not active_strip.flash_using_nodes else "Using Nodes", slider=True, icon='NODETREE')
                    row = box.row()
                    if active_strip.flash_using_nodes:
                        row.enabled = False
                    row = box.label(text="Flash Up: " + active_strip.flash_input_background)
                    row = box.row()
                    if active_strip.flash_using_nodes:
                        row.enabled = False
                    row.prop(active_strip, "flash_input")
                    row = box.row()
                    if active_strip.flash_using_nodes:
                        row.enabled = False
                    row = box.label(text="Flash Down: " + active_strip.flash_down_input_background)
                    row = box.row()
                    if active_strip.flash_using_nodes:
                        row.enabled = False
                    row.prop(active_strip, "flash_down_input")
                    row = box.separator()
                    row = box.row()
                    row.enabled = True
                    row.operator("my.flash_macro_search", text="", icon='VIEWZOOM')
                    row.prop(active_strip, "start_flash_macro_number", text="M 1")
                    row.prop(active_strip, "end_flash_macro_number", text="M 2")
                    row.prop(active_strip, "flash_bias", text="Bias", slider=True)
                    row.operator("my.build_flash_macros", text="", icon_value=orb.icon_id)
                    row = box.row()
                    if active_strip.flash_bias > 0:
                        row.label(text="Bias: Flash will come in slower and go out faster.")
                    if active_strip.flash_bias < 0:
                        row.label(text="Bias: Flash will come in faster and go out slower.")
                    if active_strip.flash_bias == 0:
                        row.label(text="Bias: Flash will come in and go out at same speed.")
            
                ##################
                # ANIMATION STRIPS
                ##################                       
                if console_context == "animation":
                    box = column.box()
                    box.separator()
                    row = box.row(align=True)
                    row.operator("my.clear_intensity", icon='CANCEL')
                    row.prop(active_strip, "intensity_prefix", text="")
                    col = box.row(align=True)
                    row.prop(active_strip, "osc_intensity", text="Intensity", slider=True)
                    row.operator("my.keyframe_intensity", icon='KEYTYPE_KEYFRAME_VEC')
                    row.operator("my.view_graph", icon='IPO_BEZIER')
                    row = box.separator()
                    row = box.row(align=True)
                    row.operator("my.clear_red", icon='CANCEL')
                    row.prop(active_strip, "red_prefix", text="")
                    row.label(text="")
                    row = box.row(align=True)
                    row.operator("my.clear_green", icon='CANCEL')
                    row.prop(active_strip, "green_prefix", text="")
                    row.prop(active_strip, "osc_color", text="")
                    row.operator("my.keyframe_color", icon='KEYTYPE_KEYFRAME_VEC')
                    row.operator("my.view_graph", icon='IPO_BEZIER')
                    row = box.row(align=True)
                    row.operator("my.clear_blue", icon='CANCEL')
                    row.prop(active_strip, "blue_prefix", text="")
                    row.label(text="")
                    row = box.separator()
                    if not active_strip.use_paths:
                        row = box.row(align=True)
                        row.operator("my.clear_pan", icon='CANCEL')
                        row.prop(active_strip, "use_paths", text="", icon='CURVE_BEZCURVE')
                        row.prop(active_strip, "pan_prefix", text="")
                        row.prop(active_strip, "osc_pan", text="Pan", slider=True)
                        row.operator("my.keyframe_pan", icon='KEYTYPE_KEYFRAME_VEC')
                        row.operator("my.view_graph", icon='IPO_BEZIER')
                        row = box.row(align=True)
                        row.operator("my.clear_tilt", icon='CANCEL')
                        row.prop(active_strip, "use_paths", text="", icon='CURVE_BEZCURVE')
                        row.prop(active_strip, "tilt_prefix", text="")
                        row.prop(active_strip, "osc_tilt", text="Tilt", slider=True)
                        row.operator("my.keyframe_tilt", icon='KEYTYPE_KEYFRAME_VEC')
                        row.operator("my.view_graph", icon='IPO_BEZIER')
                    else:
                        row = box.row(align=True)
                        row.operator("my.clear_pan", icon='CANCEL')
                        row.alert = 1
                        row.prop(active_strip, "use_paths", text="", icon='CURVE_BEZCURVE')
                        row.alert = 0
                        row.prop(active_strip, "pan_prefix", text="")
                        row.operator("my.clear_tilt", icon='CANCEL')
                        row.alert = 1
                        row.prop(active_strip, "use_paths", text="", icon='CURVE_BEZCURVE')
                        row.alert = 0
                        row.prop(active_strip, "tilt_prefix", text="")
                        row = box.row(align=True)
                        row.prop_search(active_strip, "selected_light", bpy.data, "objects", text="", icon='LIGHT_SPOT')
                    row = box.separator()
                    row = box.row(align=True)
                    row.operator("my.clear_zoom", icon='CANCEL')
                    row.prop(active_strip, "zoom_prefix", text="")
                    row = box.row(align=True)
                    row.operator("my.reset_zoom_range", icon='X')
                    row.operator("my.set_min_zoom", icon='REMOVE')
                    row.prop(active_strip, "osc_zoom", text="Custom 1", slider=True)
                    row.operator("my.set_max_zoom", icon='ADD')
                    row.operator("my.keyframe_zoom", icon='KEYTYPE_KEYFRAME_VEC')
                    row.operator("my.view_graph", icon='IPO_BEZIER')
                    row = box.separator()
                    row = box.row(align=True)
                    row.operator("my.clear_iris", icon='CANCEL')
                    row.prop(active_strip, "iris_prefix", text="")
                    row = box.row(align=True)
                    row.operator("my.reset_iris_range", icon='X')
                    row.operator("my.set_min_iris", icon='REMOVE')
                    row.prop(active_strip, "osc_iris", text="Custom 2", slider=True)
                    row.operator("my.set_max_iris", icon='ADD')
                    row.operator("my.keyframe_iris", icon='KEYTYPE_KEYFRAME_VEC')
                    row.operator("my.view_graph", icon='IPO_BEZIER')
                    row = box.separator()
                    row = box.row(align=True)
                    row.operator("my.replace_button", text="Replace * with:")
                    row.prop(scene, "replacement_value", text='', icon='FILE_PARENT')
                    if scene.auto_update_replacement:
                        row.alert = 1
                    row.prop(scene, "auto_update_replacement", text="", icon="LINKED")
                    row.alert = 0
                    row.operator("my.add_strip_operator", text="", icon='ADD')
                    row = box.row(align=True)
                    row.operator("my.record_preset", text="Store Preset", icon='NLA_PUSHDOWN')
                    row.operator("my.load_preset", text="Load Preset", icon='FILE_PARENT')
                    row = box.separator()
                    box = column.box()  
                    row = box.row()
                    row.prop(active_strip, "paths_panel_toggle", icon="TRIA_DOWN" if active_strip.paths_panel_toggle else "TRIA_RIGHT", icon_only=True, emboss=False)
                    row.label(text="Motion Paths Help", icon='CURVE_BEZCURVE')
                    if active_strip.paths_panel_toggle:
                        row = box.row(align=True)
                        row.label(text="Motion paths can allow you to make a mover")
                        row = box.row()
                        row.label(text="draw a unicorn. Use it to track mover motion")
                        row = box.row()
                        row.label(text="to any bezier path. For it to work, you")
                        row = box.row(align=True)
                        row.label(text="must create a light, a path, and an empty")
                        row = box.row()
                        row.label(text="inside 3D view. Set the empty to follow")
                        row = box.row()
                        row.label(text="the path and set the light to track the")
                        row = box.row(align=True)
                        row.label(text="empty. Then use 'Offset' to move the empty")
                        row = box.row()
                        row.label(text="along the path. 'Track To' constraint should")
                        row = box.row()
                        row.label(text="usually be set to -Z for To and Y for Up.")
                        row = box.row(align=True)
                        row.label(text="'Follow Path' constraint should usually be set")
                        row = box.row()
                        row.label(text="to Y for Forward and Z for Up. These settings")
                        row = box.row()
                        row.label(text="may vary. Mess with it until it works. Moderate")
                        row = box.row(align=True)
                        row.label(text="level of basic Blender experience is recommended")
                        row = box.row()
                        row.label(text="to use this feature without pain and swearing.")
                        row = box.row(align=True)
                        row.label(text="Look for Blender tutorials online or ask")
                        row = box.row()
                        row.label(text="Alva Theaters for help if needed.")
                        row = box.row(align=True)
                        row.label(text="Alva Theaters help email: help@alvatheaters.com")
                        row = box.row(align=True)
                        row.label(text="For venting frustration: thisisdumb@alvatheaters.com")
                    box = column.box()
                    row = box.row()
                    row.prop(scene, "bake_panel_toggle", icon="TRIA_DOWN" if scene.bake_panel_toggle else "TRIA_RIGHT", icon_only=True, emboss=False)
                    row.label(text="Create Qmeo", icon='FILE_MOVIE')
                    if scene.bake_panel_toggle:
                        row = box.row(align=True)
                        row.operator("my.delete_animation_cue_list_operator", text="", icon='CANCEL')
                        row.prop(active_strip, "animation_cue_list_number", text="Cue List")
                        row = box.row(align=True)
                        row.operator("my.delete_animation_event_list_operator", text="", icon='CANCEL')
                        row.operator("my.stop_animation_clock_operator", text="", icon='PAUSE')
                        row.prop(active_strip, "animation_event_list_number", text="Event List")
                        row = box.row()
                        row.operator("my.bake_fcurves_to_cues_operator", text="Create Qmeo", icon_value=orb.icon_id)
                        row = box.row()
                        row.operator("my.rerecord_cues_operator", text="Re-record Cues", icon_value=orb.icon_id)
                        box.separator()
                        row = box.row()
                        row.prop(active_strip, "execute_animation_on_cue_number", text='"Enable" Cue #')
                        row = box.row()
                        row.prop(active_strip, "execute_animation_with_macro_number", text="With Macro #")
                        row.operator("my.execute_animation_on_cue_operator", icon_value=orb.icon_id)
                        box.separator()
                        row = box.row()
                        row.prop(active_strip, "disable_animation_on_cue_number", text='"Disable" Cue #')
                        row = box.row()
                        row.prop(active_strip, "disable_animation_with_macro_number", text="With Macro #")
                        row.operator("my.disable_animation_on_cue_operator", icon_value=orb.icon_id)
                        box.separator()
                      
                ################
                # TRIGGER STRIPS
                ################                        
                if console_context == "trigger":
                    box = column.box()
                    box.separator()
                    row = box.row()
                    split = row.split(factor=0.25)
                    split.label(text="Trigger Prefix:")
                    split.prop(active_strip, "trigger_prefix", text="")
                    row = box.separator()
                    row = box.row()
                    split = row.split(factor=0.35)
                    split.label(text="Strip Start Argument:")
                    split.prop(active_strip, "osc_trigger", text="")
                    row = box.row()
                    split = row.split(factor=0.35)
                    split.label(text="Strip End Argument:")
                    split.prop(active_strip, "osc_trigger_end", text="")
                    row = box.row()
                    box = column.box()
                    row = box.row()
                    row.label(text="Add offset friends below:")
                    row = box.row()
                    row.prop(active_strip, "friend_list", text="")
                    
            else:
                print("Alva Context:", alva_context)
                row = column.row()
                row.label(text="No active color strip.")
                return           
                          
            if not scene.bake_panel_toggle and console_context != "animation":
                box.separator()
            row = column.row(align=True)
            row.operator("my.bump_left_five", icon='BACK')
            row.operator("my.bump_left_one", icon='BACK')
            row.operator("my.bump_up", icon='TRIA_UP')
            row.operator("my.bump_down", icon='TRIA_DOWN')
            row.operator("my.bump_right_one", icon='FORWARD')
            row.operator("my.bump_right_five", icon='FORWARD')
            return
        

class AlvaVideoPanel(bpy.types.Panel):
    bl_label = "Video"
    bl_idname = "ALVA_PT_video_panel"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Alva Sorcerer'

    def draw(self, context):
        if context.scene:
            layout = self.layout
            scene = context.scene
            layout.label(text="Coming by end of 2024: Animate PTZ cameras.")
    
        
class AlvaAudioPanel(bpy.types.Panel):
    bl_label = "Audio"
    bl_idname = "ALVA_PT_audio_panel"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Alva Sorcerer'

    def draw(self, context):
        if context.scene:
            layout = self.layout
            scene = context.scene
            column = layout.column(align=True)
            row = column.row()
            if hasattr(scene, "sequence_editor") and scene.sequence_editor:
                sequence_editor = scene.sequence_editor
                if hasattr(sequence_editor, "active_strip") and sequence_editor.active_strip:
                    active_strip = sequence_editor.active_strip
                    if active_strip.type == 'SOUND':
                        row.label(text="Select whether strip will produce or receive sound.")
                        column.separator()
                        row = column.row()
                        row.prop(active_strip, "audio_type_enum", text="")
                        if active_strip.audio_type_enum == "option_object":
                            column.separator()
                            row = column.row()
                            row.label(text="Select an empty in 3D view.")
                            row.prop_search(active_strip, "selected_empty", bpy.data, "objects", text="", icon='EMPTY_DATA')
                            column.separator()
                            row = column.row()
                            row.prop(active_strip, "audio_object_size", text="Size", icon='DRIVER_DISTANCE', slider=True)
                            column.separator()
                            row = column.row()
                            row.alert = active_strip.audio_object_activated
                            row.prop(active_strip, "audio_object_activated", text="Activate Object" if not active_strip.audio_object_activated else "Audio Object Active", toggle=True)
                            column.separator()
                            row = column.row()
                            row.operator("seq.bake_audio_operator", text="Bake Audio (Scene)")
                            layout.separator()
                        elif active_strip.audio_type_enum == "option_speaker":
                            column.separator()
                            row = column.row()
                            row.label(text="Select a speaker in 3D view.")
                            row.prop_search(active_strip, "selected_speaker", bpy.data, "objects", text="", icon='SPEAKER')
                            column.separator()
                            row = column.row()
                            row.prop(active_strip, "int_mixer_channel", text="Fader #:")
                            row.prop(active_strip, "speaker_sensitivity", text="Sensitivity:", slider=True)
                            layout.separator()
                            row = layout.row()
                            row.operator("seq.bake_audio_operator", text="Bake Audio (Scene)")
                            row = layout.row()
                            row.operator("seq.solo_track_operator", text="Solo Track")
                            row.operator("seq.export_audio_operator", text="Export Channel")
                            layout.separator()
                            box = layout.box()
                            row = box.row()
                            row.label(text="Volume Monitor (Read-only)")
                            counter = 0
                            for strip in sequence_editor.sequences:
                                if strip.type == 'SOUND':
                                    if hasattr(strip, "selected_speaker") and strip.selected_speaker is not None:
                                        label = strip.selected_speaker.name
                                        row = box.row()
                                        row.enabled = False  # Use False instead of 0 for clarity
                                        row.prop(strip, "dummy_volume", text=f"{label} Volume", slider=True)
                                        counter += 1
                            if counter == 0:
                                row = box.row()
                                row.label(text="No participating speaker strips found.")
                            box.separator()
                            row = box.row()
                            row.label(text="OSC address for audio mixer:")
                            row = box.row()
                            row.prop(scene, "audio_osc_address", text="")
                            row = box.row()
                            row.label(text="OSC argument for audio mixer:")
                            row = box.row()
                            row.prop(scene, "audio_osc_argument", text="")
                            box.separator()
                            row = box.row()
                            row.prop(scene, "str_audio_ip_address", text="IP Address")
                            row = box.row()
                            row.label(text="Port:")
                            row.prop(scene, "int_audio_port", text="")
                                       
                        
class TrackingPanel(bpy.types.Panel):
    bl_label = "Strips"
    bl_idname = "ALVA_PT_tracking_panel"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Alva Sorcerer'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        if hasattr(scene, "sequence_editor") and scene.sequence_editor:
            sequence_editor = scene.sequence_editor
            if hasattr(sequence_editor, "active_strip") and sequence_editor.active_strip:
                active_strip = sequence_editor.active_strip
                alva_context, console_context = determine_contexts(sequence_editor, active_strip)
            else:
                alva_context = "none_relevant"
                console_context = "none"
            column = layout.column(align=True)
            
            if alva_context == "only_color":
                row = column.row(align=True)
                if scene.is_filtering_left == True:
                    row.alert = 1
                    row.prop(scene, "is_filtering_left", icon='FILTER')
                    row.alert = 0
                elif scene.is_filtering_left == False:
                    row.alert = 0
                    row.prop(scene, "is_filtering_left", icon='FILTER')
                row.operator("my.select_similar", text="Select Magnetic:") 
                if scene.is_filtering_right == True:
                    row.alert = 1
                    row.prop(scene, "is_filtering_right", icon='FILTER')
                    row.alert = 0
                elif scene.is_filtering_right == False:
                    row.alert = 0
                    row.prop(scene, "is_filtering_right", icon='FILTER')
                row = column.row(align=True)
                row.prop(scene, "color_is_magnetic", text="", icon='SNAP_OFF' if not scene.color_is_magnetic else 'SNAP_ON')
                row.prop(active_strip, "color", text="")
                row.operator("my.copy_color_operator", text="", icon='FILE')
                row.operator("my.color_trigger", text="", icon='RESTRICT_SELECT_OFF')
                row = column.row(align=True)
                row.prop(scene, "strip_name_is_magnetic", text="", icon='SNAP_OFF' if not scene.strip_name_is_magnetic else 'SNAP_ON')
                row.prop(active_strip, "name", text="")  
                row.operator("my.copy_strip_name_operator", text="", icon='FILE')
                row.operator("my.strip_name_trigger", text="", icon='RESTRICT_SELECT_OFF')
                row = column.row(align=True)
                row.prop(scene, "channel_is_magnetic", text="", icon='SNAP_OFF' if not scene.channel_is_magnetic else 'SNAP_ON')
                row.prop(active_strip, "channel", text_ctxt="Channel: ")
                row.operator("my.copy_channel_operator", text="", icon='FILE')
                row.operator("my.channel_trigger", text="", icon='RESTRICT_SELECT_OFF')          
                row = column.row(align=True)
                row.prop(scene, "duration_is_magnetic", text="", icon='SNAP_OFF' if not scene.duration_is_magnetic else 'SNAP_ON')
                row.prop(active_strip, "frame_final_duration", text="Duration")
                row.operator("my.copy_duration_operator", text="", icon='FILE')
                row.operator("my.duration_trigger", text="", icon='RESTRICT_SELECT_OFF')
                row = column.row(align=True)
                row.prop(scene, "start_frame_is_magnetic", text="", icon='SNAP_OFF' if not scene.start_frame_is_magnetic else 'SNAP_ON')
                row.prop(active_strip, "frame_start", text="Start Frame")
                row.operator("my.start_frame_jump", text="", icon='PLAY')
                row.operator("my.copy_start_frame_operator", text="", icon='FILE')
                row.operator("my.start_frame_trigger", text="", icon='RESTRICT_SELECT_OFF')
                row = column.row(align=True)
                row.prop(scene, "end_frame_is_magnetic", text="", icon='SNAP_OFF' if not scene.end_frame_is_magnetic else 'SNAP_ON')
                row.prop(active_strip, "frame_final_end", text="End Frame")
                row.operator("my.end_frame_jump", text="", icon='PLAY')
                row.operator("my.copy_end_frame_operator", text="", icon='FILE')
                row.operator("my.end_frame_trigger", text="", icon='RESTRICT_SELECT_OFF')
                row = column.row(align=True)
                row.operator("my.copy_above_to_selected", text="Copy Various to Selected", icon='FILE')
                column.separator()
                if scene.i_know_the_shortcuts == False:
                    row = column.row(align=True)
                    row.operator("my.alva_extrude", text="Extrude")
                    row = column.row(align=True)
                    row.operator("my.alva_scale", text="Scale")
                    row = column.row(align=True)
                    row.operator("my.alva_grab", text="Grab")
                    row = column.row(align=True)
                    row.operator("my.alva_grab_x", text="Grab X")
                    row.operator("my.alva_grab_y", text="Grab Y")
                    row = column.row(align=True)
                    row.operator("my.cut_operator", text="Cut")
                    row = column.row(align=True)
                    row.operator("my.assign_to_channel_operator", text="Assign to Channel")
                row = column.row(align=True)
                row.prop(scene, "i_know_the_shortcuts", text="I know the shortcuts.")
                selected_color_strips = []
                selected_strips = []
                for strip in sequence_editor.sequences:
                    if strip.select:
                        selected_strips.append(strip)
                        if strip.type == 'COLOR':
                            selected_color_strips.append(strip)
                if len(selected_color_strips) > 1:
                    column.separator()
                    column.separator()
                    row = column.row(align=True)
                    row.prop(scene, "offset_value", text="Offset in BPM")
                    row.operator("my.add_offset", text="", icon='CENTER_ONLY')
                    column.separator()

            elif alva_context == "only_sound":
                row = column.row(align=True)
                row.operator("my.mute_button", icon='HIDE_OFF' if not active_strip.mute else 'HIDE_ON')
                row.prop(active_strip, "name", text="")
                row = column.row(align=True)
                row.prop(active_strip, "song_bpm_input", text="Beats per minute (BPM)")
                row = column.row(align=True)
                row.prop(active_strip, "beats_per_measure", text="Beats per measure")
                row = column.row(align=True)
                row.prop(active_strip, "song_bpm_channel", text="Generate on channel")
                row.operator("my.generate_strips", text="", icon='COLOR')
                column.separator()
                row = column.row(align=True)
                row.operator("my.start_end_frame_mapping", icon='PREVIEW_RANGE')
                row = column.row(align=True)
                row.operator("my.time_map", text="Zero Timecode", icon='TIME')
                column.separator()
                row = column.row(align=True)
                row.prop(active_strip, "show_waveform", slider=True)
                
            elif alva_context == "one_video_one_audio":
                selected_sound_strips = []
                selected_video_strips = []
                selected_strips = []
                if sequence_editor:
                    for strip in sequence_editor.sequences:
                        if strip.select:
                            selected_strips.append(strip)
                            if strip.type == 'SOUND':
                                selected_sound_strips.append(strip)
                            elif strip.type == 'MOVIE':
                                selected_video_strips.append(strip)
                selected_sound_strip = selected_sound_strips[0]
                selected_video_strip = selected_video_strips[0]
                row = column.row(align=True)
                row.operator("my.mute_button", icon='HIDE_OFF' if not active_strip.mute else 'HIDE_ON')
                row.prop(active_strip, "name", text="")
                row = column.row(align=True)
                if selected_sound_strip.frame_start != selected_video_strip.frame_start or selected_sound_strip.frame_final_duration != selected_video_strip.frame_final_duration:
                    row.alert = 1
                    row.operator("my.sync_video")
                row = column.row(align=True)
                row.operator("my.start_end_frame_mapping", icon='PREVIEW_RANGE')
                row = column.row(align=True)
                row.operator("my.time_map", icon='TIME')
        
            else:
                row = column.row(align=True)            
                row.prop(scene, "channel_selector", text="Channel")
                row.operator("my.select_channel", text="", icon='RESTRICT_SELECT_OFF')           
                row = column.row(align=True)
                row.prop(scene, "generate_quantity", text="Quantity")
                row = column.row(align=True)
                if scene.generate_quantity > 1:
                    row.prop(scene, "normal_offset", text="Offset by")
                row = column.row(align=True)
                row.operator("my.add_color_strip", icon='COLOR')        
                column.separator()
                return
                
                
class ButtonsPanel(bpy.types.Panel):
    bl_label = "Tools"  # not visible
    bl_idname = "ALVA_PT_sequencer_tool_panel"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_options = {'HIDE_HEADER'}
    
    def draw(self, context):
        pcoll = preview_collections["main"]
        orb = pcoll["orb"]
        
        layout = self.layout
        region_width = context.region.width

        num_columns = 2 if region_width > 150 and region_width < 200 else 1  

        flow = layout.grid_flow(row_major=True, columns=num_columns, even_columns=True, even_rows=False, align=True)

        # Add operators to the grid layout
        #flow.alignment = 'LEFT'
        flow.scale_y = 2
        
        
        flow.operator("my.add_macro", icon='REC', text="Macro" if region_width > 200 else "")
        flow.operator("my.add_cue", icon='PLAY', text="Cue" if region_width > 200 else "")
        flow.operator("my.add_flash", icon='LIGHT_SUN', text="Flash" if region_width > 200 else "")
        flow.operator("my.add_animation", icon='IPO_BEZIER', text="Animation" if region_width > 200 else "")
        if bpy.context.scene.triggers_enabled:
            flow.operator("my.add_trigger", icon='SETTINGS', text="Trigger" if region_width > 200 else "")
        flow.separator()
        flow.operator("seq.render_strips_operator", icon_value=orb.icon_id, text="Render" if region_width > 200 else "")
        flow.operator("my.add_strip_operator", icon='ADD', text="Add Strip" if region_width > 200 else "", emboss=True)
        flow.operator("my.go_to_cue_out_operator", icon='GHOST_ENABLED', text="Cue 0" if region_width > 200 else "")
        flow.operator("my.displays_operator", icon='MENU_PANEL', text="Displays" if region_width > 200 else "")
        flow.operator("my.about_operator", icon='INFO', text="About" if region_width > 200 else "")
        flow.operator("my.copy_above_to_selected", icon='COPYDOWN', text="Disable Clocks" if region_width > 200 else "")
        flow.operator("my.disable_all_clocks_operator", icon='MOD_TIME', text="Disable Clocks" if region_width > 200 else "")
        flow.operator("seq.show_sequencer_settings", icon='PREFERENCES', text="Settings" if region_width > 200 else "")

'''Need to figure out where to put this now that the other stuff has been moved to toolbar'''
#        column.separator()
#        column.separator()
#        row = column.row(align=True)
#        if scene.reset_color_palette:
#            row.alert = 1
#        row.prop(scene, "reset_color_palette", text="", icon='FORWARD')
#        row.alert = 0
#        row.prop(scene, "color_palette_number", text="CP #")
#        if scene.preview_color_palette:
#            row.alert = 1
#        row.prop(scene, "preview_color_palette", text="", icon='LINKED')
#        row.alert = 0
#        row.prop(scene, "color_palette_color", text="")
#        row.prop(scene, "color_palette_name", text="")
#        row.operator("my.color_palette_operator", icon_value=orb.icon_id)
            
            
class SettingsPanel(bpy.types.Panel):
    bl_label = "Alva Settings"
    bl_idname = "ALVA_PT_settings_panel"
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Alva Sorcerer'

    def draw(self, context):
        if context.scene:
            layout = self.layout
            scene = context.scene
            sequence_editor = context.scene.sequence_editor
            column = layout.column(align=True)
            row = column.row()
            
            if not context.scene.animation_enabled:
                row.label('To enable animation, type, ')
                row = column.row()
                row.label('"I understand that ETC Eos')
                row = column.row()
                row.label('cannot store this data locally')
                row = column.row()
                row.label('and it is not safe to use this bonus') 
                row = column.row()
                row.label('feature during a real show on Eos."')
                row = column.separator()
                row = column.separator()
                row = column.separator()
                row = column.separator()
                row = column.row()
                row.prop(scene, "i_understand_animation", text="")
                row = column.separator()
                row = column.separator()
                row = column.row()
                row.operator("my.enable_animation")
                row = column.separator()
                row = column.separator()
                row = column.separator()
                row = column.separator()
                row = column.separator()
                row = column.separator()
                row = column.separator()
                row = column.separator()
                
            if not context.scene.triggers_enabled:
                row = column.row()
                row.label(text='To enable triggers, type, ')
                row = column.row()
                row.label(text='"I understand this bonus feature is')
                row = column.row()
                row.label(text="unrecordable for Eos. ETC Eos cannot")
                row = column.row()
                row.label(text="store these locally. I should not") 
                row = column.row()
                row.label(text='use this during a real show with Eos."')
                row = column.separator()
                row = column.separator()
                row = column.separator()
                row = column.separator()
                row = column.row()
                row.prop(scene, "i_understand_triggers", text="")
                row = column.separator()
                row = column.separator()
                row = column.row()
                row.operator("my.enable_triggers")
                row = column.separator()
                row = column.separator()
                row = column.separator()
                row = column.separator()
                row = column.separator()
                row = column.separator()
                row = column.separator()
                row = column.separator()
            row = column.row()
            row.prop(context.scene, "is_armed_livemap", slider=True, text="Livemap")
            row = column.separator()
            row = column.separator()
            row = column.row()
            row.prop(context.scene, "sync_timecode", slider=True, text="Sync timecode on console")
            if context.scene.sync_timecode:
                row.prop(context.scene, "timecode_expected_lag", text="Expected lag in frames")
            row = column.separator()
            row = column.separator()
            row = column.row()
            row.prop(context.scene, "is_armed_release", slider=True, text="Add secondary strip on release of O key")    
            row = column.separator()
            row = column.separator()
            pcoll = preview_collections["main"]
            orb = pcoll["orb"]
            row = column.row()
            row.prop(context.scene, "is_armed_turbo", slider=True, text="Orb skips Shift+Update", icon_value=orb.icon_id)
            row = column.row()
            row.prop(context.scene, "orb_finish_snapshot", text="Snapshot after Orb")
            row = column.separator()
            row = column.separator()
            row = column.separator()
            row = column.separator()
            row = column.row()
            row.prop(context.scene, "cue_builder_toggle", slider=True)
            row = column.separator()
            row = column.separator()
            row = column.row()
            row.prop(context.scene, "using_gels_for_cyc", text="Using gels for cyc color", slider=True) 
            row = column.separator()
            row = column.separator()
            row = column.row()
            row.prop(context.scene, "cue_builder_id_offset", text="Cue builder ID offset")
            row = column.separator()
            row = column.separator() 
            row = column.separator()
            row = column.separator()
            row = column.row()
            row.prop(context.scene, "i_know_the_shortcuts", text="I know the keyboard shortcuts",  slider=True)    
            row = column.separator()
            row = column.separator()
            row = column.row()
            row.prop(context.scene, "is_updating_strip_color", text="Update strip color",  slider=True)
            row = column.separator()
            row = column.separator()
            row = column.row()
            row.label(text="Adjust frame rate in a Blender Properties window.")
            row = column.row()
            row.label(text="Frame rate must be a whole number.")
            row = column.separator()
            row = column.separator()
            box = column.box()
            row = box.row()
            row.label(text="Automatically adjust house lights on play/stop:")
            box = column.box()
            row = box.row()
            row.label(text="House OSC Address: ")
            row = box.row()
            row.prop(scene, "house_prefix", text="")
            box.separator()
            row = box.row()
            row.prop(scene, "house_down_on_play", text="House Down on Play", slider=True)
            row = box.row()
            row.prop(scene, "house_down_argument", text="")
            box.separator()
            row = box.row()
            row.prop(scene, "house_up_on_stop", text="House Up on Stop", slider=True)
            row = box.row()
            row.prop(scene, "house_up_argument", text="")
            row = column.separator()
            row = column.separator()
            row = column.row()
            if scene.scene_props.school_mode_enabled:
                row.label(text="Disable school mode:", icon='LOCKED')
            else:
                row.label(text="Enable school mode:", icon='UNLOCKED')
            row = column.row()
            row.prop(scene.scene_props, "school_mode_password", text="")
            column.separator()
            column.separator()
            if not scene.scene_props.school_mode_enabled:
                box = column.box()
                row = box.row()
                row.label(text="Lighting Console OSC RX (Receive) Settings:")
                box = column.box()
                row = box.row()
                row.prop(scene.scene_props, "str_osc_ip_address", text="IP Address")
                row = box.row()
                row.label(text="Port:")
                row.prop(scene.scene_props, "int_osc_port", text="")
                
                
def draw_alva_sequencer_menu(self, layout):
    pcoll = preview_collections["main"]
    orb = pcoll["orb"]
            
    layout = self.layout
    layout.separator()
    layout.label(text="Alva Sorcerer", icon_value=orb.icon_id)
    layout.operator("my.add_macro", text="Macro", icon='REC')
    layout.operator("my.add_cue", text="Cue", icon='PLAY')
    layout.operator("my.add_flash", text="Flash", icon='LIGHT_SUN')
    layout.operator("my.add_animation", text="Animation", icon='IPO_BEZIER')
    if bpy.context.scene.triggers_enabled:
        layout.operator("my.add_trigger", text="Trigger", icon='SETTINGS')
                
                
classes = (
    AlvaConsolePanel,
    AlvaVideoPanel,
    AlvaAudioPanel,
    TrackingPanel,
    ButtonsPanel,
    SettingsPanel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.SEQUENCER_MT_add.append(draw_alva_sequencer_menu)
    
    pcoll = bpy.utils.previews.new()
    preview_collections["main"] = pcoll
    addon_dir = os.path.dirname(__file__)
    pcoll.load("orb", os.path.join(addon_dir, "alva_orb.png"), 'IMAGE')
        
        
def unregister():
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()
    
    bpy.types.SEQUENCER_MT_add.remove(draw_alva_sequencer_menu)
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        

# For development purposes only.
if __name__ == "__main__":
    register()
