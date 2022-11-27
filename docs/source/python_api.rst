.. SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
.. SPDX-License-Identifier: CC-BY-4.0

Python API
==========


Preface
*******

API layers
----------

pypdfium2 offers two API layers:

* The raw PDFium API, to be used with :mod:`ctypes` (namespace ``pypdfium2.raw``).
* The support model API, which is a nice set of Python helper classes around the raw API (namespace ``pypdfium2``).

All wrapper objects provide a ``raw`` attribute to access the underlying ctypes object.
This allows you to use helpers where available, while the raw API can still be accessed where necessary.

The raw API is quite stable and provides a high level of backwards compatibility (seeing as PDFium is
well-tested and relied on by popular projects), but it can be difficult to use, and special care needs
to be taken about memory management.

The support model API is still in development. Backwards incompatible changes may be applied occasionally,
though they are usually limited to major releases. On the other hand, it is considerably easier to use,
and the consequences of usage mistakes are generally less serious.


Memory management
-----------------

.. Information on PDFium's behaviour: https://groups.google.com/g/pdfium/c/7qLFskabmnk/m/xQEnXiG5BgAJ
.. Limitations of weakref: https://stackoverflow.com/q/52648418/15547292/#comment131514594_58243606

PDFium objects commonly need to be closed by the caller to release allocated memory. [#ac_obj_ownership]_
Where necessary, pypdfium2's helper classes implement automatic closing on garbage collection using :class:`weakref.finalize`. Additionally, they provide ``close()`` methods that can be used to release memory explicitly.

It may be advantageous to close objects explicitly instead of relying on Python garbage collection behaviour, to release allocated memory and acquired file handles immediately. [#ac_obj_opaqueness]_
In this case, note that objects must be closed in reverse order to loading (i. e. parent objects must never be closed before child objects), and that closed objects must not be accessed anymore. [#ac_mixed_closing]_

If the order of closing is violated, pypdfium2 issues a warning, but still makes an unsafe attempt to close the child object.
``close()`` methods should be called only once. Excessive close calls are skipped with a warning.
Moreover, closing an object sets the underlying ``raw`` attribute to None, which should ideally turn illegal function calls after ``close()`` into a no-op.

It is important to note that raw objects must never be isolated from their wrappers. Continuing to use a raw object after its wrapper has been closed or garbage collected is bound to result in a use after free scenario.
Due to limitations in :mod:`weakref`, finalizers can only be attached to wrapper objects, although they would logically belong to the raw objects.

.. [#ac_obj_ownership] Only objects owned by the caller of PDFium need to be closed. For instance, page objects that belong to a page are automatically freed by PDFium, while the caller is responsible for loose page objects.

.. [#ac_obj_opaqueness] Python does not know how many resources an opaque C object might bind.

.. [#ac_mixed_closing] Consequentally, if closing an object explicitly, all child objects must be closed explicitly as well. Otherwise, they may not have been garbage collected and finalized before the explicit close call on the parent object, resulting in an illicit order of closing.


Thread incompatibility
----------------------

PDFium is not thread-compatible. If you need to parallelise tasks, use processes instead of threads.


Version
*******
.. automodule:: pypdfium2.version

Document
********
.. automodule:: pypdfium2._helpers.document

Page
****
.. automodule:: pypdfium2._helpers.page

Page Objects
************
.. automodule:: pypdfium2._helpers.pageobjects

Text Page
*********
.. automodule:: pypdfium2._helpers.textpage

Bitmap
******
.. automodule:: pypdfium2._helpers.bitmap

Matrix
******
.. automodule:: pypdfium2._helpers.matrix

Attachment
**********
.. automodule:: pypdfium2._helpers.attachment

Miscellaneous
*************
.. automodule:: pypdfium2._helpers.misc
.. automodule:: pypdfium2._helpers.unsupported
