**The Problem:**
============================================================================
Alva Theaters seeks to revolutionize technical theater by addressing a prevalent issue: hyper-specialization. In the current landscape—whether it’s high school theater, community theater, Broadway, live music, or the touring industry—technical theater is dominated by disparate systems. The lighting console differs from the audio mixer, and the video system is another entity altogether. This creates a 3rd party hodgepodge jungle. Putting together a tour or a new theater is akin to assembling a custom Windows PC from scratch.

This hyper-specialization shifts the focus away from artistic expression to technical sophistication, gear, workflows, and show file setup. The field attracts technically minded individuals and can alienate those with artistic talents. Consequently, many shows are optimized for and graded on their technical prowess rather than for their emotional and artistic impact. Even on the world stage, truly inspired and magical technical theater designs are rare. The technicals are so difficult, complicated and time-consuming. They shouldn't be.

**The Solution:**
-----------------------------------------------------------------------------
Alva Theaters aims to be the Apple of technical theater. We envision a network of theaters across America, each identical and featuring proprietary Alva technology. Our theaters will not use third-party hardware; instead, all technology will be Alva-designed and exclusive to our venues. This means no upgrades or modifications, ensuring a perfect, gorgeous user experience that resembles the sleek, unified design of a SpaceX Dragon capsule. All technical theater equipment is designed from the ground up using a first principles approach that asks, "What is the simplest possible version of the problem and how many parts, processes, and components can we delete?"

By standardizing our theaters, we can attract artistically minded professionals and enhance the quality of art.

**Question the Requirements:**
-----------------------------------------------------------------------------------
Here are the conventiona requirements that nearly all existing FOH hardware is constrained by:

- Transportability: Not required at Alva.
- Compatibility with external systems: Not required at Alva.
- Mass production for sales: Not required at Alva.
  
By eliminating these constraints, we can create an exotic, unparalleled control system. Our goal is to establish the best community theater on the planet and replicate it 100 times across America. This allows for perfect, rapid, national playback of technical theater designs, similar to how movies are distributed and shown in theaters nationwide.

**A Better Version of Time**
------------------------------------------------------------------------------
The life blood of the Alva way is animation, or keyframes. The lifeblood of traditional live performance is cues. 

**Cues:** These are requests to start doing something and do not a require a timecode clock to be running. These work best when humans are responsible for initiating control events.

**Keyframes:** These are iron chains that shackle a parameter to a certain value at a certain time on a clock. They require a timecode clock to be running. These work best for extremely precise control authority with respect to time.

Control via animation/keyframes is different from control via cues because keyframes offer a vastly superior degree of precision compared to cues. But the drawback is that they need a timecode clock to function. 

Alva Theaters prefers animation over cues because of the vastly superior precision that animation provides. One way to describe the precision is to watch any professional 3D animated film from a major studio like Walt Disney Animation Studios, Pixar, or Dreamworks. Think of the level of control precision they need to be able to make those 3D models come to life the way they do. You need a ludicrous amount of precision to make those models seem like they are alive and have feelings. Alva Sorcerer's job is to allow us to start using those same tools in technical theatre. And not just for lighting, but for the whole thing. That's why Alva stands for Animated Lighting, Video, and Audio. The goal is to make an External Multi-disciplinary Animation Renderer that can make people think the theater itself is alive and has feelings. For such is the perfection of technical theatre.




**Technical Overview for Developers:**
============================================================================

One goal of this part of the documentation is to introduce readers to the fairly bizzare world of Sorcerer from the engineering perspective. To get on the same page on what Sorcerer does, we need to talk about what exactly the software is actually trying to do. Basically, it's trying to emulate lighting consoles, audio mixers, and video switchers from one software. Right now it's mostly focused on the lighting console, but it does have some audio capability as well.

