# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

from ..assets.sli import SLI
from ..utils.event_utils import EventUtils

from .utils import get_orb_icon


def draw_settings(self, context, layout=None):
    if not layout:  # If not drawn from a node
        layout = self.layout
        mode = context.scene.scene_props.preferences_enum
        pref_source = context.scene.scene_props
    else:
        mode = self.preferences_enum
        pref_source = self # The node, so different nodes can view different parts of settings
    
    split = layout.split(factor=0.2)
    
    col1 = split.column()
    
    col1.scale_x = 1.3
    col1.scale_y = 1.3
    
    col1.operator("alva_topbar.splash", text="Splash")
    col1.separator()
    col1.prop(pref_source, "preferences_enum", expand=True)

    if not context.scene:
        return
    
    scene = context.scene
    restrictions = SLI.SLI_find_restrictions(scene)
    is_restricted = context.scene.scene_props.school_mode_enabled
    
    col2 = split.column(align=True)
    
    if mode == 'network' and 'network' not in restrictions:
        draw_network(self, context, col2)
        
    elif mode == 'sequencer':
        if 'house_lights' not in restrictions:
            draw_house_lights(self, context, col2)
        if 'sequencer' not in restrictions:
            draw_sequencer(self, context, col2)

    elif mode == 'orb':
        if 'orb' not in restrictions:
            draw_orb(self, context, col2)

    elif mode == 'stage_manager':
        row = col2.row()
        row.label(text="Nothing to display here yet.")
        
    elif mode == 'system': 
        draw_school_mode(self, context, col2, is_restricted)
        if not is_restricted:
            draw_fps(self, context, col2)


def draw_network(self, context, column):
    orb = get_orb_icon()

    scene = context.scene
    vt = scene.alva_settings_view_enum
    core = scene.scene_props.use_alva_core

    box = column.box()
    row = box.row()
    row.label(text="ALVA Network Settings:")
    row.prop(scene.scene_props, "use_alva_core", icon_value=orb.icon_id, text="In-house Mode")

    row = box.row()
    row.prop(scene, "alva_settings_view_enum", expand=True)

    if not core:
        box = column.box()
        row = box.row()
    
    # Animated
    if vt == 'option_animation':
        if core:
            box = box = column.box()
            row = box.row()
        row.alert = scene.scene_props.is_democratic
        row.operator("alva_preferences.democratic", text="Democratic", icon='HEART')
        row.alert = scene.scene_props.is_not_democratic
        row.operator("alva_preferences.nondemocratic", text="Non-democratic", icon='ORPHAN_DATA')
        row.alert = 0
    
    # Lighting
    elif vt == 'option_lighting' and not core:
        row.enabled = not scene.scene_props.use_alva_core
        row.prop(scene.scene_props, "console_type_enum", text="Console")
        row.prop(scene.scene_props, "enable_lighting", expand=True, text="")

        row = box.row()
        row.enabled = not scene.scene_props.use_alva_core
        row.prop(scene.scene_props, "str_osc_ip_address", text="")
        row.prop(scene.scene_props, "int_osc_port", text=":")
        row.prop(scene.scene_props, "int_argument_size", text="x")
    
    # Video &
    elif vt == 'option_video' and not core:
        row.enabled=False
        row.label(text="Video Switcher:")
        row.label(text="Coming soon.")
        row.prop(scene.scene_props, "enable_video", expand=True, text="")
        row = box.row()
        row.enabled=False
        row.prop(scene, "str_video_ip_address", text="")
        row.prop(scene, "int_video_port", text=":")
    
    # Audio
    elif vt == 'option_audio' and not core:
        row.enabled = not scene.scene_props.use_alva_core
        row.prop(scene.scene_props, "mixer_type_enum", text="Mixer")
        row.prop(scene.scene_props, "enable_audio", expand=True, text="")
        row = box.row()
        row.enabled = not scene.scene_props.use_alva_core
        row.prop(scene, "str_audio_ip_address", text="")
        row.prop(scene, "int_audio_port", text=":")

    # Renegade
    if core:
        box = column.box()
        row = box.row()
        row.enabled = False
        row.prop(scene.scene_props, "core_type_enum", text="ALVA Format")
        row.prop(scene.scene_props, "core_enabled", expand=True, text="")
        row = box.row()
        row.enabled = False
        row.prop(scene.scene_props, "str_core_ip_address", text="")
        row.prop(scene.scene_props, "int_core_port", text=":")
        row = box.row()
        row.enabled=False
        row.prop(scene.scene_props, "core_drives_enum", text="", icon='DISC')
        row.operator("alva_preferences.save_dtp", icon='FILE_TICK')

    column.separator()
    column.separator()


def draw_house_lights(self, context, column):
    box = column.box()
    row = box.row()
    row.label(text="Adjust House Lights on Play/Stop:")
    box = column.box()
    row = box.row()
    row.prop(context.scene, "house_down_on_play", text="On Play", slider=True)
    row.prop(context.scene, "house_down_argument", text="")
    row.prop(context.scene, "house_up_on_stop", text="On Stop", slider=True)
    row.prop(context.scene, "house_up_argument", text="")
    column.separator()
    column.separator()


