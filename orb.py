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
import time
import logging

from .updaters.sequencer_updaters import SequencerUpdaters as Updaters
from .utils.utils import Utils
from .utils.sequencer_mapping import StripMapping
from .utils.osc import OSC
from .assets.sli import SLI


'''
Any operator that talks to the console MUST ONLY call an Orb static method.
This is the ONLY place to check lighting console type inside operators. All
@staticmethods here are direct standins for operators, for organization.
'''


class Orb:
    @staticmethod
    def generate_macros_to_cues(self, context, strip='sound', enable=True):
        scene = context.scene
        console_mode = scene.scene_props.console_type_enum
        if hasattr(scene.sequence_editor, "active_strip") and scene.sequence_editor.active_strip is not None:
            active_strip = scene.sequence_editor.active_strip
        else:
            active_strip = scene

        if strip == 'sound':
            event_list = Utils.find_executor(scene, active_strip, 'event_list')
            start_macro = Utils.find_executor(scene, active_strip, 'start_macro')
            end_macro = Utils.find_executor(scene, active_strip, 'end_macro')
            start_cue = active_strip.str_start_cue
            end_cue = active_strip.str_start_cue

            if console_mode == 'option_eos':
                yield from Orb.Eos.manipulate_show_control(scene, event_list, start_macro, end_macro, start_cue, end_cue)
                yield None, "Orb complete."
            elif console_mode in ['option_ma3', 'option_ma2']:
                yield None, f"Button not supported for {console_mode} yet."
            else:
                SLI.SLI_assert_unreachable()

        elif strip == 'macro':
            Updaters.macro_update(active_strip, context)
            macro_number = Utils.find_executor(scene, active_strip, 'start_macro')
            text = active_strip.start_frame_macro_text
            is_final = not scene.strip_end_macros

            if console_mode == 'option_eos':
                yield from Orb.Eos.generate_macro_command(context, macro_number, text, first=True, final=is_final)
                yield None, "Orb complete."
            elif console_mode == 'option_ma3':
                yield None, "Button not supported for grandMA3 yet."
            elif console_mode == 'option_ma2':
                yield None, "Button not supported for grandMA2 yet."
            else:
                SLI.SLI_assert_unreachable()

            if scene.strip_end_macros:
                macro_number = Utils.find_executor(scene, active_strip, 'end_macro')
                text = active_strip.end_frame_macro_text

                if console_mode == 'option_eos':
                    yield from Orb.Eos.generate_macro_command(context, macro_number, text, first=False, final=True)
                    yield None, "Orb complete."
                elif console_mode == 'option_ma3':
                    yield None, "Button not supported for grandMA3 yet."
                elif console_mode == 'option_ma2':
                    yield None, "Button not supported for grandMA2 yet."
                else:
                    SLI.SLI_assert_unreachable()

        elif strip == 'flash':
            active_strip.flash_input = active_strip.flash_input
            active_strip.flash_down_input = active_strip.flash_down_input

            frame_rate = Utils.get_frame_rate(scene)
            strip_length_in_frames = active_strip.frame_final_duration
            strip_length_in_seconds = strip_length_in_frames / frame_rate
            bias = active_strip.flash_bias

            if console_mode == 'option_eos':
                m1_start_length = Orb.Eos.calculate_biased_start_length(bias, frame_rate, strip_length_in_frames)
                m1_text = f"{str(active_strip.flash_input_background)} Sneak Time {str(m1_start_length)} Enter "
                end_length = round((strip_length_in_seconds - m1_start_length), 1)
                m2_text = f"{str(active_strip.flash_down_input_background)} Sneak Time {str(end_length)} Enter"

                start_macro = Utils.find_executor(scene, active_strip, 'start_macro')
                end_macro = Utils.find_executor(scene, active_strip, 'end_macro')

                yield from Orb.Eos.generate_macro_command(context, start_macro, m1_text, first=True)
                yield from Orb.Eos.generate_macro_command(context, end_macro, m2_text, final=True)

                yield None, "Orb complete."
            elif console_mode == 'option_ma3':
                yield None, "Button not supported for grandMA3 yet."
            elif console_mode == 'option_ma2':
                yield None, "Button not supported for grandMA2 yet."
            else:
                SLI.SLI_assert_unreachable()
            
        elif strip == 'offset':
            macro = 'offset_macro'
            text = StripMapping.get_trigger_offset_start_map(scene, active_strip=active_strip)
            if active_strip.friend_list == "" or active_strip.osc_trigger == "":
                return {'CANCELLED', "Invalid text inputs."}
            
            macro = Utils.find_executor(scene, active_strip, 'start_macro')
            
            if console_mode == 'option_eos':
                yield from Orb.Eos.generate_macro_command(self, context, active_strip, macro, text, first=True, final=True)
                yield None, "Orb complete."
            elif console_mode == 'option_ma3':
                yield None, "Button not supported for grandMA3 yet."
            elif console_mode == 'option_ma2':
                yield None, "Button not supported for grandMA2 yet."
            else:
                SLI.SLI_assert_unreachable()
            return {'FINISHED'}
        
        elif strip == 'text':
            macro = context.space_data.text.text_macro
            active_text = context.space_data.text
            text_data = active_text.as_string()
            text_data = text_data.splitlines()
            
            if console_mode == 'option_eos':
                yield from Orb.Eos.generate_multiline_macro(self, context, scene, macro, text_data)
                yield None, "Orb complete."
            elif console_mode == 'option_ma3':
                yield None, "Button not supported for grandMA3 yet."
            elif console_mode == 'option_ma2':
                yield None, "Button not supported for grandMA2 yet."
            else:
                SLI.SLI_assert_unreachable()
            return {'FINISHED'}
            
        else:
            SLI.SLI_assert_unreachable()
            
            
            
    def render_strips(self, context, event):
        console_mode = context.scene.scene_props.console_type_enum
        
        if console_mode == 'option_eos':
            return Orb.Eos.render_strips(self, context, event)
        elif console_mode == 'option_ma3':
            self.report({'INFO'}, "Button not supported for grandMA3 yet.")
        elif console_mode == 'option_ma2':
            self.report({'INFO'}, "Button not supported for grandMA2 yet.")
        else:
            SLI.SLI_assert_unreachable()
        
    class Eos:
        @staticmethod
        def send_osc_with_delay(command, value="1", delay=0.5):
            OSC.send_osc_lighting(command, value)
            time.sleep(delay)

        ###################
        # ANIMATION STRIPS
        ###################
        @staticmethod
        def manipulate_show_control(scene, event_list, start_macro, end_macro, start_cue, end_cue, timecode=None):
            try:
                yield Orb.Eos.record_snapshot(scene), "Recording snapshot."
                yield Orb.Eos.save_console_file(scene), "Orb is running."

                yield Orb.Eos.delete_recreate_macro_enter_edit(start_macro), "Creating blank macro."
                yield Orb.Eos.type_event_list_number(event_list), "Typing event list number."
                yield Orb.Eos.type_internal_time(), "Internal Time"
                yield Orb.Eos.enter_timecode_or_just_enter(timecode), "Typing timecode for sync."
                yield Orb.Eos.type_event_list_number(event_list), "Typing event list number again."
                yield Orb.Eos.internal_enable_or_disable_foreground_live_execute_on_cue(start_cue, start_macro, "enable"), "Setting to foreground mode."

                yield Orb.Eos.delete_recreate_macro_enter_edit(end_macro), "Creating blank macro."
                yield Orb.Eos.type_event_list_number(event_list), "Typing event list number."
                yield Orb.Eos.type_internal_time(), "Internal Time"
                yield Orb.Eos.enter_timecode_or_just_enter(None), "Typing timecode for sync."
                yield Orb.Eos.type_event_list_number(event_list), "Typing event list number again."
                yield Orb.Eos.internal_enable_or_disable_foreground_live_execute_on_cue(end_cue, end_macro, "disable"), "Setting to foreground mode."

                yield Orb.Eos.reset_macro_key(), "Resetting macro key."
                yield Orb.Eos.restore_snapshot(scene), "Restoring your screen setup."

            except AttributeError as e:
                logging.error(f"Attribute error in manipulate_show_control: {e}")
                yield None, f"Attribute error: {e}"
            except ValueError as e:
                logging.error(f"Value error in manipulate_show_control: {e}")
                yield None, f"Value error: {e}"
            except RuntimeError as e:
                logging.error(f"Runtime error in manipulate_show_control: {e}")
                yield None, f"Runtime error: {e}"
            except Exception as e:
                logging.error(f"Unexpected error in manipulate_show_control: {e}")
                yield None, f"Unexpected error: {e}"
            
            
        @staticmethod
        def type_event_list_number(event_list_number):
            Orb.Eos.send_osc_with_delay("/eos/key/event")
            
            for digit in str(event_list_number):
                Orb.Eos.send_osc_with_delay(f"/eos/key/{digit}")
                
                
        @staticmethod    
        def type_internal_time():
            Orb.Eos.send_osc_with_delay("/eos/key/\\")
            Orb.Eos.send_osc_with_delay("/eos/key/internal")
            Orb.Eos.send_osc_with_delay("/eos/key/time")
            

        @staticmethod
        def enter_timecode_or_just_enter(timecode, is_delayed=False):
            if timecode:
                '''When animation-strip-start, make the macro start clock 
                at correct time per Blender's timeline'''  
                for digit in timecode:
                    Orb.Eos.send_osc_with_delay(f"/eos/key/{digit}", delay=0.2)
                time.sleep(0.5)
            Orb.Eos.send_osc_with_delay("/eos/key/enter")


        @staticmethod
        def internal_enable_or_disable_foreground_live_execute_on_cue(cue_number, macro_number, desired_state):
            Orb.Eos.send_osc_with_delay("/eos/key/\\")
            Orb.Eos.send_osc_with_delay("/eos/key/internal")
            Orb.Eos.send_osc_with_delay(f"/eos/key/{desired_state}")
            Orb.Eos.send_osc_with_delay("/eos/key/enter")
            Orb.Eos.send_osc_with_delay("/eos/key/select")
            Orb.Eos.send_osc_with_delay("/eos/softkey/3")  # "Foreground Mode" softkey
            Orb.Eos.send_osc_with_delay("/eos/key/enter")
            Orb.Eos.send_osc_with_delay("/eos/key/live")
            Orb.Eos.send_osc_with_delay("/eos/newcmd", f"Cue {str(cue_number)} Execute Macro {str(macro_number)} Enter Enter")

        @staticmethod
        def reset_macro_key():
            Orb.Eos.send_osc_with_delay("/eos/key/macro", "0")


        ####################
        # MULTI-LINE MACROS
        ####################
        @staticmethod
        def generate_multiline_macro(self, context, scene, macro, text_data):
            try:
                yield Orb.Eos.record_snapshot(scene), "Recording snapshot."
                yield Orb.Eos.save_console_file(scene), "Orb is running."
                yield Orb.Eos.delete_recreate_macro_enter_edit(macro), "Creating blank macro."
                yield Orb.Eos.reset_macro_key(), "Resetting macro key."
                yield Orb.Eos.type_tokens(text_data), "Typing macro contents"
                yield Orb.Eos.restore_snapshot(scene), "Restoring your screen setup."
            except AttributeError as e:
                logging.error(f"Attribute error in generate_multiline_macro: {e}")
                yield None, f"Attribute error: {e}"
            except ValueError as e:
                logging.error(f"Value error in generate_multiline_macro: {e}")
                yield None, f"Value error: {e}"
            except RuntimeError as e:
                logging.error(f"Runtime error in generate_multiline_macro: {e}")
                yield None, f"Runtime error: {e}"
            except Exception as e:
                logging.error(f"Unexpected error in generate_multiline_macro: {e}")
                yield None, f"Unexpected error: {e}"
            
            
        @staticmethod
        def type_tokens(text_data):
            for line in text_data:
                tokens = Utils.tokenize_macro_line(line)
                for address, argument in tokens:
                    Orb.Eos.send_osc_with_delay(address, argument, .2)
                    time.sleep(.1)

            Orb.Eos.send_osc_with_delay("/eos/softkey/6", "1", 0.1)  # "Done" softkey
            Orb.Eos.send_osc_with_delay("/eos/key/live", "1", 0.1)
            Orb.Eos.send_osc_with_delay("/eos/key/live", "0", 0.1)


        ###########################
        # SINGLE-LINE STRIP MACROS
        ###########################
        @staticmethod
        def generate_macro_command(context, macro_number, macro_text, first=False, final=False):
            try:
                if first:
                    yield Orb.Eos.record_snapshot(context.scene), "Recording snapshot."
                    yield Orb.Eos.save_console_file(context.scene), "Orb is running."

                yield Orb.Eos.initiate_macro(), "Initiating macro."
                yield Orb.Eos.type_macro_number(macro_number), "Typing macro number."
                yield Orb.Eos.learn_macro_and_exit(macro_text), "Learning macro and exiting."
                yield Orb.Eos.reset_macro_key(), "Resetting macro key."

                if final:
                    yield Orb.Eos.restore_snapshot(context.scene), "Restoring snapshot."
                    yield None, "Orb complete."
            except AttributeError as e:
                logging.error(f"Attribute error in generate_macro_command: {e}")
                yield None, f"Attribute error: {e}"
            except ValueError as e:
                logging.error(f"Value error in generate_macro_command: {e}")
                yield None, f"Value error: {e}"
            except RuntimeError as e:
                logging.error(f"Runtime error in generate_macro_command: {e}")
                yield None, f"Runtime error: {e}"
            except Exception as e:
                logging.error(f"Unexpected error in generate_macro_command: {e}")
                yield None, f"Unexpected error: {e}"


        @staticmethod
        def initiate_macro():
            Orb.Eos.send_osc_with_delay("/eos/key/live")
            Orb.Eos.send_osc_with_delay("/eos/key/live", "0", 0.5)
            Orb.Eos.send_osc_with_delay("/eos/key/learn", "Enter", 0.5)
            Orb.Eos.send_osc_with_delay("/eos/key/macro")

        @staticmethod
        def type_macro_number(macro_number):
            for digit in str(macro_number):
                Orb.Eos.send_osc_with_delay(f"/eos/key/{digit}", delay=0.2)
            Orb.Eos.send_osc_with_delay("/eos/key/enter", delay=0.1)
            Orb.Eos.send_osc_with_delay("/eos/key/enter")

        @staticmethod
        def learn_macro_and_exit(macro_text):
            Orb.Eos.send_osc_with_delay("/eos/newcmd", macro_text, 0.5)
            Orb.Eos.send_osc_with_delay("/eos/key/learn", "Enter")
            Orb.Eos.send_osc_with_delay("/eos/key/macro", "0")

        @staticmethod
        def calculate_biased_start_length(bias, frame_rate, strip_length_in_frames):
            # Normalize bias to a 0-1 scale
            normalized_bias = (bias + 49) / 98  # This will give 0 for -49 and 1 for 49
            
            # Calculate minimum and maximum start_length in seconds
            min_start_length = 1 / frame_rate  # 1 frame
            max_start_length = (strip_length_in_frames - 1) / frame_rate
            
            # Interpolate between min and max based on normalized bias
            biased_start_length = (min_start_length * (1 - normalized_bias)) + (max_start_length * normalized_bias)
            
            return round(biased_start_length, 1)
            

        ##################
        # COMMON UTILITIES
        ###################
        @staticmethod
        def save_console_file(scene):
            if not scene.is_armed_turbo:
                Orb.Eos.send_osc_with_delay("/eos/key/shift")
                Orb.Eos.send_osc_with_delay("/eos/key/update")
                Orb.Eos.send_osc_with_delay("/eos/key/shift", "0", 2)

        @staticmethod
        def record_snapshot(scene):
            snapshot = str(scene.orb_finish_snapshot)
            Orb.Eos.send_osc_with_delay("/eos/newcmd", f"Record Snapshot {snapshot} Enter Enter", 0.5)

        @staticmethod
        def restore_snapshot(scene):
            snapshot = str(scene.orb_finish_snapshot)
            Orb.Eos.send_osc_with_delay("/eos/newcmd", f"Snapshot {snapshot} Enter", 0.5)
      
        @staticmethod
        def delete_recreate_macro_enter_edit(macro_number):
            Orb.Eos.send_osc_with_delay("/eos/key/live")
            Orb.Eos.send_osc_with_delay("/eos/key/live", "0", 0.5)
            Orb.Eos.send_osc_with_delay("/eos/key/macro", "11 Enter", 0)
            Orb.Eos.send_osc_with_delay("/eos/key/macro", "11 Enter", 0.5)
            Orb.Eos.send_osc_with_delay("/eos/newcmd", f"Delete {str(macro_number)} Enter Enter", 0.5)
            Orb.Eos.send_osc_with_delay("/eos/newcmd", f"{str(macro_number)} Enter", 0.5)
            Orb.Eos.send_osc_with_delay("/eos/softkey/6", "1", 0.1)  # Edit" softkey
            
        
        ##############
        # OTHER STUFF
        ##############
        @staticmethod
        def make_qmeo(scene, frame_rate, start_frame, end_frame, cue_list):
            if hasattr(scene.sequence_editor, "active_strip") and scene.sequence_editor.active_strip is not None:
                active_strip = scene.sequence_editor.active_strip
            else:
                active_strip = scene

            event_list = Utils.find_executor(scene, active_strip, 'event_list')
            start_macro = Utils.find_executor(scene, active_strip, 'start_macro')
            end_macro = Utils.find_executor(scene, active_strip, 'end_macro')
            start_cue = active_strip.str_start_cue
            end_cue = active_strip.str_start_cue
            timecode = Utils.frame_to_timecode(active_strip.frame_start)

            yield from Orb.Eos.manipulate_show_control(scene, event_list, start_macro, end_macro, start_cue, end_cue, timecode)

            scene.scene_props.is_cue_baking = True
            Orb.Eos.update_label(scene, event_list, "Making a Qmeo! Escape to Cancel.")
            
            current_frame_number = scene.frame_current
            cue_duration = 1 / frame_rate
            cue_duration = round(cue_duration, 2)
            
            # Create a sorted list of frames.
            frames = list(range(int(start_frame), int(end_frame)))
            
            cue_duration = round(1 / frame_rate, 2)
            
            percentage_remaining = 100 / len(frames)
            percentage_steps = percentage_remaining
            
            rounded_remaining = round(percentage_remaining)
            
            Orb.Eos.update_label(scene, event_list, f"{str(rounded_remaining)}% Complete")

            if event_list:
                argument = f"Event {str(event_list)} / 1 Thru {str(end_frame)} Enter"

            wm = bpy.context.window_manager
            wm.progress_begin(0, 100)  # Start progress bar

            for i, frame in enumerate(frames):
                bpy.context.scene.frame_set(frame)
                bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
                
                current_frame_number = scene.frame_current
                
                argument = f"Record Cue {str(cue_list)} / {str(current_frame_number)} Time {str(cue_duration)} Enter Enter"
                
                if event_list:
                    timecode = Utils.frame_to_timecode(frame)
                    argument = f"{argument}, Event 1 / {str(frame)} Time {str(timecode)} Show_Control_Action Cue {str(frame)} Enter"

                percentage_remaining += percentage_steps
                rounded_remaining = round(percentage_remaining)
                Orb.Eos.update_label(scene, event_list, f"{str(rounded_remaining)}% Complete")
                print(f"{str(rounded_remaining)}% Complete")

                # Update progress bar
                wm.progress_update(i / len(frames) * 100)
                
                time.sleep(.1)
                
                OSC.send_osc_lighting("/eos/newcmd", argument)
            
            wm.progress_end()  # End progress bar
            scene.scene_props.str_bake_info = "Create Qmeo"    
            scene.scene_props.str_cue_bake_info = "Just Cues"
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
            scene.scene_props.is_cue_baking = False

        @staticmethod
        def update_label(scene, event_list, text):
            if event_list:
                scene.scene_props.str_bake_info = text
            else:
                scene.scene_props.str_cue_bake_info = text
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1) # Force UI redraw


        @staticmethod
        def render_strips(self, context, event):
            Orb.Eos.record_snapshot(context.scene)
            Orb.Eos.save_console_file(context.scene)

            all_maps = [
                (StripMapping.get_start_macro_map(context.scene), "Macro"),
                (StripMapping.get_end_macro_map(context.scene), "Macro"),
                (StripMapping.get_start_flash_macro_map(context.scene), "Macro"),
                (StripMapping.get_end_flash_macro_map(context.scene), "Macro"),
                (StripMapping.get_cue_map(context.scene), "Cue"),
                (StripMapping.get_offset_map(context.scene), "Macro")
            ]
            
            commands = []
            from .utils.event_utils import EventUtils
            event_object = EventUtils.find_relevant_clock_object(context.scene)
            if event_object == None:
                return {'CANCELLED'}
            event_list = Utils.find_executor(context.scene, context.scene, 'event_list')

            i = 1
            for action_map, description in all_maps:
                for frame in action_map:
                    actions = action_map[frame]
                    for label, index in actions:
                        fps = Utils.get_frame_rate(context.scene)
                        timecode = Utils.frame_to_timecode(frame, fps)
                        argument = f"Event {event_list} / {i} Time {timecode} Show_Control_Action {description} {index} Enter"
                        commands.append(argument)
                        i += 1
                        
            OSC.send_osc_lighting("/eos/key/blind", "1")
            OSC.send_osc_lighting("/eos/key/blind", "0")
            
            time.sleep(.5)
            
            OSC.send_osc_lighting("/eos/newcmd", f"Delete Event {event_list} / Enter Enter")
            time.sleep(.3)
            OSC.send_osc_lighting("/eos/newcmd", f"Event {event_list} / Enter Enter")
            
            for i in range(0, len(commands), 50):
                batch = commands[i:i+50]
                argument = ", ".join(batch)
                OSC.send_osc_lighting("/eos/newcmd", argument)
                time.sleep(.5)

            OSC.send_osc_lighting("/eos/key/live", "1")
            OSC.send_osc_lighting("/eos/key/live", "0")
            snapshot = str(context.scene.orb_finish_snapshot)
            OSC.send_osc_lighting("/eos/newcmd", f"Snapshot {snapshot} Enter")
            
            Orb.Eos.restore_snapshot(context.scene)

            bpy.ops.screen.animation_play()

            return {'FINISHED'}