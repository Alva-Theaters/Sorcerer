**DO** use `snake_case` for function names, Python variable names, and Blender properties.  
**DO** use `PascalCase` for class names.  
**DO** use `UPPER_CASE` for constants.  
**DO** use f-strings.  

**DO NOT** use `camelCase`.

Single-letter variables (other than `i` for enumeration) are only allowed when referring to a [list] of channel, parameter, or value, and only in the CPV folder.

See [Blender's Python Guidelines](https://developer.blender.org/docs/handbook/guidelines/python/) for reference, but go with the guidelines here in the event of conflict. For example, f-strings are okay here, but are banned in Blender.


Operator Naming
----------------
Operator bl_idnames should be in the format `alva_[topic].noun_verb`. This ensures readability and organization when Blender prints out the list of all the operators inside Blender.

Operator ClassNames should **NOT** use ALVA_operator_name as in other add-ons. Because Sorcerer is spread between a dozen different Blender space_types, Blender's internal naming scheme is adopted. Instead, they **SHOULD** use ClassNames like VIEW_3D_alva_noun_verb. Adding "alva" to the middle differentiates Sorcerer's operators from other operators while retaining the space_type name in the uppercase prefix.

✅ `alva_sequencer.macro_create`  
❌ `alva.create_macro`

✅ `SEQUENCER_OT_alva_macro_create`  
❌ `ALVA_OT_create_macro`


Python Classes
----------------
These make complicated chunks of code easier to understand. Use Python classes to:
- Separate action steps from preparation steps
- Stop yeeting tons of variables between functions
- Create visual hearchy for organization
- Provide bpy.types classes shared properties from one place via inheritance


Do not:
- Make tons of nested classes unless it is meant to be accessed from a command line
- Make tons of classes just because it seems Pythonic
- Turn a 4-line function onto a 100-line class just because it looks like you did more work


Python classes should have an execute() method for the top layer of execution. 

The execute() should clearly and articulately communicate what the class does to a new reader.

Seperate the execute() method from the `__init__` section using 2 blank lines. Use 1 blank line to separate other methods.


Comments
---------
Some say the best code is the code with exhaustive comments. Others say the best code is "self-documenting code". The first is correct because no code is truly self-documenting. The second is correct because excessive inline comments makes it harder to see the actual code.

In Sorcerer, we take the best of both worlds. Here are the guidelines:

- Long, essay-length docstrings at the top are prefered. These should explain the context and the "why". Write these as if to a child.
- Keep inline comments to a minimum by using clear naming and clear separation of concerns.
- If a chunk of code is excessively complex and fragile, consider adding *-style documentation codes inline with a key at the top or bottom.