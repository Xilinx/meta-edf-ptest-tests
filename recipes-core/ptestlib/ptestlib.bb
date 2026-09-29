SUMMARY = "EDF ptest sanity coverage package group"
LICENSE = "CLOSED"

SRC_URI += "file://lib.py"
SRC_URI += "file://logger.py"
SRC_URI += "file://edf_utiles.py"
SRC_URI += "file://urvf_reporter.py"
SRC_URI += "file://pexpect"
SRC_URI += "file://ptyprocess"

S = "${UNPACKDIR}"

inherit python3native

do_install() {
    install -d ${D}${PYTHON_SITEPACKAGES_DIR}/ptestlib
    install -m 0644 ${UNPACKDIR}/lib.py ${D}${PYTHON_SITEPACKAGES_DIR}/ptestlib/
    install -m 0644 ${UNPACKDIR}/edf_utiles.py ${D}${PYTHON_SITEPACKAGES_DIR}/ptestlib/
    install -m 0644 ${UNPACKDIR}/logger.py ${D}${PYTHON_SITEPACKAGES_DIR}/ptestlib/
    install -m 0644 ${UNPACKDIR}/urvf_reporter.py ${D}${PYTHON_SITEPACKAGES_DIR}/ptestlib/
    install -d ${D}${bindir}
    install -m 0755 ${UNPACKDIR}/urvf_reporter.py ${D}${bindir}/urvf_reporter.py
    sed -i 's/\r//' ${D}${bindir}/urvf_reporter.py
}

do_install:append() {
install -d ${D}${PYTHON_SITEPACKAGES_DIR}/pexpect
cp -r ${UNPACKDIR}/pexpect ${D}${PYTHON_SITEPACKAGES_DIR}
install -d ${D}${PYTHON_SITEPACKAGES_DIR}/ptyprocess
cp -r ${UNPACKDIR}/ptyprocess ${D}${PYTHON_SITEPACKAGES_DIR}/

}

FILES:${PN} += " \
${PYTHON_SITEPACKAGES_DIR}/ptestlib \
${PYTHON_SITEPACKAGES_DIR}/pexpect \
${PYTHON_SITEPACKAGES_DIR}/ptyprocess \
${bindir}/urvf_reporter.py \
"