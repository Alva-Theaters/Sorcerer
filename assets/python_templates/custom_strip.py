import bpy
from bpy import spy
# from spy.types import SequencerStrip will not work here.


class SEQUENCER_ST_custom_strip(spy.types.SequencerStrip):  # Not quite bpy, but pretty close!
    as_idname = 'option_custom_strip'
    as_label = "Custom Strip"  # Sorcerer will not automatically add the "Strip" to the end when drawing the label.
    as_description = "Use a custom Sorcerer strip!"
    as_icon = 'HEART'

    event_type = 'macro'  # If using ETC Eos, this tells the sync button what type of event to use, cue or macro.
    options = {'EVENT_MANAGER'}  # Add 'ORB' to use the sync button, 'EVENT_MANAGER' to stream live on playback, don't use both.


    # UI ----------------------------------------------------------------------------------------------------------------------------------
    def draw(context, column, box, active_strip):  # This will draw in the middle of the color strip panel
        row = box.row()  # Use box to make normal rows without adding lines
        row.label(text="Macro numbers:")
        row = box.row()
        row.prop(active_strip, 'message_one_text', text="Start")
        row = box.row()
        row.prop(active_strip, 'message_two_text', text="Middle") # We'll make this fire in the middle of the strip.
        row = box.row()
        row.prop(active_strip, 'message_three_text', text="End")

        box = column.box()  # Use column to make a line that goes across the entire box without making a new one
        row = box.row()
        row.label(text="Make middle message fire in the middle of the strip!")

        row.separator()


    # Mapping -----------------------------------------------------------------------------------------------------------------------------
    def poll(value):  # Make this return False when a strip should be ignored by mapping, for example if the macro number is set to 0.
        return value != ""


    # These next four can return multiple values, not just 1.
    def get_start_frame(strip):  # This tells the mapping function what time the first event should happen in reference to the strip's location.
        start = strip.frame_start

        # We'll tack on a message to the middle of the strip too, just because we can!
        strip_length_in_frames = strip.frame_final_end - strip.frame_start
        middle = start + (strip_length_in_frames / 2)
        middle = round(middle)
        
        return start, middle
    
    def get_start_value(strip):  # This tells the mapping function what the value should be for the start frame
        '''int_start/end_macro is used internally by built-in Orb operators, but is not exposed in the UI.
            Use int_start_macro or int_end_macro if you want Orb to choose one for you automatically. Defaults
            to something like Macro 88889. The allowed ranges can be set in Settings.'''
        start = strip.message_one_text
        middle = strip.message_two_text
        
        return start, middle
    

    def get_end_frame(strip):  # This is the same as the last two, just for the end of the strip. Skip if not needed.
        return strip.frame_final_end
    
    def get_end_value(strip):
        return strip.message_three_text
    

    def form_osc(strip, value):  # Only used with the 'EVENT_MANAGER' option. Use strip to access other strip data.
        address = "/eos/newcmd"
        argument = value
        print(address, argument)
        return address, argument
    

    # Orb ----------------------------------------------------------------------------------------------------------------------------------
    'Coming soon!'


def register():
    bpy.types.ColorSequence.message_one_text = bpy.props.StringProperty(default="")
    bpy.types.ColorSequence.message_two_text = bpy.props.StringProperty(default="")
    bpy.types.ColorSequence.message_three_text = bpy.props.StringProperty(default="")

    spy.utils.as_register_class(SEQUENCER_ST_custom_strip)  # "as" stands for Alva Sorcerer


def unregister():
    spy.utils.as_unregister_class(SEQUENCER_ST_custom_strip)


if __name__ == '__main__':
    register()