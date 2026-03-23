# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import platform  #, sys

# (Free)BSD libreoffice-pdfium workaround
# NOTE: alternatively, caller could manually do
#   export LD_PRELOAD="/usr/local/lib/libabsl_strings.so:/usr/local/lib/libopenjp2.so"
# on before using pypdfium2, and unset afterwards.
if platform.system().lower().endswith("bsd"):
    # print("BSD detected", file=sys.stderr)
    from pypdfium2_raw.version import PDFIUM_INFO
    if PDFIUM_INFO.origin == "system-libreoffice":
        # print("BSD libreoffice-pdfium workaround", file=sys.stderr)
        # [dlopen() manpage] RTLD_GLOBAL: The symbols defined by this shared object will be made available for symbol resolution of subsequently loaded shared objects.
        # [ctypes] On posix systems, RTLD_NOW is always added, and is not configurable.
        import ctypes
        _absl = ctypes.CDLL("/usr/local/lib/libabsl_strings.so", mode=ctypes.RTLD_GLOBAL)
        _openjp2 = ctypes.CDLL("/usr/local/lib/libopenjp2.so", mode=ctypes.RTLD_GLOBAL)

# bindings.py and accompanying platform files are generated and emplaced automatically using pypdfium2 setup tooling - see autorelease/bindings.py for a tracked sample
from pypdfium2_raw.bindings import *
