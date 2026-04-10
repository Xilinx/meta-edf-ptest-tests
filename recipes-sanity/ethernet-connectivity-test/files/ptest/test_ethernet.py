#!/usr/bin/env python3

import subprocess
import sys
import socket
import time

"""
Ethernet Interface Test Script for Linux
Tests ethernet connectivity, link status, and basic network operations
"""



def run_command(cmd,timeout=10):
    """Execute shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timeout"


def check_interface_exists(interface):
    """Check if network interface exists"""
    returncode, stdout, _ = run_command(f"ip link show {interface}")
    return returncode == 0


def check_interface_up(interface):
    """Check if interface is up"""
    returncode, stdout, _ = run_command(f"ip link show {interface}")
    if returncode == 0:
        return "state UP" in stdout
    return False


def check_ip_address(interface):
    """Get IP address of interface"""
    returncode, stdout, _ = run_command(f"ip addr show {interface}")
    if returncode == 0:
        for line in stdout.split('\n'):
            if 'inet ' in line:
                return line.strip().split()[1]
    return None


def check_link_speed(interface):
    """Check ethernet link speed"""
    returncode, stdout, _ = run_command(f"ethtool {interface} 2>/dev/null | grep Speed")
    if returncode == 0:
        return stdout.strip()
    return "Unable to determine speed"


def get_default_gateway():
    """Get default gateway from system routing table"""
    returncode, stdout, _ = run_command("ip route | grep default | awk '{print $3}' | head -1")
    if returncode == 0 and stdout.strip():
        return stdout.strip()
    return None


def ping_test(host=None, count=4):
    """Test connectivity via ping"""
    if host is None:
        host = get_default_gateway()
        if not host:
            return False
    returncode, stdout, _ = run_command(f"ping -c {count} -W 2 {host}")
    return returncode == 0


def get_host_ip():
    """Resolve hostname to IP address"""
    try:
        gateway = get_default_gateway()
        if gateway:
            return gateway
        return None
    except Exception:
        return None



def ping_flood_test(host=None):
    """Test connectivity via ping flood"""
    if host is None:
        host = get_default_gateway()
        if not host:
            return False
    print(f"Starting ping flood to {host}...")
    returncode, stdout, stderr = run_command(f"timeout 200 ping -f {host} -i 5 -c 5",timeout=200)
    if returncode == 0:
        print("Ping flood successful.")
    else:
        print(f"Ping flood failed: {stderr.strip()}")
    return returncode == 0

def main():
    print("=== Ethernet Interface Test ===\n")
    
    # Get default interface
    
    #interface = input("Enter interface name (e.g., eth0, enp0s3): ").strip()
    interface = None
    if not interface:
        rc, out, _ = run_command("ip route show default | awk '{print $5}' | head -n 1")
        if rc == 0 and out.strip():
            interface = out.strip()
            if interface not in ['lo', 'docker0'] and not interface.startswith('docker'):
                print(f"Auto-detected interface: {interface}")
            else:
                interface = None
        
        if not interface:
            rc, out, _ = run_command("ls /sys/class/net | grep -E '^eth|^en' | grep -v '^lo$' | head -n 1")
            if rc == 0 and out.strip():
                interface = out.strip()
                print(f"Auto-detected interface: {interface}")
    
    if not interface:
        print("No interface specified. Exiting.")
        return 1
    
    # Test 1: Interface exists
    print(f"\n[Checking if {interface} exists...")
    if check_interface_exists(interface):
        print(f"✓ PASS  Interface {interface} exists")
    else:
        print(f"✗ FAIL: Interface {interface} not found")
        return 1
    
    # Test 2: Interface is up
    print(f"\n Checking if {interface} is up...")
    if check_interface_up(interface):
        print(f"✓ PASS : Interface {interface} is UP")
    else:
        print(f"✗ FAIL: Interface {interface} is DOWN")
    
    # Test 3: IP address assigned
    print(f"\n Checking IP address...")
    ip_addr = check_ip_address(interface)
    if ip_addr:
        print(f"✓ PASS : IP address: {ip_addr}")
    else:
        print(f"✗ FAIL: No IP address assigned")
    
    # Test 4: Link speed
    print(f"\n Checking link speed...")
    speed = check_link_speed(interface)
    print(f"INFO: {speed}")
    
    # Test 5: Ping test
    print(f"\n Testing connectivity ...")
    if ping_test():
        print(f"✓ PASS : Network connectivity OK")
    else:
        print(f"✗ FAIL: Unable to reach external network")
    
    # Test 6: Ping flood test
    print(f"\n Starting ping flood test...")
    if ping_flood_test():
        print(f"✓ PASS : Ping flood successful")
    else:
        print(f"✗ FAIL: Ping flood failed")
    
    print("\n=== Test Complete ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
