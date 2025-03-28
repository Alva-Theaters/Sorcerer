# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.props import (FloatProperty, 
                    StringProperty, 
                    IntProperty, 
                    BoolProperty, 
                    CollectionProperty,
                    EnumProperty,
                    PointerProperty,
                    FloatVectorProperty)
from bpy.types import PropertyGroup, Sequence, Scene

from ..updaters.common import CommonUpdaters
from ..assets.tooltips import format_tooltip

# pyright: reportInvalidTypeForm=false


class COMMON_PG_alva_maintenance_errors(PropertyGroup):
    error_type: StringProperty()
    explanation: StringProperty()
    severity: IntProperty()


class PROPERTIES_PG_alva_cue_switcher_cue(PropertyGroup):
    int_number: FloatProperty()  # Why is this named int when it's float?
    str_label: StringProperty() 
    is_live: BoolProperty() 
    

class PROPERTIES_PG_alva_cue_lists(PropertyGroup):
    from ..updaters.properties import PropertiesUpdaters

    cues: CollectionProperty(type=PROPERTIES_PG_alva_cue_switcher_cue) 
    int_preview_index: IntProperty(default=0)   
    int_program_index: IntProperty(default=1) 
    int_number: IntProperty() 
    int_t_bar: IntProperty(min=0, max=100, update=PropertiesUpdaters.fader_bar_updater) 
    int_velocity_multiplier: IntProperty(default=1)  
    t_bar_target: FloatProperty(default=100)  
    is_progressive: BoolProperty(name="Switching Mode", description="Progressive, indicated by forward arrow, means Preview advances to next cue after completed transition. Swap, indicated by opposing arrows, means Program and Preview will swap") 
    int_cue_list_number: IntProperty(name="Cue List", description=format_tooltip("Cue list for this song's cues on the console"), default=1)  


class PROPERTIES_PG_alva_stage_manager(PropertyGroup):
    '''All the properties for the Stage Manager, which is basically a rocket launch
       go-no-go poll UI for stage managers to ensure shows start with everything 
       completed properly and on time.'''
    from ..assets.items import Items as AlvaItems

    # Open lobby poll
    open_lobby_poll_time: StringProperty(name="Lobby Time") 
    all_members_present: BoolProperty(name="Attendance Check") 
    stage_is_set: BoolProperty(name="Set Check")  
    cleaning_is_complete: BoolProperty(name="Cleaning Check") 
    fly_is_set: BoolProperty(name="Fly is Set") 
    go_for_lobby_open: BoolProperty(name="Lobby May Open") 
    
    # Open house poll
    open_house_poll_time: StringProperty(name="House Time") 
    set_pieces_are_set: BoolProperty(name="Set pieces set?") 
    props_are_set: BoolProperty(name="Props set?") 
    lights_are_tested: BoolProperty(name="Lights tested?") 
    sound_is_checked: BoolProperty(name="Sound checked?") 
    warmups_is_complete: BoolProperty(name="Warm-ups complete?") 
    stage_is_clear_of_props: BoolProperty(name="Props clear of stage?") 
    spotlights_are_tested: BoolProperty(name="Spotlights tested?") 
    house_manager_is_go_one: BoolProperty(name="House Manager?") 
    go_for_house_open: BoolProperty(name="Go for House Open", description="At this time, cast members may not be seen. All members, the stage is now hot, please set all remaining elements in show-open configuration") 

    # Final go/no-go poll
    go_no_go_poll_time: StringProperty(name="Final Go/No-Go Poll Time") 
    fly_is_go: BoolProperty(name="Fly?") 
    sound_is_go: BoolProperty(name="Sound?") 
    lights_is_go: BoolProperty(name="Lights?") 
    projections_is_go: BoolProperty(name="Projections?") 
    show_support_is_go: BoolProperty(name="Show Support?") 
    backstage_manager: BoolProperty(name="Backstage Manager?") 
    house_manager_is_go: BoolProperty(name="House Manager?") 
    go_for_show_open: BoolProperty(name="Go for Show Open", description='If any reason to hold the show arises, announce, "Hold, hold, hold", and state the reason for the hold over coms') 

    # Status Check
    status_check_time: StringProperty(name="Status Check Time") 
    initial_cast_in_place: BoolProperty(name="Initial Cast") 
    control_booth_is_ready: BoolProperty(name="Control Booth") 
    theater_is_ready: BoolProperty(name="Theater") 
    clear_to_proceed: BoolProperty(name="Clear to proceed with count") 

    # Non-normal conditions
    hold: BoolProperty(name="Hold, hold, hold") 
    
    # Technical anomalies
    rigging_anomaly: BoolProperty(name="Rigging Anomaly") 
    sound_anomaly: BoolProperty(name="Sound Anomaly") 
    lighting_anomaly: BoolProperty(name="Lighting Anomaly") 
    projection_anomaly: BoolProperty(name="Projection Anomaly") 
    support_systems_anomaly: BoolProperty(name="Support Systems Anomaly") 
        
    # Misc. anomalies
    medical_anomaly: BoolProperty(name="Medical Anomaly") 
    police_activity: BoolProperty(name="Police Activity") 
    missing_person: BoolProperty(name="Missing Person") 
    weather_anomaly: BoolProperty(name="Weather Anomaly")  
    shelter_in_place: BoolProperty(name="Shelter in Place") 
    
    # Human deviations
    cast_deviation: BoolProperty(name="Cast Deviation") 
    crew_deviation: BoolProperty(name="Crew Deviation") 
    audience_deviation: BoolProperty(name="Audience Deviation") 
        
    # Emergency conditions
    emergency: BoolProperty(name="General Emergency") 
    fire: BoolProperty(name="Fire, fire, fire") 
    evacuate: BoolProperty(name="Evacuate, evacuate, evacuate") 
    fire_curtain: BoolProperty(name="Fire curtain, fire curtain, fire curtain") 
    bomb: BoolProperty(name="Bomb, bomb, bomb")  
    
    sequence_status_enum: EnumProperty(
        name="Sequence Status",
        description="Position in nominal sequence",
        items=AlvaItems.sequence_steps  
    )
    flags_enum: EnumProperty(
        name="Sequence Status",
        description="Position in nominal sequence",
        items=AlvaItems.flags
    )  
    
       
