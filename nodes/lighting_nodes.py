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
from bpy.types import NodeSocket, Node, PropertyGroup
from bpy.props import *

from ..assets.items import Items as AlvaItems # type: ignore
from ..ui.common_ui import CommonUI # type: ignore
from ..ui.settings_ui import SettingsUI
from ..updaters.node_updaters import NodeUpdaters # type: ignore
from ..ui.node_ui import NodeUI # type: ignore
from ..utils.utils import Utils # type: ignore


MixerParametersSubClass = Utils.find_subclass_by_name(PropertyGroup, "MixerParameters")
CustomButtonPropertyGroupSubClass = Utils.find_subclass_by_name(PropertyGroup, "CustomButtonPropertyGroup")


LINK_LIMIT = 5


###################
# NODE SOCKETS
###################
class NODE_ST_lighting_input(NodeSocket):
    bl_idname = 'LightingInputType'
    bl_label = 'Lighting Input Socket'

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (.5, 0, 1, 1)  


class NODE_ST_lighting_output(NodeSocket):
    bl_idname = 'LightingOutputType'
    bl_label = 'Lighting Output Socket'

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (.5, 0, 1, 1)  
    
    
class NODE_ST_flash_out(NodeSocket):
    bl_idname = 'FlashOutType'
    bl_label = 'Flash Output Socket'

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (1, 1, 0, 1) 
    
    
class NODE_ST_flash_up(NodeSocket):
    bl_idname = 'FlashUpType'
    bl_label = 'Flash Up Socket'

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (1, 1, 0, 1)      
            

class NODE_ST_flash_down(NodeSocket):
    bl_idname = 'FlashDownType'
    bl_label = 'Flash Down Socket'

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (1, 1, 0, 1) 
    
    
class NODE_ST_motor_in(NodeSocket):
    bl_idname = 'MotorInputType'
    bl_label = 'Motor Input Socket'

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (.5, .5, .5, .5) 
    
    
class NODE_ST_motor_out(NodeSocket):
    bl_idname = 'MotorOutputType'
    bl_label = 'Motor Output Socket'

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (.5, .5, .5, .5) 
    
    
sockets = [
    NODE_ST_lighting_input,
    NODE_ST_lighting_output,
    NODE_ST_flash_out,
    NODE_ST_flash_up,
    NODE_ST_flash_down,
    NODE_ST_motor_in,
    NODE_ST_motor_out
]

    
def register_sockets():
    for cls in sockets:
        bpy.utils.register_class(cls)
        
def unregister_sockets():
    for cls in reversed(sockets):
        bpy.utils.unregister_class(cls)
    
    
###################
# NODES
###################
class NODE_NT_group_controller(Node):
    bl_idname = 'group_controller_type'
    bl_label = 'Group Controller Node'
    bl_icon = 'STICKY_UVS_LOC'
    bl_width_default = 300
    
    # Common property registrations in register() section.

    def init(self, context):
        group_input = self.inputs.new('LightingInputType', "Lighting Input")
        group_input.link_limit = LINK_LIMIT
        self.outputs.new('LightingOutputType', "Lighting Output")
        self.outputs.new('FlashOutType', "Flash")
        return

    def draw_buttons(self, context, layout):
        active_node = None 
        active_node = context.space_data.edit_tree.nodes.active
        column = layout.column()
        row = column.row()
        
        CommonUI.draw_text_or_group_input(self, context, row, self, object=False)
        CommonUI.draw_parameters(self, context, column, column, self)
        CommonUI.draw_footer_toggles(self, context, column, self, box=False)

    
