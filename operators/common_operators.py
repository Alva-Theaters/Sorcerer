# This file is part of Alva Sorcerer
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
import time

from ..utils.osc import OSC as osc 
from ..utils.cpvia_utils import update_alva_controller, home_alva_controller
from utils.sequencer_utils import duplicate_active_strip_to_selected
from ..updaters.common_updaters import CommonUpdaters
from ..as_ui.space_alvapref import draw_settings 
from ..cpvia.find import Find 
from ..assets.dictionaries import Dictionaries
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


class TOPBAR_OT_splash_screen(Operator):
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


class HomeControllerButton(Operator):
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


class UpdateControllerButton(Operator):
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
    
    
class COMMON_OT_strobe_props(Operator):
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


class COMMON_OT_pan_tilt_props(Operator):
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
       
    
class COMMON_OT_zoom_iris_props(Operator):
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
        

class COMMON_OT_edge_diffusion_props(Operator):
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
    
       
class COMMON_OT_gobo_props(Operator):
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
    

class COMMON_OT_alva_add_driver(Operator):
    '''Create a Sorcerer driver to control parameters with movement in 3D View'''
    bl_idname = "alva_common.driver_add"
    bl_label = "Quick Driver"

    def execute(self, context):
        try:
            prop = context.button_prop
        except:
            return
            
        len_added = 0
        for obj in bpy.context.selected_objects:
            try:
                # Lock x and y
                obj.lock_location[0] = True
                obj.lock_location[1] = True

                # Add driver
                fcurve = obj.driver_add(prop.identifier)
                driver = fcurve.driver

                # Set driver properties
                var = driver.variables.new()
                var.name = "var"
                var.type = 'TRANSFORMS'
                var.targets[0].id = obj
                var.targets[0].transform_type = 'LOC_Z'
                var.targets[0].transform_space = 'WORLD_SPACE'
                driver.expression = "(var * 50) - 50"

                # Ensure "Tweak" is selected in toolbar for instant grabbing (TWSS)
                bpy.ops.wm.tool_set_by_id(name="builtin.select")
                len_added += 1

            except:
                self.report({'WARNING'}, "Error. Ensure object types are valid")
                return {'CANCELLED'}
            
        self.report({'INFO'}, f"Added {len_added} drivers")
        return {'FINISHED'}
        

#-------------------------------------------------------------------------------------------------------------------------------------------
'''TOOLBAR Operators'''
#-------------------------------------------------------------------------------------------------------------------------------------------      
class TOOL_OT_ghost_out(Operator):
    bl_idname = "alva_tool.ghost_out"
    bl_label = "Ghost Out"
    bl_description = "Presses Go_to Cue Out on the console"
    
    def execute(self, context):
        ghost_out_time = context.scene.scene_props.ghost_out_time
        ghost_out_string = context.scene.scene_props.ghost_out_string
        argument = ghost_out_string.replace("*", str(ghost_out_time))
        osc.send_osc_lighting("/eos/newcmd", argument)

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
    
class TOOL_OT_displays(Operator):
    bl_idname = "alva_tool.displays"
    bl_label = "Displays"
    bl_description = "Presses Displays on the console"
    
    def execute(self, context):
        osc.send_osc_lighting("/eos/key/displays", "1")
        osc.send_osc_lighting("/eos/key/displays", "0")
        return {'FINISHED'}
    
class TOOL_OT_about(Operator):
    bl_idname = "alva_tool.about"
    bl_label = "About"
    bl_description = "Presses About on the console"
    
    def execute(self, context):
        osc.send_osc_lighting("/eos/key/about", "0")
        return {'FINISHED'}

class TOOL_OT_stop_clocks(Operator):
    bl_idname = "alva_tool.disable_clocks"
    bl_label = "Disable All Clocks"
    bl_description = "Disables all timecode clocks in ETC Eos"
    
    def execute(self, context):
        clock_number = 1
        
        while clock_number <= 100:
            osc.send_osc_lighting("/eos/newcmd", f"Event {str(clock_number)} / Internal Disable Enter")
            clock_number += 1
            
        return {'FINISHED'}
     
class TOOL_OT_copy_various_to_selected(Operator):
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
'''TEXT Operator'''
#------------------------------------------------------------------------------------------------------------------------------------------- 
class TEXT_OT_populate_macros(Operator):
    '''Pop-up for Sorcerer Settings menu'''
    bl_idname = "alva_text.populate_macros"
    bl_label = "Populate Macro Buttons"

    filter_group: StringProperty()  

    def execute(self, context):
        scene = context.scene
        scene.macro_buttons.clear()

        groups = {
            "All": Dictionaries.macro_buttons,
            "Basic Operations": Dictionaries.basic_operations,
            "Numbers": Dictionaries.numbers,
            "Letters": Dictionaries.letters,
            "Console Buttons": Dictionaries.console_buttons,
            "Control": Dictionaries.control,
            "Network": Dictionaries.network,
            "Attributes": Dictionaries.attributes,
            "Effects": Dictionaries.effects,
            "Time and Date": Dictionaries.time_and_date,
            "Miscellaneous": Dictionaries.miscellaneous,
            "Timecode": Dictionaries.timecode,
        }

        if self.filter_group in groups:
            for name in groups[self.filter_group]:
                item = scene.macro_buttons.add()
                item.name = name

        return {'FINISHED'}


#-------------------------------------------------------------------------------------------------------------------------------------------
'''SHOW MESSAGE Operator'''
#-------------------------------------------------------------------------------------------------------------------------------------------
class WM_OT_show_message(bpy.types.Operator):
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
    TOPBAR_OT_splash_screen,
    COMMON_OT_alva_copy_patch,
    HomeControllerButton,
    UpdateControllerButton,
    COMMON_OT_strobe_props,
    COMMON_OT_pan_tilt_props,
    COMMON_OT_zoom_iris_props,
    COMMON_OT_edge_diffusion_props,
    COMMON_OT_gobo_props,
    COMMON_OT_alva_clear_solo,
    COMMON_OT_alva_white_balance,
    COMMON_OT_alva_add_driver,
    TOOL_OT_ghost_out,
    TOOL_OT_displays,
    TOOL_OT_about,
    TOOL_OT_stop_clocks,
    TOOL_OT_copy_various_to_selected,
    WM_OT_show_message,
    TEXT_OT_populate_macros
]


def register():
    for cls in operator_classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(operator_classes):
        bpy.utils.unregister_class(cls)