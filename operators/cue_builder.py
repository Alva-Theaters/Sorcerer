# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Operator
from ..utils.rna_utils import parse_channels
from ..utils.osc import OSC

# TODO This entire script is a DRY abomination.


class SEQUENCER_OT_update_cue_builder(Operator):
    bl_idname = "alva_sequencer.update_builder"
    bl_label = "Update builder"
    bl_description = "Send all builder settings to console"
    
    def execute(self, context):
        scene = context.scene
        active_strip = scene.sequence_editor.active_strip
        
        active_strip.key_light = active_strip.key_light
        active_strip.rim_light = active_strip.rim_light
        active_strip.fill_light = active_strip.fill_light
        if scene.using_gels_for_cyc:
            active_strip.background_light_one = active_strip.background_light_one
            active_strip.background_light_two = active_strip.background_light_two
            active_strip.background_light_three = active_strip.background_light_three
            active_strip.background_light_four = active_strip.background_light_four
        else:
            active_strip.gel_one_light = active_strip.gel_one_light
        active_strip.texture_light = active_strip.texture_light
        active_strip.band_light = active_strip.band_light
        active_strip.accent_light = active_strip.accent_light
        active_strip.energy_light = active_strip.energy_light
        active_strip.energy_speed = active_strip.energy_speed
        active_strip.energy_scale = active_strip.energy_scale
        
        return {'FINISHED'}
    
    
class SEQUENCER_OT_record_cue(Operator):
    bl_idname = "alva_sequencer.record_cue"
    bl_label = "Record cue"
    bl_description = "Record the cue on the console as is"
    
    def execute(self, context):
        scene = context.scene
        active_strip = scene.sequence_editor.active_strip
        address = "/eos/newcmd"
        argument = f"Record Cue {active_strip.eos_cue_number} Enter"
        OSC.send_osc_lighting(address, argument)
        return {'FINISHED'}
    
 
