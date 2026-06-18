import os
import mmap
import struct
import subprocess
import time
import re
import dfx_test

# Memory test config
PHYS_ADDR = 0xaaaaaa0010000  # auto-detect
PAGE_SIZE = mmap.PAGESIZE
PAGE_MASK = ~(PAGE_SIZE - 1)
OFFSET = PHYS_ADDR & (PAGE_SIZE - 1)

# GPIO test config
CHIP_NAME = ["gpiochip4"]  # auto-detect
DT_AXI_PATH = "/proc/device-tree/axi"
GPIODETECT_RE = re.compile(r"(gpiochip\d+)\s+\[(.*?)\]\s+\((\d+)\s+lines\)")

def memory_test():
    print(f"=== Memory Read/Write Validation at {PHYS_ADDR} ===")
    with os.fdopen(os.open("/dev/mem", os.O_RDWR | os.O_SYNC), 'r+b') as f:
        mem = mmap.mmap(f.fileno(), PAGE_SIZE, mmap.MAP_SHARED,
                        mmap.PROT_READ | mmap.PROT_WRITE,
                        offset=PHYS_ADDR & PAGE_MASK)

        original_val = struct.unpack("<I", mem[OFFSET:OFFSET+4])[0]
        print(f"Original value at 0x{PHYS_ADDR:X}: 0x{original_val:08X}")

        for test_val in [0xDEADBEAF, 0x12345678, 0x87654321]:
            mem[OFFSET:OFFSET+4] = struct.pack("<I", test_val)
            readback_val = struct.unpack("<I", mem[OFFSET:OFFSET+4])[0]
            print(f"Wrote test value: 0x{test_val:08X}, Read back value: 0x{readback_val:08X}")
            print("PASS" if readback_val == test_val else "FAIL: Read back value does not match written value!")

        mem[OFFSET:OFFSET+4] = struct.pack("<I", original_val)
        print("Restored original value.")
        mem.close()

def gpio_toggle_test(gpio_node):
    print(f"=== GPIO Toggle Test for {gpio_node} ===")
    for i in range(4):
        iotest = subprocess.Popen(f"gpioset -t1s,1s -c {gpio_node} {i}=1", shell=True)
        time.sleep(5)
        iotest.terminate()
        iotest.wait()
        print(f"GPIO {i} toggle test complete.\n")

def run_gpiodetect():
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

    print("\n=== GPIO DIFF ===")
    if added:
        print("New GPIO chips:")
        for c in sorted(added):
            label, lines = after[c]
            print(f"  + {c} [{label}] ({lines} lines)")
        return list(added)
    else:
        print("No new GPIO chips")
        return []

def get_axi_bram_ctrl_addrs():
    results = {}
    if not os.path.isdir(DT_AXI_PATH):
        raise RuntimeError(f"{DT_AXI_PATH} does not exist")

    for entry in os.listdir(DT_AXI_PATH):
        m = re.match(r"(axi_bram_ctrl_\d+)@([0-9a-fA-F]+)", entry)
        if m:
            node_name = m.group(1)
            addr_int = int(m.group(2), 16)
            results[node_name] = addr_int

    return results

if __name__ == "__main__":
    print("Running gpiodetect (BEFORE)...")
    before = run_gpiodetect()
    for c, (label, lines) in before.items():
        print(f"  {c}: [{label}] ({lines} lines)")

    print("\n>>> Perform your action now (DFX load / overlay apply) <<<")
    machine = dfx_test.get_machine()
    board_id = dfx_test.get_id_for_board(machine)
    dfx_test.dfx_load(board_id)

    print("\nRunning gpiodetect (AFTER) dxf load ...")
    after = run_gpiodetect()
    for c, (label, lines) in after.items():
        print(f"  {c}: [{label}] ({lines} lines)")

    CHIP_NAME = diff_gpio(before, after)
    brams = get_axi_bram_ctrl_addrs()

    if not brams:
        print("FAIL: No AXI BRAM controllers found")
    else:
        for name, addr in brams.items():
            print(f"{name}: Physical address (hex): 0x{addr:08X}")
            PHYS_ADDR = addr

    memory_test()
    for gpio_node in CHIP_NAME:
        gpio_toggle_test(gpio_node)

    dfx_test.dfx_unload(board_id)
