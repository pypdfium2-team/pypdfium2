.. SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
.. SPDX-License-Identifier: CC-BY-4.0

Python API
==========

.. Warning::
    * PDFium is not thread-safe. If you need to parallelise tasks, use processes instead of threads.
    * Attempting to work with an object after it has been closed will result in a segmentation fault.
    * Not calling the ``close()`` methods as required may lead to memory leaks.

Version
*******
.. automodule:: pypdfium2.version

Document
********
.. automodule:: pypdfium2._helpers.document
    :private-members: _render_base

Page
****
.. automodule:: pypdfium2._helpers.page

Text Page
*********
.. automodule:: pypdfium2._helpers.textpage

Miscellaneous
*************
.. automodule:: pypdfium2._helpers.misc

PDFium
******

This is an assortment of PDFium members referenced in this documentation.

.. function:: FPDF_LoadDocument
.. function:: FPDF_LoadMemDocument64
.. function:: FPDF_LoadCustomDocument
.. function:: FPDF_GetLastError
.. class:: FPDF_DOCUMENT
.. class:: FPDF_PAGE
.. class:: FPDF_TEXTPAGE
.. class:: FPDF_SCHHANDLE
.. class:: FPDF_FONT
.. data:: FPDF_FONT_TYPE1
.. data:: FPDF_FONT_TRUETYPE
