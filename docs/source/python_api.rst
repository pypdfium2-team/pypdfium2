.. SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
.. SPDX-License-Identifier: CC-BY-4.0

Python API
==========

.. important::
   API documentation reflects the version of pypdfium2 it was built with.
   Version information on changes and additions may or may not be present,
   meaning this document cannot generally be used to deduce compatibility with an older release.


Preface
*******

API layers
----------

pypdfium2 provides multiple API layers:

* The raw PDFium API, to be used with :mod:`ctypes` (namespace ``pypdfium2.raw``).
* The support model API, which is a nice set of Python helper classes around the raw API (namespace ``pypdfium2``).
* The internal API, which contains various lower-level, semi-private utilities that aid with using the raw API. (``pypdfium2.internal``).

Note that the ``raw`` namespace is filtered and wraps pdfium functions with a mutex (see below).
If this is not desired, you may use ``raw_unsafe`` for the original, unaltered bindings file.

All wrapper objects provide a ``raw`` attribute to access the underlying ctypes object.
In addition, helpers automatically resolve to raw if used as C function parameter. [#ctypes_param_hook]_
This allows you to conveniently use helpers where available, while the raw API can still be accessed as necessary.

The raw API is quite stable and provides a high level of backwards compatibility (seeing as PDFium is
well-tested and relied on by popular projects), but it can be difficult to use, and special care needs
to be taken about memory management.

The support model wraps raw pdfium functions in pythonic APIs that do not require knowledge of ctypes.
They conveniently handle memory management, string transfer, error checks, and more.
On the other hand, helpers only cover a small portion of raw pdfium and are less mature.
Existing APIs may still receive backwards incompatible changes, though we strive to contain them within major releases.

.. [#ctypes_param_hook] Implemented via ctypes hook `_as_parameter_ <https://docs.python.org/3/library/ctypes.html#calling-functions-with-your-own-custom-data-types>`_


Memory management
-----------------

.. Information on PDFium's behavior: https://groups.google.com/g/pdfium/c/7qLFskabmnk/m/xQEnXiG5BgAJ
.. Limitations of weakref: https://stackoverflow.com/q/52648418/15547292/#comment131514594_58243606

.. note::
   This section covers the support model, which does a lot of protective handling around raw pdfium close functions.
   It is not applicable to the raw API itself!

PDFium objects commonly need to be closed by the caller to release allocated memory. [#ac_obj_ownership]_
Where necessary, pypdfium2's helper classes implement automatic closing on garbage collection using :class:`weakref.finalize`. Additionally, they provide ``close()`` methods that can be used to release memory explicitly.

It may be advantageous to close objects explicitly instead of relying on Python garbage collection behavior, to release allocated memory and acquired file handles immediately. [#ac_obj_opaqueness]_

Closed objects must not be accessed anymore.
Closing an object sets the underlying ``raw`` attribute to None, which should ideally prevent illegal calls on closed raw handles, though.
Attempts to re-close an already closed object are silently ignored.
Closing a parent object will automatically close any open children (e.g. pages derived from a pdf).

Note that you must not use a raw object after it was closed (explicitly or on garbage collection of the wrapper), otherwise you have a use after free scenario.
Due to the design of :mod:`weakref`, finalizers can only be attached to wrapper objects, although they would logically belong to the raw objects.

.. [#ac_obj_ownership] Only objects owned by the caller of PDFium need to be closed. For instance, page objects that belong to a page are automatically freed by PDFium, while the caller is responsible for loose page objects.

.. [#ac_obj_opaqueness] Python does not know how many resources an opaque C object might bind.


Thread incompatibility
----------------------

PDFium is not thread-compatible, meaning that one must not use multiple pdfium functions simultaneously from different threads.

However, pypdfium2 wraps pdfium functions with a mutex to ensure only a single pdfium call can run at a time.
This makes it safe for use in a threaded context, but threading pdfium calls themselves does not provide any performance advantage.


Version
*******
.. automodule:: pypdfium2.version

CLI Entrypoint
**************
.. autofunction:: pypdfium2.main

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


Internal
********

.. warning::
   The following helpers are considered internal, so their API may change any time.
   They are isolated in an own namespace (``pypdfium2.internal``).

.. automodule:: pypdfium2.internal.consts
.. automodule:: pypdfium2.internal.bases
.. automodule:: pypdfium2.internal.utils
