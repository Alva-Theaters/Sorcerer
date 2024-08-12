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


import colorsys

from ..cpvia.find import Find


PAN_MAX = 360
TILT_MAX = 135


class NodeUpdaters:
    @staticmethod
    def mixer_param_updater(self, context):
        if self.parameters:
            if self.parameters_enum == "option_intensity":
                self.parameters[0].float_intensity = self.parameters[0].float_intensity
            elif self.parameters_enum == "option_color":
                self.parameters[0].float_vec_color = self.parameters[0].float_vec_color
            elif self.parameters_enum == "option_pan_tilt":
                self.parameters[0].float_pan = self.parameters[0].float_pan
                self.parameters[0].float_tilt = self.parameters[0].float_tilt
            elif self.parameters_enum == "option_zoom":
                self.parameters[0].float_zoom = self.parameters[0].float_zoom
            elif self.parameters_enum == "option_iris":
                self.parameters[0].float_iris = self.parameters[0].float_iris


    @staticmethod           
    def flash_node_updater(self, context):
        finders = Find()
        
        up_channels_list, down_channels_list = finders.find_flash_node_channels(self)
        up_channels_str, down_channels_str = finders.join_flash_channels(up_channels_list, down_channels_list)
        
        # Update all subscribing flash strips in sequencer
        for strip in context.scene.sequence_editor.sequences_all:
            if strip.my_settings.motif_type_enum == "option_eos_flash" and strip.motif_name == self.flash_motif_names_enum and strip.flash_type_enum == 'option_use_nodes':
                strip.flash_input = f"Chan {up_channels_str} Preset {self.int_start_preset}"
                strip.flash_down_input = f"Chan {down_channels_str} Preset {self.int_end_preset}" 
                   
                    
    @staticmethod                
    def pan_tilt_graph_updater(self, context):
        '''Uses template color picker as stand-in for pan/tilt square graph controller.
           Because a circle only has 360 degrees of rotation about its axis while most
           moving lights have about 540 degrees of rotation about their axes, this thing
           has to use "overdrive" modes to track whether or not we need to extend our
           circle programmatically. Imagine not a circle, but a sort of helical disk
           with 150% the surface area of a circle'''           
        if self.pan_tilt_graph_checker != self.float_vec_pan_tilt_graph:
            scene = context.scene.scene_props
            r, g, b = self.float_vec_pan_tilt_graph[:3]
            h, s, v = colorsys.rgb_to_hsv(r, g, b)
            v *= 30
            hue_change = h - self.last_hue
            overdrive_mode = self.overdrive_mode
            
            if self.is_overdriven_left and h < .75:
                overdrive_mode = ""
                self.is_overdriven_left = False
                self.is_approaching_limit = False
                print("Overdriving for left pan")
                
            elif self.is_overdriven_right and h > .25:
                overdrive_mode = ""
                self.is_overdriven_right = False
                self.is_approaching_limit = False
                print("Overdriving for right pan")
                
            if self.is_overdriven_left and h < .85:
                self.is_approaching_limit = True
                
            elif self.is_overdriven_right and h > .15:
                self.is_approaching_limit = True
                
            # Detect a jump in hue value indicating a crossover point.
            if hue_change > 0.5 and not self.is_overdriven_right:  
                overdrive_mode = 'left'
                self.is_overdriven_left = True
            elif hue_change < -0.5 and not self.is_overdriven_left:
                overdrive_mode = 'right'
                self.is_overdriven_right = True

            if overdrive_mode == 'left':
                overdrive_h = (1 - h) * -1
                pan = (overdrive_h * PAN_MAX * -1) + (PAN_MAX * .5)
            elif overdrive_mode == 'right':
                overdrive_h = h + 1
                pan = (overdrive_h * PAN_MAX * -1) + (PAN_MAX * .5)
            else:
                pan = (h * PAN_MAX * -1) + (PAN_MAX * .5)

            # Calculate tilt based on saturation and value.
            tilt = (s * TILT_MAX) * v  # Assuming saturation and value map to tilt.

            setattr(self, 'pan_graph', round(pan))
            setattr(self, 'tilt_graph', round(tilt))

            self.pan_tilt_graph_checker = self.float_vec_pan_tilt_graph

            # Save current hue for next update.
            self.last_hue = h
            self.overdrive_mode = overdrive_mode  


    # Motor nodes
    @staticmethod
    def find_driven_mixer(self):  ## Needs to use the find function in finders
        if not self.outputs:
            return None

        for output_socket in self.outputs:
            if output_socket.is_linked:
                for link in output_socket.links:
                    if link.to_socket.bl_idname == 'MotorInputType':
                        connected_node = link.to_node
                        if connected_node.bl_idname == "mixer_type":
                            return connected_node
        return None
    
    
    @staticmethod
    def publish(self):
        connected_node = NodeUpdaters.find_driven_mixer(self)
        
        if connected_node:  # All parameters are active in pose mode, so update all
            if connected_node.mix_method_enum == 'option_pose':
                attributes = ['float_intensity', 'float_vec_color', 'float_pan', 'float_tilt', 'float_zoom', 'float_iris']
                for attr in attributes:
                    current_value = getattr(connected_node.parameters[0], attr)
                    setattr(connected_node.parameters[0], attr, current_value)
            
            else:  # Avoid pointlessly updating inactive parameters when not in pose mode
                if connected_node.parameters_enum == "option_intensity":
                    connected_node.parameters[0].float_intensity = connected_node.parameters[0].float_intensity
                elif connected_node.parameters_enum == "option_color":
                    connected_node.parameters[0].float_vec_color = connected_node.parameters[0].float_vec_color
                elif connected_node.parameters_enum == "option_pan_tilt":
                    connected_node.parameters[0].float_pan = connected_node.parameters[0].float_pan
                    connected_node.parameters[0].float_tilt = connected_node.parameters[0].float_tilt
                elif connected_node.parameters_enum == "option_zoom":
                    connected_node.parameters[0].float_zoom = connected_node.parameters[0].float_zoom
                elif connected_node.parameters_enum == "option_iris":
                    connected_node.parameters[0].float_iris = connected_node.parameters[0].float_iris

                connected_node.float_offset = (self.float_progress * .01)
    
    
    @staticmethod
    def motor_updater(self, context):
        r, g, b = self.motor[:3]
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        self.float_scale = s

        if not self.is_interacting:
            self.initial_angle = h * 360
            self.prev_angle = self.initial_angle
            self.is_interacting = True

        current_angle = h * 360
        angle_diff = current_angle - self.prev_angle

        if angle_diff > 180:
            angle_diff -= 360
        elif angle_diff < -180:
            angle_diff += 360

        self.float_progress += angle_diff
        self.prev_angle = current_angle
        
        NodeUpdaters.publish(self)
     
     
    @staticmethod   
    def props_updater(self, context):
        if self.transmission_enum == 'option_keyframe':
            NodeUpdaters.publish(self)
            
            
    @staticmethod
    def update_node_name(self, context=None):
        """Update the node name to ensure uniqueness."""
        if not self.name.startswith("MixerNode_"):
            self.name = "MixerNode_" + self.name
            
        self.node_tree_pointer = self.id_data
        self.node_name = self.name

        for param in self.parameters:
            param.node_tree_pointer = self.id_data
            param.node_name = self.name