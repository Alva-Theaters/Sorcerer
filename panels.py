# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

'''
This file is only for defining the stuff we put into the UI and when, and only very rarely do we
put runtime UI logic here. We want this file to just be for quickly seeing what is going where.

DO: Add polls, panels, header appends, menu appends, and very-high-level UI logic
DO NOT: Add line after line after line of UI logic. Put that in the as_ui folder.
'''

import bpy
from bpy.types import Panel, Menu
from bpy.types import (
    TOPBAR_MT_editor_menus,
    TOPBAR_MT_edit,
    TOPBAR_MT_render,
    TOPBAR_MT_window,
    TOPBAR_MT_help,

    VIEW3D_HT_header, 
    VIEW3D_HT_tool_header, 
    VIEW3D_MT_view,

    PROPERTIES_HT_header,
    PROPERTIES_PT_navigation_bar, 
    RENDER_PT_context,

    DOPESHEET_HT_header,
    TIME_PT_playback,
    TIME_MT_view,

    SEQUENCER_MT_view,
    SEQUENCER_MT_add,
    SEQUENCER_MT_strip,
    SEQUENCER_HT_header, 

    NODE_MT_add,
    NODE_HT_header,
    NODE_MT_view,

    GRAPH_HT_header,

    TEXT_HT_header,
    TEXT_MT_view, 

    VIEW3D_MT_object_context_menu,
    SEQUENCER_MT_context_menu
    )

from .as_ui.space_topbar import (
    draw_alva_topbar, 
    draw_alva_edit, 
    draw_alva_render, 
    draw_alva_window, 
    draw_alva_help
)
from .as_ui.space_view3d import (
    draw_tool_settings,
    draw_speaker, 
    draw_object_header, 
    draw_lighting_modifiers,
    draw_alva_view_3d_view,
    draw_view3d_cmd_line,
    draw_tool_settings,
    draw_service_mode
)
from .as_ui.properties_scene import (
    draw_alva_stage_manager, 
    draw_alva_cue_switcher, 
    draw_alva_properties_navigation,
    draw_alva_properties_sync
)
from .as_ui.space_time import (
    draw_alva_time_header, 
    draw_alva_time_view, 
    draw_alva_time_playback,
    draw_alva_time_flags
)
from .as_ui.space_sequencer import (
    draw_strip_sound_object,
    draw_strip_video,
    draw_strip_media, 
    draw_alva_sequencer_add_menu, 
    draw_alva_sequencer_cmd_line,
    draw_alva_sequencer_view,
    draw_alva_sequencer_strip
)
from .as_ui.space_node import (
    draw_node_formatter, 
    draw_alva_node_menu, 
    draw_node_header, 
    draw_alva_node_view
)
from .as_ui.space_graph import draw_graph_header
from .as_ui.space_text import draw_import_usitt_ascii, draw_macro_generator
from .as_ui.space_text import draw_text_view

from .as_ui.space_tool import draw_alva_toolbar
from .as_ui.space_common import (
    draw_generate_fixtures, 
    draw_fixture_groups, 
    draw_parameters, 
    draw_footer_toggles, 
    draw_volume_monitor
)
from .as_ui.space_wm import draw_alva_right_click
             
    
#-------------------------------------------------------------------------------------------------------------------------------------------
'''VIEW3D Panels'''
#-------------------------------------------------------------------------------------------------------------------------------------------                             
class View3D_Panel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Alva Sorcerer'

    @classmethod
    def poll(cls, context):
        return hasattr(context, "scene")
    

class VIEW3D_PT_alva_object_controller(Panel, View3D_Panel):
    '''Main controller for object parameters in 3D view'''
    bl_label = "Control Specific Lights"

    @classmethod
    def poll(cls, context):
        return (hasattr(context, "scene") and
                hasattr(context, "active_object") and
                context.active_object is not None)

    def draw(self, context):
        scene = bpy.context.scene.scene_props
        active_object = context.active_object
        
        if active_object.type == 'MESH':
            box, column = draw_object_header(self, context, scene, active_object)
            draw_parameters(self, context, column, box, active_object)
            draw_footer_toggles(self, context, column, active_object)
        
        if active_object.type == 'SPEAKER':
            draw_speaker(self, context, active_object)
        
        
class VIEW3D_PT_alva_lighting_modifiers(Panel, View3D_Panel):
    '''Modifiers for changing all lights as one'''
    bl_label = "Modify All Lights at Once"

    @classmethod
    def poll(cls, context):
        return False # Currently disabled until it actually works

    def draw(self, context):
        draw_lighting_modifiers(self, context)
        
        
