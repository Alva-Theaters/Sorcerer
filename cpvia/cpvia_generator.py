# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from functools import partial
import time

from ..cpvia.cpvia_finders import CPVIAFinders 
from ..cpvia.split_color import ColorSplitter 
from ..cpvia.flags import check_flags
from ..maintenance.logging import alva_log
from .publish import Publisher
from ..utils.cpvia_utils import add_influence_and_argument, publish_updates
from ..utils.event_utils import EventUtils


'''
The CPVIA system is essentially a communication protocol similar to DMX used only in Sorcerer.

A CPVIA request is a tuple containing Channel, Parameter, Value, Influence, Argument. 

A CPVIA request is made any time a single controller wishes to make a parameter change on the console.
We use the CPVIA protocol to standardize how all parameter change requests are made no matter the 
controller type, no matter the space_type. In frame change and during playback, CPVIA requests are
compared to one another for common simplifcation and harmonization to avoid spamming contradictory 
messages and to batch commands together.

The cpvia_generator function is responsible for building each CPVIA request using an army of helper 
functions. Effort should be taken to keep as much logic out of the cpvia_generator itself to keep 
it readable and easy to debug.
'''


class CPVIAGenerator:
    @staticmethod
    def cpvia_generator(self, context, property_name):
        alva_log("cpvia_generator", f"CPVIA Initial: {property_name}, {self}")

        start = time.time()

        cpvia_finders = CPVIAFinders()
        publisher = Publisher()

        parent = cpvia_finders.find_parent(self)
        controller_type = cpvia_finders._find_controller_type(parent, property_name)
        c, p, v = cpvia_finders.add_channel_parameter_value(parent, property_name, controller_type)

        if isinstance(context.space_data, bpy.types.SpaceView3D):
            publisher.update_other_selections(context, parent, property_name)

        if not check_flags(context, parent, c, p, v, controller_type):
            return
        
        if property_name == "color":
            color_splitter = ColorSplitter()
            p, v = color_splitter.split_color(parent, c, p, v, controller_type)

        alva_log("cpvia_generator", f"CPV: {c}, {p}, {v}")

        i, a = add_influence_and_argument(c, p, v, parent, cpvia_finders, controller_type)

        publish_updates(c, p, v, i, a, publisher)

        alva_log('time', f"cpvia_generator took {time.time() - start} seconds")


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
intensity_partial = partial(CPVIAGenerator.cpvia_generator, property_name="intensity")
color_partial = partial(CPVIAGenerator.cpvia_generator, property_name="color")
pan_partial = partial(CPVIAGenerator.cpvia_generator, property_name="pan")
tilt_partial = partial(CPVIAGenerator.cpvia_generator, property_name="tilt")
pan_graph_partial = partial(CPVIAGenerator.cpvia_generator, property_name="pan_graph")
tilt_graph_partial = partial(CPVIAGenerator.cpvia_generator, property_name="tilt_graph")
strobe_partial = partial(CPVIAGenerator.cpvia_generator, property_name="strobe")
zoom_partial = partial(CPVIAGenerator.cpvia_generator, property_name="zoom")
iris_partial = partial(CPVIAGenerator.cpvia_generator, property_name="iris")
diffusion_partial = partial(CPVIAGenerator.cpvia_generator, property_name="diffusion")
edge_partial = partial(CPVIAGenerator.cpvia_generator, property_name="edge")
gobo_id_partial = partial(CPVIAGenerator.cpvia_generator, property_name="gobo_id")
gobo_speed_partial = partial(CPVIAGenerator.cpvia_generator, property_name="gobo_speed")
prism_partial = partial(CPVIAGenerator.cpvia_generator, property_name="prism")


def test_cpvia_generator(SENSITIVITY): # Return True for fail, False for pass
    return False