# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy 
import socket
import time

from ..maintenance.logging import alva_log


class OSC:
    def correct_argument_because_etc_is_weird(argument):
        '''Required for influencers to work properly'''
        return argument.replace(" at - 00 ", " at + 00 ")
        

    def send_osc(address, argument):
        scene = bpy.context.scene.scene_props
        ip_address = scene.str_osc_ip_address
        port = scene.int_osc_port
        OSC.send_osc_string(address, ip_address, port, argument)
        
        
    def send_osc_lighting(address, argument, user=1):
        argument = OSC.correct_argument_because_etc_is_weird(argument)
        address = address.replace("/eos", f"/eos/user/{user}")
        scene = bpy.context.scene.scene_props
        ip_address = scene.str_osc_ip_address
        port = scene.int_osc_port
        alva_log("osc_lighting", argument)
        OSC.send_osc_string(address, ip_address, port, argument)


    def press_lighting_key(key):
        OSC.send_osc_lighting(f"/eos/key/{key}", "1")
        time.sleep(.3)
        OSC.send_osc_lighting(f"/eos/key/{key}", "0")


    def lighting_key_down(key):
        OSC.send_osc_lighting(f"/eos/key/{key}", "1")


    def lighting_key_up(key):
        OSC.send_osc_lighting(f"/eos/key/{key}", "0")
        
        
    def send_osc_video(address, argument):
        if not bpy.context.scene.scene_props.enable_video:
            return
        scene = bpy.context.scene.scene_props
        ip_address = scene.str_video_ip_address
        port = scene.int_video_port
        alva_log("osc_video", f"Address: {address} | Argument: {argument}")
        OSC.send_osc_string(address, ip_address, port, argument)
        
        
    def send_osc_audio(address, argument):
        if not bpy.context.scene.scene_props.enable_audio:
            return
        scene = bpy.context.scene
        ip_address = scene.str_audio_ip_address
        port = scene.int_audio_port
        alva_log("osc_audio", f"Address: {address} | Argument: {argument}")
        OSC.send_osc_string(address, ip_address, port, argument)


    def send_osc_string(osc_addr, addr, port, string):
        def pad(data):
            return data + b"\0" * (4 - (len(data) % 4 or 4))

        if not osc_addr.startswith("/"):
            osc_addr = "/" + osc_addr

        osc_addr = osc_addr.encode() + b"\0"
        string = string.encode() + b"\0"
        tag = ",s".encode()

        message = b"".join(map(pad, (osc_addr, tag, string)))
        try:
            OSC.sock.sendto(message, (addr, port))

        except Exception:
            import traceback
            traceback.print_exc()

        alva_log("osc", string)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)