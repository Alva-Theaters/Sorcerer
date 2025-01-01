# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from bpy.props import IntProperty, EnumProperty
from bpy.types import Node, NodeSocket, Operator

# pyright: reportInvalidTypeForm=false


# NODES
class InputsNode(Node):
    bl_idname = 'inputs_type'
    bl_label = 'Inputs Node'
    bl_icon = 'FORWARD'
    bl_width_default = 400

    patch_number: IntProperty(name="Patch Number", default=1, min=1, max=99, description="") 

    def init(self, context):
        for i in range(32):
            self.outputs.new('AudioOutputType', f"Output {i+1}")
        return
    
    def draw_buttons(self, context, layout):  
        layout.prop(self, "patch_number")
        
        
class OutputsNode(Node):
    bl_idname = 'outputs_type'
    bl_label = 'Outputs Node'
    bl_icon = 'BACK'
    bl_width_default = 400

    patch_number: IntProperty(name="Patch Number", default=1, min=1, max=99, description="") 

    def init(self, context):
        for i in range(16):
            input = self.inputs.new('AudioInputType', f"Input {i+1}")
            input.link_limit = 32

        return
    
    def draw_buttons(self, context, layout):  
        layout.prop(self, "patch_number")
        
        
class BusesNode(Node):
    bl_idname = 'buses_type'
    bl_label = 'Buses Node'
    bl_icon = 'OUTLINER_OB_ARMATURE'
    bl_width_default = 400

    patch_number: IntProperty(name="Patch Number", default=1, min=1, max=99, description="")  
    
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
    
    bus_number_enum: EnumProperty(items=get_buses)  

    def init(self, context):
        for i in range(1, 18):  # Assuming 17 buses based on the get_buses method
            input = self.inputs.new('AudioInputType', f"Input {i}")
            input.link_limit = 32 
            self.outputs.new('AudioOutputType', f"Output {i}")
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "bus_number_enum")
        layout.prop(self, "patch_number")

        
        
class DCAsNode(Node):
    bl_idname = 'dcas_type'
    bl_label = 'DCAs Node'
    bl_icon = 'VIEW_CAMERA'
    bl_width_default = 400

    patch_number: IntProperty(name="Patch Number", default=1, min=1, max=99, description="") 

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
        
        
class EQNode(Node):
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
    
    
class CompressorNode(Node):
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
    
    
class GateNode(Node):
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


class ReverbNode(Node):
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


class PhysicalInputsNode(Node):
    bl_idname = 'physical_inputs_type'
    bl_label = 'Physical Inputs'
    bl_icon = 'FORWARD'
    bl_width_default = 400

    def init(self, context):
        input = self.inputs.new('AudioInputType', "Input")
        input.link_limit = 32
        self.outputs.new('AudioOutputType', "Output")
        
        return
    
    def draw_buttons(self, context, layout):  
        return
    

class DanteInputsNode(Node):
    bl_idname = 'dante_inputs_type'
    bl_label = 'Dante Inputs'
    bl_icon = 'FORWARD'
    bl_width_default = 400

    def init(self, context):
        input = self.inputs.new('AudioInputType', "Input")
        input.link_limit = 32
        self.outputs.new('AudioOutputType', "Output")
        
        return
    
    def draw_buttons(self, context, layout):  
        return
    

class USBInputsNode(Node):
    bl_idname = 'usb_inputs_type'
    bl_label = 'USB Inputs'
    bl_icon = 'FORWARD'
    bl_width_default = 400

    def init(self, context):
        input = self.inputs.new('AudioInputType', "Input")
        input.link_limit = 32
        self.outputs.new('AudioOutputType', "Output")
        
        return
    
    def draw_buttons(self, context, layout):  
        return
    

class MADIInputsNode(Node):
    bl_idname = 'madi_inputs_type'
    bl_label = 'MADI Inputs'
    bl_icon = 'FORWARD'
    bl_width_default = 400

    def init(self, context):
        input = self.inputs.new('AudioInputType', "Input")
        input.link_limit = 32
        self.outputs.new('AudioOutputType', "Output")
        
        return
    
    def draw_buttons(self, context, layout):  
        return
    

