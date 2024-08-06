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
from bpy.props import StringProperty, CollectionProperty, BoolProperty, EnumProperty, IntProperty, FloatProperty, FloatVectorProperty, PointerProperty
from bpy.types import PropertyGroup, Object, ColorSequence

from ..utils.utils import Utils # type: ignore
from ..assets.items import Items as AlvaItems # type: ignore
from ..updaters.common_updaters import CommonUpdaters # type: ignore
from ..updaters.node_updaters import NodeUpdaters # type: ignore
from ..cpvia.cpvia_generator import CPVIAGenerator # type: ignore


InfluencerListSubClass = Utils.find_subclass_by_name(PropertyGroup, "InfluencerList")
ChannelsListSubClass = Utils.find_subclass_by_name(PropertyGroup, "ChannelsList")


'''
_____________________________________________________________________
AVAILABLE PROPERTY LISTS.

 1. controller_ids:
    - Contains background properties for identifying the controller 
      and its targets.
    - Includes properties like group ID, group label,
      list of group channels, and a boolean for manual input.

 2. object_only:
    - Specific to object-related properties.
    - Includes properties for muting, object identity,
      fixture-specific commands, channel index, and eraser mode.
    - Also contains pan/tilt node properties and 3D audio settings.

 3. flash_strip_parameters:
    - Properties related to Flash-strip controls.
    - Includes settings for intensity, color, pan, tilt, strobe,
      zoom, iris, and gobo IDs, for both up and down states, but
      specifically for the flash strip GUI.

 4. common_header:
    - General properties used across multiple contexts.
    - Includes manual fixture selection, group and profile enums,
      and color profile enums.

 5. common_parameters:
    - Core parameter controls such as intensity, color, pan, tilt,
      zoom, and iris.
    - Currently only used by itself for mixer nodes.

 6. common_parameters_extended:
    - Extension of the common parameters.
    - Includes properties like influence, color restore, volume,
      diffusion, strobe, edge, gobo settings, and prism.
    - Used everywhere except on mixer nodes.

 7. mins_maxes:
    - Properties defining the minimum and maximum values for
      pan, tilt, zoom, and gobo_speed.

 8. parameter_toggles:
    - Toggle switches for enabling/disabling specific features.
    - Includes toggles for influence, audio, mic linking,
      intensity, pan/tilt, color, diffusion, strobe, zoom, iris,
      edge, gobo ID, and prism.

 9. special_arguments:
    - Stores specific command strings for OSC control.
    - Includes enable/disable commands for strobe, gobo speed,
      misc effects, prism, and gobo ID with placeholders.
      
_____________________________________________________________________
HOW TO USE.

    Utils.register_properties(cls, properties, register=True)
    
        NOTE: When using this on a class, like when creating a PropertyGroup
              or custom node, or anytime you use the "property: property"
              method, these function calls must go in the register() 
              section and after the bpy.types class is registered. This
              function call cannot go in the class. Otherwise the class name 
              will not exist at the time this function is called.
        
        arguments:
            1. cls— the python class name, __name__, typically Object,
               ColorSequence, or class name of the node in PascalCase.
               
            2. properties— The list above, so controller_ids, object_only, 
               etc. Prefix with bpy.ALVA_CommonProperties.[list name like 
               patch_info] if running from text editor or by importing
               at the top with "from .[filepath] import [CommonPropeties]" 
               method, then just prefix with CommonProperties.
               
            3. register— optional argument that defaults to True. Pass
               "register=False" or "register=0" to use this function 
               in an unregister section.
               
        returns:
            1. Nothing. This registers properties into Blender's internal
               data structure.

'''

