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


import re


def register_properties(cls, properties, register=True):
    if register:
        for prop_name, prop_value in properties:
            setattr(cls, prop_name, prop_value)
    else:
        for prop_name, _ in reversed(properties):
            delattr(cls, prop_name)


def parse_channels(input_string, remove=False):
    try:
        input_string = input_string.replace("do not want", "not").replace("don't want", "not").replace(".", "").replace("!", "").replace("?", "")
        input_string = input_string.lower()

        formatted_input = re.sub(r'[()]', '', input_string)
        
        # Ensure consistent spacing around the dash for cases like '1-10', '1 -10'
        formatted_input = re.sub(r'(\d)\s*-\s*(\d)', r'\1 - \2', formatted_input)
        
        # Split by commas and whitespace
        tokens = re.split(r'[,\s]+', formatted_input)
        
        versions_of_through = (
            "through", "thru", "-", "tthru", "throu", "--", "por", "thr", 
            "to", "until", "up to", "till", "over"
        )
        versions_of_not = (
            "not", "minus", "except", "excluding", "casting", "aside", 
            "without", "leave", "omit", "remove", "other", "than", "delete",
            "deleting", "take"
        )
        versions_of_add = (
            "add", "adding", "including", "include", 
            "save", "preserve", "plus", "with", "addition", "+", "want",
            "do"
        )

        channels = []
        exclusions = []
        additions = []
        i = 0
        exclude_mode = False
        add_mode = False
        
        while i < len(tokens):
            token = tokens[i]
            
            if token in versions_of_add:
                exclude_mode = False
            elif token in ["keep", "keeping"]:
                exclude_mode = False
                add_mode = True
            elif token in versions_of_not:
                exclude_mode = True
                add_mode = False
            elif token in versions_of_through and i > 0 and i < len(tokens) - 1:
                start = int(tokens[i-1])
                end = int(tokens[i+1])
                step = 1 if start < end else -1
                range_list = list(range(start, end + step, step))
                if exclude_mode:
                    exclusions.extend(range_list)
                elif add_mode:
                    additions.extend(range_list)
                else:
                    channels.extend(range_list)
                i += 1  # Skip the end token of the range
            elif token.isdigit():
                num = int(token)
                if exclude_mode:
                    exclusions.append(num)
                elif add_mode:
                    additions.append(num)
                else:
                    channels.append(num)
            i += 1
        
        channels = [ch for ch in channels if ch not in exclusions]
        channels.extend(additions)
        
        channels = list(set(channels))
        channels.sort()
        
        if not remove:
            return channels
        else:
            return channels, exclusions
    
    except Exception as e:
        print(f"An error has occured within parse_channels: {e}")
        return None


def parse_mixer_channels(input_string):
    try:
        groups = re.findall(r'\(([^)]+)\)', input_string)
        if not groups:
            groups = [input_string]
            
        all_channels = []

        for group in groups:
            channels = parse_channels(group)
            all_channels.append(tuple(channels))

        return all_channels
    except Exception as e:
        print(f"An error has occured within parse_channels: {e}")
        return None


def update_all_controller_channel_lists(context):
    from ..cpvia.find import Find

    controllers, mixers_and_motors = Find.find_controllers(context.scene)

    for controller in controllers:
        if hasattr(controller, "str_manual_fixture_selection"):
            controller.str_manual_fixture_selection = controller.str_manual_fixture_selection