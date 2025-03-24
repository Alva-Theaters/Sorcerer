# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy


class UpdateOtherSelections:
    def __init__(self, context, parent, property_name):
        self.context = context
        self.parent = parent
        self.property_name = property_name


    def execute(self):
        if not self.is_correct_screen():
            return
        
        if self.will_be_recursive():
            return  
        
        others = self.find_others()

        if self.parent in others:
            others.remove(self.parent)
            
        for obj in others:
            self.update_other(obj)

    def will_be_recursive(self):
        return self.parent != self.context.active_object

    def is_correct_screen(self):
        return isinstance(self.context.space_data, bpy.types.SpaceView3D)

    def find_others(self):
        return [obj for obj in self.context.selected_objects if obj.type in ['MESH', 'LIGHT']]

    def update_other(self, obj):
        setattr(obj, f"alva_{self.property_name}", getattr(self.parent, f"alva_{self.property_name}"))