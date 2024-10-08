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

from bpy.types import Menu
from bpy.app.translations import contexts as i18n_contexts

# Custom icon stuff
import bpy.utils.previews
import os
preview_collections = {}
pcoll = bpy.utils.previews.new()
preview_collections["main"] = pcoll
addon_dir = os.path.dirname(__file__)
pcoll.load("orb", os.path.join(addon_dir, "alva_orb.png"), 'IMAGE')


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


menus = [
    NODE_MT_alva_lighting_nodes,
    NODE_MT_alva_general_audio_nodes,
    NODE_MT_alva_inputs_audio_nodes,
    NODE_MT_alva_outputs_audio_nodes
]


def register():
    from bpy.utils import register_class
    for menu in menus:
        register_class(menu)


def unregister():
    from bpy.utils import unregister_class
    for menu in reversed(menus):
        unregister_class(menu)