# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
import traceback
try:
    import allin1 # type: ignore
except:
    pass


class BiasCalculator():
    '''
    Returns bias in frames. Use by adding this class's integer return value to the strip's start frame.
    
    Problem: 
        Flash strips want to make a light on the stage flash up and flash down. It would be pretty boring 
        if it had to flash up just as fast as it flashes down. 

    Solution:
        We add a "Bias" property to the flash strip GUI. This number, between -49 and 49, can make the 
        light flash up super fast and go back down super slow (if a strong negative value) or the opposite
        (if a strong positive value). If bias is set to 0, it comes up and comes down at equal speed.

    This Code:
        This code is passed the bias property from the UI and the parent strip's length in frames. It then 
        converts the bias property to number of frames. Whoever called this code is then responsible for 
        adding that bias_in_frames value to the start frame to give the frame that the flash down action 
        should happen on.
    '''
    def __init__(self, bias, strip_length_in_frames):
        self.bias = bias
        self.strip_length_in_frames = strip_length_in_frames
        

    def execute(self):
        if self.bias == 0:
            return self._divide_in_half()
        elif self.bias < 0:
            return self._make_it_start_faster_and_end_slower()
        else:
            return self._make_it_start_slower_and_end_faster()
        
    def _divide_in_half(self):
        return self.strip_length_in_frames / 2

    def _make_it_start_faster_and_end_slower(self):
        proportion_of_first_half = (49 + self.bias) / 49  # It's 49 because UI shows scale of -49 to 49
        return round(self.strip_length_in_frames * proportion_of_first_half * 0.5)

    def _make_it_start_slower_and_end_faster(self):
        proportion_of_second_half = self.bias / 49  # It's 49 because UI shows scale of -49 to 49
        return round(self.strip_length_in_frames * (0.5 + proportion_of_second_half * 0.5))
    

def form_livemap_string(self):
    return f"Go_to_Cue {str(self.eos_cue_number)} Time Enter"


def duplicate_active_strip_to_selected(context):
    sequence_editor = context.scene.sequence_editor
    active_strip = sequence_editor.active_strip

    if not active_strip or active_strip.type != 'COLOR':
        return False, "No active color strip found."

    selected_strips = [strip for strip in sequence_editor.sequences if strip.select and strip != active_strip and strip.type == 'COLOR']
    
    if not selected_strips:
        return False, "No other selected color strips found."

    original_names = [strip.name for strip in selected_strips]
    original_start_frames = [strip.frame_start for strip in selected_strips]
    original_channels = [strip.channel for strip in selected_strips]

    new_strips = []
    
    for strip in selected_strips:
        sequence_editor.sequences.remove(strip)

    for original_start_frame, original_channel in zip(original_start_frames, original_channels):
        bpy.ops.sequencer.select_all(action='DESELECT')
        active_strip.select = True

        bpy.ops.sequencer.duplicate()

        duplicated_strip = next(strip for strip in sequence_editor.sequences if strip.select and strip != active_strip and strip not in new_strips)

        duplicated_strip.channel = original_channel - 1  # I don't know why this need - 1, but it goes up a channel for no reason otherwise.
        duplicated_strip.frame_start = original_start_frame
        
        new_strips.append(duplicated_strip)

        active_strip.select = False

    for new_strip, original_name in zip(new_strips, original_names):
        new_strip.name = original_name

    for strip in new_strips:
        strip.select = True

    return True, "Strips replaced with duplicates of the active strip successfully."


def find_available_channel(sequence_editor, start_frame, end_frame, start_channel=1):
    current_channel = start_channel

    while True:
        is_occupied = any(
            strip.channel == current_channel and not (strip.frame_final_end < start_frame or strip.frame_start > end_frame)
            for strip in sequence_editor.sequences
        )
        if not is_occupied:
            return current_channel
        current_channel += 1


def add_color_strip(name, length, channel, color, strip_type, frame, position=(0,0), scale=(1,1)):
    scene = bpy.context.scene
    strip = scene.sequence_editor.sequences.new_effect(
        name=name,
        type='COLOR',
        channel=channel,
        frame_start=int(frame),
        frame_end=int(frame + length)
    )
    strip.color = color
    strip.my_settings.motif_type_enum = strip_type
    strip.transform.offset_x = position[0]
    strip.transform.offset_y = position[1]
    strip.transform.scale_x = scale[0]
    strip.transform.scale_y = scale[1]


class Segment:
    def __init__(self, start, end, label):
        self.start = start
        self.end = end
        self.label = label

    def __repr__(self):
        return f"Segment(start={self.start}, end={self.end}, label='{self.label}')"

class AnalysisResult:
    def __init__(self, path, bpm, beats, beat_positions, downbeats, segments):
        self.path = path
        self.bpm = bpm
        self.beats = beats
        self.beat_positions = beat_positions
        self.downbeats = downbeats
        self.segments = segments

    def __repr__(self):
        return (f"AnalysisResult(path='{self.path}', bpm={self.bpm}, beats={self.beats}, "
                f"beat_positions={self.beat_positions}, downbeats={self.downbeats}, segments={self.segments})")


