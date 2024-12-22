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


class SEQUENCER_ST_macro(spy.types.SequencerStrip):
    as_idname = 'option_macro'
    as_description = "Build and fire macros based on strip length"
    as_icon = 'FILE_TEXT'

    def draw(self, context):
        pass


class SEQUENCER_ST_cue(spy.types.SequencerStrip):
    as_idname = 'option_cue'
    as_description = "Use strip length to define cue duration"
    as_icon = 'PLAY'

    def draw(self, context):
        pass


class SEQUENCER_ST_flash(spy.types.SequencerStrip):
    as_idname = 'option_flash'
    as_description = "Flash intensity up and down with strip length"
    as_icon = 'LIGHT_SUN'

    def draw(self, context):
        pass


class SEQUENCER_ST_animation(spy.types.SequencerStrip):
    as_idname = 'option_animation'
    as_description = "Use keyframes, or inverted cues, to control parameters"
    as_icon = 'IPO_BEZIER'

    def draw(self, context):
        pass


class SEQUENCER_ST_trigger(spy.types.SequencerStrip):
    as_idname = 'option_trigger'
    as_description = "Send discrete trigger at strip's start and/or end frame. Eos does not record this"
    as_icon = 'SETTINGS'

    def draw(self, context):
        pass


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