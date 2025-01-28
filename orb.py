# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
import time
from itertools import chain

from .updaters.sequencer import SequencerUpdaters as Updaters
from .utils.event_utils import EventUtils
from .utils.orb_utils import find_addresses, tokenize_macro_line, find_executor
from .as_ui.utils import get_strip_class
from .utils.sequencer_utils import BiasCalculator
from .utils.sequencer_mapping import StripMapper
from .cpv.publish import Publish

WHAT_DOES_THIS_DO = """
This code is for a set of operators identified in the UI with a purple orb icon.

These operators are responsible for automating repetitive tasks on the lighting console.

For example, 
    - Creating qmeos
    - Creating macros needed for Sorcerer-to-console synchronization
    - Programming channel-specific cue-timings (discrete timing) on the console's cues

This uses "yield"/generator because we want the user to be able to escape prematurely with the 
ESC key.
"""


def invoke_orb(Operator, context, as_orb_id):
    active_item = sequencer_strip_or_scene(context.scene)
    Console = get_lighting_console_instance(context.scene)

    yield from Console.prepare_console_for_automation()
    yield from complete_operator_specific_automation(context, active_item, Operator, Console, as_orb_id)
    yield from Console.restore_console_to_normal_following_automation()


def sequencer_strip_or_scene(scene):
    if hasattr(scene.sequence_editor, "active_strip") and scene.sequence_editor.active_strip is not None:
        return scene.sequence_editor.active_strip
    else:
        return scene


def get_lighting_console_instance(scene):
    console = Publish.find_installed_lighting_console_data_class(scene.scene_props.console_type_enum)
    return console(scene)  # Create instance.


def complete_operator_specific_automation(context, active_item, Operator, Console, as_orb_id):
    if not active_item:
        return {'CANCELLED'}, "No item found."
    
    if not hasattr(active_item, 'str_parent_name'):
        return {'CANCELLED'}, "Invalid item selected."
    
    if not Operator:
        return {'CANCELLED'}, "Invalid operator found."
    
    if not Console:
        return {'CANCELLED'}, "Invalid lighting console selected."
    
    if not as_orb_id:
        return {'CANCELLED'}, "No as_orb_id found."
    
    executor = get_executor(as_orb_id)

    if executor is None:
        return {'CANCELLED'}, f"Invalid as_orb_id: {as_orb_id}."
    
    yield from executor(context, active_item, Console)

    return {'FINISHED'}, "Orb complete."


def get_executor(as_orb_id):
    StripClass = get_strip_class(as_orb_id)
    if not StripClass:
        local_executors = {
            'sound': lambda ctx, item, con: SoundStrip(ctx, item).execute(con),
            'text': lambda ctx, item, con: TextSync(ctx, item).execute(con),
            'timeline': lambda ctx, item, con: TimelineSync(ctx, item).execute(con),
            'sequencer': lambda ctx, item, con: SequencerSync(ctx, item).execute(con),
            'viewport': lambda ctx, item, con: ViewportSync(ctx, item).execute(con)
        }

        return local_executors.get(as_orb_id)

    elif hasattr(StripClass, 'orb'):
        return StripClass.orb


def sound_wrapper(context, active_item, Console):
    return lambda: SoundStrip(context, active_item).execute(Console)

def timeline_wrapper(context, active_item, Console):
    return lambda: TimelineSync(context, active_item).execute(Console)

def sequencer_wrapper(context, active_item, Console):
    return lambda: SequencerSync(context, active_item).execute(Console)

def viewport_wrapper(context, active_item, Console):
    return lambda: ViewportSync(context, active_item).execute(Console)
            

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
        
        Console.record_cue(self.cue_number, self.cue_duration)

        for slowed_prop_name in slowed_properties:
            yield from self.record_discrete_times(slowed_prop_name, Console)

        Console.update_cue()

        self.active_item.name = f"Cue {str(self.cue_number)}"


    def record_discrete_times(self, slowed_prop_name, Console):
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
            members_str = simplify_channels_list(groups)
            yield Console.record_discrete_time("Group", members_str, discrete_time), "Recording groups"

        if channels:
            members_str = simplify_channels_list(channels)
            yield Console.record_discrete_time("Chan", members_str, discrete_time), "Recording channels"

        if submasters:
            members_str = simplify_channels_list(submasters)
            yield Console.record_discrete_time("Sub", members_str, discrete_time), "Recording submasters"


