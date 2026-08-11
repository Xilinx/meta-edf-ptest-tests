#!/usr/bin/env python3
from ptestlib import lib

import sys
import os
import re
import hashlib

"""
Update Boot Binary Test for AMD Versal boards
Tests image-mgmt upload-boot and verifies OSPI flash matches local boot.bin
"""

BOARD_MACHINE_MAP = {
    "AMD Versal VEK385 revA":               "versal-2ve-2vm-vek385-multidomain",
    "AMD Versal VEK385 revB":               "versal-2ve-2vm-vek385-revb-multidomain",
    "Xilinx Versal vek280 Eval board revB": "versal-vek280-multidomain",
    "Xilinx Versal VRK160 Eval board revA": "versal-vrk160-multidomain",
    "Xilinx Versal VRK165 Eval board revA": "versal-vrk165-multidomain",
}


def get_board_machine():
    """Detect board by reading /proc/device-tree/model and return machine name."""
    try:
        with open("/proc/device-tree/model", "r") as f:
            model = f.read().strip().rstrip("\x00")
        machine = BOARD_MACHINE_MAP.get(model)
        if not machine:
            print(f"FAIL: Unknown board model: {model}")
            return None
        return machine
    except Exception as e:
        print(f"FAIL: Could not read /proc/device-tree/model: {e}")
        return None


def get_bootbin_path():
    """Return path to boot.bin — user-supplied via $bootbin env var, else board-detected."""
    user_bootbin = os.environ.get("bootbin")
    if user_bootbin:
        print(f"Using user-supplied boot.bin: {user_bootbin}")
        if not os.path.exists(user_bootbin):
            print(f"FAIL: boot.bin not found at {user_bootbin}")
            return None
        return user_bootbin
    machine = get_board_machine()
    if not machine:
        return None
    script_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(script_dir, machine, "boot.bin")
    if not os.path.exists(path):
        print(f"FAIL: boot.bin not found at {path}")
        return None
    return path


