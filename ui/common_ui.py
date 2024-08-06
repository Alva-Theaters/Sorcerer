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

# Custom icon stuff
import bpy.utils.previews
import os
preview_collections = {}
pcoll = bpy.utils.previews.new()
preview_collections["main"] = pcoll
addon_dir = os.path.dirname(__file__)
pcoll.load("orb", os.path.join(addon_dir, "alva_orb.png"), 'IMAGE')


class CommonUI:   
    @staticmethod                
    def draw_toolbar(self, context):
        pcoll = preview_collections["main"]
        orb = pcoll["orb"]
        
        layout = self.layout
        region_width = context.region.width

        num_columns = 1

        flow = layout.grid_flow(row_major=True, columns=num_columns, even_columns=True, even_rows=False, align=True)
        flow.scale_y = 2
        
        space_type = context.space_data.type
        scene = context.scene.scene_props
        
        if space_type == 'SEQUENCE_EDITOR' and scene.view_sequencer_toolbar:
            flow.operator("my.add_macro", icon='REC', text="Macro" if region_width > 200 else "")
            flow.operator("my.add_cue", icon='PLAY', text="Cue" if region_width > 200 else "")
            flow.operator("my.add_flash", icon='LIGHT_SUN', text="Flash" if region_width > 200 else "")
            flow.operator("my.add_animation", icon='IPO_BEZIER', text="Animation" if region_width > 200 else "")
            flow.operator("my.add_offset_strip", icon='UV_SYNC_SELECT', text="Offset" if region_width > 200 else "")
            flow.operator("my.add_trigger", icon='SETTINGS', text="Trigger" if region_width > 200 else "")
            flow.separator()
            flow.operator("seq.render_strips_operator", icon_value=orb.icon_id, text="Render" if region_width > 200 else "")
            flow.operator("my.add_strip_operator", icon='ADD', text="Add Strip" if region_width > 200 else "", emboss=True)
            flow.operator("my.go_to_cue_out_operator", icon='GHOST_ENABLED', text="Cue 0" if region_width > 200 else "")
            flow.operator("my.displays_operator", icon='MENU_PANEL', text="Displays" if region_width > 200 else "")
            flow.operator("my.about_operator", icon='INFO', text="About" if region_width > 200 else "")
            flow.operator("my.copy_above_to_selected", icon='COPYDOWN', text="Disable Clocks" if region_width > 200 else "")
            flow.operator("my.disable_all_clocks_operator", icon='MOD_TIME', text="Disable Clocks" if region_width > 200 else "")
            flow.operator("seq.show_sequencer_settings", icon='PREFERENCES', text="Settings" if region_width > 200 else "")

        elif space_type == 'NODE_EDITOR' and scene.view_node_toolbar:
            flow.operator("node.add_group_controller_node", icon='ADD', text="Add Group" if region_width >= 200 else "", emboss=True)
            flow.operator("my.go_to_cue_out_operator", icon='GHOST_ENABLED', text="Cue 0" if region_width >= 200 else "")
            flow.operator("my.displays_operator", icon='MENU_PANEL', text="Displays" if region_width >= 200 else "")
            flow.operator("my.about_operator", icon='INFO', text="About" if region_width >= 200 else "")
            flow.operator("my.disable_all_clocks_operator", icon='MOD_TIME', text="Disable Clocks" if region_width >= 200 else "")
            flow.operator("seq.show_sequencer_settings", icon='PREFERENCES', text="Settings" if region_width > 200 else "")

        elif space_type == 'VIEW_3D' and scene.view_viewport_toolbar:
            flow.operator("node.add_group_controller_node", icon='ADD', text="Add Group" if region_width >= 200 else "", emboss=True)
            flow.operator("my.go_to_cue_out_operator", icon='GHOST_ENABLED', text="Cue 0" if region_width >= 200 else "")
            flow.operator("my.displays_operator", icon='MENU_PANEL', text="Displays" if region_width >= 200 else "")
            flow.operator("my.about_operator", icon='INFO', text="About" if region_width >= 200 else "")
            flow.operator("my.disable_all_clocks_operator", icon='MOD_TIME', text="Disable Clocks" if region_width >= 200 else "")
            flow.operator("seq.show_sequencer_settings", icon='PREFERENCES', text="Settings" if region_width > 200 else "")


    @staticmethod
    def draw_topbar(self, context):
        if (hasattr(context, "scene") and 
            hasattr(context.scene, "scene_props")): # Avoid unregistration error
            scene = context.scene.scene_props
            layout = self.layout
            layout.prop(scene, "objects_enabled", text="", icon='MESH_CUBE')
            layout.prop(scene, "strips_enabled", text="", icon='SEQUENCE')
            layout.prop(scene, "nodes_enabled", text="", icon='NODETREE')


    @staticmethod
    def draw_tool_settings(self, context):
        if (hasattr(context, "scene") and 
            hasattr(context.scene, "scene_props")): # Avoid unregistration error
            scene = context.scene.scene_props
            layout = self.layout
            column = layout.row()
            column.prop(scene, "str_osc_ip_address", text="Lighting")
            column.label(text=":")
            column.prop(scene, "int_osc_port", text="")

    @staticmethod
    def draw_splash(self, context):
        layout = self.layout
        box = layout.box()

        box.label(text="Welcome to Alva Sorcerer.", icon='INFO')
        box.label(text="Today I'm just a baby, but one day I'll grow big and strong!")
        box.separator()

        row = box.row()
        row.scale_y = 1.5
        row.operator("wm.url_open", text="Learn More").url = "https://www.alvatheaters.com/alva-sorcerer"
        row.operator("wm.url_open", text="Close").url = ""

    @staticmethod
    def draw_text_or_group_input(self, context, row_or_box, active_object, object=False):
        if object:
            row = row_or_box
        else:
            row = row_or_box.row(align=True)

        if not object: 
            row.prop(active_object, "selected_profile_enum", icon_only=True, icon='SHADERFX')

        # Decision between group and text or just group
        if not active_object.is_group_not_manual:
            row.prop(active_object, "selected_group_enum", text = "", icon='COLLECTION_NEW')
        row.prop(active_object, "str_manual_fixture_selection", text = "")

        if object:
            row.operator("object.pull_selection_operator", text="", icon='SHADERFX')
    
    def find_audio_type(enum_option):
        return True
            
    @staticmethod
    def draw_parameters(self, context, column, box, active_object):
        if not hasattr(active_object, "object_identities_enum"):
            object_type = "Strip"
        else:
            object_type = active_object.object_identities_enum
        
        space_type = context.space_data.type
        
        if space_type == 'NODE_EDITOR':
            node_tree = context.space_data.node_tree
            node_name = active_object.name
            node_tree_name = node_tree.name
        else:
            node_name = ""
            node_tree_name = ""
        
        row = box.row(align=True)
        
        # MUTE
        row.operator("object.toggle_object_mute_operator", icon='HIDE_OFF' if active_object.mute else 'HIDE_ON', text="")

        # HOME
        op_home = row.operator("node.home_group", icon='HOME', text="")
        op_home.space_type = space_type
        op_home.node_name = node_name
        op_home.node_tree_name = node_tree_name
        
        # UPDATE
        op_update = row.operator("node.update_group", icon='FILE_REFRESH', text="")
        op_update.space_type = space_type
        op_update.node_name = node_name
        op_update.node_tree_name = node_tree_name
        
        # INTENSITY
        row.prop(active_object, "float_intensity", slider=True, text="Intensity:")
        
        # STROBE
        if active_object.strobe_is_on:
            row_one = row.column(align=True)
            row_one.scale_x = 1
            op = row_one.operator("my.view_strobe_props", icon='OUTLINER_OB_LIGHTPROBE', text="")
            op.space_type = space_type
            op.node_name = node_name
            op.node_tree_name = node_tree_name
        
        # COLOR
        if active_object.color_is_on:
            sub = row.column(align=True)
            sub.scale_x = 0.3
            sub.prop(active_object, "float_vec_color", text="")
            if hasattr(active_object, "object_identities_enum") and object_type == "Influencer":
                sub_two = row.column(align=True)
                sub_two.scale_x = .3
                sub_two.prop(active_object, "float_vec_color_restore", text="")
            sub_two = row.column(align=True)
            # Do not allow students/volunteers to mess up the color profile setting.
            if not context.scene.scene_props.school_mode_enabled:
                sub_two.scale_x = 0.8
                sub_two.prop(active_object, "color_profile_enum", text="", icon='COLOR', icon_only=True)
        
        # SOUND
        if object_type == "Stage Object" and active_object.audio_is_on:
            if CommonUI.find_audio_type(active_object.sound_source_enum):
                row = box.row(align=True)
                row.alert = active_object.mic_is_linked
                row.prop(active_object, "mic_is_linked", text="", icon='LINKED' if active_object.mic_is_linked else 'UNLINKED')
                row.alert = False
                row.prop(active_object, "float_volume", text = "Volume:", slider=True)
    
        # PAN/TILT    
        if active_object.pan_tilt_is_on and object_type not in ["Stage Object", "Influencer", "Brush"]:
            row = box.row(align=True)
            op = row.operator("my.view_pan_tilt_props", icon='ORIENTATION_GIMBAL', text="")
            op.space_type = space_type
            op.node_name = node_name
            op.node_tree_name = node_tree_name
            
            row.prop(active_object, "float_pan", text="Pan", slider=True)
            row.prop(active_object, "float_tilt", text="Tilt", slider=True)
        
        # ZOOM/IRIS
        if active_object.zoom_is_on or active_object.iris_is_on:
            row = box.row(align=True)
            op = row.operator("my.view_zoom_iris_props", text="", icon='LINCURVE')
            op.space_type = space_type
            op.node_name = node_name
            op.node_tree_name = node_tree_name
            
            if active_object.zoom_is_on:
                row.prop(active_object, "float_zoom", slider=True, text="Zoom:")
            if active_object.iris_is_on:
                row.prop(active_object, "float_iris", slider=True, text="Iris:")
        
        # EDGE/DIFFUSION
        if active_object.edge_is_on or active_object.diffusion_is_on:
            row = box.row(align=True)
            op = row.operator("my.view_edge_diffusion_props", text="", icon='SELECT_SET')
            op.space_type = space_type
            op.node_name = node_name
            op.node_tree_name = node_tree_name
            
            if active_object.edge_is_on:
                row.prop(active_object, "float_edge", slider=True, text="Edge:")
            if active_object.diffusion_is_on:
                row.prop(active_object, "float_diffusion", slider=True, text="Diffusion:")
        
        # GOBO
        if active_object.gobo_id_is_on:
            row = box.row(align=True)
            op = row.operator("my.view_gobo_props", text="", icon='POINTCLOUD_DATA')
            op.space_type = space_type
            op.node_name = node_name
            op.node_tree_name = node_tree_name
            
            row.prop(active_object, "int_gobo_id", text="Gobo:")
            row.prop(active_object, "float_gobo_speed", slider=True, text="Speed:")
            row.prop(active_object, "int_prism", slider=True, text="Prism:")
    
    @staticmethod                      
    def draw_volume_monitor(self, context, sequence_editor):
        layout = self.layout
        box = layout.box()
        row = box.row()
        row.label(text="Volume Monitor (Read-only)")
        counter = 0
        for strip in sequence_editor.sequences:
            if strip.type == 'SOUND':
                if hasattr(strip, "selected_speaker") and strip.selected_speaker is not None:
                    label = strip.selected_speaker.name
                    row = box.row()
                    row.enabled = False
                    row.prop(strip, "dummy_volume", text=f"{label} Volume", slider=True)
                    counter += 1
        if counter == 0:
            row = box.row()
            row.label(text="No participating speaker strips found.")
    
    @staticmethod    
    def draw_footer_toggles(self, context, column, active_object, box=True, vertical=False):
        if box: # Normal condition
            box = column.box()
            row = box.row() 
        elif vertical: # For drawing vertically beside UI List
            row = column
            row.alert=0
            row.separator()
            scene = context.scene.scene_props
            row.prop(scene, "expand_toggles", emboss=False, text="", icon='TRIA_LEFT' if scene.expand_toggles else 'TRIA_DOWN')
            row.separator()
            if scene.expand_toggles:
                return
        else: # Normal condition for nodes, no box
            row = column.row() 
        
        if not hasattr(active_object, "object_identities_enum"):
            object_type = "Strip"
        else:
            object_type = getattr(active_object, "object_identities_enum")
        
        if object_type in ["Fixture", "Pan/Tilt Fixture"]:
            row.prop(active_object, "fixture_index_is_locked", emboss = False, icon='LOCKED' if active_object.fixture_index_is_locked else 'UNLOCKED', text="")
        
        if object_type == "Stage Object":
            row.prop(active_object, "audio_is_on", text="", icon='SOUND' if active_object.audio_is_on else 'ADD', emboss=False)
        
        if object_type not in ["Influencer", "Brush"]:
            row.prop(active_object, "strobe_is_on", text="", icon='OUTLINER_DATA_LIGHTPROBE' if active_object.strobe_is_on else 'ADD', emboss=False)
        row.prop(active_object, "color_is_on", text="", icon='COLOR' if active_object.color_is_on else 'ADD', emboss=False)
        
        if object_type not in ["Stage Object", "Influencer", "Brush"]:
            row.prop(active_object, "pan_tilt_is_on", text="", icon='ORIENTATION_GIMBAL' if active_object.pan_tilt_is_on else 'ADD', emboss=False)
        row.prop(active_object, "zoom_is_on", text="", icon='LINCURVE' if active_object.zoom_is_on else 'ADD', emboss=False)
        row.prop(active_object, "iris_is_on", text="", icon='RADIOBUT_OFF' if active_object.iris_is_on else 'ADD', emboss=False)
        
        if object_type not in ["Influencer", "Brush"]:
            row.prop(active_object, "edge_is_on", text="", icon='SELECT_SET' if active_object.edge_is_on else 'ADD', emboss=False)
            row.prop(active_object, "diffusion_is_on", text="", icon='MOD_CLOTH' if active_object.diffusion_is_on else 'ADD', emboss=False)
            row.prop(active_object, "gobo_id_is_on", text="", icon='POINTCLOUD_DATA' if active_object.gobo_id_is_on else 'ADD', emboss=False)
    
    @staticmethod    
    def draw_fixture_groups(self, context):
        layout = self.layout
        scene = context.scene
        
        row = layout.row()
        row.template_list("COMMON_UL_group_data_list", "", scene, "scene_group_data", scene.scene_props, "group_data_index")

        col = row.column(align=True)
        col.operator("patch.add_group_item", text="", icon='ADD')
        
        col.operator("patch.remove_group_item", text="", icon='REMOVE')
        col.separator()
        col.alert = scene.scene_props.highlight_mode
        col.prop(scene.scene_props, "highlight_mode", icon='OUTLINER_OB_LIGHT' if scene.scene_props.highlight_mode else 'LIGHT_DATA', text="")
        col.alert = False

        try:
            item = scene.scene_group_data[scene.scene_props.group_data_index]  # Ensure this line exists to define 'item'
        except:
            return
        
        col.separator()
        col.prop(item, "separator", text="", emboss=1, icon='ARROW_LEFTRIGHT')
        col.prop(item, "label", text="", emboss=1, icon='INFO')
        
        if item.separator or item.label:
            return
        
        CommonUI.draw_footer_toggles(self, context, col, item, box=False, vertical=True)
            
        col = layout.column(align=True)
        box = col.box()
        row = box.row()
        row.label(text="Channels:", icon='CONE')
        box = col.box()
        row = box.row()
        
        sorted_channels = sorted(item.channels_list, key=lambda ch: ch.chan)

        if len(sorted_channels) != 0:
            flow = box.grid_flow(row_major=True, columns=4, align=True)
            for channel in sorted_channels:
                operator = flow.operator("patch.remove_channel", text=str(channel.chan), icon='TRASH' if item.highlight_or_remove_enum == 'option_remove' else 'OUTLINER_OB_LIGHT')
                operator.group_id = item.name
                operator.channel = channel.chan
        else: 
            row.label(text="No channels.")
            row.separator()
        row = box.row(align=True)
        row.prop(item, "highlight_or_remove_enum", expand=True, text="")
        row.prop(scene.scene_props, "add_channel_ids", text="")
        add = row.operator("patch.add_channel", text="", icon='PLUS')
        add.group_id = item.name
        
        if item.strobe_is_on:
            col.separator()
            box = col.box()
            row = box.row()
            row.label(text="Shutter Strobe:", icon='OUTLINER_DATA_LIGHTPROBE')
            box = col.box()
            row = box.row()
            row.label(text="Strobe Enable Argument:")
            row.prop(item, "str_enable_strobe_argument", text="")
            row = box.row()
            row.label(text="Strobe Disable Argument:")
            row.prop(item, "str_disable_strobe_argument", text="")
        
        if item.color_is_on:
            col.separator()
            box = col.box()
            row = box.row()
            row.label(text="Color:", icon='COLOR')
            box = col.box()
            row = box.row()
            row.label(text="Color Profile:")
            row.prop(item, "color_profile_enum", text="")
        
        if item.pan_tilt_is_on:
            col.separator()
            box = col.box()
            row = box.row()
            row.label(text="Pan/Tilt:", icon='ORIENTATION_GIMBAL')
            box = col.box()
            row = box.row()
            row.prop(item, "pan_min", text="Pan Min:")
            row.prop(item, "pan_max", text="Max:")
            row = box.row()
            row.prop(item, "tilt_min", text="Tilt Min:")
            row.prop(item, "tilt_max", text="Max:")

        if item.zoom_is_on:
            col.separator()
            box = col.box()
            row = box.row()
            row.label(text="Zoom:", icon='LINCURVE')
            box = col.box()
            row = box.row()
            row.prop(item, "zoom_min", text="Zoom Min:")
            row.prop(item, "zoom_max", text="Max:")
        
        if item.gobo_id_is_on:
            col.separator()
            box = col.box()
            row = box.row()
            row.label(text="Gobo:", icon='POINTCLOUD_DATA')
            box = col.box()
            row = box.row()
            split = box.split(factor=.5)
            row = split.column()
            row.label(text="Gobo ID Argument")
            row = split.column()
            row.prop(item, "str_gobo_id_argument", text="", icon='POINTCLOUD_DATA')
            
            box.separator()
            
            split = box.split(factor=.5)
            row = split.column()
            row.label(text="Gobo Speed Value Argument")
            row = split.column()
            row.prop(item, "str_gobo_speed_value_argument", text="", icon='CON_ROTLIKE')
            split = box.split(factor=.5)
            row = split.column()
            row.label(text="Enable Gobo Speed Argument")
            row = split.column()
            row.prop(item, "str_enable_gobo_speed_argument", text="", icon='CHECKBOX_HLT')
            split_two = box.split(factor=.51, align=True)
            row_two = split_two.column()
            row_two.label(text="")
            row_two = split_two.column(align=True)
            row_two.prop(item, "gobo_speed_min", text="Min")
            row_two = split_two.column(align=True)
            row_two.prop(item, "gobo_speed_max", text="Max")
            
            split = box.split(factor=.5)
            row = split.column()
            row.label(text="Disable Gobo Speed Argument")
            row = split.column()
            row.prop(item, "str_disable_gobo_speed_argument", text="", icon='CHECKBOX_DEHLT')
            
            layout.separator()
            
            split = box.split(factor=.5)
            row = split.column()
            row.label(text="Enable Prism Argument")
            row = split.column()
            row.prop(item, "str_enable_prism_argument", text="", icon='TRIA_UP')
            
            split = box.split(factor=.5)
            row = split.column()
            row.label(text="Disable Prism Argument")
            row = split.column()
            row.prop(item, "str_disable_prism_argument", text="", icon='PANEL_CLOSE')
            
        row = layout.row()

        add = row.operator("patch.apply_patch_to_objects", text="Apply to Meshes Matching Channels", icon='SHADERFX')
        add.group_id = item.name
        
    @staticmethod
    def draw_generate_fixtures(self, context):
        scene = context.scene
        layout = self.layout
        active_object = context.active_object
        modifiers = []
        
        box = layout.box()
        row = box.row()
        row.label(text="Generate fixtures with console (USITT ASCII):")
        row = box.row(align=True)
        row.prop_search(context.scene.scene_props, "selected_text_block_name", bpy.data, "texts", text="")
        row.operator("my.send_usitt_ascii_to_3d", text="", icon='SHADERFX')
        box.separator()

        if scene.scene_props.console_type_enum == 'option_eos' and not scene.scene_props.school_mode_enabled:
            box = layout.box()
            row = box.row()
            row.label(text="Generate console fixtures with Blender:")
            row = box.row()
            row.prop(scene.scene_props, "array_cone_enum", text="", icon='MESH_CONE')
            row.prop(scene.scene_props, "array_modifier_enum", text="", icon='MOD_ARRAY')
            if scene.scene_props.array_curve_enum !="":
                row.prop(scene.scene_props, "array_curve_enum", text="", icon='CURVE_BEZCURVE')
                row = box.row()
                
            layout.separator()

            split = box.split(factor=.4)
            col = split.column()
            col.label(text="Group #:", icon='STICKY_UVS_LOC')
            col.label(text="Start Chan #:", icon='OUTLINER_OB_LIGHT')
            col.label(text="Group Label:", icon='INFO')
            col.separator()
            col.label(text="Maker:")
            col.label(text="Type:")
            col.label(text="Universe #:")
            col.label(text="Start Addr. #:")
            col.label(text="Channel Mode:")
            
            col2 = split.column()
            col2.prop(scene.scene_props, "int_array_group_index", text="")
            col2.prop(scene.scene_props, "int_array_start_channel", text="")
            col2.prop(scene.scene_props, "str_array_group_name", text="")
            col2.separator()
            col2.prop(scene.scene_props, "str_array_group_maker", text="")
            col2.prop(scene.scene_props, "str_array_group_type", text="")
            col2.prop(scene.scene_props, "int_array_universe", text="")
            col2.prop(scene.scene_props, "int_array_start_address", text="")
            col2.prop(scene.scene_props, "int_array_channel_mode", text="")

            column = box.column()
            CommonUI.draw_footer_toggles(self, context, column, scene.scene_props, box=False)
            
            pcoll = preview_collections["main"]
            orb = pcoll["orb"]
            
            box.operator("array.patch_group_operator", text="Generate Fixtures", icon_value=orb.icon_id)
            
