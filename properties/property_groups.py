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


class Cue(PropertyGroup):
    int_number: FloatProperty() # type: ignore # Why is this named int when it's float?
    str_label: StringProperty() # type: ignore
    is_live: BoolProperty() # type: ignore
    

class CueLists(PropertyGroup):
    '''Drawn in the main '''
    from ..updaters.properties_updaters import PropertiesUpdaters

    cues: CollectionProperty(type=Cue) # type: ignore
    int_preview_index: IntProperty(default=0)   # type: ignore
    int_program_index: IntProperty(default=1) # type: ignore
    int_number: IntProperty() # type: ignore
    int_t_bar: IntProperty(min=0, max=100, update=PropertiesUpdaters.fader_bar_updater) # type: ignore
    int_velocity_multiplier: IntProperty(default=1) # type: ignore # type: ignore
    t_bar_target: FloatProperty(default=100) # type: ignore # type: ignore
    is_progressive: BoolProperty(name="Switching Mode", description="Progressive, indicated by forward arrow, means Preview advances to next cue after completed transition. Swap, indicated by opposing arrows, means Program and Preview will swap") # type: ignore
    int_cue_list_number: IntProperty(name="Cue List", description="Cue list for this song's cues on the console", default=1) # type: ignore # type: ignore


class ShowSequencer(PropertyGroup):
    '''All the properties for the show start sequencer, basically a rocket launch
       go-no-go poll UI for stage managers to ensure shows start with everything 
       completed properly and on time.'''
    from ..assets.items import Items as AlvaItems

    # Open lobby poll
    open_lobby_poll_time: StringProperty(name="Lobby Time") # type: ignore
    all_members_present: BoolProperty(name="Attendance Check") # type: ignore
    stage_is_set: BoolProperty(name="Set Check") # type: ignore # type: ignore
    cleaning_is_complete: BoolProperty(name="Cleaning Check") # type: ignore
    fly_is_set: BoolProperty(name="Fly is Set") # type: ignore
    go_for_lobby_open: BoolProperty(name="Lobby May Open") # type: ignore
    
    # Open house poll
    open_house_poll_time: StringProperty(name="House Time") # type: ignore
    set_pieces_are_set: BoolProperty(name="Set pieces set?") # type: ignore
    props_are_set: BoolProperty(name="Props set?") # type: ignore
    lights_are_tested: BoolProperty(name="Lights tested?") # type: ignore
    sound_is_checked: BoolProperty(name="Sound checked?") # type: ignore
    warmups_is_complete: BoolProperty(name="Warm-ups complete?") # type: ignore
    stage_is_clear_of_props: BoolProperty(name="Props clear of stage?") # type: ignore
    spotlights_are_tested: BoolProperty(name="Spotlights tested?") # type: ignore
    house_manager_is_go_one: BoolProperty(name="House Manager?") # type: ignore
    go_for_house_open: BoolProperty(name="Go for House Open", description="At this time, cast members may not be seen. All members, the stage is now hot, please set all remaining elements in show-open configuration") # type: ignore

    # Final go/no-go poll
    go_no_go_poll_time: StringProperty(name="Final Go/No-Go Poll Time") # type: ignore
    fly_is_go: BoolProperty(name="Fly?") # type: ignore
    sound_is_go: BoolProperty(name="Sound?") # type: ignore
    lights_is_go: BoolProperty(name="Lights?") # type: ignore
    projections_is_go: BoolProperty(name="Projections?") # type: ignore
    show_support_is_go: BoolProperty(name="Show Support?") # type: ignore
    backstage_manager: BoolProperty(name="Backstage Manager?") # type: ignore
    house_manager_is_go: BoolProperty(name="House Manager?") # type: ignore
    go_for_show_open: BoolProperty(name="Go for Show Open", description='If any reason to hold the show arises, announce, "Hold, hold, hold", and state the reason for the hold over coms') # type: ignore

    # Status Check
    status_check_time: StringProperty(name="Status Check Time") # type: ignore
    initial_cast_in_place: BoolProperty(name="Initial Cast") # type: ignore
    control_booth_is_ready: BoolProperty(name="Control Booth") # type: ignore
    theater_is_ready: BoolProperty(name="Theater") # type: ignore
    clear_to_proceed: BoolProperty(name="Clear to proceed with count") # type: ignore

    # Non-normal conditions
    hold: BoolProperty(name="Hold, hold, hold") # type: ignore
    
    # Technical anomalies
    rigging_anomaly: BoolProperty(name="Rigging Anomaly") # type: ignore
    sound_anomaly: BoolProperty(name="Sound Anomaly") # type: ignore
    lighting_anomaly: BoolProperty(name="Lighting Anomaly") # type: ignore
    projection_anomaly: BoolProperty(name="Projection Anomaly") # type: ignore
    support_systems_anomaly: BoolProperty(name="Support Systems Anomaly") # type: ignore
        
    # Misc. anomalies
    medical_anomaly: BoolProperty(name="Medical Anomaly") # type: ignore
    police_activity: BoolProperty(name="Police Activity") # type: ignore
    missing_person: BoolProperty(name="Missing Person") # type: ignore
    weather_anomaly: BoolProperty(name="Weather Anomaly") # type: ignore # type: ignore
    shelter_in_place: BoolProperty(name="Shelter in Place") # type: ignore
    
    # Human deviations
    cast_deviation: BoolProperty(name="Cast Deviation") # type: ignore
    crew_deviation: BoolProperty(name="Crew Deviation") # type: ignore
    audience_deviation: BoolProperty(name="Audience Deviation") # type: ignore
        
    # Emergency conditions
    emergency: BoolProperty(name="General Emergency") # type: ignore
    fire: BoolProperty(name="Fire, fire, fire") # type: ignore
    evacuate: BoolProperty(name="Evacuate, evacuate, evacuate") # type: ignore
    fire_curtain: BoolProperty(name="Fire curtain, fire curtain, fire curtain") # type: ignore
    bomb: BoolProperty(name="Bomb, bomb, bomb") # type: ignore # type: ignore
    
    sequence_status_enum: EnumProperty(
        name="Sequence Status",
        description="Position in nominal sequence",
        items=AlvaItems.sequence_steps # type: ignore # type: ignore
    )
    flags_enum: EnumProperty(
        name="Sequence Status",
        description="Position in nominal sequence",
        items=AlvaItems.flags
    ) # type: ignore # type: ignore
    
       
