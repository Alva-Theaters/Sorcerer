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


## Double hashtag indicates notes for future development requiring some level of attention


import bpy
import socket
from bpy.types import Operator, Menu, NodeSocket
from bpy.props import *
import os
import bpy.utils.previews
from nodeitems_utils import NodeCategory, NodeItem, register_node_categories, unregister_node_categories
import inspect


# Purpose of this throughout the codebase is to proactively identify possible pre-bugs and to help diagnose bugs.
def sorcerer_assert_unreachable(*args):
    caller_frame = inspect.currentframe().f_back
    caller_file = caller_frame.f_code.co_filename
    caller_line = caller_frame.f_lineno
    message = "Error found at {}:{}\nCode marked as unreachable has been executed. Please report bug to Alva Theaters.".format(caller_file, caller_line)
    print(message)


preview_collections = {}


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


class CustomButtonPropertyGroup(bpy.types.PropertyGroup):
    button_label: bpy.props.StringProperty(name="Label", default="Button Label")
    button_address: bpy.props.StringProperty(default="/eos/newcmd", description="OSC Address")
    button_argument: bpy.props.StringProperty(default="Go_to_Cue Out Enter", description="OSC Argument")

    
class OvenNode(bpy.types.Node):
    bl_idname = 'oven_type'
    bl_label = 'Qmeo Node'
    bl_icon = 'FILE_MOVIE'
    bl_width_default = 500
    bl_description="Create Qmeos to store complex animation data directly on the console. Qmeos are like videos, but each frame is a lighting cue"

    def init(self, context):
        return

    def draw_buttons(self, context, layout):
        pcoll = preview_collections["main"]
        orb = pcoll["orb"]
        
        scene = context.scene.scene_props
        column = layout.column(align=True)  
        
        split = column.split(factor=1)
        row = split.column()
        row.label(text="Tooltips available on hover. Insert # for cue number and")
        
        split = column.split(factor=1)
        row = split.column()
        row.label(text="$ for cue duration or timecode. To be autofilled by Alva.")
        
        column.separator()
        column.separator()
        
        split = column.split(factor=.25)
        row = split.column()
        row.label(text="Record Cue:")
        row = split.column()
        row.prop(scene, "str_record_cue", text="")
        
        column.separator()
        
        split = column.split(factor=.25)
        row = split.column()
        row.label(text="Create Events:")
        row = split.column()
        row.prop(scene, "str_create_all_events", text="")
        
        column.separator()
        
        split = column.split(factor=.25)
        row = split.column()
        row.label(text="Setup Events:")
        row = split.column()
        row.prop(scene, "str_setup_event", text="")
        
        column.separator()
        column.separator()
        column.separator()
        
        split = column.split(factor=1)
        row = split.column()
        if scene.is_baking:
            row.alert = 1
        row.operator("my.bake_animation_operator", text=scene.str_bake_info, icon_value=orb.icon_id)
        row.alert = 0
        split = column.split(factor=.5)
        row = split.column()
        
        row.separator()
        
        if scene.is_cue_baking:
            row.alert = 1
        row.operator("my.just_cues_operator", text=scene.str_cue_bake_info, icon_value=orb.icon_id)
        row.alert = 0
        
        row = split.column()
        
        row.separator()
        
        if scene.is_event_baking:
            row.alert = 1
        row.operator("my.just_events_operator", text=scene.str_event_bake_info, icon_value=orb.icon_id)
        row.alert = 0
        
        column.separator()
        
        
def draw_arm_nodes(self, context):
    layout = self.layout
    scene = context.scene.scene_props
    
    pcoll = preview_collections["main"]
    orb = pcoll["orb"]
    layout.operator("nodes.show_node_settings", text="", icon_value=orb.icon_id, emboss=False)
    if scene.nodes_are_armed:
        layout.alert = 1
    layout.prop(scene, "nodes_are_armed", text="Arm Nodes", toggle=True)
    layout.alert = 0
          
        
class SettingsNode(bpy.types.Node):
    bl_idname = 'settings_type'
    bl_label = 'Settings Node'
    bl_icon = 'PREFERENCES'
    bl_width_default = 400
    bl_description="Sorcerer node settings"

    def init(self, context):
        return

    def draw_buttons(self, context, layout):
        scene = context.scene.scene_props
        column = layout.column(align=True)
        
        if not scene.school_mode_enabled:
