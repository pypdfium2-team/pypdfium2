.. SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
.. SPDX-License-Identifier: CC-BY-4.0

Python API
==========

.. warning::
    PDFium is not thread-safe. If you need to parallelise time-consuming PDFium tasks, use processes instead of threads.

.. note::
    
    * Calling an object's ``close()`` method ...
      
      * will free memory by applying its finalizer (which calls a PDFium function on the underlying ``raw`` object).
      * makes the object in question inoperable by setting its ``raw`` attribute to :data:`None`.
    
    * Since version 3.3, objects are closed automatically on garbage collection via :class:`weakref.finalize`, so it is not necessary to call ``close()`` manually anymore. If ``close()`` methods are called explicitly, note that objects must be closed in reverse order to loading.
    
    .. see also https://groups.google.com/g/pdfium/c/7qLFskabmnk/m/xQEnXiG5BgAJ


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

Text Page
*********
.. automodule:: pypdfium2._helpers.textpage

Matrix
******
.. automodule:: pypdfium2._helpers.matrix

Converters
**********
.. automodule:: pypdfium2._helpers.converters

Miscellaneous
*************
.. automodule:: pypdfium2._helpers.misc
