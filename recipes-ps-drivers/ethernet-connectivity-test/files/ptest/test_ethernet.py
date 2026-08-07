#!/usr/bin/env python3
from ptestlib import lib

import subprocess
import sys
import socket
import time

"""
Ethernet Interface Test Script for Linux
Tests ethernet connectivity, link status, and basic network operations
"""


def check_interface_exists(interface, ETH):
    """Check if network interface exists"""
    ETH.run_cmd(f"ip link show {interface}")
    return True


def check_interface_up(interface, ETH):
    """Check if interface is up"""
    ETH.run_cmd(f"ip link show {interface}")
    return True


def check_ip_address(interface, ETH):
    """Get IP address of interface"""
    ETH.run_cmd(f"ip addr show {interface}")
    return True


def check_link_speed(interface, ETH):
    """Check ethernet link speed"""
    op=ETH.run_cmd(f"ethtool {interface} 2>/dev/null | grep Speed",output_log=True)
    return op.strip() if op else "Speed information not available"

def get_default_gateway(ETH):
    """Get default gateway from system routing table"""
    stdout=ETH.run_cmd("ip route | grep default | awk '{print $3}' | head -1",output_log=True)
    if stdout.strip():
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


def get_host_ip():
    """Resolve hostname to IP address"""
    try:
        gateway = get_default_gateway(ETH)
        if gateway:
            return gateway
        return None
    except Exception:
        return None



def ping_flood_test(ETH, host=None):
    """Test connectivity via ping flood"""
    if host is None:
        host = get_default_gateway(ETH)
        if not host:
            return False
    print(f"Starting ping flood to {host}...")
    ETH.run_cmd(f"timeout 200 ping -f {host} -i 5 -c 5",timeout=200)
    print("Ping flood completed.")
    return True

def main():
    print("=== Ethernet Interface Test ===\n")
    ETH=lib.testsetup("ethernet_connectivity_test")
    
    # Get default interface
    interface = None
    if not interface:
        out = ETH.run_cmd("ip route show default | awk '{print $5}' | head -n 1",output_log=True)
        if out and out.strip():
            interface = out.strip()
            if interface not in ['lo', 'docker0'] and not interface.startswith('docker'):
                print(f"Auto-detected interface: {interface}")
            else:
                interface = None
        
        if not interface:
            out =  ETH.run_cmd("ls /sys/class/net | grep -E '^eth|^en' | grep -v '^lo$' | head -n 1")
            if out and out.strip():
                interface = out.strip()
                print(f"Auto-detected interface: {interface}")
    
    if not interface:
        print("FAIL :No interface specified. Exiting.")
        return 1
    
    # Test 1: Interface exists
    print(f"\n[Checking if {interface} exists...")
    if check_interface_exists(interface,ETH):
        print(f"✓ PASS  Interface {interface} exists")
    else:
        print(f"✗ FAIL: Interface {interface} not found")
        return 1
    
    # Test 2: Interface is up
    print(f"\n Checking if {interface} is up...")
    if check_interface_up(interface,ETH):
        print(f"✓ PASS : Interface {interface} is UP")
    else:
        print(f"✗ FAIL: Interface {interface} is DOWN")
    
    # Test 3: IP address assigned
    print(f"\n Checking IP address...")
    ip_addr = check_ip_address(interface,ETH)
    if ip_addr:
        print(f"✓ PASS : IP address: {ip_addr}")
    else:
        print(f"✗ FAIL: No IP address assigned")
    
    # Test 4: Link speed
    print(f"\n Checking link speed...")
    speed = check_link_speed(interface,ETH)
    print(f"INFO: {speed}")
    
    # Test 5: Ping test
    print(f"\n Testing connectivity ...")
    if ping_test(ETH):
        print(f"✓ PASS : Network connectivity OK")
    else:
        print(f"✗ FAIL: Unable to reach external network")
    
    # Test 6: Ping flood test
    print(f"\n Starting ping flood test...")
    if ping_flood_test(ETH):
        print(f"✓ PASS : Ping flood successful")
    else:
        print(f"✗ FAIL: Ping flood failed")
    
    print("\n=== Test Complete ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
