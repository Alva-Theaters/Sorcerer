# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
import time
import logging

from .updaters.sequencer import SequencerUpdaters as Updaters
from .utils.event_utils import EventUtils
from .utils.orb_utils import find_addresses, tokenize_macro_line, find_executor
from .utils.sequencer_mapping import StripMapping
from .cpv.publish import Publish
from .utils.osc import OSC
from .assets.sli import SLI


WHAT_DOES_THIS_DO = """
This code is for a set of operators identified in the UI with a purple orb icon.

These operators are responsible for automating repetitive tasks on the lighting console.

For example, 
    - Creating qmeos
    - Creating macros needed for Sorcerer-to-console synchronization
    - Programming channel-specific cue-timings (discreet timing) on the console's cues

This uses "yield"/generator because we want the user to be able to escape prematurely with the 
ESC key.

The generator is set up within a mix-in class in the operators/orb.py file. That is where the 
bpy.types.Operator classes are, as well. We use multiple operators instead of just one to
make the tooltips and other properties simple to change between instances of the operator.
"""


def invoke_orb(Operator, context, bl_idname):
    active_item = sequencer_strip_or_scene(context.scene)
    Console = get_lighting_console_instance(context.scene)

    yield from Console.prepare_console_for_automation()
    yield from complete_operator_specific_automation(context, active_item, Operator, Console, bl_idname)
    yield from Console.restore_console_to_normal_following_automation()


def sequencer_strip_or_scene(scene):
    if hasattr(scene.sequence_editor, "active_strip") and scene.sequence_editor.active_strip is not None:
        return scene.sequence_editor.active_strip
    else:
        return scene


def get_lighting_console_instance(scene):
    console = Publish.find_installed_lighting_console_data_class(scene.scene_props.console_type_enum)
    return console(scene)  # Create instance.


def complete_operator_specific_automation(context, active_item, Operator, Console, bl_idname):
    if not active_item:
        return {'CANCELLED'}, "No item found."
    
    if not hasattr(active_item, 'str_parent_name'):
        return {'CANCELLED'}, "Invalid item selected."
    
    if not Operator:
        return {'CANCELLED'}, "Invalid operator found."
    
    if not Console:
        return {'CANCELLED'}, "Invalid lighting console selected."
    
    if not bl_idname:
        return {'CANCELLED'}, "No bl_idname found."
    
    executors = {
        'alva_orb.cue_strip': lambda: CueStrip(context, active_item).execute(Console),
        'alva_orb.sound_strip': lambda: SoundStrip(context.scene, active_item).execute(Console),
        'alva_orb.macro_strip': lambda: MacroStrip(context, active_item).execute(Console),
        'alva_orb.flash_strip': lambda: FlashStrip(context, active_item).execute(Console),
        'alva_orb.offset_strip': lambda: OffsetStrip(context, active_item).execute(Console),
        'alva_orb.strips_sync': lambda: StripsSync(context).execute(Console)
    }

    executor = executors.get(bl_idname)
    if executor is None:
        return {'CANCELLED'}, f"Invalid bl_idname: {bl_idname}."
    
    yield from executor()

    return {'FINISHED'}, "Orb complete."
            

class CueStrip:
    def __init__(self, context, active_item):
        self.scene = context.scene
        self.active_item = active_item
        self.cue_duration = self.find_cue_duration()
        self.cue_number = active_item.eos_cue_number

    def find_cue_duration(self):
        frame_rate = EventUtils.get_frame_rate(self.scene)
        strip_length_in_seconds_total = int(round(self.active_item.frame_final_duration / frame_rate))
        minutes = strip_length_in_seconds_total // 60
        seconds = strip_length_in_seconds_total % 60
        return "{:02d}:{:02d}".format(minutes, seconds)
    

    def execute(self, Console):
        slowed_properties = ["key_light_slow", "rim_light_slow", "fill_light_slow", "texture_light_slow", "band_light_slow",
                 "accent_light_slow", "energy_light_slow", "cyc_light_slow"]
        
        Console.key("live")
        Console.cmd(f"Cue {str(self.cue_number)} Time {self.cue_duration} Enter")

        for slowed_prop_name in slowed_properties:
            yield self.record_discreet_time(slowed_prop_name, Console), "Recording property"

        Console.key("update")
        Console.key("enter")

        self.active_item.name = f"Cue {str(self.cue_number)}"

    def record_discreet_time(self, slowed_prop_name, Console):
        discrete_time = str(getattr(self.active_item, slowed_prop_name))

        if discrete_time == "0.0":
            return
        
        param = slowed_prop_name.replace("_slow", "")

        # Importing here for dependency reasons
        from .utils.rna_utils import parse_channels
        from .utils.cpv_utils import simplify_channels_list

        groups = parse_channels(getattr(self.scene, f"{param}_groups"))
        channels = parse_channels(getattr(self.scene, f"{param}_channels"))
        submasters = parse_channels(getattr(self.scene, f"{param}_submasters"))

        if groups:
            groups_str = simplify_channels_list(groups)
            argument = f"Group {groups_str} Time {discrete_time.zfill(2)} Enter"
            Console.cmd(argument)

        if channels:
            channels_str = simplify_channels_list(channels)
            argument = f"Chan {channels_str} Time {discrete_time.zfill(2)} Enter"
            Console.cmd(argument)

        if submasters:
            submasters_str = simplify_channels_list(submasters)
            argument = f"Sub {submasters_str} Time {discrete_time.zfill(2)} Enter"
            Console.cmd(argument)


