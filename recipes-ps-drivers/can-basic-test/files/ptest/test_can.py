#!/usr/bin/env python3

from ptestlib import lib
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
    output = CAN.run_cmd("ip link show type can 2>/dev/null", output_log=True)

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
        "dmesg 2>/dev/null | grep -i 'controller area network\\|CAN device driver'",
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
        f"ip link set {iface} up type can bitrate {bitrate} {loopback_opt} 2>&1",
        output_log=True,
    )

    if output and "error" in output.lower() and "bitrate error" not in output.lower():
        return False

    state = CAN.run_cmd(f"ip link show {iface} 2>/dev/null", output_log=True)
    return bool(state and "UP" in state)


def send_test_frame(CAN, iface, frame=TEST_FRAME_ID):
    """Send one CAN frame — success means no error output."""
    output = CAN.run_cmd(f"cansend {iface} {frame} 2>&1", output_log=True)
    return output is not None and "error" not in output.lower()


def do_loopback_test(CAN, iface, frame=TEST_FRAME_ID):
    """
    Bring up interface in loopback mode, run candump in background,
    send a frame, and verify the same frame is received back.
    """
    frame_id = frame.split("#")[0]

    output = CAN.run_cmd(
        f"candump -n 1 {iface} & sleep 0.3 && " f"cansend {iface} {frame} && wait",
        output_log=True,
    )

    if output:
        print(output.strip())

    return bool(output and frame_id in output)


def main():
    print("=== CAN Test ===")

    CAN = lib.testsetup("can_basic_test")

    pass_count = 0
    fail_count = 0

    # Test 1: interface detection
    ifaces = detect_can_interfaces(CAN)

    if ifaces:
        print(f"PASS: CAN interface(s) detected: {', '.join(ifaces)}")
        pass_count += 1
    else:
        print("FAIL: No CAN interface found")
        fail_count += 1
        return 1

    target = ifaces[0]

    # Test 2: driver loaded
    if check_driver_loaded(CAN):
        print("PASS: Driver loaded")
        pass_count += 1
    else:
        print("FAIL: CAN driver not found in dmesg")
        fail_count += 1

    # Test 3: bring interface up
    bring_interface_down(CAN, target)

    if bring_interface_up(CAN, target, CAN_BITRATE):
        print(f"PASS: Interface {target} brought up at {CAN_BITRATE} bps")
        pass_count += 1
    else:
        print(f"FAIL: Could not bring up {target}")
        fail_count += 1
        return 1

    # Test 4: send a frame
    if send_test_frame(CAN, target):
        print(f"PASS: Frame sent on {target}")
        pass_count += 1
    else:
        print(f"FAIL: Frame send failed on {target}")
        fail_count += 1

    # Test 5: loopback TX+RX
    print(f"INFO: Restarting {target} in loopback mode...")
    bring_interface_down(CAN, target)

    if bring_interface_up(CAN, target, CAN_BITRATE, loopback=True):
        if do_loopback_test(CAN, target):
            print(f"PASS: Loopback frame received on {target}")
            pass_count += 1
        else:
            print(f"FAIL: Loopback frame not received on {target}")
            fail_count += 1
    else:
        print(f"FAIL: Could not bring up {target} in loopback mode")
        fail_count += 1

    bring_interface_down(CAN, target)

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
