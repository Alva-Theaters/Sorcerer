# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from functools import partial

from .space_common import draw_text_or_group_input, draw_parameters_mini, draw_play_bar, draw_footer_toggles
from .utils import determine_sequencer_contexts

# Custom icon stuff
import bpy.utils.previews
import os
preview_collections = {}
pcoll = bpy.utils.previews.new()
preview_collections["main"] = pcoll

addon_dir = os.path.dirname(__file__)
pcoll.load("orb", os.path.join(addon_dir, "alva_orb.png"), 'IMAGE')

icons_dir = os.path.join(addon_dir, "icons")
pcoll.load("preset_one", os.path.join(icons_dir, "preset_one.png"), 'IMAGE')
pcoll.load("preset_two", os.path.join(icons_dir, "preset_two.png"), 'IMAGE')
pcoll.load("preset_three", os.path.join(icons_dir, "preset_three.png"), 'IMAGE')
pcoll.load("preset_four", os.path.join(icons_dir, "preset_four.png"), 'IMAGE')
pcoll.load("preset_five", os.path.join(icons_dir, "preset_five.png"), 'IMAGE')
pcoll.load("preset_six", os.path.join(icons_dir, "preset_six.png"), 'IMAGE')
pcoll.load("preset_seven", os.path.join(icons_dir, "preset_seven.png"), 'IMAGE')
pcoll.load("preset_eight", os.path.join(icons_dir, "preset_eight.png"), 'IMAGE')
pcoll.load("preset_nine", os.path.join(icons_dir, "preset_nine.png"), 'IMAGE')

pcoll.load("effect_one", os.path.join(icons_dir, "effect_one.png"), 'IMAGE')
pcoll.load("effect_two", os.path.join(icons_dir, "effect_two.png"), 'IMAGE')
pcoll.load("effect_three", os.path.join(icons_dir, "effect_three.png"), 'IMAGE')
pcoll.load("effect_four", os.path.join(icons_dir, "effect_four.png"), 'IMAGE')
pcoll.load("effect_five", os.path.join(icons_dir, "effect_five.png"), 'IMAGE')
pcoll.load("effect_six", os.path.join(icons_dir, "effect_six.png"), 'IMAGE')
pcoll.load("effect_seven", os.path.join(icons_dir, "effect_seven.png"), 'IMAGE')
pcoll.load("effect_eight", os.path.join(icons_dir, "effect_eight.png"), 'IMAGE')
pcoll.load("effect_nine", os.path.join(icons_dir, "effect_nine.png"), 'IMAGE')
pcoll.load("effect_ten", os.path.join(icons_dir, "effect_ten.png"), 'IMAGE')
pcoll.load("effect_eleven", os.path.join(icons_dir, "effect_eleven.png"), 'IMAGE')
pcoll.load("effect_twelve", os.path.join(icons_dir, "effect_twelve.png"), 'IMAGE')
pcoll.load("effect_thirteen", os.path.join(icons_dir, "effect_thirteen.png"), 'IMAGE')
pcoll.load("effect_fourteen", os.path.join(icons_dir, "effect_fourteen.png"), 'IMAGE')

filter_color_strips = partial(filter, bpy.types.ColorSequence.__instancecheck__)


def draw_alva_sequencer_view(self, layout):
    if bpy.context.scene.scene_props.console_type_enum == 'option_eos':
        pcoll = preview_collections["main"]
        orb = pcoll["orb"]

        layout = self.layout
        layout.separator()
        layout.label(text="Alva Sorcerer", icon_value=orb.icon_id)
        layout.prop(bpy.context.scene.scene_props, "view_sequencer_add", text="Add")
        layout.prop(bpy.context.scene.scene_props, "view_sequencer_toolbar", text="Toolbar")
        layout.prop(bpy.context.scene.scene_props, "view_sequencer_command_line", text="Command Line")
        layout.prop(bpy.context.scene.scene_props, "expand_strobe", text="Expand Strobe")


