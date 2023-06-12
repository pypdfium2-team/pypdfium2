# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import atexit
import pypdfium2.raw as pdfium_c
import pypdfium2.internal as pdfium_i


def destroy_library():
    if pdfium_i.DEBUG_AUTOCLOSE:
        import os, sys
        os.write(sys.stderr.fileno(), b"Destroy PDFium (auto)\n")
    pdfium_c.FPDF_DestroyLibrary()

# Load pdfium
# Note: PDFium developers plan changes to the initialisation API (see https://crbug.com/pdfium/1446)
pdfium_c.FPDF_InitLibrary()

# Register an exit handler that will free pdfium
# Trust in Python to call exit handlers only after all objects have been finalized
atexit.register(destroy_library)
