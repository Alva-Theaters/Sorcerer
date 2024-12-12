# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import time

from ..utils.osc import OSC

SENSITIVITY = 0.002
UPPER_TARGET = 100
LOWER_TARGET = 0

stored_time = 0


class PropertiesUpdaters:
    @staticmethod
    def fader_bar_updater(self, context):
        '''My job is to emulate the fader bar on a video switcher, but for ETC 
           Eos cues. I do it by figuring out how fast the slider is moving by 
           then guessing how long it will take to complete, and by then converting 
           those guesses into a constant stream of "Go_to_Cue 1 Sneak Time [my guess]
           Enter". The guess starts out with a big number and becomes a smaller and
           smaller number as the slider gets closer to completing. I keep track of
           the slider's direction with cue_list.t_bar_target. That avoids 
           accidentally flipping program and preview on a false start.'''
        scene = context.scene.scene_props
        cue_list = context.scene.cue_lists[scene.cue_lists_index]

        current_value = cue_list.int_t_bar
        last_value = scene.int_fader_bar_memory
        current_time = time.time()
        preview_cue = cue_list.cues[cue_list.int_preview_index].int_number
        program_cue = cue_list.cues[cue_list.int_program_index].int_number
        
        if cue_list.int_t_bar == cue_list.t_bar_target:
            PropertiesUpdaters.swap_preview_and_program(cue_list)
            cue_list.t_bar_target = LOWER_TARGET if cue_list.t_bar_target == UPPER_TARGET else UPPER_TARGET
            cue_list.int_velocity_multiplier *= -1  # to reverse how we detect false starts
            scene.int_fader_bar_memory = current_value
            return
        
        if not PropertiesUpdaters.check_time(scene, current_time):
            scene.int_fader_bar_memory = current_value
            return
        
        global stored_time
        
        time_elapsed = current_time - stored_time
        sneak_time, velocity = PropertiesUpdaters.find_sneak_time_and_velocity(current_value, last_value, time_elapsed, cue_list.int_velocity_multiplier)
        
        if (velocity * cue_list.int_velocity_multiplier) < 0:
            # Not sure why the following if-statements work correctly, but they do.
            if not cue_list.is_progressive:
                OSC.send_osc_lighting("/eos/newcmd", f"Go_to_Cue {cue_list.int_cue_list_number} / {preview_cue} Time {abs(sneak_time)} Enter")
            else:
                OSC.send_osc_lighting("/eos/newcmd", f"Go_to_Cue {cue_list.int_cue_list_number} / {program_cue} Time {sneak_time} Enter")
        else:
            if not cue_list.is_progressive:
                OSC.send_osc_lighting("/eos/newcmd", f"Go_to_Cue {cue_list.int_cue_list_number} / {program_cue} Time {sneak_time} Enter")
            else:
                OSC.send_osc_lighting("/eos/newcmd", f"Go_to_Cue {cue_list.int_cue_list_number} / {preview_cue} Time {sneak_time} Enter")
        
        scene.int_fader_bar_memory = current_value
        stored_time = current_time
     
     
    @staticmethod
    def format_time_in_seconds(seconds):
        return f"{seconds:.2f}"   
    
    
    @staticmethod
    def check_time(scene, current_time):
        '''My job is to stop the current update if the last one was too soon ago'''
        global stored_time
        time_difference = current_time - stored_time
        if abs(time_difference) < SENSITIVITY or abs(time_difference) > 1:
            stored_time = current_time
            return False
        return True
    
    
    @staticmethod
    def find_sneak_time_and_velocity(current_value, last_value, time_elapsed, velocity_multiplier):
        '''My job is to figure out what the sneak time should be right this instant'''
        current_velocity = PropertiesUpdaters.find_velocity(current_value, last_value, time_elapsed)
        sneak_time = PropertiesUpdaters.velocity_to_time_remaining(current_value, current_velocity, velocity_multiplier)
        return round(sneak_time, 2), current_velocity
    
    
    @staticmethod   
    def find_velocity(current_value, last_value, time_elapsed):
        '''My job is to figure out how fast the slider is moving'''
        if time_elapsed == 0:
            return 0
        return (current_value - last_value) / time_elapsed


    @staticmethod
    def velocity_to_time_remaining(current_value, current_velocity, velocity_multiplier, target_value=100):
        '''My job is to guess how long it will take for the slider to
           finish at its current speed'''
        if current_velocity == 0:
            return float('inf')  # Prevent division by zero
        
        # Adjust for direction using velocity_multiplier
        if velocity_multiplier < 0:
            return (current_value - 0) / abs(current_velocity)
        else:
            return (target_value - current_value) / current_velocity
        

    def swap_preview_and_program(cue_list):
        if not cue_list.is_progressive:
            temp = cue_list.int_preview_index
            cue_list.int_preview_index = cue_list.int_program_index
            cue_list.int_program_index = temp
            
        else:
            cue_list.int_program_index = (cue_list.int_preview_index)
            cue_list.int_preview_index = (cue_list.int_program_index + 1)