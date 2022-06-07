# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pypdfium2._pypdfium as pdfium


def colour_tohex(r, g, b, a=255):
    """
    Convert an RGBA colour specified by four integers ranging from 0 to 255 to a single ARGB32 value.
    
    Returns:
        (int, bool): The colour value, and a boolean signifying if an alpha channel is needed.
    """
    
    use_alpha = True
    if a == 255:
        use_alpha = False
    
    colours = (a, r, g, b)
    for col in colours:
        assert 0 <= col <= 255
    
    hex_str = "0x"
    for col in colours:
        hex_str += hex(col)[2:].zfill(2)
    
    hex_int = int(hex_str, 0)
    
    return hex_int, use_alpha


def get_colourformat(use_alpha, greyscale):
    """
    Get the required colour format according to the boolean values of *use_alpha* and *greyscale*.
    
    Returns:
        (str, int): The colour format as string, and as PDFium constant (``FPDFBitmap_...``).
    """
    
    px = "BGRA", pdfium.FPDFBitmap_BGRA
    
    if not use_alpha:
        if greyscale:
            px = "L", pdfium.FPDFBitmap_Gray
        else:
            px = "BGR", pdfium.FPDFBitmap_BGR
    
    return px


def _invert_dict(dictionary):
    """
    Returns:
        A copy of *dictionary*, with inverted keys and values.
    """
    return {v: k for k, v in dictionary.items()}


#: Convert an input pixel format to its :mod:`PIL` target format.
ColourMapping = {
    "BGRA": "RGBA",
    "BGR":  "RGB",
    "L":    "L",
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
    pdfium.PDFDEST_VIEW_UNKNOWN_MODE: "Unknown",
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
