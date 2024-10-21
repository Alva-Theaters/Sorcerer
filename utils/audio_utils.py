# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
import math

from ..maintenance.logging import alva_log
from .osc import OSC

SPEAKER_SCALE_MULTIPLIER = 5  # This makes it feel more natural out of the box.
REMAP_MINIMUM = -59  # The minimum allowed sound level in Qlab.


def render_volume(speaker, sound_object, audio_cue):
    renderer = VolumeRenderer(speaker, sound_object, audio_cue)
    return renderer.render()


class VolumeRenderer:
    def __init__(self, speaker, sound_object, audio_cue):
        self.speaker = speaker
        self.sound_object = sound_object
        self.audio_cue = audio_cue

    def render(self):
        # Use matrix to allow the speaker field to move through a static scene on a path
        speaker_location = self.speaker.matrix_world.to_translation()

        # If sound object is congruently scaled, use bounding box center and normal SPEAKER_SCALE_MULTIPLIER
        # Otherwise, use the closest vertice instead and ignore the SPEAKER_SCALE_MULTIPLIER
        sound_object_world_location, adjusted_multiplier = self._adjust_by_congruency()

        distance = round((speaker_location - sound_object_world_location).length, 2)
        scale_factor = self._find_scale_factor(adjusted_multiplier)
        adjusted_distance = max(distance / scale_factor, 1e-6)  # Division reduces the impact of scale on attenuation

        # Use logarithmic-like falloff to smooth the volume transition
        volume = self._apply_logarithmic_falloff(adjusted_distance)

        alva_log('audio', f"distance: {distance}; scale_factor: {scale_factor}, adjusted_distance: {adjusted_distance}; rendered_volume: {volume}")

        # Remap Blender's 0-1 scale to Qlab's -59 - 0 decibel scale.
        remapped_volume = self._map_volume(volume)

        self._redraw_ui()

        # Use remapped volume for OSC/Qlab
        OSCInterface.publish_volume(self.speaker.int_speaker_number, self.audio_cue, remapped_volume)

        # Use original 0-1 volume for the dummy_volume Blender property for UI
        return volume

    def _adjust_by_congruency(self):
        scale_x, scale_y, scale_z = self.sound_object.scale
        if not round(scale_x, 2) == round(scale_y, 2) == round(scale_z, 2):
            closest_vertex = GeometryHelper.find_closest_vertex_to_speaker(self.speaker, self.sound_object)
            sound_object_world_location = closest_vertex
            adjusted_multiplier = 1
        else:
            sound_object_world_location = self.sound_object.matrix_world.to_translation()
            adjusted_multiplier = SPEAKER_SCALE_MULTIPLIER

        return sound_object_world_location, adjusted_multiplier

    def _find_scale_factor(self, adjusted_multiplier):
        speaker_avg_scale = sum(self.speaker.scale) / 3
        sound_object_avg_scale = sum(self.sound_object.scale) / 3
        return adjusted_multiplier * speaker_avg_scale * sound_object_avg_scale

    def _apply_logarithmic_falloff(self, adjusted_distance):
        volume = 1 - math.log10(adjusted_distance + 1)
        return max(0, min(round(volume, 2), 1))  # Clamp the volume between 0 and 1

    def _map_volume(self, volume):
        remapped_volume = volume * (0 - REMAP_MINIMUM) + REMAP_MINIMUM
        return max(REMAP_MINIMUM, min(remapped_volume, 0))

    def _redraw_ui(self):
        if bpy.context.screen:
            for area in bpy.context.screen.areas:
                if area.type == 'SEQUENCE_EDITOR':
                    area.tag_redraw()


class GeometryHelper:
    @staticmethod
    def find_closest_vertex_to_speaker(speaker, sound_object):
        '''Find the vertex closest to the speaker in world space'''
        object_mesh = sound_object.data
        closest_vertex = None
        min_distance = float('inf')

        for vertex in object_mesh.vertices:
            vertex_world_position = sound_object.matrix_world @ vertex.co
            distance_to_speaker = (speaker.location - vertex_world_position).length

            if distance_to_speaker < min_distance:
                min_distance = distance_to_speaker
                closest_vertex = vertex_world_position
        return closest_vertex


class OSCInterface:
    @staticmethod
    def publish_volume(channel, parameter, value):
        '''Publish volume via OSC'''
        address_template = "/cue/%/level/0/$"
        address = address_template.replace('$', str(channel)).replace('%', str(parameter))
        OSC.send_osc_audio(address, str(round(value, 2)))