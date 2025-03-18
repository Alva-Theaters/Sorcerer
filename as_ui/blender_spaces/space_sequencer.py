# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from functools import partial

from ..utils import determine_sequencer_context, get_strip_class, get_orb_icon

filter_color_strips = partial(filter, bpy.types.ColorSequence.__instancecheck__)


#-------------------------------------------------------------------------------------------------------------------------------------------
'''Misc. Areas'''
#-------------------------------------------------------------------------------------------------------------------------------------------  
def draw_alva_sequencer_view_menu(self, layout):
    orb = get_orb_icon()

    if bpy.context.scene.scene_props.console_type_enum == 'option_eos':
        layout = self.layout
        layout.separator()
        layout.label(text="Alva Sorcerer", icon_value=orb.icon_id)
        layout.prop(bpy.context.scene.scene_props, "view_sequencer_add", text="Add")
        layout.prop(bpy.context.scene.scene_props, "view_sequencer_toolbar", text="Toolbar")
        layout.prop(bpy.context.scene.scene_props, "view_sequencer_command_line", text="Command Line")


def draw_alva_sequencer_add_menu(self, layout):
    if bpy.context.scene.scene_props.view_sequencer_add and bpy.context.scene.scene_props.console_type_enum == 'option_eos':
        orb = get_orb_icon()
        
        layout = self.layout
        layout.separator()
        layout.label(text="Alva Sorcerer", icon_value=orb.icon_id)
        layout.operator("alva_sequencer.add", text="Macro", icon='FILE_TEXT').Option = "option_macro"
        layout.operator("alva_sequencer.add", text="Cue", icon='PLAY').Option = "option_cue"
        layout.operator("alva_sequencer.add", text="Flash", icon='LIGHT_SUN').Option = "option_flash"
        layout.operator("alva_sequencer.add", text="Animation", icon='IPO_BEZIER').Option = "option_animation"
        #layout.operator("alva_sequencer.add", text="Offset", icon='UV_SYNC_SELECT').Option = "option_offset"
        layout.operator("alva_sequencer.add", text="Trigger", icon='SETTINGS').Option = "option_trigger"


def draw_alva_sequencer_strip_menu(self, context):
    if context.scene.scene_props.console_type_enum == 'option_eos':
        orb = get_orb_icon()

        layout = self.layout
        layout.separator()
        layout.label(text="Alva Sorcerer", icon_value=orb.icon_id)
        layout.prop(context.scene, "is_updating_strip_color", text="Sync Strip Color",  slider=True)
        layout.prop(context.scene, "is_armed_release", text="Z Adds Strip on Release", slider=True) 
        layout.prop(context.scene, "strip_end_macros", text="End Frame Macros", slider=True)
        layout.separator()
        layout.prop(context.scene, "cue_builder_toggle", slider=True, text="Cue Builder")
        layout.prop(context.scene, "using_gels_for_cyc", text="Gels for Cyc Color", slider=True)
        layout.prop(context.scene, "cue_builder_id_offset", text="Index Offset", toggle=True)


def draw_alva_sequencer_cmd_line_display(self, context):
    if (hasattr(context.scene, "scene_props") and
        context.scene.scene_props.view_sequencer_command_line):
        layout = self.layout
        scene = context.scene
        layout.prop(context.scene, "is_armed_livemap", text="", icon='PLAY')
        if context.scene.is_armed_livemap:
            layout.label(text=scene.livemap_label)
        layout.label(text=scene.command_line_label)


#-------------------------------------------------------------------------------------------------------------------------------------------
'''Strip Media'''
#-------------------------------------------------------------------------------------------------------------------------------------------  
def draw_strip_media(self, context, scene):
    '''
    This is drawn on the side panel and on the M key popup.
    
    This UI is highly context-specific.
    '''
    layout = self.layout
    scene = context.scene
    box = None

    if not context.scene.scene_props.console_type_enum == 'option_eos':
        return
    
    if not hasattr(scene, "sequence_editor") or not scene.sequence_editor:
        draw_intro_header(self, context, None, scene, None)
        return
    
    sequence_editor = scene.sequence_editor
    if hasattr(sequence_editor, "active_strip") and sequence_editor.active_strip:
        active_strip = sequence_editor.active_strip
        alva_context = determine_sequencer_context(sequence_editor, active_strip)
    else:
        alva_context = "none_relevant"
        
    column = layout.column(align=True)

    context_functions = {
        "no_selection": lambda: draw_no_selection(column),
        "none_relevant": lambda: draw_none_relevant(column),
        "incompatible_types": lambda: draw_incompatible_types(column),
        "only_sound": lambda: draw_only_sound(column, active_strip),
        "one_video_one_audio": lambda: draw_one_audio_one_video(column),
        "only_color": lambda: draw_only_color(column, context, active_strip),
    }

    box = context_functions[alva_context]()
                    
    if alva_context == "only_color":
        box.separator()
    
    formatter = column if alva_context == "only_color" else box

    draw_strip_footer(formatter)
        

