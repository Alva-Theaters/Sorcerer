# This file is part of Alva Sorcerer
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
import numpy as np  # type: ignore
from typing import List, Tuple
import time

from ..assets.sli import SLI 
from ..maintenance.logging import alva_log

# pyright: reportInvalidTypeForm=false


class Mixer:
    def mix_my_values(self, parent, param):
        """Receives a bpy object mesh, parent, and returns three lists for channels list (c), parameters list (p), 
            and values list (v)"""
        start = time.time()

        cumulative_c = []
        cumulative_p = []
        cumulative_v = []
        
        from .cpvia_finders import CPVIAFinders
        cpvia_finders = CPVIAFinders()
        channels_list = []
        channels_list = cpvia_finders._find_channels_list(parent)

        c, p, v = self.mix(parent, param, channels_list)
        cumulative_c.extend(c)
        cumulative_p.extend(p)
        cumulative_v.extend(v)

        alva_log('time', f"mix_my_values took {time.time() - start} seconds\n")
        return cumulative_c, cumulative_p, cumulative_v
        
    def mix(self, parent, parameter, channels):
        values_list = parent.parameters
        offset = parent.float_offset
        subdivisions = parent.int_subdivisions
        mode = parent.mix_method_enum
        param_mode = parameter
        param = parameter
        if parameter == "color":
            param = "vec_color"
        param = f"float_{param}"
        p = [parameter for _ in channels]
        
        if mode in ['option_gradient', 'option_pattern']:
            # Establish values list.
            values = [getattr(choice, param) for choice in values_list]
            alva_log('mix', f"Values before subdivision: {values}\n")

            # Subdivide values list.
            values = self.subdivide_values(subdivisions, values)
            alva_log('mix', f"Values after subdivision: {values}\n")
            
            # Make channels and values the same length by placing keys in the appropriate spots.
            sorted_channels, sorted_values = self.sort(channels, values)
            alva_log('mix', f"sorted_channels, sorted_values: {sorted_channels}, {sorted_values}\n")

        # Apply the desired effect to the values.
        if mode == "option_gradient": # Interpolate smoothly between the keys
            mixed = self.interpolate(sorted_channels, sorted_values, subdivisions, channels, param_mode, offset)
            alva_log('mix', f"Interpolated: {mixed}\n")
        elif mode == "option_pattern": # Alternate between the keys
            mixed = self.patternize(mode, sorted_values, channels, param_mode, offset)
            alva_log('mix', f"Patternized: {mixed}\n")
        elif mode == "option_pose": # Push all channels through the choices as one, don't mix the choices together across the channels
            mixed = self.pose(channels, param_mode, parent)
            alva_log('mix', f"Posed: {mixed}\n")
        else:
            SLI.SLI_assert_unreachable()

        alva_log('mix', f"mix.py is returning : {list(channels), p, list(mixed)}")
        return list(channels), p, list(mixed)


    '''EFFECTS'''
    def interpolate(self, 
                    sorted_channels: np.ndarray, sorted_values: List[float], subdivisions: int, 
                    channels: List[int], param_mode: str, offset: float) -> List[float]:
        '''Interpolate the missing values between the keys.'''
        if len(sorted_channels) == 1:
            return [sorted_values[0]] * len(channels)
        else:
            interpolation_points = self.get_interpolation_points(sorted_channels, channels, offset)
            if param_mode == "color":
                return self.interpolate_color(sorted_values, interpolation_points, sorted_channels)
            else:
                return list(np.interp(interpolation_points, sorted_channels, sorted_values))

    def patternize(self, sorted_values: List[float], 
                    channels: List[int], param_mode: str, offset: float) -> List[float]:
        '''Alternate between choice without interpolating betweens, creating a choppy pattern'''
        num_values = len(sorted_values)
        mixed_values = [sorted_values[i % num_values] for i in range(len(channels))]
        offset_steps = int(offset * len(channels))
        mixed_values = mixed_values[-offset_steps:] + mixed_values[:-offset_steps]

        if param_mode == "color":
            mixed_values = [(r * 100, g * 100, b * 100) for r, g, b in mixed_values]
        return mixed_values
        
    def pose(self, channels: List[int], param_mode: str, parent) -> List[float]:
        '''Instead of pushing Lang through time you might have wound up pushing time through Lang.'''
        poses = parent.parameters
        num_poses = len(poses)
        motor_node = self.find_motor_node(parent)
        progress = (motor_node.float_progress * .1)
        
        # Ensure pose_index is within range
        pose_index = int(progress * (num_poses - 1)) % num_poses
        next_pose_index = (pose_index + 1) % num_poses
        blend_factor = (progress * (num_poses - 1)) % 1
        
        mixed_values = {
            'float_intensity': [],
            'float_vec_color': [],
            'float_pan': [],
            'float_tilt': [],
            'float_zoom': [],
            'float_iris': []
        }

        for param in mixed_values.keys():
            value1 = getattr(poses[pose_index], param)
            value2 = getattr(poses[next_pose_index], param)

            if param == 'float_vec_color':
                mixed_value = tuple(v1 * (1 - blend_factor) + v2 * blend_factor for v1, v2 in zip(value1, value2))
                mixed_values[param] = [(mixed_value[0] * 100, mixed_value[1] * 100, mixed_value[2] * 100)] * len(channels)
            else:
                mixed_value = value1 * (1 - blend_factor) + value2 * blend_factor
                mixed_values[param] = [mixed_value] * len(channels)

        scaled_values = self.scale_motor(parent, param_mode, mixed_values)

        if param_mode == 'color':
            return scaled_values['float_vec_color']
        else:
            return scaled_values[f'float_{param_mode}']


    '''HELPERS'''
    def subdivide_values(self, subdivisions: int, values: List[float]) -> List[float]:
        """Subdivide the values based on the number of subdivisions."""
        if subdivisions > 0:
            for _ in range(subdivisions):
                values += values
        return values

    def sort(self, channels: List[int], values: List[float]) -> Tuple[List[int], List[float]]:
        """Sort channels and values together so they are of same length, important for numpy."""
        sorted_channels_values = sorted(zip(channels, values))
        sorted_channels, sorted_values = zip(*sorted_channels_values)
        return list(sorted_channels), list(sorted_values)
    
    def get_interpolation_points(self, sorted_channels: np.ndarray, channels: List[int], offset: float) -> np.ndarray:
        """Use numpy matrix to get interpolation points."""
        min_channel = sorted_channels[0]
        max_channel = sorted_channels[-1]
        channel_range = max_channel - min_channel
        num_interpolation_points = len(channels)
        interpolation_points = np.linspace(min_channel, max_channel, num_interpolation_points, endpoint=True) + offset * num_interpolation_points
        interpolation_points = np.mod(interpolation_points - min_channel, channel_range) + min_channel
        return interpolation_points

    def interpolate_color(self,
                sorted_values: List[Tuple[float, float, float]], interpolation_points: np.ndarray, 
                sorted_channels: np.ndarray) -> List[Tuple[float, float, float]]:
        """Interpolate between keys for color."""
        reds = [color[0] for color in sorted_values]
        greens = [color[1] for color in sorted_values]
        blues = [color[2] for color in sorted_values]
        mixed_reds = np.interp(interpolation_points, sorted_channels, reds)
        mixed_greens = np.interp(interpolation_points, sorted_channels, greens)
        mixed_blues = np.interp(interpolation_points, sorted_channels, blues)
        mixed_values = [(r * 100, g * 100, b * 100) for r, g, b in zip(mixed_reds, mixed_greens, mixed_blues)]
        return mixed_values

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

    def scale_motor(self, parent: bpy.types.Node, param_mode: str, mixed_values: List[float]) -> List[float]:
        """Scale the mixed values based on the motor node's scale."""
        motor_node = self.find_motor_node(parent)
        if motor_node:
            float_scale = motor_node.float_scale
            if param_mode == "color":
                return [(r * float_scale, g * float_scale, b * float_scale) for r, g, b in mixed_values]
            else:
                return [v * float_scale for v in mixed_values]
        return mixed_values