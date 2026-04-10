SUMMARY = "Ethernet connectivity test"
LICENSE = "CLOSED"

SRC_URI = "file://ptest/test_ethernet.py \
           file://ptest/run-ptest"

S = "${WORKDIR}"

inherit ptest

ALLOW_EMPTY:${PN} = "1"

do_install_ptest() {
    install -d ${D}${PTEST_PATH}
    install -m 0755 ${WORKDIR}/ptest/run-ptest ${D}${PTEST_PATH}
    install -m 0755 ${WORKDIR}/ptest/test_ethernet.py ${D}${PTEST_PATH}
}

