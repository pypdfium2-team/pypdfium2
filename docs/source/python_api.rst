.. SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
.. SPDX-License-Identifier: CC-BY-4.0

Python API
==========

.. Warning::
    * PDFium is not thread-safe. If you need to parallelise time-consuming PDFium tasks, use processes instead of threads.
    * Calling ``close()`` makes objects inoperable, so you should not access them anymore afterwards.

Version
*******
.. automodule:: pypdfium2.version

Document
********
.. automodule:: pypdfium2._helpers.document
    :show-inheritance:

Page
****
.. automodule:: pypdfium2._helpers.page
    :show-inheritance:

Converters
**********
.. automodule:: pypdfium2._helpers.converters
    :show-inheritance:

Text Page
*********
.. automodule:: pypdfium2._helpers.textpage

Miscellaneous
*************
.. automodule:: pypdfium2._helpers.misc
