# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import colorsys

PAN_MAX = 360
TILT_MAX = 135


class NodeUpdaters:
    @staticmethod
    def mixer_param_updater(self, context):
        if self.parameters:
            if self.parameters_enum == "option_intensity":
                self.parameters[0].alva_intensity = self.parameters[0].alva_intensity
            elif self.parameters_enum == "option_color":
                self.parameters[0].alva_color = self.parameters[0].alva_color
            elif self.parameters_enum == "option_pan_tilt":
                self.parameters[0].alva_pan = self.parameters[0].alva_pan
                self.parameters[0].alva_tilt = self.parameters[0].alva_tilt
            elif self.parameters_enum == "option_zoom":
                self.parameters[0].alva_zoom = self.parameters[0].alva_zoom
            elif self.parameters_enum == "option_iris":
                self.parameters[0].alva_iris = self.parameters[0].alva_iris

                    
    @staticmethod                
    def pan_tilt_graph_updater(self, context):
        '''Uses template color picker as stand-in for pan/tilt square graph controller.
           Because a circle only has 360 degrees of rotation about its axis while most
           moving lights have about 540 degrees of rotation about their axes, this thing
           has to use "overdrive" modes to track whether or not we need to extend our
           circle programmatically. Imagine not a circle, but a sort of helical disk
           with 150% the surface area of a circle'''           
        if self.pan_tilt_graph_checker != self.float_vec_pan_tilt_graph:
            r, g, b = self.float_vec_pan_tilt_graph[:3]
            h, s, v = colorsys.rgb_to_hsv(r, g, b)
            v *= 30
            hue_change = h - self.last_hue
            overdrive_mode = self.overdrive_mode
            
            if self.is_overdriven_left and h < .75:
                overdrive_mode = ""
                self.is_overdriven_left = False
                self.is_approaching_limit = False
                
            elif self.is_overdriven_right and h > .25:
                overdrive_mode = ""
                self.is_overdriven_right = False
                self.is_approaching_limit = False
                
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
    def find_driven_mixer(self):  # TODO Needs to use the find function in finders
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
                attributes = ['alva_intensity', 'alva_color', 'alva_pan', 'alva_tilt', 'alva_zoom', 'alva_iris']
                for attr in attributes:
                    current_value = getattr(connected_node.parameters[0], attr)
                    setattr(connected_node.parameters[0], attr, current_value)
            
            else:  # Avoid pointlessly updating inactive parameters when not in pose mode
                if connected_node.parameters_enum == "option_intensity":
                    connected_node.parameters[0].alva_intensity = connected_node.parameters[0].alva_intensity
                elif connected_node.parameters_enum == "option_color":
                    connected_node.parameters[0].alva_color = connected_node.parameters[0].alva_color
                elif connected_node.parameters_enum == "option_pan_tilt":
                    connected_node.parameters[0].alva_pan = connected_node.parameters[0].alva_pan
                    connected_node.parameters[0].alva_tilt = connected_node.parameters[0].alva_tilt
                elif connected_node.parameters_enum == "option_zoom":
                    connected_node.parameters[0].alva_zoom = connected_node.parameters[0].alva_zoom
                elif connected_node.parameters_enum == "option_iris":
                    connected_node.parameters[0].alva_iris = connected_node.parameters[0].alva_iris

                connected_node.float_offset = (self.float_progress * .01)
    
    
    @staticmethod
    def motor_updater(self, context):
        r, g, b = self.motor[:3]
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        self.float_scale = s

        # Define a smaller sensitivity to prevent rapid jumps
        MOTOR_SENSITIVITY = 1.0  # Adjust as needed

        # Calculate current angle based on hue
        current_angle = h * 360

        if not self.is_interacting:
            self.initial_angle = current_angle
            self.prev_angle = self.initial_angle
            self.is_interacting = True

        # Increment the update counter
        self.update_counter += 1

        # Only update every update_interval iterations
        if self.update_counter % self.update_interval == 0:
            # Calculate the angle difference with wrap-around handling
            angle_diff = current_angle - self.prev_angle
            if angle_diff > 180:
                angle_diff -= 360
            elif angle_diff < -180:
                angle_diff += 360

            # Calculate the float_progress increment based on the angle
            float_progress_increment = (angle_diff / 360) * 10
            self.float_progress += float_progress_increment

            # Ensure float_progress stays within bounds (0 to 10)
            if self.float_progress < 0:
                self.float_progress = 0
            elif self.float_progress > 10:
                self.float_progress = 10

            # Update the previous angle
            self.prev_angle = current_angle

        # Publish updates (if necessary)
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
            
        self.node_tree_name = self.id_data.name
        self.node_name = self.name

        for param in self.parameters:
            param.node_tree_name = self.id_data.name
            param.node_name = self.name


    @staticmethod
    def boost_index_updater(self, context):
        for item in self.custom_buttons:
            item.constant_index += self.boost_index


    @staticmethod
    def direct_select_types_updater(self, context):
        argument = self.direct_select_types_enum.replace(" ", "_")
        for button in self.custom_buttons:
            button.button_argument = f"{argument} {button.constant_index}"

            if argument == "Macro":
                button.button_argument = f"{button.button_argument} Enter"


    @staticmethod
    def constant_index_updater(self, context):
        return # This needs to fire direct_select_types_updater without losing track of the parent node. Maybe store the enum value on the button?