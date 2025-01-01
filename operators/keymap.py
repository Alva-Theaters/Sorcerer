# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

addon_keymaps = []
custom_node_editor_keymaps = []

keymap_data = {
    "3D View": {
        "space_type": "VIEW_3D",
        "items": [
            ({"idname": "alva_object.object_controller", "key": 'P', "value": 'PRESS'}, None),
            ({"idname": "alva_tool.ghost_out", "key": 'G', "value": 'PRESS', "shift": True}, None)
        ]
    },
    "Sequencer": {
        "space_type": "SEQUENCE_EDITOR",
        "items": [
            ({"idname": "alva_sequencer.command_line", "key": 'C', "value": 'PRESS'}, None),
            ({"idname": "alva_orb.orb", "key": 'SPACE', "value": 'PRESS', "shift": True}, {'as_orb_id': 'sequencer'}),
            ({"idname": "alva_tool.ghost_out", "key": 'G', "value": 'PRESS', "shift": True}, None),
            ({"idname": "alva_sequencer.scale_strips", "key": 'S', "value": 'PRESS'}, None),
            ({"idname": "alva_sequencer.extrude_strips", "key": 'E', "value": 'PRESS'}, None),
            ({"idname": "alva_sequencer.duplicate_pattern", "key": 'E', "value": 'PRESS', "shift": True}, None),
            ({"idname": 'alva_common.deselect_all', "key": 'D', "value": 'PRESS'}, None),
            ({"idname": 'alva_sequencer.add_color', "key": 'Z', "value": 'RELEASE'}, None),
            ({"idname": 'alva_sequencer.add_color_kick', "key": 'Z', "value": 'PRESS'}, None),
            ({"idname": 'alva_sequencer.add_color_pointer', "key": 'Z', "value": 'PRESS', "shift": True}, None),
            ({"idname": 'alva_sequencer.bump_vertical', "key": 'U', "value": 'PRESS'}, {"direction": 1}),
            ({"idname": 'alva_sequencer.bump_vertical', "key": 'U', "value": 'PRESS', "shift": True}, {"direction": -1}),
            ({"idname": 'alva_sequencer.bump_horizontal', "key": 'L', "value": 'PRESS'}, {"direction": -1}),
            ({"idname": 'alva_sequencer.bump_horizontal', "key": 'R', "value": 'PRESS'}, {"direction": 1}),
            ({"idname": 'alva_sequencer.bump_horizontal', "key": 'L', "value": 'PRESS', "shift": True}, {"direction": -5}),
            ({"idname": 'alva_sequencer.bump_horizontal', "key": 'R', "value": 'PRESS', "shift": True}, {"direction": 5}),
            ({"idname": "alva_sequencer.properties", "key": 'M', "value": 'PRESS'}, None),
            ({"idname": "alva_sequencer.formatter", "key": 'F', "value": 'PRESS'}, None)
        ]
    },
    "Node Editor": {
        "space_type": "NODE_EDITOR",
        "items": [
            ({"idname": "alva_node.formatter", "key": 'F', "value": 'PRESS'}, None),
            ({"idname": "alva_tool.ghost_out", "key": 'G', "value": 'PRESS', "shift": True}, None)
        ]
    },
    "Property Editor": {
        "space_type": "PROPERTIES",
        "items": [
            ({"idname": "alva_cue.take", "key": 'ONE', "value": 'PRESS'}, {"index": 1}),
            ({"idname": "alva_cue.take", "key": 'TWO', "value": 'PRESS'}, {"index": 2}),
            ({"idname": "alva_cue.take", "key": 'THREE', "value": 'PRESS'}, {"index": 3}),
            ({"idname": "alva_cue.take", "key": 'FOUR', "value": 'PRESS'}, {"index": 4}),
            ({"idname": "alva_cue.take", "key": 'FIVE', "value": 'PRESS'}, {"index": 5}),
            ({"idname": "alva_cue.take", "key": 'SIX', "value": 'PRESS'}, {"index": 6}),
            ({"idname": "alva_cue.take", "key": 'SEVEN', "value": 'PRESS'}, {"index": 7}),
            ({"idname": "alva_cue.take", "key": 'EIGHT', "value": 'PRESS'}, {"index": 8}),
            ({"idname": "alva_cue.take", "key": 'NINE', "value": 'PRESS'}, {"index": 9}),
            ({"idname": "alva_cue.take", "key": 'ZERO', "value": 'PRESS'}, {"index": 10}),

            ({"idname": "alva_cue.take", "key": 'ONE', "value": 'PRESS', "shift": True}, {"index": 11}),
            ({"idname": "alva_cue.take", "key": 'TWO', "value": 'PRESS', "shift": True}, {"index": 12}),
            ({"idname": "alva_cue.take", "key": 'THREE', "value": 'PRESS', "shift": True}, {"index": 13}),
            ({"idname": "alva_cue.take", "key": 'FOUR', "value": 'PRESS', "shift": True}, {"index": 14}),
            ({"idname": "alva_cue.take", "key": 'FIVE', "value": 'PRESS', "shift": True}, {"index": 15}),
            ({"idname": "alva_cue.take", "key": 'SIX', "value": 'PRESS', "shift": True}, {"index": 16}),
            ({"idname": "alva_cue.take", "key": 'SEVEN', "value": 'PRESS', "shift": True}, {"index": 17}),
            ({"idname": "alva_cue.take", "key": 'EIGHT', "value": 'PRESS', "shift": True}, {"index": 18}),
            ({"idname": "alva_cue.take", "key": 'NINE', "value": 'PRESS', "shift": True}, {"index": 19}),
            ({"idname": "alva_cue.take", "key": 'ZERO', "value": 'PRESS', "shift": True}, {"index": 20})
        ]
    }
}


def register_keymap_item(keymap, idname, key, value, **kwargs):
    kmi = keymap.keymap_items.new(idname, type=key, value=value, **kwargs)
    return kmi


def register_keymaps():
    wm = bpy.context.window_manager
    if wm.keyconfigs.addon:
        for keymap_name, data in keymap_data.items():
            keymap = wm.keyconfigs.addon.keymaps.new(name=keymap_name, space_type=data["space_type"])
            for item, special_params in data["items"]:
                kmi = register_keymap_item(keymap, item['idname'], item['key'], item['value'], shift=item.get("shift", False))
                
                if special_params:
                    for prop, val in special_params.items():
                        setattr(kmi.properties, prop, val)
                
                if keymap_name == "Sequencer" and item["idname"] in ["alva_sequencer.properties", "alva_sequencer.formatter"]:
                    addon_keymaps.append((keymap, kmi))
                elif keymap_name == "Node Editor" and item["idname"] == "alva_node.formatter":
                    custom_node_editor_keymaps.append((keymap, kmi))


def unregister_keymaps():
    wm = bpy.context.window_manager
    if wm.keyconfigs.addon:
        for km, kmi in addon_keymaps:
            if km and kmi:
                try:
                    km.keymap_items.remove(kmi)
                except ReferenceError:
                    pass
       
        for km, kmi in custom_node_editor_keymaps:
            if km and kmi:
                try:
                    km.keymap_items.remove(kmi)
                except ReferenceError:
                    pass
        
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