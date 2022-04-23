# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import atexit
import logging
from pypdfium2._namespace import *

logger = logging.getLogger(__name__)

FPDF_InitLibrary()
atexit.register(FPDF_DestroyLibrary)