class SoundStrip:
    def __init__(self, scene, active_item):
        self.event_list = find_executor(scene, active_item, 'event_list')
        self.start_macro = find_executor(scene, active_item, 'start_macro')
        self.end_macro = find_executor(scene, active_item, 'end_macro')
        self.start_cue = active_item.str_start_cue
        self.end_cue = active_item.str_start_cue

    def execute(self, console_mode, Operator):
        return {'FINISHED'}
    

class MacroStrip:
    def __init__(self, context, active_item):
        scene = context.scene
        Updaters.macro_update(active_item, context) # Ensure the textual input has been parsed
        self.macro_number = find_executor(scene, active_item, 'start_macro')
        self.text = active_item.start_frame_macro_text
        self.is_final = not scene.strip_end_macros

        if scene.strip_end_macros:
            self.macro_end_number = find_executor(scene, active_item, 'end_macro')
            self.text_end = active_item.end_frame_macro_text

    def execute(self, Console):
        return {'FINISHED'}


class FlashStrip:
    def __init__(self, context, active_item):
        scene = context.scene
        active_item.flash_input = active_item.flash_input
        active_item.flash_down_input = active_item.flash_down_input

        from .utils.event_utils import EventUtils
        frame_rate = EventUtils.get_frame_rate(scene)
        strip_length_in_frames = active_item.frame_final_duration
        strip_length_in_seconds = strip_length_in_frames / frame_rate
        bias = active_item.flash_bias

        # m1_start_length = Orb.Eos.calculate_biased_start_length(bias, frame_rate, strip_length_in_frames)
        # m1_text = f"{str(active_item.flash_input_background)} Sneak Time {str(m1_start_length)} Enter "
        # end_length = round((strip_length_in_seconds - m1_start_length), 1)
        # m2_text = f"{str(active_item.flash_down_input_background)} Sneak Time {str(end_length)} Enter"

        # start_macro = find_executor(scene, active_item, 'start_macro')
        # end_macro = find_executor(scene, active_item, 'end_macro')

    def execute(self, Console):
        return {'FINISHED'}


class OffsetStrip:
    def __init__(self, context, active_item):
        self.scene = context.scene
        self.macro = 'offset_macro'
        self.text = StripMapping.get_trigger_offset_start_map(self.scene, active_item=active_item)
        if active_item.friend_list == "" or active_item.osc_trigger == "":
            return {'CANCELLED', "Invalid text inputs."}
        
        #macro = find_executor(scene, active_item, 'start_macro')

    def execute(self, Console):
        return {'FINISHED'}


class TextStrips:
    def __init__(self, context, active_item):
        macro = context.space_data.text.text_macro
        active_text = context.space_data.text
        text_data = active_text.as_string()
        text_data = text_data.splitlines()

    def execute(self, Console):
        return {'FINISHED'}

            
