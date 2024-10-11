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


import bpy
from mathutils import Vector
import time

from ..assets.dictionaries import Dictionaries 
from ..cpvia.map import Mapping 
from ..cpvia.cpvia_finders import CPVIAFinders 
from ..assets.sli import SLI 
from ..utils.cpvia_utils import color_object_to_tuple_and_scale_up
from ..maintenance.logging import alva_log


class Influencers:  
    def find_my_influencer_values(self, parent, p, type):
        """Receives a bpy object mesh (parent), parameter, and controller_type, and returns three lists for channels list (c), parameters list, and values list (v)"""
        start = time.time()

        attribute_name = Dictionaries.parameter_mapping.get(p)
        if attribute_name:  # Find and map value
            new_value = getattr(parent, attribute_name)
            new_value_for_raise = new_value
            
            if p == 'color':
                restore_value = getattr(parent, "float_vec_color_restore")
            
            current_channels = self.find_influencer_current_channels(parent)
            mapping = Mapping()
            true_parent = bpy.data.objects[parent.name]
            influencer_list = self.get_list_by_parameter(true_parent, p)
            raise_channels = influencer_list.raise_channels
            old_channels = set(chan.chan for chan in raise_channels)
            new_channels = set()
            c = []
            param = []
            v = []

            if parent.alva_is_absolute:
                new_channels = current_channels | old_channels
                raise_prefix = ""
            else:
                new_channels = current_channels - old_channels
                raise_prefix = "raise_"

            # Release
            if type == "Influencer":
                for chan in list(raise_channels):
                    if chan.chan not in current_channels:
                        channel = []
                        cpvia_finders = CPVIAFinders()
                        channel = cpvia_finders.find_channel_number(chan.chan)
                        c.append(channel)
                        param.append(p)
                        if p == "color":
                            if not parent.is_erasing:
                                new_release_value = color_object_to_tuple_and_scale_up(restore_value)
                            else: new_release_value = color_object_to_tuple_and_scale_up(new_value)
                            v.append(new_release_value)
                        else: v.append(chan.original_influence * -1)
                    
            raise_channels.clear()
            
            # Raise
            for chan in new_channels:
                # Append Channel
                cpvia_finders = CPVIAFinders()
                channel = cpvia_finders.find_channel_number(chan)
                c.append(channel)
                
                # Append Parameter. 
                # Don't mess with this block unless you know exactly what you're doing.
                if type == "Brush":
                    param.append(f"{raise_prefix}{p}")
                elif type == "Influencer" and p != "color":
                    param.append(f"{raise_prefix}{p}")
                else: param.append(p)
                
                # Append Value
                if p in ["pan", "tilt", "zoom", "gobo_speed"]:
                    value_to_add = mapping.map_value(parent, channel, p, new_value, type)
                    v.append(value_to_add)
                else:
                    if p == "color":
                        if not parent.is_erasing:
                            new_raise_value = new_value_for_raise
                        else: new_raise_value = restore_value
                        
                        if type == "Brush":
                            if parent.is_erasing:
                                new_raise_value = (1, 1, 1)
                            new_raise_value = self.invert_color(new_raise_value)
                        new_raise_value = color_object_to_tuple_and_scale_up(new_raise_value)  
                        new_raise_value = self.apply_strength(parent, new_raise_value)
                        if type == "Brush" and p == "color":
                            r, g, b = new_raise_value
                            if r == 0:
                                r = -100 * parent.float_object_strength
                            if g == 0:
                                g = -100 * parent.float_object_strength
                            if b == 0:
                                b = -100 * parent.float_object_strength
                            new_raise_value = (r * -1, g * -1, b * -1)
                        v.append(new_raise_value)
                    else:
                        if type == "Brush":
                            new_value_for_raise *= parent.float_object_strength
                            if parent.is_erasing:
                                v.append(new_value_for_raise * -1)
                            else: v.append(new_value_for_raise)
                        else: v.append(new_value_for_raise)

            for chan in current_channels:
                new_channel = raise_channels.add()
                new_channel.chan = chan
                if p != "color":
                    new_channel.original_influence = new_value

            alva_log('time', f"find_my_influencer_values took {time.time() - start} seconds")
            return c, param, v
        
        else:
            SLI.SLI_assert_unreachable()
            
            
    def is_torus(self, mesh):
        # Analyze the bounding box dimensions
        bbox = mesh.bound_box
        dims = [Vector(bbox[i]) - Vector(bbox[i + 4]) for i in range(4)]
        dims = [dim.length for dim in dims]

        # Check if the dimensions are roughly equal (more like a sphere/torus) or significantly different (more like a cube)
        threshold = 0.1  # Adjust this threshold as needed
        if all(abs(dims[i] - dims[j]) < threshold for i in range(4) for j in range(i + 1, 4)):
            print("Is torus")
            return True
        print("Is not torus")
        return False
        

    def is_inside_mesh(self, obj, controller, bbox_min, bbox_max):
        #torus = is_torus(mesh_obj)
        #torus = False
        
        #if not torus:
        # Transform the object's location into the mesh object's local space.
        obj_loc_local = controller.matrix_world.inverted() @ obj.location
        inside = all(bbox_min[i] <= obj_loc_local[i] <= bbox_max[i] for i in range(3))
        return inside
        
    #        else:
    #            depsgraph = bpy.context.evaluated_depsgraph_get()
    #            evaluated_obj = mesh_obj.evaluated_get(depsgraph)

    #            # Ensure the evaluated object has mesh data
    #            if not evaluated_obj or not evaluated_obj.data or not hasattr(evaluated_obj.data, 'polygons'):
    #                print(f"Error: Object '{mesh_obj.name}' has no evaluated mesh data.")
    #                return False

    #            # Transform the object's location into the mesh object's local space
    #            obj_loc_local = evaluated_obj.matrix_world.inverted() @ obj.location

    #            # Find the closest point on the mesh
    #            success, closest, normal, _ = evaluated_obj.closest_point_on_mesh(obj_loc_local)
    #            
    #            if not success:
    #                return False

    #            # Determine if the point is inside the mesh
    #            direction = closest - obj_loc_local
    #            inside = direction.dot(normal) > 0

    #            return inside
            
            
    def find_my_restore_values(self, channels_to_restore, p, context):
        restore_values = []
        for chan in channels_to_restore:
            attribute_name = f"prev_{p}"
            if hasattr(chan, attribute_name):
                restore_values.append(getattr(chan, attribute_name))
            else:
                restore_values.append(0 if p != "color" else (0, 0, 0))
        return restore_values
        
        
    def find_influencer_current_channels(self, parent):
        """Receives a bpy object mesh, parent, and returns a set representing channels within that mesh"""
        start = time.time()

        # Get the local bounding box corners of the mesh object.
        bbox_corners_local = [Vector(corner) for corner in parent.bound_box]

        # Calculate the min and max bounding box corners in local space.
        bbox_min = Vector((min(corner.x for corner in bbox_corners_local),
                            min(corner.y for corner in bbox_corners_local),
                            min(corner.z for corner in bbox_corners_local)))
        bbox_max = Vector((max(corner.x for corner in bbox_corners_local),
                            max(corner.y for corner in bbox_corners_local),
                            max(corner.z for corner in bbox_corners_local)))
        
        lights_inside = {obj for obj in bpy.data.objects if obj.type == 'MESH' and not obj.hide_viewport and len(obj.list_group_channels) == 1 and self.is_inside_mesh(obj, parent, bbox_min, bbox_max)}
        lights_inside = {obj for obj in lights_inside if obj.name != parent.name}
        alva_log('time', f"find_influencer_current_channels took {time.time() - start} seconds")
        return lights_inside

        
    def get_list_by_parameter(self, parent, parameter):
        """Returns existing CollectionProperty item of correct type or makes a new one if none is found."""
        for inf_list in parent.influencer_list:
            if inf_list.parameter == parameter:
                return inf_list
        new_list = parent.influencer_list.add()
        new_list.parameter = parameter
        return new_list


    def invert_color(self, value):
        r, g, b = value
        return (1 - r, 1 - g, 1 - b)


    def apply_strength(self, parent, value):
        x = parent.float_object_strength
        r, g, b = value
        return (r * x, g * x, b * x)
    

def test_influencers(SENSITIVITY): # Return True for fail, False for pass
    return False