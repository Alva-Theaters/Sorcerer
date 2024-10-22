# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Operator
from bpy.props import StringProperty, IntProperty
import time

from ..utils.osc import OSC
from ..utils.cpvia_utils import update_alva_controller, home_alva_controller
from utils.sequencer_utils import duplicate_active_strip_to_selected
from ..utils.rna_utils import update_all_controller_channel_lists, apply_patch
from ..updaters.common import CommonUpdaters
from ..as_ui.space_alvapref import draw_settings 
from ..cpvia.find import Find
from ..as_ui.space_wm import (
    draw_edge_diffusion_settings, 
    draw_gobo_settings, 
    draw_pan_tilt_settings, 
    draw_strobe_settings, 
    draw_zoom_settings, 
    draw_splash
)

# pyright: reportInvalidTypeForm=false


#-------------------------------------------------------------------------------------------------------------------------------------------
'''TOPBAR Operators'''
#-------------------------------------------------------------------------------------------------------------------------------------------   
class TOPBAR_OT_alva_settings(Operator):
    '''Pop-up for Sorcerer Settings menu'''
    bl_idname = "alva_topbar.preferences"
    bl_label = "Sorcerer Settings"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return (context.scene is not None) and (context.scene.sequence_editor is not None)

    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=500)
    
    def draw(self, context):
        draw_settings(self, context)


class TOPBAR_OT_alva_splash_screen(Operator):
    bl_idname = "alva_topbar.splash"
    bl_label = "Alva Sorcerer Splash"
    
    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        width = 375
        return context.window_manager.invoke_props_dialog(self, width=width)

    def draw(self, context):
        draw_splash(self, context)

        
#-------------------------------------------------------------------------------------------------------------------------------------------
'''CONTROLLER Operators'''
#-------------------------------------------------------------------------------------------------------------------------------------------
class COMMON_OT_alva_copy_patch(Operator):
    '''Copies active object's patch to other selected objects'''
    bl_idname = "alva_common.copy_patch"
    bl_label = "Copy Patch"

    space_type: StringProperty()  
    node_name: StringProperty() 
    node_tree_name: StringProperty() 

    def execute(self, context):
        all_properties = [
            "pan_min", "pan_max", "tilt_min", "tilt_max", "zoom_min", "zoom_max", 
            "gobo_speed_min", "gobo_speed_max", "influence_is_on", "intensity_is_on", 
            "pan_tilt_is_on", "color_is_on", "diffusion_is_on", "strobe_is_on", 
            "zoom_is_on", "iris_is_on", "edge_is_on", "gobo_is_on", "prism_is_on", 
            "str_enable_strobe_argument", "str_disable_strobe_argument", 
            "str_enable_gobo_speed_argument", "str_disable_gobo_speed_argument", 
            "str_gobo_id_argument", "str_gobo_speed_value_argument", 
            "str_enable_prism_argument", "str_disable_prism_argument", "color_profile_enum",
            "alva_white_balance"
        ]

        properties = all_properties
        st = context.space_data.type

        finders = Find
        active_controller = finders.find_controller_by_space_type(context, self.space_type, self.node_name, self.node_tree_name)

        if st == 'VIEW_3D' and len(context.selected_objects) > 1:
            for obj in context.selected_objects:
                if obj != active_controller:
                    CommonUpdaters._update_properties(active_controller, obj, properties)

        elif st == 'NODE_EDITOR' and len(context.selected_nodes) > 1:
            for node in context.selected_nodes:
                if node != active_controller and node.bl_idname in ['group_controller_type', 'mixer_type']:
                    CommonUpdaters._update_properties(active_controller, node, properties)

        elif st == 'SEQUENCE_EDITOR' and len(context.selected_sequences) > 1:
            for strip in context.selected_sequences:
                if strip != active_controller and strip.type == 'COLOR':
                    CommonUpdaters._update_properties(active_controller, strip, properties)

        return {'FINISHED'}


class COMMON_OT_alva_home_controller(Operator):
    bl_idname = "alva_node.home"
    bl_label = "Home"

    space_type: StringProperty()  
    node_name: StringProperty() 
    node_tree_name: StringProperty()  

    def execute(self, context):
        finders = Find
        active_controller = finders.find_controller_by_space_type(context, self.space_type, self.node_name, self.node_tree_name)
        home_alva_controller(active_controller)
        return {'FINISHED'}