class NODE_NT_mixer(Node):
    bl_idname = 'mixer_type'
    bl_label = 'Mixer Node'
    bl_icon = 'OPTIONS'
    bl_width_default = 400

    parameters: CollectionProperty(type=MixerParametersSubClass) # type: ignore # type: ignore
    
    # Common property registrations in register() section.

    influence: IntProperty(default=1, min=1, max=10, description="How many votes this controller has when there are conflicts", options={'ANIMATABLE'}) # type: ignore # type: ignore
    show_settings: BoolProperty(default=True, name="Show Settings", description="Expand/collapse group/parameter row and UI controller row") # type: ignore # type: ignore
    float_offset: FloatProperty(name="Offset", description="Move or animate this value for a moving effect", update=NodeUpdaters.mixer_param_updater) # type: ignore
    int_subdivisions: IntProperty(name="Subdivisions", description="Subdivide the mix into multiple sections", update=NodeUpdaters.mixer_param_updater, min=0, max=32) # type: ignore # type: ignore
    columns: IntProperty(name="# of Columns:", min=1, max=8, default=3) # type: ignore # type: ignore
    scale: FloatProperty(name="Size of Choices:", min=1, max=3, default=2) # type: ignore # type: ignore
    mix_method_enum: EnumProperty(
        name="Method",
        description="Choose a mixing method",
        items=AlvaItems.mixer_methods,
        default=1
    ) # type: ignore
    parameters_enum: EnumProperty(
        name="Parameter",
        description="Choose a parameter type to mix",
        items=AlvaItems.mixer_parameters,
        default=1,
        update=NodeUpdaters.update_node_name
    ) # type: ignore # type: ignore
    node_tree_pointer: PointerProperty(
        name="Node Tree Pointer",
        type=bpy.types.NodeTree,
        description="Pointer to the node tree"
    ) # type: ignore # type: ignore
    node_name: bpy.props.StringProperty(
        name="Node Name",
        description="Name of the node"
    ) # type: ignore
    
    def init(self, context):
        self.inputs.new('MotorInputType', "Motor Input")
        self.outputs.new('FlashOutType', "Flash")
        NodeUpdaters.update_node_name(self)
        return

    def draw_buttons(self, context, layout):  
        NodeUI.draw_node_mixer(self, context, layout)
        
        
class NODE_NT_pan_tilt(Node):
    bl_idname = 'pan_tilt_type'
    bl_label = 'FOH Pan/Tilt'
    bl_icon = 'ORIENTATION_GIMBAL'
    bl_width_default = 150
    bl_description="Intuitive pan/tilt controller only for FOH, forward-facing fixtures"

    pan_tilt_channel: IntProperty(default=1, description="Channel for pan/tilt graph. Think of the circle as a helix or as an infinite staircase. Pan-around is when you fall down to go forward an inch or jump up to go forward an inch. The circle below is a helix with 150% the surface area of a circle. Only use this for front-facing FOH/catwalk movers") # type: ignore # type: ignore
    pan_is_inverted: BoolProperty(default = True) # type: ignore

    def init(self, context):
        return
    
    def draw_buttons(self, context, layout):
        NodeUI.draw_pan_tilt_node(self, context, layout)
        
        
class NODE_NT_global(Node):
    bl_idname = 'global_type'
    bl_label = 'Global Node'
    bl_icon = 'WORLD_DATA'
    bl_width_default = 600
    bl_description="Adjust any parameter across all Group Controller nodes"

    parameters_enum: EnumProperty(
        name="Parameter",
        description="Choose a parameter type to control",
        items=AlvaItems.global_node_parameters,
        default=1
    ) # type: ignore
    columns: IntProperty(name="Columns:", description="", default=3, max=8, min=1) # type: ignore
    scale: FloatProperty(name="Size:", description="", default=1, max=3, min=.2) # type: ignore

    def init(self, context):
        return

    def draw_buttons(self, context, layout):
        NodeUI.draw_global_node(self, context, layout)
             

