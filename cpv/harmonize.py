# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

from ..utils.cpv_utils import simplify_channels_list

ARGS_BEFORE_CPV = 2

# Alva Logging for this script is actually done from the event_manager.py script.


class Harmonizer:
    def remove_duplicates(change_requests):
        seen = set()
        result = []
        for item in change_requests:
            if item not in seen:
                seen.add(item[ARGS_BEFORE_CPV:])
                result.append(item)
        return result
    
    
    def democracy(no_duplicates):
        return Democracy(no_duplicates).execute()
    

    def highest_takes_precedence(no_duplicates):
        '''Standard HTP (Highest Takes Precedence) protocol mode'''
        request_dict = {}

        for generator, Parameter, c, p, v in no_duplicates:
            key = (c, p)  # Key based on channel and parameter only
            if key in request_dict:
                if v > request_dict[key][4]:  # Compare the value
                    request_dict[key] = (generator, Parameter, c, p, v)
            else:
                request_dict[key] = (generator, Parameter, c, p, v)

        no_conflicts = list(request_dict.values())
        
        return no_conflicts


    def simplify(no_conflicts):
        ''' Finds any instances where everything but channel number is the same 
            between multiple requests and combines them using "thru" and "+".
        '''
        simplified_dict = {}

        for generator, Parameter, c, p, v in no_conflicts:
            key = (generator, Parameter, p, v)  # Include generator and Parameter in the key
            if key in simplified_dict:
                simplified_dict[key][2].append(int(c))  # Store channels as integers for easier sorting
            else:
                simplified_dict[key] = (generator, Parameter, [int(c)], p, v)

        simplified = []
        for (generator, Parameter, p, v), (generator, Parameter, channels, p, v) in simplified_dict.items():
            combined_channels_str = simplify_channels_list(channels)
            simplified.append((generator, Parameter, combined_channels_str, p, v))

        return simplified
    

class Democracy:
    '''Democratic mode where each request has equal influence'''
    def __init__(self, no_duplicates):
        self.no_duplicates = no_duplicates
        self.request_dict = {}
        self.no_conflicts = []  


    def execute(self):
        '''Processes all requests and returns an averaged, conflict-free list of tuples.'''
        self._populate_request_dict()
        self._generate_no_conflicts_list()
        return self.no_conflicts

    def _populate_request_dict(self):
        '''Populates the request dictionary with summed values and counts for averaging.'''
        for generator, parameter, channel, parameter_name, value in self.no_duplicates:
            request_key = (channel, parameter_name)
            
            if self._is_new_request(request_key):
                self._initialize_request_entry(request_key, generator, parameter)
            
            self._increment_request_count(request_key)
            self._update_request_sum(request_key, value)

    def _is_new_request(self, request_key):
        '''Checks if the request key is not yet in the dictionary.'''
        return request_key not in self.request_dict
    
    def _initialize_request_entry(self, request_key, generator, parameter):
        '''Initializes a new entry in the request dictionary.'''
        self.request_dict[request_key] = {
            'count': 0,
            'sum': 0,
            'generator': generator,
            'parameter': parameter
        }

    def _increment_request_count(self, request_key):
        '''Increments the count of requests for the given key.'''
        self.request_dict[request_key]['count'] += 1

    def _update_request_sum(self, request_key, value):
        '''Updates the accumulated value (sum) for the given key.'''
        if self._is_color_value(value):
            self._ensure_color_sum_initialized(request_key, value)
            self._add_color_value_to_sum(request_key, value)
        else:
            self._add_numeric_value_to_sum(request_key, value)

    def _ensure_color_sum_initialized(self, request_key, value):
        '''Ensures the sum entry for colors is a tuple of zeros if not already initialized.'''
        if not isinstance(self.request_dict[request_key]['sum'], tuple):
            self.request_dict[request_key]['sum'] = (0,) * len(value)

    def _add_color_value_to_sum(self, request_key, value):
        '''Adds a color tuple to the current accumulated sum.'''
        current_sum = self.request_dict[request_key]['sum']
        self.request_dict[request_key]['sum'] = tuple(
            channel_sum + new_value for channel_sum, new_value in zip(current_sum, value)
        )

    def _add_numeric_value_to_sum(self, request_key, value):
        '''Adds a numeric value to the current accumulated sum.'''
        self.request_dict[request_key]['sum'] += value

    def _is_color_value(self, value):
        '''Checks if the provided value is a color (tuple).'''
        return isinstance(value, tuple)

    def _generate_no_conflicts_list(self):
        '''Creates the final list of averaged requests.'''
        for (channel, parameter_name), request_data in self.request_dict.items():
            averaged_value = self._calculate_average_value(
                request_data['sum'], request_data['count']
            )
            self.no_conflicts.append((
                request_data['generator'], 
                request_data['parameter'], 
                channel, 
                parameter_name, 
                averaged_value
            ))

    def _calculate_average_value(self, accumulated_value, count):
        '''Calculates the average value from the accumulated sum.'''
        if self._is_color_value(accumulated_value):
            return tuple(channel_sum / count for channel_sum in accumulated_value)
        return accumulated_value / count
    

def test_harmonizer(SENSITIVITY): # Return True for fail, False for pass
    return False