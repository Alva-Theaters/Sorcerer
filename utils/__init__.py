'''
PACKAGE-LEVEL OVERVIEW:
    audio_utils.py --------- Render logic for Sorcerer's 3D audio panner/renderer. 

    cpv_utils.py --------- Functions directly related to CPV often used outside the CPV folder. 
                             CPV stands for (channel, parameter, value, influence, argument).

    event_utils.py --------- Functions used by the event manager, which handles events like start,
                             stop, jump, depsgraph update, etc for lighting and audio needs.

    orb_utils.py ----------- Functions used by the Orb assistant, which automates repetitive tasks
                             on Eos remotely.

    osc.py ----------------- Functions for sending OSC messages onto the network. Uses socket module.

    rna_utils.py ---- Not to be confused with poperties like IntProperty. This is for
                             tools that live in the Properties space_type, like Cue Switcher and
                             Stage Manager. This confusion is why the folder that registers things
                             onto Scene and Object and the like is called makesrna, not properties.

    sequencer_mapping.py --- Functions that create maps of the sequencer strips for the purpose of
                             firing them at the right times during playback.

    sequencer_utils.py ----- Functions used for various common sequencer operations


AUDIO_UTILS.PY:

    This code's job is to figure out how much you should hear of a 3D audio object in
    a specific speaker. Unlike any other known spatial audio renderer, this one handles
    asymnetrically-scaled audio objects. 

    Benefits:
    - The best possible artist's experience for spatial audio
    - The UI/UX could not possibly be any more simple; every Idiot Part was deleted

    Features:
    - Animate motion with keyframes, graph editor, dope sheet, curves, constraints
    - 3D audio objects represented by custom 3D meshes, not just dots
    - Built-in stage lighting control, allowing moving lights to track 3D audio objects
    - 3D audio objects support asymnetric scaling
    - Total freedom of movement between all 3 axes

    Use Cases:
    - Technical theatre with Qlab and (ETC Eos or grandMA3)
    - Design-rated only, tranfer data to FOH hardware after designing sequences
    - Compatible with anything from basic stereo 

    Problems to Solve: 
    1. How to calculate distance to speaker when an audio object is asymnetrically scaled.
        (We care about this because this allows the user to spatially define "beds". We want
        to  define beds spatially, not with magical numbers because all the user wants to do
        is control *where* sound comes from. *Where* is a spatial direction, so we want to 
        define it spatially since we are reasoning from first-principles.)

    2. How to prevent the rendered value from getting stuck at full as audio object passes over.
        (We want it to only be at full if it's perfectly on top of the speaker. That way, you
        always have panning ability. If it's too sensitive, the sound motion just stops and 
        starts.)

    Solutions:
    1. Currently, when an audio object is asymnetrically scaled, we pretend like the mesh is 
        actually a lot of meshes. Normally, we use the mesh's bounding box center, but here,
        we use the vertices. We find out which vertice is closest to the speaker and pretend
        that is the bounding box center. When we move to the next speaker in the next iteration
        we find the vertex closest to that one.

        While doing this, we have to keep in mind that the normal algorithm multiplies the true 
        speaker scale by 5 to make it work more naturally out of the box. In the asymnetric 
        mode, we need to stop doing that.

    2. I'm pretty sure this was fixed with the apply_logarithmic_falloff method?
    
   
   '''