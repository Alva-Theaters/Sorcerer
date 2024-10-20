# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

'''
Minimizing Design Drag Coefficient (DDC) with Longer Tooltips

The Design Drag Coefficient (DDC) measures the time spent in a design process due to the 
Single-Point Delay of reading a tooltip (SPD) and consulting the manual (RTFM events). Contrary
to most UI design, Sorcerer intentionally uses longer tooltips liberally because the math
shows this actually reduces DDC. What the equation shows is that the time wasted by RTFM's
blows the time wasted by reading tooltips out of the water. So we want to reduce RTFM's at
all costs. One bad RTFM is the equivalent of reading a novella's worth of tooltips.

The general formula for DDC in this context is:

                N_actions * (T_SPD + (F_RTFM * T_RTFM))
    DDC = --------------------------------------------
                     N_actions * T_RTFM

Where:
    N_actions: The number of actions performed.
    T_SPD: Time to read a tooltip.
    F_RTFM: Frequency of RTFM events (as a fraction).
    T_RTFM: Time to read the manual (assumed to be 10 minutes = 600 seconds).

For short tooltips, where the delay is only 5% of 10 minutes for each RTFM event:

                 N_actions * (1 + (0.05 * T_RTFM))
    DDC_short = -----------------------------------
                    N_actions * T_RTFM

    DDC_short = (1000 * (1 + (0.05 * 600))) / (1000 * 600)
              = 0.050

For long tooltips, where the delay is 1% of 10 minutes per RTFM event:

                N_actions * (5 + (0.01 * T_RTFM))
    DDC_long = -----------------------------------
                   N_actions * T_RTFM

    DDC_long = (1000 * (5 + (0.01 * 600))) / (1000 * 600)
             = 0.0133
             
In summary:
- Short tooltips lead to a DDC_short of 0.050.
- Long tooltips lead to a DDC_long of 0.0133, meaning less time is wasted overall,
  via only a small decrease in RTFM frequency.

  In other words, we want to do everything we can to decrease RTFM's because that
  leads to disproportional gains in overall design efficiency.
'''


def find_tooltip(name):
    try:
        tooltip = tooltips[name.lower()]
    except:
        tooltip = ""
        print(f"Error: Could not find tooltip {name}. Returning empty string.")
    
    return format_tooltip(tooltip)


def format_tooltip(tooltip):
    if is_automatic_period():
        if tooltip.endswith("."): # In case dev forgot to remove period
            tooltip = tooltip[:-1]
        return tooltip
    
    elif is_paragraph(tooltip):
        if not tooltip.endswith("."):
            tooltip = tooltip + "."
        return tooltip
    
    return tooltip


def is_automatic_period():
    return bpy.app.version < (4, 3)
    

def is_paragraph(text):
    word_threshold = 30
    sentence_threshold = 1 # Not 2 because a second sentence will not likely have a period.
    
    word_count = len(text.split())
    sentence_count = text.count('.') + text.count('!') + text.count('?')
    
    if word_count >= word_threshold or sentence_count >= sentence_threshold:
        return True
    else:
        return False
    

tooltips = {
    # Lighting Parameters
    "intensity": "Intensity value",
    "strobe": "Strobe value",
    "color": (
        "Color value. If your fixture is not an RGB fixture, but CMY, RGBA, or something like that, "
        "Sorcerer will automatically translate RGB to the correct color profile. The best way to tell "
        "Sorcerer which color profile is here on the object controller, to the right of this field. To make "
        "changes to many at a time, use the magic 'Profile to Apply' feature on the top left of this box, "
        "or the 'Apply Patch to Objects in Scene' button at the end of the group patch below this panel"
    ),
    "color_restore": (
        "Why are there 2 colors for this one? Because remotely making relative changes to color doesn't work well. "
        "Influencers use relative changes for everything but color for this reason. This second color picker picks "
        "the color the influencer will restore channels to after passing over"
    ),
    "pan": "Pan value",
    "tilt": "Tilt value",
    "zoom": "Zoom value",
    "iris": "Iris value",
    "edge": "Edge value",
    "diffusion": "Diffusion value",
    "gobo": "Gobo ID value",
    "speed": "Gobo rotation speed value",
    "prism": "Prism value",

    # Audio Parameters
    "volume": "Stage object microphone's intensity/value",

    # Common Header
    "manual_fixture_selection": (
        "Instead of the group selector to the left, simply type in what you wish to control here. Just type in the "
        "channels you want or don't want in plain English"
    ),
    "solo": (
        "Mute all controllers but this one, and any others with solo also turned on. Clear all solos with the "
        "button on the Playback menu in the Timeline header"
    ),

    # Object Only
    "absolute": (
        "Enable absolute mode. In absolute mode, the object can animate the channels inside it while they are inside. " 
        "With this turned off, channels will only be changed by the influencer when the influencer comes and goes, not "
        "just because there is fcurve data. With this off, the influencer is in relative mode and can work on top of "
        "other effects"
    ),
    "strength": (
        "If you diminish the strength, it will act like a brush. If you keep this up all the way, it will act more like "
        "an object passing through the lights that resets them as it leaves"
    ),
    "sem": (
        '''If this is not zero, it  will behave like an "SEM" channel on ETC Eos. Use this to animate the translation '''
        '''of objects in Augment3D. This includes remote patching as well. To connect a 3D object in Augment3D to this '''
        '''channel, go to the right side tab in the A3D editor and drag the model over the SEM channel to link. Eos will '''
        '''not automatically put them on top of each other.'''
    )
}