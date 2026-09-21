#!/usr/bin/env python3
from ptestlib import lib
from ptestlib.edf_utiles import debug_print

import sys
import re

"""
Generic UART Test

Tests:
1. UART drivers present
2. UART device nodes exist
3. Console UART detection
4. UART accessibility
"""


def get_uart_devices(UART):
    """Detect available UART devices"""

    out = UART.run_cmd("ls /dev/tty* 2>/dev/null", output_log=True)

    if not out:
        return []

    return out.split()


def get_console_uart(UART):
    """Detect active console UART"""

    out = UART.run_cmd("cat /proc/consoles", output_log=True)

    if not out:
        return None

    for line in out.splitlines():
        m = re.match(r"(tty[A-Za-z0-9]+)", line)
        if m:
            return f"/dev/{m.group(1)}"

    return None


def check_uart_drivers(UART):
    """Verify UART drivers are registered"""

    out = UART.run_cmd("cat /proc/tty/drivers", output_log=True)

    return bool(out and "serial" in out)


def check_uart_access(dev, UART):
    """Verify UART can be opened"""

    try:
        UART.run_cmd(f"stty -F {dev} -a", timeout=5)
        return True
    except:
        return False


def main():

    debug_print("=== Generic UART Test ===\n")

    UART = lib.testsetup("urvf_uart_basic_test")

    #
    # Test 1
    #
    debug_print("[1] Checking UART drivers...")

    if check_uart_drivers(UART):
        debug_print("PASS : UART driver registered")
    else:
        debug_print("FAIL : No UART driver found")
        return 1

    #
    # Test 2
    #
    debug_print("\n[2] Detecting UART devices...")

    uarts = get_uart_devices(UART)

    if not uarts:
        debug_print("FAIL : No UART devices found")
        return 1

    debug_print("PASS : UART devices detected")

    for dev in uarts:
        debug_print(f"INFO : {dev}")

    #
    # Test 3
    #
    debug_print("\n[3] Detecting console UART...")

    console_uart = get_console_uart(UART)

    if console_uart:
        debug_print(f"INFO : Console UART = {console_uart}")
    else:
        debug_print("INFO : No console UART detected")

    #
    # Test 4
    #
    debug_print("\n[4] Checking UART accessibility...")

    tested = False

    for dev in uarts:

        if dev == console_uart:
            debug_print(f"SKIP : {dev} (console UART)")
            continue

        if check_uart_access(dev, UART):
            debug_print(f"PASS : {dev} accessible")
            tested = True
            break

        debug_print(f"INFO : {dev} not accessible")

    #
    # Fallback for boards having only console UART
    #
    if not tested and console_uart:

        debug_print("\nINFO : No secondary UART found")
        debug_print(f"INFO : Validating console UART {console_uart}")

        if check_uart_access(console_uart, UART):
            debug_print(f"PASS : {console_uart} accessible")
            tested = True

    if not tested:
        debug_print("FAIL : No usable UART found")
        return 1

    debug_print("\n=== UART Test Complete ===")

    return 0


if __name__ == "__main__":
    sys.exit(main())
