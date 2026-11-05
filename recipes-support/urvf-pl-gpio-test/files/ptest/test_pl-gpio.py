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
import mmap
import os
import re
import struct
import sys

"""
PL GPIO Test Script for Linux

Tests:
1. Locate {machine}-pl-bram-gpio-fw in dfx-mgr-client -listPackage
2. Load the bundle via dfx-mgr-client -load <id>
3. New GPIO chip(s) appear after DFX load
4. AXI BRAM controller address(es) found in device tree
5. Memory read/write validation at each BRAM address
6. GPIO toggle on each discovered PL GPIO chip

Usage: ptest-runner urvf-pl-gpio-test <machine>
"""

PAGE_SIZE = mmap.PAGESIZE
PAGE_MASK = ~(PAGE_SIZE - 1)

DT_AXI_PATH = "/proc/device-tree/axi"
GPIODETECT_RE = re.compile(r"(gpiochip\d+)\s+\[(.*?)\]\s+\((\d+)\s+lines\)")
TEST_VALUES = [0xDEADBEEF, 0x12345678, 0x87654321]
FW_SUFFIX = "-pl-bram-gpio-fw"


def find_package_id(GPIO, machine):
    # parts[-1] is the full Accelerator name (last col, never truncated like Base)
    # exact match prevents vek385-revb-pl-bram-gpio-fw matching machine=vek385
    target = f"{machine}{FW_SUFFIX}"
    out = GPIO.run_cmd(
        "dfx-mgr-client -listPackage 2>/dev/null || true",
        timeout=15,
        output_log=True,
    )
    if not out:
        return None

    for line in out.splitlines():
        parts = line.split()
        if len(parts) < 5 or not parts[0].isdigit():
            continue
        if parts[-1] == target:
            debug_print(f"Found package: ID={parts[0]}  Accelerator={parts[-1]}")
            return int(parts[0])

    return None


def dfx_load(GPIO, pkg_id):
    out = GPIO.run_cmd(
        f"dfx-mgr-client -load {pkg_id} 2>&1 || true",
        timeout=60,
        output_log=True,
    )
    debug_print(out.strip() if out else "")
    return bool(out and "error" not in out.lower())


def dfx_unload(GPIO, pkg_id):
    out = GPIO.run_cmd(
        f"dfx-mgr-client -unload {pkg_id} 2>&1 || true",
        timeout=30,
        output_log=True,
    )
    debug_print(out.strip() if out else "")


def run_gpiodetect(GPIO):
    result = {}
    out = GPIO.run_cmd("gpiodetect 2>/dev/null || true", output_log=True)
    if not out:
        return result
    for line in out.splitlines():
        m = GPIODETECT_RE.match(line.strip())
        if m:
            chip, label, lines = m.group(1), m.group(2), int(m.group(3))
            result[chip] = (label, lines)
    return result


def diff_gpio(before, after):
    added = set(after) - set(before)
    if added:
        for c in sorted(added):
            label, lines = after[c]
            debug_print(f"  + {c} [{label}] ({lines} lines)")
    return list(added)


def get_axi_bram_ctrl_addrs(GPIO):
    results = {}
    out = GPIO.run_cmd(f"ls {DT_AXI_PATH} 2>/dev/null || true", output_log=True)
    if not out:
        return results
    for entry in out.split():
        m = re.match(r"(axi[-_]bram[-_]ctrl[-_]\d+)@([0-9a-fA-F]+)", entry)
        if m:
            results[m.group(1)] = int(m.group(2), 16)
    return results


def memory_test(phys_addr):
    page_offset = phys_addr & (PAGE_SIZE - 1)
    page_base = phys_addr & PAGE_MASK

    with os.fdopen(os.open("/dev/mem", os.O_RDWR | os.O_SYNC), "r+b") as f:
        mem = mmap.mmap(
            f.fileno(),
            PAGE_SIZE,
            mmap.MAP_SHARED,
            mmap.PROT_READ | mmap.PROT_WRITE,
            offset=page_base,
        )
        original = struct.unpack("<I", mem[page_offset : page_offset + 4])[0]
        debug_print(f"  Original value: 0x{original:08X}")

        passed = True
        for val in TEST_VALUES:
            mem[page_offset : page_offset + 4] = struct.pack("<I", val)
            readback = struct.unpack("<I", mem[page_offset : page_offset + 4])[0]
            if readback == val:
                debug_print(f"  wrote 0x{val:08X}, read back 0x{readback:08X}")
            else:
                debug_print(
                    f"  FAIL: wrote 0x{val:08X}, read back 0x{readback:08X} (mismatch)"
                )
                passed = False

        mem[page_offset : page_offset + 4] = struct.pack("<I", original)
        debug_print("  Restored original value.")
        mem.close()

    return passed