class CommonProperties:
    controller_ids = [
        ('str_group_id',  StringProperty(default="1")),
        ('list_group_channels', CollectionProperty(type=ChannelsListSubClass)),
        ('str_group_label', StringProperty(default="")),
        ('is_group_not_manual', BoolProperty(default=False, description="Stores the decision to use manual input or group enum")),
        ('node_tree_pointer', PointerProperty(
            name="Node Tree Pointer",
            type=bpy.types.NodeTree,
            description="Pointer to the node tree"
        )),
        ('node_name', StringProperty())
    ]

    object_only = [
        ('mute', BoolProperty(default=False, description="Mute this object's OSC output")),
        ('object_identities_enum', EnumProperty(
            name="Mesh Identity",
            description="In Sorcerer, meshes can represent and control individual lighting fixtures, microphones, stage objects, brushes, and 3D bitmapping objects. Select what you want your mesh to do here",
            items=AlvaItems.object_identities
        )),
        ('str_call_fixtures_command', StringProperty(
            name="Call Fixtures Command",
            description="Command line text to focus moving fixtures onto stage object",
            update=CommonUpdaters.call_fixtures_updater
        )),
        ('int_object_channel_index', IntProperty(default=1)),
        ('is_erasing', BoolProperty(name="Eraser", description="Erase instead of add")),
        ('influencer_list', CollectionProperty(type=InfluencerListSubClass)),
        ('float_object_strength', FloatProperty(default=1, min=0, max=1)),
        ('int_fixture_index', IntProperty(default=0)),
        ('fixture_index_is_locked', BoolProperty(default=True)),
        
        # Pan/Tilt node properties. Registered on object for patch reasons.
        ('float_vec_pan_tilt_graph', FloatVectorProperty(
            name="",
            subtype='COLOR',
            size=3,
            default=(.2, .2, .2),
            min=0.0,
            max=.2,
            update=NodeUpdaters.pan_tilt_graph_updater
        )),
        ('pan_tilt_graph_checker', FloatVectorProperty(
            name="",
            subtype='COLOR',
            size=3,
            default=(.2, .2, .2),
            min=0.0,
            max=.2
        )),
        ('pan_graph', FloatProperty(
            name="Pan",
            default=0.0,
            update=CPVIAGenerator.pan_graph_updater
        )),
        ('tilt_graph', FloatProperty(
            name="Tilt",
            default=0.0,
            update=CPVIAGenerator.tilt_graph_updater
        )),
        ('pan_is_inverted', BoolProperty(default=True, description="Light is hung facing forward, for example, in FOH.")),
        ('last_hue', FloatProperty(default=0)),
        ('overdrive_mode', StringProperty(default="")),
        ('is_overdriven_left', BoolProperty(default=False)),
        ('is_overdriven_right', BoolProperty(default=False)),
        ('is_approaching_limit', BoolProperty(default=False)),
        
        # 3D Audio Properties
        ('int_speaker_number', IntProperty(name="Speaker Number", description="Number of speaker in Qlab or on sound mixer. You're seeing this here because you selected a Speaker object, and speaker objects represent real, physical speakers in your theater for the purpose of spatial audio. To pan microphones left or right, you don't use an encoder, you just move the microphone or sound object closer to the left or right inside 3D view", default=0)),
        ('sound_source_enum', EnumProperty(items=AlvaItems.get_sound_sources, name="Select either a sound strip in the sequencer or a microphone in Audio Patch", update=CommonUpdaters.sound_source_updater))
    ]

    flash_strip_parameters = [
        ('float_flash_intensity_up', FloatProperty(default=0, min=0, max=100, description="Intensity value", update=CPVIAGenerator.intensity_updater)),
        ('float_vec_flash_color_up', FloatVectorProperty(
            name="",
            subtype='COLOR',
            size=3,
            default=(1.0, 1.0, 1.0),
            min=0.0,
            max=1.0,
            description="Color value",
            update=CPVIAGenerator.color_updater
        )), 
        ('float_flash_pan_up', FloatProperty(default=0, min=-315, max=315, description="Pan value", update=CPVIAGenerator.pan_updater)),
        ('float_flash_tilt_up', FloatProperty(default=0, min=-135, max=135, description="Tilt value", update=CPVIAGenerator.tilt_updater)),
        ('float_flash_strobe_up', FloatProperty(default=0, min=0, max=100, description="Strobe value", update=CPVIAGenerator.strobe_updater)),
        ('float_flash_zoom_up', FloatProperty(default=0, min=0, max=100, description="Zoom value", update=CPVIAGenerator.zoom_updater)),
        ('float_flash_iris_up', FloatProperty(default=0, min=0, max=100, description="Iris value", update=CPVIAGenerator.iris_updater)),
        ('int_flash_gobo_id_up', IntProperty(default=1, min=0, max=20, description="Gobo selection", update=CPVIAGenerator.gobo_id_updater)),
        ('float_flash_intensity_down', FloatProperty(default=0, min=0, max=100, description="Intensity value", update=CPVIAGenerator.intensity_updater)),
        ('float_vec_flash_color_down', FloatVectorProperty(
            name="",
            subtype='COLOR',
            size=3,
            default=(1.0, 1.0, 1.0),
            min=0.0,
            max=1.0,
            description="Color value",
            update=CPVIAGenerator.color_updater
        )),
        ('float_flash_pan_down', FloatProperty(default=0, min=-315, max=315, description="Pan value", update=CPVIAGenerator.pan_updater)),
        ('float_flash_tilt_down', FloatProperty(default=0, min=-135, max=135, description="Tilt value", update=CPVIAGenerator.tilt_updater)),
        ('float_flash_strobe_down', FloatProperty(default=0, min=0, max=100, description="Strobe value", update=CPVIAGenerator.strobe_updater)),
        ('float_flash_zoom_down', FloatProperty(default=0, min=0, max=100, description="Zoom value", update=CPVIAGenerator.zoom_updater)),
        ('float_flash_iris_down', FloatProperty(default=0, min=0, max=100, description="Iris value", update=CPVIAGenerator.iris_updater)),
        ('int_flash_gobo_id_down', IntProperty(default=1, min=0, max=20, description="Gobo selection", update=CPVIAGenerator.gobo_id_updater))
    ]  

    common_header = [
        ('str_manual_fixture_selection', StringProperty(
            name="Selected Light",
            description="Instead of the group selector to the left, simply type in what you wish to control here",
            update=CommonUpdaters.controller_ids_updater
        )),
        ('selected_group_enum', EnumProperty(
            name="Selected Group",
            description="Choose a group to control. Create these groups with the Patch function on the N tab in node editor, with USITT ASCII import in the same area, or create/modify them in Properties -> World -> SORCERER: Group Channel Blocks (full screen)",
            items=AlvaItems.scene_groups,
            update=CommonUpdaters.controller_ids_updater
        )),
        ('selected_profile_enum', EnumProperty(
            name="Profile to Apply",
            description="Choose a fixture profile to apply to this fixture and any other selected fixtures. Build profiles in Blender's Properties viewport under World",
            items=AlvaItems.scene_groups,
            update=CommonUpdaters.group_profile_updater
        )),
        ('color_profile_enum', EnumProperty(
            name="Color Profile",
            description="Choose a color profile for the mesh based on the patch in the lighting console",
            items=AlvaItems.color_profiles,
        ))
    ]

    common_parameters = [
        ('influence', IntProperty(
            default=1, description="How many votes this controller gets when there are conflicts", min=1, max=10)),
        ('float_intensity', FloatProperty(
            name="Intensity",
            default=0.0,
            min=0.0,
            max=100.0,
            description="Intensity value",
            options={'ANIMATABLE'},
            update=CPVIAGenerator.intensity_updater
        )),
        ('float_vec_color', FloatVectorProperty(
            name="Color",
            subtype='COLOR',
            size=3,
            default=(1.0, 1.0, 1.0),
            min=0.0,
            max=1.0,
            description='Color value. If your fixture is not an RGB fixture, but CMY, RGBA, or something like that, Sorcerer will automatically translate RGB to the correct color profile. The best way to tell Sorcerer which color profile is here on the object controller, to the right of this field. To make changes to many at a time, use the magic "Profile to Apply" feature on the top left of this box, or the "Apply Patch to Objects in Scene" button at the end of the group patch below this panel',
            update=CPVIAGenerator.color_updater
        )),
        ('float_pan', FloatProperty(
            name="Pan",
            default=0.0,
            min=-100,
            max=100,
            description="Pan value",
            options={'ANIMATABLE'},
            update=CPVIAGenerator.pan_updater
        )),
        ('float_tilt', FloatProperty(
            name="Tilt",
            default=0.0,
            min=-100,
            max=100,
            description="Tilt value",
            options={'ANIMATABLE'},
            update=CPVIAGenerator.tilt_updater
        )),
        ('float_zoom', FloatProperty(
            name="Zoom",
            default=0.0,
            min=0.0,
            max=100.0,
            description="Zoom value",
            options={'ANIMATABLE'},
            update=CPVIAGenerator.zoom_updater
        )),
        ('float_iris', FloatProperty(
            name="Iris",
            default=0.0,
            min=0.0,
            max=100.0,
            description="Iris value",
            options={'ANIMATABLE'},
            update=CPVIAGenerator.iris_updater
        ))
    ]
        
    common_parameters_extended = [
        ('float_vec_color_restore', FloatVectorProperty(
            name="Color (restore)",
            subtype='COLOR',
            size=3,
            default=(1.0, 1.0, 1.0),
            min=0.0,
            max=1.0,
            description="Why are there 2 colors for this one? Because remotely making relative changes to color doesn't work well. Influencers use relative changes for everything but color for this reason. This second color picker picks the color the influencer will restore channels to after passing over"
        )),
        ('float_volume', FloatProperty(
            name="Volume",
            default=0.0,
            min=0.0,
            max=100.0,
            description="Volume of microphone",
            options={'ANIMATABLE'}
        )),
        ('float_diffusion', FloatProperty(
            name="Diffusion",
            default=0.0,
            min=0,
            max=100.0,
            description="Diffusion value",
            options={'ANIMATABLE'},
            update=CPVIAGenerator.diffusion_updater
        )),
        ('float_strobe', FloatProperty(
            name="Shutter Strobe",
            default=0.0,
            min=0.0,
            max=100.0,
            description="Shutter strobe value",
            options={'ANIMATABLE'},
            update=CPVIAGenerator.strobe_updater
        )),
        ('float_edge', FloatProperty(
            name="Edge",
            default=0.0,
            min=0.0,
            max=100.0,
            description="Edge value",
            options={'ANIMATABLE'},
            update=CPVIAGenerator.edge_updater
        )),
        ('int_gobo_id', IntProperty(
            name="Gobo Selection",
            default=1,
            min=0,
            max=20,
            description="Gobo selection",
            options={'ANIMATABLE'},
            update=CPVIAGenerator.gobo_id_updater
        )),
        ('float_gobo_speed', FloatProperty(
            name="Gobo Speed",
            default=0.0,
            min=-300.0,
            max=300.0,
            description="Rotation of individual gobo speed",
            options={'ANIMATABLE'},
            update=CPVIAGenerator.gobo_speed_updater
        )),
        ('int_prism', IntProperty(
            name="Prism",
            default=0,
            min=0,
            max=1,
            description="Prism value. 1 is on, 0 is off",
            options={'ANIMATABLE'},
            update=CPVIAGenerator.prism_updater
        ))
    ]
        
    mins_maxes = [
        ('pan_min', IntProperty(
            default=-270, 
            description="Minimum value for pan"
        )),
        ('pan_max', IntProperty(
            default=270, 
            description="Maximum value for pan"
        )),
        ('tilt_min', IntProperty(
            default=-135, 
            description="Minimum value for tilt"
        )),
        ('tilt_max', IntProperty(
            default=135, 
            description="Maximum value for tilt"
        )),
        ('zoom_min', IntProperty(
            default=1, 
            description="Minimum value for zoom"
        )),
        ('zoom_max', IntProperty(
            default=100, 
            description="Maximum value for zoom"
        )),
        ('gobo_speed_min', IntProperty(
            default=-200, 
            description="Minimum value for speed"
        )),
        ('gobo_speed_max', IntProperty(
            default=200, 
            description="Maximum value for speed"
        ))
    ]
        
    '''IMPORTANT: intensity_is_on MUST default to True for Event Manager to work.'''
    parameter_toggles = [
        ('influence_is_on', BoolProperty(default=False, description="Influence is enabled when checked")),
        ('audio_is_on', BoolProperty(default=False, description="Audio is enabled when checked")),
        ('mic_is_linked', BoolProperty(default=False, description="Microphone volume is linked to Intensity when red")),
        ('intensity_is_on', BoolProperty(default=True, description="Intensity is enabled when checked")),
        ('pan_tilt_is_on', BoolProperty(default=False, description="Pan/Tilt is enabled when checked")), 
        ('color_is_on', BoolProperty(default=False, description="Color is enabled when checked")),
        ('diffusion_is_on', BoolProperty(default=False, description="Diffusion is enabled when checked")),
        ('strobe_is_on', BoolProperty(default=False, description="Strobe is enabled when checked")),
        ('zoom_is_on', BoolProperty(default=False, description="Zoom is enabled when checked")),
        ('iris_is_on', BoolProperty(default=False, description="Iris is enabled when checked")),
        ('edge_is_on', BoolProperty(default=False, description="Edge is enabled when checked")),
        ('gobo_id_is_on', BoolProperty(default=False, description="Gobo ID is enabled when checked")),
        ('prism_is_on', BoolProperty(default=False, description="Prism is enabled when checked")),
    ]
        
    special_arguments = [
        ('str_enable_strobe_argument', StringProperty(
            default="# Strobe_Mode 127 Enter", description="Add # for group ID")),
        
        ('str_disable_strobe_argument', StringProperty(
            default="# Strobe_Mode 76 Enter", description="Add # for group ID")),
        
        ('str_enable_gobo_speed_argument', StringProperty(
            default="", description="Add # for group ID")),
            
        ('str_disable_gobo_speed_argument', StringProperty(
            default="", description="Add # for group ID")),
            
        ('str_gobo_id_argument', StringProperty(
            default="# Gobo_Select $ Enter", description="Add # for group ID and $ for value")),

        ('str_enable_prism_argument', StringProperty(
            default="# Beam_Fx_Select 02 Enter", description="Add # for group ID")),
            
        ('str_disable_prism_argument', StringProperty(
            default="# Beam_Fx_Select 01 Enter", description="Add # for group ID")),

        ('str_gobo_speed_value_argument', StringProperty(
            default="# Gobo_Index/Speed at $ Enter", description="Add $ for animation data and # for fixture/group ID"))
    ]



