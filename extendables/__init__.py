'''
Normal software components are like a big team of people. They get off the bus and scatter throughout the city to do their work. 
Extendable software components are like those teams of people, only they stay on the bus. An end user can't really add their own 
version of a normal software component because there are so many places they would need to visit throughout the city. They would 
have to talk to so many different people. However, the extendable teams don't need to leave the bus: all their work can be done in 
one spot and the entire team only needs to talk to one person in the city who comes to them. This makes it much easier for the end 
user to add their own custom extendable software components.

Sorcerer has a mix of extendable and normal software components. The extendable components must be entirely self-contained inside 
a single class. Everything that makes that component unique must be consolidated into that class. That class must be registered 
into the internal data structure at run time with an iterative loop. This means that the built-in classes will work the exact same 
way as the user-written classes. 

Blender works the same way, with bpy.types classes (Panels, Operators, Nodes, etc.)
'''