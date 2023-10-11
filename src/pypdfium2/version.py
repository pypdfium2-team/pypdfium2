# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# TODO namespace cleanup: group pypdfium2 and pdfium info in classes

__all__ = ("V_PYPDFIUM2", "V_LIBPDFIUM", "V_LIBPDFIUM_FULL", "V_BUILDNAME", "V_PDFIUM_IS_V8")

V_MAJOR = 4
V_MINOR = 21
V_PATCH = 0
V_BETA = None

#: str: pypdfium2 version
V_PYPDFIUM2 = f"{V_MAJOR}.{V_MINOR}.{V_PATCH}"
if V_BETA is not None:
    V_PYPDFIUM2 += f"b{V_BETA}"

#: str: Short pdfium version (git tag, commit hash or "unknown").
V_LIBPDFIUM = "6056"

#: str: Full pdfium version (in Chromium version scheme). Unset/empty if pdfium was built from source through pypdfium2's build script.
V_LIBPDFIUM_FULL = "120.0.6056.0"

#: str: The pdfium binary's origin (pdfium-binaries, source, unknown).
V_BUILDNAME = "pdfium-binaries"

# TODO consider renaming to V_IS_V8XFA or something
#: bool: Whether the pdfium binary was built with V8 support or not.
V_PDFIUM_IS_V8 = False
