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


scripts = [
    # OSC
    "print_osc_lighting",
    "print_osc_video",
    "print_osc_audio",
    "print_osc",

    # CPVIA
    "print_cpvia_generator",
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
    "print_orb"
]


def alva_log(script, string):
    if bpy.context.scene.scene_props.service_mode:
        if f"print_{script}" in scripts:
            if getattr(bpy.context.scene.scene_props, f"print_{script}"):
                print(string)