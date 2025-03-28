# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy import spy

from ..assets.tooltips import find_tooltip
from ..assets.items import Items


class CPV_FP_intensity(spy.types.FixtureParameter):
    as_idname = 'alva_intensity'
    as_property_name = 'intensity'
    as_label = "Intensity"
    as_description = find_tooltip("intensity")

    default = 0
    static_min = 0
    static_max = 100
    

    def update(controller, context):
        spy.update_cpv(controller, context, CPV_FP_intensity)
    

class CPV_FP_strobe(spy.types.FixtureParameter):
    as_idname = 'alva_strobe'
    as_property_name = 'strobe'
    as_label = "Strobe"
    icon = 'OUTLINER_OB_LIGHTPROBE'
    as_description = find_tooltip("strobe")
    new_row = True

    default = 0
    static_min = 0
    static_max = 100

    dynamic_min = "strobe_min"
    dynamic_max = "strobe_max"
    
    def poll(context, active_object, object_type):
        return active_object.strobe_is_on and object_type not in {"Influencer", "Brush"}

    def draw_popup(self, context, active_controller):
        ac = active_controller

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        if ac and hasattr(ac, "str_enable_strobe_argument"):
            layout.prop(ac, "strobe_min", text="Strobe Min")
            layout.prop(ac, "strobe_max", text="Max")

            layout.separator()
            layout.prop(ac, "str_enable_strobe_argument", text="Enable Argument")
            layout.prop(ac, "str_disable_strobe_argument", text="Disable")

        else:
            layout.label(text="Active controller not found.")

    def is_new_row(active_object):
        return True

    def update(controller, context):
        spy.update_cpv(controller, context, CPV_FP_strobe)

    def add_special_osc_argument(controller, normal_osc_argument, value):
        special_argument = getattr(controller, f"str_{'disable' if value == 0 else 'enable'}_strobe_argument")

        if value != 0:
            return f"{special_argument}, {normal_osc_argument}"
        
        return special_argument


class CPV_FP_color(spy.types.FixtureParameter):
    as_idname = 'alva_color'
    as_property_name = 'color'
    as_description = find_tooltip("color")

    default = (1.0, 1.0, 1.0)
    static_min = 0.0
    static_max = 1.0
    
    def poll(context, active_object, object_type):
        return active_object.color_is_on

    def update(controller, context):
        spy.update_cpv(controller, context, CPV_FP_color)
    
    def is_new_row(active_object):
        if not active_object.strobe_is_on:
            return True
        return False
    

class CPV_FP_color_restore(spy.types.FixtureParameter):
    as_idname = 'alva_color_restore'
    as_description = find_tooltip("color_restore")
    as_property_name = "color_restore"

    default = (1.0, 1.0, 1.0)
    static_min = 0.0
    static_max = 1.0
    
    def poll(context, active_object, object_type):
        return hasattr(active_object, "object_identities_enum") and object_type == "Influencer" and active_object.color_is_on

    def is_new_row(active_object):
        return False
    

class CPV_FP_color_profile_enum(spy.types.FixtureParameter):
    as_idname = 'color_profile_enum'
    as_description = find_tooltip("color_profile_enum")
    as_property_name = "color_profile"
    icon = 'COLOR'
    icon_only = True
    items = Items.color_profiles
    
    def poll(context, active_object, object_type):
        return not context.scene.scene_props.school_mode_enabled and object_type not in {"Influencer", "Brush"} and active_object.color_is_on
    
    def is_new_row(active_object):
        return False
    

