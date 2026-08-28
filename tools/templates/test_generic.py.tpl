#!/usr/bin/env python3

from ptestlib import lib
import sys

def main():

    TEST = lib.testsetup("${DRIVER}_basic_test")

    print("=== ${DRIVER_UPPER} Basic Test ===")

    print("SKIP : Test logic not implemented")

    return 0

if __name__ == "__main__":
    sys.exit(main())
