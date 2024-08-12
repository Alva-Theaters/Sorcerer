# This file is part of Alva ..
# Copyright (C) 2024 Alva Theaters

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


'''
=====================================================================
                      DESIGNED BY ALVA THEATERS
                       FOR THE SOLE PURPOSE OF
                         MAKING PEOPLE HAPPY
=====================================================================
'''


## Double hashtag indicates notes for future development requiring some level of attention


from functools import partial

from ..cpvia.find import Find # type: ignore
from ..cpvia.cpvia_finders import CPVIAFinders # type: ignore
from ..cpvia.split_color import ColorSplitter # type: ignore


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
        finders = Find()

        p = property_name  # Inherited from the partial.
        mode = p
        parent = finders.find_parent(self)
        c, p, v, type = find_function(parent, p)  # Should return 3 lists and a string. find_function() is find_my_channels_and_values().

        if mode == "color":
            color_splitter = ColorSplitter()
            p, v = color_splitter.split_color(parent, c, p, v, type)

        i = []
        a = []
        influence = parent.influence
        for chan, param in zip(c, p):
            argument = finders.find_my_argument_template(parent, chan, param, type)
            i.append(influence)
            a.append(argument)

        from ..event_manager import Publisher # type: ignore ## TEMPORARY
        publisher = Publisher()
        for chan, param, val, inf, arg in zip(c, p, v, i, a):
            if param in ["intensity", "raise_intensity", "lower_intensity"]:
                publisher.send_value_to_three_dee(parent, chan, param, val)
            publisher.send_cpvia(chan, param, val, inf, arg)


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