def draw_alva_sequencer_add_menu(self, layout):
    if bpy.context.scene.scene_props.view_sequencer_add and bpy.context.scene.scene_props.console_type_enum == 'option_eos':
        pcoll = preview_collections["main"]
        orb = pcoll["orb"]

        layout = self.layout
        layout.separator()
        layout.label(text="Alva Sorcerer", icon_value=orb.icon_id)
        layout.operator("alva_seq.add", text="Macro", icon='FILE_TEXT').Option = "option_macro"
        layout.operator("alva_seq.add", text="Cue", icon='PLAY').Option = "option_cue"
        layout.operator("alva_seq.add", text="Flash", icon='LIGHT_SUN').Option = "option_flash"
        layout.operator("alva_seq.add", text="Animation", icon='IPO_BEZIER').Option = "option_animation"
        #layout.operator("alva_seq.add", text="Offset", icon='UV_SYNC_SELECT').Option = "option_offset"
        layout.operator("alva_seq.add", text="Trigger", icon='SETTINGS').Option = "Option_trigger"


def draw_alva_sequencer_strip(self, context):
    if context.scene.scene_props.console_type_enum == 'option_eos':
        pcoll = preview_collections["main"]
        orb = pcoll["orb"]

        layout = self.layout
        layout.separator()
        layout.label(text="Alva Sorcerer", icon_value=orb.icon_id)
        layout.prop(context.scene, "is_updating_strip_color", text="Sync Strip Color",  slider=True)
        layout.prop(context.scene, "is_armed_release", text="Z Adds Strip on Release", slider=True) 
        layout.prop(context.scene, "strip_end_macros", text="End Frame Macros", slider=True)
        layout.separator()
        layout.prop(context.scene, "cue_builder_toggle", slider=True, text="Cue Builder")
        layout.prop(context.scene, "using_gels_for_cyc", text="Gels for Cyc Color", slider=True)
        layout.prop(context.scene, "cue_builder_id_offset", text="Index Offset", toggle=True)


def draw_alva_sequencer_cmd_line(self, context):
    if (hasattr(context.scene, "scene_props") and
        context.scene.scene_props.view_sequencer_command_line):
        layout = self.layout
        scene = context.scene
        layout.prop(context.scene, "is_armed_livemap", text="", icon='PLAY')
        if context.scene.is_armed_livemap:
            layout.label(text=scene.livemap_label)
        layout.label(text=scene.command_line_label)


def draw_strip_media(self, context, scene, bake_panel=True):
    layout = self.layout
    scene = context.scene

    if not context.scene.scene_props.console_type_enum == 'option_eos':
        return
    
    if not hasattr(scene, "sequence_editor") and scene.sequence_editor:
        draw_intro_header(self, context, None, scene, None)

    # Check if the sequence editor and active strip exist
    elif hasattr(scene, "sequence_editor") and scene.sequence_editor:
        sequence_editor = scene.sequence_editor
        if hasattr(sequence_editor, "active_strip") and sequence_editor.active_strip:
            active_strip = sequence_editor.active_strip
            alva_context, console_context = determine_sequencer_contexts(sequence_editor, active_strip)
        else:
            alva_context = "none_relevant"
            console_context = "none"
            
        column = layout.column(align=True)

        if alva_context == "incompatible_types":
            box = draw_incompatible_types(self, context, column, scene, active_strip)
    
        elif alva_context == "only_sound":
            box = draw_only_sound(self, context, column, active_strip)
            
        elif alva_context == "one_video_one_audio":
            box = draw_one_audio_one_video(self, context, column, scene, active_strip)
                
        elif alva_context == "none_relevant":
            box = draw_none_relevant(self, context, sequence_editor, column, scene)

        elif alva_context == "only_color":
            box = draw_color_header(self, context, column, scene, active_strip, console_context)
            
            if console_context == "macro":
                draw_strip_macro(self, context, column, box, active_strip)
            
            elif console_context == "cue":
                draw_strip_cue(self, context, column, box, active_strip)
                if scene.cue_builder_toggle:
                    draw_cue_builder(self, context, box, scene, active_strip)

            elif console_context == "flash":  
                row = box.row()
                #row.prop(active_strip, "flash_type_enum", expand=0, text="Method")
                
                if active_strip.flash_type_enum != 'option_use_controllers':
                    draw_strip_flash_manual(self, context, box, active_strip)
                else: draw_strip_flash_controllers(self, context, box, active_strip)
                
                draw_strip_flash_footer(self, context, box, active_strip)
                
            elif console_context == "animation":
                draw_text_or_group_input(self, context, box, active_strip, object=False)
                draw_parameters_mini(self, context, box, active_strip, use_slider=True, expand=True, text=False)
                box.separator()
                draw_play_bar(self, context, box)
                draw_footer_toggles(self, context, column, active_strip)

            elif console_context == "offset":
                draw_strip_offset(self, context, column, box, active_strip)
                        
            elif console_context == "trigger":
                draw_strip_trigger(self, context, column, box, active_strip)
        
        else:
            draw_add_buttons_row(self, context, column, scene, active_strip)
            column.separator()
            box = draw_text_insert(self, context, column, text="No active color strip.")
            return box    
                        
        if not scene.bake_panel_toggle and alva_context == "only_color" and console_context != "animation":
            box.separator()
        
        if alva_context == "only_color":
            draw_strip_footer(self, context, column)
        else:
            draw_strip_footer(self, context, box)
        

