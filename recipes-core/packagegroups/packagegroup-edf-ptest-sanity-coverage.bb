SUMMARY = "EDF ptest sanity coverage package group"
LICENSE = "CLOSED"

inherit packagegroup

RDEPENDS:${PN} = "\
    dma-basic-test \
    ethernet-connectivity-test  \
    spi-basic-test \
    image-mgmt-image-update-test \
    image-mgmt-configure-ufs-test \
    ptest-runner \
    ptestlib \
"