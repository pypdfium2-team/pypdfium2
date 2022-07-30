# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import atexit
import logging
from pypdfium2._namespace import *

logger = logging.getLogger(__name__)

# Apparently, upstream has plans to deprecate FPDF_InitLibrary(), and asks callers to transition to FPDF_InitLibraryWithConfig().
# However, we don't need any of the configuration options, so it would be more convenient for us to stick with FPDF_InitLibrary().
FPDF_InitLibrary()
atexit.register(FPDF_DestroyLibrary)
