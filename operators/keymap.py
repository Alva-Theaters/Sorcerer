# This file is part of Alva Sorcerer.
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

addon_keymaps = []
custom_node_editor_keymaps = []

def register_keymap_item(keymap, idname, key, value, **kwargs):
    kmi = keymap.keymap_items.new(idname, type=key, value=value, **kwargs)
    return kmi

def register_keymaps():
    wm = bpy.context.window_manager
    if wm.keyconfigs.addon:
        sequencer_km = wm.keyconfigs.addon.keymaps.new(name='Sequencer', space_type='SEQUENCE_EDITOR')

        # Command line stuff
        register_keymap_item(sequencer_km, "sequencer.simple_command_line", 'C', 'PRESS')
        register_keymap_item(sequencer_km, "seq.render_strips_operator", 'SPACE', 'PRESS', shift=True)

        # Define the hotkeys
        register_keymap_item(sequencer_km, "vse.scale_strips", 'S', 'PRESS')
        register_keymap_item(sequencer_km, "vse.extrude_strips", 'E', 'PRESS')
        register_keymap_item(sequencer_km, "vse.duplicate_pattern", 'E', 'PRESS', shift=True)

        # Bump up
        kmi = register_keymap_item(sequencer_km, 'sequencer.vse_bump_strip_channel', 'U', 'PRESS')
        kmi.properties.direction = 1

        # Bump down with shift
        kmi_shift = register_keymap_item(sequencer_km, 'sequencer.vse_bump_strip_channel', 'U', 'PRESS', shift=True)
        kmi_shift.properties.direction = -1

        # Deselect all
        register_keymap_item(sequencer_km, 'sequencer.vse_deselect_all', 'D', 'PRESS')

        # Add color strip
        register_keymap_item(sequencer_km, 'sequencer.vse_new_color_strip', 'Z', 'RELEASE')
        register_keymap_item(sequencer_km, 'sequencer.vse_new_color_strip_kick', 'Z', 'PRESS')
        register_keymap_item(sequencer_km, 'sequencer.vse_new_color_strip_pointer', 'Z', 'PRESS', shift=True)

        # Left and Right operators
        register_keymap_item(sequencer_km, 'sequencer.left_operator', 'L', 'PRESS')
        register_keymap_item(sequencer_km, 'sequencer.right_operator', 'R', 'PRESS')
        register_keymap_item(sequencer_km, 'sequencer.left_long_operator', 'L', 'PRESS', shift=True)
        register_keymap_item(sequencer_km, 'sequencer.right_long_operator', 'R', 'PRESS', shift=True)

        # Additional Sequencer keymaps
        kmi1 = register_keymap_item(sequencer_km, "seq.show_strip_properties", 'M', 'PRESS')
        kmi2 = register_keymap_item(sequencer_km, "seq.show_strip_formatter", 'F', 'PRESS')
        addon_keymaps.append((sequencer_km, kmi1))
        addon_keymaps.append((sequencer_km, kmi2))

        # Node Editor keymaps
        node_editor_km = wm.keyconfigs.addon.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
        node_editor_kmi = register_keymap_item(node_editor_km, "nodes.show_node_formatter", 'F', 'PRESS')
        node_editor_kmi.active = True
        custom_node_editor_keymaps.append((node_editor_km, node_editor_kmi))

def unregister_keymaps():
    '''WARNING: THIS SECTION IS EXTREMELY CRASH-HAPPY WHEN NOT PERFECT :) :) :)'''
    wm = bpy.context.window_manager
    if wm.keyconfigs.addon:
        # Safely remove addon keymaps
        for km, kmi in addon_keymaps:
            if km and kmi:
                try:
                    km.keymap_items.remove(kmi)
                except ReferenceError:
                    pass
        # Safely remove custom node editor keymaps
        for km, kmi in custom_node_editor_keymaps:
            if km and kmi:
                try:
                    km.keymap_items.remove(kmi)
                except ReferenceError:
                    pass
        # Safely remove keymaps
        for km, _ in addon_keymaps + custom_node_editor_keymaps:
            try:
                wm.keyconfigs.addon.keymaps.remove(km)
            except ReferenceError:
                pass

    addon_keymaps.clear()
    custom_node_editor_keymaps.clear()

def register():
    register_keymaps()

def unregister():
    unregister_keymaps()