# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
import re
from bpy.types import Scene, Object
    
from ..assets.dictionaries import Dictionaries 

DEFAULT_EXECUTOR_INDEX = 1


def find_addresses(starting_universe, starting_address, channel_mode, total_lights):
    address_list = []
    universe = starting_universe
    address = starting_address

    for i in range(total_lights):
        if address + channel_mode - 1 > 512:
            universe += 1
            address = 1
        address_list.append((universe, address))
        address += channel_mode
    return address_list


#-------------------------------------------------------------------------------------------------------------------------------------------
'''Text editor macros'''
#-------------------------------------------------------------------------------------------------------------------------------------------
def tokenize_macro_line(input_line):
    scene = bpy.context.scene
    if scene.add_underscores:
        try:
            input_line = add_underscores_to_keywords(input_line)
        except Exception as e:
            print(f"An error occurred while adding underscores to keywords: {e}")
            return None

    try:
        tokens = tokenize(input_line)
    except Exception as e:
        print(f"An error occurred while tokenizing macro string: {e}")
        return None

    if tokens is None:
        return None

    osc_keys = Dictionaries.osc_keys # Already lowercase
    results = []

    for token in tokens:
        token_lower = token.lower()  # Convert token to lowercase for comparison

        if token == '/':
            token = '\\'

        if token_lower in osc_keys:
            key_address = f"/eos/key/{token}"
            results.append((key_address, "1"))
            results.append((key_address, "0"))
        else:
            results.append(("/eos/newcmd", str(token)))
            
    # Check if the last token is "enter" and add it if it's not
    if tokens[-1].lower() != "enter" and scene.add_enter:
        results.append(("/eos/key/Enter", "1"))
        results.append(("/eos/key/Enter", "0"))
            
    return results


def add_underscores_to_keywords(input_string):
    osc_keys = Dictionaries.osc_keys
    macro_buttons = Dictionaries.macro_buttons

    keywords_list = set(osc_keys + macro_buttons)
    
    for keyword in keywords_list:
        if not keyword:
            continue

        if "\\" in keyword:
            continue

        keyword_no_underscore = keyword.replace("_", " ")
        
        try:
            pattern = re.compile(re.escape(keyword_no_underscore), re.IGNORECASE)
            input_string = pattern.sub(keyword, input_string)
        except re.error as e:
            print(f"Error with keyword '{keyword_no_underscore}': {e}")
    
    return input_string


def tokenize(input_string):
    replacements = ["{", "}", "[", "]", "<", ">"]
    clean_string = input_string
    for item in replacements:
        clean_string = clean_string.replace(item, "")
    
    tokens = re.findall(r'\d|[^\d\s]+', clean_string)
    return tokens


#-------------------------------------------------------------------------------------------------------------------------------------------
'''Find executor'''
#-------------------------------------------------------------------------------------------------------------------------------------------
def find_executor(scene: Scene, object: Object, executor_type: str) -> int:
    try:
        existing_prop = getattr(object, f"int_{executor_type}")
    except:
        print("An error occured in find_executor because of an invalid object or incorrect registration.")

    if existing_prop != 0 and (object.name == object.str_parent_name or isinstance(object, bpy.types.Scene)): # Middle check filters duplicates
        if isinstance(object, bpy.types.Scene) and executor_type not in ["start_macro", "end_macro"]:
            pass # We need to find a new one for Scene's event list and cue list
        else:
            return existing_prop # Don't find a new one, use the old one

    new_index = find_new_executor(scene, executor_type)

    return add_new_index(scene, new_index, object, executor_type)


def find_new_executor(scene, executor_type):
    executor_map = {
        'event_list': 'event_list',
        'cue_list': 'cue_list',
        'start_macro': 'macro',
        'end_macro': 'macro',
        'start_preset': 'preset',
        'end_preset': 'preset',
    }

    base_name = executor_map[executor_type]
    
    range_min = getattr(scene, f"orb_{base_name}s_start")
    range_max = getattr(scene, f"orb_{base_name}s_end")

    index_range = list(range(range_min, range_max + 1))

    if executor_type in executor_map:
        return find_unused_index(scene, index_range, executor_map[executor_type])
    else:
        print(f"An error occurred within find_new_executor with argument {executor_type}. Returning default index")
        return DEFAULT_EXECUTOR_INDEX


def get_all_executor_strip_names(scene):
    return [strip.name for strip in scene.sequence_editor.sequences if (strip.type == 'COLOR' or strip.type =='SOUND')]


def find_unused_index(scene, range, base_attribute):
    strips = get_all_executor_strips(scene)
    used_indices = set()

    start_attr = f"int_start_{base_attribute}"
    end_attr = f"int_end_{base_attribute}"
    attr = f"int_{base_attribute}"

    for strip in strips:
        if hasattr(strip, start_attr):
            used_indices.add(getattr(strip, start_attr))
        if hasattr(strip, end_attr):
            used_indices.add(getattr(strip, end_attr))
        if hasattr(strip, attr):
            used_indices.add(getattr(strip, attr))

    for index in range:
        if index not in used_indices:
            return index

    return None


def get_all_executor_strips(scene):
    strips = [strip for strip in scene.sequence_editor.sequences if (strip.type == 'COLOR' or strip.type =='SOUND')]
    strips.append(scene)
    return strips


def add_new_index(scene, new_index, object, executor_type):
    try:
        setattr(object, f"int_{executor_type}", new_index)
    except:
        print("An error occured while trying to set property to new index.")
    return new_index 