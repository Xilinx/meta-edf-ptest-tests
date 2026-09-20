#!/usr/bin/env python3

from ptestlib import lib
from ptestlib.edf_utiles import debug_print
import sys


def check_i2c_tools(I2C):
    try:
        I2C.run_cmd(
            "which i2cdetect && which i2cdump && which i2cget && which i2cset",
            output_log=True,
        )
        return True
    except Exception:
        return False


def get_i2c_buses(I2C):

    out = I2C.run_cmd("i2cdetect -l | awk '{print $1}'", output_log=True)

    buses = []

    for line in (out or "").splitlines():

        if line.startswith("i2c-"):
            buses.append(line.split("-")[1])

    return buses


def check_i2c_devices(I2C):

    out = I2C.run_cmd("ls /dev/i2c-* 2>/dev/null", output_log=True)

    return bool(out and out.strip())


def scan_bus(I2C, bus):

    out = I2C.run_cmd(f"i2cdetect -y {bus}", output_log=True)

    return out


def main():

    debug_print("=== Generic I2C Test ===\n")

    I2C = lib.testsetup("urvf_i2c_basic_test")

    debug_print("[1] Checking i2c-tools...")

    if check_i2c_tools(I2C):
        debug_print("PASS:i2c-tools available")
    else:
        debug_print("FAIL:i2c-tools missing")
        return 1

    debug_print("\n[2] Checking I2C device nodes...")

    if check_i2c_devices(I2C):
        debug_print("PASS:/dev/i2c-* found")
    else:
        debug_print("FAIL:No I2C device nodes found")
        return 1

    debug_print("\n[3] Detecting I2C buses...")

    buses = get_i2c_buses(I2C)

    if not buses:
        debug_print("FAIL:No I2C buses found")
        return 1

    debug_print(f"PASS:Detected buses: {', '.join(buses)}")

    debug_print("\n[4] Scanning I2C buses...")

    for bus in buses:

        debug_print(f"\nINFO: Scanning bus {bus}")

        scan = scan_bus(I2C, bus)

        if not scan:
            debug_print(f"FAIL:Unable to scan bus {bus}")
            return 1

        debug_print(f"PASS:Bus {bus} scan completed")

    debug_print("\n=== Generic I2C Test Complete ===")

    return 0


if __name__ == "__main__":
    sys.exit(main())
