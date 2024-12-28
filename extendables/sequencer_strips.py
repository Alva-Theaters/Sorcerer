# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

'''
To make your own custom Sorcerer sequencer strip type:

    1. Copy/paste the code below directly into Blender's text editor.
    2. Modify it as needed.
    3. Run it.
    4. Select your new strip type in the M menu that pops up when you have  color strip selected.

The strip types below are built into Sorcerer. Similar to Blender's bpy, Sorcerer's spy is
utilized both by the internal source code (as seen here) and by end-users extending the application.
'''

from bpy import spy

from ..as_ui.strip_types import (
    draw_strip_macro,
    draw_strip_cue,
    draw_strip_animation,
    draw_strip_flash,
    draw_strip_trigger
)
from ..utils.sequencer_utils import BiasCalculator


class SEQUENCER_ST_macro(spy.types.SequencerStrip):
    as_idname = 'option_macro'
    as_label = "Macro Strip"
    as_description = "Build and fire macros based on strip length"
    as_icon = 'FILE_TEXT'

    event_type = 'macro'
    options = {'ORB'}

    def draw(context, column, box, active_strip):
        draw_strip_macro(context, box, active_strip)

    def poll(value):
        return value != 0


    def get_start_frame(strip):
        return strip.frame_start
    
    def get_start_value(strip):
        return strip.int_start_macro
    
    
    def get_end_frame(strip):
        return strip.frame_final_end
    
    def get_end_value(strip):
        return strip.int_end_macro
    

    def form_osc(strip, value):
        address = f"/eos/macro/{value}"
        argument = "fire"
        return address, argument
    

class SEQUENCER_ST_cue(spy.types.SequencerStrip):
    as_idname = 'option_cue'
    as_label = "Cue Strip"
    as_description = "Use strip length to define cue duration"
    as_icon = 'PLAY'

    event_type = 'cue'
    options = {'ORB'}

    def draw(context, column, box, active_strip):
        draw_strip_cue(context, box, active_strip)

    
    def poll(value):
        return value != ""  # strip.eos_cue_number is actually a string, so user can specify cue list
    

    def get_start_frame(strip):
        return strip.frame_start

    def get_start_value(strip):
        return strip.eos_cue_number
    

    def form_osc(strip, value):
        address = "/eos/cue"
        argument = value
        return address, argument
    

class SEQUENCER_ST_flash(spy.types.SequencerStrip):
    as_idname = 'option_flash'
    as_label = "Flash Strip"
    as_description = "Flash intensity up and down with strip length"
    as_icon = 'LIGHT_SUN'

    event_type = 'macro'
    options = {'ORB'}

    def draw(context, column, box, active_strip):
        draw_strip_flash(context,  box, active_strip)


    def poll(value):
        return value != ""


    def get_start_frame(strip):
        return strip.frame_start
    
    def get_start_value(strip):
        return strip.int_start_macro
    
    
    def get_end_frame(strip):
        bias = strip.flash_bias
        strip_length_in_frames = strip.frame_final_duration

        bias_in_frames = BiasCalculator(bias, strip_length_in_frames).execute()

        start_frame = strip.frame_start
        end_flash_macro_frame = start_frame + bias_in_frames
        return int(round(end_flash_macro_frame))
    
    def get_end_value(strip):
        return strip.int_end_macro
    

    def form_osc(strip, value):
        address = f"/eos/macro/{value}"
        argument = "fire"
        return address, argument


class SEQUENCER_ST_animation(spy.types.SequencerStrip):
    as_idname = 'option_animation'
    as_label = "Animation Strip"
    as_description = "Use keyframes, or inverted cues, to control parameters"
    as_icon = 'IPO_BEZIER'

    def draw(context, column, box, active_strip):
        draw_strip_animation(context, column, box, active_strip)


class SEQUENCER_ST_trigger(spy.types.SequencerStrip):
    as_idname = 'option_trigger'
    as_label = "Trigger Strip"
    as_description = "Send discrete trigger at strip's start and/or end frame. Eos does not record this"
    as_icon = 'SETTINGS'

    options = {'EVENT_MANAGER'}

    def draw(context, column, box, active_strip):
        draw_strip_trigger(context, box, active_strip)


    def poll(value):
        return value != ""


    def get_start_frame(strip):
        return strip.frame_start
    
    def get_start_value(strip):
        return strip.osc_trigger
    
    
    def get_end_frame(strip):
        return strip.frame_final_end
    
    def get_end_value(strip):
        return strip.osc_trigger_end
    

    def form_osc(strip, value):
        address = strip.trigger_prefix
        argument = value
        return address, argument


strips = [
    SEQUENCER_ST_macro,
    SEQUENCER_ST_cue,
    SEQUENCER_ST_flash,
    SEQUENCER_ST_animation,
    SEQUENCER_ST_trigger
]


def register():
    for strip in strips:
        spy.utils.as_register_class(strip)

    
def unregister():
    for strip in reversed(strips):
        spy.utils.as_unregister_class(strip)