# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
import mathutils

from ..assets.sli import SLI
from ..cpv.find import Find 


def find_parent(object):
    """
    Catches and corrects cases where the object is a collection property instead of 
    a node, sequencer strip, object, etc. This function returns the bpy object so
    that the rest of the harmonizer can find what it needs.
    """
    from ..updaters.node import NodeUpdaters 
    
    if not isinstance(object, bpy.types.PropertyGroup):
        return object

    node = None
    try:
        node = Find.find_node_by_tree(object.node_name, object.node_tree_name)
    except:
        pass
    
    if node:
        return node
                
    # Run the program that's supposed to set this up since it must not have run yet
    nodes = Find.find_nodes(bpy.context.scene)
    for node in nodes:
        if node.bl_idname == 'mixer_type':
            NodeUpdaters.update_node_name(node)
            
    # Try again
    try:
        node = Find.find_node_by_tree(object.node_name, object.node_tree_name)
    except:
        pass
    
    if node:
        return node
        
    print(f"find_parent could not find parent for {object}.")
    return None


def find_controller_type(parent, property_name):
    if not hasattr(parent, "type"):
        SLI.SLI_assert_unreachable()

    if parent.type == 'MESH' and hasattr(parent, "object_identities_enum"):
        if property_name in ['pan_graph', 'tilt_graph']:
            return "Pan/Tilt"
        return parent.object_identities_enum
    
    elif parent.type == 'COLOR':
        return "strip"
    
    elif parent.type == 'CUSTOM': # Nodes
        controller_types = {
        'group_controller_type': "group",
        'mixer_type': "mixer",
        }
        return controller_types.get(parent.bl_idname, None)
    
    SLI.SLI_assert_unreachable()
        


def color_object_to_tuple_and_scale_up(v):
    if type(v) == mathutils.Color:
        return (v.r * 100, v.g * 100, v.b * 100)

    else: 
        r, g, b = v
        return (r * 100, g * 100, b * 100)
    
    
def update_nodes(connected_nodes):
    for node in connected_nodes:
        update_alva_controller(node)


def update_alva_controller(controller):
    from ..makesrna.rna_common import CommonProperties 
    props = CommonProperties

    if hasattr(controller, "bl_idname") and controller.bl_idname == 'mixer_type':
        for choice in controller.parameters:
            for prop_name, _ in props.common_parameters:
                setattr(choice, prop_name, getattr(choice, prop_name))

    else:
        for prop_name, _ in props.common_parameters + props.common_parameters_extended:
            setattr(controller, prop_name, getattr(controller, prop_name))


def home_alva_controller(controller):
    from ..makesrna.rna_common import CommonProperties 
    props = CommonProperties

    if hasattr(controller, "bl_idname") and controller.bl_idname == 'mixer_type':
        controller.float_offset = 0
        controller.int_subdivisions = 0

        for choice in controller.parameters:
            for prop_name, prop in props.common_parameters:
                try:
                    current_value = getattr(choice, prop_name)
                    if prop_name == "alva_iris":
                        setattr(choice, prop_name, 100)
                    elif prop_name == "alva_color":
                        setattr(choice, prop_name, tuple(1.0 for _ in current_value))
                    elif prop_name in ["alva_intensity", "alva_pan", "alva_tilt", "alva_zoom"]:
                        setattr(choice, prop_name, 0)
                except AttributeError:
                    print(f"Attribute {prop_name} not found in controller, skipping.")

    else:
        for prop_name, prop in props.common_parameters + props.common_parameters_extended:
            try:
                current_value = getattr(controller, prop_name)
                if prop_name == "alva_iris":
                    setattr(controller, prop_name, 100)
                elif prop_name == "alva_color":
                    setattr(controller, prop_name, tuple(1.0 for _ in current_value))
                elif prop_name in [
                    "alva_intensity", "alva_pan", "alva_tilt", "alva_zoom", "alva_strobe", 
                    "alva_edge", "alva_diffusion", "alva_gobo_speed", "alva_gobo_id", "alva_prism"]:
                    setattr(controller, prop_name, 0)
            except AttributeError:
                print(f"Attribute {prop_name} not found in controller, skipping.")


def simplify_channels_list(channels):
    #[1, 2, 3, 10, 11, 15, 16, 17, 18] -> "1 Thru 3 + 10 Thru 11 + 15 Thru 18"
    if not channels:
        return ""
    channels.sort()
    combined_channels = []
    start = channels[0]
    end = channels[0]

    for c in channels[1:]:
        if c == end + 1:
            end = c
        else:
            if start == end:
                combined_channels.append(str(start))
            else:
                combined_channels.append(f"{start} Thru {end}")
            start = end = c

    if start == end:
        combined_channels.append(str(start))
    else:
        combined_channels.append(f"{start} Thru {end}")

    return " + ".join(combined_channels)