# This file is part of Alva Sorcerer.
# Copyright (C) 2025 Alva Theaters

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

bl_info = {
    "name": "Alva Sorcerer",
    "author": "Alva Theaters",
    "location": "ShaderEditor/View3D/Sequencer/TextEditor/Properties",
    "version": (2, 1, 0),
    "blender": (4, 1, 0),
    "description": "3D animation in real life, for theatre, with Blender.",
    "warning": "Copious UI components. Not for existing Blender workflows.",
    "wiki_url": "https://alva-sorcerer.readthedocs.io/en/latest/index.html#",
    "tracker_url": "https://sorcerer.alvatheaters.com/support",
    "category": "EMARs",
}

as_info = { # Used in Sorcerer's splash
    "alpha": False,
    "beta": True,
    "rating": "Experimental",
    "restrictions_url": "https://github.com/Alva-Theaters/Sorcerer/discussions/55"
}

import bpy
import sys
import os

sys.path.append(os.path.dirname(__file__))

DEBUG = False

# START SEQUENCE - for scripts with their own register sections at the end.
MODULES = { # Order matters for dependency reasons!!!
    'strip_formatter': 'operators.strip_formatter',  # 1
    'ui_lists': 'as_ui.ui_lists',  # 2
    'property_groups': 'makesrna.property_groups',  # 3
    'lighting': 'nodes.lighting',  # 4
    'audio': 'nodes.audio',  # 5
    'node': 'operators.node',  # 6
    'properties': 'operators.properties',  # 7
    'view3d': 'operators.view3d',  # 8
    'text': 'operators.text',  # 9
    'cue_builder': 'operators.cue_builder',  # 10
    'sequencer': 'operators.sequencer',  # 11
    'orb': 'operators.orb',  # 12
    'common': 'operators.common',  # 13
    'preferences': 'operators.preferences',  # 14
    'rna_text': 'makesrna.rna_text',  # 15
    'rna_preferences': 'makesrna.rna_preferences',  # 16
    'rna_sequencer': 'makesrna.rna_sequencer',  # 17
    'rna_scene': 'makesrna.rna_scene',  # 18
    'rna_common': 'makesrna.rna_common',  # 19
    'panels': 'panels',  # 20
    'menus': 'as_ui.menus',  # 21
    'event_manager': 'event_manager',  # 22
    'keymap': 'operators.keymap',  # 23
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
    for i, register_func in enumerate(REGISTER_FUNCS, start=1):
        if DEBUG: print(f"Trying to register {i}")
        try:
            register_func()
        except Exception as e:
            print(f"Failed to register: {e}")

    from .spy import SorcererPython  # Simply importing this makes "from bpy import spy" work in Text Editor
    register_as_classes()
    bpy.app.timers.register(on_register, first_interval=.01)

def register_as_classes():
    from .extendables.lighting_consoles import register as register_lighting_consoles
    register_lighting_consoles()

    from .extendables.sequencer_strips import register as register_strips
    register_strips()

    from .extendables.fixture_parameters import register as register_parameters
    register_parameters()


def on_register():
    from .maintenance.tests import test_sorcerer
    from .event_manager import load_macro_buttons

    test_sorcerer()
    load_macro_buttons("") # This needs to be here because that code needs a very specific bpy.context and it needs to run on load.


def unregister():
    for unregister_func in reversed(UNREGISTER_FUNCS):
        try:
            unregister_func()
        except Exception as e:
            print(f"Failed to unregister: {e}")

    unregister_as_classes()

def unregister_as_classes():
    from .extendables.lighting_consoles import unregister as unregister_lighting_consoles
    unregister_lighting_consoles()

    from .extendables.sequencer_strips import unregister as unregister_strips
    unregister_strips()

    from .extendables.fixture_parameters import unregister as unregister_parameters
    unregister_parameters()