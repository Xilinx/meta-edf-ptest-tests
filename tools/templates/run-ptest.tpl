#!/bin/sh

echo "Running ${DRIVER} ptest"

output=$(python test_${DRIVER}.py)
ret=$?

if [ "$ret" -ne 0 ] || echo "$output" | grep -qE "FAIL|Unknown"; then
    echo "$output"
    exit 1
else
    exit 0
fi
