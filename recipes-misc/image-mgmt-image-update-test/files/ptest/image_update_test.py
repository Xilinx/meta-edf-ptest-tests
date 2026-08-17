#!/usr/bin/env python3
from ptestlib import lib
from ptestlib.edf_utiles import edf_print

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
            edf_print(f"FAIL: Unknown board model: {model}")
            return None
        return machine
    except Exception as e:
        edf_print(f"FAIL: Could not read /proc/device-tree/model: {e}")
        return None


def get_bootbin_path():
    """Return path to boot.bin — user-supplied via $bootbin env var, else board-detected."""
    user_bootbin = os.environ.get("bootbin")
    if user_bootbin:
        edf_print(f"Using user-supplied boot.bin: {user_bootbin}")
        if not os.path.exists(user_bootbin):
            edf_print(f"FAIL: boot.bin not found at {user_bootbin}")
            return None
        return user_bootbin
    machine = get_board_machine()
    if not machine:
        return None
    script_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(script_dir, machine, "boot.bin")
    if not os.path.exists(path):
        edf_print(f"FAIL: boot.bin not found at {path}")
        return None
    return path


def sha256_of_file(path):
    """Compute SHA256 of a local file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def get_bank_mtd_partitions(IMG_UPDATE):
    """Parse /proc/mtd and return mtd device names for Bank A Space and Bank B Space."""
    output = IMG_UPDATE.run_cmd("cat /proc/mtd", output_log=True)
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
    edf_print(f"Bank A Space: {bank_a}")
    edf_print(f"Bank B Space: {bank_b}")
    if not bank_a or not bank_b:
        edf_print("FAIL: Could not find Bank A Space or Bank B Space in /proc/mtd")
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


def show_bootstatus(IMG_UPDATE):
    """Run image-mgmt bootstatus and return parsed dict."""
    edf_print("Show boot status information")
    output = IMG_UPDATE.run_cmd("image-mgmt bootstatus", output_log=True)
    bootstatus = parse_bootstatus(output)
    edf_print("bootstatus output:")
    for key, value in bootstatus.items():
        edf_print(f"  {key}: {value}")
    return bootstatus


def update_boot_bin(IMG_UPDATE, bootbin_path):
    """Flash boot.bin using image-mgmt upload-boot."""
    output = IMG_UPDATE.run_cmd(f"image-mgmt upload-boot {bootbin_path}", output_log=True, timeout=120)
    if output and "SUCCESS" in output:
        return True
    edf_print(f"FAIL: image-mgmt upload-boot did not return SUCCESS\n{output}")
    return False


def compare_bootbin_with_ospi(IMG_UPDATE, local_bootbin, mtd_dev):
    """SHA256-compare local boot.bin against the flashed OSPI partition."""
    edf_print(f"Comparing boot.bin with OSPI partition /dev/{mtd_dev}")
    local_sha = sha256_of_file(local_bootbin)
    edf_print(f"Local boot.bin SHA256 : {local_sha}")
    bootbin_size = os.path.getsize(local_bootbin)
    edf_print(f"boot.bin size         : {bootbin_size} bytes")
    output = IMG_UPDATE.run_cmd(f"head -c {bootbin_size} /dev/{mtd_dev} | sha256sum", output_log=True)
    if not output or not output.strip():
        edf_print(f"FAIL: Could not read SHA256 from /dev/{mtd_dev}")
        return False
    ospi_sha = output.strip().split()[0]
    edf_print(f"OSPI /dev/{mtd_dev} SHA256 : {ospi_sha}")
    if local_sha == ospi_sha:
        edf_print("PASS : BOOT.BIN in OSPI is 100% identical to local BOOT.BIN")
        return True
    edf_print("FAIL: SHA256 mismatch - BOOT.BIN in OSPI differs from local BOOT.BIN")
    return False


def main():
    edf_print("=== Update Boot Binary Test ===\n")
    IMG_UPDATE = lib.testsetup("image_mgmt_image_update_test")
    IMG_UPDATE.check_sudo_request()

    bootbin_path = get_bootbin_path()
    if not bootbin_path:
        edf_print("FAIL: Could not determine boot.bin path. Exiting.")
        return 1
    edf_print(f"Using boot.bin: {bootbin_path}")

    # Test 1: Show image-mgmt help
    edf_print("\n[Test 1] Checking image-mgmt is available...")
    IMG_UPDATE.run_cmd("image-mgmt --help")
    edf_print("✓ PASS : image-mgmt is available")

    # Test 2: Read boot status before update
    edf_print("\n[Test 2] Reading boot status before update...")
    bootstatus_before = show_bootstatus(IMG_UPDATE)
    previous_bank = bootstatus_before.get("Previous Bank")
    if not previous_bank:
        edf_print("FAIL: Could not determine Previous Bank from bootstatus")
        return 1
    edf_print(f"✓ PASS : Previous Bank is {previous_bank}")

    # Test 3: Upload boot.bin
    edf_print(f"\n[Test 3] Uploading boot.bin to previous bank...")
    if update_boot_bin(IMG_UPDATE, bootbin_path):
        edf_print("✓ PASS : image-mgmt upload-boot succeeded")
    else:
        edf_print("✗ FAIL: image-mgmt upload-boot failed")
        return 1

    # Test 4: Switch bank back to previous
    edf_print(f"\n[Test 4] Switching to newly updated bank ({previous_bank})...")
    IMG_UPDATE.run_cmd(f"image-mgmt switch-bank {previous_bank}")
    edf_print(f"✓ PASS : Switched to bank {previous_bank}")

    # Test 5: Verify OSPI flash matches local boot.bin via SHA256
    edf_print("\n[Test 5] Verifying OSPI flash contents via SHA256...")
    bank_a, bank_b = get_bank_mtd_partitions(IMG_UPDATE)
    if previous_bank == "A":
        selected_mtd = bank_a
    elif previous_bank == "B":
        selected_mtd = bank_b
    else:
        edf_print(f"FAIL: Unknown Previous Bank value: {previous_bank}")
        return 1

    edf_print(f"Selected MTD partition: /dev/{selected_mtd}")
    if compare_bootbin_with_ospi(IMG_UPDATE, bootbin_path, selected_mtd):
        edf_print("✓ PASS : OSPI flash verified successfully")
    else:
        edf_print("✗ FAIL: OSPI flash verification failed")
        return 1

    edf_print("\n=== Test Complete ===")
    edf_print("Please reboot to apply changes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
