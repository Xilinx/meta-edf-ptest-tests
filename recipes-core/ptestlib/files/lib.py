import shlex
import subprocess
import time
import os
import signal
import atexit
import logging
import sys
import pexpect
from ptestlib.logger import setup_logger

log = logging.getLogger(__name__)


class testsetup:
    def __init__(self, test_name, check_non_zero=True):
        self.test_name = test_name
        self.check_non_zero = check_non_zero
        self.runner = pexpect.spawn("/bin/bash", encoding="utf-8")
        self.runner.expect(r"[#\$] ")
        self.runner.sendline("export PS1='URVF-6.2# '")
        self.prompt = "URVF-6.2# "
        self.runner.expect(self.prompt, timeout=10)
        self.runner.expect(self.prompt, timeout=10)
        self.expect = self.runner.expect  # newly added for convenience
        self.runner.sendline("pwd")
        self.runner.expect(self.prompt)
        self.runner_output = self.runner.before  # newly added for convenience
        self.log_folder = os.environ.get("LOG_FOLDER", "/tmp/test_logs")
        self.report_folder = os.environ.get("REPORT_FOLDER", "/tmp/test_reports")
        self.report_generator = os.environ.get("REPORT_GENERATOR", True)
        self.debug = os.environ.get("debug", None)
        self.log_file = f"{self.log_folder}/{self.test_name}_{int(time.time())}.log"
        os.makedirs(self.log_folder, exist_ok=True)
        os.makedirs(self.report_folder, exist_ok=True)
        self.logger = setup_logger(
            log_dirname=self.log_folder, log_filename=self.log_file
        )
        if self.debug:
            self.runner.logfile_read = sys.stdout
            self.runner.logfile = logging.getLogger().handlers[0].stream
        else:
            self.runner.logfile = logging.getLogger().handlers[0].stream
        if self.check_non_zero:
            self.runner.sendline(
                "check_nzero_exit() { ret=$? ; if [ $ret -ne 0 ]; then echo testedf_returncode=$ret; fi ;}"
            )
            self.runner.expect(self.prompt, timeout=30)

    def run_cmd(self, cmd, timeout=30, expected_list=None, output_log=None):
        output_runcmd = ""
        if self.check_non_zero:
            self.runner.sendline(cmd)
            self.runner.expect(self.prompt, timeout=timeout)
            output_runcmd = self.runner.before
            self.runner.sendline("check_nzero_exit")
            self.runner.expect(self.prompt, timeout=timeout)
            output = self.runner.before
            if "testedf_returncode=" in output:
                raise Exception(f"Command failed: {cmd} \n {output_runcmd}")
        else:
            self.runner.sendline(cmd)
            self.runner.expect(self.prompt, timeout=timeout)
            output_runcmd = self.runner.before
        if output_log is not None:
            return output_runcmd.replace(cmd, "")

    def write_sysfs(self, path, value):
        print(f"[SYSFS] {path} <- {value}")
        with open(path, "w") as f:
            f.write(str(value))

    def setup_module(self, test_module, args):
        self.check_sudo_request()
        self.run_cmd(f"modprobe {test_module} {args}")
        time.sleep(1)

    def teardown_module(self, test_module):
        self.check_sudo_request()
        self.run_cmd(f"rmmod {test_module}")
        time.sleep(1)

    def check_sudo_request(self):
        if os.geteuid() != 0:
            raise PermissionError("Must be run as root")
