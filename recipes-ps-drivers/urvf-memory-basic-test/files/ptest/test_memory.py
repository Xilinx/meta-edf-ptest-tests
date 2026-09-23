#!/usr/bin/env python3

from ptestlib import lib
from ptestlib.edf_utiles import check_string_in_dmesg, debug_print
import re
import sys

"""
Generic kernel-level memory stress test for Linux.

Ported from the mtest_kernel logic in yocto_tests (test_module/drivers/drivers_lib.py,
MTEST() function, testcase == "mtest_kernel") into an edf-ptest-coverage ptest.

Tests:
1. stress-ng is present on the target (pulled in via RDEPENDS in urvf-memory-basic-test.bb).
2. Total system memory is readable (/proc/meminfo), used to size the stress run.
3. stress-ng --vm stress run completes successfully without triggering OOM/kernel aborts.
4. dmesg does not contain memory-abort/OOM failure markers after the run.

No memory size or device path is hardcoded: the stress-ng --vm-bytes value is derived
from a fraction of total RAM (capped) so the test scales to the board under test.

stress-ng is expected to already be installed on the target image (see RDEPENDS in
urvf-memory-basic-test.bb) rather than fetched at runtime - ptest images typically have no
network access or package manager, unlike the dev-board-over-serial environment that
yocto_tests' mtest_kernel logic (which this was ported from) originally ran in.
"""

VM_WORKERS = 2
VM_TIMEOUT_SEC = 60
VM_BYTES_FRACTION = 0.25  # fraction of total RAM to stress
VM_BYTES_CAP_MB = 1024  # never request more than this, regardless of total RAM

SUCCESS_MARKERS = ["successful run completed"]
FAILURE_MARKERS = ["FAIL", "Mem abort info"]
DMESG_FAILURE_MARKERS = ["Mem abort info", "Out of memory", "oom-kill"]


def check_stress_ng(TEST):
    """Return True if stress-ng is present (installed via RDEPENDS at build time)."""
    output = TEST.run_cmd("which stress-ng 2>/dev/null || true", output_log=True)
    return bool(output and "stress-ng" in output)


def get_total_mem_kb(TEST):
    """Parse MemTotal (kB) out of /proc/meminfo."""
    output = TEST.run_cmd("cat /proc/meminfo 2>/dev/null || true", output_log=True)
    if not output:
        return None

    match = re.search(r"MemTotal:\s*(\d+)\s*kB", output)
    return int(match.group(1)) if match else None


def compute_vm_bytes_mb(total_mem_kb):
    """Derive a safe --vm-bytes size (MB) from total RAM, capped to avoid OOM."""
    total_mem_mb = total_mem_kb / 1024
    vm_bytes_mb = int(total_mem_mb * VM_BYTES_FRACTION)
    return max(16, min(vm_bytes_mb, VM_BYTES_CAP_MB))


def run_stress_ng(TEST, vm_bytes_mb):
    """
    Run stress-ng --vm and return its output, treating expected failure markers
    as an exception the same way board.serial.runcmd(expected_failures=...) did
    in yocto_tests.
    """
    cmd = (
        f"stress-ng --vm {VM_WORKERS} --vm-bytes {vm_bytes_mb}M "
        f"--timeout {VM_TIMEOUT_SEC}s --metrics-brief 2>&1 || true"
    )
    output = TEST.run_cmd(cmd, timeout=VM_TIMEOUT_SEC + 60, output_log=True) or ""
    debug_print(f"[INFO] stress-ng output:\n{output}")

    for marker in FAILURE_MARKERS:
        if marker in output:
            raise Exception(
                f"FAIL: Found failure marker '{marker}' in stress-ng output"
            )

    return output


def main():
    debug_print("=== Memory Basic Test ===")

    TEST = lib.testsetup("urvf_memory_basic_test")

    pass_count = 0
    fail_count = 0

    # Test 1: stress-ng available
    if check_stress_ng(TEST):
        debug_print("PASS: stress-ng available")
        pass_count += 1
    else:
        debug_print(
            "FAIL: stress-ng not found on target (expected via RDEPENDS in urvf-memory-basic-test.bb)"
        )
        fail_count += 1
        return 1

    # Test 2: total memory readable
    total_mem_kb = get_total_mem_kb(TEST)
    if total_mem_kb:
        debug_print(f"PASS: Total memory detected: {total_mem_kb} kB")
        pass_count += 1
    else:
        debug_print("FAIL: Could not read total memory from /proc/meminfo")
        fail_count += 1
        return 1

    vm_bytes_mb = compute_vm_bytes_mb(total_mem_kb)

    # Test 3: stress-ng vm stress run
    TEST.run_cmd("dmesg -c 2>/dev/null || true", output_log=True)
    try:
        output = run_stress_ng(TEST, vm_bytes_mb)
        if any(marker in output for marker in SUCCESS_MARKERS):
            debug_print(
                f"PASS: stress-ng completed successfully (--vm-bytes {vm_bytes_mb}M)"
            )
            pass_count += 1
        else:
            debug_print("FAIL: stress-ng did not report a successful run")
            fail_count += 1
    except Exception as e:
        debug_print(f"FAIL: stress-ng run failed: {e}")
        fail_count += 1

    # Test 4: dmesg clean after stress run
    try:
        check_string_in_dmesg(
            TEST.run_cmd, success_list=[], failure_list=DMESG_FAILURE_MARKERS
        )
        debug_print("PASS: No memory-abort/OOM markers found in dmesg")
        pass_count += 1
    except Exception as e:
        debug_print(f"FAIL: {e}")
        fail_count += 1

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
