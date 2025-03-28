Development
=============

Intro:
-----------
Within the context of Blender add-ons, this codebase is comparable in size to Hard-ops, Animation Nodes, and MTree. However, this add-on does not serve existing Blender workflows. Alva Sorcerer has nothing to do with computer graphics; we're using Blender because it's a free and open-source node engine, video editor, 3D view, graph editor, Python API, and more all rolled into one mature platform.

Basically, what we're trying to do is animate the controls of a performance venue (like a concert hall) using Blender. 

**Lighting:** Sorcerer remote-controls existing lighting consoles like ETC Eos family theatrical lighting consoles and touring consoles like grandMA3. We want Blender to remote-control them because Blender is way better at creating pre-made sequences than they are. 

Existing consoles are all built on the foundation of one of those old DMX-512 fader boards that are the size of a loaf of bread. A grandMA3 console is that, just a few thousand times more advanced, powerful, useful, fancy, and sophisticated. But all those high-end consoles start with that same foundation.

Alva Sorcerer says instead of starting with one of those crappy old DMX-512 fader boards, start with Blender. Blender is your foundation. Only focus on pre-made sequences. Busking is no longer an engineering constraint. Now, you're suddenly free to control lights in some exotic, bizarre, outside the box ways. When you see what you can do here and then look back at the lighting console by itself, you ask, "How on earth does nobody else have this stuff?" It's because they're starting with a fader board. We're starting with friggin Blender.

**Audio:** Sorcerer creates 3D audio content for Qlab. It also remote-controls Qlab for real-time monitoring. It's kind of like Dolby Atmos, but for live sound systems. We want Blender doing this because it lets you put all your creative control under one roof in a visually inspiring way.

In the case of Dolby Atmos, you have to have half a dozen softwares open at once to get anything done. Each sound object is just a sphere on the screen with a text label. The rest of the screen is blank. To make audio objects move, you need to make fade cues, so it's not easy to get precise moves. Often, the thing controlling this is in one software and the thing controlling that is in an entirely different software. 

In the case of Sorcerer, creative control of lighting, video, and audio is all in the same software. If a sound object represents a horse, it can be a horse. If a helicopter is flying over the white house, you can add a model of the white house and of a helicopter, make the helicopter fly over the white house, and set the helicopter as the audio object. If you want to move an observer through a rainforest, set up all the rainforest and animate the speaker rig through the rainforest. If you want this audio object to be bigger, just scale it up. If you want an audio object that isn't a sphere, you can make it whatever shape you want. The 3D sound panner will factor in its irregular shape. If you want a moving light to track a 3D audio object, it's so easy you may do it by accident. 

That's the only rational way to design 3D audio. Not these blank dots in a blank cube.


Logging/Service Mode:
---------------------
Logging in Sorcerer is controlled through the UI. You type “service mode” into the command line in 3D view, it adds a Service Mode panel, and you can toggle the built-in logging print statements for specific debugging needs there. Repeat the activation procedure to disable Service Mode. NOTE: Currently, if you're in grandMA3 console mode, you have to go into ETC Eos console mode to get to that command line (it's hidden because the primary feature isn't compatible with MA yet). Console-specific hiding will become far less dumb in the near future. 


Testing/Limp Mode:
------------------
Sorcerer has a testing algorithm built in that runs when the add-on is registered. It's designed like a car, hence "Limp Mode". If enough tests with enough weight fail, Sorcerer will boot into “Limp Mode”. That is indicated by a bright red label that says “Limp Mode” printed to the left of the Blender icon on the upper left, on TOPBAR_MT_editor_menus. If a script has failed a test and that script is responsible for something related to keeping fixtures from going berserk, like harmonizer.py, OSC output during frame change may be disabled to protect lighting fixtures. Look through multiple errors in the Service Mode panel, described above. The only way to clear Limp Mode and failed tests is to fix the problem in the code and re-register the add-on. 

Limp Mode is primarily intended to catch general coding mistakes rapidly and is secondarily intended to prevent malformed code from blowing lamps or over-stressing motors with contradictory commands, in rare instances.


Script and Folder Specific Explanations:
----------------------------------------
Detailed developer documentation for each folder will be added either to the script itself at the top, or to the __init__.py of the folder, whichever applies. A great place to start is the event_manager.py


<br>

Design Philosophy
=================

