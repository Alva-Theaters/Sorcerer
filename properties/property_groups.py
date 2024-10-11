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
from bpy.props import (FloatProperty, 
                    StringProperty, 
                    IntProperty, 
                    BoolProperty, 
                    CollectionProperty,
                    EnumProperty,
                    PointerProperty,
                    FloatVectorProperty)
from bpy.types import PropertyGroup, Sequence, Scene

from ..updaters.common_updaters import CommonUpdaters
from ..assets.tooltips import format_tooltip

# pyright: reportInvalidTypeForm=false


class Errors(PropertyGroup):
    error_type: StringProperty()
    explanation: StringProperty()
    severity: IntProperty()


class Cue(PropertyGroup):
    int_number: FloatProperty()  # Why is this named int when it's float?
    str_label: StringProperty() 
    is_live: BoolProperty() 
    

class CueLists(PropertyGroup):
    '''Drawn in the main '''
    from ..updaters.properties_updaters import PropertiesUpdaters

    cues: CollectionProperty(type=Cue) 
    int_preview_index: IntProperty(default=0)   
    int_program_index: IntProperty(default=1) 
    int_number: IntProperty() 
    int_t_bar: IntProperty(min=0, max=100, update=PropertiesUpdaters.fader_bar_updater) 
    int_velocity_multiplier: IntProperty(default=1)  
    t_bar_target: FloatProperty(default=100)  
    is_progressive: BoolProperty(name="Switching Mode", description="Progressive, indicated by forward arrow, means Preview advances to next cue after completed transition. Swap, indicated by opposing arrows, means Program and Preview will swap") 
    int_cue_list_number: IntProperty(name="Cue List", description=format_tooltip("Cue list for this song's cues on the console"), default=1)  


class ShowSequencer(PropertyGroup):
    '''All the properties for the show start sequencer, basically a rocket launch
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
    from ..updaters.common_updaters import CommonUpdaters

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


class AudioObjectSettings(PropertyGroup):
    from ..assets.items import Items as AlvaItems
    audio_type_enum:  EnumProperty(
        items=AlvaItems.get_audio_object_items,
        name="Audio Types",
        description="Choose what the strip should do",
        default=1
    ) 


class MySettings(PropertyGroup):
    from ..assets.items import Items as AlvaItems
    from ..updaters.sequencer_updaters import SequencerUpdaters 

    motif_type_enum:  EnumProperty(
        items=AlvaItems.enum_items,
        name="Motif Types",
        description="Choose motif type",
        update=SequencerUpdaters.motif_type_enum_updater,
        default=1
    ) 
    
    
class RaiseChannels(PropertyGroup):
    chan: PointerProperty(type=bpy.types.Object) 
    original_influence: FloatProperty()  
    original_influence_color: FloatVectorProperty() 
    
        
class InfluencerList(PropertyGroup):
    parameter: StringProperty() 
    raise_channels: CollectionProperty(type=RaiseChannels)
    
    
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
    from ..updaters.node_updaters import NodeUpdaters
    constant_index: IntProperty(name="Index", description="Number of the item on the console", update=NodeUpdaters.constant_index_updater) 


class MixerParameters(PropertyGroup):
    node_tree_pointer: PointerProperty(
        name="Node Tree Pointer",
        type=bpy.types.NodeTree,
        description="Pointer to the node tree"
    ) 
    node_name: StringProperty(
        name="Node Name",
        description="Name of the node"
    ) 

    # Common property registrations in register() section.


class MacroButtonItem(PropertyGroup):
    name: StringProperty() 

        
prop_groups = [
    Errors,
    Cue,
    CueLists,
    ShowSequencer,
    ChannelsList,
    GroupData,
    AudioObjectSettings,
    MySettings,
    RaiseChannels,
    InfluencerList,
    LightingModifier,
    CustomButtonPropertyGroup,
    MixerParameters,
    MacroButtonItem
]


def register():
    for cls in prop_groups:
        bpy.utils.register_class(cls)

    from ..utils.properties_utils import register_properties
    from .common_properties import CommonProperties
    register_properties(MixerParameters, CommonProperties.common_parameters)
    register_properties(GroupData, CommonProperties.mins_maxes)
    register_properties(GroupData, CommonProperties.special_arguments)
    register_properties(GroupData, CommonProperties.parameter_toggles)

    # This stuff has to be here for the start sequence to work.
    if not hasattr(Sequence, "my_settings"):
        Sequence.my_settings = PointerProperty(type=MySettings)
        
    Scene.channels_list_pg = PointerProperty(type=ChannelsList)
    Scene.show_sequencer = PointerProperty(type=ShowSequencer)
        
    # Need to cross-register this
    Scene.scene_group_data = CollectionProperty(type=GroupData)
    Scene.cue_lists = CollectionProperty(type=CueLists)

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
    
    from ..utils.properties_utils import register_properties
    from .common_properties import CommonProperties
    register_properties(MixerParameters, CommonProperties.common_parameters, register=False)
    register_properties(GroupData, CommonProperties.mins_maxes, register=False)
    register_properties(GroupData, CommonProperties.special_arguments, register=False)
    register_properties(GroupData, CommonProperties.parameter_toggles, register=False)

    for cls in reversed(prop_groups):
        bpy.utils.unregister_class(cls)