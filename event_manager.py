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
from bpy.app.handlers import persistent

from .utils.event_utils import EventUtils as Utils
from .utils.utils import Utils as NormalUtils
from .cpvia.find import Find
from .utils.osc import OSC
from .cpvia.harmonizer import Harmonizer
from .utils.sequencer_mapping import StripMapping
from .assets.dictionaries import Dictionaries


stored_channels = set()


'''
__________________________________________________________________________________ 
DOCUMENTATION CODE A1
Sequence of events when frame changes BEGINS and we are NOT in playback:

    A1:3. We bind the publisher to the harmonizer so that any conflicts 
          throughout the entire scene can be harmonized...

    A1:3.1 We trigger any drivers that may need to run, since Blender
           doesn't automatically fire their updaters.

    A1:3.2 We trigger any objects set to Dynamic that may need to run, 
           since Blender doesn't automatically fire their updaters.
    
    A1:1. We look for normal ALVA controllers in the scene...
    
    A1:2. We look for updates in parameters on those controllers...
       
    A1:4. We trigger the cpvia generator for those parameters...
    
    A1:5. The cpvia generator creates Channel, Parameter, Value, Influence
          Argument (CPVIA) tuple requests and adds to global change_requests...
       
    A1:6. We unbind the updater from the harmonizer so that manual updates 
          can fire normally
    
    A1:7. We delete our list of controllers since we are not in playback.
          They may have changed by next frame change, so no need to keep...
       
    A1:8. And we update the livemap preview to show user what the current 
          livemap cue is in the Sequencer header display.
       
       
    DOCUMENTATION CODE A2
    Then, when the frame change has COMPLETED, meaning all CPVIA requests are in:
           
        A2:1. Then, we take global change_requests...
        
        A2:2. We harmonize and simplify those cpvia's with the harmonizer...
        
        A2:3. We convert the cpvia's to (address, argument) with the publisher...
        
        A2:4. We send them to the console via Utils.osc.send_osc_lighting...
        
        A2:5. And we clear the global change_requests for next frame
        
__________________________________________________________________________________        
DOCUMENTATION CODE B1
Sequence of events when frame change BEGINS and we ARE in playback:
    
    B1:1. We look in the mapping for trigger strips for entries matching
          the current frame. 
          
    B1:2. If any are found, we send them to the lighting console.
    
    B1:3. The frame_change_pre will look for an existing list of controllers,
          since that list is only deleted if playback is false. If no 
          existing list of controllers is found because its the first frame
          of playback, it will create one and just not delete it.
       
    B1:4. A1:2-6; A2:1-5
    
__________________________________________________________________________________        
DOCUMENTATION CODE C1
Sequence of events when playback STARTS:
    
    C1:1. We send the house lights down, if that's enabled by user...
    
    C1:2. We create mapping of all strip events trigger strips...
    
    C1:3. We find the most relevant sound strip with a valid clock...
    
    C1:4. We fire OSC to set fps and start the console clock with the 
          sequencer's clock...
       
    C1:5. And we fire the livemap cue if enabled by user. (The rest
          is handled by frame change handlers, at least right now.
          In the future, we may add more mapping functionality to
          this handler to improve performance.)
       
       
    DOCUMENTATION CODE C2
    Sequence of events when a MANUAL SCRUB is detected DURING playback:
        
        C2:1. We fire OSC to update the timecode clock on the console
              to the new unexpected time.
        
               
    DOCUMENTATION CODE C3
    Sequence of events when playback STOPS:
        
        C3:1. We put the house lights back up, if enabled by user...
        
        C3:2. We stop the timecode clock on the console...
        
        C3:3. And we clear the mapping for trigger strips.
    
    
'''

