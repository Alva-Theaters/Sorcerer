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

from ..assets.sli import SLI
from ..utils.utils import Utils

# Custom icon stuff
import bpy.utils.previews
import os
preview_collections = {}
pcoll = bpy.utils.previews.new()
preview_collections["main"] = pcoll
addon_dir = os.path.dirname(__file__)
pcoll.load("orb", os.path.join(addon_dir, "alva_orb.png"), 'IMAGE')


class SettingsUI:   
    @staticmethod
    def draw_settings(self, context, layout=None):
        if not layout:  # If not drawn from a node
            layout = self.layout
        
        split = layout.split(factor=0.15)
        
        col1 = split.column()
        
        col1.scale_x = 1.3
        col1.scale_y = 1.3
        
        col1.operator("wm.sorcerer_splash", text="Splash")
        col1.separator()
        col1.prop(bpy.context.scene.scene_props, "preferences_enum", expand=True)

        if not context.scene:
            return
        
        mode = context.scene.scene_props.preferences_enum
        scene = context.scene
        sequence_editor = context.scene.sequence_editor
        restrictions = SLI.find_restrictions(scene)
        
        col2 = split.column(align=True)
        
        if mode == 'option_network' and 'network' not in restrictions:
            SettingsUI.draw_network(self, context, col2)
            
        elif mode == 'option_sequencer':
            if 'sequencer' not in restrictions:
                SettingsUI.draw_sync(self, context, col2)
            if 'house_lights' not in restrictions:
                SettingsUI.draw_house_lights(self, context, col2)
            if 'sequencer' not in restrictions:
                SettingsUI.draw_sequencer(self, context, col2)
                SettingsUI.draw_cue_builder(self, context, col2)
            
        elif mode == 'option_3d' and 'patch' not in restrictions:
            SettingsUI.draw_patch(self, context, col2)
            
        elif mode == 'option_nodes':
            row = col2.row()
            row.label(text="Nothing to display here yet.")

        elif mode == 'option_st_sequencer':
            row = col2.row()
            row.label(text="Nothing to display here yet.")

        elif mode == 'option_orb':
            SettingsUI.draw_orb(self, context, col2)
            
        elif mode == 'option_ui' and not scene.scene_props.school_mode_enabled:
            SettingsUI.draw_ui(self, context, col2)
            
        elif mode == 'option_system':
            if not scene.scene_props.school_mode_enabled:
                SettingsUI.draw_fps(self, context, col2)
                
            SettingsUI.draw_school_mode(self, context, col2)
            
    @staticmethod
    def draw_fps(self, context, column):
        # Label section
        box = column.box()
        row = box.row()
        row.label(text="Frames Per Second:")
        
        # FPS section
        box = column.box()
        row = box.row()
        row.label(text=f"True FPS: {str(Utils.get_frame_rate(context.scene))}")
        row.prop(context.scene.render, "fps")
        row.prop(context.scene.render, "fps_base")

        column.separator()
        column.separator()
            
    @staticmethod
    def draw_school_mode(self, context, column):
        is_restricted = context.scene.scene_props.school_mode_enabled
        
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
        col1.prop(scene, "restrict_sequencer")
        col1.prop(scene, "restrict_house_lights")
        col1.prop(scene, "restrict_influencers")
        col1.prop(scene, "restrict_stage_objects")
        
        col2 = split.column()
        col2.enabled = not is_restricted
        col2.prop(scene, "restrict_patch")
        col2.prop(scene, "restrict_strip_media")
        col2.prop(scene, "restrict_pan_tilts")
        col2.prop(scene, "restrict_brushes")

        column.separator()
        column.separator()
    
    @staticmethod    
    def draw_sync(self, context, column):
        box = column.box()
        row = box.row()
        row.label(text="Remotely Manage Console Event List:")
        box = column.box()
        row = box.row()
        row.prop(context.scene, "sync_timecode", slider=True, text="Sync Timecode on Console")
        if context.scene.sync_timecode:
            row.prop(context.scene, "timecode_expected_lag", text="Expected Lag in Frames:")
            row = box.row()
            row.prop(context.scene, "use_default_clock", text="Use default clock", slider=True)
            row.prop(context.scene, "int_event_list", text="Default clock:")

        row = box.row()
        row.prop(context.scene.scene_props, "auto_update_event_list", slider=True, text="Automatically update event list")
        column.separator()
        column.separator()
    
    @staticmethod
    def draw_orb(self, context, column):
        scene = context.scene
        box = column.box()
        row = box.row()
        row.label(text="Livemap and Orb:")
        box = column.box()
        
        split = box.split(factor=.5)
        
        col1 = split.column()
        col1.prop(scene, "is_armed_livemap", text="Livemap", slider=True)   
        col1.separator()
        col1.prop(scene, "is_armed_turbo", text="Orb skips Shift+Update", slider=True)
        col1.separator()
        col1.prop(context.scene.scene_props, "ghost_out_time", text="Ghost Out Time:")

        col2 = split.column()
        col2.prop(scene, "orb_records_snapshot", text="Orb records snapshot first", slider=True)
        col2.separator()
        col2.prop(scene, "orb_finish_snapshot", text="Snapshot After Orb:", slider=False)

        box = column.box()

        row = box.row()
        row.label(text="Orb wants you to spend more time focusing on art rather than on macros.")

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
        
    @staticmethod
    def draw_cue_builder(self, context, column):
        box = column.box()
        row = box.row()
        row.label(text="Cue Builder:")
        box = column.box()
        row = box.row()
        row.prop(context.scene, "cue_builder_toggle", slider=True, text="Visible")
        row.prop(context.scene, "cue_builder_id_offset", text="Cue builder ID offset", toggle=True)
        row = box.row()
        row.prop(context.scene, "using_gels_for_cyc", text="Using gels for cyc color", slider=True)
        column.separator()
        column.separator()
        
    @staticmethod
    def draw_sequencer(self, context, column):
        box = column.box()

        row = box.row()
        row.label(text="Strips:")
        box = column.box()

        row = box.row()
        row.prop(context.scene, "i_know_the_shortcuts", text="Show keyboard shortcuts",  slider=True)    
        row.prop(context.scene, "is_updating_strip_color", text="Update strip color",  slider=True)

        row = box.row()
        row.prop(context.scene, "is_armed_release", text="O adds strip on release", slider=True) 
        row.prop(context.scene, "strip_end_macros", text="Strip end macros", slider=True)

        active_strip = None
        for area in context.screen.areas:
            if area.type == 'SEQUENCE_EDITOR':
                if context.scene.sequence_editor.active_strip and (context.scene.sequence_editor.active_strip.type == 'COLOR' or context.scene.sequence_editor.active_strip.type == 'SOUND'):
                    active_strip = True
                    break

        if active_strip:
            target = context.scene.sequence_editor.active_strip
        else:
            target = context.scene

        box = column.box()
        row = box.row()
        row.label(text=f"Showing properties for {target.name}:")

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
        
    @staticmethod
    def draw_patch(self, context, column):
        box = column.box()
        row = box.row()
        row.label(text="Patch:")
        box = column.box()
        row = box.row()
        row.prop(context.scene.scene_props, "use_name_for_id", text="Use object name for channel #", slider=True) 
        column.separator()
        column.separator()
    
    @staticmethod
    def draw_house_lights(self, context, column):
        box = column.box()
        row = box.row()
        row.label(text="Adjust House Lights on Play/Stop:")
        box = column.box()
        row = box.row()
        row.label(text="OSC Address: ")
        row.prop(context.scene, "house_prefix", text="")
        row = box.row()
        row.prop(context.scene, "house_down_on_play", text="House Down on Play", slider=True)
        row.prop(context.scene, "house_down_argument", text="")
        row = box.row()
        row.prop(context.scene, "house_up_on_stop", text="House Up on Stop", slider=True)
        row.prop(context.scene, "house_up_argument", text="")
        column.separator()
        column.separator()
        
    @staticmethod
    def draw_ui(self, context, column):
        scene = context.scene.scene_props
        
        box = column.box()
        row = box.row()
        row.label(text="Draw:")
        box = column.box()
        
        split = box.split(factor=.5)
        
        col1 = split.column()
        col1.prop(scene, "view_ip_address_tool", text="IP address in viewport", slider=True) 
        col1.prop(scene, "view_node_add", text="Node editor add menu", slider=True)
        col1.prop(scene, "view_sequencer_toolbar", text="Sequencer toolbar", slider=True)  
        
        col2 = split.column()
        col2.prop(scene, "view_sequencer_add", text="Sequencer add menu", slider=True)
        col2.prop(scene, "view_node_toolbar", text="Node editor toolbar", slider=True) 
        col2.prop(scene, "view_viewport_toolbar", text="Viewport toolbar", slider=True)   
        
    @staticmethod
    def draw_network(self, context, column):
        pcoll = preview_collections["main"]
        orb = pcoll["orb"]

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
            row.operator("my.democratic_operator", text="Democratic", icon='HEART')
            row.alert = scene.scene_props.is_not_democratic
            row.operator("my.non_democratic_operator", text="Non-democratic", icon='ORPHAN_DATA')
            row.alert = 0
        
        # Lighting
        elif vt == 'option_lighting' and not core:
            row.enabled = not scene.scene_props.use_alva_core
            row.prop(scene.scene_props, "console_type_enum", text="Lighting Console")
            row.prop(scene.scene_props, "lighting_enabled", expand=True, text="")

            row = box.row()
            row.enabled = not scene.scene_props.use_alva_core
            row.prop(scene.scene_props, "str_osc_ip_address", text="")
            row.prop(scene.scene_props, "int_osc_port", text=":")
            row.prop(scene.scene_props, "int_argument_size", text="x")

            box.separator()

            row = box.row()
            row.prop(scene.scene_props, 'strips_enabled', text="Enable OSC from strips", slider=True)
            row.prop(scene.scene_props, 'objects_enabled', text="Enable OSC from meshes", slider=True)
            row = box.row()
            row.prop(scene.scene_props, 'nodes_enabled', text="Enable OSC from nodes", slider=True)
        
        # Video &
        elif vt == 'option_video' and not core:
            row.enabled=False
            row.label(text="Video Switcher:")
            row.label(text="Coming soon.")
            row.prop(scene.scene_props, "video_enabled", expand=True, text="")
            row = box.row()
            row.enabled=False
            row.prop(scene, "str_video_ip_address", text="")
            row.prop(scene, "int_video_port", text=":")
        
        # Audio
        elif vt == 'option_audio' and not core:
            row.enabled = not scene.scene_props.use_alva_core
            row.prop(scene.scene_props, "mixer_type_enum", text="Audio Mixer")
            row.prop(scene.scene_props, "audio_enabled", expand=True, text="")
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
            row.operator("main.save_dtp_operator", icon='FILE_TICK')

        column.separator()
        column.separator()