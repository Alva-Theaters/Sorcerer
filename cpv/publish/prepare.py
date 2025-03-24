# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

from .map import SliderToFixtureMapper
from .find_argument_template import FindArgumentTemplate


class Prepare:
    def __init__(self, LightingConsole, Publisher, Parameter):
        self.LightingConsole = LightingConsole
        self.Publisher = Publisher
        self.Parameter = Parameter
        self.value = Publisher.value


    def execute(self):
        self._dynamically_map()
        argument_template = FindArgumentTemplate(self.LightingConsole, self.Publisher, self.Parameter).execute()
        return self.value, argument_template

    def _dynamically_map(self):
        if self._should_remap():
            self.value = SliderToFixtureMapper(self.value, self.Publisher.patch_controller, self.Parameter).execute()

    def _should_remap(self):
        return hasattr(self.Parameter, 'dynamic_min') and hasattr(self.Parameter, 'dynamic_max')