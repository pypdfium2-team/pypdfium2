# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# full support model namespace

from pypdfium2._helpers.misc import *
from pypdfium2._helpers.converters import *
from pypdfium2._helpers.document import *
from pypdfium2._helpers.page import *
from pypdfium2._helpers.textpage import *


# Notes on automatic closing of objects (concerns PdfDocument, PdfPage, PdfTextPage, PdfTextSearcher):
# pypdfium2 implements __del__ finaliser methods that are run by Python once it has identified an object as garbage and is about to remove it.
# However, objects must be closed in correct order. It is illegal to close a subordinate object if any of its superordinate objects has been closed already.
# If Python garbage collects multiple objects in one cycle, it may finalise them in arbitrary order.
# Therefore, we implement checks to only call PDFium close functions if all superordinate objects are still open.
