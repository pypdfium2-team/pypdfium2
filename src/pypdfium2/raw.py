# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import threading

PdfiumMutex = threading.Lock()


def _get_members():
    
    import ctypes
    import fnmatch
    import functools
    from types import ModuleType
    import pypdfium2._raw_unsafe
    
    NAME_FILTERS = (
        (str.startswith, ("_", "struct_", "enum_")),
        (str.endswith, ("_t__", )),
        (str.__contains__, ("LibraryLoader", )),
        (fnmatch.fnmatchcase, ("uint*_t", "fpdf_*_t"))
        (str.__eq__, ("load_library", "UNCHECKED", "c_ptrdiff_t")),
    )
    
    def make_threadsafe(f):
        @functools.wraps(f)
        def pdfium_callable_threadsafe(*args, **kwargs):
            with PdfiumMutex:
                return f(*args, **kwargs)
        return pdfium_callable_threadsafe
    
    for name in dir(pypdfium2._raw_unsafe):
        
        member = getattr(pypdfium2._raw_unsafe, name)
        
        # try to mask the garbage exposed by ctypesgen, as far as possible
        if any(any(func(name, x) for x in skips) for func, skips in NAME_FILTERS):
            continue
        if isinstance(member, ModuleType) or hasattr(ctypes, name):
            continue
        
        if isinstance(member, ctypes._CFuncPtr):
            # make pdfium functions thread safe
            globals()[name] = make_threadsafe(member)
        else:
            globals()[name] = member


_get_members()
del threading, _get_members
