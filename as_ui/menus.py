# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Menu
from bpy.app.translations import contexts as i18n_contexts


def add_node_type(layout, label, node_type, icon='NONE'): # Heavily borrowed from blender/scripts/startup/bl_ui/node_add_menu.py
    translation_context = i18n_contexts.default
    add_op = layout.operator("node.add_node", text=label, text_ctxt=translation_context, icon=icon) # Not sure why it doesn't want search_weight, as in source
    add_op.type = node_type
    add_op.use_transform = True # This makes it follow cursor until you click.


class NODE_MT_alva_lighting_nodes(Menu):
    bl_idname = "NODE_MT_alva_lighting_nodes"
    bl_label = "Lighting"

    def draw(self, context):
        layout = self.layout
        is_eos = context.scene.scene_props.console_type_enum == 'option_eos'
        add_node_type(layout, "Group Controller", "group_controller_type")
        add_node_type(layout, "Mixer", "mixer_type")
        if is_eos:
            add_node_type(layout, "Direct Selects", "console_buttons_type")
        layout.separator()
        add_node_type(layout, "Settings", "settings_type")
        add_node_type(layout, "Motor", "motor_type")
        #add_node_type(layout, "Flash", "flash_type")
        add_node_type(layout, "Global", "global_type")
        if is_eos:
            add_node_type(layout, "Color Grid", "presets_type")
        add_node_type(layout, "FOH Pan/Tilt", "pan_tilt_type")


class NODE_MT_alva_general_audio_nodes(Menu):
    bl_idname = "NODE_MT_alva_general_audio_nodes"
    bl_label = "General Audio"

    def draw(self, context):
        layout = self.layout
        layout.operator("node.add_fader_bank_node", text="Fader Bank Node", icon='EMPTY_SINGLE_ARROW')
        layout.operator("node.add_buses_node", text="Buses Node", icon='OUTLINER_OB_ARMATURE')
        layout.operator("node.add_matrix_node", text="Matrix Node", icon='NETWORK_DRIVE')
        layout.operator("node.add_dcas_node", text="DCAs Node", icon='VIEW_CAMERA')
        layout.operator("node.add_eq_node", text="EQ Node", icon='SHARPCURVE')
        layout.operator("node.add_compressor_node", text="Compressor Node", icon='MOD_DYNAMICPAINT')
        layout.operator("node.add_gate_node", text="Gate Node", icon='IPO_EXPO')
        layout.operator("node.add_reverb_node", text="Reverb Node", icon='IPO_BOUNCE') 


class NODE_MT_alva_inputs_audio_nodes(Menu):
    bl_idname = "NODE_MT_alva_inputs_audio_nodes"
    bl_label = "Audio Inputs"

    def draw(self, context):
        layout = self.layout
        layout.operator("node.add_physical_inputs_node", text="Physical Inputs Node", icon='FORWARD')
        layout.operator("node.add_aes50_a_inputs_node", text="AES50-A Inputs Node", icon='FORWARD')
        layout.operator("node.add_aes50_b_inputs_node", text="AES50-B Inputs Node", icon='FORWARD')
        layout.operator("node.add_usb_inputs_node", text="USB Inputs Node", icon='FORWARD')
        layout.operator("node.add_madi_inputs_node", text="MADI Inputs Node", icon='FORWARD')
        layout.operator("node.add_dante_inputs_node", text="Dante Inputs Node", icon='FORWARD')


class NODE_MT_alva_outputs_audio_nodes(Menu):
    bl_idname = "NODE_MT_alva_outputs_audio_nodes"
    bl_label = "Audio Outputs"

    def draw(self, context):
        layout = self.layout
        layout.operator("node.add_physical_outputs_node", text="Physical Outputs Node", icon='BACK')
        layout.operator("node.add_aes50_a_outputs_node", text="AES50 Outputs Node", icon='BACK')
        layout.operator("node.add_aes50_b_outputs_node", text="AES50 Outputs Node", icon='BACK')
        layout.operator("node.add_usb_outputs_node", text="USB Outputs Node", icon='BACK')
        layout.operator("node.add_madi_outputs_node", text="MADI Outputs Node", icon='BACK')
        layout.operator("node.add_dante_outputs_node", text="Dante Outputs Node", icon='BACK')


class TEXT_MT_alva_python_templates(Menu):
    bl_idname = 'TEXT_MT_alva_python_templates'
    bl_label = "Alva Sorcerer"

    def draw(self, context):
        layout = self.layout
        layout.operator('alva_text.template_add', text="Lighting Console").template_type = 'lighting_console'
        layout.operator('alva_text.template_add', text="Sequencer Strip").template_type = 'strip'
        layout.operator('alva_text.template_add', text="Lighting Parameter").template_type = 'lighting_parameter'



def draw_text_templates_menu(self, context):
    layout = self.layout
    layout.menu('TEXT_MT_alva_python_templates')
    


menus = [
    NODE_MT_alva_lighting_nodes,
    NODE_MT_alva_general_audio_nodes,
    NODE_MT_alva_inputs_audio_nodes,
    NODE_MT_alva_outputs_audio_nodes,
    TEXT_MT_alva_python_templates
]


def register():
    from bpy.utils import register_class
    for menu in menus:
        register_class(menu)


def unregister():
    from bpy.utils import unregister_class
    for menu in reversed(menus):
        unregister_class(menu)