class StripsSync:
    BATCH_LIMIT = 50

    def __init__(self, context):
        from .utils.event_utils import EventUtils
        self.event_object, sound_strip = EventUtils.find_relevant_clock_objects(context.scene)
        self.event_list = self.event_object.int_event_list
        self.scene = context.scene

        self.all_maps = [
            (StripMapping.get_start_macro_map(self.scene), "Macro"),
            (StripMapping.get_end_macro_map(self.scene), "Macro"),
            (StripMapping.get_start_flash_macro_map(self.scene), "Macro"),
            (StripMapping.get_end_flash_macro_map(self.scene), "Macro"),
            (StripMapping.get_cue_map(self.scene), "Cue"),
            (StripMapping.get_offset_map(self.scene), "Macro")
        ]

        self.event_strings = self.strips_to_events()

    def strips_to_event_strings(self):
        fps = EventUtils.get_frame_rate(self.scene)

        event_strings = []
        i = 1
        for event_map, event_type in self.all_maps:
            for frame in event_map:
                actions = event_map[frame]
                for label, index in actions:
                    timecode = EventUtils.frame_to_timecode(frame, fps)
                    event_strings.append(f"Event {self.event_list} / {i} Time {timecode} Show_Control_Action {event_type} {index} Enter")
                    i += 1
        return event_strings


    def execute(self, Console):
        Console.key("blind")
        Console.cmd(f"Delete Event {self.event_list} / Enter Enter")
        Console.cmd(f"Event {self.event_list} / Enter Enter")
        yield from self.batch_send_event_strings()
        bpy.ops.screen.animation_play()
    
    def batch_send_event_strings(self, Console):
        for i in range(0, len(self.event_strings), 50):
            yield self.send_event_string(i, Console), "Sending event command"

    def send_event_string(self, i, Console):
        batch = self.event_strings[i:i+self.BATCH_LIMIT]
        argument = ", ".join(batch)
        Console.cmd(argument)

        
#     class Eos:
#         @staticmethod
#         def send_osc_with_delay(command, value="1", delay=0.5):
#             OSC.send_osc_lighting(command, value)
#             #time.sleep(delay)

#         @staticmethod
#         def save_console_file(scene):
#             if not scene.is_console_saving:
#                 Orb.Eos.send_osc_with_delay("/eos/key/shift")
#                 Orb.Eos.send_osc_with_delay("/eos/key/update")
#                 Orb.Eos.send_osc_with_delay("/eos/key/shift", "0", 2)

#         @staticmethod
#         def record_snapshot(scene):
#             snapshot = str(scene.orb_finish_snapshot)
#             Orb.Eos.send_osc_with_delay("/eos/newcmd", f"Record Snapshot {snapshot} Enter Enter", 0.5)

#         @staticmethod
#         def restore_snapshot(scene):
#             snapshot = str(scene.orb_finish_snapshot)
#             Orb.Eos.send_osc_with_delay("/eos/newcmd", f"Snapshot {snapshot} Enter", 0.5)
      
#         @staticmethod
#         def delete_recreate_macro_enter_edit(macro_number, live=True):
#             if live:
#                 Orb.Eos.send_osc_with_delay("/eos/key/live")
#                 Orb.Eos.send_osc_with_delay("/eos/key/live", "0", 0.5)
#             Orb.Eos.send_osc_with_delay("/eos/key/macro", "11 Enter", 0)
#             Orb.Eos.send_osc_with_delay("/eos/key/macro", "11 Enter", 0.5)
#             Orb.Eos.send_osc_with_delay("/eos/newcmd", f"Delete {str(macro_number)} Enter Enter", 0.5)
#             Orb.Eos.send_osc_with_delay("/eos/newcmd", f"{str(macro_number)} Enter", 0.5)
#             Orb.Eos.send_osc_with_delay("/eos/softkey/6", "1", 0.1)  # Edit" softkey


#         #-------------------------------------------------------------------------------------------------------------------------------------------
#         '''Show control'''
#         #-------------------------------------------------------------------------------------------------------------------------------------------
#         @staticmethod
#         def manipulate_show_control(scene, event_list, start_macro, end_macro, start_cue, end_cue, timecode=None, execute_on_cues=True):
#             try:
#                 yield Orb.Eos.record_snapshot(scene), "Recording snapshot."
#                 yield Orb.Eos.save_console_file(scene), "Orb is running."

#                 yield Orb.Eos.delete_recreate_macro_enter_edit(start_macro), "Creating blank macro."
#                 yield Orb.Eos.type_event_list_number(event_list), "Typing event list number."
#                 yield Orb.Eos.type_internal_time(), "Internal Time"
#                 yield Orb.Eos.enter_timecode_or_just_enter(timecode), "Typing timecode for sync."
#                 yield Orb.Eos.type_event_list_number(event_list), "Typing event list number again."
#                 yield Orb.Eos.internal_enable_or_disable_foreground("enable"), "Setting to foreground mode."

