# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
import math

from .osc import OSC


def render_volume(speaker, sound_object, audio_cue):
    '''Basically a crude form of the Dolby Atmos Renderer'''
    distance = (speaker.location - sound_object.location).length
    speaker_size = (speaker.scale[0] + speaker.scale[1] + speaker.scale[2]) / 3
    object_size = (sound_object.scale[0] + sound_object.scale[1] + sound_object.scale[2]) / 3
    adjusted_distance = max(distance - speaker_size - object_size, 0)
    final_distance = max(adjusted_distance, 1e-6)
    base_volume = 1.0
    volume = base_volume / final_distance
    volume = max(0, min(volume, 1))
    
    if bpy.context.screen:
        for area in bpy.context.screen.areas:
            if area.type == 'SEQUENCE_EDITOR':
                area.tag_redraw()
    
    publish_volume(speaker.int_speaker_number, audio_cue, volume)

    return volume


def publish_volume(channel, parameter, value):
    address_template = "/cue/%/level/0/$"
    address = address_template.replace('$', str(channel)).replace('%', str(parameter))
    OSC.send_osc_audio(address, str(round(value, 2)))