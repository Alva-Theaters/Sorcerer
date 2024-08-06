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
from bpy.props import IntProperty, EnumProperty
from bpy.types import NodeSocket


# NODES
class InputsNode(bpy.types.Node):
    bl_idname = 'inputs_type'
    bl_label = 'Inputs Node'
    bl_icon = 'FORWARD'
    bl_width_default = 400

    patch_number: IntProperty(name="Patch Number", default=1, min=1, max=99, description="") # type: ignore

    def init(self, context):
        for i in range(32):
            self.outputs.new('AudioOutputType', f"Output {i+1}")
        return
    
    def draw_buttons(self, context, layout):  
        layout.prop(self, "patch_number")
        
        
class OutputsNode(bpy.types.Node):
    bl_idname = 'outputs_type'
    bl_label = 'Outputs Node'
    bl_icon = 'BACK'
    bl_width_default = 400

    patch_number: IntProperty(name="Patch Number", default=1, min=1, max=99, description="") # type: ignore

    def init(self, context):
        for i in range(16):
            input = self.inputs.new('AudioInputType', f"Input {i+1}")
            input.link_limit = 32

        return
    
    def draw_buttons(self, context, layout):  
        layout.prop(self, "patch_number")
        
        
class BusesNode(bpy.types.Node):
    bl_idname = 'buses_type'
    bl_label = 'Buses Node'
    bl_icon = 'OUTLINER_OB_ARMATURE'
    bl_width_default = 400

    patch_number: IntProperty(name="Patch Number", default=1, min=1, max=99, description="")  # type: ignore
    
    def get_buses(self, context):
        items = []

        textual_numbers = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
                           "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen"]

        for i in range(17):
            if i == 0:
                i += 1
            input_prop_name = f"bus_{textual_numbers[i]}"
            input_display_name = f"Bus {i}"
            input_description = f"Corresponds to Bus {i} on the audio mixer"
            items.append((input_prop_name, input_display_name, input_description))
            
        return items
    
    bus_number_enum: EnumProperty(items=get_buses)  # type: ignore

    def init(self, context):
        for i in range(1, 18):  # Assuming 17 buses based on the get_buses method
            input = self.inputs.new('AudioInputType', f"Input {i}")
            input.link_limit = 32 
            self.outputs.new('AudioOutputType', f"Output {i}")
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "bus_number_enum")
        layout.prop(self, "patch_number")

        
        
class DCAsNode(bpy.types.Node):
    bl_idname = 'dcas_type'
    bl_label = 'DCAs Node'
    bl_icon = 'VIEW_CAMERA'
    bl_width_default = 400

    patch_number: IntProperty(name="Patch Number", default=1, min=1, max=99, description="") # type: ignore

    def init(self, context):
        for i in range(6):
            input = self.inputs.new('AudioInputType', f"Input {i+1}")
            input.link_limit = 32

        for i in range(6):
            output = self.outputs.new('AudioOutputType', f"Output {i+1}")
            output.link_limit = 32

        return
    
    def draw_buttons(self, context, layout):  
        layout.prop(self, "patch_number")
        
        
class EQNode(bpy.types.Node):
    bl_idname = 'eq_type'
    bl_label = 'EQ Node'
    bl_icon = 'SHARPCURVE'
    bl_width_default = 400

    def init(self, context):
        input = self.inputs.new('AudioInputType', "Input")
        input.link_limit = 32
        self.outputs.new('AudioOutputType', "Output")
        return
    
    def draw_buttons(self, context, layout):  
        return
    
    
class CompressorNode(bpy.types.Node):
    bl_idname = 'compressor_type'
    bl_label = 'Compressor Node'
    bl_icon = 'MOD_DYNAMICPAINT'
    bl_width_default = 400

    def init(self, context):
        input = self.inputs.new('AudioInputType', "Input")
        input.link_limit = 32
        self.inputs.new('AudioTriggerType', "Trigger")
        self.outputs.new('AudioOutputType', "Output")
        return
    
    def draw_buttons(self, context, layout):  
        return
    
    
