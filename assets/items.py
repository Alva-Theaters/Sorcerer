# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy


class Items:
    def preferences(self, context):
        items = [
            ('network', "Network", "Network settings for audio, lighting, and video."),
            ('sequencer', "Sequencer", "Settings for video sequencer area."),
            ('orb', "Orb", "Settings for Orb automation assistant."),
            ('stage_manager', "Stage Manager", "OSC Settings for Stage Manager (Properties viewer under Scene)."),
            ('system', "System", "System-wide general settings.")
        ]
        return items
    

    def color_profiles(self, context):
        items = [
            ('option_rgb', "RGB", "Red, Green, Blue"),
            ('option_rgba', "RGBA", "Red, Green, Blue, Amber"),
            ('option_rgbw', "RGBW", "Red, Green, Blue, White"),
            ('option_rgbaw', "RGBAW", "Red, Green, Blue, Amber, White"),
            ('option_rgbl', "RGBL", "Red, Green, Blue, Lime"),
            ('option_rgbam', "RGBAM", "Red, Green, Blue, Amber, Mint"),
            ('option_cmy', "CMY", "Cyan, Magenta, Yellow")
        ]
        
        return items


    def highlight_or_remove(self, context):
        items = [
            ('option_highlight', "Highlight", "Briefly highlight pressed channels on stage", 'OUTLINER_OB_LIGHT', 0),
            ('option_remove', "Remove", "Remove channels from group", 'TRASH', 1),
        ]
        
        return items


    def sequence_steps(self, context):
        items = [
            ('option_pre_show', "Pre-show", "Theater is in Initial Configuration."),
            ('option_lobby_open', "Lobby Open", "Theater is in Lobby Open Configuration"),
            ('option_house_open', "House Open", "Theater is in House Open Configuration"),
            ('option_go_for_show_start', "Go for Start", "Theater is in Final Configuration"),
            ('option_underway', "Underway", "Theater is in Underway Configuration"),
            ('option_intermission', "Intermission", "Theater is in Intermission Configuration"),
            ('option_clear', "Clear", "Theater returns to Initial Configuration")
        ]
        
        return items


    def flags(self, context):
        items = [
            ('option_highlight', "Highlight", "Briefly highlight pressed channels on stage", 'OUTLINER_OB_LIGHT', 0),
            ('option_remove', "Remove", "Remove channels from group", 'TRASH', 1),
        ]
        
        return items


    def console_types(self, context):
        from ..utils.spy_utils import REGISTERED_LIGHTING_CONSOLES

        items = []
        for cls in REGISTERED_LIGHTING_CONSOLES.values():
            items.append((cls.as_idname, cls.as_label, cls.as_description))
        return items
    

    def strip_types(self, context):
        from ..utils.spy_utils import REGISTERED_STRIPS

        items = []
        for i, cls in enumerate(REGISTERED_STRIPS.values()):
            items.append((cls.as_idname, "", cls.as_description, cls.as_icon, i))  # as_label is drawn to the right, not with this
        return items
    

    def mixer_types(self, context):
        items = [
            #('option_m32', "M32/X32", "AUse an M32/X32 mixer for real-time 3D audio monitoring"),
            ('option_qlab', "Qlab", "Use Qlab for real-time 3D audio monitoring")
        ]
        
        return items


    def core_types(self, context):
        items = [
            ('option_renegade', "Alva Renegade", "")
        ]
        
        return items


    def core_drives(self, context):
        items = [
            ('option_drive', "E:", "")
        ]
        
        return items

        
    def get_modifier_items(self, context):
        items = [("NONE", "None", "No array modifiers available")]
        obj = context.active_object
        
        if obj:
            for modifier in obj.modifiers:
                if not modifier.name.isdigit():
                    items.append((modifier.name, modifier.name, "")) 
                     
        return items


    def get_curve_items(self, context):
        items = [("NONE", "None", "No curve modifiers available")]
        obj = context.active_object
        
        if obj:
            for modifier in obj.modifiers:
                if not modifier.name.isdigit():
                    items.append((modifier.name, modifier.name, ""))
                    
        return items


    def get_cone_items(self, context):
        items = [("NONE", "None", "No suitable meshes available")]
        
        for obj in bpy.data.objects:
            if not obj.name.isdigit():
                items.append((obj.name, obj.name, ""))
                    
        return items


    def color_profiles(self, context):
        items = [
            ('option_rgb', "RGB", "Red, Green, Blue"),
            ('option_rgba', "RGBA", "Red, Green, Blue, Amber"),
            ('option_rgbw', "RGBW", "Red, Green, Blue, White"),
            ('option_rgbaw', "RGBAW", "Red, Green, Blue, Amber, White"),
            ('option_rgbl', "RGBL", "Red, Green, Blue, Lime"),
            ('option_rgbam', "RGBAM", "Red, Green, Blue, Amber, Mint"),
            ('option_cmy', "CMY", "Cyan, Magenta, Yellow")
        ]
        
        return items
    

    def freezing_modes(self, context):
        items = [
            ('option_all', "On All", "Changing parameters update console on every frames during playback"),
            ('option_seconds', "On Seconds", "Changing parameters update console on every other frame during playback"),
            ('option_thirds', "On Thirds", "Changing parameters update console on every third frame during playback"),
        ]
        
        return items


    def object_identities(self, context):
        items = [
            ('Fixture', "Fixture", "This controls a single lighting fixture.", 'OUTLINER_OB_LIGHT', 0),
            ('Pan/Tilt Fixture', "Pan/Tilt", "Select this only if you intend to use Blender's pan/tilt gimbals or constraints.", 'ORIENTATION_GIMBAL', 1),
            ('Influencer', "Influencer", "This is a bit like 3D bitmapping. Fixtures inside this object will inherit this object's parameters. Changes are reverted when the object leaves.", 'CUBE', 2),
            ('Key', "Key", "Create 3-dimensional gradients with influencers that can interact with each other.", 'CUBE', 3),
            ('Brush', "Brush", "Move this object over fixtures for a paint brush effect. Changes persist when the object leaves.", 'BRUSH_DATA', 4),
            ('Stage Object', "Stage Object", "Select the lights on a specific stage object by selecting the stage object, not a light-board group.", 'HOME', 5)
        ]
        
        return items


    def scene_groups(self, context):
        items = []

        items.append(("Dynamic", "Dynamic", "Use the object's location with respect to others to change its targets", 'VIEW3D', 0))

        if context.scene.scene_group_data:
            for group in context.scene.scene_group_data:
                items.append((group.name, group.name, ""))
                
        return items


    def get_sound_sources(self, context):
        items = []
        sequencer = context.scene.sequence_editor

        textual_numbers = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
                           "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty",
                           "twenty_one", "twenty_two", "twenty_three", "twenty_four", "twenty_five", "twenty_six", "twenty_seven", "twenty_eight", "twenty_nine", "thirty",
                           "thirty_one", "thirty_two"]

        if sequencer:
            items.extend([(strip.name, strip.name, "") for strip in sequencer.sequences_all if strip.type == 'SOUND'])
        
        for i in range(33):
            if i == 0:
                i += 1
            input_prop_name = f"input_{textual_numbers[i]}"
            input_display_name = f"Input {i}"
            input_description = f"Corresponds to Input {i} on the audio mixer"
            items.append((input_prop_name, input_display_name, input_description))

        for i in range(17):
            if i == 0:
                i += 1
            input_prop_name = f"bus_{textual_numbers[i]}"
            input_display_name = f"Bus {i}"
            input_description = f"Corresponds to Bus {i} on the audio mixer"
            items.append((input_prop_name, input_display_name, input_description))
            
        return items


    def get_speakers(self, context):
        items = []
        textual_numbers = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
                           "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty",
                           "twenty_one", "twenty_two", "twenty_three", "twenty_four", "twenty_five", "twenty_six", "twenty_seven", "twenty_eight", "twenty_nine", "thirty",
                           "thirty_one", "thirty_two"]

        if context.scene.sequencer:
            items.extend([(strip.name, strip.name, "") for strip in context.scene.sequencer.sequences_all if strip.type == 'SOUND'])
        
        for i in range(17):
            if i == 0:
                i += 1
            input_prop_name = f"output_{textual_numbers[i]}"
            input_display_name = f"Output {i}"
            input_description = f"Corresponds to Output {i} on the audio mixer"
            items.append((input_prop_name, input_display_name, input_description))
                
        for i in range(7): 
            if i == 0:
                i += 1
            input_prop_name = f"dca_{textual_numbers[i]}"
            input_display_name = f"DCA {i}"
            input_description = f"Corresponds to DCA {i} on the audio mixer"
            items.append((input_prop_name, input_display_name, input_description))
                

    def mixer_parameters(self, context):
        items = [
            ('option_intensity', "Intensity", "Mix intensities across a group", 'OUTLINER_OB_LIGHT', 1),
            ('option_color', "Color", "Mix colors across a group", 'COLOR', 2),
            ('option_pan_tilt', "Pan/Tilt", "Mix pan/tilt settings across a group", 'ORIENTATION_GIMBAL', 3),
            ('option_zoom', "Zoom", "Mix zoom settings across a group", 'LINCURVE', 4),
            ('option_iris', "Iris", "Mix iris settings across a group", 'RADIOBUT_OFF', 5)
        ]
        return items
    
    def mixer_methods(self, context):
        items = [
            ('option_gradient', "Gradient", "Mix choices across a group evenly", 'SMOOTHCURVE', 1),
            ('option_pattern', "Pattern", "Create patterns out of choices without mixing", 'IPO_CONSTANT', 2),
            ('option_pose', "Pose", "Create poses to oscillate between", 'POSE_HLT', 3),
        ]
        return items
    
    def ip_address_view_options(self, context):
        items = [
            ('option_lighting', "Lighting", "Adjust IP address/port for lighting console", 'OUTLINER_OB_LIGHT', 1),
            ('option_video', "Video", "Adjust IP address/port for video switcher", 'OUTLINER_OB_CAMERA', 2),
            ('option_audio', "Audio", "Adjust IP address/port for audio mixer", 'OUTLINER_OB_SPEAKER', 3),
        ]
        return items

    def alva_settings_positions(self, context):
        items = [
            ('option_animation', "Animated", "Animation engine settings"),
            ('option_lighting', "Lighting", "Lighting network settings"),
            ('option_video', "Video &", "Video network settings"),
            ('option_audio', "Audio", "Audio network settings")
        ]
        return items
    
    
    def transmission_options(self, context):
        items = [
            ('option_manual', "Manual", "Spin the motor using the mouse", 'MOUSE_LMB', 1),
            ('option_keyframe', "Keyframe", "Spin the motor with keyframes", 'DECORATE_KEYFRAME', 2)
        ]
        return items
    
    
    def global_node_parameters(self, context):
        items = [
            ('option_intensity', "Intensity", "Mix intensities across a group", 'OUTLINER_OB_LIGHT', 1),
            ('option_color', "Color", "Mix colors across a group", 'COLOR', 2),
            ('option_pan_tilt', "Pan/Tilt", "Mix pan/tilt settings across a group", 'ORIENTATION_GIMBAL', 3),
            ('option_zoom', "Zoom", "Mix zoom settings across a group", 'LINCURVE', 4),
            ('option_iris', "Iris", "Mix iris settings across a group", 'RADIOBUT_OFF', 5),
            ('option_compound', "Compound", "Mix iris settings across a group", 'SNAP_VERTEX', 6)
        ]
        return items
    

    def presets_node_types(self, context):
        items = [
            ('Preset', "Preset", "Record and overwrite all parameters"),
            ('Color_Palette', "Color Palette", "Record and overwrite only color data")
        ]
        return items
    
    
    def get_audio_object_items(self, context):
        items = [
            ('option_object', "Strip represents a 3D audio object", "This will produce sound and move throughout the scene", 'MESH_CUBE', 1),
            ('option_speaker', "Strip represents a speaker", "This represents a physical speaker at the the theater", 'SPEAKER', 2),
        ]
        return items


    def flash_types(self, context):
        items = [
            ('option_manual', "Manual", "Type in what feels natural", 'FILE_TEXT', 0),
            ('option_use_nodes', "Nodes", "Auto-fill Flash Up and Flash Down fields with nodes", 'NODETREE', 1),
            ('option_use_controllers', "Controllers", "Use two controllers to directly define a flash", 'NODE_SEL', 2)
        ]
        return items
    

    def offset_types(self, context):
        items = [
            ('option_intensity', "Intensity", "Create intensity offset effect"),
            ('option_zoom', "Zoom", "Create zoom offset effect"),
            ('option_iris', "Iris", "Create iris offset effect"),
            ('option_preset', "Preset", "Create offset effect with a preset"),
            ('option_color_palette', "Color Palette", "Create offset effect with a color palette"),
            ('option_intensity_palette', "Intensity Palette", "Create offset effect with an intensity palette"),
            ('option_focus_palette', "Focus Palette", "Create offset effect with a focus palette"),
            ('option_beam_palette', "Beam Palette", "Create offset effect with a beam palette")
        ]
        return items
    

    def direct_select_types(self, context):
        items = [
            ('Preset', "Preset", "Trigger or record presets", 'OUTLINER_OB_IMAGE', 0),
            ('Intensity Palette', "Intensity", "Trigger or record intensity palettes", 'OUTLINER_OB_LIGHT', 1),
            ('Color Palette', "Color", "Trigger or record color palettes", 'COLOR', 2),
            ('Focus Palette', "Focus", "Trigger or record focus palettes", 'ORIENTATION_GIMBAL', 3),
            ('Beam Palette', "Beam", "Trigger or record beam palettes", 'OUTLINER_DATA_POINTCLOUD', 4),
            ('Effect', "FX", "Trigger or record effects", 'SORTBYEXT', 5),
            ('Group', "Group", "Select or record groups", 'OUTLINER_COLLECTION', 6),
            ('Macro', "Macro", "Trigger or record macros", 'FILE_TEXT', 7)
        ]
        return items
    

    def audio_panning_falloff_types(self, context):
        items = [
            ('linear', 'Linear', '', 'IPO_LINEAR', 0),
            ('bezier', 'Bezier', '', 'IPO_BEZIER', 1),
            ('quadratic', 'Quadratic', '', 'IPO_QUADRATIC', 2),
            ('cubic', 'Cubic', '', 'IPO_CUBIC', 3),
            ('exponential', 'Exponential', '', 'IPO_EXPONENTIAL', 4),
            ('sinusoidal', 'Sinusoidal', '', 'IPO_SINUSOIDAL', 5)
        ]

        return items