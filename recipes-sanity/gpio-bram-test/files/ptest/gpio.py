
import os
import mmap
import struct
import subprocess
import time
import re
import time
import dfx_test

# Memory test config
global PHYS_ADDR
PHYS_ADDR = 0xaaaaaa0010000 # auto-detect
PAGE_SIZE = mmap.PAGESIZE
PAGE_MASK = ~(PAGE_SIZE - 1)
OFFSET = PHYS_ADDR & (PAGE_SIZE - 1)

# GPIO test config
global CHIP_NAME
CHIP_NAME = ["gpiochip4"] # auto-detect

DT_AXI_PATH = "/proc/device-tree/axi"


GPIODETECT_RE = re.compile(r"(gpiochip\d+)\s+\[(.*?)\]\s+\((\d+)\s+lines\)")


def memory_test():
    print(f"=== Memory Read/Write Validation at {PHYS_ADDR} ===")
    with os.fdopen(os.open("/dev/mem", os.O_RDWR | os.O_SYNC), 'r+b') as f:
        mem = mmap.mmap(f.fileno(), PAGE_SIZE, mmap.MAP_SHARED,
                        mmap.PROT_READ | mmap.PROT_WRITE,
                        offset=PHYS_ADDR & PAGE_MASK)

        original_bytes = mem[OFFSET:OFFSET+4]
        original_val = struct.unpack("<I", original_bytes)[0]
        print(f"Original value at 0x{PHYS_ADDR:X}: 0x{original_val:08X}")

        test_val = 0xDEADBEAF
        mem[OFFSET:OFFSET+4] = struct.pack("<I", test_val)
        print(f"Wrote test value: 0x{test_val:08X}")

        readback_val = struct.unpack("<I", mem[OFFSET:OFFSET+4])[0]
        print(f"Read back value:  0x{readback_val:08X}")
        if readback_val != test_val:
            print("FAIL: Read back value does not match written value!")
        else:
            print("PASS: Read back value matches written value.")
        test_val = 0x12345678
        mem[OFFSET:OFFSET+4] = struct.pack("<I", test_val)
        print(f"Wrote test value: 0x{test_val:08X}")

        readback_val = struct.unpack("<I", mem[OFFSET:OFFSET+4])[0]
        print(f"Read back value:  0x{readback_val:08X}")
        if readback_val != test_val:
            print("FAIL: Read back value does not match written value!")
        else:
            print("PASS: Read back value matches written value.")
        test_val = 0x87654321
        mem[OFFSET:OFFSET+4] = struct.pack("<I", test_val)
        print(f"Wrote test value: 0x{test_val:08X}")

        readback_val = struct.unpack("<I", mem[OFFSET:OFFSET+4])[0]
        print(f"Read back value:  0x{readback_val:08X}")
        if readback_val != test_val:
            print("FAIL: Read back value does not match written value!")
        else:
            print("PASS: Read back value matches written value.")

        # Restore
        mem[OFFSET:OFFSET+4] = struct.pack("<I", original_val)
        print("Restored original value.")

        mem.close()

def gpio_toggle_test(gpio_node):  # Replace with gpiod based sequence once lib in Basecamp image
    print(f"=== GPIO Toggle Test for {gpio_node} ===")
    iotest = subprocess.Popen(f"gpioset -t1s,1s -c {gpio_node} 0=1",shell=True)
    time.sleep(5)
    iotest.terminate()
    iotest.wait()
    print("GPIO 0 toggle test complete.\n")
    iotest = subprocess.Popen(f"gpioset -t1s,1s -c {gpio_node} 1=1",shell=True)
    time.sleep(5)
    iotest.terminate()
    iotest.wait()
    print("GPIO 1 toggle test complete.\n")
    iotest = subprocess.Popen(f"gpioset -t1s,1s -c {gpio_node} 2=1",shell=True)
    time.sleep(5)
    iotest.terminate()
    iotest.wait()
    print("GPIO 2 toggle test complete.\n")
    iotest = subprocess.Popen(f"gpioset -t1s,1s -c {gpio_node} 3=1",shell=True)
    time.sleep(5)
    iotest.terminate()
    iotest.wait()
    print("GPIO 3 toggle test complete.\n")


def run_gpiodetect():
    """
    Run gpiodetect and return:
    { gpiochipX: (label, num_lines) }
    """
    result = {}

    out = subprocess.check_output(["gpiodetect"], text=True)
    for line in out.splitlines():
        m = GPIODETECT_RE.match(line.strip())
        if m:
            chip = m.group(1)
            label = m.group(2)
            lines = int(m.group(3))
            result[chip] = (label, lines)

    return result


def diff_gpio(before, after):
    before_set = set(before)
    after_set = set(after)

    added = after_set - before_set
    removed = before_set - after_set
    common = before_set & after_set

    print("\n=== GPIO DIFF ===")
    GPIODETECT_RE=[]
    if added:
        print("New GPIO chips:")
        for c in sorted(added):
            label, lines = after[c]
            print(f"  + {c} [{label}] ({lines} lines)")
            GPIODETECT_RE.append(c)
        if GPIODETECT_RE:
            print(f"detcted GPIO chips: {GPIODETECT_RE} \n")
            return GPIODETECT_RE
    else:
        print("No new GPIO chips")


def get_axi_bram_ctrl_addrs():
    """
    Find AXI BRAM controller nodes and extract physical addresses.
    Returns a dict: { node_name : address_int }
    """
    results = {}

    if not os.path.isdir(DT_AXI_PATH):
        raise RuntimeError(f"{DT_AXI_PATH} does not exist")

    for entry in os.listdir(DT_AXI_PATH):
        # Match: axi_bram_ctrl_0@a0010000
        m = re.match(r"(axi_bram_ctrl_\d+)@([0-9a-fA-F]+)", entry)
        if not m:
            continue

        node_name = m.group(1)
        addr_hex = m.group(2)

        addr_int = int(addr_hex, 16)
        results[node_name] = addr_int

    return results

if __name__ == "__main__":
    print("Running gpiodetect (BEFORE)...")
    before = run_gpiodetect()

    for c, (label, lines) in before.items():
        print(f"  {c}: [{label}] ({lines} lines)")

    print("\n>>> Perform your action now (DFX load / overlay apply) <<<")
    machine=dfx_test.get_machine()
    board_id = dfx_test.get_id_for_board(machine)
    dfx_test.dfx_load(board_id)
    print("\nRunning gpiodetect (AFTER) dxf load ...")
    after = run_gpiodetect()
    for c, (label, lines) in after.items():
        print(f"  {c}: [{label}] ({lines} lines)")
    CHIP_NAME = diff_gpio(before, after)
    brams = get_axi_bram_ctrl_addrs()

    if not brams:
        print("FAIL:No AXI BRAM controllers found")
    else:
        for name, addr in brams.items():
            print(f"{name}:")
            print(f"  Physical address (hex): 0x{addr:08X}")
            PHYS_ADDR = addr
    memory_test()
    for gpio_node in CHIP_NAME:
        gpio_toggle_test(gpio_node)
    dfx_test.dfx_unload(board_id)






