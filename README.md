**3D Animation in Real Life, for Theatre, with Blender**
======================================================================

.. figure:: ../sorcerer/images/alva_sorcerer.png
   :align: center
   :alt: 3D Audio
   :width: 700px
   
Imagine an absurdly sophisticated, effortlessly intuitive, exotically bizarre entertainment lighting software designed by aliens from a distant planet. Imagine this software is capable of doing things with lights that make our expensive lighting consoles shake in their boots. Imagine that using this software as an artist is so intuitive that it feels the same as painting with a paint brush, playing piano, or writing poetry. That’s what Alva Sorcerer is trying to be. It’s not trying to be just another DMX software. It’s not just trying to make a few steps forward. It’s trying to **radically redefine extraordinary**.

Alva Sorcerer is a heavyweight Blender addon that uses OSC to remote-control ETC Eos family theatrical lighting consoles, Qlab, live sound mixers, and other professional lighting consoles. Blender is the free and open source 3D animation suite supporting modeling, rigging, animation, simulation, rendering, compositing, motion tracking and video editing. Alva Sorcerer connects that power to FOH show control to create 3D animations in real life for theatre.


1.	Software Type:
- Blender addon. Blender is an open-source 3D animation suite
- OSC remote-control for ETC Eos lighting console, common in theaters
- Produces deliverables for existing FOH hardware to play back

2.	Software Objectives:
- Provide artist-friendly, nontechnical way to create a lighting show
- Allow user to create lifelike, emotional animations with stage lights
- Allow user to integrate lighting control with music seamlessly

3.	Software Constraints:
- Must increase flexibility and precision—cannot decrease it
- User must be able to bring their own ETC Eos lighting console
- Each feature family must be fully explainable in 60 seconds, respectively

4.	DELETED Software Constraints:
- Must be able to send DMX
- Must be able to complete all basic lighting console tasks
- Must be reliable and fast enough for real-time operation

5.	Primary Achievements of Version 2:
- Automatically stores complex Blender animations onto Eos with one click
- Creates precise, musical timecode sequences on Eos in seconds
- Most feature families can be fully demonstrated in 1 minute, respectively

6.	Approach:
- First-principles approach that simplifies problems to their purest form
- Anti-parts approach that deletes dumb parts instead of fixing dumb parts
- Anti-technical approach that says the artist experience is the only priority

7.	Points of Common Confusion
- It acts like a video editor that renders out a video for the console to play later
- It provides the option to use animation, but has many other controller types
- It’s built on top of Blender to get a piggyback ride on the shoulders of giants



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
