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


# START SEQUENCE - for scripts with their own register sections at the end.
MODULES = { # Order matters for dependency reasons!!!
    'strip_formatter': 'operators.strip_formatter',
    'ui_lists': 'as_ui.ui_lists',
    'property_groups': 'makesrna.property_groups',
    'lighting': 'nodes.lighting',
    'audio': 'nodes.audio',
    'node': 'operators.node',
    'properties': 'operators.properties',
    'view3d': 'operators.view3d',
    'text': 'operators.text',
    'cue_builder': 'operators.cue_builder',
    'sequencer': 'operators.sequencer',
    'orb': 'operators.orb',
    'common': 'operators.common',
    'preferences': 'operators.preferences',
    'rna_text': 'makesrna.rna_text',
    'rna_preferences': 'makesrna.rna_preferences',
    'rna_sequencer': 'makesrna.rna_sequencer',
    'rna_scene': 'makesrna.rna_scene',
    'rna_common': 'makesrna.rna_common',
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

    from .spy import SorcererPython  # Simply importing this makes "from bpy import spy" work in Text Editor
    register_as_classes()
    bpy.app.timers.register(on_register, first_interval=.01)

def register_as_classes():
    from .assets.lighting_consoles import register
    register()


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
    from .assets.lighting_consoles import unregister
    unregister()