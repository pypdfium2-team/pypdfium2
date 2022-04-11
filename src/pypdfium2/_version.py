# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

V_MAJOR = 1
V_MINOR = 4
V_PATCH = 0
V_BETA = None

V_PYPDFIUM2 = "%s.%s.%s" % (V_MAJOR, V_MINOR, V_PATCH)  #: pypdfium2 version string
if V_BETA is not None:
    V_PYPDFIUM2 += "b%s" % V_BETA

V_LIBPDFIUM = 4997  #: PDFium library version integer (git tag)
