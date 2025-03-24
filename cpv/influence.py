# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from mathutils import Vector, kdtree
import time
import math

from .publish.publish import Publish, CPV
from ..maintenance.logging import alva_log

PARAMETER_NOT_FOUND_DEFAULT = 'alva_intensity'
WHITE_COLOR = (1, 1, 1)
MAINTAIN_ROUNDING_THRESHOLD = 3
INFLUENCE_RADIUS_MULTIPLIER = 2
LIGHT_SENSITIVITY_MULTIPLIER = 2

DEBUG = False

# Debug colors
RED = "\033[31m"
GREEN = "\033[32m"
BLUE = "\033[34m"
RESET = "\033[0m"


def find_influencer_cpv(Generator, Parameter):
    return InfluenceCPV(Generator, Parameter).execute()


class InfluenceCPV:
    '''
    We're trying to make lights on the stage turn on and off by moving a 3D mesh inside Blender.
    This class is responsible for Alva Sorcerer's Influencer tool and for its Brush tool.

    This job of this class is to trigger the publisher.

    First, we need to figure out what stuff we need to do stuff to (SetGroups). That will give 
    us the following lists of stuff:

        1. A list of channels that just showed up that we need to initialize
        2. A list of channels that we need to maintain based on recent changes to the mesh's properties
        3. A list of channels that just left that we need to restore

    Then, we need to do the things to the stuff:

        1. Initialize the new channels so the influencer can appear to move across the stage 
           (Initialize class).
        2. Maintain the old channels so we can animate influencer parameters (Maintain class).
        3. Release the channels that are no longer inside so that they don't get stuck 
           (Release class).
    '''
    def __init__(self, Generator, Parameter):
        self.parent = Generator.parent
        self.Parameter = Parameter
        self._make_parent_real()
        self.property_name = Generator.property_name
        self.controller_type = Generator.controller_type
        self.parameter_property_group = self._get_property_group_by_parameter(self.parent, Generator.property_name)
        self._is_releasing = self._is_releasing_channels()

    def _make_parent_real(self):
        if not self._parent_object_is_a_depsgraph_copy():
            return
        
        real_parent = self._find_the_real_object()
        self._ensure_parent_exists(real_parent)
        self.parent = real_parent

    def _parent_object_is_a_depsgraph_copy(self):
        return self.parent.is_evaluated

    def _find_the_real_object(self):
        return bpy.data.objects.get(self.parent.name)

    def _ensure_parent_exists(self, real_parent):
        if real_parent is None:
            raise RuntimeError("Unable to resolve the real object for the evaluated parent.")

    def _get_property_group_by_parameter(self, parent, parameter_name):
        '''DOCUMENTATION CODE A1'''
        property_group = next((group for group in parent.influencer_list if group.parameter_name == parameter_name), None)
        if property_group is None:
            property_group = parent.influencer_list.add()
            property_group.parameter_name = parameter_name
        return property_group.influenced_object_property_group
    
    def _is_releasing_channels(self):
        return self.controller_type == "Influencer" 


    def execute(self):
        start = time.time()
        if DEBUG: alva_log("influence", f"\n{RED}INFLUENCER SESSION({self.controller_type}):{RESET}")
        new_channels, maintain_channels, release_channels, values, new_channels_values = SetGroups(self).execute()
        Initialize(self).execute(new_channels, new_channels_values)
        Maintain(self).execute(maintain_channels, values)
        Release(self).execute(release_channels)
        if DEBUG: alva_log('time', f"TIME: find_influencer_cpv took {time.time() - start} seconds")


