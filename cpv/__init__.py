ORDER_OF_OPERATIONS = """
1. The parameter-specific updaters found at the bottom of cpv_generator.py are assigned to the parameter properties 
   as updaters in the makesrna folder in rna_common.py. That parameter-specific updater passes its property 
   name to the main cpv generator, that way it knows what property was updated. It passes self as "controller".

2. The CPVGenerator then finds the controller's parent, which is sometimes difficult if the parent is a mixer node,
   which uses property group properties. Those properties change self to the property group, which disguises the 
   true controller, which is the node. The CPVGenerator takes care of that.

3. The CPVGenerator then finds the controller type, which is fairly straight forward. Other classes downstream will
   reach back to see this from time to time.

4. The CPVGenerator also uses stop.py to see if there is any setting that should require this iteration to stop 
   prematurely.

5. CPVGenerator also checks if the current context is 3D view so that we know whether to update other selections. 
   In other words, if we are in 3D view and the user has 5 different lights selected, and they change a parameter
   on the active_object, they probably want that to be done to the other ones they have selected too.

6. In its execute method, CPVGenerator then returns early if stop.py said to, updates other selections if we're in
   3D view, and then finds the right downstream function to use based on the controller type. It then sends itself 
   to that function it found. Those functions are then responsible for everything else, including publishing. We
   don't return anything to CPVGenerator to reduce memory usage and efficiency.

7. Whether it's normal.py, influence.py, or mix.py, the classes there will come up with 1 or multiple (c, p, v) 
   requests. They are responsible for looping over those and sending them straight to the Publisher without going
   back to CPVGenerator.

8. When a CPV request enters the publisher, it should enter in the form (generator, channel, parameter, value) where
   generator is the CPVGenerator instance. 

9. When the publisher receives a CPV, the publisher is responsible for the following:
        a. Splitting color from RGB into whatever color profile the appropriate fixture wants
        b. Formatting color from mathutils.Color into the scaled (100, 100, 100) tuple
        c. Mapping special values like zoom and pan/tilt from the UI slider value to what the individual fixture needs
        d. Finding the "patch object" for each CPV, which is the object or controller providing things like pan_max,
           tilt_min, zoom_min, the right argument template for a certain fixture's gobo wheel, etc. 
        e. Formatting the channel and value for the console in preperation for sending over OSC
        f. Deciding whether to send OSC now or later, based on whether we need to use the harmonizer or not (this 
           would need to be done later if we are in playback, so we can wait for everyone else to show up). 

10. When it's ready, the publisher sends its CPV request(s) in (address, argument) format to the utils folder to
    be sent to the console over OSC.
"""


'''
This folder is kind of like DMX, but way less dumb. A DMX universe is basically just a list of 512
values. DMX does not provide context to tell you what the values are supposed to be. The end user 
has to manually provide that context to the computer (the patch screen). DMX stands for Digital Multiplex,
which isn't very descriptive.

CPV stands for Channel, Parameter, Value. A CPV signal provides the context needed for interpretation
within the signal itself. You just set the light to be the channel and you're done. No patch screen ever.

DMX: [value, value, value, value, value, value, ...] 
CPV: [(channel, parameter, value), (channel, parameter, value), (channel, parameter, value), ...]

The downside of CPV is it uses about 3x as much bandwidth to send the same message. DMX prioritizes speed
at the expense of user experience. CPV says that computers are way faster now than when DMX was developed, so 
we can totally afford less dumb tech. First-principles thinking tells us to simplify the problem to its most 
irreducible components: in this case, bytes and hertz. How many bytes are a DMX packet? It's basically no bytes.
What's the most amount of bytes we can pump at 60 hz? It's like a lot of bytes. Do the math and it ends up
being the equivalent of 10's of thousands of universes. 

So that's why we can totally afford CPV.

But at the same time, DMX sends all parameters on every packet, even ones that aren't changing. CPV only sends
change requests. So that difference alone makes CPV actually less expensive than DMX in 80% of cases. That's 
before you even consider the modern advances in computing speed. But at the same time, when you build a bridge,
you don't design for the 80th percentile of expected loads.

This folder contains most of the logic for Alva Sorcerer that converts the stuff you do with a controller in the 
UI to stuff the lighting console can understand. Sorcerer uses the CPV format internally. In the future, 
Alva Theaters hopes to experiment with using the CPV format externally to replace DMX in-house. 

A key benfit of CPV in the context of Sorcerer is that it is compatible with Lighting, Video and Audio (ALVA). 
Sorcerer's 3D audio renderer is already written in the CPV format. PTX camera logic will also be written in
the CPV format. This way, all theater devices, no matter the department, speak the same language.
'''