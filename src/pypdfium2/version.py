# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

__all__ = ["V_PYPDFIUM2", "V_LIBPDFIUM", "V_BUILDNAME"]

V_MAJOR = 4
V_MINOR = 0
V_PATCH = 0
V_BETA = 2

#: pypdfium2 version string.
V_PYPDFIUM2 = "%s.%s.%s" % (V_MAJOR, V_MINOR, V_PATCH)
if V_BETA is not None:
    V_PYPDFIUM2 += "b%s" % V_BETA

#: PDFium library version string (git tag or commit hash).
V_LIBPDFIUM = "5579"

#: String describing the included PDFium binary's origin (pdfium-binaries, sourcebuild)
V_BUILDNAME = "pdfium-binaries"