class ChannelsList(PropertyGroup):
    '''Used by GroupData to store multiple channels.'''
    chan: IntProperty() 
        

class GroupData(PropertyGroup):
    '''This stores properties for Fixture Groups panel, used via selected_group_enum
       in the controllers at the top'''
    from ..assets.items import Items as AlvaItems
    from ..updaters.common import CommonUpdaters

    name: StringProperty(name="Group Name", default="New Group", update=CommonUpdaters.group_name_updater) 
    channels_list: CollectionProperty(type=ChannelsList) 
    int_group_id: IntProperty(name="ID #", description="Group's number on the console") 

    show_in_presets_node: BoolProperty(name="Hide", description="Hide this when settings are hidden", default=True)

    separator: BoolProperty(name="Separate", default=False, description='Use this to separate groups', update=CommonUpdaters.ui_list_separator_updater) 
    label: BoolProperty(name="Label", default=False, description='Use this to label groups of groups', update=CommonUpdaters.ui_list_label_updater) 

    highlight_or_remove_enum: EnumProperty(
        name="Highlight or Remove",
        description="Choose whether to use this to briefly highlight fixtures or to remove fixtures from the group",
        items=AlvaItems.highlight_or_remove,
        default=0
    ) 
    color_profile_enum: EnumProperty(
        name="Color Profile",
        description="Choose a color profile for the group",
        items=AlvaItems.color_profiles
    ) 
    
    # Others registered in register section


class MySettings(PropertyGroup):
    from ..assets.items import Items as AlvaItems
    from ..updaters.sequencer import SequencerUpdaters 

    motif_type_enum:  EnumProperty(
        items=AlvaItems.strip_types,
        name="Motif Types",
        description="Choose strip type",
        update=SequencerUpdaters.motif_type_enum_updater,
        default=1
    ) 
    
    
class VIEW3D_PG_alva_influenced_object_property_group(PropertyGroup):
    channel_object: PointerProperty(type=bpy.types.Object) 
    current_influence: FloatProperty()  
    current_influence_color: FloatVectorProperty() 
    
        
class VIEW3D_PG_alva_influencer_property_group(PropertyGroup):
    parameter_name: StringProperty()
    influenced_object_property_group: CollectionProperty(type=VIEW3D_PG_alva_influenced_object_property_group)
    
    
class LightingModifier(PropertyGroup):
    name: StringProperty(name="Name", default="Lighting Modifier") 
    show_expanded: BoolProperty(name="Show Expanded", default=True) 
    mute: BoolProperty(name="Mute", default=False) 
    type: EnumProperty(
        name="Type",
        description="Type of lighting modifier",
        items = [
            ('option_brightness_contrast', "Brightness/Contrast", "Adjust overall brightness and contrast of the entire rig's intensity values"),
            ('option_saturation', "Saturation", "Adjust overall saturation of entire rig"),
            ('option_hue', "Hue", "Adjust the saturation of individual hues across the entire rig"),
            ('option_curves', "Curves", "Adjust overall brightness and contrast of entire rig's intensity values")
        ]
    ) 
    brightness: IntProperty(name="Brightness", default=0, min = -100, max = 100, description="Adjust overall brightness of the entire rig's intensity values") 
    contrast: IntProperty(name="Contrast", default=0, min = -100, max = 100, description="Adjust the difference between the brightest lights and the darkest lights") 
    saturation: IntProperty(name="Saturation", default=0, min = -100, max = 100, description="Adjust overall saturation of the entire rig") 
    
    highlights: IntProperty(name="Highlights", default=0, min = -100, max = 100, description="") 
    shadows: IntProperty(name="Shadows", default=0, min = -100, max = 100, description="")  
    whites: IntProperty(name="Whites", default=0, min = -100, max = 100, description="")  
    blacks: IntProperty(name="Blacks", default=0, min = -100, max = 100, description="") 
    
    reds: IntProperty(name="Reds", default=0, min = -100, max = 100, description="")  
    greens: IntProperty(name="Greens", default=0, min = -100, max = 100, description="") 
    blues: IntProperty(name="Blues", default=0, min = -100, max = 100, description="") 


