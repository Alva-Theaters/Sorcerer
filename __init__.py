# This file is part of Alva Sorcerer.
# Copyright (C) 2024 Alva Theaters

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

'''
=====================================================================
                      DESIGNED BY ALVA THEATERS
                       FOR THE SOLE PURPOSE OF
                         MAKING PEOPLE HAPPY
=====================================================================
'''

# This file is part of Alva Sorcerer.
# Copyright (C) 2024 Alva Theaters

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


'''
=====================================================================
                      DESIGNED BY ALVA THEATERS
                       FOR THE SOLE PURPOSE OF
                         MAKING PEOPLE HAPPY
=====================================================================
'''

## Double hashtag indicates notes for future development requiring some level of attention

bl_info = {
    "name": "Alva Sorcerer",
    "author": "Alva Theaters",
    "location": "ShaderEditor/View3D/Sequencer/TextEditor/Properties",
    "version": (2, 0, 3),
    "blender": (4, 1, 0),
    "description": "3D animation in real life, for theatre, with Blender.",
    "warning": "Copious UI components. Not for existing Blender workflows.",
    "wiki_url": "https://alva-sorcerer.readthedocs.io/en/latest/index.html#",
    "tracker_url": "https://sorcerer.alvatheaters.com/support",
    "category": "EMARs",
}

as_info = {
    "alpha": False,
    "beta": True,
    "rating": "Experimental",
    "restrictions_url": "https://github.com/Alva-Theaters/Sorcerer/discussions/55"
}

import bpy
import sys
import os

sys.path.append(os.path.dirname(__file__))

# START SEQUENCE
MODULES = {
    'strip_formatter_ops': 'operators.strip_formatter_ops',
    'ui_lists': 'as_ui.ui_lists',
    'property_groups': 'properties.property_groups',
    'lighting_nodes': 'nodes.lighting_nodes',
    'audio_nodes': 'nodes.audio_nodes',
    'node_operators': 'operators.node_operators',
    'properties_operators': 'operators.properties_operators',
    'view3d_operators': 'operators.view3d_operators',
    'cue_builder_ops': 'operators.cue_builder_ops',
    'sequencer_operators': 'operators.sequencer_operators',
    'orb_operators': 'operators.orb_operators',
    'common_operators': 'operators.common_operators',
    'text_properties': 'properties.text_properties',
    'settings_properties': 'properties.settings_properties',
    'sequencer_props': 'properties.sequencer_properties',
    'scene_properties': 'properties.scene_properties',
    'common_properties': 'properties.common_properties',
    'panels': 'panels',
    'menus': 'as_ui.menus',
    'event_manager': 'event_manager',
    'keymap': 'operators.keymap',
}

REGISTER_FUNCS = []
UNREGISTER_FUNCS = []


for module_name, module_path in MODULES.items():
    try:
        module = __import__(f"{__package__}.{module_path}", fromlist=['register', 'unregister'])
        REGISTER_FUNCS.append(module.register)
        UNREGISTER_FUNCS.append(module.unregister)
    except ImportError as e:
        print(f"Failed to import {module_name}: {e}")


def register():
    for register_func in REGISTER_FUNCS:
        try:
            register_func()
        except Exception as e:
            print(f"Failed to register: {e}")

    from .spy import SorcererPython  # Simply importing this initializes spy
    bpy.app.timers.register(on_register, first_interval=.01)


def on_register():
    from .maintenance.tests import test_sorcerer
    from .event_manager import load_macro_buttons

    test_sorcerer()
    load_macro_buttons("")


def unregister():
    for unregister_func in reversed(UNREGISTER_FUNCS):
        try:
            unregister_func()
        except Exception as e:
            print(f"Failed to unregister: {e}")