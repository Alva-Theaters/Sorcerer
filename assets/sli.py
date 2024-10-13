# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import inspect
import os


class SLI:
    def SLI_assert_unreachable(*args):
        """
        This is the preferred error-handling method. It reports traceback, line number, and tells user this is 
        a Sorcerer bug, not a Blender bug, and to report it to Alva Theaters, not Blender. Use on try/excepts 
        and on final else's that should never be reached. Only use try/except on the most downstream functions
        to avoid cascading exceptions and useless line number references. Inspired by the Blender version of this
        in the C++ code.
        """
        caller_frame = inspect.currentframe().f_back
        caller_file = caller_frame.f_code.co_filename
        caller_line = caller_frame.f_lineno
        
        caller_file = os.path.basename(caller_file)
        
        message = f"Error found at {caller_file}:{caller_line}\n" \
                    f"Code marked as unreachable has been executed. Please report bug to Alva Theaters, not Blender."
                    
        print(message)
        

    def SLI_find_restrictions(scene):
        if not scene.scene_props.school_mode_enabled:
            return []
        
        restriction_properties = [
            'restrict_network',
            'restrict_patch',
            'restrict_pan_tilt'
        ]

        true_restrictions = []

        for prop in restriction_properties:
            if getattr(scene.scene_props, prop, False):
                prop = prop.replace("restrict_", "")
                true_restrictions
                
        return true_restrictions