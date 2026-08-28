#!/usr/bin/env python3

from ptestlib import lib
import sys

"""
eMMC/SD Functional Test
"""


def detect_mmc_device(MMC):
    """Check if eMMC/SD device exists"""
    out = MMC.run_cmd("lsblk -dn -o NAME | grep '^mmcblk' | head -1", output_log=True)
    return out.strip() if out else None


def detect_mount_point(device, MMC):
    """Find writable mounted filesystem"""

    out = MMC.run_cmd(f"lsblk -nrpo MOUNTPOINT /dev/{device}", output_log=True)

    if not out:
        return None

    for mount in out.splitlines():

        mount = mount.strip()

        if not mount:
            continue

        # Skip boot partitions
        if mount in ["/efi", "/boot"]:
            continue

        writable = MMC.run_cmd(f"test -w {mount} && echo OK", output_log=True)

        if "OK" in writable:
            return mount

    return None


def emmc_sd_rw_test(mount_point, MMC):
    """Simple Read/Write test"""

    test_file = f"{mount_point}/emmc_test.txt"

    MMC.run_cmd(f"echo EDF_EMMC_TEST > {test_file} && sync")

    out = MMC.run_cmd(f"cat {test_file}", output_log=True)

    MMC.run_cmd(f"rm -f {test_file}")

    return "EDF_EMMC_TEST" in out


def main():

    print("=== eMMC/SD Functional Test ===\n")

    MMC = lib.testsetup("emmc_sd_test")

    print("\nChecking eMMC/SD device...")

    device = detect_mmc_device(MMC)

    if not device:
        print("SKIP : No eMMC/SD device found")
        return 0

    print(f"✓ PASS : Detected Device : {device}")

    print("\nChecking mounted filesystem...")

    mount_point = detect_mount_point(device, MMC)

    if not mount_point:
        print("SKIP : No writable mounted filesystem found")
        return 0

    print(f"✓ PASS : Mounted Filesystem : {mount_point}")

    print("\nChecking eMMC/SD Read Write...")

    if emmc_sd_rw_test(mount_point, MMC):
        print("✓ PASS : eMMC/SD Read Write Successful")
    else:
        print("✗ FAIL : eMMC/SD Read Write Failed")
        return 1

    print("\n=== Test Complete ===")

    return 0


if __name__ == "__main__":
    sys.exit(main())