def draw_add_buttons_row(self, context, column, scene, active_strip, lighting_icons=False, console_context=None):
    row = column.row(align=True)
    row.operator("alva_seq.add", text="", icon='FILE_TEXT').Option = "option_macro"
    row.operator("alva_seq.add", text="", icon='PLAY').Option = "option_cue"
    row.operator("alva_seq.add", text="", icon='LIGHT_SUN').Option = "option_flash"
    row.operator("alva_seq.add", text="", icon='IPO_BEZIER').Option = "option_animation"
    #row.operator("alva_seq.add", text="", icon='UV_SYNC_SELECT').Option = "option_offset"
    row.operator("alva_seq.add", text="", icon='SETTINGS').option = "Option_trigger"
    

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


def draw_intro_header(self, context, column, scene, active_strip):
    draw_add_buttons_row(self, context, column, scene, active_strip)
    column.separator()
    box = draw_text_insert(self, context, column, text="Welcome to ..")
    return box
    


def draw_incompatible_types(self, context, column, scene, active_strip):
    draw_add_buttons_row(self, context, column, scene, active_strip)
    column.separator()
    box = draw_text_insert(self, context, column, text="Incompatible strips selected.")
    return box


def draw_one_audio_one_video(self, context, column, scene, active_strip):  
    draw_add_buttons_row(self, context, column, scene, active_strip)
    column.separator()
    box = draw_text_insert(self, context, column, text="Format movie with F key.")
    return box


def draw_none_relevant(self, context, sequence_editor, column, scene): 
    draw_add_buttons_row(self, context, column, scene, None) 
    column.separator()
    box = draw_text_insert(self, context, column, text="No relevant strips selected.")
    return box


def draw_only_sound(self, context, column, active_strip):
    pcoll = preview_collections["main"]
    orb = pcoll["orb"]

    row = column.row(align=True)
    row.operator("alva_seq.mute", icon='HIDE_OFF' if not active_strip.mute else 'HIDE_ON')
    row.prop(active_strip, "name", text="")

    column.separator()
    column.separator()

    box = column.box()  

    row = box.row(align=True)
    row.operator("alva_seq.tc_left_five", text="", icon='BACK')
    row.operator("alva_seq.tc_left_one", text="", icon='TRIA_LEFT')
    row.operator("alva_seq.tc_right_one", text="", icon='TRIA_RIGHT')
    row.operator("alva_seq.tc_right_five", text="", icon='FORWARD')
    row.prop(active_strip, "int_event_list", text="Event List #")
    row.operator("alva_seq.clear_tc_clock", icon="CANCEL")
    row.operator("alva_orb.execute_on_cue", icon_value=orb.icon_id, text="")

    row = box.row()
    row.operator("alva_seq.analyze_song", icon='SHADERFX')
    return box


def draw_color_header(self, context, column, scene, active_strip, console_context):
    box = draw_color_subheader(self, context, column, active_strip, console_context)
    return box
    

def draw_color_subheader(self, context, column, active_strip, console_context):
    box = column.box()
    row = box.row(align=True)
    my_settings = active_strip.my_settings
    row.prop(my_settings, "motif_type_enum", expand=True)
    draw_strip_type_label(console_context, row)
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


def draw_strip_macro(self, context, column, box, active_strip):
    pcoll = preview_collections["main"]
    orb = pcoll["orb"]

    row = box.row()
    row.label(text='* = "Sneak Time " + [Strip length]')
    row = box.row(align=True)
    row.prop(active_strip, "start_frame_macro_text_gui")
    row.operator("alva_orb.generate_start_frame_macro", icon_value=orb.icon_id)
    if context.scene.strip_end_macros:
        row = box.separator()
        row = box.row(align=True)
        row.prop(active_strip, "end_frame_macro_text_gui")
        row.operator("alva_orb.generate_end_frame_macro", icon_value=orb.icon_id)
            

