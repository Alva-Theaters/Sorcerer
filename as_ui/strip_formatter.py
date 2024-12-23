import bpy
from functools import partial

filter_color_strips = partial(filter, bpy.types.ColorSequence.__instancecheck__)

def draw_strip_formatter_color(context, column, scene, active_strip):
    row = column.row(align=True)
    if scene.is_filtering_left:
        row.alert = 1
        row.prop(scene, "is_filtering_left", icon='FILTER')
        row.alert = 0
    elif scene.is_filtering_left == False:
        row.alert = 0
        row.prop(scene, "is_filtering_left", icon='FILTER')
    row.operator("alva_seq.select_similar", text="Select Magnetic") 
    if scene.is_filtering_right:
        row.alert = 1
        row.prop(scene, "is_filtering_right", icon='FILTER')
        row.alert = 0
    elif scene.is_filtering_right == False:
        row.alert = 0
        row.prop(scene, "is_filtering_right", icon='FILTER')

    row = column.row(align=True)
    row.prop(scene, "color_is_magnetic", text="", icon='SNAP_OFF' if not scene.color_is_magnetic else 'SNAP_ON')
    row.prop(active_strip, "color", text="")
    row.operator("alva_seq.copy_attribute", text="", icon='FILE').target = 'color'
    row.operator("alva_seq.formatter_select", text="", icon='RESTRICT_SELECT_OFF').target = 'color'

    row = column.row(align=True)
    row.prop(scene, "strip_name_is_magnetic", text="", icon='SNAP_OFF' if not scene.strip_name_is_magnetic else 'SNAP_ON')
    row.prop(active_strip, "name", text="")  
    row.operator("alva_seq.copy_attribute", text="", icon='FILE').target = 'name'
    row.operator("alva_seq.formatter_select", text="", icon='RESTRICT_SELECT_OFF').target = 'name'

    row = column.row(align=True)
    row.prop(scene, "channel_is_magnetic", text="", icon='SNAP_OFF' if not scene.channel_is_magnetic else 'SNAP_ON')
    row.prop(active_strip, "channel", text_ctxt="Channel: ")
    row.operator("alva_seq.copy_attribute", text="", icon='FILE').target = 'channel'
    row.operator("alva_seq.formatter_select", text="", icon='RESTRICT_SELECT_OFF').target = 'channel'

    row = column.row(align=True)
    row.prop(scene, "duration_is_magnetic", text="", icon='SNAP_OFF' if not scene.duration_is_magnetic else 'SNAP_ON')
    row.prop(active_strip, "frame_final_duration", text="Duration")
    row.operator("alva_seq.copy_attribute", text="", icon='FILE').target = 'frame_final_duration'
    row.operator("alva_seq.formatter_select", text="", icon='RESTRICT_SELECT_OFF').target = 'frame_final_duration'

    row = column.row(align=True)
    row.prop(scene, "start_frame_is_magnetic", text="", icon='SNAP_OFF' if not scene.start_frame_is_magnetic else 'SNAP_ON')
    row.prop(active_strip, "frame_start", text="Start Frame")
    row.operator("alva_seq.frame_jump", text="", icon='PLAY').direction = 1 
    row.operator("alva_seq.copy_attribute", text="", icon='FILE').target = 'frame_start'
    row.operator("alva_seq.formatter_select", text="", icon='RESTRICT_SELECT_OFF').target = 'frame_start'

    row = column.row(align=True)
    row.prop(scene, "end_frame_is_magnetic", text="", icon='SNAP_OFF' if not scene.end_frame_is_magnetic else 'SNAP_ON')
    row.prop(active_strip, "frame_final_end", text="End Frame")
    row.operator("alva_seq.frame_jump", text="", icon='PLAY').direction = 0
    row.operator("alva_seq.copy_attribute", text="", icon='FILE').target = 'frame_final_end'
    row.operator("alva_seq.formatter_select", text="", icon='RESTRICT_SELECT_OFF').target = 'frame_final_end'

    row = column.row(align=True)
    row.operator("alva_tool.copy", text="Copy Various to Selected", icon='FILE')
    column.separator()
    if scene.i_know_the_shortcuts == False:
        row = column.row(align=True)
        row.operator("alva_seq.hotkey_hint", text="Extrude").message = '''Type the "E" key while in sequencer to extrude pattern of 2 strips.'''

        row = column.row(align=True)
        row.operator("alva_seq.hotkey_hint", text="Scale").message = '''Type the "S" key while in sequencer to scale strips.'''

        row = column.row(align=True)
        row.operator("alva_seq.hotkey_hint", text="Grab").message = '''Type the "G" key while in sequencer to grab and move strips.'''

        row = column.row(align=True)
        row.operator("alva_seq.hotkey_hint", text="Grab X").message = '''Type the "G" key, then the "X" key while in sequencer to grab and move strips on X axis only.'''
        row.operator("alva_seq.hotkey_hint", text="Grab Y").message = '''Type the "G" key, then the "Y" key while in sequencer to grab and move strips on Y axis only.'''

        row = column.row(align=True)
        row.operator("alva_seq.hotkey_hint", text="Cut").message = '''Type the "K" key while in sequencer.'''

        row = column.row(align=True)
        row.operator("alva_seq.hotkey_hint", text="Assign to Channel").message = '''Type the "C" key while in sequencer, then channel number, then "Enter" key.'''

    row = column.row(align=True)
    row.prop(scene, "i_know_the_shortcuts", text="I know the shortcuts.")

    selected_color_strips = [strip for strip in filter_color_strips(context.selected_sequences) if strip.select]

    if len(selected_color_strips) > 1:
        column.separator()
        column.separator()

        row = column.row(align=True)
        row.prop(scene, "offset_value", text="Offset in BPM")
        row.operator("alva_seq.offset", text="", icon='CENTER_ONLY')
        column.separator()


