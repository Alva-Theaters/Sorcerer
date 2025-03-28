# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

from .find import Find 
from .publish.publish import Publish, CPV


def find_normal_cpv(Generator, Parameter):
    NormalCPV(Generator, Parameter).execute()


class NormalCPV:
    def __init__(self, Generator, Parameter):
        self.parent = Generator.parent
        self.Parameter = Parameter
        self.property_name = Generator.property_name
        self.controller_type = Generator.controller_type 
        self._set_value()  

    def _set_value(self):
        self.value = getattr(self.parent, self.property_name)


    def execute(self):
        self.trigger_downstream()
        self.publish()
    
    def trigger_downstream(self):
        if self.parent.type == 'CUSTOM':  # CUSTOM because that means node
            Find().trigger_downstream_nodes(self.parent, self.property_name, self.value)

    def publish(self):
        for channel in self.parent.list_group_channels:
            Publish(self, self.Parameter, channel.chan, self.property_name, self.value, sender=CPV).execute()