class AES50AInputsNode(Node):
    bl_idname = 'aes50_a_inputs_type'
    bl_label = 'AES50-A Inputs'
    bl_icon = 'FORWARD'
    bl_width_default = 400

    def init(self, context):
        input = self.inputs.new('AudioInputType', "Input")
        input.link_limit = 32
        self.outputs.new('AudioOutputType', "Output")
        
        return
    
    def draw_buttons(self, context, layout):  
        return
    

class AES50BInputsNode(Node):
    bl_idname = 'aes50_b_inputs_type'
    bl_label = 'AES50-B Inputs'
    bl_icon = 'FORWARD'
    bl_width_default = 400

    def init(self, context):
        input = self.inputs.new('AudioInputType', "Input")
        input.link_limit = 32
        self.outputs.new('AudioOutputType', "Output")

        return

    def draw_buttons(self, context, layout):
        return
    

class AES50AOutputsNode(Node):
    bl_idname = 'aes50_a_outputs_type'
    bl_label = 'AES50-A Outputs'
    bl_icon = 'BACK'
    bl_width_default = 400

    def init(self, context):
        input = self.inputs.new('AudioInputType', "Input")
        input.link_limit = 32
        self.outputs.new('AudioOutputType', "Output")
        
        return
    
    def draw_buttons(self, context, layout):  
        return
    

class AES50BOutputsNode(Node):
    bl_idname = 'aes50_b_outputs_type'
    bl_label = 'AES50-B Outputs'
    bl_icon = 'BACK'
    bl_width_default = 400

    def init(self, context):
        input = self.inputs.new('AudioInputType', "Input")
        input.link_limit = 32
        self.outputs.new('AudioOutputType', "Output")

        return

    def draw_buttons(self, context, layout):
        return
    

class DanteOutputsNode(Node):
    bl_idname = 'dante_outputs_type'
    bl_label = 'Dante Outputs'
    bl_icon = 'BACK'
    bl_width_default = 400

    def init(self, context):
        input = self.inputs.new('AudioInputType', "Input")
        input.link_limit = 32
        self.outputs.new('AudioOutputType', "Output")

        return

    def draw_buttons(self, context, layout):
        return
    

class PhysicalOutputsNode(Node):
    bl_idname = 'physical_outputs_type'
    bl_label = 'Physical Outputs'
    bl_icon = 'BACK'
    bl_width_default = 400

    def init(self, context):
        input = self.inputs.new('AudioInputType', "Input")
        input.link_limit = 32
        self.outputs.new('AudioOutputType', "Output")
        
        return
    
    def draw_buttons(self, context, layout):  
        return
    

class USBOutputsNode(Node):
    bl_idname = 'usb_outputs_type'
    bl_label = 'USB Outputs'
    bl_icon = 'BACK'
    bl_width_default = 400

    def init(self, context):
        input = self.inputs.new('AudioInputType', "Input")
        input.link_limit = 32
        self.outputs.new('AudioOutputType', "Output")
        
        return
    
    def draw_buttons(self, context, layout):  
        return
    

class MADIOutputsNode(Node):
    bl_idname = 'madi_outputs_type'
    bl_label = 'MADI Outputs'
    bl_icon = 'BACK'
    bl_width_default = 400

    def init(self, context):
        input = self.inputs.new('AudioInputType', "Input")
        input.link_limit = 32
        self.outputs.new('AudioOutputType', "Output")
        
        return
    
    def draw_buttons(self, context, layout):  
        return
    

