# This file is part of Alva Sorcerer
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


'''
Currently choosing not to use conventional logging methods because they seem overly complicated.
Doing it this way allows you to choose exactly what you want printed in the Blender UI with the
simplest possible UI. Don't need to learn anything at all whatsoever about how logging works. 
This method could not possibly be any simpler. 

Plus, you can change what scripts will be debugged from the Blender UI in real time without need 
to reload scripts, so it's 100 times faster and more efficient for simpler use-cases like ours.

To enable Service Mode and to get to the toggles, just type "service mode" into the 
str_manual_fixture_selection field in the group contoller in 3D View. A new panel should appear 
where you can control what is and is not printed in real time. Do the same thing to disable Service 
Mode.

Furthermore, this method doesn't add the completely pointless "LOGGING" prefix to every message,
so it reduces visual clutter.'''


scripts = [
    # OSC. Not actually separate scripts like the others.
    "print_osc_lighting",
    "print_osc_video",
    "print_osc_audio",
    "print_osc",

    # CPVIA
    "print_cpvia_generator",
    "print_find",
    "print_flags",
    "print_harmonizer",
    "print_influencers",
    "print_map",
    "print_mix",
    "print_publish",
    "print_split_color",

    # Operators
    "print_common_operators",
    "print_cue_builder_operators",
    "print_node_operators",
    "print_orb_operators",
    "print_properties_operators",
    "print_sequencer_operators",
    "print_strip_formatter_operators",
    "print_view3d_operators",

    # Updaters
    "print_common_updaters",
    "print_node_updaters",
    "print_properties_updaters",
    "print_sequencer_updaters",

    # Main
    "print_event_manager",
    "print_orb",
    "print_time"
]


def alva_log(script, string):
    if bpy.context.scene.scene_props.service_mode:
        if f"print_{script}" in scripts:
            if getattr(bpy.context.scene.scene_props, f"print_{script}"):
                print(string)
        else:
            print(f"Logging Error: {script} is not a recognized script name for logging.")