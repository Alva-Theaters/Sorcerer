# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

# Custom icon stuff
import bpy.utils.previews
import os

preview_collections = {}
pcoll = bpy.utils.previews.new()
preview_collections["main"] = pcoll

addon_dir = os.path.dirname(__file__)
pcoll.load("orb", os.path.join(addon_dir, "alva_orb.png"), 'IMAGE')

icons_dir = os.path.join(addon_dir, "icons")

pcoll.load("zoom", os.path.join(icons_dir, "zoom.png"), 'IMAGE')
pcoll.load("iris", os.path.join(icons_dir, "iris.png"), 'IMAGE')
pcoll.load("edge", os.path.join(icons_dir, "edge.png"), 'IMAGE')
pcoll.load("diffusion", os.path.join(icons_dir, "diffusion.png"), 'IMAGE')

pcoll.load("sound_dark", os.path.join(icons_dir, "sound_dark.svg"), 'IMAGE')
pcoll.load("color_dark", os.path.join(icons_dir, "color_dark.svg"), 'IMAGE')
pcoll.load("strobe_dark", os.path.join(icons_dir, "strobe_dark.svg"), 'IMAGE')
pcoll.load("pan_tilt_dark", os.path.join(icons_dir, "pan_tilt_dark.svg"), 'IMAGE')
pcoll.load("zoom_dark", os.path.join(icons_dir, "zoom_dark.png"), 'IMAGE')
pcoll.load("iris_dark", os.path.join(icons_dir, "iris_dark.png"), 'IMAGE')
pcoll.load("edge_dark", os.path.join(icons_dir, "edge_dark.png"), 'IMAGE')
pcoll.load("diffusion_dark", os.path.join(icons_dir, "diffusion_dark.svg"), 'IMAGE')
pcoll.load("gobo_dark", os.path.join(icons_dir, "gobo_dark.svg"), 'IMAGE')


def draw_text_or_group_input(context, row_or_box, active_object, object=False):
    space_type, node_tree, node_name, node_tree_name = find_tree_name(context, active_object)

    if object:
        row = row_or_box
    else:
        row = row_or_box.row(align=True)

    op_copy = row.operator("alva_common.copy_patch", text="", icon='SHADERFX')
    op_copy.space_type = space_type
    op_copy.node_name = node_name
    op_copy.node_tree_name = node_tree_name

    # Decision between group and text or just group
    if not active_object.is_text_not_group:
        row.prop(active_object, "selected_group_enum", text = "", icon='COLLECTION_NEW')
    row.prop(active_object, "str_manual_fixture_selection", text = "")


def find_tree_name(context, active_object):
    space_type = context.space_data.type
    
    if space_type == 'NODE_EDITOR':
        node_tree = context.space_data.node_tree
        node_name = active_object.name
        node_tree_name = node_tree.name
    else:
        node_tree = None
        node_name = ""
        node_tree_name = ""
    return space_type, node_tree, node_name, node_tree_name


def find_audio_type(enum_option):
    return True


