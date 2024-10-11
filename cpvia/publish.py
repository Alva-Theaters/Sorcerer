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


import bpy

from ..assets.sli import SLI
from ..utils.osc import OSC
from ..assets.dictionaries import Dictionaries
    

change_requests = []


class Publisher:
          
    def format_channel_and_value(self, c, v):
        """
        This function formats the channel and value numbers as string and then formats them
        in a way the console will understand (by adding a 0 in front of numbers 1-9.)
        """
        c = str(c)
        if bpy.context.scene.scene_props.console_type_enum == 'option_eos':
            v = int(v)
            if v >= 0 and v < 10:
                v = f"0{v}"
            elif v < 0 and v > -10:
                v = f"-0{-v}"
            else:
                v = str(v)
        else:
            v = round(v, 2)
            v = str(v)

        return c, v
    
    
    def format_channel(self, c):
        c = str(c)

        return c
    

    def format_value(self, v):
        """
        This function formats the channel and value numbers as string and then formats them
        in a way the console will understand (by adding a 0 in front of numbers 1-9.)
        """
        if bpy.context.scene.scene_props.console_type_enum == 'option_eos':
            v = int(v)
            if v >= 0 and v < 10:
                v = f"0{v}"
            elif v < 0 and v > -10:
                v = f"-0{-v}"
            else:
                v = str(v)
        else:
            v = round(v, 2)
            v = str(v)
        
        return v


    def form_osc(self, c, p, v, i, a):
        """
        This function converts cpvia into (address, argument) tuples.

        Parameters:
        cpvia: channel, parameter, value, influence, argument template.

        Returns:
        messages: A list of (address, argument) tuples.
        """
        console_mode = bpy.context.scene.scene_props.console_type_enum
        if console_mode == "option_eos":
            address = "/eos/newcmd"
        elif console_mode == 'option_ma3':
            address = "/cmd"
        elif console_mode == 'option_ma2':
            address = "/cmd"
        else:
            SLI.SLI_assert_unreachable()
            address = "/eos/newcmd"

        color_profiles = {
            # Absolute Arguments
            "rgb": ["$1", "$2", "$3"],
            "cmy": ["$1", "$2", "$3"],
            "rgbw": ["$1", "$2", "$3", "$4"],
            "rgba": ["$1", "$2", "$3", "$4"],
            "rgbl": ["$1", "$2", "$3", "$4"],
            "rgbaw": ["$1", "$2", "$3", "$4", "$5"],
            "rgbam": ["$1", "$2", "$3", "$4", "$5"],

            # Raise Arguments
            "raise_rgb": ["$1", "$2", "$3"],
            "raise_cmy": ["$1", "$2", "$3"],
            "raise_rgbw": ["$1", "$2", "$3", "$4"],
            "raise_rgba": ["$1", "$2", "$3", "$4"],
            "raise_rgbl": ["$1", "$2", "$3", "$4"],
            "raise_rgbaw": ["$1", "$2", "$3", "$4", "$5"],
            "raise_rgbam": ["$1", "$2", "$3", "$4", "$5"],

            # Lower Arguments
            "lower_rgb": ["$1", "$2", "$3"],
            "lower_cmy": ["$1", "$2", "$3"],
            "lower_rgbw": ["$1", "$2", "$3", "$4"],
            "lower_rgba": ["$1", "$2", "$3", "$4"],
            "lower_rgbl": ["$1", "$2", "$3", "$4"],
            "lower_rgbaw": ["$1", "$2", "$3", "$4", "$5"],
            "lower_rgbam": ["$1", "$2", "$3", "$4", "$5"]
        }

        if p not in color_profiles:
            c, v = self.format_channel_and_value(c, v)
            address = address.replace("#", c).replace("$", v)
            argument = a.replace("#", c).replace("$", v)
        else:
            formatted_values = [self.format_value(val) for val in v]

            c = self.format_channel(c)
            argument = a.replace("#", c)
            
            for i, fv in enumerate(formatted_values):
                argument = argument.replace(color_profiles[p][i], str(fv))

        return address, argument
    
    
    def send_cpvia(self, c, p, v, i, a):
        """
        Decides whether to send osc now (we are not playing back) or later (we are playing back).

        Parameters:
        cpvia: channel, parameter, value, influence, argument template.

        This function does not return a value.
        """
        if bpy.context.scene.scene_props.is_playing or bpy.context.scene.scene_props.in_frame_change:
            global change_requests
            change_requests.append((c, p, v, i, a))
        else:
            address, argument = self.form_osc(c, p, v, i, a)  # Should return 2 strings
            OSC.send_osc_lighting(address, argument, user=0)

            
    def find_objects(self, chan):
        relevant_objects = []
        for obj in bpy.data.objects:
            if obj.object_identities_enum == "Fixture":
                relevant_objects.append(obj)
                pass
        return relevant_objects
    

    def update_other_selections(self, context, parent, p):
        if parent != context.active_object:
            return  # Prevent infinite recursion
        
        others = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
        if parent in others:
            others.remove(parent)
        param = Dictionaries.parameter_mapping[p]
        for obj in others:
                setattr(obj, param, getattr(parent, param))
            
            
    def render_in_viewport(self, parent, chan, param, val):
        """
        Adds material to relevant objects in 3d scene and sets material as that intensity or color.

        Parameters:
        val: Either float or tuple, depending on intensity or color

        This function does not return a value.
        """
        def find_val_type(val):
            if isinstance(val, (tuple, list)):
                return "color"
            elif isinstance(val, (int, float)):
                return "intensity"
            else:
                raise ValueError("Invalid value type")

        val_type = find_val_type(val)
        objects = self.find_objects(chan)
        
        if not objects:
            return
        
        if val_type == "intensity":
            for obj in objects:
                # Ensure the object has a material slot and create one if it doesn't
                if not hasattr(obj.data, "materials"):
                    continue
                
                if not obj.data.materials:
                    mat = bpy.data.materials.new(name="Intensity_Material")
                    obj.data.materials.append(mat)
                else:
                    mat = obj.data.materials[0]

                # Enable 'Use nodes'
                if not mat.use_nodes:
                    mat.use_nodes = True
                
                nodes = mat.node_tree.nodes
                links = mat.node_tree.links
                
                # Find existing emission node or create a new one
                emission = None
                for node in nodes:
                    if node.type == 'EMISSION':
                        emission = node
                        break
                if not emission:
                    emission = nodes.new(type='ShaderNodeEmission')
                    # Add material output node and link it to emission node
                    output = nodes.new(type='ShaderNodeOutputMaterial')
                    links.new(emission.outputs['Emission'], output.inputs['Surface'])

                # Get the current value
                input = emission.inputs['Strength']
                current_val = input.default_value
                    
                if param == "raise_intensity":
                    val = current_val + val * 0.01
                elif param == "lower_intensity":
                    val = current_val - val * 0.01
                else:
                    val *= 0.01
                    
                if val > 1:
                    val = 1
                elif val < 0:
                    val = 0
                    
                print(f"Val: {val}")
                input.default_value = val

        elif val_type == "color":
            for obj in objects:
                if not hasattr(obj.data, "materials"):
                    continue
                
                # Ensure the object has a material slot and create one if it doesn't
                if not obj.data.materials:
                    mat = bpy.data.materials.new(name="Color_Material")
                    obj.data.materials.append(mat)
                else:
                    mat = obj.data.materials[0]

                # Enable 'Use nodes'
                if not mat.use_nodes:
                    mat.use_nodes = True
                
                nodes = mat.node_tree.nodes
                links = mat.node_tree.links

                # Find existing emission node or create a new one
                emission = None
                for node in nodes:
                    if node.type == 'EMISSION':
                        emission = node
                        break
                if not emission:
                    emission = nodes.new(type='ShaderNodeEmission')
                    # Add material output node and link it to emission node
                    output = nodes.new(type='ShaderNodeOutputMaterial')
                    links.new(emission.outputs['Emission'], output.inputs['Surface'])

                # Set the color value
                scaled_val = tuple(component * 0.01 for component in val)
                emission.inputs['Color'].default_value = (*scaled_val, 1)  # Assuming val is an (R, G, B) tuple

                print(f"Color: {(*scaled_val, 1)}")

        else:
            SLI.SLI_assert_unreachable()


    def clear_requests(self):
        global change_requests
        change_requests = []


def test_publisher(SENSITIVITY): # Return True for fail, False for pass
    return False