SUMMARY = "Shared Python utilities and reporting for EDF ptests"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://lib.py;beginline=1;endline=19;md5=e8f4b2dfa613d86e9d3e1acda2d66ee4"

SRC_URI += "file://lib.py"
SRC_URI += "file://logger.py"
SRC_URI += "file://edf_utiles.py"
SRC_URI += "file://urvf_reporter.py"

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


FILES:${PN} += " \
${PYTHON_SITEPACKAGES_DIR}/ptestlib \
${bindir}/urvf_reporter.py \
"

RDEPENDS:${PN} += "python3-pexpect"

PACKAGE_ARCH = "all"
