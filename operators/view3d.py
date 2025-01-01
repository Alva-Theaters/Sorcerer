# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.props import *
from bpy.types import Operator

from ..cpv.find import Find 
from ..utils.cpv_utils import simplify_channels_list
from ..utils.osc import OSC
from ..assets.tooltips import find_tooltip

# pyright: reportInvalidTypeForm=false


class VIEW3D_OT_alva_add_driver(Operator):
    '''Create a Sorcerer driver to control parameters with movement in 3D View'''
    bl_idname = "alva_object.driver_add"
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
    
    
class VIEW3D_OT_alva_toggle_object_mute(Operator):
    bl_idname = "alva_object.toggle_object_mute"
    bl_label = "Mute OSC"
    bl_description = "Disable object's OSC output"

    space_type: StringProperty() 
    node_name: StringProperty() 
    node_tree_name: StringProperty() 

    def execute(self, context):
        finders = Find
        active_controller = finders.find_controller_by_space_type(context, self.space_type, self.node_name, self.node_tree_name)
        active_controller.mute = not active_controller.mute
        return {'FINISHED'}
    
    
class VIEW3D_OT_alva_pull_fixture_selection(Operator):
    bl_idname = "alva_object.pull_selection"
    bl_label = "Pull Fixtures"
    bl_description = "Pull current selection from 3D view"

    def execute(self, context):
        channels = []
        for obj in context.selected_objects:
            if len(obj.list_group_channels) == 1:
                channels.append(obj.list_group_channels[0].chan)

        new_list = simplify_channels_list(channels)
        context.scene.scene_props.add_channel_ids = new_list
        return {'FINISHED'}
    
    
class VIEW3D_OT_alva_add_lighting_modifier(Operator):
    bl_idname = "alva_object.add_lighting_modifier"
    bl_label = "Add Lighting Modifier"
    bl_description = "Control all fixtures at once using photo-editing principles like layering"
    
    type: bpy.props.EnumProperty(
        name="Lighting Modifiers",
        description="Change all fixtures at once using photo-editing principles",
        items = [
            ('option_brightness_contrast', "Brightness/Contrast", "Adjust overall brightness and contrast of entire rig's intensity values"),
            ('option_saturation', "Saturation", "Adjust overall saturation of entire rig"),
            ('option_hue', "Hue", "Adjust the saturation of individual hues across the entire rig"),
            ('option_curves', "Curves", "Adjust overall brightness and contrast of entire rig's intensity values"),
            ('option_compressor', "Compressor", "Prevent parameters from changing too much too fast")
        ]
    )

    def execute(self, context):
        scene = context.scene
        modifier = scene.lighting_modifiers.add()
        modifier.name = self.type.replace('option_', '').replace('_', '/').title()
        modifier.type = self.type
        scene.active_modifier_index = len(scene.lighting_modifiers) - 1

        return {'FINISHED'}


class VIEW3D_OT_alva_remove_lighting_modifier(Operator):
    '''Remove selected modifier'''
    bl_idname = "alva_object.remove_lighting_modifier"
    bl_label = "Remove Lighting Modifier"

    name: StringProperty()

    def execute(self, context):
        scene = context.scene
        index = scene.lighting_modifiers.find(self.name)
        if index != -1:
            scene.lighting_modifiers.remove(index)
            scene.active_modifier_index = min(max(0, scene.active_modifier_index - 1), len(scene.lighting_modifiers) - 1)
        return {'FINISHED'}


class VIEW3D_OT_alva_bump_lighting_modifier(Operator):
    '''Bump modifiers position in the stack vertically'''
    bl_idname = "alva_object.bump_lighting_modifier"
    bl_label = "Move Lighting Modifier"

    name: StringProperty()
    direction: EnumProperty(
        items=(
            ('UP', 'Up', ''),
            ('DOWN', 'Down', '')
        )
    )

    def execute(self, context):
        scene = context.scene
        index = scene.lighting_modifiers.find(self.name)
        if index == -1:
            return {'CANCELLED'}
        new_index = index + (-1 if self.direction == 'UP' else 1)
        if new_index < 0 or new_index >= len(scene.lighting_modifiers):
            return {'CANCELLED'}
        scene.lighting_modifiers.move(index, new_index)
        scene.active_modifier_index = new_index
        return {'FINISHED'}
    
    
