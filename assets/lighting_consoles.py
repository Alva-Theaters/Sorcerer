# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy import spy
from spy.types import LightingConsole # type: ignore
from spy.utils import as_register_class # type: ignore


class CPV_LC_eos(LightingConsole):
    as_idname = 'eos'
    as_label = "ETC Eos"
    as_description = "Eos-family console type"

    absolute = {
        1: "# at $ Enter",
        2: "# Shutter_Strobe at $ Enter",
        3: "# Pan at $ Enter",
        4: "# Tilt at $ Enter",
        5: "# Zoom at $ Enter",
        6: "# Iris at $ Enter",
        7: "# Edge at $ Enter",
        8: "# Diffusion at $ Enter",
        9: "# Gobo_Select at $ Enter",
        10: "# Gobo_Mode 191 Enter, # Gobo_Index/Speed at $ Enter",
        11: "# Beam_Fx Select $ Enter",
        12: "# Red at $1 Enter, # Green at $2 Enter, # Blue at $3 Enter",
        13: "# Cyan at $1 Enter, # Magenta at $2 Enter, # Yellow at $3 Enter",
        14: "# Red at $1 Enter, # Green at $2 Enter, # Blue at $3 Enter, # White at $4 Enter",
        15: "# Red at $1 Enter, # Green at $2 Enter, # Blue at $3 Enter, # Amber at $4 Enter",
        16: "# Red at $1 Enter, # Green at $2 Enter, # Blue at $3 Enter, # Lime at $4 Enter",
        17: "# Red at $1 Enter, # Green at $2 Enter, # Blue at $3 Enter, # Amber at $4 Enter, # White at $5 Enter",
        18: "# Red at $1 Enter, # Green at $2 Enter, # Blue at $3 Enter, # Amber at $4 Enter, # Mint at $5 Enter"
    }

    increase = {
        1: "# at + $ Enter",
        2: "# Pan at + $ Enter",
        3: "# Tilt at + $ Enter",
        4: "# Diffusion at + $ Enter",
        5: "# Shutter_Strobe at + $ Enter",
        6: "# Zoom at + $ Enter",
        7: "# Iris at + $ Enter",
        8: "# Edge at + $ Enter",
        9: "# Gobo_Select at + $ Enter",
        10: "# Gobo_Mode 191 Enter, # Gobo_Index/Speed at + $ Enter",
        11: "# Beam_Fx Select + $ Enter",
        12: "# Red at + $1 Enter, # Green at + $2 Enter, # Blue at + $3 Enter",
        13: "# Cyan at + $1 Enter, # Magenta at + $2 Enter, # Yellow at + $3 Enter",
        14: "# Red at + $1 Enter, # Green at + $2 Enter, # Blue at + $3 Enter, # White at + $4 Enter",
        15: "# Red at + $1 Enter, # Green at + $2 Enter, # Blue at + $3 Enter, # Amber at + $4 Enter",
        16: "# Red at + $1 Enter, # Green at + $2 Enter, # Blue at + $3 Enter, # Lime at + $4 Enter",
        17: "# Red at + $1 Enter, # Green at + $2 Enter, # Blue at + $3 Enter, # Amber at + $4 Enter, # White at + $5 Enter",
        18: "# Red at + $1 Enter, # Green at + $2 Enter, # Blue at + $3 Enter, # Amber at + $4 Enter, # Mint at + $5 Enter"
    }

    decrease = {
        1: "# at - $ Enter",
        2: "# Shutter_Strobe at - $ Enter",
        3: "# Pan at - $ Enter",
        4: "# Tilt at - $ Enter",
        5: "# Zoom at - $ Enter",
        6: "# Iris at - $ Enter",
        7: "# Edge at - $ Enter",
        8: "# Diffusion at - $ Enter",
        9: "# Gobo_Select at - $ Enter",
        10: "# Gobo_Mode 191 Enter, # Gobo_Index/Speed at - $ Enter",
        11: "# Beam_Fx Select - $ Enter",
        12: "# Red at - $1 Enter, # Green at - $2 Enter, # Blue at - $3 Enter",
        13: "# Cyan at - $1 Enter, # Magenta at - $2 Enter, # Yellow at - $3 Enter",
        14: "# Red at - $1 Enter, # Green at - $2 Enter, # Blue at - $3 Enter, # White at - $4 Enter",
        15: "# Red at - $1 Enter, # Green at - $2 Enter, # Blue at - $3 Enter, # Amber at - $4 Enter",
        16: "# Red at - $1 Enter, # Green at - $2 Enter, # Blue at - $3 Enter, # Lime at - $4 Enter",
        17: "# Red at - $1 Enter, # Green at - $2 Enter, # Blue at - $3 Enter, # Amber at - $4 Enter, # White at - $5 Enter",
        18: "# Red at - $1 Enter, # Green at - $2 Enter, # Blue at - $3 Enter, # Amber at - $4 Enter, # Mint at - $5 Enter"
    }


