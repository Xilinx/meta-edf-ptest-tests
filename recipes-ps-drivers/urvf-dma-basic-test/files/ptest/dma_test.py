import subprocess
import time
import os
import signal
from ptestlib import lib
from ptestlib.edf_utiles import (
    write_sysfs,
    check_string_in_dmesg,
    clean_dmesg,
    debug_print,
    clear_log_file,
)
import time


def start_log_capture(log_file):
    debug_print("[INFO] Starting kernel log capture...")
    return subprocess.Popen(
        f"journalctl -kf > {log_file}", shell=True, preexec_fn=os.setsid
    )


def main():
    log_file = "/var/log/dmatest.log"
    run = lib.testsetup("urvf_dma_test")

    # 1. Verify DMA controller from device tree
    res = run.run_cmd(
        "find /sys/firmware/devicetree/base/ -maxdepth 1 \\( -name amba* -o -name axi \\)",
        output_log=True,
    )
    debug_print(res)
    clean_dmesg(run.run_cmd)
    run.run_cmd("ls /sys/class/dma")
    run.run_cmd("modprobe dmatest")
    base = "/sys/module/dmatest/parameters"

    # 4. Configure dmatest
    write_sysfs(f"{base}/iterations", 10)
    write_sysfs(f"{base}/threads_per_chan", 1)
    write_sysfs(f"{base}/channel", "")  # Enable ALL DMA channels
    write_sysfs(f"{base}/verbose", 1)  # Enable verbose logging

    # 5. Clear previous log
    clear_log_file(log_file)

    # 6. Start kernel log capture
    log_proc = start_log_capture(log_file)

    try:
        # 7. Run DMA test
        debug_print("[INFO] Starting DMA test...")
        write_sysfs(f"{base}/run", 1)
        time.sleep(60)
    finally:
        # Stop log capture
        os.killpg(os.getpgid(log_proc.pid), signal.SIGTERM)

    check_string_in_dmesg(
        run.run_cmd,
        success_list=["test passed"],
        failure_list=["test failed", "error", "ERROR:"],
    )
    debug_print("[DONE] DMA test completed")


if __name__ == "__main__":
    main()
