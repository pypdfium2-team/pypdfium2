.. SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
.. SPDX-License-Identifier: CC-BY-4.0

Python API
==========

.. warning::
    PDFium is not thread-safe. If you need to parallelise time-consuming PDFium tasks, use processes instead of threads.

.. TODO add some note about object finalization / memory management


Version
*******
.. automodule:: pypdfium2.version

Document
********
.. automodule:: pypdfium2._helpers.document

Page
****
.. automodule:: pypdfium2._helpers.page

Page Object
***********
.. automodule:: pypdfium2._helpers.pageobject
   :show-inheritance:

Text Page
*********
.. automodule:: pypdfium2._helpers.textpage

Bitmap
******
.. automodule:: pypdfium2._helpers.bitmap

Matrix
******
.. automodule:: pypdfium2._helpers.matrix

Miscellaneous
*************
.. automodule:: pypdfium2._helpers.misc