Sorcerer is kind of like a mixture between TouchOSC, common free sequence based DMX software, and ETC's iRFR remote control app. It's like TouchOSC because it communicates through OSC and is extremely powerful by connecting Eos to the mammoth toolkit of Blender. It's like common, free sequence-based DMX software because its sequencer component is fairly similar to a lot of sequence-based free dmx softwares. It's like the iRFR app and Trent Barclay's "Eos Remote" app because Sorcerer is specifically designed to commandeer ETC Eos family software. 

Sorcerer is different from all of those because you don't have to build your own controllers like in TouchOSC, because it's not DMX software, and because using Sorcerer is far more like using standalone DMX software than it is like using a typical remote control app. 

Sorcerer is most akin to Qlab. Like Qlab, it uses netwrok communication to remote control a plethora of other FOH hardware devices. However, unlike Qlab, Sorcerer thrives on keyframes and animation and curve graphs, not on cues. For this reason, QLab is best for simple sequences that rely on human cues, while Sorcerer is best for extremely complicated timecode sequences. This however is not to say that Sorcerer is not useful for extremely tasks as well.

Sorcerer is internally designated as an External Multi-disciplinary Animation Renderer (EMAR). This means that:
 - it externally remote-controls existing FOH hardware
 - it controls consoles in multiple disciplines, such as lighting consoles and audio mixing consoles
 - its primary means of control is animation, or keyframes, NOT cues (for this reason it is best for timecoded shows)
 - instead of running during the show, it renders its data into deliverables executed by dedicated FOH hardware

Alva Theaters is not aware of any other softwares that can claim the EMAR title. We hope that this changes, since this is an extremely exciting software category that needs competition. You know a software is an EMAR if it can commandeer and produce deliverables for an entire theater and if it primarily uses animation to do it.

In the future, Sorcerer will output .dtp files (Digital Theater Package files) that can be played back by the Renegade platform. Such .dtp files will contain ALVA designs (Animated Lighting, Video, and Audio).

We'll start by delving into the lighting side. Please note that this documentation is very much a work in progress.


**Non-Oscillating Effects:** 
-------------------------------------------------------------------------------------------
When you walk up to a lighting console and want to make it do a chase effect on the lights, you can do that super easily with a simple effect. Once you launch the effect, the effect will continue repeating forever and ever. Those we’ll call oscillating effects.

When you walk up to Sorcerer however, it doesn’t really work that way. In Sorcerer, to get the lights to do stuff and to continue doing stuff after you’ve left, you have to use Blender’s keyframes to animate them to do stuff. Then you have to hit play and loop the animation playback by shortening the timeline length. There’s no button to hit that just starts a constant chase effect. Sorcerer has no built-in oscillator.

Think of oscillating effects like a pot spinning on a potters wheel. It’s constantly spinning. You can change the speed of it, you can change the direction of it, but it’s constantly spinning. If you want to make a change, there are a ton of things you can do, but because it’s spinning, it’s really difficult to make super localized changes to only one very specific part of the pot. This system allows you to make relatively simple and repetitive pots very quickly. These oscillating effects are very useful in live situations where you need speed and rapid versatility, but you don’t need a ton of precision. 

Think of Sorcerer’s non-oscillating effects like a stationary sculpture. It’s not spinning, so you can carve away or add to any part you like at any time. There is no limitation to how you can make a change. In the context of lighting effects, this means you basically have what you might call “root access” to your lighting effects. You can change any tiny detail of your effect at any singular point in time and that change doesn’t have to repeat later on. These non-oscillating effects are very useful when you have slightly more time for designing and don’t need as much rapid versatility. These effects are great for creating extremely advanced timecode shows. 

Sorcerer’s non-oscillating effects are powered by Blender’s animation system, consisting of keyframes and its graph editor, non-linear action editor, and dope sheet screens. Blender’s animation system provides the organic, flowing precision needed to make 3D objects on a computer screen walk naturally, make people cry, and seem like real beings with real emotions. Sorcerer connects theatrical lighting consoles to the tools that provide that precision. 