#                 yield Orb.Eos.delete_recreate_macro_enter_edit(end_macro, live=False), "Creating blank macro."
#                 yield Orb.Eos.type_event_list_number(event_list), "Typing event list number."
#                 yield Orb.Eos.type_internal_time(), "Internal Time"
#                 yield Orb.Eos.enter_timecode_or_just_enter(None), "Typing timecode for sync."
#                 yield Orb.Eos.type_event_list_number(event_list), "Typing event list number again."
#                 yield Orb.Eos.internal_enable_or_disable_foreground("disable"), "Setting to foreground mode."

#                 yield Orb.Eos.live_and_execute_on_cue(start_cue, start_macro, execute_on_cues), "Setting start cue executor"
#                 yield Orb.Eos.live_and_execute_on_cue(end_cue, end_macro, execute_on_cues), "Setting end cue executor"

#                 yield Orb.Eos.reset_macro_key(), "Resetting macro key."
#                 yield Orb.Eos.restore_snapshot(scene), "Restoring your screen setup."

#             except AttributeError as e:
#                 logging.error(f"Attribute error in manipulate_show_control: {e}")
#                 yield None, f"Attribute error: {e}"
#             except ValueError as e:
#                 logging.error(f"Value error in manipulate_show_control: {e}")
#                 yield None, f"Value error: {e}"
#             except RuntimeError as e:
#                 logging.error(f"Runtime error in manipulate_show_control: {e}")
#                 yield None, f"Runtime error: {e}"
#             except Exception as e:
#                 logging.error(f"Unexpected error in manipulate_show_control: {e}")
#                 yield None, f"Unexpected error: {e}"
            
            
#         @staticmethod
#         def type_event_list_number(event_list_number):
#             Orb.Eos.send_osc_with_delay("/eos/key/event", delay=.2)
            
#             for digit in str(event_list_number):
#                 Orb.Eos.send_osc_with_delay(f"/eos/key/{digit}", delay=.2)
                
#         @staticmethod    
#         def type_internal_time():
#             Orb.Eos.send_osc_with_delay("/eos/key/\\", delay=.2)
#             Orb.Eos.send_osc_with_delay("/eos/key/internal", delay=.2)
#             Orb.Eos.send_osc_with_delay("/eos/key/time", delay=.2)
            
#         @staticmethod
#         def enter_timecode_or_just_enter(timecode, is_delayed=False):
#             if timecode:
#                 '''When animation-strip-start, make the macro start clock 
#                 at correct time per Blender's timeline'''  
#                 for digit in timecode:
#                     Orb.Eos.send_osc_with_delay(f"/eos/key/{digit}", delay=0.2)
#                 time.sleep(0.5)
#             Orb.Eos.send_osc_with_delay("/eos/key/enter")

#         @staticmethod
#         def internal_enable_or_disable_foreground(desired_state):
#             Orb.Eos.send_osc_with_delay("/eos/key/\\", delay=.2)
#             Orb.Eos.send_osc_with_delay("/eos/key/internal", delay=.2)
#             Orb.Eos.send_osc_with_delay(f"/eos/key/{desired_state}", delay=.2)
#             Orb.Eos.send_osc_with_delay("/eos/key/enter", delay=.2)
#             Orb.Eos.send_osc_with_delay("/eos/key/select", delay=.2)
#             Orb.Eos.send_osc_with_delay("/eos/softkey/3", delay=.2)  # "Foreground Mode" softkey
#             Orb.Eos.send_osc_with_delay("/eos/key/enter", delay=.2)

#         @staticmethod
#         def live_and_execute_on_cue(cue_number, macro_number, execute_on_cues, live=True):
#             if live:
#                 Orb.Eos.send_osc_with_delay("/eos/key/live", delay=.2)
#             if execute_on_cues:
#                 Orb.Eos.send_osc_with_delay("/eos/newcmd", f"Cue {str(cue_number)} Execute Macro {str(macro_number)} Enter Enter")

#         @staticmethod
#         def reset_macro_key():
#             Orb.Eos.send_osc_with_delay("/eos/key/macro", "0", delay=.2)


