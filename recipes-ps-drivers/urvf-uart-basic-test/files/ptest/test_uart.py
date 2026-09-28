#!/usr/bin/env python3
from ptestlib import lib
from ptestlib.edf_utiles import debug_print

import sys
import re
import time

"""
Generic UART Test

Tests:
1. PL011 UART driver registered
2. Detect all ttyAMA* devices
3. For each device:
   - Read baud rate
   - Verify TX counter increases after sending data
"""

TX_TEST_CMD = "printf '\\x00\\x00\\x00\\x00'"  # null bytes, invisible on console


def check_uart_driver(UART):
    """Verify PL011 UART driver is registered"""

    out = UART.run_cmd(
        "cat /proc/tty/driver/ttyAMA 2>/dev/null || true", output_log=True
    )
    if not out:
        return False, ""
    return "PL011" in out, out


def get_ttyama_devices(UART):
    """Detect all available ttyAMA devices"""

    out = UART.run_cmd("ls /dev/ttyAMA* 2>/dev/null || true", output_log=True)
    if not out or not out.strip():
        return []
    return out.split()


def get_console_uart(UART):
    """Detect active console UART from /proc/consoles"""

    out = UART.run_cmd("cat /proc/consoles 2>/dev/null || true", output_log=True)
    if not out:
        return None
    for line in out.splitlines():
        m = re.match(r"(ttyAMA\d+)", line)
        if m:
            return f"/dev/{m.group(1)}"
    return None


def get_baud_rate(dev, UART):
    """Read current baud rate of a UART device"""

    out = UART.run_cmd(f"stty -F {dev} 2>/dev/null || true", output_log=True)
    if not out:
        return "unknown"
    m = re.search(r"speed (\d+) baud", out)
    return m.group(1) if m else "unknown"


def get_tx_count(UART, port_num):
    """Read current TX count for a ttyAMA port"""

    out = UART.run_cmd(
        "cat /proc/tty/driver/ttyAMA 2>/dev/null || true", output_log=True
    )
    if not out:
        return None
    for line in out.splitlines():
        if line.strip().startswith(f"{port_num}:"):
            m = re.search(r"tx:(\d+)", line)
            if m:
                return int(m.group(1))
    return None


def test_uart_device(dev, UART):
    """Test baud rate and TX counter for a UART device"""

    try:
        m = re.search(r"ttyAMA(\d+)", dev)
        if not m:
            debug_print(f"FAIL : Could not parse port number from {dev}")
            return False
        port_num = m.group(1)

        baud = get_baud_rate(dev, UART)
        debug_print(f"INFO : {dev} baud rate = {baud}")

        tx_before = get_tx_count(UART, port_num)
        if tx_before is None:
            debug_print(f"FAIL : Could not read TX counter for {dev}")
            return False

        debug_print(f"INFO : TX count before = {tx_before}")

        UART.run_cmd(f"{TX_TEST_CMD} > {dev}", timeout=5)
        time.sleep(1)

        tx_after = get_tx_count(UART, port_num)
        if tx_after is None:
            debug_print(f"FAIL : Could not read TX counter after send on {dev}")
            return False

        debug_print(f"INFO : TX count after  = {tx_after}")

        if tx_after <= tx_before:
            debug_print(f"FAIL : TX counter did not increase on {dev}")
            return False

        debug_print(
            f"PASS : TX counter increased by {tx_after - tx_before} bytes on {dev}"
        )
        return True

    except Exception as e:
        debug_print(f"FAIL : Exception while testing {dev}: {e}")
        return False


def main():

    debug_print("=== Generic UART Test ===\n")

    UART = lib.testsetup("urvf_uart_basic_test")

    #
    # Test 1 - Driver check
    #
    debug_print("[1] Checking PL011 UART driver...")

    ok, driver_info = check_uart_driver(UART)
    if ok:
        debug_print("PASS : PL011 UART driver registered")
        debug_print(f"INFO : {driver_info.strip()}")
    else:
        debug_print("FAIL : PL011 UART driver not found")
        return 1

    #
    # Test 2 - Detect ttyAMA devices
    #
    debug_print("\n[2] Detecting ttyAMA devices...")

    devices = get_ttyama_devices(UART)
    if not devices:
        debug_print("FAIL : No ttyAMA devices found")
        return 1

    debug_print(f"PASS : Found {len(devices)} ttyAMA device(s): {' '.join(devices)}")

    console = get_console_uart(UART)
    if console:
        debug_print(f"INFO : Console UART = {console}")
    else:
        debug_print("INFO : No console UART detected")

    #
    # Test 3 - Test each ttyAMA device
    #
    debug_print("\n[3] Testing UART devices...")

    passed = 0
    for dev in devices:
        label = "(console)" if dev == console else "(non-console)"
        debug_print(f"\nINFO : Testing {dev} {label}...")
        if test_uart_device(dev, UART):
            passed += 1
        else:
            debug_print(f"FAIL : {dev} test failed")

    if passed != len(devices):
        debug_print(f"\nFAIL : {passed}/{len(devices)} UART device(s) passed")
        return 1

    debug_print(f"\nPASS : {passed}/{len(devices)} UART device(s) passed")
    debug_print("\n=== UART Test Complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
