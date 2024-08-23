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


def draw_alva_topbar(self, context):
    pcoll = preview_collections["main"]
    orb = pcoll["orb"]

    if (hasattr(context, "scene") and 
        hasattr(context.scene, "scene_props") and 
        context.scene.scene_props.view_topbar):
        scene = context.scene.scene_props
        layout = self.layout
        col = layout.column()
        row = col.row(align=True)
        row.operator("alva_topbar.alva_preferences", text="", icon_value=orb.icon_id, emboss=1)
        row.prop(scene, "lighting_enabled", text="", icon='OUTLINER_OB_LIGHT' if scene.lighting_enabled else 'LIGHT_DATA', emboss=1)
        row.prop(scene, "video_enabled", text="", icon='VIEW_CAMERA' if scene.video_enabled else 'OUTLINER_DATA_CAMERA', emboss=1)
        row.prop(scene, "audio_enabled", text="", icon='OUTLINER_OB_SPEAKER' if scene.audio_enabled else 'OUTLINER_DATA_SPEAKER', emboss=1)

        col = layout.column()
        row = col.row()
        row.alert = scene.has_solos
        row.operator("alva_topbar.clear_solos", text="", icon='SOLO_OFF')


def draw_alva_edit(self, context):
    pcoll = preview_collections["main"]
    orb = pcoll["orb"]

    if (hasattr(context, "scene") and 
        hasattr(context.scene, "scene_props")): # Avoid unregistration error
        layout = self.layout
        layout.separator()
        layout.operator("alva_topbar.alva_preferences", text="Sorcerer Preferences", icon_value=orb.icon_id)


def draw_alva_render(self, context):
    pcoll = preview_collections["main"]
    orb = pcoll["orb"]

    if (hasattr(context, "scene") and 
        hasattr(context.scene, "scene_props")): # Avoid unregistration error
        layout = self.layout
        layout.operator("alva_orb.render_qmeo", text="Render Qmeo", icon_value=orb.icon_id)


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