#         #-------------------------------------------------------------------------------------------------------------------------------------------
#         '''Text editor macros'''
#         #-------------------------------------------------------------------------------------------------------------------------------------------
#         @staticmethod
#         def generate_multiline_macro(self, context, scene, macro, text_data):
#             try:
#                 yield Orb.Eos.record_snapshot(scene), "Recording snapshot."
#                 yield Orb.Eos.save_console_file(scene), "Orb is running."
#                 yield Orb.Eos.delete_recreate_macro_enter_edit(macro), "Creating blank macro."
#                 yield Orb.Eos.reset_macro_key(), "Resetting macro key."
#                 yield Orb.Eos.type_tokens(text_data), "Typing macro contents"
#                 yield Orb.Eos.restore_snapshot(scene), "Restoring your screen setup."
#             except AttributeError as e:
#                 logging.error(f"Attribute error in generate_multiline_macro: {e}")
#                 yield None, f"Attribute error: {e}"
#             except ValueError as e:
#                 logging.error(f"Value error in generate_multiline_macro: {e}")
#                 yield None, f"Value error: {e}"
#             except RuntimeError as e:
#                 logging.error(f"Runtime error in generate_multiline_macro: {e}")
#                 yield None, f"Runtime error: {e}"
#             except Exception as e:
#                 logging.error(f"Unexpected error in generate_multiline_macro: {e}")
#                 yield None, f"Unexpected error: {e}"
            
#         @staticmethod
#         def type_tokens(text_data):
#             for line in text_data:
#                 tokens = tokenize_macro_line(line)
#                 for address, argument in tokens:
#                     Orb.Eos.send_osc_with_delay(address, argument, .2)
#                     time.sleep(.1)

#             Orb.Eos.send_osc_with_delay("/eos/softkey/6", "1", 0.1)  # "Done" softkey
#             Orb.Eos.send_osc_with_delay("/eos/key/live", "1", 0.1)
#             Orb.Eos.send_osc_with_delay("/eos/key/live", "0", 0.1)


#         #-------------------------------------------------------------------------------------------------------------------------------------------
#         '''Macro strips'''
#         #-------------------------------------------------------------------------------------------------------------------------------------------
#         @staticmethod
#         def generate_macro_command(context, macro_number, macro_text, first=False, final=False):
#             try:
#                 if first:
#                     yield Orb.Eos.record_snapshot(context.scene), "Recording snapshot."
#                     yield Orb.Eos.save_console_file(context.scene), "Orb is running."

#                 yield Orb.Eos.initiate_macro(), "Initiating macro."
#                 yield Orb.Eos.type_macro_number(macro_number), "Typing macro number."
#                 yield Orb.Eos.learn_macro_and_exit(macro_text), "Learning macro and exiting."
#                 yield Orb.Eos.reset_macro_key(), "Resetting macro key."

#                 if final:
#                     yield Orb.Eos.restore_snapshot(context.scene), "Restoring snapshot."
#                     yield None, "Orb complete."
#             except AttributeError as e:
#                 logging.error(f"Attribute error in generate_macro_command: {e}")
#                 yield None, f"Attribute error: {e}"
#             except ValueError as e:
#                 logging.error(f"Value error in generate_macro_command: {e}")
#                 yield None, f"Value error: {e}"
#             except RuntimeError as e:
#                 logging.error(f"Runtime error in generate_macro_command: {e}")
#                 yield None, f"Runtime error: {e}"
#             except Exception as e:
#                 logging.error(f"Unexpected error in generate_macro_command: {e}")
#                 yield None, f"Unexpected error: {e}"

#         @staticmethod
#         def initiate_macro():
#             Orb.Eos.send_osc_with_delay("/eos/key/live")
#             Orb.Eos.send_osc_with_delay("/eos/key/live", "0", 0.5)
#             Orb.Eos.send_osc_with_delay("/eos/key/learn", "Enter", 0.5)
#             Orb.Eos.send_osc_with_delay("/eos/key/macro")

#         @staticmethod
#         def type_macro_number(macro_number):
#             for digit in str(macro_number):
#                 Orb.Eos.send_osc_with_delay(f"/eos/key/{digit}", delay=0.2)
#             Orb.Eos.send_osc_with_delay("/eos/key/enter", delay=0.1)
#             Orb.Eos.send_osc_with_delay("/eos/key/enter")

#         @staticmethod
#         def learn_macro_and_exit(macro_text):
#             Orb.Eos.send_osc_with_delay("/eos/newcmd", macro_text, 0.5)
#             Orb.Eos.send_osc_with_delay("/eos/key/learn", "Enter")
#             Orb.Eos.send_osc_with_delay("/eos/key/macro", "0")

#         @staticmethod
#         def calculate_biased_start_length(bias, frame_rate, strip_length_in_frames):
#             # Normalize bias to a 0-1 scale
#             normalized_bias = (bias + 49) / 98  # This will give 0 for -49 and 1 for 49
            
