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


import bpy


# Custom icon stuff
import bpy.utils.previews
import os
preview_collections = {}
pcoll = bpy.utils.previews.new()
preview_collections["main"] = pcoll
addon_dir = os.path.dirname(__file__)
pcoll.load("orb", os.path.join(addon_dir, "alva_orb.png"), 'IMAGE')
pcoll = preview_collections["main"]
orb = pcoll["orb"]


def draw_text_view(self, context):
    layout = self.layout
    layout.separator()
    layout.prop(context.scene.scene_props, "view_ip_address_tool")


def draw_macro_generator(self, context):
    active_text = context.space_data.text
    layout = self.layout
    col = layout.column()
    
    row = col.row(align=True)
    row.prop(active_text, 'text_macro', text="Macro Number:")
    row.operator("text.generate_text_macro", icon_value=orb.icon_id)

    col.separator()

    row = col.row()
    row.prop(context.scene, "add_underscores", text="Add underscores", slider=True)

    row = col.row()
    row.prop(context.scene, "add_enter", text="Add Enter", slider=True)

    col.separator()

    col.label(text="Copy key to clipboard:")
    col.template_list("TEXT_UL_macro_list_all", "macro_buttons_list", context.scene, "macro_buttons", context.scene, "macro_buttons_index")
    
    col.label(text="Filter Macro Buttons:")
    split = col.split(factor=0.5)
    
    col1 = split.column()
    col2 = split.column()
    
    filter_options = [
        "All", "Basic Operations", "Numbers", "Letters", "Control",
        "Network", "Attributes", "Effects", "Time and Date", "Miscellaneous", "Timecode", "Console Buttons"
    ]
    
    for i, option in enumerate(filter_options):
        if i % 2 == 0:
            op = col1.operator("alva_text.populate_macros", text=option)
        else:
            op = col2.operator("alva_text.populate_macros", text=option)
        op.filter_group = option

    
def draw_import_usitt_ascii(self, context):
    layout = self.layout
    col = layout.column()
    col.operator("my.send_usitt_ascii_to_3d", text="Fixtures to 3D", icon='SHADERFX')
    col.operator("my.send_usitt_ascii_to_sequencer", text="Events to Sequencer", icon='SHADERFX')