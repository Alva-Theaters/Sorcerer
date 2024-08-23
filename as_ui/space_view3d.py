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

from .space_common import draw_text_or_group_input

# Custom icon stuff
import bpy.utils.previews
import os

preview_collections = {}
pcoll = bpy.utils.previews.new()
preview_collections["main"] = pcoll

addon_dir = os.path.dirname(__file__)
pcoll.load("orb", os.path.join(addon_dir, "alva_orb.png"), 'IMAGE')


def draw_alva_view_3d_view(self, layout):
    pcoll = preview_collections["main"]
    orb = pcoll["orb"]

    layout = self.layout
    layout.separator()
    layout.label(text="Alva Sorcerer", icon_value=orb.icon_id)
    layout.prop(bpy.context.scene.scene_props, "view_viewport_toolbar", text="Toolbar")
    layout.prop(bpy.context.scene.scene_props, "view_ip_address_tool", text="Network")
    layout.prop(bpy.context.scene.scene_props, "view_viewport_command_line", text="Command Line")
    layout.prop(bpy.context.scene.scene_props, "expand_strobe", text="Expand Strobe")


def draw_view3d_cmd_line(self, context):
    if (hasattr(context.scene, "scene_props") and
        context.scene.scene_props.view_viewport_command_line):

        row = self.layout.row()
        row.scale_x = 2
        row.prop(context.scene.scene_props, 'view3d_command_line', text="")


def draw_tool_settings(self, context):
    '''The way this is written is extremely dumb. The issue is the stupid, stupid, stupid 
        context.scene vs context.scene.scene_props stupidity. Need to eventually put 100%
        of scene-registered properties on the scene_props, but haven't yet because doing so
        would introduce hundreds of bugs throughout the codebase.'''
    if (hasattr(context, "scene") and 
        hasattr(context.scene, "scene_props") and context.scene.scene_props.view_ip_address_tool):
        scene = context.scene.scene_props
        layout = self.layout
        row = layout.row(align=True)
        row.prop(context.scene, "lock_ip_settings", text="", icon='LOCKED' if context.scene.lock_ip_settings else 'UNLOCKED')
        row.prop(context.scene, "ip_address_view_options", text="", expand=True)

        if context.scene.ip_address_view_options == 'option_lighting':
            ip = scene.str_osc_ip_address
            port = scene.int_osc_port
            if context.scene.lock_ip_settings:
                row = layout.row()
                row.label(text=f"{ip}:{port}")
            else:
                row = layout.row()
                row.prop(scene, "str_osc_ip_address", text="")
                row = layout.row()
                row.scale_x = .8
                row.prop(scene, "int_osc_port", text=":")

        elif context.scene.ip_address_view_options == 'option_video':
            ip = context.scene.str_video_ip_address
            port = context.scene.int_video_port
            if context.scene.lock_ip_settings:
                row = layout.row()
                row.label(text=f"{ip}:{port}")
            else:
                row = layout.row()
                row.prop(context.scene, "str_video_ip_address", text="")
                row = layout.row()
                row.scale_x = .9
                row.prop(context.scene, "int_video_port", text=":")

        else:
            ip = context.scene.str_audio_ip_address
            port = context.scene.int_audio_port
            if context.scene.lock_ip_settings:
                row = layout.row()
                row.label(text=f"{ip}:{port}")
            else:
                row = layout.row()
                row.prop(context.scene, "str_audio_ip_address", text="")
                row = layout.row()
                row.scale_x = .9
                row.prop(context.scene, "int_audio_port", text=":")
                

def draw_speaker(self, context, active_object):
    ao = active_object
    layout = self.layout
    box = layout.box()
    row = box.row()
    if ao.mixer_type_enum == 'option_qlab':
        row.label(text="Qlab Output:", icon='PLAY_SOUND')
        row.prop(ao, "int_speaker_number", text="crosspoint:")
    elif ao.mixer_type_enum == 'option_m32':
        row.label(text="M32/X32:", icon='PLAY_SOUND')
        row.prop(ao, "int_speaker_number", text="Bus:")
    

def draw_object_header(self, context, scene, active_object, node_layout=None):
    ao = active_object
    identity = ao.object_identities_enum
    
    if hasattr(self, "layout"):
        column = self.layout.column(align=True)
    else:
        column = node_layout.column(align=True)

    box = column.box()
    row = box.row(align=True)
    row.prop(ao, "selected_profile_enum", icon_only=True, icon='SHADERFX')
    draw_text_or_group_input(self, context, row, ao, object=True)

    if identity == "Stage Object":
        row = box.row(align=True)
        row.prop(ao, "str_call_fixtures_command", text="Summon")
        row.operator("viewport.call_fixtures_operator", text = "", icon='LOOP_BACK')
        if ao.audio_is_on:
            row = box.row()
            row.prop(ao, "sound_source_enum", text="", icon='SOUND')
        
    if identity in ["Brush", "Influencer"]:
        row = box.row(align=True)
        row.prop(ao, "float_object_strength", slider = True, text = "Strength:")
        if identity == "Brush":
            row.prop(ao, "is_erasing", icon='GPBRUSH_ERASE_STROKE', text="Erase")

    if scene.is_democratic and identity != "Brush":
        box = column.box()
        row = box.row()
        row.prop(ao, "influence", slider=False, text="Influence:")

    box = column.box()
        
    return box, column


def draw_lighting_modifiers(self, context):
    scene = bpy.context.scene
    layout = self.layout
    layout.operator_menu_enum("viewport.lighting_modifier_add", "type")
    layout.label(text="These don't actually do stuff yet.")

    for mod in scene.lighting_modifiers:
        box = layout.box()

        row = box.row()
        row.use_property_decorate = False
        row.prop(mod, "show_expanded", text="", emboss=False, icon='TRIA_DOWN' if mod.show_expanded else 'TRIA_UP')
        row.prop(mod, "name", text="", emboss = False)

        row.prop(mod, "mute", text="", icon='HIDE_OFF' if not mod.mute else 'HIDE_ON', emboss=False)
        row.use_property_decorate = True

        sub = row.row(align=True)
        props = sub.operator("viewport.lighting_modifier_move", text="", icon='TRIA_UP', emboss=False)
        props.name = mod.name
        props.direction = 'UP'
        props = sub.operator("viewport.lighting_modifier_move", text="", icon='TRIA_DOWN', emboss=False)
        props.name = mod.name
        props.direction = 'DOWN'

        row.operator("viewport.lighting_modifier_remove", text="", icon='X', emboss=False).name = mod.name

        if mod.show_expanded:
            if mod.type == 'option_brightness_contrast':
                col = box.column()
                row = box.row()
                row.prop(mod, "brightness", slider=True)
                row = box.row()
                row.prop(mod, "contrast", slider=True)
            elif mod.type == 'option_saturation':
                row = box.row()
                row.prop(mod, "saturation", slider=True)
            elif mod.type == 'option_hue':
                col = box.column()
                col.prop(mod, "reds", slider=True)
                col.prop(mod, "greens", slider=True)
                col.prop(mod, "blues", slider=True)
            else:
                col = box.column()
                col.prop(mod, "whites", slider=True)
                col.prop(mod, "highlights", slider=True)
                col.prop(mod, "shadows", slider=True)
                col.prop(mod, "blacks", slider=True)