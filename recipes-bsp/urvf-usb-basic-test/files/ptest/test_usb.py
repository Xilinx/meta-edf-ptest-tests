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
import re
import sys

"""
Generic USB Test Script for Linux

Tests:
1. USB bus device nodes exist
2. USB host controller driver loaded
3. USB root hub detected
4. USB device enumerated
5. USB storage detected via /dev/disk/by-id/
6. Partition created on USB storage
7. ext4 write + integrity verify
8. vfat write + integrity verify
"""

FILESYSTEMS = ["ext4", "vfat"]
TEST_PARTITION_SIZE = "4GiB"
TEST_FILE_KB = 10
MOUNT_POINT = "/tmp/usb_ptest_mount"
TEST_BIN_HOST = "/tmp/usb_ptest.bin"
TEST_BIN_USB = "usb_ptest.bin"


def check_usb_bus_nodes(USB):
    output = USB.run_cmd("ls /dev/bus/usb/ 2>/dev/null || true", output_log=True)
    return output.strip() if output else None


def check_driver_loaded(USB):
    output = USB.run_cmd(
        "dmesg 2>/dev/null | grep -i 'new USB bus registered' || true", output_log=True
    )
    return bool(output and output.strip())


def check_root_hub(USB):
    output = USB.run_cmd(
        "lsusb 2>/dev/null | grep -i 'root hub' || true", output_log=True
    )
    if output and output.strip():
        debug_print(output.strip())
        return True
    return False


def detect_usb_devices(USB):
    output = USB.run_cmd("lsusb 2>/dev/null || true", output_log=True)
    devices = []
    if output:
        for line in output.splitlines():
            if "root hub" not in line.lower() and line.strip():
                devices.append(line.strip())
    return devices


def detect_usb_storage(USB):
    """
    Find first USB storage block device via /dev/disk/by-id/.
    Excludes partition entries and resolves symlink to /dev/sdX.
    """
    output = USB.run_cmd(
        "find /dev/disk/by-id/ -type l "
        r"\( -name '*usb*' \) -a ! -iname '*part*' "
        "2>/dev/null || true",
        output_log=True,
    )

    if not output or not output.strip():
        return None

    for link in output.splitlines():
        link = link.strip()
        if not link:
            continue
        resolved = USB.run_cmd(
            f"readlink -f {link} 2>/dev/null || true", output_log=True
        )
        if resolved:
            resolved = resolved.strip()
            if re.match(r"^/dev/sd[a-z]+$", resolved):
                return resolved

    return None


def is_disk_in_use(USB, device):
    """Return True if the device or any of its partitions are currently mounted."""
    output = USB.run_cmd(
        f"grep -E '^{device}' /proc/mounts 2>/dev/null || true", output_log=True
    )
    return bool(output and output.strip())


def prepare_partition(USB, device):
    """Wipe all partitions and create a single fresh partition."""
    USB.run_cmd(
        f"parted -s {device} mklabel gpt "
        f"mkpart primary 0% {TEST_PARTITION_SIZE} 2>&1 || true",
        output_log=True,
    )
    USB.run_cmd("sync", output_log=True)
    output = USB.run_cmd(
        f"fdisk -l {device} 2>/dev/null | grep '{device}1' || true", output_log=True
    )
    return bool(output and output.strip())


def format_partition(USB, partition, fstype):
    if fstype == "vfat":
        cmd = f"mkfs.vfat {partition} -F 32 2>&1 || true"
    else:
        cmd = f"mkfs.{fstype} -F {partition} 2>&1 || true"
    output = USB.run_cmd(cmd, output_log=True)
    return bool(output and "error" not in output.lower())


def mount_partition(USB, partition, fstype):
    USB.run_cmd(f"mkdir -p {MOUNT_POINT} 2>/dev/null || true", output_log=True)
    output = USB.run_cmd(
        f"mount -t {fstype} {partition} {MOUNT_POINT} 2>&1 || true", output_log=True
    )
    return not (output and "error" in output.lower())


def unmount_partition(USB):
    USB.run_cmd(f"umount {MOUNT_POINT} 2>/dev/null || true", output_log=True)
    USB.run_cmd("sync", output_log=True)


def get_md5(USB, filepath):
    output = USB.run_cmd(
        f"md5sum {filepath} 2>/dev/null | awk '{{print $1}}' || true", output_log=True
    )
    return output.strip() if output else None


