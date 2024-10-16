# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Scene
from bpy.props import StringProperty, IntProperty, BoolProperty, EnumProperty, FloatProperty

from ..assets.items import Items as AlvaItems


def register():
    from ..updaters.common import CommonUpdaters

    # Sequencer
    Scene.is_armed_livemap = BoolProperty(
        default=True, name="Livemap", description="Automatically jump to correct cue on playback from middle")
    Scene.is_armed_release = BoolProperty(
        default=False, name="Add Up Strip", description="Arm this to add a second strip when Z as in zebra key is released. This is to activate kick and snare with a single motion")
    Scene.add_strip_type_default = StringProperty(default='option_flash')
    Scene.strip_end_macros = BoolProperty(default=False, name="Strip End Macros", description="Create an extra macro option on the end frame of macro strips")

    # Event manager
    Scene.house_down_on_play = BoolProperty(default=False, description="Automatically dip the house lights during playback")
    Scene.house_prefix = StringProperty(default="/eos/newcmd", description="OSC Address/Prefix for the following 2 arguments")
    Scene.house_down_argument = StringProperty(default="500 at 1 Enter", description="Argument needed to lower house lights on playback")
    Scene.house_up_on_stop = BoolProperty(default=False, description="Automatically raise the house lights for safety when sequencer stops playing")
    Scene.house_up_argument = StringProperty(default="500 at 75 Enter", description="Argument needed to raise house lights on stop")
    Scene.sync_timecode = BoolProperty(name="Sync Timecode", default=True, description="Sync console's timecode clock with Sorcerer on play/stop/scrub based on top-most active sound strip's event list number")
    Scene.timecode_expected_lag = IntProperty(name="Expected Lag", default=5, min=0, max=100, description="Expected lag in frames. Sorcerer will start the console's clock late to compensate, using this number. WARNING: May lead to early strips not being fired since this skips the first frames on the console (and any corresponding events)")
    Scene.int_event_list = IntProperty(default=1, min=1, max=99999, name="Default Clock Number", description="Use this default clock number for timecode sync if no relevant sound strip exists")
    Scene.use_default_clock = BoolProperty(default=True, name="Always Sync", description="Use the default clock number if no relevant sound strip")
    Scene.lock_ip_settings = BoolProperty(default=False, name="Lock", description="Prevent accidental adjustments")
    Scene.ip_address_view_options = EnumProperty(
        items=AlvaItems.ip_address_view_options,
        name="Edit Options",
        description="Choose which network settings to adjust/view",
        default=1
    )
    Scene.alva_settings_view_enum = EnumProperty(
        items=AlvaItems.alva_settings_positions,
        name="ALVA Network Options",
        description="Choose which network settings to adjust/view",
        default=1
    )

    # Orb
    Scene.is_armed_turbo = BoolProperty(
        default=True, name="Orb Skips Shift+Update", description="Arm this to skip the safety step where build buttons save the console file prior to messing with stuff on the console")
    Scene.orb_chill_time = FloatProperty(default=.2, name="Wait Time", description="How long Orb waits for Eos to catch up when rendering qmeos frame by frame")
    Scene.orb_finish_snapshot = IntProperty(default=1, min=1, max=9999, description="Snapshot that Orb should set when done")
    Scene.orb_records_snapshot = BoolProperty(default=True, description="Orb will record current screen as its snapshot before doing anything to restore correctly when finished")
    
    Scene.orb_macros_start = IntProperty(default=88888, max=99998, min=1, name="Range Start", description="Orb will use this range to create the background macros it needs. If Orb runs out, it will ask for a larger range")
    Scene.orb_macros_end = IntProperty(default=99999, max=99999, min=1, name="Range End", description="Orb will use this range to create the background macros it needs. If Orb runs out, it will ask for a larger range")
    Scene.orb_cue_lists_start = IntProperty(default=888, max=998, min=1, name="Range Start", description="Orb will use this range to create the background cue lists it needs for animation strips. If Orb runs out, it will ask for a larger range")
    Scene.orb_cue_lists_end = IntProperty(default=999, max=999, min=1, name="Range End", description="Orb will use this range to create the background cue lists it needs for animation strips. If Orb runs out, it will ask for a larger range")
    Scene.orb_event_lists_start = IntProperty(default=888, max=998, min=1, name="Range Start", description="Orb will use this range to create the background event lists it needs. If Orb runs out, it will ask for a larger range")
    Scene.orb_event_lists_end = IntProperty(default=999, max=999, min=1, name="Range End", description="Orb will use this range to create the background event lists it needs. If Orb runs out, it will ask for a larger range")
    Scene.orb_presets_start = IntProperty(default=8888, max=9998, min=1, name="Range Start", description="Orb will use this range to create the background presets it needs. If Orb runs out, it will ask for a larger range")
    Scene.orb_presets_end = IntProperty(default=9999, max=9999, min=1, name="Range End", description="Orb will use this range to create the background presets it needs. If Orb runs out, it will ask for a larger range")

    Scene.add_underscores = BoolProperty(default=True, name="Add Underscores", description="Orb will try to add underscores to known keywords if they are missing")
    Scene.add_enter = BoolProperty(default=True, name="Add Enter", description="Orb will automatically add Enter to the end of each line if you forgot to. Turn this off if you want to leave the commandline open, for example if this macro works with other macros or the user to add multiple things to the commandline at once")

    # Lighting
    Scene.osc_receive_port = IntProperty(min=0, max=65535)

    # Audio
    Scene.audio_osc_address = StringProperty(default="", description="Type # for channel/fader/ouput number and $ for value, to be autofilled in background by .. Use this for realtime feedback during design, then bake/export to Qlab. Set up the mixer as if these are IEM's")
    Scene.audio_osc_argument = StringProperty(default="", description="Type # for channel/fader/ouput number and $ for value, to be autofilled in background by .. Use this for realtime feedback during design, then bake/export to Qlab. Set up the mixer as if these are IEM's")
    Scene.str_audio_ip_address = StringProperty(default="192.168.1.5", description="IP address of audio mixer. Leave blank to deactivate background process", update=CommonUpdaters.network_settings_updater)
    Scene.int_audio_port = IntProperty(default=53000, description="Port where audio mixer expects to recieve UDP messages", update=CommonUpdaters.network_settings_updater)

    # Video
    Scene.str_video_ip_address = StringProperty(default="192.168.1.2", description="IP address of video system. Leave blank to deactivate background process", update=CommonUpdaters.network_settings_updater)
    Scene.int_video_port = IntProperty(default=10000, description="Port where video system expects to recieve UDP messages", update=CommonUpdaters.network_settings_updater)


def unregister():
    del Scene.is_armed_livemap
    del Scene.is_armed_release
    
    del Scene.house_down_on_play
    del Scene.house_prefix
    del Scene.house_down_argument
    del Scene.house_up_on_stop
    del Scene.house_up_argument
    del Scene.sync_timecode
    del Scene.timecode_expected_lag
    
    del Scene.is_armed_turbo
    del Scene.orb_chill_time
    del Scene.orb_finish_snapshot
    del Scene.orb_records_snapshot
    
    del Scene.osc_receive_port
    
    del Scene.audio_osc_address
    del Scene.audio_osc_argument
    del Scene.str_audio_ip_address
    del Scene.int_audio_port