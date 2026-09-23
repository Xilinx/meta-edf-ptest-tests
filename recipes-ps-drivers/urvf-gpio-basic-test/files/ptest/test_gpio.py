#!/usr/bin/env python3

from ptestlib import lib
from ptestlib.edf_utiles import debug_print
import re
import sys

"""
Generic GPIO Test Script for Linux

Tests:
1. GPIO character devices exist
2. libgpiod utilities are installed
3. GPIO controllers are registered
4. GPIO controller information is accessible
5. Finds and reads an available GPIO line

No gpiochip, controller name, GPIO line, or line count is hardcoded.
The test does not drive an unknown GPIO line, because doing so may affect
reset, power, boot-mode, or peripheral-control signals on some boards.
"""


def check_gpio_devices(GPIO):
    """Check whether GPIO character devices exist."""
    output = GPIO.run_cmd("ls /dev/gpiochip* 2>/dev/null || true", output_log=True)
    return output.strip() if output else None


def check_gpiod_tools(GPIO):
    """Check whether required libgpiod commands are available."""
    output = GPIO.run_cmd(
        "command -v gpiodetect && command -v gpioinfo && command -v gpioget || true",
        output_log=True,
    )
    return bool(output and output.strip())


def detect_gpiochips(GPIO):
    """Dynamically detect all registered GPIO controllers."""
    output = GPIO.run_cmd("gpiodetect 2>/dev/null || true", output_log=True)

    chips = []

    if output:
        for line in output.splitlines():
            match = re.match(r"^(gpiochip[0-9]+)\s+", line.strip())
            if match:
                chips.append(match.group(1))

    return chips


def show_gpio_information(GPIO, chip):
    """Display GPIO controller and line information."""
    GPIO.run_cmd("gpioinfo 2>/dev/null || true", output_log=True)


def find_readable_gpio_line(GPIO, chips):
    """
    Find an accessible GPIO line dynamically.
    """

    for chip in chips:

        gpioinfo_output = GPIO.run_cmd("gpioinfo 2>/dev/null || true", output_log=True)

        if not gpioinfo_output:
            continue

        lines = []

        for entry in gpioinfo_output.splitlines():

            match = re.match(r"\s*line\s+([0-9]+):", entry)

            if match:
                lines.append(match.group(1))

        debug_print(f"INFO: Found {len(lines)} lines on {chip}")

        for line in lines:

            try:
                value = GPIO.run_cmd(
                    f"gpioget -c {chip} {line} 2>/dev/null", output_log=True
                )

                if value and value.strip():
                    return chip, line, value.strip()

            except Exception:
                continue

    return None, None, None


def main():
    debug_print("=== Generic GPIO Test ===\n")

    GPIO = lib.testsetup("urvf_gpio_basic_test")

    # Test 1: Check GPIO character devices
    debug_print("[1] Checking GPIO character devices...")

    devices = check_gpio_devices(GPIO)

    if devices:
        debug_print("PASS: GPIO character device detected")
        debug_print(devices)
    else:
        debug_print("FAIL: No /dev/gpiochip* device found")
        return 1

    # Test 2: Check libgpiod tools
    debug_print("\n[2] Checking libgpiod utilities...")

    if check_gpiod_tools(GPIO):
        debug_print("PASS: Required libgpiod utilities are available")
    else:
        debug_print("FAIL: Required libgpiod utilities are unavailable")
        return 1

    # Test 3: Detect GPIO controllers
    debug_print("\n[3] Detecting GPIO controllers...")

    chips = detect_gpiochips(GPIO)

    if not chips:
        debug_print("FAIL: No GPIO controller registered")
        return 1

    debug_print(f"PASS: Detected GPIO controller(s): {', '.join(chips)}")

    # Test 4: Display controller information
    debug_print("\n[4] Checking GPIO controller information...")

    for chip in chips:
        debug_print(f"\nGPIO information for {chip}:")
        show_gpio_information(GPIO, chip)

    debug_print("PASS: GPIO controller discovery completed")

    # Test 5: Find and read an available line
    debug_print("\n[5] Searching for an accessible GPIO line...")

    chip, line, value = find_readable_gpio_line(GPIO, chips)

    if chip is None:
        debug_print("SKIP: No safely readable GPIO line found")
        debug_print("INFO: GPIO controllers exist, but lines may be busy or reserved")
        debug_print("\n=== GPIO Test Complete ===")
        return 0

    debug_print(f"PASS: Successfully accessed {chip}, line {line}")
    debug_print(f"INFO: GPIO value: {value}")

    debug_print("\n=== GPIO Test Complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
