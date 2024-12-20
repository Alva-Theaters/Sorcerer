# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy 
import socket
import struct
import time

from ..maintenance.logging import alva_log

DEBUG = False
TCP_TIMEOUT = .1


class OSC:
    def correct_argument_because_etc_is_weird(argument):
        '''Required for influencers to work properly'''
        return argument.replace(" at - 00", " at + 00")
        

    def send_osc_lighting(address, argument, user=1, tcp=False):
        argument = OSC.correct_argument_because_etc_is_weird(argument)
        address = address.replace("/eos", f"/eos/user/{user}")
        scene = bpy.context.scene.scene_props
        ip_address = scene.str_osc_ip_address
        port = scene.int_osc_port
        if DEBUG: alva_log("osc_lighting", argument)
        OSC.send_osc_string(address, ip_address, port, argument, tcp=tcp)


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
        if DEBUG: alva_log("osc_video", f"Address: {address} | Argument: {argument}")
        OSC.send_osc_string(address, ip_address, port, argument)
        
        
    def send_osc_audio(address, argument):
        if not bpy.context.scene.scene_props.enable_audio:
            return
        scene = bpy.context.scene
        ip_address = scene.str_audio_ip_address
        port = scene.int_audio_port
        if DEBUG: alva_log("osc_audio", f"Address: {address} | Argument: {argument}")
        OSC.send_osc_string(address, ip_address, port, argument)


    def send_osc_string(osc_addr, addr, port, string, tcp=False):
        if tcp:
            OSC.send_tcp(osc_addr, addr, string)
        else:
            OSC.send_udp(osc_addr, addr, port, string)


    def send_udp(osc_addr, addr, port, string):
        if DEBUG: alva_log("osc", f"\nOSC:\n   -Address: {osc_addr}\n   -String: {string}")
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

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


    def send_tcp(osc_addr, addr, string):
        if DEBUG: alva_log("osc", f"\nOSC:\n   -Address: {osc_addr}\n   -String: {string}")

        def pad(data):
            # Pad to a multiple of 4 bytes
            return data + b"\0" * (4 - (len(data) % 4 or 4))

        if not osc_addr.startswith("/"):
            osc_addr = "/" + osc_addr

        osc_addr = osc_addr.encode() + b"\0"
        string = string.encode() + b"\0"
        tag = ",s".encode()  # Type tag for a single string argument

        message = b"".join(map(pad, (osc_addr, tag, string)))

        message_with_size = struct.pack(">I", len(message)) + message

        port = 3032 # Per ETC, for lighting only

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(TCP_TIMEOUT)  # Set a timeout of 5 seconds
                if DEBUG: alva_log("osc", f"   Connecting to {addr}:{port}")
                sock.connect((addr, port))  # Establish connection
                if DEBUG: alva_log("osc", "   Connection successful. Sending message...")
                sock.sendall(message_with_size)  # Send the message with the size prefix
                if DEBUG: alva_log("osc", "   Message sent successfully.")

        except socket.timeout:
            if DEBUG: alva_log("osc", "   Error: Connection or send operation timed out.")
        except ConnectionRefusedError:
            if DEBUG: alva_log("osc", f"   Error: Connection refused by {addr}:{port}.")
        except Exception as e:
            if DEBUG: alva_log("osc", f"   Error occurred: {e}")
            import traceback
            traceback.print_exc()