# This file is part of Alva ..
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


def check_flags(context, parent, c, p, v, type):
    if not parent or not type or not p or not c or not v:
        print(f"Caught invalid CPVIA: {parent, type, c, p, v}")
        return False
    
    if hasattr(parent, "mute") and parent.mute:
        return False

    scene = context.scene.scene_props
    p = p[0]
    
    if not scene.lighting_enabled:
        return False
    
    # Check type-related flags
    type_checks = {
        'group': scene.nodes_enabled,
        'mixer': scene.nodes_enabled,
        'strip': scene.strips_enabled,
    }

    if type in type_checks:
        if not type_checks[type]:
            return False
    elif not scene.objects_enabled:
        return False

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
        return False
    
    if scene.has_solos and (scene.is_playing or scene.in_frame_change):
        if not parent.alva_solo:
            return False
        
    return True
