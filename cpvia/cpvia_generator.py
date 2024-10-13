# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from functools import partial
import time

from ..cpvia.find import Find 
from ..cpvia.cpvia_finders import CPVIAFinders 
from ..cpvia.split_color import ColorSplitter 
from ..cpvia.flags import check_flags
from ..maintenance.logging import alva_log


'''
The CPVIA system is essentially a communication protocol similar to DMX used only in Sorcerer.

A CPVIA request is a tuple containing Channel, Parameter, Value, Influence, Argument. 

A CPVIA request is made any time a single controller wishes to make a parameter change on the console.
We use the CPVIA protocol to standardize how all parameter change requests are made no matter the 
controller type, no matter the space_type. In frame change and during playback, CPVIA requests are
compared to one another for common simplifcation and harminization to avoid spamming contradictory 
messages and to batch commands together.

The cpvia_generator function is responsible for building each CPVIA request using an army of helper 
functions. Effort should be taken to keep as much logic out of the cpvia_generator itself to keep 
it readable and easy to debug.
'''


class CPVIAGenerator:
    @staticmethod
    def cpvia_generator(self, context, property_name, find_function):
        """
        Universal updater function that contains the common logic for all property updates.

        Parameters:
        self: The instance from which this function is called.
        context: The current context.
        property_name (str): The name of the property to update.
        find_function (function): The function that finds the channels and values for the given property.
        """
        start = time.time()

        finders = Find()
        alva_log("cpvia_generator", f"CPVIA Initial: {property_name}, {self}")

        p = property_name  # Inherited from the partial.
        mode = p
        parent = finders.find_parent(self)

        from .publish import Publisher
        publisher = Publisher()
        if isinstance(context.space_data, bpy.types.SpaceView3D):
            publisher.update_other_selections(context, parent, p)

        c, p, v, type = find_function(parent, p)  # Should return 3 lists and a string. find_function() is find_my_channels_and_values().

        if not check_flags(context, parent, c, p, v, type):
            return

        if mode == "color":
            color_splitter = ColorSplitter()
            p, v = color_splitter.split_color(parent, c, p, v, type)

        i = []
        a = []
        influence = parent.influence

        alva_log("cpvia_generator", f"CPV: {c}, {p}, {v}")
        for chan, param, val in zip(c, p, v):
            argument = finders.find_my_argument_template(parent, type, chan, param, val)
            i.append(influence)
            a.append(argument)

        #is_rendering = EventUtils.is_rendered_mode()
        is_rendering = False # Until Blender fixes their stuff. Can't enable render mode without immediately crashing.
        alva_log("cpvia_generator", f"CPVIA: {c}, {p}, {v}, {i}, {a}")
        for chan, param, val, inf, arg in zip(c, p, v, i, a):
            if param in ["intensity", "raise_intensity", "lower_intensity", "color", "raise_color", "lower_color"] and is_rendering:
                publisher.render_in_viewport(parent, chan, param, val)
            publisher.send_cpvia(chan, param, val, inf, arg)

        alva_log('time', f"cpvia_generator took {time.time() - start} seconds")


    '''These are the universal updater partial calls for direct 
       lighting parameter properties.'''
    @staticmethod
    def intensity_updater(self, context):
        return intensity_partial(self, context)
    @staticmethod
    def color_updater(self, context):
        return color_partial(self, context)
    @staticmethod
    def pan_updater(self, context):
        return pan_partial(self, context)
    @staticmethod
    def tilt_updater(self, context):
        return tilt_partial(self, context)
    @staticmethod
    def pan_graph_updater(self, context):  # For pan/tilt nodes.
        return pan_graph_partial(self, context)
    @staticmethod
    def tilt_graph_updater(self, context):  # For pan/tilt nodes.
        return tilt_graph_partial(self, context)
    @staticmethod
    def strobe_updater(self, context):
        return strobe_partial(self, context)
    @staticmethod
    def zoom_updater(self, context):
        return zoom_partial(self, context)
    @staticmethod
    def iris_updater(self, context):
        return iris_partial(self, context)
    @staticmethod
    def diffusion_updater(self, context):
        return diffusion_partial(self, context)
    @staticmethod
    def edge_updater(self, context):
        return edge_partial(self, context)
    @staticmethod
    def gobo_id_updater(self, context):
        return gobo_id_partial(self, context)
    @staticmethod
    def gobo_speed_updater(self, context):
        return gobo_speed_partial(self, context)
    @staticmethod
    def prism_updater(self, context):
        return prism_partial(self, context)


#-------------------------------------------------------------------------------------------------------------------------------------------
'''PARTIALS'''
#------------------------------------------------------------------------------------------------------------------------------------------- 
finders_instance = CPVIAFinders()
cpvia_generator = CPVIAGenerator  # No instance. Preserve controller's self.


intensity_partial = partial(cpvia_generator.cpvia_generator, property_name="intensity", find_function=finders_instance.find_my_channels_and_values)
color_partial = partial(cpvia_generator.cpvia_generator, property_name="color", find_function=finders_instance.find_my_channels_and_values)
pan_partial = partial(cpvia_generator.cpvia_generator, property_name="pan", find_function=finders_instance.find_my_channels_and_values)
tilt_partial = partial(cpvia_generator.cpvia_generator, property_name="tilt", find_function=finders_instance.find_my_channels_and_values)
pan_graph_partial = partial(cpvia_generator.cpvia_generator, property_name="pan_graph", find_function=finders_instance.find_my_channels_and_values)
tilt_graph_partial = partial(cpvia_generator.cpvia_generator, property_name="tilt_graph", find_function=finders_instance.find_my_channels_and_values)
strobe_partial = partial(cpvia_generator.cpvia_generator, property_name="strobe", find_function=finders_instance.find_my_channels_and_values)
zoom_partial = partial(cpvia_generator.cpvia_generator, property_name="zoom", find_function=finders_instance.find_my_channels_and_values)
iris_partial = partial(cpvia_generator.cpvia_generator, property_name="iris", find_function=finders_instance.find_my_channels_and_values)
diffusion_partial = partial(cpvia_generator.cpvia_generator, property_name="diffusion", find_function=finders_instance.find_my_channels_and_values)
edge_partial = partial(cpvia_generator.cpvia_generator, property_name="edge", find_function=finders_instance.find_my_channels_and_values)
gobo_id_partial = partial(cpvia_generator.cpvia_generator, property_name="gobo_id", find_function=finders_instance.find_my_channels_and_values)
gobo_speed_partial = partial(cpvia_generator.cpvia_generator, property_name="gobo_speed", find_function=finders_instance.find_my_channels_and_values)
prism_partial = partial(cpvia_generator.cpvia_generator, property_name="prism", find_function=finders_instance.find_my_channels_and_values)


def test_cpvia_generator(SENSITIVITY): # Return True for fail, False for pass
    return False