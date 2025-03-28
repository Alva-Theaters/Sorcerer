# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import time
from functools import wraps

from ..utils.cpv_utils import find_parent, find_controller_type
from .normal import find_normal_cpv
from .influence import find_influencer_cpv
from .mix import find_mixer_cpv
from .stop import check_flags
from ..maintenance.logging import alva_log
from .publish.update_others import UpdateOtherSelections

'''
The CPV system is essentially a communication protocol similar to DMX used only in Sorcerer.

A CPV request is a tuple containing Channel, Parameter, Value. 

A CPV request is made any time a single controller wishes to make a parameter change on the console.
We use the CPV protocol to standardize how all parameter change requests are made no matter the 
controller type, no matter the space_type. In frame change and during playback, CPV requests are
compared to one another for common simplification and harmonization to avoid spamming contradictory 
messages and to batch commands together.
'''

def time_logger(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        alva_log("cpv_generator", f"CPV Initial: {args[0].property_name}, {args[0]}")
        start = time.time()
        result = func(*args, **kwargs)
        alva_log('time', f"TIME: cpv_generator took {time.time() - start:.4f} seconds")
        return result
    return wrapper


class CPVGenerator:
    def __init__(self, controller, context, Parameter):
        self.controller = controller
        self.context = context
        self.Parameter = Parameter
        self.property_name = f"alva_{Parameter.as_property_name}"
        self.parent = find_parent(controller)
        self.controller_type = find_controller_type(self.parent, self.property_name)
        self.should_stop = check_flags(self.context, self.parent, self.property_name, self.controller_type)

        self.cpv_functions = {
            "Influencer": lambda: find_influencer_cpv(self, Parameter),
            "Key": lambda: find_influencer_cpv(self, Parameter),
            "Brush": lambda: find_influencer_cpv(self, Parameter),
            "Fixture": lambda: find_normal_cpv(self, Parameter),
            "Pan/Tilt Fixture": lambda: find_normal_cpv(self, Parameter),
            "Pan/Tilt": lambda: find_normal_cpv(self, Parameter),
            "group": lambda: find_normal_cpv(self, Parameter),
            "strip": lambda: find_normal_cpv(self, Parameter),
            "Stage Object": lambda: find_normal_cpv(self, Parameter),
            "mixer": lambda: find_mixer_cpv(self, Parameter)
        }

    @time_logger
    def execute(self):
        if self.should_stop: return
        UpdateOtherSelections(self.context, self.parent, self.property_name).execute()
        self.cpv_functions[self.controller_type]()


def test_cpv_generator(SENSITIVITY): # Return True for fail, False for pass
    return False