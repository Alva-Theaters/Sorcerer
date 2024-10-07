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


# Alva Logging for this script is actually done from the event_manager.py script.

from ..utils.utils import Utils


class Harmonizer:    
    @staticmethod        
    def remove_duplicates(change_requests):
        request_dict = {}

        for c, p, v, i, a in change_requests:
            key = (c, p, v)
            if key in request_dict:
                request_dict[key][1] += i  # Collect the eaten request's votes
            else:
                request_dict[key] = [a, i]  # Store argument and influence

        return [(c, p, v, influence, argument) for (c, p, v), (argument, influence) in request_dict.items()]

    @staticmethod
    def democracy(no_duplicates):
        '''Democratic mode where influence (i) is the number of votes one gets when there is a conflict'''
        request_dict = {}

        for c, p, v, i, a in no_duplicates:
            key = (c, p)
            if key not in request_dict:
                request_dict[key] = {'total_influence': 0, 'weighted_sum': 0, 'arguments': a}
            request_dict[key]['total_influence'] += i
            request_dict[key]['weighted_sum'] += v * i

        no_conflicts = []
        for key, value_dict in request_dict.items():
            c, p = key
            total_influence = value_dict['total_influence']
            weighted_sum = value_dict['weighted_sum']
            a = value_dict['arguments']
            v = weighted_sum / total_influence  # Calculate weighted average value
            no_conflicts.append((c, p, v, total_influence, a))

        return no_conflicts

    @staticmethod
    def highest_takes_precedence(no_duplicates):
        '''Standard HTP protocol mode'''
        request_dict = {}

        for c, p, v, i, a in no_duplicates:
            key = (c, p)  # Key based on channel and parameter only
            if key in request_dict:
                if v > request_dict[key][2]:  # Compare the value
                    request_dict[key] = (c, p, v, i, a)
            else:
                request_dict[key] = (c, p, v, i, a)

        no_conflicts = list(request_dict.values())
        
        return no_conflicts

    @staticmethod
    def simplify(no_conflicts):
        ''' Finds any instances where everything but channel number is the same 
            between multiple requests and combines them using "thru" for consecutive numbers.
        '''
        simplified_dict = {}

        for c, p, v, i, a in no_conflicts:
            key = (p, v, a)
            if key in simplified_dict:
                simplified_dict[key][0].append(int(c))  # Store channels as integers for easier sorting
            else:
                simplified_dict[key] = ([int(c)], p, v, i, a)

        simplified = []
        for (p, v, a), (channels, p, v, i, a) in simplified_dict.items():
            combined_channels_str = Utils.simplify_channels_list(channels)
            simplified.append((combined_channels_str, p, v, i, a))

        return simplified
    

def test_harmonizer(SENSITIVITY): # Return True for fail, False for pass
    return False