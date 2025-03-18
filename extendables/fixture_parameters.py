# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy import spy

from ..assets.tooltips import find_tooltip
from ..cpv.cpv_generator import CPVGenerator 


class CPV_FP_intensity(spy.types.FixtureParameter):
    as_idname = 'alva_intensity'
    as_property_name = 'intensity'
    as_label = "Intensity"
    as_description = find_tooltip("intensity")

    default = 0
    min = 0
    max = 100
    

    def draw_row(self, context):
        pass

    def draw_popup(self, context):
        pass

    def update(self, context):
        return CPVGenerator.intensity_updater(self, context) # Must return (generator_class, channels, parameters, values)
    

class CPV_FP_pan(spy.types.FixtureParameter):
    as_idname = 'alva_pan'
    as_property_name = 'pan'
    as_label = "Pan"
    as_description = find_tooltip("pan")

    default = 0
    min = -100
    max = 100
    

    def draw_row(self, context):
        pass

    def draw_popup(self, context):
        pass

    def update(self, context):
        return CPVGenerator.pan_updater(self, context)


class CPV_FP_tilt(spy.types.FixtureParameter):
    as_idname = 'alva_tilt'
    as_property_name = 'tilt'
    as_label = "Tilt"
    as_description = find_tooltip("tilt")

    default = 0
    min = -100
    max = 100
    

    def draw_row(self, context):
        pass

    def draw_popup(self, context):
        pass

    def update(self, context):
        return CPVGenerator.tilt_updater(self, context)


class CPV_FP_color(spy.types.FixtureParameter):
    as_idname = 'alva_color'
    as_property_name = 'color'
    as_label = "Color"
    as_description = find_tooltip("color")

    default = (1.0, 1.0, 1.0)
    min = 0.0
    max = 1.0
    
    new_row = False
    

    def draw_row(self, context):
        pass

    def draw_popup(self, context):
        pass

    def update(self, context):
        return CPVGenerator.color_updater(self, context)
    

class CPV_FP_strobe(spy.types.FixtureParameter):
    as_idname = 'alva_strobe'
    as_property_name = 'strobe'
    as_label = "Strobe"
    as_description = find_tooltip("strobe")

    default = 0
    min = 0
    max = 100
    

    def draw_row(self, context):
        pass

    def draw_popup(self, context):
        pass

    def update(self, context):
        return CPVGenerator.strobe_updater(self, context)
    

class CPV_FP_zoom(spy.types.FixtureParameter):
    as_idname = 'alva_zoom'
    as_property_name = 'zoom'
    as_label = "Zoom"
    as_description = find_tooltip("zoom")

    default = 0
    min = 0
    max = 100
    

    def draw_row(self, context):
        pass

    def draw_popup(self, context):
        pass

    def update(self, context):
        return CPVGenerator.zoom_updater(self, context)
    

class CPV_FP_iris(spy.types.FixtureParameter):
    as_idname = 'alva_iris'
    as_property_name = 'iris'
    as_label = "Iris"
    as_description = find_tooltip("iris")

    default = 0
    min = 0
    max = 100
    

    def draw_row(self, context):
        pass

    def draw_popup(self, context):
        pass

    def update(self, context):
        return CPVGenerator.iris_updater(self, context)
    

class CPV_FP_diffusion(spy.types.FixtureParameter):
    as_idname = 'alva_diffusion'
    as_property_name = 'diffusion'
    as_label = "Diffusion"
    as_description = find_tooltip("diffusion")

    default = 0
    min = 0
    max = 100
    

    def draw_row(self, context):
        pass

    def draw_popup(self, context):
        pass

    def update(self, context):
        return CPVGenerator.diffusion_updater(self, context)
    

class CPV_FP_edge(spy.types.FixtureParameter):
    as_idname = 'alva_edge'
    as_property_name = 'edge'
    as_label = "Edge"
    as_description = find_tooltip("edge")

    default = 0
    min = 0
    max = 100
    

    def draw_row(self, context):
        pass

    def draw_popup(self, context):
        pass

    def update(self, context):
        return CPVGenerator.edge_updater(self, context)
    

class CPV_FP_gobo(spy.types.FixtureParameter):
    as_idname = 'alva_gobo'
    as_property_name = 'gobo'
    as_label = "Gobo"
    as_description = find_tooltip("gobo")

    default = 0
    min = 0
    max = 100
    

    def draw_row(self, context):
        pass

    def draw_popup(self, context):
        pass

    def update(self, context):
        return CPVGenerator.gobo_id_updater(self, context)
    

class CPV_FP_gobo_speed(spy.types.FixtureParameter):
    as_idname = 'alva_gobo_speed'
    as_property_name = 'gobo_speed'
    as_label = "Speed"
    as_description = find_tooltip("speed")

    default = 0
    min = -100
    max = 100
    

    def draw_row(self, context):
        pass

    def draw_popup(self, context):
        pass

    def update(self, context):
        return CPVGenerator.gobo_speed_updater(self, context)
    

class CPV_FP_prism(spy.types.FixtureParameter):
    as_idname = 'alva_prism'
    as_property_name = 'prism'
    as_label = "Prism"
    as_description = find_tooltip("prism")

    default = 0
    min = 0
    max = 1
    

    def draw_row(self, context):
        pass

    def draw_popup(self, context):
        pass

    def update(self, context):
        return CPVGenerator.prism_updater(self, context)
    

parameters = [
    CPV_FP_intensity,
    CPV_FP_pan,
    CPV_FP_tilt,
    CPV_FP_color,
    CPV_FP_strobe,
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