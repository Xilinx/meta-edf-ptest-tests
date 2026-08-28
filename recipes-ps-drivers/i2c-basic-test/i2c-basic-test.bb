SUMMARY = "I2C read test"
LICENSE = "CLOSED"

SRC_URI = "file://ptest/test_i2c.py \
           file://ptest/run-ptest"

S = "${UNPACKDIR}"

inherit ptest


ALLOW_EMPTY:${PN} = "1"

do_install_ptest() {
    install -d ${D}${PTEST_PATH}
    install -m 0755 ${UNPACKDIR}/ptest/run-ptest ${D}${PTEST_PATH}
    install -m 0755 ${UNPACKDIR}/ptest/test_ethernet.py ${D}${PTEST_PATH}
}

PACKAGE_ARCH = "all"
