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
    "version": (2, 0),
    "blender": (4, 1, 0),
    "description": "3D animation in real life, for theatre, with Blender.",
    "warning": "For reliability, migrate all data to console prior to real show.",
    "wiki_url": "https://alva-sorcerer.readthedocs.io/en/latest/index.html#",
    "tracker_url": "https://www.workstraight.com/site/login",
    "category": "EMARs",
}

import sys
import os

sys.path.append(os.path.dirname(__file__))

import bpy

try:
    from .operators.strip_formatter_ops import register as strip_formatter_ops_register, unregister as strip_formatter_ops_unregister
except ImportError as e:
    print(f"Failed to import strip_formatter_ops: {e}")

try:
    from .ui.ui_lists import register as ui_lists_register, unregister as ui_lists_unregister
except ImportError as e:
    print(f"Failed to import ui_lists: {e}")

try:
    from .properties.property_groups import register as property_groups_register, unregister as property_groups_unregister
except ImportError as e:
    print(f"Failed to import property_groups: {e}")

try:
    from .nodes.lighting_nodes import register as lighting_nodes_register, unregister as lighting_nodes_unregister
except ImportError as e:
    print(f"Failed to import lighting_nodes: {e}")

try:
    from .nodes.audio_nodes import register as audio_nodes_register, unregister as audio_nodes_unregister
except ImportError as e:
    print(f"Failed to import audio_nodes: {e}")

try:
    from .operators.node_operators import register as node_operators_register, unregister as node_operators_unregister
except ImportError as e:
    print(f"Failed to import node_operators: {e}")

try:
    from .operators.properties_operators import register as props_operators_register, unregister as props_operators_unregister
except ImportError as e:
    print(f"Failed to import properties_operators: {e}")

try:
    from .operators.view3d_operators import register as view3d_operators_register, unregister as view3d_operators_unregister
except ImportError as e:
    print(f"Failed to import view3d_operators: {e}")

try:
    from .operators.cue_builder_ops import register as cue_builder_ops_register, unregister as cue_builder_ops_unregister
except ImportError as e:
    print(f"Failed to import cue_builder_ops: {e}")

try:
    from .operators.sequencer_operators import register as sequencer_operators_register, unregister as sequencer_operators_unregister
except ImportError as e:
    print(f"Failed to import sequencer_operators: {e}")

try:
    from .operators.common_operators import register as common_operators_register, unregister as common_operators_unregister
except ImportError as e:
    print(f"Failed to import common_operators: {e}")

try:
    from .properties.text_properties import register as text_properties_register, unregister as text_properties_unregister
except ImportError as e:
    print(f"Failed to import text_properties: {e}")

try:
    from .properties.settings_properties import register as settings_properties_register, unregister as settings_properties_unregister
except ImportError as e:
    print(f"Failed to import settings_properties: {e}")

try:
    from .properties.sequencer_props import register as sequencer_props_register, unregister as sequencer_props_unregister
except ImportError as e:
    print(f"Failed to import sequencer_props: {e}")

try:
    from .properties.scene_properties import register as scene_props_register, unregister as scene_props_unregister
except ImportError as e:
    print(f"Failed to import scene_properties: {e}")

try:
    from .properties.common_properties import register as common_properties_register, unregister as common_properties_unregister
except ImportError as e:
    print(f"Failed to import common_properties: {e}")

try:
    from .panels import register as panels_register, unregister as panels_unregister
except ImportError as e:
    print(f"Failed to import panels: {e}")

try:
    from .event_manager import register as event_manager_register, unregister as event_manager_unregister
except ImportError as e:
    print(f"Failed to import event_manager: {e}")

try:
    from .operators.keymap import register as keymap_register, unregister as keymap_unregister
except ImportError as e:
    print(f"Failed to import event_manager: {e}")


