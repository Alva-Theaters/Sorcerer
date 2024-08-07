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

from ..ui.common_ui import CommonUI as CommonUI

# Custom icon stuff
import bpy.utils.previews
import os
preview_collections = {}
pcoll = bpy.utils.previews.new()
preview_collections["main"] = pcoll
addon_dir = os.path.dirname(__file__)
pcoll.load("orb", os.path.join(addon_dir, "alva_orb.png"), 'IMAGE')

pcoll = preview_collections["main"]
orb = pcoll["orb"]


class SequencerUI:
    @staticmethod
    def draw_strip_media(self, context, scene, bake_panel=True):
        layout = self.layout
        scene = context.scene
        
        if not hasattr(scene, "sequence_editor") and scene.sequence_editor:
            SequencerUI.draw_intro_header(self, context, None, scene, None, motif_name=False)

        # Check if the sequence editor and active strip exist
        elif hasattr(scene, "sequence_editor") and scene.sequence_editor:
            sequence_editor = scene.sequence_editor
            if hasattr(sequence_editor, "active_strip") and sequence_editor.active_strip:
                active_strip = sequence_editor.active_strip
                alva_context, console_context = SequencerUI.determine_contexts(sequence_editor, active_strip)
            else:
                alva_context = "none_relevant"
                console_context = "none"
                
            column = layout.column(align=True)

            if alva_context == "incompatible_types":
                box = SequencerUI.draw_incompatible_types(self, context, column, scene, active_strip)
        
            elif alva_context == "only_sound":
                box = SequencerUI.draw_only_sound(self, context, column, active_strip)
                
            elif alva_context == "one_video_one_audio":
                box = SequencerUI.draw_one_audio_one_video(self, context, column, scene, active_strip)
                    
            elif alva_context == "none_relevant":
                box = SequencerUI.draw_none_relevant(self, context, sequence_editor, column, scene)

            elif alva_context == "only_color":
                box = SequencerUI.draw_color_header(self, context, column, scene, active_strip, console_context)
                
                if console_context == "macro":
                    SequencerUI.draw_strip_macro(self, context, column, box, active_strip)
             
                elif console_context == "cue":
                    SequencerUI.draw_strip_cue(self, context, column, box, active_strip)
                    if scene.cue_builder_toggle:
                        SequencerUI.draw_cue_builder(self, context, box, scene, active_strip)
    
                elif console_context == "flash":  
                    row = box.row()
                    row.prop(active_strip, "flash_type_enum", expand=0, text="Method")
                    
                    if active_strip.flash_type_enum != 'option_use_controllers':
                        SequencerUI.draw_strip_flash_manual(self, context, box, active_strip)
                    else: SequencerUI.draw_strip_flash_controllers(self, context, box, active_strip)
                    
                    SequencerUI.draw_strip_flash_footer(self, context, box, active_strip)
                   
                elif console_context == "animation":
                    CommonUI.draw_text_or_group_input(self, context, box, active_strip, object=False)
                    CommonUI.draw_parameters(self, context, column, box, active_strip)
                    CommonUI.draw_footer_toggles(self, context, column, active_strip)
                    if bake_panel:
                        box = column.box()
                        SequencerUI.draw_bake_panel(self, context, box, scene, active_strip)

                elif console_context == "offset":
                    SequencerUI.draw_strip_offset(self, context, column, box, active_strip)
                          
                elif console_context == "trigger":
                    SequencerUI.draw_strip_trigger(self, context, column, box, active_strip)
            
            else:
                SequencerUI.draw_add_buttons_row(self, context, column, scene, active_strip, motif_name=False)
                column.separator()
                box = SequencerUI.draw_text_insert(self, context, column, text="No active color strip.")
                return box    
                          
            if not scene.bake_panel_toggle and alva_context == "only_color" and console_context != "animation":
                box.separator()
            
            if alva_context == "only_color":
                SequencerUI.draw_strip_footer(self, context, column)
            else:
                SequencerUI.draw_strip_footer(self, context, box)
            

    @staticmethod
    def draw_add_buttons_row(self, context, column, scene, active_strip, motif_name=False, lighting_icons=False, console_context=None):
        # Motif prefix.
        row = column.row(align=True)
        if lighting_icons:
            strip_type = active_strip.my_settings.motif_type_enum
            row.prop(scene.my_tool, "motif_names_enum", text="", icon='REC' if strip_type == "option_eos_macro" else 'PLAY' if strip_type == "option_eos_cue" else 'OUTLINER_OB_LIGHT' if strip_type == "option_eos_flash" else 'IPO_BEZIER' if strip_type == "option_animation" else 'SETTINGS', icon_only=True)
        else:
            row.prop(scene.my_tool, "motif_names_enum", text="", icon='COLOR', icon_only=True)
        
        if motif_name:
            if active_strip.is_linked and not console_context == "animation":
                row.alert = 1
            row.prop(active_strip, "motif_name", text="")
            row.alert = 0
        
        # Add buttons.
        row.operator("my.add_macro", text="", icon='REC')
        row.operator("my.add_cue", text="", icon='PLAY')
        row.operator("my.add_flash", text="", icon='LIGHT_SUN')
        row.operator("my.add_animation", text="", icon='IPO_BEZIER')
        row.operator("my.add_offset_strip", text="", icon='UV_SYNC_SELECT')
        row.operator("my.add_trigger", text="", icon='SETTINGS')
        

    @staticmethod
    def draw_text_insert(self, context, column, text):
        column.separator()
        box = column.box()
        row = box.row()
        row.label(text=text)
        return box


    '''
    Not refactoring the following 4 functions to make it easy to add
    extra functionality for those contexts later.
    '''


    @staticmethod
    def draw_intro_header(self, context, column, scene, active_strip):
        SequencerUI.draw_add_buttons_row(self, context, column, scene, active_strip)
        column.separator()
        box = SequencerUI.draw_text_insert(self, context, column, text="Welcome to ..")
        return box
        

    @staticmethod
    def draw_incompatible_types(self, context, column, scene, active_strip):
        SequencerUI.draw_add_buttons_row(self, context, column, scene, active_strip)
        column.separator()
        box = SequencerUI.draw_text_insert(self, context, column, text="Incompatible strips selected.")
        return box
    

    @staticmethod
    def draw_one_audio_one_video(self, context, column, scene, active_strip):  
        SequencerUI.draw_add_buttons_row(self, context, column, scene, active_strip)
        column.separator()
        box = SequencerUI.draw_text_insert(self, context, column, text="Format movie with F key.")
        return box
    

    @staticmethod    
    def draw_none_relevant(self, context, sequence_editor, column, scene): 
        SequencerUI.draw_add_buttons_row(self, context, column, scene, None) 
        column.separator()
        box = SequencerUI.draw_text_insert(self, context, column, text="No relevant strips selected.")
        return box
    

    @staticmethod    
    def draw_only_sound(self, context, column, active_strip):
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
        column.separator() ## ?

        row = box.row()
        row.operator("seq.analyze_song", icon='SHADERFX')

        column.separator() ## ?

        row = box.row()
        row.operator("my.generate_text", icon="TEXT")

        box.separator()
        row = box.row(align=True) ## ?
        return box
        

    @staticmethod    
    def draw_color_header(self, context, column, scene, active_strip, console_context):
        SequencerUI.draw_add_buttons_row(self, context, column, scene, active_strip, motif_name=True, lighting_icons=True, console_context=console_context) 
        column.separator()
        box = SequencerUI.draw_color_subheader(self, context, column, active_strip, console_context)
        return box
        

    @staticmethod
    def draw_color_subheader(self, context, column, active_strip, console_context):
        box = column.box()
        row = box.row(align=True)
        row.operator("my.mute_button", icon='HIDE_OFF' if not active_strip.mute else 'HIDE_ON')
        my_settings = active_strip.my_settings
        row.prop(my_settings, "motif_type_enum", expand=True)
        SequencerUI.draw_strip_type_label(console_context, row)
        if console_context != 'animation' and active_strip.motif_name != "":
            if active_strip.is_linked and console_context != "animation":
                row.alert = 1
                row.prop(active_strip, "is_linked", icon='LINKED')
            else:
                row.alert = 0
                row.prop(active_strip, "is_linked", icon='UNLINKED')
        box = column.box()
        return box
    

    def draw_strip_type_label(console_context, row):
        if console_context == 'macro':
            row.label(text="  Macro Strip")
        elif console_context == 'cue':
            row.label(text="  Cue Strip")
        elif console_context == 'flash':
            row.label(text="  Flash Strip")
        elif console_context == 'animation':
            row.label(text="  Animation Strip")
        elif console_context == 'offset':
            row.label(text="  Offset Strip")
        elif console_context == 'trigger':
            row.label(text="  Trigger Strip")


    @staticmethod    
    def draw_strip_macro(self, context, column, box, active_strip):
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
                

    @staticmethod    
    def draw_strip_cue(self, context, column, box, active_strip):
        row = box.row(align=True)  
        row.prop(active_strip, "eos_cue_number", text="Cue #")
        row.operator("my.go_to_cue_out_operator", text="", icon='GHOST_ENABLED')
        if context.scene.cue_builder_toggle:
            row.operator("my.update_builder", text="", icon='FILE_REFRESH')
        row.operator("my.record_cue", text="", icon='REC')
        row.operator("my.sync_cue", icon_value=orb.icon_id)
        box.separator()
        row = box.row(align=True)
        row.prop(active_strip, "background_color", text="")
        row.prop(active_strip, "accent_color", text="")
        

    def draw_builder_row(box, ops_list, id, active_strip, label, alert_flag, is_color=True, record_prop_name=""):
        event_icons = ['EVENT_F1', 'EVENT_F2', 'EVENT_F3', 'EVENT_F4']
        color_icons = ['COLORSET_01_VEC', 'COLORSET_02_VEC', 'COLORSET_03_VEC', 'COLORSET_04_VEC', 
                    'COLORSET_05_VEC', 'COLORSET_06_VEC', 'COLORSET_07_VEC', 'COLORSET_08_VEC']
        row = box.row(align=True)
        row.operator(f"my.{id}_groups", text="", icon='PREFERENCES')
        row.prop(active_strip, f"{id}_light", text=label, slider=True)
        row.alert = alert_flag
        row_icons = color_icons if is_color else event_icons
        for op, icon in zip(ops_list, row_icons):
            row.operator(op, text="", icon=icon)
        
        row.prop(active_strip, record_prop_name, text="", icon='REC')


    @staticmethod    
    def draw_cue_builder(self, context, box, scene, active_strip):
        key_ops = ["my.focus_one", "my.focus_two", "my.focus_three", "my.focus_four"]

        rim_ops = ["my.focus_rim_one", "my.focus_rim_two", "my.focus_rim_three", "my.focus_rim_four"]

        fill_ops = ["my.focus_fill_one", "my.focus_fill_two", "my.focus_fill_three", "my.focus_fill_four"]

        cyc_ops = ["my.focus_cyc_one", "my.focus_cyc_two", "my.focus_cyc_three", "my.focus_cyc_four",
                    "my.focus_cyc_five", "my.focus_cyc_six", "my.focus_cyc_seven", "my.focus_cyc_eight"]
        
        band_ops = ["my.focus_band_one", "my.focus_band_two", "my.focus_band_three", "my.focus_band_four",
                    "my.focus_band_five", "my.focus_band_six", "my.focus_band_seven", "my.focus_band_eight"]
        
        accent_ops = ["my.focus_accent_one", "my.focus_accent_two", "my.focus_accent_three", "my.focus_accent_four",
                    "my.focus_accent_five", "my.focus_accent_six", "my.focus_accent_seven", "my.focus_accent_eight"]
        
        texture_ops = ["my.focus_texture_one", "my.focus_texture_two", "my.focus_texture_three", "my.focus_texture_four",
                    "my.focus_texture_five", "my.focus_texture_six", "my.focus_texture_seven", "my.focus_texture_eight"]
        
        effect_ids = ["1", "2", "3", "4", "5", "6"]

        fx_ops = ["my.focus_energy_one", "my.focus_energy_two", "my.focus_energy_three", "my.focus_energy_four", "my.focus_energy_five", "my.focus_energy_six"]

        # Key, Rim, and Fill rows
        SequencerUI.draw_builder_row(box, key_ops, 'key', active_strip, "Key", active_strip.key_is_recording, is_color=0, record_prop_name="key_is_recording")
        SequencerUI.draw_builder_row(box, rim_ops, 'rim', active_strip, "Rim/Hair", active_strip.rim_is_recording, is_color=0, record_prop_name="rim_is_recording")
        SequencerUI.draw_builder_row(box, fill_ops, 'fill', active_strip, "Fill", active_strip.fill_is_recording, is_color=0, record_prop_name="fill_is_recording")
        
        # Background row
        if scene.using_gels_for_cyc:
            row = box.row(align=True)
            row.operator("my.gel_one_groups", text="", icon='PREFERENCES')
            row.prop(active_strip, "background_light_one", text="Cyc 1", slider=True)
            row.prop(active_strip, "background_light_two", text="Cyc 2", slider=True)
            row.prop(active_strip, "background_light_three", text="Cyc 3", slider=True)
            row.prop(active_strip, "background_light_four", text="Cyc 4", slider=True)
        else:
            SequencerUI.draw_builder_row(box, cyc_ops, 'cyc', active_strip, "Cyclorama", active_strip.cyc_is_recording, is_color=1, record_prop_name="cyc_is_recording")

        # Texture, Band, and Accent rows
        SequencerUI.draw_builder_row(box, texture_ops, 'texture', active_strip, "Texture", active_strip.texture_is_recording, is_color=1, record_prop_name="texture_is_recording")
        SequencerUI.draw_builder_row(box, band_ops, 'band', active_strip, "Band", active_strip.band_is_recording, is_color=1, record_prop_name="band_is_recording")
        SequencerUI.draw_builder_row(box, accent_ops, 'accent', active_strip, "Accent", active_strip.accent_is_recording, is_color=1, record_prop_name="accent_is_recording")

        box.separator()

        # Energy Intensity row
        row = box.row(align=True)
        row.operator("my.energy_groups", text="", icon='PREFERENCES')
        row.prop(active_strip, "energy_light", text="Energy Intensity", slider=True)

        # Effects row
        row = box.row(align=True)
        row.operator("my.stop_effect", text="", icon='CANCEL')
        for effect_id, operator in zip(effect_ids, fx_ops):
            row.alert = active_strip.cue_builder_effect_id == effect_id
            row.operator(operator, text="", icon='SHADERFX')
            row.alert = 0
        row.prop(active_strip, "energy_speed", text="Speed", slider=True)
        row.prop(active_strip, "energy_scale", text="Scale", slider=True)

        
    @staticmethod    
    def draw_strip_flash_manual(self, context, box, active_strip):
        is_manual_enabled = (active_strip.flash_type_enum != 'option_use_nodes')
            
        row = box.row()
        row = box.label(text=f"Flash Up: {active_strip.flash_input_background}")
        row = box.row(align=True)
        row.enabled = is_manual_enabled
        row.prop(active_strip, "flash_input")
        row.operator("my.flash_copy_down", text="", icon='DOWNARROW_HLT')
        
        row = box.row()
        row = box.label(text=f"Flash Down: {active_strip.flash_down_input_background}")
        row = box.row()
        row.enabled = is_manual_enabled
        row.prop(active_strip, "flash_down_input")
        
        row = box.separator()
        

    @staticmethod    
    def draw_strip_flash_controllers(self, context, box, active_strip):

        # Top row
        row = box.row(align=True)
        row.operator("node.home_group", icon='HOME', text="")
        row.operator("node.update_group", icon='FILE_REFRESH', text="")
        ## Use of row.alert logic here is probably redundant per existing Blender UI rules.
        if active_strip.str_manual_fixture_selection == "":
            if not active_strip.selected_group_enum:
                row.alert = 1
            row.prop(active_strip, "selected_group_enum", text="", icon_only=False, icon='LIGHT')
            row.alert = 0
        row.prop(active_strip, "str_manual_fixture_selection", text="")
        row.operator("node.home_group", icon='HOME', text="")
        row.operator("node.update_group", icon='FILE_REFRESH', text="")
        
        # Parameters rows
        row = box.row()
        row.prop(active_strip, "float_flash_intensity_up", slider=True, text="Intensity:")
        row.prop(active_strip, "float_flash_intensity_down", slider=True, text="Intensity:")

        row = box.row()
        row.prop(active_strip, "float_flash_pan_up", slider=True, text="Pan:")
        row.prop(active_strip, "float_flash_pan_down", slider=True, text="Pan:")

        row = box.row()
        row.prop(active_strip, "float_flash_tilt_up", slider=True, text="Tilt:")
        row.prop(active_strip, "float_flash_tilt_down", slider=True, text="Tilt:")

        row = box.row()
        row.prop(active_strip, "float_flash_zoom_up", slider=True, text="Zoom:")
        row.prop(active_strip, "float_flash_zoom_down", slider=True, text="Zoom:")

        row = box.row()
        row.prop(active_strip, "float_flash_iris_up", slider=True, text="Iris:")
        row.prop(active_strip, "float_flash_iris_down", slider=True, text="Iris:")

        row = box.row()
        row.prop(active_strip, "int_flash_gobo_id_up", slider=True, text="Gobo ID:")
        row.prop(active_strip, "int_flash_gobo_id_down", slider=True, text="Gobo ID:")
    

    @staticmethod
    def draw_strip_flash_footer(self, context, box, active_strip):
        '''New goal is to delete as many macro orb buttons as possible and let
           Sorcerer do all that by itself so that the user doesn't have to think 
           about dumb macro numbers or dumb preset numbers. The best part is no
           part. Let's delete this entire process from the user's job description'''
        if not active_strip.flash_type_enum == 'option_use_controllers':
            row = box.row()
            row.enabled = True
            row.operator("my.flash_macro_search", text="", icon='VIEWZOOM')
            row.prop(active_strip, "start_flash_macro_number", text="Up Macro")
            row.prop(active_strip, "end_flash_macro_number", text="Down Macro")
            row.operator("my.build_flash_macros", text="", icon_value=orb.icon_id)
        else: box.separator()

        row = box.row()
        row.prop(active_strip, "flash_bias", text="Bias", slider=True)

        row = box.row()
        if active_strip.flash_bias > 0:
            row.label(text="Bias: Flash will come in slower and go out faster.")
        if active_strip.flash_bias < 0:
            row.label(text="Bias: Flash will come in faster and go out slower.")
        if active_strip.flash_bias == 0:
            row.label(text="Bias: Flash will come in and go out at same speed.")


    @staticmethod    
    def draw_bake_panel(self, context, box, scene, active_strip):
        row = box.row()
        row.prop(scene, "bake_panel_toggle", icon="TRIA_DOWN" if scene.bake_panel_toggle else "TRIA_RIGHT", icon_only=True, emboss=False)
        row.label(text="Film a Qmeo", icon='FILE_MOVIE')
        if scene.bake_panel_toggle:
            row = box.row(align=True)
            row.operator("my.delete_animation_cue_list_operator", text="", icon='CANCEL')
            row.prop(active_strip, "animation_cue_list_number", text="Cue List")

            row = box.row(align=True)
            row.operator("my.delete_animation_event_list_operator", text="", icon='CANCEL')
            row.operator("my.stop_animation_clock_operator", text="", icon='PAUSE')
            row.prop(active_strip, "animation_event_list_number", text="Event List")

            row = box.row()
            row.operator("my.bake_fcurves_to_cues_operator", text=scene.scene_props.str_bake_info, icon_value=orb.icon_id)

            row = box.row()
            row.operator("my.rerecord_cues_operator", text=scene.scene_props.str_cue_bake_info, icon_value=orb.icon_id)
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
        

    @staticmethod    
    def draw_strip_trigger(self, context, column, box, active_strip):
        box.separator(factor=.01)
        
        row = box.row()
        split = row.split(factor=0.25)
        split.label(text="Address:")
        split.prop(active_strip, "trigger_prefix", text="")
        row = box.separator()
        
        row = box.row()
        row.enabled = not active_strip.use_macro
        split = row.split(factor=0.35)
        split.label(text="Start Frame:")
        split.prop(active_strip, "osc_trigger", text="")
        
        row = box.row()
        split = row.split(factor=0.35)
        split.label(text="End Frame:")
        split.prop(active_strip, "osc_trigger_end", text="")

        row = box.row()
        box = column.box()
        row = box.row()
        row.label(text="Start Frame Offsets:")
        
        row = box.row()
        row.prop(active_strip, "friend_list", text="")
        row = box.row(align=True)
        row.prop(active_strip, "use_macro", expand=True, text="")
        row.prop(active_strip, "offset_macro", text="Offset Macro")
        row.operator("my.generate_offset_macro", text="", icon_value=orb.icon_id)
        box.separator(factor=.01)


    @staticmethod    
    def draw_strip_offset(self, context, column, box, active_strip):
        box.separator(factor=.01)

        row = box.row()
        row.prop(active_strip, 'offset_type_enum', text="")
        if active_strip.offset_type_enum == 'option_intensity':
            row.prop(active_strip, 'offset_intensity', text="Intensity:", slider=True)
        elif active_strip.offset_type_enum == 'option_zoom':    
            row.prop(active_strip, 'offset_zoom', text="Zoom:", slider=True)
        elif active_strip.offset_type_enum == 'option_iris':
            row.prop(active_strip, 'offset_iris', text="Iris:", slider=True)
        elif active_strip.offset_type_enum == 'option_color_palette':
            row.prop(active_strip, 'offset_color_palette', text="CP:")
        elif active_strip.offset_type_enum == 'option_intensity_palette':
            row.prop(active_strip, 'offset_intensity_palette', text="IP:")
        elif active_strip.offset_type_enum == 'option_focus_palette':
            row.prop(active_strip, 'offset_focus_palette', text="FP:")
        elif active_strip.offset_type_enum == 'option_beam_palette':
            row.prop(active_strip, 'offset_beam_palette', text="BP:")
        row.prop(active_strip, 'offset_fade_time', text="Fade:")

        row = box.row(align=True)
        row.prop(active_strip, 'offset_channels', text="")

        box.separator()

        row = box.row(align=True)
        row.prop(active_strip, "use_macro", expand=True, text="")
        row.prop(active_strip, "offset_macro", text="Offset Macro")
        row.operator("my.generate_offset_macro", text="", icon_value=orb.icon_id)
        
        box.separator(factor=.01)
    

    @staticmethod    
    def draw_strip_footer(self, context, column):
        row = column.row(align=True)
        row.operator("my.bump_left_five", icon='BACK')
        row.operator("my.bump_left_one", icon='BACK')
        row.operator("my.bump_up", icon='TRIA_UP')
        row.operator("my.bump_down", icon='TRIA_DOWN')
        row.operator("my.bump_right_one", icon='FORWARD')
        row.operator("my.bump_right_five", icon='FORWARD')
        

    @staticmethod    
    def draw_strip_sound_object(self, context, column, active_strip):
        row = column.row()
        row.prop_search(active_strip, "selected_stage_object", bpy.data, "objects", text="", icon='HOME')
        row.prop(active_strip, "audio_object_activated", text="", slider=True)

        column.separator()

        row = column.row()
        row.operator("seq.bake_audio_operator", text="Render to Sound Files", icon='FILE_TICK')


    @staticmethod
    def draw_animate_lighting_video_audio(self, context):
        if context.scene:
            pcoll = preview_collections["main"]
            orb = pcoll["orb"]
            
            scene = context.scene.scene_props
            layout = self.layout
            column = layout.column(align=True)  
            
            box = column.box()

            row = box.row()
            row.label(text="LIGHTING:")

            box = column.box()

            row = box.row()
            row.alert = scene.is_cue_baking
            row.operator("my.bake_fcurves_to_cues_operator", text=scene.str_bake_info, icon_value=orb.icon_id)
            row.operator("my.rerecord_cues_operator", text=scene.str_cue_bake_info, icon_value=orb.icon_id)
            
            column.separator()
            
            box = column.box()

            row = box.row()
            row.label(text="VIDEO:")

            box = column.box()

            row = box.row()
            row.label(text="Coming by end of 2024: Animate PTZ cameras.")
            
            column.separator()
            
            box = column.box()

            row = box.row()
            row.label(text="AUDIO:")

            box = column.box()

            row = box.row()
            row.operator("seq.render_all_audio_objects_operator", text="Render all Audio Objects", icon='FILE_TICK')

    # @staticmethod  ## Does this need to be rewritten or deleted?
    # def draw_strip_speaker(self, context, column, active_strip):
    #     column.separator()
    #     row = column.row()
    #     row.label(text="Select a speaker in 3D view.")
    #     row.prop_search(active_strip, "selected_speaker", bpy.data, "objects", text="", icon='SPEAKER')
    #     column.separator()
    #     row = column.row()
    #     row.prop(active_strip, "int_mixer_channel", text="Fader #:")
    #     row.prop(active_strip, "speaker_sensitivity", text="Sensitivity:", slider=True)
    #     layout.separator()
    #     row = layout.row()
    #     row.operator("seq.bake_audio_operator", text="Bake Audio (Scene)")
    #     row = layout.row()
    #     row.operator("seq.solo_track_operator", text="Solo Track")
    #     row.operator("seq.export_audio_operator", text="Export Channel")
    #     layout.separator()
        

    @staticmethod
    def draw_strip_video(self, context):
        if context.scene:
            layout = self.layout
            layout.label(text="Coming by end of 2024: Animate PTZ cameras.")
            layout.separator()
            layout.label(text="&")
        

    @staticmethod
    def draw_strip_formatter_color(self, context, column, scene, sequence_editor, active_strip):
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

        ## Can we use an existing function for this?
        ## Or possibly just use alva_context?
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
            

    @staticmethod
    def draw_strip_formatter_sound(self, context, column, active_strip):
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
        row = column.row()
        row.prop(active_strip, "volume", text="Volume")
        

    @staticmethod
    def draw_strip_formatter_video_audio(self, context, column, active_strip, sequence_editor):
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
        

    @staticmethod
    def draw_strip_formatter_generator(self, context, column, scene):
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
    

    @staticmethod    
    def draw_sequencer_add_menu(self, layout):
        layout = self.layout
        layout.separator()
        layout.label(text="Alva Sorcerer", icon_value=orb.icon_id)
        layout.operator("my.add_macro", text="Macro", icon='REC')
        layout.operator("my.add_cue", text="Cue", icon='PLAY')
        layout.operator("my.add_flash", text="Flash", icon='LIGHT_SUN')
        layout.operator("my.add_animation", text="Animation", icon='IPO_BEZIER')
        layout.operator("my.add_offset_strip", text="Offset", icon='UV_SYNC_SELECT')
        layout.operator("my.add_trigger", text="Trigger", icon='SETTINGS')


    @staticmethod        
    def draw_sequencer_cmd_line(self, context):
        if (hasattr(context.scene, "command_line_label") and
            hasattr(context.scene, "livemap_label")):
            layout = self.layout
            scene = context.scene
            layout.label(text=scene.livemap_label)
            layout.label(text=scene.command_line_label)
        

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
                elif motif_type == "option_offset":
                    console_context = "offset"
                elif motif_type == "option_trigger":
                    console_context = "trigger"
        else:
            alva_context = "none_relevant"
            console_context = "none"

        return alva_context, console_context
    
        
'''Need to figure out where to put this now that the other stuff has been moved to toolbar.
   It does make sense to incorporate this now since we have an accesible color splitter.
   Will be reliant on patch though.
'''
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
