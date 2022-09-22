# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# private utility functions

import pypdfium2._pypdfium as pdfium


def validate_colours(fill_colour, colour_scheme):
    colours = [fill_colour]
    if colour_scheme is not None:
        colours += list( colour_scheme.colours.values() )
    for col in colours:
        if len(col) != 4:
            raise ValueError("Colour must consist of exactly 4 values.")
        if not all(0 <= c <= 255 for c in col):
            raise ValueError("Colour value exceeds boundaries.")


def auto_bitmap_format(fill_colour, greyscale, prefer_bgrx):
    # no need to take alpha values of colour_scheme into account (drawings are additive)
    if (fill_colour[3] < 255):
        return pdfium.FPDFBitmap_BGRA
    elif greyscale:
        return pdfium.FPDFBitmap_Gray
    elif prefer_bgrx:
        return pdfium.FPDFBitmap_BGRx
    else:
        return pdfium.FPDFBitmap_BGR