The way we get that precision to the console itself is one of 2 ways: we can stream the data in real time over OSC, or we can record the animation onto the console frame by frame, cue by cue. Streaming in real-time at full speed via OSC can be slow and laggy, especially if the console can’t handle the bandwidth. That’s why we need to go slow, and often frame by frame. To playback at full speed at full strength, Sorcerer’s Orb feature allows us to create a Qmeo, defined above, with the press of a button. The non-oscillating effect is now stored on the console as an event list/cue list pair where each cue in the cue list represents a frame of the animation, while the event list is responsible for for firing the cues/frames in time with the correct frame rate. Now, a Sorcerer-created non-oscillating effect can be played back on the console like a normal effect. However, note that it is next to impossible to make meaningful changes to the qmeo without deleting and recreating the qmeo with Sorcerer.



**Basic Python Data Structure (For Beginners):**
------------------------------------------------------------------

**Class Inheritance:**
When we create a panel, operator, or anything else with the line class ALVA_OT_SomeOperator(bpy.types.Operator), we are actually creating a subclass of the built-in Python class bpy.types.Operator. The reason the execute method is called "execute" and not something else, like execute_operator(), is because the parent class Operator has the method execute, which is called by Blender’s lower-level UI code when the button is pressed. By defining our execute method, we are overriding that specific method in the parent class.

**Methods vs. Functions:**
A method in a class starts with the argument self and is written as def some_method(self, custom_argument). A function, on the other hand, does not include self and is defined as def some_function(custom_argument). In Sorcerer, many functions are placed within classes and may or may not need to inherit properties of the class defined in the class’s __init__(self) method. This distinction is crucial when calling a method or function from outside the class. For methods, an instance of the class must be created first (e.g., some_class = SomeClass(), followed by some_class.some_function()). For functions, you can call them directly from the class (e.g., SomeClass.some_function()).

**Decorators:**

@staticmethod: Turns a method into a function, removing the need for an instance to call it. This is useful for updaters and UI draws where self must refer to the original caller and not the class that houses the function.
@persistent: Used on global-level functions appended to Blender’s event handlers. It ensures that event handling continues to work even if the script is reloaded or the addon is reinstalled.
@classmethod: Used primarily for poll methods in panel classes, allowing the method to determine whether the class can be instantiated. Poll methods receive cls as the first argument, representing the class itself, and context for determining the appropriate UI context. These methods decide whether the panel should be shown.


**Now for the .py’s and folders.**
----------------------------------------------------------

**__init__.py:** Sorcerer’s __init__.py does not contain any runtime logic. It’s just the start sequencer. Its only job is to manage the linear dependency graph of the start sequence. It imports the register() functions from each script that has one as unique names and fires  them in the correct sequence. If you are trying to develop Sorcerer from the text editor and you are getting “not registered” errors, ensure that you are running each script in the exact order specified by the __init__.py. 


**panels.py:**  Sorcerer is a heavyweight addon. Its UI encompasses 6 different space_types across Blender at the time of writing this. It has about 15 different UI panels and hundreds of operators. Here, you will see that every UI draw uses custom helper draw functions. This allows us to reuse common UI elements in many different panels and popups without repeating code. Many of these custom helper draw functions have optional Boolean arguments for selectively making minor changes to how the element should be drawn in each context. These are very similar to the UI draw functions built into bpy, which also have these optional arguments (row.prop() for example). The ones Sorcerer has are just one layer of abstraction above that.

At the end of this script, you will find a register section that appends draw functions to various non-panel UI elements. To avoid appending the same custom element many times in a coding session, we use background checker properties to keep track of whether the element has already been added.

**event_manager.py:** This script is heavily documented within the script. Basically, its job is to manage events within Blender, as the name suggests. When the user changes the frame on the timeline, event_manager has to do stuff. When the user moves a cube across the viewport, event_manager has to do stuff. When the user presses play, presses stop, jumps the progress bar during playback, the event_manager has to do stuff. The stuff event_manager has to do can be divided into 3 neat categories:

1. Keep the console’s timecode clock in sync with Blender’s timeline but without actually streaming a constant timecode signal. We do it this way since all events are stored onto the console’s hard drive anyway. We also do this because it’s 100x easier for the end user to not have to set up a complicated timecode system just to make lights dance. This function is mostly associated with functionality on the Sequencer part of Sorcerer.

2. Find parameters on controllers that are changing either because of playback, frame change (animation), or because of transforms, modifier changes, or constraint changes to relevant objects in Blender’s 3D view. event_manager needs to avoid finding changes that don’t actually need to be sent to the console. This step is necessary partly because Blender’s internal dependency graph system does not update animated custom add-on properties during playback.

3. Create, harmonize, and publish CPVIA requests. Because Sorcerer is essentially its own lighting console that remote controls other consoles with OSC, it needs to reinvent DMX using OSC. CPVIA is a sort of internal DMX protocol invented by Alva Theaters. CPVIA says that any time any controller (controller being an influencer, brush, node, mixer, animation strip, etc.) wants to make a specific parameter on a specific fixture do stuff, it needs to create a formal request in the format (Channel, Parameter, Value, Influence, Argument), which is a tuple. 

If we are NOT in frame change, we send the CPVIA to the console immediately after converting it to (address, argument) for OSC protocol. 

If we ARE in frame change (or playback) however, we can’t send it just yet because there might be other CPVIA requests being formed from different controllers that also want to change that same parameter. So we don’t want to potentially spam the console with conflicting messages. In this case, we wait until everyone has had a chance to say their piece before we actually send the OSC. This happens on Blender’s frame_change_pre event handler. So all this happens while the frame is changing. 

Once the frame is done changing, once everyone—all the controllers—has spoken, we then take all the CPVIA requests to harmonize and simplify them. If we are in democratic mode, the Influence argument of each CPVIA determines how many votes the CPVIA gets in the democracy any time there is a conflict. If we are on non-democratic mode, we use Highest Takes Precedence (HTP) protocol, which means the CPVIA with highest value is the only one listened to. 

Once all the CPVIA’s have been harmonized and simplified, we send them all to the console. They will be bunched up into super long OSC strings for efficiency, depending on how the user has set their network settings. (50 is the maximum allowed grouping number.)


**orb.py:** The Orb is any button in the UI with Alva’s “orb” icon. The Orb is a tool that automates repetitive tasks on the lighting console. Because Sorcerer is (supposed to be) compatible with multiple console types, all Orb logic needs to be kept separate from main operator scripts for organization purposes. Most Orb operators should utilize “yield” and generators so that they can be called from modal operators and be terminated prematurely by the user with the scape key (without crashing Blender). From the operator scripts, Orb operator classes themselves should only call one helper function within orb.py. The logic for deciding between console types should all be kept in this script to keep Sorcerer DRY.


**spy.py:** spy, or SorcererPython, is a sort of API here to make it easier for casual users to interact with Sorcerer functions programmatically. Inspired by Blender's bpy. Look for the spy documentation below. Also, note that spy is supposed to be registered directly to bpy. Remember that this spy.py script is purely an abstraction layer and should not itself contain runtime logic like calculations.


**/utils/:** Contains common functions/methods that do stuff and return stuff. In here you will find a lot of the logic used for generating OSC syntax, for example the script that converts Blender’s RGB color profile to the color profile the fixture uses. You will also find the logic that makes the mixer nodes tick. 

**/assets/:** This contains things like common dictionaries, UI Lists, “get_items” functions, property groups, and the like. It stores most everything that is just stuff that doesn’t do stuff on its own.

**/nodes/:** Something that separates Sorcerer’s custom nodes from other addon nodes is that Sorcerer’s nodes don’t live in a custom node tree, they live in the primary shader node tree in World. This is because we want node groups! If we polled them to only appear in a custom node tree, the way Blender wants us to do it, then node groups wouldn’t work anymore. Blender can become unstable when reloading Sorcerer scripts while working on nodes. Blender crashes a lot. However, the crashing is strictly limited to development, when scripts are constantly being reloaded and reloaded and reloaded. If we learn that the crashing does persist into normal use for the end user, we will switch it over to a custom node tree. But until then, node groups, node groups, node groups!

