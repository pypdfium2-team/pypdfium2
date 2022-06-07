.. SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
.. SPDX-License-Identifier: CC-BY-4.0

Python API
==========

.. Warning::
    * PDFium is not thread-safe. If you need to parallelise tasks, use processes instead of threads.
    * Attempting to work with an object after it has been closed will result in a segmentation fault.

Version
*******
.. automodule:: pypdfium2.version

Document
********
.. automodule:: pypdfium2._helpers.document
    :special-members: __len__
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

.. function:: pypdfium2.FPDF_LoadDocument
.. function:: pypdfium2.FPDF_LoadMemDocument
.. function:: pypdfium2.FPDF_LoadCustomDocument
.. class:: pypdfium2.FPDF_DOCUMENT
.. class:: pypdfium2.FPDF_PAGE
.. class:: pypdfium2.FPDF_TEXTPAGE
.. class:: pypdfium2.FPDF_FONT
.. data:: pypdfium2.FPDF_FONT_TYPE1
.. data:: pypdfium2.FPDF_FONT_TRUETYPE
