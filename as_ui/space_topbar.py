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


import bpy

from .space_time import is_qmeo_parent_a_sound_strip

# Custom icon stuff
import bpy.utils.previews
import os

preview_collections = {}
pcoll = bpy.utils.previews.new()
preview_collections["main"] = pcoll

addon_dir = os.path.dirname(__file__)
pcoll.load("orb", os.path.join(addon_dir, "alva_orb.png"), 'IMAGE')


def draw_alva_topbar(self, context):
    pcoll = preview_collections["main"]
    orb = pcoll["orb"]

    if (hasattr(context, "scene") and 
        hasattr(context.scene, "scene_props") and 
        context.scene.scene_props.view_topbar):
        layout = self.layout
        if context.scene.scene_props.limp_mode:
            row = layout.row()
            row.alert = 1
            scene = context.scene.scene_props
            row.label(text=f"ALVA LIMP MODE: {scene.user_limp_mode_explanation}. Systems Down: {scene.number_of_systems_down}")
            row.alert = 0
        row = layout.row(align=True)
        row.operator("alva_topbar.preferences", text="", icon_value=orb.icon_id, emboss=0)
        layout.label(text=" +")


def draw_alva_edit(self, context):
    pcoll = preview_collections["main"]
    orb = pcoll["orb"]

    if (hasattr(context, "scene") and 
        hasattr(context.scene, "scene_props")): # Avoid unregistration error
        layout = self.layout
        layout.separator()
        layout.operator("alva_topbar.preferences", text="Sorcerer Preferences", icon_value=orb.icon_id)


def draw_alva_render(self, context):
    pcoll = preview_collections["main"]
    orb = pcoll["orb"]

    if (hasattr(context, "scene") and 
        hasattr(context.scene, "scene_props") and
        context.scene.scene_props.console_type_enum == 'option_eos'):
        is_sound = is_qmeo_parent_a_sound_strip(context)
        
        layout = self.layout
        layout.operator("alva_orb.render_qmeo", text="Render Qmeo", icon_value=orb.icon_id).is_sound = is_sound


def draw_alva_window(self, context):
    if (hasattr(context, "scene") and 
        hasattr(context.scene, "scene_props")): # Avoid unregistration error
        layout = self.layout
        layout.separator()
        layout.prop(context.scene.scene_props, "view_topbar", text="Alva Topbar")


def draw_alva_help(self, context):
    pcoll = preview_collections["main"]
    orb = pcoll["orb"]

    if (hasattr(context, "scene") and
        hasattr(context.scene, "scene_props")): # Avoid unregistration error
        scene = context.scene.scene_props
        layout = self.layout
        layout.separator()
        layout.operator("wm.url_open", text="Sorcerer Manual", icon_value=orb.icon_id).url = "https://alva-sorcerer.readthedocs.io/en/latest/index.html#"
        layout.operator("wm.url_open", text="Tutorials").url = "https://www.youtube.com/channel/UCE6Td8fdLPvv3VLdfjIz5Dw"
        layout.operator("wm.url_open", text="Support").url = "https://sorcerer.alvatheaters.com/support/"
        layout.operator("wm.url_open", text="User Community").url = "https://www.reddit.com/r/alvatheaterssoftware/"