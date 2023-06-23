# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import atexit
import os, sys
import pypdfium2.raw as pdfium_c
import pypdfium2.internal as pdfium_i


def init_lib():
    # NOTE PDFium developers plan changes to the initialisation API (see https://crbug.com/pdfium/1446)
    assert not pdfium_i.LIBRARY_AVAILABLE
    if pdfium_i.DEBUG_AUTOCLOSE:
        print("Initialize PDFium (auto)", file=sys.stderr)
    pdfium_c.FPDF_InitLibrary()
    pdfium_i.LIBRARY_AVAILABLE.value = True


def destroy_lib():
    assert pdfium_i.LIBRARY_AVAILABLE
    if pdfium_i.DEBUG_AUTOCLOSE:
        # use os.write() rather than print() to avoid "reentrant call" exceptions on shutdown (see https://stackoverflow.com/q/75367828/15547292)
        os.write(sys.stderr.fileno(), b"Destroy PDFium (auto)\n")
    pdfium_c.FPDF_DestroyLibrary()
    pdfium_i.LIBRARY_AVAILABLE.value = False


# Load pdfium
init_lib()

# Register an exit handler that will free pdfium
# Trust in Python to call exit handlers only after all objects have been finalized
atexit.register(destroy_lib)
