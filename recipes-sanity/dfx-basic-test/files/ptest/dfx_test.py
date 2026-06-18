import subprocess

def get_id_for_board(board_name):
    """Execute dfx-mgr-client to find package ID for the given board."""
    result = subprocess.run(
        ["dfx-mgr-client", "-listPackage"],
        capture_output=True,
        text=True,
        check=True
    )

    for line in result.stdout.splitlines():
        if board_name.lower() in line.lower() and "XRT_FLAT" in line:
            return line.split()[0]
    return None


def find_machine(device_tree_path='/proc/device-tree/model'):
    """Identify machine from device tree model."""
    dict_rev = {"VEK385 revA": "vek385", "VEK385 revB": "vek385-revb"}
    machine_bsp = ["ZCU111", "ZCU102", "ZCU104", "ZCU106", "VCK190", "VMK180", 
                   "VRK160", "VRK165", "ZCU208", "VPK180", "VPK120", "VEK280"]
    
    try:
        with open(device_tree_path, 'r') as f:
            data = f.read().lower()
    except FileNotFoundError:
        return None

    # Check revision-specific machines first
    for key, value in dict_rev.items():
        if key.lower() in data:
            return value

    # Then check standard machines
    for machine in machine_bsp:
        if machine.lower() in data:
            return machine

    return None


def main():
    """Load and unload DFX board."""
    print("INFO: DFX manager client load and unload test")
    
    machine = find_machine()
    if not machine:
        print("FAIL: No matching machine found in device tree model")
        return False

    print(f"Machine: {machine}")
    
    board_id = get_id_for_board(machine)
    if not board_id:
        print(f"FAIL: No matching board found for {machine}")
        return False

    # Load board
    result = subprocess.run(
        ["dfx-mgr-client", "-load", board_id],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"FAIL loading board: {result.stderr}")
        return False

    # Unload board
    result = subprocess.run(
        ["dfx-mgr-client", "-unload", board_id],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"FAIL unloading board: {result.stderr}")
        return False

    print("PASS: DFX manager client load and unload test")
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