# Focus key
class SEQUENCER_OT_focus_one(Operator):
    bl_idname = "alva_sequencer.focus_one"
    bl_label = "Preset 1"
    bl_description = "Set to preset one, possibly for general look"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(1, 'key', active_strip.key_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_two(Operator):
    bl_idname = "alva_sequencer.focus_two"
    bl_label = "Preset 2"
    bl_description = "Set to preset two, possibly for side lighting"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(2, 'key', active_strip.key_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_three(Operator):
    bl_idname = "alva_sequencer.focus_three"
    bl_label = "Preset 3"
    bl_description = "Set to preset three, possibly for paramount lighting"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(3, 'key', active_strip.key_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_four(Operator):
    bl_idname = "alva_sequencer.focus_four"
    bl_label = "Preset 4"
    bl_description = "Set to preset four, possibly for McCandless lighting"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(4, 'key', active_strip.key_is_recording, context)
        return {'FINISHED'}
    
class SEQUENCER_OT_focus_five(Operator):
    bl_idname = "alva_sequencer.focus_five"
    bl_label = "Preset 5"
    bl_description = "Set to preset five"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(5, 'key', active_strip.key_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_six(Operator):
    bl_idname = "alva_sequencer.focus_six"
    bl_label = "Preset 6"
    bl_description = "Set to preset six"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(6, 'key', active_strip.key_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_seven(Operator):
    bl_idname = "alva_sequencer.focus_seven"
    bl_label = "Preset 7"
    bl_description = "Set to preset seven"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(7, 'key', active_strip.key_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_eight(Operator):
    bl_idname = "alva_sequencer.focus_eight"
    bl_label = "Preset 8"
    bl_description = "Set to preset eight"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(8, 'key', active_strip.key_is_recording, context)
        return {'FINISHED'}
    
class SEQUENCER_OT_focus_nine(Operator):
    bl_idname = "alva_sequencer.focus_nine"
    bl_label = "Preset 9"
    bl_description = "Set to preset nine"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(9, 'key', active_strip.key_is_recording, context)
        return {'FINISHED'}


# Focus rim.
class SEQUENCER_OT_focus_rim_one(Operator):
    bl_idname = "alva_sequencer.focus_rim_one"
    bl_label = "Preset 1"
    bl_description = "Set to preset one, possibly for wide wash"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(1, 'rim', active_strip.rim_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_rim_two(Operator):
    bl_idname = "alva_sequencer.focus_rim_two"
    bl_label = "Preset 2"
    bl_description = "Set to preset two, possibly for SR wash"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(2, 'rim', active_strip.rim_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_rim_three(Operator):
    bl_idname = "alva_sequencer.focus_rim_three"
    bl_label = "Preset 3"
    bl_description = "Set to preset three, possibly for SL wash"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(3, 'rim', active_strip.rim_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_rim_four(Operator):
    bl_idname = "alva_sequencer.focus_rim_four"
    bl_label = "Preset 4"
    bl_description = "Set to preset four, possibly for CS"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(4, 'rim', active_strip.rim_is_recording, context)
        return {'FINISHED'}
    
class SEQUENCER_OT_focus_rim_five(Operator):
    bl_idname = "alva_sequencer.focus_rim_five"
    bl_label = "Preset 5"
    bl_description = "Set to preset five"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(5, 'rim', active_strip.rim_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_rim_six(Operator):
    bl_idname = "alva_sequencer.focus_rim_six"
    bl_label = "Preset 6"
    bl_description = "Set to preset six"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(6, 'rim', active_strip.rim_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_rim_seven(Operator):
    bl_idname = "alva_sequencer.focus_rim_seven"
    bl_label = "Preset 7"
    bl_description = "Set to preset seven"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(7, 'rim', active_strip.rim_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_rim_eight(Operator):
    bl_idname = "alva_sequencer.focus_rim_eight"
    bl_label = "Preset 8"
    bl_description = "Set to preset eight"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(8, 'rim', active_strip.rim_is_recording, context)
        return {'FINISHED'}
    
class SEQUENCER_OT_focus_rim_nine(Operator):
    bl_idname = "alva_sequencer.focus_rim_nine"
    bl_label = "Preset 9"
    bl_description = "Set to preset nine"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(9, 'rim', active_strip.rim_is_recording, context)
        return {'FINISHED'}


# Focus fill
class SEQUENCER_OT_focus_fill_one(Operator):
    bl_idname = "alva_sequencer.focus_fill_one"
    bl_label = "Preset 1"
    bl_description = "Set to preset one"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(1, 'fill', active_strip.fill_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_fill_two(Operator):
    bl_idname = "alva_sequencer.focus_fill_two"
    bl_label = "Preset 2"
    bl_description = "Set to preset two"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(2, 'fill', active_strip.fill_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_fill_three(Operator):
    bl_idname = "alva_sequencer.focus_fill_three"
    bl_label = "Preset 3"
    bl_description = "Set to preset three"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(3, 'fill', active_strip.fill_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_fill_four(Operator):
    bl_idname = "alva_sequencer.focus_fill_four"
    bl_label = "Preset 4"
    bl_description = "Set to preset four"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(4, 'fill', active_strip.fill_is_recording, context)
        return {'FINISHED'}
    
class SEQUENCER_OT_focus_fill_five(Operator):
    bl_idname = "alva_sequencer.focus_fill_five"
    bl_label = "Preset 5"
    bl_description = "Set to preset five"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(5, 'fill', active_strip.fill_is_recording, context)
        return {'FINISHED'}
    
class SEQUENCER_OT_focus_fill_six(Operator):
    bl_idname = "alva_sequencer.focus_fill_six"
    bl_label = "Preset 6"
    bl_description = "Set to preset six"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(6, 'fill', active_strip.fill_is_recording, context)
        return {'FINISHED'}
    
class SEQUENCER_OT_focus_fill_seven(Operator):
    bl_idname = "alva_sequencer.focus_fill_seven"
    bl_label = "Preset 7"
    bl_description = "Set to preset seven"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(7, 'fill', active_strip.fill_is_recording, context)
        return {'FINISHED'}
    
class SEQUENCER_OT_focus_fill_eight(Operator):
    bl_idname = "alva_sequencer.focus_fill_eight"
    bl_label = "Preset 8"
    bl_description = "Set to preset eight"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(8, 'fill', active_strip.fill_is_recording, context)
        return {'FINISHED'}
    
class SEQUENCER_OT_focus_fill_nine(Operator):
    bl_idname = "alva_sequencer.focus_fill_nine"
    bl_label = "Preset 9"
    bl_description = "Set to preset nine"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(9, 'fill', active_strip.fill_is_recording, context)
        return {'FINISHED'}


# Focus texture.
class SEQUENCER_OT_focus_texture_one(Operator):
    bl_idname = "alva_sequencer.focus_texture_one"
    bl_label = "Preset 1"
    bl_description = "Set to preset one"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(1, 'texture', active_strip.texture_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_texture_two(Operator):
    bl_idname = "alva_sequencer.focus_texture_two"
    bl_label = "Preset 2"
    bl_description = "Set to preset two"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(2, 'texture', active_strip.texture_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_texture_three(Operator):
    bl_idname = "alva_sequencer.focus_texture_three"
    bl_label = "Preset 3"
    bl_description = "Set to preset three"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(3, 'texture', active_strip.texture_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_texture_four(Operator):
    bl_idname = "alva_sequencer.focus_texture_four"
    bl_label = "Preset 4"
    bl_description = "Set to preset four"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(4, 'texture', active_strip.texture_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_texture_five(Operator):
    bl_idname = "alva_sequencer.focus_texture_five"
    bl_label = "Preset 5"
    bl_description = "Set to preset five"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(5, 'texture', active_strip.texture_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_texture_six(Operator):
    bl_idname = "alva_sequencer.focus_texture_six"
    bl_label = "Preset 6"
    bl_description = "Set to preset six"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(6, 'texture', active_strip.texture_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_texture_seven(Operator):
    bl_idname = "alva_sequencer.focus_texture_seven"
    bl_label = "Preset 7"
    bl_description = "Set to preset seven"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(7, 'texture', active_strip.texture_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_texture_eight(Operator):
    bl_idname = "alva_sequencer.focus_texture_eight"
    bl_label = "Preset 8"
    bl_description = "Set to preset eight"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(8, 'texture', active_strip.texture_is_recording, context)
        return {'FINISHED'}
    
class SEQUENCER_OT_focus_texture_nine(Operator):
    bl_idname = "alva_sequencer.focus_texture_nine"
    bl_label = "Preset 9"
    bl_description = "Set to preset nine"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(9, 'texture', active_strip.texture_is_recording, context)
        return {'FINISHED'}


# Focus band.
class SEQUENCER_OT_focus_band_one(Operator):
    bl_idname = "alva_sequencer.focus_band_one"
    bl_label = "Preset 1"
    bl_description = "Set to preset one"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(1, 'band', active_strip.band_is_recording, context)
        return {'FINISHED'}  
    
class SEQUENCER_OT_focus_band_two(Operator):
    bl_idname = "alva_sequencer.focus_band_two"
    bl_label = "Preset 2"
    bl_description = "Set to preset two"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(2, 'band', active_strip.band_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_band_three(Operator):
    bl_idname = "alva_sequencer.focus_band_three"
    bl_label = "Preset 3"
    bl_description = "Set to preset three"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(3, 'band', active_strip.band_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_band_four(Operator):
    bl_idname = "alva_sequencer.focus_band_four"
    bl_label = "Preset 4"
    bl_description = "Set to preset four"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(4, 'band', active_strip.band_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_band_five(Operator):
    bl_idname = "alva_sequencer.focus_band_five"
    bl_label = "Preset 5"
    bl_description = "Set to preset five"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(5, 'band', active_strip.band_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_band_six(Operator):
    bl_idname = "alva_sequencer.focus_band_six"
    bl_label = "Preset 6"
    bl_description = "Set to preset six"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(6, 'band', active_strip.band_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_band_seven(Operator):
    bl_idname = "alva_sequencer.focus_band_seven"
    bl_label = "Preset 7"
    bl_description = "Set to preset seven"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(7, 'band', active_strip.band_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_band_eight(Operator):
    bl_idname = "alva_sequencer.focus_band_eight"
    bl_label = "Preset 8"
    bl_description = "Set to preset eight"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(8, 'band', active_strip.band_is_recording, context)
        return {'FINISHED'}
    
class SEQUENCER_OT_focus_band_nine(Operator):
    bl_idname = "alva_sequencer.focus_band_nine"
    bl_label = "Preset 9"
    bl_description = "Set to preset nine"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(9, 'band', active_strip.band_is_recording, context)
        return {'FINISHED'}
    

# Focus accent.
class SEQUENCER_OT_focus_accent_one(Operator):
    bl_idname = "alva_sequencer.focus_accent_one"
    bl_label = "Preset 1"
    bl_description = "Set to preset one"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(1, 'accent', active_strip.accent_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_accent_two(Operator):
    bl_idname = "alva_sequencer.focus_accent_two"
    bl_label = "Preset 2"
    bl_description = "Set to preset two"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(2, 'accent', active_strip.accent_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_accent_three(Operator):
    bl_idname = "alva_sequencer.focus_accent_three"
    bl_label = "Preset 3"
    bl_description = "Set to preset three"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(3, 'accent', active_strip.accent_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_accent_four(Operator):
    bl_idname = "alva_sequencer.focus_accent_four"
    bl_label = "Preset 4"
    bl_description = "Set to preset four"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(4, 'accent', active_strip.accent_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_accent_five(Operator):
    bl_idname = "alva_sequencer.focus_accent_five"
    bl_label = "Preset 5"
    bl_description = "Set to preset five"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(5, 'accent', active_strip.accent_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_accent_six(Operator):
    bl_idname = "alva_sequencer.focus_accent_six"
    bl_label = "Preset 6"
    bl_description = "Set to preset six"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(6, 'accent', active_strip.accent_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_accent_seven(Operator):
    bl_idname = "alva_sequencer.focus_accent_seven"
    bl_label = "Preset 7"
    bl_description = "Set to preset seven"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(7, 'accent', active_strip.accent_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_accent_eight(Operator):
    bl_idname = "alva_sequencer.focus_accent_eight"
    bl_label = "Preset 8"
    bl_description = "Set to preset eight"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(8, 'accent', active_strip.accent_is_recording, context)
        return {'FINISHED'}
    
class SEQUENCER_OT_focus_accent_nine(Operator):
    bl_idname = "alva_sequencer.focus_accent_nine"
    bl_label = "Preset 9"
    bl_description = "Set to preset nine"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(9, 'accent', active_strip.accent_is_recording, context)
        return {'FINISHED'}


# Focus cyc.
class SEQUENCER_OT_focus_cyc_one(Operator):
    bl_idname = "alva_sequencer.focus_cyc_one"
    bl_label = "Preset 1"
    bl_description = "Set to preset one"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(1, 'cyc', active_strip.cyc_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_cyc_two(Operator):
    bl_idname = "alva_sequencer.focus_cyc_two"
    bl_label = "Preset 2"
    bl_description = "Set to preset two"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(2, 'cyc', active_strip.cyc_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_cyc_three(Operator):
    bl_idname = "alva_sequencer.focus_cyc_three"
    bl_label = "Preset 3"
    bl_description = "Set to preset three"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(3, 'cyc', active_strip.cyc_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_cyc_four(Operator):
    bl_idname = "alva_sequencer.focus_cyc_four"
    bl_label = "Preset 4"
    bl_description = "Set to preset four"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(4, 'cyc', active_strip.cyc_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_cyc_five(Operator):
    bl_idname = "alva_sequencer.focus_cyc_five"
    bl_label = "Preset 5"
    bl_description = "Set to preset five"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(5, 'cyc', active_strip.cyc_is_recording, context)
        return {'FINISHED'}

class SEQUENCER_OT_focus_cyc_six(Operator):
    bl_idname = "alva_sequencer.focus_cyc_six"
    bl_label = "Preset 6"
    bl_description = "Set to preset six"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(6, 'cyc', active_strip.cyc_is_recording, context)
        return {'FINISHED'}
    
class SEQUENCER_OT_focus_cyc_seven(Operator):
    bl_idname = "alva_sequencer.focus_cyc_seven"
    bl_label = "Preset 7"
    bl_description = "Set to preset seven"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(7, 'cyc', active_strip.cyc_is_recording, context)
        return {'FINISHED'}
    
class SEQUENCER_OT_focus_cyc_eight(Operator):
    bl_idname = "alva_sequencer.focus_cyc_eight"
    bl_label = "Preset 8"
    bl_description = "Set to preset eight"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(8, 'cyc', active_strip.cyc_is_recording, context)
        return {'FINISHED'} 
    
class SEQUENCER_OT_focus_cyc_nine(Operator):
    bl_idname = "alva_sequencer.focus_cyc_nine"
    bl_label = "Preset 9"
    bl_description = "Set to preset nine"
    
    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        send_cue_builder_group_command(9, 'cyc', active_strip.cyc_is_recording, context)
        return {'FINISHED'} 
 
 
# Effects.
class SEQUENCER_OT_focus_energy(Operator):
    bl_label = "Effect"
    bl_description = "Set to specified effect"
    
    def execute(self, context):
        scene = context.scene
        active_strip = scene.sequence_editor.active_strip
        
        if context.screen:
            groups = parse_channels(scene.energy_light_groups)
            active_strip.cue_builder_effect_id = str(self.effect_number)
            
            for group in groups:
                address = "/eos/newcmd"
                argument = f"Group {group} Effect {self.effect_number + scene.cue_builder_id_offset} Enter"
                OSC.send_osc_lighting(address, argument)
        return {'FINISHED'}

class SEQUENCER_OT_focus_energy_one(SEQUENCER_OT_focus_energy):
    bl_idname = "alva_sequencer.focus_energy_one"
    bl_label = "Effect 1"
    effect_number = 1

class SEQUENCER_OT_focus_energy_two(SEQUENCER_OT_focus_energy):
    bl_idname = "alva_sequencer.focus_energy_two"
    bl_label = "Effect 2"
    effect_number = 2

class SEQUENCER_OT_focus_energy_three(SEQUENCER_OT_focus_energy):
    bl_idname = "alva_sequencer.focus_energy_three"
    bl_label = "Effect 3"
    effect_number = 3

class SEQUENCER_OT_focus_energy_four(SEQUENCER_OT_focus_energy):
    bl_idname = "alva_sequencer.focus_energy_four"
    bl_label = "Effect 4"
    effect_number = 4

class SEQUENCER_OT_focus_energy_five(SEQUENCER_OT_focus_energy):
    bl_idname = "alva_sequencer.focus_energy_five"
    bl_label = "Effect 5"
    effect_number = 5

class SEQUENCER_OT_focus_energy_six(SEQUENCER_OT_focus_energy):
    bl_idname = "alva_sequencer.focus_energy_six"
    bl_label = "Effect 6"
    effect_number = 6

class SEQUENCER_OT_focus_energy_seven(SEQUENCER_OT_focus_energy):
    bl_idname = "alva_sequencer.focus_energy_seven"
    bl_label = "Effect 7"
    effect_number = 7

class SEQUENCER_OT_focus_energy_eight(SEQUENCER_OT_focus_energy):
    bl_idname = "alva_sequencer.focus_energy_eight"
    bl_label = "Effect 8"
    effect_number = 8

class SEQUENCER_OT_focus_energy_nine(SEQUENCER_OT_focus_energy):
    bl_idname = "alva_sequencer.focus_energy_nine"
    bl_label = "Effect 9"
    effect_number = 9

class SEQUENCER_OT_focus_energy_ten(SEQUENCER_OT_focus_energy):
    bl_idname = "alva_sequencer.focus_energy_ten"
    bl_label = "Effect 10"
    effect_number = 10

class SEQUENCER_OT_focus_energy_eleven(SEQUENCER_OT_focus_energy):
    bl_idname = "alva_sequencer.focus_energy_eleven"
    bl_label = "Effect 11"
    effect_number = 11

class SEQUENCER_OT_focus_energy_twelve(SEQUENCER_OT_focus_energy):
    bl_idname = "alva_sequencer.focus_energy_twelve"
    bl_label = "Effect 12"
    effect_number = 12

class SEQUENCER_OT_focus_energy_thirteen(SEQUENCER_OT_focus_energy):
    bl_idname = "alva_sequencer.focus_energy_thirteen"
    bl_label = "Effect 13"
    effect_number = 13

class SEQUENCER_OT_focus_energy_fourteen(SEQUENCER_OT_focus_energy):
    bl_idname = "alva_sequencer.focus_energy_fourteen"
    bl_label = "Effect 14"
    effect_number = 14

    
def send_cue_builder_group_command(id, group_type, recording, context):
    scene = context.scene
    active_strip = scene.sequence_editor.active_strip
    groups = parse_channels(getattr(scene, "{}_light_groups".format(group_type)))

    if not recording:
        command_suffix = "Preset " + str(id + scene.cue_builder_id_offset) + " Enter"
    else:
        command_suffix = "Record Preset " + str(id + scene.cue_builder_id_offset) + " Enter Enter"

    address = "/eos/newcmd"
    argument_parts = ["Group " + str(group) + " " + command_suffix for group in groups]
    argument = " + ".join(argument_parts)
    OSC.send_osc_lighting(address, argument)

    setattr(active_strip, f"cue_builder_{group_type}_id", str(id))
    
class SEQUENCER_OT_stop_effect(Operator):
    bl_idname = "alva_sequencer.stop_effect"
    bl_label = ""
    bl_description = "Stop effect"
    
    def execute(self, context):
        scene = context.scene
        active_strip = scene.sequence_editor.active_strip
        
        if context.screen:
            groups = parse_channels(scene.energy_light_groups)
            active_strip.cue_builder_effect_id = ""
            
            for group in groups:
                address = "/eos/newcmd"
                argument = str("Group " + str(group) + " Effect Enter")
                ip_address = context.scene.scene_props.str_osc_ip_address
                port = context.scene.scene_props.int_osc_port
                OSC.send_osc_lighting(address, argument)
        return {'FINISHED'}
    

# Channel list pop-ups.    
class SEQUENCER_OT_key_groups(Operator):
    bl_idname = "alva_sequencer.key_groups"
    bl_label = "Settings"
    bl_description = "Set groups for key light"
    
    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=300)

    def draw(self, context):
        active_strip = context.scene.sequence_editor.active_strip

        self.layout.prop(context.scene, "key_light_groups", text="Groups")
        self.layout.prop(context.scene, "key_light_channels", text="Channels")
        self.layout.prop(context.scene, "key_light_submasters", text="Submasters")
        self.layout.prop(active_strip, "key_light_slow")
     
class SEQUENCER_OT_rim_groups(Operator):
    bl_idname = "alva_sequencer.rim_groups"
    bl_label = "Settings"
    bl_description = "Set groups for rim light"
    
    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=300)

    def draw(self, context):
        active_strip = context.scene.sequence_editor.active_strip

        self.layout.prop(context.scene, "rim_light_groups", text="Groups")
        self.layout.prop(context.scene, "rim_light_channels", text="Channels")
        self.layout.prop(context.scene, "rim_light_submasters", text="Submasters")
        self.layout.prop(active_strip, "rim_light_slow")
              
class SEQUENCER_OT_fill_groups(Operator):
    bl_idname = "alva_sequencer.fill_groups"
    bl_label = "Settings"
    bl_description = "Set groups for fill light"
    
    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=300)

    def draw(self, context):
        active_strip = context.scene.sequence_editor.active_strip

        self.layout.prop(context.scene, "fill_light_groups", text="Groups")
        self.layout.prop(context.scene, "fill_light_channels", text="Channels")
        self.layout.prop(context.scene, "fill_light_submasters", text="Submasters")
        self.layout.prop(active_strip, "fill_light_slow")
             
class SEQUENCER_OT_texture_groups(Operator):
    bl_idname = "alva_sequencer.texture_groups"
    bl_label = "Settings"
    bl_description = "Set groups for texture light"
    
    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=300)

    def draw(self, context):
        active_strip = context.scene.sequence_editor.active_strip

        self.layout.prop(context.scene, "texture_light_groups", text="Groups")
        self.layout.prop(context.scene, "texture_light_channels", text="Channels")
        self.layout.prop(context.scene, "texture_light_submasters", text="Submasters")
        self.layout.prop(active_strip, "texture_light_slow")
             
class SEQUENCER_OT_band_groups(Operator):
    bl_idname = "alva_sequencer.band_groups"
    bl_label = "Settings"
    bl_description = "Set groups for band light"
    
    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=300)

    def draw(self, context):
        active_strip = context.scene.sequence_editor.active_strip

        self.layout.prop(context.scene, "band_light_groups", text="Groups")
        self.layout.prop(context.scene, "band_light_channels", text="Channels")
        self.layout.prop(context.scene, "band_light_submasters", text="Submasters")
        self.layout.prop(active_strip, "band_light_slow")
           
class SEQUENCER_OT_accent_groups(Operator):
    bl_idname = "alva_sequencer.accent_groups"
    bl_label = "Settings"
    bl_description = "Set groups for accent light"
    
    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=300)

    def draw(self, context):
        active_strip = context.scene.sequence_editor.active_strip

        self.layout.prop(context.scene, "accent_light_groups", text="Groups")
        self.layout.prop(context.scene, "accent_light_channels", text="Channels")
        self.layout.prop(context.scene, "accent_light_submasters", text="Submasters")
        self.layout.prop(active_strip, "accent_light_slow")
        
class SEQUENCER_OT_energy_groups(Operator):
    bl_idname = "alva_sequencer.energy_groups"
    bl_label = "Settings"
    bl_description = "Set groups for energy light"
    
    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=300)

    def draw(self, context):
        active_strip = context.scene.sequence_editor.active_strip

        self.layout.prop(context.scene, "energy_light_groups", text="Groups")
        self.layout.prop(context.scene, "energy_light_channels", text="Channels")
        self.layout.prop(context.scene, "energy_light_submasters", text="Submasters")
        self.layout.prop(active_strip, "energy_light_slow")
        
class SEQUENCER_OT_gel_one_groups(Operator):
    bl_idname = "alva_sequencer.gel_one_groups"
    bl_label = "Settings"
    bl_description = "Set groups for gel 1 light"
    
    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        scene = context.scene
        return context.window_manager.invoke_props_dialog(self, width=300)

    def draw(self, context):
        scene = context.scene
        if not scene.using_gels_for_cyc:
            active_strip = context.scene.sequence_editor.active_strip
            self.layout.prop(context.scene, "cyc_light_groups", text="Groups")
            self.layout.prop(context.scene, "cyc_light_channels", text="Channels")
            self.layout.prop(context.scene, "cyc_light_submasters", text="Submasters")
            self.layout.prop(active_strip, "cyc_light_slow")
        else:
            self.layout.prop(context.scene, "cyc_one_light_groups", text="Gel 1")
            self.layout.prop(context.scene, "cyc_two_light_groups", text="Gel 2")
            self.layout.prop(context.scene, "cyc_three_light_groups", text="Gel 3")
            self.layout.prop(context.scene, "cyc_four_light_groups", text="Gel 4")


cue_builder_operators = [
    SEQUENCER_OT_update_cue_builder,
    SEQUENCER_OT_record_cue,

    SEQUENCER_OT_focus_one,
    SEQUENCER_OT_focus_two,
    SEQUENCER_OT_focus_three,
    SEQUENCER_OT_focus_four,
    SEQUENCER_OT_focus_five,
    SEQUENCER_OT_focus_six,
    SEQUENCER_OT_focus_seven,
    SEQUENCER_OT_focus_eight,
    SEQUENCER_OT_focus_nine,

    SEQUENCER_OT_focus_rim_one,
    SEQUENCER_OT_focus_rim_two,
    SEQUENCER_OT_focus_rim_three,
    SEQUENCER_OT_focus_rim_four,
    SEQUENCER_OT_focus_rim_five,
    SEQUENCER_OT_focus_rim_six,
    SEQUENCER_OT_focus_rim_seven,
    SEQUENCER_OT_focus_rim_eight,
    SEQUENCER_OT_focus_rim_nine,

    SEQUENCER_OT_focus_fill_one,
    SEQUENCER_OT_focus_fill_two,
    SEQUENCER_OT_focus_fill_three,
    SEQUENCER_OT_focus_fill_four,
    SEQUENCER_OT_focus_fill_five,
    SEQUENCER_OT_focus_fill_six,
    SEQUENCER_OT_focus_fill_seven,
    SEQUENCER_OT_focus_fill_eight,
    SEQUENCER_OT_focus_fill_nine,

    SEQUENCER_OT_focus_texture_one,
    SEQUENCER_OT_focus_texture_two,
    SEQUENCER_OT_focus_texture_three,
    SEQUENCER_OT_focus_texture_four,
    SEQUENCER_OT_focus_texture_five,
    SEQUENCER_OT_focus_texture_six,
    SEQUENCER_OT_focus_texture_seven,
    SEQUENCER_OT_focus_texture_eight,
    SEQUENCER_OT_focus_texture_nine,

    SEQUENCER_OT_focus_band_one,
    SEQUENCER_OT_focus_band_two,
    SEQUENCER_OT_focus_band_three,
    SEQUENCER_OT_focus_band_four,
    SEQUENCER_OT_focus_band_five,
    SEQUENCER_OT_focus_band_six,
    SEQUENCER_OT_focus_band_seven,
    SEQUENCER_OT_focus_band_eight,
    SEQUENCER_OT_focus_band_nine,

    SEQUENCER_OT_focus_accent_one,
    SEQUENCER_OT_focus_accent_two,
    SEQUENCER_OT_focus_accent_three,
    SEQUENCER_OT_focus_accent_four,
    SEQUENCER_OT_focus_accent_five,
    SEQUENCER_OT_focus_accent_six,
    SEQUENCER_OT_focus_accent_seven,
    SEQUENCER_OT_focus_accent_eight,
    SEQUENCER_OT_focus_accent_nine,

    SEQUENCER_OT_focus_cyc_one,
    SEQUENCER_OT_focus_cyc_two,
    SEQUENCER_OT_focus_cyc_three,
    SEQUENCER_OT_focus_cyc_four,
    SEQUENCER_OT_focus_cyc_five,
    SEQUENCER_OT_focus_cyc_six,
    SEQUENCER_OT_focus_cyc_seven,
    SEQUENCER_OT_focus_cyc_eight,
    SEQUENCER_OT_focus_cyc_nine,

    SEQUENCER_OT_focus_energy_one,
    SEQUENCER_OT_focus_energy_two,
    SEQUENCER_OT_focus_energy_three,
    SEQUENCER_OT_focus_energy_four,
    SEQUENCER_OT_focus_energy_five,
    SEQUENCER_OT_focus_energy_six,
    SEQUENCER_OT_focus_energy_seven,
    SEQUENCER_OT_focus_energy_eight,
    SEQUENCER_OT_focus_energy_nine,
    SEQUENCER_OT_focus_energy_ten,
    SEQUENCER_OT_focus_energy_eleven,
    SEQUENCER_OT_focus_energy_twelve,
    SEQUENCER_OT_focus_energy_thirteen,
    SEQUENCER_OT_focus_energy_fourteen,

    SEQUENCER_OT_stop_effect,

    SEQUENCER_OT_key_groups,
    SEQUENCER_OT_rim_groups,
    SEQUENCER_OT_fill_groups,
    SEQUENCER_OT_texture_groups,
    SEQUENCER_OT_band_groups,
    SEQUENCER_OT_accent_groups,
    SEQUENCER_OT_energy_groups,
    SEQUENCER_OT_gel_one_groups
]


def register():
    from bpy.utils import register_class
    for cls in cue_builder_operators:
        register_class(cls)
        

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(cue_builder_operators):
        unregister_class(cls)