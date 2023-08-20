# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# TODO consider switching this to a yaml file and only assemble V_PYPDFIUM2 in the library?
# advantages: denotes this is a static data file, easier r/w, accessibility in conda recipe via load_data_file()

__all__ = ("V_PYPDFIUM2", "V_LIBPDFIUM", "V_BUILDNAME", "V_PDFIUM_IS_V8")

V_MAJOR = 4
V_MINOR = 18
V_PATCH = 0
V_BETA = None

#: pypdfium2 version string
V_PYPDFIUM2 = f"{V_MAJOR}.{V_MINOR}.{V_PATCH}"
if V_BETA is not None:
    V_PYPDFIUM2 += f"b{V_BETA}"

#: PDFium library version string (git tag or commit hash)
V_LIBPDFIUM = "5868"

#: String describing the included PDFium binary's origin (pdfium-binaries, source)
V_BUILDNAME = "pdfium-binaries"

# TODO consider changing to V_IS_V8XFA: bool or V_BUILDTYPE: str ?
#: Whether the included PDFium binary was built with V8 support or not
V_PDFIUM_IS_V8 = False
