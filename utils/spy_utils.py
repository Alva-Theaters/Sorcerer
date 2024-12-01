# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later


REGISTERED_LIGHTING_CONSOLES = {}

class _SorcererPython:
    class types:
        class LightingConsole:
            rounding_points = 0

            def execute(self):
                # Will later house orb functionality.
                return
            
            def format_value(value):
                return str(value)
        
        
    class utils:
        def as_register_class(cls):
            is_valid_console = _SorcererPython.utils._validate_lighting_console(cls)
            if is_valid_console:
                REGISTERED_LIGHTING_CONSOLES[cls.as_idname] = cls
        
        @staticmethod
        def _validate_lighting_console(cls):
            required_attributes = {
                "as_idname": "an 'as_idname' attribute",
                "as_label": "an 'as_label' attribute",
                "as_description": "an 'as_description' attribute",
                "osc_address": "an 'osc_address' attribute",
                "absolute": 'an "absolute" dictionary containing absolute argument templates',
                "increase": 'an "increase" dictionary containing relative argument templates',
                "decrease": 'a "decrease" dictionary containing relative argument templates',
            }

            missing_attributes = []
            for attr, description in required_attributes.items():
                if not hasattr(cls, attr) or not getattr(cls, attr, None):
                    missing_attributes.append(description)

            if missing_attributes:
                print(f"\nERROR: Class '{cls.__name__}' is missing the following required attributes:")
                for issue in missing_attributes:
                    print(f"  - {issue}")
                return False

            return True

            
        @staticmethod
        def as_unregister_class(cls):
            if cls.as_idname in REGISTERED_LIGHTING_CONSOLES:
                del REGISTERED_LIGHTING_CONSOLES[cls.as_idname]
            else:
                print(f"\nWARNING: Class '{cls.__name__}' with ID '{cls.as_idname}' was not found in registered consoles.")