#             # Calculate minimum and maximum start_length in seconds
#             min_start_length = 1 / frame_rate  # 1 frame
#             max_start_length = (strip_length_in_frames - 1) / frame_rate
            
#             # Interpolate between min and max based on normalized bias
#             biased_start_length = (min_start_length * (1 - normalized_bias)) + (max_start_length * normalized_bias)
            
#             return round(biased_start_length, 1)
            
                
#         #-------------------------------------------------------------------------------------------------------------------------------------------
#         '''Qmeos'''
#         #-------------------------------------------------------------------------------------------------------------------------------------------
#         @staticmethod
#         def make_qmeo(scene, frame_rate, start_frame, end_frame, is_sound):
#             if is_sound:
#                 active_strip = scene.sequence_editor.active_strip
#                 execute_on_cues = True
#             else:
#                 active_strip = scene
#                 execute_on_cues = False

#             event_list = find_executor(scene, active_strip, 'event_list')
#             start_macro = find_executor(scene, active_strip, 'start_macro')
#             end_macro = find_executor(scene, active_strip, 'end_macro')
#             cue_list = find_executor(scene, active_strip, 'cue_list')
#             timecode = EventUtils.frame_to_timecode(active_strip.frame_start)

#             active_strip.str_parent_name = active_strip.name # Allow find_executor() to distinguish duplicates

#             if execute_on_cues:
#                 start_cue = active_strip.str_start_cue
#                 end_cue = active_strip.str_end_cue
#             else:
#                 start_cue, end_cue = None, None

#             yield from Orb.Eos.manipulate_show_control(scene, event_list, start_macro, end_macro, start_cue, end_cue, timecode, execute_on_cues)

#             yield from Orb.Eos.bake_qmeo_generator(scene, event_list, frame_rate, start_frame, end_frame, cue_list, end_macro)

#         @staticmethod
#         def bake_qmeo_generator(scene, event_list, frame_rate, start_frame, end_frame, cue_list, end_macro):
#             frames = list(range(int(start_frame), int(end_frame)))
#             cue_duration = round(1 / frame_rate, 2)

#             if event_list:
#                 yield Orb.Eos.delete_recreate_event_list(event_list, end_frame, frame_rate), "Recreating event list"

#             if cue_list:
#                 yield Orb.Eos.delete_cue_list(cue_list), "Recreating cue list"

#             wm = bpy.context.window_manager
#             wm.progress_begin(0, 100)

#             for i, frame in enumerate(frames):
#                 Orb.Eos.qmeo_frame(frame, scene, cue_list, event_list, cue_duration, wm, frames, i)

#             wm.progress_end()
#             bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

#             yield Orb.Eos.final_event_stop_clock(event_list, frames[-1], end_macro), "Setting final event to stop clock"
#             yield Orb.Eos.reset_cue_list(), "Resetting cue list"

#         @staticmethod
#         def delete_recreate_event_list(event_list, end_frame, fps):
#             # Delete event list so we don't have unexpected leftover baggage.
#             Orb.Eos.send_osc_with_delay("/eos/newcmd/", f"Delete Event {event_list} / Enter Enter", delay=.3)

#             # Recreate the event list from a blank slate.
#             argument = f"Event {str(event_list)} / 1 Thru {str(end_frame - 1)} Enter"
#             Orb.Eos.send_osc_with_delay("/eos/newcmd/", argument, delay=.2)

#             # Set the frame rate based on Blender scene.
#             int_fps = int(fps)
#             Orb.Eos.send_osc_with_delay("/eos/newcmd", f"Event {event_list} / Frame_Rate {int_fps} Enter", delay=.2)

#             # Go back to live for convenience.
#             OSC.press_lighting_key("live")
#             time.sleep(.2)

#         @staticmethod
#         def delete_cue_list(cue_list):
#             Orb.Eos.send_osc_with_delay("/eos/newcmd/", f"Delete Cue {cue_list} / Enter Enter", delay=.3)

#         @staticmethod
#         def qmeo_frame(frame, scene, cue_list, event_list, cue_duration, wm, frames, i):
#             # Get ready to record cue with the new CPV updates.
#             current_frame_number = scene.frame_current
#             argument_one = f"Record Cue {str(cue_list)} / {str(current_frame_number)} Time {str(cue_duration)} Enter Enter"

#             # Get ready to record the cue while also binding cue to its event.
#             if event_list:
#                 timecode = EventUtils.frame_to_timecode(frame)
#                 argument_two = f"Event {event_list} / {str(frame)} Time {str(timecode)} Show_Control_Action Cue {str(frame)} Enter"

