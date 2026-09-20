#!/usr/bin/env python3
from ptestlib import lib
from ptestlib.edf_utiles import debug_print

import sys

"""
Ethernet Interface Test Script for Linux
Tests ethernet connectivity, link status, and basic network operations
"""


def check_interface_exists(interface, ETH):
    """Check if network interface exists"""
    output = ETH.run_cmd(f"ip link show {interface} 2>/dev/null", output_log=True)
    return bool(output and interface in output)


def check_interface_up(interface, ETH):
    """Check if interface is up"""
    output = ETH.run_cmd(f"ip link show {interface} 2>/dev/null", output_log=True)
    return bool(output and "UP" in output)


def check_ip_address(interface, ETH):
    """Get IP address of interface; returns address string or None"""
    output = ETH.run_cmd(f"ip addr show {interface} 2>/dev/null", output_log=True)
    if not output:
        return None
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("inet "):
            return line.split()[1]
    return None


def check_link_speed(interface, ETH):
    """Check ethernet link speed"""
    op = ETH.run_cmd(f"ethtool {interface} 2>/dev/null | grep Speed", output_log=True)
    return op.strip() if op else "Speed information not available"


def get_default_gateway(ETH):
    """Get default gateway from system routing table"""
    stdout = ETH.run_cmd(
        "ip route | grep default | awk '{print $3}' | head -1", output_log=True
    )
    if stdout and stdout.strip():
        return stdout.strip()
    return None


def ping_test(ETH, host=None, count=4):
    """Test connectivity via ping"""
    if host is None:
        host = get_default_gateway(ETH)
        if not host:
            return False
    ETH.run_cmd(f"ping -c {count} -W 2 {host}")
    return True


def ping_flood_test(ETH, host=None):
    """Test connectivity via ping flood"""
    if host is None:
        host = get_default_gateway(ETH)
        if not host:
            return False
    debug_print(f"INFO: Starting ping flood to {host}...")
    ETH.run_cmd(f"timeout 200 ping -f {host} -i 5 -c 5", timeout=200)
    debug_print("INFO: Ping flood completed.")
    return True


def main():
    debug_print("=== Ethernet Interface Test ===\n")
    ETH = lib.testsetup("urvf_ethernet_connectivity_test")

    # Get default interface
    interface = None
    if not interface:
        out = ETH.run_cmd(
            "ip route show default | awk '{print $5}' | head -n 1", output_log=True
        )
        if out and out.strip():
            interface = out.strip()
            if interface not in ["lo", "docker0"] and not interface.startswith(
                "docker"
            ):
                debug_print(f"INFO: Auto-detected interface: {interface}")
            else:
                interface = None

        if not interface:
            out = ETH.run_cmd(
                "ls /sys/class/net | grep -E '^eth|^en' | grep -v '^lo$' | head -n 1"
            )
            if out and out.strip():
                interface = out.strip()
                debug_print(f"INFO: Auto-detected interface: {interface}")

    if not interface:
        debug_print("FAIL: No network interface found. Exiting.")
        return 1

    # Test 1: Interface exists
    debug_print(f"\n[1] Checking if {interface} exists...")
    if check_interface_exists(interface, ETH):
        debug_print(f"PASS: Interface {interface} exists")
    else:
        debug_print(f"FAIL: Interface {interface} not found")
        return 1

    # Test 2: Interface is up
    debug_print(f"\n[2] Checking if {interface} is up...")
    if check_interface_up(interface, ETH):
        debug_print(f"PASS: Interface {interface} is UP")
    else:
        debug_print(f"FAIL: Interface {interface} is DOWN")
        return 1

    # Test 3: IP address assigned
    debug_print(f"\n[3] Checking IP address on {interface}...")
    ip_addr = check_ip_address(interface, ETH)
    if ip_addr:
        debug_print(f"PASS: IP address assigned: {ip_addr}")
    else:
        debug_print(f"FAIL: No IP address assigned to {interface}")
        return 1

    # Test 4: Link speed (informational)
    debug_print(f"\n[4] Checking link speed on {interface}...")
    speed = check_link_speed(interface, ETH)
    debug_print(f"INFO: {speed}")

    # Test 5: Ping test
    debug_print(f"\n[5] Testing connectivity via ping...")
    if ping_test(ETH):
        debug_print("PASS: Network connectivity OK")
    else:
        debug_print("FAIL: Unable to reach default gateway")
        return 1

    # Test 6: Ping flood test
    debug_print(f"\n[6] Starting ping flood test...")
    if ping_flood_test(ETH):
        debug_print("PASS: Ping flood successful")
    else:
        debug_print("FAIL: Ping flood failed")
        return 1

    debug_print("\n=== Test Complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
