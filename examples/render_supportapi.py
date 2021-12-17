#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: CC-BY-4.0 

import os
import sys
import pypdfium2 as pdfium


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("Usage: example.py somefile.pdf")
        sys.exit()
    
    filename = sys.argv[1]
    
    with pdfium.PdfContext(filename) as pdf:
        n_pages = pdfium.FPDF_GetPageCount(pdf)
    
    page_indices = [i for i in range(n_pages)]
    
    generator = pdfium.render_pdf(
        filename,
        page_indices = page_indices,
        scale = 1,
        rotation = 0,
        colour = 0xFFFFFFFF,
        annotations = True,
        greyscale = False,
        optimise_mode = pdfium.OptimiseMode.none,
        n_processes = os.cpu_count(),
    )
    
    for image, suffix in generator:
        image.save(f"out_{suffix}.png")
        image.close()
