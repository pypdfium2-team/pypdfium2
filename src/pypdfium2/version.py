# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

__all__ = ["V_PYPDFIUM2", "V_LIBPDFIUM", "IS_SOURCEBUILD"]

V_MAJOR = 3
V_MINOR = 13
V_PATCH = 0
V_BETA = None

#: pypdfium2 version string.
V_PYPDFIUM2 = "%s.%s.%s" % (V_MAJOR, V_MINOR, V_PATCH)
if V_BETA is not None:
    V_PYPDFIUM2 += "b%s" % V_BETA

#: PDFium library version string (git tag or commit hash).
V_LIBPDFIUM = "5473"

#: Whether the included PDFium binary was built from source locally (:data:`True`) or downloaded from pdfium-binaries (:data:`False`).
IS_SOURCEBUILD = False
