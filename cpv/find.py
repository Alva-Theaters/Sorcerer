# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from ..assets.dictionaries import Dictionaries 
from ..assets.sli import SLI


class Find:
    def find_controller_by_space_type(context, space_type, node_name, node_tree_name):
        '''Used by home, update, and special props operators to find 
            correct active controller, whether node, strip, or object'''
        if space_type == 'NODE_EDITOR':
            if node_name and node_tree_name:
                return Find.find_node_by_tree(node_name, node_tree_name)
            else:
                SLI.SLI_assert_unreachable()
        
        elif space_type == 'SEQUENCE_EDITOR':
            return context.scene.sequence_editor.active_strip
        
        elif space_type == 'VIEW_3D':
            return context.active_object
        
        else:
            print(f"Invalid space_type: {space_type}")
            SLI.SLI_assert_unreachable()


    #-------------------------------------------------------------------------------------------------------------------------------------------
    '''NODE finders'''
    #-------------------------------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def find_channels_from_node_links(input_socket, group_list, update_nodes, is_input=True):
        '''Finds the channels inside just one socket'''
        connected_nodes = Find.find_connected_nodes(input_socket, is_input)

        if update_nodes:
            update_nodes(connected_nodes)

        for node in connected_nodes:
            if node.bl_idname == "group_controller_type":
                group_list.extend(Find._find_node_channels_list(node))
            elif node.bl_idname == "mixer_type":
                group_list.extend(Find._find_node_channels_list(node))

    @staticmethod
    def _find_node_channels_list(node):
        return [str(channel.chan) for channel in node.list_group_channels]


    @staticmethod
    def find_connected_nodes(socket, is_input=True):
        '''Returns list of nodes connected to socket, including those connected 
            to input sockets of found nodes.'''
        connected_nodes = []

        def add_connected_nodes(current_socket):
            if is_input:
                links = current_socket.links
                from_socket_attr = 'from_socket'
                to_socket_attr = 'to_socket'
            else:
                links = current_socket.links
                from_socket_attr = 'to_socket'
                to_socket_attr = 'from_socket'

            for link in links:
                connected_node = getattr(link, from_socket_attr).node
                if connected_node not in connected_nodes:
                    connected_nodes.append(connected_node)
                    # Recursively find nodes connected to the current node's sockets
                    for next_socket in connected_node.inputs if is_input else connected_node.outputs:
                        add_connected_nodes(next_socket)
                    if connected_node.bl_idname == 'ShaderNodeGroup':
                        group_node_tree = connected_node.node_tree
                        for node in group_node_tree.nodes:
                            if node.type == 'GROUP_OUTPUT':
                                for inner_socket in node.inputs if is_input else node.outputs:
                                    add_connected_nodes(inner_socket)

        add_connected_nodes(socket)
        return connected_nodes


    @staticmethod    
    def find_node_by_tree(node_name, node_tree_name, pointer=False):
        '''Finds the node by the node name and by the node tree name. Used
            mostly for operators drawn on nodes that need to operate on the
            node. Because Blender isn't smart enough to let us pass the node 
            class instance to a pointer property on the operator class.
            
            Passing pointer as truthy means node_tree_name being passed is
            a pointer property to the actual id, not just the name. We have
            to do this because bpy.types.Operator can store string props, but
            not PointerProperty the way bpy.types.Node can.'''
        if not pointer:
            node_tree = bpy.data.node_groups.get(node_tree_name)
        else:
            node_tree = node_tree_name
            
        if not node_tree:
            for world in bpy.data.worlds:
                if world.node_tree and world.node_tree.name == node_tree_name:
                    node_tree = world.node_tree
                    if not node_tree:
                        return None

        return node_tree.nodes.get(node_name) 


    @staticmethod
    def join_flash_channels(up_channels_list, down_channels_list):
        up_channels_str = ' + '.join(up_channels_list)
        down_channels_str = ' + '.join(down_channels_list)
        return up_channels_str, down_channels_str


    def trigger_downstream_nodes(self, parent, attribute_name, new_value):
        """Receives a bpy object and returns nothing"""
        for output_socket in parent.outputs:
            if output_socket.bl_idname == 'LightingOutputType':
                for link in output_socket.links:
                    connected_node = link.to_socket.node
                    if connected_node.bl_idname == "group_controller_type":
                        setattr(connected_node, f"alva_{attribute_name}", new_value + getattr(connected_node, f"alva_{attribute_name}"))
                    elif connected_node.bl_idname == "mixer_type":
                        connected_node.mirror_upstream_group_controllers()
                        
        
    #-------------------------------------------------------------------------------------------------------------------------------------------
    '''CONTROLLER finders'''
    #-------------------------------------------------------------------------------------------------------------------------------------------
    # Find object, strip, and node controllers.
    def find_controllers(scene):
        controllers = []
        objects = []
        strips = []
        nodes = []
        mixers_and_motors = []

        if scene.scene_props.enable_objects:
            objects = Find.find_objects(scene)
        if scene.scene_props.enable_strips:
            strips = Find.find_strips(scene)
        if scene.scene_props.enable_nodes:
            nodes = Find.find_nodes(scene)
            mixers_and_motors = [node for node in nodes if node.bl_idname in ['mixer_type', 'motor_type']]

        controllers = objects + strips + nodes

        return controllers, mixers_and_motors

    def find_objects(scene):
        if not scene.scene_props.enable_objects:
            return []
        return [obj for obj in scene.objects]

    def find_strips(scene):
        if not scene.scene_props.enable_strips or not hasattr(scene, "sequence_editor"):
            return []
        strips = []
        for strip in scene.sequence_editor.sequences_all:
            if strip.type == 'COLOR' and strip.my_settings.motif_type_enum == 'option_animation':
                strips.append(strip)
        return strips

    def find_nodes(scene):
        if not scene.scene_props.enable_nodes:
            return []
        node_trees = set()
        nodes = []
        if bpy.context.scene.world and bpy.context.scene.world.node_tree:
            node_trees.add(bpy.context.scene.world.node_tree)
        for node_tree in bpy.data.node_groups:
            node_trees.add(node_tree)
        for node_tree in node_trees:
            for node in node_tree.nodes:
                nodes.append(node)
        return nodes