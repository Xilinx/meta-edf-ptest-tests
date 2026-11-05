SUMMARY = "CAN interface and loopback validation ptest"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://ptest/run-ptest;beginline=2;endline=20;md5=e8f4b2dfa613d86e9d3e1acda2d66ee4"

SRC_URI = "file://ptest/test_can.py \
           file://ptest/run-ptest"

S = "${UNPACKDIR}"

inherit ptest

ALLOW_EMPTY:${PN} = "1"

do_install_ptest() {
    install -d ${D}${PTEST_PATH}
    install -m 0755 ${UNPACKDIR}/ptest/run-ptest ${D}${PTEST_PATH}
    install -m 0755 ${UNPACKDIR}/ptest/test_can.py ${D}${PTEST_PATH}
}

PACKAGE_ARCH = "all"
