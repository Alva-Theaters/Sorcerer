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
import mathutils

from ..assets.dictionaries import Dictionaries
from ..utils.osc import OSC
from ..utils.utils import Utils


class EventUtils:
    @staticmethod
    def convert_to_props(scene, controllers):
        '''Find the animated properties inside the controllers.'''
        props = []

        for controller in controllers:
            if hasattr(controller, 'bl_idname') and controller.bl_idname == 'mixer_type':
                props.extend(EventUtils._find_props(controller, is_mixer=True))
            else:
                props.extend(EventUtils._find_props(controller, is_mixer=False))
        return props

    @staticmethod
    def _find_props(controller, is_mixer=False):
        props = []
        if is_mixer:
            props_location = controller.parameters
        else: 
            props_location = controller
            
        for toggle, toggle_types in Dictionaries.parameter_toggles.items():
            if getattr(props_location, toggle, False):
                for property in toggle_types:
                    if EventUtils._has_keyframes(props_location, property):
                        raw_value = getattr(props_location, property, None)
                        value = EventUtils._extract_value(raw_value)
                        props.append((controller, property, value))
        return props
    
    @staticmethod
    def _extract_value(raw_value):
        '''Extract the numerical value or a simple representation from the property value.
           MUST do this to avoid setting references (which magically change) instead of
           the actual static number.'''
        if isinstance(raw_value, (int, float)):
            return raw_value
        elif isinstance(raw_value, (tuple, list)) and all(isinstance(x, (int, float)) for x in raw_value):
            return tuple(raw_value)
        elif isinstance(raw_value, mathutils.Color):
            return tuple(raw_value)
        elif isinstance(raw_value, mathutils.Vector):
            return tuple(raw_value)
        else:
            return str(raw_value)

    @staticmethod
    def _has_keyframes(controller, property):
        if hasattr(controller, "animation_data") and controller.animation_data:
            if hasattr(controller.animation_data, "action") and controller.animation_data.action:
                for fcurve in controller.animation_data.action.fcurves:
                    if fcurve.data_path.endswith(property):
                        return len(fcurve.keyframe_points) > 0

        if isinstance(controller, bpy.types.ColorSequence):
            return True

        if hasattr(controller, "bl_idname") and controller.bl_idname in ['group_controller_type', 'mixer_type']:
            node_tree = controller.id_data  # Get the node tree containing the node
            if hasattr(node_tree, "animation_data") and node_tree.animation_data:
                action = node_tree.animation_data.action
                if action:
                    for fcurve in action.fcurves:
                        # Check if the data path corresponds to the node and the property
                        if fcurve.data_path.startswith(controller.path_from_id()) and fcurve.data_path.endswith(property):
                            return len(fcurve.keyframe_points) > 0
        return False

    @staticmethod
    def find_updates(old_graph, new_graph):
        '''Find properties that actually need to send OSC right now.'''
        old_dict = {(controller, parameter): value for controller, parameter, value in old_graph}
        new_dict = {(controller, parameter): value for controller, parameter, value in new_graph}

        # Only consider updates if there is a corresponding entry in both graphs and the value has changed
        updates = [(controller, parameter, new_value) 
                   for (controller, parameter), new_value in new_dict.items() 
                   if (controller, parameter) in old_dict and old_dict[(controller, parameter)] != new_value]

        return updates

    @staticmethod
    def use_harmonizer(flag):
        bpy.context.scene.scene_props.in_frame_change = flag

    @staticmethod
    def fire_updaters(updates): 
        '''Start the logic to create a CPVIA request for the controller's 
           changed property.'''
        for controller, property, value in updates:
            setattr(controller, property, getattr(controller, property))

    @staticmethod
    def trigger_special_update(obj):
        properties = ['float_intensity', 'float_vec_color', 'float_zoom', 'float_iris']
        for prop in properties:
            value = getattr(obj, prop)
            if isinstance(value, float) and value != 0:
                setattr(obj, prop, value)
            elif isinstance(value, mathutils.Color) and any(v != 0 for v in value):
                setattr(obj, prop, value)
                
    @staticmethod
    def check_and_trigger_drivers(updated_objects):
        evaluated_to_original = [obj.name for obj in updated_objects]
        
        for obj in bpy.data.objects:
            if obj.object_identities_enum == "Stage Object":
                if obj.animation_data:
                    for driver in obj.animation_data.drivers:
                        data_path = driver.data_path
                        try:
                            if '"' in data_path:
                                # Quoted property
                                prop_name = data_path.split('"')[1]
                            else:
                                # Unquoted property (like float_intensity)
                                prop_name = data_path.split('.')[-1]
                            
                            for var in driver.driver.variables:
                                for target in var.targets:
                                    if target.id.name in evaluated_to_original:
                                        EventUtils.trigger_special_update(obj)
                        except IndexError:
                            print(f"Failed to parse data path '{data_path}' for drivers on '{obj.name}'")
                        except Exception as e:
                            print(f"Error processing driver on '{obj.name}': {e}")


    @staticmethod
    def find_relevant_clock_object(scene):    
        relevant_object = None
        for strip in scene.sequence_editor.sequences:
            if (strip.type == 'SOUND' and
                not strip.mute and 
                getattr(strip, 'int_event_list', 0) != 0 and
                strip.frame_start <= scene.frame_current < strip.frame_final_end):
                relevant_object = strip
        if not relevant_object and scene.use_default_clock:
            relevant_object = scene
        return relevant_object
            
    @staticmethod
    def find_livemap_cue(scene, current_frame, active_strip):
        relevant_strips = [strip for strip in scene.sequence_editor.sequences if getattr(strip, 'eos_cue_number', 0) != 0 and strip.my_settings.motif_type_enum == 'option_eos_cue' and not strip.mute]
        closest_strip = None
        for strip in relevant_strips:
            if strip.frame_start <= current_frame:
                if closest_strip is None or strip.frame_start > closest_strip.frame_start:
                    closest_strip = strip
        return closest_strip

                        
    @staticmethod                   
    def on_scrub_detected(current_frame):
        scene = bpy.context.scene
        relevant_sound_strip = None
        current_frame = scene.frame_current
        current_frame = current_frame + scene.timecode_expected_lag
        relevant_sound_strip = EventUtils.find_relevant_clock_object(scene)
        
        if relevant_sound_strip:
            fps = Utils.get_frame_rate(scene)
            timecode = Utils.frame_to_timecode(current_frame, fps)
            clock = relevant_sound_strip.int_event_list
            OSC.send_osc_lighting("/eos/newcmd", f"Event {clock} / Internal Time {timecode} Enter, Event {clock} / Internal Enable Enter")