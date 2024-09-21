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


import bpy
import re

from ..utils.utils import Utils 
from ..cpvia.mix import Mixer 
from ..assets.sli import SLI 
from ..assets.dictionaries import Dictionaries 
from ..cpvia.map import Mapping 
from ..cpvia.find import Find 
from ..maintenance.logging import alva_log


NUMBER_TO_ADD_IF_NULL = 1


class CPVIAFinders:
    def find_my_channels_and_values(self, parent, p):  # aka find_function
        """
        Intensity updater function called from universal_updater that returns 2 lists for channels and values,
        as well as the controller type for use when building the osc argument

        Parameters:
        self: The object from which this function is called.
        p: Parameter.

        Returns:
        c: Channel list
        v: Values list
        type: Controller type
        """
        alva_log("find", f"Find my Channels and Values: {parent}, {p}")
        if p in ['pan_graph', 'tilt_graph']:
            controller_type = self._find_my_controller_type(parent, pan_tilt_node=True)  # Should return a string.
        else:
            controller_type = self._find_my_controller_type(parent, pan_tilt_node=False)  # Should return a string.
        
        if controller_type in ["Influencer", "Brush"]:
            alva_log("find", f"Is Influencer or Brush.")
            from .influencers import Influencers
            influencers = Influencers()  # Must be instance.
            c, p, v = influencers.find_my_influencer_values(parent, p, controller_type)
            return c, p, v, controller_type
        
        elif controller_type in ["Fixture", "Pan/Tilt Fixture", "Pan/Tilt"]:
            alva_log("find", f"Is Channel.")
            channel = self.find_channel_number(parent)
            value = self._find_my_value(parent, p, controller_type, channel)
            p = self._strip_graph_suffix(p)  # Change [pan or tilt]_graph to simple
            return [channel], [p], [value], controller_type
        
        elif controller_type in  ["group", "strip", "Stage Object"]:
            alva_log("find", f"Is Group.")
            c, p, v = self._find_my_group_values(parent, p, controller_type)
            return c, p, v, controller_type
        
        elif controller_type == "mixer":
            alva_log("find", f"Is Mixer.")
            mixing = Mixer()
            c, p, v = mixing.mix_my_values(parent, p)
            return c, p, v, controller_type
                    
        else: return None, None, None, None
        
        
    def _find_my_controller_type(self, parent, pan_tilt_node=False):
        """
        Function called by find_my_channels_and_[parameter values] functions to find controller type.

        Parameters:
        parent: The object from which this function is called. Should only be a mesh or known node type.
        
        Returns:
        type: The controller type in string, to be used to determine how to find channel list.
        """
        if hasattr(parent, "type"):
            if parent.type == 'MESH':
                if hasattr(parent, "object_identities_enum") and not pan_tilt_node:
                    return parent.object_identities_enum
                elif hasattr(parent, "object_identities_enum") and pan_tilt_node:
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
                unmapped_value = Utils.color_object_to_tuple_and_scale_up(unmapped_value)
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
                new_value = Utils.color_object_to_tuple_and_scale_up(new_value)
            
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