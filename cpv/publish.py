# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from ..assets.sli import SLI
from ..utils.osc import OSC
from ..assets.dictionaries import Dictionaries
from .map import SliderToFixtureMapper
from .split_color import ColorSplitter
    
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

    @property
    def is_bound_to_harmonizer(self):
        return bpy.context.scene.scene_props.is_playing or bpy.context.scene.scene_props.in_frame_change

    def find_my_patch_controller(self):
        if self.generator.controller_type not in ["Fixture", "Pan/Tilt Fixture"]:
            for obj in bpy.data.objects:
                if obj.object_identities_enum == "Fixture" and obj.list_group_channels[0].chan == self.channel:
                    return obj
        return self.generator.parent


    def execute(self):
        if self.property_name in PROPERTIES_TO_MAP:
            self.value = SliderToFixtureMapper(self).execute()

        if self.property_name == 'color':
            self.property_name, self.value = ColorSplitter(self.generator, self).execute()

        argument_template = self._find_my_argument_template()

        self.send_cpv(argument_template)

    def _find_my_argument_template(self):
        console_mode = bpy.context.scene.scene_props.console_type_enum
        if console_mode == "option_eos":
            argument_template = Dictionaries.eos_arguments_dict.get(self.property_name, "Unknown Argument")
        elif console_mode == 'option_ma3':
            argument_template = Dictionaries.ma3_arguments_dict.get(self.property_name, "Unknown Argument")
        elif console_mode == 'option_ma2':
            argument_template = Dictionaries.ma2_arguments_dict.get(self.property_name, "Unknown Argument")
        else:
            SLI.SLI_assert_unreachable()
            return "Invalid console mode."

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

    def send_cpv(self, argument_template):
        if self.is_bound_to_harmonizer and not self.is_harmonized:
            global change_requests
            change_requests.append((self.generator, self.channel, self.property_name, self.value))
        else:
            address, full_argument = self.form_osc(argument_template)
            OSC.send_osc_lighting(address, full_argument, user=0)

    def form_osc(self, argument_template):
        channel = self.channel
        parameter = self.property_name
        value = self.value
        address = self._find_osc_address()

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
            address = address.replace("#", channel).replace("$", value)
            argument = argument_template.replace("#", channel).replace("$", value)
        else:
            formatted_values = [self.format_value(val) for val in value]

            channel = self.format_channel(channel)
            argument = argument_template.replace("#", channel)
            
            for i, formatted_value in enumerate(formatted_values):
                argument = argument.replace(color_profiles[parameter][i], str(formatted_value))

        return address, argument
    
    def _find_osc_address(self):
        console_mode = bpy.context.scene.scene_props.console_type_enum
        if console_mode == "option_eos":
            return "/eos/newcmd"
        elif console_mode == 'option_ma3':
            return "/cmd"
        elif console_mode == 'option_ma2':
            return "/cmd"
        else:
            SLI.SLI_assert_unreachable()
            return "/eos/newcmd"
    
    def format_channel(self, channel):
        return str(channel)
    
    def format_value(self, value):
        rounding = {
            "option_eos": 0,
            "option_grandMA2": 2,
            "option_grandMA3": 2
        }
        console_type = bpy.context.scene.scene_props.console_type_enum
        value = round(value, rounding[console_type])
        if console_type == 'option_eos':
            value = self.add_zero_prefix_for_eos(value)
        else:
            value = str(value)
        return value
    
    def add_zero_prefix_for_eos(self, value):
        '''We have to do this stuff because Eos interprets "1" as 10, "2" as 20, etc.'''
        if -10 < value < 10:
            return f"{'-0' if value < 0 else '0'}{abs(value)}"
        return str(value)

    def find_objects():
        relevant_objects = []
        for obj in bpy.data.objects:
            if obj.object_identities_enum == "Fixture":
                relevant_objects.append(obj)
                pass
        return relevant_objects


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