def draw_strip_formatter_sound(column, active_strip):
    row = column.row(align=True)
    row.operator("alva_seq.mute", icon='HIDE_OFF' if not active_strip.mute else 'HIDE_ON')
    row.prop(active_strip, "name", text="")
    row = column.row(align=True)
    row.prop(active_strip, "song_bpm_input", text="Beats per minute (BPM)")
    row = column.row(align=True)
    row.prop(active_strip, "beats_per_measure", text="Beats per measure")
    row = column.row(align=True)
    row.prop(active_strip, "song_bpm_channel", text="Generate on channel")
    row.operator("alva_seq.generate_on_song", text="", icon='COLOR')
    column.separator()
    row = column.row(align=True)
    row.operator("alva_seq.start_end_frame_mapping", icon='PREVIEW_RANGE')
    row = column.row(align=True)
    row.operator("alva_seq.set_timecode", text="Zero Timecode", icon='TIME')
    column.separator()
    row = column.row(align=True)
    row.prop(active_strip, "show_waveform", slider=True)
    row = column.row()
    row.prop(active_strip, "volume", text="Volume")
    

def draw_strip_formatter_video_audio(column, active_strip, sequence_editor):
    selected_sound_strips = []
    selected_video_strips = []
    selected_strips = []
    if sequence_editor:
        for strip in sequence_editor.sequences:
            if strip.select:
                selected_strips.append(strip)
                if strip.type == 'SOUND':
                    selected_sound_strips.append(strip)
                elif strip.type == 'MOVIE':
                    selected_video_strips.append(strip)
    selected_sound_strip = selected_sound_strips[0]
    selected_video_strip = selected_video_strips[0]

    row = column.row(align=True)
    row.operator("alva_seq.mute", icon='HIDE_OFF' if not active_strip.mute else 'HIDE_ON')
    row.prop(active_strip, "name", text="")

    row = column.row(align=True)
    if selected_sound_strip.frame_start != selected_video_strip.frame_start or selected_sound_strip.frame_final_duration != selected_video_strip.frame_final_duration:
        row.alert = 1
        row.operator("alva_seq.sync_video")

    row = column.row(align=True)
    row.operator("alva_seq.start_end_frame_mapping", icon='PREVIEW_RANGE')

    row = column.row(align=True)
    row.operator("alva_seq.set_timecode", icon='TIME')
    

def draw_strip_formatter_generator(column, scene):
    row = column.row(align=True)            
    row.prop(scene, "channel_selector", text="Channel")
    row.operator("alva_seq.select_channel", text="", icon='RESTRICT_SELECT_OFF')   

    row = column.row(align=True)
    row.prop(scene, "generate_quantity", text="Quantity")

    row = column.row(align=True)
    if scene.generate_quantity > 1:
        row.prop(scene, "normal_offset", text="Offset by")

    row = column.row(align=True)
    row.operator("alva_seq.generate", icon='COLOR')  

    column.separator()