def sha256_of_file(path):
    """Compute SHA256 of a local file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def get_bank_mtd_partitions(BOOT):
    """Parse /proc/mtd and return mtd device names for Bank A Space and Bank B Space."""
    output = BOOT.run_cmd("cat /proc/mtd", output_log=True)
    bank_a = None
    bank_b = None
    for line in (output or "").splitlines():
        match = re.match(r'^(mtd\d+):\s+\S+\s+\S+\s+"(.+)"', line)
        if match:
            dev, name = match.group(1), match.group(2)
            if name == "Bank A Space":
                bank_a = dev
            elif name == "Bank B Space":
                bank_b = dev
    print(f"Bank A Space: {bank_a}")
    print(f"Bank B Space: {bank_b}")
    if not bank_a or not bank_b:
        print("FAIL: Could not find Bank A Space or Bank B Space in /proc/mtd")
    return bank_a, bank_b


def parse_bootstatus(data):
    """Parse image-mgmt bootstatus output into a dict."""
    parameter = ["active", "inactive", "A", "B"]
    status_dict = {}
    for line in (data or "").strip().split("\n"):
        line = re.sub(r"\[.*?\]\s*", "", line).strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if key in ("Bank A Status", "Bank B Status", "Active Bank", "Previous Bank"):
            if value in parameter:
                status_dict[key] = value
        elif key in ("Bank A CRC", "Bank B CRC", "Product Name", "Product Revision", "UUID"):
            status_dict[key] = value
    return status_dict


def show_bootstatus(BOOT):
    """Run image-mgmt bootstatus and return parsed dict."""
    print("Show boot status information")
    output = BOOT.run_cmd("image-mgmt bootstatus", output_log=True)
    bootstatus = parse_bootstatus(output)
    print("bootstatus output:")
    for key, value in bootstatus.items():
        print(f"  {key}: {value}")
    return bootstatus


def update_boot_bin(BOOT, bootbin_path):
    """Flash boot.bin using image-mgmt upload-boot."""
    output = BOOT.run_cmd(f"image-mgmt upload-boot {bootbin_path}", output_log=True, timeout=120)
    if output and "SUCCESS" in output:
        return True
    print(f"FAIL: image-mgmt upload-boot did not return SUCCESS\n{output}")
    return False


def compare_bootbin_with_ospi(BOOT, local_bootbin, mtd_dev):
    """SHA256-compare local boot.bin against the flashed OSPI partition."""
    print(f"Comparing boot.bin with OSPI partition /dev/{mtd_dev}")
    local_sha = sha256_of_file(local_bootbin)
    print(f"Local boot.bin SHA256 : {local_sha}")
    bootbin_size = os.path.getsize(local_bootbin)
    print(f"boot.bin size         : {bootbin_size} bytes")
    output = BOOT.run_cmd(f"head -c {bootbin_size} /dev/{mtd_dev} | sha256sum", output_log=True)
    if not output or not output.strip():
        print(f"FAIL: Could not read SHA256 from /dev/{mtd_dev}")
        return False
    ospi_sha = output.strip().split()[0]
    print(f"OSPI /dev/{mtd_dev} SHA256 : {ospi_sha}")
    if local_sha == ospi_sha:
        print("PASS : BOOT.BIN in OSPI is 100% identical to local BOOT.BIN")
        return True
    print("FAIL: SHA256 mismatch - BOOT.BIN in OSPI differs from local BOOT.BIN")
    return False


def main():
    print("=== Update Boot Binary Test ===\n")
    BOOT = lib.testsetup("update_bootbin_test")
    BOOT.check_sudo_request()

    # Detect board and resolve boot.bin path
    bootbin_path = get_bootbin_path()
    if not bootbin_path:
        print("FAIL: Could not determine boot.bin path. Exiting.")
        return 1
    print(f"Using boot.bin: {bootbin_path}")

    # Test 1: Show image-mgmt help
    print("\n[Test 1] Checking image-mgmt is available...")
    BOOT.run_cmd("image-mgmt --help")
    print("✓ PASS : image-mgmt is available")

    # Test 2: Read boot status before update
    print("\n[Test 2] Reading boot status before update...")
    bootstatus_before = show_bootstatus(BOOT)
    previous_bank = bootstatus_before.get("Previous Bank")
    if not previous_bank:
        print("FAIL: Could not determine Previous Bank from bootstatus")
        return 1
    print(f"✓ PASS : Previous Bank is {previous_bank}")

    # Test 3: Upload boot.bin
    print(f"\n[Test 3] Uploading boot.bin to previous bank...")
    if update_boot_bin(BOOT, bootbin_path):
        print("✓ PASS : image-mgmt upload-boot succeeded")
    else:
        print("✗ FAIL: image-mgmt upload-boot failed")
        return 1

    # Test 4: Switch bank back to previous
    print(f"\n[Test 4] Switching to newly updated  bank ({previous_bank})...")
    BOOT.run_cmd(f"image-mgmt switch-bank {previous_bank}")
    print(f"✓ PASS : Switched to bank {previous_bank}")

    # Test 5: Verify OSPI flash matches local boot.bin via SHA256
    print("\n[Test 5] Verifying OSPI flash contents via SHA256...")
    bank_a, bank_b = get_bank_mtd_partitions(BOOT)
    if previous_bank == "A":
        selected_mtd = bank_a
    elif previous_bank == "B":
        selected_mtd = bank_b
    else:
        print(f"FAIL: Unknown Previous Bank value: {previous_bank}")
        return 1

    print(f"Selected MTD partition: /dev/{selected_mtd}")
    if compare_bootbin_with_ospi(BOOT, bootbin_path, selected_mtd):
        print("✓ PASS : OSPI flash verified successfully")
    else:
        print("✗ FAIL: OSPI flash verification failed")
        return 1

    print("\n=== Test Complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
