# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from .space_common import draw_text_or_group_input, draw_parameters_mini
from .utils import get_orb_icon

DISASTER_THRESHOLD = 3


def draw_alva_view_3d_view(self, layout):
    orb = get_orb_icon()

    layout = self.layout
    layout.separator()
    layout.label(text="Alva Sorcerer", icon_value=orb.icon_id)
    layout.prop(bpy.context.scene.scene_props, "view_viewport_toolbar", text="Toolbar")
    layout.prop(bpy.context.scene.scene_props, "view_ip_address_tool", text="Network")
    layout.prop(bpy.context.scene.scene_props, "view_parameters_header", text="Parameters")
    layout.prop(bpy.context.scene.scene_props, "view_viewport_command_line", text="Command Line")
    layout.prop(bpy.context.scene.scene_props, "expand_strobe", text="Expand Strobe")


def draw_view3d_cmd_line(self, context):
    if (hasattr(context.scene, "scene_props") and
        context.scene.scene_props.view_viewport_command_line and
        context.scene.scene_props.console_type_enum == 'option_eos'):

        row = self.layout.row()
        row.scale_x = 2
        row.prop(context.scene.scene_props, 'view3d_command_line', text="")


def draw_tool_settings(self, context):
    '''The way this is written is extremely dumb. The issue is the stupid, stupid, stupid 
        context.scene vs context.scene.scene_props stupidity. Need to eventually put 100%
        of scene-registered properties on the scene_props, but haven't yet because doing so
        would introduce hundreds of bugs throughout the codebase.'''
    if (hasattr(context, "scene") and 
        hasattr(context.scene, "scene_props")):
        if context.scene.scene_props.school_mode_enabled and context.scene.scene_props.restrict_network:
            return
        
        layout = self.layout
        
        if context.scene.scene_props.view_ip_address_tool:
            scene = context.scene.scene_props
            
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
                    
        if context.area.type != 'VIEW_3D':
            return
        
        obj = context.active_object
        if obj and obj.type == 'MESH' and context.scene.scene_props.view_parameters_header:
            draw_parameters_mini(self, context, layout, obj, use_slider=True, expand=False)
                

def draw_speaker(self, context, active_object, use_split=True):
    ao = active_object
    scene = context.scene.scene_props

    channel_labels = {
        'option_qlab': "Qlab Channel:",
        'option_m32': "M32/X32 Bus:"
    }

    try:
        label = channel_labels[scene.mixer_type_enum]
    except:
        label = "Invalid audio mixer"

    layout = self.layout
    if use_split:
        box = layout.box()
    else:
        box = layout
    box.use_property_split = use_split
    box.use_property_decorate = False

    row = box.row()
    row.prop(ao, "int_speaker_number", text=label)
    # row = box.row()
    # row.prop(ao, "falloff_types", text="Falloff:" if use_split else "Falloff")


def draw_object_header(self, context, scene, active_object, node_layout=None):
    ao = active_object
    identity = ao.object_identities_enum
    
    if hasattr(self, "layout"):
        column = self.layout.column(align=True)
    else:
        column = node_layout.column(align=True)

    box = column.box()
    row = box.row(align=True)
    #row.prop(ao, "selected_profile_enum", icon_only=True, icon='SHADERFX')
    draw_text_or_group_input(self, context, row, ao, object=True)

    if identity == "Stage Object":
        row = box.row(align=True)
        row.prop(ao, "str_call_fixtures_command", text="Summon")
        row.operator("alva_object.summon_movers", text = "", icon='LOOP_BACK')
        if ao.audio_is_on:
            row = box.row()
            row.prop(ao, "sound_source_enum", text="", icon='SOUND')
        
    if identity in ["Brush", "Influencer"]:
        row = box.row(align=True)
        row.prop(ao, "float_object_strength", slider = True, text = "Strength:")
        if identity == "Brush":
            row.prop(ao, "is_erasing", text="Erase", toggle=True)
        else:
            row.prop(ao, "alva_is_absolute", icon='FCURVE', text="")

    if scene.is_democratic and identity != "Brush":
        box = column.box()
        row = box.row()
        row.prop(ao, "influence", slider=False, text="Influence:")

    box = column.box()
        
    return box, column


