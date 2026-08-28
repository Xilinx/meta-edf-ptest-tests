#!/usr/bin/env python3

from ptestlib import lib
import sys


def check_i2c_tools(I2C):
    I2C.run_cmd(
        "which i2cdetect && which i2cdump && which i2cget && which i2cset",
        output_log=True,
    )
    return True


def get_i2c_buses(I2C):

    out = I2C.run_cmd("i2cdetect -l | awk '{print $1}'", output_log=True)

    buses = []

    for line in out.splitlines():

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

    print("=== Generic I2C Test ===\n")

    I2C = lib.testsetup("i2c_basic_test")

    print("[1] Checking i2c-tools...")

    if check_i2c_tools(I2C):
        print("PASS : i2c-tools available")
    else:
        print("FAIL : i2c-tools missing")
        return 1

    print("\n[2] Checking I2C device nodes...")

    if check_i2c_devices(I2C):
        print("PASS : /dev/i2c-* found")
    else:
        print("FAIL : No I2C device nodes found")
        return 1

    print("\n[3] Detecting I2C buses...")

    buses = get_i2c_buses(I2C)

    if not buses:
        print("FAIL : No I2C buses found")
        return 1

    print(f"PASS : Detected buses: {', '.join(buses)}")

    print("\n[4] Scanning I2C buses...")

    for bus in buses:

        print(f"\nScanning bus {bus}")

        scan = scan_bus(I2C, bus)

        if not scan:
            print(f"FAIL : Unable to scan bus {bus}")
            return 1

        print(f"PASS : Bus {bus} scan completed")

    print("\n=== Generic I2C Test Complete ===")

    return 0


if __name__ == "__main__":
    sys.exit(main())
