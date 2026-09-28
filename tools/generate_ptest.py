#!/usr/bin/env python3

import os
import sys
from string import Template

if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} <driver> <category>")
    print(f"  e.g. {sys.argv[0]} pl-gpio recipes-misc")
    sys.exit(1)

driver = sys.argv[1].lower()
category = sys.argv[2]
recipe_name = f"urvf-{driver}-test"

vars = {"DRIVER": driver, "DRIVER_UPPER": driver.upper()}

template_dir = "tools/templates"

recipe_dir = f"{category}/{recipe_name}"
ptest_dir = f"{recipe_dir}/files/ptest"

os.makedirs(ptest_dir, exist_ok=True)

# recipe
with open(f"{template_dir}/recipe.bb.tpl") as f:
    recipe = Template(f.read()).safe_substitute(vars)

# run-ptest
with open(f"{template_dir}/run-ptest.tpl") as f:
    run_ptest = Template(f.read()).safe_substitute(vars)

# python test
with open(f"{template_dir}/test_generic.py.tpl") as f:
    test_py = Template(f.read()).safe_substitute(vars)

with open(f"{recipe_dir}/{recipe_name}.bb", "w") as f:
    f.write(recipe)

with open(f"{ptest_dir}/run-ptest", "w") as f:
    f.write(run_ptest)

with open(f"{ptest_dir}/test_{driver}.py", "w") as f:
    f.write(test_py)

os.chmod(f"{ptest_dir}/run-ptest", 0o755)
os.chmod(f"{ptest_dir}/test_{driver}.py", 0o755)

print(f"Generated {recipe_name}")

# --------------------------------------------------
# Update packagegroup
# --------------------------------------------------

packagegroup_file = (
    "recipes-core/packagegroups/" "packagegroup-edf-ptest-sanity-coverage.bb"
)

with open(packagegroup_file, "r") as f:
    content = f.read()

if recipe_name not in content:

    last_quote = content.rfind('"')

    content = content[:last_quote] + f"    {recipe_name} \\\n" + content[last_quote:]

    with open(packagegroup_file, "w") as f:
        f.write(content)

    print(f"Added {recipe_name} to packagegroup")

else:
    print(f"{recipe_name} already exists in packagegroup")
