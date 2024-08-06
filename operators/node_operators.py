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
from bpy.types import Operator
from bpy.props import StringProperty

from ..ui.node_ui import NodeUI # type: ignore
from ..cpvia.find import Find # type: ignore


class NODE_OT_add_console_buttons(Operator):
    bl_idname = "node.add_console_buttons_node"
    bl_label = "Add Console Buttons"
    bl_description="Adjust all intensities of group controller nodes on this level"

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('console_buttons_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'} 
          
        
class NODE_OT_add_oven(Operator):
    bl_idname = "node.add_oven_node"
    bl_label = "Add Oven"
    bl_description="Create qmeos to store complex animation data directly on the console. Qmeos are like videos, but each frame is a lighting cue"

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('oven_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
        
    
class NODE_OT_add_settings(Operator):
    bl_idname = "node.add_settings_node"
    bl_label = "Add Settings"
    bl_description="Sorcerer node settings"

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('settings_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
        
    
class NODE_OT_add_global(Operator):
    bl_idname = "node.add_global_node"
    bl_label = "Add Global"
    bl_description="Adjust all intensities of group controller nodes on this level"

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('global_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        self.execute(context)
        bpy.ops.node.translate_attach_remove_on_cancel('INVOKE_DEFAULT', node='NEW')
        return {'FINISHED'}
        
    
class NODE_OT_add_presets(Operator):
    bl_idname = "node.add_presets_node"
    bl_label = "Add Presets"
    bl_description="Record and recall console presets"

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('presets_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
    
        
class NODE_OT_add_pan_tilt(Operator):
    bl_idname = "node.add_pan_tilt_node"
    bl_label = "Add Pan/Tilt controller for FOH-hung mover"
    bl_description="Intuitive pan/tilt controller only for FOH, forward-facing fixtures"

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('pan_tilt_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}    
    

class NODE_OT_add_group_controller(Operator):
    bl_idname = "node.add_group_controller_node"
    bl_label = "Control a group defined in Properties"
    bl_description="Control a group defined in Properties"

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('group_controller_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
        

class NODE_OT_add_mixer(Operator):
    bl_idname = "node.add_mixer_node"
    bl_label = "Mix 3 different parameter choices across a group"
    bl_description="Mix 3 different parameter choices accross a group"

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('mixer_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
    
    
class NODE_OT_add_motor(Operator):
    bl_idname = "node.add_motor_node"
    bl_label = "Create oscillations for mixer node progress"
    bl_description="Create oscillations for mixer node progress"

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('motor_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
    

class NODE_OT_add_flash(Operator):
    bl_idname = "node.add_flash_node"
    bl_label = "Connect to flash strips in the sequencer"
    bl_description="Autofill the Flash Up and Flash Down fields of flash strips in Sequencer with node settings and noodle links. Intended primarily for pose-based choreography"

    def execute(self, context):
        tree = context.space_data.edit_tree
        my_node = tree.nodes.new('flash_type')
        my_node.location = (100, 100)
        
        return {'FINISHED'}
        
        
class NODE_OT_node_formatter(Operator):
    bl_idname = "nodes.show_node_formatter"
    bl_label = "Node Formatter"
    
    @classmethod
    def poll(cls, context):
        return (context.scene is not None)

    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=300)
                
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        column = layout.column(align=True)
        
        space = context.space_data.edit_tree.nodes
        active_node = None 

        if hasattr(context.space_data, 'edit_tree') and context.space_data.edit_tree is not None:
            active_node = context.space_data.edit_tree.nodes.active

            if active_node and (active_node.bl_idname == "group_controller_type" or active_node.bl_idname == "group_driver_type" or active_node.bl_idname == "master_type"):
                NodeUI.draw_node_formatter_group(self, context, active_node)
                    
            elif active_node and active_node.bl_idname == "mixer_type" or active_node.bl_idname == "mixer_driver_type":
                NodeUI.draw_node_formatter_mixer(self, context, active_node)

            NodeUI.draw_node_formatter_footer(self, context, active_node)
            
            
class NODE_OT_keyframe_mixer(bpy.types.Operator):
    '''Keyframe mixer properties, since I key doesn't work here'''
    bl_idname = 'nodes.keyframe_mixer'
    bl_label = "Keyframe mixer"
    
    space_type: bpy.props.StringProperty() # type: ignore
    node_name: bpy.props.StringProperty() # type: ignore
    node_tree_name: bpy.props.StringProperty() # type: ignore
    
    def execute(self, context):
        finders = Find
        active_controller = finders.find_controller_by_space_type(context, self.space_type, self.node_name, self.node_tree_name)
        if not active_controller:
            return {'CANCELLED'}
        
        try:
            parameters = active_controller.parameters
            print("SUCCESS")
        except Exception as e:
            self.report({'INFO'}, "Please contact Alva Theaters.")
            print(f"Error: {str(e)}")
            return {'CANCELLED'}
        
        # Assuming `parameters` is a collection, we will access properties directly by name.
        if active_controller.parameters_enum == 'option_intensity':
            data_path = 'parameters["float_intensity"]'
            value = parameters.get("float_intensity")
            
        elif active_controller.parameters_enum == 'option_color':
            data_path = 'parameters["float_vec_color"]'
            value = parameters.get("float_vec_color")
            
        elif active_controller.parameters_enum == 'option_pan_tilt':
            data_path = 'parameters["float_pan"]'
            value = parameters.get("float_pan")
            
        elif active_controller.parameters_enum == 'option_zoom':
            data_path = 'parameters["float_zoom"]'
            value = parameters.get("float_zoom")
            
        elif active_controller.parameters_enum == 'option_iris':
            data_path = 'parameters["float_iris"]'
            value = parameters.get("float_iris")
        
        print(f"Attempting to keyframe: {data_path} with value: {value}")
        
        try:
            # Attempting to use keyframe_insert with the correct path
            active_controller.keyframe_insert(data_path=data_path, frame=bpy.context.scene.frame_current)
        except Exception as e:
            print(f"Failed to keyframe: {str(e)}")
            self.report({'ERROR'}, f"Failed to keyframe: {str(e)}")
            for prop_name in parameters.keys():
                print(f"Property name: {prop_name}")
                print(f"Value: {parameters[prop_name]}")
            return {'CANCELLED'}
    
        return {'FINISHED'}

            
operator_classes = [
    NODE_OT_add_console_buttons,
    NODE_OT_add_oven,
    NODE_OT_add_settings,
    NODE_OT_add_global,
    NODE_OT_add_presets,
    NODE_OT_add_pan_tilt,
    NODE_OT_add_group_controller,
    NODE_OT_add_mixer,
    NODE_OT_add_motor,
    NODE_OT_add_flash,
    NODE_OT_node_formatter,
    NODE_OT_keyframe_mixer
]


def register():
    for cls in operator_classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(operator_classes):
        bpy.utils.unregister_class(cls)