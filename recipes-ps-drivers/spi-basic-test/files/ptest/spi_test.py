from ptestlib.edf_utiles import check_string_in_dmesg, clean_dmesg, edf_print, get_spi_node, kernel_verbosity, setup_modeprobe, teardown_modeprobe

from ptestlib import lib

if __name__ == "__main__":
    run =  lib.testsetup("spi_test")
    mtd_node = get_spi_node()
    kernel_verbosity(1)
    if not mtd_node:
        edf_print("FAIL :No MTD nodes found with 'mtd0' or 'user' in the name.")
        exit(1)
    edf_print(f"Found MTD nodes: {mtd_node}")
    clean_dmesg(run.run_cmd)
    for dev in mtd_node:
        edf_print(f"Setting up MTD speedtest for device: mtd{dev}")
        setup_modeprobe(dev, "mtd_speedtest", runcmd=run.run_cmd,count=1)
        teardown_modeprobe(run.run_cmd, "mtd_speedtest")
        check_string_in_dmesg(run.run_cmd, success_list=["mtd_speedtest: finished"], failure_list=["failed","error","ERROR:"])
        edf_print(f"Setting up MTD readtest for device: mtd{dev}")
        setup_modeprobe(dev, "mtd_readtest", runcmd=run.run_cmd)
        check_string_in_dmesg(run.run_cmd, success_list=["mtd_readtest: finished"], failure_list=["failed","error","ERROR:"])
        teardown_modeprobe(run.run_cmd, "mtd_readtest")