def draw_sequencer(self, context, column):
    active_strip = None
    for area in context.screen.areas:
        if area.type == 'SEQUENCE_EDITOR':
            if context.scene.sequence_editor.active_strip and (context.scene.sequence_editor.active_strip.type == 'COLOR' or context.scene.sequence_editor.active_strip.type == 'SOUND'):
                active_strip = True
                break

    is_scene = False
    has_strip = False

    if active_strip:
        target = context.scene.sequence_editor.active_strip
        has_strip = True
    else:
        target = context.scene
        is_scene = True

    box = column.box()
    row = box.row()
    row.operator("alva_preferences.context_to_scene", text="", icon='SCENE_DATA')
    row.label(text=f"Showing properties for {target.name}:")

    if is_scene or (has_strip and target.type == 'SOUND'):
        row = box.row()
        row.prop(target, "int_cue_list", text="Cue List:") 
        row.prop(target, "int_event_list", text="Event List:")

    row = box.row()
    row.prop(target, "str_start_cue", text="Start Cue") 

    row = box.row()
    row.prop(target, "str_end_cue", text="End Cue")

    row = box.row()
    row.prop(target, "int_start_macro", text="Start Macro:") 
    row.prop(target, "int_end_macro", text="End Macro:")

    row = box.row()
    row.prop(target, "int_start_preset", text="Start Preset:") 
    row.prop(target, "int_end_preset", text="End Preset:")

    column.separator()
    column.separator()
            

def draw_fps(self, context, column):
    # Label section
    box = column.box()
    row = box.row()
    row.label(text="Frames Per Second:")
    
    # FPS section
    box = column.box()
    row = box.row()
    row.label(text=f"True FPS: {str(EventUtils.get_frame_rate(context.scene))}")
    row.prop(context.scene.render, "fps")
    row.prop(context.scene.render, "fps_base")

    column.separator()
    column.separator()
            

def draw_school_mode(self, context, column, is_restricted):
    # Label section
    box = column.box()
    row = box.row()
    row.label(text="School Mode:")
    
    # Enable/Disable section
    box = column.box()
    row = box.row()
    if is_restricted:
        row.label(text="Exit:", icon='LOCKED')
    else:
        row.label(text="Enter:", icon='UNLOCKED')
        
    row = box.row()
    row.prop(context.scene.scene_props, "school_mode_password", text="")

    box.separator()
    
    # Restrictions section
    row = box.row()
    row.label(text="Restrictions:")
    split = box.split(factor=.5)
    scene = context.scene.scene_props
    
    col1 = split.column()
    col1.enabled = not is_restricted
    col1.prop(scene, "restrict_network")
    col1.prop(scene, "restrict_pan_tilt")
    
    col2 = split.column()
    col2.enabled = not is_restricted
    col2.prop(scene, "restrict_patch")

    column.separator()
    column.separator()
    

def draw_orb(self, context, column):
    scene = context.scene
    box = column.box()
    row = box.row()
    row.label(text="Orb:")
    box = column.box()
    
    split = box.split(factor=.5)
    
    col1 = split.column()
    col1.prop(scene, "is_console_saving", text="Orb skips Shift+Update", slider=True)
    col1.separator()
    col1.prop(scene, "orb_chill_time", text="Wait Time:", slider=False)

    col2 = split.column()
    col2.prop(scene, "orb_records_snapshot", text="Orb records snapshot first", slider=True)
    col2.separator()
    col2.prop(scene, "orb_finish_snapshot", text="Snapshot After Orb:", slider=False)

    row = box.row()
    row.use_property_split = True
    row.use_property_decorate = False
    row.prop(context.scene.scene_props, "ghost_out_time", text="Ghost Out Time:")
    row = box.row()
    row.use_property_split = True
    row.use_property_decorate = False
    row.prop(context.scene.scene_props, "ghost_out_string", text="Ghost Out Command:")

    box = column.box()

    row = box.row()
    row.label(text="Allow Orb to have these all to itself in the background:")

    row = box.row()
    row.separator()
    row.prop(scene, "orb_macros_start", text="Macro Range Start:")
    row.prop(scene, "orb_macros_end", text="End:")

    row = box.row()
    row.separator()
    row.prop(scene, "orb_cue_lists_start", text="Cue List Range Start:")
    row.prop(scene, "orb_cue_lists_end", text="End:")

    row = box.row()
    row.separator()
    row.prop(scene, "orb_event_lists_start", text="Event List Range Start:")
    row.prop(scene, "orb_event_lists_end", text="End:")

    row = box.row()
    row.separator()
    row.prop(scene, "orb_presets_start", text="Preset Range Start:")
    row.prop(scene, "orb_presets_end", text="End:")

    box.separator()