def register():
    try:
        strip_formatter_ops_register()
    except Exception as e:
        print("Failed to register strip_formatter_ops:", e)

    try:
        ui_lists_register()
    except Exception as e:
        print("Failed to register ui_lists:", e)

    try:
        property_groups_register()
    except Exception as e:
        print("Failed to register property_groups:", e)

    try:
        lighting_nodes_register()
    except Exception as e:
        print("Failed to register lighting_nodes:", e)

    try:
        audio_nodes_register()
    except Exception as e:
        print("Failed to register audio_nodes:", e)

    try:
        node_operators_register()
    except Exception as e:
        print("Failed to register node_operators:", e)

    try:
        props_operators_register()
    except Exception as e:
        print("Failed to register properties_operators:", e)

    try:
        view3d_operators_register()
    except Exception as e:
        print("Failed to register view3d_operators:", e)

    try:
        cue_builder_ops_register()
    except Exception as e:
        print("Failed to register cue_builder_ops:", e)

    try:
        sequencer_operators_register()
    except Exception as e:
        print("Failed to register sequencer_operators:", e)

    try:
        common_operators_register()
    except Exception as e:
        print("Failed to register common_operators:", e)

    try:
        text_properties_register()
    except Exception as e:
        print("Failed to register text_properties:", e)

    try:
        settings_properties_register()
    except Exception as e:
        print("Failed to register settings_properties:", e)

    try:
        sequencer_props_register()
    except Exception as e:
        print("Failed to register sequencer_props:", e)

    try:
        scene_props_register()
    except Exception as e:
        print("Failed to register scene_properties:", e)

    try:
        common_properties_register()
    except Exception as e:
        print("Failed to register common_properties:", e)

    try:
        panels_register()
    except Exception as e:
        print("Failed to register panels:", e)

    try:
        event_manager_register()
    except Exception as e:
        print("Failed to register event_manager:", e)

    try:
        keymap_register()
    except Exception as e:
        print("Failed to register keymap:", e)


def unregister():
    try:
        keymap_unregister()
    except Exception as e:
        print("Failed to unregister keymap:", e)

    try:
        event_manager_unregister()
    except Exception as e:
        print("Failed to unregister event_manager:", e)

    try:
        panels_unregister()
    except Exception as e:
        print("Failed to unregister panels:", e)

    try:
        common_properties_unregister()
    except Exception as e:
        print("Failed to unregister common_properties:", e)

    try:
        sequencer_props_unregister()
    except Exception as e:
        print("Failed to unregister sequencer_props:", e)

    try:
        settings_properties_unregister()
    except Exception as e:
        print("Failed to unregister settings_properties:", e)

    try:
        text_properties_unregister()
    except Exception as e:
        print("Failed to unregister text_properties:", e)

    try:
        common_operators_unregister()
    except Exception as e:
        print("Failed to unregister common_operators:", e)

    try:
        sequencer_operators_unregister()
    except Exception as e:
        print("Failed to unregister sequencer_operators:", e)

    try:
        cue_builder_ops_unregister()
    except Exception as e:
        print("Failed to unregister cue_builder_ops:", e)

    try:
        view3d_operators_unregister()
    except Exception as e:
        print("Failed to unregister view3d_operators:", e)

    try:
        scene_props_unregister()
    except Exception as e:
        print("Failed to unregister scene_properties:", e)

    try:
        props_operators_unregister()
    except Exception as e:
        print("Failed to unregister properties_operators:", e)

    try:
        node_operators_unregister()
    except Exception as e:
        print("Failed to unregister node_operators:", e)

    try:
        audio_nodes_unregister()
    except Exception as e:
        print("Failed to unregister audio_nodes:", e)

    try:
        lighting_nodes_unregister()
    except Exception as e:
        print("Failed to unregister lighting_nodes:", e)

    try:
        property_groups_unregister()
    except Exception as e:
        print("Failed to unregister property_groups:", e)

    try:
        ui_lists_unregister()
    except Exception as e:
        print("Failed to unregister ui_lists:", e)

    try:
        strip_formatter_ops_unregister()
    except Exception as e:
        print("Failed to unregister strip_formatter_ops:", e)