def draw_strip_cue(self, context, column, box, active_strip):
    pcoll = preview_collections["main"]
    orb = pcoll["orb"]

    row = box.row(align=True)  
    row.prop(active_strip, "eos_cue_number", text="Cue #")
    row.operator("alva_tool.ghost_out", text="", icon='GHOST_ENABLED')
    if context.scene.cue_builder_toggle:
        row.operator("my.update_builder", text="", icon='FILE_REFRESH')
    row.operator("my.record_cue", text="", icon='REC')
    row.operator("alva_orb.generate_cue", icon_value=orb.icon_id)
    row = box.row(align=True)
    row.scale_y = 2
    row.scale_x = .6
    row.prop(active_strip, "sixty_color", text="")
    row.scale_x = .4
    row.prop(active_strip, "thirty_color", text="")
    row.scale_x = .21
    row.prop(active_strip, "ten_color", text="")


def draw_builder_row(box, ops_list, id, active_strip, label, alert_flag, is_color=True, record_prop_name=""):
    pcoll = preview_collections["main"]
    preset_one = pcoll["preset_one"]
    preset_two = pcoll["preset_two"]
    preset_three = pcoll["preset_three"]
    preset_four = pcoll["preset_four"]
    preset_five = pcoll["preset_five"]
    preset_six = pcoll["preset_six"]
    preset_seven = pcoll["preset_seven"]
    preset_eight = pcoll["preset_eight"]
    preset_nine = pcoll["preset_nine"]
    event_icons = [preset_one.icon_id, preset_two.icon_id, preset_three.icon_id, preset_four.icon_id, preset_five.icon_id, preset_six.icon_id, preset_seven.icon_id, preset_eight.icon_id, preset_nine.icon_id]
    color_icons = ['COLORSET_01_VEC', 'COLORSET_02_VEC', 'COLORSET_03_VEC', 'COLORSET_04_VEC',
                'COLORSET_05_VEC', 'COLORSET_06_VEC', 'COLORSET_07_VEC', 'COLORSET_08_VEC']
    alert_ids = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]

    row = box.row(align=True)
    row.operator(f"my.{id}_groups", text="", icon='PREFERENCES')
    row.prop(active_strip, f"{id}_light", text=label, slider=True)
    row.alert = alert_flag
    row_icons = color_icons if is_color else event_icons
    active_alert_id = getattr(active_strip, f"cue_builder_{id}_id")
    for op, icon, alert_id in zip(ops_list, row_icons, alert_ids):
        if is_color:
            row.alert = (active_alert_id == alert_id or alert_flag)
            row.operator(op, text="", icon=icon)
            row.alert = False
        else:
            row.alert = (active_alert_id == alert_id or alert_flag)
            row.operator(op, text="", icon_value=icon)
            row.alert = False

    row.prop(active_strip, record_prop_name, text="", icon='REC')


