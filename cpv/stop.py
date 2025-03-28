# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

from ..maintenance.logging import alva_log


def check_flags(context, parent, property_name, controller_type):
    if not parent or not controller_type:
        alva_log("stop", "STOP: Stopping CPV per nonetypes.\n")
        return True

    if hasattr(parent, "mute") and parent.mute:
        alva_log("stop", "STOP: Stopping CPV per mute.\n")
        return True

    scene = context.scene.scene_props

    if scene.freeze_cpv:
        alva_log("stop", "STOP: Stopping CPV per freezing.\n")
        return True

    if not scene.enable_lighting:
        alva_log("stop", "STOP: Stopping CPV per enable_lighting.\n")
        return True
    
    # Check type-related flags
    type_checks = {
        'group': scene.enable_nodes,
        'mixer': scene.enable_nodes,
        'strip': scene.enable_strips,
    }

    if controller_type in type_checks:
        if not type_checks[controller_type]:
            alva_log("stop", "STOP: Stopping CPV per type_checks.\n")
            return True
        
    elif not scene.enable_objects:
        alva_log("stop", "STOP: Stopping CPV per type_checks.\n")
        return True
    
    if scene.has_solos and (scene.is_playing or scene.in_frame_change):
        if not parent.alva_solo:
            alva_log("stop", "STOP: Stopping CPV per solos.\n")
            return True
        
    if controller_type == 'mixer': # Bypass parameter toggles for mixers since they don't have them.
        alva_log("stop", "STOP: CPV passes all flags, continuing.\n")
        return False

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

    if property_name in param_flags and not param_flags[property_name]:
        alva_log("stop", "STOP: Stopping CPV per parameter toggles.\n")
        return True

    if scene.in_frame_change:
        frame = round(context.scene.frame_current) # This is technically a float
        freeze_mode = parent.freezing_mode_enum
        if freeze_mode == 'option_seconds':
            if not scene.enable_seconds:
                alva_log("stop", "STOP: Stopping CPV per render freezing (seconds globally disabled).\n")
                return True
            if frame % 2 != 0:
                alva_log("stop", "STOP: Stopping CPV per render freezing (seconds).\n")
                return True
        elif freeze_mode == 'option_thirds':
            if not scene.enable_thirds:
                alva_log("stop", "STOP: Stopping CPV per render freezing (thirds globally disabled).\n")
                return True
            if frame % 3 != 0:
                alva_log("stop", "STOP: Stopping CPV per render freezing (thirds).\n")
                return True
        
    alva_log("stop", "STOP: CPV passes all flags, continuing.\n")
    return False


def test_flags(SENSITIVITY): # Return True for fail, False for pass
    return False