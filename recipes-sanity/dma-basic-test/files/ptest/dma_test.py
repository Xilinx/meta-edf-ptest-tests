#!/usr/bin/env python3

import subprocess
import time
import os
import signal


def run(cmd, check=True):
    print(f"[CMD] {cmd}")
    return subprocess.run(cmd, shell=True, check=check, text=True, capture_output=True)


def write_sysfs(path, value):
    print(f"[SYSFS] {path} <- {value}")
    with open(path, "w") as f:
        f.write(str(value))


def clear_log_file(log_file):
    with open(log_file, "w"):
        pass


def start_log_capture(log_file):
    print("[INFO] Starting kernel log capture...")
    return subprocess.Popen(f"journalctl -kf > {log_file}", shell=True, preexec_fn=os.setsid)


def check_dma_test_results(log_file):
    print("[INFO] DMA test results:")
    run(f"grep -i dmatest {log_file}", check=False)
    with open(log_file) as f:
        for line in f:
            if "test failed" in line.lower():
                print(f"FAIL : DMA TEST FAILED {line.strip()}")
                assert False
    subprocess.run(f"cat {log_file}", shell=True, check=True, text=True, capture_output=False)
    print("PASS DMA test completed")


def main():
    log_file = "/var/log/dmatest.log"

    # 1. Verify DMA controller from device tree
    res = run("find /sys/firmware/devicetree/base/ -maxdepth 1 \\( -name amba* -o -name axi \\)")
    print(res.stdout)

    # 2. List DMA channels
    run("dmesg -c")
    print("[INFO] DMA channels available:")
    print(run("ls /sys/class/dma").stdout)

    # 3. Load dmatest module
    run("modprobe dmatest")

    base = "/sys/module/dmatest/parameters"

    # 4. Configure dmatest
    write_sysfs(f"{base}/iterations", 10)
    write_sysfs(f"{base}/threads_per_chan", 1)
    write_sysfs(f"{base}/channel", "")  # Enable ALL DMA channels
    write_sysfs(f"{base}/verbose", 1)   # Enable verbose logging

    # 5. Clear previous log
    clear_log_file(log_file)

    # 6. Start kernel log capture
    log_proc = start_log_capture(log_file)

    try:
        # 7. Run DMA test
        print("[INFO] Starting DMA test...")
        write_sysfs(f"{base}/run", 1)
        time.sleep(60)
    finally:
        # Stop log capture
        os.killpg(os.getpgid(log_proc.pid), signal.SIGTERM)

    # 8. Show results
    check_dma_test_results(log_file)
    print("[DONE] DMA test completed")


if __name__ == "__main__":
    main()