class SetGroups:
    '''
    We're trying to make lights on the stage turn on and off by moving a 3D mesh inside Blender.

    The job of this class is to find the groups of stuff (fixtures) we need to do stuff with 
    (internal groups) and to (external groups).

    First, in the __init__(), we need to:
    
        1. Decide if we are going to release fixtures no longer inside our mesh (is_releasing).
           We don't want to release fixtures if we are in Brush mode since the changes a 
           brush makes persist after the brush leaves.
        2. Decide if we will maintain the parameters of fixtures still inside based on the 
           animation of the influencer's parameters (is_maintaining). We only need to do
           this while in Influencer mode and not while in Brush mode because a brush only
           needs to make a change once. An influencer on the other hand is more like a
           persistent 3D object in that its parameters can ebb and flow over time while it
           is on top of fixtures.

    Second, in the execute(), we need to find 2 groups of fixtures for use inside this class:

        1. Stationary meshes representing fixtures that are currently inside the mesh we're 
           moving (_current_channels).
        2. The meshes that we already did stuff to last time this code ran (_stored_channels).

    Third, in the execute(), we need to use those lists to find the groups we need to do stuff to outside this class:

        1. Fixtures that just showed up inside our mesh (new_channels)
        2. Fixtures that disappeared (release_channels)
        3. Fixtures we need to maintain based on our mesh's animation (maintain_channels)
    '''
    def __init__(self, influencer):
        self.influencer = influencer
        self._is_releasing = self.influencer._is_releasing
        self.is_maintaining = self._is_maintaining_channels()

    def _is_maintaining_channels(self):
        return self.influencer.controller_type in ["Influencer", "Key"]


    def execute(self):
        start = time.time()
        _current_channels, values = self._find_current_channels()
        _stored_channels = [chan.channel_object for chan in self.influencer.parameter_property_group]

        if DEBUG: alva_log('time', f"TIME: find_influencer_current_channels took {time.time() - start} seconds")
        if DEBUG: alva_log("influence", f"{RED}SetGroups._execute | Current channels: {[obj.name for obj in _current_channels]}\nSetGroups._execute | Stored Channels: {[obj.name for obj in _stored_channels]}")

        new_channels = [chan for chan in _current_channels if chan not in _stored_channels]
        release_channels = [chan for chan in _stored_channels if chan not in _current_channels]
        maintain_channels = [chan for chan in _current_channels if chan in _stored_channels] if self.is_maintaining else []

        # Align values with new_channels
        if self.influencer.controller_type == "Key":
            new_channels_values = [values[_current_channels.index(chan)] for chan in new_channels]
        else: 
            new_channels_values = None

        if DEBUG: alva_log("influence", f"SetGroups._execute | Must Initialize: {[obj.name for obj in new_channels]}\n"
                            f"SetGroups._execute | Must Maintain: {[obj.name for obj in maintain_channels]}\n"
                            f"SetGroups._execute | Must Release: {[obj.name for obj in release_channels]}{RESET}")

        return new_channels, maintain_channels, release_channels, values, new_channels_values
        
    def _find_current_channels(self):
        if self.influencer.controller_type != "Key":
            self._trigger_object_id_updaters()
            channel_objects = FindObjectsInside(self.influencer.parent).execute()
            return list(channel_objects), []
        else:
            light_objects, influencers, strengths = FindInfluenceField(self.influencer.parent).execute()
            if DEBUG: alva_log("influence", f"SetGroups._find_current_channels | lights, influencers, strengths: {light_objects, influencers, strengths}")
            harmonized_channels, harmonized_values = self._harmonize_influence_field(light_objects, influencers, strengths)
            return list(harmonized_channels), list(harmonized_values)
        
    def _trigger_object_id_updaters(self):
        # This just needs to run the str_manual_fixture_selection updater on all linked (within same collection) influencers
        return None
        
    def _harmonize_influence_field(self, light_objects, influencers, strengths):
        harmonized_channels = []
        harmonized_values = []

        light_influence_map = {}

        # Aggregate influences per light
        for light, influencer, strength in zip(light_objects, influencers, strengths):
            if light not in light_influence_map:
                light_influence_map[light] = []
            light_influence_map[light].append((influencer, strength))

        # Blend influences for each light
        for light, influence_data in light_influence_map.items():
            blended_value = sum(
                data[1] * getattr(data[0], f"alva_{self.influencer.property_name}", 0)
                for data in influence_data
            )
            harmonized_channels.append(light)
            harmonized_values.append(blended_value)

        if DEBUG: alva_log("influence", f"{GREEN}SetGroups._harmonize_influence_field | Harmonized channels: {[chan.name for chan in harmonized_channels]}\nSetGroups._harmonize_influence_field | Harmonized values: {[round(value, 2) for value in harmonized_values]}")

        return harmonized_channels, harmonized_values


