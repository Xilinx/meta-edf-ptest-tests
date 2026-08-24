SUMMARY = "Image mgmt image update test"
LICENSE = "CLOSED"

SRC_URI = "file://ptest/image_update_test.py \
           file://ptest/run-ptest \
           file://ptest/versal-2ve-2vm-vek385-multidomain/boot.bin \
           file://ptest/versal-2ve-2vm-vek385-revb-multidomain/boot.bin \
           file://ptest/versal-vek280-multidomain/boot.bin \
           file://ptest/versal-vrk160-multidomain/boot.bin \
           file://ptest/versal-vrk165-multidomain/boot.bin"

S = "${UNPACKDIR}"

inherit ptest

ALLOW_EMPTY:${PN} = "1"

do_install_ptest() {
    install -d ${D}${PTEST_PATH}
    install -m 0755 ${UNPACKDIR}/ptest/run-ptest ${D}${PTEST_PATH}
    install -m 0755 ${UNPACKDIR}/ptest/image_update_test.py ${D}${PTEST_PATH}
    for machine in versal-2ve-2vm-vek385-multidomain \
                   versal-2ve-2vm-vek385-revb-multidomain \
                   versal-vek280-multidomain \
                   versal-vrk160-multidomain \
                   versal-vrk165-multidomain; do
        install -d ${D}${PTEST_PATH}/${machine}
        install -m 0644 ${UNPACKDIR}/ptest/${machine}/boot.bin ${D}${PTEST_PATH}/${machine}/boot.bin
    done
}

RDEPENDS:${PN}-ptest = "ptestlib"

PACKAGE_ARCH = "all"
