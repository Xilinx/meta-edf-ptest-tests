SUMMARY = "HDMI 2.1 XFMC out-of-tree kernel module"
DESCRIPTION = "Out-of-tree kernel module build used to validate the kernel module \
               development flow for HDMI 2.1 FMC hardware."
LICENSE = "GPL-2.0-only"
LIC_FILES_CHKSUM = "file://LICENSE.md;md5=eb723b61539feef013de476e68b5c50a"

inherit module

# AUTOREV until this is pinned to a specific commit for reproducible regression builds
SRC_URI = "git://github.com/Xilinx/hdmi21-modules.git;protocol=https;branch=master"
SRCREV = "${AUTOREV}"

EXTRA_OEMAKE += "KERNEL_SRC=${STAGING_KERNEL_DIR}"
