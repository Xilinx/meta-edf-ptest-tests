import subprocess
import sys


def test_dnf_install(pkg):
    """Test DNF install operation"""
    print(f"**************************Testing DNF install operation for pkg {pkg}**********")
    result = subprocess.run(['dnf', 'install', '-y', pkg], text=True)
    if result.returncode != 0:
        return(f"FAIL: Install failed\n{result.stdout}")
    else:
        return(f"PASS : dnf Install")


def test_dnf_remove(pkg):
    """Test DNF remove operation"""
    print(f"**************************Testing DNF remove operation for pkg {pkg}**********")
    result = subprocess.run(['dnf', 'remove', '-y', pkg],capture_output=True, text=True)
    if result.returncode != 0 or "No packages marked for removal" in  f"{result.stdout}\n{result.stderr}":
        return(f"FAIL: Remove failed\n{result.stdout}")
    else:
        return(f"PASS : dnf Remove")

def test_dnf_reinstall(pkg):
    """Test DNF reinstall operation"""
    print(f"**************************Testing DNF reinstall operation for pkg {pkg}**********")
    result = subprocess.run(['dnf', 'reinstall', '-y', pkg], text=True)
    if result.returncode != 0:
        return(f"FAIL: Reinstall failed\n{result.stdout}")
    else:
        return("PASS : dnf Reinstall"  )
    

def test_dnf_upgrade():
    """Test DNF upgrade operation"""
    print("****************Testing zero DNF upgrade operation**************")
    result = subprocess.run(['dnf', 'check-update',], capture_output=True,text=True)
    output = f"{result.stdout}\n{result.stderr}"
    if result.returncode != 0:
      print(output)
      return(f"FAIL: Upgrade failed")
    else:
      return(f"PASS : dnf Upgrade")

if __name__ == "__main__":
    pkg = sys.argv[1] if len(sys.argv) > 1 else 'gcc'
    test_result=test_dnf_upgrade()
    print(test_result)
    test_result=test_dnf_install(pkg)
    print(test_result)
    test_result=test_dnf_reinstall(pkg)
    print(test_result)
    test_result=test_dnf_remove(pkg)
    print(test_result)

