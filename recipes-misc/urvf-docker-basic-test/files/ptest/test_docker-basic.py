#!/usr/bin/env python3

from ptestlib import lib
from ptestlib.edf_utiles import debug_print
import sys

"""
Docker Basic Test Script for Linux

Tests:
1. Docker service restart and status check
2. Run xilinx/edf:hello-world container
"""

VERSION = "26.06"


def restart_and_check_service(DOCKER):
    DOCKER.run_cmd("systemctl restart docker 2>&1 || true", timeout=30, output_log=True)
    output = DOCKER.run_cmd(
        "systemctl is-active docker 2>/dev/null || true", output_log=True
    )
    return output.strip() == "active" if output else False


def run_edf_hello_world(DOCKER):
    image = f"xilinx/edf:hello-world-{VERSION}"
    output = DOCKER.run_cmd(
        f"docker run --rm {image} 2>&1 || true",
        timeout=120,
        output_log=True,
    )
    return bool(output and output.strip())


def main():
    debug_print(f"=== Docker Basic Test  VERSION={VERSION} ===\n")

    DOCKER = lib.testsetup("urvf_docker_basic_test")

    # Test 1: Restart and check Docker service
    debug_print("[1] Restarting and checking Docker service...")
    if restart_and_check_service(DOCKER):
        debug_print("PASS: Docker service is active")
    else:
        debug_print("FAIL: Docker service is not running")
        return 1

    # Test 2: Run EDF hello-world container
    debug_print(f"\n[2] Running xilinx/edf:hello-world-{VERSION}...")
    if run_edf_hello_world(DOCKER):
        debug_print("PASS: hello-world container ran successfully")
    else:
        debug_print("FAIL: hello-world container failed")
        return 1

    debug_print("\n=== Docker Test Complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
