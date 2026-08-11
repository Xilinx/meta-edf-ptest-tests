#!/usr/bin/env python3
from ptestlib import lib

import sys
import os

"""
Configure UFS Test for AMD Versal boards
Tests image-mgmt ufs-config write, query, and verifies config matches reference JSON
"""


def write_ufs_config(UFS, ufs_config_file):
    """Write UFS config using image-mgmt."""
    print(f"Writing UFS config from {ufs_config_file}")
    output = UFS.run_cmd(f"image-mgmt ufs-config --write {ufs_config_file}", output_log=True, timeout=10)
    if output and "SUCCESS" in output:
        return True
    print(f"FAIL: image-mgmt ufs-config --write did not return SUCCESS\n{output}")
    return False


def query_ufs_config(UFS, script_dir):
    """Query UFS config — tool auto-saves to ufs_config_query.json in the ptest dir."""
    print("Querying UFS config")
    UFS.run_cmd(f"cd {script_dir}")
    output = UFS.run_cmd("image-mgmt ufs-config --query", output_log=True)
    if not output or "SUCCESS" not in output:
        print(f"FAIL: image-mgmt ufs-config --query did not return SUCCESS\n{output}")
        return False
    return True


def verify_ufs_config(UFS, script_dir, ufs_config_file):
    """Diff query output against the reference config file."""
    query_file = f"{script_dir}/ufs_config_query.json"
    print(f"Verifying {query_file} against {ufs_config_file}")
    output = UFS.run_cmd(f"diff -Ewa {query_file} {ufs_config_file}", output_log=True)
    if output and output.strip():
        print(f"FAIL: UFS config mismatch\n{output}")
        return False
    return True


def main():
    print("=== Configure UFS Test ===\n")
    UFS = lib.testsetup("configure_ufs_test")
    UFS.check_sudo_request()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    ufs_config_file = os.path.join(script_dir, "ufs_config.json")

    if not os.path.exists(ufs_config_file):
        print(f"FAIL: ufs_config.json not found at {ufs_config_file}")
        return 1

    print("-----------------AMD System Boot Image Recovery Tool - Configure UFS Device Test-------------------")

    # Test 1: Write UFS config
    print("\n[Test 1] Writing UFS config...")
    if write_ufs_config(UFS, ufs_config_file):
        print("✓ PASS : image-mgmt ufs-config --write succeeded")
    else:
        print("✗ FAIL: image-mgmt ufs-config --write failed")
        return 1

    # Test 2: Query UFS config
    print("\n[Test 2] Querying UFS config...")
    if query_ufs_config(UFS, script_dir):
        print("✓ PASS : image-mgmt ufs-config --query succeeded")
    else:
        print("✗ FAIL: image-mgmt ufs-config --query failed")
        return 1

    # Test 3: Verify query output matches reference config
    print("\n[Test 3] Verifying query output matches reference config...")
    if verify_ufs_config(UFS, script_dir, ufs_config_file):
        print("✓ PASS : UFS config verified - query matches written config")
    else:
        print("✗ FAIL: UFS config mismatch - query differs from written config")
        return 1

    print("\n=== Test Complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
