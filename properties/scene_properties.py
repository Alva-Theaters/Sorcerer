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
from bpy.props import IntProperty, StringProperty, BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty, PointerProperty, CollectionProperty
from bpy.types import PropertyGroup, Scene

from ..updaters.common_updaters import CommonUpdaters # type: ignore
from ..updaters.properties_updaters import PropertiesUpdaters # type: ignore
from ..utils.utils import Utils # type: ignore
from ..properties.common_properties import CommonProperties # type: ignore
from ..assets.items import Items as AlvaItems # type: ignore


LightingModifierSubClass = Utils.find_subclass_by_name(PropertyGroup, "LightingModifier")

class SceneProperties(PropertyGroup):
    group_data_index: IntProperty(name="Index", default=0, update=CommonUpdaters.highlight_mode_updater) # type: ignore
    expand_toggles: BoolProperty(name="Parameter toggle position", default=True, description="Choose whether to draw the toggles beside group name or off to the side") # type: ignore

    add_channel_ids: StringProperty(name="Add channel ID's", update=CommonUpdaters.channel_ids_updater)     # type: ignore
    
    view3d_command_line: StringProperty(name="Lighting Console Command Line", default="", update=CommonUpdaters.view3d_cmd_line_updater) # type: ignore

    str_osc_ip_address: StringProperty(default="192.168.1.1", description="This should be the IP address of the console. This must set for anything to work. Press the About key on the console to find the console's IP address. Console must be on same local network", update=CommonUpdaters.network_settings_updater) # type: ignore
    int_osc_port: IntProperty(min=0, max=65535, description="On the console, Displays > Setup > System Settings > Show Control > OSC > (enable OSC RX and make the port number there on the left match the one in this field in Alva. OSC TX = transmit and OSC RX = receive. We want receive", default=8000, update=CommonUpdaters.network_settings_updater) # type: ignore
    string_osc_receive_port: IntProperty(min=0, max=65535) # type: ignore
    
    str_record_cue: StringProperty(default="Record Cue # Time $ Enter Enter", description="Write command line syntax for recording cue # with duration $. # and $ are filled in by Orb as cue number and duration, respectively") # type: ignore
    str_create_all_events: StringProperty(default="Event 1 / 1 Thru # Enter", description="Write command line syntax to initialize all events. Orb will replace # with the final event number based on the sequencer's end frame") # type: ignore
    str_setup_event: StringProperty(default="Event 1 / # Time $ Show_Control_Action Cue # Enter", description="Write command line syntax to setup each event. # is frame/cue and $ is timecode") # type: ignore
    str_bake_info: StringProperty(default="Bake Animation to Cues (to Qmeo)") # type: ignore
    str_event_bake_info: StringProperty(default="Just Events")  # type: ignore
    str_cue_bake_info: StringProperty(default="Just Cues")  # type: ignore
    selected_text_block_name: StringProperty() # type: ignore

    preferences_enum: EnumProperty(
        name="Preferences",
        description="",
        items=AlvaItems.preferences # type: ignore
    )
    
    is_playing: BoolProperty(
        default=False, description="Tells harmonizer publisher if an update is associated with playback") # type: ignore
        
    in_frame_change: BoolProperty(
        default=False, description="Tells harmonizer publisher if an update is associated with a single frame change. Allows harmonization during manual frame changes") # type: ignore # type: ignore
        
    is_democratic: BoolProperty(
        default=False, description="This is a democracy. When different controllers try to change the same channel parameter, their Influence parameter gives them votes in a weighted average") # type: ignore # type: ignore
    
    is_not_democratic: BoolProperty(
        default=True, description="This isn't a democracy anymore. When different controllers try to change the same channel parameter, the strongest completely erases everyone else's opinion") # type: ignore # type: ignore

    console_type_enum: EnumProperty(
        name="Lighting Console Type",
        description="Select the type of 3rd party lighting console you wish to commandeer with Sorcerer",
        items=AlvaItems.console_types
    ) # type: ignore # type: ignore
    
    mixer_type_enum: EnumProperty(
        name="Audio Mixer Type",
        description="Select the type of 3rd party audio mixer you wish to commandeer with Sorcerer",
        items=AlvaItems.mixer_types
    ) # type: ignore # type: ignore
    
    core_type_enum: EnumProperty(
        name="Theater Type",
        description="Select the model theater",
        items=AlvaItems.core_types
    ) # type: ignore

    core_drives_enum: EnumProperty(
        name="Theater Drive",
        description="Select the drive you will use to transport DTP assets to the core",
        items=AlvaItems.core_drives
    ) # type: ignore
    
    str_core_ip_address: StringProperty(name="Theater IP Address", default="") # type: ignore
    
    int_core_port: IntProperty(name="Theater Port", default=0) # type: ignore # type: ignore
    
    int_argument_size: IntProperty(name="Maximum Argument Size", default=40, min=1, max=65, description="How many consecutive command line commands can be added to one OSC packet.") # type: ignore

    is_baking: BoolProperty(default=False, description="Sorcerer is currently baking") # type: ignore # type: ignore
    
    is_cue_baking: BoolProperty(default=False, description="Sorcerer is currently baking") # type: ignore # type: ignore
    
    is_event_baking: BoolProperty(default=False, description="Sorcerer is currently baking") # type: ignore # type: ignore
    
    show_presets: BoolProperty(default=False, description="Shows buttons on intensities panel") # type: ignore # type: ignore
    
    color_is_preset_mode: BoolProperty(default=False, description="Show color with just the preset buttons") # type: ignore # type: ignore
    
    color_is_expanded: BoolProperty(default=False, description="Show color with expanded color pickers")   # type: ignore # type: ignore
    
    expand_channel_settings: BoolProperty(default=False, description="View active channel settings")   # type: ignore
    
    expand_prefixes_is_on: BoolProperty(default=False, description="Expand the place to adjust the OSC syntax") # type: ignore # type: ignore
    
    record_settings_is_on: BoolProperty(default=False, description="Dummy property for UI") # type: ignore # type: ignore

    nodes_are_armed: BoolProperty(default=True, description="Make the parameter controller nodes stop transmitting") # type: ignore # type: ignore

    # STRING
    school_mode_password: StringProperty(default="", description="Reduces potential for students or volunteers to break things", update=CommonUpdaters.school_mode_password_updater) # type: ignore # type: ignore
    school_mode_enabled: BoolProperty(default=False, description="Reduces potential for students or volunteers to break things") # type: ignore # type: ignore

    restrict_network: BoolProperty(name="Network", default=True, description="When school mode is enabled, you can't change network settings.") # type: ignore # type: ignore
    restrict_patch: BoolProperty(name="Patch", default=True, description="When school mode is enabled, you can't change patch settings.") # type: ignore # type: ignore
    restrict_house_lights: BoolProperty(name="House Lights", default=True, description="When school mode is enabled, you can't change house lights settings.") # type: ignore
    restrict_strip_media: BoolProperty(name="Controller Settings", default=False, description="When school mode is enabled, you can't change controller settings.") # type: ignore
    restrict_sequencer: BoolProperty(name="Sequencer Settings", default=True, description="When school mode is enabled, you can't change sequencer settings.") # type: ignore # type: ignore
    restrict_stage_objects: BoolProperty(name="Stage Objects", default=False, description="When school mode is enabled, stage objects are disabled") # type: ignore
    restrict_influencers: BoolProperty(name="Influencers", default=False, description="When school mode is enabled, influencers are disabled") # type: ignore
    restrict_pan_tilts: BoolProperty(name="Pan/Tilts", default=True, description="When school mode is enabled, stage pan_tilt objects are disabled") # type: ignore # type: ignore
    restrict_brushes: BoolProperty(name="Brushes", default=False, description="When school mode is enabled, brushes are disabled") # type: ignore # type: ignore

    view_ip_address_tool: BoolProperty(name="Viewport IP Address Tool Header", default=True, description="Draw the IP Address box in Viewport tool settings area") # type: ignore
    view_sequencer_add: BoolProperty(name="Sequencer Add", default=True, description="Draw the Add menu on the Sequencer") # type: ignore
    view_node_add: BoolProperty(name="Node Add", default=True, description="Draw the Add menu on the Node Editor") # type: ignore
    view_node_toolbar: BoolProperty(name="Node Toolbar", default=True, description="Draw Alva toolbar in node editor") # type: ignore
    view_sequencer_toolbar: BoolProperty(name="Sequencer Toolbar", default=True, description="Draw Alva toolbar in sequencer") # type: ignore
    view_viewport_toolbar: BoolProperty(name="Viewport Toolbar", default=True, description="Draw Alva toolbar in viewport") # type: ignore

    auto_update_event_list: BoolProperty(default=False, description="Automatically update events in the console's event list when things change without the need to press Shift+Spacebar") # type: ignore

    lighting_enabled: BoolProperty(default=True, description="Enable OSC for lighting") # type: ignore # type: ignore
    video_enabled: BoolProperty(default=False, description="Enable OSC for video") # type: ignore
    audio_enabled: BoolProperty(default=True, description="Enable OSC for audio") # type: ignore
    nodes_enabled: BoolProperty(default=True, name="Enable Nodes", description="Enable nodes OSC output") # type: ignore # type: ignore
    strips_enabled: BoolProperty(default=True, name="Enable Strips", description="Enable sequencer strips OSC output") # type: ignore # type: ignore
    objects_enabled: BoolProperty(default=True, name="Enable Objects", description="Enable 3D view OSC output") # type: ignore
    
    core_enabled: BoolProperty(default=True, description="Enable Core for lighting, video, and audio") # type: ignore
    use_alva_core: BoolProperty(default=False, name="In-house Mode", description="Commandeer your local Alva theater") # type: ignore

    ghost_out_time: IntProperty(default=1, name="Ghost Out Time", description="This does not impact the lighting console's own Go_to_Cue time") # type: ignore

    highlight_mode: BoolProperty(default=False, name="Highlight Mode", description="Automatically highlight the selected group on stage", update=CommonUpdaters.highlight_mode_updater) # type: ignore
    int_highlight_value: IntProperty(name="Highlight Intensity", description="Value 1-100 that the highlight function should set highlighted lights to", min=1, max=100, default=100) # type: ignore
    float_highlight_time: FloatProperty(name="Highlight Sneak Time", description="How quickly the highlight should come up, in seconds", min=0, max=5, default=.5) # type: ignore
    string_highlight_memory: StringProperty() # type: ignore # type: ignore

    active_controller: IntProperty(
        name="Active Controller",
        description="Index of the active controller",
        default=0,
        min=0
    )         # type: ignore
    array_modifier_enum: EnumProperty(
        name="Modifiers",
        description="Choose an Array modifier",
        items=AlvaItems.get_modifier_items,
        default=0
    ) # type: ignore
    array_curve_enum: EnumProperty(
        name="Curves",
        description="Choose a curve modifier if applicable",
        items=AlvaItems.get_curve_items,
        default=0
    ) # type: ignore # type: ignore
    array_cone_enum: EnumProperty(
        name="Cones",
        description="You're supposed to make a bunch of cones in 3D View using an Array modifier to represent the group of lights to be patched so that Sorcerer can patch Augment 3D for you",
        items=AlvaItems.get_cone_items,
        update=CommonUpdaters.cone_enum_updater,
        default=0
    ) # type: ignore # type: ignore

    '''TWO LONE STRINGS'''
    str_group_label_to_add: StringProperty(default="") # type: ignore
    int_group_number_to_add: IntProperty(default=1, min=1, max=9999, description="Index of group as on console") # type: ignore
    str_group_channels_to_add: StringProperty(default="") # type: ignore
    
    int_array_quantity: IntProperty(default=1, min=1, max=999, description="How many lights to add", update=CommonUpdaters.update_light_array) # type: ignore
    float_offset_x: FloatProperty(default=1, min=0, max=100, unit = 'LENGTH', update=CommonUpdaters.update_light_positions) # type: ignore
    float_offset_y: FloatProperty(default=0, min=0, max=100, unit = 'LENGTH', update=CommonUpdaters.update_light_positions) # type: ignore
    float_offset_z: FloatProperty(default=0, min=-1000, max=100, unit = 'LENGTH', update=CommonUpdaters.update_light_positions) # type: ignore

    str_array_group_name: StringProperty(default="", description="Group label on console") # type: ignore
    str_array_group_maker: StringProperty(default="", description="Fixture manufacturer on console") # type: ignore # type: ignore
    str_array_group_type: StringProperty(default="", description="Fixture type on console") # type: ignore
    
    int_array_group_index: IntProperty(default=1, max=9999, description="Group number on console") # type: ignore
    int_array_start_channel: IntProperty(default=1, max=9999, description="Channel number to start at on console") # type: ignore
    
    int_array_universe: IntProperty(default=1, max=9999, description="Universe to start patching to on console") # type: ignore # type: ignore
    int_array_start_address: IntProperty(default=1, max=9999, description="Address to start patching to on console") # type: ignore
    int_array_channel_mode: IntProperty(default=1, max=9999, description="How many channels each fixture needs on console") # type: ignore

    bool_eos_console_mode: BoolProperty(default=False, description="I am using an ETC Eos lighting console") # type: ignore

    str_preset_assignment_argument: StringProperty(
            default=" Group # Record Preset $ Enter Enter", 
            description="Use # for group number and $ for preset number"
    ) # type: ignore # type: ignore
    
    selected_mesh_name: StringProperty(default="", description="Select a mesh in 3D view that represents light fixtures") # type: ignore # type: ignore

    selected_array_name: StringProperty(default="", description="Select an array modifier in 3D view that represents a group of light fixtures") # type: ignore

    channel_controller_is_active: BoolProperty(default=False, description="This allows the channel updaters to know whether to consider selected objects or not") # type: ignore # type: ignore

    int_cue_fader_bar: IntProperty(min=0, max=100, update=PropertiesUpdaters.fader_bar_updater) # type: ignore
    int_fader_bar_memory: IntProperty(default=0) # type: ignore
    str_preview_cue_index: StringProperty() # type: ignore
    str_program_cue_index: StringProperty() # type: ignore
    float_time_memory: FloatProperty() # type: ignore
    float_auto_time: FloatProperty(name="Auto Time", description="Duration that Auto uses") # type: ignore
    float_blue_time: FloatProperty(name="Blue Time", description="Duration that Blue uses") # type: ignore
    float_black_time: FloatProperty(name="Black Time", description="Duration that Black uses") # type: ignore
    float_restore_time: FloatProperty(name="Restore Time", description="Duration that Restore uses") # type: ignore
    string_blue_cue: StringProperty(name="Blue Cue Number", description="Cue number of blueout cue.") # type: ignore
    string_black_cue: StringProperty(name="Black Cue Number", description="Cue number of blackout cue.") # type: ignore
    string_restore_cue: StringProperty(name="Restore Cue Number", description="Cue number of restore cue.") # type: ignore
    
    cue_lists_index: IntProperty(default=0) # type: ignore
    
    use_name_for_id: BoolProperty(default=True, name="Use Name", description="Choose between using the Fixture ID or name to assign objects to channels") # type: ignore # type: ignore

    input_one: IntProperty(name="Mic Input 1", description="Corresponds to Input 1 on the audio mixer") # type: ignore
    input_two: IntProperty(name="Mic Input 2", description="Corresponds to Input 2 on the audio mixer") # type: ignore # type: ignore
    input_three: IntProperty(name="Mic Input 3", description="Corresponds to Input 3 on the audio mixer") # type: ignore
    input_four: IntProperty(name="Mic Input 4", description="Corresponds to Input 4 on the audio mixer") # type: ignore # type: ignore
    input_five: IntProperty(name="Mic Input 5", description="Corresponds to Input 5 on the audio mixer") # type: ignore
    input_six: IntProperty(name="Mic Input 6", description="Corresponds to Input 6 on the audio mixer") # type: ignore
    input_seven: IntProperty(name="Mic Input 7", description="Corresponds to Input 7 on the audio mixer") # type: ignore
    input_eight: IntProperty(name="Mic Input 8", description="Corresponds to Input 8 on the audio mixer") # type: ignore
    input_nine: IntProperty(name="Mic Input 9", description="Corresponds to Input 9 on the audio mixer") # type: ignore
    input_ten: IntProperty(name="Mic Input 10", description="Corresponds to Input 10 on the audio mixer") # type: ignore
    input_eleven: IntProperty(name="Mic Input 11", description="Corresponds to Input 11 on the audio mixer") # type: ignore
    input_twelve: IntProperty(name="Mic Input 12", description="Corresponds to Input 12 on the audio mixer") # type: ignore
    input_thirteen: IntProperty(name="Mic Input 13", description="Corresponds to Input 13 on the audio mixer") # type: ignore
    input_fourteen: IntProperty(name="Mic Input 14", description="Corresponds to Input 14 on the audio mixer") # type: ignore
    input_fifteen: IntProperty(name="Mic Input 15", description="Corresponds to Input 15 on the audio mixer") # type: ignore
    input_sixteen: IntProperty(name="Mic Input 16", description="Corresponds to Input 16 on the audio mixer") # type: ignore
    input_seventeen: IntProperty(name="Mic Input 17", description="Corresponds to Input 17 on the audio mixer") # type: ignore
    input_eighteen: IntProperty(name="Mic Input 18", description="Corresponds to Input 18 on the audio mixer") # type: ignore
    input_nineteen: IntProperty(name="Mic Input 19", description="Corresponds to Input 19 on the audio mixer") # type: ignore # type: ignore
    input_twenty: IntProperty(name="Mic Input 20", description="Corresponds to Input 20 on the audio mixer") # type: ignore
    input_twenty_one: IntProperty(name="Mic Input 21", description="Corresponds to Input 21 on the audio mixer") # type: ignore
    input_twenty_two: IntProperty(name="Mic Input 22", description="Corresponds to Input 22 on the audio mixer") # type: ignore # type: ignore
    input_twenty_three: IntProperty(name="Mic Input 23", description="Corresponds to Input 23 on the audio mixer") # type: ignore
    input_twenty_four: IntProperty(name="Mic Input 24", description="Corresponds to Input 24 on the audio mixer") # type: ignore
    input_twenty_five: IntProperty(name="Mic Input 25", description="Corresponds to Input 25 on the audio mixer") # type: ignore
    input_twenty_six: IntProperty(name="Mic Input 26", description="Corresponds to Input 26 on the audio mixer") # type: ignore
    input_twenty_seven: IntProperty(name="Mic Input 27", description="Corresponds to Input 27 on the audio mixer") # type: ignore
    input_twenty_eight: IntProperty(name="Mic Input 28", description="Corresponds to Input 28 on the audio mixer") # type: ignore
    input_twenty_nine: IntProperty(name="Mic Input 29", description="Corresponds to Input 29 on the audio mixer") # type: ignore
    input_thirty: IntProperty(name="Mic Input 30", description="Corresponds to Input 30 on the audio mixer") # type: ignore
    input_thirty_one: IntProperty(name="Mic Input 31", description="Corresponds to Input 31 on the audio mixer") # type: ignore
    input_thirty_two: IntProperty(name="Mic Input 32", description="Corresponds to Input 32 on the audio mixer") # type: ignore

    output_one: IntProperty(name="Output 1", description="Corresponds to Output 1 on the audio mixer") # type: ignore
    output_two: IntProperty(name="Output 2", description="Corresponds to Output 2 on the audio mixer") # type: ignore
    output_three: IntProperty(name="Output 3", description="Corresponds to Output 3 on the audio mixer") # type: ignore
    output_four: IntProperty(name="Output 4", description="Corresponds to Output 4 on the audio mixer") # type: ignore
    output_five: IntProperty(name="Output 5", description="Corresponds to Output 5 on the audio mixer") # type: ignore
    output_six: IntProperty(name="Output 6", description="Corresponds to Output 6 on the audio mixer") # type: ignore
    output_seven: IntProperty(name="Output 7", description="Corresponds to Output 7 on the audio mixer") # type: ignore
    output_eight: IntProperty(name="Output 8", description="Corresponds to Output 8 on the audio mixer") # type: ignore
    output_nine: IntProperty(name="Output 9", description="Corresponds to Output 9 on the audio mixer") # type: ignore
    output_ten: IntProperty(name="Output 10", description="Corresponds to Output 10 on the audio mixer") # type: ignore
    output_eleven: IntProperty(name="Output 11", description="Corresponds to Output 11 on the audio mixer") # type: ignore
    output_twelve: IntProperty(name="Output 12", description="Corresponds to Output 12 on the audio mixer") # type: ignore
    output_thirteen: IntProperty(name="Output 13", description="Corresponds to Output 13 on the audio mixer") # type: ignore
    output_fourteen: IntProperty(name="Output 14", description="Corresponds to Output 14 on the audio mixer") # type: ignore
    output_fifteen: IntProperty(name="Output 15", description="Corresponds to Output 15 on the audio mixer") # type: ignore
    output_sixteen: IntProperty(name="Output 16", description="Corresponds to Output 16 on the audio mixer") # type: ignore

    bus_one: IntProperty(name="Bus 1", description="Corresponds to Bus 1 on the audio mixer") # type: ignore
    bus_two: IntProperty(name="Bus 2", description="Corresponds to Bus 2 on the audio mixer") # type: ignore
    bus_three: IntProperty(name="Bus 3", description="Corresponds to Bus 3 on the audio mixer") # type: ignore
    bus_four: IntProperty(name="Bus 4", description="Corresponds to Bus 4 on the audio mixer") # type: ignore
    bus_five: IntProperty(name="Bus 5", description="Corresponds to Bus 5 on the audio mixer") # type: ignore
    bus_six: IntProperty(name="Bus 6", description="Corresponds to Bus 6 on the audio mixer") # type: ignore
    bus_seven: IntProperty(name="Bus 7", description="Corresponds to Bus 7 on the audio mixer") # type: ignore # type: ignore
    bus_eight: IntProperty(name="Bus 8", description="Corresponds to Bus 8 on the audio mixer") # type: ignore # type: ignore
    bus_nine: IntProperty(name="Bus 9", description="Corresponds to Bus 9 on the audio mixer") # type: ignore # type: ignore
    bus_ten: IntProperty(name="Bus 10", description="Corresponds to Bus 10 on the audio mixer") # type: ignore
    bus_eleven: IntProperty(name="Bus 11", description="Corresponds to Bus 11 on the audio mixer") # type: ignore
    bus_twelve: IntProperty(name="Bus 12", description="Corresponds to Bus 12 on the audio mixer") # type: ignore
    bus_thirteen: IntProperty(name="Bus 13", description="Corresponds to Bus 13 on the audio mixer") # type: ignore
    bus_fourteen: IntProperty(name="Bus 14", description="Corresponds to Bus 14 on the audio mixer") # type: ignore
    bus_fifteen: IntProperty(name="Bus 15", description="Corresponds to Bus 15 on the audio mixer") # type: ignore
    bus_sixteen: IntProperty(name="Bus 16", description="Corresponds to Bus 16 on the audio mixer") # type: ignore

    dca_one: IntProperty(name="DCA 1", description="Corresponds to DCA 1 on the audio mixer") # type: ignore
    dca_two: IntProperty(name="DCA 2", description="Corresponds to DCA 2 on the audio mixer") # type: ignore
    dca_three: IntProperty(name="DCA 3", description="Corresponds to DCA 3 on the audio mixer") # type: ignore
    dca_four: IntProperty(name="DCA 4", description="Corresponds to DCA 4 on the audio mixer") # type: ignore
    dca_five: IntProperty(name="DCA 5", description="Corresponds to DCA 5 on the audio mixer") # type: ignore
    dca_six: IntProperty(name="DCA 6", description="Corresponds to DCA 6 on the audio mixer") # type: ignore
    

