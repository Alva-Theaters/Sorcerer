# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from ..assets.dictionaries import Dictionaries 
from ..assets.sli import SLI


class Find:
    def find_my_argument_template(self, parent, type, chan, param, value):
        console_mode = bpy.context.scene.scene_props.console_type_enum
        if console_mode == "option_eos":
            argument = Dictionaries.eos_arguments_dict.get(f"str_{param}_argument", "Unknown Argument")
        elif console_mode == 'option_ma3':
            argument = Dictionaries.ma3_arguments_dict.get(f"str_{param}_argument", "Unknown Argument")
        elif console_mode == 'option_ma2':
            argument = Dictionaries.ma2_arguments_dict.get(f"str_{param}_argument", "Unknown Argument")
        else:
            SLI.SLI_assert_unreachable()
            return "Invalid console mode."

        needs_special = False
        if param in ['strobe', 'prism']:
            needs_special = True
            if value == 0:
                special_argument = self.find_my_patch(parent, chan, type, f"str_disable_{param}_argument")
            else: special_argument = self.find_my_patch(parent, chan, type, f"str_enable_{param}_argument")

        if needs_special:
            if param == 'strobe':
                if value == 0:
                    argument = f"{special_argument}"
                else:
                    argument = f"{special_argument}, {argument}"
            else:
                argument = special_argument

        return argument
                


    def find_my_patch(self, parent, chan, type, desired_property):
        """
        [EDIT 6/29/24: This docustring is slightly outdated now after revising the code for 
        new patch system]
        
        Below, "patch" refers to a special setting like an argument or min/max for something
        like pan/tilt, strobe, gobo things, etc.
        
        This function finds the best patch for a given channel. If the controller type is
        not Fixture or P/T Fixture, then it tries to find an object in the 3D scene that
        represents that channel. If it finds one, it will return that object's desired
        property. If the controller type (type) is Fixture or P/T Fixture, then it will
        use that object's patch. If neither of those 2 options work out, it will give up,
        surrender, and just use the parent controller's patch. 
        
        The goal of this function is to ensure that the user has a way to patch all fixtures
        and expect that Sorcerer will behave more or less like a full-blown console——that is
        to say, things like color profiles, mins and maxes, and other things fade away into
        the background and the user doesn't hardly ever have to worry about it. With this
        function, if the user patches the min/max, color profiles, and abilities and whatnot
        for each fixture, then this function will always use that patch for each individual
        fixture——regardless of what controller is controlling the fixture.
        
        At the same time however, if the user doesn't feel like patching beforehand, they
        can make things happen extremely quickly without ever thinking about patch. That's
        why we have a local patch built into the UI of each controller.
        
        Parameters:
            parent: the parent controller object, a node, object, or color strip
            chan: the channel number as defined by the parent's list_group_channels
            type: the controllertype of parent controller object, can be mixer, group node, stage object, etc.
            desired_property: the patch property that is being requested, in string form
            
        Returns:
            desired_property: The value of the requested property, aka the patch info
        """
        if type not in ["Fixture", "Pan/Tilt Fixture"]:
            for obj in bpy.data.objects:
                if obj.object_identities_enum == "Fixture" and obj.list_group_channels[0].chan == chan:
                    return getattr(obj, desired_property)
                
        return getattr(parent, desired_property)


    '''NOTE: If random stuff broke that used to be fine, it's probably this function's fault.'''
    def find_parent(self, object):
        """
        Catches and corrects cases where the object is a collection property instead of 
        a node, sequencer strip, object, etc. This function returns the bpy object so
        that the rest of the harmonizer can find what it needs.
        
        Parameters: 
            object: A bpy object that may be a node, strip, object, or collection property
        Returns:
            parent: A bpy object that may be a node, strip, or object
        """
        from ..updaters.node import NodeUpdaters 
        
        if not isinstance(object, bpy.types.PropertyGroup):
            return object

        node = None
        try:
            node = Find.find_node_by_tree(object.node_name, object.node_tree_pointer, pointer=True)
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
            node = Find.find_node_by_tree(object.node_name, object.node_tree_pointer, pointer=True)
        except:
            pass
        
        if node:
            return node
            
        print(f"find_parent could not find parent for {object}.")
        return None
        
        
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
                group_list.extend(Find.find_channels_list(node, string=True))
            elif node.bl_idname == "mixer_type":
                group_list.extend(Find.find_channels_list(node, string=True))


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
                        setattr(connected_node, attribute_name, new_value)
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