class SoundStrip:
    def __init__(self, context, active_item):
        scene = context.scene
        self.event_list = find_executor(scene, active_item, 'event_list')
        self.start_macro = find_executor(scene, active_item, 'start_macro')
        self.end_macro = find_executor(scene, active_item, 'end_macro')


    def execute(self, Console):
        yield from Console.record_timecode_macro(self.start_macro, self.event_list, state='enable')
        yield from Console.record_timecode_macro(self.end_macro, self.event_list, state='disable')
    

class MacroStrip:
    def __init__(self, context, active_item):
        self.scene = context.scene
        Updaters.macro_update(active_item, context) # Ensure the textual input has been parsed

        self.start_macro_number = find_executor(self.scene, active_item, 'start_macro')
        self.start_macro_text = active_item.start_frame_macro_text

        if self.scene.strip_end_macros:
            self.end_macro_number = find_executor(self.scene, active_item, 'end_macro')
            self.end_macro_text = active_item.end_frame_macro_text

    def execute(self, Console):
        if self.start_macro_text != "" and self.start_macro_number != 0:
            yield from Console.record_one_line_macro(self.start_macro_number, self.start_macro_text)

        if self.scene.strip_end_macros and self.end_macro_text != "" and self.end_macro_number != 0:
            yield from Console.record_one_line_macro(self.end_macro_number, self.end_macro_text)

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

        bias_in_frames = BiasCalculator(bias, strip_length_in_frames).execute()
        m1_start_length_in_seconds = round((bias_in_frames / frame_rate), 2)
        self.start_macro_text = f"{str(active_item.flash_input_background)} Sneak Time {str(m1_start_length_in_seconds)} Enter "
        end_length = round((strip_length_in_seconds - m1_start_length_in_seconds), 1)
        self.end_macro_text = f"{str(active_item.flash_down_input_background)} Sneak Time {str(end_length)} Enter"

        self.start_macro_number = find_executor(scene, active_item, 'start_macro')
        self.end_macro_number = find_executor(scene, active_item, 'end_macro')


    def execute(self, Console):
        yield from Console.record_one_line_macro(self.start_macro_number, self.start_macro_text)
        yield from Console.record_one_line_macro(self.end_macro_number, self.end_macro_text)


class TextSync:
    def __init__(self, context, active_item):
        self.macro = context.space_data.text.text_macro
        active_text = context.space_data.text
        text_data = active_text.as_string()
        text_data = text_data.splitlines()

        all_tokens = []
        for line in text_data:
            tokens = tokenize_macro_line(line)
            for token in tokens:
                all_tokens.append(token)
        self.tokens = all_tokens

    def execute(self, Console):
        yield from Console.record_multiline_macro(self.macro, self.tokens)

            
class SequencerSync:
    BATCH_LIMIT = 50

    def __init__(self, context, active_item):
        from .utils.event_utils import EventUtils
        self.event_object, sound_strip = EventUtils.find_relevant_clock_objects(context.scene)
        self.event_list = self.event_object.int_event_list
        self.scene = context.scene

        self.event_map = StripMapper(context.scene, orb=True).execute()

        self.event_strings = self.strips_to_event_strings()

    def strips_to_event_strings(self):
        fps = EventUtils.get_frame_rate(self.scene)
        
        event_strings = []
        for i, (frame, events) in enumerate(self.event_map.items(), start=1):
            for event_type, value in events:  # Iterate over the list of tuples
                timecode = EventUtils.frame_to_timecode(int(frame), fps)  # Convert frame to int if needed
                event_strings.append(f"Event {self.event_list} / {i} Time {timecode} Show_Control_Action {event_type} {value} Enter")
        return event_strings


    def execute(self, Console):
        Console.key("blind")
        Console.cmd(f"Delete Event {self.event_list} / Enter Enter")
        Console.cmd(f"Event {self.event_list} / Enter Enter")
        yield from self.batch_send_event_strings(Console)
        Console.key("live")
        bpy.ops.screen.animation_play()

    def batch_send_event_strings(self, Console):
        for i in range(0, len(self.event_strings), 50):
            yield self.send_event_string(i, Console), "Sending event command"

    def send_event_string(self, i, Console):
        batch = self.event_strings[i:i+self.BATCH_LIMIT]
        argument = ", ".join(batch)
        Console.cmd(argument)


