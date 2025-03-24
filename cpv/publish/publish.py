# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from ...utils.osc import OSC
from ..split_color import ColorSplitter
from .form_osc import FormOSC
from .prepare import Prepare
from ...utils.spy_utils import REGISTERED_LIGHTING_CONSOLES
    
change_requests = []

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


class Publish:
    def __init__(self, Generator, Parameter, channel, property_name, value, sender, is_already_harmonized=False):
        self.Generator = Generator
        self.Parameter = Parameter
        self.channel = channel
        self.property_name = property_name.replace("alva_", "")
        self.value = value
        self._sender = sender
        self._is_already_harmonized = is_already_harmonized
        self._is_color = self._is_color()
        self.patch_controller = self.find_my_patch_controller()
        self.LightingConsole = self.find_installed_lighting_console_data_class()

    def _is_color(self):
        return self.property_name in VERSIONS_OF_COLOR

    def find_my_patch_controller(self):
        if self.Generator.controller_type not in ["Fixture", "Pan/Tilt Fixture"]:
            for obj in bpy.data.objects:
                if obj.object_identities_enum == "Fixture" and obj.list_group_channels[0].chan == self.channel:
                    return obj
        return self.Generator.parent
    
    @staticmethod
    def find_installed_lighting_console_data_class(console_mode=None):
        if not console_mode:
            console_mode = bpy.context.scene.scene_props.console_type_enum
        return REGISTERED_LIGHTING_CONSOLES[console_mode]

    @property
    def _in_playback_or_frame_change(self):
        scene = bpy.context.scene.scene_props
        return scene.is_playing or scene.in_frame_change
    
    @property
    def _publish_mode(self):
        return MODE_LOOKUP[(self._sender, self._is_already_harmonized, self._in_playback_or_frame_change)]
    
    @property
    def _should_wait_for_others(self):
        return self._publish_mode == ADD_TO_COLLECTION
    
    @property
    def _should_yield_to_event_manager(self):
        return self._publish_mode == RETURN_TO_EVENT_MANAGER_FOR_HARMONIZATION


    def execute(self):
        self._split_color()
        self._publish()

    def _split_color(self):
        if self._is_color:
            self.property_name, self.value = ColorSplitter(self.Generator, self).execute()

    def _publish(self):
        if self._should_wait_for_others:
            self._add_to_collection()
            return

        self.value, self.argument_template = Prepare(self.LightingConsole, self, self.Parameter).execute()
        full_argument, address = FormOSC(self.LightingConsole, self).execute()

        if self._should_yield_to_event_manager:
            return full_argument, address
        
        self._send_now(full_argument, address)

    def _add_to_collection(self):
        global change_requests
        change_requests.append((self.Generator, self.channel, self.property_name, self.value))
    
    def _send_now(self, full_argument, address):
        OSC.send_osc_lighting(address, full_argument, user=0)


def test_publisher(SENSITIVITY): # Return True for fail, False for pass
    return False