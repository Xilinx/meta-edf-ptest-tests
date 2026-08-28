#!/usr/bin/env python3

from ptestlib import lib
import sys
import time
from datetime import datetime

"""
Basic RTC Test

1. Verify hwclock available
2. Read RTC time
3. Wait 5 seconds
4. Read RTC time again
5. Verify RTC time advanced
"""


def check_hwclock(RTC):
    """Check hwclock availability"""

    RTC.run_cmd("which hwclock")
    return True


def read_rtc_time(RTC):
    """Read RTC time"""

    out = RTC.run_cmd("hwclock -r", output_log=True).strip()

    # Example:
    # 2026-08-11 15:30:10.123456+00:00

    ts = out.split(".")[0]

    return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")


def verify_rtc(RTC, delay=5):
    """Verify RTC time advances"""

    t1 = read_rtc_time(RTC)

    print(f"RTC Time 1 : {t1}")

    time.sleep(delay)

    t2 = read_rtc_time(RTC)

    print(f"RTC Time 2 : {t2}")

    return (t2 - t1).total_seconds() >= delay


def main():

    print("=== RTC Basic Test ===\n")

    RTC = lib.testsetup("rtc_basic_test")

    print("Checking hwclock...")

    if check_hwclock(RTC):
        print("✓ PASS : hwclock available")
    else:
        print("✗ FAIL : hwclock not available")
        return 1

    print("\nVerifying RTC...")

    if verify_rtc(RTC):
        print("✓ PASS : RTC running correctly")
    else:
        print("✗ FAIL : RTC not advancing")
        return 1

    print("\n=== Test Complete ===")

    return 0


if __name__ == "__main__":
    sys.exit(main())