def run_filesystem_test(USB, partition, fstype):
    """format → mount → write → unmount → remount → md5 verify → umount"""
    debug_print(f"  Formatting as {fstype}...")
    if not format_partition(USB, partition, fstype):
        debug_print(f"  FAIL: mkfs.{fstype} failed")
        return False

    debug_print(f"  Mounting...")
    if not mount_partition(USB, partition, fstype):
        debug_print(f"  FAIL: mount failed")
        return False

    debug_print(f"  Writing {TEST_FILE_KB}KB random data...")
    USB.run_cmd(
        f"dd if=/dev/urandom of={TEST_BIN_HOST} "
        f"bs=1024 count={TEST_FILE_KB} 2>/dev/null || true",
        output_log=True,
    )
    USB.run_cmd(
        f"cp {TEST_BIN_HOST} {MOUNT_POINT}/{TEST_BIN_USB} 2>/dev/null || true",
        output_log=True,
    )
    USB.run_cmd("sync", output_log=True)

    md5_orig = get_md5(USB, TEST_BIN_HOST)

    debug_print(f"  Unmounting and remounting...")
    unmount_partition(USB)

    if not mount_partition(USB, partition, fstype):
        debug_print(f"  FAIL: remount failed")
        return False

    md5_usb = get_md5(USB, f"{MOUNT_POINT}/{TEST_BIN_USB}")
    unmount_partition(USB)

    debug_print(f"  md5 original : {md5_orig}")
    debug_print(f"  md5 on USB   : {md5_usb}")

    if md5_orig and md5_usb and md5_orig == md5_usb:
        return True

    debug_print(f"  FAIL: md5 mismatch — data corrupted")
    return False


def cleanup(USB):
    unmount_partition(USB)
    USB.run_cmd(f"rm -f {TEST_BIN_HOST}", output_log=True)
    USB.run_cmd(f"rm -rf {MOUNT_POINT}", output_log=True)


def main():
    debug_print("=== USB Test ===")

    USB = lib.testsetup("urvf_usb_basic_test")

    pass_count = 0
    fail_count = 0

    # Test 1: bus nodes
    buses = check_usb_bus_nodes(USB)
    if buses:
        debug_print(f"PASS: Device nodes: {buses}")
        pass_count += 1
    else:
        debug_print("FAIL: No /dev/bus/usb/ entries found")
        fail_count += 1
        return 1

    # Test 2: driver loaded
    if check_driver_loaded(USB):
        debug_print("PASS: Driver loaded")
        pass_count += 1
    else:
        debug_print("SKIP: USB driver message not found in dmesg")

    # Test 3: root hub
    if check_root_hub(USB):
        debug_print("PASS: USB root hub detected")
        pass_count += 1
    else:
        debug_print("FAIL: No USB root hub found")
        fail_count += 1

    # Test 4: device enumerated
    devices = detect_usb_devices(USB)
    if devices:
        debug_print(f"PASS: USB device(s) enumerated:")
        for d in devices:
            debug_print(f"  {d}")
        pass_count += 1
    else:
        debug_print("FAIL: No USB device plugged in")
        fail_count += 1

    # Test 5: storage detection
    disk = detect_usb_storage(USB)
    if not disk:
        debug_print("FAIL: No USB storage found")
        return 1

    debug_print(f"PASS: USB storage detected: {disk}")
    pass_count += 1

    # Test 6: partition creation
    if is_disk_in_use(USB, disk):
        debug_print(f"FAIL: USB storage {disk} is in use (mounted — possibly rootfs)")
        fail_count += 1
        debug_print(f"=== PASS:{pass_count} FAIL:{fail_count} ===")
        return 1

    partition = f"{disk}1"
    debug_print(f"\nPreparing {disk} — creating {TEST_PARTITION_SIZE} partition...")
    if prepare_partition(USB, disk):
        debug_print(f"PASS: Partition {partition} created")
        pass_count += 1
    else:
        debug_print(f"FAIL: Could not partition {disk}")
        fail_count += 1
        debug_print(f"=== PASS:{pass_count} FAIL:{fail_count} ===")
        return 1

    # Tests 7-8: filesystem integrity
    for fstype in FILESYSTEMS:
        debug_print(f"\n[{fstype.upper()}]")
        if run_filesystem_test(USB, partition, fstype):
            debug_print(f"PASS: {fstype} integrity verified")
            pass_count += 1
        else:
            debug_print(f"FAIL: {fstype} integrity test failed")
            fail_count += 1

    cleanup(USB)

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
