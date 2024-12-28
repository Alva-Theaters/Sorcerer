# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

from ..utils import get_orb_icon


def draw_text_view(self, context):
    layout = self.layout
    layout.separator()
    layout.prop(context.scene.scene_props, "view_ip_address_tool")


def draw_macro_generator(self, context):
    orb = get_orb_icon()

    active_text = context.space_data.text
    layout = self.layout
    col = layout.column()
    
    row = col.row(align=True)
    row.prop(active_text, 'text_macro', text="Macro Number:")
    row.operator("alva_orb.orb", icon_value=orb.icon_id).as_orb_id = 'generate_macro'

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
    col.operator("alva_text.text_to_3d", text="Fixtures to 3D", icon='SHADERFX')