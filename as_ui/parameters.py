# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from ..utils.spy_utils import REGISTERED_PARAMETERS

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

pcoll = preview_collections["main"]
zoom = pcoll["zoom"]
edge = pcoll["edge"]

EMPTY = ''
NORMAL_ICON = 'icon'
CUSTOM_ICON = 'custom_icon'
NO_ICON = 'no_icon'

prop_args = ['as_idname', 'as_label', 'icon', 'icon_value', 'is_new_row', 'icon_only']


def draw_parameters(context, box, active_object):
    Parameters(context, box, active_object).execute()


class Parameters:
    def __init__(self, context, box, active_object):
        self.context = context
        self.box = box
        self.active_object = active_object
        self.space_type = context.space_data.type
        self.object_type = self.find_object_type()
        self.set_node_tree_names()
    
    def find_object_type(self):
        if hasattr(self.active_object, "object_identities_enum"):
            return self.active_object.object_identities_enum
        return "Strip"

    def set_node_tree_names(self):
        if self.space_type == 'NODE_EDITOR':
            self.node_tree = self.context.space_data.node_tree
            self.node_name = self.active_object.name
            self.node_tree_name = self.node_tree.name
        else:
            self.node_name = ""
            self.node_tree_name = ""

    def draw_button_with_node_ids(self, as_idname, icon=EMPTY, icon_value=EMPTY):
        if icon != EMPTY:
            op = self.row.operator('alva_common.parameter_popup', icon=icon, text="")
            op.space_type = self.space_type
            op.node_name = self.node_name
            op.node_tree_name = self.node_tree_name
            op.parameter_as_idname = as_idname

        if icon_value != EMPTY:
            icon_id = zoom.icon_id if icon_value == 'zoom' else edge.icon_id # Must go in same script because of Blender bug.
            op = self.row.operator('alva_common.parameter_popup', icon_value=icon_id, text="")
            op.space_type = self.space_type
            op.node_name = self.node_name
            op.node_tree_name = self.node_tree_name
            op.parameter_as_idname = as_idname

    def draw_new_row(self):
        self.row = self.box.row(align=True)


    def execute(self):
        self.draw_new_row()
        DrawButtons(self).execute()
        parameter_classes = self.find_parameter_classes()
        self.draw_all_parameters(parameter_classes)

    def find_parameter_classes(self):
        parameters = []
        for param_class in REGISTERED_PARAMETERS.values():
            param_info = {arg: getattr(param_class, arg, EMPTY) for arg in prop_args}
            param_info = self.add_poll(param_class, param_info)
            param_info = self.add_draw_popup(param_class, param_info)
            parameters.append(param_info)

        return parameters
    
    def add_poll(self, param_class, param_info):
        if hasattr(param_class, "poll"):
            param_info["poll"] = param_class.poll
        return param_info

    def add_draw_popup(self, param_class, param_info):
        if hasattr(param_class, "draw_popup"):
            param_info["popup"] = True
        return param_info
    
    def draw_all_parameters(self, parameter_classes):
        for param_info in parameter_classes:
            if self.should_stop_at_poll(param_info):
                continue
            DrawParameterCombo(self, **param_info).execute()

    def should_stop_at_poll(self, param_info):
        poll_func = param_info.get("poll", None)
        if poll_func and not poll_func(self.context, self.active_object, self.object_type):
            return True


class DrawParameterCombo:
    def __init__(self, Parameters, as_idname, icon=EMPTY, as_label="", icon_only=False, slider=True, popup=None, is_new_row=None, icon_value=EMPTY, poll=None):
        self.Parameters = Parameters
        self.active_object = Parameters.active_object
        self.is_new_row = is_new_row
        self.popup = popup
        self.icon_only = icon_only
        self.as_idname = as_idname
        self.as_label = as_label
        self.icon = icon
        self.icon_value = icon_value
        self.slider = slider
        self.icon_mode = self.find_icon_mode()

    def find_icon_mode(self):
        if self.icon == EMPTY and self.icon_value == EMPTY:
            return NO_ICON
        if self.icon != EMPTY:
            return NORMAL_ICON
        return CUSTOM_ICON
    

    def execute(self):
        self.draw_new_row_if_needed()
        self.draw_popup_button_if_needed()
        self.draw_parameter()

    def draw_new_row_if_needed(self):
        if self.is_new_row and self.is_new_row(self.active_object):
            self.Parameters.draw_new_row()

    def draw_new_row(self):
        self.Parameters.row = self.Parameters.box.row(align=True)

    def draw_popup_button_if_needed(self):
        if self.popup and self.icon_only == EMPTY:
            self.draw_button_with_icon()

    def draw_button_with_icon(self):
        if self.icon_mode == CUSTOM_ICON:
            self.Parameters.draw_button_with_node_ids(self.as_idname, icon_value=self.icon_value)
        if self.icon_mode == NORMAL_ICON:
            self.Parameters.draw_button_with_node_ids(self.as_idname, icon=self.icon)

    def draw_parameter(self):
        icon_style_lookup = {
            NO_ICON: self.draw_parameter_without_icon,
            NORMAL_ICON: self.draw_parameter_with_normal_icon,
            CUSTOM_ICON: self.draw_parameter_without_icon
        }
        icon_style_lookup[self.icon_mode]()

    def draw_parameter_without_icon(self):
        self.Parameters.row.prop(self.active_object, self.as_idname, text=self.as_label, slider=self.slider)
        
    def draw_parameter_with_normal_icon(self):
        icon_id = self.icon_only if self.icon_only != EMPTY else False # Must not be passed as '' or EMPTY
        self.Parameters.row.prop(self.active_object, self.as_idname, icon=self.icon, text=self.as_label, icon_only=icon_id, slider=self.slider)


class DrawButtons:
    def __init__(self, parameters_instance):
        self.Parameters = parameters_instance
        self.row = parameters_instance.row


    def execute(self):
        self.draw_mute()
        self.draw_solo()
        self.draw_home()
        self.draw_update()
    
    def draw_mute(self):
        self.Parameters.draw_button_with_node_ids("alva_object.toggle_object_mute", 
                                                  icon='HIDE_ON' if self.Parameters.active_object.mute else 'HIDE_OFF')
        
    def draw_solo(self):
        self.row.prop(self.Parameters.active_object, "alva_solo", text="", 
                      icon='SOLO_OFF' if not self.Parameters.active_object.alva_solo else 'SOLO_ON')
        
    def draw_home(self):
        self.Parameters.draw_button_with_node_ids("alva_node.home", icon='HOME')
        
    def draw_update(self):
        self.Parameters.draw_button_with_node_ids("alva_node.update", icon='FILE_REFRESH')


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