class VIEW3D_PT_alva_fixture_groups(Panel, View3D_Panel):
    '''Access to scene-level Sorcerer patch for lighting'''
    bl_label = "Make Groups"

    def draw(self, context):
        draw_fixture_groups(self, context)
            
            
class VIEW3D_PT_alva_fixture_generator(Panel, View3D_Panel):
    """Automation tools for rapidly creating lighting fixtures"""
    bl_label = "Patch Console Remotely"

    @classmethod
    def poll(cls, context):
        return (hasattr(context, "scene") and
                hasattr(context, "active_object") and
                context.active_object is not None and
                context.scene.scene_props.console_type_enum == 'option_eos')

    def draw(self, context):
        draw_generate_fixtures(self, context)


class VIEW3D_PT_alva_service_mode(Panel):
    """Access debug print settings"""
    bl_label = "Service Mode"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Alva Sorcerer'

    @classmethod
    def poll(cls, context):
        return context.scene.scene_props.service_mode

    def draw(self, context):
        draw_service_mode(self, context)


#-------------------------------------------------------------------------------------------------------------------------------------------
'''PROPERTIES Panels'''
#-------------------------------------------------------------------------------------------------------------------------------------------                  
class PropertiesPanel:
    bl_space_type = "PROPERTIES"
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    bl_category = 'Alva Sorcerer'
    

class SCENE_PT_alva_cue_switcher(Panel, PropertiesPanel):
    '''Live video switcher type system but for lighting cues'''
    bl_label = "ALVA M/E 1 Lighting Cue Switcher"

    @classmethod
    def poll(cls, context):
        return context.scene.scene_props.console_type_enum == 'option_eos'

    def draw(self, context):
        draw_alva_cue_switcher(self, context)


class SCENE_PT_alva_stage_manager(Panel, PropertiesPanel):
    '''Stage manager tool for sequencing show operations, similar
       to Go-No-Go software used in rocket launches.'''
    bl_label = "ALVA Stage Manager"

    def draw(self, context):
        draw_alva_stage_manager(self, context)


#-------------------------------------------------------------------------------------------------------------------------------------------
'''TIME Panel'''
#-------------------------------------------------------------------------------------------------------------------------------------------
class TIME_PT_alva_flags(Panel):
    bl_idname = "TIME_PT_alva_flags"
    bl_label = "Render"
    bl_space_type = 'DOPESHEET_EDITOR'
    bl_region_type = 'HEADER'
    bl_ui_units_x = 10

    @classmethod
    def poll(cls, context):
        return context.scene.scene_props.console_type_enum == 'option_eos'

    def draw(self, context):
        draw_alva_time_flags(self, context)
            
            
#-------------------------------------------------------------------------------------------------------------------------------------------
'''SEQUENCER Panels'''
#-------------------------------------------------------------------------------------------------------------------------------------------
class SequencerPanel:
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Alva Sorcerer'
    
    @classmethod
    def poll(cls, context):
        return (hasattr(context, "scene") and
                context.scene.scene_props.console_type_enum == 'option_eos' and
                context.scene and
                hasattr(context.scene, "sequence_editor") and
                context.scene.sequence_editor and 
                hasattr(context.scene.sequence_editor, "active_strip") and
                context.scene.sequence_editor.active_strip) 


class SEQUENCER_PT_alva_Lighting(Panel, SequencerPanel):
    '''This is the primary side panel for everything lighting in Sequencer.'''
    bl_label = "Lighting"
    
    @classmethod
    def poll(cls, context):
        return context.scene

    def draw(self, context):
        draw_strip_media(self, context, context.scene)
        
        
class SEQUENCER_PT_alva_Video(Panel, SequencerPanel):
    '''Currently does nothing, but will soon be for PTZ camera animation.'''
    bl_label = "Video"

    @classmethod
    def poll(cls, context):
        return False # Temporarily disabled until it's built

    def draw(self, context):
        draw_strip_video(self, context)
        

class SEQUENCER_PT_alva_Audio(Panel, SequencerPanel):
    '''This is for the 3D audio system on the Sequencer side.'''
    bl_label = "Audio"

    def draw(self, context):
        scene = context.scene
        column = self.layout.column(align=True)
        active_strip = scene.sequence_editor.active_strip
        sequence_editor = scene.sequence_editor

        if active_strip.type == 'SOUND':
            draw_strip_sound_object(self, context, column, active_strip)
            draw_volume_monitor(self, context, sequence_editor)