class COMMON_OT_alva_update_controller(Operator):
    bl_idname = "alva_node.update"
    bl_label = "Update"

    space_type: StringProperty() 
    node_name: StringProperty() 
    node_tree_name: StringProperty() 

    def execute(self, context):
        finders = Find
        active_controller = finders.find_controller_by_space_type(context, self.space_type, self.node_name, self.node_tree_name)
        update_alva_controller(active_controller)
        return {'FINISHED'}
    
    
class COMMON_OT_alva_strobe_props(Operator):
    bl_idname = "alva_common.strobe_properties"
    bl_label = "View Strobe Properties"
    
    space_type: StringProperty() 
    node_name: StringProperty() 
    node_tree_name: StringProperty() 
    
    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=250)

    def draw(self, context):
        finders = Find
        active_controller = finders.find_controller_by_space_type(context, self.space_type, self.node_name, self.node_tree_name)
        draw_strobe_settings(self, context, active_controller)


class COMMON_OT_alva_pan_tilt_props(Operator):
    bl_idname = "alva_common.pan_tilt_properties"
    bl_label = "Pan/Tilt Properties"
    bl_description = "Access pan and tilt min and max settings"

    space_type: StringProperty() 
    node_name: StringProperty() 
    node_tree_name: StringProperty() 
    
    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=200)

    def draw(self, context):
        finders = Find
        active_controller = finders.find_controller_by_space_type(context, self.space_type, self.node_name, self.node_tree_name)
        draw_pan_tilt_settings(self, context, active_controller)
       
    
class COMMON_OT_alva_zoom_iris_props(Operator):
    bl_idname = "alva_common.zoom_iris_properties"
    bl_label = "Zoom/Iris Properties"
    bl_description = "Access min and max settings"

    space_type: StringProperty() 
    node_name: StringProperty() 
    node_tree_name: StringProperty()  
    
    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=200)

    def draw(self, context):
        finders = Find
        active_controller = finders.find_controller_by_space_type(context, self.space_type, self.node_name, self.node_tree_name)
        draw_zoom_settings(self, context, active_controller)
        

class COMMON_OT_alva_edge_diffusion_props(Operator):
    bl_idname = "alva_common.edge_diffusion_properties"
    bl_label = "Edge/Diffusion Properties"
    
    space_type: StringProperty()  
    node_name: StringProperty()  
    node_tree_name: StringProperty()  
    
    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=200)

    def draw(self, context):
        finders = Find
        active_controller = finders.find_controller_by_space_type(context, self.space_type, self.node_name, self.node_tree_name)
        draw_edge_diffusion_settings(self, context, active_controller)
    
       
class COMMON_OT_alva_gobo_props(Operator):
    bl_idname = "alva_common.gobo_properties"
    bl_label = "View Gobo Properties"
    bl_description = "Access gobo-related settings"

    space_type: StringProperty() 
    node_name: StringProperty() 
    node_tree_name: StringProperty() 
    
    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        finders = Find
        active_controller = finders.find_controller_by_space_type(context, self.space_type, self.node_name, self.node_tree_name)
        draw_gobo_settings(self, context, active_controller)


class COMMON_OT_alva_clear_solo(Operator):
    '''Turns off the solo on all controllers'''
    bl_idname = "alva_playback.clear_solos"
    bl_label = "Clear Solos"

    def execute(self, context):
        all_controllers, mixers_and_motors = Find.find_controllers(context.scene)
        for controller in all_controllers:
            if hasattr(controller, 'alva_solo') and controller.alva_solo:
                controller.alva_solo = False

        context.scene.scene_props.has_solos = False
        return {'FINISHED'}
    

