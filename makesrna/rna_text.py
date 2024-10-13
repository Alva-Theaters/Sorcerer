# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Text
from bpy.props import IntProperty


def register():
    Text.text_macro = IntProperty(name="Macro Number", default=1, min=1, max=99999, description="The macro number on the console to overwrite")

def unregister():
    del Text.text_macro