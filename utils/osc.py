# SPDX-FileCopyrightText: 2024 Alva Theaters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy 
import socket
import struct
import time

from ..maintenance.logging import alva_log

DEBUG = False

ETC_EOS_TCP_PORT = 3032
TCP_TIMEOUT = 5 # Not sure why this has to be 5, but setting it to 1 or below seems to break Eos. Extremely fickle on ETC's end.
SLIP_END = b'\xC0'
SLIP_ESC = b'\xDB'
SLIP_ESC_END = b'\xDC'
SLIP_ESC_ESC = b'\xDD'

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


    def slip_encode(data):
        """Encodes data using SLIP (RFC1055) with a double END character."""
        encoded = bytearray()
        for byte in data:
            if byte == 0xC0:  # END byte
                encoded.extend(SLIP_ESC + SLIP_ESC_END)
            elif byte == 0xDB:  # ESC byte
                encoded.extend(SLIP_ESC + SLIP_ESC_ESC)
            else:
                encoded.append(byte)

        # Add the SLIP END character to mark the end of the packet
        encoded.extend(SLIP_END + SLIP_END)
        return bytes(encoded)


    def send_tcp(osc_addr, addr, string):
        if DEBUG: alva_log("osc", f"\nOSC:\n   -Address: {osc_addr}\n   -String: {string}")

        def pad(data):
            return data + b"\0" * (4 - (len(data) % 4 or 4))

        if not osc_addr.startswith("/"):
            osc_addr = "/" + osc_addr

        osc_addr = osc_addr.encode() + b"\0"
        string = string.encode() + b"\0"
        port = ETC_EOS_TCP_PORT
        tag = ",s".encode()

        message = b"".join(map(pad, (osc_addr, tag, string)))

        # Add a 4-byte size prefix to the message for TCP-based OSC
        message_with_size = struct.pack(">I", len(message)) + message

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(TCP_TIMEOUT)
                if DEBUG: alva_log("osc", f"   Connecting to {addr}:{port}")
                sock.connect((addr, port))
                if DEBUG: alva_log("osc", "   Connection successful. Sending message...")
                sock.sendall(message_with_size)
                if DEBUG: alva_log("osc", "   Message sent successfully.")

                # Explicitly handle server disconnection
                if DEBUG: alva_log("osc", "   Disconnecting from server.")
                response = sock.recv(1024)
                if DEBUG: alva_log("osc", f"   Server response: {response}")

                #time.sleep(3)

        except socket.timeout:
            if DEBUG: alva_log("osc", "   Error: Connection or send operation timed out.")
        except ConnectionRefusedError:
            if DEBUG: alva_log("osc", f"   Error: Connection refused by {addr}:{port}.")
        except Exception as e:
            if DEBUG: alva_log("osc", f"   Error occurred: {e}")
            import traceback
            traceback.print_exc()