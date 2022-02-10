# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import logging
import pypdfium2 as pdfium
from pypdfium2._cli.toc import print_toc
from .conftest import TestFiles


def test_read_toc():
    
    with pdfium.PdfContext(TestFiles.bookmarks) as pdf:
        toc = pdfium.get_toc(pdf)
        print()
        print_toc(toc)


def test_read_toc_circular(caplog):
    with caplog.at_level(logging.CRITICAL):
        with pdfium.PdfContext(TestFiles.bookmarks_circular) as pdf:
            toc = pdfium.get_toc(pdf)
            print_toc(toc)
            assert "circular bookmark reference" in caplog.text