class Initialize:
    def __init__(self, influencer):
        self.influencer = influencer
        self.is_relative = self._is_relative()
        self.is_erasing = self._is_erasing_brush()
        self._set_argument_prefix()

    def _is_relative(self):
        influencer = self.influencer
        return (
            influencer.controller_type == "Brush" or
            influencer.controller_type in ["Influencer", "Key"] and influencer.property_name != "color"
        )

    def _set_argument_prefix(self):
        influencer = self.influencer
        if self.is_relative:
            prefix = "lower" if self.is_erasing else "raise"
            self.property_name = f"{prefix}_{influencer.property_name}"
        else:
            self.property_name = influencer.property_name

    def _is_erasing_brush(self):
        influencer = self.influencer
        return (
            influencer.controller_type == "Brush" and
            influencer.parent.is_erasing
        )


    def execute(self, new_channels, values):
        if values: # 3D gradient mode
            list(map(self._initiate_channel, new_channels, values))
        else:
            list(map(self._initiate_channel, new_channels))

    def _initiate_channel(self, channel_object, value=None):
        channel_number = self._get_initiate_channel_number(channel_object)
        value = self._determine_initiate_value(value)
        Publish(self.influencer, self.influencer.Parameter, channel_number, self.property_name, value, sender=CPV).execute()
        self._set_memory_item(self.influencer.parameter_property_group, channel_object, value)
        if DEBUG: alva_log("influence", f"{BLUE}Initialize._initiate_channel | Channel {channel_number} | Value: {round(value, 2)}, Property name: {self.property_name}")

    def _get_initiate_channel_number(self, channel_object):
        return channel_object.list_group_channels[0].chan

    def _determine_initiate_value(self, input_value=None):
        return input_value if input_value else getattr(self.influencer.parent, f"alva_{self.influencer.property_name}")

    def _set_memory_item(self, collection, channel_object, value):
        new_channel = collection.add()
        new_channel.channel_object = channel_object
        if self.influencer.property_name == "color":
            new_channel.current_influence_color = value
        else:
            new_channel.current_influence = value


