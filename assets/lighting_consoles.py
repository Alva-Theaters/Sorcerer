# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

'''
To make your own custom lighting console:

    1. Copy/paste the code below directly into Blender's text editor.
    2. Modify it as needed.
    3. Run it.
    4. Select your new lighting console in Alva Sorcerer preferences under Network.

The lighting consoles below are built into Sorcerer. Similar to Blender's bpy, Sorcerer's spy is
utilized both by the internal source code (as seen here) and by end-users extending the application.
'''

from bpy import spy
import time

from ..utils.osc import OSC


class CPV_LC_eos(spy.types.LightingConsole):
    as_idname = 'option_eos'
    as_label = "ETC Eos"
    as_description = "Eos-family console type"

    osc_address = "/eos/newcmd"
    rounding_points = 0

    absolute = {
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

    increase = {
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
        '''We have to do this stuff because Eos interprets "1" as 10, "2" as 20, etc.'''
        if -10 < value < 10:
            return f"{'-0' if value < 0 else '0'}{abs(value)}"
        return str(value)
    

    def key(self, key_string, direction=None):
        if direction is None:
            OSC.press_lighting_key(key_string)
        elif direction is False:
            OSC.lighting_key_up(key_string)
        elif direction:
            OSC.lighting_key_down(key_string)


    def cmd(self, command_string):
        OSC.send_osc_lighting(self.osc_address, command_string, tcp=True)


    def record_snapshot(self):
        snapshot = str(self.scene.orb_finish_snapshot)
        self.cmd(f"Record Snapshot {snapshot} Enter Enter")


    def restore_snapshot(self):
        snapshot = str(self.scene.orb_finish_snapshot)
        self.cmd(f"Snapshot {snapshot} Enter")


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


    def record_discreet_time(self, Orb, slowed_prop_name):
        discrete_time = str(getattr(Orb.active_item, slowed_prop_name))

        if discrete_time == "0.0":
            return
        
        param = slowed_prop_name.replace("_slow", "")

        # Importing here for dependency reasons
        from ..utils.rna_utils import parse_channels
        from ..utils.cpv_utils import simplify_channels_list

        groups = parse_channels(getattr(Orb.scene, f"{param}_groups"))
        channels = parse_channels(getattr(Orb.scene, f"{param}_channels"))
        submasters = parse_channels(getattr(Orb.scene, f"{param}_submasters"))

        if groups:
            groups_str = simplify_channels_list(groups)
            argument = f"Group {groups_str} Time {discrete_time.zfill(2)} Enter"
            self.cmd(argument)

        if channels:
            channels_str = simplify_channels_list(channels)
            argument = f"Chan {channels_str} Time {discrete_time.zfill(2)} Enter"
            self.cmd(argument)

        if submasters:
            submasters_str = simplify_channels_list(submasters)
            argument = f"Sub {submasters_str} Time {discrete_time.zfill(2)} Enter"
            self.cmd(argument)

    def update_cue(self):
        self.key("update")
        self.key("enter")


class CPV_LC_grandma_3(spy.types.LightingConsole):
    as_idname = 'grandma3'
    as_label = "grandMA3"
    as_description = "grandMA3 family console type"

    osc_address = "/cmd"
    rounding_points = 2

    absolute = {
        "intensity": "Fixture # at $",
        "pan": "Fixture #; Attribute Pan at $",
        "tilt": "Fixture #; Attribute Tilt at $",
        "diffusion": "Fixture #; Attribute Frost1 at $",
        "zoom": "Fixture #; Attribute Zoom at $",
        "iris": "Fixture #; Attribute Iris at $",
        "edge": "Fixture #; Attribute Focus1 at $",
        "rgb": "Fixture #; Attribute ColorRGB_R at $1; Attribute ColorRGB_G at $2; Attribute ColorRGB_B at $3",
        "cmy": "Fixture #; Attribute ColorRGB_C at $1; Attribute ColorRGB_M at $2; Attribute ColorRGB_Y at $3",
        "rgbw": "Fixture #; Attribute ColorRGB_R at $1; Attribute ColorRGB_G at $2; Attribute ColorRGB_B at $3; Attribute ColorRGB_W at $4",
        "rgba": "Fixture #; Attribute ColorRGB_R at $1; Attribute ColorRGB_G at $2; Attribute ColorRGB_B at $3; Attribute ColorRGB_A at $4",
        "rgbl": "Fixture #; Attribute ColorRGB_R at $1; Attribute ColorRGB_G at $2; Attribute ColorRGB_B at $3; Attribute ColorRGB_L at $4",
        "rgbaw": "Fixture #; Attribute ColorRGB_R at $1; Attribute ColorRGB_G at $2; Attribute ColorRGB_B at $3; Attribute ColorRGB_A at $4; Attribute ColorRGB_W at $5",
        "rgbam": "Fixture #; Attribute ColorRGB_R at $1; Attribute ColorRGB_G at $2; Attribute ColorRGB_B at $3; Attribute ColorRGB_A at $4; Attribute ColorRGB_M at $5",
    }

    increase = {
        "raise_intensity": "Fixture # at + $",
        "raise_pan": "Fixture #; Attribute Pan at + $",
        "raise_tilt": "Fixture #; Attribute Tilt at + $",
        "raise_diffusion": "Fixture #; Attribute Frost1 at + $",
        "raise_zoom": "Fixture #; Attribute Zoom at + $",
        "raise_iris": "Fixture #; Attribute Iris at + $",
        "raise_edge": "Fixture #; Attribute Focus1 at + $",
        "raise_rgb": "Fixture #; Attribute ColorRGB_R at + $1; Attribute ColorRGB_G at + $2; Attribute ColorRGB_B at + $3",
        "raise_cmy": "Fixture #; Attribute ColorRGB_C at + $1; Attribute ColorRGB_M at + $2; Attribute ColorRGB_Y at + $3",
        "raise_rgbw": "Fixture #; Attribute ColorRGB_R at + $1; Attribute ColorRGB_G at + $2; Attribute ColorRGB_B at + $3; Attribute ColorRGB_W at + $4",
        "raise_rgba": "Fixture #; Attribute ColorRGB_R at + $1; Attribute ColorRGB_G at + $2; Attribute ColorRGB_B at + $3; Attribute ColorRGB_A at + $4",
        "raise_rgbl": "Fixture #; Attribute ColorRGB_R at + $1; Attribute ColorRGB_G at + $2; Attribute ColorRGB_B at + $3; Attribute ColorRGB_L at + $4",
        "raise_rgbaw": "Fixture #; Attribute ColorRGB_R at + $1; Attribute ColorRGB_G at + $2; Attribute ColorRGB_B at + $3; Attribute ColorRGB_A at + $4; Attribute ColorRGB_W at + $5",
        "raise_rgbam": "Fixture #; Attribute ColorRGB_R at + $1; Attribute ColorRGB_G at + $2; Attribute ColorRGB_B at + $3; Attribute ColorRGB_A at + $4; Attribute ColorRGB_M at + $5",
    }
    
    decrease = {
        "lower_intensity": "Fixture # at - $",
        "lower_pan": "Fixture #; Attribute Pan at - $",
        "lower_tilt": "Fixture #; Attribute Tilt at - $",
        "lower_diffusion": "Fixture #; Attribute Frost1 at - $",
        "lower_zoom": "Fixture #; Attribute Zoom at - $",
        "lower_iris": "Fixture #; Attribute Iris at - $",
        "lower_edge": "Fixture #; Attribute Focus1 at - $",
        "lower_rgb": "Fixture #; Attribute ColorRGB_R at - $1; Attribute ColorRGB_G at - $2; Attribute ColorRGB_B at - $3",
        "lower_cmy": "Fixture #; Attribute ColorRGB_C at - $1; Attribute ColorRGB_M at - $2; Attribute ColorRGB_Y at - $3",
        "lower_rgbw": "Fixture #; Attribute ColorRGB_R at - $1; Attribute ColorRGB_G at - $2; Attribute ColorRGB_B at - $3; Attribute ColorRGB_W at - $4",
        "lower_rgba": "Fixture #; Attribute ColorRGB_R at - $1; Attribute ColorRGB_G at - $2; Attribute ColorRGB_B at - $3; Attribute ColorRGB_A at - $4",
        "lower_rgbl": "Fixture #; Attribute ColorRGB_R at - $1; Attribute ColorRGB_G at - $2; Attribute ColorRGB_B at - $3; Attribute ColorRGB_L at - $4",
        "lower_rgbaw": "Fixture #; Attribute ColorRGB_R at - $1; Attribute ColorRGB_G at - $2; Attribute ColorRGB_B at - $3; Attribute ColorRGB_A at - $4; Attribute ColorRGB_W at - $5",
        "lower_rgbam": "Fixture #; Attribute ColorRGB_R at - $1; Attribute ColorRGB_G at - $2; Attribute ColorRGB_B at - $3; Attribute ColorRGB_A at - $4; Attribute ColorRGB_M at - $5",
    }


consoles = [
    CPV_LC_eos,
    CPV_LC_grandma_3
]


def register():
    for cls in consoles:
        spy.utils.as_register_class(cls)


def unregister():
    for cls in reversed(consoles):
        spy.utils.as_unregister_class(cls)