# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.props import StringProperty, CollectionProperty, BoolProperty, EnumProperty, IntProperty, FloatProperty, FloatVectorProperty, PointerProperty
from bpy.types import Object, ColorSequence, Sequence, Scene, Light

from ..utils.rna_utils import register_properties
from ..assets.items import Items as AlvaItems 
from ..updaters.common import CommonUpdaters 
from ..updaters.sequencer import SequencerUpdaters 
from ..updaters.node import NodeUpdaters 
from ..cpv.cpv_generator import CPVGenerator 
from .property_groups import VIEW3D_PG_alva_influencer_property_group, ChannelsList, VIEW3D_PG_alva_speaker_list
from ..assets.tooltips import find_tooltip


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

    register_properties(cls, properties, register=True)
    
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
               at the top with "from .[filepath] import [CommonProperties]" 
               method, then just prefix with CommonProperties.
               
            3. register— optional argument that defaults to True. Pass
               "register=False" or "register=0" to use this function 
               in an unregister section.
               
        returns:
            1. Nothing. This registers properties into Blender's internal
               data structure.

'''

# NOTE: We use find_tooltip() because Sorcerer is multi-lingual and because Blender's C++ does weird things with periods."

class CommonProperties:
    controller_ids = [
        ('str_group_id',  StringProperty(default="1")),
        ('list_group_channels', CollectionProperty(type=ChannelsList)),
        ('str_group_label', StringProperty(default="")),
        ('is_text_not_group', BoolProperty(default=True, description="Stores the decision to use manual input or group enum")),
        ('node_tree_name', StringProperty),
        ('node_name', StringProperty())
    ]

    object_only = [
        ('mute', BoolProperty(name="Mute OSC", default=False, description=find_tooltip("mute"))),
        ('object_identities_enum', EnumProperty(
            name="Mesh Identity",
            description="Background only",
            items=AlvaItems.object_identities,
            default=2
        )),
        ('str_call_fixtures_command', StringProperty(
            name="Summon Movers Command",
            description=find_tooltip("summon_movers"),
            update=CommonUpdaters.call_fixtures_updater
        )),
        ('is_erasing', BoolProperty(name="Eraser", description=find_tooltip("erase"))),
        ('influencer_list', CollectionProperty(type=VIEW3D_PG_alva_influencer_property_group)),
        ('float_object_strength', FloatProperty(name="Strength", default=1, min=0, max=1, description=find_tooltip("strength"), update=CommonUpdaters.controller_ids_updater)),
        ('alva_is_absolute', BoolProperty(name="Absolute", default=False, description=find_tooltip("absolute"))),
        ('int_alva_sem', IntProperty(name="SEM", default=0, min=0, max=9999, description=find_tooltip("sem"))),

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
            update=CPVGenerator.pan_graph_updater
        )),
        ('tilt_graph', FloatProperty(
            name="Tilt",
            default=0.0,
            update=CPVGenerator.tilt_graph_updater
        )),
        ('pan_is_inverted', BoolProperty(default=True, description="Light is hung facing forward, for example, in FOH")),
        ('last_hue', FloatProperty(default=0)),
        ('overdrive_mode', StringProperty(default="")),
        ('is_overdriven_left', BoolProperty(default=False)),
        ('is_overdriven_right', BoolProperty(default=False)),
        ('is_approaching_limit', BoolProperty(default=False)),
        
        # 3D Audio Properties
        ('speaker_list', CollectionProperty(type=VIEW3D_PG_alva_speaker_list)),
        ('falloff_types', EnumProperty(name="Falloff Types", items=AlvaItems.audio_panning_falloff_types, description="Determines the fade curve when an audio object starts leaving or approaching a speaker")),
        ('int_speaker_number', IntProperty(name="Speaker Number", update=CommonUpdaters.speaker_number_updater, description=find_tooltip("speaker_number"), default=0)),
        ('sound_source_enum', EnumProperty(name="Sound Source", items=AlvaItems.get_sound_sources, description=find_tooltip("sound_source")))
    ]

    flash_strip_parameters = [
        ('float_flash_intensity_up', FloatProperty(name="Intensity Up", default=0, min=0, max=100, description="Intensity value", update=CPVGenerator.intensity_updater)),
        ('float_vec_flash_color_up', FloatVectorProperty(
            name="Color Up",
            subtype='COLOR',
            size=3,
            default=(1.0, 1.0, 1.0),
            min=0.0,
            max=1.0,
            description="Color value",
            update=CPVGenerator.color_updater
        )), 
        ('float_flash_pan_up', FloatProperty(name="Pan Up", default=0, min=-315, max=315, description="Pan value", update=CPVGenerator.pan_updater)),
        ('float_flash_tilt_up', FloatProperty(name="Tilt Up", default=0, min=-135, max=135, description="Tilt value", update=CPVGenerator.tilt_updater)),
        ('float_flash_strobe_up', FloatProperty(name="Strobe Up", default=0, min=0, max=100, description="Strobe value", update=CPVGenerator.strobe_updater)),
        ('float_flash_zoom_up', FloatProperty(name="Zoom Up", default=0, min=0, max=100, description="Zoom value", update=CPVGenerator.zoom_updater)),
        ('float_flash_iris_up', FloatProperty(name="Iris Up", default=0, min=0, max=100, description="Iris value", update=CPVGenerator.iris_updater)),
        ('int_flash_gobo_id_up', IntProperty(name="Gobo ID Up", default=1, min=0, max=20, description="Gobo selection", update=CPVGenerator.gobo_id_updater)),
        ('float_flash_intensity_down', FloatProperty(name="Inensity Down", default=0, min=0, max=100, description="Intensity value", update=CPVGenerator.intensity_updater)),
        ('float_vec_flash_color_down', FloatVectorProperty(
            name="Color Down",
            subtype='COLOR',
            size=3,
            default=(1.0, 1.0, 1.0),
            min=0.0,
            max=1.0,
            description="Color value",
            update=CPVGenerator.color_updater
        )),
        ('float_flash_pan_down', FloatProperty(name="Pan Down", default=0, min=-315, max=315, description="Pan value", update=CPVGenerator.pan_updater)),
        ('float_flash_tilt_down', FloatProperty(name="Tilt Down", default=0, min=-135, max=135, description="Tilt value", update=CPVGenerator.tilt_updater)),
        ('float_flash_strobe_down', FloatProperty(name="Strobe Down", default=0, min=0, max=100, description="Strobe value", update=CPVGenerator.strobe_updater)),
        ('float_flash_zoom_down', FloatProperty(name="Zoom Down", default=0, min=0, max=100, description="Zoom value", update=CPVGenerator.zoom_updater)),
        ('float_flash_iris_down', FloatProperty(name="Iris Down", default=0, min=0, max=100, description="Iris value", update=CPVGenerator.iris_updater)),
        ('int_flash_gobo_id_down', IntProperty(name="Gobo ID Down", default=1, min=0, max=20, description="Gobo selection", update=CPVGenerator.gobo_id_updater))
    ]  

    common_header = [
        ('str_manual_fixture_selection', StringProperty(
            name="Selected Light(s)",
            description=find_tooltip("manual_fixture_selection"),
            default="1",
            update=CommonUpdaters.controller_ids_updater
        )),
        ('selected_group_enum', EnumProperty(
            name="Selected Group",
            description=find_tooltip("selected_group_enum"),
            items=AlvaItems.scene_groups,
            update=CommonUpdaters.controller_ids_updater
        )),
        ('selected_profile_enum', EnumProperty(
            name="Profile to Apply",
            description=find_tooltip("selected_profile_enum"),
            items=AlvaItems.scene_groups,
            update=CommonUpdaters.group_profile_updater
        )),
        ('color_profile_enum', EnumProperty(
            name="Color Profile",
            description=find_tooltip("color_profile_enum"),
            items=AlvaItems.color_profiles,
        )),
        ('alva_solo', BoolProperty(
            name="Solo",
            description=find_tooltip("solo"),
            update=CommonUpdaters.solo_updater
        )),
        ('freezing_mode_enum', EnumProperty(
            name="Freezing",
            description=find_tooltip("freezing_mode_enum"),
            items=AlvaItems.freezing_modes,
        )),
    ]

    common_parameters = [
        ('influence', IntProperty(
            default=1, description="", min=1, max=10)),
        ('alva_intensity', IntProperty(
            name="Intensity",
            default=0,
            min=0,
            max=100,
            description=find_tooltip("intensity"),
            options={'ANIMATABLE'},
            update=CPVGenerator.intensity_updater
        )),
        ('alva_color', FloatVectorProperty(
            name="Color",
            subtype='COLOR',
            size=3,
            default=(1.0, 1.0, 1.0),
            min=0.0,
            max=1.0,
            description=find_tooltip("color"),
            update=CPVGenerator.color_updater
        )),
        ('alva_pan', IntProperty(
            name="Pan",
            default=0,
            min=-100,
            max=100,
            description=find_tooltip("pan"),
            options={'ANIMATABLE'},
            update=CPVGenerator.pan_updater
        )),
        ('alva_tilt', IntProperty(
            name="Tilt",
            default=0,
            min=-100,
            max=100,
            description=find_tooltip("tilt"),
            options={'ANIMATABLE'},
            update=CPVGenerator.tilt_updater
        )),
        ('alva_zoom', IntProperty(
            name="Zoom",
            default=0,
            min=0,
            max=100,
            description=find_tooltip("zoom"),
            options={'ANIMATABLE'},
            update=CPVGenerator.zoom_updater
        )),
        ('alva_iris', IntProperty(
            name="Iris",
            default=100,
            min=0,
            max=100,
            description=find_tooltip("iris"),
            options={'ANIMATABLE'},
            update=CPVGenerator.iris_updater
        ))
    ]
        
    common_parameters_extended = [
        ('alva_color_restore', FloatVectorProperty(
            name="Color (restore)",
            subtype='COLOR',
            size=3,
            default=(1.0, 1.0, 1.0),
            min=0.0,
            max=1.0,
            description=find_tooltip("color_restore"),
        )),
        ('alva_volume', IntProperty(
            name="Volume",
            default=0,
            min=0,
            max=100,
            description=find_tooltip("volume"),
            options={'ANIMATABLE'}
        )),
        ('alva_diffusion', IntProperty(
            name="Diffusion",
            default=0,
            min=0,
            max=100,
            description=find_tooltip("diffusion"),
            options={'ANIMATABLE'},
            update=CPVGenerator.diffusion_updater
        )),
        ('alva_strobe', IntProperty(
            name="Strobe",
            default=0,
            min=0,
            max=100,
            description=find_tooltip("strobe"),
            options={'ANIMATABLE'},
            update=CPVGenerator.strobe_updater
        )),
        ('alva_edge', IntProperty(
            name="Edge",
            default=0,
            min=0,
            max=100,
            description=find_tooltip("edge"),
            options={'ANIMATABLE'},
            update=CPVGenerator.edge_updater
        )),
        ('alva_gobo', IntProperty(
            name="Gobo ID",
            default=1,
            min=0,
            max=20,
            description=find_tooltip("gobo"),
            options={'ANIMATABLE'},
            update=CPVGenerator.gobo_id_updater
        )),
        ('alva_gobo_speed', IntProperty(
            name="Speed",
            default=0,
            min=-100,
            max=100,
            description=find_tooltip("speed"),
            options={'ANIMATABLE'},
            update=CPVGenerator.gobo_speed_updater
        )),
        ('alva_prism', IntProperty(
            name="Prism",
            default=0,
            min=0,
            max=1,
            description=find_tooltip("prism"),
            options={'ANIMATABLE'},
            update=CPVGenerator.prism_updater
        ))
    ]
        
    mins_maxes = [
        ('strobe_min', IntProperty(
            name="Stobe Min", 
            default=0, 
            description=find_tooltip("strobe_min")
        )),
        ('strobe_max', IntProperty(
            name="Strobe Max", 
            default=20, 
            description=find_tooltip("strobe_max")
        )),
        ('alva_white_balance', FloatVectorProperty(
            name="White Balance",
            subtype='COLOR',
            size=3,
            default=(1.0, 1.0, 1.0),
            min=0.0,
            max=1.0,
            description=find_tooltip("white_balance"),
        )),
        ('pan_min', IntProperty(
            name="Pan Min", 
            default=-270, 
            description=find_tooltip("pan_min")
        )),
        ('pan_max', IntProperty(
            name="Pan Max", 
            default=270, 
            description=find_tooltip("pan_max")
        )),
        ('tilt_min', IntProperty(
            name="Tilt Min", 
            default=-135, 
            description=find_tooltip("tilt_min")
        )),
        ('tilt_max', IntProperty(
            name="Tilt Max", 
            default=135, 
            description=find_tooltip("tilt_max")
        )),
        ('zoom_min', IntProperty(
            name="Zoom Min", 
            default=1, 
            description=find_tooltip("zoom_min")
        )),
        ('zoom_max', IntProperty(
            name="Zoom Max", 
            default=100, 
            description=find_tooltip("zoom_max")
        )),
        ('gobo_speed_min', IntProperty(
            name="Gobo Rotation Speed Min", 
            default=-200, 
            description=find_tooltip("speed_min")
        )),
        ('gobo_speed_max', IntProperty(
            name="Gobo Rotation Speed Min", 
            default=200, 
            description=find_tooltip("speed_max")
        ))
    ]
        
    '''IMPORTANT: intensity_is_on MUST default to True for Event Manager to work.'''
    parameter_toggles = [
        ('intensity_is_on', BoolProperty(default=True)),
        ('audio_is_on', BoolProperty(name="Audio Toggle", default=False, description=find_tooltip("enable_audio"))),
        ('mic_is_linked', BoolProperty(name="Microphone Linking", default=False, description=find_tooltip("enable_microphone"))),
        ('pan_tilt_is_on', BoolProperty(name="Pan/Tilt Toggle", default=False, description=find_tooltip("enable_pan_tilt"))), 
        ('color_is_on', BoolProperty(name="Color Toggle", default=False, description=find_tooltip("enable_color"))),
        ('diffusion_is_on', BoolProperty(name="Diffusion Toggle", default=False, description=find_tooltip("enable_diffusion"))),
        ('strobe_is_on', BoolProperty(name="Strobe Toggle", default=False, description=find_tooltip("enable_strobe"))),
        ('zoom_is_on', BoolProperty(name="Zoom Toggle", default=False, description=find_tooltip("enable_zoom"))),
        ('iris_is_on', BoolProperty(name="Iris Toggle", default=False, description=find_tooltip("enable_iris"))),
        ('edge_is_on', BoolProperty(name="Edge Toggle", default=False, description=find_tooltip("enable_edge"))),
        ('gobo_is_on', BoolProperty(name="Gobo Toggle", default=False, description=find_tooltip("enable_gobo"))),
        ('prism_is_on', BoolProperty(name="Prism Toggle", default=False, description=find_tooltip("enable_prism"))),
    ]

    special_arguments = [
        ('str_enable_strobe_argument', StringProperty(
            name="Enable Strobe Argument", 
            default="# Strobe_Mode 127 Enter", 
            description=find_tooltip("simple_enable_disable_argument"))),
        
        ('str_disable_strobe_argument', StringProperty(
            name="Disable Strobe Argument", 
            default="# Strobe_Mode 76 Enter", 
            description=find_tooltip("simple_enable_disable_argument"))),
        
        ('str_enable_gobo_speed_argument', StringProperty(
            name="Enable Gobo Rotation Argument", 
            default="", 
            description=find_tooltip("simple_enable_disable_argument"))),
            
        ('str_disable_gobo_speed_argument', StringProperty(
            name="Disable Gobo Rotation Argument", 
            default="", 
            description=find_tooltip("simple_enable_disable_argument"))),
            
        ('str_gobo_id_argument', StringProperty(
            name="Select Gobo Argument", 
            default="# Gobo_Select $ Enter", 
            description=find_tooltip("gobo_argument"))),

        ('str_enable_prism_argument', StringProperty(
            name="Enable Prism Argument", 
            default="# Beam_Fx_Select 02 Enter", 
            description=find_tooltip("simple_enable_disable_argument"))),
            
        ('str_disable_prism_argument', StringProperty(
            name="Disable Prism Argument", 
            default="# Beam_Fx_Select 01 Enter", 
            description=find_tooltip("simple_enable_disable_argument"))),

        ('str_gobo_speed_value_argument', StringProperty(
            name="Gobo Speed Value Argument", 
            default="# Gobo_Index/Speed at $ Enter", 
            description=find_tooltip("gobo_argument")))
    ]

    timecode_executors = [
        ('str_parent_name', StringProperty(default="")), # Used by the find_executor algorithm for memory between iterations
         
        ('int_event_list', IntProperty(
            name="Event List", 
            min=0, 
            max=9999, 
            default=0, 
            description=find_tooltip("event_list"))),
        
        ('int_cue_list', IntProperty(
            name="Cue List", 
            min=0, max=999, 
            default=0, 
            description=find_tooltip("cue_list"))),
        
        ('str_start_cue', StringProperty(
            name="Start Cue", 
            default="1 / 1", 
            update=SequencerUpdaters.timecode_clock_update_safety, 
            description=find_tooltip("start_cue"))),
        
        ('str_end_cue', StringProperty(
            name="End Cue", 
            default="1 / 2", 
            update=SequencerUpdaters.timecode_clock_update_safety, 
            description=find_tooltip("end_cue"))),
        
        ('int_start_macro', IntProperty(
            name="Start Macro", 
            min=0,
            max=99999, 
            default=1, 
            description=find_tooltip("start_macro"))),
        
        ('int_end_macro', IntProperty(
            name="End Macro", 
            min=0, 
            max=99999, 
            default=0, 
            description=find_tooltip("end_macro"))),
        
        ('int_start_preset', IntProperty(
            name="Start Preset", 
            default=0, 
            min=0, 
            max=9999, 
            description=find_tooltip("start_preset"))),
        
        ('int_end_preset', IntProperty(
            name="End Preset", 
            default=0, 
            min=0, 
            max=9999, 
            description=find_tooltip("end_preset")))
    ]


def register():
    register_properties(
        Object, 
        *[
            CommonProperties.controller_ids,
            CommonProperties.object_only,  # Unique
            CommonProperties.common_header,
            CommonProperties.common_parameters,
            CommonProperties.common_parameters_extended,
            CommonProperties.mins_maxes,
            CommonProperties.parameter_toggles,
            CommonProperties.special_arguments
        ]
    )

    register_properties(
        Light, 
        *[
            CommonProperties.controller_ids,
            CommonProperties.common_header,
            CommonProperties.common_parameters,
            CommonProperties.common_parameters_extended,
            CommonProperties.mins_maxes,
            CommonProperties.parameter_toggles
        ]
    )

    # ColorSequence, excluding object_only
    register_properties(
        ColorSequence, 
        *[
            CommonProperties.controller_ids,
            CommonProperties.common_header,
            CommonProperties.common_parameters,
            CommonProperties.common_parameters_extended,
            CommonProperties.mins_maxes,
            CommonProperties.parameter_toggles,
            CommonProperties.special_arguments,
            CommonProperties.flash_strip_parameters  # Unique
        ]
    )

    # Sequence
    register_properties(Sequence, CommonProperties.timecode_executors)

    # Scene
    register_properties(Scene, CommonProperties.timecode_executors)


def unregister():
    register_properties(
        Object, 
        *[
            CommonProperties.object_only,

            CommonProperties.controller_ids,
            CommonProperties.common_header,
            CommonProperties.common_parameters,
            CommonProperties.common_parameters_extended,
            CommonProperties.mins_maxes,
            CommonProperties.parameter_toggles,
            CommonProperties.special_arguments
        ],
        register=False
    )

    register_properties(
        Light, 
        *[
            CommonProperties.controller_ids,
            CommonProperties.common_header,
            CommonProperties.common_parameters,
            CommonProperties.common_parameters_extended,
            CommonProperties.mins_maxes,
            CommonProperties.parameter_toggles
        ],
        register=False
    )

    # ColorSequence, excluding object_only
    register_properties(
        ColorSequence, 
        *[
            CommonProperties.controller_ids,
            CommonProperties.common_header,
            CommonProperties.common_parameters,
            CommonProperties.common_parameters_extended,
            CommonProperties.mins_maxes,
            CommonProperties.parameter_toggles,
            CommonProperties.special_arguments,

            CommonProperties.flash_strip_parameters
        ],
        register=False
    )

    # Sequence
    register_properties(Sequence, CommonProperties.timecode_executors, register=False)

    # Scene
    register_properties(Scene, CommonProperties.timecode_executors, register=False)  