class Maintain:
    '''
    We're trying to make lights on the stage turn on and off by moving a 3D mesh inside Blender.

    What happens when a light is eaten by the influencer and then you change a parameter on the influencer?
    Does the light follow along or no? Without this class, the light would not follow along. That's because
    without this class, the only time an influencer can influence a light is when the light enters (Initiate 
    class) or when a light exits (Release class). This class is here to say, "Hey, if you make changes to
    the influencer, that shouldn't just impact how it influences lights in the future, it should also impact
    the lights currently in its tummy. 

    We maintain lights currently eaten by:

        1. Finding the memory item, which tells us what we already did to the light
        2. Finding the stored value inside the memory item
        3. Finding the current value, from the UI of the influencer object (parent)
        4. Calculating the change between the above two values, because we use relative
           adjustments so multiple influencers can overlap and coexist with on-console effects
        5. Calculating the new value to store in memory, this helps us be on the right track
           next time. This also helps us avoid "missing" update problems when Blender's depgraph
           skips updates during rapid, manual slider moves*.
        6. Deciding if the current amount of change is big enough to warrant updating the console
        7. Setting the property name prefix, which is the only way we communicate positive and 
           negative to the console. That's why we use abs() so much. The Publisher is exclusively
           responsible for applying +/-. It does that by altering argument, not by altering value.
        8. Publishing to the console, if we decided to.
        9. Updating the memory item so we remember it next iteration.

    This allows the user to animate the parameters on an influencer while it moves across the scene
    over lights. The user experience is exactly what you would expect: it just magically works
    exactly as you would expect. No unnecesary UI complications (like in versions below 2.1).

    Key things to consider:

        1. From the publisher's perspective, directionality is 100% determined by the prefix (lower_ or raise_).
        2. The value passed is always positive and represents only the magnitude of the change.

    * = When you slide a slider in Blender from 0 to 100 quickly, Blender probably won't run that property's
        updater 100 different times for 1, 2, 3, 4, 5, etc. It may run 3 times, 10 times, or just 2 times.
        So it may run on 12, 45, 76, and finally on 100. It's debounced.
     '''
    def __init__(self, influencer):
        self.influencer = influencer
        self.is_relative = self._is_relative()

    def _is_relative(self):
        return self.influencer.property_name != "color"


    def execute(self, maintain_channels, values):
        if values:
            list(map(self._maintain_channel, maintain_channels, values))
        else:
            list(map(self._maintain_channel, maintain_channels))

    def _maintain_channel(self, channel_object, value=None):
        channel_number = self._get_maintain_channel_number(channel_object)
        memory_item = self._get_memory_item(channel_object)
        stored_value = self._determine_stored_value(memory_item)
        current_value = self._determine_current_value(value)
        needed_change, is_positive = self._determine_needed_change(stored_value, current_value)
        new_memory_value = self._determine_new_memory_value(current_value)
        must_proceed = self._should_proceed(needed_change)
        self._set_argument_prefix(is_positive)
        if DEBUG: alva_log("influence", f"{BLUE}Maintain._maintain_channel | Channel {channel_number} | (Stored value: {round(stored_value, 2)}, Current value: {round(current_value, 2)}, Needed change: {round(needed_change, 2)}, is_positive: {GREEN if is_positive else RED}{is_positive}{BLUE}, New memory value: {round(new_memory_value, 2)}, Property name: {self.property_name}, Must proceed: {GREEN if must_proceed else RED}{must_proceed}{RESET})")

        if must_proceed:
            Publish(self.influencer, self.influencer.Parameter, channel_number, self.property_name, needed_change, sender=CPV).execute()
            self._update_memory_item(memory_item, new_memory_value)

    def _get_memory_item(self, channel_object):
        return next(
            (item for item in self.influencer.parameter_property_group if item.channel_object == channel_object),
            None
        )

    def _get_maintain_channel_number(self, channel_object):
        return channel_object.list_group_channels[0].chan
    
    def _determine_stored_value(self, memory_item):
        prop = "current_influence" if self.influencer.property_name != "color" else "current_influence_color"
        value = (getattr(memory_item, prop))
        if self.influencer.property_name == "color":
            return value
        else:
            return value
    
    def _determine_current_value(self, input_value=None):
        return input_value if input_value else getattr(self.influencer.parent, f"alva_{self.influencer.property_name}")
    
    def _determine_needed_change(self, stored_value, current_value):
        if self.influencer.property_name == "color":
            return current_value, True # The True doesn't matter.
        
        change = abs(stored_value - current_value)
        is_positive = True if stored_value < current_value else False
        return change, is_positive
    
    def _determine_new_memory_value(self, current_value):
        return current_value
    
    def _should_proceed(self, needed_change):
        if self.influencer.property_name == "color":
            return True # TODO - This should be smarter.
        return not math.isclose(needed_change, 0, rel_tol=1e-5, abs_tol=1e-5)
    
    def _set_argument_prefix(self, is_positive):
        influencer = self.influencer
        if self.is_relative:
            prefix = "raise" if is_positive else "lower"
            self.property_name = f"{prefix}_{influencer.property_name}"
        else:
            self.property_name = influencer.property_name

    def _update_memory_item(self, memory_item, new_value):
        collection = self.influencer.parameter_property_group
        index = self._find_index(collection, memory_item)

        if index is not None:
            item = collection[index]
            if self.influencer.property_name == "color":
                item.current_influence_color = new_value
            else:
                item.current_influence = new_value

    @staticmethod
    def _find_index(collection, memory_item):
        index = None
        for i, item in enumerate(collection):
            if item == memory_item:
                index = i
                break
        return index


