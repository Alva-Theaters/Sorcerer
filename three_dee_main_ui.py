# This file is part of Alva Sorcerer.
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


import bpy
from bpy.types import Operator, Menu
import os
import bpy.utils.previews


preview_collections = {}


def draw_is_influencer(self, context):
    scene = context.scene
    layout = self.layout
    active_object = context.active_object
    row = layout.row()
    
    if active_object is not None and active_object.select_get() and active_object.type == 'MESH':
        if active_object.is_influencer:
            row.alert = context.active_object.is_influencer
            row.prop(active_object, "is_influencer", toggle=True, text="This Mesh Can Influence Lights") 
        else:
            row.prop(active_object, "is_influencer", toggle=True, text="Make this Mesh Influence Lights") 


def gather_controller_nodes(node_tree, controllers):
    for node in node_tree.nodes:
        if node.bl_idname == 'group_controller_type':
            controllers.append(node)
        elif node.bl_idname == 'ShaderNodeGroup' and node.node_tree:
            gather_controller_nodes(node.node_tree, controllers)


class LightArrayPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Patch"
    bl_idname = "OBJECT_PT_light_array"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Alva Sorcerer'

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        active_object = context.active_object
        modifiers = []
        
        box = layout.box()
        row = box.row()
        row.label(text="Import patch from console (USITT ASCII):")
        row = box.row(align=True)
        row.prop_search(context.scene.scene_props, "selected_text_block_name", bpy.data, "texts", text="")
        row.operator("my.send_usitt_ascii_to_3d", text="", icon='SHADERFX')
        box.separator()

        if scene.scene_props.bool_eos_console_mode and not scene.scene_props.school_mode_enabled:
            box = layout.box()
            row = box.row()
            row.label(text="Create patch with Sorcerer:")
            row = box.row()
            row.prop(scene.scene_props, "array_cone_enum", text="", icon='MESH_CONE')
            row = box.row()
            row.prop(scene.scene_props, "array_modifier_enum", text="", icon='MOD_ARRAY')
            row = box.row()
            if scene.scene_props.array_curve_enum !="":
                row.prop(scene.scene_props, "array_curve_enum", text="", icon='CURVE_BEZCURVE')
                row = box.row()
                
            layout.separator()

            split = box.split(factor=.4)
            col = split.column()
            col.label(text="Group #:", icon='STICKY_UVS_LOC')
            col.label(text="Start Chan #:", icon='OUTLINER_OB_LIGHT')
            col.label(text="Group Label:", icon='INFO')
            col.separator()
            col.label(text="Maker:")
            col.label(text="Type:")
            col.label(text="Universe #:")
            col.label(text="Start Addr. #:")
            col.label(text="Channel Mode:")
            col = split.column()
            col.prop(scene.scene_props, "int_array_group_index", text="")
            col.prop(scene.scene_props, "int_array_start_channel", text="")
            col.prop(scene.scene_props, "str_array_group_name", text="")
            col.separator()
            col.prop(scene.scene_props, "str_array_group_maker", text="")
            col.prop(scene.scene_props, "str_array_group_type", text="")
            col.prop(scene.scene_props, "int_array_universe", text="")
            col.prop(scene.scene_props, "int_array_start_address", text="")
            col.prop(scene.scene_props, "int_array_channel_mode", text="")
            
            box.separator()
            
            split = box.split(factor=.5)
            col = split.column()
            col.prop(scene.scene_props, "strobe_is_on", text="Strobe", slider=True)
                      
            col = split.column()
            col.prop(scene.scene_props, "color_is_on", text="Color", slider=True)
            
            split = box.split(factor=1)
            col = split.column()            
            col.prop(scene.scene_props, "pan_tilt_is_on", text="Pan/Tilt", slider=True)
            
            split = box.split(factor=.5)
            col = split.column()
            col.prop(scene.scene_props, "zoom_is_on", text="Zoom", slider=True)
            
            col = split.column()
            col.prop(scene.scene_props, "iris_is_on", text="Iris", slider=True)
            
            split = box.split(factor=.5)
            col = split.column()
            col.prop(scene.scene_props, "edge_is_on", text="Edge", slider=True)
            
            col = split.column()
            col.prop(scene.scene_props, "diffusion_is_on", text="Diffusion", slider=True)
            
            split = box.split(factor=1)
            col = split.column()
            col.prop(scene.scene_props, "gobo_id_is_on", text="Gobo", slider=True)
            
            pcoll = preview_collections["main"]
            my_icon = pcoll["my_icon"]
            
            box.separator()
            box.operator("array.patch_group_operator", text="Patch Group", icon_value=my_icon.icon_id)

            box.separator()
            