## Simply do not have the time to fix democratic mode. Color and influencers both have isssues in democratic mode.
#            row = column.row()
#            row.label(text="Harmonizer Settings:")
#            
#            row = column.row()
#            if scene.is_democratic:
#                row.alert = 1
#            row.operator("my.democratic_operator", text="Democratic", icon='HEART')
#            row.alert = 0
#            if scene.is_not_democratic:
#                row.alert = 1
#            row.operator("my.non_democratic_operator", text="Non-democratic", icon='ORPHAN_DATA')
#            row.alert = 0
#            
#            column.separator()
#            column.separator()
            
            box = column.box()
            row = box.row()
            row.label(text="Lighting Console OSC RX (Receive) Settings:")
            box = column.box()
            row = box.row()
            row.prop(scene, "str_osc_ip_address", text="IP Address")
            row = box.row()
            row.label(text="Port:")
            row.prop(scene, "int_osc_port", text="")
            
            column.separator()
            
            row = column.row()
            row.prop(scene, "bool_eos_console_mode", text="Eos Console Mode", toggle=False)
            row.label(text="")
            
            column.separator()
        
        row = column.row()
        if scene.school_mode_enabled:
            row.label(text="Disable school mode:", icon='LOCKED')
        else:
            row.label(text="Enable school mode:", icon='UNLOCKED')
            
        row = column.row()
        row.prop(scene, "school_mode_password", text="")
        column.separator()
        
        if not scene.school_mode_enabled: 
            column.separator()
            layout.separator()
            
            box = column.box()  
            row = box.row()

            row.prop(scene, "expand_prefixes_is_on", icon="TRIA_DOWN" if scene.expand_prefixes_is_on else "TRIA_RIGHT", icon_only=True, emboss=False)

            row.label(text="OSC Syntax Templates")      
            
            if scene.expand_prefixes_is_on:
                box = column.box()

                row = box.row()
                row.label(text="Command Line Address:")
                row = box.row()
                row.prop(scene, "str_command_line_address", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Channel Template:")
                row = box.row()
                row.prop(scene, "str_channel_template", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Group Template:")
                row = box.row()
                row.prop(scene, "str_group_template", text = "")
                
                box.separator()
                box.separator()
                box.separator()
                
                row = box.row()
                row.label(text="Intensity Argument:", icon='OUTLINER_OB_LIGHT')
                row = box.row()
                row.prop(scene, "str_intensity_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Strobe Argument:", icon='OUTLINER_OB_LIGHTPROBE')
                row = box.row()
                row.prop(scene, "str_strobe_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Pan Argument:", icon='ORIENTATION_GIMBAL')
                row = box.row()
                row.prop(scene, "str_pan_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Tilt Argument:", icon='ORIENTATION_GIMBAL')
                row = box.row()
                row.prop(scene, "str_tilt_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Red Argument:", icon='COLORSET_01_VEC')
                row = box.row()
                row.prop(scene, "str_red_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Blue Argument:", icon='COLORSET_04_VEC')
                row = box.row()
                row.prop(scene, "str_blue_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Green Argument:", icon='COLORSET_03_VEC')
                row = box.row()
                row.prop(scene, "str_green_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Amber Argument:", icon='COLORSET_02_VEC')
                row = box.row()
                row.prop(scene, "str_amber_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="White Argument:", icon='COLORSET_13_VEC')
                row = box.row()
                row.prop(scene, "str_white_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Mint Argument:", icon='COLORSET_07_VEC')
                row = box.row()
                row.prop(scene, "str_mint_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Lime Argument:", icon='COLORSET_12_VEC')
                row = box.row()
                row.prop(scene, "str_lime_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Zoom Argument:", icon='LINCURVE')
                row = box.row()
                row.prop(scene, "str_zoom_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Iris Argument:", icon='MESH_CIRCLE')
                row = box.row()
                row.prop(scene, "str_iris_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Edge Argument:", icon='SELECT_SET')
                row = box.row()
                row.prop(scene, "str_edge_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Diffusion Argument:", icon='MOD_CLOTH')
                row = box.row()
                row.prop(scene, "str_diffusion_argument", text = "")
                
        
class PresetsNode(bpy.types.Node):
    bl_idname = 'presets_type'
    bl_label = 'Presets Node'
    bl_icon = 'LIGHTPROBE_GRID'
    bl_width_default = 1200
    bl_description="Record and recall console presets"
    
    color_argument_template: bpy.props.StringProperty(default="Group # Color_Palette $ Enter", description="Write the OSC syntax your console expects for recalling color palettes. Insert # for group number and $ for color palette number.")
    preset_argument_template: bpy.props.StringProperty(default="Group # Preset $ Enter", description="Write the OSC syntax your console expects for recalling presets. Insert # for group number and $ for color palette number.")
    record_color_argument_template: bpy.props.StringProperty(default="Group # Record Color_Palette $ Enter", description="Write the OSC syntax your console expects for recording color palettes. Insert # for group number and $ for color palette number.")
    record_preset_argument_template: bpy.props.StringProperty(default="Group # Record Preset $ Enter", description="Write the OSC syntax your console expects for recording presets. Insert # for group number and $ for color palette number.")

    expand_settings: bpy.props.BoolProperty(default=False, description="Settings")
    is_recording: bpy.props.BoolProperty(default=False, description="Recording")
    
    index_offset: bpy.props.IntProperty(default=0, description="Start button index here")

    def init(self, context):
        return

    def draw_buttons(self, context, layout):
        scene = context.scene
        column = layout.column(align=True)
        
        row = column.row()

        world = scene.world

        if world is not None and world.node_tree:
            node_tree = world.node_tree

            for controller in node_tree.nodes:
                if controller.bl_idname == 'group_controller_type':
                    box = column.box()
                    row = box.row(align=True)
                    row.label(text=f"{controller.str_group_id}: {controller.str_group_label}")

                    row.prop(self, "is_recording", text="", icon='REC')
                    
                    if self.is_recording:
                        row.alert = 1
 
                    op = row.operator("my.color_one", text="", icon='COLORSET_01_VEC')
                    op.color_argument_template = self.color_argument_template
                    op.record_color_argument_template = self.record_color_argument_template
                    op.index_offset = self.index_offset
                    op.group_id = controller.str_group_id
                    op.is_recording = self.is_recording

                    op = row.operator("my.color_two", text="", icon='COLORSET_02_VEC')
                    op.color_argument_template = self.color_argument_template
                    op.record_color_argument_template = self.record_color_argument_template
                    op.index_offset = self.index_offset
                    op.group_id = controller.str_group_id
                    op.is_recording = self.is_recording

                    op = row.operator("my.color_three", text="", icon='COLORSET_03_VEC')
                    op.color_argument_template = self.color_argument_template
                    op.record_color_argument_template = self.record_color_argument_template
                    op.index_offset = self.index_offset
                    op.group_id = controller.str_group_id
                    op.is_recording = self.is_recording

                    op = row.operator("my.color_four", text="", icon='COLORSET_04_VEC')
                    op.color_argument_template = self.color_argument_template
                    op.record_color_argument_template = self.record_color_argument_template
                    op.index_offset = self.index_offset
                    op.group_id = controller.str_group_id
                    op.is_recording = self.is_recording

                    op = row.operator("my.color_five", text="", icon='COLORSET_05_VEC')
                    op.color_argument_template = self.color_argument_template
                    op.record_color_argument_template = self.record_color_argument_template
                    op.index_offset = self.index_offset
                    op.group_id = controller.str_group_id
                    op.is_recording = self.is_recording

                    op = row.operator("my.color_six", text="", icon='COLORSET_06_VEC')
                    op.color_argument_template = self.color_argument_template
                    op.record_color_argument_template = self.record_color_argument_template
                    op.index_offset = self.index_offset
                    op.group_id = controller.str_group_id
                    op.is_recording = self.is_recording

                    op = row.operator("my.color_seven", text="", icon='COLORSET_07_VEC')
                    op.color_argument_template = self.color_argument_template
                    op.record_color_argument_template = self.record_color_argument_template
                    op.index_offset = self.index_offset
                    op.group_id = controller.str_group_id
                    op.is_recording = self.is_recording

                    op = row.operator("my.color_eight", text="", icon='COLORSET_08_VEC')
                    op.color_argument_template = self.color_argument_template
                    op.record_color_argument_template = self.record_color_argument_template
                    op.index_offset = self.index_offset
                    op.group_id = controller.str_group_id
                    op.is_recording = self.is_recording

                    op = row.operator("my.color_nine", text="", icon='COLORSET_09_VEC')
                    op.color_argument_template = self.color_argument_template
                    op.record_color_argument_template = self.record_color_argument_template
                    op.index_offset = self.index_offset
                    op.group_id = controller.str_group_id
                    op.is_recording = self.is_recording

                    op = row.operator("my.color_ten", text="", icon='COLORSET_11_VEC')
                    op.color_argument_template = self.color_argument_template
                    op.record_color_argument_template = self.record_color_argument_template
                    op.index_offset = self.index_offset
                    op.group_id = controller.str_group_id
                    op.is_recording = self.is_recording

                    op = row.operator("my.color_eleven", text="", icon='COLORSET_12_VEC')
                    op.color_argument_template = self.color_argument_template
                    op.record_color_argument_template = self.record_color_argument_template
                    op.index_offset = self.index_offset
                    op.group_id = controller.str_group_id
                    op.is_recording = self.is_recording

                    op = row.operator("my.color_twelve", text="", icon='COLORSET_13_VEC')
                    op.color_argument_template = self.color_argument_template
                    op.record_color_argument_template = self.record_color_argument_template
                    op.index_offset = self.index_offset
                    op.group_id = controller.str_group_id
                    op.is_recording = self.is_recording

                    op = row.operator("my.color_thirteen", text="", icon='COLORSET_14_VEC')
                    op.color_argument_template = self.color_argument_template
                    op.record_color_argument_template = self.record_color_argument_template
                    op.index_offset = self.index_offset
                    op.group_id = controller.str_group_id
                    op.is_recording = self.is_recording

                    op = row.operator("my.color_fourteen", text="", icon='COLORSET_15_VEC')
                    op.color_argument_template = self.color_argument_template
                    op.record_color_argument_template = self.record_color_argument_template
                    op.index_offset = self.index_offset
                    op.group_id = controller.str_group_id
                    op.is_recording = self.is_recording

                    op = row.operator("my.f_one", text="", icon='EVENT_F1')
                    op.preset_argument_template = self.preset_argument_template
                    op.record_preset_argument_template = self.record_preset_argument_template
                    op.index_offset = self.index_offset
                    op.group_id = controller.str_group_id
                    op.is_recording = self.is_recording

                    op = row.operator("my.f_two", text="", icon='EVENT_F2')
                    op.preset_argument_template = self.preset_argument_template
                    op.record_preset_argument_template = self.record_preset_argument_template
                    op.index_offset = self.index_offset
                    op.group_id = controller.str_group_id
                    op.is_recording = self.is_recording

                    op = row.operator("my.f_three", text="", icon='EVENT_F3')
                    op.preset_argument_template = self.preset_argument_template
                    op.record_preset_argument_template = self.record_preset_argument_template
                    op.index_offset = self.index_offset
                    op.group_id = controller.str_group_id
                    op.is_recording = self.is_recording

                    op = row.operator("my.f_four", text="", icon='EVENT_F4')
                    op.preset_argument_template = self.preset_argument_template
                    op.record_preset_argument_template = self.record_preset_argument_template
                    op.index_offset = self.index_offset
                    op.group_id = controller.str_group_id
                    op.is_recording = self.is_recording

                    op = row.operator("my.f_five", text="", icon='EVENT_F5')
                    op.preset_argument_template = self.preset_argument_template
                    op.record_preset_argument_template = self.record_preset_argument_template
                    op.index_offset = self.index_offset
                    op.group_id = controller.str_group_id
                    op.is_recording = self.is_recording

                    op = row.operator("my.f_six", text="", icon='EVENT_F6')
                    op.preset_argument_template = self.preset_argument_template
                    op.record_preset_argument_template = self.record_preset_argument_template
                    op.index_offset = self.index_offset
                    op.group_id = controller.str_group_id
                    op.is_recording = self.is_recording

                    op = row.operator("my.f_seven", text="", icon='EVENT_F7')
                    op.preset_argument_template = self.preset_argument_template
                    op.record_preset_argument_template = self.record_preset_argument_template
                    op.index_offset = self.index_offset
                    op.group_id = controller.str_group_id
                    op.is_recording = self.is_recording

                    op = row.operator("my.f_eight", text="", icon='EVENT_F8')
                    op.preset_argument_template = self.preset_argument_template
                    op.record_preset_argument_template = self.record_preset_argument_template
                    op.index_offset = self.index_offset
                    op.group_id = controller.str_group_id
                    op.is_recording = self.is_recording

                    op = row.operator("my.f_nine", text="", icon='EVENT_F9')
                    op.preset_argument_template = self.preset_argument_template
                    op.record_preset_argument_template = self.record_preset_argument_template
                    op.index_offset = self.index_offset
                    op.group_id = controller.str_group_id
                    op.is_recording = self.is_recording

                    op = row.operator("my.f_ten", text="", icon='EVENT_F10')
                    op.preset_argument_template = self.preset_argument_template
                    op.record_preset_argument_template = self.record_preset_argument_template
                    op.index_offset = self.index_offset
                    op.group_id = controller.str_group_id
                    op.is_recording = self.is_recording

                    op = row.operator("my.f_eleven", text="", icon='EVENT_F11')
                    op.preset_argument_template = self.preset_argument_template
                    op.record_preset_argument_template = self.record_preset_argument_template
                    op.index_offset = self.index_offset
                    op.group_id = controller.str_group_id
                    op.is_recording = self.is_recording

                    op = row.operator("my.f_twelve", text="", icon='EVENT_F12')
                    op.preset_argument_template = self.preset_argument_template
                    op.record_preset_argument_template = self.record_preset_argument_template
                    op.index_offset = self.index_offset
                    op.group_id = controller.str_group_id
                    op.is_recording = self.is_recording
                    
                    row.alert = 0
                   
            column.separator()
            row = column.row() 
            row.prop(self, "color_argument_template", icon='COLOR', text="")
            row.prop(self, "preset_argument_template", icon='EVENT_F1', text="")
            row.prop(self, "index_offset", icon='ADD', text="Index Offset")
            column.separator()
            row = column.row() 
            row.prop(self, "record_color_argument_template", icon='COLOR', text="")
            row.prop(self, "record_preset_argument_template", icon='EVENT_F1', text="")
            row.label(text="")
            column.separator()
            row = column.row()
            row.label(text="Insert # for group number and $ for index")                
                   
            
class IntensitiesNode(bpy.types.Node):
    bl_idname = 'intensities_type'
    bl_label = 'Intensities Node'
    bl_icon = 'OUTLINER_OB_LIGHT'
    bl_width_default = 600
    bl_description="Adjust all intensities of group controller nodes on this level"

    def init(self, context):
        return

    def draw_buttons(self, context, layout):
        scene = context.scene
        column = layout.column(align=True)
        
        row = column.row()

        world = scene.world

        if world is not None and world.node_tree:
            node_tree = world.node_tree

            for controller in node_tree.nodes:
                if controller.bl_idname == 'group_controller_type':
                    row = column.row(align=True)        
                    row.prop(controller, "float_intensity", slider=True, text=controller.str_group_label)
        
        
class ColorsNode(bpy.types.Node):
    bl_idname = 'colors_type'
    bl_label = 'Colors Node'
    bl_icon = 'COLOR'
    bl_width_default = 1200
    bl_description="Adjust all colors of group controller nodes on this level"

    def init(self, context):
        return

    def draw_buttons(self, context, layout):
        scene = context.scene
        column = layout.column(align=True)
        row = column.row()
        count = 0
        
        if scene.scene_props.color_is_preset_mode:
            world = scene.world
            if world is not None and world.node_tree:
                node_tree = world.node_tree
                for controller in node_tree.nodes:
                    if controller.bl_idname == 'group_controller_type':
                        row = column.row(align=True)
                        row.label(text=controller.str_group_label)
                        row.operator("my.enable_record", text="", icon='REC')
                        row.operator("my.color_one", text="", icon='COLORSET_01_VEC')
                        row.operator("my.color_two", text="", icon='COLORSET_02_VEC')
                        row.operator("my.color_three", text="", icon='COLORSET_03_VEC')
                        row.operator("my.color_four", text="", icon='COLORSET_04_VEC')
                        row.operator("my.color_five", text="", icon='COLORSET_05_VEC')
                        row.operator("my.color_six", text="", icon='COLORSET_06_VEC')
                        row.operator("my.color_seven", text="", icon='COLORSET_07_VEC')
                        row.operator("my.color_eight", text="", icon='COLORSET_08_VEC')
                        row.operator("my.color_nine", text="", icon='COLORSET_09_VEC')
                        row.operator("my.color_ten", text="", icon='COLORSET_11_VEC')
                        row.operator("my.color_eleven", text="", icon='COLORSET_12_VEC')
                        row.operator("my.color_twelve", text="", icon='COLORSET_13_VEC')
                        row.operator("my.color_thirteen", text="", icon='COLORSET_14_VEC')
                        row.operator("my.color_fourteen", text="", icon='COLORSET_15_VEC')
                        
                        row = column.row(align=True)
                
                row = column.row()
                row.prop(scene.scene_props, "color_is_preset_mode", text = "Show Presets Buttons", slider = True)
                    
        else:
            displayed_count = 0
            row = column.row(align=True)
            world = scene.world

            if world is not None and world.node_tree:
                node_tree = world.node_tree

                flow = column.grid_flow(columns=4, align=True)

                displayed_count = 0
                for controller in node_tree.nodes:
                    if controller.bl_idname == 'group_controller_type':
                        if controller.color_is_on:
                            box = flow.box()
                            box.template_color_picker(controller, "float_vec_color", value_slider=False, lock_luminosity=False, cubic=True)
                            box.label(text=controller.str_group_label)
                            displayed_count += 1                     
                              
            row = column.row()
            row.prop(scene.scene_props, "color_is_preset_mode", text = "Show Presets Buttons", slider = True)
            row.prop(scene.scene_props, "color_is_expanded", text = "Expand Color", slider = True)
                
                
class StrobesNode(bpy.types.Node):
    bl_idname = 'strobes_type'
    bl_label = 'Strobes Node'
    bl_icon = 'OUTLINER_DATA_LIGHTPROBE'
    bl_width_default = 400
    bl_description="Adjust all strobes of group controller nodes on this level"

    def init(self, context):
        return

    def draw_buttons(self, context, layout):
        scene = context.scene
        column = layout.column(align=True)
        row = column.row()
        world = scene.world
        if world is not None and world.node_tree:
            
            node_tree = world.node_tree
            
            for controller in node_tree.nodes:
                if controller.bl_idname == 'group_controller_type':
                    
                    row = column.row()
                    row.prop(controller, "float_strobe", slider=True, text=controller.str_group_label)
                    
            
class ZoomsNode(bpy.types.Node):
    bl_idname = 'zooms_type'
    bl_label = 'Zooms Node'
    bl_icon = 'LINCURVE'
    bl_width_default = 400
    bl_description="Adjust all zooms of group controller nodes on this level"

    def init(self, context):
        return

    def draw_buttons(self, context, layout):
        scene = context.scene
        column = layout.column(align=True)
        
        row = column.row()
        
        world = scene.world

        if world is not None and world.node_tree:
            node_tree = world.node_tree

            for controller in node_tree.nodes:
                if controller.bl_idname == 'group_controller_type':
                    row = column.row()
                    row.prop(controller, "float_zoom", slider=True, text=controller.str_group_label)
              
            
class EdgesNode(bpy.types.Node):
    bl_idname = 'edges_type'
    bl_label = 'Edges Node'
    bl_icon = 'SELECT_SET'
    bl_width_default = 400
    bl_description="Adjust all edges of group controller nodes on this level"

    def init(self, context):
        return

    def draw_buttons(self, context, layout):
        scene = context.scene
        column = layout.column(align=True)
        
        row = column.row()

        world = scene.world

        if world is not None and world.node_tree:
            node_tree = world.node_tree

            for controller in node_tree.nodes:
                if controller.bl_idname == 'group_controller_type':
                    row = column.row()
                    row.prop(controller, "float_edge", slider=True, text=controller.str_group_label)
                   
                
class PanTiltNode(bpy.types.Node):
    bl_idname = 'pan_tilt_type'
    bl_label = 'FOH Pan/Tilt'
    bl_icon = 'ORIENTATION_GIMBAL'
    bl_width_default = 150
    bl_description="Intuitive pan/tilt controller only for FOH, forward-facing fixtures"

    pan_tilt_channel: bpy.props.IntProperty(default=1, description="Channel for pan/tilt graph. Think of the circle as a helix or as an infinite staircase. Pan-around is when you fall down to go forward an inch or jump up to go forward an inch. The circle below is a helix with 150% the surface area of a circle. Only use this for front-facing FOH/catwalk movers")
    pan_is_inverted: bpy.props.BoolProperty(default = True)

    def init(self, context):
        return
    
    def draw_buttons(self, context, layout):
        scene = context.scene
        column = layout.column(align=True)
        
        row = column.row(align=True)  
        
        channel_string = str(self.pan_tilt_channel)
        active_object = None
        
        for obj in bpy.data.objects:
            if obj.type == 'MESH' and obj.name == channel_string:
                active_object = obj
                break
        
        if active_object is not None:
            #row.prop(active_object, "pan_is_inverted", text="", icon='SORT_DESC')
            row.prop(self, "pan_tilt_channel", text="Channel:")
            column.separator()
            column.separator()
            
            row = column.row()
            
            if active_object:
                row.template_color_picker(active_object, "float_vec_pan_tilt_graph", value_slider = True)

                if active_object.is_overdriven_left:
                    row = column.row()
                    row.alert = 1
                    row.scale_x = .55
                    row.label(text="")
                    row.scale_x = 1
                    row.label(text="|")
                    row.alert = 0
                    row = column.row()
                    row.alert = 1
                    row.label(text = "Extending for left-pan")
                    row.alert = 0
                    
                    if active_object.is_approaching_limit:
                        row = column.row()
                        row.alert = 1
                        row.label(text = "Will soon pan-around!")
                        row.alert = 0
                    
                if active_object.is_overdriven_right:
                    row = column.row()
                    row.alert = 1
                    row.scale_x = .55
                    row.label(text="")
                    row.scale_x = 1
                    row.label(text="|")
                    row.alert = 0
                    row = column.row()
                    row.alert = 1
                    row.label(text = "Extending for right-pan")
                    row.alert = 0
                    
                    if active_object.is_approaching_limit:
                        row = column.row()
                        row.alert = 1
                        row.label(text = "Will soon pan-around!")
                        row.alert = 0
                        
        else: 
            row.label(text="No light selected.")
            row.prop(self, "pan_tilt_channel", text="Channel:")
            
            
class ConsoleButtonsNode(bpy.types.Node):
    bl_idname = 'console_buttons_type'
    bl_label = 'Console Buttons Node'
    bl_icon = 'DESKTOP'
    bl_width_default = 400
    bl_description="Create console buttons with custom OSC syntax"

    custom_buttons: bpy.props.CollectionProperty(type=CustomButtonPropertyGroup)
    active_button_index: bpy.props.IntProperty()
    number_of_columns: bpy.props.IntProperty(default=3)
    expand_settings: bpy.props.BoolProperty(default=True)

    def init(self, context):
        return
    
    def draw_buttons(self, context, layout):
        counter = 0
        box = layout.box()
        row = box.row()
        
        for index, button in enumerate(self.custom_buttons):
            if counter == 0:
                row.prop(self, "expand_settings", icon='PREFERENCES', text="", emboss=True)
            if counter % self.number_of_columns == 0 and counter != 0:
                row = box.row()
            op = row.operator("node.custom_button", text=button.button_label)
            op.button_index = index

            counter += 1
        
        if self.expand_settings:
            counter_two = 0
            for index, button in enumerate(self.custom_buttons):
                if counter_two == 0:
                    box = layout.box()
                row = box.row()
                op_up = row.operator("node.bump_up_custom_button", icon='TRIA_UP', text="")
                op_up.button_index = index

                op_down = row.operator("node.bump_down_custom_button", icon='TRIA_DOWN', text="")
                op_down.button_index = index
                row.prop(button, "button_label", text="", icon='INFO')
                row.prop(button, "button_address", text="", icon='RNA_ADD')
                row.prop(button, "button_argument", text="", icon='MOD_HUE_SATURATION')
                
                op_remove = row.operator("node.remove_custom_button", icon='X', text="")
                op_remove.button_index = index 
                counter_two += 1

            row = box.row()
            row.operator("node.add_custom_button", icon='ADD', text="Add Custom Button")
            row.prop(self, "number_of_columns", icon='CENTER_ONLY', text="# of Columns")
            
            
class FlashUpSocket(NodeSocket):
    bl_idname = 'FlashUpType'
    bl_label = 'Flash Up Socket'

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (1, 1, 0, 1)      
            

class FlashDownSocket(NodeSocket):
    bl_idname = 'FlashDownType'
    bl_label = 'Flash Down Socket'

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (1, 1, 0, 1) 
            
            
def trigger_flash_node_updaters(self, context):
    for node_tree in bpy.data.node_groups:
        if node_tree.bl_idname == 'AlvaNodeTree':
            for node in node_tree.nodes:
                if node.bl_idname == "flash_type":
                    node.flash_motif_names_enum = node.flash_motif_names_enum
    return

            
def flash_node_updater(self, context):
    up_groups_list = []
    down_groups_list = []

    for input_socket in self.inputs:
        if isinstance(input_socket, FlashUpSocket):
            for link in input_socket.links:
                connected_node = link.from_socket.node
                if connected_node.bl_idname == "group_controller_type":
                    up_groups_list.append(connected_node.str_selected_light)
                elif connected_node.bl_idname == "group_driver_type":
                    for output_socket in connected_node.outputs:
                        if output_socket.bl_idname == 'GroupOutputType':
                            for link in output_socket.links:
                                driven_node = link.to_socket.node
                                if driven_node.bl_idname == "group_controller_type":
                                    up_groups_list.append(driven_node.str_selected_light)
                elif connected_node.bl_idname == "mixer_type":
                    down_groups_list.append(connected_node.str_selected_light)               
                elif connected_node.bl_idname == "mixer_driver_type":
                    for output_socket in connected_node.outputs:
                        if output_socket.bl_idname == 'MixerOutputType':
                            for link in output_socket.links:
                                driven_node = link.to_socket.node
                                if driven_node.bl_idname == "mixer_type":
                                    up_groups_list.append(driven_node.str_selected_group)
                elif connected_node.bl_idname == 'ShaderNodeGroup':
                    group_node_tree = connected_node.node_tree
                    for node in group_node_tree.nodes:
                        if node.type == 'GROUP_OUTPUT':
                            for socket in node.inputs:
                                if socket.name == "Flash":
                                    for inner_link in socket.links:
                                        interior_connected_node = inner_link.from_node
                                        if interior_connected_node.bl_idname == 'group_controller_type':
                                            up_groups_list.append(interior_connected_node.str_selected_light)
                                        elif interior_connected_node.bl_idname == "group_driver_type":
                                            for output_socket in interior_connected_node.outputs:
                                                if output_socket.bl_idname == 'GroupOutputType':
                                                    for link in output_socket.links:
                                                        driven_node = link.to_socket.node
                                                        if driven_node.bl_idname == "group_controller_type":
                                                            up_groups_list.append(driven_node.str_selected_light)
                                            
        elif isinstance(input_socket, FlashDownSocket):
            for link in input_socket.links:
                connected_node = link.from_socket.node
                if connected_node.bl_idname == "group_controller_type":
                    down_groups_list.append(connected_node.str_selected_light)
                elif connected_node.bl_idname == "group_driver_type":
                    for output_socket in connected_node.outputs:
                        if output_socket.bl_idname == 'GroupOutputType':
                            for link in output_socket.links:
                                driven_node = link.to_socket.node
                                if driven_node.bl_idname == "group_controller_type":
                                    down_groups_list.append(driven_node.str_selected_light)
                elif connected_node.bl_idname == "mixer_type":
                    down_groups_list.append(connected_node.str_selected_light)               
                elif connected_node.bl_idname == "mixer_driver_type":
                    for output_socket in connected_node.outputs:
                        if output_socket.bl_idname == 'MixerOutputType':
                            for link in output_socket.links:
                                driven_node = link.to_socket.node
                                if driven_node.bl_idname == "mixer_type":
                                    down_groups_list.append(driven_node.str_selected_group)
                elif connected_node.bl_idname == 'ShaderNodeGroup':
                    group_node_tree = connected_node.node_tree
                    for node in group_node_tree.nodes:
                        if node.type == 'GROUP_OUTPUT':
                            for socket in node.inputs:
                                if socket.name == "Flash":
                                    for inner_link in socket.links:
                                        interior_connected_node = inner_link.from_node
                                        if interior_connected_node.bl_idname == 'group_controller_type':
                                            down_groups_list.append(interior_connected_node.str_selected_light)
                                        elif interior_connected_node.bl_idname == "group_driver_type":
                                            for output_socket in interior_connected_node.outputs:
                                                if output_socket.bl_idname == 'GroupOutputType':
                                                    for link in output_socket.links:
                                                        driven_node = link.to_socket.node
                                                        if driven_node.bl_idname == "group_controller_type":
                                                            down_groups_list.append(driven_node.str_selected_light)
    
    for strip in context.scene.sequence_editor.sequences_all:
        if strip.my_settings.motif_type_enum == "option_eos_flash" and strip.motif_name == self.flash_motif_names_enum and strip.flash_using_nodes:
            up_groups_str = ' + Group '.join(up_groups_list)
            down_groups_str = ' + Group '.join(down_groups_list)
            strip.flash_input = f"Group {up_groups_str} Preset {self.int_up_preset_assignment}"
            strip.flash_down_input = f"Group {down_groups_str} Preset {self.int_down_preset_assignment}" 
                
                
class FlashNode(bpy.types.Node):
    bl_idname = 'flash_type'
    bl_label = 'Flash Node'
    bl_icon = 'LIGHT_SUN'
    bl_width_default = 190
    bl_description="Autofill the Flash Up and Flash Down fields of flash strips in Sequencer with node settings and noodle links. Intended primarily for pose-based choreography"
    
    def get_motif_name_items(self, context):
        unique_names = set()

        sequences = context.scene.sequence_editor.sequences_all
        for seq in sequences:
            if hasattr(seq, 'motif_name'): 
                unique_names.add(seq.motif_name)

        if unique_names:
            items = [(name, name, "") for name in sorted(unique_names)]
        else:
            items = [('NONE', 'No Motifs', 'No motifs available')]

        return items

    flash_motif_names_enum: bpy.props.EnumProperty(
        name="",
        description="List of unique motif names",
        items=get_motif_name_items,
        update=flash_node_updater,
        default=0
    )
    
    show_effect_preset_settings: BoolProperty(default=False, description="Show settings")
    int_up_preset_assignment: IntProperty(default=0, description="Preset number on console")
    int_down_preset_assignment: IntProperty(default=0, description="Preset number on console")
    
    def init(self, context):
        self.inputs.new('FlashUpType', "Flash Up")
        self.inputs.new('FlashDownType', "Flash Down")
        return
    
    def draw_buttons(self, context, layout):
        pcoll = preview_collections["main"]
        orb = pcoll["orb"]
        
        node_tree = context.space_data.node_tree
        
        layout.prop(self, "flash_motif_names_enum", text="", icon='SEQ_SEQUENCER')
        column = layout.column()
        row = column.row(align=True)
        row.prop(self, "show_effect_preset_settings", icon='PREFERENCES', emboss=True, icon_only=True)
        op = row.operator("node.flash_preset_search_operator", text="", icon='VIEWZOOM')
        op.node_name = self.name
        row.prop(self, "int_up_preset_assignment", text="Up Preset:")
        op = row.operator("node.record_effect_preset_operator", text="", icon_value=orb.icon_id)
        op.node_name = self.name
        op.node_tree_name = node_tree.name
        row = column.row(align=True)
        row.prop(self, "int_down_preset_assignment", text="Down Preset:")
        op = row.operator("node.record_down_effect_preset_operator", text="", icon_value=orb.icon_id)
        op.node_name = self.name
        op.node_tree_name = node_tree.name
        
        world = context.scene.world
        conflict = False
        conflict_node_name = ""
        
        if world is not None and world.node_tree and self.int_up_preset_assignment not in (0, 1) and self.int_down_preset_assignment not in (0, 1):
            node_tree = world.node_tree
            for controller in node_tree.nodes:
                if controller.bl_idname == 'flash_type' and controller.name != self.name and controller.int_up_preset_assignment == self.int_up_preset_assignment:
                    conflict = True
                    conflict_node_name = str(controller.label)
                    if conflict_node_name == "":
                        conflict_node_name = str(controller.name)
                        if conflict_node_name == "":
                            conflict_node_name = "Another"
                    break
                
        if conflict:
            row = column.row()
            row.label(text=f"{conflict_node_name} uses same preset.", icon='ERROR')
            
        if self.show_effect_preset_settings:
            column.separator()
            column.separator()
            row = column.row()
            row.label(text="Argument Template")
            row = column.row()
            row.prop(context.scene.scene_props, "str_preset_assignment_argument", text="")

        layout.separator()
        
        
class NodeSettingsPanel(bpy.types.Panel):
    bl_label = "Node Formatter"
    bl_idname = "NODE_PT_controller_toggles"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Alva Sorcerer'
    
    @classmethod
    def poll(cls, context): ## Need to add a ton more of these.
        return hasattr(context.space_data, 'edit_tree') and context.space_data.edit_tree and context.space_data.edit_tree.nodes.active
    
    def draw(self, context):
        DrawSettingsNode.draw_buttons(context, self.layout)


class DrawSettingsNode:
    @staticmethod
    def draw_buttons(context, layout):
        pcoll = preview_collections["main"]
        orb = pcoll["orb"]
      
        layout = self.layout
        scene = context.scene
        column = layout.column(align=True)
        row = column.row()
        space = context.space_data.edit_tree.nodes
        active_node = None 
        active_node = context.space_data.edit_tree.nodes.active

        if active_node and (active_node.bl_idname == "group_controller_type" or active_node.bl_idname == "group_driver_type" or active_node.bl_idname == "master_type"):
            row.prop(active_node, "strobe_is_on", text="Strobe", slider=True)
            row.prop(active_node, "color_is_on", text="Color", slider=True)
            
            row = column.row()
            row.prop(active_node, "pan_tilt_is_on", text="Pan/Tilt", slider=True)
            
            row = column.row()
            row.prop(active_node, "zoom_is_on", text="Zoom", slider=True)
            row.prop(active_node, "iris_is_on", text="Iris", slider=True)
            
            row = column.row()
            row.prop(active_node, "edge_is_on", text="Edge", slider=True)
            row.prop(active_node, "diffusion_is_on", text="Diffusion", slider=True)
            
            row = column.row()
            row.prop(active_node, "gobo_id_is_on", text="Gobo", slider=True)
            
            column.separator()
            
            if active_node.bl_idname == "group_controller_type":
                row = column.row()
                row.prop(active_node, "influence", text="Influence")
                
                column.separator()
                
        elif active_node and active_node.bl_idname == "mixer_type" or active_node.bl_idname == "mixer_driver_type":
            row = layout.row(align=True)
            row.prop(active_node, "str_selected_group", text="")
            row = layout.row(align=True)
            row.prop(active_node, "parameters_enum", text="")
            if active_node.parameters_enum == 'option_color':
                row.prop(active_node, "color_profile_enum", text="")
  
            if active_node.parameters_enum != None:
                row = layout.row()
                row.prop(active_node, "show_middle", text="Show Middle", slider=True)
                
                if not active_node.show_middle:
                    row.prop(active_node, "every_other", text="Every Other", slider=True)
                    
            row = layout.row()
            row.prop(active_node, "collapse_most", text="Collapse most")
            
        row = layout.row()
        row.prop(active_node, "label", text="Label")
        row = layout.row()
        row.prop(active_node, "use_custom_color", text="", icon='HIDE_ON' if not active_node.use_custom_color else 'HIDE_OFF')
        row.prop(active_node, "color", text="")
            

def draw_alva_node_menu(self, layout):
    pcoll = preview_collections["main"]
    orb = pcoll["orb"]
    
    layout = self.layout
    layout.label(text="Primary Nodes", icon_value=orb.icon_id)
    layout.operator("node.add_group_controller_node", text="Group Controller", icon='STICKY_UVS_LOC')
    layout.operator("node.add_mixer_node", text="Mixer", icon='OPTIONS')
    layout.operator("node.add_mixer_driver_node", text="Mixer Driver", icon='DECORATE_DRIVER')
    layout.operator("node.add_group_driver_node", text="Group Driver", icon='DECORATE_DRIVER')
    layout.operator("node.add_master_node", text="Master", icon='DECORATE_DRIVER')
    layout.operator("node.add_flash_node", text="Flash", icon='LIGHT_SUN')
    
    layout.separator()
    
    layout.label(text="Single-parameter Nodes", icon_value=orb.icon_id)
    layout.operator("node.add_intensities_node", text="Intensities", icon='OUTLINER_OB_LIGHT')
    layout.operator("node.add_colors_node", text="Colors", icon='COLOR')
    layout.operator("node.add_strobes_node", text="Strobes", icon='OUTLINER_DATA_LIGHTPROBE')
    layout.operator("node.add_zooms_node", text="Zooms", icon='LINCURVE')
    layout.operator("node.add_edges_node", text="Edges", icon='SELECT_SET')
    
    layout.separator()
    
    layout.label(text="Specialty Nodes", icon_value=orb.icon_id)
    layout.operator("node.add_oven_node", text="Renderer", icon='OUTLINER_OB_CAMERA')
    layout.operator("node.add_settings_node", text="Settings", icon='PREFERENCES')
    layout.operator("node.add_console_buttons_node", text="Console Buttons", icon='DESKTOP')
    layout.operator("node.add_presets_node", text="Presets", icon='LIGHTPROBE_GRID')
    layout.operator("node.add_pan_tilt_node", text="Pan/Tilt", icon='ORIENTATION_GIMBAL')
    
    
    
class AlvaSorcererNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'ShaderNodeTree' or 
                context.space_data.tree_type == 'AlvaNodeTree')


categories = [
    AlvaSorcererNodeCategory('PRIMARYNODES', "Primary Nodes", items=[
        NodeItem("group_controller_type"),
        NodeItem("group_driver_type"),
        NodeItem("mixer_type"),
        NodeItem("mixer_driver_type"),
        NodeItem("master_type"),
        NodeItem("flash_type"),
    ]),

    AlvaSorcererNodeCategory('SINGLEPARAMNODES', "Single-parameter Nodes", items=[
        NodeItem("intensities_type"),
        NodeItem("colors_type"),
        NodeItem("strobes_type"),
        NodeItem("zooms_type"),
        NodeItem("edges_type"),
    ]),
    AlvaSorcererNodeCategory('SPECIALTYNODES', "Specialty Nodes", items=[
        NodeItem("oven_type"),
        NodeItem("node_settings_type"),
        NodeItem("console_buttons_type"),
        NodeItem("presets_type"),
        NodeItem("pan_tilt_type"),
    ]),
]
    

class NodesToolbar(bpy.types.Panel):
    bl_label = "Tools"  # not visible
    bl_idname = "ALVA_PT_nodes_toolbar"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_options = {'HIDE_HEADER'}
    
    def draw(self, context):
        layout = self.layout
        region_width = context.region.width

        num_columns = 1

        flow = layout.grid_flow(row_major=True, columns=num_columns, even_columns=True, even_rows=False, align=True)
        flow.scale_y = 2
        
        flow.operator("node.add_group_controller_node", icon='ADD', text="Add Group" if region_width >= 200 else "", emboss=True)
        flow.operator("my.go_to_cue_out_operator", icon='GHOST_ENABLED', text="Cue 0" if region_width >= 200 else "")
        flow.operator("my.displays_operator", icon='MENU_PANEL', text="Displays" if region_width >= 200 else "")
        flow.operator("my.about_operator", icon='INFO', text="About" if region_width >= 200 else "")
        flow.operator("my.disable_all_clocks_operator", icon='MOD_TIME', text="Disable Clocks" if region_width >= 200 else "")
        flow.operator("nodes.show_node_settings", icon='PREFERENCES', text="Settings" if region_width >= 200 else "")


classes = (
    CustomButtonPropertyGroup,
    OvenNode,
    SettingsNode,
    IntensitiesNode,
    PresetsNode,
    ColorsNode,
    StrobesNode,
    ZoomsNode,
    EdgesNode,
    NodeSettingsPanel,
    ConsoleButtonsNode,
    PanTiltNode,
    FlashNode,
    FlashUpSocket,
    FlashDownSocket,
    NodesToolbar,
)


def register():
    register_node_categories("SORCERER_NODES", categories)
    
    for cls in classes:
        bpy.utils.register_class(cls)
    
    pcoll = bpy.utils.previews.new()
    preview_collections["main"] = pcoll
    addon_dir = os.path.dirname(__file__)
    pcoll.load("orb", os.path.join(addon_dir, "alva_orb.png"), 'IMAGE')
    
    bpy.types.NODE_HT_header.append(draw_arm_nodes)
    bpy.types.NODE_MT_add.append(draw_alva_node_menu)
        
        
def unregister():
    bpy.types.NODE_MT_add.remove(draw_alva_node_menu)
    bpy.types.NODE_HT_header.remove(draw_arm_nodes)
    
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    unregister_node_categories("SORCERER_NODES")
        
        
# For development purposes only.
if __name__ == "__main__":
    register()