def register():

    common_properties = CommonProperties()

    # Object, excluding flash_strip_parameters
    Utils.register_properties(Object, CommonProperties.controller_ids)
    Utils.register_properties(Object, CommonProperties.object_only)  # Unique
    Utils.register_properties(Object, CommonProperties.common_header)
    Utils.register_properties(Object, CommonProperties.common_parameters)
    Utils.register_properties(Object, CommonProperties.common_parameters_extended)
    Utils.register_properties(Object, CommonProperties.mins_maxes)
    Utils.register_properties(Object, CommonProperties.parameter_toggles)
    Utils.register_properties(Object, CommonProperties.special_arguments)

    # ColorSequence, excluding object_only
    Utils.register_properties(ColorSequence, CommonProperties.controller_ids)
    Utils.register_properties(ColorSequence, CommonProperties.common_header)
    Utils.register_properties(ColorSequence, CommonProperties.common_parameters)
    Utils.register_properties(ColorSequence, CommonProperties.common_parameters_extended)
    Utils.register_properties(ColorSequence, CommonProperties.mins_maxes)
    Utils.register_properties(ColorSequence, CommonProperties.parameter_toggles)
    Utils.register_properties(ColorSequence, CommonProperties.special_arguments)
    Utils.register_properties(ColorSequence, CommonProperties.flash_strip_parameters)  # Unique