# Slated for next release

#            box = layout.box()
#            row = box.row()
#            row.label(text="Realtime 3D Feedback for Augment3D", icon='VIEW_PAN')
#            
#            row = box.row(align=True)
#            row.scale_y = 1.3
#            row.scale_x = 2
#            row.operator("array.patch_group_operator", text="Spread")
#            row.operator("array.patch_group_operator", text="Bump")
#            row.operator("array.patch_group_operator", text="", icon='BACK')
#            
#            row.operator("array.patch_group_operator", text="", icon='SORT_DESC')
#            row.operator("array.patch_group_operator", text="", icon='SORT_ASC')
#            row.operator("array.patch_group_operator", text="", icon='FORWARD')
#            
#            box.separator()
                
                
class ChannelControllerPanel(bpy.types.Panel):
    bl_label = "Channel Controller"
    bl_idname = "ALVA_PT_channel_controller_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Alva Sorcerer'

    def draw(self, context):
        scene = bpy.context.scene.scene_props
        layout = self.layout
        column = layout.column(align=True)
        active_object = context.active_object
        
        row = column.row(align=True)
        if context.active_object:
            
            if active_object.type == 'MESH' and "is_influencer" in active_object and active_object["is_influencer"]:
                row = column.row()
                #row.prop(active_object, "int_intro", text="Intro:")
                if scene.is_democratic:
                    row.prop(active_object, "influence", text="Influence:", slider = True)
            
                #row.prop(active_object, "int_outro", text="Outro:")
                column.separator()
                row = column.row()
                row.label(text="Only intensity is supported for influencers at this time.")
                row = column.row(align=True)
                
            else:
                row = column.row()
                if scene.is_democratic:
                    row.prop(active_object, "influence", text="Influence", slider = True)
                    column.separator()
                    row = column.row()
                
            row.prop(active_object, "float_intensity", text="Intensity:", slider = True)
            #row.operator("my.keyframe_channel_intensity_operator", text="", icon='KEYTYPE_KEYFRAME_VEC')
            column.separator()
            row = column.row()
            row.prop(active_object, "float_gobo_speed", text="Gobo Rotator Speed:", slider = True)
            column.separator()
            row = column.row()
            row.prop(active_object, "color_profile_enum", text="")
            
            layout.separator()
            
            split = layout.split(factor=0.33333)
            row = split.column()

            row.label(text="Basic")
            row.prop(active_object, "float_diffusion", text="Diffusion:", slider = True)
            row.prop(active_object, "float_iris", text="Iris:", slider=True)
            row = split.column()
            row.template_color_picker(active_object, "float_vec_color")
            row = split.column()

            row.label(text="Shape")
            row.prop(active_object, "int_gobo_id", text="Gobo ID:", slider = False)
            row.prop(active_object, "float_zoom", text="Zoom:", slider = True)
            row.prop(active_object, "float_edge", text="Edge:", slider = True)
            
            split = layout.split(factor=1)
            row = split.column()
            row.label(text="Pan/Tilt")
            
            split = layout.split(factor=.5)
            row = split.column()
            row.prop(active_object, "float_pan", text="Pan", slider=True)
            row = split.column()
            row.prop(active_object, "float_tilt", text="Tilt", slider=True)
            
            layout.separator()        
            
        if not scene.school_mode_enabled:
            row = layout.row()
            row.prop(scene, "expand_prefixes_is_on", icon="TRIA_DOWN" if scene.expand_prefixes_is_on else "TRIA_RIGHT", icon_only=True, emboss=False)
            row.label(text="Scene Settings")      
            
            if scene.expand_prefixes_is_on:
                box = layout.box()
                box.separator()
                row = box.row()
                row.label(text="", icon='CON_ROTLIKE')
                row.prop(scene, "speed_min", text="Speed Min:")
                row.prop(scene, "speed_max", text="Max:")
                
                row = box.row()
                row.label(text="", icon='LINCURVE')
                row.prop(scene, "zoom_min", text="Zoom Min:")
                row.prop(scene, "zoom_max", text="Max:")
                
                row = box.row()
                row.label(text="", icon='ORIENTATION_GIMBAL')
                row.prop(scene, "pan_min", text="Pan Min:")
                row.prop(scene, "pan_max", text="Max:")
                
                row = box.row()
                row.label(text="", icon='ORIENTATION_GIMBAL')
                row.prop(scene, "tilt_min", text="Tilt Min:")
                row.prop(scene, "tilt_max", text="Max:")

                box.separator()
            
                row = box.row()
                row.label(text="Intensity Argument:", icon='OUTLINER_OB_LIGHT')
                row = box.row()
                row.prop(scene, "str_intensity_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Pan Argument:", icon='ORIENTATION_GIMBAL')
                row = box.row()
                row.prop(scene, "str_pan_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Tilt Argument:", icon='ORIENTATION_GIMBAL')
                row = box.row()
                row.prop(scene, "str_tilt_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Red Argument:", icon='COLORSET_01_VEC')
                row = box.row()
                row.prop(scene, "str_red_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Blue Argument:", icon='COLORSET_04_VEC')
                row = box.row()
                row.prop(scene, "str_blue_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Green Argument:", icon='COLORSET_03_VEC')
                row = box.row()
                row.prop(scene, "str_green_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Amber Argument:", icon='COLORSET_02_VEC')
                row = box.row()
                row.prop(scene, "str_amber_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="White Argument:", icon='COLORSET_13_VEC')
                row = box.row()
                row.prop(scene, "str_white_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Mint Argument:", icon='COLORSET_07_VEC')
                row = box.row()
                row.prop(scene, "str_mint_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Lime Argument:", icon='COLORSET_12_VEC')
                row = box.row()
                row.prop(scene, "str_lime_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Cyan Argument:", icon='SEQUENCE_COLOR_05')
                row = box.row()
                row.prop(scene, "str_cyan_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Magenta Argument:", icon='SEQUENCE_COLOR_06')
                row = box.row()
                row.prop(scene, "str_magenta_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Yellow Argument:", icon='SEQUENCE_COLOR_03')
                row = box.row()
                row.prop(scene, "str_yellow_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Zoom Argument:", icon='LINCURVE')
                row = box.row()
                row.prop(scene, "str_zoom_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Iris Argument:", icon='MESH_CIRCLE')
                row = box.row()
                row.prop(scene, "str_iris_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Edge Argument:", icon='SELECT_SET')
                row = box.row()
                row.prop(scene, "str_edge_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Diffusion Argument:", icon='MOD_CLOTH')
                row = box.row()
                row.prop(scene, "str_diffusion_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Gobo ID Argument:", icon='POINTCLOUD_DATA')
                row = box.row()
                row.prop(scene, "str_gobo_id_argument", text = "")
                
                box.separator()
                
                row = box.row()
                row.label(text="Speed Argument:", icon='CON_ROTLIKE')
                row = box.row()
                row.prop(scene, "str_speed_argument", text = "")


class ModalChannelControllerPanel(Operator):
    bl_idname = "my.show_properties"
    bl_label = "Channel Controller"
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=500)
    
    def draw(self, context):
        layout = self.layout
        column = layout.column(align=True)
        active_object = bpy.context.active_object
        
        row = layout.row()
        
        if active_object.type == 'MESH' and "is_influencer" in active_object and active_object["is_influencer"]:
            row = column.row()
            #row.prop(active_object, "int_intro", text="Intro:")
            row.prop(active_object, "influence", text="Influence:", slider = True)
            #row.prop(active_object, "int_outro", text="Outro:")
            column.separator()
            row = column.row()
            row.label(text="Only intensity is supported for influencers at this time.")
            
        row = column.row(align=True)
        row.prop(active_object, "float_intensity", text="Intensity:", slider = True)
        row.operator("my.keyframe_channel_intensity_operator", text="", icon='KEYTYPE_KEYFRAME_VEC')
        column.separator()
        row = column.row(align=True)
        row.prop(active_object, "float_gobo_speed", text="Gobo Rotator Speed:", slider = True)
        row.operator("my.keyframe_channel_speed_operator", text="", icon='KEYTYPE_KEYFRAME_VEC')
        
        layout.separator()
        layout.separator()
        
        # I hate that I have to comment this out, but I cannot get the darn thing to align properly
        
