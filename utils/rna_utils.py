# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import re


def register_properties(cls, properties, register=True):
    if register:
        for prop_name, prop_value in properties:
            setattr(cls, prop_name, prop_value)
    else:
        for prop_name, _ in reversed(properties):
            delattr(cls, prop_name)


def parse_channels(input_string, remove=False):
    '''
    Parses input to extract specified ranges, exclusions, additions, and filters for evens/odds.
    Examples:
    "I want 1-10 evens but I don't want 4-7 but keep 5" => [2, 6, 8, 10]
    "I want odds from 1-10" => [1, 3, 5, 7, 9]
    '''
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
        keywords_evens = {"even", "evens"}
        keywords_odds = {"odd", "odds"}

        channels = []
        exclusions = []
        additions = []
        i = 0
        exclude_mode = False
        add_mode = False
        filter_evens = False
        filter_odds = False
        
        while i < len(tokens):
            token = tokens[i]
            
            if token in versions_of_add:
                exclude_mode = False
                add_mode = False
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
                if filter_evens:
                    range_list = [n for n in range_list if n % 2 == 0]
                elif filter_odds:
                    range_list = [n for n in range_list if n % 2 != 0]
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
            elif token in keywords_evens:
                filter_evens = True
                filter_odds = False
            elif token in keywords_odds:
                filter_odds = True
                filter_evens = False
            i += 1
        
        # Apply exclusions
        channels = [ch for ch in channels if ch not in exclusions]
        
        # Apply additions
        channels.extend(additions)
        
        # Deduplicate, sort, and apply final filters
        channels = list(set(channels))
        channels.sort()
        if filter_evens:
            channels = [ch for ch in channels if ch % 2 == 0]
        elif filter_odds:
            channels = [ch for ch in channels if ch % 2 != 0]
        
        if not remove:
            return channels
        else:
            return channels, exclusions
    
    except Exception as e:
        print(f"An error has occurred within parse_channels: {e}")
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
    from ..cpv.find import Find

    controllers, mixers_and_motors = Find.find_controllers(context.scene)

    for controller in controllers:
        if hasattr(controller, "str_manual_fixture_selection"):
            controller.str_manual_fixture_selection = controller.str_manual_fixture_selection


def apply_patch(item, object):
    properties = [
        "pan_min", "pan_max", "tilt_min", "tilt_max", "zoom_min", "zoom_max", 
        "gobo_speed_min", "gobo_speed_max", "influence_is_on", "intensity_is_on", 
        "pan_tilt_is_on", "color_is_on", "diffusion_is_on", "strobe_is_on", 
        "zoom_is_on", "iris_is_on", "edge_is_on", "gobo_is_on", "prism_is_on", 
        "str_enable_strobe_argument", "str_disable_strobe_argument", 
        "str_enable_gobo_speed_argument", "str_disable_gobo_speed_argument", 
        "str_gobo_id_argument", "str_gobo_speed_value_argument", 
        "str_enable_prism_argument", "str_disable_prism_argument", "color_profile_enum"
    ]

    for prop in properties:
        setattr(object, prop, getattr(item, prop))