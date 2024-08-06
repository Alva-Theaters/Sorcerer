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


from bpy.types import Scene
from bpy.props import StringProperty, IntProperty, BoolProperty


def register():
    # Sequencer
    Scene.is_armed_livemap = BoolProperty(
        default=True, name="Arm Livemap", description="Arm livemap to automatically jump to correct cue on playback from middle")
    Scene.is_armed_release = BoolProperty(
        default=False, name="Arm Add Extra Strip on Release of O", description="Arm this to add a second strip when O as in Oscar key is released. This is to activate kick and snare with a single finger")
    
    # Event manager
    Scene.house_down_on_play = BoolProperty(default=False, description="Automatically dip the house lights during playback")
    Scene.house_prefix = StringProperty(default="/eos/newcmd", description="OSC Address/Prefix for the following 2 arguments")
    Scene.house_down_argument = StringProperty(default="500 at 1 Enter", description="Argument needed to lower house lights on playback")
    Scene.house_up_on_stop = BoolProperty(default=False, description="Automatically raise the house lights for safety when sequencer stops playing")
    Scene.house_up_argument = StringProperty(default="500 at 75 Enter", description="Argument needed to raise house lights on stop")
    Scene.sync_timecode = BoolProperty(default=True, description="Sync console's timecode clock with Sorcerer on play/stop/scrub based on top-most active sound strip's event list number")
    Scene.timecode_expected_lag = IntProperty(default=0, min=0, max=100, description="Expected lag in frames")

    # Orb
    Scene.is_armed_turbo = BoolProperty(
        default=False, name="Orb Skips Shift+Update", description="Arm this to skip the safety step where build buttons save the console file prior to messing with stuff on the console")
    Scene.orb_finish_snapshot = IntProperty(default=1, min=1, max=9999, description="Snapshot that Orb should set when done")
    Scene.orb_records_snapshot = BoolProperty(default=False, description="Orb will record current screen as its snapshot before doing anything to restore correctly when finished.")

    # Lighting
    Scene.osc_receive_port = IntProperty(min=0, max=65535)  

    # Audio
    Scene.audio_osc_address = StringProperty(default="", description="Type # for channel/fader/ouput number and $ for value, to be autofilled in background by .. Use this for realtime feedback during design, then bake/export to Qlab. Set up the mixer as if these are IEM's")
    Scene.audio_osc_argument = StringProperty(default="", description="Type # for channel/fader/ouput number and $ for value, to be autofilled in background by .. Use this for realtime feedback during design, then bake/export to Qlab. Set up the mixer as if these are IEM's")
    Scene.str_audio_ip_address = StringProperty(default="", description="IP address of audio mixer. Leave blank to deactivate background process")
    Scene.int_audio_port = IntProperty(default=10023, description="Port where audio mixer expects to recieve UDP messages")


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
    del Scene.orb_finish_snapshot
    del Scene.orb_records_snapshot
    
    del Scene.osc_receive_port
    
    del Scene.audio_osc_address
    del Scene.audio_osc_argument
    del Scene.str_audio_ip_address
    del Scene.int_audio_port