class ChannelsList(PropertyGroup):
    '''Used by GroupData to store multiple channels.'''
    chan: IntProperty() # type: ignore
        

class GroupData(PropertyGroup):
    '''This stores properties for Fixture Groups panel, used via selected_group_enum
       in the controllers at the top'''
    from ..assets.items import Items as AlvaItems
    from ..updaters.common_updaters import CommonUpdaters

    name: StringProperty(name="Group Name", default="New Group", update=CommonUpdaters.group_name_updater) # type: ignore
    channels_list: CollectionProperty(type=ChannelsList) # type: ignore
    int_group_id: IntProperty(name="ID #", description="Group's number on the console") # type: ignore

    separator: BoolProperty(name="Separate", default=False, description='Use this to separate groups', update=CommonUpdaters.ui_list_separator_updater) # type: ignore
    label: BoolProperty(name="Label", default=False, description='Use this to label groups of groups', update=CommonUpdaters.ui_list_label_updater) # type: ignore

    highlight_or_remove_enum: EnumProperty(
        name="Highlight or Remove",
        description="Choose whether to use this to briefly highlight fixtures or to remove fixtures from the group",
        items=AlvaItems.highlight_or_remove,
        default=1
    ) # type: ignore
    color_profile_enum: EnumProperty(
        name="Color Profile",
        description="Choose a color profile for the group",
        items=AlvaItems.color_profiles
    ) # type: ignore
    
    # Others registered in register section
    

class AudioObjectSettings(PropertyGroup):
    from ..assets.items import Items as AlvaItems
    audio_type_enum:  EnumProperty(
        items=AlvaItems.get_audio_object_items,
        name="Audio Types",
        description="Choose what the strip should do",
        default=1
    ) # type: ignore


class MySettings(PropertyGroup):
    from ..assets.items import Items as AlvaItems
    from ..updaters.sequencer_updaters import SequencerUpdaters # type: ignore

    motif_type_enum:  EnumProperty(
        items=AlvaItems.enum_items,
        name="Motif Types",
        description="Choose motif type",
        update=SequencerUpdaters.motif_type_enum_updater,
        default=1
    ) # type: ignore
    
    
class MyMotifs(PropertyGroup):
    from ..assets.items import Items as AlvaItems
    from ..updaters.sequencer_updaters import SequencerUpdaters # type: ignore

    motif_names_enum: EnumProperty(
        name="",
        description="List of unique motif names",
        items=AlvaItems.get_motif_name_items,
        update=SequencerUpdaters.motif_names_updater
    ) # type: ignore
    
    
class RaiseChannels(PropertyGroup):
    chan: PointerProperty(type=bpy.types.Object) # type: ignore
    original_influence: FloatProperty() # type: ignore # type: ignore
    original_influence_color: FloatVectorProperty() # type: ignore
    
        