Delete Parts As Often As Possible!!!:
------------------------------------
Sorcerer is specifically designed to have as few UI elements as possible while also offering the most powerful and precise control system. The UI is kept lean by constantly questioning the validity of every part, by deleting so many parts that some occasionally have to be added back in, and by never fixing a broken part without first trying to delete it. All the parts are purely fictional constructs that are only there to make up for some technical or conceptual constraint. Always challenge the constraint that prompts the part.


What Stuff is Trying to Do What Stuff?
---------------------------------------
First-principles thinking is about breaking a problem down to irreducible simplicity. We want
to forget everything we think we know and only add back in what we absolutely know for sure. 

For example, for 3D audio, the only things we can be absolutely sure of are:
   1. Speakers, the boxy things that make noise in real life
   2. Audio objects, the things that spatially represent the things that made the noises
   3. Sound sources, the things that say what the noise sounds like
   4. Animation, the thing that makes the noise move through space through time

In the UI, the only things that can be created in relation to 3D audio are speakers, audio objects (regular meshes), sound sources (sound strips in the video editor), and keyframes. There are no beds, zones, layers, formats, metadata, cues, fades, or anything like that.

Sound strips are trying to reconnect to physical objects. That's the stuff trying to do stuff.


Idiot Parts:
------------
It's super easy to add imaginary compexity to a software when you solve problems by adding more parts. When you have a problem, you should try to delete the part that has the problem before you try to fix the part that has the problem. Most of the time you spend thinking about software should be spent trying to come up with ways to delete big parts. You should throw a party every time you figure out how to delete a massive chunk of UI. Instead of adding minor, incremental parts and improvements to parts you already have, you should measure success by how much stuff you figured out how to delete.

The best software is the software that looks like it's 1/8th baked. If you open a software and it looks extremely sophisticated because there are so many buttons and switches and levers, it was not designed using first principles. It probably has a ton of Idiot Parts. 

If you instead open up a software and it's like, "There's nothing here, where are all the parts?", it is either a very simple software that doesn't do much of anything, or it is a very sophisticated software that was designed from first-principles. Quality design tends towards outward simplicity, not towards outward complexity.

Idiot Parts are parts that are there because of some imaginary technical constraint. Almost all the parts are ultimately Idiot Parts. It's just a matter of how difficult they are to delete. If a part is there specifically because another part was designed poorly, it is clearly an Idiot Part. If a part is there because of a fundamentally flawed foundation of thinking, it is much harder to recognize it as an Idiot Part. 

Parts that are not Idiot Parts are parts that are directly and inseparably related to the stuff that is trying to do the stuff. In the context of Sorcerer, parts that are not Idiot Parts are parameters like intensity and color. A part in Sorcerer that **is** an Idiot Part is Orb. Orb is an Idiot Part because it is only there because Sorcerer isn't smart enough to do all the tasks that Orb does entirely automatically in the background without ever bothering the user. It could be that smart, but it's not yet. So all of Orb is an Idiot Part. It's dumb because only an Idiot would say we shouldn't try to delete it. That's because it does not directly serve the true purpose of the software; rather, it only serves a fictional, manufactured, technical constraint that doesn't need to exist.

The easiest way to tell if a part is ultimately an Idiot Part or not is to imagine a alien civilization 100,000 years ahead of us technologically. Imagine they have an absurdly sophisticated solution to your problem that is 100,000 years ahead of us in every way we can't even imagine. Is it likely that their design includes your part? Probably not. Ultimately, the part you're challenging is probably an Idiot Part. It's just a matter of how soon it can be deleted.


80/20:
------
A lot of softwares try to design for 100% of use cases. They end up creating a product that is good for everyone but is not great for anyone. Sorcerer is instead designed only for the 80% of use cases. For example, it is limited in the parameter types supported. It doesn't do any of the advanced, newer effects that all the super fancy lights can do nowadays. That's because adding those controls would make the interface too complicated for 80% of users.

Sorcerer is designed to be extremely amazing for the 80%. It's okay if it's nightmare fuel for the 20%.
I would rather make an extraordinary product for 20 people than make a mediocre product for everyone.

This, however, is NOT an excuse to ignore users. If a user wants a feature that doesn't align with Alva's goals, there should be a realistic pathway to solving their problem anyway. That's why Alva Theaters may in the future offer development services whereby people can pay for custom feature additions.

Ultimately, the best version of Sorcerer is one that is perfect for everyone. But in the meantime, we're focusing on the 80 percent.

<br>

Conceptual
==========
Here are some wider-scope concepts that may help better understand what Sorcerer's codebase is trying to do within the grand scheme of things.