class NODE_NT_motor(Node):
    bl_idname = 'motor_type'
    bl_label = 'Motor'
    bl_icon = 'ANTIALIASED'
    bl_width_default = 175
    bl_description="Drive mixer node oscillations"

    motor: FloatVectorProperty(
        name="",
        subtype='COLOR',
        size=3,
        default=(.1, .1, .1),
        min=0.0,
        max=1,
        update=NodeUpdaters.motor_updater
    ) # type: ignore
    transmission_enum: EnumProperty(
        name="Transmission",
        description="Choose whether to spin the motor manually or with keyframes",
        items=AlvaItems.transmission_options,
        default=1
    ) # type: ignore
    float_progress: FloatProperty(name="Progress:", description="How far along in the steps the mixer is", default=0, update=NodeUpdaters.props_updater) # type: ignore # type: ignore
    float_scale: FloatProperty(name="Scale:", description="Size of the effect, 1 is no reduction, 0 is complete reduction", default=1, min=0, max=1, update=NodeUpdaters.props_updater) # type: ignore

    initial_angle: FloatProperty(name="Initial Angle", default=0) # type: ignore
    prev_angle: FloatProperty(name="Previous Angle", default=0) # type: ignore
    is_interacting: BoolProperty(name="Is Interacting", default=False) # type: ignore

    def init(self, context):
        self.outputs.new('MotorOutputType', "Motor Out")
        return
    
    def draw_buttons(self, context, layout):
        NodeUI.draw_motor_node(self, context, layout)

            
class NODE_NT_console_buttons(Node):
    bl_idname = 'console_buttons_type'
    bl_label = 'Console Buttons Node'
    bl_icon = 'DESKTOP'
    bl_width_default = 400
    bl_description="Create console buttons with custom OSC syntax"

    custom_buttons: CollectionProperty(type=CustomButtonPropertyGroupSubClass) # type: ignore
    active_button_index: IntProperty() # type: ignore
    number_of_columns: IntProperty(default=3) # type: ignore
    expand_settings: BoolProperty(default=True) # type: ignore

    def init(self, context):
        return
    
    def draw_buttons(self, context, layout):
        NodeUI.draw_console_node(self, context, layout)
        

class NODE_NT_flash(Node):
    bl_idname = 'flash_type'
    bl_label = 'Flash Node'
    bl_icon = 'LIGHT_SUN'
    bl_width_default = 190
    bl_description="Autofill the Flash Up and Flash Down fields of flash strips in Sequencer with node settings and noodle links. Intended primarily for pose-based choreography"
    
    node_tree_pointer: PointerProperty(
        name="Node Tree Pointer",
        type=bpy.types.NodeTree,
        description="Pointer to the node tree"
    ) # type: ignore
    
    flash_motif_names_enum: EnumProperty(
        name="",
        description="List of unique motif names",
        items=AlvaItems.get_motif_name_items,
        update=NodeUpdaters.flash_node_updater,
        default=0
    ) # type: ignore
    
    show_effect_preset_settings: BoolProperty(default=False, description="Show settings", update=NodeUpdaters.flash_node_updater) # type: ignore
    int_up_preset_assignment: IntProperty(default=0, description="Preset number on console", update=NodeUpdaters.flash_node_updater) # type: ignore # type: ignore
    int_down_preset_assignment: IntProperty(default=0, description="Preset number on console", update=NodeUpdaters.flash_node_updater) # type: ignore # type: ignore
    
    def init(self, context):
        up = self.inputs.new('FlashUpType', "Flash Up")
        down = self.inputs.new('FlashDownType', "Flash Down")
        up.link_limit = LINK_LIMIT
        down.link_limit = LINK_LIMIT
        self.node_tree_pointer = self.id_data
        return
    
    def draw_buttons(self, context, layout):
        NodeUI.draw_flash_node(self, context, layout)
        
        
