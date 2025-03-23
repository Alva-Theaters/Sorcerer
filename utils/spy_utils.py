# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later


REGISTERED_LIGHTING_CONSOLES = {}
REGISTERED_STRIPS = {}
REGISTERED_PARAMETERS = {}


class SpyDataStructure:
    class types:
        class LightingConsole:
            rounding_points = 0
            
            def format_value(value):
                return str(value)
            

            def key(self, key_string, direction=None):
                print("Pressing key up then down.")


            def cmd(self, command_string):
                print("Sending command.")


            def save_console_file(self):
                print("Saving console file.")


            def prepare_console_for_automation(self):
                print("Preparing console for automation.")


            def restore_console_to_normal_following_automation(self):
                print("Restoring console following automation.")


            def record_cue(self, cue_number, cue_duration):
                print("Recording a cue.")


            def record_discrete_time(self, Orb, slowed_prop_name):
                print("Recording discrete time.")


            def update_cue(self):
                print("Updating a cue.")


        class SequencerStrip:
            streaming = False  # Seems better than using a hasattr in the mapping function

            def draw(self, context):
                pass


        class FixtureParameter:
            def draw_row(self, context):
                pass

            def draw_popup(self, context):
                pass
        
        
    class utils:
        def as_register_class(cls):
            is_valid_console, cls_id = SpyDataStructure.utils._validate_cls(cls)
            if not is_valid_console:
                return
            
            if cls_id == SpyDataStructure.types.LightingConsole:
                if cls.as_idname in REGISTERED_LIGHTING_CONSOLES:
                    del REGISTERED_LIGHTING_CONSOLES[cls.as_idname]
                REGISTERED_LIGHTING_CONSOLES[cls.as_idname] = cls

            elif cls_id == SpyDataStructure.types.SequencerStrip:
                if cls.as_idname in REGISTERED_STRIPS:
                    del REGISTERED_STRIPS[cls.as_idname]
                REGISTERED_STRIPS[cls.as_idname] = cls

            elif cls_id == SpyDataStructure.types.FixtureParameter:
                if cls.as_idname in REGISTERED_PARAMETERS:
                    del REGISTERED_PARAMETERS[cls.as_idname]
                REGISTERED_PARAMETERS[cls.as_idname] = cls
        
        @staticmethod
        def _validate_cls(cls):
            required_attributes = {
                SpyDataStructure.types.LightingConsole: {
                    "as_idname": "an 'as_idname' attribute",
                    "as_label": "an 'as_label' attribute",
                    "as_description": "an 'as_description' attribute",
                    "osc_address": "an 'osc_address' attribute",
                    "absolute": 'an "absolute" dictionary containing absolute argument templates',
                    "increase": 'an "increase" dictionary containing relative argument templates',
                    "decrease": 'a "decrease" dictionary containing relative argument templates',
                },
                SpyDataStructure.types.SequencerStrip: {
                    "as_idname": "an 'as_idname' attribute",
                    "as_label": "an 'as_label' attribute",
                    "as_description": "an 'as_description' attribute",
                    "as_icon": "an 'as_icon' attribute"
                },
                SpyDataStructure.types.FixtureParameter: {
                    "as_idname": "an 'as_idname' attribute",
                    "as_description": "an 'as_description' attribute"
                }
            }

            subclass = SpyDataStructure.utils.find_subclass(cls)

            try:
                required_attributes = required_attributes[subclass]
            except KeyError:
                print(f"Class {cls} does not have a valid mix-in class.")
                return False, None

            missing_attributes = []
            for attr, description in required_attributes.items():
                if not hasattr(cls, attr) or not getattr(cls, attr, None):
                    missing_attributes.append(description)

            if missing_attributes:
                print(f"\nERROR: Class '{cls.__name__}' is missing the following required attributes:")
                for issue in missing_attributes:
                    print(f"  - {issue}")
                return False, None

            return True, subclass
        

        @staticmethod
        def find_subclass(cls):
            if issubclass(cls, SpyDataStructure.types.LightingConsole):
                return SpyDataStructure.types.LightingConsole
            elif issubclass(cls, SpyDataStructure.types.SequencerStrip):
                return SpyDataStructure.types.SequencerStrip
            elif issubclass(cls, SpyDataStructure.types.FixtureParameter):
                return SpyDataStructure.types.FixtureParameter

            
        @staticmethod
        def as_unregister_class(cls):
            if cls.as_idname in REGISTERED_LIGHTING_CONSOLES:
                del REGISTERED_LIGHTING_CONSOLES[cls.as_idname]
            elif cls.as_idname in REGISTERED_STRIPS:
                del REGISTERED_STRIPS[cls.as_idname]
            elif cls.as_idname in REGISTERED_PARAMETERS:
                del REGISTERED_PARAMETERS[cls.as_idname]
            else:
                print(f"\nWARNING: Class '{cls.__name__}' with ID '{cls.as_idname}' was not found in registration.")