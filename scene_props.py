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


import bpy
from bpy.props import *
import time
import socket


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


def cone_enum_updater(self,context):
    space = context.space_data.edit_tree.nodes
    if context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
        
    bpy.ops.object.select_all(action='DESELECT')

    obj_to_select = bpy.data.objects.get(context.scene.scene_props.array_cone_enum)

    if obj_to_select:
        context.view_layer.objects.active = obj_to_select
        obj_to_select.select_set(True)
            
    context.scene.scene_props.str_array_group_name = context.scene.scene_props.array_cone_enum
    
    
def get_modifier_items(self, context):
    items = [("NONE", "None", "No array modifiers available")]
    
    obj_name = context.scene.scene_props.array_cone_enum
    obj = bpy.data.objects.get(obj_name)

    if obj:
        for modifier in obj.modifiers:
            if not modifier.name.isdigit():
                items.append((modifier.name, modifier.name, ""))  
    return items


def get_curve_items(self, context):
    items = [("NONE", "None", "No curve modifiers available")]
    obj = context.active_object
    if obj:
        for modifier in obj.modifiers:
            if not modifier.name.isdigit():
                items.append((modifier.name, modifier.name, ""))
    return items


def get_cone_items(self, context):
    items = [("NONE", "None", "No suitable meshes available")]
    for obj in bpy.data.objects:
        if obj:
            if not obj.name.isdigit():
                items.append((obj.name, obj.name, ""))
    return items


def school_mode_password_updater(self, context):
    if self.school_mode_password in ["Halayna Hutchins", "halayana hutchins", "halyana hutchins", "halayana huchins", "halayna huchins", "halayna hutchins", "Halayna hutchins", "halayna Hutchins"]:
        self.school_mode_enabled = not self.school_mode_enabled
        self.school_mode_password = ""


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


def update_light_array(self, context):
    scene = context.scene
    base_light = context.active_object

    if base_light and base_light.type == 'LIGHT':
        address_list = find_addresses(self.int_array_universe, self.int_array_start_address, self.int_array_channel_mode, 300)
        
        collection_name = f"Group {self.int_array_group_index}: {self.str_array_group_name}"

        if collection_name not in bpy.data.collections:
            new_collection = bpy.data.collections.new(name=collection_name)
            scene.collection.children.link(new_collection)
        else:
            new_collection = bpy.data.collections[collection_name]

        scripted_lights = [obj for obj in new_collection.objects if obj.type == 'LIGHT']
        current_quantity = len(scripted_lights)
        desired_quantity = self.int_array_quantity - 1
        
        ip_address = scene.scene_props.str_osc_ip_address
        port = scene.scene_props.int_osc_port
        address = scene.scene_props.str_command_line_address
        
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
                    
                send_osc_string(address, ip_address, port, "Patch Enter")
                time.sleep(.1)
                send_osc_string(address, ip_address, port, f"Chan {new_light_object.name} Type {self.str_array_group_maker} {self.str_array_group_type} Enter, Chan {new_light_object.name} Position {position_x} / {position_y} / {position_z} Enter, Chan {new_light_object.name} Orientation {round(new_light_object.rotation_euler.x)} / {round(new_light_object.rotation_euler.y)} / {round(new_light_object.rotation_euler.z)} Enter, Chan {new_light_object.name} at {str(current_universe)} / {str(current_channel)} Enter")
                        
        elif current_quantity > desired_quantity:
            for light_object in scripted_lights[desired_quantity:]:
                send_osc_string(address, ip_address, port, "Patch Enter")
                time.sleep(.1)
                send_osc_string(address, ip_address, port, f"Delete Chan {light_object.name} Enter Enter")
                bpy.data.objects.remove(light_object, do_unlink=True)
                
        argument = "Chan "       
        if len(new_collection.objects) != 0: 
            for light in new_collection.objects:
                argument += f"{light.name} "
            argument += "Enter"
            send_osc_string(address, ip_address, port, argument)

        
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
                    
                    send_osc_string(address, ip_address, port, "Patch Enter")
                    time.sleep(.1)
                    send_osc_string(address, ip_address, port, f"Chan {light_object.name} Position {position_x} / {position_y} / {position_z} Enter, Chan {light_object.name} Orientation {round(light_object.rotation_euler.x)} / {round(light_object.rotation_euler.y)} / {round(light_object.rotation_euler.z)} Enter")
                    
            argument = "Chan "       
            if len(light_collection.objects) != 0: 
                for light in light_collection.objects:
                    argument += f"{light.name} "
                argument += "Enter"
                send_osc_string(address, ip_address, port, argument)
                send_osc_string("/eos/key/group", ip_address, port, "1")
                send_osc_string("/eos/key/group", ip_address, port, "0")
                send_osc_string("/eos/key/group", ip_address, port, "1")
                send_osc_string("/eos/key/group", ip_address, port, "0")
                time.sleep(.5)
                send_osc_string(address, ip_address, port, f"Group {self.int_array_group_index} Enter, + {argument} Enter Enter")
                send_osc_string(address, ip_address, port, f"Group {self.int_array_group_index} Enter, + {argument} Enter Enter")
                send_osc_string(address, ip_address, port, f"Group {self.int_array_group_index} Enter, + {argument} Enter Enter")
                print(f"Group {self.int_array_group_index} Enter, + {argument}")
                time.sleep(.5)
                send_osc_string(address, ip_address, port, "Patch Enter")
                send_osc_string(address, ip_address, port, "Patch Enter")
                send_osc_string(address, ip_address, port, argument)


