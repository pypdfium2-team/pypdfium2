# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# This code has 2 main purposes:
# a) Wrap pdfium functions with a mutex so they can safely be used in a threaded context.
# b) Try to mask the garbage exposed by ctypesgen (as far as possible), to achieve a purer namespace.
#    This is a bit controversial since it may negatively impact import performance, and normally python devs say "practicality beats purity" ...

import threading
import functools

PdfiumMutex = threading.Lock()

def _make_threadsafe(f):
    @functools.wraps(f)
    def pdfium_callable_threadsafe(*args, **kwargs):
        with PdfiumMutex:
            return f(*args, **kwargs)
    return pdfium_callable_threadsafe


def _get_members():
    
    import re
    import ctypes
    import fnmatch
    from types import ModuleType
    import pypdfium2._raw_unsafe
    
    _compile_wildcards = lambda *patterns: [re.compile(fnmatch.translate(p)) for p in patterns]
    
    NAME_FILTERS = (
        (str.startswith, ["_", "struct_", "enum_"]),
        (str.endswith, ["_t__"]),
        (str.__contains__, ["LibraryLoader"]),
        (str.__eq__, ["load_library", "add_library_search_dirs", "UNCHECKED", "c_ptrdiff_t"]),
        (lambda n, x: x.match(n), _compile_wildcards("fpdf_*_t")),
    )
    
    for name in dir(pypdfium2._raw_unsafe):
        member = getattr(pypdfium2._raw_unsafe, name)
        if any(any(func(name, x) for x in skips) for func, skips in NAME_FILTERS):
            continue
        if isinstance(member, ModuleType) or hasattr(ctypes, name):
            continue
        if isinstance(member, ctypes._CFuncPtr):
            member = _make_threadsafe(member)
        globals()[name] = member


_get_members()
del threading, functools, _make_threadsafe, _get_members
