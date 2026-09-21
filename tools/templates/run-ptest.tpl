#!/bin/sh

echo "Running ${DRIVER} ptest"
python test_${DRIVER}.py
if [ $? -ne 0 ]; then
    exit 1
fi
exit 0
