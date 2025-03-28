# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.props import IntProperty, EnumProperty, FloatVectorProperty
from bpy.types import Object, ColorSequence, Light, Node

from ..makesrna.property_groups import MixerParameters

REGISTERED_LIGHTING_CONSOLES = {}
REGISTERED_STRIPS = {}
REGISTERED_PARAMETERS = {}
REGISTERED_CONTROLLERS = {}


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


        class LightingController:
            def execute(updater):
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
                register_bpy_property(cls)

            elif cls_id == SpyDataStructure.types.LightingController:
                if cls.as_idname in REGISTERED_CONTROLLERS:
                    del REGISTERED_CONTROLLERS[cls.as_idname]
                REGISTERED_CONTROLLERS[cls.as_idname] = cls

        
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
                    "as_description": "an 'as_description' attribute",
                    "as_property_name": "an 'as_property_name' attribute"
                },
                SpyDataStructure.types.LightingController: {
                    "as_idname": "an 'as_idname' attribute",
                    "as_description": "an 'as_description' attribute",
                    "execute": "an 'execute()' method"
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
            elif issubclass(cls, SpyDataStructure.types.LightingController):
                return SpyDataStructure.types.LightingController

            
        @staticmethod
        def as_unregister_class(cls):
            if cls.as_idname in REGISTERED_LIGHTING_CONSOLES:
                del REGISTERED_LIGHTING_CONSOLES[cls.as_idname]
            elif cls.as_idname in REGISTERED_STRIPS:
                del REGISTERED_STRIPS[cls.as_idname]
            elif cls.as_idname in REGISTERED_PARAMETERS:
                del REGISTERED_PARAMETERS[cls.as_idname]
            elif cls.as_idname in REGISTERED_CONTROLLERS:
                del REGISTERED_CONTROLLERS[cls.as_idname]
            else:
                print(f"\nWARNING: Class '{cls.__name__}' with ID '{cls.as_idname}' was not found in registration.")


def register_bpy_property(cls):
    as_idname = getattr(cls, 'as_idname', None)
    name = getattr(cls, 'as_label', "")
    description = getattr(cls, 'as_description', "")
    default = getattr(cls, 'default', 0)
    min = getattr(cls, 'static_min', 0)
    max = getattr(cls, 'static_max', 100)
    update = getattr(cls, 'update', None)
    items = getattr(cls, 'items', None)

    if items:
        prop = EnumProperty(
            name=name,
            description=description,
            items=items
        )

    elif isinstance(default, tuple):
        prop = FloatVectorProperty(
            name=name,
            description=description,
            default=default,
            size=len(default),
            min=min,
            max=max,
            update=update,
            options={'ANIMATABLE'},
            subtype='COLOR'
        )
        
    elif isinstance(default, int):
        prop = IntProperty(
            name=name,
            description=description,
            default=default,
            min=min,
            max=max,
            update=update,
            options={'ANIMATABLE'}
        )
        
    else:
        print(f"Skipping {cls.__name__}: Unsupported property type.")
        return

    controller_types = [Object, ColorSequence, Light, Node, MixerParameters]
    for controller in controller_types:
        setattr(controller, as_idname, prop)