def draw_cue_builder(self, context, box, scene, active_strip):
    pcoll = preview_collections["main"]
    effect_one = pcoll["effect_one"]
    effect_two = pcoll["effect_two"]
    effect_three = pcoll["effect_three"]
    effect_four = pcoll["effect_four"]
    effect_five = pcoll["effect_five"]
    effect_six = pcoll["effect_six"]
    effect_seven = pcoll["effect_seven"]
    effect_eight = pcoll["effect_eight"]
    effect_nine = pcoll["effect_nine"]
    effect_ten = pcoll["effect_ten"]
    effect_eleven = pcoll["effect_eleven"]
    effect_twelve = pcoll["effect_twelve"]
    effect_thirteen = pcoll["effect_thirteen"]
    effect_fourteen = pcoll["effect_fourteen"]

    key_ops = ["my.focus_one", "my.focus_two", "my.focus_three", "my.focus_four", "my.focus_five", "my.focus_six", "my.focus_seven", "my.focus_eight", "my.focus_nine"]

    rim_ops = ["my.focus_rim_one", "my.focus_rim_two", "my.focus_rim_three", "my.focus_rim_four", "my.focus_rim_five", "my.focus_rim_six", "my.focus_rim_seven", "my.focus_rim_eight", "my.focus_rim_nine"]

    fill_ops = ["my.focus_fill_one", "my.focus_fill_two", "my.focus_fill_three", "my.focus_fill_four", "my.focus_fill_five", "my.focus_fill_six", "my.focus_fill_seven", "my.focus_fill_eight", "my.focus_fill_nine"]

    cyc_ops = ["my.focus_cyc_one", "my.focus_cyc_two", "my.focus_cyc_three", "my.focus_cyc_four",
                "my.focus_cyc_five", "my.focus_cyc_six", "my.focus_cyc_seven", "my.focus_cyc_eight", "my.focus_texture_nine"]
    
    band_ops = ["my.focus_band_one", "my.focus_band_two", "my.focus_band_three", "my.focus_band_four",
                "my.focus_band_five", "my.focus_band_six", "my.focus_band_seven", "my.focus_band_eight", "my.focus_texture_nine"]
    
    accent_ops = ["my.focus_accent_one", "my.focus_accent_two", "my.focus_accent_three", "my.focus_accent_four",
                "my.focus_accent_five", "my.focus_accent_six", "my.focus_accent_seven", "my.focus_accent_eight", "my.focus_texture_nine"]
    
    texture_ops = ["my.focus_texture_one", "my.focus_texture_two", "my.focus_texture_three", "my.focus_texture_four",
                "my.focus_texture_five", "my.focus_texture_six", "my.focus_texture_seven", "my.focus_texture_eight", "my.focus_texture_nine"]
    
    effect_ids = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14"]

    fx_ops = ["my.focus_energy_one", "my.focus_energy_two", "my.focus_energy_three", "my.focus_energy_four", "my.focus_energy_five", "my.focus_energy_six", "my.focus_energy_seven", "my.focus_energy_eight", "my.focus_energy_nine", "my.focus_energy_ten", "my.focus_energy_eleven", "my.focus_energy_twelve", "my.focus_energy_thirteen", "my.focus_energy_fourteen"]

    fx_icons = [effect_one.icon_id, effect_two.icon_id, effect_three.icon_id, effect_four.icon_id, effect_five.icon_id, effect_six.icon_id, effect_seven.icon_id, effect_eight.icon_id, effect_nine.icon_id, effect_ten.icon_id, effect_eleven.icon_id, effect_twelve.icon_id, effect_thirteen.icon_id, effect_fourteen.icon_id]

    # Key, Rim, and Fill rows
    draw_builder_row(box, key_ops, 'key', active_strip, "Key", active_strip.key_is_recording, is_color=0, record_prop_name="key_is_recording")
    draw_builder_row(box, rim_ops, 'rim', active_strip, "Rim/Hair", active_strip.rim_is_recording, is_color=0, record_prop_name="rim_is_recording")
    draw_builder_row(box, fill_ops, 'fill', active_strip, "Fill", active_strip.fill_is_recording, is_color=0, record_prop_name="fill_is_recording")

    # Background row
    if scene.using_gels_for_cyc:
        row = box.row(align=True)
        row.operator("my.gel_one_groups", text="", icon='PREFERENCES')
        row.prop(active_strip, "background_light_one", text="Cyc 1", slider=True)
        row.prop(active_strip, "background_light_two", text="Cyc 2", slider=True)
        row.prop(active_strip, "background_light_three", text="Cyc 3", slider=True)
        row.prop(active_strip, "background_light_four", text="Cyc 4", slider=True)
    else:
        draw_builder_row(box, cyc_ops, 'gel_one', active_strip, "Cyc", active_strip.cyc_is_recording, is_color=1, record_prop_name="cyc_is_recording")

    # Texture, Band, and Accent rows
    draw_builder_row(box, texture_ops, 'texture', active_strip, "Texture", active_strip.texture_is_recording, is_color=1, record_prop_name="texture_is_recording")
    draw_builder_row(box, band_ops, 'band', active_strip, "Band", active_strip.band_is_recording, is_color=1, record_prop_name="band_is_recording")
    draw_builder_row(box, accent_ops, 'accent', active_strip, "Accent", active_strip.accent_is_recording, is_color=1, record_prop_name="accent_is_recording")

    box.separator()

    # Energy Intensity row
    row = box.row(align=True)
    row.operator("my.energy_groups", text="", icon='PREFERENCES')
    row.prop(active_strip, "energy_light", text="Effect", slider=True)
    row.prop(active_strip, "energy_speed", text="Speed", slider=True)
    row.prop(active_strip, "energy_scale", text="Scale", slider=True)

    # Effects row
    row = box.row(align=True)
    row.operator("my.stop_effect", text="", icon='CANCEL')
    for effect_id, operator, icon in zip(effect_ids, fx_ops, fx_icons):
        row.alert = active_strip.cue_builder_effect_id == effect_id
        row.operator(operator, text="", icon_value=icon)
        row.alert = 0

        
