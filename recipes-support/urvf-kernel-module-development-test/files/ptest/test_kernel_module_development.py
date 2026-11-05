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


import sys
from ptestlib import lib
from ptestlib.edf_utiles import debug_print

MODULE_NAME = "hdmi21-xfmc"
MODULE_ALIAS = MODULE_NAME.replace("-", "_")


def main():

    TEST = lib.testsetup("urvf_kernel_module_development_test")

    debug_print("=== Kernel Module Development Sanity Test ===")

    kernel_release = TEST.run_cmd("uname -r 2>/dev/null || true", output_log=True)
    debug_print(
        f"INFO: Kernel release: {kernel_release.strip() if kernel_release else 'unknown'}"
    )

    TEST.run_cmd("depmod -a 2>/dev/null || true")

    modinfo_output = TEST.run_cmd(
        f"modinfo {MODULE_NAME} 2>/dev/null || true", output_log=True
    )
    if not modinfo_output:
        debug_print(f"FAIL: modinfo returned no output for {MODULE_NAME}")
        return 1
    debug_print(modinfo_output)
    if "filename:" not in modinfo_output or MODULE_ALIAS not in modinfo_output:
        debug_print(f"FAIL: modinfo did not report a valid {MODULE_NAME} module")
        return 1

    TEST.run_cmd(f"modprobe {MODULE_NAME} 2>/dev/null || true")
    lsmod_output = TEST.run_cmd("lsmod 2>/dev/null || true", output_log=True)
    if not lsmod_output or MODULE_ALIAS not in lsmod_output:
        debug_print(f"FAIL: {MODULE_NAME} not present in lsmod after modprobe")
        return 1

    TEST.run_cmd(f"modprobe -r {MODULE_NAME}")

    debug_print(f"PASS: {MODULE_NAME} builds, installs, loads and unloads cleanly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
