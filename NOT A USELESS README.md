
**Technical Overview for Developers:**
============================================================================

We’ll start by going over just the .py files and the folders. The following will assume you have at least a basic understanding of Python within the context of Blender and bpy. Some of this wil be geared to beginner developers, as well as those completely new to Sorcerer.


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
