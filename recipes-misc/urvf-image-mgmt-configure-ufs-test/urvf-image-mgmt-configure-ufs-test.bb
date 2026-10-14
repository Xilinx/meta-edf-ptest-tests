SUMMARY = "Image mgmt configure UFS test"
LICENSE = "CLOSED"

SRC_URI = "file://ptest/configure_ufs_test.py \
           file://ptest/run-ptest \
           file://ptest/ufs_config.json"

S = "${UNPACKDIR}"

inherit ptest

ALLOW_EMPTY:${PN} = "1"

do_install_ptest() {
    install -d ${D}${PTEST_PATH}
    install -m 0755 ${UNPACKDIR}/ptest/run-ptest ${D}${PTEST_PATH}
    install -m 0755 ${UNPACKDIR}/ptest/configure_ufs_test.py ${D}${PTEST_PATH}
    install -m 0644 ${UNPACKDIR}/ptest/ufs_config.json ${D}${PTEST_PATH}
}

PACKAGE_ARCH = "all"
