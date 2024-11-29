# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

from ..utils.cpv_utils import simplify_channels_list

# Alva Logging for this script is actually done from the event_manager.py script.


class Harmonizer:    
    @staticmethod
    def remove_duplicates(change_requests):
        seen = set()
        result = []
        for item in change_requests:
            if item[1:] not in seen:  # Check for uniqueness based on (c, p, v)
                seen.add(item[1:])  # Add only (c, p, v)
                result.append(item)  # Keep the whole tuple including generator
        return result
    
    @staticmethod
    def democracy(no_duplicates):
        '''Democratic mode where each request has equal influence'''
        request_dict = {}

        for generator, c, p, v in no_duplicates:
            key = (c, p)
            if key not in request_dict:
                request_dict[key] = {'count': 0, 'sum': 0, 'generator': generator}
            
            request_dict[key]['count'] += 1
            if isinstance(v, tuple):  # If color
                if not isinstance(request_dict[key]['sum'], tuple):
                    request_dict[key]['sum'] = (0,) * len(v)
                request_dict[key]['sum'] = tuple(s + val for s, val in zip(request_dict[key]['sum'], v))
            else:
                request_dict[key]['sum'] += v

        no_conflicts = []
        for key, value_dict in request_dict.items():
            c, p = key
            count = value_dict['count']
            sum_value = value_dict['sum']
            generator = value_dict['generator']

            # Calculate average value
            if isinstance(sum_value, tuple):  # If color
                v = tuple(s / count for s in sum_value)
            else:
                v = sum_value / count

            no_conflicts.append((generator, c, p, v))

        return no_conflicts
    
    @staticmethod
    def highest_takes_precedence(no_duplicates):
        '''Standard HTP (Highest Takes Precedence) protocol mode'''
        request_dict = {}

        for generator, c, p, v in no_duplicates:
            key = (c, p)  # Key based on channel and parameter only
            if key in request_dict:
                if v > request_dict[key][3]:  # Compare the value
                    request_dict[key] = (generator, c, p, v)
            else:
                request_dict[key] = (generator, c, p, v)

        no_conflicts = list(request_dict.values())
        
        return no_conflicts

    @staticmethod
    def simplify(no_conflicts):
        ''' Finds any instances where everything but channel number is the same 
            between multiple requests and combines them using "thru" for consecutive numbers.
        '''
        simplified_dict = {}

        for generator, c, p, v in no_conflicts:
            key = (p, v)
            if key in simplified_dict:
                simplified_dict[key][0].append(int(c))  # Store channels as integers for easier sorting
            else:
                simplified_dict[key] = (generator, [int(c)], p, v)

        simplified = []
        for (p, v), (channels, p, v) in simplified_dict.items():
            combined_channels_str = simplify_channels_list(channels)
            simplified.append((combined_channels_str, p, v))

        return simplified
    
    @staticmethod
    def simplify(no_conflicts):
        ''' Finds any instances where everything but channel number is the same 
            between multiple requests and combines them using "thru" and "+".
        '''
        simplified_dict = {}

        for generator, c, p, v in no_conflicts:
            key = (generator, p, v)  # Include generator in the key to keep controller and parent ID's unique
            if key in simplified_dict:
                simplified_dict[key][1].append(int(c))  # Store channels as integers for easier sorting
            else:
                simplified_dict[key] = (generator, [int(c)], p, v)

        simplified = []
        for (generator, p, v), (generator, channels, p, v) in simplified_dict.items():
            combined_channels_str = simplify_channels_list(channels)
            simplified.append((generator, combined_channels_str, p, v))

        return simplified
    

def test_harmonizer(SENSITIVITY): # Return True for fail, False for pass
    return False