# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

from ..utils.cpvia_utils import simplify_channels_list

# Alva Logging for this script is actually done from the event_manager.py script.


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
            if isinstance(v, tuple): # If color
                request_dict[key]['weighted_sum'] = tuple(
                    request_dict[key]['weighted_sum'][j] + v[j] * i if isinstance(request_dict[key]['weighted_sum'], tuple)
                    else v[j] * i for j in range(len(v))
                )
            else:
                request_dict[key]['weighted_sum'] += v * i

        no_conflicts = []
        for key, value_dict in request_dict.items():
            c, p = key
            total_influence = value_dict['total_influence']
            weighted_sum = value_dict['weighted_sum']
            a = value_dict['arguments']

            # Calculate weighted average value
            if isinstance(weighted_sum, tuple): # If color
                v = tuple(ws / total_influence for ws in weighted_sum)
            else:
                v = weighted_sum / total_influence

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
            combined_channels_str = simplify_channels_list(channels)
            simplified.append((combined_channels_str, p, v, i, a))

        return simplified
    

def test_harmonizer(SENSITIVITY): # Return True for fail, False for pass
    return False