def draw_strip_flash_manual(self, context, box, active_strip):
    is_manual_enabled = (active_strip.flash_type_enum != 'option_use_nodes')
        
    row = box.row()
    row = box.label(text=f"Flash Up: {active_strip.flash_input_background}")
    row = box.row(align=True)
    row.enabled = is_manual_enabled
    row.prop(active_strip, "flash_input", text="")
    row.operator("alva_seq.flash_copy_down", text="", icon='DOWNARROW_HLT')
    
    row = box.row()
    row = box.label(text=f"Flash Down: {active_strip.flash_down_input_background}")
    row = box.row()
    row.enabled = is_manual_enabled
    row.prop(active_strip, "flash_down_input", text="")
    
    row = box.separator()
    

def draw_strip_flash_controllers(self, context, box, active_strip):
    # Top row
    row = box.row(align=True)
    row.operator("alva_node.home", icon='HOME', text="")
    row.operator("alva_node.update", icon='FILE_REFRESH', text="")
    if active_strip.str_manual_fixture_selection == "":
        if not active_strip.selected_group_enum:
            row.prop(active_strip, "selected_group_enum", text="", icon_only=False, icon='LIGHT')
    row.prop(active_strip, "str_manual_fixture_selection", text="")
    row.operator("alva_node.home", icon='HOME', text="")
    row.operator("alva_node.update", icon='FILE_REFRESH', text="")
    
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


def draw_strip_flash_footer(self, context, box, active_strip):
    pcoll = preview_collections["main"]
    orb = pcoll["orb"]

    row = box.row(align=True)
    row.prop(active_strip, "flash_bias", text="Bias", slider=True)
    row.operator("alva_orb.generate_flash_macros", text="", icon_value=orb.icon_id)

    row = box.row()
    if active_strip.flash_bias > 0:
        row.label(text="Bias: Flash will come in slower and go out faster.")
    if active_strip.flash_bias < 0:
        row.label(text="Bias: Flash will come in faster and go out slower.")
    if active_strip.flash_bias == 0:
        row.label(text="Bias: Flash will come in and go out at same speed.")
    

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

    box.separator(factor=.01)


def draw_strip_offset(self, context, column, box, active_strip):
    pcoll = preview_collections["main"]
    orb = pcoll["orb"]

    box.separator(factor=.01)

    row = box.row()
    row.scale_y = 2
    row.prop(active_strip, 'offset_type_enum', text="")
    if active_strip.offset_type_enum == 'option_intensity':
        row.prop(active_strip, 'offset_intensity', text="", slider=True)
    elif active_strip.offset_type_enum == 'option_zoom':    
        row.prop(active_strip, 'offset_zoom', text="", slider=True)
    elif active_strip.offset_type_enum == 'option_iris':
        row.prop(active_strip, 'offset_iris', text="", slider=True)
    elif active_strip.offset_type_enum == 'option_color_palette':
        row.prop(active_strip, 'offset_color_palette', text="")
    elif active_strip.offset_type_enum == 'option_intensity_palette':
        row.prop(active_strip, 'offset_intensity_palette', text="")
    elif active_strip.offset_type_enum == 'option_focus_palette':
        row.prop(active_strip, 'offset_focus_palette', text="")
    elif active_strip.offset_type_enum == 'option_beam_palette':
        row.prop(active_strip, 'offset_beam_palette', text="")
    row.prop(active_strip, 'offset_fade_time', text="Fade:")

    row = box.row(align=True)
    row.prop(active_strip, 'offset_channels', text="")
    row.prop(active_strip, "use_macro", text="", icon='FILE_TEXT')
    row.operator("alva_orb.generate_offset_macro", text="", icon_value=orb.icon_id)
    
    box.separator(factor=.01)


def draw_strip_footer(self, context, column):
    row = column.row(align=True)
    row.operator("alva_seq.bump_horizontal", text="-5", icon='BACK').direction = -5
    row.operator("alva_seq.bump_horizontal", text="-1", icon='BACK').direction = -1
    row.operator("alva_seq.bump_horizontal", icon='TRIA_UP').direction = -1
    row.operator("alva_seq.bump_horizontal", icon='TRIA_DOWN').direction = 1
    row.operator("alva_seq.bump_vertical", text="1", icon='FORWARD').direction = 1
    row.operator("alva_seq.bump_vertical", text="5", icon='FORWARD').direction = 5
    

