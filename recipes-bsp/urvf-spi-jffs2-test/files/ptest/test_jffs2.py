#!/usr/bin/env python3
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


from ptestlib import lib
from ptestlib.edf_utiles import debug_print
import sys

"""
SPI NOR Flash + JFFS2 Validation Test
"""


def get_md5(SPI, path):
    out = SPI.run_cmd(
        f"md5sum {path} 2>/dev/null | awk '{{print $1}}' || true", output_log=True
    )
    return out.strip() if out else None


def main():

    debug_print("=== SPI Flash JFFS2 Test ===\n")

    SPI = lib.testsetup("urvf_spi_flash_jffs2_test")

    # Define these before try so cleanup block can always reference them
    mtd_block = None
    mount_dir = "./spi_flash"

    try:
        mtd_info = SPI.run_cmd("cat /proc/mtd", output_log=True)

        mtd_num = "17" if "mtd17:" in mtd_info else "0"

        mtd_dev = f"/dev/mtd{mtd_num}"
        mtd_block = f"/dev/mtdblock{mtd_num}"

        debug_print(f"INFO: Using device: {mtd_dev}")

        debug_print("\n[1] Checking MTD Device...")
        SPI.run_cmd(f"mtd_debug info {mtd_dev}")
        debug_print(f"PASS: {mtd_dev} detected")

        debug_print("\n[2] Erasing Flash...")
        SPI.run_cmd(f"flash_erase -j {mtd_dev} 0 0", timeout=300)
        debug_print("PASS: Flash erase successful")

        debug_print("\n[3] Mounting JFFS2...")
        SPI.run_cmd(f"mkdir -p {mount_dir}")
        SPI.run_cmd(f"mount -t jffs2 {mtd_block} {mount_dir}")
        debug_print("PASS: JFFS2 mounted")

        debug_print("\n[4] Creating Test File...")
        SPI.run_cmd("dd if=/dev/urandom of=/tmp/jffs2.bin bs=1024 count=4096")
        SPI.run_cmd(f"cp /tmp/jffs2.bin {mount_dir}/")
        debug_print("PASS: File write successful")

        debug_print("\n[5] Remounting Filesystem...")
        SPI.run_cmd(f"umount {mtd_block}")
        SPI.run_cmd(f"mount -t jffs2 {mtd_block} {mount_dir}")
        debug_print("PASS: Remount successful")

        debug_print("\n[6] Verifying Data Integrity...")
        src_md5 = get_md5(SPI, "/tmp/jffs2.bin")
        dst_md5 = get_md5(SPI, f"{mount_dir}/jffs2.bin")

        if src_md5 is None or dst_md5 is None:
            debug_print("FAIL: Could not read MD5 — file missing or md5sum failed")
            return 1

        if src_md5 != dst_md5:
            debug_print(f"FAIL: MD5 mismatch ({src_md5} != {dst_md5})")
            return 1

        debug_print("PASS: MD5 verification successful")

        SPI.run_cmd(f"umount {mtd_block} || true")
        SPI.run_cmd(f"rm -rf {mount_dir}")
        SPI.run_cmd("rm -f /tmp/jffs2.bin")

        debug_print("\n=== Test Complete ===")
        return 0

    except Exception as e:

        debug_print(f"\nFAIL: {e}")

        try:
            if mtd_block:
                SPI.run_cmd(f"umount {mtd_block} || true")
            SPI.run_cmd(f"rm -rf {mount_dir} 2>/dev/null || true")
            SPI.run_cmd("rm -f /tmp/jffs2.bin")
        except Exception:
            pass

        return 1


if __name__ == "__main__":
    sys.exit(main())
