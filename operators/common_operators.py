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

from ..utils.osc import OSC as osc # type: ignore
from ..utils.utils import Utils
from ..ui.common_ui import CommonUI # type: ignore
from ..ui.settings_ui import SettingsUI # type: ignore
from ..cpvia.find import Find # type: ignore
from ..assets.dictionaries import Dictionaries
        
        
#-------------------------------------------------------------------------------------------------------------------------------------------
'''CONTROLLER Operators'''
#-------------------------------------------------------------------------------------------------------------------------------------------
class HomeControllerButton(Operator):
    bl_idname = "node.home_group"
    bl_label = "Home Group"

    space_type: StringProperty() # type: ignore # type: ignore
    node_name: StringProperty() # type: ignore
    node_tree_name: StringProperty() # type: ignore # type: ignore

    def execute(self, context):
        finders = Find
        active_controller = finders.find_controller_by_space_type(context, self.space_type, self.node_name, self.node_tree_name)
        Utils.home_alva_controller(active_controller)
        return {'FINISHED'}


class UpdateControllerButton(Operator):
    bl_idname = "node.update_group"
    bl_label = "Update Group"

    space_type: StringProperty() # type: ignore
    node_name: StringProperty() # type: ignore
    node_tree_name: StringProperty() # type: ignore

    def execute(self, context):
        finders = Find
        active_controller = finders.find_controller_by_space_type(context, self.space_type, self.node_name, self.node_tree_name)
        Utils.update_alva_controller(active_controller)
        return {'FINISHED'}
    
    
class COMMON_OT_strobe_props(Operator):
    bl_idname = "my.view_strobe_props"
    bl_label = "View Strobe Properties"
    
    space_type: StringProperty() # type: ignore
    node_name: StringProperty() # type: ignore
    node_tree_name: StringProperty() # type: ignore
    
    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        finders = Find
        active_controller = finders.find_controller_by_space_type(context, self.space_type, self.node_name, self.node_tree_name)
        CommonUI.draw_strobe_settings(self, context, active_controller)


class COMMON_OT_pan_tilt_props(Operator):
    bl_idname = "my.view_pan_tilt_props"
    bl_label = "Pan/Tilt Properties"
    bl_description = "Access pan and tilt min and max settings"

    space_type: StringProperty() # type: ignore
    node_name: StringProperty() # type: ignore
    node_tree_name: StringProperty() # type: ignore
    
    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        finders = Find
        active_controller = finders.find_controller_by_space_type(context, self.space_type, self.node_name, self.node_tree_name)
        CommonUI.draw_pan_tilt_settings(self, context, active_controller)
       
    
class COMMON_OT_zoom_iris_props(Operator):
    bl_idname = "my.view_zoom_iris_props"
    bl_label = "Zoom Properties"
    bl_description = "Access zoom min and max settings"

    space_type: StringProperty() # type: ignore
    node_name: StringProperty() # type: ignore
    node_tree_name: StringProperty() # type: ignore # type: ignore
    
    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        finders = Find
        active_controller = finders.find_controller_by_space_type(context, self.space_type, self.node_name, self.node_tree_name)
        CommonUI.draw_zoom_settings(self, context, active_controller)
        

class COMMON_OT_edge_diffusion_props(Operator):
    bl_idname = "my.view_edge_diffusion_props"
    bl_label = "Edge/Diffusion Properties"
    
    space_type: StringProperty() # type: ignore # type: ignore
    node_name: StringProperty() # type: ignore # type: ignore
    node_tree_name: StringProperty()  # type: ignore
    
    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        finders = Find
        active_controller = finders.find_controller_by_space_type(context, self.space_type, self.node_name, self.node_tree_name)
        CommonUI.draw_edge_diffusion_settings(self, context, active_controller)
    
       
class COMMON_OT_gobo_props(Operator):
    bl_idname = "my.view_gobo_props"
    bl_label = "View Gobo Properties"
    bl_description = "Access gobo-related settings"

    space_type: StringProperty() # type: ignore
    node_name: StringProperty() # type: ignore
    node_tree_name: StringProperty() # type: ignore
    
    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        finders = Find
        active_controller = finders.find_controller_by_space_type(context, self.space_type, self.node_name, self.node_tree_name)
        CommonUI.draw_gobo_settings(self, context, active_controller)
        

