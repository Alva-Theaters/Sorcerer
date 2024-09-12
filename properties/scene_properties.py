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

from ..updaters.common_updaters import CommonUpdaters 
from ..updaters.properties_updaters import PropertiesUpdaters 
from ..utils.utils import Utils 
from ..properties.common_properties import CommonProperties 
from ..assets.items import Items as AlvaItems 

# pyright: reportInvalidTypeForm=false


LightingModifierSubClass = Utils.find_subclass_by_name(PropertyGroup, "LightingModifier")
ErrorsSubClass = Utils.find_subclass_by_name(PropertyGroup, "Errors")

class SceneProperties(PropertyGroup):
    group_data_index: IntProperty(name="Index", default=0, update=CommonUpdaters.highlight_mode_updater) 
    expand_toggles: BoolProperty(name="Parameter Toggle Position", default=True, description="Choose whether to draw the toggles beside group name or off to the side") 

    add_channel_ids: StringProperty(name="Add Channels", description="Just type in the channels you want or don't want in plain English", update=CommonUpdaters.channel_ids_updater)     
    
    view3d_command_line: StringProperty(name="Lighting Console Command Line Input", default="", update=CommonUpdaters.view3d_cmd_line_updater) 

    str_osc_ip_address: StringProperty(default="192.168.1.1", description="This should be the IP address of the console. This must set for anything to work. Press the About key on the console to find the console's IP address. Console must be on same local network", update=CommonUpdaters.network_settings_updater) 
    int_osc_port: IntProperty(min=0, max=65535, description="On the console, Displays > Setup > System Settings > Show Control > OSC > (enable OSC RX and make the port number there on the left match the one in this field in Alva. OSC TX = transmit and OSC RX = receive. We want receive", default=8000, update=CommonUpdaters.network_settings_updater) 
    string_osc_receive_port: IntProperty(min=0, max=65535) 
    
    str_record_cue: StringProperty(default="Record Cue # Time $ Enter Enter", description="Write command line syntax for recording cue # with duration $. # and $ are filled in by Orb as cue number and duration, respectively") 
    str_create_all_events: StringProperty(default="Event 1 / 1 Thru # Enter", description="Write command line syntax to initialize all events. Orb will replace # with the final event number based on the sequencer's end frame") 
    str_setup_event: StringProperty(default="Event 1 / # Time $ Show_Control_Action Cue # Enter", description="Write command line syntax to setup each event. # is frame/cue and $ is timecode") 
    str_bake_info: StringProperty(default="Bake Animation to Cues (to Qmeo)") 
    str_event_bake_info: StringProperty(default="Just Events")  
    str_cue_bake_info: StringProperty(default="Just Cues")  
    selected_text_block_name: StringProperty() 

    preferences_enum: EnumProperty(
        name="Preferences",
        description="",
        items=AlvaItems.preferences 
    )
    
    is_playing: BoolProperty(
        default=False, description="Tells harmonizer publisher if an update is associated with playback") 
        
    in_frame_change: BoolProperty(
        default=False, description="Tells harmonizer publisher if an update is associated with a single frame change. Allows harmonization during manual frame changes")  
        
    is_democratic: BoolProperty(
        default=False, description="This is a democracy. When different controllers try to change the same channel parameter, their Influence parameter gives them votes in a weighted average")  
    
    is_not_democratic: BoolProperty(
        default=True, description="This isn't a democracy anymore. When different controllers try to change the same channel parameter, the strongest completely erases everyone else's opinion")  

    console_type_enum: EnumProperty(
        name="Lighting Console Type",
        description="Select the type of 3rd party lighting console you wish to commandeer with Sorcerer",
        items=AlvaItems.console_types
    )  
    
    mixer_type_enum: EnumProperty(
        name="Audio Mixer Type",
        description="Select the type of 3rd party audio mixer you wish to commandeer with Sorcerer",
        items=AlvaItems.mixer_types
    )  

    core_type_enum: EnumProperty(
        name="Theater Type",
        description="Select the model theater",
        items=AlvaItems.core_types
    ) 

    core_drives_enum: EnumProperty(
        name="Theater Drive",
        description="Select the drive you will use to transport DTP assets to the core",
        items=AlvaItems.core_drives
    ) 

    # Service Mode
    service_mode: BoolProperty(default=False)
    limp_mode: BoolProperty(default=False)
    errors: CollectionProperty(type=ErrorsSubClass) 
    number_of_systems_down: IntProperty(default=0)
    user_limp_mode_explanation: StringProperty()
    errors_index: IntProperty(default=0)
    # OSC
    print_osc_lighting: BoolProperty(default=False, description="Enable built-in debug prints to external command line for this script", name="OSC Lighting") 
    print_osc_video: BoolProperty(default=False, description="Enable built-in debug prints to external command line for this script", name="OSC Video") 
    print_osc_audio: BoolProperty(default=False, description="Enable built-in debug prints to external command line for this script", name="OSC Audio") 
    print_osc: BoolProperty(default=False, description="Enable built-in debug prints to external command line for this script", name="All OSC") 
    # CPVIA
    print_cpvia_generator: BoolProperty(default=False, description="Enable built-in debug prints to external command line for this script", name="cpvia_generator.py") 
    print_find: BoolProperty(default=False, description="Enable built-in debug prints to external command line for this script", name="cpvia_finders.py") 
    print_flags: BoolProperty(default=False, description="Enable built-in debug prints to external command line for this script", name="flags.py") 
    print_harmonizer: BoolProperty(default=False, description="Enable built-in debug prints to external command line for this script", name="harmonizer.py") 
    print_influencers: BoolProperty(default=False, description="Enable built-in debug prints to external command line for this script", name="influencers.py") 
    print_map: BoolProperty(default=False, description="Enable built-in debug prints to external command line for this script", name="map.py") 
    print_mix: BoolProperty(default=False, description="Enable built-in debug prints to external command line for this script", name="mix.py") 
    print_publish: BoolProperty(default=False, description="Enable built-in debug prints to external command line for this script", name="publish.py") 
    print_split_color: BoolProperty(default=False, description="Enable built-in debug prints to external command line for this script", name="split_color.py") 
    # Operators
    print_common_operators: BoolProperty(default=False, description="Enable built-in debug prints to external command line for this script", name="common_operators.py") 
    print_cue_builder_operators: BoolProperty(default=False, description="Enable built-in debug prints to external command line for this script", name="cue_builder_operators.py") 
    print_node_operators: BoolProperty(default=False, description="Enable built-in debug prints to external command line for this script", name="node_operators.py") 
    print_orb_operators: BoolProperty(default=False, description="Enable built-in debug prints to external command line for this script", name="orb_operators.py") 
    print_properties_operators: BoolProperty(default=False, description="Enable built-in debug prints to external command line for this script", name="properties_operators.py") 
    print_sequencer_operators: BoolProperty(default=False, description="Enable built-in debug prints to external command line for this script", name="sequencer_operators.py") 
    print_strip_formatter_operators: BoolProperty(default=False, description="Enable built-in debug prints to external command line for this script", name="strip_formatter_operators") 
    print_view3d_operators: BoolProperty(default=False, description="Enable built-in debug prints to external command line for this script", name="view3d_operators.py") 
    # Updaters
    print_common_updaters: BoolProperty(default=False, description="Enable built-in debug prints to external command line for this script", name="common_updaters.py") 
    print_node_updaters: BoolProperty(default=False, description="Enable built-in debug prints to external command line for this script", name="node_updaters.py") 
    print_properties_updaters: BoolProperty(default=False, description="Enable built-in debug prints to external command line for this script", name="properties_updaters.py") 
    print_sequencer_updaters: BoolProperty(default=False, description="Enable built-in debug prints to external command line for this script", name="sequencer_updaters.py") 
    # Main
    print_event_manager: BoolProperty(default=False, description="Enable built-in debug prints to external command line for this script", name="event_manager.py") 
    print_orb: BoolProperty(default=False, description="Enable built-in debug prints to external command line for this script", name="orb.py") 
    print_time: BoolProperty(default=False, description="Enable built-in debug prints to external command line for speed tests", name="Time") 
    
    str_core_ip_address: StringProperty(name="Theater IP Address", default="") 
    
    int_core_port: IntProperty(name="Theater Port", default=0)  
    
    int_argument_size: IntProperty(name="Maximum Argument Size", default=40, min=1, max=65, description="How many consecutive command line commands can be batched onto one OSC packet.") 

    is_baking: BoolProperty(default=False, description="Sorcerer is currently baking")  
    is_cue_baking: BoolProperty(default=False, description="Sorcerer is currently baking")  
    is_event_baking: BoolProperty(default=False, description="Sorcerer is currently baking")  
    freeze_cpvia: BoolProperty(default=False, description="Used by Patch Console Remotely orb operator to prevent random CPVIA updates interfering with patching operations") 

    show_presets: BoolProperty(default=False, description="Shows buttons on intensities panel")  
    
    color_is_preset_mode: BoolProperty(default=False, description="Show color with just the preset buttons")  
    
    color_is_expanded: BoolProperty(default=False, description="Show color with expanded color pickers")    
    
    expand_channel_settings: BoolProperty(default=False, description="View active channel settings")   
    
    expand_prefixes_is_on: BoolProperty(default=False, description="Expand the place to adjust the OSC syntax")  
    
    record_settings_is_on: BoolProperty(default=False, description="Dummy property for UI")  

    nodes_are_armed: BoolProperty(default=True, description="Make the parameter controller nodes stop transmitting")  

    # STRING
    school_mode_password: StringProperty(default="", description="Reduces potential for students or volunteers to break things", update=CommonUpdaters.school_mode_password_updater)  
    school_mode_enabled: BoolProperty(default=False, description="Reduces potential for students or volunteers to break things")  

    restrict_network: BoolProperty(name="Network", default=True, description="When school mode is enabled, you can't change network settings")
    restrict_patch: BoolProperty(name="Patch", default=True, description="When school mode is enabled, you can't change patch settings")  
    restrict_pan_tilt: BoolProperty(name="Pan/Tilts", default=True, description="When school mode is enabled, stage pan_tilt objects are disabled")  

    view_ip_address_tool: BoolProperty(name="IP Address", default=True, description="Draw the IP Address box in Tool Settings or Header area") 
    view_sequencer_add: BoolProperty(name="Sequencer Add", default=True, description="Draw the Add menu on the Sequencer") 
    view_alva_time_header: BoolProperty(name="View Header", default=True, description="Draw sync and Orb settings in header") 
    view_node_add_lighting: BoolProperty(name="Node Add (Lighting)", default=True, description="Draw the Add menu on the Node Editor for lighting") 
    view_node_add_audio: BoolProperty(name="Node Add (Audio)", default=False, description="Draw the Add menu on the Node Editor for audio. (Experimental)") 
    view_node_toolbar: BoolProperty(name="Node Toolbar", default=True, description="Draw Alva toolbar in node editor") 
    view_sequencer_toolbar: BoolProperty(name="Sequencer Toolbar", default=True, description="Draw Alva toolbar in sequencer") 
    view_viewport_toolbar: BoolProperty(name="Viewport Toolbar", default=True, description="Draw Alva toolbar in viewport") 
    view_topbar: BoolProperty(name="Viewport Topbar", default=True, description="Draw Alva topbar section on the very top of Blender on the right") 
    view_sequencer_command_line: BoolProperty(name="Command Line", default=True, description="Draw the sequencer's internal command line") 
    view_viewport_command_line: BoolProperty(name="Command Line", default=True, description="Draw the viewport's command line for Eos") 
    view_node_formatter: BoolProperty(name="Header Formatter", default=True, description="Draw the node formatter in the header") 
    expand_strobe: BoolProperty(name="Expand Strobe", default=True, description="Draw the Strobe slider in its own row as opposed to only within the popup. This must be checked to animate strobe") 

    enable_lighting: BoolProperty(name="Enable Lighting", default=True, description="Enable OSC for lighting")  
    enable_video: BoolProperty(name="Enable Video", default=False, description="Enable OSC for video") 
    enable_audio: BoolProperty(name="Enable Audio", default=True, description="Enable OSC for audio") 
    enable_nodes: BoolProperty(name="Enable Nodes", default=True, description="Enable nodes OSC output")  
    enable_strips: BoolProperty(name="Enable Strips", default=True, description="Enable sequencer strips OSC output")  
    enable_objects: BoolProperty(name="Enable Objects", default=True, description="Enable 3D view OSC output") 
    enable_seconds: BoolProperty(name="Freeze Seconds", default=True, description="Controllers set to On Seconds will only be rendered every other frame (right click them to set). When unchecked, these controllers will be completely disabled during frame change and playback")  
    enable_thirds: BoolProperty(name="Freeze Thirds", default=True, description="Controllers set to On Thirds will only be rendered every third frame (right click them to set). When unchecked, these controllers will be completely disabled during frame change and playback") 
    
    has_solos: BoolProperty() 

    core_enabled: BoolProperty(name="Enable Core", default=True, description="Enable Renegade's core") 
    use_alva_core: BoolProperty(default=False, name="In-house Mode", description="Commandeer your local Alva theater") 

    ghost_out_time: IntProperty(default=1, name="Ghost Out Time", description="This does not impact the lighting console's own Go_to_Cue time") 
    ghost_out_string: StringProperty(default="Go_to_Cue Out Time * Enter", name="Ghost Out Command", description="This is what the Ghost Out button will tell the console. Add * for Ghost Out Time")

    highlight_mode: BoolProperty(default=False, name="Highlight Mode", description="Automatically highlight the selected group on stage", update=CommonUpdaters.highlight_mode_updater) 
    int_highlight_value: IntProperty(name="Highlight Intensity", description="Value 1-100 that the highlight function should set highlighted lights to", min=1, max=100, default=100) 
    float_highlight_time: FloatProperty(name="Highlight Sneak Time", description="How quickly the highlight should come up, in seconds", min=0, max=5, default=.5) 
    string_highlight_memory: StringProperty()  

    active_controller: IntProperty(
        name="Active Controller",
        description="Index of the active controller",
        default=0,
        min=0
    )         
    array_modifier_enum: EnumProperty(
        name="Modifiers",
        description="Choose an Array modifier",
        items=AlvaItems.get_modifier_items,
        default=0
    ) 
    array_curve_enum: EnumProperty(
        name="Curves",
        description="Choose a curve modifier if applicable",
        items=AlvaItems.get_curve_items,
        default=0
    )  
    array_cone_enum: EnumProperty(
        name="Cones",
        description="You're supposed to make a bunch of cones in 3D View using an Array modifier to represent the group of lights to be patched so that Orb can patch Augment 3D for you",
        items=AlvaItems.get_cone_items,
        update=CommonUpdaters.cone_enum_updater,
        default=0
    )  

    int_array_quantity: IntProperty(default=1, min=1, max=999, description="How many lights to add", update=CommonUpdaters.update_light_array) 
    float_offset_x: FloatProperty(default=1, min=0, max=100, unit = 'LENGTH', update=CommonUpdaters.update_light_positions) 
    float_offset_y: FloatProperty(default=0, min=0, max=100, unit = 'LENGTH', update=CommonUpdaters.update_light_positions) 
    float_offset_z: FloatProperty(default=0, min=-1000, max=100, unit = 'LENGTH', update=CommonUpdaters.update_light_positions) 

    str_array_group_name: StringProperty(name="Group Name", default="", description="Group label on console") 
    str_array_group_maker: StringProperty(name="Group Maker/Maufacturer", default="", description="Fixture manufacturer on console")  
    str_array_group_type: StringProperty(name="Fixture Type", default="", description="Fixture type on console") 
    
    int_array_group_index: IntProperty(name="Group #", default=1, max=9999, description="Group number on console") 
    int_array_start_channel: IntProperty(name="Start Channel #", default=1, max=9999, description="Channel number to start at on console") 
    
    int_group_number: IntProperty(name="Group #", default=0, max=9999, min=0, description="Group to create for this set. Set to 0 to skip recording group")  
    int_array_universe: IntProperty(name="Universe #", default=1, max=9999, min=1, description="Universe to start patching to on console")  
    int_array_start_address: IntProperty(name="Start Address #", default=1, max=9999, min=1, description="Address to start patching to on console") 
    int_array_channel_mode: IntProperty(name="Channel Mode", default=1, max=9999, min=1, description="How many channels each fixture needs on console") 

    bool_eos_console_mode: BoolProperty(default=False, description="I am using an ETC Eos lighting console") 

    str_preset_assignment_argument: StringProperty(
            default=" Group # Record Preset $ Enter Enter", 
            description="Use # for group number and $ for preset number"
    )  
    
    selected_mesh_name: StringProperty(default="", description="Select a mesh in 3D view that represents light fixtures")  

    selected_array_name: StringProperty(default="", description="Select an array modifier in 3D view that represents a group of light fixtures") 

    int_cue_fader_bar: IntProperty(min=0, max=100, update=PropertiesUpdaters.fader_bar_updater) 
    int_fader_bar_memory: IntProperty(default=0) 
    str_preview_cue_index: StringProperty() 
    str_program_cue_index: StringProperty() 
    float_time_memory: FloatProperty() 
    float_auto_time: FloatProperty(name="Auto Time", description="Duration that Auto uses") 
    float_blue_time: FloatProperty(name="Blue Time", description="Duration that Blue uses") 
    float_black_time: FloatProperty(name="Black Time", description="Duration that Black uses") 
    float_restore_time: FloatProperty(name="Restore Time", description="Duration that Restore uses") 
    string_blue_cue: StringProperty(name="Blue Cue Number", description="Cue number of blueout cue") 
    string_black_cue: StringProperty(name="Black Cue Number", description="Cue number of blackout cue") 
    string_restore_cue: StringProperty(name="Restore Cue Number", description="Cue number of restore cue") 
    
    cue_lists_index: IntProperty(default=0) 
    
    use_name_for_id: BoolProperty(default=True, name="Use Name", description="Choose between using the Fixture ID or name to assign objects to channels")  

    input_one: IntProperty(name="Mic Input 1", description="Corresponds to Input 1 on the audio mixer") 
    input_two: IntProperty(name="Mic Input 2", description="Corresponds to Input 2 on the audio mixer")  
    input_three: IntProperty(name="Mic Input 3", description="Corresponds to Input 3 on the audio mixer") 
    input_four: IntProperty(name="Mic Input 4", description="Corresponds to Input 4 on the audio mixer")  
    input_five: IntProperty(name="Mic Input 5", description="Corresponds to Input 5 on the audio mixer") 
    input_six: IntProperty(name="Mic Input 6", description="Corresponds to Input 6 on the audio mixer") 
    input_seven: IntProperty(name="Mic Input 7", description="Corresponds to Input 7 on the audio mixer") 
    input_eight: IntProperty(name="Mic Input 8", description="Corresponds to Input 8 on the audio mixer") 
    input_nine: IntProperty(name="Mic Input 9", description="Corresponds to Input 9 on the audio mixer") 
    input_ten: IntProperty(name="Mic Input 10", description="Corresponds to Input 10 on the audio mixer") 
    input_eleven: IntProperty(name="Mic Input 11", description="Corresponds to Input 11 on the audio mixer") 
    input_twelve: IntProperty(name="Mic Input 12", description="Corresponds to Input 12 on the audio mixer") 
    input_thirteen: IntProperty(name="Mic Input 13", description="Corresponds to Input 13 on the audio mixer") 
    input_fourteen: IntProperty(name="Mic Input 14", description="Corresponds to Input 14 on the audio mixer") 
    input_fifteen: IntProperty(name="Mic Input 15", description="Corresponds to Input 15 on the audio mixer") 
    input_sixteen: IntProperty(name="Mic Input 16", description="Corresponds to Input 16 on the audio mixer") 
    input_seventeen: IntProperty(name="Mic Input 17", description="Corresponds to Input 17 on the audio mixer") 
    input_eighteen: IntProperty(name="Mic Input 18", description="Corresponds to Input 18 on the audio mixer") 
    input_nineteen: IntProperty(name="Mic Input 19", description="Corresponds to Input 19 on the audio mixer")  
    input_twenty: IntProperty(name="Mic Input 20", description="Corresponds to Input 20 on the audio mixer") 
    input_twenty_one: IntProperty(name="Mic Input 21", description="Corresponds to Input 21 on the audio mixer") 
    input_twenty_two: IntProperty(name="Mic Input 22", description="Corresponds to Input 22 on the audio mixer")  
    input_twenty_three: IntProperty(name="Mic Input 23", description="Corresponds to Input 23 on the audio mixer") 
    input_twenty_four: IntProperty(name="Mic Input 24", description="Corresponds to Input 24 on the audio mixer") 
    input_twenty_five: IntProperty(name="Mic Input 25", description="Corresponds to Input 25 on the audio mixer") 
    input_twenty_six: IntProperty(name="Mic Input 26", description="Corresponds to Input 26 on the audio mixer") 
    input_twenty_seven: IntProperty(name="Mic Input 27", description="Corresponds to Input 27 on the audio mixer") 
    input_twenty_eight: IntProperty(name="Mic Input 28", description="Corresponds to Input 28 on the audio mixer") 
    input_twenty_nine: IntProperty(name="Mic Input 29", description="Corresponds to Input 29 on the audio mixer") 
    input_thirty: IntProperty(name="Mic Input 30", description="Corresponds to Input 30 on the audio mixer") 
    input_thirty_one: IntProperty(name="Mic Input 31", description="Corresponds to Input 31 on the audio mixer") 
    input_thirty_two: IntProperty(name="Mic Input 32", description="Corresponds to Input 32 on the audio mixer") 

    output_one: IntProperty(name="Output 1", description="Corresponds to Output 1 on the audio mixer") 
    output_two: IntProperty(name="Output 2", description="Corresponds to Output 2 on the audio mixer") 
    output_three: IntProperty(name="Output 3", description="Corresponds to Output 3 on the audio mixer") 
    output_four: IntProperty(name="Output 4", description="Corresponds to Output 4 on the audio mixer") 
    output_five: IntProperty(name="Output 5", description="Corresponds to Output 5 on the audio mixer") 
    output_six: IntProperty(name="Output 6", description="Corresponds to Output 6 on the audio mixer") 
    output_seven: IntProperty(name="Output 7", description="Corresponds to Output 7 on the audio mixer") 
    output_eight: IntProperty(name="Output 8", description="Corresponds to Output 8 on the audio mixer") 
    output_nine: IntProperty(name="Output 9", description="Corresponds to Output 9 on the audio mixer") 
    output_ten: IntProperty(name="Output 10", description="Corresponds to Output 10 on the audio mixer") 
    output_eleven: IntProperty(name="Output 11", description="Corresponds to Output 11 on the audio mixer") 
    output_twelve: IntProperty(name="Output 12", description="Corresponds to Output 12 on the audio mixer") 
    output_thirteen: IntProperty(name="Output 13", description="Corresponds to Output 13 on the audio mixer") 
    output_fourteen: IntProperty(name="Output 14", description="Corresponds to Output 14 on the audio mixer") 
    output_fifteen: IntProperty(name="Output 15", description="Corresponds to Output 15 on the audio mixer") 
    output_sixteen: IntProperty(name="Output 16", description="Corresponds to Output 16 on the audio mixer") 

    bus_one: IntProperty(name="Bus 1", description="Corresponds to Bus 1 on the audio mixer") 
    bus_two: IntProperty(name="Bus 2", description="Corresponds to Bus 2 on the audio mixer") 
    bus_three: IntProperty(name="Bus 3", description="Corresponds to Bus 3 on the audio mixer") 
    bus_four: IntProperty(name="Bus 4", description="Corresponds to Bus 4 on the audio mixer") 
    bus_five: IntProperty(name="Bus 5", description="Corresponds to Bus 5 on the audio mixer") 
    bus_six: IntProperty(name="Bus 6", description="Corresponds to Bus 6 on the audio mixer") 
    bus_seven: IntProperty(name="Bus 7", description="Corresponds to Bus 7 on the audio mixer")  
    bus_eight: IntProperty(name="Bus 8", description="Corresponds to Bus 8 on the audio mixer")  
    bus_nine: IntProperty(name="Bus 9", description="Corresponds to Bus 9 on the audio mixer")  
    bus_ten: IntProperty(name="Bus 10", description="Corresponds to Bus 10 on the audio mixer") 
    bus_eleven: IntProperty(name="Bus 11", description="Corresponds to Bus 11 on the audio mixer") 
    bus_twelve: IntProperty(name="Bus 12", description="Corresponds to Bus 12 on the audio mixer") 
    bus_thirteen: IntProperty(name="Bus 13", description="Corresponds to Bus 13 on the audio mixer") 
    bus_fourteen: IntProperty(name="Bus 14", description="Corresponds to Bus 14 on the audio mixer") 
    bus_fifteen: IntProperty(name="Bus 15", description="Corresponds to Bus 15 on the audio mixer") 
    bus_sixteen: IntProperty(name="Bus 16", description="Corresponds to Bus 16 on the audio mixer") 

    dca_one: IntProperty(name="DCA 1", description="Corresponds to DCA 1 on the audio mixer") 
    dca_two: IntProperty(name="DCA 2", description="Corresponds to DCA 2 on the audio mixer") 
    dca_three: IntProperty(name="DCA 3", description="Corresponds to DCA 3 on the audio mixer") 
    dca_four: IntProperty(name="DCA 4", description="Corresponds to DCA 4 on the audio mixer") 
    dca_five: IntProperty(name="DCA 5", description="Corresponds to DCA 5 on the audio mixer") 
    dca_six: IntProperty(name="DCA 6", description="Corresponds to DCA 6 on the audio mixer") 
    

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