# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
import numpy as np   # type: ignore
from typing import List, Tuple, Union
import time
import mathutils

from ..assets.sli import SLI 
from ..maintenance.logging import alva_log
from .publish.publish import Publish, CPV

# pyright: reportInvalidTypeForm=false

OFFSET_SENSITIVITY = .25


def find_mixer_cpv(Generator, Parameter):
    """Receives a bpy object mesh, parent, and returns three lists for channels list (c), parameters list (p), 
        and values list (v)"""
    start_time = time.time()
    MixCPV(Generator, Parameter).execute(start_time)


class MixCPV:
    def __init__(self, Generator, Parameter):
        self.parent = Generator.parent
        self.Parameter = Parameter
        self.property_name = Generator.property_name
        self.controller_type = Generator.controller_type 
        self.channels_list = [channel.chan for channel in self.parent.list_group_channels]


    def execute(self, start_time):
        parent = self.parent
        parameter = self.property_name
        channels = self.channels_list
        values_list = parent.parameters
        param = self.add_alva_prefix_to_param(parameter)
        values = [getattr(choice, param) for choice in values_list]
        subdivisions = parent.int_subdivisions
        mode = parent.mix_method_enum
        param_mode = parameter

        offset = self.apply_offset_sensitivity(parent)

        if mode == "option_gradient":
            channels, values = self.Interpolate().execute(values, subdivisions, channels, offset, param_mode)

        elif mode == "option_pattern":
            values = self.Patternize().execute(values, channels, param_mode, offset)

        elif mode == "option_pose":
            values = self.Pose().execute(channels, param_mode, parent)

        else:
            SLI.SLI_assert_unreachable()

        alva_log('mix', f"MAIN. mix.py is returning: {channels, values}")
        for channel, value in zip(channels, values):
            Publish(self, self.Parameter, channel, parameter, value, sender=CPV).execute()

        alva_log('time', f"TIME: mix_my_values took {time.time() - start_time} seconds\n")
    
    @staticmethod
    def apply_offset_sensitivity(parent):
        return parent.float_offset * OFFSET_SENSITIVITY
    
    @staticmethod
    def add_alva_prefix_to_param(param):
        return f"alva_{param}"
    

    class Interpolate:
        '''
        This needs to 
        
        1. Find all the selections/choices in the mixer UI. These are keys, sort of like keyframes.
        2. Subdivide that list of keys based on the user's Subdivide selection.
        3. Correct cases where there are less channels than keys.
        4. Interpolate between keys expanding for number of channels. This will be values.
        '''
        def execute(self, keys, subdivisions, channels, offset, param_mode):
            keys = self.subdivide_values(subdivisions, keys)
            keys = self.compress_keys(keys, len(channels), param_mode)
            values = self.interpolate_keys_to_values(channels, keys, offset, param_mode)
            return channels, values
        
        def subdivide_values(self, subdivisions: int, values: List[Union[float, mathutils.Color]]) -> List[Union[float, mathutils.Color]]:
            if subdivisions > 0:
                for _ in range(subdivisions):
                    values += values
            return values
        
        def compress_keys(self, keys: List[Union[float, Tuple[float, float, float]]], num_channels: int, param_mode: str) -> List[Union[float, Tuple[float, float, float]]]:
            """
            All we're trying to do is basically compress the keys to get them to fit into a smaller number 
            of keys if we have more keys than channels.

            So, if there are 2 channels but our list of keys is [0, 100, 0], it should return 50, 50.

            If there are 3 channels and the list of keys is [0, 100, 0, 0, 100, 0], it should return 50, 0, 50.

            So it should say ok, divide the number of keys by the number of channels (sample size). That's 2. 
            Then it should average the first 2 (50), average the next 2 (0), and then average the final pair 
            (50).
            """
            if len(keys) < num_channels:
                return keys
            
            if num_channels == 0:
                sample_size = 1
            else:
                sample_size = len(keys) / num_channels  # Determine how many keys per channel

            compressed_keys = []

            for i in range(num_channels):
                start = int(i * sample_size)
                end = int((i + 1) * sample_size)
                group = keys[start:end]

                if param_mode == "color":
                    averaged_key = mathutils.Color((
                        sum(color.r for color in group) / len(group),
                        sum(color.g for color in group) / len(group),
                        sum(color.b for color in group) / len(group),
                    ))
                else:
                    averaged_key = sum(group) / len(group)
                
                compressed_keys.append(averaged_key)

            return compressed_keys
        
        def interpolate_keys_to_values(self, channels: List[int], keys: List[Union[float, mathutils.Color]], offset: float, param_mode: str) -> List[Union[float, mathutils.Color]]:
            alva_log("mix", f"\nMIXER SESSION:\nINTERP. Input channels: {channels}\nINTERP. Input keys: {keys}\nINTERP. Offset: {offset}")

            num_keys = len(keys)
            fractional_offset = offset * num_keys

            interpolation_points = (np.linspace(0, num_keys - 1, len(channels)) + fractional_offset) % num_keys

            if param_mode == "color":
                reds = [key.r for key in keys]
                greens = [key.g for key in keys]
                blues = [key.b for key in keys]

                interpolated_reds = np.interp(interpolation_points, range(num_keys), reds, period=num_keys)
                interpolated_greens = np.interp(interpolation_points, range(num_keys), greens, period=num_keys)
                interpolated_blues = np.interp(interpolation_points, range(num_keys), blues, period=num_keys)

                interpolated_values = [
                    mathutils.Color((r, g, b))
                    for r, g, b in zip(interpolated_reds, interpolated_greens, interpolated_blues)
                ]
            else:
                interpolated_values = np.interp(interpolation_points, range(num_keys), keys, period=num_keys).tolist()

            alva_log("mix", f"INTERP. Interpolated values with offset: {interpolated_values}")
            return interpolated_values
    

    class Patternize:
        def execute(self, values: List[float], 
                    channels: List[int], param: str, offset: float) -> List[float]:
            '''Alternate between choice without interpolating betweens, creating a choppy pattern'''
            num_values = len(values)
            mixed_values = [values[i % num_values] for i in range(len(channels))]
            offset_steps = int(offset * len(channels))
            mixed_values = mixed_values[-offset_steps:] + mixed_values[:-offset_steps]

            if param == "color":
                mixed_values = [(r, g, b) for r, g, b in mixed_values]
            return mixed_values
        
    class Pose:
        def execute(self, channels: List[int], param_mode: str, parent) -> List[float]:
            '''Instead of pushing Lang through time you might have wound up pushing time through Lang.'''
            poses = parent.parameters
            num_poses = len(poses)
            motor_node = self.find_motor_node(parent)
            if motor_node:
                progress = (motor_node.float_progress * .1)
            else:
                progress = .1
            
            # Ensure pose_index is within range
            pose_index = int(progress * (num_poses - 1)) % num_poses
            next_pose_index = (pose_index + 1) % num_poses
            blend_factor = (progress * (num_poses - 1)) % 1
            
            mixed_values = {
                'alva_intensity': [],
                'alva_color': [],
                'alva_pan': [],
                'alva_tilt': [],
                'alva_zoom': [],
                'alva_iris': []
            }

            for param in mixed_values.keys():
                value1 = getattr(poses[pose_index], param)
                value2 = getattr(poses[next_pose_index], param)

                if param == 'alva_color':
                    mixed_value = tuple(v1 * (1 - blend_factor) + v2 * blend_factor for v1, v2 in zip(value1, value2))
                    mixed_values[param] = [(mixed_value[0], mixed_value[1], mixed_value[2])] * len(channels)
                else:
                    mixed_value = value1 * (1 - blend_factor) + value2 * blend_factor
                    mixed_values[param] = [mixed_value] * len(channels)

            scaled_values = self.scale_motor(parent, param_mode, mixed_values, motor_node)

            if param_mode == 'color':
                return scaled_values['alva_color']
            else:
                return scaled_values[f'alva_{param_mode}']
            
        def find_motor_node(self, mixer_node: bpy.types.Node) -> bpy.types.Node:
            """Find the motor node connected to the mixer node."""
            if not mixer_node.inputs:
                return None
            for input_socket in mixer_node.inputs:
                if input_socket.is_linked:
                    for link in input_socket.links:
                        if link.from_socket.bl_idname == 'MotorOutputType':
                            connected_node = link.from_node
                            if connected_node.bl_idname == 'motor_type':
                                return connected_node
            return None

        def scale_motor(self, parent: bpy.types.Node, param_mode: str, mixed_values: List[float], motor_node: bpy.types.Node) -> List[float]:
            """Scale the mixed values based on the motor node's scale."""
            if motor_node:
                float_scale = motor_node.float_scale
            else:
                float_scale = 1

            if param_mode == "color" and "alva_color" in mixed_values:
                mixed_values['alva_color'] = [
                    (r * float_scale, g * float_scale, b * float_scale) for r, g, b in mixed_values['alva_color']
                ]
            elif param_mode != "color":
                for key, values in mixed_values.items():
                    if isinstance(values[0], (int, float)):
                        mixed_values[key] = [v * float_scale for v in values]

            return mixed_values


def test_mixer(SENSITIVITY): # Return True for fail, False for pass
    return False