# Slated for next release

#            box = layout.box()
#            row = box.row()
#            row.label(text="Realtime 3D Feedback for Augment3D", icon='VIEW_PAN')
#            
#            row = box.row(align=True)
#            row.scale_y = 1.3
#            row.scale_x = 2
#            row.operator("array.patch_group_operator", text="Spread")
#            row.operator("array.patch_group_operator", text="Bump")
#            row.operator("array.patch_group_operator", text="", icon='BACK')
#            
#            row.operator("array.patch_group_operator", text="", icon='SORT_DESC')
#            row.operator("array.patch_group_operator", text="", icon='SORT_ASC')
#            row.operator("array.patch_group_operator", text="", icon='FORWARD')
#            
#            box.separator()

                
    @staticmethod
    def draw_strobe_settings(self, context, active_controller):
        layout = self.layout
        column = layout.row()
        
        if active_controller:
            split = layout.split(factor=0.5)
            row = split.column()
            row.label(text="Strobe Value", icon='OUTLINER_DATA_LIGHTPROBE')
            row = split.column()
            row.prop(active_controller, "float_strobe", text="", slider=True)
            
            row.operator("popup.keyframe_strobe_popup_operator", text="Keyframe", icon='KEYTYPE_KEYFRAME_VEC')
            
            layout.separator()
            
            if hasattr(active_controller, "str_enable_strobe_argument"):
                split = layout.split(factor=0.5)
                row = split.column()
                row.label(text="Enable Strobe Argument")
                row = split.column()
                row.prop(active_controller, "str_enable_strobe_argument", text="", icon='OUTLINER_DATA_LIGHTPROBE')
                
                split = layout.split(factor=0.5)
                row = split.column()
                row.label(text="Disable Strobe Argument")
                row = split.column()
                row.prop(active_controller, "str_disable_strobe_argument", text="", icon='PANEL_CLOSE')

    @staticmethod    
    def draw_pan_tilt_settings(self, context, active_controller):
        layout = self.layout
        
        if active_controller:
            row = layout.row()
            row.prop(active_controller, "pan_min", text="Pan Min:")
            row.prop(active_controller, "pan_max", text="Max:")
            
            row = layout.row()
            
            row.prop(active_controller, "tilt_min", text="Tilt Min:")
            row.prop(active_controller, "tilt_max", text="Max:")
        else:
            layout.label(text="Active controller not found.")
    
    @staticmethod    
    def draw_zoom_settings(self, context, active_controller):
        layout = self.layout
        
        if active_controller:
            row = layout.row()
            row.prop(active_controller, "zoom_min", text="Zoom Min:")
            row.prop(active_controller, "zoom_max", text="Max:")

        else:
            layout.label(text="Active controller not found.")
    
    @staticmethod 
    def draw_edge_diffusion_settings(self, context, active_controller):   
        layout = self.layout
        
        if active_controller:
            row = layout.row()
            row.label(text="Nothing to adjust here.")
        else:
            layout.label(text="Active controller not found.")
    
    @staticmethod    
    def draw_gobo_settings(self, context, active_controller):
        layout = self.layout

        if active_controller:
            split = layout.split(factor=.5)
            row = split.column()
            row.label(text="Gobo ID Argument")
            row = split.column()
            row.prop(active_controller, "str_gobo_id_argument", text="", icon='POINTCLOUD_DATA')
            
            layout.separator()
            
            split = layout.split(factor=.5)
            row = split.column()
            row.label(text="Gobo Speed Value Argument")
            row = split.column()
            row.prop(active_controller, "str_gobo_speed_value_argument", text="", icon='CON_ROTLIKE')
            split = layout.split(factor=.5)
            row = split.column()
            row.label(text="Enable Gobo Speed Argument")
            row = split.column()
            row.prop(active_controller, "str_enable_gobo_speed_argument", text="", icon='CHECKBOX_HLT')
            split_two = layout.split(factor=.51, align=True)
            row_two = split_two.column()
            row_two.label(text="")
            row_two = split_two.column(align=True)
            row_two.prop(active_controller, "gobo_speed_min", text="Min")
            row_two = split_two.column(align=True)
            row_two.prop(active_controller, "gobo_speed_max", text="Max")
            
            split = layout.split(factor=.5)
            row = split.column()
            row.label(text="Disable Gobo Speed Argument")
            row = split.column()
            row.prop(active_controller, "str_disable_gobo_speed_argument", text="", icon='CHECKBOX_DEHLT')
            
            layout.separator()
            
            split = layout.split(factor=.5)
            row = split.column()
            row.label(text="Enable Prism Argument")
            row = split.column()
            row.prop(active_controller, "str_enable_prism_argument", text="", icon='TRIA_UP')
            
            split = layout.split(factor=.5)
            row = split.column()
            row.label(text="Disable Prism Argument")
            row = split.column()
            row.prop(active_controller, "str_disable_prism_argument", text="", icon='PANEL_CLOSE')
            
        else:
            layout.label(text="Active controller not found.")