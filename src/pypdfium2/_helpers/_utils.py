# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pypdfium2._pypdfium as pdfium


def validate_colors(bg_color, color_scheme):
    colors = [bg_color]
    if color_scheme is not None:
        colors += list( color_scheme.kwargs.values() )
    for col in colors:
        if len(col) != 4:
            raise ValueError("Color must consist of exactly 4 values.")
        if not all(0 <= c <= 255 for c in col):
            raise ValueError("Color value exceeds boundaries.")


def auto_bitmap_format(bg_color, greyscale, prefer_bgrx):
    # no need to take alpha values of color_scheme into account (drawings are additive)
    if (bg_color[3] < 255):
        return pdfium.FPDFBitmap_BGRA
    elif greyscale:
        return pdfium.FPDFBitmap_Gray
    elif prefer_bgrx:
        return pdfium.FPDFBitmap_BGRx
    else:
        return pdfium.FPDFBitmap_BGR


def color_tohex(color, rev_byteorder):
    """
    Convert an RGBA color specified by 4 integers ranging from 0 to 255 to a single 32-bit integer as required by PDFium.
    If using regular byte order, the output format will be ARGB. If using reversed byte order, it will be ABGR.
    """
    
    r, g, b, a = color
    
    # color is interpreted differently with FPDF_REVERSE_BYTE_ORDER (perhaps inadvertently?)
    if rev_byteorder:
        channels = (a, b, g, r)
    else:
        channels = (a, r, g, b)
    
    c_color = 0
    shift = 24
    for c in channels:
        c_color |= c << shift
        shift -= 8
    
    return c_color


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

def _transform_dict(main, transformer):
    """
    Remap each value of a *main* dictionary through a second *transformer* dictionary, if contained.
    Otherwise, take over the existing value as-is.
    
    Returns:
        Transformed variant of the *main* dictionary.
    """
    output = {}
    for key, value in main.items():
        if value in transformer.keys():
            output[key] = transformer[value]
        else:
            output[key] = value
    return output


#: Convert a PDFium pixel format constant to string, assuming regular byte order.
BitmapConstToStr = {
    pdfium.FPDFBitmap_Gray: "L",
    pdfium.FPDFBitmap_BGR:  "BGR",
    pdfium.FPDFBitmap_BGRA: "BGRA",
    pdfium.FPDFBitmap_BGRx: "BGRX",
}

# Convert a reverse pixel format string to its regular counterpart.
UnreverseBitmapStr = {
    "BGR":  "RGB",
    "BGRA": "RGBA",
    "BGRX": "RGBX",
}

#: Convert a PDFium pixel format constant to string, assuming reversed byte order.
BitmapConstToReverseStr = _transform_dict(BitmapConstToStr, UnreverseBitmapStr)

#: Convert a PDFium view mode constant (``PDFDEST_VIEW_*``) to string.
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

#: Convert a PDFium error constant (``FPDF_ERR_*``) to string.
ErrorMapping = {
    pdfium.FPDF_ERR_SUCCESS:  "Success",
    pdfium.FPDF_ERR_UNKNOWN:  "Unknown error",
    pdfium.FPDF_ERR_FILE:     "File access error",
    pdfium.FPDF_ERR_FORMAT:   "Data format error",
    pdfium.FPDF_ERR_PASSWORD: "Incorrect password error",
    pdfium.FPDF_ERR_SECURITY: "Unsupported security scheme error",
    pdfium.FPDF_ERR_PAGE:     "Page not found or content error",
}

#: Convert a PDFium object type constant (``FPDF_PAGEOBJ_*``) to string.
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
