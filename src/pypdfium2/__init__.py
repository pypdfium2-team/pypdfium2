# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import atexit
import logging
from pypdfium2 import _version
from pypdfium2._pypdfium import *
from pypdfium2._helpers.constants import *
from pypdfium2._helpers.error_handler import *
from pypdfium2._helpers.utilities import *
from pypdfium2._helpers.opener import *
from pypdfium2._helpers.page_renderer import *
from pypdfium2._helpers.pdf_renderer import *
from pypdfium2._helpers.toc import *
from pypdfium2._helpers.saver import *
from pypdfium2._helpers.boxes import *


logger = logging.getLogger(__name__)

__version__ = _version.V_PYPDFIUM2
__pdfium_version__ = _version.V_LIBPDFIUM


FPDF_InitLibrary()

def exit_handler():
    FPDF_DestroyLibrary()

atexit.register(exit_handler)
