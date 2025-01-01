# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

'''
Currently choosing not to use conventional logging methods because they seem overly complicated.
Doing it this way allows you to choose exactly what you want printed in the Blender UI with the
simplest possible UI. Don't need to learn anything at all whatsoever about how logging works. 
This method could not possibly be any simpler. 

Plus, you can change what scripts will be debugged from the Blender UI in real time without need 
to reload scripts, so it's 100 times faster and more efficient for simpler use-cases like ours.

To enable Service Mode and to get to the toggles, just type "service mode" into the Eos command 
line in 3D View. A new panel should appear where you can control what is and is not printed in real 
time. Do the same thing to disable Service Mode.

Furthermore, this method doesn't add the completely pointless "LOGGING" prefix to every message,
so it reduces visual clutter.
'''

LOGGING_FORMAT_SPEC = """
Logging for major classes should be in the following format for readability:

    INFLUENCER SESSION: # for more complex chunks
    SUBTYPE 1. Logging info
    SUBTYPE 1. More logging info
    SUBTYPE 1. More logging info
    SUBTYPE 2. More logging info from maybe a different subclass
    SUBTYPE 2. More logging info

    HARMONIZER SESSION:  # For less complex chunks
    Logging info
    More logging info
    Even more logging info

    SOME OTHER SESSION:
    Some more logging info...

Separate chunks of logging with blank lines so dissimilar logging statements don't quish together.
"""


scripts = [ # These correspond directly to property names registered to scene, drawn in the service mode panel.
    # OSC. Not actually separate scripts like the others.
    "print_osc_lighting",
    "print_osc_video",
    "print_osc_audio",
    "print_osc",

    # CPV
    "print_cpv_generator",
    "print_find",
    "print_stop",
    "print_harmonize",
    "print_influence",
    "print_map",
    "print_mix",
    "print_publish",
    "print_split_color",
    "print_audio",

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