# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from functools import partial

from ..as_ui.space_common import (
    draw_text_or_group_input, 
    draw_parameters_mini, 
    draw_play_bar, 
    draw_footer_toggles
)

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


def draw_strip_macro(context, box, active_strip):
    pcoll = preview_collections["main"]
    orb = pcoll["orb"]

    row = box.row()
    row.label(text='* = "Sneak Time " + [Strip length]')
    row = box.row(align=True)
    row.prop(active_strip, "start_frame_macro_text_gui")
    row.operator("alva_orb.orb", icon_value=orb.icon_id).as_orb_id = 'option_macro'
    if context.scene.strip_end_macros:
        row = box.separator()
        row = box.row(align=True)
        row.prop(active_strip, "end_frame_macro_text_gui")
            

def draw_strip_cue(context, box, active_strip):
    draw_strip_cue_top(context, box, active_strip)
    if context.scene.cue_builder_toggle:
        draw_cue_builder(context, box, active_strip)


def draw_strip_cue_top(context, box, active_strip):
    pcoll = preview_collections["main"]
    orb = pcoll["orb"]

    row = box.row(align=True)  
    row.prop(active_strip, "eos_cue_number", text="Cue #")
    row.operator("alva_tool.ghost_out", text="", icon='GHOST_ENABLED')
    if context.scene.cue_builder_toggle:
        row.operator("alva_sequencer.update_builder", text="", icon='FILE_REFRESH')
    row.operator("alva_sequencer.record_cue", text="", icon='REC')
    row.operator("alva_orb.orb", icon_value=orb.icon_id).as_orb_id = 'option_cue'
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
    row.operator(f"alva_sequencer.{id}_groups", text="", icon='PREFERENCES')
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


def draw_cue_builder(context, box, active_strip):
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

    key_ops = ["alva_sequencer.focus_one", "alva_sequencer.focus_two", "alva_sequencer.focus_three", "alva_sequencer.focus_four", "alva_sequencer.focus_five", "alva_sequencer.focus_six", "alva_sequencer.focus_seven", "alva_sequencer.focus_eight", "alva_sequencer.focus_nine"]

    rim_ops = ["alva_sequencer.focus_rim_one", "alva_sequencer.focus_rim_two", "alva_sequencer.focus_rim_three", "alva_sequencer.focus_rim_four", "alva_sequencer.focus_rim_five", "alva_sequencer.focus_rim_six", "alva_sequencer.focus_rim_seven", "alva_sequencer.focus_rim_eight", "alva_sequencer.focus_rim_nine"]

    fill_ops = ["alva_sequencer.focus_fill_one", "alva_sequencer.focus_fill_two", "alva_sequencer.focus_fill_three", "alva_sequencer.focus_fill_four", "alva_sequencer.focus_fill_five", "alva_sequencer.focus_fill_six", "alva_sequencer.focus_fill_seven", "alva_sequencer.focus_fill_eight", "alva_sequencer.focus_fill_nine"]

    cyc_ops = ["alva_sequencer.focus_cyc_one", "alva_sequencer.focus_cyc_two", "alva_sequencer.focus_cyc_three", "alva_sequencer.focus_cyc_four",
                "alva_sequencer.focus_cyc_five", "alva_sequencer.focus_cyc_six", "alva_sequencer.focus_cyc_seven", "alva_sequencer.focus_cyc_eight", "alva_sequencer.focus_texture_nine"]
    
    band_ops = ["alva_sequencer.focus_band_one", "alva_sequencer.focus_band_two", "alva_sequencer.focus_band_three", "alva_sequencer.focus_band_four",
                "alva_sequencer.focus_band_five", "alva_sequencer.focus_band_six", "alva_sequencer.focus_band_seven", "alva_sequencer.focus_band_eight", "alva_sequencer.focus_texture_nine"]
    
    accent_ops = ["alva_sequencer.focus_accent_one", "alva_sequencer.focus_accent_two", "alva_sequencer.focus_accent_three", "alva_sequencer.focus_accent_four",
                "alva_sequencer.focus_accent_five", "alva_sequencer.focus_accent_six", "alva_sequencer.focus_accent_seven", "alva_sequencer.focus_accent_eight", "alva_sequencer.focus_texture_nine"]
    
    texture_ops = ["alva_sequencer.focus_texture_one", "alva_sequencer.focus_texture_two", "alva_sequencer.focus_texture_three", "alva_sequencer.focus_texture_four",
                "alva_sequencer.focus_texture_five", "alva_sequencer.focus_texture_six", "alva_sequencer.focus_texture_seven", "alva_sequencer.focus_texture_eight", "alva_sequencer.focus_texture_nine"]
    
    effect_ids = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14"]

    fx_ops = ["alva_sequencer.focus_energy_one", "alva_sequencer.focus_energy_two", "alva_sequencer.focus_energy_three", "alva_sequencer.focus_energy_four", "alva_sequencer.focus_energy_five", "alva_sequencer.focus_energy_six", "alva_sequencer.focus_energy_seven", "alva_sequencer.focus_energy_eight", "alva_sequencer.focus_energy_nine", "alva_sequencer.focus_energy_ten", "alva_sequencer.focus_energy_eleven", "alva_sequencer.focus_energy_twelve", "alva_sequencer.focus_energy_thirteen", "alva_sequencer.focus_energy_fourteen"]

    fx_icons = [effect_one.icon_id, effect_two.icon_id, effect_three.icon_id, effect_four.icon_id, effect_five.icon_id, effect_six.icon_id, effect_seven.icon_id, effect_eight.icon_id, effect_nine.icon_id, effect_ten.icon_id, effect_eleven.icon_id, effect_twelve.icon_id, effect_thirteen.icon_id, effect_fourteen.icon_id]

    # Key, Rim, and Fill rows
    draw_builder_row(box, key_ops, 'key', active_strip, "Key", active_strip.key_is_recording, is_color=0, record_prop_name="key_is_recording")
    draw_builder_row(box, rim_ops, 'rim', active_strip, "Rim/Hair", active_strip.rim_is_recording, is_color=0, record_prop_name="rim_is_recording")
    draw_builder_row(box, fill_ops, 'fill', active_strip, "Fill", active_strip.fill_is_recording, is_color=0, record_prop_name="fill_is_recording")

    # Background row
    if context.scene.using_gels_for_cyc:
        row = box.row(align=True)
        row.operator("alva_sequencer.gel_one_groups", text="", icon='PREFERENCES')
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
    row.operator("alva_sequencer.energy_groups", text="", icon='PREFERENCES')
    row.prop(active_strip, "energy_light", text="Effect", slider=True)
    row.prop(active_strip, "energy_speed", text="Speed", slider=True)
    row.prop(active_strip, "energy_scale", text="Scale", slider=True)

    # Effects row
    row = box.row(align=True)
    row.operator("alva_sequencer.stop_effect", text="", icon='CANCEL')
    for effect_id, operator, icon in zip(effect_ids, fx_ops, fx_icons):
        row.alert = active_strip.cue_builder_effect_id == effect_id
        row.operator(operator, text="", icon_value=icon)
        row.alert = 0


