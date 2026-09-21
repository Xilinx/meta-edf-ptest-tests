SUMMARY = "EDF ptest sanity coverage package group"
LICENSE = "CLOSED"

inherit packagegroup

RDEPENDS:${PN} = "\
    dma-basic-test \
    ethernet-connectivity-test  \
    spi-basic-test \
    image-mgmt-image-update-test \
    image-mgmt-configure-ufs-test \
    gpio-basic-test \
    i2c-basic-test \
    urvf-kernel-module-development-test \
    rtc-basic-test \
    sd-basic-test \
    spi-jffs2-test \
    uart-basic-test \
    ptest-runner \
    ptestlib \
    wdt-basic-test \
    can-basic-test \
    usb-basic-test \
"
