# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
import time

from ..assets.sli import SLI
from ..maintenance.logging import alva_log


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
        connected_nodes = FindConnectedNodes(input_socket, is_input).execute()

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
                connected_nodes = FindConnectedNodes(output_socket, is_input=False).execute()
                for connected_node in connected_nodes:
                    setattr(connected_node, f"alva_{attribute_name}", getattr(parent, f"alva_{attribute_name}"))
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
    

class FindConnectedNodes:
    def __init__(self, original_socket, is_input):
        self.original_socket = original_socket
        self.socket_attr = 'from_socket' if is_input else 'to_socket'
        self.LINKABLE_NODE_TYPES = ['group_controller_type', 'mixer_type']
        self.is_input = is_input
        self.connected_nodes = []

    def execute(self):
        start_time = time.time()
        self.socket_to_links(self.original_socket)
        alva_log('time', f"TIME: FindConnectedNodes took {time.time() - start_time} seconds\n")
        return self.connected_nodes

    def socket_to_links(self, socket, socket_index=None):
        if not socket.links:
            return 
        
        for i, link in enumerate(socket.links):
            node = self.node_from_link(link)

            if node:
                self.connected_nodes.append(node)
                self.process_downstream_socket_recursive(node)

    def node_from_link(self, link):
        connected_socket = getattr(link, self.socket_attr)
        connected_node = connected_socket.node

        if not self.validate_node(connected_node):
            if connected_node.bl_idname == 'ShaderNodeGroup':
                socket_list = connected_node.outputs if self.is_input else connected_node.inputs
                socket_index = self.find_socket_index(connected_socket, socket_list)
                self.process_group_node(connected_node, socket_index)
                return
        
        return connected_node
    
    def find_socket_index(self, target_socket, sockets_list):
        """Find the index of the target socket in its node's inputs or outputs."""
        for i, socket in enumerate(sockets_list):
            if socket == target_socket:
                return i
        raise ValueError(f"Socket {target_socket.name} not found in node {target_socket.node.name}")
        
    def validate_node(self, node):
        if node in self.connected_nodes:
            return False
        
        if str(node.bl_idname) not in self.LINKABLE_NODE_TYPES:
            return False
        
        return True
    
    def process_downstream_socket_recursive(self, node, node_group=False):
        for next_socket in node.inputs if self.is_input else node.outputs:
            self.socket_to_links(next_socket)

    def process_group_node(self, group_node, socket_index):
        group_node_tree = group_node.node_tree
        group_input_node = next((n for n in group_node_tree.nodes if n.type == 'GROUP_INPUT'), None)

        if not group_input_node:
            return
        
        internal_sockets = group_input_node.inputs if self.is_input else group_input_node.outputs
        internal_socket = internal_sockets[socket_index]
        self.socket_to_links(internal_socket)