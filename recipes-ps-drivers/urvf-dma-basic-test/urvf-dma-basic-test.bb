SUMMARY = "Ethernet connectivity test"
LICENSE = "CLOSED"

inherit ptest


SRC_URI = "file://ptest/dma_test.py \
           file://ptest/run-ptest"

S = "${UNPACKDIR}"


ALLOW_EMPTY:${PN} = "1"

do_install_ptest() {
    install -d ${D}${PTEST_PATH}
    install -m 0755 ${UNPACKDIR}/ptest/run-ptest ${D}${PTEST_PATH}
    install -m 0755 ${UNPACKDIR}/ptest/dma_test.py ${D}${PTEST_PATH}
}

PACKAGE_ARCH = "all"
