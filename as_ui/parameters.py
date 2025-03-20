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
icons_dir = os.path.join(addon_dir, "icons")

pcoll.load("zoom", os.path.join(icons_dir, "zoom.png"), 'IMAGE')
pcoll.load("edge", os.path.join(icons_dir, "edge.png"), 'IMAGE')


def draw_parameters(context, box, active_object):
    pcoll = preview_collections["main"]
    zoom = pcoll["zoom"]
    edge = pcoll["edge"]

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


    strobe_and_color_row_conditions = [
        active_object.strobe_is_on or active_object.color_is_on
    ]

    strobe_conditions = [
        active_object.strobe_is_on,
        object_type not in {"Influencer", "Brush"}
    ]

    color_conditions = [
        active_object.color_is_on
    ]

    restore_color_conditions = [
        hasattr(active_object, "object_identities_enum"),
        object_type == "Influencer"
    ]

    color_profile_conditions = [
        not context.scene.scene_props.school_mode_enabled,
        object_type not in {"Influencer", "Brush"}
    ]

    pan_and_tilt_row_conditions = [
        active_object.pan_tilt_is_on,
        object_type not in {"Stage Object", "Influencer", "Brush"},
        not context.scene.scene_props.school_mode_enabled or not context.scene.scene_props.restrict_pan_tilt,
    ]

    zoom_and_iris_row_conditions = [
        active_object.zoom_is_on or active_object.iris_is_on
    ]

    zoom_conditions = [
        active_object.zoom_is_on
    ]

    iris_conditions = [
        active_object.iris_is_on
    ]

    edge_and_diffusion_conditions = [
        (active_object.edge_is_on or active_object.diffusion_is_on),
        object_type not in {"Influencer", "Brush"}
    ]

    edge_conditions = [
        active_object.edge_is_on
    ]

    diffusion_conditions = [
        active_object.diffusion_is_on
    ]

    gobo_row_conditions = [
        active_object.gobo_is_on,
        object_type not in {"Influencer", "Brush"}
    ]
    
    row = box.row(align=True)
    draw_mute_solo_home_update(space_type, node_name, node_tree_name, active_object, row)
    draw_intensity(active_object, row)

    if all(strobe_and_color_row_conditions):
        row = box.row(align=True)

        if all(strobe_conditions):
            draw_strobe(space_type, node_name, node_tree_name, active_object, row)

        if all(color_conditions):
            draw_color(active_object, row)

            if all(restore_color_conditions):
                draw_restore_color(active_object, row)

            if all(color_profile_conditions):
                draw_color_profile(active_object, row)
  
    if all(pan_and_tilt_row_conditions):
        draw_pan_tilt(space_type, node_name, node_tree_name, active_object, box)

    if all(zoom_and_iris_row_conditions):
        row = draw_zoom_iris_row(space_type, node_name, node_tree_name, zoom, active_object, box)

        if all(zoom_conditions):
            draw_zoom(active_object, row)

        if all(iris_conditions):
            draw_iris(active_object, row)
    
    if all(edge_and_diffusion_conditions):
        row = draw_edge_diffusion_row(space_type, node_name, node_tree_name, edge, box)

        if all(edge_conditions):
            draw_edge(active_object, row)
            
        if all(diffusion_conditions):
            draw_diffusion(active_object, row)
            
    if all(gobo_row_conditions):
        draw_gobo_row(space_type, node_name, node_tree_name, active_object, box)


def draw_mute_solo_home_update(space_type, node_name, node_tree_name, active_object, row):
    # MUTE
    op_mute = row.operator("alva_object.toggle_object_mute", icon='HIDE_ON' if active_object.mute else 'HIDE_OFF', text="")
    op_mute.space_type = space_type
    op_mute.node_name = node_name
    op_mute.node_tree_name = node_tree_name

    # SOLO
    row.prop(active_object, "alva_solo", text="", icon='SOLO_OFF' if not active_object.alva_solo else 'SOLO_ON')

    # HOME
    op_home = row.operator("alva_node.home", icon='HOME', text="")
    op_home.space_type = space_type
    op_home.node_name = node_name
    op_home.node_tree_name = node_tree_name
    
    # UPDATE
    op_update = row.operator("alva_node.update", icon='FILE_REFRESH', text="")
    op_update.space_type = space_type
    op_update.node_name = node_name
    op_update.node_tree_name = node_tree_name


def draw_intensity(active_object, row):
    row.prop(active_object, "alva_intensity", slider=True, text="Intensity")