#-------------------------------------------------------------------------------------------------------------------------------------------
'''NODE Panels'''
#-------------------------------------------------------------------------------------------------------------------------------------------
class NodePanel:
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Alva Sorcerer'
    
    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'ShaderNodeTree' and 
                context.space_data.id == context.scene.world)


class NODE_PT_alva_node_formatter(Panel, NodePanel):
    '''Control color, label, etc. of our nodes in pop-up menu'''
    bl_label = "Node Formatter"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'ShaderNodeTree' and
                context.space_data.id == context.scene.world and
                hasattr(context.space_data.edit_tree, 'nodes') and
                context.space_data.edit_tree.nodes.active)

    def draw(self, context):
        draw_node_formatter(self, context)


class NODE_PT_alva_fixture_generator(Panel, NodePanel):
    """Automation tools for rapidly creating lighting fixtures"""
    bl_label = "Patch Console Remotely"

    @classmethod
    def poll(cls, context):
        return (context.space_data.tree_type == 'ShaderNodeTree' and 
                context.space_data.id == context.scene.world and
                context.scene.scene_props.console_type_enum == 'option_eos')

    def draw(self, context):
        draw_generate_fixtures(self, context)
        
        
class NODE_PT_alva_fixture_groups(Panel, NodePanel):
    '''Change the fixture groups found in the controller drop downs.'''
    bl_label = "Make Groups"

    def draw(self, context):
        draw_fixture_groups(self, context)


#-------------------------------------------------------------------------------------------------------------------------------------------
'''TEXT Panels'''
#-------------------------------------------------------------------------------------------------------------------------------------------
class TextPanel:
    bl_space_type = 'TEXT_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Alva Sorcerer'
    
    @classmethod
    def poll(cls, context):
        return context.space_data.text is not None and context.scene.scene_props.console_type_enum == 'option_eos'
    

class TEXT_PT_alva_macro_generator(Panel, TextPanel):
    '''Multi-line macro creator for ETC Eos'''
    bl_label = "Macro Generator"
    
    def draw(self, context):
        draw_macro_generator(self, context)
        
        
class TEXT_PT_alva_import_patch(Panel, TextPanel):
    '''Use USITT ASCII to import a patch into Sorcerer'''
    bl_label = "Import USITT ASCII"
    
    def draw(self, context):
        draw_import_usitt_ascii(self, context)


#-------------------------------------------------------------------------------------------------------------------------------------------
'''COMMON Toolbars'''
#-------------------------------------------------------------------------------------------------------------------------------------------
class ToolbarPanel:
    bl_label = "Tools"  # not visible
    bl_region_type = 'TOOLS'
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        return context.scene.scene_props.console_type_enum == 'option_eos'


class VIEW3D_PT_alva_toolbar(Panel, ToolbarPanel):
    bl_space_type = 'VIEW_3D'

    def draw(self, context):
        draw_alva_toolbar(self, context)
        
        
class SEQUENCER_PT_alva_toolbar(Panel, ToolbarPanel):
    '''Toolbar extension for Sorcerer tools.'''
    bl_space_type = 'SEQUENCE_EDITOR'
    
    def draw(self, context):
        draw_alva_toolbar(self, context)
        
        
class NODE_PT_alva_toolbar(Panel, ToolbarPanel):
    '''Toolbar extension for Sorcerer tools.'''
    bl_space_type = 'NODE_EDITOR'
            
    def draw(self, context):
        draw_alva_toolbar(self, context)


#-------------------------------------------------------------------------------------------------------------------------------------------
'''RIGHT CLICK'''
#-------------------------------------------------------------------------------------------------------------------------------------------
class WM_MT_button_context(Menu):
    bl_label = ""

    def draw(self, context):
        pass
        
        
panels = [
    VIEW3D_PT_alva_object_controller,
    VIEW3D_PT_alva_lighting_modifiers,
    VIEW3D_PT_alva_fixture_groups,
    VIEW3D_PT_alva_fixture_generator,
    VIEW3D_PT_alva_service_mode,

    SCENE_PT_alva_cue_switcher,
    SCENE_PT_alva_stage_manager,

    TIME_PT_alva_flags,

    SEQUENCER_PT_alva_Lighting,
    SEQUENCER_PT_alva_Video,
    SEQUENCER_PT_alva_Audio,

    NODE_PT_alva_node_formatter,
    NODE_PT_alva_fixture_generator,
    NODE_PT_alva_fixture_groups,

    TEXT_PT_alva_macro_generator,
    TEXT_PT_alva_import_patch,

    VIEW3D_PT_alva_toolbar,
    SEQUENCER_PT_alva_toolbar,
    NODE_PT_alva_toolbar,

    WM_MT_button_context
]


