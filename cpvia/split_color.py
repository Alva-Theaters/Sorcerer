# This file is part of Alva Sorcerer
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


from ..cpvia.publish import Publisher # type: ignore
from ..cpvia.find import Find # type: ignore
from ..utils.utils import is_rendered_mode


class ColorSplitter:
    def calculate_closeness(self, rgb_input, target_rgb, sensitivity=1.0):
        diff = sum(abs(input_c - target_c) for input_c, target_c in zip(rgb_input, target_rgb))
        normalized_diff = diff / (300 * sensitivity)
        closeness_score = max(0, min(1, 1 - normalized_diff))
        return closeness_score


    def rgb_converter(self, red, green, blue):
        return red, green, blue
        
            
    def rgba_converter(self, red, green, blue):
        # Calculate the influence of red and the lack of green on the amber component.
        red_influence = red / 100
        green_deficit = 1 - abs(green - 50) / 50
        amber_similarity = red_influence * green_deficit
        white_similarity = min(red, green, blue) / 100
        
        if amber_similarity > white_similarity:
            amber = round(amber_similarity * 100)
        else:
            amber = round(75 * white_similarity)
            
        return red, green, blue, amber

        
    def rgbw_converter(self, red, green, blue):
        white_similarity = min(red, green, blue) / 100
        white_peak = 75 + (25 * white_similarity)  # Peaks at 100 for pure white.

        white = round(white_peak * white_similarity)
        
        return red, green, blue, white


    def rgbaw_converter(self, red, green, blue):
        amber_sensitivity=1.0
        white_sensitivity=1.0
        
        # Define pure color values for comparison
        pure_colors = {
            'amber': (100, 50, 0),
            'white': (100, 100, 100),
            'red': (100, 0, 0),
            'green': (0, 100, 0),
            'blue': (0, 0, 100)
        }
        
        # Calculate closeness scores for each target color, specifying sensitivity where needed.
        scores = {}
        for color, rgb in pure_colors.items():
            if color == 'amber':
                scores[color] = self.calculate_closeness((red, green, blue), rgb, amber_sensitivity)
            elif color == 'white':
                scores[color] = self.calculate_closeness((red, green, blue), rgb, white_sensitivity)
            else:
                scores[color] = self.calculate_closeness((red, green, blue), rgb)
                
        amber = round(scores['amber'] * 100)
        white = round(scores['white'] * 100)

        return red, green, blue, amber, white


    def rgbl_converter(self, red, green, blue):
        lime = 0
        
        # Lime peaks at 100 for yellow (100, 100, 0) and white (100, 100, 100).
        if red == 100 and green == 100:
            lime = 100
        # For other combinations, calculate lime based on the lesser of red and green, but only if blue is not dominant.
        elif blue < red and blue < green:
            lime = round((min(red, green) / 100) * 100)
        
        return red, green, blue, lime


    def rgbam_converter(self, red, green, blue):
        # Handle exact targets with conditional logic.
        if (red, green, blue) == (0, 0, 0):  # Black
            amber, mint = 0, 0
        elif (red, green, blue) == (100, 0, 0):  # Pure Red
            amber, mint = 0, 0
        elif (red, green, blue) == (0, 100, 0):  # Pure Green
            amber, mint = 0, 0
        elif (red, green, blue) == (0, 0, 100):  # Pure Blue
            amber, mint = 0, 0
        elif (red, green, blue) == (100, 100, 100):  # White
            amber, mint = 100, 100
        elif (red, green, blue) == (58, 100, 14):  # Specific Mint Peak
            amber, mint = 0, 100
        elif (red, green, blue) == (100, 50, 0):  # Specific Amber Peak
            amber, mint = 100, 0
        else:
            proximity_to_white = min(red, green, blue) / 100
            amber = round(100 * proximity_to_white)
            mint = round(100 * proximity_to_white)
            
            # Adjust for proximity to the specific mint peak color.
            if green == 100 and red > 0 and blue > 0:
                mint_peak_proximity = min(red / 58, blue / 14)
                mint = round(100 * mint_peak_proximity)
        
        return red, green, blue, amber, mint


    def cmy_converter(self, red, green, blue):
        # Define a tolerance for near-maximum RGB values to treat them as 1.
        tolerance = 0.01
        red_scaled = red / 100.0
        green_scaled = green / 100.0
        blue_scaled = blue / 100.0

        # Apply the tolerance to treat near-maximum values as 1.
        cyan = int((1 - min(red_scaled + tolerance, 1)) * 100)
        magenta = int((1 - min(green_scaled + tolerance, 1)) * 100)
        yellow = int((1 - min(blue_scaled + tolerance, 1)) * 100)

        return cyan, magenta, yellow
    

    def balance_white(self, white_balance, converted_values, is_subtractive=False):
        if white_balance != (100, 100, 100): # Must balance
            if is_subtractive:
                balanced_values = tuple(
                    min(max(100 - ((100 - cv) * wb / 100), 0), 100)
                    for cv, wb in zip(converted_values, white_balance)
                )
            else:
                balanced_values = tuple(
                    int(cv * wb / 100) for cv, wb in zip(converted_values, white_balance)
                )
            return balanced_values
            
        else: # No need to balance
            return converted_values

        
    def split_color(self, parent, c, p, v, type):
        """
        Splits the input (r, g, b) tuple for value (v) into tuples like (r, g, b, a, m)
        for the value entries and updates the parameter (p) value for each entry to the 
        color profile (pf) enumerator option found with find_my_patch().
        
        This function prepares the parameters and values for later processing by the 
        find_my_argument() function, ensuring that the correct argument is formed based 
        on the received v tuple. The updated parameter p indirectly reflects the 
        color_profile choice, allowing the publisher to interpret the v tuple correctly.

        Also processes wwhite balance.
        
        Parameters:
            parent: The parent controller object.
            c: The channel list.
            p: The parameter, as list
            v: The value list.
            type: The controller type.

        Returns:
            new_p: The updated parameter list.
            new_v: The updated value list.
        """
        new_p = []
        new_v = []
        for chan, val in zip(c, v):  # 4chan lol
            finders = Find() # needs to be an instance
            pf = finders.find_my_patch(parent, chan, type, "color_profile_enum") # this returns option_rgb, option_rgba, etc.
            profile_converters = {
                # Absolute Arguments
                'rgba': (self.rgba_converter, 4),
                'rgbw': (self.rgbw_converter, 4),
                'rgbaw': (self.rgbaw_converter, 5),
                'rgbl': (self.rgbl_converter, 4),
                'cmy': (self.cmy_converter, 3),
                'rgbam': (self.rgbam_converter, 5),

                # Raise Arguments
                'raise_rgba': (self.rgba_converter, 4),
                'raise_rgbw': (self.rgbw_converter, 4),
                'raise_rgbaw': (self.rgbaw_converter, 5),
                'raise_rgbl': (self.rgbl_converter, 4),
                'raise_cmy': (self.cmy_converter, 3),
                'raise_rgbam': (self.rgbam_converter, 5),

                # Lower Arguments
                'lower_rgba': (self.rgba_converter, 4),
                'lower_rgbw': (self.rgbw_converter, 4),
                'lower_rgbaw': (self.rgbaw_converter, 5),
                'lower_rgbl': (self.rgbl_converter, 4),
                'lower_cmy': (self.cmy_converter, 3),
                'lower_rgbam': (self.rgbam_converter, 5)
            }

            mode = pf.replace("option_", "")
            corrected_key = p[0].replace("color", mode)
            
            is_rendering = is_rendered_mode()
            if is_rendering:
                publisher = Publisher()
                publisher.render_in_viewport(parent, chan, corrected_key, val)

            is_subtractive = corrected_key in ['cmy', 'raise_cmy', 'lower_cmy']

            wb = finders.find_my_patch(parent, chan, type, "alva_white_balance")
            from ..utils.utils import Utils
            white_balance = Utils.color_object_to_tuple_and_scale_up(wb)

            if corrected_key in ['rgb', 'raise_rgb', 'lower_rgb']: # No need to split
                balanced = self.balance_white(white_balance, val, is_subtractive)
                new_p.append(corrected_key)
                new_v.append(balanced)
                
            elif corrected_key in profile_converters: # Must split
                converter, num_values = profile_converters[corrected_key]
                converted_values = converter(*val[:3])
                balanced = self.balance_white(white_balance, converted_values, is_subtractive)
                
                new_p.append(corrected_key)
                new_v.append(balanced[:num_values])
            else: raise ValueError(f"Unknown color profile: {corrected_key}")

        return new_p, new_v