class EventManager:
    def __init__(self):
        self.last_frame = -1
        
        self.start_mapping = None
        self.offset_start_mapping = None
        self.end_mapping = None
        
        self.old_graph = []
        self.controllers = []
        
        
    #-------------------------------------------------------------------------------------------------------------------------------------------
    '''Depsgraph PRE handler'''
    #-------------------------------------------------------------------------------------------------------------------------------------------
    def render_audio_objects(self, scene):
        '''This all needs to be redone. May also need to switch to deps post?'''
        if not hasattr(scene, "sequence_editor") or not scene.sequence_editor:
            return
        
        audio_objects = {}
        for strip in scene.sequence_editor.sequences_all:
            if strip.type == 'SOUND' and strip.audio_type_enum == "option_object" and strip.audio_object_activated:
                audio_objects[strip.sound.filepath] = (strip.selected_stage_object, strip.audio_object_size)

        for strip in scene.sequence_editor.sequences_all:
            if strip.type == 'SOUND' and strip.audio_type_enum == "option_speaker":
                if strip.sound.filepath in audio_objects:
                    empty, object_size = audio_objects[strip.sound.filepath]
                    speaker = strip.selected_speaker
                    if speaker and empty:
                        sensitivity = getattr(strip, 'speaker_sensitivity', 1)
                        strip.dummy_volume = Utils.render_volume(speaker, empty, sensitivity, object_size, strip.int_mixer_channel)


    #-------------------------------------------------------------------------------------------------------------------------------------------
    '''Depsgraph POST handler'''
    #-------------------------------------------------------------------------------------------------------------------------------------------
    def find_influencer_and_brush_updates(self, scene, depsgraph):
        '''Looks for internal Blender changes on meshes set to Influencer, Brush
           or Pan/Tilt type'''
        if not depsgraph:
            return

        updated_objects = {update.id for update in depsgraph.updates if isinstance(update.id, bpy.types.Object)}
        for update in depsgraph.updates:
            if isinstance(update.id, bpy.types.Object):
                obj = update.id

                if obj.object_identities_enum in {"Influencer", "Brush", "Stage Object", "Fixture"}:
                    if update.is_updated_transform:
                        Utils.trigger_special_update(obj)

        Utils.check_and_trigger_drivers(updated_objects)
        

    #-------------------------------------------------------------------------------------------------------------------------------------------
    '''Frame Change PRE handlers'''
    #-------------------------------------------------------------------------------------------------------------------------------------------
    def timecode_scrubbing_and_fire_strip_mapping(self, scene):
        if scene.scene_props.is_playing and scene.sync_timecode:
            current_frame = scene.frame_current
            if abs(current_frame - self.last_frame) > 1 and self.last_frame != -1:
                '''C2:1'''
                Utils.on_scrub_detected(current_frame)
                
            self.last_frame = current_frame
        

        # Trigger-strips.
        '''B1:1-2'''
        frame = scene.frame_current
        if self.start_mapping and frame in self.start_mapping:
            for trigger_prefix, osc_trigger in self.start_mapping[frame]:
                OSC.send_osc_lighting(trigger_prefix, osc_trigger)

        if self.offset_start_mapping and frame in self.offset_start_mapping:
            for item in self.offset_start_mapping[frame]:
                try:
                    trigger_prefix, osc_trigger = item
                    OSC.send_osc_lighting(trigger_prefix, osc_trigger)
                except ValueError as e:
                    print(f"Error: {e}")

        if self.end_mapping and frame in self.end_mapping: # Trigger strip end frame.
            for trigger_prefix, osc_trigger_end in self.end_mapping[frame]:
                OSC.send_osc_lighting(trigger_prefix, osc_trigger_end) 


    def fire_parameter_updaters(self, scene):
        '''DOCUMENTATION CODE A1'''
        '''A1:3'''
        Utils.use_harmonizer(True)

        '''A1:3.1'''
        objects_with_drivers = {obj for obj in scene.objects if obj.animation_data and obj.animation_data.drivers}
        Utils.check_and_trigger_drivers(objects_with_drivers)

        '''A1:3.2'''
        dynamic_objects = {obj for obj in scene.objects if obj.animation_data and obj.object_identities_enum in ["Influencer", "Brush"]}
        for obj in dynamic_objects:
            Utils.trigger_special_update(obj)

        if not scene.scene_props.is_playing or not self.controllers:
            '''A1:1 and B1:3'''
            self.controllers = Find.find_controllers(scene)
        
        current_controllers = self.controllers
        
        new_graph = Utils.convert_to_props(scene, current_controllers)
        '''A1:2'''
        updates = Utils.find_updates(self.old_graph, new_graph)
        
        '''A1:4,6'''
        Utils.fire_updaters(updates)
        Utils.use_harmonizer(False)
        
        self.old_graph = new_graph
        
        if not scene.scene_props.is_playing:
            '''A1:7'''
            self.controllers = []
            

    def update_livemap(self, scene):
        context = bpy.context
        if not context.screen or bpy.context.screen.is_animation_playing:
            return

        active_strip = context.scene.sequence_editor.active_strip
        current_frame = context.scene.frame_current
        
        if not not active_strip:
            return
        
        relevant_cue_strip = Utils.find_livemap_cue(scene, current_frame, active_strip)
                        
        if not relevant_cue_strip:
            scene.livemap_label = "Livemap Cue: "
            return 
        
        '''A1:8'''
        scene.livemap_label = f"Livemap Cue: {relevant_cue_strip.eos_cue_number}"
   
           
    #-------------------------------------------------------------------------------------------------------------------------------------------
    '''Playback START handler'''  
    #------------------------------------------------------------------------------------------------------------------------------------------- 
    def start_timecode_session(self, scene):
        '''DOCUMENTATION CODE C1'''
        scene.scene_props.is_playing = True

        # Go house down.
        '''C1:1'''
        if scene.house_down_on_play: 
            house_prefix = scene.house_prefix
            house_down_argument = scene.house_down_argument
            OSC.send_osc_lighting(house_prefix, house_down_argument)

        # Get trigger maps
        '''C1:2'''
        self.start_mapping = StripMapping.get_trigger_start_map(scene)
        self.offset_start_mapping = StripMapping.get_trigger_offset_start_map(scene)
        self.end_mapping = StripMapping.get_trigger_end_map(scene)

        # Go timecode sync.
        if scene.sync_timecode:
            '''C1:3'''
            relevant_clock_object = Utils.find_relevant_clock_object(scene)

            if relevant_clock_object:
                current_frame = scene.frame_current
                fps = NormalUtils.get_frame_rate(scene)
                lag = scene.timecode_expected_lag
                timecode = NormalUtils.frame_to_timecode(current_frame+lag, fps)
                int_fps = int(fps)
                clock = relevant_clock_object.int_event_list
                '''C1:4'''
                OSC.send_osc_lighting("/eos/newcmd", f"Event {clock} / Frame_Rate {int_fps} Enter")
                OSC.send_osc_lighting("/eos/newcmd", f"Event {clock} / Internal Time {timecode} Enter, Event {clock} / Internal Enable Enter")

        # Go livemap.
        '''C1:5'''
        if scene.sequence_editor and scene.is_armed_livemap:
            current_frame = scene.frame_current  
            active_strip = scene.sequence_editor.active_strip
            relevant_cue_strip = Utils.find_livemap_cue(scene, current_frame, active_strip)

            if relevant_cue_strip:
                eos_cue_number_selected = relevant_cue_strip.eos_cue_number
                OSC.send_osc_lighting("/eos/newcmd", f"Go_to_Cue {eos_cue_number_selected} Time 1 Enter")
                scene.livemap_label = f"Livemap Cue: {eos_cue_number_selected}"
                return 


    #-------------------------------------------------------------------------------------------------------------------------------------------
    '''Playback STOP handler'''
    #-------------------------------------------------------------------------------------------------------------------------------------------
    def end_timecode_session(self, scene):
        '''DOCUMENTATION CODE C3'''
        scene.scene_props.is_playing = False
        scene = bpy.context.scene
        
        # Go house up.
        if scene.house_up_on_stop == True:
            '''C3:1'''
            house_prefix = scene.house_prefix
            house_up_argument = scene.house_up_argument
            OSC.send_osc_lighting(house_prefix, house_up_argument)
        
        # End timecode.    
        if scene.sync_timecode:
            '''C3:2'''
            relevant_sound_strip = Utils.find_relevant_clock_object(scene)
                
            if relevant_sound_strip:
                clock = relevant_sound_strip.int_event_list
                OSC.send_osc_lighting("/eos/newcmd", f"Event {clock} / Internal Disable Enter")

        '''C3:3'''
        self.start_mapping = None
        self.offset_start_mapping = None
        self.end_mapping = None

    
    #-------------------------------------------------------------------------------------------------------------------------------------------
    '''Frame Change POST handler'''
    #-------------------------------------------------------------------------------------------------------------------------------------------     
    def publish_pending_cpvia_requests(self, scene):
        '''DOCUMENTATION CODE A2'''
        '''A2:1'''
        from .cpvia.publish import change_requests

        '''A2:2'''
        no_duplicates = Harmonizer.remove_duplicates(change_requests)
        if scene.scene_props.is_democratic:
            no_conflicts = Harmonizer.democracy(no_duplicates)
        else:
            no_conflicts = Harmonizer.highest_takes_precedence(no_duplicates)
        simplified = Harmonizer.simplify(no_conflicts)

        '''A2:3'''
        from .cpvia.publish import Publisher
        publisher = Publisher()
        for request in simplified:
            address, argument = publisher.form_osc(*request)  # Should return 2 strings
            '''A2:4'''
            OSC.send_osc_lighting(address, argument)

        if not scene.scene_props.is_playing:
            scene.scene_props.in_frame_change = False

        '''A2:5'''
        publisher.clear_requests()
        
      
