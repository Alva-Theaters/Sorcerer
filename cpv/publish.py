# SPDX-FileCopyrightText: 2025 Alva Theaters
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
VERSIONS_OF_COLOR = ['color', 'raise_color', 'lower_color']

# Callers
CPV = 'CPV'
EVENT_MANAGER = 'EVENT_MANAGER'

# Publish Modes
SEND_NOW = 'SEND_NOW'
ADD_TO_COLLECTION = 'ADD_TO_COLLECTION'
RETURN_TO_EVENT_MANAGER_FOR_HARMONIZATION = 'RETURN_TO_EVENT_MANAGER_FOR_HARMONIZATION'

MODE_LOOKUP = { # (_sender, _is_already_harmonized, _in_playback_or_frame_change)
    (CPV, False, False): SEND_NOW,
    (CPV, False, True): ADD_TO_COLLECTION,
    (EVENT_MANAGER, True, True): RETURN_TO_EVENT_MANAGER_FOR_HARMONIZATION, # 3rd is irrelevant here
    (EVENT_MANAGER, True, False): RETURN_TO_EVENT_MANAGER_FOR_HARMONIZATION # 3rd is irrelevant here
}

COLOR_PROFILES = {
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


class Publish:
    def __init__(self, generator, channel, property_name, value, sender, is_already_harmonized=False):
        self.generator = generator
        self.channel = channel
        self.property_name = property_name
        self.value = value
        self.patch_controller = self.find_my_patch_controller()
        self._sender = sender
        self._is_already_harmonized = is_already_harmonized

    @property
    def _in_playback_or_frame_change(self):
        scene = bpy.context.scene.scene_props
        return scene.is_playing or scene.in_frame_change
    
    @property
    def _publish_mode(self):
        if (self._sender, self._is_already_harmonized, self._in_playback_or_frame_change) not in MODE_LOOKUP:
            SLI.SLI_assert_unreachable()
            return None
        
        return MODE_LOOKUP[(self._sender, self._is_already_harmonized, self._in_playback_or_frame_change)]

    def find_my_patch_controller(self):
        if self.generator.controller_type not in ["Fixture", "Pan/Tilt Fixture"]:
            for obj in bpy.data.objects:
                if obj.object_identities_enum == "Fixture" and obj.list_group_channels[0].chan == self.channel:
                    return obj
        return self.generator.parent
    
    @staticmethod
    def find_installed_lighting_console_data_class(console_mode=None):
        if not console_mode:
            console_mode = bpy.context.scene.scene_props.console_type_enum
            
        try:
            return REGISTERED_LIGHTING_CONSOLES[console_mode]
        except KeyError:
            print(f"Error: The console mode '{console_mode}' is not registered.")
            return None


    def execute(self):
        mode = self._publish_mode

        if mode == ADD_TO_COLLECTION:
            self._add_to_collection()
            return
        
        if mode in [RETURN_TO_EVENT_MANAGER_FOR_HARMONIZATION, SEND_NOW]:
            self._initialize_data_class_attributes()
            self._finalize_fixture_specific_attributes()

        if mode == RETURN_TO_EVENT_MANAGER_FOR_HARMONIZATION:
            return self.form_osc() # Returns full_argument, address
        
        if mode == SEND_NOW:
            self._send_now()

    def _add_to_collection(self):
        global change_requests
        change_requests.append((self.generator, self.channel, self.property_name, self.value))

    def _initialize_data_class_attributes(self):
        self._DataClass = self.find_installed_lighting_console_data_class()
        self._address = self._DataClass.osc_address
        self._rounding_points = self._DataClass.rounding_points
        self._format_value_function = self._DataClass.format_value

    def _finalize_fixture_specific_attributes(self):
        if self.property_name in PROPERTIES_TO_MAP:
            self.value = SliderToFixtureMapper(self).execute()

        if self.property_name in VERSIONS_OF_COLOR:
            self.property_name, self.value = ColorSplitter(self.generator, self).execute()

        self._argument_template = self._find_argument_template() # Color splitter goes first to id argument type needed

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
        special_argument = getattr(self.patch_controller, f"str_{'disable' if self.value == 0 else 'enable'}_{self.property_name}_argument")

        if self.property_name == 'strobe' and self.value != 0:
            return f"{special_argument}, {argument_template}"
        
        return special_argument

    def form_osc(self):
        channel = self.format_channel(self.channel)
        parameter = self.property_name
        value = self.value

        if parameter in COLOR_PROFILES:
            formatted_values = [self.format_value(val) for val in value]
            argument = self._argument_template.replace("#", channel)
            
            for i, formatted_value in enumerate(formatted_values):
                argument = argument.replace(COLOR_PROFILES[parameter][i], str(formatted_value))

            return argument, self._address

        value = self.format_value(value)
        address = self._address.replace("#", channel).replace("$", value)
        argument = self._argument_template.replace("#", channel).replace("$", value)
        return argument, address
    
    def format_channel(self, channel):
        return str(channel)
    
    def format_value(self, value):
        value = round(value, self._rounding_points)
        value = self._format_value_function(value)
        return value
    
    def _send_now(self):
        full_argument, address = self.form_osc()
        OSC.send_osc_lighting(address, full_argument, user=0)


def clear_requests():
    global change_requests
    change_requests = []
    

def update_other_selections(context, parent, property_name):
    if parent != context.active_object:
        return  # Prevent infinite recursion
    
    others = [obj for obj in bpy.context.selected_objects if obj.type in ['MESH', 'LIGHT']]
    if parent in others:
        others.remove(parent)
    for obj in others:
            setattr(obj, f"alva_{property_name}", getattr(parent, f"alva_{property_name}"))


def test_publisher(SENSITIVITY): # Return True for fail, False for pass
    return False