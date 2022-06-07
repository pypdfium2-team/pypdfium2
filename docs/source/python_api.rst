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
