# This file is part of Alva Sorcerer.
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


'''
=====================================================================
This is the third major iteration of the harmonizer. It is not yet
complete. It will replace the entire existing harmonizer.py.
=====================================================================
'''


## Double hashtag indicates notes for future development requiring some level of attention


import bpy
from functools import partial


def send_osc_string(osc_addr, addr, port, string):
    def pad(data):
        return data + b"\0" * (4 - (len(data) % 4 or 4))

    if not osc_addr.startswith("/"):
        osc_addr = "/" + osc_addr

    osc_addr = osc_addr.encode() + b"\0"
    string = string.encode() + b"\0"
    tag = ",s".encode()

    message = b"".join(map(pad, (osc_addr, tag, string)))
    try:
        sock.sendto(message, (addr, port))

    except Exception:
        import traceback
        traceback.print_exc()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


class HarmonizerBase:
    INFLUENCER = 'influencer'
    CHANNEL = 'channel'
    GROUP = 'group'
    MIXER = 'mixer'
    PAN_TILT = 'pan_tilt'


class HarmonizerPublisher(HarmonizerBase):
    def __init__(self):
        self.change_requests = []
    
    def send_cpvia(self, c, p, v, i, a):
        """
        Decides whether to send osc now (we are not playing back) or later (we are playing back).

        Parameters:
        cpvia: channel, parameter, value, influence, argument template.

        This function does not return a value.
        """
        if c and p and v and i and a:
            self.add_change_request(c, p, v, i, a) if bpy.context.scene.is_playing else self.send_osc_now(c, p, v, i, a)
        else: print("Invalid cpvia request found in Sorcerer.")
         
    def add_change_request(self, c, p, v, i, a):
        """
        This function creates a change request that will later be harmonized with against other change requests.

        Parameters:
        cpvia: channel, parameter, value, influence, argument template.

        This function does not return a value. It appends a change request to change_requests.
        """
        if c and p and v and i and a:
            self.change_requests.append(c, p, v, i, a)
        else: print("Invalid cpvia request found in Sorcerer's add_change_request.")
          
    def send_osc_now(self, c, p, v, i, a):
        """
        This function creates a list of (address, argument) tuples, each tuple to be separately passed to the send_osc() function.

        Parameters:
        cpvia: channel, parameter, value, influence, argument template.

        This function does not return a value.
        """
        if c and p and v and i and a:
            try: 
                messages = self.form_osc(c, p, v, i, a)  # Should return a list of tuples.
                if not isinstance(address, str) or not isinstance(argument, str):
                    raise ValueError("Invalid address and argument.")
            except ValueError as e:
                print(f"Error in finding address or argument: {e}")
            except Exception as e:
                print(f"Unexpected error in finding address or argument: {e}")
            send_osc(messages)
                # 
        else: print("Invalid cpvia request found in Sorcerer's send_osc_now.")
        
    def form_osc(self, c, p, v, i, a):
        """
        This function converts cpvia into (address, argument) tuples

        Parameters:
        cpvia: channel, parameter, value, influence, argument template.

        Returns:
        messages: A list of (address, argument) tuples.
        """  
        if c and p and v and i and a:
            try:
                address = bpy.context.scene.str_address_template
                if not address or not isinstance(address, str):
                    raise ValueError("Invalid address template.")
            except ValueError as e:
                print(f"Error in address template: {e}")
            except Exception as e:
                print(f"Unexpected error in address template: {e}")
            address = address.replace("#", c).replace("$", v)
            argument = a.replace("#", c).replace("$", v)
            return (address, argument)
        else: raise ValueError("Invalid cpvia request found in Sorcerer's form_osc.")
            
            