def register():
    from bpy.utils import register_class
    for cls in panels:
        register_class(cls)
    
    TOPBAR_MT_editor_menus.prepend(draw_alva_topbar)
    TOPBAR_MT_edit.append(draw_alva_edit)
    TOPBAR_MT_render.prepend(draw_alva_render)
    TOPBAR_MT_window.append(draw_alva_window)
    TOPBAR_MT_help.append(draw_alva_help)

    VIEW3D_MT_view.append(draw_alva_view_3d_view)
    VIEW3D_HT_header.append(draw_view3d_cmd_line)
    VIEW3D_HT_tool_header.prepend(draw_tool_settings)

    PROPERTIES_HT_header.append(draw_tool_settings)
    PROPERTIES_PT_navigation_bar.prepend(draw_alva_properties_navigation)
    RENDER_PT_context.prepend(draw_alva_properties_sync)

    DOPESHEET_HT_header.append(draw_alva_time_header) # This goes on space_time too
    TIME_PT_playback.prepend(draw_alva_time_playback)
    TIME_MT_view.append(draw_alva_time_view)

    SEQUENCER_MT_view.append(draw_alva_sequencer_view)
    SEQUENCER_MT_add.append(draw_alva_sequencer_add_menu)
    SEQUENCER_MT_strip.append(draw_alva_sequencer_strip)
    SEQUENCER_HT_header.append(draw_alva_sequencer_cmd_line)

    NODE_MT_add.append(draw_alva_node_menu)
    NODE_HT_header.append(draw_node_header)
    NODE_MT_view.append(draw_alva_node_view)

    GRAPH_HT_header.append(draw_graph_header)

    TEXT_HT_header.append(draw_tool_settings)
    TEXT_MT_view.append(draw_text_view)

    WM_MT_button_context.append(draw_alva_right_click)
    VIEW3D_MT_object_context_menu.append(draw_alva_right_click)
    SEQUENCER_MT_context_menu.append(draw_alva_right_click)


def unregister():
    from bpy.utils import unregister_class
    for cls in panels:
        unregister_class(cls)
    
    TOPBAR_MT_editor_menus.remove(draw_alva_topbar)
    TOPBAR_MT_edit.remove(draw_alva_edit)
    TOPBAR_MT_render.remove(draw_alva_render)
    TOPBAR_MT_window.remove(draw_alva_window)
    TOPBAR_MT_help.remove(draw_alva_help)

    VIEW3D_MT_view.remove(draw_alva_view_3d_view)
    VIEW3D_HT_header.remove(draw_view3d_cmd_line)
    VIEW3D_HT_tool_header.remove(draw_tool_settings)

    PROPERTIES_HT_header.remove(draw_tool_settings)
    PROPERTIES_PT_navigation_bar.remove(draw_alva_properties_navigation)
    RENDER_PT_context.remove(draw_alva_properties_sync)

    DOPESHEET_HT_header.remove(draw_alva_time_header) # This goes on space_time too
    TIME_PT_playback.remove(draw_alva_time_playback)
    TIME_MT_view.remove(draw_alva_time_view)

    SEQUENCER_MT_view.remove(draw_alva_sequencer_view)
    SEQUENCER_MT_add.remove(draw_alva_sequencer_add_menu)
    SEQUENCER_MT_strip.remove(draw_alva_sequencer_strip)
    SEQUENCER_HT_header.remove(draw_alva_sequencer_cmd_line)

    NODE_MT_add.remove(draw_alva_node_menu)
    NODE_HT_header.remove(draw_node_header)
    NODE_MT_view.remove(draw_alva_node_view)

    GRAPH_HT_header.remove(draw_graph_header)

    TEXT_HT_header.remove(draw_tool_settings)
    TEXT_MT_view.remove(draw_text_view)

    WM_MT_button_context.remove(draw_alva_right_click)
    VIEW3D_MT_object_context_menu.remove(draw_alva_right_click)
    SEQUENCER_MT_context_menu.remove(draw_alva_right_click)