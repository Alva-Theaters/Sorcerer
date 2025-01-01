# SPDX-FileCopyrightText: 2025 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy 
import socket
import struct
import time

from ..maintenance.logging import alva_log

DEBUG = False

_eos_sock = None  # Persistent connection reference
ETC_EOS_TCP_PORT = 3032
TCP_TIMEOUT = 5 # Not sure why this has to be 5, but setting it to 1 or below seems to break Eos. Extremely fickle on ETC's end.

buttons_are_tcp = True


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
        #from bpy import spy
        #bpy.spy.make_eos_macros((1, 10), (1, 10), "Go_to_Cue * Enter")


    def press_lighting_key(key):
        OSC.send_osc_lighting(f"/eos/key/{key}", "1", tcp=buttons_are_tcp)
        OSC.send_osc_lighting(f"/eos/key/{key}", "0", tcp=buttons_are_tcp)


    def lighting_key_down(key):
        OSC.send_osc_lighting(f"/eos/key/{key}", "1", tcp=buttons_are_tcp)


    def lighting_key_up(key):
        OSC.send_osc_lighting(f"/eos/key/{key}", "0", tcp=buttons_are_tcp)
        
        
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


    def send_tcp(osc_addr, ip, string):
        """Send a single OSC message to Eos via persistent TCP connection."""
        global _eos_sock

        if _eos_sock is None:
            OSC.connect_eos(ip)
        
        if not osc_addr.startswith("/"):
            osc_addr = "/" + osc_addr

        # Prepare an OSC message with size prefix
        def pad(data):
            return data + b"\x00" * (4 - (len(data) % 4 or 4))

        encoded_addr = osc_addr.encode() + b"\0"
        encoded_string = string.encode() + b"\0"
        tag = b",s"

        message = b"".join(map(pad, (encoded_addr, tag, encoded_string)))
        message_with_size = struct.pack(">I", len(message)) + message

        # Actually send over the persistent socket
        try:
            if DEBUG: print(f"[DEBUG] Sending to Eos: {osc_addr} | '{string}'")
            _eos_sock.sendall(message_with_size)

        except socket.timeout:
            if DEBUG:
                print("[DEBUG] Error: send operation timed out.")
            OSC.disconnect_eos()
        except (ConnectionResetError, ConnectionRefusedError):
            if DEBUG:
                print("[DEBUG] Error: Eos connection reset/refused.")
            OSC.disconnect_eos()
        except Exception as e:
            if DEBUG:
                print(f"[DEBUG] General error during send: {e}")
            OSC.disconnect_eos()

        time.sleep(.1)


    def connect_eos(ip, port=ETC_EOS_TCP_PORT, timeout=TCP_TIMEOUT):
        global _eos_sock
        if _eos_sock is not None:
            return
        
        if DEBUG:
            print(f"[DEBUG] Connecting to Eos at {ip}:{port} ...")
        try:
            _eos_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            _eos_sock.settimeout(timeout)
            _eos_sock.connect((ip, port))
            if DEBUG:
                print("[DEBUG] Eos connection successful!")
        except Exception as e:
            if DEBUG:
                print(f"[DEBUG] Failed to connect: {e}")
            _eos_sock = None

    def disconnect_eos():
        global _eos_sock
        if _eos_sock:
            try:
                _eos_sock.close()
            except:
                pass
        _eos_sock = None