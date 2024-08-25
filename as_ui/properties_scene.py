# This file is part of Alva ..
# Copyright (C) 2024 Alva Theaters

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


'''
=====================================================================
                      DESIGNED BY ALVA THEATERS
                       FOR THE SOLE PURPOSE OF
                         MAKING PEOPLE HAPPY
=====================================================================
'''


## Double hashtag indicates notes for future development requiring some level of attention


import bpy

from .space_time import draw_properties_sync

# Custom icon stuff
import bpy.utils.previews
import os
preview_collections = {}
pcoll = bpy.utils.previews.new()
preview_collections["main"] = pcoll
addon_dir = os.path.dirname(__file__)
pcoll.load("orb", os.path.join(addon_dir, "alva_orb.png"), 'IMAGE')


poll_one = ""
poll_two = ""
poll_three = ""
poll_four = ""


def draw_alva_properties_navigation(self, context): # To indicate to user that Sorcerer has stuff here
    pcoll = preview_collections["main"]
    orb = pcoll["orb"]

    layout = self.layout
    row = layout.row()
    row.alignment = 'RIGHT'
    row.label(text="", icon_value=orb.icon_id)


def draw_alva_properties_sync(self, context):
    return


def draw_alva_cue_switcher(self, context):
    layout = self.layout
    scene = context.scene.scene_props
        
    if len(context.scene.cue_lists) > 0:
        cue_list = context.scene.cue_lists[scene.cue_lists_index]
        #cue = cue_list.cues[cue_list.int_preview_index]
        
        # Cue lists
        split = layout.split(factor=0.5)
        
        # Preview Cues with Add/Remove buttons
        col1 = split.column()
        col1.label(text="Preview:")
        row = col1.row()
        row.template_list("SCENE_UL_preview_cue_list", "", cue_list, "cues", cue_list, "int_preview_index")
        
        col_buttons = row.column(align=True)
        col_buttons.operator("cue.add_cue", text="", icon='ADD')
        col_buttons.operator("cue.remove_cue", text="", icon='REMOVE')
        
        col_buttons.separator()
        col_buttons.prop(cue_list, "is_progressive", text="", icon='FORWARD' if cue_list.is_progressive else 'ARROW_LEFTRIGHT', emboss=False)
        
        # Program Cues with Add/Remove buttons
        col2 = split.column()
        col2.alert = 1
        col2.label(text="Program:")
        row = col2.row()
        row.alert=1
        row.enabled=0
        row.template_list("SCENE_UL_program_cue_list", "", cue_list, "cues", cue_list, "int_program_index")
        row.alert=0
        

        layout.separator()
        
        t_bar_split = layout.split(factor=.15)
        
        col1 = t_bar_split.column()
        col1.scale_y = 3
        col1.alert = 1
        col1.operator("cue.cut", text="Cut")
        col1.operator("cue.self", text="Self")
        
        col2 = t_bar_split.column()
        col2.scale_y = 6
        col2.alert = 1
        if cue_list.int_t_bar == 0 or cue_list.int_t_bar == 100:
            col2.alert = 0
        col2.prop(cue_list, "int_t_bar", slider=True, text="T-bar")
        col2.alert=0
        
        layout.separator()
        
        # Outer split to divide the panel into left and right halves
        outer_split = layout.split(factor=0.7)

        # Use the left half for our content
        left = outer_split.column()

        # Inner split to create three columns in the left half
        inner_split = left.split(factor=0.25)
        col1 = inner_split.column()
        col2 = inner_split.column()
        col3 = inner_split.column()
        col4 = inner_split.column()

        # Create boxes for each group and organize them into the columns

        # Box for Auto
        box_restore = col1.box()
        box_restore.label(text="Fade to Preview:")
        row = box_restore.row()
        row.scale_y = 3
        row.alert = 1
        row.operator("cue.auto", text="Auto")
        row.alert = 0
        box_restore.prop(scene, "float_auto_time", text="Rate:")
        box_restore.label(text="(Preview cue)")

        # Box for Restore
        box_restore = col2.box()
        box_restore.label(text="Restore to Base Cue:")
        row = box_restore.row()
        row.scale_y = 3
        row.alert = 1
        row.operator("cue.restore", text="Restore")
        row.alert = 0
        box_restore.prop(scene, "float_restore_time", text="Rate:")
        box_restore.prop(scene, "string_restore_cue", text="Cue")

        # Box for Black
        box_black = col3.box()
        box_black.label(text="Fade to Black:")
        row = box_black.row()
        row.scale_y = 3
        row.alert = 1
        row.operator("cue.black", text="Black")
        row.alert = 0
        box_black.prop(scene, "float_black_time", text="Rate:")
        box_black.prop(scene, "string_black_cue", text="Cue")

        # Box for Blue
        box_blue = col4.box()
        box_blue.label(text="Fade to Blue:")
        row = box_blue.row()
        row.scale_y = 3
        row.alert = 1
        row.operator("cue.blue", text="Blue")
        row.alert = 0
        box_blue.prop(scene, "float_blue_time", text="Rate:")
        box_blue.prop(scene, "string_blue_cue", text="Cue")

        # Right column for the list of songs
        right = outer_split.column()
        box = right.box()
        row = box.row()
        row.label(text="Songs:")
        row = box.row()
        row.template_list("SCENE_UL_cue_list_list", "", context.scene, "cue_lists", scene, "cue_lists_index")

        # Add/Remove buttons for the master cue list
        col = row.column(align=True)
        col.operator("cue_list.add_list", text="", icon='ADD')
        col.operator("cue_list.remove_list", text="", icon='REMOVE')
        
        row = box.row()
        row.prop(cue_list, "int_cue_list_number", text="Cue List:")
        
    else:
        layout.operator("cue_list.add_list", text="Add Song", icon='ADD')


