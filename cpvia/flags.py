# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

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

    # Check for freeze mode
    if scene.in_frame_change:
        frame = round(context.scene.frame_current) # This is technically a float
        freeze_mode = parent.freezing_mode_enum
        if freeze_mode == 'option_seconds':
            if not scene.enable_seconds:
                alva_log("flags", "Stopping CPVIA per render freezing (seconds globally disabled).")
                return False
            if frame % 2 != 0:
                alva_log("flags", "Stopping CPVIA per render freezing (seconds).")
                return False
        elif freeze_mode == 'option_thirds':
            if not scene.enable_thirds:
                alva_log("flags", "Stopping CPVIA per render freezing (thirds globally disabled).")
                return False
            if frame % 3 != 0:
                alva_log("flags", "Stopping CPVIA per render freezing (thirds).")
                return False
        
    alva_log("flags", "CPVIA passes all flags, continuing.")
    return True


def test_flags(SENSITIVITY): # Return True for fail, False for pass
    return False