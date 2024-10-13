# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

from .utils import get_orb_icon


def draw_alva_toolbar(self, context):
    orb = get_orb_icon()
    
    layout = self.layout
    region_width = context.region.width

    num_columns = 1

    flow = layout.grid_flow(row_major=True, columns=num_columns, even_columns=True, even_rows=False, align=True)
    flow.scale_y = 2
    
    space_type = context.space_data.type
    scene = context.scene.scene_props
    
    if space_type == 'SEQUENCE_EDITOR' and scene.view_sequencer_toolbar:
        flow.operator("alva_seq.add", icon='FILE_TEXT', text="Macro" if region_width > 200 else "").Option = "option_macro"
        flow.operator("alva_seq.add", icon='PLAY', text="Cue" if region_width > 200 else "").Option = "option_cue"
        flow.operator("alva_seq.add", icon='LIGHT_SUN', text="Flash" if region_width > 200 else "").Option = "option_flash"
        flow.operator("alva_seq.add", icon='IPO_BEZIER', text="Animation" if region_width > 200 else "").Option = "option_animation"
        #flow.operator("alva_seq.add", icon='UV_SYNC_SELECT', text="Offset" if region_width > 200 else "").Option = "option_offset"
        flow.operator("alva_seq.add", icon='SETTINGS', text="Trigger" if region_width > 200 else "").Option = "Option_trigger"
        flow.separator()
        flow.operator("alva_playback.clear_solos", icon='SOLO_OFF', text="Clear Solos" if region_width >= 200 else "")
        flow.operator("alva_orb.render_strips", icon_value=orb.icon_id, text="Render" if region_width > 200 else "")
        flow.operator("alva_seq.duplicate", icon='ADD', text="Add Strip" if region_width > 200 else "", emboss=True)
        flow.operator("alva_tool.ghost_out", icon='GHOST_ENABLED', text="Cue 0" if region_width > 200 else "")
        flow.operator("alva_tool.displays", icon='MENU_PANEL', text="Displays" if region_width > 200 else "")
        flow.operator("alva_tool.about", icon='INFO', text="About" if region_width > 200 else "")
        flow.operator("alva_tool.copy", icon='COPYDOWN', text="Disable Clocks" if region_width > 200 else "")
        flow.operator("alva_tool.disable_clocks", icon='MOD_TIME', text="Disable Clocks" if region_width > 200 else "")

    elif space_type == 'NODE_EDITOR' and scene.view_node_toolbar:
        flow.operator("alva_playback.clear_solos", icon='SOLO_OFF', text="Clear Solos" if region_width >= 200 else "")
        flow.operator("alva_tool.ghost_out", icon='GHOST_ENABLED', text="Cue 0" if region_width >= 200 else "")
        flow.operator("alva_tool.displays", icon='MENU_PANEL', text="Displays" if region_width >= 200 else "")
        flow.operator("alva_tool.about", icon='INFO', text="About" if region_width >= 200 else "")
        flow.operator("alva_tool.disable_clocks", icon='MOD_TIME', text="Disable Clocks" if region_width >= 200 else "")

    elif space_type == 'VIEW_3D' and scene.view_viewport_toolbar:
        flow.operator("alva_playback.clear_solos", icon='SOLO_OFF', text="Clear Solos" if region_width >= 200 else "")
        flow.operator("alva_tool.ghost_out", icon='GHOST_ENABLED', text="Cue 0" if region_width >= 200 else "")
        flow.operator("alva_tool.displays", icon='MENU_PANEL', text="Displays" if region_width >= 200 else "")
        flow.operator("alva_tool.about", icon='INFO', text="About" if region_width >= 200 else "")
        flow.operator("alva_tool.disable_clocks", icon='MOD_TIME', text="Disable Clocks" if region_width >= 200 else "")
