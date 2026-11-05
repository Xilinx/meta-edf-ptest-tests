#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


from ptestlib import lib
from ptestlib.edf_utiles import debug_print
import re
import sys

"""
Generic CAN Test Script for Linux

Tests:
1. CAN network interface(s) exist
2. CAN driver is loaded (dmesg confirms CAN core registration)
3. CAN interface can be brought up with a bitrate
4. A CAN frame can be transmitted without error
5. Loopback TX+RX — frame sent is received back on the same interface

Interface is brought back down after the test.
"""

CAN_BITRATE = 1000000
TEST_FRAME_ID = "123#DEADBEEF"


def detect_can_interfaces(CAN):
    """Discover all CAN network interfaces via ip link."""
    output = CAN.run_cmd("ip link show type can 2>/dev/null || true", output_log=True)

    ifaces = []

    if output:
        for line in output.splitlines():
            match = re.match(r"^\d+:\s+(can[0-9]+):", line.strip())
            if match:
                ifaces.append(match.group(1))

    return ifaces


def check_driver_loaded(CAN):
    """Confirm CAN core driver is registered via dmesg."""
    output = CAN.run_cmd(
        "dmesg 2>/dev/null | grep -i 'controller area network\\|CAN device driver' || true",
        output_log=True,
    )
    return bool(output and output.strip())


def bring_interface_down(CAN, iface):
    """Bring the CAN interface down."""
    CAN.run_cmd(f"ip link set {iface} down 2>/dev/null || true", output_log=True)


def bring_interface_up(CAN, iface, bitrate=CAN_BITRATE, loopback=False):
    """Bring the CAN interface up with optional loopback mode."""
    loopback_opt = "loopback on" if loopback else ""

    output = CAN.run_cmd(
        f"ip link set {iface} up type can bitrate {bitrate} {loopback_opt} 2>&1 || true",
        output_log=True,
    )

    if output and "error" in output.lower() and "bitrate error" not in output.lower():
        return False

    state = CAN.run_cmd(f"ip link show {iface} 2>/dev/null || true", output_log=True)
    return bool(state and "UP" in state)


def send_test_frame(CAN, iface, frame=TEST_FRAME_ID):
    """Send one CAN frame — success means no error output."""
    output = CAN.run_cmd(f"cansend {iface} {frame} 2>&1 || true", output_log=True)
    return output is not None and "error" not in output.lower()


def do_loopback_test(CAN, iface, frame=TEST_FRAME_ID):
    """
    Bring up interface in loopback mode, run candump in background,
    send a frame, and verify the same frame is received back.
    """
    frame_id = frame.split("#")[0]

    output = CAN.run_cmd(
        f"candump -n 1 -T 3000 {iface} & sleep 1 && cansend {iface} {frame} && wait || true",
        output_log=True,
    )

    if output:
        debug_print(output.strip())

    return bool(output and frame_id in output)


def main():
    debug_print("=== CAN Test ===")

    CAN = lib.testsetup("urvf_can_basic_test")

    # Test 1: interface detection
    ifaces = detect_can_interfaces(CAN)

    if not ifaces:
        debug_print("FAIL: No CAN interface found")
        return 1

    debug_print(f"PASS: CAN interface(s) detected: {', '.join(ifaces)}")
    target = ifaces[0]

    # Test 2: driver loaded (SKIP if not found — dmesg may be cleared by earlier tests)
    if check_driver_loaded(CAN):
        debug_print("PASS: Driver loaded")
    else:
        debug_print("SKIP: CAN driver not found in dmesg")

    # Test 3: bring interface up
    bring_interface_down(CAN, target)

    if not bring_interface_up(CAN, target, CAN_BITRATE):
        debug_print(f"FAIL: Could not bring up {target}")
        bring_interface_down(CAN, target)
        return 1

    debug_print(f"PASS: Interface {target} brought up at {CAN_BITRATE} bps")

    # Test 4: send a frame
    if not send_test_frame(CAN, target):
        debug_print(f"FAIL: Frame send failed on {target}")
        bring_interface_down(CAN, target)
        return 1

    debug_print(f"PASS: Frame sent on {target}")

    # Test 5: loopback TX+RX
    debug_print(f"INFO: Restarting {target} in loopback mode...")
    bring_interface_down(CAN, target)

    if not bring_interface_up(CAN, target, CAN_BITRATE, loopback=True):
        debug_print(f"FAIL: Could not bring up {target} in loopback mode")
        bring_interface_down(CAN, target)
        return 1

    if not do_loopback_test(CAN, target):
        debug_print(f"FAIL: Loopback frame not received on {target}")
        bring_interface_down(CAN, target)
        return 1

    debug_print(f"PASS: Loopback frame received on {target}")
    bring_interface_down(CAN, target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