Procedural vs. Non-Procedural Control:
--------------------------------------
If you’re already familiar with Blender, you likely associate the term “procedural” with geometry nodes. If you don’t, what is meant here by “procedural” is a type of software that does a thing with a list of instructions in more or less plain English. Procedural is great for doing a ton of things super fast, but you sacrifice a lot of precision and creative control. Non-procedural control works more like a sculpture that you carve slowly by hand. 3D animation and graph editors, for example. We’re talking about procedural vs. nonprocedural because traditional lighting consoles, like ETC Eos, are almost purely procedural in how they control stage lights. What we’re doing with Sorcerer is we’re giving lighting designers the joy of nonprocedural control. We’re letting them control lighting rigs through time by hand for the first time.


Non-Oscillating Effects:
------------------------
Effects on lighting consoles sort of have an internal motor that makes them continuously do stuff for forever until you tell them to stop. Effects in Sorcerer/Blender don’t work like that. Almost all the effects you can make here need to be manually “spun” to get them to move. (That analogy is why we have “Motor Nodes”.) You do that with keyframes. This is sort of like the difference between designing something on a potter’s wheel or on a lathe, and carving something that isn’t spinning. Effects on lighting consoles are pretty much always spinning, so you’re limited in how specific changes can be through time. But with animation effects, there are no limitations to where changes can be made. It’s not spinning, so super localized changes are super easy. This however comes at the cost of some of the speed and efficiency that you get with lighting consoles. 


<br>

Areas to Dive Into:
===================
Below are the general areas contributions can focus on. 


Core:
----------------------
Examples:
   - makesrna System
   - Event Manager
   - CPV System (Fade Engine)

Needs:

   - Delete all items registered directly to scene, use scene_props for everything.
   - Delete "my_motifs" CollectionProperty from Sequencer.
   - There are still some incorrectly named bpy.types Classes.
   - Rewrite event_manager script to be more clear and readable.
   - Eliminate bpy dependencies as far upstream as possible so we can migrate logic to Cython or C++.
   - Implement CPV testing since we have none at all at the moment.


UI:
----
**Lazy Pixel Count Index (LPCI):** Occasionally take a screenshot of the main UI and take it into a paint program where you can draw on it with a marker. Find all areas on the Sorcerer UI that are not white space and cannot be made useful to the user. Mark those all up with red marker. That's your LPCI. Make that area be as small as possible.

Rules:

   - Never try to fix a broken part without first trying to delete the part.
   - Always question the requirement or constraint that prompts the part's existence.
   - Try to avoid UI parts that only serve a technical purpose, not an artistic purpose.
   - Never force the user to click more than 3 times to control something.
   - Minimize LPCI by creating the simplest possible form of the UI.
   - The longer a central design remains unchanged, the more apparent its flaws become to users.
   - No UI part shall take up more space than it truly needs.

Needs:

   - Improve tooltip consistency and translations.
   - Some areas need to be refactored.
   - Rewrite all parameter-drawing code in prep for extendables adoption.


Orb:
-----
Needs:

   - Improve usability of the automatic macro finder. Honestly this should be exposed somewhere.
   - Clarify how the user is supposed to use the timecode control stuff.


API:
-----
Needs:

   - Dramatically improve the docs.
   - Expand the "extendables" scripting system to fixture parameters too.


Sequencer:
-----------
Needs:

   - Strip formatter tool should be more consistent, it hides a lot when you need it.
   - Improve channel-finding code.


Nodes:
-------
Needs:

   - Conceptualize the first node-based effect engine in Sorcerer.
   - Get the dang pan/tilt node working properly since it's still a dumpster fire.


Cue Switcher:
---------------
Needs:

   - Integrate with node editor for enhanced versatility.
   - Incorporate control of effects for true "Mix Effect" system.


Stage Manager:
----------------
Needs:

   - Integrate with OSC better to allow custom messages to be sent to 3rd party display/monitor systems.
   - Increase overall customization.


Current Dumpster Fires:
=========================

   - spy API docs (what docs?)
   - Sorcerer Manual (very outdated)
   - Testing (what testing?)
   - 3D Gradients (technically still experimental)
   - grandMA3 Support (still only does core animation)


General Gripes and Complaints:
=================================
 
   - Color, you need to stop being a special snowflake. Just because you're a tuple doesn't mean you need 
     your own special code in every single function. Everyone else is just float/int. Everyone else is better
     than you. Get it together.