def analyze_song(self, filepath):
    try:
        return allin1.analyze(filepath, keep_byproducts=True)
    except Exception as e:
        print("An error occurred in allin1.analyze()!")
        print(traceback.format_exc())
        print(f"Error Type: {type(e).__name__}, Message: {e}")
        print("Allin1 not found or failed. Returning hardcoded dummy class.")

        return AnalysisResult(
            path=filepath, 
            bpm=100,
            beats=[
                0.33, 0.75, 1.14, 1.55, 1.97, 2.38, 2.79, 3.21, 3.62, 4.03, 4.44, 4.86, 5.27, 5.68, 6.10, 6.51, 6.92, 7.33,
                7.75, 8.16, 8.57, 8.98, 9.40, 9.81, 10.22, 10.63, 11.05, 11.46, 11.87, 12.29, 12.70, 13.11, 13.53, 13.94,
                14.35, 14.76, 15.18, 15.59, 16.00, 16.41, 16.83, 17.24, 17.65, 18.06, 18.48, 18.89, 19.30, 19.71, 20.13,
                20.54, 20.95, 21.36, 21.78, 22.19, 22.60, 23.01, 23.43, 23.84, 24.25, 24.66, 25.08, 25.49, 25.90, 26.31,
                26.73, 27.14, 27.55, 27.96, 28.38, 28.79, 29.20, 29.61, 30.03, 30.44, 30.85, 31.26, 31.68, 32.09, 32.50,
                32.91, 33.33, 33.74, 34.15, 34.56, 34.98, 35.39, 35.80, 36.21, 36.63, 37.04, 37.45, 37.86, 38.28, 38.69,
                39.10, 39.51, 39.93, 40.34, 40.75, 41.16, 41.58, 41.99, 42.40, 42.81, 43.23, 43.64, 44.05, 44.46, 44.88,
                45.29, 45.70, 46.11, 46.53, 46.94, 47.35, 47.76, 48.18, 48.59, 49.00, 49.41, 49.83, 50.24, 50.65, 51.06,
                51.48, 51.89, 52.30, 52.71, 53.13, 53.54, 53.95, 54.36, 54.78, 55.19, 55.60, 56.01, 56.43, 56.84, 57.25,
                57.66, 58.08, 58.49, 58.90, 59.31, 59.73, 60.14, 60.55, 60.96, 61.38, 61.79, 62.20, 62.61, 63.03, 63.44,
                63.85, 64.26, 64.68, 65.09, 65.50, 65.91, 66.33, 66.74, 67.15, 67.56, 67.98, 68.39, 68.80, 69.21, 69.63,
                70.04, 70.45, 70.86, 71.28, 71.69, 72.10, 72.51, 72.93, 73.34, 73.75, 74.16, 74.58, 74.99, 75.40, 75.81,
                76.23, 76.64, 77.05, 77.46, 77.88, 78.29, 78.70, 79.11, 79.53, 79.94, 80.35, 80.76, 81.18, 81.59, 82.00,
                82.41, 82.83, 83.24, 83.65, 84.06, 84.48, 84.89, 85.30, 85.71, 86.13, 86.54, 86.95, 87.36, 87.78, 88.19,
                88.60, 89.01, 89.43, 89.84, 90.25, 90.66, 91.08, 91.49, 91.90, 92.31, 92.73, 93.14, 93.55, 93.96, 94.38,
                94.79, 95.20, 95.61, 96.03, 96.44, 96.85, 97.26, 97.68, 98.09, 98.50, 98.91, 99.33, 99.74, 100.15, 100.56,
                100.98, 101.39, 101.80, 102.21, 102.63, 103.04, 103.45, 103.86, 104.28, 104.69, 105.10, 105.51, 105.93
            ],
            beat_positions=[
                1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4,
                1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4,
                1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4,
                1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4,
                1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4,
                1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4,
                1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4,
                1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4
            ],
            downbeats=[
                0.33, 1.94, 3.53, 5.12, 6.71, 8.30, 9.90, 11.49, 13.08, 14.67, 16.26, 17.86, 19.45, 21.04, 22.63, 24.22, 25.82,
                27.41, 29.00, 30.59, 32.18, 33.78, 35.37, 36.96, 38.55, 40.14, 41.74, 43.33, 44.92, 46.51, 48.10, 49.70, 51.29,
                52.88, 54.47, 56.06, 57.66, 59.25, 60.84, 62.43, 64.02, 65.62, 67.21, 68.80, 70.39, 71.98, 73.58, 75.17, 76.76,
                78.35, 79.94, 81.54, 83.13, 84.72, 86.31, 87.90, 89.50, 91.09, 92.68, 94.27, 95.86, 97.46, 99.05, 100.64, 102.23,
                103.82, 105.42, 107.01, 108.60, 110.19, 111.78, 113.38, 114.97, 116.56, 118.15, 119.74, 121.34, 122.93, 124.52,
                126.11, 127.70, 129.30, 130.89, 132.48, 134.07, 135.66, 137.26, 138.85, 140.44, 142.03, 143.62, 145.22, 146.81,
                148.40, 149.99, 151.58, 153.18, 154.67
            ],
            segments=[
                Segment(start=0.0, end=0.33, label='start'), 
                Segment(start=0.33, end=13.13, label='intro'), 
                Segment(start=13.13, end=37.53, label='chorus'), 
                Segment(start=37.53, end=51.53, label='verse'), 
                Segment(start=51.53, end=64.34, label='verse'), 
                Segment(start=64.34, end=89.93, label='chorus'), 
                Segment(start=89.93, end=105.93, label='bridge'), 
                Segment(start=105.93, end=134.74, label='chorus'), 
                Segment(start=134.74, end=153.95, label='chorus'), 
                Segment(start=153.95, end=154.67, label='end'),
            ]
    )