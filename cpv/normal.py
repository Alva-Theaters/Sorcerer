# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

from .find import Find 
from .publish import Publish


def find_normal_cpv(generator):
    NormalCPV(generator).execute()

class NormalCPV:
    def __init__(self, generator):
        self.parent = generator.parent
        self.property_name = generator.property_name
        self.controller_type = generator.controller_type   

    def execute(self):
        self._strip_graph_suffix()
        value = self._find_value()
        
        if self.parent.type == 'CUSTOM':  # CUSTOM because that means node
            Find().trigger_downstream_nodes(self.parent, self.property_name, value)
        
        for channel in self.parent.list_group_channels:
            Publish(self, channel.chan, self.property_name, value).execute()
    
    def _strip_graph_suffix(self):
        if self.property_name in ['pan_graph', 'tilt_graph']:
            return self.property_name.replace("_graph", "")
        return self.property_name
    
    def _find_value(self):
        return getattr(self.parent, f"alva_{self.property_name}")