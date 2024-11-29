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

This folder contains most of the logic for Alva Sorcerer that converts the stuff you do with a controller in the 
UI to stuff the lighting console can understand. Sorcerer uses the CPV format internally. In the future, 
Alva Theaters hopes to experiment with using the CPV format externally to replace DMX in-house. 

A key benfit of CPV in the context of Sorcerer is that it is compatible for Lighting, Video and Audio (ALVA). 
Sorcerer's 3D audio renderer is already written in the CPV format. PTX camera logic will also be written in
the CPV format. This way, all theater devices, no matter the department, speak the same language.
'''