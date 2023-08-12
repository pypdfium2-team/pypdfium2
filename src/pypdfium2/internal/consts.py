# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pypdfium2.raw as pdfium_r
from pypdfium2.version import V_PDFIUM_IS_V8


class _fallback_dict (dict):
    
    def get(self, key, default_prefix="Unhandled constant"):
        return dict.get(self, key, f"{default_prefix} {key}")


#: Convert a rotation value in degrees to a PDFium constant.
RotationToConst = {
    0:   0,
    90:  1,
    180: 2,
    270: 3,
}

#: Convert a PDFium rotation constant to a value in degrees. Inversion of :data:`.RotationToConst`.
RotationToDegrees = {v: k for k, v in RotationToConst.items()}


#: Get the number of channels for a PDFium bitmap format. (:attr:`FPDFBitmap_Unknown` is deliberately not handled.)
BitmapTypeToNChannels = {
    pdfium_r.FPDFBitmap_Gray: 1,
    pdfium_r.FPDFBitmap_BGR:  3,
    pdfium_r.FPDFBitmap_BGRA: 4,
    pdfium_r.FPDFBitmap_BGRx: 4,
}

#: Convert a PDFium bitmap format to string, assuming BGR byte order. (:attr:`FPDFBitmap_Unknown` is deliberately not handled.)
BitmapTypeToStr = {
    pdfium_r.FPDFBitmap_Gray: "L",
    pdfium_r.FPDFBitmap_BGR:  "BGR",
    pdfium_r.FPDFBitmap_BGRA: "BGRA",
    pdfium_r.FPDFBitmap_BGRx: "BGRX",
}

#: Convert a PDFium bitmap format to string, assuming RGB byte order. (:attr:`FPDFBitmap_Unknown` is deliberately not handled.)
BitmapTypeToStrReverse = {
    pdfium_r.FPDFBitmap_Gray: "L",
    pdfium_r.FPDFBitmap_BGR:  "RGB",
    pdfium_r.FPDFBitmap_BGRA: "RGBA",
    pdfium_r.FPDFBitmap_BGRx: "RGBX",
}

#: Convert a string to PDFium bitmap format, assuming BGR byte order. Inversion of :data:`BitmapTypeToStr`.
BitmapStrToConst = {v: k for k, v in BitmapTypeToStr.items()}

#: Convert a string to PDFium bitmap format, assuming RGB byte order. Inversion of :data:`BitmapTypeToStrReverse`.
BitmapStrReverseToConst = {v: k for k, v in BitmapTypeToStrReverse.items()}

#: Convert a PDFium form type (:attr:`FORMTYPE_*`) to string.
FormTypeToStr = _fallback_dict({
    pdfium_r.FORMTYPE_NONE:           "None",
    pdfium_r.FORMTYPE_ACRO_FORM:      "AcroForm",
    pdfium_r.FORMTYPE_XFA_FULL:       "XFA",
    pdfium_r.FORMTYPE_XFA_FOREGROUND: "XFAF",
})

#: Convert a PDFium color space constant (:attr:`FPDF_COLORSPACE_*`) to string.
ColorspaceToStr = _fallback_dict({
    pdfium_r.FPDF_COLORSPACE_UNKNOWN:    "?",
    pdfium_r.FPDF_COLORSPACE_DEVICEGRAY: "DeviceGray",
    pdfium_r.FPDF_COLORSPACE_DEVICERGB:  "DeviceRGB",
    pdfium_r.FPDF_COLORSPACE_DEVICECMYK: "DeviceCMYK",
    pdfium_r.FPDF_COLORSPACE_CALGRAY:    "CalGray",
    pdfium_r.FPDF_COLORSPACE_CALRGB:     "CalRGB",
    pdfium_r.FPDF_COLORSPACE_LAB:        "Lab",
    pdfium_r.FPDF_COLORSPACE_ICCBASED:   "ICCBased",
    pdfium_r.FPDF_COLORSPACE_SEPARATION: "Separation",
    pdfium_r.FPDF_COLORSPACE_DEVICEN:    "DeviceN",
    pdfium_r.FPDF_COLORSPACE_INDEXED:    "Indexed",  # i. e. palettized
    pdfium_r.FPDF_COLORSPACE_PATTERN:    "Pattern",
})

#: Convert a PDFium view mode constant (:attr:`PDFDEST_VIEW_*`) to string.
ViewmodeToStr = _fallback_dict({
    pdfium_r.PDFDEST_VIEW_UNKNOWN_MODE: "?",
    pdfium_r.PDFDEST_VIEW_XYZ:   "XYZ",
    pdfium_r.PDFDEST_VIEW_FIT:   "Fit",
    pdfium_r.PDFDEST_VIEW_FITH:  "FitH",
    pdfium_r.PDFDEST_VIEW_FITV:  "FitV",
    pdfium_r.PDFDEST_VIEW_FITR:  "FitR",
    pdfium_r.PDFDEST_VIEW_FITB:  "FitB",
    pdfium_r.PDFDEST_VIEW_FITBH: "FitBH",
    pdfium_r.PDFDEST_VIEW_FITBV: "FitBV",
})