class SceneProperties(bpy.types.PropertyGroup):
    str_command_line_address: StringProperty(
        default="/eos/newcmd", description="Write in the address your console uses to denote a command line entry through OSC")
        
    str_channel_template: StringProperty(
        default="Channel *", description="Add any syntax needed to specify channel and use * for channel number")
        
    str_group_template: StringProperty(
        default="Group *", description="Add any syntax needed to specify group and use * for group number")
        
    str_intensity_argument: StringProperty(
        default="# at $ Enter", description="Add $ for animation data and # for fixture/group ID, this is for group and channel controllers")
        
    str_pan_argument: StringProperty(
        default="# Pan at $ Enter", description="Add $ for animation data and # for fixture/group ID, this is for the channel controller only")
        
    str_tilt_argument: StringProperty(
        default="# Tilt at $ Enter", description="Add $ for animation data and # for fixture/group ID, this is for the channel controller only")
        
    str_red_argument: StringProperty(
        default="# Red at $ Enter", description="Add $ for animation data and # for fixture/group ID, this is for group and channel controllers")
        
    str_blue_argument: StringProperty(
        default="# Blue at $ Enter", description="Add $ for animation data and # for fixture/group ID, this is for group and channel controllers")
            
    str_green_argument: StringProperty(
        default="# Green at $ Enter", description="Add $ for animation data and # for fixture/group ID, this is for group and channel controllers")
        
    str_amber_argument: StringProperty(
        default="# Amber at $ Enter", description="Add $ for animation data and # for fixture/group ID, this is for group and channel controllers")
        
    str_white_argument: StringProperty(
        default="# White at $ Enter", description="Add $ for animation data and # for fixture/group ID, this is for group and channel controllers")
        
    str_mint_argument: StringProperty(
        default="# Mint at $ Enter", description="Add $ for animation data and # for fixture/group ID, this is for group and channel controllers")
        
    str_lime_argument: StringProperty(
        default="# Lime at $ Enter", description="Add $ for animation data and # for fixture/group ID, this is for group and channel controllers")
    
    str_cyan_argument: StringProperty(
        default="# Cyan at $ Enter", description="Add $ for animation data and # for fixture/group ID, this is for group and channel controllers")
       
    str_magenta_argument: StringProperty(
        default="# Magenta at $ Enter", description="Add $ for animation data and # for fixture/group ID, this is for group and channel controllers")
       
    str_yellow_argument: StringProperty(
        default="# Yellow at $ Enter", description="Add $ for animation data and # for fixture/group ID, this is for group and channel controllers")
       
    str_diffusion_argument: StringProperty(
        default="# Diffusion at $ Enter", description="Add $ for animation data and # for fixture/group ID, this is for group and channel controllers")
        
    str_strobe_argument: StringProperty(
        default="# Strobe at $ Enter", description="Add $ for animation data and # for fixture/group ID")
        
    str_zoom_argument: StringProperty(
        default="# Zoom at $ Enter", description="Add $ for animation data and # for fixture/group ID, this is for the channel controller only")
        
    str_iris_argument: StringProperty(
        default="# Iris at $ Enter", description="Add $ for animation data and # for fixture/group ID, this is for group and channel controllers")
        
    str_edge_argument: StringProperty(
        default="# Edge at $ Enter", description="Add $ for animation data and # for fixture/group ID, this is for group and channel controllers")
        
    str_gobo_id_argument: StringProperty(
        default="# Gobo_Select at $ Enter", description="Add $ for animation data and # for fixture/group ID, this is for the channel controller only")
        
    str_speed_argument: StringProperty(
        default="# Gobo_Mode 191 Enter, # Gobo_Index/Speed at $ Enter", description="Add $ for animation data and # for fixture/group ID, this is for the channel controller only")
        
    str_changer_speed_argument: StringProperty(
        default="# Changer_Speed at $ Enter", description="Add $ for animation data and # for fixture/group ID, this is for the channel controller only")
        
    bpy.types.Object.str_gobo_speed_value_argument: StringProperty(
        default="# Gobo_Index/Speed at $ Enter", description="Add $ for animation data and # for fixture/group ID")
        
    str_prism_argument: StringProperty(
        default="# Beam_Fx Select $ Enter", description="Add $ for animation data and # for fixture/group ID")
        
    str_misc_effect_argument: StringProperty(
        default="# Misc_Effect at $ Enter", description="Add $ for animation data and # for fixture/group ID")
        
    group_data: StringProperty(name="Group Data")
    
    add_channel_ids: StringProperty(name="Add channel ID's")    
    
    str_osc_ip_address: StringProperty(default="192.168.1.1", description="This should be the IP address of the console. This must set for anything to work. Press the About key on the console to find the console's IP address. Console must be on same local network")
    '''LONE INTEGER'''
    int_osc_port: IntProperty(min=0, max=65535, description="On the console, Displays > Setup > System Settings > Show Control > OSC > (enable OSC RX and make the port number there on the left match the one in this field in Alva. OSC TX = transmit and OSC RX = receive. We want receive", default=8000)
    string_osc_receive_port: IntProperty(min=0, max=65535)
    
    str_record_cue: StringProperty(default="Record Cue # Time $ Enter Enter", description="Write command line syntax for recording cue # with duration $. # and $ are filled in by Alva as cue number and duration, respectively")
    str_create_all_events: StringProperty(default="Event 1 / 1 Thru # Enter", description="Write command line syntax to initialize all events. Alva will replace # with the final event number based on the sequencer's end frame")
    str_setup_event: StringProperty(default="Event 1 / # Time $ Show_Control_Action Cue # Enter", description="Write command line syntax to setup each event. # is frame/cue and $ is timecode")
    str_bake_info: StringProperty(default="Bake Animation to Cues")
    str_event_bake_info: StringProperty(default="Just Events") 
    str_cue_bake_info: StringProperty(default="Just Cues") 
    selected_text_block_name: StringProperty()

    is_playing: BoolProperty(
        default=False, description="Tells updaters when and when not to send their own osc")
        
    is_democratic: BoolProperty(
        default=True, description="This is a democracy. When different controllers try to change the same channel parameter, their Influence parameter gives them votes in a weighted average")
    
    is_not_democratic: BoolProperty(
        default=False, description="This isn't a democracy anymore. When different controllers try to change the same channel parameter, the strongest completely erases everyone else's opinion")

    is_baking: BoolProperty(default=False, description="Alva is currently baking")
    
    is_cue_baking: BoolProperty(default=False, description="Alva is currently baking")
    
    is_event_baking: BoolProperty(default=False, description="Alva is currently baking")
    
    show_presets: BoolProperty(default=False, description="Shows buttons on intensities panel")
    
    color_is_preset_mode: BoolProperty(default=False, description="Show color with just the preset buttons")
    
    color_is_expanded: BoolProperty(default=False, description="Show color with expanded color pickers")  
    
    expand_channel_settings: BoolProperty(default=False, description="View active channel settings")  
    
    expand_prefixes_is_on: BoolProperty(default=False, description="Expand the place to adjust the OSC syntax")
    
    record_settings_is_on: BoolProperty(default=False, description="Dummy property for UI")

    nodes_are_armed: BoolProperty(default=True, description="Make the parameter controller nodes stop transmitting")

    # STRING
    school_mode_password: StringProperty(default="", description="Reduces potential for students or volunteers to break things", update=school_mode_password_updater)

    school_mode_enabled: BoolProperty(default=False, description="Reduces potential for students or volunteers to break things")

    active_controller: IntProperty(
        name="Active Controller",
        description="Index of the active controller",
        default=0,
        min=0
    )        
    pan_min: IntProperty(
        default=-275, 
        min=-500, 
        max=0, 
        description=(
            "Minimum value for pan, this is for the controller "
            "above and is scene-specific, not channel-specific"
        )
    )   
    pan_max: IntProperty(
        default=275, 
        min=0, 
        max=500, 
        description=(
            "Maximum value for pan, this is for the controller"
            " above and is scene-specific, not channel-specific"
        )
    )
    tilt_min: IntProperty(
        default=-135, 
        min=-500, 
        max =0, 
        description=(
            "Minimum value for tilt, this is for the controller "
            "above and is scene-specific, not channel-specific"
        )
    )   
    tilt_max: IntProperty(
        default=135, 
        min=0, 
        max=500, 
        description=(
            "Maximum value for tilt, this is for the controller "
            "above and is scene-specific, not channel-specific"
        )
    )
    strobe_min: IntProperty(
        default=0, 
        description=(
            "Minimum value for strobe, this is for the controller "
            "above and is scene-specific, not channel-specific"
        )
    )    
    strobe_max: IntProperty(
        default=10, 
        description=(
            "Maximum value for strobe, this is for the controller "
            "above and is scene-specific, not channel-specific"
        )
    )
    zoom_min: IntProperty(
        default=10, 
        min=0, 
        max=100, 
        description=(
            "Minimum value for zoom, this is for the controller above and "
            "is scene-specific, not channel-specific"
        )
    )    
    zoom_max: IntProperty(
        default=100, 
        min=15, 
        max=300, 
        description=(
            "Maximum value for zoom, this is for the controller above and "
            "is scene-specific, not channel-specific"
        )
    )
    iris_min: IntProperty(
        default=0, 
        description=(
            "Minimum value for iris, this is for the controller above and "
            "is scene-specific, not channel-specific"
        )
    )    
    iris_max: IntProperty(
        default=100, 
        description=(
            "Maximum value for iris, this is for the controller above and is "
            "scene-specific, not channel-specific"
        )
    )
    edge_min: IntProperty(
        default=0, 
        description=(
            "Minimum value for edge, this is for the controller above and "
            "is scene-specific, not channel-specific"
        )
    )    
    edge_max: IntProperty(
        default=100, 
        description=(
            "Maximum value for edge, this is for the controller above and "
            "is scene-specific, not channel-specific"
        )
    )
    speed_min: IntProperty(
        default=-200, 
        min=-500, 
        max=0, 
        description=(
            "Minimum value for speed, this is for the controller above "
            "and is scene-specific, not channel-specific"
        )
    )    
    speed_max: IntProperty(
        default=200, 
        min=0, 
        max=500, 
        description=(
            "Maximum value for speed, this is for the controller above "
            "and is scene-specific, not channel-specific"
        )
    )
    array_modifier_enum: EnumProperty(
        name="Modifiers",
        description="Choose an Array modifier",
        items=get_modifier_items,
        default=0
    )
    array_curve_enum: EnumProperty(
        name="Curves",
        description="Choose a curve modifier if applicable",
        items=get_curve_items,
        default=0
    )
    array_cone_enum: EnumProperty(
        name="Cones",
        description="You're supposed to make a bunch of cones in 3D View using an Array modifier to represent the group of lights to be patched so that Sorcerer can patch Augment 3D for you",
        items=get_cone_items,
        update=cone_enum_updater,
        default=0
    )

    '''TWO LONE STRINGS'''
    str_group_label_to_add: StringProperty(default="")
    int_group_number_to_add: IntProperty(default=1, min=1, max=9999, description="Index of group as on console")
    str_group_channels_to_add: StringProperty(default="")
    
    int_array_quantity: IntProperty(default=1, min=1, max=999, description="How many lights to add", update=update_light_array)
    float_offset_x: FloatProperty(default=1, min=0, max=100, unit = 'LENGTH', update=update_light_positions)
    float_offset_y: FloatProperty(default=0, min=0, max=100, unit = 'LENGTH', update=update_light_positions)
    float_offset_z: FloatProperty(default=0, min=-1000, max=100, unit = 'LENGTH', update=update_light_positions)

    str_array_group_name: StringProperty(default="", description="Group label on console")
    str_array_group_maker: StringProperty(default="", description="Fixture manufacturer on console")
    str_array_group_type: StringProperty(default="", description="Fixture type on console")
    
    int_array_group_index: IntProperty(default=1, max=9999, description="Group number on console")
    int_array_start_channel: IntProperty(default=1, max=9999, description="Channel number to start at on console")
    
    int_array_universe: IntProperty(default=1, max=9999, description="Universe to start patching to on console")
    int_array_start_address: IntProperty(default=1, max=9999, description="Address to start patching to on console")
    int_array_channel_mode: IntProperty(default=1, max=9999, description="How many channels each fixture needs on console")

    bool_eos_console_mode: BoolProperty(default=False, description="I am using an ETC Eos lighting console")

    str_preset_assignment_argument: StringProperty(
            default=" Group # Record Preset $ Enter Enter", 
            description="Use # for group number and $ for preset number"
    )
    
    selected_mesh_name: StringProperty(default="", description="Select a mesh in 3D view that represents light fixtures")

    selected_array_name: StringProperty(default="", description="Select an array modifier in 3D view that represents a group of light fixtures")

    # Activaters for patch system.
    color_is_on: bpy.props.BoolProperty(default=False, description="Color is enabled when checked")
    diffusion_is_on: bpy.props.BoolProperty(default=False, description="Diffusion is enabled when checked")
    strobe_is_on: bpy.props.BoolProperty(default=False, description="Strobe is enabled when checked")
    zoom_is_on: bpy.props.BoolProperty(default=False, description="Zoom is enabled when checked")
    iris_is_on: bpy.props.BoolProperty(default=False, description="Iris is enabled when checked")
    edge_is_on: bpy.props.BoolProperty(default=False, description="Edge is enabled when checked")
    gobo_id_is_on: bpy.props.BoolProperty(default=False, description="Gobo ID is enabled when checked")
    pan_tilt_is_on: bpy.props.BoolProperty(default=False, description="Pan/Tilt is enabled when checked")


def register():
    bpy.utils.register_class(SceneProperties)
    bpy.types.Scene.scene_props = PointerProperty(type=SceneProperties)
    
    
def unregister():
    del bpy.types.Scene.scene_props
    bpy.utils.unregister_class(SceneProperties)
    

# For development purposes only.
if __name__ == "__main__":
    register()
