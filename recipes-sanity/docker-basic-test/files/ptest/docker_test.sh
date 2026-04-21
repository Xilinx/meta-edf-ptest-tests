#!/bin/bash

set -e

VERSION="${1:-25.11}"

echo "Restarting Docker service..."
systemctl restart docker

echo "Checking Docker status..."
systemctl is-active --quiet docker || {
    echo "FAIL: Docker service is not running"
    exit 1
}

echo "Running hello-world image..."
docker run -it xilinx/edf:hello-world-${VERSION} && echo "PASS: hello-world container ran successfully" || echo "FAIL: hello-world container failed"

echo "Pulling devtools image..."
docker pull xilinx/edf:devtools-${VERSION} && echo "PASS: devtools image pulled successfully" || echo "FAIL: devtools image pull failed"

echo "Running devtools container..."
docker run -it xilinx/edf:devtools-${VERSION} bash -c "
echo 'Checking GCC version inside container...'
gcc --version && echo 'PASS: GCC version check successful' || echo 'FAIL: GCC version check failed'
" && echo "PASS: devtools container ran successfully" || echo "FAIL: devtools container failed"

# Local docker image testing
DEVTOOLS_FILE="${2:-/home/amd-edf/container-devtools-edf-amd-cortexa78-mali-common.rootfs.tar}"
if [ ! -f "$DEVTOOLS_FILE" ]; then
    echo "Devtools file not found. Copying from NFS..."
    mkdir -p /nfsroot
    mount -t nfs -o nolock,proto=tcp,port=2049 10.10.70.101:/exports/root /nfsroot
    cp -L /nfsroot/container-devtools-edf-amd-cortexa78-mali-common.rootfs.tar.bz2 /home/amd-edf
    echo "Unzipping Docker image..."
    bunzip2 /home/amd-edf/container-devtools-edf-amd-cortexa78-mali-common.rootfs.tar.bz2
else
    echo "Devtools file already available at $DEVTOOLS_FILE"
fi
echo "Importing Docker image..."
IMAGE_ID=$(docker import /home/amd-edf/container-devtools-edf-amd-cortexa78-mali-common.rootfs.tar)
docker run -it $IMAGE_ID  bash -c "
echo 'Checking GCC version inside local container...'
gcc --version && echo 'PASS: GCC version check successful' || echo 'FAIL: GCC version check failed'
" && echo "PASS: local container ran successfully" || echo "FAIL: local container failed"


echo "All Docker tests completed."