def draw_alva_stage_manager(self, context):
    layout = self.layout
    scene = context.scene.show_sequencer
    
    global poll_one
    global poll_two
    global poll_three
    global poll_four

    row = layout.row()
    row.scale_y = 2

    row.prop(scene, "sequence_status_enum", expand=True)
    row.alert = 0
    if (scene.weather_anomaly or 
        scene.shelter_in_place or scene.emergency or scene.fire or 
        scene.evacuate or scene.fire_curtain or scene.hold):
        row.alert = True
    row.prop(scene, "hold", text="HOLD", toggle=1)
    
    '''CHECKLISTS/POLLS SECTION'''
    
    # Lobby Open Checklist
    layout.separator()
    layout.separator()
    row = layout.row()
    row.label(text="Lobby Open Checklist")
    row.scale_x = .25
    row.prop(scene, "open_lobby_poll_time", text="Time")
    box = layout.box()
    row = box.row()
    row.label(text='"All crew, yes/no poll for Lobby Open beginning with Backstage, are all members present?..."')
    row = box.row()
    row.alert = not scene.all_members_present
    row.prop(scene, "all_members_present", text="All Members Present" if scene.all_members_present else "Are All Members Present?", toggle=True)
    row.alert = 0
    row.label(text="", icon='RIGHTARROW')
    row.alert = not scene.stage_is_set
    row.prop(scene, "stage_is_set", text="Stage is Set" if scene.stage_is_set else "Is Stage Set?", toggle=True)
    row.alert = 0
    row.label(text="", icon='RIGHTARROW')
    row.alert = not scene.cleaning_is_complete
    row.prop(scene, "cleaning_is_complete", text="Stage is Clean" if scene.cleaning_is_complete else "Is Stage Clean?", toggle=True)                     
    row.alert = 0
    row.label(text="", icon='RIGHTARROW')
    row.alert = not scene.fly_is_set
    row.prop(scene, "fly_is_set", text="Fly is Set" if scene.fly_is_set else "Is Fly Set?", toggle=True)   
    row = box.row()
    if (not scene.go_for_lobby_open or not scene.fly_is_set or not scene.cleaning_is_complete or not
        scene.stage_is_set or not scene.all_members_present):
        row.alert = True
        poll_one = "Hold"
    else: poll_one = "Go"
    row.prop(scene, "go_for_lobby_open", emboss=False, text='"Go for Lobby Open. Crew, set the theater to House Open Configuration."' if scene.go_for_lobby_open else "Lobby Stay Closed", toggle=True)
    
    # House Open Checklist
    layout.separator()
    layout.separator()
    row = layout.row()
    row.label(text="House Open Checklist")
    row.scale_x = .25
    row.prop(scene, "open_house_poll_time", text="Time")
    box = layout.box()
    row = box.row()
    row.label(text='"All crew, yes/no poll for House Open beginning with backstage, are set pieces placed?..."')
    row = box.row()
    row.alert = not scene.set_pieces_are_set
    row.prop(scene, "set_pieces_are_set", text="Set Pieces Are Placed" if scene.set_pieces_are_set else "Are Set Pieces Placed?", toggle=True)
    row.alert = 0
    row.label(text="", icon='RIGHTARROW')
    row.alert = not scene.props_are_set
    row.prop(scene, "props_are_set", text="Props Are Placed" if scene.props_are_set else "Are Props Placed?", toggle=True)
    row.alert = 0
    row.label(text="", icon='RIGHTARROW')
    row.alert = not scene.lights_are_tested
    row.prop(scene, "lights_are_tested", text="Lights Are Tested" if scene.lights_are_tested else "Are Lights Tested?", toggle=True)                     
    row.alert = 0
    row.label(text="", icon='RIGHTARROW')
    row.alert = not scene.sound_is_checked
    row.prop(scene, "sound_is_checked", text="Sound is Checked" if scene.sound_is_checked else "Is Sound Checked?", toggle=True)  
    row = box.row()
    row.alert = 0
    row.label(text="", icon='RIGHTARROW')
    row.alert = not scene.warmups_is_complete
    row.prop(scene, "warmups_is_complete", text="Warm-ups is Complete" if scene.warmups_is_complete else "Is Warm-ups Complete?", toggle=True)          
    row.alert = 0
    row.label(text="", icon='RIGHTARROW')
    row.alert = not scene.stage_is_clear_of_props
    row.prop(scene, "stage_is_clear_of_props", text="Stage is Cleared" if scene.stage_is_clear_of_props else "Is Stage Clear?", toggle=True)
    row.alert = 0
    row.label(text="", icon='RIGHTARROW')
    row.alert = not scene.spotlights_are_tested
    row.prop(scene, "spotlights_are_tested", text="Spotlights Are Tested" if scene.spotlights_are_tested else "Are Spotlights Tested?", toggle=True)                     
    row.alert = 0
    row.label(text="", icon='RIGHTARROW')
    row.alert = not scene.house_manager_is_go_one
    row.prop(scene, "house_manager_is_go_one", text="HM Go for House Open" if scene.house_manager_is_go_one else "Is House Manager Clear?", toggle=True)  
    row = box.row()
    if (not scene.go_for_house_open or not scene.set_pieces_are_set or not scene.props_are_set
        or not scene.lights_are_tested or not scene.sound_is_checked or not scene.warmups_is_complete
        or not scene.stage_is_clear_of_props or not scene.spotlights_are_tested or not
        scene.house_manager_is_go_one):
        row.alert = True
        poll_two = "Hold"
    else: poll_two = "Go" 
    row.prop(scene, "go_for_house_open", emboss=False, text='"Crew, set the theater to Show Open Configuration. House Manager, please open the house."' if scene.go_for_house_open else "House Stay Closed", toggle=True)
                
    # Final Go/No Go poll
    layout.separator()
    layout.separator()
    row = layout.row()
    row.label(text="Go/No Go Poll")
    row.scale_x = .25
    row.prop(scene, "go_no_go_poll_time", text="Time")
    box = layout.box()
    row = box.row()
    row.label
    row.label(text='"All crew, go/no go poll for Show-Start beginning with fly..."')
    row = box.row()
    row.alert = not scene.fly_is_go
    row.prop(scene, "fly_is_go", text="Fly is Go" if scene.fly_is_go else "Fly", toggle=True)
    row.alert = 0
    row.label(text="", icon='RIGHTARROW')
    row.alert = not scene.sound_is_go
    row.prop(scene, "sound_is_go", text="Sound is Go" if scene.sound_is_go else "Sound", toggle=True)
    row.alert = 0
    row.label(text="", icon='RIGHTARROW')
    row.alert = not scene.lights_is_go
    row.prop(scene, "lights_is_go", text="Lights is Go" if scene.lights_is_go else "Lights", toggle=True)
    row.alert = 0
    row.label(text="", icon='RIGHTARROW')
    row.alert = not scene.projections_is_go
    row.prop(scene, "projections_is_go", text="Projections is Go" if scene.projections_is_go else "Projections", toggle=True)
    row = box.row()
    row.label(text="", icon='RIGHTARROW')
    row.alert = not scene.show_support_is_go
    row.prop(scene, "show_support_is_go", text="Show Support is Go" if scene.show_support_is_go else "Show Support", toggle=True)
    row.alert = 0
    row.label(text="", icon='RIGHTARROW')
    row.alert = not scene.backstage_manager
    row.prop(scene, "backstage_manager", text="No Outstanding Tasks" if scene.backstage_manager else "Backstage Manager", toggle=True)
    row.alert = 0
    row.label(text="", icon='RIGHTARROW')
    row.alert = not scene.house_manager_is_go
    row.prop(scene, "house_manager_is_go", text="Proceed with Show-Start" if scene.house_manager_is_go else "House Manager", toggle=True)
    row.label(text="")
    row = box.row()
    if (not scene.go_for_show_open or not scene.house_manager_is_go or not scene.backstage_manager
        or not scene.show_support_is_go or not scene.projections_is_go or not scene.lights_is_go
        or not scene.sound_is_go or not scene.fly_is_go):
        row.alert=1
        poll_three = "Hold"
    else: poll_three = "Go"
    row.prop(scene, "go_for_show_open", emboss=0, text='''"Go for Show-Start. Crew, set the theater to Underway Configuration. To hold, announce 'Hold, hold, hold.'"''' if scene.go_for_show_open else "Show Stay Closed", toggle=True)

    # House Open Checklist
    layout.separator()
    layout.separator()
    row = layout.row()
    row.label(text="Status Check")
    row.scale_x = .25
    row.prop(scene, "status_check_time", text="Time")
    box = layout.box()
    row = box.row()
    row.label(text='"Time is T minus 2 minutes. House manager, please close house doors. All crew, please maintain a sterile theater.')
    row = box.row()
    row.label(text='Now, Status Check, starting with Backstage Manager. Initial cast in place?..."')
    row = box.row()
    row.alert = not scene.initial_cast_in_place
    row.prop(scene, "initial_cast_in_place", text="Initial Cast in Place" if scene.initial_cast_in_place else "Initial Cast in Place?", toggle=True)
    row.alert = 0
    row.label(text="", icon='RIGHTARROW')
    row.alert = not scene.theater_is_ready
    row.prop(scene, "theater_is_ready", text="Stage in Underway Configuration" if scene.theater_is_ready else "Stage in Underway Configuration?", toggle=True)
    row.alert = 0
    row.label(text="", icon='RIGHTARROW')
    row.alert = not scene.control_booth_is_ready
    row.prop(scene, "control_booth_is_ready", text="Control Booth in Underway Configuration" if scene.control_booth_is_ready else "Control Booth in Underway Configuration?", toggle=True)                   
    row.alert = 0
    row = box.row()
    if (not scene.clear_to_proceed or not scene.initial_cast_in_place or not scene.theater_is_ready or not scene.control_booth_is_ready):
        row.alert = True
        poll_four = "Hold"
    else: poll_four = "Go"
    row.prop(scene, "clear_to_proceed", emboss=False, text='"Continuing with Show-Start... T minus 10, 9, 8, 7, 6, 5, 4, 3 , 2, 1, Renegade is in startup, Underway"' if scene.clear_to_proceed else "Not Clear to Proceed", toggle=True)
        
    layout.separator()
    
    
    '''ANOMALIES SECTION'''
    flow = layout.grid_flow(row_major=True, columns=3, even_columns=True, even_rows=True, align=True)
    
    # Technical Anomalies Box 
    box = flow.box()
    box.label(text="Technical Anomalies")
    col = box.column()
    row = col.row()
    row.alert = scene.rigging_anomaly
    row.prop(scene, "rigging_anomaly", text="Rigging Anomaly" if scene.rigging_anomaly else "Rigging Anomaly", toggle=True)
    row.alert = 0
    row = col.row()
    row.alert = scene.sound_anomaly
    row.prop(scene, "sound_anomaly", text="Sound Anomaly" if scene.sound_anomaly else "Sound Anomaly", toggle=True)
    row.alert = 0
    row = col.row()
    row.alert = scene.lighting_anomaly
    row.prop(scene, "lighting_anomaly", text="Lighting Anomaly" if scene.lighting_anomaly else "Lighting Anomaly", toggle=True)
    row.alert = 0
    row = col.row()
    row.alert = scene.projection_anomaly
    row.prop(scene, "projection_anomaly", text="Projection Anomaly" if scene.projection_anomaly else "Projection Anomaly", toggle=True)
    row.alert = 0
    row = col.row()
    row.alert = scene.support_systems_anomaly
    row.prop(scene, "support_systems_anomaly", text="Support Systems Anomaly" if scene.support_systems_anomaly else "Support Systems Anomaly", toggle=True)
    row.alert = 0
    
    # Misc. Anomalies Box
    box = flow.box()
    box.label(text="Miscellaneous Anomalies")
    col = box.column()
    row = col.row()
    row.alert = scene.medical_anomaly
    row.prop(scene, "medical_anomaly", text="Medical Anomaly" if scene.medical_anomaly else "Medical Anomaly", toggle=True)
    row.alert = 0
    row = col.row()
    row.alert = scene.police_activity
    row.prop(scene, "police_activity", text="Police Activity" if scene.police_activity else "Police Activity", toggle=True)
    row.alert = 0
    row = col.row()
    row.alert = scene.missing_person
    row.prop(scene, "missing_person", text="Missing Person" if scene.missing_person else "Missing Person", toggle=True)
    row.alert = 0
    row = col.row()
    row.alert = scene.weather_anomaly
    row.prop(scene, "weather_anomaly", text="Weather Anomaly" if scene.weather_anomaly else "Weather Anomaly", toggle=True)
    row.alert = 0
    row = col.row()
    row.alert = scene.shelter_in_place
    row.prop(scene, "shelter_in_place", text="Shelter in Place" if scene.shelter_in_place else "Shelter in Place", toggle=True)
    row.alert = 0
    
    # Human Deviations Box
    box = flow.box()
    box.label(text="Human Deviations")
    col = box.column()
    row = col.row()
    row.alert = scene.cast_deviation
    row.prop(scene, "cast_deviation", text="Possible Cast Deviation" if scene.cast_deviation else "Cast Deviation", toggle=True)
    row.alert = 0
    row = col.row()
    row.alert = scene.crew_deviation
    row.prop(scene, "crew_deviation", text="Possible Crew Deviation" if scene.crew_deviation else "Crew Deviation", toggle=True)
    row.alert = 0
    row = col.row()
    row.alert = scene.audience_deviation
    row.prop(scene, "audience_deviation", text="Possible Audience Deviation" if scene.audience_deviation else "Audience Deviation", toggle=True)
    row.alert = 0
    
    # Emergency Conditions Box
    box = flow.box()
    box.label(text="Emergency Conditions")
    col = box.column()
    row = col.row()
    row.alert = scene.emergency
    row.prop(scene, "emergency", text='"Emergency, emergency, emergency"' if scene.emergency else "Emergency", toggle=True)
    row.alert = 0
    row = col.row()
    row.alert = scene.fire
    row.prop(scene, "fire", text='"Fire, fire, fire"' if scene.fire else "Fire", toggle=True)
    row.alert = 0
    row = col.row()
    row.alert = scene.evacuate
    row.prop(scene, "evacuate", text='"Evacuate, evacuate, evacuate"' if scene.evacuate else "Evacuate", toggle=True)
    row.alert = 0
    row = col.row()
    row.alert = scene.fire_curtain
    row.prop(scene, "fire_curtain", text='"Engage Fire Curtain"' if scene.fire_curtain else "Fire Curtain", toggle=True)
    row.alert = 0
    row = col.row()
    row.alert = scene.bomb
    row.prop(scene, "bomb", text='"Bomb, bomb, bomb"' if scene.bomb else "Bomb", toggle=True)
    row.alert = 0