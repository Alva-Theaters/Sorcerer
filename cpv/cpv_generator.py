# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
import time

from ..utils.cpv_utils import find_parent, find_controller_type
from .normal import find_normal_cpv
from .influence import find_influencer_cpv
from .mix import find_mixer_cpv
from .stop import check_flags
from ..maintenance.logging import alva_log
from .publish import update_other_selections


'''
The CPV system is essentially a communication protocol similar to DMX used only in Sorcerer.

A CPV request is a tuple containing Channel, Parameter, Value. 

A CPV request is made any time a single controller wishes to make a parameter change on the console.
We use the CPV protocol to standardize how all parameter change requests are made no matter the 
controller type, no matter the space_type. In frame change and during playback, CPV requests are
compared to one another for common simplifcation and harmonization to avoid spamming contradictory 
messages and to batch commands together.
'''
class CPVGenerator:
    def __init__(self, controller, context, property_name):
        self.controller = controller
        self.context = context
        self.property_name = property_name
        self.parent = find_parent(controller)
        self.controller_type = find_controller_type(self.parent, self.property_name)

        self.cpv_functions = {
            "Influencer": lambda: find_influencer_cpv(self),
            "Key": lambda: find_influencer_cpv(self),
            "Brush": lambda: find_influencer_cpv(self),
            "Fixture": lambda: find_normal_cpv(self),
            "Pan/Tilt Fixture": lambda: find_normal_cpv(self),
            "Pan/Tilt": lambda: find_normal_cpv(self),
            "group": lambda: find_normal_cpv(self),
            "strip": lambda: find_normal_cpv(self),
            "Stage Object": lambda: find_normal_cpv(self),
            "mixer": lambda: find_mixer_cpv(self)
        }

    @property
    def is_allowed(self):
        return check_flags(self.context, self.parent, self.property_name, self.controller_type)

    @property
    def is_view3d(self):
        return isinstance(self.context.space_data, bpy.types.SpaceView3D)

    def execute(self):
        if not self.is_allowed:
            return

        alva_log("cpv_generator", f"CPV Initial: {self.property_name}, {self}")

        start = time.time()

        if self.is_view3d:
            update_other_selections(self.context, self.parent, self.property_name)

        self.cpv_functions[self.controller_type]()

        alva_log('time', f"TIME: cpv_generator took {time.time() - start} seconds")


    @staticmethod
    def intensity_updater(controller, context):
        return CPVGenerator(controller, context, property_name="intensity").execute()

    @staticmethod
    def color_updater(controller, context):
        return CPVGenerator(controller, context, property_name="color").execute()

    @staticmethod
    def pan_updater(controller, context):
        return CPVGenerator(controller, context, property_name="pan").execute()

    @staticmethod
    def tilt_updater(controller, context):
        return CPVGenerator(controller, context, property_name="tilt").execute()

    @staticmethod
    def pan_graph_updater(controller, context):
        return CPVGenerator(controller, context, property_name="pan_graph").execute()

    @staticmethod
    def tilt_graph_updater(controller, context):
        return CPVGenerator(controller, context, property_name="tilt_graph").execute()

    @staticmethod
    def strobe_updater(controller, context):
        return CPVGenerator(controller, context, property_name="strobe").execute()

    @staticmethod
    def zoom_updater(controller, context):
        return CPVGenerator(controller, context, property_name="zoom").execute()

    @staticmethod
    def iris_updater(controller, context):
        return CPVGenerator(controller, context, property_name="iris").execute()

    @staticmethod
    def diffusion_updater(controller, context):
        return CPVGenerator(controller, context, property_name="diffusion").execute()

    @staticmethod
    def edge_updater(controller, context):
        return CPVGenerator(controller, context, property_name="edge").execute()

    @staticmethod
    def gobo_id_updater(controller, context):
        return CPVGenerator(controller, context, property_name="gobo").execute()

    @staticmethod
    def gobo_speed_updater(controller, context):
        return CPVGenerator(controller, context, property_name="gobo_speed").execute()

    @staticmethod
    def prism_updater(controller, context):
        return CPVGenerator(controller, context, property_name="prism").execute()


def test_cpv_generator(SENSITIVITY): # Return True for fail, False for pass
    return False