def unregister():
    # Object, excluding flash_strip_parameters
    Utils.register_properties(Object, CommonProperties.controller_ids, register=False)
    Utils.register_properties(Object, CommonProperties.object_only, register=False)  # Unique
    Utils.register_properties(Object, CommonProperties.common_header, register=False)
    Utils.register_properties(Object, CommonProperties.common_parameters, register=False)
    Utils.register_properties(Object, CommonProperties.common_parameters_extended, register=False)
    Utils.register_properties(Object, CommonProperties.mins_maxes, register=False)
    Utils.register_properties(Object, CommonProperties.parameter_toggles, register=False)
    Utils.register_properties(Object, CommonProperties.special_arguments, register=False)

    # ColorSequence, excluding object_only
    Utils.register_properties(ColorSequence, CommonProperties.controller_ids, register=False)
    Utils.register_properties(ColorSequence, CommonProperties.common_header, register=False)
    Utils.register_properties(ColorSequence, CommonProperties.common_parameters, register=False)
    Utils.register_properties(ColorSequence, CommonProperties.common_parameters_extended, register=False)
    Utils.register_properties(ColorSequence, CommonProperties.mins_maxes, register=False)
    Utils.register_properties(ColorSequence, CommonProperties.parameter_toggles, register=False)
    Utils.register_properties(ColorSequence, CommonProperties.special_arguments, register=False)
    Utils.register_properties(ColorSequence, CommonProperties.flash_strip_parameters, register=False)  # Unique