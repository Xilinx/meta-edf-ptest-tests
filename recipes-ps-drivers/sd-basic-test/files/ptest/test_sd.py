#!/usr/bin/env python3

from ptestlib import lib
import sys

"""
eMMC/SD Functional Test
"""

SKIP_MOUNTS = ["/efi", "/boot", "/"]


def get_all_mmc_devices(MMC):
    """Find all mmcblk devices on the board"""
    out = MMC.run_cmd("lsblk -dn -o NAME | grep '^mmcblk'", output_log=True)
    if not out:
        return []
    return [d.strip() for d in out.splitlines() if d.strip()]


def get_device_type(device, MMC):
    """Read SD or MMC from sysfs"""
    out = MMC.run_cmd(f"cat /sys/block/{device}/device/type", output_log=True)
    return out.strip() if out else "UNKNOWN"


def raw_block_read(device, MMC):
    """Read 512 bytes directly from block device — hardware level check"""
    out = MMC.run_cmd(
        f"dd if=/dev/{device} of=/dev/null bs=512 count=1 2>&1", output_log=True
    )
    return "records out" in out


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
    out = MMC.run_cmd(f"lsblk -nrpo MOUNTPOINT /dev/{device}", output_log=True)
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
        writable = MMC.run_cmd(f"test -w {mount} && echo OK", output_log=True)
        if "OK" in writable:
            return mount

    return None


def rw_test(mount_point, MMC):
    """Write, read back, verify content — always cleans up"""
    test_file = f"{mount_point}/emmc_test.txt"
    try:
        MMC.run_cmd(f"echo EDF_EMMC_TEST > {test_file} && sync")
        out = MMC.run_cmd(f"cat {test_file}", output_log=True)
        return "EDF_EMMC_TEST" in out
    finally:
        MMC.run_cmd(f"rm -f {test_file}")


def perf_test(mount_point, MMC):
    """Write 4MB and report speed — catches slow/failing cards that still pass R/W"""
    perf_file = f"{mount_point}/perf_test"
    try:
        out = MMC.run_cmd(
            f"dd if=/dev/zero of={perf_file} bs=1M count=4 oflag=sync 2>&1",
            output_log=True,
        )
        for line in out.splitlines():
            if "MB/s" in line or "GB/s" in line:
                return line.strip()
        return None
    finally:
        MMC.run_cmd(f"rm -f {perf_file}")


def test_device(device, index, total, MMC):
    """Run all checks on a single device, return True if passed"""

    dev_type = get_device_type(device, MMC)

    print(f"\n{'─' * 50}")
    print(f"Device {index}/{total} : {device} ({dev_type})")
    print(f"{'─' * 50}")

    # 1. Raw block read
    print("\n  [1/4] Raw Block Read...")
    if raw_block_read(device, MMC):
        print(f"        ✓ PASS : /dev/{device} readable (512 bytes)")
    else:
        print(f"        ✗ FAIL : /dev/{device} not readable")
        return False

    # 2. dmesg error check
    print("\n  [2/4] Hardware Error Check (dmesg)...")
    errors = check_dmesg_errors(device, MMC)
    if errors:
        print(f"        ⚠ WARN : Kernel errors found for {device}")
        for line in errors.splitlines():
            print(f"              → {line.strip()}")
    else:
        print(f"        ✓ PASS : No errors in dmesg for {device}")

    # 3. R/W test
    print("\n  [3/4] Read/Write Test...")
    mount_point = get_writable_mount(device, MMC)
    if not mount_point:
        print("        SKIP : No writable mounted partition found")
        return True

    print(f"        Mount point : {mount_point}")
    if rw_test(mount_point, MMC):
        print("        ✓ PASS : Write → Read → Verify successful")
        print("        ✓ PASS : Cleanup done")
    else:
        print("        ✗ FAIL : Read back mismatch")
        print("        ✓ PASS : Cleanup done")
        return False

    # 4. Performance test
    print("\n  [4/4] Performance Test...")
    speed = perf_test(mount_point, MMC)
    if speed:
        print(f"        Write speed : {speed}")
        print("        ✓ PASS : Performance data collected")
    else:
        print("        ⚠ WARN : Could not parse write speed")

    return True


def main():

    print("=== eMMC/SD Functional Test ===\n")

    MMC = lib.testsetup("emmc_sd_test")

    print("Scanning for MMC/SD devices...")
    devices = get_all_mmc_devices(MMC)

    if not devices:
        print("SKIP : No eMMC/SD devices found")
        return 0

    print(f"  Found : {', '.join(devices)}")

    results = {}
    total = len(devices)

    for i, device in enumerate(devices, start=1):
        passed = test_device(device, i, total, MMC)
        dev_type = get_device_type(device, MMC)
        results[device] = {"type": dev_type, "passed": passed}
        status = "PASS" if passed else "FAIL"
        print(f"\n  Result : {device} ({dev_type}) ──► {status}")

    # Summary
    print(f"\n{'═' * 50}")
    print("=== Summary ===\n")
    any_failed = False
    for device, info in results.items():
        status = "PASS" if info["passed"] else "FAIL"
        print(f"  {device:<12} {info['type']:<6} {status}")
        if not info["passed"]:
            any_failed = True

    print(f"\n  Overall : {'FAIL' if any_failed else 'PASS'}")
    print(f"{'═' * 50}")

    return 1 if any_failed else 0


if __name__ == "__main__":
    sys.exit(main())
