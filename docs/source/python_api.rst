.. SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
.. SPDX-License-Identifier: CC-BY-4.0

Python API
==========

.. Warning::
    * PDFium is not safe for thread-based parallelisation, in the sense that multiple PDFium calls must never happen simultaneously in different threads.
      If you need to paralellise time-consuming PDFium tasks, please use processes instead of threads.
    * Attempting to work with an object after it has been closed will result in a segmentation fault.
    * Not calling the ``close()`` methods as required may lead to memory leaks.

Version
*******
.. automodule:: pypdfium2.version

Converters
**********
.. automodule:: pypdfium2._helpers.converters
    :show-inheritance:

Document
********
.. automodule:: pypdfium2._helpers.document
    :show-inheritance:

Page
****
.. automodule:: pypdfium2._helpers.page
    :show-inheritance:

Text Page
*********
.. automodule:: pypdfium2._helpers.textpage

Miscellaneous
*************
.. automodule:: pypdfium2._helpers.misc
