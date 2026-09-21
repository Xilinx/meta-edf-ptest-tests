#!/usr/bin/env python3

from ptestlib import lib
from ptestlib.edf_utiles import debug_print
import re
import sys

"""
Generic Watchdog Test Script for Linux

Tests:
1. Watchdog character device nodes exist (/dev/watchdog*)
2. Watchdog driver is loaded (dmesg confirms watchdog activity)
3. Watchdog device info is readable via wdctl
4. Watchdog keepalive ping loop works without resetting the board

No device path, driver name, or timeout value is hardcoded.
The test pings the watchdog repeatedly and does NOT let the timer expire.
"""

PING_COUNT = 6
PING_SLEEP = 4  # seconds between pings — must be < watchdog timeout


def check_watchdog_devices(WD):
    """Check whether /dev/watchdog* character device nodes exist."""
    output = WD.run_cmd("ls /dev/watchdog* 2>/dev/null || true", output_log=True)
    return output.strip() if output else None


def check_driver_loaded(WD):
    """Confirm a watchdog driver is active via dmesg."""
    output = WD.run_cmd("dmesg 2>/dev/null | grep -i 'watchdog'", output_log=True)
    return bool(output and output.strip())


def detect_watchdog_devices(WD):
    """Return sorted list of numbered /dev/watchdogN device paths."""
    output = WD.run_cmd("ls /dev/watchdog* 2>/dev/null || true", output_log=True)

    devices = []

    if output:
        for entry in output.split():
            entry = entry.strip()
            if re.match(r"^/dev/watchdog[0-9]+$", entry):
                devices.append(entry)

    return sorted(devices)


def read_wdctl_info(WD, device):
    """Return wdctl output for the given device, or None on failure."""
    output = WD.run_cmd(f"wdctl {device} 2>/dev/null", output_log=True)
    return output.strip() if output else None


def do_keepalive_pings(WD, device, count=PING_COUNT, sleep_sec=PING_SLEEP):
    """
    Open the watchdog via a shell file descriptor, send keepalive pings,
    then close. Uses exec 3>device / echo -n 1 >&3 / exec 3>&- to keep
    the fd open across pings — matching the manual test exactly.
    """
    ping_cmds = " && ".join(
        f'echo -n "1" >&3 && echo "Ping {i}" && sleep {sleep_sec}'
        for i in range(1, count + 1)
    )

    cmd = (
        f"exec 3>{device} && "
        f'echo "WDT opened, starting keepalive..." && '
        f"{ping_cmds} && "
        f"exec 3>&- && "
        f'echo "done"'
    )

    output = WD.run_cmd(cmd, output_log=True)

    if output:
        debug_print(output.strip())

    return bool(output and "done" in output)


def main():
    debug_print("=== Watchdog Test ===")

    WD = lib.testsetup("urvf_watchdog_basic_test")

    pass_count = 0
    fail_count = 0

    # Test 1: device nodes present
    devices_str = check_watchdog_devices(WD)

    if devices_str:
        debug_print(f"PASS: Device nodes: {devices_str}")
        pass_count += 1
    else:
        debug_print("FAIL: No /dev/watchdog* device found")
        fail_count += 1
        return 1

    # Test 2: driver loaded
    if check_driver_loaded(WD):
        debug_print("PASS: Driver loaded")
        pass_count += 1
    else:
        debug_print("FAIL: Driver not found in dmesg")
        fail_count += 1

    # Test 3: wdctl readable — use last numbered device
    devices = detect_watchdog_devices(WD)
    target = devices[-1] if devices else None

    if target:
        info = read_wdctl_info(WD, target)
        if info:
            debug_print("PASS: wdctl readable")
            debug_print(info)
            pass_count += 1
        else:
            debug_print(f"FAIL: wdctl returned no output for {target}")
            fail_count += 1
    else:
        debug_print("FAIL: No numbered watchdog device found for wdctl")
        fail_count += 1

    # Test 4: keepalive ping loop
    if target:
        ok = do_keepalive_pings(WD, target)
        if ok:
            debug_print("PASS: Keepalive done, board alive")
            pass_count += 1
        else:
            debug_print(f"FAIL: Keepalive ping failed on {target}")
            fail_count += 1
    else:
        debug_print("FAIL: No device available for keepalive test")
        fail_count += 1

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
