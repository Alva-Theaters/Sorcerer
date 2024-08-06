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

## Double hashtag indicates notes for future development requiring some level of attention


from bpy.props import *
from bpy.types import Scene, ColorSequence, SoundSequence, Object

from ..assets.items import Items as AlvaItems
from ..updaters.sequencer_updaters import SequencerUpdaters as Updaters
from ..updaters.common_updaters import CommonUpdaters
from ..utils.utils import Utils


def empty_objects_poll(self, object):
    '''Only returns true for Empty bpy object. Used for [?]'''
    return object.type == 'MESH' and object.object_identities_enum == 'Stage Object'


def speaker_objects_poll(self, object):
    '''Only returns true for Speaker bpy object. Used for [?]'''
    return object.type == 'SPEAKER'


def register(): 
    Scene.command_line_label = StringProperty(default="Cmd Line: ")

    ColorSequence.is_linked = BoolProperty(
        default=False, name="", description="Link this to make it so that this strip will automatically stay in sync with all other strips sharing the same motif name above", update=Updaters.is_linked_updater)
    ColorSequence.motif_name = StringProperty(default="", description="Use this to link cues together that should act as one. They must have the same name here and have the link button turned on so that it is red for them to automatically update each other. Not everything will necessarily be updated.")
    ColorSequence.strip_length_proxy = IntProperty(name="", min=-9999, max=1000000)  ## Is this junk?


    # Strip formatter
    Scene.color_is_magnetic = BoolProperty(name="", description="Select Magnetic button will only select other strips if they share Active Strip's color", default=False)
    Scene.strip_name_is_magnetic = BoolProperty(name="", description="Select Magnetic button will only select other strips if they share Active Strip's strip name", default=False)
    Scene.channel_is_magnetic = BoolProperty(name="", description="Select Magnetic button will only select other strips if they share Active Strip's channel", default=False)
    Scene.duration_is_magnetic = BoolProperty(name="", description="Select Magnetic button will only select other strips if they share Active Strip's duration", default=False)
    Scene.start_frame_is_magnetic = BoolProperty(name="", description="Select Magnetic button will only select other strips if they share Active Strip's start frame", default=False)
    Scene.end_frame_is_magnetic = BoolProperty(name="", description="Select Magnetic button will only select other strips if they share Active Strip's end frame", default=False)
    Scene.is_filtering_left = BoolProperty(name="", description="Select Magnetic button will only select other strips if they are an exact match for the magnetic properties. If this is disabled, any strip matching as little as 1 magnetic property will be selected", default=False)
    Scene.is_filtering_right = BoolProperty(name="", description="The quick-select buttons below will deselect strips that don't match the button if this is enabled. If this is disabled, the quick-select button will only add to selections without ever deselecting anything", default=False)
    Scene.channel_selector = IntProperty(min=0, max=32, description="Enter the channel number you wish to select. Or, in the sequencer, just type the number of the channel you want. 0 for 10, and hold down shift to get up to 20. Only works up to channel 20")
    Scene.generate_quantity = IntProperty(min=1, max=10000, default=1, description="Enter in how many strips you want")
    Scene.normal_offset = IntProperty(min=0, max=10000, default=25, description="Enter in the desired offset in frames. A large offset number will result in long strips. Once created, you can do offsets using BPM instead. If you want to generate using BPM, select the sound file and do it there")
    Scene.i_know_the_shortcuts = BoolProperty(default=False)
    SoundSequence.song_bpm_input = IntProperty(name="", min=1, max=250, description='Use this to determine what strips will be generated and where')
    SoundSequence.song_bpm_channel = IntProperty(name="", min=1, max=32, description='Use this to choose which channel to place the new strips on')
    SoundSequence.beats_per_measure = IntProperty(name="", min=1, max=16, description='Use this to determine how many beats are in each measure. In a time signature like 3/4, this would be the top number 3')


    # Sound strips
    SoundSequence.song_timecode_clock_number = IntProperty(name="", min=0, max=99, description="This should be the number of the event list you have created on the console for this song")
    SoundSequence.execute_on_cue_number = IntProperty(name="", min=0, max=10000, update=Updaters.timecode_clock_update_safety, description="Specifies which cue will start (or enable) the timecode clock. Can't be the same as first cue in Blender sequence or that will create loop")
    SoundSequence.execute_with_macro_number = IntProperty(name="", min=0, max=100000, description="Specifies which macro number to build to use to start the timecode clock on the console")
    SoundSequence.disable_on_cue_number = IntProperty(name="", min=0, max=10000, update=Updaters.timecode_clock_update_safety, description="Specifies which cue will stop (or disable) the timecode clock")
    SoundSequence.disable_with_macro_number = IntProperty(name="", min=0, max=100000, description="Specifies which macro number to build to use to start the timecode clock on the console")
    # 3D sound
    SoundSequence.audio_type_enum = EnumProperty(
        items=AlvaItems.get_audio_object_items,
        name="Audio Types",
        description="Choose whether the strip represents a speaker or audio object",
        default=1
    )
    SoundSequence.selected_stage_object = PointerProperty(
        type=Object,
        poll=empty_objects_poll,
        name="Selected Empty",
        description='You are supposed to link this audio object strip to an object set to Stage Object over in 3D view',
        update=CommonUpdaters.sound_source_updater
    )
    SoundSequence.selected_speaker = PointerProperty(
        type=Object,
        poll=speaker_objects_poll,
        name="Selected Speaker",
        description='You are supposed to link this speaker strip to a "speaker" object over in 3D view'
    )
    SoundSequence.speaker_sensitivity = FloatProperty(name="Sensitivity", description="Sensitivity of speaker", default=.5, min=0, max=1)
    SoundSequence.audio_object_activated = BoolProperty(default=False, name="Activate Audio Object", description="Activate renderer for this audio object. Leaving this on when not needed may introduce lag")
    SoundSequence.dummy_volume = FloatProperty(default=0, name="Dummy Volume", min=0, max=1)
    SoundSequence.audio_object_size = FloatProperty(default=1, name="Dummy Volume", min=0, max=20)
    SoundSequence.int_mixer_channel = IntProperty(default=1, name="Channel/fader number on mixer", min=1, max=9999, description='This is for the OSC real-time monitor below. This is talking about the fader on the audio mixer. It will be replace "#" in the OSC templates below')
    

    # Macro strips
    ColorSequence.start_frame_macro = IntProperty(name="", min=0, max=99999, update=Updaters.motif_property_updater)
    ColorSequence.start_frame_macro_text = StringProperty(name="")
    ColorSequence.start_frame_macro_text_gui = StringProperty(name="", update=Updaters.macro_update)
    ColorSequence.end_frame_macro = IntProperty(name="", min=0, max=99999, update=Updaters.motif_property_updater)
    ColorSequence.end_frame_macro_text = StringProperty(name="")
    ColorSequence.end_frame_macro_text_gui = StringProperty(name="", update=Updaters.macro_update)
    ColorSequence.start_macro_muted = BoolProperty(name="", description="Toggle mute/unmute for the start macro", default=False)
    ColorSequence.end_macro_muted = BoolProperty(name="", description="Toggle mute/unmute for the end macro", default=False)


    # Cue Strips
    ColorSequence.eos_cue_number = StringProperty(name="", update=Updaters.motif_property_updater, description="This argument will be fired with the above prefix when frame 1 of the strip comes up in the sequencer. The top three fields here will definitely work on any console brand/type that has an OSC input library")
    ColorSequence.osc_auto_cue = StringProperty(get=Utils.get_auto_cue_string)
    # Livemap label for header/footer.
    Scene.livemap_label = StringProperty(name="Livemap Label", default="Livemap Cue:")
    # Cue builder
    Scene.cue_builder_toggle = BoolProperty(
        name="Cue Builder Panel", 
        description="Build cues inside Alva so you don't have to constantly switch back and forth between Alva and the console.", 
        default = True
    ) 
    Scene.cue_builder_id_offset = IntProperty(name="", description="Set this to 100 (or any integer) to make the cue builder buttons start at Preset 100/Effect 100, or similar")
    Scene.builder_settings_toggle = BoolProperty(
        name="Builder Settings Panel", 
        description="Select which groups are in key, rim, fill, band, accent, and background light categories.", 
        default = False
    ) 
    Scene.using_gels_for_cyc = BoolProperty(
        name="", 
        description="Mix backdrop color by mixing intensities of 4 channels gelled differently", 
        default = True
    ) 
    Scene.is_updating_strip_color = BoolProperty(
        name="", 
        description="When checked,changing the strip lighting effect type, the color of the strip changes to match the effect type.", 
        default = True
    ) 
    Scene.key_light_groups = StringProperty(name="Key Light Groups")
    Scene.rim_light_groups = StringProperty(name="Rim Light Groups")
    Scene.fill_light_groups = StringProperty(name="Fill Light Groups")
    Scene.texture_light_groups = StringProperty(name="Texture Light Groups")
    Scene.band_light_groups = StringProperty(name="Band Light Groups")
    Scene.accent_light_groups = StringProperty(name="Accent Light Groups")
    Scene.energy_light_groups = StringProperty(name="Accent Light Groups")
    Scene.cyc_light_groups = StringProperty(name="Background Light 1 Groups")
    Scene.cyc_two_light_groups = StringProperty(name="Background Light 1 Groups")
    Scene.cyc_three_light_groups = StringProperty(name="Background Light 1 Groups")
    Scene.cyc_four_light_groups = StringProperty(name="Background Light 1 Groups")   
    ColorSequence.key_light = IntProperty(name="Key Light", min=0, max=100, update=Updaters.key_light_updater, description="White, nuetral, primary light for primary performers")
    ColorSequence.rim_light = IntProperty(name="Rim Light", min=0, max=100,  update=Updaters.rim_light_updater, description="White or warm light coming from upstage to create definition between foreground and background")
    ColorSequence.fill_light = IntProperty(name="Fill Light", min=0, max=100,  update=Updaters.fill_light_updater, description="White, nuetral light to balance edges between key and rim lights")
    ColorSequence.texture_light = IntProperty(name="Texture Light", min=0, max=100,  update=Updaters.texture_light_updater, description="Faint light with gobo to create texture on surfaces without interfering with key light")
    ColorSequence.band_light = IntProperty(name="Band Light", min=0, max=100,  update=Updaters.band_light_updater, description="Strongly saturated light for the band to create mood")
    ColorSequence.accent_light = IntProperty(name="Accent Light", min=0, max=100,  update=Updaters.accent_light_updater, description="Color scheme typically should have only 1-2 colors, this being one of them")
    ColorSequence.energy_light = IntProperty(name="Energy Light", min=0, max=100,  update=Updaters.energy_light_updater, description="Intensity of lights on energy effect")
    ColorSequence.energy_speed = IntProperty(name="Energy Speed", min=0, max=500, update=Updaters.energy_speed_updater, description="Speed of energy effect")
    ColorSequence.energy_scale = IntProperty(name="Energy Scale", min=0, max=500, update=Updaters.energy_scale_updater, description="Scale of energy effect")
    ColorSequence.background_light = IntProperty(name="Background Light", min=0, max=100,  update=Updaters.background_light_updater, description="Background light intensity, typically for cyclorama or uplights. Change the colors on console, not here")
    ColorSequence.background_light_one = IntProperty(name="Background Light 1", min=0, max=100,  update=Updaters.background_light_updater, description="Background light intensity, typically for cyclorama or uplights. Change the colors on console, not here")
    ColorSequence.background_light_two = IntProperty(name="Background Light 2", min=0, max=100,  update=Updaters.background_two_light_updater, description="Use these additional slots if you're controlling backdrop color by varying intensity of multiple channels with different color gels")
    ColorSequence.background_light_three = IntProperty(name="Background Light 3", min=0, max=100,  update=Updaters.background_three_light_updater, description="Use these additional slots if you're controlling backdrop color by varying intensity of multiple channels with different color gels")
    ColorSequence.background_light_four = IntProperty(name="Background Light 4", min=0, max=100,  update=Updaters.background_four_light_updater, description="Use these additional slots if you're controlling backdrop color by varying intensity of multiple channels with different color gels")
    ColorSequence.band_color = FloatVectorProperty(name="Band Color", subtype='COLOR', size=3, min=0.0, max=1.0, default=(1.0, 1.0, 1.0), description="Dummy, reference color only. Does not control console parameters")
    ColorSequence.accent_color = FloatVectorProperty(name="Accent Color", subtype='COLOR', size=3, min=0.0, max=1.0, default=(1.0, 1.0, 1.0), description="Dummy, reference color only. Does not control console parameters")
    ColorSequence.background_color = FloatVectorProperty(name="Background Color", subtype='COLOR', size=3, min=0.0, max=1.0, default=(1.0, 1.0, 1.0), description="Dummy, reference color only. Does not control console parameters")
    ColorSequence.cue_builder_effect_id = StringProperty(name="")
    ColorSequence.key_is_recording = BoolProperty(
        name="", 
        description="Record presets when pose buttons are red", 
        default = False
    ) 
    ColorSequence.rim_is_recording = BoolProperty(
        name="", 
        description="Record presets when pose buttons are red", 
        default = False
    ) 
    ColorSequence.fill_is_recording = BoolProperty(
        name="", 
        description="Record presets when pose buttons are red", 
        default = False
    ) 
    ColorSequence.texture_is_recording = BoolProperty(
        name="", 
        description="Record presets when pose buttons are red", 
        default = False
    ) 
    ColorSequence.band_is_recording = BoolProperty(
        name="", 
        description="Record presets when pose buttons are red", 
        default = False
    ) 
    ColorSequence.accent_is_recording = BoolProperty(
        name="", 
        description="Record presets when pose buttons are red", 
        default = False
    ) 
    ColorSequence.cyc_is_recording = BoolProperty(
        name="", 
        description="Record presets when pose buttons are red", 
        default = False
    ) 


    # Flash strips
    ColorSequence.flash_input = StringProperty(name="", description="Type in what feels natural as a request for a flash up. It IS the software's job to read your mind", update=Updaters.flash_input_updater)
    ColorSequence.flash_down_input = StringProperty(name="", description="Type in the second half of the flash, which tells Sorcerer what to do to flash back down", update=Updaters.flash_down_input_updater)
    ColorSequence.flash_input_background = StringProperty(name="",)
    ColorSequence.flash_down_input_background = StringProperty(name="",)
    ColorSequence.start_flash_macro_number = IntProperty(name="", min=0, max=99999, description="This is the macro number on the console that Alva will use to fire the beginning of the flash", update=Updaters.motif_property_updater)
    ColorSequence.end_flash_macro_number = IntProperty(name="", min=0, max=99999, description="This is the macro number on the console that Alva will use to fire the end of the flash", update=Updaters.motif_property_updater)
    ColorSequence.frame_middle = IntProperty(name="", min=-100000, max=100000, default=0)
    ColorSequence.flash_bias = IntProperty(name="", min=-49, max=49, default=0, description="This allows you to make the flash start with a rapid fade up and then fade down slowly and vise-versa", update=Updaters.motif_property_updater)
    ColorSequence.flash_prefix = StringProperty(name="", default="")
    ColorSequence.start_flash = StringProperty(name="", default="")
    ColorSequence.end_flash = StringProperty(name="", default="")
    ColorSequence.flash_type_enum = EnumProperty(
        items=AlvaItems.flash_types,
        name="Flash Types",
        description="Choose how to create flashes",
        default=0
    )
    ColorSequence.int_up_preset_assignment = IntProperty(name="Flash up Preset")
    ColorSequence.int_down_preset_assignment = IntProperty(name="Flash up Preset")


    # Animation strips
    Scene.bake_panel_toggle = BoolProperty(
        name="Oven", 
        description="Use this to store animation data locally on the console", 
        default = False
    ) 
    ColorSequence.animation_cue_list_number = IntProperty(default=10, min=2, max=99999)
    ColorSequence.animation_event_list_number = IntProperty(default=10, min=2, max=99999)
    ColorSequence.execute_animation_on_cue_number = IntProperty(name="", min=0, max=10000, description="Specifies which cue will start (or enable) the timecode clock")
    ColorSequence.execute_animation_with_macro_number = IntProperty(name="", min=0, max=100000, description="Specifies which macro number to build to use to start the timecode clock on the console")
    ColorSequence.disable_animation_on_cue_number = IntProperty(name="", min=0, max=10000, update=Updaters.timecode_clock_update_safety, description="Specifies which cue will stop (or disable) the timecode clock")
    ColorSequence.disable_animation_with_macro_number = IntProperty(name="", min=0, max=100000, description="Specifies which macro number to build to use to start the timecode clock on the console")
    

    # Trigger strips
    ColorSequence.trigger_prefix = StringProperty(name="", default="/eos/newcmd", description="Prefix, aka address, is the first half of an OSC message. The top three fields here will definitely work on any console brand/type that has an OSC input library", update=Updaters.motif_property_updater)
    ColorSequence.osc_trigger = StringProperty(name="", description="This argument will be fired with the above prefix when frame 1 of the strip comes up in the sequencer. The top three fields here will definitely work on any console brand/type that has an OSC input library", update=Updaters.motif_property_updater)
    ColorSequence.osc_trigger_end = StringProperty(name="", description="This argument will be fired with the above prefix when the final frame of the strip comes up in the sequencer. The top three fields here will definitely work on any console brand/type that has an OSC input library", update=Updaters.motif_property_updater)


    # Offset strips
    ColorSequence.offset_type_enum = EnumProperty(
        items=AlvaItems.offset_types,
        name="Offset Types",
        description="Choose offset type",
        default=0
    )
    ColorSequence.offset_intensity = IntProperty(name="Intensity", description="Value to take the channels to.", default=0, min=0, max=100)
    ColorSequence.offset_zoom = IntProperty(name="Zoom", description="Zoom to take the channels to.", default=0, min=0, max=150)
    ColorSequence.offset_iris = IntProperty(name="Iris", description="iris to take the channels to.", default=100, min=0, max=100)
    ColorSequence.offset_color_palette = IntProperty(name="CP", description="CP to take the channels to.", default=1, min=1, max=99999)
    ColorSequence.offset_intensity_palette = IntProperty(name="IP", description="IP to take the channels to.", default=1, min=1, max=99999)
    ColorSequence.offset_focus_palette = IntProperty(name="FP", description="FP to take the channels to.", default=1, min=1, max=99999)
    ColorSequence.offset_beam_palette = IntProperty(name="BP", description="BP to take the channels to.", default=1, min=1, max=99999)
    ColorSequence.offset_channels = StringProperty(name="Offset Channels", description="Just type in the channels to offset. Use () for simultaneous offset groups")
    ColorSequence.offset_fade_time = FloatProperty(name="Fade Time", description="The fade time, or sneak time, for each channel when triggered, in seconds", default=.5, min=0)
    ColorSequence.use_macro = BoolProperty(name="Use Macro", default=False, update=Updaters.motif_property_updater)
    ColorSequence.offset_macro = IntProperty(name="Offsets Macro", min=0, max=99999, update=Updaters.motif_property_updater)
    ColorSequence.friend_list = StringProperty(default="", name="Offsets", description='Create offset effects by typing in the numbers of channels that should accompany the Start Strip in its action. Use () to separate concurrent offset groups. For example, 1-10 for 1 wipe or (1-5) (5-10) for 2 simultaneous wipes. Concurrent offset groups must be equal in number of channels')



