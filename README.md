<!--
Following Blender's lead on this, keeping this short and concise. Seems like a good idea
since this way, we can put all the efforts towards one place, the main website. Previously,
there were issues where the website would be up to date, but this readme was very
different and old, or the other way around. This way there is only one primary communicator 
to maintain.

EDIT; Eh, can probably add a more complete feature list. Not well-known enough to forgo.
-->

Alva Sorcerer
==============
Sorcerer is a Blender add-on that lets Blender animate a performance venue's control booth. Blender is ["the free and open source 3D creation suite."](https://projects.blender.org/blender/blender/) Sorcerer connects Blender's animation tools directly to QLab for 3D audio and to ETC Eos or grandMA3 for lighting control.

With Sorcerer, your lighting rig transforms from a computerized army of robots into an expressive troupe of dancers, each with an audible voice.

![Alva Sorcerer/Blender](images/alva_sorcerer_fcurves.png)

Feature Categories
-------------------
- **3D Viewport:** Control lights with 3D meshes
    - 3D Bitmapping
    - 3D Gradients (Experimental)
    - 3D Magic Sheets
    - Driver Support
    - Follow Paths/Curves
 
- **Live Spatial Audio (LSA):** Control sounds with 3D meshes
    - Move listener through stationary soundscape
    - Represent audio objects/scenes with detailed meshes
    - LSA animation (graph editor, NLA editor, dope sheet, etc.)
    - Full, 3-dimensional range of freedom for objects
    - Considers Blender's constraints system (follow curves)
    - Supports asymnetrically scaled audio objects
    - Synchronize LSA with lighting control in-software
    - Connects with Qlab for realtime playback
    - Mixdown speaker-specific audio files for final show
    - Connects directly with sequencer
      
- **Video Sequence Editor:** Sequence FOH events intuitively
    - Cue Strips
    - Macro Strips
    - Flash Strips
    - Trigger Strips
    - Offset Strips (Experimental)
    - AI Song Analyzer (External Dependency Required)
      
- **Node Editor:** Use node layouts for controllers
    - Mixer Nodes (Gradients)
    - Group Controller Nodes
    - Node Groups
    - Node Links
    - Direct Select Nodes
    - Presets Grid Nodes
    - Pan/Tilt Nodes
      
- **Graph Editor:** Animate parameters with emotive precision
    - Animate ~50% of Sorcerer properties
    - Graph Controllers (2025)
      
- **Text Editor:** Script or extend Sorcerer with its API
    - Iterative macro generation
    - Access many Sorcerer functions
    - Add custom lighting consoles
    - Add custom strip types (Experimental)
    - Instant Docs with .explain()
    - Access via "from bpy import spy"
      
- **Remote Patch:** Add lights to Augment3D with Blender
    - Considers most constraints
    - Considers array modifiers
    - Considers orientation
    - Also patches DMX if provided
      
- **Cue Switcher:** Preview and "take" lighting cues
    - Multiple cue groups
    - Custom fade time button
    - Numpad Hotkeys
      
- **Stage Manager:** Stage-manage like a rocket launch director
    - Manages opening and closing of lobby, house, and show
    - Organizes multiple crew polls
    - Plans for forseeable anomalies
    - Sends custom OSC at target points (2025)
 
- **Orb:** Automation assistant that completes boring, repetitive tasks
    - Creates qmeos, which stores animation data onto Eos
    - Creates macros needed for sequenced events
    - Syncs sequencer events to event lists
    - Completes many other repetitive tasks throughout Sorcerer
    - Ensures all data can be stored directly on FOH hardware
    - Uses TCP network protocol for reliability (Experimenal)
      
- **Fade Engine:** Under the hood, it works much like a real console
    - Harmonizes conflicting controllers
    - Simplifies and batches OSC messages
    - Handles differing color profiles, min/maxes, and other special needs
    - Level of Detail (LOD) style system to decrease bandwidth
    - Democracy mode and HTP mode
    - Uses UDP network protocol for speed
       

Links
-----
- [Sorcerer Website](https://sorcerer.alvatheaters.com/)
- [Manual](https://alva-sorcerer.readthedocs.io/en/latest/index.html#)
- [Support](https://sorcerer.alvatheaters.com/support)

Development/Python API
-----------------------
- [Development README](https://github.com/Alva-Theaters/Sorcerer/blob/main/maintenance/DEVELOPERS.md)

License
-------
Sorcerer is licensed under the GNU General Public License, Version 3.