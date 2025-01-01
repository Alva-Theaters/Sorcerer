# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

'''
The problem is that Blender's custom properties cannot be assigned dynamic mins and maxes.

That's bad because it makes it difficult for the user to make full use of sliders. We want the
user to be able to set the min, set the max, and then have the far left end of the slider be the 
min and the far right end of the slider be the max. Naturally however, only a small part of the 
slider towards the middle would actually be useful.

We can fix this by defaulting all properties to a static 0-100 scale for positive-only parameters
(like intensity), or to a -100 to 100 scale for negative and positive parameters (like pan/tilt). 
However, we would need to remap the value from the slider to the value the lighting fixture needs 
based on the user's min/max input. 

That's what this code does. It says, "Hey, the slider is on its own program independent of the 
min/max set for the fixture. We need to remap that in the background so that we tell the fixture
to go to a value that reflects its min/max (that probably isn't 0-100 or -100-100)."
'''


class SliderToFixtureMapper:
    MAX_UNIPOLAR = 100
    MIN_UNIPOLAR = -100
    BIPOLAR_SCALE = 200

    def __init__(self, publisher):
        self.publisher = publisher
        self.min_property_name = f"{self.publisher.property_name}_min"
        self.max_property_name = f"{self.publisher.property_name}_max"
        self.min_val, self.max_val = self.find_min_max_values()
        self.unmapped_value = self.publisher.value

    @property
    def is_negative_capable(self):
        return self.min_val < 0 <= self.max_val
    
    def find_min_max_values(self):
        try:
            min_value = getattr(self.publisher.patch_controller, self.min_property_name)
            max_value = getattr(self.publisher.patch_controller, self.max_property_name)
        except AttributeError:
            raise ValueError(
                f"Patch controller is missing required attributes: {self.min_property}, {self.max_property}"
            )
        return min_value, max_value
    

    def execute(self):
        return self.map_to_bipolar_range() if self.is_negative_capable else self.map_to_unipolar_range()

    def map_to_bipolar_range(self):
        if self.unmapped_value == 0:
            return 0
        return self._scale_bipolar_value()

    def map_to_unipolar_range(self):
        normalized_value = self.unmapped_value / self.MAX_UNIPOLAR
        return normalized_value * (self.max_val - self.min_val) + self.min_val

    def _scale_bipolar_value(self):
        normalized_value = self.unmapped_value / self.MAX_UNIPOLAR
        return normalized_value * (self.max_val if self.unmapped_value > 0 else abs(self.min_val))

        
def test_mapping(SENSITIVITY): # Return True for fail, False for pass
    return False