#        split = layout.split(factor=.05)
#        
#        row = split.column()
#        row.label(text="")
#        row.operator("my.keyframe_channel_diffusion_operator", text="", icon='KEYTYPE_KEYFRAME_VEC')
#        row.operator("my.keyframe_channel_iris_operator", text="", icon='KEYTYPE_KEYFRAME_VEC')
#        #col.operator("my.keyframe_channel_color_operator", text="", icon='KEYTYPE_KEYFRAME_VEC')
#        
#        row = split.column()
#        row.label(text="Basic")
#        row.prop(active_object, "float_diffusion", text="Diffusion:", slider = True)
#        row.prop(active_object, "float_iris", text="Iris:")
#        
#        
#        row = split.column()
#        row.template_color_picker(active_object, "float_vec_color")
#        
#        
#        row = split.column()
#        new_split = row.split(factor=.85)
#        new_row = new_split.column()
#        new_row.label(text="Shape")
#        new_row.prop(active_object, "int_gobo_id", text="Gobo ID:", slider = True)
#        new_row.prop(active_object, "float_zoom", text="Zoom:", slider = True)
#        new_row.prop(active_object, "float_edge", text="Edge:", slider = True)
#        
#        
#        row = new_split.column()
#        row.label(text="")
#        row.operator("my.keyframe_channel_gobo_operator", text="", icon='KEYTYPE_KEYFRAME_VEC')
#        row.operator("my.keyframe_channel_zoom_operator", text="", icon='KEYTYPE_KEYFRAME_VEC')
#        row.operator("my.keyframe_channel_edge_operator", text="", icon='KEYTYPE_KEYFRAME_VEC')
#        
#        
#        layout.separator()
        
        split = layout.split(factor=.3333)

        col = split.column()
        row = col.row(align=True)
        row.prop(active_object, "float_diffusion", text="Diffusion:", slider=True)
        row.operator("my.keyframe_channel_diffusion_operator", text="", icon='KEYTYPE_KEYFRAME_VEC')

        col = split.column()
        row = col.row(align=True)
        row.prop(active_object, "color_profile_enum", text="")
        
        col = split.column()
        row = col.row(align=True)
        row.prop(active_object, "int_gobo_id", text="Gobo:", slider=True)
        row.operator("my.keyframe_channel_gobo_operator", text="", icon='KEYTYPE_KEYFRAME_VEC')
        
        split = layout.split(factor=.3333)

        col = split.column()
        row = col.row(align=True)
        row.prop(active_object, "float_iris", text="Iris:", slider=True)
        row.operator("my.keyframe_channel_iris_operator", text="", icon='KEYTYPE_KEYFRAME_VEC')

        col = split.column()
        row = col.row(align=True)
        row.prop(active_object, "float_vec_color", text="")
        row.operator("my.keyframe_channel_color_operator", text="", icon='KEYTYPE_KEYFRAME_VEC')
        
        col = split.column()
        row = col.row(align=True)
        row.prop(active_object, "float_zoom", text="Zoom:", slider=True)
        row.operator("my.keyframe_channel_zoom_operator", text="", icon='KEYTYPE_KEYFRAME_VEC')
        
        split = layout.split(factor=.3333)

        col = split.column()
        row = col.row(align=True)
        row.label(text="")

        col = split.column()
        row = col.row(align=True)
        row.label(text="")
        
        col = split.column()
        row = col.row(align=True)
        row.prop(active_object, "float_edge", text="Edge:", slider=True)
        row.operator("my.keyframe_channel_edge_operator", text="", icon='KEYTYPE_KEYFRAME_VEC')

        layout.separator()
        layout.separator()

        split = layout.split(factor=.5)

        col = split.column()
        row = col.row(align=True)
        row.prop(active_object, "float_pan", text="Pan:", slider=True)
        row.operator("my.keyframe_channel_pan_operator", text="", icon='KEYTYPE_KEYFRAME_VEC')

        col = split.column()
        row = col.row(align=True)
        row.prop(active_object, "float_tilt", text="Tilt:", slider=True)
        row.operator("my.keyframe_channel_tilt_operator", text="", icon='KEYTYPE_KEYFRAME_VEC')
        
        layout.separator()
        layout.separator()
          
            