class CPV_LC_grandma_3(LightingConsole):
    as_idname = 'grandma3'
    as_label = "grandMA3"
    as_description = "grandMA3 family console type"

    absolute = {
        1: "# at $ Enter",
        2: "# Shutter_Strobe at $ Enter",
        3: "# Pan at $ Enter",
        4: "# Tilt at $ Enter",
        5: "# Zoom at $ Enter",
        6: "# Iris at $ Enter",
        7: "# Edge at $ Enter",
        8: "# Diffusion at $ Enter",
        9: "# Gobo_Select at $ Enter",
        10: "# Gobo_Mode 191 Enter, # Gobo_Index/Speed at $ Enter",
        11: "# Beam_Fx Select $ Enter",
        12: "# Red at $1 Enter, # Green at $2 Enter, # Blue at $3 Enter",
        13: "# Cyan at $1 Enter, # Magenta at $2 Enter, # Yellow at $3 Enter",
        14: "# Red at $1 Enter, # Green at $2 Enter, # Blue at $3 Enter, # White at $4 Enter",
        15: "# Red at $1 Enter, # Green at $2 Enter, # Blue at $3 Enter, # Amber at $4 Enter",
        16: "# Red at $1 Enter, # Green at $2 Enter, # Blue at $3 Enter, # Lime at $4 Enter",
        17: "# Red at $1 Enter, # Green at $2 Enter, # Blue at $3 Enter, # Amber at $4 Enter, # White at $5 Enter",
        18: "# Red at $1 Enter, # Green at $2 Enter, # Blue at $3 Enter, # Amber at $4 Enter, # Mint at $5 Enter"
    }

    increase = {
        1: "# at + $ Enter",
        2: "# Pan at + $ Enter",
        3: "# Tilt at + $ Enter",
        4: "# Diffusion at + $ Enter",
        5: "# Shutter_Strobe at + $ Enter",
        6: "# Zoom at + $ Enter",
        7: "# Iris at + $ Enter",
        8: "# Edge at + $ Enter",
        9: "# Gobo_Select at + $ Enter",
        10: "# Gobo_Mode 191 Enter, # Gobo_Index/Speed at + $ Enter",
        11: "# Beam_Fx Select + $ Enter",
        12: "# Red at + $1 Enter, # Green at + $2 Enter, # Blue at + $3 Enter",
        13: "# Cyan at + $1 Enter, # Magenta at + $2 Enter, # Yellow at + $3 Enter",
        14: "# Red at + $1 Enter, # Green at + $2 Enter, # Blue at + $3 Enter, # White at + $4 Enter",
        15: "# Red at + $1 Enter, # Green at + $2 Enter, # Blue at + $3 Enter, # Amber at + $4 Enter",
        16: "# Red at + $1 Enter, # Green at + $2 Enter, # Blue at + $3 Enter, # Lime at + $4 Enter",
        17: "# Red at + $1 Enter, # Green at + $2 Enter, # Blue at + $3 Enter, # Amber at + $4 Enter, # White at + $5 Enter",
        18: "# Red at + $1 Enter, # Green at + $2 Enter, # Blue at + $3 Enter, # Amber at + $4 Enter, # Mint at + $5 Enter"
    }

    decrease = {
        1: "# at - $ Enter",
        2: "# Shutter_Strobe at - $ Enter",
        3: "# Pan at - $ Enter",
        4: "# Tilt at - $ Enter",
        5: "# Zoom at - $ Enter",
        6: "# Iris at - $ Enter",
        7: "# Edge at - $ Enter",
        8: "# Diffusion at - $ Enter",
        9: "# Gobo_Select at - $ Enter",
        10: "# Gobo_Mode 191 Enter, # Gobo_Index/Speed at - $ Enter",
        11: "# Beam_Fx Select - $ Enter",
        12: "# Red at - $1 Enter, # Green at - $2 Enter, # Blue at - $3 Enter",
        13: "# Cyan at - $1 Enter, # Magenta at - $2 Enter, # Yellow at - $3 Enter",
        14: "# Red at - $1 Enter, # Green at - $2 Enter, # Blue at - $3 Enter, # White at - $4 Enter",
        15: "# Red at - $1 Enter, # Green at - $2 Enter, # Blue at - $3 Enter, # Amber at - $4 Enter",
        16: "# Red at - $1 Enter, # Green at - $2 Enter, # Blue at - $3 Enter, # Lime at - $4 Enter",
        17: "# Red at - $1 Enter, # Green at - $2 Enter, # Blue at - $3 Enter, # Amber at - $4 Enter, # White at - $5 Enter",
        18: "# Red at - $1 Enter, # Green at - $2 Enter, # Blue at - $3 Enter, # Amber at - $4 Enter, # Mint at - $5 Enter"
    }


consoles = [
    CPV_LC_eos,
    CPV_LC_grandma_3
]


def as_register():
    for cls in consoles:
        as_register_class(cls)