#-------------------------------------------------------------------------------------------------------------------------------------------
'''SPLASH Operators'''
#-------------------------------------------------------------------------------------------------------------------------------------------   
class TOPBAR_OT_splash_screen(Operator):
    bl_idname = "wm.sorcerer_splash"
    bl_label = "Alva Sorcerer Splash"
    
    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        width = 375
        return context.window_manager.invoke_props_dialog(self, width=width)

    def draw(self, context):
        CommonUI.draw_splash(self, context)
        
        
#-------------------------------------------------------------------------------------------------------------------------------------------
'''TOOLBAR Operators'''
#-------------------------------------------------------------------------------------------------------------------------------------------      
class TOOL_OT_ghost_out(Operator):
    bl_idname = "my.go_to_cue_out_operator"
    bl_label = "Ghost out"
    bl_description = "Presses Go_to Cue Out on the console"
    
    def execute(self, context):
        ghost_out_time = context.scene.scene_props.ghost_out_time
        osc.send_osc_lighting("/eos/newcmd", f"Go_to_Cue Out Time {str(ghost_out_time)} Enter")
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
    bl_idname = "my.displays_operator"
    bl_label = "Displays"
    bl_description = "Presses Displays on the console"
    
    def execute(self, context):
        ip_address = context.scene.scene_props.str_osc_ip_address
        port = context.scene.scene_props.int_osc_port
        osc.send_osc_lighting("/eos/key/displays", "1")
        osc.send_osc_lighting("/eos/key/displays", "0")
        return {'FINISHED'}
    
class TOOL_OT_about(Operator):
    bl_idname = "my.about_operator"
    bl_label = "About"
    bl_description = "Presses About on the console"
    
    def execute(self, context):
        osc.send_osc_lighting("/eos/key/about", "0")
        return {'FINISHED'}

class TOOL_OT_stop_clocks(Operator):
    bl_idname = "my.disable_all_clocks_operator"
    bl_label = "Disable All Clocks"
    bl_description = "Disables all timecode clocks in ETC Eos"
    
    def execute(self, context):
        ip_address = context.scene.scene_props.str_osc_ip_address
        port = context.scene.scene_props.int_osc_port
        clock_number = 1
        
        while clock_number <= 100:
            osc.send_osc_lighting("/eos/newcmd", f"Event {str(clock_number)} / Internal Disable Enter")
            clock_number += 1
            
        return {'FINISHED'}
     
class TOOL_OT_copy_various_to_selected(Operator):
    bl_idname = "my.copy_above_to_selected"
    bl_label = "Copy to Selected"
    bl_description = "Copy some properties of the active strip to all the other selected strips"

    def execute(self, context):
        active_strip = context.scene.sequence_editor.active_strip
        
        # Avoid infinite recursion on color updater.
        if active_strip and active_strip.type == 'COLOR':
            global stop_updating_color
            stop_updating_color = "Yes"
        
        Utils.duplicate_active_strip_to_selected(context)
                        
        stop_updating_color = "No"
                    
        return {'FINISHED'}


class TOOL_OT_alva_settings(Operator):
    '''Pop-up for Sorcerer Settings menu'''
    bl_idname = "seq.show_sequencer_settings"
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
        SettingsUI.draw_settings(self, context)


class TEXT_OT_populate_macros(Operator):
    '''Pop-up for Sorcerer Settings menu'''
    bl_idname = "text.alva_populate_macros"
    bl_label = "Populate Macro Buttons"

    filter_group: StringProperty()  # type: ignore

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
    bl_idname = "wm.show_message"
    bl_label = "Alva Sorcerer"
    
    message: StringProperty(name="Message", default="") # type: ignore

    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.label(text=self.message)
        
        
operator_classes = [
    HomeControllerButton,
    UpdateControllerButton,
    COMMON_OT_strobe_props,
    COMMON_OT_pan_tilt_props,
    COMMON_OT_zoom_iris_props,
    COMMON_OT_edge_diffusion_props,
    COMMON_OT_gobo_props,
    TOPBAR_OT_splash_screen,
    TOOL_OT_ghost_out,
    TOOL_OT_displays,
    TOOL_OT_about,
    TOOL_OT_stop_clocks,
    TOOL_OT_copy_various_to_selected,
    TOOL_OT_alva_settings,
    WM_OT_show_message,
    TEXT_OT_populate_macros
]


def register():
    for cls in operator_classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(operator_classes):
        bpy.utils.unregister_class(cls)