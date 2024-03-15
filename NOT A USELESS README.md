Hello there, human! 

This is a Blender 4 add-on called Alva Sorcerer. Sorcerer is primarily intended for theatrical lighting artists who wish to separate the art from the technicals. Sorcerer provides node-based light design, sequence-based light design, 3D-object-based lighting effects, and an animation renderer to existing lighting consoles without replacing the existing console. In addition to real-time output, it produces deliverables the console can play back by itself during the final show. Sorcerer is not DMX software. It is instead an OSC remote-control software. While most Sorcerer features are universal, some features are currently only for ETC Eos family consoles. Explicit, comprehensive support for grandMA 3, Hog, and MagicQ is coming. 

Alva Sorcerer is considered an External Multimedia Animation Renderer. "External" because it does not directly control anything, but only remote-controls existing hardware control systems. "Multimedia" because it also produces 3D audio object deliverables and will soon also produce deliverables for PTZ camera systems. "Animation" because it creates a direct link between technical theatre and the animation suite behemoth that is Blender. "Renderer" because its primary purpose is to produce deliverables to be executed on show day by dedicated, performance-rated show control hardware (in much the same way that video editing software produces deliverables to be executed by movie theaters without the movie theater needing the video editing software). Sorcerer is the only known tool of its kind.

Alva Sorcerer is 3D animation but in real life, for technical theatre.

To use this software, you must download and install a recent version of Blender from blender.org. Currently, the exact URL to go to is:

https://www.blender.org/download/

If you found the correct download file, you should be able to double-click it and your operating system should walk you through the install process smoothly.

Once you have Blender downloaded and installed, you will need to go to User Preferences to tell Blender to run Sorcerer. On the top left, Edit > Preferences. Then, on the left side, press the “Add-ons” tab button. Then, go to the top right corner and press “Install”. Then, find the compressed “Sorcerer” folder. Ensure the compressed/zipped folder is still named Sorcerer with no spaces, capital letters, or special characters. Click that in the Blender add-on window and it should pop up as an add-on. Go ahead and check the checkbox to enable the add-on and read the warnings. Essentially, it just lets you know that it isn’t necessarily safe to have this software actually running during a real show with an audience, that it’s far better to store the data created by this software locally on the console. There are many automation tools in Sorcerer to help you with that. Here is that formal warning:

Warning: For optimal performance and reliability during live shows, it's advised to transfer all timings created with this software directly to the console's internal memory prior to the event. While this add-on is a valuable tool for setting up and integrating into an FOH setup, it's not recommended to have Blender/Sorcerer actively running and sending OSC commands during the live show itself. Follow best practices for a seamless experience.

If installing Sorcerer did not work as expected and you can’t figure out what’s going on, Googling it may help (type in keywords for general Blender add-on installation problems). If that doesn’t work, contact Alva Theaters at help@alvatheaters.com.

Once you have Sorcerer installed, navigate either to 3D view, Video Editing, the Shader Editor, or the Sorcerer Nodes view. Warning: the dedicated Sorcerer Nodes view is not compatible with node groups, so use the Shader Editor is you wish to utilize node groups.

Now, follow intuition, tooltips, and the demo videos/streams on Alva Theaters’ YouTube channel to figure out what to do with the software. If none of that helps, either contact Alva by email at help@alvatheaters.com, by phone at (855) 512-2700, or, maybe you’ll be forced to read the documentation. It is our goal however to create software that is so intuitive that it doesn’t need documentation/instructions. If you feel the need to vent about something you think is needlessly confusing and/or dumb, send us an email at thisisdumb@alvatheaters.com. You can also ask our Not a Dumb Chatbot.

Core Feature Sets of Sorcerer:

•	“Orb” assistant that rapidly automates many repetitive tasks on Eos
•	Most static menu panels can be hidden and accessed instead as popups
•	Rapidly create flash effects with the sequencer and link to nodes
•	Unlimited number of group controllers in node editor
•	Animate 3D objects over the lighting plot in 3D view for 3D-object-based effects
•	Directly link pan/tilt of movers to 3D audio objects and create deliverables
•	Create “qmeo” deliverables after animating complex effects
•	Fully patch Eos consoles using Sorcerer’s UI style
•	Mix multiple parameter choices across groups with mixer nodes
•	Sequencer automatically creates events in the Eos event list based on strips
•	Use your own Python code to control lights or 3D audio objects
•	“School mode” password-protects key settings that students/volunteers shouldn’t touch


Core Relevant Blender Feature Sets:

•	Rapidly create 3D lighting plot with Blender’s UI before patching
•	Create exorbitantly complex show files with node layering/grouping
•	Asset manager can connect nodes directly to marketplaces and internet
•	Advanced animation tools like Graph Editor, NLA Editor, and Dope Sheet
•	Blender’s .blend file management
•	Blender’s highly customizable UI themes and keymap
•	Performance capture for moving lights using motion tracking
•	Blender’s sophisticated curve, modifier, constraint, and physics tools
•	Many other tools within Blender that have been under continuous, iterative evolution for 3 decades
