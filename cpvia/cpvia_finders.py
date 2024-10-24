# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
import re

from ..utils.cpvia_utils import color_object_to_tuple_and_scale_up
from ..cpvia.mix import Mixer 
from ..assets.sli import SLI 
from ..assets.dictionaries import Dictionaries 
from ..cpvia.map import Mapping 
from ..cpvia.find import Find 
from ..maintenance.logging import alva_log

NUMBER_TO_ADD_IF_NULL = 1


class CPVIAFinders:
    '''NOTE: If random stuff broke that used to be fine, it's probably this function's fault.'''
    def find_parent(self, object):
        """
        Catches and corrects cases where the object is a collection property instead of 
        a node, sequencer strip, object, etc. This function returns the bpy object so
        that the rest of the harmonizer can find what it needs.
        
        Parameters: 
            object: A bpy object that may be a node, strip, object, or collection property
        Returns:
            parent: A bpy object that may be a node, strip, or object
        """
        from ..updaters.node import NodeUpdaters 
        
        if not isinstance(object, bpy.types.PropertyGroup):
            return object

        node = None
        try:
            node = Find.find_node_by_tree(object.node_name, object.node_tree_pointer, pointer=True)
        except:
            pass
        
        if node:
            return node
                    
        # Run the program that's supposed to set this up since it must not have run yet
        nodes = Find.find_nodes(bpy.context.scene)
        for node in nodes:
            if node.bl_idname == 'mixer_type':
                NodeUpdaters.update_node_name(node)
                
        # Try again
        try:
            node = Find.find_node_by_tree(object.node_name, object.node_tree_pointer, pointer=True)
        except:
            pass
        
        if node:
            return node
            
        print(f"find_parent could not find parent for {object}.")
        return None


    def find_my_argument_template(self, parent, type, chan, param, value):
        console_mode = bpy.context.scene.scene_props.console_type_enum
        if console_mode == "option_eos":
            argument = Dictionaries.eos_arguments_dict.get(f"str_{param}_argument", "Unknown Argument")
        elif console_mode == 'option_ma3':
            argument = Dictionaries.ma3_arguments_dict.get(f"str_{param}_argument", "Unknown Argument")
        elif console_mode == 'option_ma2':
            argument = Dictionaries.ma2_arguments_dict.get(f"str_{param}_argument", "Unknown Argument")
        else:
            SLI.SLI_assert_unreachable()
            return "Invalid console mode."

        needs_special = False
        if param in ['strobe', 'prism']:
            needs_special = True
            if value == 0:
                special_argument = self.find_my_patch(parent, chan, type, f"str_disable_{param}_argument")
            else: special_argument = self.find_my_patch(parent, chan, type, f"str_enable_{param}_argument")

        if needs_special:
            if param == 'strobe':
                if value == 0:
                    argument = f"{special_argument}"
                else:
                    argument = f"{special_argument}, {argument}"
            else:
                argument = special_argument

        return argument
    
    
    def add_channel_parameter_value(self, parent, property_name, controller_type):
        """
        Intensity updater function called from universal_updater that returns 3 lists for channel,
        parameter, and value.

        Parameters:
        self: The object from which this function is called.
        p: Parameter.

        Returns:
        c: Channel list
        v: Values list
        type: Controller type
        """
        alva_log("find", f"Find my Channels and Values: {parent}, {property_name}")
        
        if controller_type in ["Influencer", "Brush"]:
            alva_log("find", f"Is Influencer or Brush.")
            from .influencers import Influencers
            influencers = Influencers()  # Must be instance.
            return influencers.find_my_influencer_values(parent, property_name, controller_type)
        
        elif controller_type in ["Fixture", "Pan/Tilt Fixture", "Pan/Tilt"]:
            alva_log("find", f"Is Channel.")
            channel = self.find_channel_number(parent)
            value = self._find_my_value(parent, property_name, controller_type, channel)
            parameter = self._strip_graph_suffix(property_name)  # Change [pan or tilt]_graph to simple
            return [channel], [parameter], [value]
        
        elif controller_type in  ["group", "strip", "Stage Object"]:
            alva_log("find", f"Is Group.")
            return self._find_my_group_values(parent, property_name, controller_type)
            
        elif controller_type == "mixer":
            alva_log("find", f"Is Mixer.")
            mixing = Mixer()
            return mixing.mix_my_values(parent, property_name)
              
        else: return None, None, None
        
        
    def _find_controller_type(self, parent, p):
        """
        Function called by find_my_channels_and_[parameter values] functions to find controller type.

        Parameters:
        parent: The object from which this function is called. Should only be a mesh or known node type.
        
        Returns:
        type: The controller type in string, to be used to determine how to find channel list.
        """
        is_pan_tilt_node = p in ['pan_graph', 'tilt_graph']
           
        if hasattr(parent, "type"):
            if parent.type == 'MESH':
                if hasattr(parent, "object_identities_enum") and not is_pan_tilt_node:
                    return parent.object_identities_enum
                elif hasattr(parent, "object_identities_enum") and is_pan_tilt_node:
                    return "Pan/Tilt"
                else: SLI.SLI_assert_unreachable()
            
            elif parent.type == 'COLOR':  # Color strip
                return "strip"
            
            elif parent.type == 'CUSTOM': # Nodes
                controller_types = {
                'group_controller_type': "group",
                'mixer_type': "mixer",
                }
                return controller_types.get(parent.bl_idname, None)
        else:
            SLI.SLI_assert_unreachable()
            
            
    def find_channel_number(self, parent):
        """This is where we try to find the channel number of the object."""
        try:
            return parent.list_group_channels[0].chan
        except:
            return NUMBER_TO_ADD_IF_NULL


    def _find_int(string):        
        """Tries to find an integer inside the string and returns it as an int. 
           Returns 1 if no integer is found.
        """
        match = re.search(r'\d+', string)
        return int(match.group()) if match else NUMBER_TO_ADD_IF_NULL


    def _find_my_value(self, parent, p, type, chan):
        """Recieves a bpy object mesh (parent), and parameter, and returns integers in a [list]
           This is for single fixtures."""
        attribute_name = Dictionaries.parameter_mapping.get(p)
        if attribute_name:
            unmapped_value = getattr(parent, attribute_name)
            if p == "color":
                unmapped_value = color_object_to_tuple_and_scale_up(unmapped_value)
            elif p in ["strobe", "pan", "tilt", "zoom", "gobo_speed"]:  # NOT "pan_graph" or "tilt_graph" since that is mapped by the node updater
                mapping = Mapping()
                try: 
                    value = mapping.map_value(parent, chan, p, unmapped_value, type)
                    return value
                except AttributeError:
                    print("Error in find_my_value when attempting to call map_value.")
                    
            return unmapped_value
        else:
            return None
            
            
    def _strip_graph_suffix(self, p):
        if p in ['pan_graph', 'tilt_graph']:
            p = p.replace("_graph", "")
            return p
        else:
            return p
            
            
    def _find_my_group_values(self, parent, p, type):
        """Recieves a bpy object mesh (parent), parameter, and controller_type, and returns three lists for channels list (c), parameters list, and values list (v)"""
        c = []
        param = []
        v = []
        
        attribute_name = Dictionaries.parameter_mapping.get(p)
        if attribute_name:  # Find and map value
            new_value = getattr(parent, attribute_name)
            
            if p == "color":
                new_value = color_object_to_tuple_and_scale_up(new_value)
            
            if parent.type == 'CUSTOM':
                finders = Find()
                finders.trigger_downstream_nodes(parent, attribute_name, new_value)
            
            channels_list = []
            channels_list = self._find_channels_list(parent)
            
            mapping = Mapping()
            for channel in channels_list:
                c.append(channel)
                param.append(p)
                if p in ["strobe", "pan", "tilt", "zoom", "gobo_speed", "pan_tilt"]:
                    value_to_add = mapping.map_value(parent, channel, p, new_value, type)
                    v.append(value_to_add)
                else:
                    v.append(new_value)
            return c, param, v
        
        else: SLI.SLI_assert_unreachable()
        
        
    def _find_channels_list(self, parent, string=False):
        """Recieves a bpy object and returns list of channels, which are ints.
           The channels list should always be parent.list_group_channels, which
           is maintained by the updater for the group enum and text input."""
        channels_list = []
            
        for channel in parent.list_group_channels:
            if string:
                channels_list.append(str(channel.chan))
            else: 
                channels_list.append(channel.chan)
                
        return channels_list