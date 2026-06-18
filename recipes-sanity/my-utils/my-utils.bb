SUMMARY = "My custom utility"
LICENSE = "CLOSED"

SRC_URI = "file://my-tool.c \
           file://ptest/run-ptest"

S = "${UNPACKDIR}"

inherit ptest

do_compile() {
    ${CC} ${CFLAGS} ${LDFLAGS} my-tool.c -o my-tool
}

do_install() {
    install -d ${D}${bindir}
    install -m 0755 my-tool ${D}${bindir}
}


do_install_ptest() {
    install -d ${D}${PTEST_PATH}
    install -m 0755 ${UNPACKDIR}/ptest/run-ptest ${D}${PTEST_PATH}
}