def draw_footer_toggles(context, column, active_object, box=True, vertical=False):
    pcoll = preview_collections["main"]

    zoom = pcoll["zoom"]
    edge = pcoll["edge"]
    iris = pcoll["iris"]
    diffusion = pcoll["diffusion"]

    strobe_dark = pcoll["strobe_dark"]
    color_dark = pcoll["color_dark"]
    pan_tilt_dark = pcoll["pan_tilt_dark"]
    zoom_dark = pcoll["zoom_dark"]
    iris_dark = pcoll["iris_dark"]
    edge_dark = pcoll["edge_dark"]
    diffusion_dark = pcoll["diffusion_dark"]
    gobo_dark = pcoll["gobo_dark"]

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
    
    if object_type not in ["Influencer", "Brush"]:
        if active_object.strobe_is_on:
            row.prop(active_object, "strobe_is_on", text="", icon='OUTLINER_DATA_LIGHTPROBE', emboss=False)
        else: row.prop(active_object, "strobe_is_on", text="", icon_value=strobe_dark.icon_id, emboss=False)
    
    if active_object.color_is_on:
        row.prop(active_object, "color_is_on", text="", icon='COLOR', emboss=False)
    else: row.prop(active_object, "color_is_on", text="", icon_value=color_dark.icon_id, emboss=False)
    
    if object_type not in ["Stage Object", "Influencer", "Brush"]:
        if not (context.scene.scene_props.school_mode_enabled and context.scene.scene_props.restrict_pan_tilt):
            if active_object.pan_tilt_is_on:
                row.prop(active_object, "pan_tilt_is_on", text="", icon='ORIENTATION_GIMBAL', emboss=False)
            else: row.prop(active_object, "pan_tilt_is_on", text="", icon_value=pan_tilt_dark.icon_id, emboss=False)

    if active_object.zoom_is_on:
        row.prop(active_object, "zoom_is_on", text="", icon_value=zoom.icon_id, emboss=False)
    else: row.prop(active_object, "zoom_is_on", text="", icon_value=zoom_dark.icon_id, emboss=False)

    if active_object.iris_is_on:
        row.prop(active_object, "iris_is_on", text="", icon_value=iris.icon_id, emboss=False)
    else: row.prop(active_object, "iris_is_on", text="", icon_value=iris_dark.icon_id, emboss=False)
    
    if object_type not in ["Influencer", "Brush"]:
        if active_object.edge_is_on:
            row.prop(active_object, "edge_is_on", text="", icon_value=edge.icon_id, emboss=False)
        else: row.prop(active_object, "edge_is_on", text="", icon_value=edge_dark.icon_id, emboss=False)
        
        if active_object.diffusion_is_on:
            row.prop(active_object, "diffusion_is_on", text="", icon_value=diffusion.icon_id, emboss=False)
        else: row.prop(active_object, "diffusion_is_on", text="", icon_value=diffusion_dark.icon_id, emboss=False)

        if active_object.gobo_is_on:
            row.prop(active_object, "gobo_is_on", text="", icon='POINTCLOUD_DATA', emboss=False)
        else: row.prop(active_object, "gobo_is_on", text="", icon_value=gobo_dark.icon_id, emboss=False)

                
def draw_volume_monitor(self, context, sequence_editor):
    active_strip = sequence_editor.active_strip
    layout = self.layout
    box = layout.box()
    row = box.row()
    row.label(text="Volume Monitor (Read-only)")
    is_nothing = True

    if active_strip.selected_stage_object is None:
        row = box.row()
        row.label(text="No participating speaker strips found.")
        return
    
    sound_object = bpy.data.objects[active_strip.selected_stage_object.name]

    object_speakers = None
    for speaker_list in sound_object.speaker_list:
        if speaker_list.name == active_strip.name:
            object_speakers = speaker_list

    if not object_speakers:
        return
    
    speakers = [speaker for speaker in object_speakers.speakers]
    for speaker in speakers:
        if hasattr(active_strip, "selected_stage_object") and active_strip.selected_stage_object is not None:
            row = box.row()
            row.enabled = False
            row.prop(speaker, "dummy_volume", text=f"{speaker.speaker_name} Volume ({speaker.speaker_number})", slider=True)
            is_nothing = False
    if is_nothing:
        row = box.row()
        row.label(text="No participating speaker strips found.")


