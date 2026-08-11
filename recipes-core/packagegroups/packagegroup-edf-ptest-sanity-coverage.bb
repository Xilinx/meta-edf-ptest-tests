SUMMARY = "EDF ptest sanity coverage package group"
LICENSE = "CLOSED"

inherit packagegroup

RDEPENDS:${PN} = "\
    dma-basic-test \
    ethernet-connectivity-test  \
    spi-basic-test \
    update-bootbin-test \
    configure-ufs-test \
    ptest-runner \
    ptestlib \
"