class InfluencerList(PropertyGroup):
    parameter: StringProperty() # type: ignore
    raise_channels: CollectionProperty(type=RaiseChannels) # type: ignore
    
    
class LightingModifier(PropertyGroup):
    name: StringProperty(name="Name", default="Lighting Modifier") # type: ignore
    show_expanded: BoolProperty(name="Show Expanded", default=True) # type: ignore
    mute: BoolProperty(name="Mute", default=False) # type: ignore
    type: EnumProperty(
        name="Type",
        description="Type of lighting modifier",
        items = [
            ('option_brightness_contrast', "Brightness/Contrast", "Adjust overall brightness and contrast of the entire rig's intensity values"),
            ('option_saturation', "Saturation", "Adjust overall saturation of entire rig"),
            ('option_hue', "Hue", "Adjust the saturation of individual hues across the entire rig"),
            ('option_curves', "Curves", "Adjust overall brightness and contrast of entire rig's intensity values")
        ]
    ) # type: ignore
    brightness: IntProperty(name="Brightness", default=0, min = -100, max = 100, description="Adjust overall brightness of the entire rig's intensity values") # type: ignore
    contrast: IntProperty(name="Contrast", default=0, min = -100, max = 100, description="Adjust the difference between the brightest lights and the darkest lights") # type: ignore
    saturation: IntProperty(name="Saturation", default=0, min = -100, max = 100, description="Adjust overall saturation of the entire rig") # type: ignore
    
    highlights: IntProperty(name="Highlights", default=0, min = -100, max = 100, description="") # type: ignore
    shadows: IntProperty(name="Shadows", default=0, min = -100, max = 100, description="") # type: ignore # type: ignore
    whites: IntProperty(name="Whites", default=0, min = -100, max = 100, description="") # type: ignore # type: ignore
    blacks: IntProperty(name="Blacks", default=0, min = -100, max = 100, description="") # type: ignore
    
    reds: IntProperty(name="Reds", default=0, min = -100, max = 100, description="") # type: ignore # type: ignore
    greens: IntProperty(name="Greens", default=0, min = -100, max = 100, description="") # type: ignore
    blues: IntProperty(name="Blues", default=0, min = -100, max = 100, description="") # type: ignore


class CustomButtonPropertyGroup(PropertyGroup):
    button_label: StringProperty(name="Label", default="Button Label") # type: ignore # type: ignore
    button_address: StringProperty(default="/eos/cmd") # type: ignore
    button_argument: StringProperty(default="") # type: ignore
    from ..updaters.node_updaters import NodeUpdaters
    constant_index: IntProperty(name="Index", description="Number of the item on the console", update=NodeUpdaters.constant_index_updater) # type: ignore


class MixerParameters(PropertyGroup):
    node_tree_pointer: PointerProperty(
        name="Node Tree Pointer",
        type=bpy.types.NodeTree,
        description="Pointer to the node tree"
    ) # type: ignore
    node_name: StringProperty(
        name="Node Name",
        description="Name of the node"
    ) # type: ignore

    # Common property registrations in register() section.


class MacroButtonItem(PropertyGroup):
    name: StringProperty() # type: ignore

        
prop_groups = [
    Cue,
    CueLists,
    ShowSequencer,
    ChannelsList,
    GroupData,
    AudioObjectSettings,
    MySettings,
    MyMotifs,
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

    from ..utils.utils import Utils
    from .common_properties import CommonProperties
    Utils.register_properties(MixerParameters, CommonProperties.common_parameters)
    Utils.register_properties(GroupData, CommonProperties.mins_maxes)
    Utils.register_properties(GroupData, CommonProperties.special_arguments)
    Utils.register_properties(GroupData, CommonProperties.parameter_toggles)

    # This stuff has to be here for the start sequence to work.
    if not hasattr(Sequence, "my_settings"):
        Sequence.my_settings = PointerProperty(type=MySettings)
    if not hasattr(Scene, "my_tool"):
        Scene.my_tool = PointerProperty(type=MyMotifs)
        
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
    if hasattr(Scene, "my_tool"):
        del Scene.my_tool
    
    from ..utils.utils import Utils
    from .common_properties import CommonProperties
    Utils.register_properties(MixerParameters, CommonProperties.common_parameters, register=False)
    Utils.register_properties(GroupData, CommonProperties.mins_maxes, register=False)
    Utils.register_properties(GroupData, CommonProperties.special_arguments, register=False)
    Utils.register_properties(GroupData, CommonProperties.parameter_toggles, register=False)

    for cls in reversed(prop_groups):
        bpy.utils.unregister_class(cls)