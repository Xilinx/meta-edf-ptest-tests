SUMMARY = "PL-GPIO basic test"
LICENSE = "CLOSED"

SRC_URI = "file://ptest/test_pl-gpio.py \
           file://ptest/run-ptest"

S = "${UNPACKDIR}"

inherit ptest

ALLOW_EMPTY:${PN} = "1"

do_install_ptest() {
    install -d ${D}${PTEST_PATH}
    install -m 0755 ${UNPACKDIR}/ptest/run-ptest ${D}${PTEST_PATH}
    install -m 0755 ${UNPACKDIR}/ptest/test_pl-gpio.py ${D}${PTEST_PATH}
}

PACKAGE_ARCH = "all"