#: Convert a PDFium object type constant (:attr:`FPDF_PAGEOBJ_*`) to string.
ObjectTypeToStr = _fallback_dict({
    pdfium_r.FPDF_PAGEOBJ_UNKNOWN: "?",
    pdfium_r.FPDF_PAGEOBJ_TEXT:    "text",
    pdfium_r.FPDF_PAGEOBJ_PATH:    "path",
    pdfium_r.FPDF_PAGEOBJ_IMAGE:   "image",
    pdfium_r.FPDF_PAGEOBJ_SHADING: "shading",
    pdfium_r.FPDF_PAGEOBJ_FORM:    "form",
})

#: Convert an object type string to a PDFium constant. Inversion of :data:`.ObjectTypeToStr`.
ObjectTypeToConst = {v: k for k, v in ObjectTypeToStr.items()}

#: Convert a PDFium page mode constant (:attr:`PAGEMODE_*`) to string.
PageModeToStr = _fallback_dict({
    pdfium_r.PAGEMODE_UNKNOWN:        "?",
    pdfium_r.PAGEMODE_USENONE:        "None",
    pdfium_r.PAGEMODE_USEOUTLINES:    "Outline",
    pdfium_r.PAGEMODE_USETHUMBS:      "Thumbnails",
    pdfium_r.PAGEMODE_FULLSCREEN:     "Full-screen",
    pdfium_r.PAGEMODE_USEOC:          "Layers",
    pdfium_r.PAGEMODE_USEATTACHMENTS: "Attachments",
})

#: Convert a PDFium error constant (:attr:`FPDF_ERR_*`) to string.
ErrorToStr = _fallback_dict({
    pdfium_r.FPDF_ERR_SUCCESS:  "Success",
    pdfium_r.FPDF_ERR_UNKNOWN:  "Unknown error",
    pdfium_r.FPDF_ERR_FILE:     "File access error",
    pdfium_r.FPDF_ERR_FORMAT:   "Data format error",
    pdfium_r.FPDF_ERR_PASSWORD: "Incorrect password error",
    pdfium_r.FPDF_ERR_SECURITY: "Unsupported security scheme error",
    pdfium_r.FPDF_ERR_PAGE:     "Page not found or content error",
})

if V_PDFIUM_IS_V8:
    #: Convert a PDFium XFA error constant (:attr:`FPDF_ERR_XFA*`) to string. Available only with V8/XFA enabled builds.
    XFAErrorToStr = _fallback_dict({
        pdfium_r.FPDF_ERR_XFALOAD:   "Load error",
        pdfium_r.FPDF_ERR_XFALAYOUT: "Layout error",
    })

#: Convert a PDFium unsupported constant (:attr:`FPDF_UNSP_*`) to string.
UnsupportedInfoToStr = _fallback_dict({
    pdfium_r.FPDF_UNSP_DOC_XFAFORM:               "XFA form",
    pdfium_r.FPDF_UNSP_DOC_PORTABLECOLLECTION:    "Portable collection",
    pdfium_r.FPDF_UNSP_DOC_ATTACHMENT:            "Attachment (incomplete support)",  # https://crbug.com/pdfium/1945
    pdfium_r.FPDF_UNSP_DOC_SECURITY:              "Security",
    pdfium_r.FPDF_UNSP_DOC_SHAREDREVIEW:          "Shared review",
    pdfium_r.FPDF_UNSP_DOC_SHAREDFORM_ACROBAT:    "Shared form (acrobat)",
    pdfium_r.FPDF_UNSP_DOC_SHAREDFORM_FILESYSTEM: "Shared form (filesystem)",
    pdfium_r.FPDF_UNSP_DOC_SHAREDFORM_EMAIL:      "Shared form (email)",
    pdfium_r.FPDF_UNSP_ANNOT_3DANNOT:             "3D annotation",
    pdfium_r.FPDF_UNSP_ANNOT_MOVIE:               "Movie annotation",
    pdfium_r.FPDF_UNSP_ANNOT_SOUND:               "Sound annotation",
    pdfium_r.FPDF_UNSP_ANNOT_SCREEN_MEDIA:        "Screen media annotation",
    pdfium_r.FPDF_UNSP_ANNOT_SCREEN_RICHMEDIA:    "Screen rich media annotation",
    pdfium_r.FPDF_UNSP_ANNOT_ATTACHMENT:          "Attachment annotation",
    pdfium_r.FPDF_UNSP_ANNOT_SIG:                 "Signature annotation",
})