event_manager_instance = EventManager()  # Must use () here for binding


@persistent
def load_macro_buttons(string):
    scene = bpy.context.scene
    scene.macro_buttons.clear()

    for button in Dictionaries.macro_buttons:
        item = scene.macro_buttons.add()
        item.name = button

@persistent
def on_depsgraph_update_pre(scene):    
    event_manager_instance.render_audio_objects(scene)

@persistent
def on_depsgraph_update_post(scene, depsgraph):
    event_manager_instance.find_influencer_and_brush_updates(scene, depsgraph)

@persistent
def on_frame_change_pre(scene):
    event_manager_instance.timecode_scrubbing_and_fire_strip_mapping(scene)
    event_manager_instance.fire_parameter_updaters(scene)
    event_manager_instance.update_livemap(scene)

@persistent
def on_animation_playback(scene):
    event_manager_instance.start_timecode_session(scene)

@persistent
def on_animation_playback_end(scene):
    event_manager_instance.end_timecode_session(scene)

@persistent
def on_frame_change_post(scene):
    event_manager_instance.publish_pending_cpvia_requests(scene)
          
                    
def register():
    bpy.app.handlers.load_post.append(load_macro_buttons)
    bpy.app.handlers.depsgraph_update_pre.append(on_depsgraph_update_pre)
    bpy.app.handlers.depsgraph_update_post.append(on_depsgraph_update_post)
    bpy.app.handlers.frame_change_pre.append(on_frame_change_pre)
    bpy.app.handlers.frame_change_post.append(on_frame_change_post)
    bpy.app.handlers.animation_playback_pre.append(on_animation_playback)
    bpy.app.handlers.animation_playback_post.append(on_animation_playback_end)


def unregister():
    bpy.app.handlers.load_post.remove(load_macro_buttons)
    bpy.app.handlers.depsgraph_update_pre.remove(on_depsgraph_update_pre)
    bpy.app.handlers.depsgraph_update_post.remove(on_depsgraph_update_post)
    bpy.app.handlers.frame_change_pre.remove(on_frame_change_pre)
    bpy.app.handlers.frame_change_post.remove(on_frame_change_post)
    bpy.app.handlers.animation_playback_pre.remove(on_animation_playback)
    bpy.app.handlers.animation_playback_post.remove(on_animation_playback_end)