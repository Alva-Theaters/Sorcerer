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
        '''
        Figure out how much of each sound strip should be in each speaker. 
        
        1. Use matrix to ensure constraints have a say since we want user to be able 
           to put both speaker rigs and audio objects on follow_paths.

        2. Use the closest vertice as sound_object center if scaling is not uniform since 
           we don't have a better way figure out how close a point is to an iregular mesh.

        3. Multiply sound_object scale by 5 for better experience if scaling is uniform since
           the default scale of one results in too small a fade radius. Fade radius meaning
           if the fade radius is too small, the volume goes down to 0 way too fast.

        4. Find total scale factor by considering both sound_object and speaker scales since
           we want user to change speaker sensitivity and object size intuitively, not 
           with numerical inputs. Allow them to just use the normal scale modal with S key.

        5. Calculate the volume by dividing distance and total scale factor.

        6. Apply logarithmic falloff for better experience. Without this, it was falling off
           in a funky way that didn't feel natural.

        7. Expand volume from 0-1 scale to scale needed for selected audio system (like Qlab).
           0 in Qlab means 0 decibels, so it doesn't do anything to it. Volume is 0 at -59 db 
           in Qlab. A mixer like the M32 will probably be similar.

        8. Send the expanded volume over the network with (channel, parameter, value) format.
           In the future, this may be incorporated directly into the CPVIA folder. For now,
           we're just mimicking its format.

        9. Return the original 0-1 volume for internal Blender needs, like the UI property. 
           We're using 0-1 in Blender because... maybe this should be switched to expanded db?
        '''
        speaker_location = self.speaker.matrix_world.to_translation()
        sound_object_location, adjustment_multiplier = self._adjust_by_congruency()
        distance = round((speaker_location - sound_object_location).length, 2)
        scale_factor = self._find_scale_factor(adjustment_multiplier)
        volume = max(distance / scale_factor, 1e-6)
        logarithmic_volume = self._apply_logarithmic_falloff(volume)
        alva_log('audio', f"distance: {distance}; scale_factor: {scale_factor}, logarithmic_volume: {logarithmic_volume}")
        expanded_volume = self._map_volume(logarithmic_volume)
        self._redraw_ui()
        OSCInterface.publish_volume(self.speaker.int_speaker_number, self.audio_cue, expanded_volume)
        return logarithmic_volume

    def _adjust_by_congruency(self):
        scale_x, scale_y, scale_z = self.sound_object.scale
        if round(scale_x, 2) == round(scale_y, 2) == round(scale_z, 2):
            sound_object_world_location = self.sound_object.matrix_world.to_translation()
            adjusted_multiplier = SPEAKER_SCALE_MULTIPLIER
        else:
            closest_vertex = GeometryHelper.find_closest_vertex_to_speaker(self.speaker, self.sound_object)
            sound_object_world_location = closest_vertex
            adjusted_multiplier = 1

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