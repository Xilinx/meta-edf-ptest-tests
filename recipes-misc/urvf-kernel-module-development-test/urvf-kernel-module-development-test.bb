SUMMARY = "Kernel module development sanity test"
LICENSE = "CLOSED"

DEPENDS = "hdmi21-xfmc"

SRC_URI = "file://ptest/test_kernel_module_development.py \
           file://ptest/run-ptest"

S = "${UNPACKDIR}"

inherit ptest

ALLOW_EMPTY:${PN} = "1"

do_install_ptest() {
    install -d ${D}${PTEST_PATH}
    install -m 0755 ${UNPACKDIR}/ptest/run-ptest ${D}${PTEST_PATH}
    install -m 0755 ${UNPACKDIR}/ptest/test_kernel_module_development.py ${D}${PTEST_PATH}
}

RDEPENDS:${PN} += "kernel-module-hdmi21-xfmc"

