# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pypdfium2._pypdfium as pdfium


def colour_tohex(r, g, b, a=255, greyscale=False):
    """
    Convert an RGBA colour specified by four integers ranging from 0 to 255 to a single value.
    
    Returns:
        (int, bool): The colour value, and a boolean signifying if an alpha channel is needed.
    """
    
    use_alpha = True
    if a == 255:
        use_alpha = False
    
    if greyscale and not use_alpha:
        colours = (a, r, g, b)
    else:
        colours = (a, b, g, r)
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
        (str, int): The colour format as string, and as PDFium colour format constant (``FPDFBitmap_...``).
    """
    
    px = "BGRA", pdfium.FPDFBitmap_BGRA
    
    if not use_alpha:
        if greyscale:
            px = "L", pdfium.FPDFBitmap_Gray
        else:
            px = "BGR", pdfium.FPDFBitmap_BGR
    
    return px


#: Get the target pixel format string for :mod:`PIL` that corresponds to an input pixel format string.
ColourMapping = {
    "BGRA": "RGBA",
    "BGR":  "RGB",
    "L":    "L",
}

#: Get the view mode string that corresponds to a PDFium view mode constant (``PDFDEST_VIEW_...``).
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

#: Get the error string that corresponds to a PDFium error constant (``FPDF_ERR_...``).
ErrorMapping = {
    pdfium.FPDF_ERR_SUCCESS:  "Success",
    pdfium.FPDF_ERR_UNKNOWN:  "Unknown error",
    pdfium.FPDF_ERR_FILE:     "File access error",
    pdfium.FPDF_ERR_FORMAT:   "Data format error",
    pdfium.FPDF_ERR_PASSWORD: "Incorrect password error",
    pdfium.FPDF_ERR_SECURITY: "Unsupported security scheme error",
    pdfium.FPDF_ERR_PAGE:     "Page not found or content error",
}

#: Get the object type string that corresponds to a PDFium object type constant (``FPDF_PAGEOBJ_...``).
ObjtypeToName = {
    pdfium.FPDF_PAGEOBJ_UNKNOWN: "unknown",
    pdfium.FPDF_PAGEOBJ_TEXT:    "text",
    pdfium.FPDF_PAGEOBJ_PATH:    "path",
    pdfium.FPDF_PAGEOBJ_IMAGE:   "image",
    pdfium.FPDF_PAGEOBJ_SHADING: "shading",
    pdfium.FPDF_PAGEOBJ_FORM:    "form",
}

#: Get the PDFium object type constant that corresponds to an object type string (inversion of :data:`.ObjtypeToName`).
ObjtypeToConst = {v: k for k, v in ObjtypeToName.items()}

#: Get the PDFium rotation constant that corresponds to a rotation value in degrees.
RotationToConst = {
    0:   0,
    90:  1,
    180: 2,
    270: 3,
}

#: Get the rotation value in degrees that corresponds to a PDFium rotation constant (inversion of :data:`.RotationToConst`).
RotationToDegrees = {v: k for k, v in RotationToConst.items()}
