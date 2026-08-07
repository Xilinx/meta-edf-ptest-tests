import atexit
import os
import time

def get_spi_node(proc_mtd="/proc/mtd"):
    """
    Retrieve the line numbers of MTD (Memory Technology Device) entries from the specified 
    proc filesystem file.
    This function reads the contents of the specified `proc_mtd` file, which typically contains 
    information about memory devices. It looks for lines that start with "mtd" and extracts 
    the MTD number (e.g., mtd0) and the name of the device. The function collects the line 
    numbers for "mtd0" and any entries that contain the word "user" in their name. If a 
    "user" entry is found, the function stops further processing.
    Args:
        proc_mtd (str): The path to the proc file containing MTD information. Defaults to 
                         "/proc/mtd".
    Returns:
        list: A list of integers representing the line numbers of "mtd0" and any "user" 
              entries found in the file.
    """
    line_numbers = []
    with open(proc_mtd, "r") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("mtd"):
                continue

            parts = line.split(None, 3)
            if len(parts) != 4:
                continue
            mtd = parts[0].rstrip(":")
            name = parts[3].strip('"')
            if mtd == "mtd0" or "user" in name.lower():
                line_numbers.append(int(mtd.replace("mtd", "")))
                if "user" in name.lower():
                    break
    return line_numbers

def clean_dmesg(runcmd):
    """
    Clear the kernel message buffer by executing the 'dmesg -c' command.
    This function runs the 'dmesg -c' command, which clears the kernel message buffer 
    and outputs its contents. It is useful for resetting the kernel log before running 
    tests or capturing new messages.
    Args:
        runcmd (function): A function that takes a command string as an argument and 
                           executes it. This
    """
    runcmd("dmesg -c")

def kernel_verbosity(level):
    """
    Set the kernel message verbosity level by writing to /proc/sys/kernel/printk.
    This function allows you to adjust the verbosity of kernel messages by writing 
    the specified level to the /proc/sys/kernel/printk file. The level can be an 
    integer value that corresponds to the desired verbosity level.
    Args:
        level (int): The desired kernel message verbosity level.

    LevelMeaning
    0-EMERG
    1-ALERT
    2-CRIT
    3-ERROR
    4-WARNING
    5-NOTICE
    6-INFO
    7-DEBUG
    8-CONSOLE
    9-DEFAULT
    """
    check_sudo_request()
    with open("/proc/sys/kernel/printk", "w") as f:
        f.write(f"{level}\n")

def check_sudo_request():
    """
    check if the script is running with root privileges.
    This function checks if the effective user ID (EUID) of the current process is 0, which indicates that the script is running with root privileges. If the EUID is not 0, it raises a PermissionError to indicate that the script must be run as root.
    """
    if os.geteuid() != 0:
        raise PermissionError("Must be run as root")
    
def setup_modeprobe(dev, module, runcmd, count=None, timeout=600):
    check_sudo_request()
    try:
        if count:
            runcmd(f"modprobe  {module} dev={dev} count={count}",timeout=timeout)
        else:
            runcmd(f"modprobe  {module} dev={dev}",timeout=timeout)
        time.sleep(1)
    except Exception as e:
        raise Exception(f"Error during setup of module {module}: {e}")

def teardown_modeprobe(runcmd, test_module):
    check_sudo_request()
    try:
        runcmd(f"rmmod {test_module}")
        time.sleep(1)
    except Exception as e:
        raise Exception(f"Error during teardown of module {test_module}: {e}")

def check_string_in_dmesg(runcmd,success_list,failure_list=None):
    """
    Check if specific strings are present in the kernel message buffer (dmesg).
    This function runs the 'dmesg' command to retrieve the kernel message buffer and checks if the specified search strings are present in the output. It returns True if all strings are found, and False otherwise.
    Args:
        success_list (list): A list of strings to search for in the kernel message buffer.
        failure_list (list, optional): A list of strings that indicate failure if found in the kernel message buffer.
    Returns:
        bool: True if all search strings are found, False otherwise.
    """
    dmesg_output = runcmd("dmesg --color=never",output_log=True)
    if failure_list:
        for search_string in failure_list:
            if search_string in dmesg_output:
                raise Exception(f"FAIL: Found failure string '{search_string}' in dmesg output.")
                
                
    if all(search_string in dmesg_output for search_string in success_list):
        edf_print(f"PASS: All success strings found in dmesg output {success_list}")
        return True
    else:
        raise Exception(f"FAIL: Not all success strings found in dmesg output {success_list}")
def edf_print( *args, **kwargs):
    ENABLE_PRINT = os.getenv("DEBUG_PRINT", "0") == "1"
    if ENABLE_PRINT:
        print(*args, **kwargs)

def write_sysfs(path, value):
    edf_print(f"[SYSFS] {path} <- {value}")
    with open(path, "w") as f:
        f.write(str(value))

def clear_log_file(log_file):
    with open(log_file, "w"):
        pass