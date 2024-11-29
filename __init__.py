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

TOP_LEVEL_DIRECTORY = """
First of all, the purpose of Alva Sorcerer is to basically animate an entire theater control booth 
with Blender. Most of Sorcerer is just for lighting, but some is for 3D audio too.

- as_ui: The vast majority of UI drawing code. Sorcerer's UI uses many helper functions because
    many UI draws are shared between Blender space_types. For this reason, panels.py only
    contains the least amount of UI logic possible. The .py file names should match Blender's
    internal codebase (for example, space_view3d.py).

- assets: This is just for stuff stuff. No logic should be here. Just dictionaries, item getters,
    lighting console data structures, tooltips, just stuff stuff. Toiletries, basically.

- cpv: The stuff here defines Sorcerer's internal data structure, in the format CPV. CPV stands 
    for (channel, parameter, value). This folder is essentially a CPV packet generator. 

    If user makes a controller that controls channels 1-10 and sets zoom from 0 to 100, this 
    folder is responsible for saying, "Ok, what channels does this controller target, what
    is the new value, what type of controller is it, what is the true zoom range of each
    fixture so we can map our new value accordingly, and what state is Blender in (playback,
    frame change, normal depsgraph update, scrub, etc.)?" Then, this folder "publishes" 
    the resulting CPV packet(s) through OSC to inform the lighting console. If in playback,
    this folder is also reponsible for fade engine duties such as harmonizing conflicting
    controller inputs. If 3 different controllers are trying to set the zoom on channel
    1 to 7, 23, and 100, respectively, during a frame change, this folder is responsible 
    for figuring out what the heck to tell the console.

- makesrna: This is where the vast majority of Sorcerer's properties are registered. It's 
    called "makesrna" and not "properties" to avoid confusion with space_properties.
    "makesrna" is borrowed from the Blender source. Some nodes and operators define
    their properties locally, but most should be defined here.

- nodes: Definitions for audio and lighting nodes. Note that Sorcerer's nodes live in World,
    not in a custom node tree (the way Blender would like us to do it). We do it against
    Blender's wishes because we want node groups. Node groups don't work in custom node
    trees. 

    Most node logic should be in the operators, as_ui, or cpv folder, not here. As a general
    rule, separate Class(bpy.types.) definitions from verbose runtime logic where possible.
    That way it's far easier to see what is what without having to scroll through essays 
    upon essays of code (Blender's space_view3d.py I'm looking at you).

- operators: Just the operators, as you would expect, mostly separated by space_type, but sometimes
    by pop-up or tool type. File name conventions borrowed again from the Blender source.

- startup: Files for the user's convenience, like the UI theme .xml and startup.blend, which helps
    new users start with the screen setup best for Sorcerer (because Sorcerer workflows are
    not really relevant to computer graphics workflows). 

- updaters: The updaters for anything that is not a CPV update (direct parameter update). 

- utils: Please do not make a misc_utils.py here. Right now, everything is organized into the 
    type is utils and there is no "utils.py" that just has anything and everything in it.
    Let's keep it that way.

- event_manager.py: This script is here to define what happens on events like play, stop, 
    scrub, frame change, and translate/transform. This script encompasses 3D audio and lighting,
    but most of the code is for lighting.

- orb.py: This script's job is to automate repetitive, boring tasks on lighting consoles.
    We use this tool because "creating macros" != "art".

- panels.py: This file is only for defining the stuff we put into the UI and when, and only very 
    rarely do we put runtime UI logic here. We want this file to just be for quickly 
    seeing what is going where.

- spy.py: This script, spy, is a sort of API here to make it easier for users to interact with 
    Sorcerer functions programmatically. Inspired by Blender's bpy API. Access from Blender's 
    built-in Text Editor or Console through "from bpy import spy".
"""


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
    bpy.app.timers.register(on_register, first_interval=.01)


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