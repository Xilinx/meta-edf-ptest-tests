SUMMARY = "SPI flash read and speed ptest"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://ptest/run-ptest;beginline=2;endline=20;md5=e8f4b2dfa613d86e9d3e1acda2d66ee4"

SRC_URI = "file://ptest/spi_test.py \
           file://ptest/run-ptest"

inherit ptest


S = "${UNPACKDIR}"


ALLOW_EMPTY:${PN} = "1"

do_install_ptest() {
    install -d ${D}${PTEST_PATH}
    install -m 0755 ${UNPACKDIR}/ptest/run-ptest ${D}${PTEST_PATH}
    install -m 0755 ${UNPACKDIR}/ptest/spi_test.py ${D}${PTEST_PATH}
}

PACKAGE_ARCH = "all"