def draw_play_bar(context, layout):
    '''Copy/pasted from /scripts/startup/bl_ui/space_time.py.
        This is here because the normal keymaps don't work for 
        keyframing in the popup window context.
        
        With modifications from raw source for view_3d space
        compatibility.'''
    scene = context.scene
    screen = context.screen

    row = layout.row(align=True)
    row.label(text="")
    row.operator("screen.frame_jump", text="", icon='REW').end = False
    row.operator("screen.keyframe_jump", text="", icon='PREV_KEYFRAME').next = False
    if not screen.is_animation_playing:
        if scene.sync_mode == 'AUDIO_SYNC' and context.preferences.system.audio_device == 'JACK':
            row.scale_x = 2
            row.operator("screen.animation_play", text="", icon='PLAY')
            row.scale_x = 1
        else:
            row.operator("screen.animation_play", text="", icon='PLAY_REVERSE').reverse = True
            row.operator("screen.animation_play", text="", icon='PLAY')
    else:
        row.scale_x = 2
        row.operator("screen.animation_play", text="", icon='PAUSE')
        row.scale_x = 1
    row.operator("screen.keyframe_jump", text="", icon='NEXT_KEYFRAME').next = True
    row.operator("screen.frame_jump", text="", icon='FF').end = True
    row.label(text="")


def draw_fixture_groups(self, context, pull_fixtures=True):
    layout = self.layout
    scene = context.scene

    row = layout.row()
    row.template_list("COMMON_UL_group_data_list", "", scene, "scene_group_data", scene.scene_props, "group_data_index")

    col = row.column(align=True)
    col.operator("alva_common.add_group", text="", icon='ADD')
    col.operator("alva_common.remove_group", text="", icon='REMOVE')
    if len(scene.scene_group_data) > 1:
        col.separator()
        col.operator("alva_common.bump_group", text="", icon='TRIA_UP').direction = -1
        col.operator("alva_common.bump_group", text="", icon='TRIA_DOWN').direction = 1
    col.separator()
    col.alert = scene.scene_props.highlight_mode
    col.prop(scene.scene_props, "highlight_mode", icon='OUTLINER_OB_LIGHT' if scene.scene_props.highlight_mode else 'LIGHT_DATA', text="")
    col.alert = False

    try:
        item = scene.scene_group_data[scene.scene_props.group_data_index]
    except:
        return
    
    if item.separator or item.label:
        return
    
    sorted_channels = sorted(item.channels_list, key=lambda ch: ch.chan)

    layout.separator()
    col = layout.column()

    has_channels = False
    if len(sorted_channels) != 0:
        has_channels = True
        flow = col.grid_flow(row_major=True, columns=4, align=True)
        for channel in sorted_channels:
            operator = flow.operator("alva_common.remove_or_highlight_channel", text=str(channel.chan), icon='TRASH' if item.highlight_or_remove_enum == 'option_remove' else 'OUTLINER_OB_LIGHT')
            operator.group_id = item.name
            operator.channel = channel.chan
    else:
        col.label(text="Add channels by typing them below.")

    if has_channels:
        layout.separator()

    row = layout.row(align=True)
    if has_channels:
        row.prop(item, "highlight_or_remove_enum", expand=True, text="")
    row.prop(scene.scene_props, "add_channel_ids", text="")

    if pull_fixtures:
        row.operator("alva_object.pull_selection", text="", icon='VIEW3D')


def draw_generate_fixtures(self, context):
    scene = context.scene
    layout = self.layout

    layout.use_property_split = True
    layout.use_property_decorate = False

    if scene.scene_props.school_mode_enabled and scene.scene_props.restrict_patch:
        return
    
    layout.use_property_split = True
    layout.use_property_decorate = False

    layout.column().prop(scene.scene_props, "int_group_number", text="Group")
    layout.column().prop(scene.scene_props, "int_array_start_channel", text="Channel")
    layout.column().prop(scene.scene_props, "int_array_universe", text="Universe")
    layout.column().prop(scene.scene_props, "int_array_start_address", text="Address")
    layout.separator()
    layout.column().prop(scene.scene_props, "int_array_channel_mode", text="Mode")

    layout.separator()
    
    pcoll = preview_collections["main"]
    orb = pcoll["orb"]
    
    layout.operator("alva_orb.orb", text="Generate Fixtures", icon_value=orb.icon_id).as_orb_id = 'viewport'