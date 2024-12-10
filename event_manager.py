# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.app.handlers import persistent
import time

from .assets.dictionaries import Dictionaries
from .cpv.find import Find
from .cpv.harmonize import Harmonizer
from .maintenance.logging import alva_log
from .utils.audio_utils import render_volume
from .utils.event_utils import EventUtils as Utils
from .utils.osc import OSC
from .utils.sequencer_mapping import StripMapping


stored_channels = set()


'''
__________________________________________________________________________________
EVENT MANAGER OBJECTIVES:

This script is here to define what happens on events like play, stop, 
scrub, frame change, and translate/transform. This script encompasses
3D audio and lighting, but most of the code is for lighting.

We need to basically simulate a full-blown theatrical lighting console
and Dolby Atmos sound system inside Blender. Unlike a lighting console,
Sorcerer works primarily with f-curves. That presents many unique 
challenges. 

    Objective 1. Harmonize.
        Traditional animation is different from ALVA lighting animation
        because traditional 3D animation doesn't usually require 
        controlling hundreds of completely separate objects at once, 
        outside simulations at least. For this reason, we need to use
        a controller-based approach where you control objects more 
        indirectly. However, you can have hundreds of different controllers, 
        and each controller can target whatever it wants whenever it wants.
        As a result, they can tend to disagree. So we need to harmonize
        the disagreements so we don't spam the lighting console with 
        contradictory commands. We also want to simplify them as best
        we can to minimize bandwidth usage. We even give the user 
        "freezing" options they can use to make individual controllers
        only go every other frame or every third frame.

    Objective 2. Sync.
        We need to keep the lighting console's timecode clock in sync with 
        Blender's timecode clock during playback. We do this with singular
        OSC commands, not by actually streaming a continuous timecode 
        signal. This way, it's far, far simpler for the end user. It even 
        works through WiFi. We can get away with this where others can't 
        because Sorcerer is not intended for realtime use at FOH during 
        final shows. It's a lot like how you don't keep a video editor
        open when you show a movie to an audience. You instead render out
        the movie, close the video editor (in this case Sorcerer), and play
        back the movie with something else that's far better for a realtime,
        high stress, high reliability environment.

        In addition to just keeping timecode in sync, we also have little
        optional things we'd like to do on play and on stop. For example,
        turning the house lights down a little on play, turning them back
        up on stop, firing the latest cue in the sequencer if we are starting
        from the middle of a cue sequence (otherwise you would have to 
        constantly scrub backwards to fire the most relevant cue or the stage
        may look completely wrong for the moment you're working on.) The 
        user can turn all these things off and on in Sorcerer Preferences.

    Objective 3. Fix Blender's Depsgraph.
        Blender's depsgraph system does not automatically run the updaters
        of custom properties when they are updated by fcurves during frame 
        change or playback. That means we need to sort of build our own 
        depsgraph system that just looks for stuff that changed since the 
        last frame. That way we know what stuff needs to be done during frame
        change.

    Objective 4 (solved by orb.py).
        Say you use Sorcerer to make a super emotional, lifelike, fluid,
        organic, natural, and lively lighting animation that is so amazing
        that no one has ever seen stage lights move, dance and breath the way
        you just made them move, dance, and breath. But the problem you
        now have is that Blender does this stuff by sending a crap ton of
        OSC commands. It's not very reliable. It lags. It's slow. It really
        stinks for continuous, real-time playback. It's fine for design work
        but certainly not for the final show. It's like video editors: the 
        playback inside the video editor kind of stinks until you render the 
        video. So we need a way to get all the animation stuff (and other 
        types of stuff) from Blender onto the console where it can be 
        "played back" reliably.

        If you want to play a Blender animation on a lighting console, you 
        can't just load the .blend file on the lighting console and merge 
        the f-curve data onto, well, there's nothing to merge it to. Lighting 
        consoles kinda sorta do super simple curves in their effect editors, 
        but those are extremely primitive compared to the graph editors in 3D 
        animation suites like Blender and Maya. So we need a way to force-feed 
        this f-curve data down the console's throat in a way it can understand.

        So what we do is we basically have this automatic Orb assistant 
        manually animate the sequence on the console frame-by-frame by hitting 
        record cue for every frame. And then we bind each cue to the right 
        timecode frame on the console's event list.

        We call the end result a "qmeo". A qmeo is like a video, but every 
        frame is a lighting cue, not a picture. To make a qmeo actually work, 
        we need 3 things:

            a. The console needs to have the cue for each timecode frame
               stored on its own hard drive, preferably in an out-of-the-way
               cue list. The cue transition time needs to reflect the frame
               rate.

            b. The console needs to have an event list that binds each cue
               to its respective timecode frame. This way we don't have to
               worry about them getting out of sync from using imprecise 
               cue timings.

            c. The user needs an extremely simple way to record and play 
               back these qmeos. Preferably the user is able to just go to
               a specific cue or fire a specific macro. The qmeo plays, the
               qmeo finishes, and the qmeo stops its own clock when its done
               so that the user doesn't have to.

            d. While Sorcerer is building a qmeo, the user needs to be able
               to escape out of that process without terminating Blender. 
               Especially if they accidentally started to build a super long
               qmeo.

        We solve all these problems with the Orb assistant. Most buttons 
        in Sorcerer's UI that use the purple orb icon are Orb operators. 
        See orb.py to learn how we do it.


    Objective 5 (solved by the CPV folder).
        Sorcerer is almost its own full blown lighting console with its own army 
        of different controller types that can all be trying to do stuff to the 
        same stuff at once. That creates two problems:
         
            1. Sorcerer does not send DMX, it doesn't have a patch page,
               but it still needs to know things about specific fixtures or 
               its commands to the lighting console won't make any sense.

            2. We can't have all our controllers speaking whatever language they 
               choose. They need to all speak the same language. That language is 
               called CPV. A CPV request is a tuple in the form of

               (Channel, Parameter, Value)

        Every single controller that ever wants to make a change to a parameter
        on the console must make a change request in the CPV format. This 
        is how we keep everything sorted out in the data flow.

        We need to keep this so organized because we often need to do a ton of 
        stuff to the requests to make them kosher for the fixture on the console.
        For example, mapping values to the right min/max, appending appropriate 
        enable and disable commands for things like strobe (we definitely don't
        want the user to have to manually enable such things. If they increase 
        strobe value, we can reasonably infer they want the strobe on), and 
        setting the argument to be relative or absolute based on the controller
        type. We complete all these operations at various stages, so the CPV
        format is very important.

        See the cpv folder to see how we manage the primary control flow.

        
    Objective 6. 3D Audio Panner.
        This is currently out of order, but will be repaired soon. If you need 
        it, go back to Alva Sequencer where it still works.

        Actually just kidding, it's fixed now, just need to update this...


Hopefully that provides you a general idea of what Sorcerer does, what kinds 
of problems it solves, and how it solves them. Below is a more in-depth,
technical documentation that is referenced within this script at each stage.


__________________________________________________________________________________ 
DOCUMENTATION CODE A1
Sequence of events when frame changes BEGINS and we are NOT in playback:

    A1:3. We bind the publisher to the harmonizer so that any conflicts 
          throughout the entire scene can be harmonized...

    A1:3.1 We trigger any drivers that may need to run, since Blender
           doesn't automatically fire their updaters.

    A1:3.2 We trigger any controllers set to Dynamic that may need to run, 
           since Blender doesn't automatically fire their updaters.
    
    A1:1. We look for normal ALVA controllers in the scene...
    
    A1:2. We look for updates in parameters on those controllers...
       
    A1:4. We trigger the cpv generator for those parameters...
    
    A1:5. The cpv generator creates Channel, Parameter, Value (CPV) tuple 
          requests and adds to global change_requests...
       
    A1:6. We unbind the updater from the harmonizer so that manual updates 
          can fire normally
    
    A1:7. We delete our list of controllers since we are not in playback.
          They may have changed by next frame change, so no need to keep...
       
    A1:8. And we update the livemap preview to show user what the current 
          livemap cue is in the Sequencer header display.
       
       
    DOCUMENTATION CODE A2 TODO: This needs to be updated post CPVIA => CPV
    Then, when the frame change has COMPLETED, meaning all CPV requests are in:
           
        A2:1. Then, we take global change_requests...
        
        A2:2. We harmonize and simplify those cpv's with the harmonizer...
        
        A2:3. We convert the cpv's to (address, argument) with the publisher...
        
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
        self.mixers_and_motors = []
        
        
    #-------------------------------------------------------------------------------------------------------------------------------------------
    '''Depsgraph PRE and Frame Change PRE handler'''
    #-------------------------------------------------------------------------------------------------------------------------------------------
    def render_audio_objects(self, scene):
        if not hasattr(scene, "sequence_editor") or not scene.sequence_editor:
            return
        
        for strip in scene.sequence_editor.sequences_all:
            if strip.type == 'SOUND' and not strip.selected_stage_object:
                sound_object = bpy.data.objects[strip.selected_stage_object.name]

                for speaker_list in sound_object.speaker_list:
                    if speaker_list.name == strip.name:
                        for speaker in speaker_list.speakers:
                            speaker.dummy_volume = render_volume(speaker.speaker_pointer, sound_object, strip.int_sound_cue)


    #-------------------------------------------------------------------------------------------------------------------------------------------
    '''Depsgraph POST handler'''
    #-------------------------------------------------------------------------------------------------------------------------------------------
    def find_transform_updates_and_trigger_cpv(self, scene, depsgraph):
        '''Starts CPV updates on meshes currently transforming.'''
        if not depsgraph or scene.scene_props.in_frame_change or scene.scene_props.is_playing:
            return
        
        alva_log("event_manager", f"Depsgraph POST handler called. in_frame_change: {scene.scene_props.in_frame_change}")

        for update in depsgraph.updates:
            obj = update.id
            if not isinstance(obj, bpy.types.Object):
                continue

            if obj.object_identities_enum not in ["Influencer", "Brush"]:
                continue

            if update.is_updated_transform:
                start = time.time()
                alva_log("event_manager", f"Transform found for object {obj}. Triggering special update.")
                Utils.trigger_special_update(obj)
                alva_log('time', f"TIME: trigger_special_update and is_updated_transform took {time.time() - start} seconds")
                
                if obj.int_alva_sem != 0:
                    alva_log("event_manager", f"Triggering SEM update for {obj}.")
                    Utils.trigger_sem(obj, obj.int_alva_sem)

        start = time.time()
        updated_objects = {update.id for update in depsgraph.updates if isinstance(update.id, bpy.types.Object)}
        alva_log("event_manager", f"Updated objects from depsgraph_post: {updated_objects}")
        Utils.check_and_trigger_drivers(updated_objects)
        alva_log('time', f"TIME: check_and_trigger_drivers took {time.time() - start} seconds")


    #-------------------------------------------------------------------------------------------------------------------------------------------
    '''Frame Change PRE handlers'''
    #-------------------------------------------------------------------------------------------------------------------------------------------
    def timecode_scrubbing_and_fire_strip_mapping(self, scene):
        if scene.scene_props.is_playing and scene.sync_timecode:
            current_frame = scene.frame_current
            if abs(current_frame - self.last_frame) > 1 and self.last_frame != -1:
                '''C2:1'''
                Utils.on_scrub_detected(current_frame)
                alva_log("event_manager", "Scrub Detected.")
                
            self.last_frame = current_frame
        

        # Trigger-strips.
        '''B1:1-2'''
        frame = scene.frame_current
        if self.start_mapping and frame in self.start_mapping:
            for trigger_prefix, osc_trigger in self.start_mapping[frame]:
                OSC.send_osc_lighting(trigger_prefix, osc_trigger, user=0)

        if self.offset_start_mapping and frame in self.offset_start_mapping:
            for item in self.offset_start_mapping[frame]:
                try:
                    trigger_prefix, osc_trigger = item
                    OSC.send_osc_lighting(trigger_prefix, osc_trigger, user=0)
                except ValueError as e:
                    print(f"Error: {e}")

        if self.end_mapping and frame in self.end_mapping: # Trigger strip end frame.
            for trigger_prefix, osc_trigger_end in self.end_mapping[frame]:
                OSC.send_osc_lighting(trigger_prefix, osc_trigger_end, user=0) 


    def fire_parameter_updaters(self, scene):
        alva_log("event_manager", f"frame_change_pre firing in fire_parameter_updaters. Frame is: {scene.frame_current}.")

        '''DOCUMENTATION CODE A1'''
        '''A1:3'''
        Utils.use_harmonizer(True)

        '''A1:3.1'''
        objects_with_drivers = {obj for obj in scene.objects if obj.animation_data and obj.animation_data.drivers}
        Utils.check_and_trigger_drivers(objects_with_drivers)

        '''A1:3.2'''
        dynamic_objects = {obj for obj in scene.objects if obj.animation_data and (obj.object_identities_enum in ["Influencer", "Brush"] or obj.int_alva_sem != 0)}
        for obj in dynamic_objects:
            Utils.trigger_special_update(obj)
            if obj.int_alva_sem != 0:
                Utils.trigger_sem(obj, obj.int_alva_sem)

        if not scene.scene_props.is_playing or not self.controllers:
            '''A1:1 and B1:3'''
            self.controllers, self.mixers_and_motors = Find.find_controllers(scene)

        Utils.trigger_special_mixer_props(self.mixers_and_motors)

        current_controllers = self.controllers
        alva_log("event_manager", f"Current controllers: {current_controllers}")
        
        new_graph = Utils.convert_to_props(scene, current_controllers)
        '''A1:2'''
        updates = Utils.find_updates(self.old_graph, new_graph)
        alva_log("event_manager", f"Updates: {updates}")
        
        '''A1:4,6'''
        Utils.fire_updaters(updates)
        Utils.use_harmonizer(False)
        
        self.old_graph = new_graph
        
        if not scene.scene_props.is_playing:
            '''A1:7'''
            self.controllers = []
            self.mixers_and_motors = []
            

    def update_livemap(self, scene):
        context = bpy.context
        if not context.screen or bpy.context.screen.is_animation_playing:
            return

        active_strip = context.scene.sequence_editor.active_strip
        current_frame = context.scene.frame_current
        
        if not active_strip:
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
            OSC.send_osc_lighting(house_prefix, house_down_argument, user=0)

        # Get trigger maps
        '''C1:2'''
        self.start_mapping = StripMapping.get_trigger_start_map(scene)
        self.offset_start_mapping = StripMapping.get_trigger_offset_start_map(scene)
        self.end_mapping = StripMapping.get_trigger_end_map(scene)

        # Go timecode sync.
        if scene.sync_timecode:
            '''C1:3'''
            relevant_lighting_clock_object, relevant_sound_strip = Utils.find_relevant_clock_objects(scene)

            if relevant_lighting_clock_object:
                current_frame = scene.frame_current
                fps = Utils.get_frame_rate(scene)
                lag = scene.timecode_expected_lag
                timecode = Utils.frame_to_timecode(current_frame+lag, fps)
                int_fps = int(fps)
                clock = relevant_lighting_clock_object.int_event_list
                '''C1:4'''
                OSC.send_osc_lighting("/eos/newcmd", f"Event {clock} / Frame_Rate {int_fps} Enter", user=0)
                OSC.send_osc_lighting("/eos/newcmd", f"Event {clock} / Internal Time {timecode} Enter, Event {clock} / Internal Enable Enter", user=0)

                if hasattr(relevant_sound_strip, "int_sound_cue"):
                    OSC.send_osc_audio(f"/cue/{relevant_sound_strip.int_sound_cue}/start", "")

        # Go livemap.
        '''C1:5'''
        if scene.sequence_editor and scene.is_armed_livemap:
            current_frame = scene.frame_current  
            active_strip = scene.sequence_editor.active_strip
            relevant_cue_strip = Utils.find_livemap_cue(scene, current_frame, active_strip)

            if relevant_cue_strip:
                eos_cue_number_selected = relevant_cue_strip.eos_cue_number
                OSC.send_osc_lighting("/eos/newcmd", f"Go_to_Cue {eos_cue_number_selected} Time 1 Enter", user=0)
                scene.livemap_label = f"Livemap Cue: {eos_cue_number_selected}"
                return 


    #-------------------------------------------------------------------------------------------------------------------------------------------
    '''Playback STOP handler'''
    #-------------------------------------------------------------------------------------------------------------------------------------------
    def end_timecode_session(self, scene):
        CMD_ADDRESS = "/eos/newcmd"
        INTERNAL_DISABLE = "Event $ / Internal Disable Enter"
        PAUSE_SOUND = "/cue/$/pause"
        
        '''DOCUMENTATION CODE C3'''
        scene.scene_props.is_playing = False
        
        # Go house up.
        if scene.house_up_on_stop:
            '''C3:1'''
            house_prefix = scene.house_prefix
            house_up_argument = scene.house_up_argument
            OSC.send_osc_lighting(house_prefix, house_up_argument, user=0)
        
        # End timecode.    
        if scene.sync_timecode:
            '''C3:2'''
            relevant_lighting_clock_object, relevant_sound_strip = Utils.find_relevant_clock_objects(scene)
                
            if relevant_lighting_clock_object:
                clock = relevant_lighting_clock_object.int_event_list
                OSC.send_osc_lighting(CMD_ADDRESS, INTERNAL_DISABLE.replace("$", clock), user=0)

                if hasattr(relevant_sound_strip, "int_sound_cue"):
                    OSC.send_osc_audio(PAUSE_SOUND.replace("$", relevant_sound_strip.int_sound_cue), "")

        '''C3:3'''
        self.start_mapping = None
        self.offset_start_mapping = None
        self.end_mapping = None

    
    #-------------------------------------------------------------------------------------------------------------------------------------------
    '''Frame Change POST handler'''
    #-------------------------------------------------------------------------------------------------------------------------------------------     
    def publish_pending_cpv_requests(self, scene):
        '''DOCUMENTATION CODE A2'''
        '''A2:1'''
        from .cpv.publish import change_requests

        '''A2:2'''
        alva_log("harmonize", f"HARMONIZER SESSION:\nchange_requests: {[request[1:] for request in change_requests]}")
        no_duplicates = Harmonizer.remove_duplicates(change_requests)
        alva_log("harmonize", f"no_duplicates: {[request[1:] for request in no_duplicates]}")
        if scene.scene_props.is_democratic:
            no_conflicts = Harmonizer.democracy(no_duplicates)
            alva_log("harmonize", f"Democratic. no_conflicts: {[request[1:] for request in no_conflicts]}")
        else:
            no_conflicts = Harmonizer.highest_takes_precedence(no_duplicates)
            alva_log("harmonize", f"HTP. no_conflicts: {[request[1:] for request in no_conflicts]}")
        simplified = Harmonizer.simplify(no_conflicts)
        alva_log("harmonize", f"simplified: {[request[1:] for request in simplified]}\n")

        '''A2:3'''
        from .cpv.publish import Publish, clear_requests
        for request in simplified:
            publisher = Publish(*request, is_harmonized=True)
            '''A2:4'''
            publisher.execute()

        if not scene.scene_props.is_playing:
            scene.scene_props.in_frame_change = False

        '''A2:5'''
        clear_requests()


event_manager_instance = EventManager()


@persistent
def load_macro_buttons(string): # bpy passes string, but we don't need it here.
    '''This is for the UI List that gives the user the known macro buttons to choose from in Text Editor when
       they use QWERTY to write Eos macros. You can just type them in with QWERTY, but you have these to click
       as well. This needs to run from Sorcerer's main __init__.py because it needs to run from the correct
       bpy.context. It also needs to have already run before the user has a chance to go over there and look
       at it and catch it empty. User should not come up to an empty UI List here.'''
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
    event_manager_instance.find_transform_updates_and_trigger_cpv(scene, depsgraph)

@persistent
def on_frame_change_pre(scene):
    start = time.time()
    event_manager_instance.timecode_scrubbing_and_fire_strip_mapping(scene)
    event_manager_instance.fire_parameter_updaters(scene)
    event_manager_instance.update_livemap(scene)
    event_manager_instance.render_audio_objects(scene)
    alva_log('time', f"TIME: on_frame_change_pre took {time.time() - start} seconds")

@persistent
def on_animation_playback(scene):
    event_manager_instance.start_timecode_session(scene)

@persistent
def on_animation_playback_end(scene):
    event_manager_instance.end_timecode_session(scene)

@persistent
def on_frame_change_post(scene):
    event_manager_instance.publish_pending_cpv_requests(scene)
          
                    
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
