# This file is part of Alva ..
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
import time
from bpy.props import *

from ..utils.utils import Utils
from ..utils.osc import OSC


class CommonUpdaters:
    @staticmethod              
    def controller_ids_updater(self, context):
        """This creates property group instances based on the manual 
           text input or group_profile_enum for list_group_channels"""
        if self.str_manual_fixture_selection != "":
            self.is_group_not_manual = True
            channels_list = Utils.parse_channels(self.str_manual_fixture_selection)
        else:
            self.is_group_not_manual = False
            item = [item for item in context.scene.scene_group_data if item.name == self.selected_group_enum]
            channels_list = [chan.chan for chan in item[0].channels_list]
        
        self.list_group_channels.clear()
        
        for chan in channels_list:
            item = self.list_group_channels.add()
            item.chan = chan
            
    @staticmethod
    def group_profile_updater(self, context):
        profile = bpy.context.scene.scene_group_data.get(self.selected_profile_enum)

        # List of properties to update
        properties = [
            "pan_min", "pan_max", "tilt_min", "tilt_max", "zoom_min", "zoom_max", 
            "gobo_speed_min", "gobo_speed_max", "influence_is_on", "intensity_is_on", 
            "pan_tilt_is_on", "color_is_on", "diffusion_is_on", "strobe_is_on", 
            "zoom_is_on", "iris_is_on", "edge_is_on", "gobo_id_is_on", "prism_is_on", 
            "str_enable_strobe_argument", "str_disable_strobe_argument", 
            "str_enable_gobo_speed_argument", "str_disable_gobo_speed_argument", 
            "str_gobo_id_argument", "str_gobo_speed_value_argument", 
            "str_enable_prism_argument", "str_disable_prism_argument", "color_profile_enum"
        ]

        for prop in properties:
            setattr(self, prop, getattr(profile, prop))


    #-------------------------------------------------------------------------------------------------------------------------------------------
    '''PATCH system'''
    #------------------------------------------------------------------------------------------------------------------------------------------- 
    @staticmethod
    def group_name_updater(self, context):
        '''When user adds a new group to Lighting Patch, scene, this ensures unique names.'''
        existing_names = [item.name for item in context.scene.scene_group_data if item != self]

        if self.name in existing_names:
            base_name = self.name
            suffix = 1
            
            new_name = f"{base_name}.{suffix:03}"
            while new_name in existing_names:
                suffix += 1
                new_name = f"{base_name}.{suffix:03}"
            self.name = new_name
            
    @staticmethod
    def ui_list_separator_updater(self, context):
        if self.separator and self.label:
            self.label = False
            
    @staticmethod
    def ui_list_label_updater(self, context):
        if self.separator and self.label:
            self.separator = False
            
            
    @staticmethod
    def sound_source_updater(self, context):
        '''Keeps the enum on the object controller synced with that on 
           the sound strip. Ensures that an object does not point to a 
           sound strip that isn't pointing back'''
        space_type = context.space_data.type
        
        if space_type == 'VIEW_3D' and self.type == 'MESH':
            strip = context.scene.sequence_editor.sequences_all.get(self.sound_source_enum)
            if strip:
                strip.selected_stage_object = self

        elif space_type == 'SEQUENCE_EDITOR' and self.type == 'SOUND':
            mesh = self.selected_stage_object
            if mesh:
                mesh.sound_source_enum = self.name
             

    @staticmethod    
    def highlight_mode_updater(self, context):
        '''Main logic for Patch's highlight system.'''
        scene = context.scene.scene_props
        
        try:
            item = context.scene.scene_group_data[scene.group_data_index]
        except:
            return
        
        # Clear any existing highlighted group
        if scene.string_highlight_memory != "":
            OSC.send_osc_lighting("/eos/newcmd", f"Chan {scene.string_highlight_memory} Out")
        
        # Clear scene selection so we can leave only the correct objects selected
        bpy.ops.object.select_all(action='DESELECT')
        
        if scene.highlight_mode:
            relevant_channels = [channel.chan for channel in item.channels_list]
            relevant_objects = []
            for obj in bpy.data.objects:
                obj_index = obj.int_fixture_index
                obj_name_as_int = Utils.try_parse_int(obj.name)
                
                if obj_index in relevant_channels or (obj_name_as_int is not None and obj_name_as_int in relevant_channels):
                    relevant_objects.append(obj)
                    
            # Create a string of relevant channels separated by commas
            channels_list = " + ".join(map(str, relevant_channels))
            OSC.send_osc_lighting("/eos/newcmd", f"Chan {channels_list} at {scene.int_highlight_value} Sneak Time {scene.float_highlight_time} Enter")
            
            for obj in relevant_objects:
                obj.select_set(True)
                
            # Allow this to be undone later
            scene.string_highlight_memory = channels_list
    
    
    def call_fixtures_updater(self, context):
        bpy.ops.viewport.call_fixtures_operator()


    def update_light_array(self, context):
        scene = context.scene
        base_light = context.active_object

        if base_light and base_light.type == 'LIGHT':
            address_list = Utils.find_addresses(self.int_array_universe, self.int_array_start_address, self.int_array_channel_mode, 300)
            
            collection_name = f"Group {self.int_array_group_index}: {self.str_array_group_name}"

            if collection_name not in bpy.data.collections:
                new_collection = bpy.data.collections.new(name=collection_name)
                scene.collection.children.link(new_collection)
            else:
                new_collection = bpy.data.collections[collection_name]

            scripted_lights = [obj for obj in new_collection.objects if obj.type == 'LIGHT']
            current_quantity = len(scripted_lights)
            desired_quantity = self.int_array_quantity - 1
            
            address = "/eos/newcmd"
            
            if current_quantity < desired_quantity:
                for i, (current_universe, current_channel) in enumerate(address_list[current_quantity:desired_quantity], start=current_quantity + 1):
                    str_calculated_name = str(i + 1 + self.int_array_start_channel)
                    new_light_data = bpy.data.lights.new(name=str_calculated_name, type=base_light.data.type)
                    new_light_object = bpy.data.objects.new(name=str_calculated_name, object_data=new_light_data)
                    new_collection.objects.link(new_light_object)
                    new_light_object.location = (
                        base_light.location.x + self.float_offset_x * i,
                        base_light.location.y + self.float_offset_y * i,
                        base_light.location.z + self.float_offset_z * i,
                    )
                    
                    new_light_object.scale = base_light.scale

                    position_x = round(new_light_object.location.x / .3048)
                    position_y = round(new_light_object.location.y / .3048)
                    position_z = round(new_light_object.location.z / .3048)
                        
                    OSC.send_osc_lighting(address, "Patch Enter")
                    time.sleep(.1)
                    OSC.send_osc_lighting(address, f"Chan {new_light_object.name} Type {self.str_array_group_maker} {self.str_array_group_type} Enter, Chan {new_light_object.name} Position {position_x} / {position_y} / {position_z} Enter, Chan {new_light_object.name} Orientation {round(new_light_object.rotation_euler.x)} / {round(new_light_object.rotation_euler.y)} / {round(new_light_object.rotation_euler.z)} Enter, Chan {new_light_object.name} at {str(current_universe)} / {str(current_channel)} Enter")
                            
            elif current_quantity > desired_quantity:
                for light_object in scripted_lights[desired_quantity:]:
                    OSC.send_osc_lighting(address, "Patch Enter")
                    time.sleep(.1)
                    OSC.send_osc_lighting(address, f"Delete Chan {light_object.name} Enter Enter")
                    bpy.data.objects.remove(light_object, do_unlink=True)
                    
            argument = "Chan "       
            if len(new_collection.objects) != 0: 
                for light in new_collection.objects:
                    argument += f"{light.name} "
                argument += "Enter"
                OSC.send_osc_lighting(address, argument)

            
    def update_light_positions(self, context):
        base_light = context.active_object
        if base_light and base_light.type == 'LIGHT':
            collection_name = f"Group {self.int_array_group_index}: {self.str_array_group_name}"

            if collection_name in bpy.data.collections:
                scene = context.scene
                ip_address = scene.scene_props.str_osc_ip_address
                port = scene.scene_props.int_osc_port
                address = scene.scene_props.str_command_line_address
                light_collection = bpy.data.collections[collection_name]
                
                for i, light_object in enumerate(light_collection.objects):
                    if light_object.type == 'LIGHT':
                        # Calculate the new position based on the base light and offsets
                        new_position = (
                            base_light.location.x + self.float_offset_x * i,
                            base_light.location.y + self.float_offset_y * i,
                            base_light.location.z + self.float_offset_z * i,
                        )

                        # Update the light object's position
                        light_object.location = new_position
                        
                        position_x = round(light_object.location.x / .3048)
                        position_y = round(light_object.location.y / .3048)
                        position_z = round(light_object.location.z / .3048)
                        
                        OSC.send_osc_lighting(address, "Patch Enter")
                        time.sleep(.1)
                        OSC.send_osc_lighting(address, f"Chan {light_object.name} Position {position_x} / {position_y} / {position_z} Enter, Chan {light_object.name} Orientation {round(light_object.rotation_euler.x)} / {round(light_object.rotation_euler.y)} / {round(light_object.rotation_euler.z)} Enter")
                        
                argument = "Chan "       
                if len(light_collection.objects) != 0: 
                    for light in light_collection.objects:
                        argument += f"{light.name} "
                    argument += "Enter"
                    OSC.send_osc_lighting(address, argument)
                    OSC.send_osc_lighting("/eos/key/group", "1")
                    OSC.send_osc_lighting("/eos/key/group", "0")
                    OSC.send_osc_lighting("/eos/key/group", "1")
                    OSC.send_osc_lighting("/eos/key/group", "0")
                    time.sleep(.5)
                    OSC.send_osc_lighting(address, f"Group {self.int_array_group_index} Enter, + {argument} Enter Enter")
                    OSC.send_osc_lighting(address, f"Group {self.int_array_group_index} Enter, + {argument} Enter Enter")
                    OSC.send_osc_lighting(address, f"Group {self.int_array_group_index} Enter, + {argument} Enter Enter")
                    time.sleep(.5)
                    OSC.send_osc_lighting(address, "Patch Enter")
                    OSC.send_osc_lighting(address, "Patch Enter")
                    OSC.send_osc_lighting(address, argument)
                    
    @staticmethod
    def cone_enum_updater(self,context):
        '''IDK. Something about Patch Generator I think???'''
        space = context.space_data.edit_tree.nodes
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
            
        bpy.ops.object.select_all(action='DESELECT')

        obj_to_select = bpy.data.objects.get(context.scene.scene_props.array_cone_enum)

        if obj_to_select:
            context.view_layer.objects.active = obj_to_select
            obj_to_select.select_set(True)
                
        context.scene.scene_props.str_array_group_name = context.scene.scene_props.array_cone_enum


    #-------------------------------------------------------------------------------------------------------------------------------------------
    '''SETTINGS'''
    #-------------------------------------------------------------------------------------------------------------------------------------------     
    @staticmethod        
    def school_mode_password_updater(self, context):
        '''Checks password on text field update. If correct, it 
           toggles state of school_mode and clears the text field.'''
        if self.school_mode_password.lower() in ["password123", "password 123"]:
            self.school_mode_enabled = not self.school_mode_enabled  # toggle state
            self.school_mode_password = ""  # Clear password field


    #-------------------------------------------------------------------------------------------------------------------------------------------
    '''TEXT'''
    #-------------------------------------------------------------------------------------------------------------------------------------------  
    @staticmethod
    def update_macro_buttons_index(self, context):
        if context.area.type == 'TEXT_EDITOR':
            selected_index = context.scene.macro_buttons_index
            if 0 <= selected_index < len(context.scene.macro_buttons):
                selected_macro_button = context.scene.macro_buttons[selected_index].name
                context.window_manager.clipboard = f" {selected_macro_button} "