class HarmonizerFinders(HarmonizerBase):
    
    def find_my_properties(self):
        """
        Finds the influence and the argument templates using self.
        
        Returns:
        This function returns influence (i) as an integer and argument (a) as a string.
        """  
        try:
            i = self.find_my_influence(self)  # Should return an integer.
            if not isinstance(i, int):
                raise ValueError("Influence must be an integer.")
            a = self.find_my_argument_template(self)  # Should return a string.
            if not isinstance(a, str):
                raise ValueError("Argument template must be a string.")     
            return i, a
        
        except ValueError as e:
            print(f"Error in finding influence or template: {e}")

        except Exception as e:
            print(f"Unexpected error in finding influence or template: {e}")
            
            
    def find_my_controller_type(self):
        """
        Function called by find_my_channels_and_[parameter values] functions to find controller type.

        Parameters:
        self: The object from which this function is called. Should only be a mesh or known node type.
        
        Returns:
        type: The controller type in string, to be used to determine how to find channel list.
        """    
        if hasattr(self, "type"):
            if self.type == 'MESH':
                if hasattr(self, "is_influencer") and self.is_influencer:
                    return "influencer"
            elif hasattr(self, "int_object_channel_index") and self.int_object_channel_index != 0 and isinstance(self.int_object_channel_index, int):
                return "channel"
            else: sorcerer_assert_unreachable()
                
            controller_types = {
            'group_controller_type': "group",
            'mixer_type': "mixer",
            'pan_tilt_type': "pan_tilt",
            }
            
            return controller_types.get(self.type, None)
            
        else: sorcerer_assert_unreachable()
        
        
    def find_my_channels_and_values(self, p):
        """
        Intensity updater function called from universal_updater that returns 2 lists for channels and values.

        Parameters:
        self: The object from which this function is called.
        p: Parameter.
        
        Returns:
        c: Channel list
        v: Values list
        """
        try:
            controller_type = self.find_my_controller_type(self)  # Should return a string.
            if controller_type is None:
                raise ValueError(f"Could not find controller type of {self.name}'s {p}.")
            except ValueError as e:
                print(f"Error in finding controller type for {p}: {e}")
                return None, None
            except Exception as e:
                print(f"Unexpected error in finding controller type for {p}: {e}")
                return None, None
        
        if controller_type == "influencer":
            try:  # Find channels.
                current_channels = self.find_influencer_current_channels(self)  # Should return a list.
                if not isinstance(current_channels, list):
                    raise ValueError(f"Error in finding influencer {self.name}'s new channels.")
                channels_to_restore, channels_to_add = find_influencer_channels_to_change(self, current_channels)  # Should return a list
                if not isinstance(channels_to_restore, list) or not isinstance(channels_to_add, list):
                    raise ValueError(f"Error in finding influencer {self.name}'s channels to restore or add.")
            except ValueError as e:
                print(f"Error in updating {p}: {e}")
                return None, None
            except Exception as e:
                print(f"Unexpected error in updating {p}: {e}")
                return None, None
            try:  # Find intensities.
                add_value = self.find_my_value(self, p)  # Should return a list with just one [integer].
                if not isinstance(add_value, list):
                    raise ValueError(f"Error in finding influencer {self.name}'s new values.")
                restore_values = self.find_my_restore_values(self, p)
                if not isinstance(restore_values, list):
                    raise ValueError(f"Error in finding influencer {self.name}'s restore values.")
            c = new_channels + channels_to_restore
            v = add_values + restore_values
            return c, v
        
        elif controller_type == "channel":
            value = self.find_my_value(self, p)  # Should return an integer.
            if not isinstance(value, int):
                raise ValueError(f"Error in finding channel {self.name}'s values.")
            return [self.int_object_channel_index], [value]
        
        elif controller_type == "group":
            try: 
                c, v = self.find_my_group_values(self, p)  # Should return two lists.
                if not isinstance(c, list) or not isinstance(v, list):
                    raise ValueError(f"Error in mixing group controller {self.name}'s values.")
                return c, v
        
        elif controller_type == "mixer":
            try: 
                mixing = HarmonizerMixer()
                c, v = mixing.mix_my_values(self, p)  # Should return two lists.
                if not isinstance(c, list) or not isinstance(v, list):
                    raise ValueError(f"Error in mixing group controller {self.name}'s values.")
                return c, v
        
        elif controller_type == "pan_tilt":
            try: 
                mapper = HarmonizerMapper()
                c, v = mapper.map_my_pan_tilt_values(self, p)  # Should return two lists.
                if not isinstance(c, list) or not isinstance(v, list):
                    raise ValueError(f"Error in mapping pan_tilt controller {self.name}'s values.")
                return c, v
                    
        else: sorcerer_assert_unreachable()
        
        
    """Recieves a bpy object mesh, self, and returns a list representing channels within that mesh"""
    def find_influencer_current_channels(self):
        # Use the get_lights_within_mesh function in the library to get channels, then add them to its captured_set().
        return current_channels
        
        
    """Recieves a bpy object mesh, self, and returns two lists representing channels that used to be 
       within that mesh but just left, as well as new additions."""   
    def find_influencer_channels_to_change(self, current_channels):
        # Compare current channels with the object's captured_set()
        return channels_to_restore, channels_to_add
        
        
    """Recieves a bpy object mesh, self, and returns a list of restore values"""
    def find_my_restore_values(channels_to_restore, p):
        # Use the background property registered on the objects to restore.
        return restore_values


    """Recieves a bpy object mesh, self, and returns a integers in a [list]"""
    def find_my_value(self, p):
        # Use effects to mix up values inside a group, or simply return a single integer
        return value


    """Recieves a bpy object mesh, self, and returns two lists for channels list (c) and values list (v)"""    
    def find_my_group_values(self, p):
        # Use effects to mix up values inside a group, or simply return a simple value
        return channels, values
        
        
"""This should house all logic for mapping sliders and other inputs to fixture-appropriate values"""
class HarmonizerMapper(HarmonizerBase):
    
    
    