class FaderBankNode(Node):
    bl_idname = 'fader_bank_type'
    bl_label = 'Fader Bank'
    bl_icon = 'FORWARD'
    bl_width_default = 400

    def init(self, context):
        input = self.inputs.new('AudioInputType', "Input")
        input.link_limit = 8
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
class AddInputsNode(Operator):
    bl_idname = "node.add_inputs_node"
    bl_label = ""
    bl_description=""

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('inputs_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
    
    
class AddOutputsNode(Operator):
    bl_idname = "node.add_outputs_node"
    bl_label = ""
    bl_description=""

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('outputs_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
    
    
class AddBusesNode(Operator):
    bl_idname = "node.add_buses_node"
    bl_label = ""
    bl_description=""

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('buses_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
    
    
class AddDCAsNode(Operator):
    bl_idname = "node.add_dcas_node"
    bl_label = ""
    bl_description=""

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('dcas_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
    
    
class AddEQNode(Operator):
    bl_idname = "node.add_eq_node"
    bl_label = ""
    bl_description=""

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('eq_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
    

class AddCompressorNode(Operator):
    bl_idname = "node.add_compressor_node"
    bl_label = ""
    bl_description="lmao it's a foot"

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('compressor_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
    
    
class AddGateNode(Operator):
    bl_idname = "node.add_gate_node"
    bl_label = ""
    bl_description=""

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('gate_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
    
    
class AddReverbNode(Operator):
    bl_idname = "node.add_reverb_node"
    bl_label = ""
    bl_description=""

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('reverb_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
    

class AddPhysicalInputsNode(Operator):
    bl_idname = "node.add_physical_inputs_node"
    bl_label = ""
    bl_description = ""

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('physical_inputs_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}


class AddAES50AInputsNode(Operator):
    bl_idname = "node.add_aes50_a_inputs_node"
    bl_label = ""
    bl_description = ""

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('aes50_a_inputs_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}


class AddAES50BInputsNode(Operator):
    bl_idname = "node.add_aes50_b_inputs_node"
    bl_label = ""
    bl_description = ""

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('aes50_b_inputs_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}


class AddUSBInputsNode(Operator):
    bl_idname = "node.add_usb_inputs_node"
    bl_label = ""
    bl_description = ""

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('usb_inputs_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}


class AddMADIInputsNode(Operator):
    bl_idname = "node.add_madi_inputs_node"
    bl_label = ""
    bl_description = ""

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('madi_inputs_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}


class AddDanteInputsNode(Operator):
    bl_idname = "node.add_dante_inputs_node"
    bl_label = ""
    bl_description = ""

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('dante_inputs_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}


class AddPhysicalOutputsNode(Operator):
    bl_idname = "node.add_physical_outputs_node"
    bl_label = ""
    bl_description = ""

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('physical_outputs_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}


class AddAES50AOutputsNode(Operator):
    bl_idname = "node.add_aes50_a_outputs_node"
    bl_label = ""
    bl_description = ""

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('aes50_a_outputs_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
    

class AddAES50BOutputsNode(Operator):
    bl_idname = "node.add_aes50_b_outputs_node"
    bl_label = ""
    bl_description = ""

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('aes50_b_outputs_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}


class AddUSBOutputsNode(Operator):
    bl_idname = "node.add_usb_outputs_node"
    bl_label = ""
    bl_description = ""

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('usb_outputs_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}


class AddMADIOutputsNode(Operator):
    bl_idname = "node.add_madi_outputs_node"
    bl_label = ""
    bl_description = ""

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('madi_outputs_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}


class AddDanteOutputsNode(Operator):
    bl_idname = "node.add_dante_outputs_node"
    bl_label = ""
    bl_description = ""

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('dante_outputs_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}


class AddFaderBankNode(Operator):
    bl_idname = "node.add_fader_bank_node"
    bl_label = ""
    bl_description = ""

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('fader_bank_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}


class AddMatrixNode(Operator):
    bl_idname = "node.add_matrix_node"
    bl_label = ""
    bl_description = ""

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('matrix_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
    

nodes = [
    InputsNode,
    OutputsNode,
    BusesNode,
    DCAsNode,
    EQNode,
    CompressorNode,
    GateNode,
    ReverbNode,
    PhysicalOutputsNode,
    DanteOutputsNode,
    MADIOutputsNode,
    AES50AOutputsNode,
    AES50BOutputsNode,
    USBInputsNode,
    USBOutputsNode,
    PhysicalInputsNode,
    DanteInputsNode,
    MADIInputsNode,
    AES50AInputsNode,
    AES50BInputsNode,
    FaderBankNode
]

sockets = [
    AudioOutputType,
    AudioInputType,
    AudioTriggerType
]

operators = [
    AddInputsNode,
    AddOutputsNode,
    AddBusesNode,
    AddDCAsNode,
    AddEQNode,
    AddCompressorNode,
    AddGateNode,
    AddReverbNode,
    AddPhysicalInputsNode,
    AddAES50AInputsNode,
    AddAES50BInputsNode,
    AddUSBInputsNode,
    AddMADIInputsNode,
    AddDanteInputsNode,
    AddPhysicalOutputsNode,
    AddAES50AOutputsNode,
    AddAES50BOutputsNode,
    AddUSBOutputsNode,
    AddMADIOutputsNode,
    AddDanteOutputsNode,
    AddFaderBankNode,
    AddMatrixNode
]


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