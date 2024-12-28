# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

from .space_time import is_qmeo_parent_a_sound_strip
from ..utils import get_orb_icon

orb = get_orb_icon()


def draw_alva_topbar(self, context):
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
    if (hasattr(context, "scene") and 
        hasattr(context.scene, "scene_props")): # Avoid unregistration error
        layout = self.layout
        layout.separator()
        layout.operator("alva_topbar.preferences", text="Sorcerer Preferences", icon_value=orb.icon_id)


def draw_alva_render(self, context):
    if (hasattr(context, "scene") and 
        hasattr(context.scene, "scene_props") and
        context.scene.scene_props.console_type_enum == 'option_eos'):
        is_sound = is_qmeo_parent_a_sound_strip(context)
        
        layout = self.layout
        layout.operator("alva_orb.orb", text="Render Qmeo", icon_value=orb.icon_id).as_id = 'timeline'


def draw_alva_window(self, context):
    if (hasattr(context, "scene") and 
        hasattr(context.scene, "scene_props")): # Avoid unregistration error
        layout = self.layout
        layout.separator()
        layout.prop(context.scene.scene_props, "view_topbar", text="Alva Topbar")


def draw_alva_help(self, context):
    if (hasattr(context, "scene") and
        hasattr(context.scene, "scene_props")): # Avoid unregistration error
        scene = context.scene.scene_props
        layout = self.layout
        layout.separator()
        layout.operator("wm.url_open", text="Sorcerer Manual", icon_value=orb.icon_id).url = "https://alva-sorcerer.readthedocs.io/en/latest/index.html#"
        layout.operator("wm.url_open", text="Tutorials").url = "https://www.youtube.com/channel/UCE6Td8fdLPvv3VLdfjIz5Dw"
        layout.operator("wm.url_open", text="Support").url = "https://sorcerer.alvatheaters.com/support/"
        layout.operator("wm.url_open", text="User Community").url = "https://www.reddit.com/r/alvatheaterssoftware/"