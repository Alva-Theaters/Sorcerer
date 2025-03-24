# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy import spy

from ..cpv.normal import NormalCPV
from ..cpv.mix import MixCPV
from ..cpv.influence import InfluenceCPV


class CPV_CO_group(spy.types.LightingController):
    as_idname = 'group_controller'
    as_description = 'Control single fixtures or groups equally'

    def execute(updater):
        NormalCPV(updater).execute()


class CPV_CO_mix(spy.types.LightingController):
    as_idname = 'mix_controller'
    as_description = 'Creating simple mix effects'

    def execute(updater):
        MixCPV(updater).execute()


class CPV_CO_influence(spy.types.LightingController):
    as_idname = 'influence_controller'
    as_description = 'Use 3D objects to control parameters'

    def execute(updater):
        InfluenceCPV(updater).execute()


controllers = [
    CPV_CO_group,
    CPV_CO_mix,
    CPV_CO_influence
]


def register():
    for cls in controllers:
        spy.utils.as_register_class(cls)


def unregister():
    for cls in reversed(controllers):
        spy.utils.as_unregister_class(cls)