# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

ABSOLUTE = 'absolute'
RAISE = 'raise'
LOWER = 'lower'


class FindArgumentTemplate:
    def __init__(self, LightingConsole, Publisher, Parameter):
        self.LightingConsole = LightingConsole
        self.Publisher = Publisher
        self.Parameter = Parameter

        self.set_mode = self._find_set_mode()
        self.argument_dict = self._get_argument_dict()
    
    def _find_set_mode(self):
        if "raise_" in self.Publisher.property_name:
            return RAISE
        if "lower_" in self.Publisher.property_name:
            return LOWER
        return ABSOLUTE
    
    def _get_argument_dict(self):
        if self.set_mode == ABSOLUTE:
            return self.LightingConsole.absolute
        if self.set_mode == RAISE:
            return self.LightingConsole.increase
        return self.LightingConsole.lower
    

    def execute(self):
        argument_template = self.find_argument()
        special_argument_func = self._find_special_argument_func()
        if special_argument_func:
            argument_template = special_argument_func(self.Publisher.patch_controller, argument_template, self.Publisher.value)
        return argument_template
    
    def find_argument(self):
        argument = self.argument_dict.get(self.Publisher.property_name, None)
        
        if argument:
            return argument
        
        if hasattr(self.Parameter, "argument_if_not_found"):
            return getattr(self.Parameter, "argument_if_not_found")
        
        return f"Argument not found for {self.Publisher.property_name}"
    
    def _find_special_argument_func(self):
        if hasattr(self.Parameter, "add_special_osc_argument"):
            return getattr(self.Parameter, "add_special_osc_argument")