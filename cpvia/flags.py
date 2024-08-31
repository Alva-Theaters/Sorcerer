# This file is part of Alva Sorcerer
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


from ..maintenance.logging import alva_log


def check_flags(context, parent, c, p, v, type):
    if not parent or not type or not p or not c or not v:
        alva_log("flags", "Stopping CPVIA per nonetypes.")
        return False

    if hasattr(parent, "mute") and parent.mute:
        alva_log("flags", "Stopping CPVIA per mute.")
        return False

    scene = context.scene.scene_props
    p = p[0]

    if scene.freeze_cpvia:
        alva_log("flags", "Stopping CPVIA per freezing.")
        return False

    if not scene.enable_lighting:
        alva_log("flags", "Stopping CPVIA per enable_lighting.")
        return False
    
    # Check type-related flags
    type_checks = {
        'group': scene.enable_nodes,
        'mixer': scene.enable_nodes,
        'strip': scene.enable_strips,
    }

    if type in type_checks:
        if not type_checks[type]:
            alva_log("flags", "Stopping CPVIA per type_checks.")
            return False
    elif not scene.enable_objects:
        alva_log("flags", "Stopping CPVIA per type_checks.")
        return False
    
    if scene.has_solos and (scene.is_playing or scene.in_frame_change):
        if not parent.alva_solo:
            alva_log("flags", "Stopping CPVIA per solos.")
            return False
        
    if type == 'mixer': # Bypass parameter toggles for mixers since they don't have them.
        alva_log("flags", "CPVIA passes all flags, continuing.")
        return True

    # Check parameter-related flags
    param_flags = {
        'strobe': parent.strobe_is_on,
        'color': parent.color_is_on,
        'pan': parent.pan_tilt_is_on,
        'tilt': parent.pan_tilt_is_on,
        'zoom': parent.zoom_is_on,
        'iris': parent.iris_is_on,
        'edge': parent.edge_is_on,
        'diffusion': parent.diffusion_is_on,
        'gobo_id': parent.gobo_is_on,
        'gobo_speed': parent.gobo_is_on,
        'prism': parent.gobo_is_on,
    }

    if p in param_flags and not param_flags[p]:
        alva_log("flags", "Stopping CPVIA per parameter toggles.")
        return False
        
    alva_log("flags", "CPVIA passes all flags, continuing.")
    return True


def test_flags(SENSITIVITY): # Return True for fail, False for pass
    return False