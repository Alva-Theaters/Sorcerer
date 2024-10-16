# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
import math

from ..maintenance.logging import alva_log
from .osc import OSC

SPEAKER_SCALE_MULTIPLIER = 5
REMAP_MINIMUM = -59


def render_volume(speaker, sound_object, audio_cue):
    '''Basically a crude form of the Dolby Atmos Renderer'''
    sound_object_world_location = sound_object.matrix_world.to_translation()
    distance = round((speaker.location - sound_object_world_location).length, 2)

    scale_factor = SPEAKER_SCALE_MULTIPLIER * ((speaker.scale[0] + speaker.scale[1] + speaker.scale[2]) / 3) * \
                   ((sound_object.scale[0] + sound_object.scale[1] + sound_object.scale[2]) / 3)

    adjusted_distance = max(distance / scale_factor, 1e-6)  # Division reduces the impact of scale on attenuation

    # Use logarithmic-like falloff to smooth the volume transition
    volume = 1 - math.log10(adjusted_distance + 1)
    volume = max(0, min(volume, 1))  # Clamp the volume between 0 and 1
    volume = round(volume, 2)

    alva_log('audio', f"distance: {distance}; scale_factor: {scale_factor}, adjusted_distance: {adjusted_distance}; rendered_volume: {volume}")

    # Remap the volume to the -50 to 0 range
    remapped_volume = volume * (0 - REMAP_MINIMUM) + REMAP_MINIMUM
    remapped_volume = max(REMAP_MINIMUM, min(remapped_volume, 0))

    if bpy.context.screen:
        for area in bpy.context.screen.areas:
            if area.type == 'SEQUENCE_EDITOR':
                area.tag_redraw()

    publish_volume(speaker.int_speaker_number, audio_cue, remapped_volume)

    return volume



def publish_volume(channel, parameter, value):
    address_template = "/cue/%/level/0/$"
    address = address_template.replace('$', str(channel)).replace('%', str(parameter))
    OSC.send_osc_audio(address, str(round(value, 2)))