def draw_strobe(space_type, node_name, node_tree_name, active_object, row):
    op = row.operator("alva_common.strobe_properties", icon='OUTLINER_OB_LIGHTPROBE', text="")
    op.space_type = space_type
    op.node_name = node_name
    op.node_tree_name = node_tree_name

    row.prop(active_object, "alva_strobe", text="Strobe", slider = True)


def draw_color(active_object, row):
    row.prop(active_object, "alva_color", text="")


def draw_restore_color(active_object, row):
    row.prop(active_object, "alva_color_restore", text="")


def draw_color_profile(active_object, row):
    row.prop(active_object, "color_profile_enum", text="", icon='COLOR', icon_only=True)


def draw_pan_tilt(space_type, node_name, node_tree_name, active_object, box):
    row = box.row(align=True)
    op = row.operator("alva_common.pan_tilt_properties", icon='ORIENTATION_GIMBAL', text="")
    op.space_type = space_type
    op.node_name = node_name
    op.node_tree_name = node_tree_name
    
    row.prop(active_object, "alva_pan", text="Pan", slider=True)
    row.prop(active_object, "alva_tilt", text="Tilt", slider=True)


def draw_zoom_iris_row(space_type, node_name, node_tree_name, zoom, active_object, box):
    row = box.row(align=True)
    op = row.operator("alva_common.zoom_iris_properties", text="", icon_value=zoom.icon_id)
    op.space_type = space_type
    op.node_name = node_name
    op.node_tree_name = node_tree_name
    return row
    
    
def draw_zoom(active_object, row):
    row.prop(active_object, "alva_zoom", slider=True, text="Zoom")


def draw_iris(active_object, row):
    row.prop(active_object, "alva_iris", slider=True, text="Iris")


def draw_edge_diffusion_row(space_type, node_name, node_tree_name, edge, box):
    row = box.row(align=True)
    op = row.operator("alva_common.edge_diffusion_properties", text="", icon_value=edge.icon_id)
    op.space_type = space_type
    op.node_name = node_name
    op.node_tree_name = node_tree_name
    return row


def draw_edge(active_object, row):
    row.prop(active_object, "alva_edge", slider=True, text="Edge")


def draw_diffusion(active_object, row):
    row.prop(active_object, "alva_diffusion", slider=True, text="Diffusion")


def draw_gobo_row(space_type, node_name, node_tree_name, active_object, box):
    row = box.row(align=True)
    op = row.operator("alva_common.gobo_properties", text="", icon='POINTCLOUD_DATA')
    op.space_type = space_type
    op.node_name = node_name
    op.node_tree_name = node_tree_name

    row.prop(active_object, "alva_gobo", text="Gobo")
    row.prop(active_object, "alva_gobo_speed", slider=True, text="Speed")
    row.prop(active_object, "alva_prism", slider=True, text="Prism")


def draw_parameters_mini(context, layout, active_object, use_slider=False, expand=True, text=True):
    ao = active_object
    scene = context.scene.scene_props

    omit_end = not scene.is_parameter_bar_expanded and not expand

    layout.use_property_split = expand
    layout.use_property_decorate = expand

    if expand:
        element = layout
    else:
        row = layout.row(align=True)
        row.scale_x = 1 if omit_end else .7
        element = row

    if text:
        element.prop(ao, "str_manual_fixture_selection", text="")
        
    if ao.intensity_is_on:
        element.prop(ao, "alva_intensity", slider=use_slider)
    if ao.strobe_is_on and not omit_end:
        element.prop(ao, "alva_strobe", slider=use_slider)
    if ao.color_is_on:
        element.prop(ao, "alva_color", slider=use_slider, text="Color" if expand else "")
    if ao.pan_tilt_is_on:
        if not (scene.school_mode_enabled and scene.restrict_pan_tilt):
            element.prop(ao, "alva_pan", slider=use_slider)
            element.prop(ao, "alva_tilt", slider=use_slider)
    if ao.zoom_is_on:
        element.prop(ao, "alva_zoom", slider=use_slider)

    if not omit_end:
        if ao.iris_is_on:
            element.prop(ao, "alva_iris", slider=use_slider)
        if ao.edge_is_on:
            element.prop(ao, "alva_edge", slider=use_slider)
        if ao.diffusion_is_on:
            element.prop(ao, "alva_diffusion", slider=use_slider)
        if ao.gobo_is_on:
            element.prop(ao, "alva_gobo", slider=use_slider)
            element.prop(ao, "alva_gobo_speed", slider=use_slider)
            element.prop(ao, "alva_prism", slider=use_slider)

    if not expand:
        layout.prop(scene, "is_parameter_bar_expanded", icon='FORWARD', text="")