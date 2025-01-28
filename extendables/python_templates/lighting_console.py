# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy import spy #from spy.types import LightingConsole will not work here.
import time

'''If a new lighting console comes out with a robust OSC library, you can make it compatible with Sorcerer yourself with 
this. At this time (12/2024), the only known consoles with a sufficient OSC library are ETC Eos and grandMA, which are 
already supported internally. New custom consoles can be shared publically the same way normal Blender add-ons are.'''


class CPV_LC_custom_console(spy.types.LightingConsole):  # CPV is Sorcerer's fade engine, the Channel, Parameter, Value (CPV) system.
    as_idname = 'option_custom'
    as_label = "Custom Console"  # This will be selectable in OSC settings under Lighting.
    as_description = "Custom console type"

    osc_address = "/custom/newcmd"
    rounding_points = 0  # Can the console accept values like 20.32? Or does it need integers? Round here.

    absolute = {  # These are ETC Eos's templates, for reference.
        '''
        # will be replaced with channel number.
        $ will be replaced with value.
        '''

        "intensity": "# at $ Enter",
        "pan": "# Pan at $ Enter",
        "tilt": "# Tilt at $ Enter",
        "diffusion": "# Diffusion at $ Enter",
        "strobe": "# Shutter_Strobe at $ Enter",
        "zoom": "# Zoom at $ Enter",
        "iris": "# Iris at $ Enter",
        "edge": "# Edge at $ Enter",
        "gobo": "# Gobo_Select at $ Enter",
        "gobo_speed": "# Gobo_Mode 191 Enter, # Gobo_Index/Speed at $ Enter",
        "changer_speed": "# Changer_Speed at $ Enter",
        "prism": "# Beam_Fx Select $ Enter",
        "rgb": "# Red at $1 Enter, # Green at $2 Enter, # Blue at $3 Enter",
        "cmy": "# Cyan at $1 Enter, # Magenta at $2 Enter, # Yellow at $3 Enter",
        "rgbw": "# Red at $1 Enter, # Green at $2 Enter, # Blue at $3 Enter, # White at $4 Enter",
        "rgba": "# Red at $1 Enter, # Green at $2 Enter, # Blue at $3 Enter, # Amber at $4 Enter",
        "rgbl": "# Red at $1 Enter, # Green at $2 Enter, # Blue at $3 Enter, # Lime at $4 Enter",
        "rgbaw": "# Red at $1 Enter, # Green at $2 Enter, # Blue at $3 Enter, # Amber at $4 Enter, # White at $5 Enter",
        "rgbam": "# Red at $1 Enter, # Green at $2 Enter, # Blue at $3 Enter, # Amber at $4 Enter, # Mint at $5 Enter",
    }

    increase = {  # These relative templates are used for influencers, which need to overlap with on-console effects.
        "raise_intensity": "# at + $ Enter",
        "raise_pan": "# Pan at + $ Enter",
        "raise_tilt": "# Tilt at + $ Enter",
        "raise_diffusion": "# Diffusion at + $ Enter",
        "raise_strobe": "# Shutter_Strobe at + $ Enter",
        "raise_zoom": "# Zoom at + $ Enter",
        "raise_iris": "# Iris at + $ Enter",
        "raise_edge": "# Edge at + $ Enter",
        "raise_gobo": "# Gobo_Select at + $ Enter",
        "raise_gobo_speed": "# Gobo_Mode 191 Enter, # Gobo_Index/Speed at + $ Enter",
        "raise_changer_speed": "# Changer_Speed at + $ Enter",
        "raise_prism": "# Beam_Fx Select + $ Enter",
        "raise_rgb": "# Red at + $1 Enter, # Green at + $2 Enter, # Blue at + $3 Enter",
        "raise_cmy": "# Cyan at + $1 Enter, # Magenta at + $2 Enter, # Yellow at + $3 Enter",
        "raise_rgbw": "# Red at + $1 Enter, # Green at + $2 Enter, # Blue at + $3 Enter, # White at + $4 Enter",
        "raise_rgba": "# Red at + $1 Enter, # Green at + $2 Enter, # Blue at + $3 Enter, # Amber at + $4 Enter",
        "raise_rgbl": "# Red at + $1 Enter, # Green at + $2 Enter, # Blue at + $3 Enter, # Lime at + $4 Enter",
        "raise_rgbaw": "# Red at + $1 Enter, # Green at + $2 Enter, # Blue at + $3 Enter, # Amber at + $4 Enter, # White at + $5 Enter",
        "raise_rgbam": "# Red at + $1 Enter, # Green at + $2 Enter, # Blue at + $3 Enter, # Amber at + $4 Enter, # Mint at + $5 Enter",
    }

    decrease = {
        "lower_intensity": "# at - $ Enter",
        "lower_pan": "# Pan at - $ Enter",
        "lower_tilt": "# Tilt at - $ Enter",
        "lower_diffusion": "# Diffusion at - $ Enter",
        "lower_strobe": "# Shutter_Strobe at - $ Enter",
        "lower_zoom": "# Zoom at - $ Enter",
        "lower_iris": "# Iris at - $ Enter",
        "lower_edge": "# Edge at - $ Enter",
        "lower_gobo": "# Gobo_Select at - $ Enter",
        "lower_gobo_speed": "# Gobo_Mode 191 Enter, # Gobo_Index/Speed at - $ Enter",
        "lower_changer_speed": "# Changer_Speed at - $ Enter",
        "lower_prism": "# Beam_Fx Select - $ Enter",
        "lower_rgb": "# Red at - $1 Enter, # Green at - $2 Enter, # Blue at - $3 Enter",
        "lower_cmy": "# Cyan at - $1 Enter, # Magenta at - $2 Enter, # Yellow at - $3 Enter",
        "lower_rgbw": "# Red at - $1 Enter, # Green at - $2 Enter, # Blue at - $3 Enter, # White at - $4 Enter",
        "lower_rgba": "# Red at - $1 Enter, # Green at - $2 Enter, # Blue at - $3 Enter, # Amber at - $4 Enter",
        "lower_rgbl": "# Red at - $1 Enter, # Green at - $2 Enter, # Blue at - $3 Enter, # Lime at - $4 Enter",
        "lower_rgbaw": "# Red at - $1 Enter, # Green at - $2 Enter, # Blue at - $3 Enter, # Amber at - $4 Enter, # White at - $5 Enter",
        "lower_rgbam": "# Red at - $1 Enter, # Green at - $2 Enter, # Blue at - $3 Enter, # Amber at - $4 Enter, # Mint at - $5 Enter"
    }

    def __init__(self, scene):
        self.scene = scene

    def format_value(value):  
        # If you need special formatting of values, format them here. For example, ETC Eos needs a "1" formatted as "01".
        # Do NOT round here.
        return str(value)
    

    # Orb Actions. These will be called by the Orb operator for various automation routines. --------------------------------------------
    def key(self, key_strings, direction=None):
        if not isinstance(key_strings, list):
            key_strings = [key_strings]

        if direction is None:
            for key_string in key_strings:
                spy.press_lighting_key(key_string)
        elif direction is False:
            for key_string in key_strings:
                spy.lighting_key_up(key_string)
        elif direction:
            for key_string in key_strings:
                spy.lighting_key_down(key_string)


    def cmd(self, command_string):
        spy.send_osc_lighting(self.osc_address, command_string, tcp=True)


    def save_console_file(self):
        if self.scene.is_console_saving:
            self.key("shift", True)
            self.key("update")
            time.sleep(2)
            self.key("shift", False)


    def prepare_console_for_automation(self):
        yield self.record_snapshot(), "Saving your screen"
        yield self.save_console_file(), "Saving the console file"


    def restore_console_to_normal_following_automation(self):
        yield self.restore_snapshot(), "Restoring your screen"  


    def record_cue(self, cue_number, cue_duration):
        self.key("live")
        self.cmd(f"Cue {str(cue_number)} Time {cue_duration} Enter")


    def record_discrete_time(self, type_id, members_str, discrete_time):
        argument = f"{type_id} {members_str} Time {discrete_time.zfill(2)} Enter"
        self.cmd(argument)


    def record_one_line_macro(self, macro_number, macro_text):
        yield self.learn_macro(), "Initiating macro."  # These would be helper function 
        yield self.type_macro_number(macro_number), "Typing macro number."
        # And so on...


    # Helper methods. These method names are trivial. -----------------------------------------------------------------------------------
    def record_snapshot(self):
        pass  # Fill in with the logic for your console, if needed.


    def restore_snapshot(self):
        pass
    

    def learn_macro(self):
        pass


    def type_macro_number(self, macro_number):
        pass


def register():
    spy.utils.as_register_class(CPV_LC_custom_console)


def unregister():
    spy.utils.as_unregister_class(CPV_LC_custom_console)


if __name__ == '__main__':
    register()