class CPV_FP_pan(spy.types.FixtureParameter):
    as_idname = 'alva_pan'
    as_property_name = 'pan'
    as_label = "Pan"
    icon = 'ORIENTATION_GIMBAL'
    as_description = find_tooltip("pan")
    new_row = True

    default = 0
    static_min = -100
    static_max = 100

    dynamic_min = "pan_min"
    dynamic_max = "pan_max"
    
    def poll(context, active_object, object_type):
        return active_object.pan_tilt_is_on and object_type not in {"Stage Object", "Influencer", "Brush"} and not context.scene.scene_props.school_mode_enabled or not context.scene.scene_props.restrict_pan_tilt

    def draw_popup(self, context, active_controller):
        ac = active_controller

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        if ac:
            layout.prop(ac, "pan_min", text="Pan Min")
            layout.prop(ac, "pan_max", text="Max")
            
            layout.separator()
            
            layout.prop(ac, "tilt_min", text="Tilt Min")
            layout.prop(ac, "tilt_max", text="Max")
        else:
            layout.label(text="Active controller not found.")

    def is_new_row(active_object):
        return True

    def update(controller, context):
        spy.update_cpv(controller, context, CPV_FP_pan)
    

class CPV_FP_tilt(spy.types.FixtureParameter):
    as_idname = 'alva_tilt'
    as_property_name = 'tilt'
    as_label = "Tilt"
    as_description = find_tooltip("tilt")

    default = 0
    static_min = -100
    static_max = 100

    dynamic_min = "tilt_min"
    dynamic_max = "tilt_max"
    
    def poll(context, active_object, object_type):
        return active_object.pan_tilt_is_on and object_type not in {"Stage Object", "Influencer", "Brush"} and not context.scene.scene_props.school_mode_enabled or not context.scene.scene_props.restrict_pan_tilt

    def draw_popup(self, context, active_controller):
        ac = active_controller

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        if ac:
            layout.prop(ac, "pan_min", text="Pan Min")
            layout.prop(ac, "pan_max", text="Max")
            
            layout.separator()
            
            layout.prop(ac, "tilt_min", text="Tilt Min")
            layout.prop(ac, "tilt_max", text="Max")
        else:
            layout.label(text="Active controller not found.")

    def is_new_row(active_object):
        return False

    def update(controller, context):
        spy.update_cpv(controller, context, CPV_FP_tilt)


class CPV_FP_zoom(spy.types.FixtureParameter):
    as_idname = 'alva_zoom'
    as_property_name = 'zoom'
    as_label = "Zoom"
    icon_value = 'zoom'
    as_description = find_tooltip("zoom")
    new_row = True

    default = 0
    static_min = 0
    static_max = 100

    dynamic_min = "zoom_min"
    dynamic_max = "zoom_max"
    
    def poll(context, active_object, object_type):
        return active_object.zoom_is_on
    
    def draw_popup(self, context, active_controller):
        ac = active_controller

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        if active_controller:
            layout.prop(ac, "zoom_min", text="Zoom Min")
            layout.prop(ac, "zoom_max", text="Max")

        else:
            layout.label(text="Active controller not found.")

    def is_new_row(active_object):
        return True

    def update(controller, context):
        spy.update_cpv(controller, context, CPV_FP_zoom)
    

class CPV_FP_iris(spy.types.FixtureParameter):
    as_idname = 'alva_iris'
    as_property_name = 'iris'
    as_label = "Iris"
    as_description = find_tooltip("iris")

    default = 100
    static_min = 0
    static_max = 100
    
    def poll(context, active_object, object_type):
        return active_object.iris_is_on
    
    def draw_popup(self, context, active_controller):
        ac = active_controller

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        if active_controller:
            layout.prop(ac, "zoom_min", text="Zoom Min")
            layout.prop(ac, "zoom_max", text="Max")

        else:
            layout.label(text="Active controller not found.")

    def is_new_row(active_object):
        if not active_object.zoom_is_on:
            return True
        return False

    def update(controller, context):
        spy.update_cpv(controller, context, CPV_FP_iris)
    

class CPV_FP_edge(spy.types.FixtureParameter):
    as_idname = 'alva_edge'
    as_property_name = 'edge'
    as_label = "Edge"
    icon_value = 'edge'
    as_description = find_tooltip("edge")
    new_row = True

    default = 0
    static_min = 0
    static_max = 100
    
    def poll(context, active_object, object_type):
        return active_object.edge_is_on

    def draw_popup(self, context, active_controller):
        layout = self.layout
        
        if active_controller:
            row = layout.row()
            row.label(text="Nothing to adjust here.")
        else:
            layout.label(text="Active controller not found.")

    def is_new_row(active_object):
        return True

    def update(controller, context):
        spy.update_cpv(controller, context, CPV_FP_edge)