def gpio_toggle_test(GPIO, gpio_node, lines):
    for i in range(lines):
        GPIO.run_cmd(
            f"gpioset -t1s,1s -c {gpio_node} {i}=1 & sleep 5 && kill %1 2>/dev/null; true",
            timeout=15,
            output_log=True,
        )
        debug_print(f"  GPIO {i} toggle complete")
    return True


def main():
    machine = os.environ.get("MACHINE")
    if not machine:
        print(
            "Please set the MACHINE environment variable.  e.g. MACHINE=vek385 ptest-runner urvf-pl-gpio-test"
        )
        return 1

    debug_print(f"=== PL GPIO Test  machine={machine} ===")

    GPIO = lib.testsetup("urvf_pl-gpio_basic_test")

    # Test 1: find the firmware bundle in dfx-mgr-client -listPackage
    debug_print(
        f"INFO: Searching for '{machine}{FW_SUFFIX}' in dfx-mgr-client -listPackage..."
    )
    pkg_id = find_package_id(GPIO, machine)
    if pkg_id is None:
        debug_print(
            f"FAIL: Package '{machine}{FW_SUFFIX}' not found in dfx-mgr-client -listPackage"
        )
        return 1
    debug_print(f"PASS: Package found  ID={pkg_id}")

    # Test 2: load the bundle
    debug_print("INFO: Capturing gpiodetect state before DFX load...")
    before = run_gpiodetect(GPIO)

    debug_print(f"INFO: Loading package ID={pkg_id}...")
    if not dfx_load(GPIO, pkg_id):
        debug_print("FAIL: dfx-mgr-client -load failed")
        return 1
    debug_print(f"PASS: Bundle loaded  ID={pkg_id}")

    # Test 3: new GPIO chips must appear
    debug_print("INFO: Capturing gpiodetect state after DFX load...")
    after = run_gpiodetect(GPIO)
    new_chips = diff_gpio(before, after)
    if not new_chips:
        debug_print("FAIL: No new PL GPIO chips appeared after DFX load")
        dfx_unload(GPIO, pkg_id)
        return 1
    debug_print(f"PASS: New PL GPIO chip(s): {', '.join(sorted(new_chips))}")

    # Test 4: AXI BRAM controllers must appear in device tree
    brams = get_axi_bram_ctrl_addrs(GPIO)
    if not brams:
        debug_print("FAIL: No AXI BRAM controllers found in device tree")
        dfx_unload(GPIO, pkg_id)
        return 1
    debug_print(f"PASS: Found BRAM controller(s): {', '.join(brams.keys())}")

    # Test 5: memory read/write at each BRAM address
    mem_ok = True
    for name, addr in brams.items():
        debug_print(f"INFO: Memory test — {name} @ 0x{addr:08X}")
        if not memory_test(addr):
            debug_print(f"FAIL: Memory test failed for {name}")
            mem_ok = False
    if not mem_ok:
        dfx_unload(GPIO, pkg_id)
        return 1
    debug_print("PASS: All memory tests passed")

    # Test 6: GPIO toggle on each new chip
    gpio_ok = True
    for gpio_node in sorted(new_chips):
        _, lines = after[gpio_node]
        debug_print(f"INFO: GPIO toggle test — {gpio_node}")
        if not gpio_toggle_test(GPIO, gpio_node, lines):
            debug_print(f"FAIL: GPIO toggle test failed for {gpio_node}")
            gpio_ok = False
    if not gpio_ok:
        dfx_unload(GPIO, pkg_id)
        return 1
    debug_print("PASS: All GPIO toggle tests passed")

    # Cleanup
    debug_print(f"INFO: Unloading package ID={pkg_id}...")
    dfx_unload(GPIO, pkg_id)
    debug_print("PASS: DFX bundle unloaded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