**/audio/:** Doesn't exist yet. This houses most of Sorcerer’s 3D audio system and experimental Midas M32/Behringer X32 node-based sound design system. Sorcerer’s 3D sound system is quickly becoming the holy grail of 3D sound design for live performances. That means a system that fades completely into the background, whereby you forget you’re even using a 3D sound renderer. You just link sound strips to  objects in 3D view and you animate the objects however you want, and it just works.

The experimental Midas M32/Behringer X32 node-based sound design system is intended to allow Sorcerer to remote-control common live sound mixers the same way it already commandeers lighting consoles. 

TBC

API Reference (from bpy import spy)
=============================================================

Sorcerer now features an API targeted at the end user. It's called spy, short for SorcererPython. With absolutely zero setup, nontechnical users can commandeer the lighting console from Blender's text editor. 

**Accessing spy:**
--------------------------------------------------------------------
Users shall access spy through the following 2 lines of code:

*import bpy*

*from bpy import spy*

After those two lines, the user has full access to the spy functions below:

**OSC Functions**
------------------------------------------------------------------------
The *send_osc_lighting(address, argument)* function sends an OSC message to control the lighting console. You pass it an address and an argument, and it doesn’t return anything. The *lighting_command(command_as_string)* function sends a command string to the lighting console. You pass it a command line string, and it doesn’t return anything.

The *press_lighting_key(key_as_string)* function simulates pressing a key on the lighting console. You pass it the key name as a string, and it doesn’t return anything. The *lighting_key_down(key_as_string)* function presses a key down on the lighting console without releasing it. You pass it the key name as a string, and it doesn’t return anything. The *lighting_key_up(key_as_string)* function releases a key on the lighting console. You pass it the key name as a string, and it doesn’t return anything.

**Example Implementations:**

import bpy

from bpy import spy

import time


Just for fun:

spy.osc.lighting_command("3")

time.sleep(1)

spy.osc.lighting_command("2")

time.sleep(1)

spy.osc.lighting_command("1")

time.sleep(1)

spy.osc.lighting_command("Boom!") # Just a fun little demo



**Edit a macro**

spy.osc.lighting_key_down("Macro")

spy.osc.lighting_key_down("Macro")

spy.osc.lighting_key_up("Macro")

time.sleep(.3)

spy.osc.press_lighting_key("softkey_6") # Start editing the top macro


The *send_osc_video(address, argument)* function sends an OSC message to control the video switcher. You pass it an address and an argument, and it doesn’t return anything. The *send_osc_audio(address, argument)* function sends an OSC message to control the audio mixer. You pass it an address and an argument, and it doesn’t return anything. The *send_osc_string(osc_address, destination_ip_address, destination_udp_port, string_to_send)* function sends a OSC message to a custom destination, or to a place not defined within Sorcerer's settings. You pass it an OSC address, an address, a port, and a string, and it doesn’t return anything.

**Utility Functions**
----------------------------------------------------------------------
The *get_frame_rate(scene)* function gets the true frame rate of the scene by calculating considering the scene's fps and the scene's fps_base. It also rounds the result to 2 decimal places. If you instead use *bpy.context.render.fps*, you will just get the integer fps, which is not necessarily the complete picture that you need if the fps_base is something other than 1. For most Sorcerer operations, we use this function to get the true frame rate. This spy function returns a float rounded to 2 decimal points.

The *parse_channels(input_string)* function parses an input string and returns a list of channel numbers based on what it sees in the string. For ecample, if you pass the function "1 - 5, 6 - 10", it will return [1, 2, 3, 4, 5, 6, 7, 8, 9, 10].

The *parse_mixer_channels(input_string)* function converts a string of mixer channel numbers into a list of tuples. You pass it the input string, and it returns a list of tuples. This is typically used when you want concurrent groups when user uses () (). So for example, if you were to pass this function "(1 - 5) (6 - 10)", the function would return [(1, 2, 3, 4, 5), (6, 7, 8, 9, 10)]. Whereas the normal *parse_channels(input_string)* function would just return a list if integers regardless of () in the input string.

