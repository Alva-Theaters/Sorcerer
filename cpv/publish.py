# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from ..assets.sli import SLI
from ..utils.osc import OSC
from .map import SliderToFixtureMapper
from .split_color import ColorSplitter
from ..utils.spy_utils import REGISTERED_LIGHTING_CONSOLES
    
change_requests = []
PROPERTIES_TO_MAP = ["strobe", "pan", "tilt", "zoom", "gobo_speed"]


class Publish:
    def __init__(self, generator, channel, property_name, value, is_harmonized=False):
        self.generator = generator
        self.channel = channel
        self.property_name = property_name
        self.value = value
        self.patch_controller = self.find_my_patch_controller()
        self.is_harmonized = is_harmonized
        self._DataClass = self.find_data_class()
        self._address = self._DataClass.osc_address
        self._rounding_points = self._DataClass.rounding_points
        self._format_value_function = self._DataClass.format_value

    @property
    def is_bound_to_harmonizer(self):
        return bpy.context.scene.scene_props.is_playing or bpy.context.scene.scene_props.in_frame_change

    def find_my_patch_controller(self):
        if self.generator.controller_type not in ["Fixture", "Pan/Tilt Fixture"]:
            for obj in bpy.data.objects:
                if obj.object_identities_enum == "Fixture" and obj.list_group_channels[0].chan == self.channel:
                    return obj
        return self.generator.parent
    
    @staticmethod
    def find_data_class():
        console_mode = bpy.context.scene.scene_props.console_type_enum
        try:
            return REGISTERED_LIGHTING_CONSOLES[console_mode]
        except KeyError:
            print(f"Error: The console mode '{console_mode}' is not registered.")
            return None


    def execute(self):
        if self.property_name in PROPERTIES_TO_MAP:
            self.value = SliderToFixtureMapper(self).execute()

        if self.property_name in ['color', 'raise_color', 'lower_color']:
            self.property_name, self.value = ColorSplitter(self.generator, self).execute()

        # This needs to go after ColorSplitter because it must see color type
        # ("RGB" for example) in self.property_name, not just "color."
        self._argument_template = self._find_argument_template()

        if self.is_bound_to_harmonizer and not self.is_harmonized:
            global change_requests
            change_requests.append((self.generator, self.channel, self.property_name, self.value))
        else:
            full_argument, address = self.form_osc()
            OSC.send_osc_lighting(address, full_argument, user=0)

    def _find_argument_template(self):
        if "raise_" not in self.property_name and "lower_" not in self.property_name:
            argument_template = self._DataClass.absolute.get(self.property_name, "Unknown Argument")
        elif "raise_" in self.property_name:
            argument_template = self._DataClass.increase.get(self.property_name, "Unknown Argument")
        elif "lower_" in self.property_name:
            argument_template = self._DataClass.decrease.get(self.property_name, "Unknown Argument")
        else:
            SLI.SLI_assert_unreachable()
            return "Invalid lighting console."

        if self.property_name in ['strobe', 'prism']:
            argument_template = self._apply_special_parameter_syntax(argument_template)

        return argument_template

    def _apply_special_parameter_syntax(self, argument_template):
        if self.value == 0:
            special_argument = getattr(self.patch_controller, f"str_disable_{self.property_name}_argument")
        else: special_argument = getattr(self.patch_controller, f"str_enable_{self.property_name}_argument")

        if self.property_name == 'strobe':
            if self.value == 0:
                argument = f"{special_argument}"
            else:
                argument = f"{special_argument}, {argument_template}"
        else:
            argument = special_argument

        return argument

    def form_osc(self):
        channel = self.channel
        parameter = self.property_name
        value = self.value

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

        if parameter not in color_profiles:
            channel = self.format_channel(channel)
            value = self.format_value(value)
            address = self._address.replace("#", channel).replace("$", value)
            argument = self._argument_template.replace("#", channel).replace("$", value)
        else:
            formatted_values = [self.format_value(val) for val in value]

            channel = self.format_channel(channel)
            address = self._address
            argument = self._argument_template.replace("#", channel)
            
            for i, formatted_value in enumerate(formatted_values):
                argument = argument.replace(color_profiles[parameter][i], str(formatted_value))

        return argument, address
    
    def format_channel(self, channel):
        return str(channel)
    
    def format_value(self, value):
        value = round(value, self._rounding_points)
        value = self._format_value_function(value)
        return value


def clear_requests():
    global change_requests
    change_requests = []
    

def update_other_selections(context, parent, property_name):
    if parent != context.active_object:
        return  # Prevent infinite recursion
    
    others = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
    if parent in others:
        others.remove(parent)
    for obj in others:
            setattr(obj, f"alva_{property_name}", getattr(parent, f"alva_{property_name}"))


def test_publisher(SENSITIVITY): # Return True for fail, False for pass
    return False