import subprocess
"""
Execute dfx-mgr-client command to list packages and print output.
This script runs the dfx-mgr-client utility with the '-listPackage' parameter
to retrieve available packages. It captures and displays the standard output,
and prints any error messages if the command fails.
The '/proc/device-tree/model' path reference indicates this is intended for use
on a Xilinx ZynqMP ZCU106 Rev1.0 embedded platform, where device tree information
can be queried to identify the machine/board model.
Returns:
    None. Prints package list to stdout or error messages to stderr.
Raises:
    FileNotFoundError: If dfx-mgr-client is not found in the system PATH.
"""


def get_id_for_board(board_name):
    result = subprocess.run(
        ["dfx-mgr-client", "-listPackage"],
        capture_output=True,
        text=True,
        check=True
    )

    for line in result.stdout.splitlines():
        if board_name.lower() in line.lower() and "XRT_FLAT" in line:
            parts = line.split()
            print(parts[0])
            return parts[0]   # ID column

    return None

dict_REV={"VEK385 revA":"vek385","VEK385 revB":"vek385-revb"}
MACHINE_BSP=["ZCU111","ZCU102","ZCU104","ZCU106","VCK190","VMK180","VRK160","VRK165","ZCU208","VMK180","VPK180","VPK120"]
print("INFO :DFX manager client load and unload test")
machine="None"
with open('/proc/device-tree/model', 'r') as f:
    data=f.read().lower()
for key in dict_REV.keys():
    if key.lower() in data:
        machine =dict_REV[key].lower()
        break
if  machine == "None":
    for m in MACHINE_BSP:
        if m.lower() in data:
            machine = m
            break
if machine == "None":
    print("FAIL: No matching machine found in device tree model")
else:
    print(f"Machine: {machine}")
board_id = get_id_for_board(machine)
if board_id:
    result = subprocess.run(
            ["dfx-mgr-client", "-load", board_id  ],
            capture_output=True,
            text=True
        )
else:
    print(f"FAIL: No matching board found for {machine}")

if result.returncode != 0:
    print(f"FAIL loading board: {result.stderr}")
    assert False, "Failed to load"
        

result = subprocess.run(
      ["dfx-mgr-client", "-unload", board_id],
        capture_output=True,
        text=True
        )
if result.returncode != 0:
    print(f"FAIL unloading board: {result.stderr}")
    assert False, "Failed to unload"

print("PASS :DFX manger client load and unload test")