The get_light_rotation_degrees function gets the true rotation degrees of a light object after applying modifiers and constraints. You need this, not the built-in x_rotation/y_rotation accessible in Blender's UI because that number is not impacted by modifiers and/or constraints. You pass this spy function the light object’s name as a string, and it returns the rotation as x_rotation_degrees, y_rotation_degrees.

The try_parse_int function safely converts a value to an integer, avoiding runtime errors. You pass it the value, and it returns the integer or None. The swap_preview_and_program function swaps the preview and program for the ALVA M/E Switcher. You pass it a list of cues, and it doesn’t return anything.

The frame_to_timecode function converts the current frame number to a timecode string format (00:00:00:00). You pass it the frame number and optionally the frames per second (fps), and it returns the timecode string. The time_to_frame function converts a given time of a song to a frame number. You pass it the time, frame rate, and the start frame of the song strip, and it returns the frame number.

The add_color_strip function adds a color strip to the timeline. You pass it the name, length, channel, color, strip type, and start frame of the strip, and it doesn’t return anything. The analyze_song function uses AI to analyze a song for beats and sections. You pass it the context and the file path of the song, and it returns the analysis result.

The find_available_channel function finds an available channel to avoid overlapping strips in the sequence editor. You pass it the sequence editor, start frame, end frame, and optionally the starting channel (default is 1), and it returns the available channel. The duplicate_active_strip_to_selected function duplicates the active strip to selected strips. You pass it the context, and it doesn’t return anything.

The find_relevant_clock_strip function finds the most relevant sound strip with a timecode clock assignment. You pass it the scene object, and it returns the relevant strip object. The calculate_bias_offseter function calculates bias for flash strip background timing. You pass it the bias, frame rate, and the length of the strip in frames, and it returns the calculated bias as a float.

The render_volume function calculates the volume for a 3D audio object and a speaker pair. You pass it the speaker, empty object, sensitivity, object size, and the integer mixer channel, and it returns the calculated volume. The color_object_to_tuple_and_scale_up function formats Blender color objects for lighting console use. You pass it the Blender color object, and it returns a tuple of integers scaled to 0-100.

The update_alva_controller function updates the ALVA controller. You pass it the controller object, and it doesn’t return anything. The home_alva_controller function resets the ALVA controller to its home position. You pass it the controller object, and it doesn’t return anything.

Find Functions
For more advanced usage and detailed information on spy.find functions, please refer to the source code and developer documentation.

The is_inside_mesh function checks if an object is inside a mesh object. You pass it the object and the mesh object, and it returns true if the object is inside the mesh. The invert_color function inverts a color value, used for influencer calculations. You pass it the color value, and it returns the inverted color.

The find_int function finds and returns an integer within a string. You pass it the string, and it returns the integer or 1 if no integer is found. The mix_my_values function mixes values for the cpvia_generator in mixer nodes. You pass it the parent object and the parameter to mix, and it returns the mixed values.

The split_color function converts Blender's RGB space to the correct color space for fixtures. You pass it the parent object, red, green, and blue components, and the type of conversion, and it returns the converted color. The find_my_patch function finds the best patch for a given channel. You pass it the parent object, channel number, type of patch, and the desired property, and it returns the best patch.

The find_parent function corrects cases where self is a collection property instead of a node or object. You pass it the object, and it returns the parent object. The find_controllers function finds relevant strips, objects, and nodes in the scene for Sorcerer. You pass it the scene object, and it returns the relevant controllers.

The find_strips function finds relevant strips in the scene for Sorcerer. You pass it the scene object, and it returns the relevant strips. The find_objects function finds relevant objects in the scene for Sorcerer. You pass it the scene object, and it returns the relevant objects. The find_nodes function finds relevant nodes in the scene for Sorcerer. You pass it the scene object, and it returns the relevant nodes.
