# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
import mathutils
import math

from ..assets.dictionaries import Dictionaries
from ..utils.osc import OSC
from ..maintenance.logging import alva_log


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
    def trigger_special_mixer_props(mixers_and_motors):
        attributes_to_check = []

        for node in mixers_and_motors:
            if node.bl_idname == 'mixer_type' and node.mix_method_enum != 'option_pose':
                attributes_to_check = [
                    ("float_offset", "float_offset_checker"),
                    ("int_subdivisions", "int_subdivisions_checker")
                ]
            elif node.bl_idname == 'motor_type' and node.transmission_enum == 'option_keyframe':
                attributes_to_check = [
                    ("float_progress", "float_progress_checker"),
                    ("float_scale", "float_scale_checker")
                ]
            else:
                continue

            for attr, checker in attributes_to_check:
                if getattr(node, attr) != getattr(node, checker):
                    setattr(node, attr, getattr(node, attr))
                    setattr(node, checker, getattr(node, attr))


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
            if prop != "float_iris":
                if isinstance(value, int) and value != 0:
                    setattr(obj, prop, value)
                elif isinstance(value, mathutils.Color) and any(v != 1 for v in value):
                    setattr(obj, prop, value)
            else:  # TODO Temporary fix. This needs to be way smarter.
                if isinstance(value, int) and value != 100:
                    setattr(obj, prop, value)
                elif isinstance(value, mathutils.Color) and any(v != 1 for v in value):
                    setattr(obj, prop, value)
    
    @staticmethod
    def trigger_sem(obj, chan_num):
        x_focus, y_focus, z_focus, x_orientation, y_orientation, z_orientation = EventUtils.get_loc_rot(obj, use_matrix=True)
        OSC.send_osc_lighting("/eos/newcmd", f"Chan {chan_num} X_Focus {x_focus} Enter, Chan {chan_num} Y_Focus {y_focus} Enter, Chan {chan_num} Z_Focus {z_focus} Enter, Chan {chan_num} X_Orientation {x_orientation} Enter, Chan {chan_num} Y_Orientation {y_orientation} Enter, Chan {chan_num} Z_Orientation {z_orientation} Enter", user=0)
                
    @staticmethod
    def check_and_trigger_drivers(updated_objects):
        evaluated_to_original = [obj.name for obj in updated_objects]
        for obj in bpy.data.objects:
            if hasattr(obj, "object_identities_enum"):
                if obj.animation_data and obj.animation_data.drivers:
                    alva_log("event_manager", "Found animation data in check_and_trigger_drivers.")
                    for driver in obj.animation_data.drivers:
                        alva_log("event_manager", "Found driver in check_and_trigger_drivers.")
                        data_path = driver.data_path
                        try:
                            for var in driver.driver.variables:
                                for target in var.targets:
                                    if target.id.name in evaluated_to_original:
                                        EventUtils.trigger_special_update(obj)
                        except IndexError:
                            print(f"Failed to parse data path '{data_path}' for drivers on '{obj.name}'")
                        except Exception as e:
                            print(f"Error processing driver on '{obj.name}': {e}")


    @staticmethod
    def find_relevant_clock_objects(scene):    
        relevant_lighting_clock_object = None
        relevant_audio_strip = None
        for strip in scene.sequence_editor.sequences:
            if (strip.type == 'SOUND' and
                not strip.mute and 
                getattr(strip, 'int_event_list', 0) != 0 and
                strip.frame_start <= scene.frame_current < strip.frame_final_end):
                relevant_lighting_clock_object = strip
            if (strip.type == 'SOUND' and
                not strip.mute and 
                getattr(strip, 'int_sound_cue', 0) != 0 and
                strip.frame_start <= scene.frame_current < strip.frame_final_end):
                relevant_audio_strip = strip
        if not relevant_lighting_clock_object and scene.use_default_clock:
            relevant_lighting_clock_object = scene
        return relevant_lighting_clock_object, relevant_audio_strip
            

    @staticmethod
    def find_livemap_cue(scene, current_frame, active_strip):
        relevant_strips = [strip for strip in scene.sequence_editor.sequences if getattr(strip, 'eos_cue_number', 0) != 0 and strip.my_settings.motif_type_enum == 'option_cue' and not strip.mute]
        closest_strip = None
        for strip in relevant_strips:
            if strip.frame_start <= current_frame:
                if closest_strip is None or strip.frame_start > closest_strip.frame_start:
                    closest_strip = strip
        return closest_strip

                        
    @staticmethod                   
    def on_scrub_detected(current_frame):
        scene = bpy.context.scene
        relevant_lighting_clock_object = None
        current_frame = scene.frame_current
        current_frame = current_frame + scene.timecode_expected_lag
        relevant_lighting_clock_object, relevant_sound_strip = EventUtils.find_relevant_clock_objects(scene)
        
        if relevant_lighting_clock_object:
            fps = EventUtils.get_frame_rate(scene)
            timecode = EventUtils.frame_to_timecode(current_frame, fps)
            clock = relevant_lighting_clock_object.int_event_list
            OSC.send_osc_lighting("/eos/newcmd", f"Event {clock} / Internal Time {timecode} Enter, Event {clock} / Internal Enable Enter")


    def is_rendered_mode():
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type == 'VIEW_3D':
                    for space in area.spaces:
                        if space.type == 'VIEW_3D' and space.shading.type == 'RENDERED':
                            return True
        return False
    

    def get_frame_rate(scene):
        return round((scene.render.fps / scene.render.fps_base), 2)
    

    def frame_to_timecode(frame, fps=None):
        context = bpy.context
        """Convert frame number to timecode format."""
        if fps is None:
            fps = context.scene.render.fps_base * context.scene.render.fps
        hours = int(frame // (fps * 3600))
        frame %= fps * 3600
        minutes = int(frame // (fps * 60))
        frame %= fps * 60
        seconds = int(frame // fps)
        frames = int(round(frame % fps))
        return "{:02}:{:02}:{:02}:{:02}".format(hours, minutes, seconds, frames)
    

    def time_to_frame(time, frame_rate, start_frame):
        return int(time * frame_rate) + start_frame
    

    def get_loc_rot(obj, use_matrix=False):
        x_pos, y_pos, z_pos, x_rot_rad, y_rot_rad, z_rot_rad  = EventUtils.get_original_loc_rot(obj, use_matrix)

        # Convert meters to feet.
        position_x = round(x_pos / .3048, 2)
        position_y = round(y_pos / .3048, 2)
        position_z = round(z_pos / .3048, 2)

        # Round and rotate x by 180 degrees (pi in radians) since cone facing up is the same as a light facing down.
        orientation_x = round(math.degrees(x_rot_rad + math.pi), 2)
        orientation_y = round(math.degrees(y_rot_rad), 2)
        orientation_z = round(math.degrees(z_rot_rad), 2)

        return position_x, position_y, position_z, orientation_x, orientation_y, orientation_z
    
    
    def get_original_loc_rot(obj, use_matrix=False):
        if use_matrix:
            depsgraph = bpy.context.evaluated_depsgraph_get()
            eval_obj = obj.evaluated_get(depsgraph)
            
            bpy.context.view_layer.update()
            
            matrix = eval_obj.matrix_world
            euler = matrix.to_euler('XYZ')

            # Convert radians to degrees for rotation
            x_rot_rad = euler.x
            y_rot_rad = euler.y
            z_rot_rad = euler.z

            position = matrix.translation
            x_pos = position.x
            y_pos = position.y
            z_pos = position.z

        else:
            x_pos = obj.location.x
            y_pos = obj.location.y
            z_pos = obj.location.z
            x_rot_rad = obj.rotation_euler.x
            y_rot_rad = obj.rotation_euler.y
            z_rot_rad = obj.rotation_euler.z

        return x_pos, y_pos, z_pos, x_rot_rad, y_rot_rad, z_rot_rad 