class Release:
    def __init__(self, influencer):
        self.influencer = influencer
        self._needs_prefix = self._is_needing_prefix()
        self._set_argument_prefix()

    def _is_needing_prefix(self):
        influencer = self.influencer
        return (
            influencer.controller_type == "Brush" or
            influencer.controller_type in ["Influencer", "Key"] and influencer.property_name != "color"
        )
    
    def _set_argument_prefix(self):
        influencer = self.influencer
        if self._needs_prefix:
            self._property_name = f"lower_{influencer.property_name}"
        else:
            self._property_name = influencer.property_name


    def execute(self, release_channels):
        release_function = (self._release_channel_from_all if 
                            self.influencer._is_releasing else 
                            self._release_channel_from_memory
        )
        for channel in release_channels:
            release_function(channel)

    def _release_channel_from_all(self, channel_object):
        channel_number = self._get_release_channel_number(channel_object)
        memory_item = self._get_memory_item(channel_object)
        value = self._determine_release_value(memory_item)
        Publish(self.influencer, self.influencer.Parameter, channel_number, self._property_name, value, sender=CPV).execute()
        self._remove_memory_item(memory_item)

    def _release_channel_from_memory(self, channel_object):  # So that brushes can target the same obj many times
        memory_item = self._get_memory_item(channel_object)
        self._remove_memory_item(memory_item)

    def _get_memory_item(self, channel_object):
        return next(
            (item for item in self.influencer.parameter_property_group if item.channel_object == channel_object),
            None
        )

    def _get_release_channel_number(self, channel_object):
        return channel_object.list_group_channels[0].chan
    
    def _determine_release_value(self, memory_item):
        if self.influencer.property_name != "color":
            return memory_item.current_influence
        else:
            return self.influencer.parent.alva_color_restore

    def _remove_memory_item(self, memory_item):
        collection = self.influencer.parameter_property_group
        index = self._find_index(collection, memory_item)

        if index is not None:
            collection.remove(index)

    @staticmethod
    def _find_index(collection, memory_item):
        index = None
        for i, item in enumerate(collection):
            if item == memory_item:
                index = i
                break
        return index


class FindObjectsInside:
    def __init__(self, parent):
        self.parent = parent
        self.bbox_corners = self._get_bbox_corners()
        self.bbox_min = self._get_bbox_min()
        self.bbox_max = self._get_bbox_max()
        self.kd_tree, self.object_map = self._build_kd_tree()

    def _get_bbox_corners(self):
        return [Vector(corner) for corner in self.parent.bound_box]

    def _get_bbox_min(self):
        return Vector((min(corner.x for corner in self.bbox_corners),
                       min(corner.y for corner in self.bbox_corners),
                       min(corner.z for corner in self.bbox_corners)))

    def _get_bbox_max(self):
        return Vector((max(corner.x for corner in self.bbox_corners),
                       max(corner.y for corner in self.bbox_corners),
                       max(corner.z for corner in self.bbox_corners)))

    def _build_kd_tree(self):
        """Builds a KD-tree and maps indices to objects."""
        objects = [
            obj for obj in bpy.data.objects
            if obj.type == 'MESH' and not obj.hide_viewport
        ]
        kd = kdtree.KDTree(len(objects))
        object_map = {}

        for index, obj in enumerate(objects):
            local_location = self.parent.matrix_world.inverted() @ obj.location
            kd.insert(local_location, index)
            object_map[index] = obj  # Map index to the Blender object

        kd.balance()
        return kd, object_map
    
    def _get_key_vectors(self):
        return {
            (0, 0, 0): .75,
            (10, 0, 0): .75
        }
    
    def _extrapolate_bbox(self):
        return Vector((min(corner.x for corner in self.bbox_corners),
                       min(corner.y for corner in self.bbox_corners),
                       min(corner.z for corner in self.bbox_corners)))


    def execute(self):
        lights_inside = self._get_lights_inside()
        return lights_inside

    def _get_lights_inside(self):
        """Query the KD-tree to find objects within the bounding sphere of the bounding box."""
        # Calculate center and radius of bounding sphere
        bbox_center = (self.bbox_min + self.bbox_max) / 2
        bbox_radius = max((corner - bbox_center).length for corner in self.bbox_corners)

        result = set()
        # KDTree.find_range returns (location, index, distance)
        for result_item in self.kd_tree.find_range(bbox_center, bbox_radius):
            index = result_item[1]  # Extract index from the result
            obj = self.object_map[index]
            if self._is_valid_light_object(obj):
                result.add(obj)
        return result

    def _is_valid_light_object(self, obj):
        return (
            obj.type == 'MESH'
            and not obj.hide_viewport
            and len(obj.list_group_channels) == 1
            and obj.name != self.parent.name
            and self._is_inside_precomputed_bbox(obj)
        )

    def _is_inside_precomputed_bbox(self, obj):
        """Check if an object's location is within the precomputed bounding box."""
        obj_loc_local = self.parent.matrix_world.inverted() @ obj.location
        return all(
            self.bbox_min[i] <= obj_loc_local[i] <= self.bbox_max[i]
            for i in range(3)
        )
    

