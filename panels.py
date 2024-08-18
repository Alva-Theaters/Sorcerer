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
from bpy.types import Panel, Scene
from bpy.types import (
    TOPBAR_HT_upper_bar, 
    VIEW3D_HT_header, 
    VIEW3D_HT_tool_header, 
    SEQUENCER_HT_header, 
    SEQUENCER_MT_add,
    DOPESHEET_HT_header,
    NODE_MT_add,
    NODE_HT_header,
    GRAPH_HT_header,
    TEXT_HT_header
    )

from .ui.node_ui import NodeUI
from .ui.sequencer_ui import SequencerUI
from .ui.view3d_ui import View3DUI
from .ui.common_ui import CommonUI
from .ui.properties_ui import PropertiesUI
from .ui.text_ui import TextUI


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
        NodeUI.draw_node_formatter(self, context)


class NODE_PT_alva_fixture_generator(Panel, NodePanel):
    """Automation tools for rapidly creating lighting fixtures"""
    bl_label = "Generate Fixtures"

    def draw(self, context):
        CommonUI.draw_generate_fixtures(self, context)
        
        
class NODE_PT_alva_fixture_groups(Panel, NodePanel):
    '''Change the fixture groups found in the controller drop downs.'''
    bl_label = "Fixture Groups"

    def draw(self, context):
        CommonUI.draw_fixture_groups(self, context)
             
    
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
    bl_label = "Object Controller"

    @classmethod
    def poll(cls, context):
        return (hasattr(context, "scene") and
                hasattr(context, "active_object") and
                context.active_object is not None)

    def draw(self, context):
        scene = bpy.context.scene.scene_props
        active_object = context.active_object

        #if active
        
        if active_object.type == 'MESH':
            box, column = View3DUI.draw_object_header(self, context, scene, active_object)
            CommonUI.draw_parameters(self, context, column, box, active_object)
            CommonUI.draw_footer_toggles(self, context, column, active_object)
        
        if active_object.type == 'SPEAKER':
            View3DUI.draw_speaker(self, context, active_object)
        
        
class VIEW3D_PT_alva_lighting_modifiers(Panel, View3D_Panel):
    '''Modifiers for changing all lights as one'''
    bl_label = "Lighting Modifiers (Global)"

    def draw(self, context):
        View3DUI.draw_lighting_modifiers(self, context)
        
        
class VIEW3D_PT_alva_fixture_groups(Panel, View3D_Panel):
    '''Access to scene-level Sorcerer patch for lighting'''
    bl_label = "Fixture Groups"

    def draw(self, context):
        CommonUI.draw_fixture_groups(self, context)
            
            
class VIEW3D_PT_alva_fixture_generator(Panel, View3D_Panel):
    """Automation tools for rapidly creating lighting fixtures"""
    bl_label = "Generate Fixtures"

    def draw(self, context):
        CommonUI.draw_generate_fixtures(self, context)
            
            
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
        SequencerUI.draw_strip_media(self, context, context.scene)
        
        
class SEQUENCER_PT_alva_Video(Panel, SequencerPanel):
    '''Currently does nothing, but will soon be for PTZ camera animation.'''
    bl_label = "Video"

    def draw(self, context):
        SequencerUI.draw_strip_video(self, context)
        

class SEQUENCER_PT_alva_Audio(Panel, SequencerPanel):
    '''This is for the 3D audio system on the Sequencer side.'''
    bl_label = "Audio"

    def draw(self, context):
        scene = context.scene
        column = self.layout.column(align=True)
        active_strip = scene.sequence_editor.active_strip
        sequence_editor = scene.sequence_editor

        if active_strip.type == 'SOUND':
            if active_strip.audio_type_enum == "option_object":
                SequencerUI.draw_strip_sound_object(self, context, column, active_strip)
                CommonUI.draw_volume_monitor(self, context, sequence_editor)
            elif active_strip.audio_type_enum == "option_speaker":
                SequencerUI.draw_strip_seaker(self, context, column, active_strip)
                CommonUI.draw_volume_monitor(self, context)


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

    def draw(self, context):
        PropertiesUI.draw_cue_switcher(self, context)


class SCENE_PT_alva_show_sequencer(Panel, PropertiesPanel):
    '''Stage manager tool for sequencing show operations, similar
       to Go-No-Go software used in rocket launches.'''
    bl_label = "ALVA Show-Start Sequencer"

    def draw(self, context):
        PropertiesUI.draw_show_sequencer(self, context)
        
        
