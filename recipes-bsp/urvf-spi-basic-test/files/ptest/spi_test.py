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

from ptestlib.edf_utiles import (
    check_string_in_dmesg,
    clean_dmesg,
    debug_print,
    get_spi_node,
    kernel_verbosity,
    setup_modeprobe,
    teardown_modeprobe,
)

from ptestlib import lib
import sys

"""
SPI Basic Test
Tests MTD speedtest and readtest for each detected SPI MTD device.
"""


def main():
    debug_print("=== SPI Basic Test ===\n")

    run = lib.testsetup("urvf_spi_test")

    try:
        mtd_node = get_spi_node()
        kernel_verbosity(1)
    except Exception as e:
        debug_print(f"FAIL: Test setup failed: {e}")
        return 1

    if not mtd_node:
        debug_print("FAIL: No MTD nodes found with 'mtd0' or 'user' in the name.")
        return 1

    debug_print(f"INFO: Found MTD nodes: {mtd_node}")
    run.run_cmd("dmesg -c 2>/dev/null || true", output_log=True)

    any_failed = False

    for dev in mtd_node:
        debug_print(f"\nINFO: Testing MTD device: mtd{dev}")

        # Speed test
        debug_print(f"INFO: Setting up MTD speedtest for device: mtd{dev}")
        try:
            setup_modeprobe(dev, "mtd_speedtest", runcmd=run.run_cmd, count=1)
            teardown_modeprobe(run.run_cmd, "mtd_speedtest")
            check_string_in_dmesg(
                run.run_cmd,
                success_list=["mtd_speedtest: finished"],
                failure_list=["failed", "error", "ERROR:"],
            )
            debug_print(f"PASS: mtd{dev} speedtest completed")
        except Exception as e:
            debug_print(f"FAIL: mtd_speedtest on mtd{dev}: {e}")
            any_failed = True
            continue

        # Read test
        debug_print(f"INFO: Setting up MTD readtest for device: mtd{dev}")
        try:
            setup_modeprobe(dev, "mtd_readtest", runcmd=run.run_cmd)
            try:
                check_string_in_dmesg(
                    run.run_cmd,
                    success_list=["mtd_readtest: finished"],
                    failure_list=["failed", "error", "ERROR:"],
                )
                debug_print(f"PASS: mtd{dev} readtest completed")
            finally:
                teardown_modeprobe(run.run_cmd, "mtd_readtest")
        except Exception as e:
            debug_print(f"FAIL: mtd_readtest on mtd{dev}: {e}")
            any_failed = True
            continue

    return 1 if any_failed else 0


if __name__ == "__main__":
    sys.exit(main())