class CPV_FP_diffusion(spy.types.FixtureParameter):
    as_idname = 'alva_diffusion'
    as_property_name = 'diffusion'
    as_label = "Diffusion"
    as_description = find_tooltip("diffusion")

    default = 0
    static_min = 0
    static_max = 100
    
    def poll(context, active_object, object_type):
        return active_object.diffusion_is_on

    def draw_row(self, context):
        pass

    def draw_popup(self, context, active_controller):
        layout = self.layout
        
        if active_controller:
            row = layout.row()
            row.label(text="Nothing to adjust here.")
        else:
            layout.label(text="Active controller not found.")

    def is_new_row(active_object):
        if not active_object.edge_is_on:
            return True
        return False

    def update(controller, context):
        spy.update_cpv(controller, context, CPV_FP_diffusion)
    

class CPV_FP_gobo(spy.types.FixtureParameter):
    as_idname = 'alva_gobo'
    as_property_name = 'gobo'
    as_label = "Gobo"
    icon = 'POINTCLOUD_DATA'
    as_description = find_tooltip("gobo")
    new_row = True

    default = 0
    static_min = 0
    static_max = 20

    def poll(context, active_object, object_type):
        return active_object.gobo_is_on and object_type not in {"Influencer", "Brush"}

    def draw_popup(self, context, active_controller):
        layout = self.layout

        if not active_controller:
            layout.label(text="Active controller not found.")
            return
        
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

    def is_new_row(active_object):
        return True

    def update(controller, context):
        spy.update_cpv(controller, context, CPV_FP_gobo)
    

class CPV_FP_gobo_speed(spy.types.FixtureParameter):
    as_idname = 'alva_gobo_speed'
    as_property_name = 'gobo_speed'
    as_label = "Speed"
    as_description = find_tooltip("speed")

    default = 0
    static_min = -100
    static_max = 100

    dynamic_min = "gobo_speed_min"
    dynamic_max = "gobo_speed_max"
    
    def poll(context, active_object, object_type):
        return active_object.gobo_is_on and object_type not in {"Influencer", "Brush"}
    
    def is_new_row(active_object):
        return False

    def update(controller, context):
        spy.update_cpv(controller, context, CPV_FP_gobo_speed)

    def add_special_osc_argument(controller, normal_osc_argument, value):
        if value == 0:
            return normal_osc_argument
        
        special_argument = getattr(controller, f"str_enable_gobo_speed_argument")
        return f"{special_argument}, {normal_osc_argument}"
    

class CPV_FP_prism(spy.types.FixtureParameter):
    as_idname = 'alva_prism'
    as_property_name = 'prism'
    as_label = "Prism"
    as_description = find_tooltip("prism")

    default = 0
    static_min = 0
    static_max = 1
    
    def poll(context, active_object, object_type):
        return active_object.gobo_is_on and object_type not in {"Influencer", "Brush"}
    
    def is_new_row(active_object):
        return False

    def update(controller, context):
        spy.update_cpv(controller, context, CPV_FP_prism)

    def add_special_osc_argument(controller, normal_osc_argument, value):
        if value == 1:
            return getattr(controller, f"str_enable_prism_argument")
        return getattr(controller, f"str_disable_prism_argument")
    

parameters = [
    CPV_FP_intensity,
    CPV_FP_strobe,
    CPV_FP_color,
    CPV_FP_color_restore,
    CPV_FP_color_profile_enum,
    CPV_FP_pan,
    CPV_FP_tilt,
    CPV_FP_zoom,
    CPV_FP_iris,
    CPV_FP_edge,
    CPV_FP_diffusion,
    CPV_FP_gobo,
    CPV_FP_gobo_speed,
    CPV_FP_prism
]


def register():
    for cls in parameters:
        spy.utils.as_register_class(cls)


def unregister():
    for cls in reversed(parameters):
        spy.utils.as_unregister_class(cls)


