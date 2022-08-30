# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pypdfium2._pypdfium as pdfium


def get_bitmap_format(colour, greyscale, rev_byteorder):
    
    if len(colour) != 4:
        raise ValueError("Colour must be a sequence of four values (red, green, blue, alpha).")
    if not all(0 <= c <= 255 for c in colour):
        raise ValueError("Colour value exceeds boundaries.")
    
    if (colour[3] < 255):
        px_const = pdfium.FPDFBitmap_BGRA
    else:
        if greyscale:
            # attempting to use FPDF_REVERSE_BYTE_ORDER with FPDFBitmap_Gray is not only unnecessary, but also causes issues, so prohibit it (pdfium bug?)
            px_const = pdfium.FPDFBitmap_Gray
            rev_byteorder = False
        else:
            px_const = pdfium.FPDFBitmap_BGR
    
    if rev_byteorder:
        px_str = BitmapFormatToStrReverse[px_const]
    else:
        px_str = BitmapFormatToStr[px_const]
    
    return px_const, px_str, rev_byteorder


def colour_tohex(r, g, b, a, rev_byteorder):
    """
    Convert an RGBA colour specified by 4 integers ranging from 0 to 255 to a single 32-bit integer as required by PDFium.
    If using regular byte order, the output format will be ARGB. If using reversed byte order, it will be ABGR.
    """
    
    # colour is interpreted differently with FPDF_REVERSE_BYTE_ORDER (perhaps inadvertently?)
    if rev_byteorder:
        channels = (a, b, g, r)
    else:
        channels = (a, r, g, b)
    
    c_colour = 0
    shift = 24
    for c in channels:
        c_colour |= c << shift
        shift -= 8
    
    return c_colour


def get_functype(struct, funcname):
    """
    Parameters:
        struct (ctypes.Structure): A structure (e. g. ``FPDF_FILEWRITE``).
        funcname (str): Name of the callback function to implement (e. g. ``WriteBlock``).
    Returns:
        A :meth:`ctypes.CFUNCTYPE` instance to wrap the callback function.
        For some reason, this is not done automatically, although the information is present in the bindings file.
        This is a convenience function to retrieve the declaration.
    """
    return {k: v for k, v in struct._fields_}[funcname]


def _invert_dict(dictionary):
    """
    Returns:
        A copy of *dictionary*, with inverted keys and values.
    """
    return {v: k for k, v in dictionary.items()}


#: Convert a PDFium pixel format constant to string, assuming regular byte order.
BitmapFormatToStr = {
    pdfium.FPDFBitmap_BGRA: "BGRA",
    pdfium.FPDFBitmap_BGR:  "BGR",
    pdfium.FPDFBitmap_Gray: "L",
}

#: Convert a PDFium pixel format constant to string, assuming reversed byte order.
BitmapFormatToStrReverse = {
    pdfium.FPDFBitmap_BGRA: "RGBA",
    pdfium.FPDFBitmap_BGR:  "RGB",
    pdfium.FPDFBitmap_Gray: "L",
}

#: Convert a PDFium view mode constant (``PDFDEST_VIEW_...``) to string.
ViewmodeMapping = {
    pdfium.PDFDEST_VIEW_XYZ:   "XYZ",
    pdfium.PDFDEST_VIEW_FIT:   "Fit",
    pdfium.PDFDEST_VIEW_FITH:  "FitH",
    pdfium.PDFDEST_VIEW_FITV:  "FitV",
    pdfium.PDFDEST_VIEW_FITR:  "FitR",
    pdfium.PDFDEST_VIEW_FITB:  "FitB",
    pdfium.PDFDEST_VIEW_FITBH: "FitBH",
    pdfium.PDFDEST_VIEW_FITBV: "FitBV",
    pdfium.PDFDEST_VIEW_UNKNOWN_MODE: "?",
}

#: Convert a PDFium error constant (``FPDF_ERR_...``) to string.
ErrorMapping = {
    pdfium.FPDF_ERR_SUCCESS:  "Success",
    pdfium.FPDF_ERR_UNKNOWN:  "Unknown error",
    pdfium.FPDF_ERR_FILE:     "File access error",
    pdfium.FPDF_ERR_FORMAT:   "Data format error",
    pdfium.FPDF_ERR_PASSWORD: "Incorrect password error",
    pdfium.FPDF_ERR_SECURITY: "Unsupported security scheme error",
    pdfium.FPDF_ERR_PAGE:     "Page not found or content error",
}

#: Convert a PDFium object type constant (``FPDF_PAGEOBJ_...``) to string.
ObjtypeToName = {
    pdfium.FPDF_PAGEOBJ_UNKNOWN: "unknown",
    pdfium.FPDF_PAGEOBJ_TEXT:    "text",
    pdfium.FPDF_PAGEOBJ_PATH:    "path",
    pdfium.FPDF_PAGEOBJ_IMAGE:   "image",
    pdfium.FPDF_PAGEOBJ_SHADING: "shading",
    pdfium.FPDF_PAGEOBJ_FORM:    "form",
}

#: Convert an object type string to a PDFium constant. Inversion of :data:`ObjtypeToName`.
ObjtypeToConst = _invert_dict(ObjtypeToName)

#: Convert a rotation value in degrees to a PDFium constant.
RotationToConst = {
    0:   0,
    90:  1,
    180: 2,
    270: 3,
}

#: Convert a PDFium rotation constant to a value in degrees. Inversion of :data:`RotationToConst`.
RotationToDegrees = _invert_dict(RotationToConst)