class GateNode(bpy.types.Node):
    bl_idname = 'gate_type'
    bl_label = 'Gate Node'
    bl_icon = 'IPO_EXPO'
    bl_width_default = 400

    def init(self, context):
        input = self.inputs.new('AudioInputType', "Input")
        input.link_limit = 32
        self.inputs.new('AudioTriggerType', "Trigger")
        self.outputs.new('AudioOutputType', "Output")
        
        return
    
    def draw_buttons(self, context, layout):  
        return


class ReverbNode(bpy.types.Node):
    bl_idname = 'reverb_type'
    bl_label = 'Reverb Node'
    bl_icon = 'IPO_BOUNCE'
    bl_width_default = 400

    def init(self, context):
        input = self.inputs.new('AudioInputType', "Input")
        input.link_limit = 32
        self.outputs.new('AudioOutputType', "Output")
        
        return
    
    def draw_buttons(self, context, layout):  
        return
    
    
# SOCKETS
class AudioOutputType(NodeSocket):
    bl_idname = 'AudioOutputType'
    bl_label = 'Audio Output Socket'

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (1, 1, 1, 1)


class AudioInputType(NodeSocket):
    bl_idname = 'AudioInputType'
    bl_label = 'Audio Input Socket'

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (1, 1, 1, 1)
    
    
class AudioTriggerType(NodeSocket):
    bl_idname = 'AudioTriggerType'
    bl_label = 'Audio Trigger Socket'

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (1, 1, 1, 1)
    
    
#ADD NODE OPERATORS
class AddInputsNode(bpy.types.Operator):
    bl_idname = "node.add_inputs_node"
    bl_label = ""
    bl_description=""

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('inputs_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
    
    
class AddOutputsNode(bpy.types.Operator):
    bl_idname = "node.add_outputs_node"
    bl_label = ""
    bl_description=""

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('outputs_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
    
    
class AddBusesNode(bpy.types.Operator):
    bl_idname = "node.add_buses_node"
    bl_label = ""
    bl_description=""

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('buses_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
    
    
class AddDCAsNode(bpy.types.Operator):
    bl_idname = "node.add_dcas_node"
    bl_label = ""
    bl_description=""

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('dcas_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
    
    
class AddEQNode(bpy.types.Operator):
    bl_idname = "node.add_eq_node"
    bl_label = ""
    bl_description=""

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('eq_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
    

class AddCompressorNode(bpy.types.Operator):
    bl_idname = "node.add_compressor_node"
    bl_label = ""
    bl_description=""

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('compressor_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
    
    
class AddGateNode(bpy.types.Operator):
    bl_idname = "node.add_gate_node"
    bl_label = ""
    bl_description=""

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('gate_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
    
    
class AddReverbNode(bpy.types.Operator):
    bl_idname = "node.add_reverb_node"
    bl_label = ""
    bl_description=""

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('reverb_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
    

nodes = (
    InputsNode,
    OutputsNode,
    BusesNode,
    DCAsNode,
    EQNode,
    CompressorNode,
    GateNode,
    ReverbNode
)

sockets = (
    AudioOutputType,
    AudioInputType,
    AudioTriggerType
)

operators = (
    AddInputsNode,
    AddOutputsNode,
    AddBusesNode,
    AddDCAsNode,
    AddEQNode,
    AddCompressorNode,
    AddGateNode,
    AddReverbNode
)

def register():
    
    for cls in nodes:
        bpy.utils.register_class(cls)
        
    for cls in sockets:
        bpy.utils.register_class(cls)
        
    for cls in operators:
        bpy.utils.register_class(cls)
            
        
def unregister():
    for cls in reversed(operators):
        bpy.utils.unregister_class(cls)
        
    for cls in reversed(sockets):
        bpy.utils.unregister_class(cls)
        
    for cls in reversed(nodes):
        bpy.utils.unregister_class(cls)