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

Operator ClassNames should **NOT** use ALVA_operator_name as in other add-ons. Because Sorcerer is spread between a dozen different Blender space_types, Blender's internal naming scheme is adopted. Instead, they **SHOULD** use ClassNames like VIEW_3D_alva_verb_noun. Adding "alva" to the middle differentiates Sorcerer's operators from other operators while retaining the space_type name in the uppercase prefix.

✅ `alva_sequencer.macro_create`  
❌ `alva.create_macro`

✅ `SEQUENCER_OT_alva_macro_create`  
❌ `ALVA_OT_create_macro`