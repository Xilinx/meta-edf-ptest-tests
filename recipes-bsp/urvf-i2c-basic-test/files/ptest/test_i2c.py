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
import sys


def check_i2c_tools(I2C):
    out = I2C.run_cmd(
        "which i2cdetect && which i2cdump && which i2cget && which i2cset 2>/dev/null || true",
        output_log=True,
    )
    return bool(out and out.strip())


def get_i2c_buses(I2C):

    out = I2C.run_cmd(
        "i2cdetect -l 2>/dev/null | awk '{print $1}' || true", output_log=True
    )

    buses = []

    for line in (out or "").splitlines():

        if line.startswith("i2c-"):
            buses.append(line.split("-")[1])

    return buses


def check_i2c_devices(I2C):

    out = I2C.run_cmd("ls /dev/i2c-* 2>/dev/null || true", output_log=True)

    return bool(out and out.strip())


def scan_bus(I2C, bus):

    out = I2C.run_cmd(f"i2cdetect -y {bus} 2>/dev/null || true", output_log=True)

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
