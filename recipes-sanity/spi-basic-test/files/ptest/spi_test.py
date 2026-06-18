import shlex
import subprocess
import time
import os

def run_cmd(cmd):
    print("Executing:", shlex.join(cmd))
    subprocess.run(cmd, check=True, capture_output=True, text=True)

def check_result(test_name):
    dmesg = subprocess.run(["dmesg", "--color=never"], capture_output=True, text=True).stdout
    print(f"{'FAIL' if 'finished' not in dmesg else 'PASS'}: {test_name}")

def setup_mtd_speedtest(dev):
    if os.geteuid() != 0:
        raise PermissionError("Must be run as root")

    with open("/proc/sys/kernel/printk", "w") as f:
        f.write("8\n")

    run_cmd(['dmesg', '-c'])
    run_cmd(["modprobe", "mtd_speedtest", f"dev={dev}", "count=1"])
    time.sleep(1)

def teardown(test_module):
    run_cmd(["rmmod", test_module])
    time.sleep(1)


def setup_mtd_readtest(dev):
    if os.geteuid() != 0:
        raise PermissionError("Must be run as root")

    run_cmd(["modprobe", "mtd_readtest", f"dev={dev}"])
    time.sleep(1)

def get_mtd0_or_user_line_numbers(proc_mtd="/proc/mtd"):
    line_numbers = []

    with open(proc_mtd, "r") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line.startswith("mtd"):
                continue

            parts = line.split(None, 3)
            if len(parts) != 4:
                continue

            mtd = parts[0].rstrip(":")
            name = parts[3].strip('"')

            if mtd == "mtd0" or "user" in name.lower():
                line_numbers.append(int(mtd.replace("mtd", "")))
                if "user" in name.lower():
                    break

    return line_numbers

if __name__ == "__main__":
    mtd_node = get_mtd0_or_user_line_numbers()
    if not mtd_node:
        print("FAIL :No MTD nodes found with 'mtd0' or 'user' in the name.")
        
    print(f"Found MTD nodes: {mtd_node}")
    for dev in mtd_node:
        print(f"Setting up MTD speedtest for device: mtd{dev}")
        setup_mtd_speedtest(dev)
        teardown("mtd_speedtest")
        check_result(f"MTD speedtest for device: mtd{dev}")
        print(f"Setting up MTD readtest for device: mtd{dev}")
        setup_mtd_readtest(dev)
        check_result(f"MTD readtest for device: mtd{dev}")
        teardown("mtd_readtest")
       