class TimelineSync:
    def __init__(self, context, active_item):
        self.scene = context.scene
        self.frame_rate = EventUtils.get_frame_rate(context.scene)
        self.start_frame = context.scene.frame_start
        self.end_frame = context.scene.frame_end

        self.event_list = find_executor(context.scene, context.scene, 'event_list')
        self.start_macro = find_executor(context.scene, context.scene, 'start_macro')
        self.end_macro = find_executor(context.scene, context.scene, 'end_macro')
        self.cue_list = find_executor(context.scene, context.scene, 'cue_list')

    def execute(self, Console):
        yield from Console.record_timecode_macro(self.start_macro, self.event_list, state='enable')
        yield from Console.record_timecode_macro(self.end_macro, self.event_list, state='disable')

        frames = list(range(int(self.start_frame), int(self.end_frame)))
        cue_duration = round(1 / self.frame_rate, 2)

        yield from Console.delete_recreate_event_list(self.event_list, self.end_frame, self.frame_rate)
        yield Console.delete_cue_list(self.cue_list), "Recreating cue list"

        wm = bpy.context.window_manager
        wm.progress_begin(0, 100)
 
        for i, frame in enumerate(frames):
            yield from self.qmeo_frame(Console, frame, cue_duration, wm, frames, i)

        wm.progress_end()
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

        final_frame = frames[-1]
        timecode = EventUtils.frame_to_timecode(final_frame) # Ensure this event has a time component even if something above got skipped
        
        yield Console.final_event_stop_clock(self.event_list, final_frame, timecode, self.end_macro), "Setting final event to stop clock"
        yield Console.reset_cue_list(), "Resetting cue list"

    def qmeo_frame(self, Console, frame, cue_duration, wm, frames, i):
        # Get ready to record cue with the new CPV updates.
        current_frame_number = self.scene.frame_current
        argument_one = Console.make_record_qmeo_cue_argument(self.cue_list, current_frame_number, cue_duration)

        # Get ready to record the cue while also binding cue to its event.
        timecode = EventUtils.frame_to_timecode(frame)
        argument_two = Console.make_record_qmeo_event_argument(self.event_list, frame, timecode)

        # Update progress bar to keep user in the loop.
        wm.progress_update(i / len(frames) * 100)
        
        # Go ahead and actually send the final command
        self.scene.frame_set(frame)
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
        time.sleep(.1)
        yield Console.send_frame(argument_one, argument_two), "Recording frame"
        time.sleep(self.scene.orb_chill_time)