def unregister():
    del Scene.command_line_label

    del ColorSequence.is_linked
    del ColorSequence.motif_name
    del ColorSequence.strip_length_proxy

    # Strip formatter
    del Scene.color_is_magnetic
    del Scene.strip_name_is_magnetic
    del Scene.channel_is_magnetic
    del Scene.duration_is_magnetic
    del Scene.start_frame_is_magnetic
    del Scene.end_frame_is_magnetic
    del Scene.is_filtering_left
    del Scene.is_filtering_right
    del Scene.channel_selector
    del Scene.generate_quantity
    del Scene.normal_offset
    del Scene.i_know_the_shortcuts
    del SoundSequence.song_bpm_input
    del SoundSequence.song_bpm_channel
    del SoundSequence.beats_per_measure

    # Sound strips
    del SoundSequence.song_timecode_clock_number
    del SoundSequence.execute_on_cue_number
    del SoundSequence.execute_with_macro_number
    del SoundSequence.disable_on_cue_number
    del SoundSequence.disable_with_macro_number
    del SoundSequence.audio_type_enum
    del SoundSequence.selected_stage_object
    del SoundSequence.selected_speaker
    del SoundSequence.speaker_sensitivity
    del SoundSequence.audio_object_activated
    del SoundSequence.dummy_volume
    del SoundSequence.audio_object_size
    del SoundSequence.int_mixer_channel

    # Macro strips
    del ColorSequence.start_frame_macro
    del ColorSequence.start_frame_macro_text
    del ColorSequence.start_frame_macro_text_gui
    del ColorSequence.end_frame_macro
    del ColorSequence.end_frame_macro_text
    del ColorSequence.end_frame_macro_text_gui
    del ColorSequence.start_macro_muted
    del ColorSequence.end_macro_muted

    # Cue strips
    del ColorSequence.eos_cue_number
    del ColorSequence.osc_auto_cue
    del Scene.livemap_label
    del Scene.cue_builder_toggle
    del Scene.cue_builder_id_offset
    del Scene.builder_settings_toggle
    del Scene.using_gels_for_cyc
    del Scene.is_updating_strip_color
    del Scene.key_light_groups
    del Scene.rim_light_groups
    del Scene.fill_light_groups
    del Scene.texture_light_groups
    del Scene.band_light_groups
    del Scene.accent_light_groups
    del Scene.energy_light_groups
    del Scene.cyc_light_groups
    del Scene.cyc_two_light_groups
    del Scene.cyc_three_light_groups
    del Scene.cyc_four_light_groups
    del ColorSequence.key_light
    del ColorSequence.rim_light
    del ColorSequence.fill_light
    del ColorSequence.texture_light
    del ColorSequence.band_light
    del ColorSequence.accent_light
    del ColorSequence.energy_light
    del ColorSequence.energy_speed
    del ColorSequence.energy_scale
    del ColorSequence.background_light_one
    del ColorSequence.background_light_two
    del ColorSequence.background_light_three
    del ColorSequence.background_light_four
    del ColorSequence.band_color
    del ColorSequence.accent_color
    del ColorSequence.background_color
    del ColorSequence.cue_builder_effect_id
    del ColorSequence.key_is_recording
    del ColorSequence.rim_is_recording
    del ColorSequence.fill_is_recording
    del ColorSequence.texture_is_recording
    del ColorSequence.band_is_recording
    del ColorSequence.accent_is_recording
    del ColorSequence.cyc_is_recording

    # Flash strips
    del ColorSequence.flash_input
    del ColorSequence.flash_down_input
    del ColorSequence.flash_input_background
    del ColorSequence.flash_down_input_background
    del ColorSequence.start_flash_macro_number
    del ColorSequence.end_flash_macro_number
    del ColorSequence.frame_middle
    del ColorSequence.flash_bias
    del ColorSequence.flash_prefix
    del ColorSequence.start_flash
    del ColorSequence.end_flash
    del ColorSequence.flash_type_enum
    del ColorSequence.int_up_preset_assignment
    del ColorSequence.int_down_preset_assignment

    # Animation strips
    del Scene.bake_panel_toggle
    del ColorSequence.animation_cue_list_number
    del ColorSequence.animation_event_list_number
    del ColorSequence.execute_animation_on_cue_number
    del ColorSequence.execute_animation_with_macro_number
    del ColorSequence.disable_animation_on_cue_number
    del ColorSequence.disable_animation_with_macro_number

    # Trigger strips
    del ColorSequence.trigger_prefix
    del ColorSequence.osc_trigger
    del ColorSequence.osc_trigger_end

    # Offset strips
    del ColorSequence.friend_list
    del ColorSequence.offset_macro
    del ColorSequence.use_macro