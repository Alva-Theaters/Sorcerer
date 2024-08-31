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


from ..cpvia.find import Find # type: ignore
from ..assets.sli import SLI # type: ignore


class Mapping:
    def map_value(self, parent, chan, p, unmapped_value, type):
        min_val, max_val = self.find_my_min_max(parent, chan, type, p)
        if p in ["strobe", "pan", "tilt", "zoom", "gobo_speed"]:
            if min_val <= 0 and max_val >= 0:
                # Normalizing around zero
                if unmapped_value == 0:
                    mapped_value = 0
                elif unmapped_value > 0:
                    normalized_value = unmapped_value / 100
                    mapped_value = normalized_value * max_val
                else:
                    normalized_value = unmapped_value / 100
                    mapped_value = normalized_value * abs(min_val)
            else:
                # Map the slider value from -100 to 100 to the min_val to max_val range
                if unmapped_value >= 0:
                    normalized_value = unmapped_value / 100
                    mapped_value = normalized_value * (max_val - min_val) + min_val
                else:
                    normalized_value = (unmapped_value + 100) / 200
                    mapped_value = (normalized_value * (max_val - min_val)) + min_val
            return mapped_value
        else: SLI.SLI_assert_unreachable()


    def find_my_min_max(self, parent, chan, type, p):  
        """
        Finds the relevant min/max values for a specified parameter p
        
        Arguments:
            parent: The parent object/node/strip
            p: The property type, should be pan, tilt, zoom, gobo_speed, or pan_tilt only
            
        Returns:
            min_value, max_value: 2 integers
        """
        try:
            min_property = f"{p}_min"
            max_property = f"{p}_max"
            finders = Find()
            min_value = finders.find_my_patch(parent, chan, type, min_property)
            max_value = finders.find_my_patch(parent, chan, type, max_property)
            return min_value, max_value
        except AttributeError as e:
            print(f"Error in find_my_min_max: {e}")
            return None, None
        
def test_mapping(SENSITIVITY): # Return True for fail, False for pass
    return False