#-------------------------------------------------------------------------------------------------------------------------------------------
'''TEXT Panels'''
#-------------------------------------------------------------------------------------------------------------------------------------------
class TextPanel:
    bl_space_type = 'TEXT_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Alva Sorcerer'
    
    @classmethod
    def poll(cls, context):
        return context.space_data.text is not None
    

class TEXT_PT_alva_macro_generator(Panel, TextPanel):
    '''Multi-line macro creator for ETC Eos'''
    bl_label = "Macro Generator"
    
    def draw(self, context):
        TextUI.draw_macro_generator(self, context)
        
        
class TEXT_PT_alva_import_patch(Panel, TextPanel):
    '''Use USITT ASCII to import a patch into Sorcerer'''
    bl_label = "Import USITT ASCII"
    
    def draw(self, context):
        TextUI.draw_import_usitt_ascii(self, context)


#-------------------------------------------------------------------------------------------------------------------------------------------
'''COMMON Toolbars'''
#-------------------------------------------------------------------------------------------------------------------------------------------
class ToolbarPanel:
    bl_label = "Tools"  # not visible
    bl_region_type = 'TOOLS'
    bl_options = {'HIDE_HEADER'}


class VIEW3D_PT_alva_toolbar(Panel, ToolbarPanel):
    bl_space_type = 'VIEW_3D'

    def draw(self, context):
        CommonUI.draw_toolbar(self, context)
        
        
class SEQUENCER_PT_alva_toolbar(Panel, ToolbarPanel):
    '''Toolbar extension for Sorcerer tools.'''
    bl_space_type = 'SEQUENCE_EDITOR'
    
    def draw(self, context):
        CommonUI.draw_toolbar(self, context)
        
        
class NODE_PT_alva_toolbar(Panel, ToolbarPanel):
    '''Toolbar extension for Sorcerer tools.'''
    bl_space_type = 'NODE_EDITOR'
            
    def draw(self, context):
        CommonUI.draw_toolbar(self, context)
        
        
panels = [
    NODE_PT_alva_node_formatter,
    NODE_PT_alva_fixture_generator,
    NODE_PT_alva_fixture_groups,
    VIEW3D_PT_alva_object_controller,
    VIEW3D_PT_alva_lighting_modifiers,
    VIEW3D_PT_alva_fixture_groups,
    VIEW3D_PT_alva_fixture_generator,
    SCENE_PT_alva_cue_switcher,
    SCENE_PT_alva_show_sequencer,
    TEXT_PT_alva_macro_generator,
    TEXT_PT_alva_import_patch,
    VIEW3D_PT_alva_toolbar,
    SEQUENCER_PT_alva_toolbar,
    NODE_PT_alva_toolbar,
    SEQUENCER_PT_alva_Lighting,
    SEQUENCER_PT_alva_Video,
    SEQUENCER_PT_alva_Audio,
]


def register():
    from bpy.utils import register_class
    for cls in panels:
        register_class(cls)
    
    TOPBAR_HT_upper_bar.append(CommonUI.draw_topbar)

    VIEW3D_HT_header.append(View3DUI.draw_view3d_cmd_line)
    VIEW3D_HT_tool_header.prepend(CommonUI.draw_tool_settings)

    SEQUENCER_MT_add.append(SequencerUI.draw_sequencer_add_menu)
    SEQUENCER_HT_header.append(SequencerUI.draw_sequencer_cmd_line)

    DOPESHEET_HT_header.append(SequencerUI.draw_timeline_sync) # This goes on space_time too

    NODE_MT_add.append(NodeUI.draw_alva_node_menu)
    NODE_HT_header.append(NodeUI.draw_node_header)

    GRAPH_HT_header.append(CommonUI.draw_graph_header)

    TEXT_HT_header.append(CommonUI.draw_tool_settings)


def unregister():
    from bpy.utils import unregister_class
    for cls in panels:
        unregister_class(cls)
    
    TOPBAR_HT_upper_bar.remove(CommonUI.draw_topbar)

    VIEW3D_HT_header.remove(View3DUI.draw_view3d_cmd_line)
    VIEW3D_HT_tool_header.remove(CommonUI.draw_tool_settings)

    SEQUENCER_MT_add.remove(SequencerUI.draw_sequencer_add_menu)
    SEQUENCER_HT_header.remove(SequencerUI.draw_sequencer_cmd_line)

    DOPESHEET_HT_header.remove(SequencerUI.draw_timeline_sync)

    NODE_MT_add.remove(NodeUI.draw_alva_node_menu)
    NODE_HT_header.remove(NodeUI.draw_node_header)

    GRAPH_HT_header.remove(CommonUI.draw_graph_header)

    TEXT_HT_header.remove(CommonUI.draw_tool_settings)