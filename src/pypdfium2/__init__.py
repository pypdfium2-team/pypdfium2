# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0

import atexit
import logging

from pypdfium2._logging import setup_logger

logger = logging.getLogger(__name__)
setup_logger(logger)

from pypdfium2 import _pypdfium as pdfium
from pypdfium2._constants import *
from pypdfium2._exceptions import *
from pypdfium2._helpers import *
from pypdfium2._version import V_LIBPDFIUM, V_PYPDFIUM2

__version__ = V_PYPDFIUM2
__pdfium_version__ = V_LIBPDFIUM

pdfium.FPDF_InitLibrary()


def exit_handler():
    pdfium.FPDF_DestroyLibrary()


atexit.register(exit_handler)
