# SPDX-License-Identifier: MIT
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import os
import signal
import subprocess
import sys
import time

from ptestlib import lib
from ptestlib.edf_utiles import debug_print, write_sysfs


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
        "find /sys/firmware/devicetree/base/ -maxdepth 1 \\( -name amba* -o -name axi \\) 2>/dev/null || true",
        output_log=True,
    )
    if res and res.strip():
        debug_print(f"PASS: DMA controller node found: {res.strip()}")
    else:
        debug_print("FAIL: No DMA controller node found in device tree")
        return 1

    run.run_cmd("dmesg -c 2>/dev/null || true", output_log=True)

    res = run.run_cmd("ls /sys/class/dma 2>/dev/null || true", output_log=True)
    if not res or not res.strip():
        debug_print("FAIL: /sys/class/dma is empty or missing")
        return 1
    debug_print(f"PASS: DMA class entries: {res.strip()}")

    res = run.run_cmd("modprobe dmatest 2>&1 || true", output_log=True)
    if res and (
        "error" in res.lower() or "fatal" in res.lower() or "not found" in res.lower()
    ):
        debug_print(f"FAIL: modprobe dmatest failed: {res.strip()}")
        return 1
    debug_print("PASS: dmatest module loaded")
    base = "/sys/module/dmatest/parameters"

    # 4. Configure dmatest
    try:
        write_sysfs(f"{base}/iterations", 10)
        write_sysfs(f"{base}/threads_per_chan", 1)
        write_sysfs(f"{base}/channel", "")
        write_sysfs(f"{base}/verbose", 1)
    except OSError as e:
        debug_print(f"FAIL: Could not configure dmatest parameters: {e}")
        return 1
    debug_print("PASS: dmatest parameters configured")

    # 5. Clear previous log
    try:
        with open(log_file, "w"):
            pass
    except OSError as e:
        debug_print(f"FAIL: Could not clear log file {log_file}: {e}")
        return 1

    # 6. Start kernel log capture
    log_proc = start_log_capture(log_file)

    try:
        # 7. Run DMA test
        debug_print("[INFO] Starting DMA test...")
        try:
            write_sysfs(f"{base}/run", 1)
        except OSError as e:
            debug_print(f"FAIL: Could not start dmatest: {e}")
            return 1
        time.sleep(60)
    finally:
        # Stop log capture
        os.killpg(os.getpgid(log_proc.pid), signal.SIGTERM)

    # 8. Check dmesg for pass/fail
    dmesg_out = run.run_cmd("dmesg --color=never 2>/dev/null || true", output_log=True)

    if not dmesg_out or not dmesg_out.strip():
        debug_print("FAIL: No dmesg output captured")
        return 1

    for s in ["test failed", "error", "ERROR:"]:
        if s in dmesg_out:
            debug_print(f"FAIL: Found failure string '{s}' in dmesg output")
            return 1

    if "test passed" in dmesg_out:
        debug_print("PASS: DMA test passed")
        return 0

    debug_print("FAIL: 'test passed' not found in dmesg output")
    return 1


if __name__ == "__main__":
    sys.exit(main())