def draw_lighting_modifiers(self, context):
    scene = bpy.context.scene
    layout = self.layout
    layout.operator_menu_enum("alva_object.add_lighting_modifier", "type")
    layout.label(text="These don't actually do stuff yet.")

    for mod in scene.lighting_modifiers:
        box = layout.box()

        row = box.row()
        row.use_property_decorate = False
        row.prop(mod, "show_expanded", text="", emboss=False, icon='TRIA_DOWN' if mod.show_expanded else 'TRIA_RIGHT')
        row.prop(mod, "name", text="", emboss = False)

        row.prop(mod, "mute", text="", icon='HIDE_OFF' if not mod.mute else 'HIDE_ON', emboss=False)
        row.use_property_decorate = True

        sub = row.row(align=True)
        props = sub.operator("alva_object.bump_lighting_modifier", text="", icon='TRIA_UP', emboss=False)
        props.name = mod.name
        props.direction = 'UP'
        props = sub.operator("alva_object.bump_lighting_modifier", text="", icon='TRIA_DOWN', emboss=False)
        props.name = mod.name
        props.direction = 'DOWN'

        row.operator("alva_object.remove_lighting_modifier", text="", icon='X', emboss=False).name = mod.name

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


def draw_service_mode(self, context):
    scene = context.scene.scene_props
    layout = self.layout

    if scene.limp_mode:
        if len(scene.errors) > DISASTER_THRESHOLD:
            is_disaster = True
        else:
            is_disaster = False

        row = layout.row()
        row.alert = is_disaster
        row.label(text="SORCERER ERRORS:")
        layout.template_list("VIEW3D_UL_alva_errors_list", "", scene, "errors", scene, "errors_index")
    
        try:
            item = scene.errors[scene.errors_index]
            layout.label(text=f"Type: {item.error_type}")
            layout.label(text=f"Explanation: {item.explanation}")
            layout.label(text=f"Severity: {str(item.severity)}")
            layout.label(text="Run from command line for details.")
        except:
            print("Could not find item for service mode UI List.")

    layout.use_property_split = True
    layout.use_property_decorate = False

    scene = context.scene.scene_props

    # OSC
    col = layout.column(heading="OSC")
    col.prop(scene, "print_osc_lighting")
    col.prop(scene, "print_osc_video")
    col.prop(scene, "print_osc_audio")
    col.prop(scene, "print_osc")

    # CPVIA
    col = layout.column(heading="CPVIA")
    col.prop(scene, "print_cpvia_generator")
    col.prop(scene, "print_find")
    col.prop(scene, "print_flags")
    col.prop(scene, "print_harmonizer")
    col.prop(scene, "print_influencers")
    col.prop(scene, "print_map")
    col.prop(scene, "print_mix")
    col.prop(scene, "print_publish")
    col.prop(scene, "print_split_color")
    col.prop(scene, "print_audio")

    # Operators
    col = layout.column(heading="Operators")
    col.prop(scene, "print_common_operators")
    col.prop(scene, "print_cue_builder_operators")
    col.prop(scene, "print_node_operators")
    col.prop(scene, "print_orb_operators")
    col.prop(scene, "print_properties_operators")
    col.prop(scene, "print_sequencer_operators")
    col.prop(scene, "print_strip_formatter_operators")
    col.prop(scene, "print_view3d_operators")

    # Updaters
    col = layout.column(heading="Updaters")
    col.prop(scene, "print_common_updaters")
    col.prop(scene, "print_node_updaters")
    col.prop(scene, "print_properties_updaters")
    col.prop(scene, "print_sequencer_updaters")

    # Main
    col = layout.column(heading="Main")
    col.prop(scene, "print_event_manager")
    col.prop(scene, "print_orb")
    col.prop(scene, "print_time")