class COMMON_OT_alva_white_balance(Operator):
    '''Set the current value as white. This is like setting your white balance on a camera'''
    bl_idname = "alva_common.white_balance"
    bl_label = "Set White Balance"

    space_type: StringProperty() 
    node_name: StringProperty() 
    node_tree_name: StringProperty() 

    def execute(self, context):
        active_controller = Find.find_controller_by_space_type(context, self.space_type, self.node_name, self.node_tree_name)
        if hasattr(active_controller, "float_vec_color"):
            active_controller.alva_white_balance = active_controller.float_vec_color
        else:
            self.report({'INFO'}, "Cannot white balance mixers")
            return {'CANCELLED'}
        time.sleep(.2) # Because it threw an error without, I think?
        active_controller.float_vec_color = (1.0, 1.0, 1.0)
        return {'FINISHED'}
    

class COMMON_OT_alva_apply_patch(Operator):
    '''Apply to selected objects'''
    bl_idname = "alva_common.patch_to_selected"
    bl_label = "Apply Settings"
    
    group_id: StringProperty()
    
    def execute(self, context):
        item = context.scene.scene_group_data.get(self.group_id)  # Get the object by name
        if item is None:
            self.report({'ERROR'}, "Group not found")
            return {'CANCELLED'}
        
        for obj in context.selected_objects:
            try:
                apply_patch(item, obj)
            except: pass
          
        return {'FINISHED'}
    

class COMMON_OT_alva_add_group(Operator):
    bl_idname = "alva_common.add_group"
    bl_label = "Add a new group"

    def execute(self, context):
        scene = context.scene
        new_item = scene.scene_group_data.add()
        new_item.name = "New Group"
        scene.scene_props.group_data_index = len(scene.scene_group_data) - 1
        return {'FINISHED'}
    

class COMMON_OT_alva_remove_group(Operator):
    bl_idname = "alva_common.remove_group"
    bl_label = "Remove the selected group"

    def execute(self, context):
        scene = context.scene
        index = scene.scene_props.group_data_index

        scene.scene_group_data.remove(index)

        if index > 0:
            scene.scene_props.group_data_index = index - 1
        else:
            scene.scene_props.group_data_index = 0
        return {'FINISHED'}


class COMMON_OT_alva_bump_group(Operator):
    bl_idname = "alva_common.bump_group"
    bl_label = "Bump Group Up or Down"
    
    direction: bpy.props.IntProperty()

    def execute(self, context):
        scene = context.scene
        index = scene.scene_props.group_data_index
        
        if self.direction == 1 and index < len(scene.scene_group_data) - 1:
            scene.scene_group_data.move(index, index + 1)
            scene.scene_props.group_data_index += 1
        elif self.direction == -1 and index > 0:
            scene.scene_group_data.move(index, index - 1)
            scene.scene_props.group_data_index -= 1
        else:
            self.report({'WARNING'}, "Cannot move further in this direction")
        
        return {'FINISHED'}
    
    
class COMMON_OT_alva_remove_channel_from_group(Operator):
    bl_idname = "alva_common.remove_or_highlight_channel"
    bl_label = "Highlight or Remove"
    bl_description = "Highlight or remove channel, depending on selection below"
    
    group_id: StringProperty()
    channel: IntProperty()
    
    def execute(self, context):
        item = context.scene.scene_group_data.get(self.group_id)
        if item is None:
            self.report({'ERROR'}, "Group not found")
            return {'CANCELLED'}
        
        if item.highlight_or_remove_enum == 'option_remove':
            index_to_remove = -1
            for idx, channel in enumerate(item.channels_list):
                if channel.chan == self.channel:
                    index_to_remove = idx
                    break
            
            if index_to_remove != -1:
                item.channels_list.remove(index_to_remove)
            else:
                self.report({'WARNING'}, "Channel not found")
        else:
            scene = context.scene.scene_props

            OSC.send_osc_lighting("/eos/newcmd", f"{self.channel} at + 100 Sneak Time .5 Enter")
            time.sleep(.5)
            OSC.send_osc_lighting("/eos/newcmd", f"{self.channel} at + - 100 Sneak Time 1 Enter")

        update_all_controller_channel_lists(context)
        
        return {'FINISHED'}
        

