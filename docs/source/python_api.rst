.. SPDX-FileCopyrightText: 2024 geisserml <geisserml@gmail.com>
.. SPDX-License-Identifier: CC-BY-4.0

Python API
==========


Preface
*******

Thread incompatibility
----------------------

PDFium is not thread-safe. It is not allowed to call pdfium functions simultaneously across different threads, not even with different documents. [#illegal_threading]_
However, you may still use pdfium in a threaded context if it is ensured that only a single pdfium call can be made at a time (e.g. via mutex).
It is fine to do pdfium work in one thread and other work in other threads.

The same applies to pypdfium2's helpers, or any wrapper calling pdfium, whether directly or indirectly, unless protected by mutex.

To parallelize expensive pdfium tasks such as rendering, consider processes instead of threads.

.. [#illegal_threading] Doing so would crash or corrupt the process.

API layers
----------

pypdfium2 provides multiple API layers:

* The raw PDFium API, to be used with :mod:`ctypes` (``pypdfium2.raw`` or ``pypdfium2_raw`` [#raw_model]_).
* The support model API, which is a set of Python helper classes around the raw API (``pypdfium2``).
* Additionally, there is the internal API, which contains various utilities that aid with using the raw API and are accessed by helpers, but do not fit in the support model namespace itself (``pypdfium2.internal``).

Wrapper objects provide a ``raw`` attribute to access the underlying ctypes object.
In addition, helpers automatically resolve to raw if used as C function parameter. [#ctypes_param_hook]_
This allows to conveniently use helpers where available, while the raw API can still be accessed as needed.

The raw API is quite stable and provides a high level of backwards compatibility (seeing as PDFium is well-tested and relied on by popular projects), but it can be difficult to use, and special care needs to be taken with memory management.

The support model API is still in beta stage. It only covers a subset of pdfium features. Backwards incompatible changes may be applied occasionally, although we try to contain them within major releases. On the other hand, it is supposed to be safer and easier to use ("pythonic"), abstracting the finnicky interaction with C functions.

.. [#raw_model] The latter does not automatically initialize pdfium on import.
.. [#ctypes_param_hook] Implemented via ctypes hook `_as_parameter_ <https://docs.python.org/3/library/ctypes.html#calling-functions-with-your-own-custom-data-types>`_


Memory management
-----------------

.. Info on PDFium's close functions: https://groups.google.com/g/pdfium/c/7qLFskabmnk/m/xQEnXiG5BgAJ
.. weakref limitations: https://stackoverflow.com/q/52648418/15547292/#comment131514594_58243606

.. note::
   This section covers the support model. It is not applicable to the raw API alone!

PDFium objects commonly need to be closed by the caller to release allocated memory. [#ac_obj_ownership]_
Where necessary, pypdfium2's helper classes implement automatic closing on garbage collection using :class:`weakref.finalize`. Additionally, they provide ``close()`` methods that can be used to release memory explicitly.

It may be advantageous to close objects explicitly instead of relying on Python garbage collection behaviour, to release allocated memory and acquired file handles immediately. [#ac_obj_opaqueness]_

Closed objects must not be accessed anymore.
Closing an object sets the underlying ``raw`` attribute to None, which should prevent illegal use of closed raw handles, though.
Attempts to re-close an already closed object are silently ignored.
Closing a parent object will automatically close any open children (e.g. pages derived from a pdf).

Raw objects must not be detached from their wrappers. Accessing a raw object after it was closed, whether explicitly or on garbage collection of the wrapper, is illegal (use after free).
Due to limitations in :mod:`weakref`, finalizers can only be attached to wrapper objects, although they logically belong to the raw object.

.. [#ac_obj_ownership] Only objects owned by the caller of PDFium need to be closed. For instance, pageobjects that belong to a page are automatically freed by PDFium, while the caller is responsible for loose pageobjects.

.. [#ac_obj_opaqueness] Python does not know how many resources an opaque C object might bind.


Version
*******
.. note::
   Version info can be fooled. See it as orientation rather than inherently reliable data.

.. automodule:: pypdfium2.version

Document
********
.. automodule:: pypdfium2._helpers.document

Page
****
.. automodule:: pypdfium2._helpers.page

Pageobjects
***********
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


Internal
********

.. warning::
   The following helpers are considered internal, so their API may change any time.
   They are isolated in an own namespace (``pypdfium2.internal``).

.. automodule:: pypdfium2.internal.consts
.. automodule:: pypdfium2.internal.bases
.. automodule:: pypdfium2.internal.utils
