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


import bpy
from .scene_props import register as scene_props_register, unregister as scene_props_unregister
from .sequencer_main import register as sequencer_main_register, unregister as sequencer_main_unregister
from .three_dee_operators import register as three_dee_operators_register, unregister as three_dee_operators_unregister
from .sequencer_operators import register as sequencer_operators_register, unregister as sequencer_operators_unregister
from .harmonizer import register as harmonizer_register, unregister as harmonizer_unregister
from .three_dee_main_ui import register as three_dee_main_ui_register, unregister as three_dee_main_ui_unregister
from .three_dee_nodes_ui import register as three_dee_nodes_ui_register, unregister as three_dee_nodes_ui_unregister
from .sequencer_ui import register as sequencer_ui_register, unregister as sequencer_ui_unregister
from .hotkeys_popups import register as hotkeys_popups_register, unregister as hotkeys_popups_unregister


bl_info = {
    "name": "Alva Sorcerer",
    "author": "Alva Theaters",
    "location": "Nodes/View3D/Sequencer", 
    "version": (1, 0),
    "blender": (4, 0, 2),
    "description": "3D animation but in real life, for theatrical light design/audio.",
    "warning": "For reliability, migrate all data to console prior to real show.",
    "wiki_url": "https://blendermarket.com/products/sorcerer/docs",
    "tracker_url": "https://www.workstraight.com/site/login",
    }


def register():
    try:
        scene_props_register()
    except Exception as e:
        print("Failed to register scene props:", e)
    
    try:
        sequencer_main_register()
    except Exception as e:
        print("Failed to register sequencer main:", e)
    
    try:
        three_dee_operators_register()
    except Exception as e:
        print("Failed to register 3D operators:", e)
    
    try:
        sequencer_operators_register()
    except Exception as e:
        print("Failed to register sequencer operators:", e)
    
    try:
        harmonizer_register()
    except Exception as e:
        print("Failed to register harmonizer:", e)
    
    try:
        three_dee_main_ui_register()
    except Exception as e:
        print("Failed to register 3D main UI:", e)
    
    try:
        three_dee_nodes_ui_register()
    except Exception as e:
        print("Failed to register 3D nodes UI:", e)
    
    try:
        sequencer_ui_register()
    except Exception as e:
        print("Failed to register sequencer UI:", e)
    
    try:
        hotkeys_popups_register()
    except Exception as e:
        print("Failed to register hotkeys and popups:", e)
        

def unregister():
    try:
        scene_props_unregister()
    except Exception as e:
        print("Failed to unregister scene props:", e)
    
    try:
        sequencer_main_unregister()
    except Exception as e:
        print("Failed to unregister sequencer main:", e)
    
    try:
        three_dee_operators_unregister()
    except Exception as e:
        print("Failed to unregister 3D operators:", e)
    
    try:
        sequencer_operators_unregister()
    except Exception as e:
        print("Failed to unregister sequencer operators:", e)
    
    try:
        harmonizer_unregister()
    except Exception as e:
        print("Failed to unregister harmonizer:", e)
    
    try:
        three_dee_main_ui_unregister()
    except Exception as e:
        print("Failed to unregister 3D main UI:", e)
    
    try:
        three_dee_nodes_ui_unregister()
    except Exception as e:
        print("Failed to unregister 3D nodes UI:", e)
    
    try:
        sequencer_ui_unregister()
    except Exception as e:
        print("Failed to unregister sequencer UI:", e)
    
    try:
        hotkeys_popups_unregister()
    except Exception as e:
        print("Failed to unregister hotkeys and popups:", e)
  

if __name__ == "__main__":
    register()
