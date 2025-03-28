# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from ..cpv.mix import test_mixer
from ..cpv.publish.map import test_mapping
from ..cpv.cpv_generator import test_cpv_generator
from ..cpv.stop import test_flags
from ..cpv.publish.publish import test_publisher
from ..cpv.harmonize import test_harmonizer
from ..cpv.influence import test_influencers
from ..cpv.split_color import test_split_color


# TODO: This currently does nothing. It should probably do stuff.


def test_sorcerer():
    cpv_fails, cpv_fail_explanation, cpv_fail_severity = test_cpv(
        CPV_GENERATOR_SENSITIVITY = .5,
        FLAGS_SENSITIVITY = .5,
        HARMONIZER_SENSITIVITY = .5,
        INFLUENCERS_SENSITIVITY = .5,
        MAPPING_SENSITIVITY = .5,
        MIXER_SENSITIVITY = .5,
        PUBLISHER_SENSITIVITY = .5,
        SPLIT_COLOR_SENSITIVITY = .5,
        THRESHOLD = 3
    )

    orb_fails, orb_fail_explanation, orb_fail_severity = test_orb(
        RENDER_QMEO_SENSITIVITY = .5,
        STRIPS_SENSITIVITY = .5,
        RENDER_SEQUENCER_SENSITIVITY = .5,
        PATCH_GROUPS_SENSITIVITY = .5
    )

    scene = bpy.context.scene.scene_props
    scene.errors.clear()

    if cpv_fails:
        scene.limp_mode = True
        new_error = scene.errors.add()
        new_error.error_type = "CPV"
        new_error.explanation = cpv_fail_explanation
        new_error.severity = cpv_fail_severity

    if orb_fails:
        scene.limp_mode = True
        new_error = scene.errors.add()
        new_error.error_type = "ORB"
        new_error.explanation = orb_fail_explanation
        new_error.severity = orb_fail_severity

    if not orb_fails and not cpv_fails:
        scene.limp_mode = False

    num_errors = 0
    if orb_fails:
        scene.user_limp_mode_explanation = orb_fail_explanation
        num_errors = 1
    if cpv_fails:
        scene.user_limp_mode_explanation = cpv_fail_explanation # Overwrite with the more important error
        num_errors += 1
    scene.number_of_systems_down = num_errors


def test_cpv(
        CPV_GENERATOR_SENSITIVITY,
        FLAGS_SENSITIVITY,
        HARMONIZER_SENSITIVITY,
        INFLUENCERS_SENSITIVITY,
        MAPPING_SENSITIVITY,
        MIXER_SENSITIVITY,
        PUBLISHER_SENSITIVITY,
        SPLIT_COLOR_SENSITIVITY,
        THRESHOLD
    ): # Returns True for fail, False for pass, which I here is opposite of how it's supposed to be.

    test_results = {
        'cpv_generator_fails': test_cpv_generator(CPV_GENERATOR_SENSITIVITY),
        'flags_fails': test_flags(FLAGS_SENSITIVITY),
        'harmonizer_fails': test_harmonizer(HARMONIZER_SENSITIVITY),
        'influencers_fails': test_influencers(INFLUENCERS_SENSITIVITY),
        'mapping_fails': test_mapping(MAPPING_SENSITIVITY),
        'mixer_fails': test_mixer(MIXER_SENSITIVITY),
        'publisher_fails': test_publisher(PUBLISHER_SENSITIVITY),
        'split_color_fails': test_split_color(SPLIT_COLOR_SENSITIVITY)
    }

    severity_dictionary = {
        'mixer_fails': (1, "Mixer has failed a quality control test."),
        'mapping_fails': (2, "Mapping has failed a quality control test."),
        'cpv_generator_fails': (5, "CPV Generator has failed a quality control test."),
        'flags_fails': (3, "Flags has failed a quality control test."),
        'publisher_fails': (3, "Publisher has failed a quality control test."),
        'harmonizer_fails': (2, "Harmonizer has failed a quality control test."),
        'influencers_fails': (1, "Influencers has failed a quality control test."),
        'split_color_fails': (1, "Split Color has failed a quality control test.")
    }

    severity = sum(severity_dictionary[key][0] for key, value in test_results.items() if value)
    warnings = [severity_dictionary[key][1] for key, value in test_results.items() if value]

    if severity < THRESHOLD:
        return False, "", severity
    else:
        for warning in warnings:
            print(warning)
        return True, "CPV fail", severity


def test_orb(
        RENDER_QMEO_SENSITIVITY,
        STRIPS_SENSITIVITY,
        RENDER_SEQUENCER_SENSITIVITY,
        PATCH_GROUPS_SENSITIVITY
    ): # Returns True for fail, False for pass
    from ..orb import test_orb

    if test_orb():
        return True, "Orb fail", 3
    return False, "", 0