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

"""
eMMC/SD Functional Test
"""

SKIP_MOUNTS = ["/efi", "/boot", "/"]


def get_all_mmc_devices(MMC):
    """Find all mmcblk devices on the board"""
    out = MMC.run_cmd("lsblk -dn -o NAME | grep '^mmcblk' || true", output_log=True)
    if not out:
        return []
    return [d.strip() for d in out.splitlines() if d.strip()]


def get_device_type(device, MMC):
    """Read SD or MMC from sysfs"""
    out = MMC.run_cmd(
        f"cat /sys/block/{device}/device/type 2>/dev/null || true", output_log=True
    )
    return out.strip() if out else "UNKNOWN"


def raw_block_read(device, MMC):
    """Read 512 bytes directly from block device — hardware level check"""
    out = MMC.run_cmd(
        f"dd if=/dev/{device} of=/dev/null bs=512 count=1 2>&1 || true", output_log=True
    )
    return bool(out and "records out" in out)


def check_dmesg_errors(device, MMC):
    """Check kernel log for hardware faults on this device"""
    # grep exits 1 when no matches found (no errors = good); suppress to avoid exception
    out = MMC.run_cmd(
        f"dmesg | grep -i {device} | grep -i 'error\\|fail\\|timeout\\|reset' || true",
        output_log=True,
    )
    return out.strip() if out else None


def get_writable_mount(device, MMC):
    """Find best writable mount point — prefers /storage, skips rootfs and efi"""
    out = MMC.run_cmd(
        f"lsblk -nrpo MOUNTPOINT /dev/{device} 2>/dev/null || true", output_log=True
    )
    if not out:
        return None

    mounts = [
        m.strip()
        for m in out.splitlines()
        if m.strip() and m.strip() not in SKIP_MOUNTS
    ]

    # prefer /storage type partitions
    mounts = sorted(mounts, key=lambda m: m == "/storage", reverse=True)

    for mount in mounts:
        writable = MMC.run_cmd(f"test -w {mount} && echo OK || true", output_log=True)
        if writable and "OK" in writable:
            return mount

    return None


def rw_test(mount_point, MMC):
    """Write, read back, verify content — always cleans up"""
    test_file = f"{mount_point}/emmc_test.txt"
    try:
        MMC.run_cmd(f"echo EDF_EMMC_TEST > {test_file} && sync || true")
        out = MMC.run_cmd(f"cat {test_file} 2>/dev/null || true", output_log=True)
        return bool(out and "EDF_EMMC_TEST" in out)
    finally:
        MMC.run_cmd(f"rm -f {test_file}")


def perf_test(mount_point, MMC):
    """Write 4MB and report speed — catches slow/failing cards that still pass R/W"""
    perf_file = f"{mount_point}/perf_test"
    try:
        out = MMC.run_cmd(
            f"dd if=/dev/zero of={perf_file} bs=1M count=4 oflag=sync 2>&1 || true",
            output_log=True,
        )
        for line in (out or "").splitlines():
            if "MB/s" in line or "GB/s" in line:
                return line.strip()
        return None
    finally:
        MMC.run_cmd(f"rm -f {perf_file}")


def test_device(device, index, total, MMC):
    """Run all checks on a single device, return True if passed"""

    dev_type = get_device_type(device, MMC)

    debug_print(f"\n{'─' * 50}")
    debug_print(f"Device {index}/{total} : {device} ({dev_type})")
    debug_print(f"{'─' * 50}")

    # 1. Raw block read
    debug_print("\n  [1/4] Raw Block Read...")
    if raw_block_read(device, MMC):
        debug_print(f"        PASS: /dev/{device} readable (512 bytes)")
    else:
        debug_print(f"        FAIL: /dev/{device} not readable")
        return False

    # 2. dmesg error check
    debug_print("\n  [2/4] Hardware Error Check (dmesg)...")
    errors = check_dmesg_errors(device, MMC)
    if errors:
        debug_print(f"        WARN: Kernel errors found for {device}")
        for line in errors.splitlines():
            debug_print(f"        INFO: {line.strip()}")
    else:
        debug_print(f"        PASS: No errors in dmesg for {device}")

    # 3. R/W test
    debug_print("\n  [3/4] Read/Write Test...")
    mount_point = get_writable_mount(device, MMC)
    if not mount_point:
        debug_print("        SKIP : No writable mounted partition found")
        return True

    debug_print(f"        INFO: Mount point: {mount_point}")
    if rw_test(mount_point, MMC):
        debug_print("        PASS: Write -> Read -> Verify successful")
        debug_print("        PASS: Cleanup done")
    else:
        debug_print("        FAIL: Read back mismatch")
        debug_print("        PASS: Cleanup done")
        return False

    # 4. Performance test
    debug_print("\n  [4/4] Performance Test...")
    speed = perf_test(mount_point, MMC)
    if speed:
        debug_print(f"        INFO: Write speed: {speed}")
        debug_print("        PASS: Performance data collected")
    else:
        debug_print("        WARN: Could not parse write speed")

    return True


def main():

    debug_print("=== eMMC/SD Functional Test ===\n")

    MMC = lib.testsetup("urvf_emmc_sd_test")

    debug_print("Scanning for MMC/SD devices...")
    devices = get_all_mmc_devices(MMC)

    if not devices:
        debug_print("FAIL: No eMMC/SD devices found")
        return 1

    debug_print(f"INFO: Found: {', '.join(devices)}")

    results = {}
    total = len(devices)

    for i, device in enumerate(devices, start=1):
        passed = test_device(device, i, total, MMC)
        dev_type = get_device_type(device, MMC)
        results[device] = {"type": dev_type, "passed": passed}
        status = "PASS" if passed else "FAIL"
        debug_print(f"\nINFO: Result: {device} ({dev_type}) -> {status}")

    # Summary
    debug_print(f"\n{'═' * 50}")
    debug_print("=== Summary ===\n")
    any_failed = False
    for device, info in results.items():
        status = "PASS" if info["passed"] else "FAIL"
        debug_print(f"  {device:<12} {info['type']:<6} {status}")
        if not info["passed"]:
            any_failed = True

    debug_print(f"\n  Overall : {'FAIL' if any_failed else 'PASS'}")
    debug_print(f"{'═' * 50}")

    return 1 if any_failed else 0


if __name__ == "__main__":
    sys.exit(main())