class NODE_NT_alva_presets(Node):
    bl_idname = 'presets_type'
    bl_label = 'Presets Node'
    bl_icon = 'LIGHTPROBE_VOLUME'
    bl_width_default = 600
    bl_description="Record and recall console presets"
    
    preset_argument_template: StringProperty(default="Group # Preset $ Enter", description="Write the OSC syntax your console expects for recalling presets. Insert # for group number and $ for color palette number.") # type: ignore # type: ignore
    record_preset_argument_template: StringProperty(default="Group # Record Preset $ Enter", description="Write the OSC syntax your console expects for recording presets. Insert # for group number and $ for color palette number.") # type: ignore

    expand_settings: BoolProperty(default=False, description="Settings") # type: ignore
    is_recording: BoolProperty(default=False, description="Recording") # type: ignore

    index_offset: IntProperty(default=0, description="Start button index here") # type: ignore

    def init(self, context):
        return

    def draw_buttons(self, context, layout):
        NodeUI.draw_presets_node(self, context, layout)
        return


class NODE_NT_settings(Node):
    bl_idname = 'settings_type'
    bl_label = 'Settings Node'
    bl_icon = 'PREFERENCES'
    bl_width_default = 400
    bl_description="Sorcerer node settings"

    def init(self, context):
        return

    def draw_buttons(self, context, layout):
        SettingsUI.draw_settings(self, context, layout)


class NODE_NT_oven(Node):
    bl_idname = 'oven_type'
    bl_label = 'Qmeo Node'
    bl_icon = 'FILE_MOVIE'
    bl_width_default = 175
    bl_description="Create Qmeos to store complex animation data directly on the console. Qmeos are like videos, but each frame is a lighting cue"

    def init(self, context):
        return

    def draw_buttons(self, context, layout):
        NodeUI.draw_oven_node(self, context, layout)


nodes = [
    NODE_NT_group_controller,
    NODE_NT_mixer,
    NODE_NT_motor,
    NODE_NT_console_buttons,
    NODE_NT_flash,
    NODE_NT_pan_tilt,
    NODE_NT_global,
    NODE_NT_alva_presets,
    NODE_NT_settings,
    NODE_NT_oven
]

    
def register_nodes():
    for cls in nodes:
        bpy.utils.register_class(cls)
        
        
def unregister_nodes():
    for cls in reversed(nodes):
        bpy.utils.unregister_class(cls)
        

def register():
    register_sockets()
    register_nodes()
    
    from ..properties.common_properties import CommonProperties # type: ignore
    common_properties = CommonProperties()
    
    # Group controller node common property registrations.
    Utils.register_properties(NODE_NT_group_controller, common_properties.controller_ids)
    Utils.register_properties(NODE_NT_group_controller, common_properties.common_header)
    Utils.register_properties(NODE_NT_group_controller, common_properties.common_parameters)
    Utils.register_properties(NODE_NT_group_controller, common_properties.common_parameters_extended)
    Utils.register_properties(NODE_NT_group_controller, common_properties.mins_maxes)
    Utils.register_properties(NODE_NT_group_controller, common_properties.parameter_toggles)
    Utils.register_properties(NODE_NT_group_controller, common_properties.special_arguments)

    # Mixer node common property registrations.
    Utils.register_properties(NODE_NT_mixer, common_properties.controller_ids)
    Utils.register_properties(NODE_NT_mixer, common_properties.common_header)


def unregister():
    from ..properties.common_properties import CommonProperties # type: ignore
    common_properties = CommonProperties()
    
    Utils.register_properties(NODE_NT_mixer, common_properties.controller_ids, register=False)
    Utils.register_properties(NODE_NT_mixer, common_properties.common_header, register=False)
    
    Utils.register_properties(NODE_NT_group_controller, common_properties.controller_ids, register=False)
    Utils.register_properties(NODE_NT_group_controller, common_properties.common_header, register=False)
    Utils.register_properties(NODE_NT_group_controller, common_properties.common_parameters, register=False)
    Utils.register_properties(NODE_NT_group_controller, common_properties.common_parameters_extended, register=False)
    Utils.register_properties(NODE_NT_group_controller, common_properties.mins_maxes, register=False)
    Utils.register_properties(NODE_NT_group_controller, common_properties.parameter_toggles, register=False)
    Utils.register_properties(NODE_NT_group_controller, common_properties.special_arguments, register=False)

    unregister_nodes()
    unregister_sockets()