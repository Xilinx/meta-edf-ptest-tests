#!/usr/bin/env python3

from ptestlib import lib
from ptestlib.edf_utiles import debug_print
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

    try:
        RTC.run_cmd("which hwclock")
        return True
    except Exception:
        return False


def read_rtc_time(RTC):
    """Read RTC time"""

    out = RTC.run_cmd("hwclock -r", output_log=True).strip()

    # Example:
    # 2026-08-11 15:30:10.123456+00:00

    try:
        ts = out.split(".")[0]
        return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
    except (ValueError, AttributeError):
        return None


def verify_rtc(RTC, delay=5):
    """Verify RTC time advances"""

    t1 = read_rtc_time(RTC)
    if t1 is None:
        return False

    debug_print(f"INFO: RTC Time 1: {t1}")

    time.sleep(delay)

    t2 = read_rtc_time(RTC)
    if t2 is None:
        return False

    debug_print(f"INFO: RTC Time 2: {t2}")

    return (t2 - t1).total_seconds() >= delay


def main():

    debug_print("=== RTC Basic Test ===\n")

    RTC = lib.testsetup("urvf_rtc_basic_test")

    debug_print("[1] Checking hwclock...")

    if check_hwclock(RTC):
        debug_print("PASS:hwclock available")
    else:
        debug_print("FAIL:hwclock not available")
        return 1

    debug_print("\n[2] Verifying RTC...")

    if verify_rtc(RTC):
        debug_print("PASS:RTC running correctly")
    else:
        debug_print("FAIL:RTC not advancing")
        return 1

    debug_print("\n=== Test Complete ===")

    return 0


if __name__ == "__main__":
    sys.exit(main())
