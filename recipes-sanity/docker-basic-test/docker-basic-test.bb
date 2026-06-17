SUMMARY = "Docker test for devtool and hello world"
LICENSE = "CLOSED"

SRC_URI = "file://ptest/docker_test.sh \
           file://ptest/run-ptest"

S = "${UNPACKDIR}"

inherit ptest

ALLOW_EMPTY:${PN} = "1"

do_install_ptest() {
    install -d ${D}${PTEST_PATH}
    install -m 0755 ${UNPACKDIR}/ptest/run-ptest ${D}${PTEST_PATH}
    install -m 0755 ${UNPACKDIR}/ptest/docker_test.sh ${D}${PTEST_PATH}
}

PACKAGE_ARCH = "all"
RDEPENDS:${PN}-ptest += "bash"