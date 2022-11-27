# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import atexit
import logging
from pypdfium2.version import *
from pypdfium2._helpers import *
from pypdfium2 import raw

logger = logging.getLogger(__name__)  # FIXME perhaps unnecessary?

# Note: PDFium developers plan changes to the initialisation API (see https://crbug.com/pdfium/1446)
raw.FPDF_InitLibrary()
atexit.register(raw.FPDF_DestroyLibrary)