class CustomButtonPropertyGroup(PropertyGroup):
    button_label: StringProperty(name="Label", default="Button Label")  
    button_address: StringProperty(default="/eos/cmd") 
    button_argument: StringProperty(default="") 
    from ..updaters.node import NodeUpdaters
    constant_index: IntProperty(name="Index", description="Number of the item on the console", update=NodeUpdaters.constant_index_updater) 


class MixerParameters(PropertyGroup):
    node_tree_name: StringProperty(
        name="Node Tree Name",
        description="Name of the node tree"
    ) 
    node_name: StringProperty(
        name="Node Name",
        description="Name of the node"
    ) 

    # Common property registrations in register() section.


class VIEW3D_PG_alva_speakers(PropertyGroup):
    speaker_number: IntProperty()  # Stores the int_speaker_number of associated speaker
    speaker_name: StringProperty()
    dummy_volume: FloatProperty(min=0, max=1)  # Stores the panned volume level data for this strip/speaker pair
    speaker_pointer: PointerProperty(type=bpy.types.Object)


class VIEW3D_PG_alva_speaker_list(PropertyGroup):  # Registered to mesh objects
    name: StringProperty()  # Stores the name of the associated sound strip from sequencer
    speakers: CollectionProperty(type=VIEW3D_PG_alva_speakers)  # List of all speakers in 3D scene


class MacroButtonItem(PropertyGroup):
    name: StringProperty() 

        
prop_groups = [
    COMMON_PG_alva_maintenance_errors,
    PROPERTIES_PG_alva_cue_switcher_cue,
    PROPERTIES_PG_alva_cue_lists,
    PROPERTIES_PG_alva_stage_manager,
    ChannelsList,
    GroupData,
    MySettings,
    VIEW3D_PG_alva_influenced_object_property_group,
    VIEW3D_PG_alva_influencer_property_group,
    LightingModifier,
    CustomButtonPropertyGroup,
    MixerParameters,
    VIEW3D_PG_alva_speakers,
    VIEW3D_PG_alva_speaker_list,
    MacroButtonItem
]


def register():
    for cls in prop_groups:
        bpy.utils.register_class(cls)

    from ..utils.rna_utils import register_properties
    from .rna_common import CommonProperties
    register_properties(GroupData, CommonProperties.mins_maxes)
    register_properties(GroupData, CommonProperties.special_arguments)
    register_properties(GroupData, CommonProperties.parameter_toggles)

    # This stuff has to be here for the start sequence to work.
    if not hasattr(Sequence, "my_settings"):
        Sequence.my_settings = PointerProperty(type=MySettings)
        
    Scene.channels_list_pg = PointerProperty(type=ChannelsList)
    Scene.show_sequencer = PointerProperty(type=PROPERTIES_PG_alva_stage_manager)
        
    # Need to cross-register this
    Scene.scene_group_data = CollectionProperty(type=GroupData)
    Scene.cue_lists = CollectionProperty(type=PROPERTIES_PG_alva_cue_lists)

    Scene.macro_buttons = CollectionProperty(type=MacroButtonItem)
    Scene.macro_buttons_index = IntProperty(update=CommonUpdaters.update_macro_buttons_index)
    

def unregister():
    if hasattr(Scene, "macro_buttons"):
        del Scene.macro_buttons
    if hasattr(Scene, "macro_buttons_index"):
        del Scene.macro_buttons_index
    if hasattr(Sequence, "my_settings"):
        del Sequence.my_settings

    if hasattr(Scene, "cue_lists"):
        del Scene.cue_lists
    if hasattr(Scene, "scene_group_data"):
        del Scene.scene_group_data
    if hasattr(Scene, "show_sequencer"):
        del Scene.show_sequencer
    if hasattr(Scene, "channels_list_pg"):
        del Scene.channels_list_pg
    
    from ..utils.rna_utils import register_properties
    from .rna_common import CommonProperties
    register_properties(GroupData, CommonProperties.mins_maxes, register=False)
    register_properties(GroupData, CommonProperties.special_arguments, register=False)
    register_properties(GroupData, CommonProperties.parameter_toggles, register=False)

    for cls in reversed(prop_groups):
        bpy.utils.unregister_class(cls)