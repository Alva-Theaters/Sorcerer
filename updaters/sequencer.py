# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import re
from functools import partial
import bpy
from bpy.props import *
from bpy.types import ColorSequence

from .common import CommonUpdaters as CommonUpdaters
from ..assets.dictionaries import Dictionaries as Dictionaries
from ..utils.osc import OSC
from ..utils.rna_utils import parse_channels
    

stop_updating_color = "No"
filter_color_strips = partial(filter, ColorSequence.__instancecheck__) 
animation_string = ""


class SequencerUpdaters:
    def timecode_clock_update_safety(self, context):
        '''
        Prevents user from setting timecode clock cue number to first cue on sequence 
        to prevent infinite looping on the console.'''
        sorted_strips = sorted([s for s in context.scene.sequence_editor.sequences_all if s.type == 'COLOR'], key=lambda s: s.frame_start)

        first_eos_cue_strip = None
        
        for strip in sorted_strips:
            if strip.my_settings.motif_type_enum == 'option_cue':
                first_eos_cue_strip = strip
                break

        if first_eos_cue_strip and first_eos_cue_strip.eos_cue_number == self.str_start_cue and self.str_start_cue:
                self.str_start_cue = ""
                print("Cue # for timecode clock cannot be equal to the first cue in the sequence. That will result in infinite looping. The console would go to cue " + str(self.str_start_cue) + " and then the timecode clock would start, and then the timecode clock would immediately call the first cue, thereby starting the timecode clock over again. This would repeat forever without advancing to the next frames.")
                return
                
        
    def replace_asterisk_with_sneak_time(macro_text, duration):
        if '*' in macro_text:
            macro_text = macro_text.replace('*', 'Sneak Time ' + str(duration))

        return macro_text


    def format_macro_text(macro_text):
        commands_to_replace = Dictionaries.commands_to_replace

        for cmd in commands_to_replace:
            if cmd in macro_text:
                macro_text = macro_text.replace(cmd, cmd.replace(' ', '_'))

        '''Courtesy fix in case user accidentally added * in bottom where it is nonsensical.
           We don't need to check is_start because if it was the top, it would have been replaced already.'''
        macro_text = macro_text.replace("*", "Time")

        if not macro_text.strip().lower().endswith('enter') and not macro_text.strip().lower().endswith('out'):
            macro_text += ' Enter'

        return macro_text         
                   
            
    def universal_macro_update(self, context, is_start):
        '''
        Universal macro updater for Macro strips. Just updates the read-only text.
        '''
        active_strip = context.scene.sequence_editor.active_strip
        
        if is_start:
            self.start_frame_macro_text = self.start_frame_macro_text_gui
            macro_text = self.start_frame_macro_text
        else:
            self.end_frame_macro_text = self.end_frame_macro_text_gui
            macro_text = self.end_frame_macro_text
        
        frame_rate = context.scene.render.fps / context.scene.render.fps_base
        strip_length_in_seconds_total = active_strip.frame_final_duration / frame_rate
        
        # Convert total seconds to minutes and fractional seconds format.
        minutes = int(strip_length_in_seconds_total // 60)
        seconds = strip_length_in_seconds_total % 60
        duration = "{:02d}:{:04.1f}".format(minutes, seconds)  
        
        if is_start:
            macro_text = SequencerUpdaters.replace_asterisk_with_sneak_time(macro_text, duration)

        macro_text = SequencerUpdaters.format_macro_text(macro_text)
        print(f"Macro text: {macro_text}\nis_start: {is_start}\n\n")
        if is_start:
            self.start_frame_macro_text = macro_text
        else:
            self.end_frame_macro_text = macro_text


    def macro_update(self, context):
        '''Uses the universal macro updater'''
        SequencerUpdaters.universal_macro_update(self, context, is_start=True)
        SequencerUpdaters.universal_macro_update(self, context, is_start=False)


    def update_flash_input(self, context, input_string, is_flash_down=False):
        '''Tries to interpret what the user is trying to input into the Flash strip text field.'''
        sequence_editor = context.scene.sequence_editor
        if sequence_editor and sequence_editor.active_strip and sequence_editor.active_strip.type == 'COLOR':
            active_strip = context.scene.sequence_editor.active_strip
            space_replacements = Dictionaries.space_replacements
            replacements = Dictionaries.replacements
            input_string = input_string.lower()

            # Apply space replacements first to combine common multi-word phrases into single tokens.
            for key, value in space_replacements.items():
                input_string = input_string.replace(key, value)

            # Replace hyphen between numbers with 'thru'.
            input_string = re.sub(r'(\d+)\s*-\s*(\d+)', r'\1 thru \2', input_string)
            
            # Replace commas followed by spaces with ' + '.
            input_string = re.sub(r',\s*', ' + ', input_string)
            
            # Insert space between letters and numbers.
            input_string = re.sub(r'(\D)(\d)', r'\1 \2', input_string)
            input_string = re.sub(r'(\d)(\D)', r'\1 \2', input_string)

            words = input_string.split()

            # Apply the main replacements.
            formatted_words = [replacements.get(word, word) for word in words]

            # Handle specific cases like adding "Channel" at the start if needed.
            if formatted_words and formatted_words[0].isdigit():
                formatted_words.insert(0, "Channel")

            formatted_command = " ".join(formatted_words)

            # Replace any double "at".
            formatted_command = re.sub(r'\bat at\b', "at", formatted_command)
            
            new_formatted_words = []
            i = 0
            while i < len(formatted_words):
                new_formatted_words.append(formatted_words[i])
                if (i + 1 < len(formatted_words) and
                        formatted_words[i].isdigit() and
                        formatted_words[i + 1].isdigit()):
                    # Check if the next word is 'at' to avoid 'at at'.
                    if formatted_words[i + 1] != 'at':
                        new_formatted_words.append("at")
                i += 1

            formatted_command = " ".join(new_formatted_words)

            formatted_command = formatted_command.replace("at at", "at")
            
            if ' at ' not in formatted_command and 'Palette' not in formatted_command and 'Preset' not in formatted_command and not formatted_command.endswith(' at'):
                formatted_command += ' at Full' if not is_flash_down else ' at 0'
            
            final_command = str(formatted_command)
            if is_flash_down:
                active_strip.flash_down_input_background = final_command
                active_strip.flash_down_input_background = formatted_command
            else:
                active_strip.flash_input_background = final_command
                active_strip.flash_input_background = formatted_command
            active_strip.flash_prefix = "eos"
            
    @staticmethod
    def flash_input_updater(self, context):
        SequencerUpdaters.update_flash_input(self, context, self.flash_input)
        
    @staticmethod
    def flash_down_input_updater(self, context):
        SequencerUpdaters.update_flash_input(self, context, self.flash_down_input, is_flash_down=True)


    def motif_property_updater(self, context): ##
        '''This needs to loop through all strips sharing the same Motif Name that have 
           Linking turned on and it needs to set all the active properties to the 
           active_strip's. Also needs to only do this for the active_strip's strip type 
           enum.
        '''
        active_strip = context.scene.sequence_editor.active_strip
        
        if self != active_strip:
            return  # Stops infinite recursion


    def motif_type_enum_updater(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        if not active_strip:
            return
        
        motif_type_enum = context.scene.sequence_editor.active_strip.my_settings.motif_type_enum
        
        global stop_updating_color
        if stop_updating_color == "No" and context.scene.is_updating_strip_color:
            
            if motif_type_enum == "option_macro":
                active_strip.color = (1, 0, 0)
            elif motif_type_enum == "option_cue":
                active_strip.color = (0, 0, .5)
            elif motif_type_enum == "option_flash":
                active_strip.color = (1, 1, 0)
            elif motif_type_enum == "option_animation":
                active_strip.color = (0, 1, 0)
            elif motif_type_enum == "option_offset":
                active_strip.color = (.5, 1, 1)
            else:
                active_strip.color = (1, 1, 1)
                
            
    def color_palette_color_updater(self, context): ##
        '''This needs to be completely rewritten to incorporate ColorSplitter. See Sequencer 1.1
           to see how this is supposed to work. Currently completely deactivated.'''
        return          
                         
      
    def light_updater(self, context, light_value, param):
        '''This really needs to be incorporated into the depsgraph. This is for Cue Builder.'''
        if context.screen:
            if self.mute:
                return
            
            if param in ["cyc_one_light", "cyc_two_light", "cyc_three_light", "cyc_four_light"]:
                groups = parse_channels(getattr(context.scene, f"{param}_groups"))
                channels = []
                submasters = []
            else:
                groups = parse_channels(getattr(context.scene, f"{param}_groups"))
                channels = parse_channels(getattr(context.scene, f"{param}_channels"))
                submasters = parse_channels(getattr(context.scene, f"{param}_submasters"))

            light_str = str(light_value)

            for group in groups:
                address = "/eos/newcmd"
                argument = f"Group {group} at {light_str.zfill(2)} Enter"
                OSC.send_osc_lighting(address, argument)

            for chan in channels:
                address = "/eos/newcmd"
                argument = f"Chan {chan} at {light_str.zfill(2)} Enter"
                OSC.send_osc_lighting(address, argument)

            for sub in submasters:
                address = "/eos/newcmd"
                argument = f"Sub {sub} at {light_str.zfill(2)} Enter"
                OSC.send_osc_lighting(address, argument)
        return


    def effect_updater(self, context, effect_value, effect_type): ##
        '''This really needs to be incorporated into the depsgraph. This is for Cue Builder.'''
        if context.screen:
            if self.mute:
                return

            effect_str = str(effect_value)
            address = "/eos/newcmd"
            argument = f"Effect {self.cue_builder_effect_id} {effect_type} {effect_str.zfill(2)} Enter"
            OSC.send_osc_lighting(address, argument)
        return


    def key_light_updater(self, context):
        SequencerUpdaters.light_updater(self, context, self.key_light, "key_light")

    def rim_light_updater(self, context):
        SequencerUpdaters.light_updater(self, context, self.rim_light, "rim_light")

    def fill_light_updater(self, context):
        SequencerUpdaters.light_updater(self, context, self.fill_light, "fill_light")

    def texture_light_updater(self, context):
        SequencerUpdaters.light_updater(self, context, self.texture_light, "texture_light")

    def band_light_updater(self, context):
        SequencerUpdaters.light_updater(self, context, self.band_light, "band_light")

    def accent_light_updater(self, context):
        SequencerUpdaters.light_updater(self, context, self.accent_light, "accent_light")

    def energy_light_updater(self, context):
        SequencerUpdaters.light_updater(self, context, self.energy_light, "energy_light")

    def energy_speed_updater(self, context):
        SequencerUpdaters.effect_updater(self, context, self.energy_speed, "Rate")

    def energy_scale_updater(self, context):
        SequencerUpdaters.effect_updater(self, context, self.energy_scale, "Scale")

    def cyc_light_updater(self, context):
        SequencerUpdaters.light_updater(self, context, self.gel_one_light, "cyc_light")

    def background_light_updater(self, context):
        SequencerUpdaters.light_updater(self, context, self.background_light_one, "cyc_one_light")

    def background_two_light_updater(self, context):
        SequencerUpdaters.light_updater(self, context, self.background_light_two, "cyc_two_light")

    def background_three_light_updater(self, context):
        SequencerUpdaters.light_updater(self, context, self.background_light_three, "cyc_three_light")

    def background_four_light_updater(self, context):
        SequencerUpdaters.light_updater(self, context, self.background_light_four, "cyc_four_light")


    def selected_stage_object_updater(self, context):
        sound_object = bpy.data.objects[self.selected_stage_object.name]
        sound_object.speaker_list.clear()
        speaker_objects = [obj for obj in bpy.data.objects if obj.type == 'SPEAKER' and obj.users > 0 and obj.int_speaker_number != 0]

        new_speaker_list = sound_object.speaker_list.add()
        new_speaker_list.name = self.name  # Set to active sound strip's name
    
        for speaker in speaker_objects:
            new_speaker = new_speaker_list.speakers.add()
            new_speaker.speaker_number = speaker.int_speaker_number
            new_speaker.speaker_name = speaker.name
            new_speaker.speaker_pointer = speaker