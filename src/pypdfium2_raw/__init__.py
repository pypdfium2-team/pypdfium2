# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import platform  #, sys

# (Free)BSD libreoffice-pdfium workaround: make implicit dependency libraries available for symbol resolution
if platform.system().lower().endswith("bsd"):  # pragma: no cover
    from pypdfium2_raw.version import PDFIUM_INFO
    if PDFIUM_INFO.origin == "system-libreoffice":
        import ctypes
        _absl = ctypes.CDLL("/usr/local/lib/libabsl_strings.so", mode=ctypes.RTLD_GLOBAL)
        _openjp2 = ctypes.CDLL("/usr/local/lib/libopenjp2.so", mode=ctypes.RTLD_GLOBAL)

# bindings.py and accompanying platform files are generated and emplaced automatically using pypdfium2 setup tooling - see autorelease/bindings.py for a tracked sample
from pypdfium2_raw.bindings import *
