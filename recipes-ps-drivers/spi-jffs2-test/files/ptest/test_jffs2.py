#!/usr/bin/env python3

from ptestlib import lib
import sys

"""
SPI NOR Flash + JFFS2 Validation Test
"""


def get_md5(SPI, path):
    return SPI.run_cmd(f"md5sum {path} | awk '{{print $1}}'", output_log=True).strip()


def main():

    print("=== SPI Flash JFFS2 Test ===\n")

    SPI = lib.testsetup("spi_flash_jffs2_test")

    try:
        mtd_info = SPI.run_cmd("cat /proc/mtd", output_log=True)

        mtd_num = "17" if "mtd17:" in mtd_info else "0"

        mtd_dev = f"/dev/mtd{mtd_num}"
        mtd_block = f"/dev/mtdblock{mtd_num}"
        mount_dir = "./spi_flash"

        print(f"Using device: {mtd_dev}")

        print("\n[ Checking MTD Device ]")
        SPI.run_cmd(f"mtd_debug info {mtd_dev}")
        print(f"✓ PASS : {mtd_dev} detected")

        print("\n[ Erasing Flash ]")
        SPI.run_cmd(f"flash_erase -j {mtd_dev} 0 0", timeout=300)
        print("✓ PASS : Flash erase successful")

        print("\n[ Mounting JFFS2 ]")
        SPI.run_cmd(f"mkdir -p {mount_dir}")
        SPI.run_cmd(f"mount -t jffs2 {mtd_block} {mount_dir}")
        print("✓ PASS : JFFS2 mounted")

        print("\n[ Creating Test File ]")
        SPI.run_cmd("dd if=/dev/urandom of=/tmp/jffs2.bin bs=1024 count=4096")

        SPI.run_cmd(f"cp /tmp/jffs2.bin {mount_dir}/")

        print("✓ PASS : File write successful")

        print("\n[ Remounting Filesystem ]")

        SPI.run_cmd(f"umount {mtd_block}")

        SPI.run_cmd(f"mount -t jffs2 {mtd_block} {mount_dir}")

        print("✓ PASS : Remount successful")

        print("\n[ Verifying Data Integrity ]")

        src_md5 = get_md5(SPI, "/tmp/jffs2.bin")
        dst_md5 = get_md5(SPI, f"{mount_dir}/jffs2.bin")

        if src_md5 != dst_md5:
            print(f"✗ FAIL : MD5 mismatch " f"({src_md5} != {dst_md5})")
            return 1

        print("✓ PASS : MD5 verification successful")

        SPI.run_cmd(f"umount {mtd_block} || true")
        SPI.run_cmd(f"rm -rf {mount_dir}")
        SPI.run_cmd("rm -f /tmp/jffs2.bin")

        print("\n=== Test Complete ===")
        return 0

    except Exception as e:

        print(f"\n✗ FAIL : {e}")

        try:
            SPI.run_cmd("umount /dev/mtdblock17 || true")
            SPI.run_cmd("umount /dev/mtdblock0 || true")
            SPI.run_cmd("rm -rf ./spi_flash")
            SPI.run_cmd("rm -f /tmp/jffs2.bin")
        except Exception:
            pass

        return 1


if __name__ == "__main__":
    sys.exit(main())