class GroupsPanel(bpy.types.Panel):
    bl_label = "Group/Channel Blocks"
    bl_idname = "ALVA_PT_groups_panel"
    bl_space_type = "PROPERTIES"
    bl_region_type = 'WINDOW'
    bl_context = "world"
    bl_category = 'Alva Sorcerer'

    def draw(self, context):
        layout = self.layout
        scene = context.scene.scene_props
        column = layout.column(align=True)
        
        row = column.row()  
        row.label(text="These do not need to match console groups. This tells Alva if controllers conflict with each other. Alva will usually send individualize commands to channels even when you use Group Controller nodes (for effects purposes). Packets will not exceed 50 commands each. It fails near 135 commands per packet.")    
        
        column.separator()
        
        row = column.row(align=True)
        row.label(text="Group to Add's Label:")
        
        row = column.row()
        row.prop(scene, "str_group_label_to_add", text="")
        row.label(text="")
        
        column.separator()
        
        row = column.row()
        row.label(text="Channels:")
        
        row = column.row()
        row.prop(scene, "str_group_channels_to_add", text="")
        row.label(text="")
        
        column.separator()
        column.separator()
        
        row = column.row(align=0)
        row.prop(scene, "int_group_number_to_add", text="Group #:")
        row.operator("group.add_group_to_scene", text="Add Group", icon='ADD')
        row.label(text="")
        row.label(text="")
        
        column.separator()
        column.separator()
        
        try:
            groups_data = eval(scene.group_data)
        except (SyntaxError, NameError):
            groups_data = {}
            
        counter = 0
        row = layout.row()

        for group_id, group_info in groups_data.items():
            if counter % 4 == 0 and counter != 0:
                # Only create a new row after every 4 boxes, but not at the first iteration
                row = layout.row()

            box = row.box()
            header_row = box.row()  # Create a row inside the box for the header
            header_row.label(text="{}: Group {}".format(group_info['label'], group_id))
            
            remove_group_op = header_row.operator("group.remove_group", text="", icon='X', emboss=False)
            remove_group_op.group_id = int(group_id)

            cols = box.column_flow(columns=4, align=True)
            for channel in group_info['channels']:
                col = cols.column(align=True)
                remove_op = col.operator(
                    "group.remove_channel_from_group", 
                    text=str(channel), 
                    icon='TRASH'
                )
                remove_op.group_id = str(group_id)
                remove_op.channel = channel

            add_channel_row = box.row(align=True)  # Use a different variable to avoid confusion
            add_channel_row.prop(scene, "add_channel_ids", text="")

            add_op = add_channel_row.operator("group.add_channel_to_group", text="", icon='PLUS')
            add_op.group_id = str(group_id)

            box.separator()
            counter += 1
                   
              