class FindInfluenceField:  
    def __init__(self, parent):
        self.parent = parent  # The influencer object (3D mesh) whose field we're evaluating.
        self.influencers = self._find_all_relevant_influencers()
        if DEBUG: alva_log("influence", f"{BLUE}FindInfluencerField.__init__ | Relevant influencers: {[obj.name for obj in self.influencers]}")

    def execute(self):
        light_objects = []
        influencers = []
        strengths = []

        # Iterate over all lights in the scene
        for light in self._find_all_lights_in_scene():
            for influencer in self.influencers:
                strength = self._calculate_strength(light, influencer)
                if abs(strength) > 0:  # Only include if within the range of influence
                    light_objects.append(light)
                    influencers.append(influencer)
                    strengths.append(strength)

        return light_objects, influencers, strengths

    def _find_all_relevant_influencers(self):
        # Return all "Key" influencer meshes in the same Blender collection
        return [
            obj for obj in self.parent.users_collection[0].objects
            if obj.object_identities_enum == "Key"
        ]

    def _find_all_lights_in_scene(self):
        # Return all light objects in the scene
        lights = [
            obj for obj in bpy.data.objects
            if obj.object_identities_enum == "Fixture" and obj.users > 0
        ]
        if DEBUG: alva_log("influence", f"FindInfluencerField._find_all_lights_in_scene | Lights: {[obj.name for obj in lights]}")
        return lights

    def _calculate_strength(self, light, influencer):
        # Strength depends on proximity and scale
        distance = (light.location - influencer.location).length
        influence_radius = sum(influencer.scale) * INFLUENCE_RADIUS_MULTIPLIER  # Average scale defines the radius
        light_sensitivity = sum(light.scale) * LIGHT_SENSITIVITY_MULTIPLIER

        if distance > influence_radius:
            return 0  # Out of range
        
        strength = max(0, (1 - (distance / influence_radius)) * light_sensitivity)

        if influencer.is_erasing:
            strength *= -1

        if DEBUG: alva_log("influence", f"FindInfluencerField._calculate_strength | {light.name} | Distance: {round(distance, 2)}, Influence radius: {round(influence_radius, 2)}, Light sensitivity: {round(light_sensitivity, 2)}, Strength: {round(strength, 2)}")

        return strength


'''
DOCUMENTATION CODE A1:
When an influencer does stuff to a channel's parameter, Sorcerer needs to remember that the next time
this script runs. We need create the following property group to remember it:

This property group is registered to bpy.types.Object as CollectionProperty influencer_list.

    1. The Parameter We Were Operating On (influencer_list.parameter_name). Currently this is
       just something like "intensity" as opposed to "alva_intensity".

    2. The List Of Meshes Influenced (influencer_list.influenced_object_property_group)
        This PropertyGroup is registered to the above PropertyGroup as CollectionProperty 
        influenced_object_property_group. Inside is:

        a. The single fixture/channel the influenced object represents (channel_number).
        b. The currently stored noncolor parameter influence by the owning influencer 
           object (current_influence).
        c. The currently stored color parameter influence by the owning influencer 
           object (current_influence_color).
'''
        

def test_influencers(SENSITIVITY): # Return True for fail, False for pass
    return False


def invert_color(self, value):
    r, g, b = value
    return (1 - r, 1 - g, 1 - b)


def apply_strength(self, parent, value):
    x = parent.float_object_strength
    r, g, b = value
    return (r * x, g * x, b * x)