#             # Update progress bar to keep user in the loop.
#             wm.progress_update(i / len(frames) * 100)
            
#             # Go ahead and actually send the final command
#             delay = scene.orb_chill_time
#             scene.frame_set(frame)
#             bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
#             time.sleep(.1)
#             Orb.Eos.send_osc_with_delay("/eos/newcmd", argument_one, delay=.1)
#             Orb.Eos.send_osc_with_delay("/eos/newcmd", argument_two, delay)

#         @staticmethod
#         def reset_cue_list():
#             Orb.Eos.send_osc_with_delay("/eos/newcmd/", "Cue 1 / Enter")

#         @staticmethod
#         def final_event_stop_clock(event_list, final_frame, end_macro):
#             timecode = EventUtils.frame_to_timecode(final_frame) # Ensure this event has a time component even if something above got skipped
#             Orb.Eos.send_osc_with_delay("/eos/newcmd", f"Event {event_list} / {str(final_frame)} Time {str(timecode)} Show_Control_Action Macro {str(end_macro)} Enter")


#         #-------------------------------------------------------------------------------------------------------------------------------------------
#         '''Render Strips'''
#         #-------------------------------------------------------------------------------------------------------------------------------------------
#         @staticmethod

        

#         #-------------------------------------------------------------------------------------------------------------------------------------------
#         '''Patch Group'''
#         #-------------------------------------------------------------------------------------------------------------------------------------------
#         @staticmethod
#         def patch_group(self, context):
#             scene = context.scene
#             address = "/eos/newcmd"

#             # Ensure at least one object is selected.
#             original_objects = [obj for obj in context.selected_objects]
#             if not original_objects:
#                 yield {'CANCELLED'}, "Please select at least one object in the viewport so Orb knows where to patch it on Augment 3D"
#                 return
            
#             yield Orb.Eos.record_snapshot(context.scene), "Orb is running"
#             yield Orb.Eos.save_console_file(context.scene), "Orb is running"
            
#             # Prevent random CPV updates from interfering.
#             scene.scene_props.freeze_cpv = True

#             # Setup the patch screen.
#             OSC.send_osc_lighting("/eos/key/blind", "1")
#             OSC.send_osc_lighting("/eos/key/blind", "0")
#             #time.sleep(.3)
#             OSC.send_osc_lighting("/eos/newcmd", "Patch Enter")
#             #time.sleep(.3)

#             # Loop over the selected objects.
#             yield from Orb.Eos.loop_over_parents(self, context, original_objects, scene, address)
            
#             # Re-nable CPV.
#             scene.scene_props.freeze_cpv = False

#             Orb.Eos.restore_snapshot(scene)

#             self.report({'INFO'}, "Orb complete.")
#             return {'FINISHED'}
        
#         @staticmethod
#         def loop_over_parents(self, context, original_objects, scene, address):
#             for obj in original_objects:
#                 # Set the active-object.
#                 bpy.ops.object.select_all(action='DESELECT')
#                 obj.select_set(True)
#                 context.view_layer.objects.active = obj
                
#                 # Apply all array and curve modifiers on active_object.
#                 is_group = False
#                 array_modifiers, curve_modifiers = Orb.Eos.find_modifiers(self, context)
#                 for array in array_modifiers:
#                     bpy.ops.object.modifier_apply(modifier=array.name)
#                     is_group = True
#                 for curve in curve_modifiers:
#                     bpy.ops.object.modifier_apply(modifier=curve.name)
                
#                 # Separate by loose parts and set transform pivot point to center of mass.
#                 if context.object.mode != 'OBJECT':
#                     bpy.ops.object.mode_set(mode='OBJECT')
#                 bpy.ops.object.editmode_toggle()
#                 bpy.ops.mesh.separate(type='LOOSE')
#                 bpy.ops.object.mode_set(mode='OBJECT')

#                 # Create a new collection for the separated objects
#                 if is_group:
#                     collection_name = f"{obj.name}_Group"
#                     new_collection = bpy.data.collections.new(collection_name)
#                     bpy.context.scene.collection.children.link(new_collection)
                
#                 for obj in context.selected_objects:
#                     if obj.type == 'MESH':
#                         context.view_layer.objects.active = obj
#                         bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')
                        
#                         if is_group:
#                             new_collection.objects.link(obj)

#                             for coll in obj.users_collection:
#                                 if coll != new_collection:
#                                     coll.objects.unlink(obj)  # Unlink from the original collections