def draw_strip_flash(context, box, active_strip):
    row = box.row()
    #row.prop(active_strip, "flash_type_enum", expand=0, text="Method") Doesn't work yet
    
    if active_strip.flash_type_enum != 'option_use_controllers':
        draw_strip_flash_manual(context, box, active_strip)
    else: draw_strip_flash_controllers(context, box, active_strip)
    
    draw_strip_flash_footer(context, box, active_strip)

        
def draw_strip_flash_manual(context, box, active_strip):
    is_manual_enabled = (active_strip.flash_type_enum != 'option_use_nodes')
        
    row = box.row()
    row = box.label(text=f"Flash Up: {active_strip.flash_input_background}")
    row = box.row(align=True)
    row.enabled = is_manual_enabled
    row.prop(active_strip, "flash_input", text="")
    row.operator("alva_sequencer.flash_copy_down", text="", icon='DOWNARROW_HLT')
    
    row = box.row()
    row = box.label(text=f"Flash Down: {active_strip.flash_down_input_background}")
    row = box.row()
    row.enabled = is_manual_enabled
    row.prop(active_strip, "flash_down_input", text="")
    
    row = box.separator()
    

def draw_strip_flash_controllers(context, box, active_strip):
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


def draw_strip_flash_footer(context, box, active_strip):
    pcoll = preview_collections["main"]
    orb = pcoll["orb"]

    row = box.row(align=True)
    row.prop(active_strip, "flash_bias", text="Bias", slider=True)
    row.operator("alva_orb.orb", text="", icon_value=orb.icon_id).as_orb_id = 'option_flash'

    row = box.row()
    if active_strip.flash_bias > 0:
        row.label(text="Bias: Flash will come in slower and go out faster.")
    if active_strip.flash_bias < 0:
        row.label(text="Bias: Flash will come in faster and go out slower.")
    if active_strip.flash_bias == 0:
        row.label(text="Bias: Flash will come in and go out at same speed.")
    

def draw_strip_animation(context, column, box, active_strip):
    draw_text_or_group_input(context, box, active_strip, object=False)
    draw_parameters_mini(context, box, active_strip, use_slider=True, expand=True, text=False)
    box.separator()
    draw_play_bar(context, box)
    draw_footer_toggles(context, column, active_strip)


def draw_strip_trigger(context, box, active_strip):
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


def draw_strip_offset(context, box, active_strip):
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
    row.operator("alva_orb.orb", text="", icon_value=orb.icon_id).as_orb_id = 'option_offset'
    
    box.separator(factor=.01)