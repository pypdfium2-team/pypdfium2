# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import atexit
import os, sys
import pypdfium2.raw as pdfium_c
import pypdfium2.internal as pdfium_i


def destroy_lib():
    if pdfium_i.DEBUG_AUTOCLOSE:
        os.write(sys.stderr.fileno(), b"Destroy PDFium (auto)\n")
    if pdfium_i._LIBRARY_DESTROYED:
        os.write(sys.stderr.fileno(), b"-> Library is destroyed already, return.\n")
        return
    pdfium_c.FPDF_DestroyLibrary()
    pdfium_i._LIBRARY_DESTROYED.value = True

# Load pdfium
# Note: PDFium developers plan changes to the initialisation API (see https://crbug.com/pdfium/1446)
pdfium_c.FPDF_InitLibrary()

# Register an exit handler that will free pdfium
# Trust in Python to call exit handlers only after all objects have been finalized
atexit.register(destroy_lib)