#                 # Find indexes.
#                 starting_universe = scene.scene_props.int_array_universe
#                 start_address = scene.scene_props.int_array_start_address
#                 channels_to_add = scene.scene_props.int_array_channel_mode
#                 total_lights = len([chan for chan in bpy.data.objects if chan.select_get()])

#                 # Create list of all valid universe/addresses beforehand since trying to calculate this
#                 # dynamically is far more error-prone.
#                 addresses_list = find_addresses(starting_universe, start_address, channels_to_add, total_lights)
            
#                 # Loop over the channels within that object, assuming there was an array
#                 yield Orb.Eos.loop_over_children(self, context, scene, addresses_list, channels_to_add, address, is_group, obj.name), "Patching channels"

#                 # Get out of edit mode.
#                 bpy.ops.object.editmode_toggle()
#                 bpy.ops.object.editmode_toggle()
                
#         @staticmethod
#         def find_modifiers(self, context):
#             array_modifiers = []
#             curve_modifiers = []

#             if context.active_object and context.active_object.modifiers:
#                 for mod in context.active_object.modifiers:
#                     if mod.type == 'ARRAY':
#                         array_modifiers.append(mod)
#                     elif mod.type == 'CURVE':
#                         curve_modifiers.append(mod)

#             return array_modifiers, curve_modifiers

#         @staticmethod
#         def loop_over_children(self, context, scene, addresses_list, channels_to_add, address, is_group, group_name):
#             relevant_channels = []

#             # Ensure correct console mode.
#             OSC.send_osc_lighting("/eos/key/blind", "1")
#             OSC.send_osc_lighting("/eos/key/blind", "0")
#             time.sleep(.3)
#             OSC.send_osc_lighting("/eos/newcmd", "Patch Enter")
#             time.sleep(.3)

#             for i, chan in enumerate([obj for obj in bpy.data.objects if obj.select_get()]):
#                 chan_num = scene.scene_props.int_array_start_channel
#                 current_universe, current_address = addresses_list[i]

#                 position_x, position_y, position_z, orientation_x, orientation_y, orientation_z = EventUtils.get_loc_rot(chan, use_matrix=True)

#                 # Set channel-specific UI fields inside the loop.
#                 chan.str_manual_fixture_selection = str(chan_num)
#                 scene.scene_props.int_array_start_channel += 1
                
#                 # Patch the channel on the console.
#                 OSC.send_osc_lighting(address, f"Chan {chan_num} Position {position_x} / {position_y} / {position_z} Enter, Chan {chan_num} Orientation {orientation_x} / {orientation_y} / {orientation_z} Enter, Chan {chan_num} at {str(current_universe)} / {str(current_address)} Enter")
#                 #time.sleep(.3)

#                 # Add this channel to the list.
#                 channel_number = chan_num
#                 relevant_channels.append(channel_number)
                
#             # Set scene-specific UI fields outside the loop.
#             scene.scene_props.int_array_start_channel = chan_num + 1
#             scene.scene_props.int_array_start_address = current_address + channels_to_add
#             scene.scene_props.int_array_universe = current_universe
#             scene.scene_props.int_array_group_index += 1

#             # Select the new lights on the console for highlight visibility.
#             argument = "Chan "
#             if len(relevant_channels) != 0: 
#                 for light in relevant_channels:
#                     argument += f"{light} "
#                 argument += "Enter Enter Full Enter"
#             OSC.send_osc_lighting(address, argument)

#             # Record group
#             if is_group:
#                 # Add group to console
#                 group_number = scene.scene_props.int_group_number
#                 Orb.Eos.record_group(group_number, relevant_channels)
#                 scene.scene_props.int_group_number += 1

#                 # Add group to Sorcerer group_data
#                 new_group = scene.scene_group_data.add()
#                 new_group.name = group_name
#                 for channel in relevant_channels:
#                     new_channel = new_group.channels_list.add()
#                     new_channel.chan = channel


#         @staticmethod
#         def record_group(group_number, channels):
#             if group_number != 0:
#                 OSC.send_osc_lighting("/eos/key/live", "1")
#                 OSC.send_osc_lighting("/eos/key/live", "0")
#                 #time.sleep(.1)
#                 channels = [str(chan) for chan in channels]
#                 argument = " + ".join(channels)
#                 argument = f"Chan {argument} Record Group {group_number} Enter Enter"
#                 Orb.Eos.send_osc_with_delay("/eos/newcmd", argument)


def test_orb(): # Return True for fail, False for pass
    return False