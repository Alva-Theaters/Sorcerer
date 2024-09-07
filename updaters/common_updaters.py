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
import time
from bpy.props import *

from ..utils.utils import Utils
from ..utils.osc import OSC


class CommonUpdaters:
    @staticmethod
    def controller_ids_updater(self, context):
        """This intuits what mode the user must want the object to be,
           based on what is or isn't typed into the manual selection 
           field. That mode is used by CPVIA when the controller happens 
           to be an object.

           It also is responsible for updating all background properties
           for controllers like labels, channels lists, and others."""
        if not hasattr(self, "str_manual_fixture_selection") or not hasattr(self, "selected_group_enum"):
            return
        
        if self.str_manual_fixture_selection != "":
            self.is_text_not_group = True # Used primarily by UI
            channels_list = Utils.parse_channels(self.str_manual_fixture_selection)

            num_channels = len(channels_list)
            if num_channels > 1:
                new_type = "Stage Object"
            elif num_channels == 1:
                new_type = "Fixture"
            elif num_channels == 0:
                new_type = "Influencer" # If the input text was unintelligible

        else:
            self.is_text_not_group = False
            self.str_group_label = self.selected_group_enum
            if self.selected_group_enum == "Dynamic":
                new_type = "Influencer"
                channels_list = []
            else:
                new_type = "Stage Object"
                item = [item for item in context.scene.scene_group_data if item.name == self.selected_group_enum]
                if item is not None:
                    channels_list = [chan.chan for chan in item[0].channels_list]

        if new_type == "Influencer" and hasattr(self, "float_object_strength"):
            if self.float_object_strength != 1:
                new_type = "Brush"

        if hasattr(self, "object_identities_enum"):
            self.object_identities_enum = new_type

        # Update channels list
        self.list_group_channels.clear()
        for chan in channels_list:
            item = self.list_group_channels.add()
            item.chan = chan

        # "Secret" Backdoor to Service Mode
        if self.str_manual_fixture_selection.lower() == "service mode":
            context.scene.scene_props.service_mode = not context.scene.scene_props.service_mode
            self.str_manual_fixture_selection = ""

            
    @staticmethod
    def group_profile_updater(self, context):
        all_properties = [
            "pan_min", "pan_max", "tilt_min", "tilt_max", "zoom_min", "zoom_max", 
            "gobo_speed_min", "gobo_speed_max", "influence_is_on", "intensity_is_on", 
            "pan_tilt_is_on", "color_is_on", "diffusion_is_on", "strobe_is_on", 
            "zoom_is_on", "iris_is_on", "edge_is_on", "gobo_is_on", "prism_is_on", 
            "str_enable_strobe_argument", "str_disable_strobe_argument", 
            "str_enable_gobo_speed_argument", "str_disable_gobo_speed_argument", 
            "str_gobo_id_argument", "str_gobo_speed_value_argument", 
            "str_enable_prism_argument", "str_disable_prism_argument", "color_profile_enum"
        ]
        toggle_properties = [ 
            "pan_tilt_is_on", "color_is_on", "diffusion_is_on", "strobe_is_on", 
            "zoom_is_on", "iris_is_on", "edge_is_on", "gobo_is_on", "prism_is_on"
        ]

        if self.selected_profile_enum == 'Dynamic': 
            properties = all_properties
            st = context.space_data.type

            if st == 'VIEW_3D' and len(context.selected_objects) > 1:
                for obj in context.selected_objects:
                    if obj != self:
                        CommonUpdaters._update_properties(self, obj, properties)

            elif st == 'NODE_EDITOR' and len(context.selected_nodes) > 1:
                for node in context.selected_nodes:
                    if node != self and node.bl_idname in ['group_controller_type', 'mixer_type']:
                        CommonUpdaters._update_properties(self, node, properties)

            elif st == 'SEQUENCE_EDITOR' and len(context.selected_sequences) > 1:
                for strip in context.selected_sequences:
                    if strip != self and strip.type == 'COLOR':
                        CommonUpdaters._update_properties(self, strip, properties)

        else:
            properties = toggle_properties
            profile = context.scene.scene_group_data.get(self.selected_profile_enum)
            
            if not profile:
                return
            
            CommonUpdaters._update_properties(profile, self, properties)

    def _update_properties(source, target, properties):
        for prop in properties:
            setattr(target, prop, getattr(source, prop))

        # Fire the object type updater so the UI isn't wonkified.
        setattr(target, "str_manual_fixture_selection", getattr(target, "str_manual_fixture_selection"))

        
    @staticmethod
    def solo_updater(self, context):
        from ..cpvia.find import Find
        all_controllers = Find.find_controllers(context.scene)

        for controller in all_controllers:
            if hasattr(controller, 'alva_solo') and controller.alva_solo:
                context.scene.scene_props.has_solos = True
                return

        context.scene.scene_props.has_solos = False

        
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
    def channel_ids_updater(self, context):
        index = context.scene.scene_props.group_data_index
        item = context.scene.scene_group_data[index]

        if item is None:
            return
        
        channels_to_add, channels_to_remove = Utils.parse_channels(context.scene.scene_props.add_channel_ids, remove=True) # returns list of ints
        
        if len(channels_to_add) == 0 and len(channels_to_remove) == 0:
            return
        
        i = 0
        if len(channels_to_add) > 0:
            for channel in channels_to_add:
                # Check if the channel already exists
                if any(ch.chan == channel for ch in item.channels_list):
                    continue
                
                new_channel = item.channels_list.add()
                new_channel.chan = channel
                i += 1
            
        if i == 0 and len(channels_to_remove) == 0:
            return
        
        for channel in channels_to_remove:
            for i, ch in enumerate(item.channels_list):
                if ch.chan == channel:
                    item.channels_list.remove(i)
                    break

        Utils.update_all_controller_channel_lists(context)
             

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
                if len(obj.list_group_channels) == 1:
                    obj_index = obj.list_group_channels[0].chan
                    if obj_index in relevant_channels:
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


    def view3d_cmd_line_updater(self, context):
        original = context.scene.scene_props.view3d_command_line

        if original != "":
            try:
                with_underscores = Utils.add_underscores_to_keywords(original)
                OSC.send_osc_lighting("/eos/cmd", f"{with_underscores} Enter")
            except:
                OSC.send_osc_lighting("/eos/cmd", f"{original} Enter")
            context.scene.scene_props.view3d_command_line = ""
        else:
            OSC.press_lighting_key("enter")


    def network_settings_updater(self, context):
        context.scene.lock_ip_settings = True


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
        '''I still don't know what this does. I see what it's doing but I don't know why it's doing it.'''
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

                text_block = context.space_data.text
                if text_block:
                    text_block.write(f"{selected_macro_button} ")
                    new_cursor_position = text_block.current_character

                    if new_cursor_position < len(text_block.lines[text_block.current_line_index].body):
                        text_block.select_set(new_cursor_position - 1)
                        bpy.ops.text.delete(type='NEXT_CHARACTER')
                        
                        text_block.write(text_block.lines[text_block.current_line_index].body[new_cursor_position - 1])