class ParameterComboPanel(bpy.types.Panel):
    bl_label = "Parameter Combo"
    bl_idname = "ALVA_PT_parameter_combo_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "world"
    bl_category = 'Alva Sorcerer'

    def draw(self, context):
        layout = self.layout
        column = layout.column(align=True)
        
        split = layout.split(factor=0.03)

        world = context.scene.world
        scene = context.scene.scene_props
        controllers = []

        if world is not None and world.node_tree:
            gather_controller_nodes(world.node_tree, controllers)

        row = split.column()
        row.label(text="Color")
        for controller in controllers:
            if controller.bl_idname == 'group_controller_type':
                if controller.color_is_on:
                    row.prop(controller, "float_vec_color", slider=True, text="")
                else: row.label(text="")        

        row = split.column()
        row.label(text="Intensities")
        for controller in controllers:
            if controller.bl_idname == 'group_controller_type':
                row.prop(controller, "float_intensity", slider=True, text=controller.str_group_label)       
                    
        row = split.column()
        row.label(text="Strobes")
        for controller in controllers:
            if controller.bl_idname == 'group_controller_type':
                if controller.strobe_is_on:
                    row.prop(controller, "float_strobe", slider=True, text=controller.str_group_label)
                else: row.label(text="")

        pan_tilt_col = split.column()
        pan_tilt_col.label(text="Pan/Tilt")
        for controller in controllers:
            if controller.bl_idname == 'group_controller_type':
                if controller.pan_tilt_is_on:
                    pan_tilt_split = pan_tilt_col.split(factor=0.5)
                    pan_col = pan_tilt_split.column()
                    pan_col.prop(controller, "float_pan", slider=True, text="P", icon_only=True)
                    tilt_col = pan_tilt_split.column()
                    tilt_col.prop(controller, "float_tilt", slider=True, text="T", icon_only=True)
                else:
                    pan_tilt_col.label(text="")      
           
        row = split.column()
        row.label(text="Zoom")
        for controller in controllers:
            if controller.bl_idname == 'group_controller_type':
                if controller.zoom_is_on:
                    row.prop(controller, "float_zoom", slider=True, text=controller.str_group_label) 
                else: row.label(text="")
            
        row = split.column()
        row.label(text="Iris")
        for controller in controllers:
            if controller.bl_idname == 'group_controller_type':
                if controller.edge_is_on:
                    row.prop(controller, "float_iris", slider=True, text=controller.str_group_label)   
                else: row.label(text="")        
               
        row = split.column()
        row.label(text="Edges")
        for controller in controllers:
            if controller.bl_idname == 'group_controller_type':
                if controller.edge_is_on:
                    row.prop(controller, "float_edge", slider=True, text=controller.str_group_label)
                else: row.label(text="")
              
        row = split.column()
        row.label(text="Diffusion")
        for controller in controllers:
            if controller.bl_idname == 'group_controller_type':
                if controller.diffusion_is_on:
                    row.prop(controller, "float_diffusion", slider=True, text=controller.str_group_label)
                else: row.label(text="")
            
        
        row = split.column()
        row.label(text="Gobo")
        for controller in controllers:
            if controller.bl_idname == 'group_controller_type':
                if controller.gobo_id_is_on:
                    row.prop(controller, "int_gobo_id", text=controller.str_group_label)
                else: row.label(text="")
                     
        row = split.column()
        row.label(text="Speed")
        for controller in controllers:
            if controller.bl_idname == 'group_controller_type':
                if controller.gobo_id_is_on:
                    row.prop(controller, "float_gobo_speed", text=controller.str_group_label)
                else: row.label(text="")
        
        row = split.column()
        row.label(text="Prism")
        for controller in controllers:
            if controller.bl_idname == 'group_controller_type':
                if controller.gobo_id_is_on:
                    row.prop(controller, "int_prism", slider=True, text=controller.str_group_label)
                else: row.label(text="")

 
