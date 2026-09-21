SUMMARY = "Spi read and speed test"
LICENSE = "CLOSED"

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