def draw_strip_sound_object(self, context, column, active_strip):
    row = column.row(align=True)
    row.operator('alva_seq.refresh_audio_object_selection', icon='FILE_REFRESH', text="")
    row.prop_search(active_strip, "selected_stage_object", bpy.data, "objects", text="", icon='VIEW3D')
    row.operator("alva_seq.export_audio", text="", icon='FILE_TICK')
    row = column.row()
    row.prop(active_strip, 'int_sound_cue', text="Sound Cue")
    

def draw_strip_video(self, context):
    if context.scene:
        layout = self.layout
        layout.label(text="Coming by end of 2024: Animate PTZ cameras.")
        layout.separator()
        layout.label(text="&")
    

def draw_strip_formatter_color(self, context, column, scene, sequence_editor, active_strip):
    row = column.row(align=True)
    if scene.is_filtering_left:
        row.alert = 1
        row.prop(scene, "is_filtering_left", icon='FILTER')
        row.alert = 0
    elif scene.is_filtering_left == False:
        row.alert = 0
        row.prop(scene, "is_filtering_left", icon='FILTER')
    row.operator("alva_seq.select_similar", text="Select Magnetic") 
    if scene.is_filtering_right:
        row.alert = 1
        row.prop(scene, "is_filtering_right", icon='FILTER')
        row.alert = 0
    elif scene.is_filtering_right == False:
        row.alert = 0
        row.prop(scene, "is_filtering_right", icon='FILTER')

    row = column.row(align=True)
    row.prop(scene, "color_is_magnetic", text="", icon='SNAP_OFF' if not scene.color_is_magnetic else 'SNAP_ON')
    row.prop(active_strip, "color", text="")
    row.operator("alva_seq.copy_attribute", text="", icon='FILE').target = 'color'
    row.operator("alva_seq.formatter_select", text="", icon='RESTRICT_SELECT_OFF').target = 'color'

    row = column.row(align=True)
    row.prop(scene, "strip_name_is_magnetic", text="", icon='SNAP_OFF' if not scene.strip_name_is_magnetic else 'SNAP_ON')
    row.prop(active_strip, "name", text="")  
    row.operator("alva_seq.copy_attribute", text="", icon='FILE').target = 'name'
    row.operator("alva_seq.formatter_select", text="", icon='RESTRICT_SELECT_OFF').target = 'name'

    row = column.row(align=True)
    row.prop(scene, "channel_is_magnetic", text="", icon='SNAP_OFF' if not scene.channel_is_magnetic else 'SNAP_ON')
    row.prop(active_strip, "channel", text_ctxt="Channel: ")
    row.operator("alva_seq.copy_attribute", text="", icon='FILE').target = 'channel'
    row.operator("alva_seq.formatter_select", text="", icon='RESTRICT_SELECT_OFF').target = 'channel'

    row = column.row(align=True)
    row.prop(scene, "duration_is_magnetic", text="", icon='SNAP_OFF' if not scene.duration_is_magnetic else 'SNAP_ON')
    row.prop(active_strip, "frame_final_duration", text="Duration")
    row.operator("alva_seq.copy_attribute", text="", icon='FILE').target = 'frame_final_duration'
    row.operator("alva_seq.formatter_select", text="", icon='RESTRICT_SELECT_OFF').target = 'frame_final_duration'

    row = column.row(align=True)
    row.prop(scene, "start_frame_is_magnetic", text="", icon='SNAP_OFF' if not scene.start_frame_is_magnetic else 'SNAP_ON')
    row.prop(active_strip, "frame_start", text="Start Frame")
    row.operator("alva_seq.frame_jump", text="", icon='PLAY').direction = 1 
    row.operator("alva_seq.copy_attribute", text="", icon='FILE').target = 'frame_start'
    row.operator("alva_seq.formatter_select", text="", icon='RESTRICT_SELECT_OFF').target = 'frame_start'

    row = column.row(align=True)
    row.prop(scene, "end_frame_is_magnetic", text="", icon='SNAP_OFF' if not scene.end_frame_is_magnetic else 'SNAP_ON')
    row.prop(active_strip, "frame_final_end", text="End Frame")
    row.operator("alva_seq.frame_jump", text="", icon='PLAY').direction = 0
    row.operator("alva_seq.copy_attribute", text="", icon='FILE').target = 'frame_final_end'
    row.operator("alva_seq.formatter_select", text="", icon='RESTRICT_SELECT_OFF').target = 'frame_final_end'

    row = column.row(align=True)
    row.operator("alva_tool.copy", text="Copy Various to Selected", icon='FILE')
    column.separator()
    if scene.i_know_the_shortcuts == False:
        row = column.row(align=True)
        row.operator("alva_seq.hotkey_hint", text="Extrude").message = '''Type the "E" key while in sequencer to extrude pattern of 2 strips.'''

        row = column.row(align=True)
        row.operator("alva_seq.hotkey_hint", text="Scale").message = '''Type the "S" key while in sequencer to scale strips.'''

        row = column.row(align=True)
        row.operator("alva_seq.hotkey_hint", text="Grab").message = '''Type the "G" key while in sequencer to grab and move strips.'''

        row = column.row(align=True)
        row.operator("alva_seq.hotkey_hint", text="Grab X").message = '''Type the "G" key, then the "X" key while in sequencer to grab and move strips on X axis only.'''
        row.operator("alva_seq.hotkey_hint", text="Grab Y").message = '''Type the "G" key, then the "Y" key while in sequencer to grab and move strips on Y axis only.'''

        row = column.row(align=True)
        row.operator("alva_seq.hotkey_hint", text="Cut").message = '''Type the "K" key while in sequencer.'''

        row = column.row(align=True)
        row.operator("alva_seq.hotkey_hint", text="Assign to Channel").message = '''Type the "C" key while in sequencer, then channel number, then "Enter" key.'''

    row = column.row(align=True)
    row.prop(scene, "i_know_the_shortcuts", text="I know the shortcuts.")

    selected_color_strips = [strip for strip in filter_color_strips(context.selected_sequences) if strip.select]

    if len(selected_color_strips) > 1:
        column.separator()
        column.separator()

        row = column.row(align=True)
        row.prop(scene, "offset_value", text="Offset in BPM")
        row.operator("alva_seq.offset", text="", icon='CENTER_ONLY')
        column.separator()