class GroupSettingsPanel(bpy.types.Panel):
    bl_label = "Group Settings"
    bl_idname = "ALVA_PT_group_settings_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "world"
    bl_category = 'Alva Sorcerer'
        
    def draw(self, context):
        layout = self.layout
        column = layout.column(align=True)
        
        row = column.row()
        
        world = context.scene.world
        scene = context.scene.scene_props

        controllers = []

        if world is not None and world.node_tree:
            gather_controller_nodes(world.node_tree, controllers)

            for controller in controllers:
                if controller.bl_idname == 'group_controller_type':
                    box = layout.box()
                    row = box.row(align=True)
                    row.enabled=False
                    row.scale_x = .7
                    row.label(text="GROUP NAME")
                    row.scale_x = .5
                    row.label(text="COLOR PROFILE")
                    row.scale_x = 1
                    row.prop(scene, "record_settings_is_on", icon='BLANK1', text="")
                    row.prop(scene, "record_settings_is_on", icon='BLANK1', text="")
                    row.prop(scene, "record_settings_is_on", icon='BLANK1', text="")
                    row.prop(scene, "record_settings_is_on", icon='BLANK1', text="")
                    row.prop(scene, "record_settings_is_on", icon='BLANK1', text="")
                    row.prop(scene, "record_settings_is_on", icon='BLANK1', text="")
                    row.prop(scene, "record_settings_is_on", icon='BLANK1', text="")
                    row.prop(scene, "record_settings_is_on", icon='BLANK1', text="")
                    row.scale_x = .1
                    row.label(text="")
                    row.scale_x = 1
                    row.label(text="          |ENABLE STROBE")
                    row.label(text="          DISABLE STROBE|")
                    row.scale_x = .1
                    row.label(text="")
                    row.scale_x = 1
                    row.label(text="              GOBO ID   ")
                    row.scale_x = .1
                    row.label(text="")
                    row.scale_x = 1
                    row.label(text="          |SPEED VALUE")
                    row.label(text="          ENABLE SPEED")
                    row.label(text="          DISABLE SPEED|")
                    row.scale_x = .1
                    row.label(text="")
                    row.scale_x = 1
                    row.label(text="          |ENABLE PRISM")
                    row.label(text="          DISABLE PRISM|")
                    break

            for controller in controllers:
                if controller.bl_idname == 'group_controller_type':
                    box = layout.box()
                    row = box.row(align=True)
                    row.scale_x = .7
                    row.label(text=f"{controller.str_group_id}: {controller.label}")
                    row.scale_x = .5
                    if controller.color_is_on:
                        row.prop(controller, "color_profile_enum", icon='RESTRICT_COLOR_ON', text="")
                    else: row.label(text="")
                    row.scale_x = 1
                    row.prop(controller, "color_is_on", icon='RESTRICT_COLOR_ON', text="")
                    row.prop(controller, "strobe_is_on", icon='OUTLINER_DATA_LIGHTPROBE', text="")
                    row.prop(controller, "pan_tilt_is_on", icon='ORIENTATION_GIMBAL', text="")
                    row.prop(controller, "zoom_is_on", icon='LINCURVE', text="")
                    row.prop(controller, "iris_is_on", icon='RADIOBUT_OFF', text="")
                    row.prop(controller, "edge_is_on", icon='SELECT_SET', text="")
                    row.prop(controller, "diffusion_is_on", icon='MOD_CLOTH', text="")
                    row.prop(controller, "gobo_id_is_on", icon='POINTCLOUD_DATA', text="")
                    row.scale_x = .1
                    row.label(text="")
                    row.scale_x = 1
                    if controller.strobe_is_on:
                        row.prop(controller, "str_enable_strobe_argument", text="", icon='OUTLINER_DATA_LIGHTPROBE')
                        row.prop(controller, "str_disable_strobe_argument", text="", icon='CHECKBOX_DEHLT')
                    else: 
                        row.label(text="")
                        row.label(text="")
                    row.scale_x = .1
                    row.label(text="")
                    row.scale_x = 1
                    if controller.gobo_id_is_on:
                        row.prop(controller, "str_gobo_id_argument", text="", icon='POINTCLOUD_DATA')
                        row.scale_x = .1
                        row.label(text="")
                        row.scale_x = 1
                        row.prop(controller, "str_gobo_speed_value_argument", text="", icon='CON_ROTLIKE')
                        row.prop(controller, "str_enable_gobo_speed_argument", text="", icon='CHECKBOX_HLT')
                        row.prop(controller, "str_disable_gobo_speed_argument", text="", icon='CHECKBOX_DEHLT')
                        row.scale_x = .1
                        row.label(text="")
                        row.scale_x = 1
                        row.prop(controller, "str_enable_prism_argument", text="", icon='TRIA_UP')
                        row.prop(controller, "str_disable_prism_argument", text="", icon='CHECKBOX_DEHLT')
                    else:
                        row.label(text="")
                        row.scale_x = .1
                        row.label(text="")
                        row.scale_x = 1
                        row.label(text="")
                        row.label(text="")
                        row.label(text="")
                        row.scale_x = .1
                        row.label(text="")
                        row.scale_x = 1
                        row.label(text="")
                        row.label(text="")
                    
            layout.separator()
            layout.separator()
        
            for controller in controllers:
                if controller.bl_idname == 'group_controller_type':
                    box = layout.box()
                    row = box.row(align=True) 
                    row.label(text=controller.str_group_label)
                    if controller.pan_tilt_is_on:  
                        row.prop(controller, "pan_min", text="Pan Min")
                        row.prop(controller, "pan_max", text="Max")
                        row.scale_x = .1
                        row.label(text="")
                        row.scale_x = 1
                        row.prop(controller, "tilt_min", text="Tilt Min")
                        row.prop(controller, "tilt_max", text="Max")
                    else:
                        row.label(text="")
                        row.label(text="")
                        row.scale_x = .1
                        row.label(text="")
                        row.scale_x = 1
                        row.label(text="")
                        row.label(text="")
                    row.scale_x = .1
                    row.label(text="")
                    row.scale_x = 1            
                    if controller.strobe_is_on:    
                        row.prop(controller, "strobe_min", text="Strobe Min")
                        row.prop(controller, "strobe_max", text="Max")
                    else:
                        row.label(text="")
                        row.label(text="")
                    row.scale_x = .1
                    row.label(text="")
                    row.scale_x = 1 
                    if controller.zoom_is_on:
                        row.prop(controller, "zoom_min", text="Zoom Min")
                        row.prop(controller, "zoom_max", text="Max")
                    else:
                        row.label(text="")
                        row.label(text="")
                    row.scale_x = .1
                    row.label(text="")
                    row.scale_x = 1 
                    if controller.iris_is_on:
                        row.prop(controller, "iris_min", text="Iris Min")
                        row.prop(controller, "iris_max", text="Max")
                    else:
                        row.label(text="")
                        row.label(text="")
                    row.scale_x = .1
                    row.label(text="")
                    row.scale_x = 1            
                    if controller.edge_is_on:       
                        row.prop(controller, "edge_min", text="Edge Min")
                        row.prop(controller, "edge_max", text="Max")
                    else:
                        row.label(text="")
                        row.label(text="")
                    row.scale_x = .1
                    row.label(text="")
                    row.scale_x = 1 
                    if controller.gobo_id_is_on:
                        row.prop(controller, "speed_min", text="Speed Min")
                        row.prop(controller, "speed_max", text="Max")
                    else:
                        row.label(text="")
                        row.label(text="")


classes = (
    ChannelControllerPanel,
    GroupsPanel,
    ModalChannelControllerPanel,
    ParameterComboPanel,
    GroupSettingsPanel,
    LightArrayPanel
)


addon_keymaps = []


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.VIEW3D_HT_header.append(draw_is_influencer)

    wm = bpy.context.window_manager
    if wm.keyconfigs.addon:
        km = wm.keyconfigs.addon.keymaps.new(name='Object Mode', space_type='EMPTY')
        kmi = km.keymap_items.new("my.show_properties", 'P', 'PRESS')
        addon_keymaps.append((km, kmi))
        
    pcoll = bpy.utils.previews.new()
    preview_collections["main"] = pcoll
    icons_dir = "/Users/easystreetphotography1/Downloads"
    pcoll.load("my_icon", os.path.join(icons_dir, "alva_orb.png"), 'IMAGE')
    
    

def unregister():
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    
    bpy.types.VIEW3D_HT_header.remove(draw_is_influencer)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


# For development purposes only.
if __name__ == "__main__":
    register()


            