def register():
    bpy.utils.register_class(SceneProperties)
    Scene.scene_props = PointerProperty(type=SceneProperties)
    Scene.lighting_modifiers = CollectionProperty(type=LightingModifierSubClass)
    Scene.active_modifier_index = IntProperty(default=-1)
    
    common_properties = CommonProperties()
    Utils.register_properties(SceneProperties, common_properties.mins_maxes)
    Utils.register_properties(SceneProperties, common_properties.parameter_toggles)
    Utils.register_properties(SceneProperties, common_properties.special_arguments)


def unregister():
    common_properties = CommonProperties()
    Utils.register_properties(SceneProperties, common_properties.mins_maxes, register=False)
    Utils.register_properties(SceneProperties, common_properties.parameter_toggles, register=False)
    Utils.register_properties(SceneProperties, common_properties.special_arguments, register=False)

    del Scene.active_modifier_index
    del Scene.lighting_modifiers
    bpy.utils.unregister_class(SceneProperties)

def unregister():
    common_properties = CommonProperties()
    Utils.register_properties(SceneProperties, common_properties.mins_maxes, register=False)
    Utils.register_properties(SceneProperties, common_properties.parameter_toggles, register=False)
    Utils.register_properties(SceneProperties, common_properties.special_arguments, register=False)

    if hasattr(Scene, "active_modifier_index"):
        del Scene.active_modifier_index
    if hasattr(Scene, "lighting_modifiers"):
        del Scene.lighting_modifiers
    if hasattr(Scene, "scene_props"):
        del Scene.scene_props

    bpy.utils.unregister_class(SceneProperties)