# Header --------------------------------------------------------------------------------------------------
def draw_intro_header(self, context, column, scene, active_strip):  # Only drawn very rarely.
    draw_add_buttons_row(self, context, column, scene, active_strip)
    column.separator()
    box = draw_text_insert(self, context, column, text="Welcome to Alva Sorcerer!") 
    return box

def draw_add_buttons_row(column):
    row = column.row(align=True)
    row.operator("alva_sequencer.add", text="", icon='FILE_TEXT').Option = "option_macro"
    row.operator("alva_sequencer.add", text="", icon='PLAY').Option = "option_cue"
    row.operator("alva_sequencer.add", text="", icon='LIGHT_SUN').Option = "option_flash"
    row.operator("alva_sequencer.add", text="", icon='IPO_BEZIER').Option = "option_animation"
    #row.operator("alva_sequencer.add", text="", icon='UV_SYNC_SELECT').Option = "option_offset"
    row.operator("alva_sequencer.add", text="", icon='SETTINGS').Option = "option_trigger"

def draw_text_insert(column, text):
    column.separator()
    box = column.box()
    row = box.row()
    row.label(text=text)
    return box


# Context Draws --------------------------------------------------------------------------------------------------
def draw_no_selection(column):
    draw_add_buttons_row(column)
    column.separator()
    box = draw_text_insert(column, text="No active color strip.")
    return box  

def draw_none_relevant(column): 
    draw_add_buttons_row(column) 
    column.separator()
    box = draw_text_insert(column, text="No relevant strips selected.")
    return box

def draw_incompatible_types(column):
    draw_add_buttons_row(column)
    column.separator()
    box = draw_text_insert(column, text="Incompatible strips selected.")
    return box

def draw_only_sound(column, active_strip):
    orb = get_orb_icon()

    row = column.row(align=True)
    row.operator("alva_sequencer.mute", icon='HIDE_OFF' if not active_strip.mute else 'HIDE_ON')
    row.prop(active_strip, "name", text="")

    column.separator()
    column.separator()

    box = column.box()  

    row = box.row(align=True)
    row.prop(active_strip, "int_start_macro", text="Start Macro #")
    row.operator("alva_orb.orb", icon_value=orb.icon_id, text="").as_orb_id = 'sound'

    row = box.row()
    row.operator("alva_sequencer.analyze_song", icon='SHADERFX')
    return box

def draw_one_audio_one_video(column):  
    draw_add_buttons_row(column)
    column.separator()
    box = draw_text_insert(column, text="Format movie with F key.")
    return box

def draw_only_color(column, context, active_strip):
    as_orb_id = active_strip.my_settings.motif_type_enum
    Strip = get_strip_class(as_orb_id)
    if not Strip:
        return box
    
    box = column.box()
    row = box.row(align=True)
    my_settings = active_strip.my_settings
    row.prop(my_settings, "motif_type_enum", expand=True)
    row.label(text=f"  {Strip.as_label}")
    box = column.box()

    Strip().draw(context, column, box, active_strip)
    return box


# FOOTER --------------------------------------------------------------------------------------------------
def draw_strip_footer(column):
    row = column.row(align=True)
    row.operator("alva_sequencer.bump_horizontal", text="-5", icon='BACK').direction = -5
    row.operator("alva_sequencer.bump_horizontal", text="-1", icon='BACK').direction = -1
    row.operator("alva_sequencer.bump_vertical", icon='TRIA_UP').direction = 1
    row.operator("alva_sequencer.bump_vertical", icon='TRIA_DOWN').direction = -1
    row.operator("alva_sequencer.bump_horizontal", text="1", icon='FORWARD').direction = 1
    row.operator("alva_sequencer.bump_horizontal", text="5", icon='FORWARD').direction = 5
    

# Other Strip Types --------------------------------------------------------------------------------------------------
def draw_strip_sound_object(column, active_strip):
    row = column.row(align=True)
    row.operator('alva_sequencer.refresh_audio_object_selection', icon='FILE_REFRESH', text="")
    row.prop_search(active_strip, "selected_stage_object", bpy.data, "objects", text="", icon='VIEW3D')
    row.operator("alva_sequencer.export_audio", text="", icon='FILE_TICK')
    row = column.row()
    row.prop(active_strip, 'int_sound_cue', text="Sound Cue")
    
def draw_strip_video(self, context):
    if context.scene:
        layout = self.layout
        layout.label(text="Coming by end of 2024: Animate PTZ cameras.")
        layout.separator()
        layout.label(text="&")