# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy import spy
#from spy.types import FixtureParameter will not work here.
from bpy.props import IntProperty, StringProperty

'''
Sorcerer does not use big fixture libraries to store every parameter type on every fixture in the universe (like GTDF). 
It only has the basic parameter types built-in.

If you need a more advanced parameter type, you can add your own directly to Sorcerer with a script like this. Your custom
parameter will be treated just like any other built-in parameter if you set it up correctly here. That means it will be 
animatable, will be harmonized with other conflicting controllers, and will receive other benefits from Sorcerer.
'''


class CPV_FP_custom_gobo(spy.types.FixtureParameter): # FP stands for FixtureParameter.
    as_idname = 'alva_gobo_two' # This must be unique, but is not exposed anywhere in the UI.
    as_property_name = 'gobo_two' # This links to the argument in the lighting console's OSC dictionary.
    as_label = "2 Gobo" # This is the label drawn in the UI, typically on the slider. Delete for enum properties.
    icon = 'POINTCLOUD_DATA' # This will be drawn on the popup button for extra settings.
    as_description = "Gobo wheel 2" # This is the tooltip.
    new_row = True # This tells Sorcerer to go to the next row in the parameters section.

    default = 0 # These are like when you create bpy.props properties.
    static_min = 0 # The statics are what we tell Blender. Later we will have dynamics, which are only for Sorcerer.
    static_max = 20

    argument_if_not_found = "# Gobo_Select_2 at $ Enter" # If your as_property_name is not found in the lighting console.

    def poll(context, active_object, object_type): # Not the same as a Python poll function. Only for hiding in Sorcerer.
        return object_type not in {"Influencer", "Brush"} # other types are Key, Fixture, group, strip, Stage Object, and mixer.

    def draw_popup(self, context, active_controller): # Draws when the popup button is pressed, for additional settings.
        layout = self.layout

        if not active_controller: # active_controller is the object, strip, or node currently active per Sorcerer.
            layout.label(text="Active controller not found.")
            return
        
        layout.separator()
        
        split = layout.split(factor=0.5)
        
        row = split.column()
        row.label(text="Enable Gobo Two Speed Argument")
        
        row = split.column()
        row.prop(active_controller, "str_enable_gobo_two_speed_argument", text="", icon='CHECKBOX_HLT') # You must register these.
        
        split_two = layout.split(factor=0.51, align=True)
        
        row_two = split_two.column()
        row_two.label(text="")
        
        row_two = split_two.column(align=True)
        row_two.prop(active_controller, "gobo_two_speed_min", text="Min") # You must register these with Blender yourself as well.
        
        row_two = split_two.column(align=True)
        row_two.prop(active_controller, "gobo_two_speed_max", text="Max")

    def is_new_row(active_object):
        return True

    def update(controller, context):
        spy.update_cpv(controller, context, CPV_FP_custom_gobo) # On update, this sends the appropriate data to the engine.
    

class CPV_FP_custom_gobo_speed(spy.types.FixtureParameter):
    as_idname = 'alva_gobo_two_speed'
    as_property_name = 'gobo_two_speed'
    as_label = "2 Speed"
    as_description = "Gobo 2 rotation speed"

    default = 0
    static_min = -100
    static_max = 100

    # Register the dynamics with Blender yourself please.
    dynamic_min = "gobo_two_speed_min" # The dynamics are the ones the user can control. The static ones are set once.
    dynamic_max = "gobo_two_speed_max" # The dynamics are used to give the user full use of Blender sliders.

    argument_if_not_found = "# Changer_Speed_2 at $ Enter"
    
    def poll(context, active_object, object_type):
        return object_type not in {"Influencer", "Brush"}
    
    def is_new_row(active_object):
        return False

    def update(controller, context):
        spy.update_cpv(controller, context, CPV_FP_custom_gobo_speed)

    def add_special_osc_argument(controller, normal_osc_argument, value): 
        # Use this if your parameter needs extra/special steps on the console to activate and deactivate.
        if value == 0:
            return normal_osc_argument # This is what Sorcerer would normally send by itself.
        
        enable_argument = getattr(controller, f"str_enable_gobo_two_speed_argument")
        return f"{enable_argument}, {normal_osc_argument}"
    

parameters = [
    CPV_FP_custom_gobo,
    CPV_FP_custom_gobo_speed
]


def register():
    for cls in parameters:
        spy.utils.as_register_class(cls) # Remember this uses spy.utils.as_register_class, NOT Blender's bpy version.

    # Register and unregister these with Blender as normal.
    bpy.types.Object.str_enable_gobo_two_speed_argument = StringProperty(
        name="Enable Gobo Two Speed Argument",
        description="Argument for enabling Gobo Two speed",
        default=""
    )

    bpy.types.Object.gobo_two_speed_min = IntProperty(
        name="Gobo Two Speed Min",
        description="Minimum Gobo Two speed value",
        default=-100
    )

    bpy.types.Object.gobo_two_speed_max = IntProperty(
        name="Gobo Two Speed Max",
        description="Maximum Gobo Two speed value",
        default=100
    )


def unregister():
    for cls in reversed(parameters):
        spy.utils.as_unregister_class(cls) # Again, this is spy, not bpy. SorcererPython, not BlenderPython.

    del bpy.types.Object.str_enable_gobo_two_speed_argument
    del bpy.types.Object.gobo_two_speed_min
    del bpy.types.Object.gobo_two_speed_max


if __name__ == '__main__':
    register()