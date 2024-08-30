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
            'restrict_sync',
            'restrict_patch', 
            'restrict_house_lights', 
            'restrict_strip_media', 
            'restrict_sequencer', 
            'restrict_stage_objects', 
            'restrict_influencers', 
            'restrict_pan_tilts', 
            'restrict_brushes'
        ]

        true_restrictions = []

        for prop in restriction_properties:
            if getattr(scene.scene_props, prop, False):
                prop = prop.replace("restrict_", "")
                true_restrictions
                
        return true_restrictions