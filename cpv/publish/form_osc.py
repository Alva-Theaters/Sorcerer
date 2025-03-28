# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

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


class FormOSC:
    def __init__(self, LightingConsole, Publisher):
        self.Publisher = Publisher
        self.parameter = Publisher.property_name

        self._address = LightingConsole.osc_address
        self._rounding_points = LightingConsole.rounding_points
        self._format_value_function = LightingConsole.format_value

        if not self.Publisher._is_color:
            self.channel = self.format_channel(Publisher.channel)
            self.value = self.format_value(Publisher.value)

    def format_channel(self, channel):
        return str(channel)
    
    def format_value(self, value):
        value = round(value, self._rounding_points)
        value = self._format_value_function(value)
        return value


    def execute(self):
        if self.Publisher._is_color:
            return self._format_color_object()
        argument = self._find_argument()
        address = self._find_address()
        return argument, address
    
    def _format_color_object(self):
        property_name = self.Publisher.property_name
        formatted_values = [self.format_value(val) for val in self.Publisher.value]
        argument = self.Publisher.argument_template.replace("#", self.format_channel(self.Publisher.channel))
        
        for i, formatted_value in enumerate(formatted_values):
            argument = argument.replace(COLOR_PROFILES[property_name][i], str(formatted_value))

        return argument, self._address
    
    def _find_argument(self):
        return self.Publisher.argument_template.replace("#", self.channel).replace("$", self.value)
    
    def _find_address(self):
        return self._address.replace("#", self.channel).replace("$", self.value)