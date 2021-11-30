#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: CC-BY-4.0

import sys
import pypdfium2 as pdfium

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage: example.py somefile.pdf")
        sys.exit()

    filename = sys.argv[1]

    with pdfium.PdfContext(filename) as pdf:
        pil_image = pdfium.render_page(
            pdf,
            page_index=0,
            scale=1,
            rotation=0,
            background_colour=0xFFFFFFFF,
            render_annotations=True,
            optimise_mode=pdfium.OptimiseMode.none,
        )

    pil_image.save("out.png")
