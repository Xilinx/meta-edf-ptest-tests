SUMMARY = "EDF ptest sanity coverage package group"
LICENSE = "CLOSED"

inherit packagegroup

RDEPENDS:${PN} = "\
    urvf-dma-basic-test \
    urvf-ethernet-connectivity-test  \
    urvf-spi-basic-test \
    urvf-image-mgmt-image-update-test \
    urvf-image-mgmt-configure-ufs-test \
    urvf-gpio-basic-test \
    urvf-i2c-basic-test \
    urvf-kernel-module-development-test \
    urvf-rtc-basic-test \
    urvf-sd-basic-test \
    urvf-spi-jffs2-test \
    urvf-uart-basic-test \
    ptest-runner \
    ptestlib \
    urvf-wdt-basic-test \
    urvf-can-basic-test \
    urvf-usb-basic-test \
    urvf-memory-basic-test \
"
