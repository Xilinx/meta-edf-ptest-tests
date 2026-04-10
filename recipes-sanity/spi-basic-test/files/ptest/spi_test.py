import shlex
import subprocess
import time
import os
import sys

def run_cmd(cmd):
    print("Executing:", shlex.join(cmd))
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)

def check_result(test_name):
   dmesg = subprocess.run(["dmesg", "--color=never"], capture_output=True, text=True).stdout
   if "finished" not in dmesg:
       print(f"FAIL:{test_name}")
   else:
       print(f"PASS:{test_name}")
def setup_mtd_speedtest(dev):
    if os.geteuid() != 0:
        raise PermissionError("Must be run as root")

    # echo 8 > /proc/sys/kernel/printk
    with open("/proc/sys/kernel/printk", "w") as f:
        f.write("8\n")

    # depmod
    run_cmd(['dmesg', '-c'])

    run_cmd([
        "modprobe",
        "mtd_speedtest",
        f"dev={dev}",
        "count=1"
    ])
    # sleep 1
    time.sleep(1)

def setup_mtd_readtest(dev):
    """
    dev: integer MTD index (e.g., 0, 17)
    """
    if os.geteuid() != 0:
        raise PermissionError("Must be run as root")

    run_cmd([
        "modprobe",
        "mtd_readtest",
        f"dev={dev}", 
    ])

    time.sleep(1)
def get_mtd0_or_user_line_numbers(proc_mtd="/proc/mtd"): 
    """
    Return line numbers (1-based) from /proc/mtd
    where the entry is either:
      - mtd0
      - partition name contains 'user' (case-insensitive)

    Returns:
        List[int]
    """
    line_numbers = []

    with open(proc_mtd, "r") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()

            if not line.startswith("mtd"):
                continue

            # Example line:
            # mtd17: 005c0000 00020000 "User Scratchpad"
            parts = line.split(None, 3)
            if len(parts) != 4:
                continue

            mtd = parts[0].rstrip(":")
            name = parts[3].strip('"')

            if mtd == "mtd0" or "user" in name.lower():
                mtd_num = int(mtd.replace("mtd", ""))
                if "user" in name.lower():
                    line_numbers=[]
                    line_numbers.append(mtd_num)
                    break
                line_numbers.append(mtd_num)
    return line_numbers

if __name__ == "__main__":
    mtd_node=get_mtd0_or_user_line_numbers()
    print(f"Found MTD nodes: {mtd_node}")
    for dev in mtd_node:
        print(f"Setting up MTD speedtest for device: mtd{dev}")
        setup_mtd_speedtest(dev)
        check_result(f"MTD speedtest for device: mtd{dev}")
        print(f"Setting up MTD readtest for device: mtd{dev}")
        setup_mtd_readtest(dev)
        check_result(f"MTD speedtest for device: mtd{dev}")

