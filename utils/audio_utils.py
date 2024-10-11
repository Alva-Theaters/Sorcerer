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

from .osc import OSC


def render_volume(speaker, empty, sensitivity, object_size, int_mixer_channel):
    '''Basically a crude form of the Dolby Atmos Renderer'''
    distance = (speaker.location - empty.location).length
    adjusted_distance = max(distance - object_size, 0)
    final_distance = adjusted_distance + sensitivity
    final_distance = max(final_distance, 1e-6)
    base_volume = 1.0
    volume = base_volume / final_distance
    volume = max(0, min(volume, 1))
    
    if bpy.context.screen:
        for area in bpy.context.screen.areas:
            if area.type == 'SEQUENCE_EDITOR':
                area.tag_redraw()
            
    if bpy.context.scene.str_audio_ip_address != "":
        address = bpy.context.scene.audio_osc_address.format("#", str(int_mixer_channel))
        address = address.format("$", round(volume))
        argument = bpy.context.scene.audio_osc_argument.format("#", str(int_mixer_channel))
        argument = argument.format("$", round(volume))
        OSC.send_osc_lighting(address, argument)
    return volume