#-------------------------------------------------------------------------------------------------------------------------------------------
'''TOOLBAR Operators'''
#-------------------------------------------------------------------------------------------------------------------------------------------      
class TOOL_OT_alva_ghost_out(Operator):
    bl_idname = "alva_tool.ghost_out"
    bl_label = "Ghost Out"
    bl_description = "Presses Go_to Cue Out on the console"
    
    def execute(self, context):
        ghost_out_time = context.scene.scene_props.ghost_out_time
        ghost_out_string = context.scene.scene_props.ghost_out_string
        argument = ghost_out_string.replace("*", str(ghost_out_time))
        OSC.send_osc_lighting("/eos/newcmd", argument)

        for obj in bpy.context.scene.objects:
            if obj.type == "MESH" and hasattr(obj.data, 'materials'):
                for mat in obj.data.materials:
                    if mat and mat.use_nodes:
                        nodes = mat.node_tree.nodes
                        for node in nodes:
                            if node.type == 'EMISSION':
                                node.inputs['Color'].default_value = (1, 1, 1, 1)
                                node.inputs['Strength'].default_value = 0
        
        return {'FINISHED'}
    
class TOOL_OT_alva_displays(Operator):
    bl_idname = "alva_tool.displays"
    bl_label = "Displays"
    bl_description = "Presses Displays on the console"
    
    def execute(self, context):
        OSC.send_osc_lighting("/eos/key/displays", "1")
        OSC.send_osc_lighting("/eos/key/displays", "0")
        return {'FINISHED'}
    
class TOOL_OT_alva_about(Operator):
    bl_idname = "alva_tool.about"
    bl_label = "About"
    bl_description = "Presses About on the console"
    
    def execute(self, context):
        OSC.send_osc_lighting("/eos/key/about", "0")
        return {'FINISHED'}

class TOOL_OT_alva_stop_clocks(Operator):
    bl_idname = "alva_tool.disable_clocks"
    bl_label = "Disable All Clocks"
    bl_description = "Disables all timecode clocks in ETC Eos"
    
    def execute(self, context):
        clock_number = 1
        
        while clock_number <= 100:
            OSC.send_osc_lighting("/eos/newcmd", f"Event {str(clock_number)} / Internal Disable Enter")
            clock_number += 1
            
        return {'FINISHED'}
     
class TOOL_OT_alva_copy_various_to_selected(Operator):
    bl_idname = "alva_tool.copy"
    bl_label = "Copy to Selected"
    bl_description = "Copy some properties of the active strip to all the other selected strips"

    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        
        # Avoid infinite recursion on color updater.
        if active_strip and active_strip.type == 'COLOR':
            global stop_updating_color
            stop_updating_color = "Yes"
        
        duplicate_active_strip_to_selected(context)
                        
        stop_updating_color = "No"
                    
        return {'FINISHED'}
    

#-------------------------------------------------------------------------------------------------------------------------------------------
'''SHOW MESSAGE Operator'''
#-------------------------------------------------------------------------------------------------------------------------------------------
class WM_OT_alva_show_message(bpy.types.Operator):
    '''DO NOT DELETE. This is for showing error messages with updaters,
       where access to self.report is not allowed.'''
    bl_idname = "alva_wm.show_message"
    bl_label = "Alva Sorcerer"
    
    message: StringProperty(name="Message", default="") 

    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.label(text=self.message)
        
        
operator_classes = [
    TOPBAR_OT_alva_settings,
    TOPBAR_OT_alva_splash_screen,
    COMMON_OT_alva_copy_patch,
    COMMON_OT_alva_home_controller,
    COMMON_OT_alva_update_controller,
    COMMON_OT_alva_strobe_props,
    COMMON_OT_alva_pan_tilt_props,
    COMMON_OT_alva_zoom_iris_props,
    COMMON_OT_alva_edge_diffusion_props,
    COMMON_OT_alva_gobo_props,
    COMMON_OT_alva_clear_solo,
    COMMON_OT_alva_white_balance,
    COMMON_OT_alva_apply_patch,
    COMMON_OT_alva_add_group,
    COMMON_OT_alva_remove_group,
    COMMON_OT_alva_bump_group,
    COMMON_OT_alva_remove_channel_from_group,
    TOOL_OT_alva_ghost_out,
    TOOL_OT_alva_displays,
    TOOL_OT_alva_about,
    TOOL_OT_alva_stop_clocks,
    TOOL_OT_alva_copy_various_to_selected,
    WM_OT_alva_show_message
]


def register():
    for cls in operator_classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(operator_classes):
        bpy.utils.unregister_class(cls)