def draw_strip_formatter_sound(self, context, column, active_strip):
    row = column.row(align=True)
    row.operator("alva_seq.mute", icon='HIDE_OFF' if not active_strip.mute else 'HIDE_ON')
    row.prop(active_strip, "name", text="")
    row = column.row(align=True)
    row.prop(active_strip, "song_bpm_input", text="Beats per minute (BPM)")
    row = column.row(align=True)
    row.prop(active_strip, "beats_per_measure", text="Beats per measure")
    row = column.row(align=True)
    row.prop(active_strip, "song_bpm_channel", text="Generate on channel")
    row.operator("alva_seq.generate_on_song", text="", icon='COLOR')
    column.separator()
    row = column.row(align=True)
    row.operator("alva_seq.start_end_frame_mapping", icon='PREVIEW_RANGE')
    row = column.row(align=True)
    row.operator("alva_seq.set_timecode", text="Zero Timecode", icon='TIME')
    column.separator()
    row = column.row(align=True)
    row.prop(active_strip, "show_waveform", slider=True)
    row = column.row()
    row.prop(active_strip, "volume", text="Volume")
    

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
    row.operator("alva_seq.mute", icon='HIDE_OFF' if not active_strip.mute else 'HIDE_ON')
    row.prop(active_strip, "name", text="")

    row = column.row(align=True)
    if selected_sound_strip.frame_start != selected_video_strip.frame_start or selected_sound_strip.frame_final_duration != selected_video_strip.frame_final_duration:
        row.alert = 1
        row.operator("alva_seq.sync_video")

    row = column.row(align=True)
    row.operator("alva_seq.start_end_frame_mapping", icon='PREVIEW_RANGE')

    row = column.row(align=True)
    row.operator("alva_seq.set_timecode", icon='TIME')
    

def draw_strip_formatter_generator(self, context, column, scene):
    row = column.row(align=True)            
    row.prop(scene, "channel_selector", text="Channel")
    row.operator("alva_seq.select_channel", text="", icon='RESTRICT_SELECT_OFF')   

    row = column.row(align=True)
    row.prop(scene, "generate_quantity", text="Quantity")

    row = column.row(align=True)
    if scene.generate_quantity > 1:
        row.prop(scene, "normal_offset", text="Offset by")

    row = column.row(align=True)
    row.operator("alva_seq.generate", icon='COLOR')  

    column.separator()