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


import bpy


# Custom icon stuff
import bpy.utils.previews
import os

preview_collections = {}
pcoll = bpy.utils.previews.new()
preview_collections["main"] = pcoll

addon_dir = os.path.dirname(__file__)
pcoll.load("orb", os.path.join(addon_dir, "alva_orb.png"), 'IMAGE')


def draw_alva_toolbar(self, context):
    pcoll = preview_collections["main"]
    orb = pcoll["orb"]
    
    layout = self.layout
    region_width = context.region.width

    num_columns = 1

    flow = layout.grid_flow(row_major=True, columns=num_columns, even_columns=True, even_rows=False, align=True)
    flow.scale_y = 2
    
    space_type = context.space_data.type
    scene = context.scene.scene_props
    
    if space_type == 'SEQUENCE_EDITOR' and scene.view_sequencer_toolbar:
        flow.operator("my.add_macro", icon='FILE_TEXT', text="Macro" if region_width > 200 else "")
        flow.operator("my.add_cue", icon='PLAY', text="Cue" if region_width > 200 else "")
        flow.operator("my.add_flash", icon='LIGHT_SUN', text="Flash" if region_width > 200 else "")
        flow.operator("my.add_animation", icon='IPO_BEZIER', text="Animation" if region_width > 200 else "")
        #flow.operator("my.add_offset_strip", icon='UV_SYNC_SELECT', text="Offset" if region_width > 200 else "")
        flow.operator("my.add_trigger", icon='SETTINGS', text="Trigger" if region_width > 200 else "")
        flow.separator()
        flow.operator("alva_playback.clear_solos", icon='SOLO_OFF', text="Clear Solos" if region_width >= 200 else "")
        flow.operator("seq.render_strips_operator", icon_value=orb.icon_id, text="Render" if region_width > 200 else "")
        flow.operator("my.add_strip_operator", icon='ADD', text="Add Strip" if region_width > 200 else "", emboss=True)
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
