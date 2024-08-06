**3D Animation in Real Life, for Theatre, with Blender**
======================================================================
Imagine an absurdly sophisticated, effortlessly intuitive, exotically bizarre entertainment lighting software designed by aliens from a distant planet. Imagine this software is capable of doing things with lights that make our expensive lighting consoles shake in their boots. Imagine that using this software as an artist is so intuitive that it feels the same as painting with a paint brush, playing piano, or writing poetry. That’s what Alva Sorcerer is trying to be. It’s not trying to be just another DMX software. It’s not just trying to make a few steps forward. It’s trying to radically redefine extraordinary.

Alva Sorcerer is a heavyweight Blender addon that uses OSC to remote-control ETC Eos family theatrical lighting consoles, Qlab, live sound mixers, and other professional lighting consoles. Blender is the free and open source 3D animation suite supporting modeling, rigging, animation, simulation, rendering, compositing, motion tracking and video editing. Alva Sorcerer connects that power to FOH show control to create 3D animations in real life for theatre.


**What Does it Actually Do?**
---------------------------------------

Imagine the software they use to make 3D animated movies like Tangled, Kung Fu Panda, Frozen, movies like that. Sorcerer lets you use that kind of software to control the lighting, video, and audio at a theater. That's why it's called 3D animation in real life, for theatre, with Blender. Basically, in one software only, you have god-like control over everything in the theater at all times in the most intuitive way possible. There's no programming, there's no syntax, there's hardly any technicals, it's just organic artistic flow.


**Entry-level Features:**
---------------------------------------

- Automation tools for ETC Eos lighting consoles like copy/paste macro builder and timecode setup
- Sequence-based timecode editing for ETC Eos
- True 3D audio panner with animatable audio objects
- Mixers, which make gradients on ETC Eos extremely simple
- Node-based ML editors, which replaces many magic sheets
- Stage-manage a theater show like a bad*ss rocket launch director
- 3D magic sheets without need for words, sliders, buttons, or anything like that
- Use virtual 3D objects to influence lights for super intuitive effects
- Full-screen robust graph editor for precisely editing fades



**What Sorcerer IS:**
---------------------------------------

- Node-based light design for ETC Eos
- Sequence-based light design for ETC Eos
- Animation-based light design for ETC Eos
- 3D bitmapping for light design for ETC Eos
- Motion capture for light design for ETC Eos
- 3D audio panner for Qlab and M32
- Automation tools for ETC Eos
- ADHD friendly


**What Sorcerer Does NOT Do:**
---------------------------------------

- It is not DMX software, it instead remote-controls professional consoles and produces deliverables
- Sorcerer is not visualization software
- It does not output multichannel audio, it instead works with Qlab and/or an audio mixer
- It is not meant to send OSC during final shows, it instead creates deliverables stored on FOH hardware for the final show(s)


**Use Cases:**
------------------

- Use an absurdly simple node layout to provide students or volunteers the simplest conceivable way to control lights
- Output short, extremely sophisticated and precise lighting animations as deliverables to play as effects
- Animate moving lights to track 3D audio objects
- Use the video editor to make timecoding on Eos absurdly intuitive
- Use node layouts to build lighting cues the way a painter would, not how a computer programmer would
- Create exotic lighting effects by animating 3D objects that influence the lights they move over


**Relevant Blender Feature Sets:**
---------------------------------------

- Advanced animation tools like Graph Editor, NLA Editor, Dope Sheet, arrays, and constraints 
- Blender’s .blend file management 
- Blender’s highly customizable UI and keymap 
- Asset manager for organizing and sharing file components
- Many other tools within Blender that have been under continuous, iterative, open source evolution for 3 decades
- The Blender community


**Compatibility:**
---------------------------------------

- Alva Sequencer was initially developed in Blender 2.79, but has since been adapted to Blender 4.0
- Alva Sorcerer was developed on Blender 4.0
- Basic Sorcerer/Sequencer functionality has been tested on Blender 3.5 without any sign of problems, although 4.1 introduces a Cancel button on all popups, but this does not do anything yet for most Sorcerer/Sequencer popups, also it appears there may be an issue with the toolbar and add menu not showing in Node Editor for Blender 4.1, not confirmed yet though
- Alva Sequencer was designed primarily for ETC Eos, but some features like animation and trigger strips should work on other consoles
- Excluding the patch feature, Alva Sorcerer-only features were designed with universal lighting console compatibility in mind, but it has not been tested on consoles other than Eos
- 3D audio file playback is compatible with any software capable of playing numerous tracks at once to numerous sound card outputs (Qlab, for example)
- 3D audio realtime monitoring should be compatible with most sound mixers that support OSC input


**Installation and Setup:**
---------------------------------------

- Download and install the latest version of Blender from Blender.org
- Click "Preferences" under "Edit" at the top left, click the "Add-ons" button on the left, click the "Install" button on the top right, select Sorcerer/Sequencer, and then click the checkbox next to the new addon to enable Sorcerer/Sequencer. 
- Navigate to the Shader Editor/World, 3D view, or to the video editor  to find Sorcerer/Sequencer UI elements on side N panels, on the T toolbars on the right, by the orb icon in the headers, or on keyboard popup menus ("P" in 3D view for channel controller, "F" in node editor and video editor for Formatter, and "M" in the video editor for Strip Media)
- Note: Blender recently changed its Preferences UI. The latest version (4.2) has the Install Addon button on a drop down off a down arrow button in the upper right-hand corner inside Preferences.


**Examples and Tutorials:**
---------------------------------------

- Alva Theaters YouTube channel: https://www.youtube.com/channel/UCE6Td8fdLPvv3VLdfjIz5Dw
- Software Documentation: https://alva-sorcerer.readthedocs.io/en/latest/index.html#


**Contributions Guidelines:**
---------------------------------------

- Currently the biggest need is to complete Beta testing by testing features and fixing issues that come up there. Most of the features currently work, but only just.
- This is a massive codebase with a massive feature set that I cannot adequately maintain alone. Any help is much appreciated.
- The vast majority of the code is largely PEP8ified.
- Contact info is help@alvatheaters.com


**Support and Community:**
---------------------------------------

- If you are a customer of Alva Theaters, the software you purchased should be supported via WorkStraight, so create work order requests through the links provided to you on the marketplace if something is broken
- If you are not a customer, you can ask for help at help@alvatheaters.com
- If a decision made by the software seems really dumb, consider venting about it to thisisdumb@alvatheaters.com
- Alva Theaters has a subreddit for discussing its software: https://www.reddit.com/r/alvatheaterssoftware/


**Boring Dev Notes:**
------------------------
3/28/2024 — I'm experimenting with the new Blender 4.1 stable build. I'm finding that that the new "Cancel" UI element they added to popup menus does indeed affect ALL popup menus including addon ones (see release video if you haven't already). Will need to expedite adding cancel logic to all those modals now. The button does not appear to be causing runtime errors, fortunately.