"""This should house all logic for mixing values with the mixers"""   
class HarmonizerMixer(HarmonizerBase):
    
    """Recieves a bpy object mesh, self, and returns two lists for channels list (c) and values list (v)"""    
    def mix_my_values(self, p):
        if isinstance(channel_list, str):
            channel_list = [int(chan.strip()) for chan in channel_list.split(',') if chan.strip().isdigit()]
        
        elif all(isinstance(chan, bpy.types.Object) for chan in channel_list):
            channel_list = sorted(channel_list, key=lambda obj: obj.name)
            channel_list = [obj.name for obj in channel_list]
        else:
            channel_list = sorted(channel_list)
       
        sorted_channels = sorted(channel_list)
        mixed_values = []

        if value_two is None and mode == "alternate":
            # Alternating between value_one and value_three for each channel.
            for counter, chan in enumerate(sorted_channels, start=1):
                chan_value = value_three if counter % 2 == 0 else value_one
                mixed_values.append((chan, chan_value))

        elif value_two is None:
            # Interpolating between value_one and value_three for the channel list.
            num_channels = len(sorted_channels)
            for index, chan in enumerate(sorted_channels):
                ratio = index / (num_channels - 1) if num_channels > 1 else 0
                chan_value = ((1 - ratio) * value_one + ratio * value_three)
                mixed_values.append((chan, chan_value))

        else:
                num_channels = len(sorted_channels)
                mid_index = num_channels // 2

                for index, chan in enumerate(sorted_channels):
                    if num_channels % 2 == 1:  # If odd number of channels.
                        if index == mid_index:
                            chan_value = value_two
                        elif index < mid_index:
                            # Interpolate between value_one and value_two.
                            ratio = index / mid_index
                            chan_value = (1 - ratio) * value_one + ratio * value_two
                        else:
                            # Interpolate between value_two and value_three.
                            ratio = (index - mid_index) / mid_index
                            chan_value = (1 - ratio) * value_two + ratio * value_three
                    else:  # If even number of channels, treat the two middle indices as value_two.
                        if index == mid_index or index == mid_index - 1:
                            chan_value = value_two
                        elif index < mid_index:
                            # Interpolate between value_one and value_two.
                            ratio = index / (mid_index - 1)
                            chan_value = (1 - ratio) * value_one + ratio * value_two
                        else:
                            # Interpolate between value_two and value_three.
                            ratio = (index - mid_index) / (mid_index - 1)
                            chan_value = (1 - ratio) * value_two + ratio * value_three

                    mixed_values.append((chan, chan_value))
        return channels, values
    
    
def universal_updater(self, context, property_name, find_function):
    """
    Universal updater function that contains the common logic for all property updates.

    Parameters:
    self: The instance from which this function is called.
    context: The current context.
    property_name (str): The name of the property to update.
    find_function (function): The function that finds the channels and values for the given property.
    """
    p = property_name
    
    try:
        c, v = find_function(self, p)  # Should return 2 lists.
        if not isinstance(c, list) or not isinstance(v, list):
            raise ValueError(f"Channel and value lists are required for {p}.")

        i, a = find_my_properties(self)  # Should return an int and string.
        if not isinstance(i, int) or not isinstance(a, str):
            raise ValueError(f"Influence and argument template are required for {p}.")
            
        send_cpvia(c, p, v, i, a)  # No return value.

    except ValueError as e:
        print(f"Error in updating {p}: {e}")

    except Exception as e:
        print(f"Unexpected error in updating {p}: {e}")

    
intensity_updater = partial(universal_updater, property_name="intensity", find_function=find_my_channels_and_values)
color_updater = partial(universal_updater, property_name="color", find_function=find_my_channels_and_values)
pan_updater = partial(universal_updater, property_name="pan", find_function=find_my_channels_and_values)
tilt_updater = partial(universal_updater, property_name="tilt", find_function=find_my_channels_and_values)
strobe_updater = partial(universal_updater, property_name="strobe", find_function=find_my_channels_and_values)
zoom_updater = partial(universal_updater, property_name="zoom", find_function=find_my_channels_and_values)
iris_updater = partial(universal_updater, property_name="iris", find_function=find_my_channels_and_values)
diffusion_updater = partial(universal_updater, property_name="diffusion", find_function=find_my_channels_and_values)
edge_updater = partial(universal_updater, property_name="edge", find_function=find_my_channels_and_values)
gobo_id_updater = partial(universal_updater, property_name="gobo_id", find_function=find_my_channels_and_values)
gobo_speed_updater = partial(universal_updater, property_name="gobo_speed", find_function=find_my_channels_and_values)
prism_updater = partial(universal_updater, property_name="prism", find_function=find_my_channels_and_values)
pan_tilt_updater = partial(universal_updater, property_name="pan_tilt", find_function=find_my_channels_and_values)


# For development purposes only
if __name__ == "__main__":
    register()