class ViewportSync():
    def __init__(self, context, active_item):
        self.context = context
        self.scene = context.scene
        self.original_objects = [obj for obj in context.selected_objects]

        self.starting_universe = context.scene.scene_props.int_array_universe
        self.start_address = context.scene.scene_props.int_array_start_address
        self.channels_to_add = context.scene.scene_props.int_array_channel_mode


    def execute(self, Console):
        self.scene.scene_props.freeze_cpv = True  # Prevent random CPV updates from interfering.

        if not self.original_objects:
            yield {'CANCELLED'}, "Please select at least one object in the viewport so Orb knows where to patch it on Augment 3D"
            return

        Console.prepare_patch()
        yield self.loop_over_parents(Console), "Patching"

        self.scene.scene_props.freeze_cpv = False  # Re-nable CPV.
        
    def loop_over_parents(self, Console):
        for obj in self.original_objects:
            self.set_active_object(obj)
            is_group = self.decide_if_group(obj)
            self.apply_modifiers()
            self.separate_by_loose_parts()
            new_collection = self.create_collection(is_group, obj)
            
            for obj in self.context.selected_objects:
                self.origin_and_collection_set(obj, is_group, new_collection)

            num_total_lights = len([chan for chan in bpy.data.objects if chan.select_get()])
            addresses_list = find_addresses(self.starting_universe, self.start_address, self.channels_to_add, num_total_lights)
        
            # Loop over the channels within that object, assuming there was an array
            self.loop_over_children(Console, addresses_list, self.channels_to_add, is_group, obj.name)

            self.edit_mode_exit()

    def set_active_object(self, obj):
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        self.context.view_layer.objects.active = obj

    def decide_if_group(self, obj):
        array_modifiers = [mod for mod in obj.modifiers if mod.type == 'ARRAY']
        return len(array_modifiers) > 0

    def apply_modifiers(self):
        array_modifiers, curve_modifiers = self.find_modifiers()
        for modifier in chain(array_modifiers, curve_modifiers):
            bpy.ops.object.modifier_apply(modifier=modifier.name)
            
    def find_modifiers(self):
        context = self.context

        if not (context.active_object and context.active_object.modifiers):
            return [], []
        
        array_mods = [mod for mod in context.active_object.modifiers if mod.type == 'ARRAY']
        curve_mods = [mod for mod in context.active_object.modifiers if mod.type == 'CURVE']

        return array_mods, curve_mods
    
    def separate_by_loose_parts(self):
        if self.context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.separate(type='LOOSE')
        bpy.ops.object.mode_set(mode='OBJECT')

    def create_collection(self, is_group, obj):
        if not is_group:
            return
        
        collection_name = f"{obj.name}_Group"
        new_collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(new_collection)
        return new_collection

    def origin_and_collection_set(self, obj, is_group, new_collection):
        if obj.type != 'MESH':
            return

        self.origin_set_center_mass(obj)
        
        if not is_group:
            return

        new_collection.objects.link(obj)

        for coll in obj.users_collection:
            self.original_collection_unlink(coll, obj, new_collection)

    def origin_set_center_mass(self, obj):
        self.context.view_layer.objects.active = obj
        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')

    def original_collection_unlink(self, coll, obj, new_collection):
        if coll != new_collection:
            coll.objects.unlink(obj)

    def edit_mode_exit(self):
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()

 
    def loop_over_children(self, Console, addresses_list, channels_to_add, is_group, group_name):
        relevant_channels = []

        Console.prepare_patch()

        for i, chan in enumerate([obj for obj in bpy.data.objects if obj.select_get()]):
            chan_num = self.scene.scene_props.int_array_start_channel
            uni, addr = addresses_list[i]

            pos_x, pos_y, pos_z, or_x, or_y, or_z = EventUtils.get_loc_rot(chan, use_matrix=True)

            # Set channel-specific UI fields inside the loop.
            chan.str_manual_fixture_selection = str(chan_num)
            self.scene.scene_props.int_array_start_channel += 1
            
            Console.patch_light(chan_num, pos_x, pos_y, pos_z, or_x, or_y, or_z, uni, addr)

            # Add this channel to the list.
            channel_number = chan_num
            relevant_channels.append(channel_number)
            
        # Set scene-specific UI fields outside the loop.
        self.scene.scene_props.int_array_start_channel = chan_num + 1
        self.scene.scene_props.int_array_start_address = addr + channels_to_add
        self.scene.scene_props.int_array_universe = uni
        self.scene.scene_props.int_array_group_index += 1

        # Select the lights on the console for user's convenience
        lights = [str(num) for num in relevant_channels]
        lights = " + ".join(lights)
        Console.select_lights(lights)
        

        # Record group
        if is_group:
            # Add group to console
            group_number = self.scene.scene_props.int_group_number
            if group_number != 0:
                Console.record_group(lights, group_number)
                self.scene.scene_props.int_group_number += 1

            # Add group to Sorcerer group_data
            new_group = self.scene.scene_group_data.add()
            new_group.name = group_name
            for channel in relevant_channels:
                new_channel = new_group.channels_list.add()
                new_channel.chan = channel


def test_orb(): # Return True for fail, False for pass
    return False