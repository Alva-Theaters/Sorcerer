Development
=============

Logging/Service Mode:
---------------------
Logging in Sorcerer is controlled through the UI. You type “service mode” into the command line in 3D view, it adds a Service Mode panel, and you can toggle the built-in logging print statements for specific debugging needs there. Repeat the activation procedure to disable Service Mode.


Testing/Limp Mode:
------------------
Sorcerer has a testing algorithm built in that runs when the add-on is registered. It's designed like a car, hence "Limp Mode". If enough tests with enough weight fail, Sorcerer will boot into “Limp Mode”. That is indicated by a bright red label that says “Limp Mode” printed to the left of the Blender icon on the upper left, on TOPBAR_MT_editor_menus. If a script has failed a test and that script is responsible for something related to keeping fixtures from going berserk, like harmonizer.py, OSC output during frame change may be disabled to protect lighting fixtures. Look through multiple errors in the Service Mode panel, described above. The only way to clear Limp Mode and failed tests is to fix the problem in the code and re-register the add-on. 

Limp Mode is primarily intended to catch general coding mistakes rapidly and is secondarily intended to prevent malformed code from blowing lamps or over-stressing motors with contradictory commands, in rare instances.


Script and Folder Specific Explanations:
----------------------------------------
Detailed developer documentation for each folder will be added either to the script itself at the top, or to the __init__.py of the folder, whichever applies. A great place to start is the event_manager.py


Delete Parts:
-------------
Sorcerer is specifically designed to have as few UI elements as possible while also offering the most powerful and precise lighting control system. The UI is kept lean by constantly questioning the validity of every part, by deleting so many parts that some occasionally have to be added back in, and by never fixing a broken part without first trying to delete it. All the parts are purely fictional constructs that are only there to make up for some technical or conceptual constraint. Always challenge the constraint that prompts the part.

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