SUMMARY = "EDF ptest sanity coverage package group"
LICENSE = "CLOSED"

inherit packagegroup

RDEPENDS:${PN} = "\
    dfx-basic-test \
    docker-basic-test \
    rpm-basic-test \
    dma-basic-test \
    ethernet-connectivity-test  \
    spi-basic-test \
    gpio-bram-test \
    ptest-runner \
"