class VIEW3D_OT_alva_summon_movers(Operator):
    bl_idname = "alva_object.summon_movers"
    bl_label = "Summon Movers"
    bl_description = "You're supposed to type in a command line command in the space to the left and then fire that command by pressing this button. Use this feature to call any relevant moving lights to focus on this set piece"

    def execute(self, context):
        scene = context.scene.scene_props
        active_object = context.active_object
        string = active_object.str_call_fixtures_command
        
        if not string.endswith(" Enter"):
            string = f"{string} Enter"
        
        OSC.send_osc_lighting("/eos/newcmd", string)
        return {'FINISHED'}


class VIEW3D_OT_alva_object_controller(Operator):
    bl_idname = "alva_object.object_controller"
    bl_label = "Object Controller"
    
    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        width = 180
        return context.window_manager.invoke_popup(self, width=width)

    @classmethod
    def poll(cls, context):
        return (hasattr(context, "scene") and
                hasattr(context, "active_object"))

    def draw(self, context):
        active_object = context.active_object
        from ..as_ui.space_common import draw_parameters_mini, draw_play_bar
        from ..as_ui.blender_spaces.space_view3d import draw_speaker
        
        if active_object.type == 'MESH':
            draw_parameters_mini(context, self.layout, active_object, use_slider=True)
            self.layout.separator()
            draw_play_bar(context, self.layout)
        
        if active_object.type == 'SPEAKER':
            draw_speaker(self, context, active_object, use_split=False)

class VIEW3D_OT_alva_duplicate_object(Operator):
    bl_idname = "alva_object.duplicate_object"
    bl_label = find_tooltip("alva_object.duplicate_object")
    bl_options = {'REGISTER', 'UNDO'}

    Axis: EnumProperty(
        items=[('X', 'X Axis', 'Move along X axis'),
               ('Y', 'Y Axis', 'Move along Y axis'),
               ('Z', 'Z Axis', 'Move along Z axis')],
        name="Axis",
        default='X'
    )
    Direction: IntProperty(
        name="Direction",
        description=find_tooltip("duplicate_direction"),
        default=1,
        min=-1,
        max=1
    )
    Quantity: IntProperty(
        name="Quantity",
        description=find_tooltip("duplicate_quantity"),
        default=1,
        min=1
    )

    @classmethod
    def poll(cls, context):
        return (hasattr(context, "scene") and
                hasattr(context, "active_object"))

    def execute(self, context):
        if context.object:
            axis_map = {'X': (1, 0, 0), 'Y': (0, 1, 0), 'Z': (0, 0, 1)}
            move_vector = tuple(self.Direction * axis_map[self.Axis][i] for i in range(3))

            for i in range(self.Quantity):
                bpy.ops.object.duplicate()
                bpy.ops.transform.translate(value=move_vector)
                new_obj = context.object
                if hasattr(new_obj, "list_group_channels") and len(new_obj.list_group_channels) == 1:
                    new_obj.str_manual_fixture_selection = str(new_obj.list_group_channels[0].chan + 1)

            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "No object selected")
            return {'CANCELLED'}


classes = (
    VIEW3D_OT_alva_add_driver,
    VIEW3D_OT_alva_toggle_object_mute,
    VIEW3D_OT_alva_pull_fixture_selection,
    VIEW3D_OT_alva_add_lighting_modifier,
    VIEW3D_OT_alva_remove_lighting_modifier,
    VIEW3D_OT_alva_bump_lighting_modifier,
    VIEW3D_OT_alva_summon_movers,
    VIEW3D_OT_alva_object_controller,
    VIEW3D_OT_alva_duplicate_object
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
            
        
def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)