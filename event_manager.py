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
from bpy.app.handlers import persistent

from .utils.event_utils import EventUtils as Utils
from .utils.utils import Utils as NormalUtils
from .cpvia.find import Find
from .cpvia.cpvia_finders import CPVIAFinders
from .assets.sli import SLI
from .utils.osc import OSC
from .cpvia.harmonizer import Harmonizer
from .utils.sequencer_mapping import StripMapping
from .assets.dictionaries import Dictionaries


change_requests = []
stored_channels = set()


'''
__________________________________________________________________________________ 
DOCUMENTATION CODE A1
Sequence of events when frame changes BEGINS and we are NOT in playback:
    
    A1:1. We look for ALVA controllers in the scene...
    
    A1:2. We look for updates in parameters on those controllers...
       
    A1:3. We bind the publisher to the harmonizer so that any conflicts 
          throughout the entire scene can be harmonized...
       
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
    
    C1:4. We fire OSC to start the console clock with the sequencer's 
          clock...
       
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

                if obj.object_identities_enum in {"Influencer", "Brush", "Stage Object"}:
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
        if not scene.scene_props.is_playing or not self.controllers:
            '''A1:1 and B1:3'''
            self.controllers = Find.find_controllers(scene)
        
        current_controllers = self.controllers
        
        new_graph = Utils.convert_to_props(scene, current_controllers)
        '''A1:2'''
        updates = Utils.find_updates(self.old_graph, new_graph)
        
        '''A1:3,4,6'''
        Utils.use_harmonizer(True)
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
        '''C1:2''' # No instance
#        self.start_mapping = None
#        self.offset_mapping = None
#        self.end_mapping = None
        self.start_mapping = StripMapping.get_trigger_start_map(scene)
        self.offset_start_mapping = StripMapping.get_trigger_offset_start_map(scene)
        self.end_mapping = StripMapping.get_trigger_end_map(scene)
             
        # Go timecode sync.    
        if scene.sync_timecode:
            '''C1:3'''
            relevant_sound_strip = Utils.find_relevant_clock_strip(scene)
            
            if relevant_sound_strip:
                current_frame = scene.frame_current
                fps = NormalUtils.get_frame_rate(scene)
                lag = scene.timecode_expected_lag
                timecode = NormalUtils.frame_to_timecode(current_frame+lag, fps)
                clock = relevant_sound_strip.song_timecode_clock_number
                '''C1:4'''
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
            relevant_sound_strip = Utils.find_relevant_clock_strip(scene)
                
            if relevant_sound_strip:
                clock = relevant_sound_strip.song_timecode_clock_number
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
        global change_requests

        '''A2:2'''
        no_duplicates = Harmonizer.remove_duplicates(change_requests)
        if scene.scene_props.is_democratic:
            no_conflicts = Harmonizer.democracy(no_duplicates)
        else:
            no_conflicts = Harmonizer.highest_takes_precedence(no_duplicates)
        simplified = Harmonizer.simplify(no_conflicts)

        '''A2:3'''
        publisher = Publisher()
        for request in simplified:
            address, argument = publisher.form_osc(*request)  # Should return 2 strings
            '''A2:4'''
            OSC.send_osc_lighting(address, argument) 
        
        if not scene.scene_props.is_playing:
            scene.scene_props.in_frame_change = False
            
        '''A2:5'''
        change_requests = []
        
      
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
    
    
## This is here for now because of dumb global variable stuff. Handling of change_requests global needs to be way less dumb.
class Publisher:
          
    def format_channel_and_value(self, c, v):
        """
        This function formats the channel and value numbers as string and then formats them
        in a way the console will understand (by adding a 0 in front of numbers 1-9.)
        """
        c = str(c)
        v = int(v)
        
        if v >= 0 and v < 10:
            v = f"0{v}"
        elif v < 0 and v > -10:
            v = f"-0{-v}"
        else:
            v = str(v)

        return c, v
    
    
    def format_channel(self, c):
        c = str(c)

        return c
    

    def format_value(self, v):
        """
        This function formats the channel and value numbers as string and then formats them
        in a way the console will understand (by adding a 0 in front of numbers 1-9.)
        """
        v = int(v)
        
        if v >= 0 and v < 10:
            v = f"0{v}"
        elif v < 0 and v > -10:
            v = f"-0{-v}"
        else:
            v = str(v)
        return v
        
        
    def form_osc(self, c, p, v, i, a):
        """
        This function converts cpvia into (address, argument) tuples.

        Parameters:
        cpvia: channel, parameter, value, influence, argument template.

        Returns:
        messages: A list of (address, argument) tuples.
        """
        address = "/eos/newcmd"

        color_profiles = {
            # Absolute Arguments
            "rgb": ["$1", "$2", "$3"],
            "cmy": ["$1", "$2", "$3"],
            "rgbw": ["$1", "$2", "$3", "$4"],
            "rgba": ["$1", "$2", "$3", "$4"],
            "rgbl": ["$1", "$2", "$3", "$4"],
            "rgbaw": ["$1", "$2", "$3", "$4", "$5"],
            "rgbam": ["$1", "$2", "$3", "$4", "$5"],

            # Raise Arguments
            "raise_rgb": ["$1", "$2", "$3"],
            "raise_cmy": ["$1", "$2", "$3"],
            "raise_rgbw": ["$1", "$2", "$3", "$4"],
            "raise_rgba": ["$1", "$2", "$3", "$4"],
            "raise_rgbl": ["$1", "$2", "$3", "$4"],
            "raise_rgbaw": ["$1", "$2", "$3", "$4", "$5"],
            "raise_rgbam": ["$1", "$2", "$3", "$4", "$5"],

            # Lower Arguments
            "lower_rgb": ["$1", "$2", "$3"],
            "lower_cmy": ["$1", "$2", "$3"],
            "lower_rgbw": ["$1", "$2", "$3", "$4"],
            "lower_rgba": ["$1", "$2", "$3", "$4"],
            "lower_rgbl": ["$1", "$2", "$3", "$4"],
            "lower_rgbaw": ["$1", "$2", "$3", "$4", "$5"],
            "lower_rgbam": ["$1", "$2", "$3", "$4", "$5"]
        }

        if p not in color_profiles:
            c, v = self.format_channel_and_value(c, v)
            address = address.replace("#", c).replace("$", v)
            argument = a.replace("#", c).replace("$", v)
        else:
            formatted_values = [self.format_value(val) for val in v]

            c = self.format_channel(c)
            argument = a.replace("#", c)
            
            for i, fv in enumerate(formatted_values):
                argument = argument.replace(color_profiles[p][i], str(fv))

        return address, argument
    
    
    def send_cpvia(self, c, p, v, i, a):
        """
        Decides whether to send osc now (we are not playing back) or later (we are playing back).

        Parameters:
        cpvia: channel, parameter, value, influence, argument template.

        This function does not return a value.
        """
        if bpy.context.scene.scene_props.is_playing or bpy.context.scene.scene_props.in_frame_change:
            global change_requests
            change_requests.append((c, p, v, i, a))
        else:
            address, argument = self.form_osc(c, p, v, i, a)  # Should return 2 strings
            OSC.send_osc_lighting(address, argument)
            
            
    def find_objects(self, chan):
        relevant_objects = []
        for obj in bpy.data.objects:
            if obj.int_object_channel_index == chan and chan != 1:
                relevant_objects.append(obj)
                pass
            try:
                number = CPVIAFinders._find_int(obj.name)
                if number == int(chan):
                    relevant_objects.append(obj)
            except:
                pass
        return relevant_objects
            
            
    def send_value_to_three_dee(self, parent, chan, param, val):
        """
        Adds material to relevant objects in 3d scene and sets material as that intensity or color.

        Parameters:
        val: Either float or tuple, depending on intensity or color

        This function does not return a value.
        """
        def find_val_type(val):
            if isinstance(val, (tuple, list)):
                return "color"
            elif isinstance(val, (int, float)):
                return "intensity"
            else:
                raise ValueError("Invalid value type")

        val_type = find_val_type(val)
        objects = self.find_objects(chan)
        
        if not objects:
            return
        
        if val_type == "intensity":
            for obj in objects:
                # Ensure the object has a material slot and create one if it doesn't
                if not hasattr(obj.data, "materials"):
                    continue
                
                if not obj.data.materials:
                    mat = bpy.data.materials.new(name="Intensity_Material")
                    obj.data.materials.append(mat)
                else:
                    mat = obj.data.materials[0]

                # Enable 'Use nodes'
                if not mat.use_nodes:
                    mat.use_nodes = True
                
                nodes = mat.node_tree.nodes
                links = mat.node_tree.links
                
                # Find existing emission node or create a new one
                emission = None
                for node in nodes:
                    if node.type == 'EMISSION':
                        emission = node
                        break
                if not emission:
                    emission = nodes.new(type='ShaderNodeEmission')
                    # Add material output node and link it to emission node
                    output = nodes.new(type='ShaderNodeOutputMaterial')
                    links.new(emission.outputs['Emission'], output.inputs['Surface'])

                # Get the current value
                input = emission.inputs['Strength']
                current_val = input.default_value
                    
                if param == "raise_intensity":
                    val = current_val + val * 0.01
                elif param == "lower_intensity":
                    val = current_val - val * 0.01
                else:
                    val *= 0.01
                    
                if val > 1:
                    val = 1
                elif val < 0:
                    val = 0
                    
                input.default_value = val

        elif val_type == "color":
            for obj in objects:
                if not hasattr(obj.data, "materials"):
                    continue
                
                # Ensure the object has a material slot and create one if it doesn't
                if not obj.data.materials:
                    mat = bpy.data.materials.new(name="Color_Material")
                    obj.data.materials.append(mat)
                else:
                    mat = obj.data.materials[0]

                # Enable 'Use nodes'
                if not mat.use_nodes:
                    mat.use_nodes = True
                
                nodes = mat.node_tree.nodes
                links = mat.node_tree.links

                # Find existing emission node or create a new one
                emission = None
                for node in nodes:
                    if node.type == 'EMISSION':
                        emission = node
                        break
                if not emission:
                    emission = nodes.new(type='ShaderNodeEmission')
                    # Add material output node and link it to emission node
                    output = nodes.new(type='ShaderNodeOutputMaterial')
                    links.new(emission.outputs['Emission'], output.inputs['Surface'])

                # Set the color value
                scaled_val = tuple(component * 0.01 for component in val)
                emission.inputs['Color'].default_value = (*scaled_val, 1)  # Assuming val is an (R, G, B) tuple

        else:
            SLI.SLI_assert_unreachable()