r"""Wrapper for fpdf_annot.h

Generated with:
/opt/hostedtoolcache/Python/3.10.13/x64/bin/ctypesgen --no-srcinfo --library pdfium --runtime-libdirs . --compile-libdirs ~/work/pypdfium2/pypdfium2/data/linux_x64 --headers fpdf_annot.h fpdf_attachment.h fpdf_catalog.h fpdf_dataavail.h fpdf_doc.h fpdf_edit.h fpdf_ext.h fpdf_flatten.h fpdf_formfill.h fpdf_fwlevent.h fpdf_javascript.h fpdf_ppo.h fpdf_progressive.h fpdf_save.h fpdf_searchex.h fpdf_signature.h fpdf_structtree.h fpdf_sysfontinfo.h fpdf_text.h fpdf_thumbnail.h fpdf_transformpage.h fpdfview.h -o ~/work/pypdfium2/pypdfium2/data/linux_x64/bindings.py

Do not modify this file.
"""

# Begin preamble for Python

# TODO
# - add c_ptrdiff_t and _variadic_function only on an as-needed basis
# - check if we can remove the _variadic_function wrapper entirely and use plain ctypes instead
# - Avoid ctypes glob import (pollutes namespace)


import ctypes
from ctypes import *  # noqa: F401, F403

def _get_ptrdiff_t():

    int_types = (ctypes.c_int16, ctypes.c_int32)
    if hasattr(ctypes, "c_int64"):
        # Some builds of ctypes apparently do not have ctypes.c_int64
        # defined; it's a pretty good bet that these builds do not
        # have 64-bit pointers.
        int_types += (ctypes.c_int64,)

    c_ptrdiff_t = None
    for t in int_types:
        if ctypes.sizeof(t) == ctypes.sizeof(ctypes.c_size_t):
            c_ptrdiff_t = t

    return c_ptrdiff_t

c_ptrdiff_t = _get_ptrdiff_t()


class _variadic_function(object):
    def __init__(self, func, restype, argtypes, errcheck):
        self.func = func
        self.func.restype = restype
        self.argtypes = argtypes
        if errcheck:
            self.func.errcheck = errcheck

    def _as_parameter_(self):
        # So we can pass this variadic function as a function pointer
        return self.func

    def __call__(self, *args):
        fixed_args = []
        i = 0
        for argtype in self.argtypes:
            # Typecheck what we can
            fixed_args.append(argtype.from_param(args[i]))
            i += 1
        return self.func(*fixed_args + list(args[i:]))

# End preamble

# Begin loader

import sys
import ctypes
import ctypes.util
from pathlib import Path


def _find_library(libname, libdirs):
    
    if sys.platform in ("win32", "cygwin", "msys"):
        patterns = ["{}.dll", "lib{}.dll", "{}"]
    elif sys.platform == "darwin":
        patterns = ["lib{}.dylib", "{}.dylib", "lib{}.so", "{}.so", "{}"]
    else:  # assume unix pattern or plain libname
        patterns = ["lib{}.so", "{}.so", "{}"]
    
    RELDIR = Path(__file__).parent
    
    for dir in libdirs:
        # joining an absolute path silently discardy the path before
        dir = (RELDIR / dir).resolve(strict=False)
        for pat in patterns:
            libpath = dir / pat.format(libname)
            if libpath.is_file():
                return str(libpath)
    
    libpath = ctypes.util.find_library(libname)
    if not libpath:
        raise ImportError(f"Library '{libname} could not be found in {libdirs} or system.'")
    return libpath

# End loader


_libdirs = ['.']
_libpath = _find_library("pdfium", _libdirs)
_lib = ctypes.CDLL(_libpath)
# No modules

enum_anon_2 = c_int
FPDF_TEXTRENDERMODE_UNKNOWN = (-1)
FPDF_TEXTRENDERMODE_FILL = 0
FPDF_TEXTRENDERMODE_STROKE = 1
FPDF_TEXTRENDERMODE_FILL_STROKE = 2
FPDF_TEXTRENDERMODE_INVISIBLE = 3
FPDF_TEXTRENDERMODE_FILL_CLIP = 4
FPDF_TEXTRENDERMODE_STROKE_CLIP = 5
FPDF_TEXTRENDERMODE_FILL_STROKE_CLIP = 6
FPDF_TEXTRENDERMODE_CLIP = 7
FPDF_TEXTRENDERMODE_LAST = FPDF_TEXTRENDERMODE_CLIP
FPDF_TEXT_RENDERMODE = enum_anon_2

class struct_fpdf_action_t__ (Structure):
    pass
FPDF_ACTION = POINTER(struct_fpdf_action_t__)

class struct_fpdf_annotation_t__ (Structure):
    pass
FPDF_ANNOTATION = POINTER(struct_fpdf_annotation_t__)

class struct_fpdf_attachment_t__ (Structure):
    pass
FPDF_ATTACHMENT = POINTER(struct_fpdf_attachment_t__)

class struct_fpdf_avail_t__ (Structure):
    pass
FPDF_AVAIL = POINTER(struct_fpdf_avail_t__)

class struct_fpdf_bitmap_t__ (Structure):
    pass
FPDF_BITMAP = POINTER(struct_fpdf_bitmap_t__)

class struct_fpdf_bookmark_t__ (Structure):
    pass
FPDF_BOOKMARK = POINTER(struct_fpdf_bookmark_t__)

class struct_fpdf_clippath_t__ (Structure):
    pass
FPDF_CLIPPATH = POINTER(struct_fpdf_clippath_t__)

class struct_fpdf_dest_t__ (Structure):
    pass
FPDF_DEST = POINTER(struct_fpdf_dest_t__)

class struct_fpdf_document_t__ (Structure):
    pass
FPDF_DOCUMENT = POINTER(struct_fpdf_document_t__)

class struct_fpdf_font_t__ (Structure):
    pass
FPDF_FONT = POINTER(struct_fpdf_font_t__)

class struct_fpdf_form_handle_t__ (Structure):
    pass
FPDF_FORMHANDLE = POINTER(struct_fpdf_form_handle_t__)

class struct_fpdf_glyphpath_t__ (Structure):
    pass
FPDF_GLYPHPATH = POINTER(struct_fpdf_glyphpath_t__)

class struct_fpdf_javascript_action_t (Structure):
    pass
FPDF_JAVASCRIPT_ACTION = POINTER(struct_fpdf_javascript_action_t)

class struct_fpdf_link_t__ (Structure):
    pass
FPDF_LINK = POINTER(struct_fpdf_link_t__)

class struct_fpdf_page_t__ (Structure):
    pass
FPDF_PAGE = POINTER(struct_fpdf_page_t__)

class struct_fpdf_pagelink_t__ (Structure):
    pass
FPDF_PAGELINK = POINTER(struct_fpdf_pagelink_t__)

class struct_fpdf_pageobject_t__ (Structure):
    pass
FPDF_PAGEOBJECT = POINTER(struct_fpdf_pageobject_t__)

class struct_fpdf_pageobjectmark_t__ (Structure):
    pass
FPDF_PAGEOBJECTMARK = POINTER(struct_fpdf_pageobjectmark_t__)

class struct_fpdf_pagerange_t__ (Structure):
    pass
FPDF_PAGERANGE = POINTER(struct_fpdf_pagerange_t__)

class struct_fpdf_pathsegment_t (Structure):
    pass
FPDF_PATHSEGMENT = POINTER(struct_fpdf_pathsegment_t)

class struct_fpdf_schhandle_t__ (Structure):
    pass
FPDF_SCHHANDLE = POINTER(struct_fpdf_schhandle_t__)

class struct_fpdf_signature_t__ (Structure):
    pass
FPDF_SIGNATURE = POINTER(struct_fpdf_signature_t__)
FPDF_SKIA_CANVAS = POINTER(None)

class struct_fpdf_structelement_t__ (Structure):
    pass
FPDF_STRUCTELEMENT = POINTER(struct_fpdf_structelement_t__)

class struct_fpdf_structelement_attr_t__ (Structure):
    pass
FPDF_STRUCTELEMENT_ATTR = POINTER(struct_fpdf_structelement_attr_t__)

class struct_fpdf_structtree_t__ (Structure):
    pass
FPDF_STRUCTTREE = POINTER(struct_fpdf_structtree_t__)

class struct_fpdf_textpage_t__ (Structure):
    pass
FPDF_TEXTPAGE = POINTER(struct_fpdf_textpage_t__)

class struct_fpdf_widget_t__ (Structure):
    pass
FPDF_WIDGET = POINTER(struct_fpdf_widget_t__)

class struct_fpdf_xobject_t__ (Structure):
    pass
FPDF_XOBJECT = POINTER(struct_fpdf_xobject_t__)
FPDF_BOOL = c_int
FPDF_RESULT = c_int
FPDF_DWORD = c_ulong
FS_FLOAT = c_float
enum__FPDF_DUPLEXTYPE_ = c_int
DuplexUndefined = 0
Simplex = (DuplexUndefined + 1)
DuplexFlipShortEdge = (Simplex + 1)
DuplexFlipLongEdge = (DuplexFlipShortEdge + 1)
FPDF_DUPLEXTYPE = enum__FPDF_DUPLEXTYPE_
FPDF_WCHAR = c_ushort
FPDF_BYTESTRING = POINTER(c_char)
FPDF_WIDESTRING = POINTER(FPDF_WCHAR)

class struct_FPDF_BSTR_ (Structure):
    __slots__ = ['str', 'len']
struct_FPDF_BSTR_._fields_ = [
    ('str', POINTER(c_char)),
    ('len', c_int),
]
FPDF_BSTR = struct_FPDF_BSTR_
FPDF_STRING = POINTER(c_char)

class struct__FS_MATRIX_ (Structure):
    __slots__ = ['a', 'b', 'c', 'd', 'e', 'f']
struct__FS_MATRIX_._fields_ = [
    ('a', c_float),
    ('b', c_float),
    ('c', c_float),
    ('d', c_float),
    ('e', c_float),
    ('f', c_float),
]
FS_MATRIX = struct__FS_MATRIX_

class struct__FS_RECTF_ (Structure):
    __slots__ = ['left', 'top', 'right', 'bottom']
struct__FS_RECTF_._fields_ = [
    ('left', c_float),
    ('top', c_float),
    ('right', c_float),
    ('bottom', c_float),
]
FS_LPRECTF = POINTER(struct__FS_RECTF_)
FS_RECTF = struct__FS_RECTF_
FS_LPCRECTF = POINTER(FS_RECTF)

class struct_FS_SIZEF_ (Structure):
    __slots__ = ['width', 'height']
struct_FS_SIZEF_._fields_ = [
    ('width', c_float),
    ('height', c_float),
]
FS_LPSIZEF = POINTER(struct_FS_SIZEF_)
FS_SIZEF = struct_FS_SIZEF_
FS_LPCSIZEF = POINTER(FS_SIZEF)

class struct_FS_POINTF_ (Structure):
    __slots__ = ['x', 'y']
struct_FS_POINTF_._fields_ = [
    ('x', c_float),
    ('y', c_float),
]
FS_LPPOINTF = POINTER(struct_FS_POINTF_)
FS_POINTF = struct_FS_POINTF_
FS_LPCPOINTF = POINTER(FS_POINTF)

class struct__FS_QUADPOINTSF (Structure):
    __slots__ = ['x1', 'y1', 'x2', 'y2', 'x3', 'y3', 'x4', 'y4']
struct__FS_QUADPOINTSF._fields_ = [
    ('x1', FS_FLOAT),
    ('y1', FS_FLOAT),
    ('x2', FS_FLOAT),
    ('y2', FS_FLOAT),
    ('x3', FS_FLOAT),
    ('y3', FS_FLOAT),
    ('x4', FS_FLOAT),
    ('y4', FS_FLOAT),
]
FS_QUADPOINTSF = struct__FS_QUADPOINTSF
FPDF_ANNOTATION_SUBTYPE = c_int
FPDF_ANNOT_APPEARANCEMODE = c_int
FPDF_OBJECT_TYPE = c_int
enum_anon_3 = c_int
FPDF_RENDERERTYPE_AGG = 0
FPDF_RENDERERTYPE_SKIA = 1
FPDF_RENDERER_TYPE = enum_anon_3

class struct_FPDF_LIBRARY_CONFIG_ (Structure):
    __slots__ = ['version', 'm_pUserFontPaths', 'm_pIsolate', 'm_v8EmbedderSlot', 'm_pPlatform', 'm_RendererType']
struct_FPDF_LIBRARY_CONFIG_._fields_ = [
    ('version', c_int),
    ('m_pUserFontPaths', POINTER(POINTER(c_char))),
    ('m_pIsolate', POINTER(None)),
    ('m_v8EmbedderSlot', c_uint),
    ('m_pPlatform', POINTER(None)),
    ('m_RendererType', FPDF_RENDERER_TYPE),
]
FPDF_LIBRARY_CONFIG = struct_FPDF_LIBRARY_CONFIG_

if hasattr(_lib, "FPDF_InitLibraryWithConfig"):
    FPDF_InitLibraryWithConfig = _lib.FPDF_InitLibraryWithConfig
    FPDF_InitLibraryWithConfig.argtypes = [POINTER(FPDF_LIBRARY_CONFIG)]
    FPDF_InitLibraryWithConfig.restype = None

if hasattr(_lib, "FPDF_InitLibrary"):
    FPDF_InitLibrary = _lib.FPDF_InitLibrary
    FPDF_InitLibrary.argtypes = []
    FPDF_InitLibrary.restype = None

if hasattr(_lib, "FPDF_DestroyLibrary"):
    FPDF_DestroyLibrary = _lib.FPDF_DestroyLibrary
    FPDF_DestroyLibrary.argtypes = []
    FPDF_DestroyLibrary.restype = None

if hasattr(_lib, "FPDF_SetSandBoxPolicy"):
    FPDF_SetSandBoxPolicy = _lib.FPDF_SetSandBoxPolicy
    FPDF_SetSandBoxPolicy.argtypes = [FPDF_DWORD, FPDF_BOOL]
    FPDF_SetSandBoxPolicy.restype = None

if hasattr(_lib, "FPDF_LoadDocument"):
    FPDF_LoadDocument = _lib.FPDF_LoadDocument
    FPDF_LoadDocument.argtypes = [FPDF_STRING, FPDF_BYTESTRING]
    FPDF_LoadDocument.restype = FPDF_DOCUMENT

if hasattr(_lib, "FPDF_LoadMemDocument"):
    FPDF_LoadMemDocument = _lib.FPDF_LoadMemDocument
    FPDF_LoadMemDocument.argtypes = [POINTER(None), c_int, FPDF_BYTESTRING]
    FPDF_LoadMemDocument.restype = FPDF_DOCUMENT

if hasattr(_lib, "FPDF_LoadMemDocument64"):
    FPDF_LoadMemDocument64 = _lib.FPDF_LoadMemDocument64
    FPDF_LoadMemDocument64.argtypes = [POINTER(None), c_size_t, FPDF_BYTESTRING]
    FPDF_LoadMemDocument64.restype = FPDF_DOCUMENT

class struct_anon_4 (Structure):
    __slots__ = ['m_FileLen', 'm_GetBlock', 'm_Param']
struct_anon_4._fields_ = [
    ('m_FileLen', c_ulong),
    ('m_GetBlock', CFUNCTYPE(c_int, POINTER(None), c_ulong, POINTER(c_ubyte), c_ulong)),
    ('m_Param', POINTER(None)),
]
FPDF_FILEACCESS = struct_anon_4

class struct_FPDF_FILEHANDLER_ (Structure):
    __slots__ = ['clientData', 'Release', 'GetSize', 'ReadBlock', 'WriteBlock', 'Flush', 'Truncate']
struct_FPDF_FILEHANDLER_._fields_ = [
    ('clientData', POINTER(None)),
    ('Release', CFUNCTYPE(None, POINTER(None))),
    ('GetSize', CFUNCTYPE(FPDF_DWORD, POINTER(None))),
    ('ReadBlock', CFUNCTYPE(FPDF_RESULT, POINTER(None), FPDF_DWORD, POINTER(None), FPDF_DWORD)),
    ('WriteBlock', CFUNCTYPE(FPDF_RESULT, POINTER(None), FPDF_DWORD, POINTER(None), FPDF_DWORD)),
    ('Flush', CFUNCTYPE(FPDF_RESULT, POINTER(None))),
    ('Truncate', CFUNCTYPE(FPDF_RESULT, POINTER(None), FPDF_DWORD)),
]
FPDF_FILEHANDLER = struct_FPDF_FILEHANDLER_

if hasattr(_lib, "FPDF_LoadCustomDocument"):
    FPDF_LoadCustomDocument = _lib.FPDF_LoadCustomDocument
    FPDF_LoadCustomDocument.argtypes = [POINTER(FPDF_FILEACCESS), FPDF_BYTESTRING]
    FPDF_LoadCustomDocument.restype = FPDF_DOCUMENT

if hasattr(_lib, "FPDF_GetFileVersion"):
    FPDF_GetFileVersion = _lib.FPDF_GetFileVersion
    FPDF_GetFileVersion.argtypes = [FPDF_DOCUMENT, POINTER(c_int)]
    FPDF_GetFileVersion.restype = FPDF_BOOL

if hasattr(_lib, "FPDF_GetLastError"):
    FPDF_GetLastError = _lib.FPDF_GetLastError
    FPDF_GetLastError.argtypes = []
    FPDF_GetLastError.restype = c_ulong

if hasattr(_lib, "FPDF_DocumentHasValidCrossReferenceTable"):
    FPDF_DocumentHasValidCrossReferenceTable = _lib.FPDF_DocumentHasValidCrossReferenceTable
    FPDF_DocumentHasValidCrossReferenceTable.argtypes = [FPDF_DOCUMENT]
    FPDF_DocumentHasValidCrossReferenceTable.restype = FPDF_BOOL

if hasattr(_lib, "FPDF_GetTrailerEnds"):
    FPDF_GetTrailerEnds = _lib.FPDF_GetTrailerEnds
    FPDF_GetTrailerEnds.argtypes = [FPDF_DOCUMENT, POINTER(c_uint), c_ulong]
    FPDF_GetTrailerEnds.restype = c_ulong

if hasattr(_lib, "FPDF_GetDocPermissions"):
    FPDF_GetDocPermissions = _lib.FPDF_GetDocPermissions
    FPDF_GetDocPermissions.argtypes = [FPDF_DOCUMENT]
    FPDF_GetDocPermissions.restype = c_ulong

if hasattr(_lib, "FPDF_GetDocUserPermissions"):
    FPDF_GetDocUserPermissions = _lib.FPDF_GetDocUserPermissions
    FPDF_GetDocUserPermissions.argtypes = [FPDF_DOCUMENT]
    FPDF_GetDocUserPermissions.restype = c_ulong

if hasattr(_lib, "FPDF_GetSecurityHandlerRevision"):
    FPDF_GetSecurityHandlerRevision = _lib.FPDF_GetSecurityHandlerRevision
    FPDF_GetSecurityHandlerRevision.argtypes = [FPDF_DOCUMENT]
    FPDF_GetSecurityHandlerRevision.restype = c_int

if hasattr(_lib, "FPDF_GetPageCount"):
    FPDF_GetPageCount = _lib.FPDF_GetPageCount
    FPDF_GetPageCount.argtypes = [FPDF_DOCUMENT]
    FPDF_GetPageCount.restype = c_int

if hasattr(_lib, "FPDF_LoadPage"):
    FPDF_LoadPage = _lib.FPDF_LoadPage
    FPDF_LoadPage.argtypes = [FPDF_DOCUMENT, c_int]
    FPDF_LoadPage.restype = FPDF_PAGE

if hasattr(_lib, "FPDF_GetPageWidthF"):
    FPDF_GetPageWidthF = _lib.FPDF_GetPageWidthF
    FPDF_GetPageWidthF.argtypes = [FPDF_PAGE]
    FPDF_GetPageWidthF.restype = c_float

if hasattr(_lib, "FPDF_GetPageWidth"):
    FPDF_GetPageWidth = _lib.FPDF_GetPageWidth
    FPDF_GetPageWidth.argtypes = [FPDF_PAGE]
    FPDF_GetPageWidth.restype = c_double

if hasattr(_lib, "FPDF_GetPageHeightF"):
    FPDF_GetPageHeightF = _lib.FPDF_GetPageHeightF
    FPDF_GetPageHeightF.argtypes = [FPDF_PAGE]
    FPDF_GetPageHeightF.restype = c_float

if hasattr(_lib, "FPDF_GetPageHeight"):
    FPDF_GetPageHeight = _lib.FPDF_GetPageHeight
    FPDF_GetPageHeight.argtypes = [FPDF_PAGE]
    FPDF_GetPageHeight.restype = c_double

if hasattr(_lib, "FPDF_GetPageBoundingBox"):
    FPDF_GetPageBoundingBox = _lib.FPDF_GetPageBoundingBox
    FPDF_GetPageBoundingBox.argtypes = [FPDF_PAGE, POINTER(FS_RECTF)]
    FPDF_GetPageBoundingBox.restype = FPDF_BOOL

if hasattr(_lib, "FPDF_GetPageSizeByIndexF"):
    FPDF_GetPageSizeByIndexF = _lib.FPDF_GetPageSizeByIndexF
    FPDF_GetPageSizeByIndexF.argtypes = [FPDF_DOCUMENT, c_int, POINTER(FS_SIZEF)]
    FPDF_GetPageSizeByIndexF.restype = FPDF_BOOL

if hasattr(_lib, "FPDF_GetPageSizeByIndex"):
    FPDF_GetPageSizeByIndex = _lib.FPDF_GetPageSizeByIndex
    FPDF_GetPageSizeByIndex.argtypes = [FPDF_DOCUMENT, c_int, POINTER(c_double), POINTER(c_double)]
    FPDF_GetPageSizeByIndex.restype = c_int

class struct_FPDF_COLORSCHEME_ (Structure):
    __slots__ = ['path_fill_color', 'path_stroke_color', 'text_fill_color', 'text_stroke_color']
struct_FPDF_COLORSCHEME_._fields_ = [
    ('path_fill_color', FPDF_DWORD),
    ('path_stroke_color', FPDF_DWORD),
    ('text_fill_color', FPDF_DWORD),
    ('text_stroke_color', FPDF_DWORD),
]
FPDF_COLORSCHEME = struct_FPDF_COLORSCHEME_

if hasattr(_lib, "FPDF_RenderPageBitmap"):
    FPDF_RenderPageBitmap = _lib.FPDF_RenderPageBitmap
    FPDF_RenderPageBitmap.argtypes = [FPDF_BITMAP, FPDF_PAGE, c_int, c_int, c_int, c_int, c_int, c_int]
    FPDF_RenderPageBitmap.restype = None

if hasattr(_lib, "FPDF_RenderPageBitmapWithMatrix"):
    FPDF_RenderPageBitmapWithMatrix = _lib.FPDF_RenderPageBitmapWithMatrix
    FPDF_RenderPageBitmapWithMatrix.argtypes = [FPDF_BITMAP, FPDF_PAGE, POINTER(FS_MATRIX), POINTER(FS_RECTF), c_int]
    FPDF_RenderPageBitmapWithMatrix.restype = None

if hasattr(_lib, "FPDF_ClosePage"):
    FPDF_ClosePage = _lib.FPDF_ClosePage
    FPDF_ClosePage.argtypes = [FPDF_PAGE]
    FPDF_ClosePage.restype = None

if hasattr(_lib, "FPDF_CloseDocument"):
    FPDF_CloseDocument = _lib.FPDF_CloseDocument
    FPDF_CloseDocument.argtypes = [FPDF_DOCUMENT]
    FPDF_CloseDocument.restype = None

if hasattr(_lib, "FPDF_DeviceToPage"):
    FPDF_DeviceToPage = _lib.FPDF_DeviceToPage
    FPDF_DeviceToPage.argtypes = [FPDF_PAGE, c_int, c_int, c_int, c_int, c_int, c_int, c_int, POINTER(c_double), POINTER(c_double)]
    FPDF_DeviceToPage.restype = FPDF_BOOL

if hasattr(_lib, "FPDF_PageToDevice"):
    FPDF_PageToDevice = _lib.FPDF_PageToDevice
    FPDF_PageToDevice.argtypes = [FPDF_PAGE, c_int, c_int, c_int, c_int, c_int, c_double, c_double, POINTER(c_int), POINTER(c_int)]
    FPDF_PageToDevice.restype = FPDF_BOOL

if hasattr(_lib, "FPDFBitmap_Create"):
    FPDFBitmap_Create = _lib.FPDFBitmap_Create
    FPDFBitmap_Create.argtypes = [c_int, c_int, c_int]
    FPDFBitmap_Create.restype = FPDF_BITMAP

if hasattr(_lib, "FPDFBitmap_CreateEx"):
    FPDFBitmap_CreateEx = _lib.FPDFBitmap_CreateEx
    FPDFBitmap_CreateEx.argtypes = [c_int, c_int, c_int, POINTER(None), c_int]
    FPDFBitmap_CreateEx.restype = FPDF_BITMAP

if hasattr(_lib, "FPDFBitmap_GetFormat"):
    FPDFBitmap_GetFormat = _lib.FPDFBitmap_GetFormat
    FPDFBitmap_GetFormat.argtypes = [FPDF_BITMAP]
    FPDFBitmap_GetFormat.restype = c_int

if hasattr(_lib, "FPDFBitmap_FillRect"):
    FPDFBitmap_FillRect = _lib.FPDFBitmap_FillRect
    FPDFBitmap_FillRect.argtypes = [FPDF_BITMAP, c_int, c_int, c_int, c_int, FPDF_DWORD]
    FPDFBitmap_FillRect.restype = None

if hasattr(_lib, "FPDFBitmap_GetBuffer"):
    FPDFBitmap_GetBuffer = _lib.FPDFBitmap_GetBuffer
    FPDFBitmap_GetBuffer.argtypes = [FPDF_BITMAP]
    FPDFBitmap_GetBuffer.restype = POINTER(c_ubyte)
    FPDFBitmap_GetBuffer.errcheck = lambda v,*a : cast(v, c_void_p)

if hasattr(_lib, "FPDFBitmap_GetWidth"):
    FPDFBitmap_GetWidth = _lib.FPDFBitmap_GetWidth
    FPDFBitmap_GetWidth.argtypes = [FPDF_BITMAP]
    FPDFBitmap_GetWidth.restype = c_int

if hasattr(_lib, "FPDFBitmap_GetHeight"):
    FPDFBitmap_GetHeight = _lib.FPDFBitmap_GetHeight
    FPDFBitmap_GetHeight.argtypes = [FPDF_BITMAP]
    FPDFBitmap_GetHeight.restype = c_int

if hasattr(_lib, "FPDFBitmap_GetStride"):
    FPDFBitmap_GetStride = _lib.FPDFBitmap_GetStride
    FPDFBitmap_GetStride.argtypes = [FPDF_BITMAP]
    FPDFBitmap_GetStride.restype = c_int

if hasattr(_lib, "FPDFBitmap_Destroy"):
    FPDFBitmap_Destroy = _lib.FPDFBitmap_Destroy
    FPDFBitmap_Destroy.argtypes = [FPDF_BITMAP]
    FPDFBitmap_Destroy.restype = None

if hasattr(_lib, "FPDF_VIEWERREF_GetPrintScaling"):
    FPDF_VIEWERREF_GetPrintScaling = _lib.FPDF_VIEWERREF_GetPrintScaling
    FPDF_VIEWERREF_GetPrintScaling.argtypes = [FPDF_DOCUMENT]
    FPDF_VIEWERREF_GetPrintScaling.restype = FPDF_BOOL

if hasattr(_lib, "FPDF_VIEWERREF_GetNumCopies"):
    FPDF_VIEWERREF_GetNumCopies = _lib.FPDF_VIEWERREF_GetNumCopies
    FPDF_VIEWERREF_GetNumCopies.argtypes = [FPDF_DOCUMENT]
    FPDF_VIEWERREF_GetNumCopies.restype = c_int

if hasattr(_lib, "FPDF_VIEWERREF_GetPrintPageRange"):
    FPDF_VIEWERREF_GetPrintPageRange = _lib.FPDF_VIEWERREF_GetPrintPageRange
    FPDF_VIEWERREF_GetPrintPageRange.argtypes = [FPDF_DOCUMENT]
    FPDF_VIEWERREF_GetPrintPageRange.restype = FPDF_PAGERANGE

if hasattr(_lib, "FPDF_VIEWERREF_GetPrintPageRangeCount"):
    FPDF_VIEWERREF_GetPrintPageRangeCount = _lib.FPDF_VIEWERREF_GetPrintPageRangeCount
    FPDF_VIEWERREF_GetPrintPageRangeCount.argtypes = [FPDF_PAGERANGE]
    FPDF_VIEWERREF_GetPrintPageRangeCount.restype = c_size_t

if hasattr(_lib, "FPDF_VIEWERREF_GetPrintPageRangeElement"):
    FPDF_VIEWERREF_GetPrintPageRangeElement = _lib.FPDF_VIEWERREF_GetPrintPageRangeElement
    FPDF_VIEWERREF_GetPrintPageRangeElement.argtypes = [FPDF_PAGERANGE, c_size_t]
    FPDF_VIEWERREF_GetPrintPageRangeElement.restype = c_int

if hasattr(_lib, "FPDF_VIEWERREF_GetDuplex"):
    FPDF_VIEWERREF_GetDuplex = _lib.FPDF_VIEWERREF_GetDuplex
    FPDF_VIEWERREF_GetDuplex.argtypes = [FPDF_DOCUMENT]
    FPDF_VIEWERREF_GetDuplex.restype = FPDF_DUPLEXTYPE

if hasattr(_lib, "FPDF_VIEWERREF_GetName"):
    FPDF_VIEWERREF_GetName = _lib.FPDF_VIEWERREF_GetName
    FPDF_VIEWERREF_GetName.argtypes = [FPDF_DOCUMENT, FPDF_BYTESTRING, POINTER(c_char), c_ulong]
    FPDF_VIEWERREF_GetName.restype = c_ulong

if hasattr(_lib, "FPDF_CountNamedDests"):
    FPDF_CountNamedDests = _lib.FPDF_CountNamedDests
    FPDF_CountNamedDests.argtypes = [FPDF_DOCUMENT]
    FPDF_CountNamedDests.restype = FPDF_DWORD

if hasattr(_lib, "FPDF_GetNamedDestByName"):
    FPDF_GetNamedDestByName = _lib.FPDF_GetNamedDestByName
    FPDF_GetNamedDestByName.argtypes = [FPDF_DOCUMENT, FPDF_BYTESTRING]
    FPDF_GetNamedDestByName.restype = FPDF_DEST

if hasattr(_lib, "FPDF_GetNamedDest"):
    FPDF_GetNamedDest = _lib.FPDF_GetNamedDest
    FPDF_GetNamedDest.argtypes = [FPDF_DOCUMENT, c_int, POINTER(None), POINTER(c_long)]
    FPDF_GetNamedDest.restype = FPDF_DEST

if hasattr(_lib, "FPDF_GetXFAPacketCount"):
    FPDF_GetXFAPacketCount = _lib.FPDF_GetXFAPacketCount
    FPDF_GetXFAPacketCount.argtypes = [FPDF_DOCUMENT]
    FPDF_GetXFAPacketCount.restype = c_int

if hasattr(_lib, "FPDF_GetXFAPacketName"):
    FPDF_GetXFAPacketName = _lib.FPDF_GetXFAPacketName
    FPDF_GetXFAPacketName.argtypes = [FPDF_DOCUMENT, c_int, POINTER(None), c_ulong]
    FPDF_GetXFAPacketName.restype = c_ulong

if hasattr(_lib, "FPDF_GetXFAPacketContent"):
    FPDF_GetXFAPacketContent = _lib.FPDF_GetXFAPacketContent
    FPDF_GetXFAPacketContent.argtypes = [FPDF_DOCUMENT, c_int, POINTER(None), c_ulong, POINTER(c_ulong)]
    FPDF_GetXFAPacketContent.restype = FPDF_BOOL

class struct__IPDF_JsPlatform (Structure):
    __slots__ = ['version', 'app_alert', 'app_beep', 'app_response', 'Doc_getFilePath', 'Doc_mail', 'Doc_print', 'Doc_submitForm', 'Doc_gotoPage', 'Field_browse', 'm_pFormfillinfo', 'm_isolate', 'm_v8EmbedderSlot']
struct__IPDF_JsPlatform._fields_ = [
    ('version', c_int),
    ('app_alert', CFUNCTYPE(c_int, POINTER(struct__IPDF_JsPlatform), FPDF_WIDESTRING, FPDF_WIDESTRING, c_int, c_int)),
    ('app_beep', CFUNCTYPE(None, POINTER(struct__IPDF_JsPlatform), c_int)),
    ('app_response', CFUNCTYPE(c_int, POINTER(struct__IPDF_JsPlatform), FPDF_WIDESTRING, FPDF_WIDESTRING, FPDF_WIDESTRING, FPDF_WIDESTRING, FPDF_BOOL, POINTER(None), c_int)),
    ('Doc_getFilePath', CFUNCTYPE(c_int, POINTER(struct__IPDF_JsPlatform), POINTER(None), c_int)),
    ('Doc_mail', CFUNCTYPE(None, POINTER(struct__IPDF_JsPlatform), POINTER(None), c_int, FPDF_BOOL, FPDF_WIDESTRING, FPDF_WIDESTRING, FPDF_WIDESTRING, FPDF_WIDESTRING, FPDF_WIDESTRING)),
    ('Doc_print', CFUNCTYPE(None, POINTER(struct__IPDF_JsPlatform), FPDF_BOOL, c_int, c_int, FPDF_BOOL, FPDF_BOOL, FPDF_BOOL, FPDF_BOOL, FPDF_BOOL)),
    ('Doc_submitForm', CFUNCTYPE(None, POINTER(struct__IPDF_JsPlatform), POINTER(None), c_int, FPDF_WIDESTRING)),
    ('Doc_gotoPage', CFUNCTYPE(None, POINTER(struct__IPDF_JsPlatform), c_int)),
    ('Field_browse', CFUNCTYPE(c_int, POINTER(struct__IPDF_JsPlatform), POINTER(None), c_int)),
    ('m_pFormfillinfo', POINTER(None)),
    ('m_isolate', POINTER(None)),
    ('m_v8EmbedderSlot', c_uint),
]
IPDF_JSPLATFORM = struct__IPDF_JsPlatform
TimerCallback = CFUNCTYPE(None, c_int)

class struct__FPDF_SYSTEMTIME (Structure):
    __slots__ = ['wYear', 'wMonth', 'wDayOfWeek', 'wDay', 'wHour', 'wMinute', 'wSecond', 'wMilliseconds']
struct__FPDF_SYSTEMTIME._fields_ = [
    ('wYear', c_ushort),
    ('wMonth', c_ushort),
    ('wDayOfWeek', c_ushort),
    ('wDay', c_ushort),
    ('wHour', c_ushort),
    ('wMinute', c_ushort),
    ('wSecond', c_ushort),
    ('wMilliseconds', c_ushort),
]
FPDF_SYSTEMTIME = struct__FPDF_SYSTEMTIME

class struct__FPDF_FORMFILLINFO (Structure):
    __slots__ = ['version', 'Release', 'FFI_Invalidate', 'FFI_OutputSelectedRect', 'FFI_SetCursor', 'FFI_SetTimer', 'FFI_KillTimer', 'FFI_GetLocalTime', 'FFI_OnChange', 'FFI_GetPage', 'FFI_GetCurrentPage', 'FFI_GetRotation', 'FFI_ExecuteNamedAction', 'FFI_SetTextFieldFocus', 'FFI_DoURIAction', 'FFI_DoGoToAction', 'm_pJsPlatform', 'xfa_disabled', 'FFI_DisplayCaret', 'FFI_GetCurrentPageIndex', 'FFI_SetCurrentPage', 'FFI_GotoURL', 'FFI_GetPageViewRect', 'FFI_PageEvent', 'FFI_PopupMenu', 'FFI_OpenFile', 'FFI_EmailTo', 'FFI_UploadTo', 'FFI_GetPlatform', 'FFI_GetLanguage', 'FFI_DownloadFromURL', 'FFI_PostRequestURL', 'FFI_PutRequestURL', 'FFI_OnFocusChange', 'FFI_DoURIActionWithKeyboardModifier']
struct__FPDF_FORMFILLINFO._fields_ = [
    ('version', c_int),
    ('Release', CFUNCTYPE(None, POINTER(struct__FPDF_FORMFILLINFO))),
    ('FFI_Invalidate', CFUNCTYPE(None, POINTER(struct__FPDF_FORMFILLINFO), FPDF_PAGE, c_double, c_double, c_double, c_double)),
    ('FFI_OutputSelectedRect', CFUNCTYPE(None, POINTER(struct__FPDF_FORMFILLINFO), FPDF_PAGE, c_double, c_double, c_double, c_double)),
    ('FFI_SetCursor', CFUNCTYPE(None, POINTER(struct__FPDF_FORMFILLINFO), c_int)),
    ('FFI_SetTimer', CFUNCTYPE(c_int, POINTER(struct__FPDF_FORMFILLINFO), c_int, TimerCallback)),
    ('FFI_KillTimer', CFUNCTYPE(None, POINTER(struct__FPDF_FORMFILLINFO), c_int)),
    ('FFI_GetLocalTime', CFUNCTYPE(FPDF_SYSTEMTIME, POINTER(struct__FPDF_FORMFILLINFO))),
    ('FFI_OnChange', CFUNCTYPE(None, POINTER(struct__FPDF_FORMFILLINFO))),
    ('FFI_GetPage', CFUNCTYPE(FPDF_PAGE, POINTER(struct__FPDF_FORMFILLINFO), FPDF_DOCUMENT, c_int)),
    ('FFI_GetCurrentPage', CFUNCTYPE(FPDF_PAGE, POINTER(struct__FPDF_FORMFILLINFO), FPDF_DOCUMENT)),
    ('FFI_GetRotation', CFUNCTYPE(c_int, POINTER(struct__FPDF_FORMFILLINFO), FPDF_PAGE)),
    ('FFI_ExecuteNamedAction', CFUNCTYPE(None, POINTER(struct__FPDF_FORMFILLINFO), FPDF_BYTESTRING)),
    ('FFI_SetTextFieldFocus', CFUNCTYPE(None, POINTER(struct__FPDF_FORMFILLINFO), FPDF_WIDESTRING, FPDF_DWORD, FPDF_BOOL)),
    ('FFI_DoURIAction', CFUNCTYPE(None, POINTER(struct__FPDF_FORMFILLINFO), FPDF_BYTESTRING)),
    ('FFI_DoGoToAction', CFUNCTYPE(None, POINTER(struct__FPDF_FORMFILLINFO), c_int, c_int, POINTER(c_float), c_int)),
    ('m_pJsPlatform', POINTER(IPDF_JSPLATFORM)),
    ('xfa_disabled', FPDF_BOOL),
    ('FFI_DisplayCaret', CFUNCTYPE(None, POINTER(struct__FPDF_FORMFILLINFO), FPDF_PAGE, FPDF_BOOL, c_double, c_double, c_double, c_double)),
    ('FFI_GetCurrentPageIndex', CFUNCTYPE(c_int, POINTER(struct__FPDF_FORMFILLINFO), FPDF_DOCUMENT)),
    ('FFI_SetCurrentPage', CFUNCTYPE(None, POINTER(struct__FPDF_FORMFILLINFO), FPDF_DOCUMENT, c_int)),
    ('FFI_GotoURL', CFUNCTYPE(None, POINTER(struct__FPDF_FORMFILLINFO), FPDF_DOCUMENT, FPDF_WIDESTRING)),
    ('FFI_GetPageViewRect', CFUNCTYPE(None, POINTER(struct__FPDF_FORMFILLINFO), FPDF_PAGE, POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double))),
    ('FFI_PageEvent', CFUNCTYPE(None, POINTER(struct__FPDF_FORMFILLINFO), c_int, FPDF_DWORD)),
    ('FFI_PopupMenu', CFUNCTYPE(FPDF_BOOL, POINTER(struct__FPDF_FORMFILLINFO), FPDF_PAGE, FPDF_WIDGET, c_int, c_float, c_float)),
    ('FFI_OpenFile', CFUNCTYPE(POINTER(FPDF_FILEHANDLER), POINTER(struct__FPDF_FORMFILLINFO), c_int, FPDF_WIDESTRING, POINTER(c_char))),
    ('FFI_EmailTo', CFUNCTYPE(None, POINTER(struct__FPDF_FORMFILLINFO), POINTER(FPDF_FILEHANDLER), FPDF_WIDESTRING, FPDF_WIDESTRING, FPDF_WIDESTRING, FPDF_WIDESTRING, FPDF_WIDESTRING)),
    ('FFI_UploadTo', CFUNCTYPE(None, POINTER(struct__FPDF_FORMFILLINFO), POINTER(FPDF_FILEHANDLER), c_int, FPDF_WIDESTRING)),
    ('FFI_GetPlatform', CFUNCTYPE(c_int, POINTER(struct__FPDF_FORMFILLINFO), POINTER(None), c_int)),
    ('FFI_GetLanguage', CFUNCTYPE(c_int, POINTER(struct__FPDF_FORMFILLINFO), POINTER(None), c_int)),
    ('FFI_DownloadFromURL', CFUNCTYPE(POINTER(FPDF_FILEHANDLER), POINTER(struct__FPDF_FORMFILLINFO), FPDF_WIDESTRING)),
    ('FFI_PostRequestURL', CFUNCTYPE(FPDF_BOOL, POINTER(struct__FPDF_FORMFILLINFO), FPDF_WIDESTRING, FPDF_WIDESTRING, FPDF_WIDESTRING, FPDF_WIDESTRING, FPDF_WIDESTRING, POINTER(FPDF_BSTR))),
    ('FFI_PutRequestURL', CFUNCTYPE(FPDF_BOOL, POINTER(struct__FPDF_FORMFILLINFO), FPDF_WIDESTRING, FPDF_WIDESTRING, FPDF_WIDESTRING)),
    ('FFI_OnFocusChange', CFUNCTYPE(None, POINTER(struct__FPDF_FORMFILLINFO), FPDF_ANNOTATION, c_int)),
    ('FFI_DoURIActionWithKeyboardModifier', CFUNCTYPE(None, POINTER(struct__FPDF_FORMFILLINFO), FPDF_BYTESTRING, c_int)),
]
FPDF_FORMFILLINFO = struct__FPDF_FORMFILLINFO

if hasattr(_lib, "FPDFDOC_InitFormFillEnvironment"):
    FPDFDOC_InitFormFillEnvironment = _lib.FPDFDOC_InitFormFillEnvironment
    FPDFDOC_InitFormFillEnvironment.argtypes = [FPDF_DOCUMENT, POINTER(FPDF_FORMFILLINFO)]
    FPDFDOC_InitFormFillEnvironment.restype = FPDF_FORMHANDLE

if hasattr(_lib, "FPDFDOC_ExitFormFillEnvironment"):
    FPDFDOC_ExitFormFillEnvironment = _lib.FPDFDOC_ExitFormFillEnvironment
    FPDFDOC_ExitFormFillEnvironment.argtypes = [FPDF_FORMHANDLE]
    FPDFDOC_ExitFormFillEnvironment.restype = None

if hasattr(_lib, "FORM_OnAfterLoadPage"):
    FORM_OnAfterLoadPage = _lib.FORM_OnAfterLoadPage
    FORM_OnAfterLoadPage.argtypes = [FPDF_PAGE, FPDF_FORMHANDLE]
    FORM_OnAfterLoadPage.restype = None

if hasattr(_lib, "FORM_OnBeforeClosePage"):
    FORM_OnBeforeClosePage = _lib.FORM_OnBeforeClosePage
    FORM_OnBeforeClosePage.argtypes = [FPDF_PAGE, FPDF_FORMHANDLE]
    FORM_OnBeforeClosePage.restype = None

if hasattr(_lib, "FORM_DoDocumentJSAction"):
    FORM_DoDocumentJSAction = _lib.FORM_DoDocumentJSAction
    FORM_DoDocumentJSAction.argtypes = [FPDF_FORMHANDLE]
    FORM_DoDocumentJSAction.restype = None

if hasattr(_lib, "FORM_DoDocumentOpenAction"):
    FORM_DoDocumentOpenAction = _lib.FORM_DoDocumentOpenAction
    FORM_DoDocumentOpenAction.argtypes = [FPDF_FORMHANDLE]
    FORM_DoDocumentOpenAction.restype = None

if hasattr(_lib, "FORM_DoDocumentAAction"):
    FORM_DoDocumentAAction = _lib.FORM_DoDocumentAAction
    FORM_DoDocumentAAction.argtypes = [FPDF_FORMHANDLE, c_int]
    FORM_DoDocumentAAction.restype = None

if hasattr(_lib, "FORM_DoPageAAction"):
    FORM_DoPageAAction = _lib.FORM_DoPageAAction
    FORM_DoPageAAction.argtypes = [FPDF_PAGE, FPDF_FORMHANDLE, c_int]
    FORM_DoPageAAction.restype = None

if hasattr(_lib, "FORM_OnMouseMove"):
    FORM_OnMouseMove = _lib.FORM_OnMouseMove
    FORM_OnMouseMove.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, c_int, c_double, c_double]
    FORM_OnMouseMove.restype = FPDF_BOOL

if hasattr(_lib, "FORM_OnMouseWheel"):
    FORM_OnMouseWheel = _lib.FORM_OnMouseWheel
    FORM_OnMouseWheel.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, c_int, POINTER(FS_POINTF), c_int, c_int]
    FORM_OnMouseWheel.restype = FPDF_BOOL

if hasattr(_lib, "FORM_OnFocus"):
    FORM_OnFocus = _lib.FORM_OnFocus
    FORM_OnFocus.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, c_int, c_double, c_double]
    FORM_OnFocus.restype = FPDF_BOOL

if hasattr(_lib, "FORM_OnLButtonDown"):
    FORM_OnLButtonDown = _lib.FORM_OnLButtonDown
    FORM_OnLButtonDown.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, c_int, c_double, c_double]
    FORM_OnLButtonDown.restype = FPDF_BOOL

if hasattr(_lib, "FORM_OnRButtonDown"):
    FORM_OnRButtonDown = _lib.FORM_OnRButtonDown
    FORM_OnRButtonDown.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, c_int, c_double, c_double]
    FORM_OnRButtonDown.restype = FPDF_BOOL

if hasattr(_lib, "FORM_OnLButtonUp"):
    FORM_OnLButtonUp = _lib.FORM_OnLButtonUp
    FORM_OnLButtonUp.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, c_int, c_double, c_double]
    FORM_OnLButtonUp.restype = FPDF_BOOL

if hasattr(_lib, "FORM_OnRButtonUp"):
    FORM_OnRButtonUp = _lib.FORM_OnRButtonUp
    FORM_OnRButtonUp.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, c_int, c_double, c_double]
    FORM_OnRButtonUp.restype = FPDF_BOOL

if hasattr(_lib, "FORM_OnLButtonDoubleClick"):
    FORM_OnLButtonDoubleClick = _lib.FORM_OnLButtonDoubleClick
    FORM_OnLButtonDoubleClick.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, c_int, c_double, c_double]
    FORM_OnLButtonDoubleClick.restype = FPDF_BOOL

if hasattr(_lib, "FORM_OnKeyDown"):
    FORM_OnKeyDown = _lib.FORM_OnKeyDown
    FORM_OnKeyDown.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, c_int, c_int]
    FORM_OnKeyDown.restype = FPDF_BOOL

if hasattr(_lib, "FORM_OnKeyUp"):
    FORM_OnKeyUp = _lib.FORM_OnKeyUp
    FORM_OnKeyUp.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, c_int, c_int]
    FORM_OnKeyUp.restype = FPDF_BOOL

if hasattr(_lib, "FORM_OnChar"):
    FORM_OnChar = _lib.FORM_OnChar
    FORM_OnChar.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, c_int, c_int]
    FORM_OnChar.restype = FPDF_BOOL

if hasattr(_lib, "FORM_GetFocusedText"):
    FORM_GetFocusedText = _lib.FORM_GetFocusedText
    FORM_GetFocusedText.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, POINTER(None), c_ulong]
    FORM_GetFocusedText.restype = c_ulong

if hasattr(_lib, "FORM_GetSelectedText"):
    FORM_GetSelectedText = _lib.FORM_GetSelectedText
    FORM_GetSelectedText.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, POINTER(None), c_ulong]
    FORM_GetSelectedText.restype = c_ulong

if hasattr(_lib, "FORM_ReplaceAndKeepSelection"):
    FORM_ReplaceAndKeepSelection = _lib.FORM_ReplaceAndKeepSelection
    FORM_ReplaceAndKeepSelection.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, FPDF_WIDESTRING]
    FORM_ReplaceAndKeepSelection.restype = None

if hasattr(_lib, "FORM_ReplaceSelection"):
    FORM_ReplaceSelection = _lib.FORM_ReplaceSelection
    FORM_ReplaceSelection.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, FPDF_WIDESTRING]
    FORM_ReplaceSelection.restype = None

if hasattr(_lib, "FORM_SelectAllText"):
    FORM_SelectAllText = _lib.FORM_SelectAllText
    FORM_SelectAllText.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE]
    FORM_SelectAllText.restype = FPDF_BOOL

if hasattr(_lib, "FORM_CanUndo"):
    FORM_CanUndo = _lib.FORM_CanUndo
    FORM_CanUndo.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE]
    FORM_CanUndo.restype = FPDF_BOOL

if hasattr(_lib, "FORM_CanRedo"):
    FORM_CanRedo = _lib.FORM_CanRedo
    FORM_CanRedo.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE]
    FORM_CanRedo.restype = FPDF_BOOL

if hasattr(_lib, "FORM_Undo"):
    FORM_Undo = _lib.FORM_Undo
    FORM_Undo.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE]
    FORM_Undo.restype = FPDF_BOOL

if hasattr(_lib, "FORM_Redo"):
    FORM_Redo = _lib.FORM_Redo
    FORM_Redo.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE]
    FORM_Redo.restype = FPDF_BOOL

if hasattr(_lib, "FORM_ForceToKillFocus"):
    FORM_ForceToKillFocus = _lib.FORM_ForceToKillFocus
    FORM_ForceToKillFocus.argtypes = [FPDF_FORMHANDLE]
    FORM_ForceToKillFocus.restype = FPDF_BOOL

if hasattr(_lib, "FORM_GetFocusedAnnot"):
    FORM_GetFocusedAnnot = _lib.FORM_GetFocusedAnnot
    FORM_GetFocusedAnnot.argtypes = [FPDF_FORMHANDLE, POINTER(c_int), POINTER(FPDF_ANNOTATION)]
    FORM_GetFocusedAnnot.restype = FPDF_BOOL

if hasattr(_lib, "FORM_SetFocusedAnnot"):
    FORM_SetFocusedAnnot = _lib.FORM_SetFocusedAnnot
    FORM_SetFocusedAnnot.argtypes = [FPDF_FORMHANDLE, FPDF_ANNOTATION]
    FORM_SetFocusedAnnot.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPage_HasFormFieldAtPoint"):
    FPDFPage_HasFormFieldAtPoint = _lib.FPDFPage_HasFormFieldAtPoint
    FPDFPage_HasFormFieldAtPoint.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, c_double, c_double]
    FPDFPage_HasFormFieldAtPoint.restype = c_int

if hasattr(_lib, "FPDFPage_FormFieldZOrderAtPoint"):
    FPDFPage_FormFieldZOrderAtPoint = _lib.FPDFPage_FormFieldZOrderAtPoint
    FPDFPage_FormFieldZOrderAtPoint.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, c_double, c_double]
    FPDFPage_FormFieldZOrderAtPoint.restype = c_int

if hasattr(_lib, "FPDF_SetFormFieldHighlightColor"):
    FPDF_SetFormFieldHighlightColor = _lib.FPDF_SetFormFieldHighlightColor
    FPDF_SetFormFieldHighlightColor.argtypes = [FPDF_FORMHANDLE, c_int, c_ulong]
    FPDF_SetFormFieldHighlightColor.restype = None

if hasattr(_lib, "FPDF_SetFormFieldHighlightAlpha"):
    FPDF_SetFormFieldHighlightAlpha = _lib.FPDF_SetFormFieldHighlightAlpha
    FPDF_SetFormFieldHighlightAlpha.argtypes = [FPDF_FORMHANDLE, c_ubyte]
    FPDF_SetFormFieldHighlightAlpha.restype = None

if hasattr(_lib, "FPDF_RemoveFormFieldHighlight"):
    FPDF_RemoveFormFieldHighlight = _lib.FPDF_RemoveFormFieldHighlight
    FPDF_RemoveFormFieldHighlight.argtypes = [FPDF_FORMHANDLE]
    FPDF_RemoveFormFieldHighlight.restype = None

if hasattr(_lib, "FPDF_FFLDraw"):
    FPDF_FFLDraw = _lib.FPDF_FFLDraw
    FPDF_FFLDraw.argtypes = [FPDF_FORMHANDLE, FPDF_BITMAP, FPDF_PAGE, c_int, c_int, c_int, c_int, c_int, c_int]
    FPDF_FFLDraw.restype = None

if hasattr(_lib, "FPDF_GetFormType"):
    FPDF_GetFormType = _lib.FPDF_GetFormType
    FPDF_GetFormType.argtypes = [FPDF_DOCUMENT]
    FPDF_GetFormType.restype = c_int

if hasattr(_lib, "FORM_SetIndexSelected"):
    FORM_SetIndexSelected = _lib.FORM_SetIndexSelected
    FORM_SetIndexSelected.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, c_int, FPDF_BOOL]
    FORM_SetIndexSelected.restype = FPDF_BOOL

if hasattr(_lib, "FORM_IsIndexSelected"):
    FORM_IsIndexSelected = _lib.FORM_IsIndexSelected
    FORM_IsIndexSelected.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, c_int]
    FORM_IsIndexSelected.restype = FPDF_BOOL

if hasattr(_lib, "FPDF_LoadXFA"):
    FPDF_LoadXFA = _lib.FPDF_LoadXFA
    FPDF_LoadXFA.argtypes = [FPDF_DOCUMENT]
    FPDF_LoadXFA.restype = FPDF_BOOL
enum_FPDFANNOT_COLORTYPE = c_int
FPDFANNOT_COLORTYPE_Color = 0
FPDFANNOT_COLORTYPE_InteriorColor = (FPDFANNOT_COLORTYPE_Color + 1)
FPDFANNOT_COLORTYPE = enum_FPDFANNOT_COLORTYPE

if hasattr(_lib, "FPDFAnnot_IsSupportedSubtype"):
    FPDFAnnot_IsSupportedSubtype = _lib.FPDFAnnot_IsSupportedSubtype
    FPDFAnnot_IsSupportedSubtype.argtypes = [FPDF_ANNOTATION_SUBTYPE]
    FPDFAnnot_IsSupportedSubtype.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPage_CreateAnnot"):
    FPDFPage_CreateAnnot = _lib.FPDFPage_CreateAnnot
    FPDFPage_CreateAnnot.argtypes = [FPDF_PAGE, FPDF_ANNOTATION_SUBTYPE]
    FPDFPage_CreateAnnot.restype = FPDF_ANNOTATION

if hasattr(_lib, "FPDFPage_GetAnnotCount"):
    FPDFPage_GetAnnotCount = _lib.FPDFPage_GetAnnotCount
    FPDFPage_GetAnnotCount.argtypes = [FPDF_PAGE]
    FPDFPage_GetAnnotCount.restype = c_int

if hasattr(_lib, "FPDFPage_GetAnnot"):
    FPDFPage_GetAnnot = _lib.FPDFPage_GetAnnot
    FPDFPage_GetAnnot.argtypes = [FPDF_PAGE, c_int]
    FPDFPage_GetAnnot.restype = FPDF_ANNOTATION

if hasattr(_lib, "FPDFPage_GetAnnotIndex"):
    FPDFPage_GetAnnotIndex = _lib.FPDFPage_GetAnnotIndex
    FPDFPage_GetAnnotIndex.argtypes = [FPDF_PAGE, FPDF_ANNOTATION]
    FPDFPage_GetAnnotIndex.restype = c_int

if hasattr(_lib, "FPDFPage_CloseAnnot"):
    FPDFPage_CloseAnnot = _lib.FPDFPage_CloseAnnot
    FPDFPage_CloseAnnot.argtypes = [FPDF_ANNOTATION]
    FPDFPage_CloseAnnot.restype = None

if hasattr(_lib, "FPDFPage_RemoveAnnot"):
    FPDFPage_RemoveAnnot = _lib.FPDFPage_RemoveAnnot
    FPDFPage_RemoveAnnot.argtypes = [FPDF_PAGE, c_int]
    FPDFPage_RemoveAnnot.restype = FPDF_BOOL

if hasattr(_lib, "FPDFAnnot_GetSubtype"):
    FPDFAnnot_GetSubtype = _lib.FPDFAnnot_GetSubtype
    FPDFAnnot_GetSubtype.argtypes = [FPDF_ANNOTATION]
    FPDFAnnot_GetSubtype.restype = FPDF_ANNOTATION_SUBTYPE

if hasattr(_lib, "FPDFAnnot_IsObjectSupportedSubtype"):
    FPDFAnnot_IsObjectSupportedSubtype = _lib.FPDFAnnot_IsObjectSupportedSubtype
    FPDFAnnot_IsObjectSupportedSubtype.argtypes = [FPDF_ANNOTATION_SUBTYPE]
    FPDFAnnot_IsObjectSupportedSubtype.restype = FPDF_BOOL

if hasattr(_lib, "FPDFAnnot_UpdateObject"):
    FPDFAnnot_UpdateObject = _lib.FPDFAnnot_UpdateObject
    FPDFAnnot_UpdateObject.argtypes = [FPDF_ANNOTATION, FPDF_PAGEOBJECT]
    FPDFAnnot_UpdateObject.restype = FPDF_BOOL

if hasattr(_lib, "FPDFAnnot_AddInkStroke"):
    FPDFAnnot_AddInkStroke = _lib.FPDFAnnot_AddInkStroke
    FPDFAnnot_AddInkStroke.argtypes = [FPDF_ANNOTATION, POINTER(FS_POINTF), c_size_t]
    FPDFAnnot_AddInkStroke.restype = c_int

if hasattr(_lib, "FPDFAnnot_RemoveInkList"):
    FPDFAnnot_RemoveInkList = _lib.FPDFAnnot_RemoveInkList
    FPDFAnnot_RemoveInkList.argtypes = [FPDF_ANNOTATION]
    FPDFAnnot_RemoveInkList.restype = FPDF_BOOL

if hasattr(_lib, "FPDFAnnot_AppendObject"):
    FPDFAnnot_AppendObject = _lib.FPDFAnnot_AppendObject
    FPDFAnnot_AppendObject.argtypes = [FPDF_ANNOTATION, FPDF_PAGEOBJECT]
    FPDFAnnot_AppendObject.restype = FPDF_BOOL

if hasattr(_lib, "FPDFAnnot_GetObjectCount"):
    FPDFAnnot_GetObjectCount = _lib.FPDFAnnot_GetObjectCount
    FPDFAnnot_GetObjectCount.argtypes = [FPDF_ANNOTATION]
    FPDFAnnot_GetObjectCount.restype = c_int

if hasattr(_lib, "FPDFAnnot_GetObject"):
    FPDFAnnot_GetObject = _lib.FPDFAnnot_GetObject
    FPDFAnnot_GetObject.argtypes = [FPDF_ANNOTATION, c_int]
    FPDFAnnot_GetObject.restype = FPDF_PAGEOBJECT

if hasattr(_lib, "FPDFAnnot_RemoveObject"):
    FPDFAnnot_RemoveObject = _lib.FPDFAnnot_RemoveObject
    FPDFAnnot_RemoveObject.argtypes = [FPDF_ANNOTATION, c_int]
    FPDFAnnot_RemoveObject.restype = FPDF_BOOL

if hasattr(_lib, "FPDFAnnot_SetColor"):
    FPDFAnnot_SetColor = _lib.FPDFAnnot_SetColor
    FPDFAnnot_SetColor.argtypes = [FPDF_ANNOTATION, FPDFANNOT_COLORTYPE, c_uint, c_uint, c_uint, c_uint]
    FPDFAnnot_SetColor.restype = FPDF_BOOL

if hasattr(_lib, "FPDFAnnot_GetColor"):
    FPDFAnnot_GetColor = _lib.FPDFAnnot_GetColor
    FPDFAnnot_GetColor.argtypes = [FPDF_ANNOTATION, FPDFANNOT_COLORTYPE, POINTER(c_uint), POINTER(c_uint), POINTER(c_uint), POINTER(c_uint)]
    FPDFAnnot_GetColor.restype = FPDF_BOOL

if hasattr(_lib, "FPDFAnnot_HasAttachmentPoints"):
    FPDFAnnot_HasAttachmentPoints = _lib.FPDFAnnot_HasAttachmentPoints
    FPDFAnnot_HasAttachmentPoints.argtypes = [FPDF_ANNOTATION]
    FPDFAnnot_HasAttachmentPoints.restype = FPDF_BOOL

if hasattr(_lib, "FPDFAnnot_SetAttachmentPoints"):
    FPDFAnnot_SetAttachmentPoints = _lib.FPDFAnnot_SetAttachmentPoints
    FPDFAnnot_SetAttachmentPoints.argtypes = [FPDF_ANNOTATION, c_size_t, POINTER(FS_QUADPOINTSF)]
    FPDFAnnot_SetAttachmentPoints.restype = FPDF_BOOL

if hasattr(_lib, "FPDFAnnot_AppendAttachmentPoints"):
    FPDFAnnot_AppendAttachmentPoints = _lib.FPDFAnnot_AppendAttachmentPoints
    FPDFAnnot_AppendAttachmentPoints.argtypes = [FPDF_ANNOTATION, POINTER(FS_QUADPOINTSF)]
    FPDFAnnot_AppendAttachmentPoints.restype = FPDF_BOOL

if hasattr(_lib, "FPDFAnnot_CountAttachmentPoints"):
    FPDFAnnot_CountAttachmentPoints = _lib.FPDFAnnot_CountAttachmentPoints
    FPDFAnnot_CountAttachmentPoints.argtypes = [FPDF_ANNOTATION]
    FPDFAnnot_CountAttachmentPoints.restype = c_size_t

if hasattr(_lib, "FPDFAnnot_GetAttachmentPoints"):
    FPDFAnnot_GetAttachmentPoints = _lib.FPDFAnnot_GetAttachmentPoints
    FPDFAnnot_GetAttachmentPoints.argtypes = [FPDF_ANNOTATION, c_size_t, POINTER(FS_QUADPOINTSF)]
    FPDFAnnot_GetAttachmentPoints.restype = FPDF_BOOL

if hasattr(_lib, "FPDFAnnot_SetRect"):
    FPDFAnnot_SetRect = _lib.FPDFAnnot_SetRect
    FPDFAnnot_SetRect.argtypes = [FPDF_ANNOTATION, POINTER(FS_RECTF)]
    FPDFAnnot_SetRect.restype = FPDF_BOOL

if hasattr(_lib, "FPDFAnnot_GetRect"):
    FPDFAnnot_GetRect = _lib.FPDFAnnot_GetRect
    FPDFAnnot_GetRect.argtypes = [FPDF_ANNOTATION, POINTER(FS_RECTF)]
    FPDFAnnot_GetRect.restype = FPDF_BOOL

if hasattr(_lib, "FPDFAnnot_GetVertices"):
    FPDFAnnot_GetVertices = _lib.FPDFAnnot_GetVertices
    FPDFAnnot_GetVertices.argtypes = [FPDF_ANNOTATION, POINTER(FS_POINTF), c_ulong]
    FPDFAnnot_GetVertices.restype = c_ulong

if hasattr(_lib, "FPDFAnnot_GetInkListCount"):
    FPDFAnnot_GetInkListCount = _lib.FPDFAnnot_GetInkListCount
    FPDFAnnot_GetInkListCount.argtypes = [FPDF_ANNOTATION]
    FPDFAnnot_GetInkListCount.restype = c_ulong

if hasattr(_lib, "FPDFAnnot_GetInkListPath"):
    FPDFAnnot_GetInkListPath = _lib.FPDFAnnot_GetInkListPath
    FPDFAnnot_GetInkListPath.argtypes = [FPDF_ANNOTATION, c_ulong, POINTER(FS_POINTF), c_ulong]
    FPDFAnnot_GetInkListPath.restype = c_ulong

if hasattr(_lib, "FPDFAnnot_GetLine"):
    FPDFAnnot_GetLine = _lib.FPDFAnnot_GetLine
    FPDFAnnot_GetLine.argtypes = [FPDF_ANNOTATION, POINTER(FS_POINTF), POINTER(FS_POINTF)]
    FPDFAnnot_GetLine.restype = FPDF_BOOL

if hasattr(_lib, "FPDFAnnot_SetBorder"):
    FPDFAnnot_SetBorder = _lib.FPDFAnnot_SetBorder
    FPDFAnnot_SetBorder.argtypes = [FPDF_ANNOTATION, c_float, c_float, c_float]
    FPDFAnnot_SetBorder.restype = FPDF_BOOL

if hasattr(_lib, "FPDFAnnot_GetBorder"):
    FPDFAnnot_GetBorder = _lib.FPDFAnnot_GetBorder
    FPDFAnnot_GetBorder.argtypes = [FPDF_ANNOTATION, POINTER(c_float), POINTER(c_float), POINTER(c_float)]
    FPDFAnnot_GetBorder.restype = FPDF_BOOL

if hasattr(_lib, "FPDFAnnot_GetFormAdditionalActionJavaScript"):
    FPDFAnnot_GetFormAdditionalActionJavaScript = _lib.FPDFAnnot_GetFormAdditionalActionJavaScript
    FPDFAnnot_GetFormAdditionalActionJavaScript.argtypes = [FPDF_FORMHANDLE, FPDF_ANNOTATION, c_int, POINTER(FPDF_WCHAR), c_ulong]
    FPDFAnnot_GetFormAdditionalActionJavaScript.restype = c_ulong

if hasattr(_lib, "FPDFAnnot_HasKey"):
    FPDFAnnot_HasKey = _lib.FPDFAnnot_HasKey
    FPDFAnnot_HasKey.argtypes = [FPDF_ANNOTATION, FPDF_BYTESTRING]
    FPDFAnnot_HasKey.restype = FPDF_BOOL

if hasattr(_lib, "FPDFAnnot_GetValueType"):
    FPDFAnnot_GetValueType = _lib.FPDFAnnot_GetValueType
    FPDFAnnot_GetValueType.argtypes = [FPDF_ANNOTATION, FPDF_BYTESTRING]
    FPDFAnnot_GetValueType.restype = FPDF_OBJECT_TYPE

if hasattr(_lib, "FPDFAnnot_SetStringValue"):
    FPDFAnnot_SetStringValue = _lib.FPDFAnnot_SetStringValue
    FPDFAnnot_SetStringValue.argtypes = [FPDF_ANNOTATION, FPDF_BYTESTRING, FPDF_WIDESTRING]
    FPDFAnnot_SetStringValue.restype = FPDF_BOOL

if hasattr(_lib, "FPDFAnnot_GetStringValue"):
    FPDFAnnot_GetStringValue = _lib.FPDFAnnot_GetStringValue
    FPDFAnnot_GetStringValue.argtypes = [FPDF_ANNOTATION, FPDF_BYTESTRING, POINTER(FPDF_WCHAR), c_ulong]
    FPDFAnnot_GetStringValue.restype = c_ulong

if hasattr(_lib, "FPDFAnnot_GetNumberValue"):
    FPDFAnnot_GetNumberValue = _lib.FPDFAnnot_GetNumberValue
    FPDFAnnot_GetNumberValue.argtypes = [FPDF_ANNOTATION, FPDF_BYTESTRING, POINTER(c_float)]
    FPDFAnnot_GetNumberValue.restype = FPDF_BOOL

if hasattr(_lib, "FPDFAnnot_SetAP"):
    FPDFAnnot_SetAP = _lib.FPDFAnnot_SetAP
    FPDFAnnot_SetAP.argtypes = [FPDF_ANNOTATION, FPDF_ANNOT_APPEARANCEMODE, FPDF_WIDESTRING]
    FPDFAnnot_SetAP.restype = FPDF_BOOL

if hasattr(_lib, "FPDFAnnot_GetAP"):
    FPDFAnnot_GetAP = _lib.FPDFAnnot_GetAP
    FPDFAnnot_GetAP.argtypes = [FPDF_ANNOTATION, FPDF_ANNOT_APPEARANCEMODE, POINTER(FPDF_WCHAR), c_ulong]
    FPDFAnnot_GetAP.restype = c_ulong

if hasattr(_lib, "FPDFAnnot_GetLinkedAnnot"):
    FPDFAnnot_GetLinkedAnnot = _lib.FPDFAnnot_GetLinkedAnnot
    FPDFAnnot_GetLinkedAnnot.argtypes = [FPDF_ANNOTATION, FPDF_BYTESTRING]
    FPDFAnnot_GetLinkedAnnot.restype = FPDF_ANNOTATION

if hasattr(_lib, "FPDFAnnot_GetFlags"):
    FPDFAnnot_GetFlags = _lib.FPDFAnnot_GetFlags
    FPDFAnnot_GetFlags.argtypes = [FPDF_ANNOTATION]
    FPDFAnnot_GetFlags.restype = c_int

if hasattr(_lib, "FPDFAnnot_SetFlags"):
    FPDFAnnot_SetFlags = _lib.FPDFAnnot_SetFlags
    FPDFAnnot_SetFlags.argtypes = [FPDF_ANNOTATION, c_int]
    FPDFAnnot_SetFlags.restype = FPDF_BOOL

if hasattr(_lib, "FPDFAnnot_GetFormFieldFlags"):
    FPDFAnnot_GetFormFieldFlags = _lib.FPDFAnnot_GetFormFieldFlags
    FPDFAnnot_GetFormFieldFlags.argtypes = [FPDF_FORMHANDLE, FPDF_ANNOTATION]
    FPDFAnnot_GetFormFieldFlags.restype = c_int

if hasattr(_lib, "FPDFAnnot_GetFormFieldAtPoint"):
    FPDFAnnot_GetFormFieldAtPoint = _lib.FPDFAnnot_GetFormFieldAtPoint
    FPDFAnnot_GetFormFieldAtPoint.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, POINTER(FS_POINTF)]
    FPDFAnnot_GetFormFieldAtPoint.restype = FPDF_ANNOTATION

if hasattr(_lib, "FPDFAnnot_GetFormFieldName"):
    FPDFAnnot_GetFormFieldName = _lib.FPDFAnnot_GetFormFieldName
    FPDFAnnot_GetFormFieldName.argtypes = [FPDF_FORMHANDLE, FPDF_ANNOTATION, POINTER(FPDF_WCHAR), c_ulong]
    FPDFAnnot_GetFormFieldName.restype = c_ulong

if hasattr(_lib, "FPDFAnnot_GetFormFieldAlternateName"):
    FPDFAnnot_GetFormFieldAlternateName = _lib.FPDFAnnot_GetFormFieldAlternateName
    FPDFAnnot_GetFormFieldAlternateName.argtypes = [FPDF_FORMHANDLE, FPDF_ANNOTATION, POINTER(FPDF_WCHAR), c_ulong]
    FPDFAnnot_GetFormFieldAlternateName.restype = c_ulong

if hasattr(_lib, "FPDFAnnot_GetFormFieldType"):
    FPDFAnnot_GetFormFieldType = _lib.FPDFAnnot_GetFormFieldType
    FPDFAnnot_GetFormFieldType.argtypes = [FPDF_FORMHANDLE, FPDF_ANNOTATION]
    FPDFAnnot_GetFormFieldType.restype = c_int

if hasattr(_lib, "FPDFAnnot_GetFormFieldValue"):
    FPDFAnnot_GetFormFieldValue = _lib.FPDFAnnot_GetFormFieldValue
    FPDFAnnot_GetFormFieldValue.argtypes = [FPDF_FORMHANDLE, FPDF_ANNOTATION, POINTER(FPDF_WCHAR), c_ulong]
    FPDFAnnot_GetFormFieldValue.restype = c_ulong

if hasattr(_lib, "FPDFAnnot_GetOptionCount"):
    FPDFAnnot_GetOptionCount = _lib.FPDFAnnot_GetOptionCount
    FPDFAnnot_GetOptionCount.argtypes = [FPDF_FORMHANDLE, FPDF_ANNOTATION]
    FPDFAnnot_GetOptionCount.restype = c_int

if hasattr(_lib, "FPDFAnnot_GetOptionLabel"):
    FPDFAnnot_GetOptionLabel = _lib.FPDFAnnot_GetOptionLabel
    FPDFAnnot_GetOptionLabel.argtypes = [FPDF_FORMHANDLE, FPDF_ANNOTATION, c_int, POINTER(FPDF_WCHAR), c_ulong]
    FPDFAnnot_GetOptionLabel.restype = c_ulong

if hasattr(_lib, "FPDFAnnot_IsOptionSelected"):
    FPDFAnnot_IsOptionSelected = _lib.FPDFAnnot_IsOptionSelected
    FPDFAnnot_IsOptionSelected.argtypes = [FPDF_FORMHANDLE, FPDF_ANNOTATION, c_int]
    FPDFAnnot_IsOptionSelected.restype = FPDF_BOOL

if hasattr(_lib, "FPDFAnnot_GetFontSize"):
    FPDFAnnot_GetFontSize = _lib.FPDFAnnot_GetFontSize
    FPDFAnnot_GetFontSize.argtypes = [FPDF_FORMHANDLE, FPDF_ANNOTATION, POINTER(c_float)]
    FPDFAnnot_GetFontSize.restype = FPDF_BOOL

if hasattr(_lib, "FPDFAnnot_IsChecked"):
    FPDFAnnot_IsChecked = _lib.FPDFAnnot_IsChecked
    FPDFAnnot_IsChecked.argtypes = [FPDF_FORMHANDLE, FPDF_ANNOTATION]
    FPDFAnnot_IsChecked.restype = FPDF_BOOL

if hasattr(_lib, "FPDFAnnot_SetFocusableSubtypes"):
    FPDFAnnot_SetFocusableSubtypes = _lib.FPDFAnnot_SetFocusableSubtypes
    FPDFAnnot_SetFocusableSubtypes.argtypes = [FPDF_FORMHANDLE, POINTER(FPDF_ANNOTATION_SUBTYPE), c_size_t]
    FPDFAnnot_SetFocusableSubtypes.restype = FPDF_BOOL

if hasattr(_lib, "FPDFAnnot_GetFocusableSubtypesCount"):
    FPDFAnnot_GetFocusableSubtypesCount = _lib.FPDFAnnot_GetFocusableSubtypesCount
    FPDFAnnot_GetFocusableSubtypesCount.argtypes = [FPDF_FORMHANDLE]
    FPDFAnnot_GetFocusableSubtypesCount.restype = c_int

if hasattr(_lib, "FPDFAnnot_GetFocusableSubtypes"):
    FPDFAnnot_GetFocusableSubtypes = _lib.FPDFAnnot_GetFocusableSubtypes
    FPDFAnnot_GetFocusableSubtypes.argtypes = [FPDF_FORMHANDLE, POINTER(FPDF_ANNOTATION_SUBTYPE), c_size_t]
    FPDFAnnot_GetFocusableSubtypes.restype = FPDF_BOOL

if hasattr(_lib, "FPDFAnnot_GetLink"):
    FPDFAnnot_GetLink = _lib.FPDFAnnot_GetLink
    FPDFAnnot_GetLink.argtypes = [FPDF_ANNOTATION]
    FPDFAnnot_GetLink.restype = FPDF_LINK

if hasattr(_lib, "FPDFAnnot_GetFormControlCount"):
    FPDFAnnot_GetFormControlCount = _lib.FPDFAnnot_GetFormControlCount
    FPDFAnnot_GetFormControlCount.argtypes = [FPDF_FORMHANDLE, FPDF_ANNOTATION]
    FPDFAnnot_GetFormControlCount.restype = c_int

if hasattr(_lib, "FPDFAnnot_GetFormControlIndex"):
    FPDFAnnot_GetFormControlIndex = _lib.FPDFAnnot_GetFormControlIndex
    FPDFAnnot_GetFormControlIndex.argtypes = [FPDF_FORMHANDLE, FPDF_ANNOTATION]
    FPDFAnnot_GetFormControlIndex.restype = c_int

if hasattr(_lib, "FPDFAnnot_GetFormFieldExportValue"):
    FPDFAnnot_GetFormFieldExportValue = _lib.FPDFAnnot_GetFormFieldExportValue
    FPDFAnnot_GetFormFieldExportValue.argtypes = [FPDF_FORMHANDLE, FPDF_ANNOTATION, POINTER(FPDF_WCHAR), c_ulong]
    FPDFAnnot_GetFormFieldExportValue.restype = c_ulong

if hasattr(_lib, "FPDFAnnot_SetURI"):
    FPDFAnnot_SetURI = _lib.FPDFAnnot_SetURI
    FPDFAnnot_SetURI.argtypes = [FPDF_ANNOTATION, POINTER(c_char)]
    FPDFAnnot_SetURI.restype = FPDF_BOOL

if hasattr(_lib, "FPDFDoc_GetAttachmentCount"):
    FPDFDoc_GetAttachmentCount = _lib.FPDFDoc_GetAttachmentCount
    FPDFDoc_GetAttachmentCount.argtypes = [FPDF_DOCUMENT]
    FPDFDoc_GetAttachmentCount.restype = c_int

if hasattr(_lib, "FPDFDoc_AddAttachment"):
    FPDFDoc_AddAttachment = _lib.FPDFDoc_AddAttachment
    FPDFDoc_AddAttachment.argtypes = [FPDF_DOCUMENT, FPDF_WIDESTRING]
    FPDFDoc_AddAttachment.restype = FPDF_ATTACHMENT

if hasattr(_lib, "FPDFDoc_GetAttachment"):
    FPDFDoc_GetAttachment = _lib.FPDFDoc_GetAttachment
    FPDFDoc_GetAttachment.argtypes = [FPDF_DOCUMENT, c_int]
    FPDFDoc_GetAttachment.restype = FPDF_ATTACHMENT

if hasattr(_lib, "FPDFDoc_DeleteAttachment"):
    FPDFDoc_DeleteAttachment = _lib.FPDFDoc_DeleteAttachment
    FPDFDoc_DeleteAttachment.argtypes = [FPDF_DOCUMENT, c_int]
    FPDFDoc_DeleteAttachment.restype = FPDF_BOOL

if hasattr(_lib, "FPDFAttachment_GetName"):
    FPDFAttachment_GetName = _lib.FPDFAttachment_GetName
    FPDFAttachment_GetName.argtypes = [FPDF_ATTACHMENT, POINTER(FPDF_WCHAR), c_ulong]
    FPDFAttachment_GetName.restype = c_ulong

if hasattr(_lib, "FPDFAttachment_HasKey"):
    FPDFAttachment_HasKey = _lib.FPDFAttachment_HasKey
    FPDFAttachment_HasKey.argtypes = [FPDF_ATTACHMENT, FPDF_BYTESTRING]
    FPDFAttachment_HasKey.restype = FPDF_BOOL

if hasattr(_lib, "FPDFAttachment_GetValueType"):
    FPDFAttachment_GetValueType = _lib.FPDFAttachment_GetValueType
    FPDFAttachment_GetValueType.argtypes = [FPDF_ATTACHMENT, FPDF_BYTESTRING]
    FPDFAttachment_GetValueType.restype = FPDF_OBJECT_TYPE

if hasattr(_lib, "FPDFAttachment_SetStringValue"):
    FPDFAttachment_SetStringValue = _lib.FPDFAttachment_SetStringValue
    FPDFAttachment_SetStringValue.argtypes = [FPDF_ATTACHMENT, FPDF_BYTESTRING, FPDF_WIDESTRING]
    FPDFAttachment_SetStringValue.restype = FPDF_BOOL

if hasattr(_lib, "FPDFAttachment_GetStringValue"):
    FPDFAttachment_GetStringValue = _lib.FPDFAttachment_GetStringValue
    FPDFAttachment_GetStringValue.argtypes = [FPDF_ATTACHMENT, FPDF_BYTESTRING, POINTER(FPDF_WCHAR), c_ulong]
    FPDFAttachment_GetStringValue.restype = c_ulong

if hasattr(_lib, "FPDFAttachment_SetFile"):
    FPDFAttachment_SetFile = _lib.FPDFAttachment_SetFile
    FPDFAttachment_SetFile.argtypes = [FPDF_ATTACHMENT, FPDF_DOCUMENT, POINTER(None), c_ulong]
    FPDFAttachment_SetFile.restype = FPDF_BOOL

if hasattr(_lib, "FPDFAttachment_GetFile"):
    FPDFAttachment_GetFile = _lib.FPDFAttachment_GetFile
    FPDFAttachment_GetFile.argtypes = [FPDF_ATTACHMENT, POINTER(None), c_ulong, POINTER(c_ulong)]
    FPDFAttachment_GetFile.restype = FPDF_BOOL

if hasattr(_lib, "FPDFCatalog_IsTagged"):
    FPDFCatalog_IsTagged = _lib.FPDFCatalog_IsTagged
    FPDFCatalog_IsTagged.argtypes = [FPDF_DOCUMENT]
    FPDFCatalog_IsTagged.restype = FPDF_BOOL

class struct__FX_FILEAVAIL (Structure):
    __slots__ = ['version', 'IsDataAvail']
struct__FX_FILEAVAIL._fields_ = [
    ('version', c_int),
    ('IsDataAvail', CFUNCTYPE(FPDF_BOOL, POINTER(struct__FX_FILEAVAIL), c_size_t, c_size_t)),
]
FX_FILEAVAIL = struct__FX_FILEAVAIL

if hasattr(_lib, "FPDFAvail_Create"):
    FPDFAvail_Create = _lib.FPDFAvail_Create
    FPDFAvail_Create.argtypes = [POINTER(FX_FILEAVAIL), POINTER(FPDF_FILEACCESS)]
    FPDFAvail_Create.restype = FPDF_AVAIL

if hasattr(_lib, "FPDFAvail_Destroy"):
    FPDFAvail_Destroy = _lib.FPDFAvail_Destroy
    FPDFAvail_Destroy.argtypes = [FPDF_AVAIL]
    FPDFAvail_Destroy.restype = None

class struct__FX_DOWNLOADHINTS (Structure):
    __slots__ = ['version', 'AddSegment']
struct__FX_DOWNLOADHINTS._fields_ = [
    ('version', c_int),
    ('AddSegment', CFUNCTYPE(None, POINTER(struct__FX_DOWNLOADHINTS), c_size_t, c_size_t)),
]
FX_DOWNLOADHINTS = struct__FX_DOWNLOADHINTS

if hasattr(_lib, "FPDFAvail_IsDocAvail"):
    FPDFAvail_IsDocAvail = _lib.FPDFAvail_IsDocAvail
    FPDFAvail_IsDocAvail.argtypes = [FPDF_AVAIL, POINTER(FX_DOWNLOADHINTS)]
    FPDFAvail_IsDocAvail.restype = c_int

if hasattr(_lib, "FPDFAvail_GetDocument"):
    FPDFAvail_GetDocument = _lib.FPDFAvail_GetDocument
    FPDFAvail_GetDocument.argtypes = [FPDF_AVAIL, FPDF_BYTESTRING]
    FPDFAvail_GetDocument.restype = FPDF_DOCUMENT

if hasattr(_lib, "FPDFAvail_GetFirstPageNum"):
    FPDFAvail_GetFirstPageNum = _lib.FPDFAvail_GetFirstPageNum
    FPDFAvail_GetFirstPageNum.argtypes = [FPDF_DOCUMENT]
    FPDFAvail_GetFirstPageNum.restype = c_int

if hasattr(_lib, "FPDFAvail_IsPageAvail"):
    FPDFAvail_IsPageAvail = _lib.FPDFAvail_IsPageAvail
    FPDFAvail_IsPageAvail.argtypes = [FPDF_AVAIL, c_int, POINTER(FX_DOWNLOADHINTS)]
    FPDFAvail_IsPageAvail.restype = c_int

if hasattr(_lib, "FPDFAvail_IsFormAvail"):
    FPDFAvail_IsFormAvail = _lib.FPDFAvail_IsFormAvail
    FPDFAvail_IsFormAvail.argtypes = [FPDF_AVAIL, POINTER(FX_DOWNLOADHINTS)]
    FPDFAvail_IsFormAvail.restype = c_int

if hasattr(_lib, "FPDFAvail_IsLinearized"):
    FPDFAvail_IsLinearized = _lib.FPDFAvail_IsLinearized
    FPDFAvail_IsLinearized.argtypes = [FPDF_AVAIL]
    FPDFAvail_IsLinearized.restype = c_int
enum_anon_5 = c_int
FILEIDTYPE_PERMANENT = 0
FILEIDTYPE_CHANGING = 1
FPDF_FILEIDTYPE = enum_anon_5

if hasattr(_lib, "FPDFBookmark_GetFirstChild"):
    FPDFBookmark_GetFirstChild = _lib.FPDFBookmark_GetFirstChild
    FPDFBookmark_GetFirstChild.argtypes = [FPDF_DOCUMENT, FPDF_BOOKMARK]
    FPDFBookmark_GetFirstChild.restype = FPDF_BOOKMARK

if hasattr(_lib, "FPDFBookmark_GetNextSibling"):
    FPDFBookmark_GetNextSibling = _lib.FPDFBookmark_GetNextSibling
    FPDFBookmark_GetNextSibling.argtypes = [FPDF_DOCUMENT, FPDF_BOOKMARK]
    FPDFBookmark_GetNextSibling.restype = FPDF_BOOKMARK

if hasattr(_lib, "FPDFBookmark_GetTitle"):
    FPDFBookmark_GetTitle = _lib.FPDFBookmark_GetTitle
    FPDFBookmark_GetTitle.argtypes = [FPDF_BOOKMARK, POINTER(None), c_ulong]
    FPDFBookmark_GetTitle.restype = c_ulong

if hasattr(_lib, "FPDFBookmark_GetCount"):
    FPDFBookmark_GetCount = _lib.FPDFBookmark_GetCount
    FPDFBookmark_GetCount.argtypes = [FPDF_BOOKMARK]
    FPDFBookmark_GetCount.restype = c_int

if hasattr(_lib, "FPDFBookmark_Find"):
    FPDFBookmark_Find = _lib.FPDFBookmark_Find
    FPDFBookmark_Find.argtypes = [FPDF_DOCUMENT, FPDF_WIDESTRING]
    FPDFBookmark_Find.restype = FPDF_BOOKMARK

if hasattr(_lib, "FPDFBookmark_GetDest"):
    FPDFBookmark_GetDest = _lib.FPDFBookmark_GetDest
    FPDFBookmark_GetDest.argtypes = [FPDF_DOCUMENT, FPDF_BOOKMARK]
    FPDFBookmark_GetDest.restype = FPDF_DEST

if hasattr(_lib, "FPDFBookmark_GetAction"):
    FPDFBookmark_GetAction = _lib.FPDFBookmark_GetAction
    FPDFBookmark_GetAction.argtypes = [FPDF_BOOKMARK]
    FPDFBookmark_GetAction.restype = FPDF_ACTION

if hasattr(_lib, "FPDFAction_GetType"):
    FPDFAction_GetType = _lib.FPDFAction_GetType
    FPDFAction_GetType.argtypes = [FPDF_ACTION]
    FPDFAction_GetType.restype = c_ulong

if hasattr(_lib, "FPDFAction_GetDest"):
    FPDFAction_GetDest = _lib.FPDFAction_GetDest
    FPDFAction_GetDest.argtypes = [FPDF_DOCUMENT, FPDF_ACTION]
    FPDFAction_GetDest.restype = FPDF_DEST

if hasattr(_lib, "FPDFAction_GetFilePath"):
    FPDFAction_GetFilePath = _lib.FPDFAction_GetFilePath
    FPDFAction_GetFilePath.argtypes = [FPDF_ACTION, POINTER(None), c_ulong]
    FPDFAction_GetFilePath.restype = c_ulong

if hasattr(_lib, "FPDFAction_GetURIPath"):
    FPDFAction_GetURIPath = _lib.FPDFAction_GetURIPath
    FPDFAction_GetURIPath.argtypes = [FPDF_DOCUMENT, FPDF_ACTION, POINTER(None), c_ulong]
    FPDFAction_GetURIPath.restype = c_ulong

if hasattr(_lib, "FPDFDest_GetDestPageIndex"):
    FPDFDest_GetDestPageIndex = _lib.FPDFDest_GetDestPageIndex
    FPDFDest_GetDestPageIndex.argtypes = [FPDF_DOCUMENT, FPDF_DEST]
    FPDFDest_GetDestPageIndex.restype = c_int

if hasattr(_lib, "FPDFDest_GetView"):
    FPDFDest_GetView = _lib.FPDFDest_GetView
    FPDFDest_GetView.argtypes = [FPDF_DEST, POINTER(c_ulong), POINTER(FS_FLOAT)]
    FPDFDest_GetView.restype = c_ulong

if hasattr(_lib, "FPDFDest_GetLocationInPage"):
    FPDFDest_GetLocationInPage = _lib.FPDFDest_GetLocationInPage
    FPDFDest_GetLocationInPage.argtypes = [FPDF_DEST, POINTER(FPDF_BOOL), POINTER(FPDF_BOOL), POINTER(FPDF_BOOL), POINTER(FS_FLOAT), POINTER(FS_FLOAT), POINTER(FS_FLOAT)]
    FPDFDest_GetLocationInPage.restype = FPDF_BOOL

if hasattr(_lib, "FPDFLink_GetLinkAtPoint"):
    FPDFLink_GetLinkAtPoint = _lib.FPDFLink_GetLinkAtPoint
    FPDFLink_GetLinkAtPoint.argtypes = [FPDF_PAGE, c_double, c_double]
    FPDFLink_GetLinkAtPoint.restype = FPDF_LINK

if hasattr(_lib, "FPDFLink_GetLinkZOrderAtPoint"):
    FPDFLink_GetLinkZOrderAtPoint = _lib.FPDFLink_GetLinkZOrderAtPoint
    FPDFLink_GetLinkZOrderAtPoint.argtypes = [FPDF_PAGE, c_double, c_double]
    FPDFLink_GetLinkZOrderAtPoint.restype = c_int

if hasattr(_lib, "FPDFLink_GetDest"):
    FPDFLink_GetDest = _lib.FPDFLink_GetDest
    FPDFLink_GetDest.argtypes = [FPDF_DOCUMENT, FPDF_LINK]
    FPDFLink_GetDest.restype = FPDF_DEST

if hasattr(_lib, "FPDFLink_GetAction"):
    FPDFLink_GetAction = _lib.FPDFLink_GetAction
    FPDFLink_GetAction.argtypes = [FPDF_LINK]
    FPDFLink_GetAction.restype = FPDF_ACTION

if hasattr(_lib, "FPDFLink_Enumerate"):
    FPDFLink_Enumerate = _lib.FPDFLink_Enumerate
    FPDFLink_Enumerate.argtypes = [FPDF_PAGE, POINTER(c_int), POINTER(FPDF_LINK)]
    FPDFLink_Enumerate.restype = FPDF_BOOL

if hasattr(_lib, "FPDFLink_GetAnnot"):
    FPDFLink_GetAnnot = _lib.FPDFLink_GetAnnot
    FPDFLink_GetAnnot.argtypes = [FPDF_PAGE, FPDF_LINK]
    FPDFLink_GetAnnot.restype = FPDF_ANNOTATION

if hasattr(_lib, "FPDFLink_GetAnnotRect"):
    FPDFLink_GetAnnotRect = _lib.FPDFLink_GetAnnotRect
    FPDFLink_GetAnnotRect.argtypes = [FPDF_LINK, POINTER(FS_RECTF)]
    FPDFLink_GetAnnotRect.restype = FPDF_BOOL

if hasattr(_lib, "FPDFLink_CountQuadPoints"):
    FPDFLink_CountQuadPoints = _lib.FPDFLink_CountQuadPoints
    FPDFLink_CountQuadPoints.argtypes = [FPDF_LINK]
    FPDFLink_CountQuadPoints.restype = c_int

if hasattr(_lib, "FPDFLink_GetQuadPoints"):
    FPDFLink_GetQuadPoints = _lib.FPDFLink_GetQuadPoints
    FPDFLink_GetQuadPoints.argtypes = [FPDF_LINK, c_int, POINTER(FS_QUADPOINTSF)]
    FPDFLink_GetQuadPoints.restype = FPDF_BOOL

if hasattr(_lib, "FPDF_GetPageAAction"):
    FPDF_GetPageAAction = _lib.FPDF_GetPageAAction
    FPDF_GetPageAAction.argtypes = [FPDF_PAGE, c_int]
    FPDF_GetPageAAction.restype = FPDF_ACTION

if hasattr(_lib, "FPDF_GetFileIdentifier"):
    FPDF_GetFileIdentifier = _lib.FPDF_GetFileIdentifier
    FPDF_GetFileIdentifier.argtypes = [FPDF_DOCUMENT, FPDF_FILEIDTYPE, POINTER(None), c_ulong]
    FPDF_GetFileIdentifier.restype = c_ulong

if hasattr(_lib, "FPDF_GetMetaText"):
    FPDF_GetMetaText = _lib.FPDF_GetMetaText
    FPDF_GetMetaText.argtypes = [FPDF_DOCUMENT, FPDF_BYTESTRING, POINTER(None), c_ulong]
    FPDF_GetMetaText.restype = c_ulong

if hasattr(_lib, "FPDF_GetPageLabel"):
    FPDF_GetPageLabel = _lib.FPDF_GetPageLabel
    FPDF_GetPageLabel.argtypes = [FPDF_DOCUMENT, c_int, POINTER(None), c_ulong]
    FPDF_GetPageLabel.restype = c_ulong
__uint8_t = c_ubyte
__uint16_t = c_ushort
__uint32_t = c_uint
__time_t = c_long
uint8_t = __uint8_t
uint16_t = __uint16_t
uint32_t = __uint32_t

class struct_FPDF_IMAGEOBJ_METADATA (Structure):
    __slots__ = ['width', 'height', 'horizontal_dpi', 'vertical_dpi', 'bits_per_pixel', 'colorspace', 'marked_content_id']
struct_FPDF_IMAGEOBJ_METADATA._fields_ = [
    ('width', c_uint),
    ('height', c_uint),
    ('horizontal_dpi', c_float),
    ('vertical_dpi', c_float),
    ('bits_per_pixel', c_uint),
    ('colorspace', c_int),
    ('marked_content_id', c_int),
]
FPDF_IMAGEOBJ_METADATA = struct_FPDF_IMAGEOBJ_METADATA

if hasattr(_lib, "FPDF_CreateNewDocument"):
    FPDF_CreateNewDocument = _lib.FPDF_CreateNewDocument
    FPDF_CreateNewDocument.argtypes = []
    FPDF_CreateNewDocument.restype = FPDF_DOCUMENT

if hasattr(_lib, "FPDFPage_New"):
    FPDFPage_New = _lib.FPDFPage_New
    FPDFPage_New.argtypes = [FPDF_DOCUMENT, c_int, c_double, c_double]
    FPDFPage_New.restype = FPDF_PAGE

if hasattr(_lib, "FPDFPage_Delete"):
    FPDFPage_Delete = _lib.FPDFPage_Delete
    FPDFPage_Delete.argtypes = [FPDF_DOCUMENT, c_int]
    FPDFPage_Delete.restype = None

if hasattr(_lib, "FPDF_MovePages"):
    FPDF_MovePages = _lib.FPDF_MovePages
    FPDF_MovePages.argtypes = [FPDF_DOCUMENT, POINTER(c_int), c_ulong, c_int]
    FPDF_MovePages.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPage_GetRotation"):
    FPDFPage_GetRotation = _lib.FPDFPage_GetRotation
    FPDFPage_GetRotation.argtypes = [FPDF_PAGE]
    FPDFPage_GetRotation.restype = c_int

if hasattr(_lib, "FPDFPage_SetRotation"):
    FPDFPage_SetRotation = _lib.FPDFPage_SetRotation
    FPDFPage_SetRotation.argtypes = [FPDF_PAGE, c_int]
    FPDFPage_SetRotation.restype = None

if hasattr(_lib, "FPDFPage_InsertObject"):
    FPDFPage_InsertObject = _lib.FPDFPage_InsertObject
    FPDFPage_InsertObject.argtypes = [FPDF_PAGE, FPDF_PAGEOBJECT]
    FPDFPage_InsertObject.restype = None

if hasattr(_lib, "FPDFPage_RemoveObject"):
    FPDFPage_RemoveObject = _lib.FPDFPage_RemoveObject
    FPDFPage_RemoveObject.argtypes = [FPDF_PAGE, FPDF_PAGEOBJECT]
    FPDFPage_RemoveObject.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPage_CountObjects"):
    FPDFPage_CountObjects = _lib.FPDFPage_CountObjects
    FPDFPage_CountObjects.argtypes = [FPDF_PAGE]
    FPDFPage_CountObjects.restype = c_int

if hasattr(_lib, "FPDFPage_GetObject"):
    FPDFPage_GetObject = _lib.FPDFPage_GetObject
    FPDFPage_GetObject.argtypes = [FPDF_PAGE, c_int]
    FPDFPage_GetObject.restype = FPDF_PAGEOBJECT

if hasattr(_lib, "FPDFPage_HasTransparency"):
    FPDFPage_HasTransparency = _lib.FPDFPage_HasTransparency
    FPDFPage_HasTransparency.argtypes = [FPDF_PAGE]
    FPDFPage_HasTransparency.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPage_GenerateContent"):
    FPDFPage_GenerateContent = _lib.FPDFPage_GenerateContent
    FPDFPage_GenerateContent.argtypes = [FPDF_PAGE]
    FPDFPage_GenerateContent.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPageObj_Destroy"):
    FPDFPageObj_Destroy = _lib.FPDFPageObj_Destroy
    FPDFPageObj_Destroy.argtypes = [FPDF_PAGEOBJECT]
    FPDFPageObj_Destroy.restype = None

if hasattr(_lib, "FPDFPageObj_HasTransparency"):
    FPDFPageObj_HasTransparency = _lib.FPDFPageObj_HasTransparency
    FPDFPageObj_HasTransparency.argtypes = [FPDF_PAGEOBJECT]
    FPDFPageObj_HasTransparency.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPageObj_GetType"):
    FPDFPageObj_GetType = _lib.FPDFPageObj_GetType
    FPDFPageObj_GetType.argtypes = [FPDF_PAGEOBJECT]
    FPDFPageObj_GetType.restype = c_int

if hasattr(_lib, "FPDFPageObj_Transform"):
    FPDFPageObj_Transform = _lib.FPDFPageObj_Transform
    FPDFPageObj_Transform.argtypes = [FPDF_PAGEOBJECT, c_double, c_double, c_double, c_double, c_double, c_double]
    FPDFPageObj_Transform.restype = None

if hasattr(_lib, "FPDFPageObj_GetMatrix"):
    FPDFPageObj_GetMatrix = _lib.FPDFPageObj_GetMatrix
    FPDFPageObj_GetMatrix.argtypes = [FPDF_PAGEOBJECT, POINTER(FS_MATRIX)]
    FPDFPageObj_GetMatrix.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPageObj_SetMatrix"):
    FPDFPageObj_SetMatrix = _lib.FPDFPageObj_SetMatrix
    FPDFPageObj_SetMatrix.argtypes = [FPDF_PAGEOBJECT, POINTER(FS_MATRIX)]
    FPDFPageObj_SetMatrix.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPage_TransformAnnots"):
    FPDFPage_TransformAnnots = _lib.FPDFPage_TransformAnnots
    FPDFPage_TransformAnnots.argtypes = [FPDF_PAGE, c_double, c_double, c_double, c_double, c_double, c_double]
    FPDFPage_TransformAnnots.restype = None

if hasattr(_lib, "FPDFPageObj_NewImageObj"):
    FPDFPageObj_NewImageObj = _lib.FPDFPageObj_NewImageObj
    FPDFPageObj_NewImageObj.argtypes = [FPDF_DOCUMENT]
    FPDFPageObj_NewImageObj.restype = FPDF_PAGEOBJECT

if hasattr(_lib, "FPDFPageObj_CountMarks"):
    FPDFPageObj_CountMarks = _lib.FPDFPageObj_CountMarks
    FPDFPageObj_CountMarks.argtypes = [FPDF_PAGEOBJECT]
    FPDFPageObj_CountMarks.restype = c_int

if hasattr(_lib, "FPDFPageObj_GetMark"):
    FPDFPageObj_GetMark = _lib.FPDFPageObj_GetMark
    FPDFPageObj_GetMark.argtypes = [FPDF_PAGEOBJECT, c_ulong]
    FPDFPageObj_GetMark.restype = FPDF_PAGEOBJECTMARK

if hasattr(_lib, "FPDFPageObj_AddMark"):
    FPDFPageObj_AddMark = _lib.FPDFPageObj_AddMark
    FPDFPageObj_AddMark.argtypes = [FPDF_PAGEOBJECT, FPDF_BYTESTRING]
    FPDFPageObj_AddMark.restype = FPDF_PAGEOBJECTMARK

if hasattr(_lib, "FPDFPageObj_RemoveMark"):
    FPDFPageObj_RemoveMark = _lib.FPDFPageObj_RemoveMark
    FPDFPageObj_RemoveMark.argtypes = [FPDF_PAGEOBJECT, FPDF_PAGEOBJECTMARK]
    FPDFPageObj_RemoveMark.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPageObjMark_GetName"):
    FPDFPageObjMark_GetName = _lib.FPDFPageObjMark_GetName
    FPDFPageObjMark_GetName.argtypes = [FPDF_PAGEOBJECTMARK, POINTER(None), c_ulong, POINTER(c_ulong)]
    FPDFPageObjMark_GetName.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPageObjMark_CountParams"):
    FPDFPageObjMark_CountParams = _lib.FPDFPageObjMark_CountParams
    FPDFPageObjMark_CountParams.argtypes = [FPDF_PAGEOBJECTMARK]
    FPDFPageObjMark_CountParams.restype = c_int

if hasattr(_lib, "FPDFPageObjMark_GetParamKey"):
    FPDFPageObjMark_GetParamKey = _lib.FPDFPageObjMark_GetParamKey
    FPDFPageObjMark_GetParamKey.argtypes = [FPDF_PAGEOBJECTMARK, c_ulong, POINTER(None), c_ulong, POINTER(c_ulong)]
    FPDFPageObjMark_GetParamKey.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPageObjMark_GetParamValueType"):
    FPDFPageObjMark_GetParamValueType = _lib.FPDFPageObjMark_GetParamValueType
    FPDFPageObjMark_GetParamValueType.argtypes = [FPDF_PAGEOBJECTMARK, FPDF_BYTESTRING]
    FPDFPageObjMark_GetParamValueType.restype = FPDF_OBJECT_TYPE

if hasattr(_lib, "FPDFPageObjMark_GetParamIntValue"):
    FPDFPageObjMark_GetParamIntValue = _lib.FPDFPageObjMark_GetParamIntValue
    FPDFPageObjMark_GetParamIntValue.argtypes = [FPDF_PAGEOBJECTMARK, FPDF_BYTESTRING, POINTER(c_int)]
    FPDFPageObjMark_GetParamIntValue.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPageObjMark_GetParamStringValue"):
    FPDFPageObjMark_GetParamStringValue = _lib.FPDFPageObjMark_GetParamStringValue
    FPDFPageObjMark_GetParamStringValue.argtypes = [FPDF_PAGEOBJECTMARK, FPDF_BYTESTRING, POINTER(None), c_ulong, POINTER(c_ulong)]
    FPDFPageObjMark_GetParamStringValue.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPageObjMark_GetParamBlobValue"):
    FPDFPageObjMark_GetParamBlobValue = _lib.FPDFPageObjMark_GetParamBlobValue
    FPDFPageObjMark_GetParamBlobValue.argtypes = [FPDF_PAGEOBJECTMARK, FPDF_BYTESTRING, POINTER(None), c_ulong, POINTER(c_ulong)]
    FPDFPageObjMark_GetParamBlobValue.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPageObjMark_SetIntParam"):
    FPDFPageObjMark_SetIntParam = _lib.FPDFPageObjMark_SetIntParam
    FPDFPageObjMark_SetIntParam.argtypes = [FPDF_DOCUMENT, FPDF_PAGEOBJECT, FPDF_PAGEOBJECTMARK, FPDF_BYTESTRING, c_int]
    FPDFPageObjMark_SetIntParam.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPageObjMark_SetStringParam"):
    FPDFPageObjMark_SetStringParam = _lib.FPDFPageObjMark_SetStringParam
    FPDFPageObjMark_SetStringParam.argtypes = [FPDF_DOCUMENT, FPDF_PAGEOBJECT, FPDF_PAGEOBJECTMARK, FPDF_BYTESTRING, FPDF_BYTESTRING]
    FPDFPageObjMark_SetStringParam.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPageObjMark_SetBlobParam"):
    FPDFPageObjMark_SetBlobParam = _lib.FPDFPageObjMark_SetBlobParam
    FPDFPageObjMark_SetBlobParam.argtypes = [FPDF_DOCUMENT, FPDF_PAGEOBJECT, FPDF_PAGEOBJECTMARK, FPDF_BYTESTRING, POINTER(None), c_ulong]
    FPDFPageObjMark_SetBlobParam.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPageObjMark_RemoveParam"):
    FPDFPageObjMark_RemoveParam = _lib.FPDFPageObjMark_RemoveParam
    FPDFPageObjMark_RemoveParam.argtypes = [FPDF_PAGEOBJECT, FPDF_PAGEOBJECTMARK, FPDF_BYTESTRING]
    FPDFPageObjMark_RemoveParam.restype = FPDF_BOOL

if hasattr(_lib, "FPDFImageObj_LoadJpegFile"):
    FPDFImageObj_LoadJpegFile = _lib.FPDFImageObj_LoadJpegFile
    FPDFImageObj_LoadJpegFile.argtypes = [POINTER(FPDF_PAGE), c_int, FPDF_PAGEOBJECT, POINTER(FPDF_FILEACCESS)]
    FPDFImageObj_LoadJpegFile.restype = FPDF_BOOL

if hasattr(_lib, "FPDFImageObj_LoadJpegFileInline"):
    FPDFImageObj_LoadJpegFileInline = _lib.FPDFImageObj_LoadJpegFileInline
    FPDFImageObj_LoadJpegFileInline.argtypes = [POINTER(FPDF_PAGE), c_int, FPDF_PAGEOBJECT, POINTER(FPDF_FILEACCESS)]
    FPDFImageObj_LoadJpegFileInline.restype = FPDF_BOOL

if hasattr(_lib, "FPDFImageObj_SetMatrix"):
    FPDFImageObj_SetMatrix = _lib.FPDFImageObj_SetMatrix
    FPDFImageObj_SetMatrix.argtypes = [FPDF_PAGEOBJECT, c_double, c_double, c_double, c_double, c_double, c_double]
    FPDFImageObj_SetMatrix.restype = FPDF_BOOL

if hasattr(_lib, "FPDFImageObj_SetBitmap"):
    FPDFImageObj_SetBitmap = _lib.FPDFImageObj_SetBitmap
    FPDFImageObj_SetBitmap.argtypes = [POINTER(FPDF_PAGE), c_int, FPDF_PAGEOBJECT, FPDF_BITMAP]
    FPDFImageObj_SetBitmap.restype = FPDF_BOOL

if hasattr(_lib, "FPDFImageObj_GetBitmap"):
    FPDFImageObj_GetBitmap = _lib.FPDFImageObj_GetBitmap
    FPDFImageObj_GetBitmap.argtypes = [FPDF_PAGEOBJECT]
    FPDFImageObj_GetBitmap.restype = FPDF_BITMAP

if hasattr(_lib, "FPDFImageObj_GetRenderedBitmap"):
    FPDFImageObj_GetRenderedBitmap = _lib.FPDFImageObj_GetRenderedBitmap
    FPDFImageObj_GetRenderedBitmap.argtypes = [FPDF_DOCUMENT, FPDF_PAGE, FPDF_PAGEOBJECT]
    FPDFImageObj_GetRenderedBitmap.restype = FPDF_BITMAP

if hasattr(_lib, "FPDFImageObj_GetImageDataDecoded"):
    FPDFImageObj_GetImageDataDecoded = _lib.FPDFImageObj_GetImageDataDecoded
    FPDFImageObj_GetImageDataDecoded.argtypes = [FPDF_PAGEOBJECT, POINTER(None), c_ulong]
    FPDFImageObj_GetImageDataDecoded.restype = c_ulong

if hasattr(_lib, "FPDFImageObj_GetImageDataRaw"):
    FPDFImageObj_GetImageDataRaw = _lib.FPDFImageObj_GetImageDataRaw
    FPDFImageObj_GetImageDataRaw.argtypes = [FPDF_PAGEOBJECT, POINTER(None), c_ulong]
    FPDFImageObj_GetImageDataRaw.restype = c_ulong

if hasattr(_lib, "FPDFImageObj_GetImageFilterCount"):
    FPDFImageObj_GetImageFilterCount = _lib.FPDFImageObj_GetImageFilterCount
    FPDFImageObj_GetImageFilterCount.argtypes = [FPDF_PAGEOBJECT]
    FPDFImageObj_GetImageFilterCount.restype = c_int

if hasattr(_lib, "FPDFImageObj_GetImageFilter"):
    FPDFImageObj_GetImageFilter = _lib.FPDFImageObj_GetImageFilter
    FPDFImageObj_GetImageFilter.argtypes = [FPDF_PAGEOBJECT, c_int, POINTER(None), c_ulong]
    FPDFImageObj_GetImageFilter.restype = c_ulong

if hasattr(_lib, "FPDFImageObj_GetImageMetadata"):
    FPDFImageObj_GetImageMetadata = _lib.FPDFImageObj_GetImageMetadata
    FPDFImageObj_GetImageMetadata.argtypes = [FPDF_PAGEOBJECT, FPDF_PAGE, POINTER(FPDF_IMAGEOBJ_METADATA)]
    FPDFImageObj_GetImageMetadata.restype = FPDF_BOOL

if hasattr(_lib, "FPDFImageObj_GetImagePixelSize"):
    FPDFImageObj_GetImagePixelSize = _lib.FPDFImageObj_GetImagePixelSize
    FPDFImageObj_GetImagePixelSize.argtypes = [FPDF_PAGEOBJECT, POINTER(c_uint), POINTER(c_uint)]
    FPDFImageObj_GetImagePixelSize.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPageObj_CreateNewPath"):
    FPDFPageObj_CreateNewPath = _lib.FPDFPageObj_CreateNewPath
    FPDFPageObj_CreateNewPath.argtypes = [c_float, c_float]
    FPDFPageObj_CreateNewPath.restype = FPDF_PAGEOBJECT

if hasattr(_lib, "FPDFPageObj_CreateNewRect"):
    FPDFPageObj_CreateNewRect = _lib.FPDFPageObj_CreateNewRect
    FPDFPageObj_CreateNewRect.argtypes = [c_float, c_float, c_float, c_float]
    FPDFPageObj_CreateNewRect.restype = FPDF_PAGEOBJECT

if hasattr(_lib, "FPDFPageObj_GetBounds"):
    FPDFPageObj_GetBounds = _lib.FPDFPageObj_GetBounds
    FPDFPageObj_GetBounds.argtypes = [FPDF_PAGEOBJECT, POINTER(c_float), POINTER(c_float), POINTER(c_float), POINTER(c_float)]
    FPDFPageObj_GetBounds.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPageObj_GetRotatedBounds"):
    FPDFPageObj_GetRotatedBounds = _lib.FPDFPageObj_GetRotatedBounds
    FPDFPageObj_GetRotatedBounds.argtypes = [FPDF_PAGEOBJECT, POINTER(FS_QUADPOINTSF)]
    FPDFPageObj_GetRotatedBounds.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPageObj_SetBlendMode"):
    FPDFPageObj_SetBlendMode = _lib.FPDFPageObj_SetBlendMode
    FPDFPageObj_SetBlendMode.argtypes = [FPDF_PAGEOBJECT, FPDF_BYTESTRING]
    FPDFPageObj_SetBlendMode.restype = None

if hasattr(_lib, "FPDFPageObj_SetStrokeColor"):
    FPDFPageObj_SetStrokeColor = _lib.FPDFPageObj_SetStrokeColor
    FPDFPageObj_SetStrokeColor.argtypes = [FPDF_PAGEOBJECT, c_uint, c_uint, c_uint, c_uint]
    FPDFPageObj_SetStrokeColor.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPageObj_GetStrokeColor"):
    FPDFPageObj_GetStrokeColor = _lib.FPDFPageObj_GetStrokeColor
    FPDFPageObj_GetStrokeColor.argtypes = [FPDF_PAGEOBJECT, POINTER(c_uint), POINTER(c_uint), POINTER(c_uint), POINTER(c_uint)]
    FPDFPageObj_GetStrokeColor.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPageObj_SetStrokeWidth"):
    FPDFPageObj_SetStrokeWidth = _lib.FPDFPageObj_SetStrokeWidth
    FPDFPageObj_SetStrokeWidth.argtypes = [FPDF_PAGEOBJECT, c_float]
    FPDFPageObj_SetStrokeWidth.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPageObj_GetStrokeWidth"):
    FPDFPageObj_GetStrokeWidth = _lib.FPDFPageObj_GetStrokeWidth
    FPDFPageObj_GetStrokeWidth.argtypes = [FPDF_PAGEOBJECT, POINTER(c_float)]
    FPDFPageObj_GetStrokeWidth.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPageObj_GetLineJoin"):
    FPDFPageObj_GetLineJoin = _lib.FPDFPageObj_GetLineJoin
    FPDFPageObj_GetLineJoin.argtypes = [FPDF_PAGEOBJECT]
    FPDFPageObj_GetLineJoin.restype = c_int

if hasattr(_lib, "FPDFPageObj_SetLineJoin"):
    FPDFPageObj_SetLineJoin = _lib.FPDFPageObj_SetLineJoin
    FPDFPageObj_SetLineJoin.argtypes = [FPDF_PAGEOBJECT, c_int]
    FPDFPageObj_SetLineJoin.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPageObj_GetLineCap"):
    FPDFPageObj_GetLineCap = _lib.FPDFPageObj_GetLineCap
    FPDFPageObj_GetLineCap.argtypes = [FPDF_PAGEOBJECT]
    FPDFPageObj_GetLineCap.restype = c_int

if hasattr(_lib, "FPDFPageObj_SetLineCap"):
    FPDFPageObj_SetLineCap = _lib.FPDFPageObj_SetLineCap
    FPDFPageObj_SetLineCap.argtypes = [FPDF_PAGEOBJECT, c_int]
    FPDFPageObj_SetLineCap.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPageObj_SetFillColor"):
    FPDFPageObj_SetFillColor = _lib.FPDFPageObj_SetFillColor
    FPDFPageObj_SetFillColor.argtypes = [FPDF_PAGEOBJECT, c_uint, c_uint, c_uint, c_uint]
    FPDFPageObj_SetFillColor.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPageObj_GetFillColor"):
    FPDFPageObj_GetFillColor = _lib.FPDFPageObj_GetFillColor
    FPDFPageObj_GetFillColor.argtypes = [FPDF_PAGEOBJECT, POINTER(c_uint), POINTER(c_uint), POINTER(c_uint), POINTER(c_uint)]
    FPDFPageObj_GetFillColor.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPageObj_GetDashPhase"):
    FPDFPageObj_GetDashPhase = _lib.FPDFPageObj_GetDashPhase
    FPDFPageObj_GetDashPhase.argtypes = [FPDF_PAGEOBJECT, POINTER(c_float)]
    FPDFPageObj_GetDashPhase.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPageObj_SetDashPhase"):
    FPDFPageObj_SetDashPhase = _lib.FPDFPageObj_SetDashPhase
    FPDFPageObj_SetDashPhase.argtypes = [FPDF_PAGEOBJECT, c_float]
    FPDFPageObj_SetDashPhase.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPageObj_GetDashCount"):
    FPDFPageObj_GetDashCount = _lib.FPDFPageObj_GetDashCount
    FPDFPageObj_GetDashCount.argtypes = [FPDF_PAGEOBJECT]
    FPDFPageObj_GetDashCount.restype = c_int

if hasattr(_lib, "FPDFPageObj_GetDashArray"):
    FPDFPageObj_GetDashArray = _lib.FPDFPageObj_GetDashArray
    FPDFPageObj_GetDashArray.argtypes = [FPDF_PAGEOBJECT, POINTER(c_float), c_size_t]
    FPDFPageObj_GetDashArray.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPageObj_SetDashArray"):
    FPDFPageObj_SetDashArray = _lib.FPDFPageObj_SetDashArray
    FPDFPageObj_SetDashArray.argtypes = [FPDF_PAGEOBJECT, POINTER(c_float), c_size_t, c_float]
    FPDFPageObj_SetDashArray.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPath_CountSegments"):
    FPDFPath_CountSegments = _lib.FPDFPath_CountSegments
    FPDFPath_CountSegments.argtypes = [FPDF_PAGEOBJECT]
    FPDFPath_CountSegments.restype = c_int

if hasattr(_lib, "FPDFPath_GetPathSegment"):
    FPDFPath_GetPathSegment = _lib.FPDFPath_GetPathSegment
    FPDFPath_GetPathSegment.argtypes = [FPDF_PAGEOBJECT, c_int]
    FPDFPath_GetPathSegment.restype = FPDF_PATHSEGMENT

if hasattr(_lib, "FPDFPathSegment_GetPoint"):
    FPDFPathSegment_GetPoint = _lib.FPDFPathSegment_GetPoint
    FPDFPathSegment_GetPoint.argtypes = [FPDF_PATHSEGMENT, POINTER(c_float), POINTER(c_float)]
    FPDFPathSegment_GetPoint.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPathSegment_GetType"):
    FPDFPathSegment_GetType = _lib.FPDFPathSegment_GetType
    FPDFPathSegment_GetType.argtypes = [FPDF_PATHSEGMENT]
    FPDFPathSegment_GetType.restype = c_int

if hasattr(_lib, "FPDFPathSegment_GetClose"):
    FPDFPathSegment_GetClose = _lib.FPDFPathSegment_GetClose
    FPDFPathSegment_GetClose.argtypes = [FPDF_PATHSEGMENT]
    FPDFPathSegment_GetClose.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPath_MoveTo"):
    FPDFPath_MoveTo = _lib.FPDFPath_MoveTo
    FPDFPath_MoveTo.argtypes = [FPDF_PAGEOBJECT, c_float, c_float]
    FPDFPath_MoveTo.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPath_LineTo"):
    FPDFPath_LineTo = _lib.FPDFPath_LineTo
    FPDFPath_LineTo.argtypes = [FPDF_PAGEOBJECT, c_float, c_float]
    FPDFPath_LineTo.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPath_BezierTo"):
    FPDFPath_BezierTo = _lib.FPDFPath_BezierTo
    FPDFPath_BezierTo.argtypes = [FPDF_PAGEOBJECT, c_float, c_float, c_float, c_float, c_float, c_float]
    FPDFPath_BezierTo.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPath_Close"):
    FPDFPath_Close = _lib.FPDFPath_Close
    FPDFPath_Close.argtypes = [FPDF_PAGEOBJECT]
    FPDFPath_Close.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPath_SetDrawMode"):
    FPDFPath_SetDrawMode = _lib.FPDFPath_SetDrawMode
    FPDFPath_SetDrawMode.argtypes = [FPDF_PAGEOBJECT, c_int, FPDF_BOOL]
    FPDFPath_SetDrawMode.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPath_GetDrawMode"):
    FPDFPath_GetDrawMode = _lib.FPDFPath_GetDrawMode
    FPDFPath_GetDrawMode.argtypes = [FPDF_PAGEOBJECT, POINTER(c_int), POINTER(FPDF_BOOL)]
    FPDFPath_GetDrawMode.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPageObj_NewTextObj"):
    FPDFPageObj_NewTextObj = _lib.FPDFPageObj_NewTextObj
    FPDFPageObj_NewTextObj.argtypes = [FPDF_DOCUMENT, FPDF_BYTESTRING, c_float]
    FPDFPageObj_NewTextObj.restype = FPDF_PAGEOBJECT

if hasattr(_lib, "FPDFText_SetText"):
    FPDFText_SetText = _lib.FPDFText_SetText
    FPDFText_SetText.argtypes = [FPDF_PAGEOBJECT, FPDF_WIDESTRING]
    FPDFText_SetText.restype = FPDF_BOOL

if hasattr(_lib, "FPDFText_SetCharcodes"):
    FPDFText_SetCharcodes = _lib.FPDFText_SetCharcodes
    FPDFText_SetCharcodes.argtypes = [FPDF_PAGEOBJECT, POINTER(uint32_t), c_size_t]
    FPDFText_SetCharcodes.restype = FPDF_BOOL

if hasattr(_lib, "FPDFText_LoadFont"):
    FPDFText_LoadFont = _lib.FPDFText_LoadFont
    FPDFText_LoadFont.argtypes = [FPDF_DOCUMENT, POINTER(uint8_t), uint32_t, c_int, FPDF_BOOL]
    FPDFText_LoadFont.restype = FPDF_FONT

if hasattr(_lib, "FPDFText_LoadStandardFont"):
    FPDFText_LoadStandardFont = _lib.FPDFText_LoadStandardFont
    FPDFText_LoadStandardFont.argtypes = [FPDF_DOCUMENT, FPDF_BYTESTRING]
    FPDFText_LoadStandardFont.restype = FPDF_FONT

if hasattr(_lib, "FPDFTextObj_GetFontSize"):
    FPDFTextObj_GetFontSize = _lib.FPDFTextObj_GetFontSize
    FPDFTextObj_GetFontSize.argtypes = [FPDF_PAGEOBJECT, POINTER(c_float)]
    FPDFTextObj_GetFontSize.restype = FPDF_BOOL

if hasattr(_lib, "FPDFFont_Close"):
    FPDFFont_Close = _lib.FPDFFont_Close
    FPDFFont_Close.argtypes = [FPDF_FONT]
    FPDFFont_Close.restype = None

if hasattr(_lib, "FPDFPageObj_CreateTextObj"):
    FPDFPageObj_CreateTextObj = _lib.FPDFPageObj_CreateTextObj
    FPDFPageObj_CreateTextObj.argtypes = [FPDF_DOCUMENT, FPDF_FONT, c_float]
    FPDFPageObj_CreateTextObj.restype = FPDF_PAGEOBJECT

if hasattr(_lib, "FPDFTextObj_GetTextRenderMode"):
    FPDFTextObj_GetTextRenderMode = _lib.FPDFTextObj_GetTextRenderMode
    FPDFTextObj_GetTextRenderMode.argtypes = [FPDF_PAGEOBJECT]
    FPDFTextObj_GetTextRenderMode.restype = FPDF_TEXT_RENDERMODE

if hasattr(_lib, "FPDFTextObj_SetTextRenderMode"):
    FPDFTextObj_SetTextRenderMode = _lib.FPDFTextObj_SetTextRenderMode
    FPDFTextObj_SetTextRenderMode.argtypes = [FPDF_PAGEOBJECT, FPDF_TEXT_RENDERMODE]
    FPDFTextObj_SetTextRenderMode.restype = FPDF_BOOL

if hasattr(_lib, "FPDFTextObj_GetText"):
    FPDFTextObj_GetText = _lib.FPDFTextObj_GetText
    FPDFTextObj_GetText.argtypes = [FPDF_PAGEOBJECT, FPDF_TEXTPAGE, POINTER(FPDF_WCHAR), c_ulong]
    FPDFTextObj_GetText.restype = c_ulong

if hasattr(_lib, "FPDFTextObj_GetRenderedBitmap"):
    FPDFTextObj_GetRenderedBitmap = _lib.FPDFTextObj_GetRenderedBitmap
    FPDFTextObj_GetRenderedBitmap.argtypes = [FPDF_DOCUMENT, FPDF_PAGE, FPDF_PAGEOBJECT, c_float]
    FPDFTextObj_GetRenderedBitmap.restype = FPDF_BITMAP

if hasattr(_lib, "FPDFTextObj_GetFont"):
    FPDFTextObj_GetFont = _lib.FPDFTextObj_GetFont
    FPDFTextObj_GetFont.argtypes = [FPDF_PAGEOBJECT]
    FPDFTextObj_GetFont.restype = FPDF_FONT

if hasattr(_lib, "FPDFFont_GetFontName"):
    FPDFFont_GetFontName = _lib.FPDFFont_GetFontName
    FPDFFont_GetFontName.argtypes = [FPDF_FONT, POINTER(c_char), c_ulong]
    FPDFFont_GetFontName.restype = c_ulong

if hasattr(_lib, "FPDFFont_GetFontData"):
    FPDFFont_GetFontData = _lib.FPDFFont_GetFontData
    FPDFFont_GetFontData.argtypes = [FPDF_FONT, POINTER(uint8_t), c_size_t, POINTER(c_size_t)]
    FPDFFont_GetFontData.restype = FPDF_BOOL

if hasattr(_lib, "FPDFFont_GetIsEmbedded"):
    FPDFFont_GetIsEmbedded = _lib.FPDFFont_GetIsEmbedded
    FPDFFont_GetIsEmbedded.argtypes = [FPDF_FONT]
    FPDFFont_GetIsEmbedded.restype = c_int

if hasattr(_lib, "FPDFFont_GetFlags"):
    FPDFFont_GetFlags = _lib.FPDFFont_GetFlags
    FPDFFont_GetFlags.argtypes = [FPDF_FONT]
    FPDFFont_GetFlags.restype = c_int

if hasattr(_lib, "FPDFFont_GetWeight"):
    FPDFFont_GetWeight = _lib.FPDFFont_GetWeight
    FPDFFont_GetWeight.argtypes = [FPDF_FONT]
    FPDFFont_GetWeight.restype = c_int

if hasattr(_lib, "FPDFFont_GetItalicAngle"):
    FPDFFont_GetItalicAngle = _lib.FPDFFont_GetItalicAngle
    FPDFFont_GetItalicAngle.argtypes = [FPDF_FONT, POINTER(c_int)]
    FPDFFont_GetItalicAngle.restype = FPDF_BOOL

if hasattr(_lib, "FPDFFont_GetAscent"):
    FPDFFont_GetAscent = _lib.FPDFFont_GetAscent
    FPDFFont_GetAscent.argtypes = [FPDF_FONT, c_float, POINTER(c_float)]
    FPDFFont_GetAscent.restype = FPDF_BOOL

if hasattr(_lib, "FPDFFont_GetDescent"):
    FPDFFont_GetDescent = _lib.FPDFFont_GetDescent
    FPDFFont_GetDescent.argtypes = [FPDF_FONT, c_float, POINTER(c_float)]
    FPDFFont_GetDescent.restype = FPDF_BOOL

if hasattr(_lib, "FPDFFont_GetGlyphWidth"):
    FPDFFont_GetGlyphWidth = _lib.FPDFFont_GetGlyphWidth
    FPDFFont_GetGlyphWidth.argtypes = [FPDF_FONT, uint32_t, c_float, POINTER(c_float)]
    FPDFFont_GetGlyphWidth.restype = FPDF_BOOL

if hasattr(_lib, "FPDFFont_GetGlyphPath"):
    FPDFFont_GetGlyphPath = _lib.FPDFFont_GetGlyphPath
    FPDFFont_GetGlyphPath.argtypes = [FPDF_FONT, uint32_t, c_float]
    FPDFFont_GetGlyphPath.restype = FPDF_GLYPHPATH

if hasattr(_lib, "FPDFGlyphPath_CountGlyphSegments"):
    FPDFGlyphPath_CountGlyphSegments = _lib.FPDFGlyphPath_CountGlyphSegments
    FPDFGlyphPath_CountGlyphSegments.argtypes = [FPDF_GLYPHPATH]
    FPDFGlyphPath_CountGlyphSegments.restype = c_int

if hasattr(_lib, "FPDFGlyphPath_GetGlyphPathSegment"):
    FPDFGlyphPath_GetGlyphPathSegment = _lib.FPDFGlyphPath_GetGlyphPathSegment
    FPDFGlyphPath_GetGlyphPathSegment.argtypes = [FPDF_GLYPHPATH, c_int]
    FPDFGlyphPath_GetGlyphPathSegment.restype = FPDF_PATHSEGMENT

if hasattr(_lib, "FPDFFormObj_CountObjects"):
    FPDFFormObj_CountObjects = _lib.FPDFFormObj_CountObjects
    FPDFFormObj_CountObjects.argtypes = [FPDF_PAGEOBJECT]
    FPDFFormObj_CountObjects.restype = c_int

if hasattr(_lib, "FPDFFormObj_GetObject"):
    FPDFFormObj_GetObject = _lib.FPDFFormObj_GetObject
    FPDFFormObj_GetObject.argtypes = [FPDF_PAGEOBJECT, c_ulong]
    FPDFFormObj_GetObject.restype = FPDF_PAGEOBJECT
time_t = __time_t

class struct_tm (Structure):
    __slots__ = ['tm_sec', 'tm_min', 'tm_hour', 'tm_mday', 'tm_mon', 'tm_year', 'tm_wday', 'tm_yday', 'tm_isdst', 'tm_gmtoff', 'tm_zone']
struct_tm._fields_ = [
    ('tm_sec', c_int),
    ('tm_min', c_int),
    ('tm_hour', c_int),
    ('tm_mday', c_int),
    ('tm_mon', c_int),
    ('tm_year', c_int),
    ('tm_wday', c_int),
    ('tm_yday', c_int),
    ('tm_isdst', c_int),
    ('tm_gmtoff', c_long),
    ('tm_zone', POINTER(c_char)),
]

class struct__UNSUPPORT_INFO (Structure):
    __slots__ = ['version', 'FSDK_UnSupport_Handler']
struct__UNSUPPORT_INFO._fields_ = [
    ('version', c_int),
    ('FSDK_UnSupport_Handler', CFUNCTYPE(None, POINTER(struct__UNSUPPORT_INFO), c_int)),
]
UNSUPPORT_INFO = struct__UNSUPPORT_INFO

if hasattr(_lib, "FSDK_SetUnSpObjProcessHandler"):
    FSDK_SetUnSpObjProcessHandler = _lib.FSDK_SetUnSpObjProcessHandler
    FSDK_SetUnSpObjProcessHandler.argtypes = [POINTER(UNSUPPORT_INFO)]
    FSDK_SetUnSpObjProcessHandler.restype = FPDF_BOOL

if hasattr(_lib, "FSDK_SetTimeFunction"):
    FSDK_SetTimeFunction = _lib.FSDK_SetTimeFunction
    FSDK_SetTimeFunction.argtypes = [CFUNCTYPE(time_t, )]
    FSDK_SetTimeFunction.restype = None

if hasattr(_lib, "FSDK_SetLocaltimeFunction"):
    FSDK_SetLocaltimeFunction = _lib.FSDK_SetLocaltimeFunction
    FSDK_SetLocaltimeFunction.argtypes = [CFUNCTYPE(POINTER(struct_tm), POINTER(time_t))]
    FSDK_SetLocaltimeFunction.restype = None

if hasattr(_lib, "FPDFDoc_GetPageMode"):
    FPDFDoc_GetPageMode = _lib.FPDFDoc_GetPageMode
    FPDFDoc_GetPageMode.argtypes = [FPDF_DOCUMENT]
    FPDFDoc_GetPageMode.restype = c_int

if hasattr(_lib, "FPDFPage_Flatten"):
    FPDFPage_Flatten = _lib.FPDFPage_Flatten
    FPDFPage_Flatten.argtypes = [FPDF_PAGE, c_int]
    FPDFPage_Flatten.restype = c_int
enum_anon_7 = c_int
FWL_EVENTFLAG_ShiftKey = (1 << 0)
FWL_EVENTFLAG_ControlKey = (1 << 1)
FWL_EVENTFLAG_AltKey = (1 << 2)
FWL_EVENTFLAG_MetaKey = (1 << 3)
FWL_EVENTFLAG_KeyPad = (1 << 4)
FWL_EVENTFLAG_AutoRepeat = (1 << 5)
FWL_EVENTFLAG_LeftButtonDown = (1 << 6)
FWL_EVENTFLAG_MiddleButtonDown = (1 << 7)
FWL_EVENTFLAG_RightButtonDown = (1 << 8)
FWL_EVENTFLAG = enum_anon_7
enum_anon_8 = c_int
FWL_VKEY_Back = 0x08
FWL_VKEY_Tab = 0x09
FWL_VKEY_NewLine = 0x0A
FWL_VKEY_Clear = 0x0C
FWL_VKEY_Return = 0x0D
FWL_VKEY_Shift = 0x10
FWL_VKEY_Control = 0x11
FWL_VKEY_Menu = 0x12
FWL_VKEY_Pause = 0x13
FWL_VKEY_Capital = 0x14
FWL_VKEY_Kana = 0x15
FWL_VKEY_Hangul = 0x15
FWL_VKEY_Junja = 0x17
FWL_VKEY_Final = 0x18
FWL_VKEY_Hanja = 0x19
FWL_VKEY_Kanji = 0x19
FWL_VKEY_Escape = 0x1B
FWL_VKEY_Convert = 0x1C
FWL_VKEY_NonConvert = 0x1D
FWL_VKEY_Accept = 0x1E
FWL_VKEY_ModeChange = 0x1F
FWL_VKEY_Space = 0x20
FWL_VKEY_Prior = 0x21
FWL_VKEY_Next = 0x22
FWL_VKEY_End = 0x23
FWL_VKEY_Home = 0x24
FWL_VKEY_Left = 0x25
FWL_VKEY_Up = 0x26
FWL_VKEY_Right = 0x27
FWL_VKEY_Down = 0x28
FWL_VKEY_Select = 0x29
FWL_VKEY_Print = 0x2A
FWL_VKEY_Execute = 0x2B
FWL_VKEY_Snapshot = 0x2C
FWL_VKEY_Insert = 0x2D
FWL_VKEY_Delete = 0x2E
FWL_VKEY_Help = 0x2F
FWL_VKEY_0 = 0x30
FWL_VKEY_1 = 0x31
FWL_VKEY_2 = 0x32
FWL_VKEY_3 = 0x33
FWL_VKEY_4 = 0x34
FWL_VKEY_5 = 0x35
FWL_VKEY_6 = 0x36
FWL_VKEY_7 = 0x37
FWL_VKEY_8 = 0x38
FWL_VKEY_9 = 0x39
FWL_VKEY_A = 0x41
FWL_VKEY_B = 0x42
FWL_VKEY_C = 0x43
FWL_VKEY_D = 0x44
FWL_VKEY_E = 0x45
FWL_VKEY_F = 0x46
FWL_VKEY_G = 0x47
FWL_VKEY_H = 0x48
FWL_VKEY_I = 0x49
FWL_VKEY_J = 0x4A
FWL_VKEY_K = 0x4B
FWL_VKEY_L = 0x4C
FWL_VKEY_M = 0x4D
FWL_VKEY_N = 0x4E
FWL_VKEY_O = 0x4F
FWL_VKEY_P = 0x50
FWL_VKEY_Q = 0x51
FWL_VKEY_R = 0x52
FWL_VKEY_S = 0x53
FWL_VKEY_T = 0x54
FWL_VKEY_U = 0x55
FWL_VKEY_V = 0x56
FWL_VKEY_W = 0x57
FWL_VKEY_X = 0x58
FWL_VKEY_Y = 0x59
FWL_VKEY_Z = 0x5A
FWL_VKEY_LWin = 0x5B
FWL_VKEY_Command = 0x5B
FWL_VKEY_RWin = 0x5C
FWL_VKEY_Apps = 0x5D
FWL_VKEY_Sleep = 0x5F
FWL_VKEY_NumPad0 = 0x60
FWL_VKEY_NumPad1 = 0x61
FWL_VKEY_NumPad2 = 0x62
FWL_VKEY_NumPad3 = 0x63
FWL_VKEY_NumPad4 = 0x64
FWL_VKEY_NumPad5 = 0x65
FWL_VKEY_NumPad6 = 0x66
FWL_VKEY_NumPad7 = 0x67
FWL_VKEY_NumPad8 = 0x68
FWL_VKEY_NumPad9 = 0x69
FWL_VKEY_Multiply = 0x6A
FWL_VKEY_Add = 0x6B
FWL_VKEY_Separator = 0x6C
FWL_VKEY_Subtract = 0x6D
FWL_VKEY_Decimal = 0x6E
FWL_VKEY_Divide = 0x6F
FWL_VKEY_F1 = 0x70
FWL_VKEY_F2 = 0x71
FWL_VKEY_F3 = 0x72
FWL_VKEY_F4 = 0x73
FWL_VKEY_F5 = 0x74
FWL_VKEY_F6 = 0x75
FWL_VKEY_F7 = 0x76
FWL_VKEY_F8 = 0x77
FWL_VKEY_F9 = 0x78
FWL_VKEY_F10 = 0x79
FWL_VKEY_F11 = 0x7A
FWL_VKEY_F12 = 0x7B
FWL_VKEY_F13 = 0x7C
FWL_VKEY_F14 = 0x7D
FWL_VKEY_F15 = 0x7E
FWL_VKEY_F16 = 0x7F
FWL_VKEY_F17 = 0x80
FWL_VKEY_F18 = 0x81
FWL_VKEY_F19 = 0x82
FWL_VKEY_F20 = 0x83
FWL_VKEY_F21 = 0x84
FWL_VKEY_F22 = 0x85
FWL_VKEY_F23 = 0x86
FWL_VKEY_F24 = 0x87
FWL_VKEY_NunLock = 0x90
FWL_VKEY_Scroll = 0x91
FWL_VKEY_LShift = 0xA0
FWL_VKEY_RShift = 0xA1
FWL_VKEY_LControl = 0xA2
FWL_VKEY_RControl = 0xA3
FWL_VKEY_LMenu = 0xA4
FWL_VKEY_RMenu = 0xA5
FWL_VKEY_BROWSER_Back = 0xA6
FWL_VKEY_BROWSER_Forward = 0xA7
FWL_VKEY_BROWSER_Refresh = 0xA8
FWL_VKEY_BROWSER_Stop = 0xA9
FWL_VKEY_BROWSER_Search = 0xAA
FWL_VKEY_BROWSER_Favorites = 0xAB
FWL_VKEY_BROWSER_Home = 0xAC
FWL_VKEY_VOLUME_Mute = 0xAD
FWL_VKEY_VOLUME_Down = 0xAE
FWL_VKEY_VOLUME_Up = 0xAF
FWL_VKEY_MEDIA_NEXT_Track = 0xB0
FWL_VKEY_MEDIA_PREV_Track = 0xB1
FWL_VKEY_MEDIA_Stop = 0xB2
FWL_VKEY_MEDIA_PLAY_Pause = 0xB3
FWL_VKEY_MEDIA_LAUNCH_Mail = 0xB4
FWL_VKEY_MEDIA_LAUNCH_MEDIA_Select = 0xB5
FWL_VKEY_MEDIA_LAUNCH_APP1 = 0xB6
FWL_VKEY_MEDIA_LAUNCH_APP2 = 0xB7
FWL_VKEY_OEM_1 = 0xBA
FWL_VKEY_OEM_Plus = 0xBB
FWL_VKEY_OEM_Comma = 0xBC
FWL_VKEY_OEM_Minus = 0xBD
FWL_VKEY_OEM_Period = 0xBE
FWL_VKEY_OEM_2 = 0xBF
FWL_VKEY_OEM_3 = 0xC0
FWL_VKEY_OEM_4 = 0xDB
FWL_VKEY_OEM_5 = 0xDC
FWL_VKEY_OEM_6 = 0xDD
FWL_VKEY_OEM_7 = 0xDE
FWL_VKEY_OEM_8 = 0xDF
FWL_VKEY_OEM_102 = 0xE2
FWL_VKEY_ProcessKey = 0xE5
FWL_VKEY_Packet = 0xE7
FWL_VKEY_Attn = 0xF6
FWL_VKEY_Crsel = 0xF7
FWL_VKEY_Exsel = 0xF8
FWL_VKEY_Ereof = 0xF9
FWL_VKEY_Play = 0xFA
FWL_VKEY_Zoom = 0xFB
FWL_VKEY_NoName = 0xFC
FWL_VKEY_PA1 = 0xFD
FWL_VKEY_OEM_Clear = 0xFE
FWL_VKEY_Unknown = 0
FWL_VKEYCODE = enum_anon_8

if hasattr(_lib, "FPDFDoc_GetJavaScriptActionCount"):
    FPDFDoc_GetJavaScriptActionCount = _lib.FPDFDoc_GetJavaScriptActionCount
    FPDFDoc_GetJavaScriptActionCount.argtypes = [FPDF_DOCUMENT]
    FPDFDoc_GetJavaScriptActionCount.restype = c_int

if hasattr(_lib, "FPDFDoc_GetJavaScriptAction"):
    FPDFDoc_GetJavaScriptAction = _lib.FPDFDoc_GetJavaScriptAction
    FPDFDoc_GetJavaScriptAction.argtypes = [FPDF_DOCUMENT, c_int]
    FPDFDoc_GetJavaScriptAction.restype = FPDF_JAVASCRIPT_ACTION

if hasattr(_lib, "FPDFDoc_CloseJavaScriptAction"):
    FPDFDoc_CloseJavaScriptAction = _lib.FPDFDoc_CloseJavaScriptAction
    FPDFDoc_CloseJavaScriptAction.argtypes = [FPDF_JAVASCRIPT_ACTION]
    FPDFDoc_CloseJavaScriptAction.restype = None

if hasattr(_lib, "FPDFJavaScriptAction_GetName"):
    FPDFJavaScriptAction_GetName = _lib.FPDFJavaScriptAction_GetName
    FPDFJavaScriptAction_GetName.argtypes = [FPDF_JAVASCRIPT_ACTION, POINTER(FPDF_WCHAR), c_ulong]
    FPDFJavaScriptAction_GetName.restype = c_ulong

if hasattr(_lib, "FPDFJavaScriptAction_GetScript"):
    FPDFJavaScriptAction_GetScript = _lib.FPDFJavaScriptAction_GetScript
    FPDFJavaScriptAction_GetScript.argtypes = [FPDF_JAVASCRIPT_ACTION, POINTER(FPDF_WCHAR), c_ulong]
    FPDFJavaScriptAction_GetScript.restype = c_ulong

if hasattr(_lib, "FPDF_ImportPagesByIndex"):
    FPDF_ImportPagesByIndex = _lib.FPDF_ImportPagesByIndex
    FPDF_ImportPagesByIndex.argtypes = [FPDF_DOCUMENT, FPDF_DOCUMENT, POINTER(c_int), c_ulong, c_int]
    FPDF_ImportPagesByIndex.restype = FPDF_BOOL

if hasattr(_lib, "FPDF_ImportPages"):
    FPDF_ImportPages = _lib.FPDF_ImportPages
    FPDF_ImportPages.argtypes = [FPDF_DOCUMENT, FPDF_DOCUMENT, FPDF_BYTESTRING, c_int]
    FPDF_ImportPages.restype = FPDF_BOOL

if hasattr(_lib, "FPDF_ImportNPagesToOne"):
    FPDF_ImportNPagesToOne = _lib.FPDF_ImportNPagesToOne
    FPDF_ImportNPagesToOne.argtypes = [FPDF_DOCUMENT, c_float, c_float, c_size_t, c_size_t]
    FPDF_ImportNPagesToOne.restype = FPDF_DOCUMENT

if hasattr(_lib, "FPDF_NewXObjectFromPage"):
    FPDF_NewXObjectFromPage = _lib.FPDF_NewXObjectFromPage
    FPDF_NewXObjectFromPage.argtypes = [FPDF_DOCUMENT, FPDF_DOCUMENT, c_int]
    FPDF_NewXObjectFromPage.restype = FPDF_XOBJECT

if hasattr(_lib, "FPDF_CloseXObject"):
    FPDF_CloseXObject = _lib.FPDF_CloseXObject
    FPDF_CloseXObject.argtypes = [FPDF_XOBJECT]
    FPDF_CloseXObject.restype = None

if hasattr(_lib, "FPDF_NewFormObjectFromXObject"):
    FPDF_NewFormObjectFromXObject = _lib.FPDF_NewFormObjectFromXObject
    FPDF_NewFormObjectFromXObject.argtypes = [FPDF_XOBJECT]
    FPDF_NewFormObjectFromXObject.restype = FPDF_PAGEOBJECT

if hasattr(_lib, "FPDF_CopyViewerPreferences"):
    FPDF_CopyViewerPreferences = _lib.FPDF_CopyViewerPreferences
    FPDF_CopyViewerPreferences.argtypes = [FPDF_DOCUMENT, FPDF_DOCUMENT]
    FPDF_CopyViewerPreferences.restype = FPDF_BOOL

class struct__IFSDK_PAUSE (Structure):
    __slots__ = ['version', 'NeedToPauseNow', 'user']
struct__IFSDK_PAUSE._fields_ = [
    ('version', c_int),
    ('NeedToPauseNow', CFUNCTYPE(FPDF_BOOL, POINTER(struct__IFSDK_PAUSE))),
    ('user', POINTER(None)),
]
IFSDK_PAUSE = struct__IFSDK_PAUSE

if hasattr(_lib, "FPDF_RenderPageBitmapWithColorScheme_Start"):
    FPDF_RenderPageBitmapWithColorScheme_Start = _lib.FPDF_RenderPageBitmapWithColorScheme_Start
    FPDF_RenderPageBitmapWithColorScheme_Start.argtypes = [FPDF_BITMAP, FPDF_PAGE, c_int, c_int, c_int, c_int, c_int, c_int, POINTER(FPDF_COLORSCHEME), POINTER(IFSDK_PAUSE)]
    FPDF_RenderPageBitmapWithColorScheme_Start.restype = c_int

if hasattr(_lib, "FPDF_RenderPageBitmap_Start"):
    FPDF_RenderPageBitmap_Start = _lib.FPDF_RenderPageBitmap_Start
    FPDF_RenderPageBitmap_Start.argtypes = [FPDF_BITMAP, FPDF_PAGE, c_int, c_int, c_int, c_int, c_int, c_int, POINTER(IFSDK_PAUSE)]
    FPDF_RenderPageBitmap_Start.restype = c_int

if hasattr(_lib, "FPDF_RenderPage_Continue"):
    FPDF_RenderPage_Continue = _lib.FPDF_RenderPage_Continue
    FPDF_RenderPage_Continue.argtypes = [FPDF_PAGE, POINTER(IFSDK_PAUSE)]
    FPDF_RenderPage_Continue.restype = c_int

if hasattr(_lib, "FPDF_RenderPage_Close"):
    FPDF_RenderPage_Close = _lib.FPDF_RenderPage_Close
    FPDF_RenderPage_Close.argtypes = [FPDF_PAGE]
    FPDF_RenderPage_Close.restype = None

class struct_FPDF_FILEWRITE_ (Structure):
    __slots__ = ['version', 'WriteBlock']
struct_FPDF_FILEWRITE_._fields_ = [
    ('version', c_int),
    ('WriteBlock', CFUNCTYPE(c_int, POINTER(struct_FPDF_FILEWRITE_), POINTER(None), c_ulong)),
]
FPDF_FILEWRITE = struct_FPDF_FILEWRITE_

if hasattr(_lib, "FPDF_SaveAsCopy"):
    FPDF_SaveAsCopy = _lib.FPDF_SaveAsCopy
    FPDF_SaveAsCopy.argtypes = [FPDF_DOCUMENT, POINTER(FPDF_FILEWRITE), FPDF_DWORD]
    FPDF_SaveAsCopy.restype = FPDF_BOOL

if hasattr(_lib, "FPDF_SaveWithVersion"):
    FPDF_SaveWithVersion = _lib.FPDF_SaveWithVersion
    FPDF_SaveWithVersion.argtypes = [FPDF_DOCUMENT, POINTER(FPDF_FILEWRITE), FPDF_DWORD, c_int]
    FPDF_SaveWithVersion.restype = FPDF_BOOL

if hasattr(_lib, "FPDFText_GetCharIndexFromTextIndex"):
    FPDFText_GetCharIndexFromTextIndex = _lib.FPDFText_GetCharIndexFromTextIndex
    FPDFText_GetCharIndexFromTextIndex.argtypes = [FPDF_TEXTPAGE, c_int]
    FPDFText_GetCharIndexFromTextIndex.restype = c_int

if hasattr(_lib, "FPDFText_GetTextIndexFromCharIndex"):
    FPDFText_GetTextIndexFromCharIndex = _lib.FPDFText_GetTextIndexFromCharIndex
    FPDFText_GetTextIndexFromCharIndex.argtypes = [FPDF_TEXTPAGE, c_int]
    FPDFText_GetTextIndexFromCharIndex.restype = c_int

if hasattr(_lib, "FPDF_GetSignatureCount"):
    FPDF_GetSignatureCount = _lib.FPDF_GetSignatureCount
    FPDF_GetSignatureCount.argtypes = [FPDF_DOCUMENT]
    FPDF_GetSignatureCount.restype = c_int

if hasattr(_lib, "FPDF_GetSignatureObject"):
    FPDF_GetSignatureObject = _lib.FPDF_GetSignatureObject
    FPDF_GetSignatureObject.argtypes = [FPDF_DOCUMENT, c_int]
    FPDF_GetSignatureObject.restype = FPDF_SIGNATURE

if hasattr(_lib, "FPDFSignatureObj_GetContents"):
    FPDFSignatureObj_GetContents = _lib.FPDFSignatureObj_GetContents
    FPDFSignatureObj_GetContents.argtypes = [FPDF_SIGNATURE, POINTER(None), c_ulong]
    FPDFSignatureObj_GetContents.restype = c_ulong

if hasattr(_lib, "FPDFSignatureObj_GetByteRange"):
    FPDFSignatureObj_GetByteRange = _lib.FPDFSignatureObj_GetByteRange
    FPDFSignatureObj_GetByteRange.argtypes = [FPDF_SIGNATURE, POINTER(c_int), c_ulong]
    FPDFSignatureObj_GetByteRange.restype = c_ulong

if hasattr(_lib, "FPDFSignatureObj_GetSubFilter"):
    FPDFSignatureObj_GetSubFilter = _lib.FPDFSignatureObj_GetSubFilter
    FPDFSignatureObj_GetSubFilter.argtypes = [FPDF_SIGNATURE, POINTER(c_char), c_ulong]
    FPDFSignatureObj_GetSubFilter.restype = c_ulong

if hasattr(_lib, "FPDFSignatureObj_GetReason"):
    FPDFSignatureObj_GetReason = _lib.FPDFSignatureObj_GetReason
    FPDFSignatureObj_GetReason.argtypes = [FPDF_SIGNATURE, POINTER(None), c_ulong]
    FPDFSignatureObj_GetReason.restype = c_ulong

if hasattr(_lib, "FPDFSignatureObj_GetTime"):
    FPDFSignatureObj_GetTime = _lib.FPDFSignatureObj_GetTime
    FPDFSignatureObj_GetTime.argtypes = [FPDF_SIGNATURE, POINTER(c_char), c_ulong]
    FPDFSignatureObj_GetTime.restype = c_ulong

if hasattr(_lib, "FPDFSignatureObj_GetDocMDPPermission"):
    FPDFSignatureObj_GetDocMDPPermission = _lib.FPDFSignatureObj_GetDocMDPPermission
    FPDFSignatureObj_GetDocMDPPermission.argtypes = [FPDF_SIGNATURE]
    FPDFSignatureObj_GetDocMDPPermission.restype = c_uint

if hasattr(_lib, "FPDF_StructTree_GetForPage"):
    FPDF_StructTree_GetForPage = _lib.FPDF_StructTree_GetForPage
    FPDF_StructTree_GetForPage.argtypes = [FPDF_PAGE]
    FPDF_StructTree_GetForPage.restype = FPDF_STRUCTTREE

if hasattr(_lib, "FPDF_StructTree_Close"):
    FPDF_StructTree_Close = _lib.FPDF_StructTree_Close
    FPDF_StructTree_Close.argtypes = [FPDF_STRUCTTREE]
    FPDF_StructTree_Close.restype = None

if hasattr(_lib, "FPDF_StructTree_CountChildren"):
    FPDF_StructTree_CountChildren = _lib.FPDF_StructTree_CountChildren
    FPDF_StructTree_CountChildren.argtypes = [FPDF_STRUCTTREE]
    FPDF_StructTree_CountChildren.restype = c_int

if hasattr(_lib, "FPDF_StructTree_GetChildAtIndex"):
    FPDF_StructTree_GetChildAtIndex = _lib.FPDF_StructTree_GetChildAtIndex
    FPDF_StructTree_GetChildAtIndex.argtypes = [FPDF_STRUCTTREE, c_int]
    FPDF_StructTree_GetChildAtIndex.restype = FPDF_STRUCTELEMENT

if hasattr(_lib, "FPDF_StructElement_GetAltText"):
    FPDF_StructElement_GetAltText = _lib.FPDF_StructElement_GetAltText
    FPDF_StructElement_GetAltText.argtypes = [FPDF_STRUCTELEMENT, POINTER(None), c_ulong]
    FPDF_StructElement_GetAltText.restype = c_ulong

if hasattr(_lib, "FPDF_StructElement_GetActualText"):
    FPDF_StructElement_GetActualText = _lib.FPDF_StructElement_GetActualText
    FPDF_StructElement_GetActualText.argtypes = [FPDF_STRUCTELEMENT, POINTER(None), c_ulong]
    FPDF_StructElement_GetActualText.restype = c_ulong

if hasattr(_lib, "FPDF_StructElement_GetID"):
    FPDF_StructElement_GetID = _lib.FPDF_StructElement_GetID
    FPDF_StructElement_GetID.argtypes = [FPDF_STRUCTELEMENT, POINTER(None), c_ulong]
    FPDF_StructElement_GetID.restype = c_ulong

if hasattr(_lib, "FPDF_StructElement_GetLang"):
    FPDF_StructElement_GetLang = _lib.FPDF_StructElement_GetLang
    FPDF_StructElement_GetLang.argtypes = [FPDF_STRUCTELEMENT, POINTER(None), c_ulong]
    FPDF_StructElement_GetLang.restype = c_ulong

if hasattr(_lib, "FPDF_StructElement_GetStringAttribute"):
    FPDF_StructElement_GetStringAttribute = _lib.FPDF_StructElement_GetStringAttribute
    FPDF_StructElement_GetStringAttribute.argtypes = [FPDF_STRUCTELEMENT, FPDF_BYTESTRING, POINTER(None), c_ulong]
    FPDF_StructElement_GetStringAttribute.restype = c_ulong

if hasattr(_lib, "FPDF_StructElement_GetMarkedContentID"):
    FPDF_StructElement_GetMarkedContentID = _lib.FPDF_StructElement_GetMarkedContentID
    FPDF_StructElement_GetMarkedContentID.argtypes = [FPDF_STRUCTELEMENT]
    FPDF_StructElement_GetMarkedContentID.restype = c_int

if hasattr(_lib, "FPDF_StructElement_GetType"):
    FPDF_StructElement_GetType = _lib.FPDF_StructElement_GetType
    FPDF_StructElement_GetType.argtypes = [FPDF_STRUCTELEMENT, POINTER(None), c_ulong]
    FPDF_StructElement_GetType.restype = c_ulong

if hasattr(_lib, "FPDF_StructElement_GetObjType"):
    FPDF_StructElement_GetObjType = _lib.FPDF_StructElement_GetObjType
    FPDF_StructElement_GetObjType.argtypes = [FPDF_STRUCTELEMENT, POINTER(None), c_ulong]
    FPDF_StructElement_GetObjType.restype = c_ulong

if hasattr(_lib, "FPDF_StructElement_GetTitle"):
    FPDF_StructElement_GetTitle = _lib.FPDF_StructElement_GetTitle
    FPDF_StructElement_GetTitle.argtypes = [FPDF_STRUCTELEMENT, POINTER(None), c_ulong]
    FPDF_StructElement_GetTitle.restype = c_ulong

if hasattr(_lib, "FPDF_StructElement_CountChildren"):
    FPDF_StructElement_CountChildren = _lib.FPDF_StructElement_CountChildren
    FPDF_StructElement_CountChildren.argtypes = [FPDF_STRUCTELEMENT]
    FPDF_StructElement_CountChildren.restype = c_int

if hasattr(_lib, "FPDF_StructElement_GetChildAtIndex"):
    FPDF_StructElement_GetChildAtIndex = _lib.FPDF_StructElement_GetChildAtIndex
    FPDF_StructElement_GetChildAtIndex.argtypes = [FPDF_STRUCTELEMENT, c_int]
    FPDF_StructElement_GetChildAtIndex.restype = FPDF_STRUCTELEMENT

if hasattr(_lib, "FPDF_StructElement_GetParent"):
    FPDF_StructElement_GetParent = _lib.FPDF_StructElement_GetParent
    FPDF_StructElement_GetParent.argtypes = [FPDF_STRUCTELEMENT]
    FPDF_StructElement_GetParent.restype = FPDF_STRUCTELEMENT

if hasattr(_lib, "FPDF_StructElement_GetAttributeCount"):
    FPDF_StructElement_GetAttributeCount = _lib.FPDF_StructElement_GetAttributeCount
    FPDF_StructElement_GetAttributeCount.argtypes = [FPDF_STRUCTELEMENT]
    FPDF_StructElement_GetAttributeCount.restype = c_int

if hasattr(_lib, "FPDF_StructElement_GetAttributeAtIndex"):
    FPDF_StructElement_GetAttributeAtIndex = _lib.FPDF_StructElement_GetAttributeAtIndex
    FPDF_StructElement_GetAttributeAtIndex.argtypes = [FPDF_STRUCTELEMENT, c_int]
    FPDF_StructElement_GetAttributeAtIndex.restype = FPDF_STRUCTELEMENT_ATTR

if hasattr(_lib, "FPDF_StructElement_Attr_GetCount"):
    FPDF_StructElement_Attr_GetCount = _lib.FPDF_StructElement_Attr_GetCount
    FPDF_StructElement_Attr_GetCount.argtypes = [FPDF_STRUCTELEMENT_ATTR]
    FPDF_StructElement_Attr_GetCount.restype = c_int

if hasattr(_lib, "FPDF_StructElement_Attr_GetName"):
    FPDF_StructElement_Attr_GetName = _lib.FPDF_StructElement_Attr_GetName
    FPDF_StructElement_Attr_GetName.argtypes = [FPDF_STRUCTELEMENT_ATTR, c_int, POINTER(None), c_ulong, POINTER(c_ulong)]
    FPDF_StructElement_Attr_GetName.restype = FPDF_BOOL

if hasattr(_lib, "FPDF_StructElement_Attr_GetType"):
    FPDF_StructElement_Attr_GetType = _lib.FPDF_StructElement_Attr_GetType
    FPDF_StructElement_Attr_GetType.argtypes = [FPDF_STRUCTELEMENT_ATTR, FPDF_BYTESTRING]
    FPDF_StructElement_Attr_GetType.restype = FPDF_OBJECT_TYPE

if hasattr(_lib, "FPDF_StructElement_Attr_GetBooleanValue"):
    FPDF_StructElement_Attr_GetBooleanValue = _lib.FPDF_StructElement_Attr_GetBooleanValue
    FPDF_StructElement_Attr_GetBooleanValue.argtypes = [FPDF_STRUCTELEMENT_ATTR, FPDF_BYTESTRING, POINTER(FPDF_BOOL)]
    FPDF_StructElement_Attr_GetBooleanValue.restype = FPDF_BOOL

if hasattr(_lib, "FPDF_StructElement_Attr_GetNumberValue"):
    FPDF_StructElement_Attr_GetNumberValue = _lib.FPDF_StructElement_Attr_GetNumberValue
    FPDF_StructElement_Attr_GetNumberValue.argtypes = [FPDF_STRUCTELEMENT_ATTR, FPDF_BYTESTRING, POINTER(c_float)]
    FPDF_StructElement_Attr_GetNumberValue.restype = FPDF_BOOL

if hasattr(_lib, "FPDF_StructElement_Attr_GetStringValue"):
    FPDF_StructElement_Attr_GetStringValue = _lib.FPDF_StructElement_Attr_GetStringValue
    FPDF_StructElement_Attr_GetStringValue.argtypes = [FPDF_STRUCTELEMENT_ATTR, FPDF_BYTESTRING, POINTER(None), c_ulong, POINTER(c_ulong)]
    FPDF_StructElement_Attr_GetStringValue.restype = FPDF_BOOL

if hasattr(_lib, "FPDF_StructElement_Attr_GetBlobValue"):
    FPDF_StructElement_Attr_GetBlobValue = _lib.FPDF_StructElement_Attr_GetBlobValue
    FPDF_StructElement_Attr_GetBlobValue.argtypes = [FPDF_STRUCTELEMENT_ATTR, FPDF_BYTESTRING, POINTER(None), c_ulong, POINTER(c_ulong)]
    FPDF_StructElement_Attr_GetBlobValue.restype = FPDF_BOOL

if hasattr(_lib, "FPDF_StructElement_GetMarkedContentIdCount"):
    FPDF_StructElement_GetMarkedContentIdCount = _lib.FPDF_StructElement_GetMarkedContentIdCount
    FPDF_StructElement_GetMarkedContentIdCount.argtypes = [FPDF_STRUCTELEMENT]
    FPDF_StructElement_GetMarkedContentIdCount.restype = c_int

if hasattr(_lib, "FPDF_StructElement_GetMarkedContentIdAtIndex"):
    FPDF_StructElement_GetMarkedContentIdAtIndex = _lib.FPDF_StructElement_GetMarkedContentIdAtIndex
    FPDF_StructElement_GetMarkedContentIdAtIndex.argtypes = [FPDF_STRUCTELEMENT, c_int]
    FPDF_StructElement_GetMarkedContentIdAtIndex.restype = c_int

class struct__FPDF_SYSFONTINFO (Structure):
    __slots__ = ['version', 'Release', 'EnumFonts', 'MapFont', 'GetFont', 'GetFontData', 'GetFaceName', 'GetFontCharset', 'DeleteFont']
struct__FPDF_SYSFONTINFO._fields_ = [
    ('version', c_int),
    ('Release', CFUNCTYPE(None, POINTER(struct__FPDF_SYSFONTINFO))),
    ('EnumFonts', CFUNCTYPE(None, POINTER(struct__FPDF_SYSFONTINFO), POINTER(None))),
    ('MapFont', CFUNCTYPE(POINTER(c_ubyte), POINTER(struct__FPDF_SYSFONTINFO), c_int, FPDF_BOOL, c_int, c_int, POINTER(c_char), POINTER(FPDF_BOOL))),
    ('GetFont', CFUNCTYPE(POINTER(c_ubyte), POINTER(struct__FPDF_SYSFONTINFO), POINTER(c_char))),
    ('GetFontData', CFUNCTYPE(c_ulong, POINTER(struct__FPDF_SYSFONTINFO), POINTER(None), c_uint, POINTER(c_ubyte), c_ulong)),
    ('GetFaceName', CFUNCTYPE(c_ulong, POINTER(struct__FPDF_SYSFONTINFO), POINTER(None), POINTER(c_char), c_ulong)),
    ('GetFontCharset', CFUNCTYPE(c_int, POINTER(struct__FPDF_SYSFONTINFO), POINTER(None))),
    ('DeleteFont', CFUNCTYPE(None, POINTER(struct__FPDF_SYSFONTINFO), POINTER(None))),
]
FPDF_SYSFONTINFO = struct__FPDF_SYSFONTINFO

class struct_FPDF_CharsetFontMap_ (Structure):
    __slots__ = ['charset', 'fontname']
struct_FPDF_CharsetFontMap_._fields_ = [
    ('charset', c_int),
    ('fontname', POINTER(c_char)),
]
FPDF_CharsetFontMap = struct_FPDF_CharsetFontMap_

if hasattr(_lib, "FPDF_GetDefaultTTFMap"):
    FPDF_GetDefaultTTFMap = _lib.FPDF_GetDefaultTTFMap
    FPDF_GetDefaultTTFMap.argtypes = []
    FPDF_GetDefaultTTFMap.restype = POINTER(FPDF_CharsetFontMap)

if hasattr(_lib, "FPDF_AddInstalledFont"):
    FPDF_AddInstalledFont = _lib.FPDF_AddInstalledFont
    FPDF_AddInstalledFont.argtypes = [POINTER(None), POINTER(c_char), c_int]
    FPDF_AddInstalledFont.restype = None

if hasattr(_lib, "FPDF_SetSystemFontInfo"):
    FPDF_SetSystemFontInfo = _lib.FPDF_SetSystemFontInfo
    FPDF_SetSystemFontInfo.argtypes = [POINTER(FPDF_SYSFONTINFO)]
    FPDF_SetSystemFontInfo.restype = None

if hasattr(_lib, "FPDF_GetDefaultSystemFontInfo"):
    FPDF_GetDefaultSystemFontInfo = _lib.FPDF_GetDefaultSystemFontInfo
    FPDF_GetDefaultSystemFontInfo.argtypes = []
    FPDF_GetDefaultSystemFontInfo.restype = POINTER(FPDF_SYSFONTINFO)

if hasattr(_lib, "FPDF_FreeDefaultSystemFontInfo"):
    FPDF_FreeDefaultSystemFontInfo = _lib.FPDF_FreeDefaultSystemFontInfo
    FPDF_FreeDefaultSystemFontInfo.argtypes = [POINTER(FPDF_SYSFONTINFO)]
    FPDF_FreeDefaultSystemFontInfo.restype = None

if hasattr(_lib, "FPDFText_LoadPage"):
    FPDFText_LoadPage = _lib.FPDFText_LoadPage
    FPDFText_LoadPage.argtypes = [FPDF_PAGE]
    FPDFText_LoadPage.restype = FPDF_TEXTPAGE

if hasattr(_lib, "FPDFText_ClosePage"):
    FPDFText_ClosePage = _lib.FPDFText_ClosePage
    FPDFText_ClosePage.argtypes = [FPDF_TEXTPAGE]
    FPDFText_ClosePage.restype = None

if hasattr(_lib, "FPDFText_CountChars"):
    FPDFText_CountChars = _lib.FPDFText_CountChars
    FPDFText_CountChars.argtypes = [FPDF_TEXTPAGE]
    FPDFText_CountChars.restype = c_int

if hasattr(_lib, "FPDFText_GetUnicode"):
    FPDFText_GetUnicode = _lib.FPDFText_GetUnicode
    FPDFText_GetUnicode.argtypes = [FPDF_TEXTPAGE, c_int]
    FPDFText_GetUnicode.restype = c_uint

if hasattr(_lib, "FPDFText_IsGenerated"):
    FPDFText_IsGenerated = _lib.FPDFText_IsGenerated
    FPDFText_IsGenerated.argtypes = [FPDF_TEXTPAGE, c_int]
    FPDFText_IsGenerated.restype = c_int

if hasattr(_lib, "FPDFText_IsHyphen"):
    FPDFText_IsHyphen = _lib.FPDFText_IsHyphen
    FPDFText_IsHyphen.argtypes = [FPDF_TEXTPAGE, c_int]
    FPDFText_IsHyphen.restype = c_int

if hasattr(_lib, "FPDFText_HasUnicodeMapError"):
    FPDFText_HasUnicodeMapError = _lib.FPDFText_HasUnicodeMapError
    FPDFText_HasUnicodeMapError.argtypes = [FPDF_TEXTPAGE, c_int]
    FPDFText_HasUnicodeMapError.restype = c_int

if hasattr(_lib, "FPDFText_GetFontSize"):
    FPDFText_GetFontSize = _lib.FPDFText_GetFontSize
    FPDFText_GetFontSize.argtypes = [FPDF_TEXTPAGE, c_int]
    FPDFText_GetFontSize.restype = c_double

if hasattr(_lib, "FPDFText_GetFontInfo"):
    FPDFText_GetFontInfo = _lib.FPDFText_GetFontInfo
    FPDFText_GetFontInfo.argtypes = [FPDF_TEXTPAGE, c_int, POINTER(None), c_ulong, POINTER(c_int)]
    FPDFText_GetFontInfo.restype = c_ulong

if hasattr(_lib, "FPDFText_GetFontWeight"):
    FPDFText_GetFontWeight = _lib.FPDFText_GetFontWeight
    FPDFText_GetFontWeight.argtypes = [FPDF_TEXTPAGE, c_int]
    FPDFText_GetFontWeight.restype = c_int

if hasattr(_lib, "FPDFText_GetTextRenderMode"):
    FPDFText_GetTextRenderMode = _lib.FPDFText_GetTextRenderMode
    FPDFText_GetTextRenderMode.argtypes = [FPDF_TEXTPAGE, c_int]
    FPDFText_GetTextRenderMode.restype = FPDF_TEXT_RENDERMODE

if hasattr(_lib, "FPDFText_GetFillColor"):
    FPDFText_GetFillColor = _lib.FPDFText_GetFillColor
    FPDFText_GetFillColor.argtypes = [FPDF_TEXTPAGE, c_int, POINTER(c_uint), POINTER(c_uint), POINTER(c_uint), POINTER(c_uint)]
    FPDFText_GetFillColor.restype = FPDF_BOOL

if hasattr(_lib, "FPDFText_GetStrokeColor"):
    FPDFText_GetStrokeColor = _lib.FPDFText_GetStrokeColor
    FPDFText_GetStrokeColor.argtypes = [FPDF_TEXTPAGE, c_int, POINTER(c_uint), POINTER(c_uint), POINTER(c_uint), POINTER(c_uint)]
    FPDFText_GetStrokeColor.restype = FPDF_BOOL

if hasattr(_lib, "FPDFText_GetCharAngle"):
    FPDFText_GetCharAngle = _lib.FPDFText_GetCharAngle
    FPDFText_GetCharAngle.argtypes = [FPDF_TEXTPAGE, c_int]
    FPDFText_GetCharAngle.restype = c_float

if hasattr(_lib, "FPDFText_GetCharBox"):
    FPDFText_GetCharBox = _lib.FPDFText_GetCharBox
    FPDFText_GetCharBox.argtypes = [FPDF_TEXTPAGE, c_int, POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double)]
    FPDFText_GetCharBox.restype = FPDF_BOOL

if hasattr(_lib, "FPDFText_GetLooseCharBox"):
    FPDFText_GetLooseCharBox = _lib.FPDFText_GetLooseCharBox
    FPDFText_GetLooseCharBox.argtypes = [FPDF_TEXTPAGE, c_int, POINTER(FS_RECTF)]
    FPDFText_GetLooseCharBox.restype = FPDF_BOOL

if hasattr(_lib, "FPDFText_GetMatrix"):
    FPDFText_GetMatrix = _lib.FPDFText_GetMatrix
    FPDFText_GetMatrix.argtypes = [FPDF_TEXTPAGE, c_int, POINTER(FS_MATRIX)]
    FPDFText_GetMatrix.restype = FPDF_BOOL

if hasattr(_lib, "FPDFText_GetCharOrigin"):
    FPDFText_GetCharOrigin = _lib.FPDFText_GetCharOrigin
    FPDFText_GetCharOrigin.argtypes = [FPDF_TEXTPAGE, c_int, POINTER(c_double), POINTER(c_double)]
    FPDFText_GetCharOrigin.restype = FPDF_BOOL

if hasattr(_lib, "FPDFText_GetCharIndexAtPos"):
    FPDFText_GetCharIndexAtPos = _lib.FPDFText_GetCharIndexAtPos
    FPDFText_GetCharIndexAtPos.argtypes = [FPDF_TEXTPAGE, c_double, c_double, c_double, c_double]
    FPDFText_GetCharIndexAtPos.restype = c_int

if hasattr(_lib, "FPDFText_GetText"):
    FPDFText_GetText = _lib.FPDFText_GetText
    FPDFText_GetText.argtypes = [FPDF_TEXTPAGE, c_int, c_int, POINTER(c_ushort)]
    FPDFText_GetText.restype = c_int

if hasattr(_lib, "FPDFText_CountRects"):
    FPDFText_CountRects = _lib.FPDFText_CountRects
    FPDFText_CountRects.argtypes = [FPDF_TEXTPAGE, c_int, c_int]
    FPDFText_CountRects.restype = c_int

if hasattr(_lib, "FPDFText_GetRect"):
    FPDFText_GetRect = _lib.FPDFText_GetRect
    FPDFText_GetRect.argtypes = [FPDF_TEXTPAGE, c_int, POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double)]
    FPDFText_GetRect.restype = FPDF_BOOL

if hasattr(_lib, "FPDFText_GetBoundedText"):
    FPDFText_GetBoundedText = _lib.FPDFText_GetBoundedText
    FPDFText_GetBoundedText.argtypes = [FPDF_TEXTPAGE, c_double, c_double, c_double, c_double, POINTER(c_ushort), c_int]
    FPDFText_GetBoundedText.restype = c_int

if hasattr(_lib, "FPDFText_FindStart"):
    FPDFText_FindStart = _lib.FPDFText_FindStart
    FPDFText_FindStart.argtypes = [FPDF_TEXTPAGE, FPDF_WIDESTRING, c_ulong, c_int]
    FPDFText_FindStart.restype = FPDF_SCHHANDLE

if hasattr(_lib, "FPDFText_FindNext"):
    FPDFText_FindNext = _lib.FPDFText_FindNext
    FPDFText_FindNext.argtypes = [FPDF_SCHHANDLE]
    FPDFText_FindNext.restype = FPDF_BOOL

if hasattr(_lib, "FPDFText_FindPrev"):
    FPDFText_FindPrev = _lib.FPDFText_FindPrev
    FPDFText_FindPrev.argtypes = [FPDF_SCHHANDLE]
    FPDFText_FindPrev.restype = FPDF_BOOL

if hasattr(_lib, "FPDFText_GetSchResultIndex"):
    FPDFText_GetSchResultIndex = _lib.FPDFText_GetSchResultIndex
    FPDFText_GetSchResultIndex.argtypes = [FPDF_SCHHANDLE]
    FPDFText_GetSchResultIndex.restype = c_int

if hasattr(_lib, "FPDFText_GetSchCount"):
    FPDFText_GetSchCount = _lib.FPDFText_GetSchCount
    FPDFText_GetSchCount.argtypes = [FPDF_SCHHANDLE]
    FPDFText_GetSchCount.restype = c_int

if hasattr(_lib, "FPDFText_FindClose"):
    FPDFText_FindClose = _lib.FPDFText_FindClose
    FPDFText_FindClose.argtypes = [FPDF_SCHHANDLE]
    FPDFText_FindClose.restype = None

if hasattr(_lib, "FPDFLink_LoadWebLinks"):
    FPDFLink_LoadWebLinks = _lib.FPDFLink_LoadWebLinks
    FPDFLink_LoadWebLinks.argtypes = [FPDF_TEXTPAGE]
    FPDFLink_LoadWebLinks.restype = FPDF_PAGELINK

if hasattr(_lib, "FPDFLink_CountWebLinks"):
    FPDFLink_CountWebLinks = _lib.FPDFLink_CountWebLinks
    FPDFLink_CountWebLinks.argtypes = [FPDF_PAGELINK]
    FPDFLink_CountWebLinks.restype = c_int

if hasattr(_lib, "FPDFLink_GetURL"):
    FPDFLink_GetURL = _lib.FPDFLink_GetURL
    FPDFLink_GetURL.argtypes = [FPDF_PAGELINK, c_int, POINTER(c_ushort), c_int]
    FPDFLink_GetURL.restype = c_int

if hasattr(_lib, "FPDFLink_CountRects"):
    FPDFLink_CountRects = _lib.FPDFLink_CountRects
    FPDFLink_CountRects.argtypes = [FPDF_PAGELINK, c_int]
    FPDFLink_CountRects.restype = c_int

if hasattr(_lib, "FPDFLink_GetRect"):
    FPDFLink_GetRect = _lib.FPDFLink_GetRect
    FPDFLink_GetRect.argtypes = [FPDF_PAGELINK, c_int, c_int, POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double)]
    FPDFLink_GetRect.restype = FPDF_BOOL

if hasattr(_lib, "FPDFLink_GetTextRange"):
    FPDFLink_GetTextRange = _lib.FPDFLink_GetTextRange
    FPDFLink_GetTextRange.argtypes = [FPDF_PAGELINK, c_int, POINTER(c_int), POINTER(c_int)]
    FPDFLink_GetTextRange.restype = FPDF_BOOL

if hasattr(_lib, "FPDFLink_CloseWebLinks"):
    FPDFLink_CloseWebLinks = _lib.FPDFLink_CloseWebLinks
    FPDFLink_CloseWebLinks.argtypes = [FPDF_PAGELINK]
    FPDFLink_CloseWebLinks.restype = None

if hasattr(_lib, "FPDFPage_GetDecodedThumbnailData"):
    FPDFPage_GetDecodedThumbnailData = _lib.FPDFPage_GetDecodedThumbnailData
    FPDFPage_GetDecodedThumbnailData.argtypes = [FPDF_PAGE, POINTER(None), c_ulong]
    FPDFPage_GetDecodedThumbnailData.restype = c_ulong

if hasattr(_lib, "FPDFPage_GetRawThumbnailData"):
    FPDFPage_GetRawThumbnailData = _lib.FPDFPage_GetRawThumbnailData
    FPDFPage_GetRawThumbnailData.argtypes = [FPDF_PAGE, POINTER(None), c_ulong]
    FPDFPage_GetRawThumbnailData.restype = c_ulong

if hasattr(_lib, "FPDFPage_GetThumbnailAsBitmap"):
    FPDFPage_GetThumbnailAsBitmap = _lib.FPDFPage_GetThumbnailAsBitmap
    FPDFPage_GetThumbnailAsBitmap.argtypes = [FPDF_PAGE]
    FPDFPage_GetThumbnailAsBitmap.restype = FPDF_BITMAP

if hasattr(_lib, "FPDFPage_SetMediaBox"):
    FPDFPage_SetMediaBox = _lib.FPDFPage_SetMediaBox
    FPDFPage_SetMediaBox.argtypes = [FPDF_PAGE, c_float, c_float, c_float, c_float]
    FPDFPage_SetMediaBox.restype = None

if hasattr(_lib, "FPDFPage_SetCropBox"):
    FPDFPage_SetCropBox = _lib.FPDFPage_SetCropBox
    FPDFPage_SetCropBox.argtypes = [FPDF_PAGE, c_float, c_float, c_float, c_float]
    FPDFPage_SetCropBox.restype = None

if hasattr(_lib, "FPDFPage_SetBleedBox"):
    FPDFPage_SetBleedBox = _lib.FPDFPage_SetBleedBox
    FPDFPage_SetBleedBox.argtypes = [FPDF_PAGE, c_float, c_float, c_float, c_float]
    FPDFPage_SetBleedBox.restype = None

if hasattr(_lib, "FPDFPage_SetTrimBox"):
    FPDFPage_SetTrimBox = _lib.FPDFPage_SetTrimBox
    FPDFPage_SetTrimBox.argtypes = [FPDF_PAGE, c_float, c_float, c_float, c_float]
    FPDFPage_SetTrimBox.restype = None

if hasattr(_lib, "FPDFPage_SetArtBox"):
    FPDFPage_SetArtBox = _lib.FPDFPage_SetArtBox
    FPDFPage_SetArtBox.argtypes = [FPDF_PAGE, c_float, c_float, c_float, c_float]
    FPDFPage_SetArtBox.restype = None

if hasattr(_lib, "FPDFPage_GetMediaBox"):
    FPDFPage_GetMediaBox = _lib.FPDFPage_GetMediaBox
    FPDFPage_GetMediaBox.argtypes = [FPDF_PAGE, POINTER(c_float), POINTER(c_float), POINTER(c_float), POINTER(c_float)]
    FPDFPage_GetMediaBox.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPage_GetCropBox"):
    FPDFPage_GetCropBox = _lib.FPDFPage_GetCropBox
    FPDFPage_GetCropBox.argtypes = [FPDF_PAGE, POINTER(c_float), POINTER(c_float), POINTER(c_float), POINTER(c_float)]
    FPDFPage_GetCropBox.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPage_GetBleedBox"):
    FPDFPage_GetBleedBox = _lib.FPDFPage_GetBleedBox
    FPDFPage_GetBleedBox.argtypes = [FPDF_PAGE, POINTER(c_float), POINTER(c_float), POINTER(c_float), POINTER(c_float)]
    FPDFPage_GetBleedBox.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPage_GetTrimBox"):
    FPDFPage_GetTrimBox = _lib.FPDFPage_GetTrimBox
    FPDFPage_GetTrimBox.argtypes = [FPDF_PAGE, POINTER(c_float), POINTER(c_float), POINTER(c_float), POINTER(c_float)]
    FPDFPage_GetTrimBox.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPage_GetArtBox"):
    FPDFPage_GetArtBox = _lib.FPDFPage_GetArtBox
    FPDFPage_GetArtBox.argtypes = [FPDF_PAGE, POINTER(c_float), POINTER(c_float), POINTER(c_float), POINTER(c_float)]
    FPDFPage_GetArtBox.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPage_TransFormWithClip"):
    FPDFPage_TransFormWithClip = _lib.FPDFPage_TransFormWithClip
    FPDFPage_TransFormWithClip.argtypes = [FPDF_PAGE, POINTER(FS_MATRIX), POINTER(FS_RECTF)]
    FPDFPage_TransFormWithClip.restype = FPDF_BOOL

if hasattr(_lib, "FPDFPageObj_TransformClipPath"):
    FPDFPageObj_TransformClipPath = _lib.FPDFPageObj_TransformClipPath
    FPDFPageObj_TransformClipPath.argtypes = [FPDF_PAGEOBJECT, c_double, c_double, c_double, c_double, c_double, c_double]
    FPDFPageObj_TransformClipPath.restype = None

if hasattr(_lib, "FPDFPageObj_GetClipPath"):
    FPDFPageObj_GetClipPath = _lib.FPDFPageObj_GetClipPath
    FPDFPageObj_GetClipPath.argtypes = [FPDF_PAGEOBJECT]
    FPDFPageObj_GetClipPath.restype = FPDF_CLIPPATH

if hasattr(_lib, "FPDFClipPath_CountPaths"):
    FPDFClipPath_CountPaths = _lib.FPDFClipPath_CountPaths
    FPDFClipPath_CountPaths.argtypes = [FPDF_CLIPPATH]
    FPDFClipPath_CountPaths.restype = c_int

if hasattr(_lib, "FPDFClipPath_CountPathSegments"):
    FPDFClipPath_CountPathSegments = _lib.FPDFClipPath_CountPathSegments
    FPDFClipPath_CountPathSegments.argtypes = [FPDF_CLIPPATH, c_int]
    FPDFClipPath_CountPathSegments.restype = c_int

if hasattr(_lib, "FPDFClipPath_GetPathSegment"):
    FPDFClipPath_GetPathSegment = _lib.FPDFClipPath_GetPathSegment
    FPDFClipPath_GetPathSegment.argtypes = [FPDF_CLIPPATH, c_int, c_int]
    FPDFClipPath_GetPathSegment.restype = FPDF_PATHSEGMENT

if hasattr(_lib, "FPDF_CreateClipPath"):
    FPDF_CreateClipPath = _lib.FPDF_CreateClipPath
    FPDF_CreateClipPath.argtypes = [c_float, c_float, c_float, c_float]
    FPDF_CreateClipPath.restype = FPDF_CLIPPATH

if hasattr(_lib, "FPDF_DestroyClipPath"):
    FPDF_DestroyClipPath = _lib.FPDF_DestroyClipPath
    FPDF_DestroyClipPath.argtypes = [FPDF_CLIPPATH]
    FPDF_DestroyClipPath.restype = None

if hasattr(_lib, "FPDFPage_InsertClipPath"):
    FPDFPage_InsertClipPath = _lib.FPDFPage_InsertClipPath
    FPDFPage_InsertClipPath.argtypes = [FPDF_PAGE, FPDF_CLIPPATH]
    FPDFPage_InsertClipPath.restype = None
FPDF_OBJECT_UNKNOWN = 0
FPDF_OBJECT_BOOLEAN = 1
FPDF_OBJECT_NUMBER = 2
FPDF_OBJECT_STRING = 3
FPDF_OBJECT_NAME = 4
FPDF_OBJECT_ARRAY = 5
FPDF_OBJECT_DICTIONARY = 6
FPDF_OBJECT_STREAM = 7
FPDF_OBJECT_NULLOBJ = 8
FPDF_OBJECT_REFERENCE = 9
FPDF_POLICY_MACHINETIME_ACCESS = 0
FPDF_ERR_SUCCESS = 0
FPDF_ERR_UNKNOWN = 1
FPDF_ERR_FILE = 2
FPDF_ERR_FORMAT = 3
FPDF_ERR_PASSWORD = 4
FPDF_ERR_SECURITY = 5
FPDF_ERR_PAGE = 6
FPDF_ANNOT = 0x01
FPDF_LCD_TEXT = 0x02
FPDF_NO_NATIVETEXT = 0x04
FPDF_GRAYSCALE = 0x08
FPDF_DEBUG_INFO = 0x80
FPDF_NO_CATCH = 0x100
FPDF_RENDER_LIMITEDIMAGECACHE = 0x200
FPDF_RENDER_FORCEHALFTONE = 0x400
FPDF_PRINTING = 0x800
FPDF_RENDER_NO_SMOOTHTEXT = 0x1000
FPDF_RENDER_NO_SMOOTHIMAGE = 0x2000
FPDF_RENDER_NO_SMOOTHPATH = 0x4000
FPDF_REVERSE_BYTE_ORDER = 0x10
FPDF_CONVERT_FILL_TO_STROKE = 0x20
FPDFBitmap_Unknown = 0
FPDFBitmap_Gray = 1
FPDFBitmap_BGR = 2
FPDFBitmap_BGRx = 3
FPDFBitmap_BGRA = 4
FORMTYPE_NONE = 0
FORMTYPE_ACRO_FORM = 1
FORMTYPE_XFA_FULL = 2
FORMTYPE_XFA_FOREGROUND = 3
FORMTYPE_COUNT = 4
JSPLATFORM_ALERT_BUTTON_OK = 0
JSPLATFORM_ALERT_BUTTON_OKCANCEL = 1
JSPLATFORM_ALERT_BUTTON_YESNO = 2
JSPLATFORM_ALERT_BUTTON_YESNOCANCEL = 3
JSPLATFORM_ALERT_BUTTON_DEFAULT = JSPLATFORM_ALERT_BUTTON_OK
JSPLATFORM_ALERT_ICON_ERROR = 0
JSPLATFORM_ALERT_ICON_WARNING = 1
JSPLATFORM_ALERT_ICON_QUESTION = 2
JSPLATFORM_ALERT_ICON_STATUS = 3
JSPLATFORM_ALERT_ICON_ASTERISK = 4
JSPLATFORM_ALERT_ICON_DEFAULT = JSPLATFORM_ALERT_ICON_ERROR
JSPLATFORM_ALERT_RETURN_OK = 1
JSPLATFORM_ALERT_RETURN_CANCEL = 2
JSPLATFORM_ALERT_RETURN_NO = 3
JSPLATFORM_ALERT_RETURN_YES = 4
JSPLATFORM_BEEP_ERROR = 0
JSPLATFORM_BEEP_WARNING = 1
JSPLATFORM_BEEP_QUESTION = 2
JSPLATFORM_BEEP_STATUS = 3
JSPLATFORM_BEEP_DEFAULT = 4
FXCT_ARROW = 0
FXCT_NESW = 1
FXCT_NWSE = 2
FXCT_VBEAM = 3
FXCT_HBEAM = 4
FXCT_HAND = 5
FPDFDOC_AACTION_WC = 0x10
FPDFDOC_AACTION_WS = 0x11
FPDFDOC_AACTION_DS = 0x12
FPDFDOC_AACTION_WP = 0x13
FPDFDOC_AACTION_DP = 0x14
FPDFPAGE_AACTION_OPEN = 0
FPDFPAGE_AACTION_CLOSE = 1
FPDF_FORMFIELD_UNKNOWN = 0
FPDF_FORMFIELD_PUSHBUTTON = 1
FPDF_FORMFIELD_CHECKBOX = 2
FPDF_FORMFIELD_RADIOBUTTON = 3
FPDF_FORMFIELD_COMBOBOX = 4
FPDF_FORMFIELD_LISTBOX = 5
FPDF_FORMFIELD_TEXTFIELD = 6
FPDF_FORMFIELD_SIGNATURE = 7
FPDF_FORMFIELD_COUNT = 8
FPDF_ANNOT_UNKNOWN = 0
FPDF_ANNOT_TEXT = 1
FPDF_ANNOT_LINK = 2
FPDF_ANNOT_FREETEXT = 3
FPDF_ANNOT_LINE = 4
FPDF_ANNOT_SQUARE = 5
FPDF_ANNOT_CIRCLE = 6
FPDF_ANNOT_POLYGON = 7
FPDF_ANNOT_POLYLINE = 8
FPDF_ANNOT_HIGHLIGHT = 9
FPDF_ANNOT_UNDERLINE = 10
FPDF_ANNOT_SQUIGGLY = 11
FPDF_ANNOT_STRIKEOUT = 12
FPDF_ANNOT_STAMP = 13
FPDF_ANNOT_CARET = 14
FPDF_ANNOT_INK = 15
FPDF_ANNOT_POPUP = 16
FPDF_ANNOT_FILEATTACHMENT = 17
FPDF_ANNOT_SOUND = 18
FPDF_ANNOT_MOVIE = 19
FPDF_ANNOT_WIDGET = 20
FPDF_ANNOT_SCREEN = 21
FPDF_ANNOT_PRINTERMARK = 22
FPDF_ANNOT_TRAPNET = 23
FPDF_ANNOT_WATERMARK = 24
FPDF_ANNOT_THREED = 25
FPDF_ANNOT_RICHMEDIA = 26
FPDF_ANNOT_XFAWIDGET = 27
FPDF_ANNOT_REDACT = 28
FPDF_ANNOT_FLAG_NONE = 0
FPDF_ANNOT_FLAG_INVISIBLE = (1 << 0)
FPDF_ANNOT_FLAG_HIDDEN = (1 << 1)
FPDF_ANNOT_FLAG_PRINT = (1 << 2)
FPDF_ANNOT_FLAG_NOZOOM = (1 << 3)
FPDF_ANNOT_FLAG_NOROTATE = (1 << 4)
FPDF_ANNOT_FLAG_NOVIEW = (1 << 5)
FPDF_ANNOT_FLAG_READONLY = (1 << 6)
FPDF_ANNOT_FLAG_LOCKED = (1 << 7)
FPDF_ANNOT_FLAG_TOGGLENOVIEW = (1 << 8)
FPDF_ANNOT_APPEARANCEMODE_NORMAL = 0
FPDF_ANNOT_APPEARANCEMODE_ROLLOVER = 1
FPDF_ANNOT_APPEARANCEMODE_DOWN = 2
FPDF_ANNOT_APPEARANCEMODE_COUNT = 3
FPDF_FORMFLAG_NONE = 0
FPDF_FORMFLAG_READONLY = (1 << 0)
FPDF_FORMFLAG_REQUIRED = (1 << 1)
FPDF_FORMFLAG_NOEXPORT = (1 << 2)
FPDF_FORMFLAG_TEXT_MULTILINE = (1 << 12)
FPDF_FORMFLAG_TEXT_PASSWORD = (1 << 13)
FPDF_FORMFLAG_CHOICE_COMBO = (1 << 17)
FPDF_FORMFLAG_CHOICE_EDIT = (1 << 18)
FPDF_FORMFLAG_CHOICE_MULTI_SELECT = (1 << 21)
FPDF_ANNOT_AACTION_KEY_STROKE = 12
FPDF_ANNOT_AACTION_FORMAT = 13
FPDF_ANNOT_AACTION_VALIDATE = 14
FPDF_ANNOT_AACTION_CALCULATE = 15
PDF_LINEARIZATION_UNKNOWN = (-1)
PDF_NOT_LINEARIZED = 0
PDF_LINEARIZED = 1
PDF_DATA_ERROR = (-1)
PDF_DATA_NOTAVAIL = 0
PDF_DATA_AVAIL = 1
PDF_FORM_ERROR = (-1)
PDF_FORM_NOTAVAIL = 0
PDF_FORM_AVAIL = 1
PDF_FORM_NOTEXIST = 2
PDFACTION_UNSUPPORTED = 0
PDFACTION_GOTO = 1
PDFACTION_REMOTEGOTO = 2
PDFACTION_URI = 3
PDFACTION_LAUNCH = 4
PDFACTION_EMBEDDEDGOTO = 5
PDFDEST_VIEW_UNKNOWN_MODE = 0
PDFDEST_VIEW_XYZ = 1
PDFDEST_VIEW_FIT = 2
PDFDEST_VIEW_FITH = 3
PDFDEST_VIEW_FITV = 4
PDFDEST_VIEW_FITR = 5
PDFDEST_VIEW_FITB = 6
PDFDEST_VIEW_FITBH = 7
PDFDEST_VIEW_FITBV = 8

def FPDF_ARGB(a, r, g, b):
    return uint32_t(((((uint32_t(b).value & 0xff) | ((uint32_t(g).value & 0xff) << 8)) | ((uint32_t(r).value & 0xff) << 16)) | ((uint32_t(a).value & 0xff) << 24))).value

def FPDF_GetBValue(argb):
    return uint8_t(argb).value

def FPDF_GetGValue(argb):
    return uint8_t((uint16_t(argb).value >> 8)).value

def FPDF_GetRValue(argb):
    return uint8_t((argb >> 16)).value

def FPDF_GetAValue(argb):
    return uint8_t((argb >> 24)).value
FPDF_COLORSPACE_UNKNOWN = 0
FPDF_COLORSPACE_DEVICEGRAY = 1
FPDF_COLORSPACE_DEVICERGB = 2
FPDF_COLORSPACE_DEVICECMYK = 3
FPDF_COLORSPACE_CALGRAY = 4
FPDF_COLORSPACE_CALRGB = 5
FPDF_COLORSPACE_LAB = 6
FPDF_COLORSPACE_ICCBASED = 7
FPDF_COLORSPACE_SEPARATION = 8
FPDF_COLORSPACE_DEVICEN = 9
FPDF_COLORSPACE_INDEXED = 10
FPDF_COLORSPACE_PATTERN = 11
FPDF_PAGEOBJ_UNKNOWN = 0
FPDF_PAGEOBJ_TEXT = 1
FPDF_PAGEOBJ_PATH = 2
FPDF_PAGEOBJ_IMAGE = 3
FPDF_PAGEOBJ_SHADING = 4
FPDF_PAGEOBJ_FORM = 5
FPDF_SEGMENT_UNKNOWN = (-1)
FPDF_SEGMENT_LINETO = 0
FPDF_SEGMENT_BEZIERTO = 1
FPDF_SEGMENT_MOVETO = 2
FPDF_FILLMODE_NONE = 0
FPDF_FILLMODE_ALTERNATE = 1
FPDF_FILLMODE_WINDING = 2
FPDF_FONT_TYPE1 = 1
FPDF_FONT_TRUETYPE = 2
FPDF_LINECAP_BUTT = 0
FPDF_LINECAP_ROUND = 1
FPDF_LINECAP_PROJECTING_SQUARE = 2
FPDF_LINEJOIN_MITER = 0
FPDF_LINEJOIN_ROUND = 1
FPDF_LINEJOIN_BEVEL = 2
FPDF_PRINTMODE_EMF = 0
FPDF_PRINTMODE_TEXTONLY = 1
FPDF_PRINTMODE_POSTSCRIPT2 = 2
FPDF_PRINTMODE_POSTSCRIPT3 = 3
FPDF_PRINTMODE_POSTSCRIPT2_PASSTHROUGH = 4
FPDF_PRINTMODE_POSTSCRIPT3_PASSTHROUGH = 5
FPDF_PRINTMODE_EMF_IMAGE_MASKS = 6
FPDF_PRINTMODE_POSTSCRIPT3_TYPE42 = 7
FPDF_PRINTMODE_POSTSCRIPT3_TYPE42_PASSTHROUGH = 8
FPDF_UNSP_DOC_XFAFORM = 1
FPDF_UNSP_DOC_PORTABLECOLLECTION = 2
FPDF_UNSP_DOC_ATTACHMENT = 3
FPDF_UNSP_DOC_SECURITY = 4
FPDF_UNSP_DOC_SHAREDREVIEW = 5
FPDF_UNSP_DOC_SHAREDFORM_ACROBAT = 6
FPDF_UNSP_DOC_SHAREDFORM_FILESYSTEM = 7
FPDF_UNSP_DOC_SHAREDFORM_EMAIL = 8
FPDF_UNSP_ANNOT_3DANNOT = 11
FPDF_UNSP_ANNOT_MOVIE = 12
FPDF_UNSP_ANNOT_SOUND = 13
FPDF_UNSP_ANNOT_SCREEN_MEDIA = 14
FPDF_UNSP_ANNOT_SCREEN_RICHMEDIA = 15
FPDF_UNSP_ANNOT_ATTACHMENT = 16
FPDF_UNSP_ANNOT_SIG = 17
PAGEMODE_UNKNOWN = (-1)
PAGEMODE_USENONE = 0
PAGEMODE_USEOUTLINES = 1
PAGEMODE_USETHUMBS = 2
PAGEMODE_FULLSCREEN = 3
PAGEMODE_USEOC = 4
PAGEMODE_USEATTACHMENTS = 5
FLATTEN_FAIL = 0
FLATTEN_SUCCESS = 1
FLATTEN_NOTHINGTODO = 2
FLAT_NORMALDISPLAY = 0
FLAT_PRINT = 1
FPDF_RENDER_READY = 0
FPDF_RENDER_TOBECONTINUED = 1
FPDF_RENDER_DONE = 2
FPDF_RENDER_FAILED = 3
FPDF_INCREMENTAL = 1
FPDF_NO_INCREMENTAL = 2
FPDF_REMOVE_SECURITY = 3
FXFONT_ANSI_CHARSET = 0
FXFONT_DEFAULT_CHARSET = 1
FXFONT_SYMBOL_CHARSET = 2
FXFONT_SHIFTJIS_CHARSET = 128
FXFONT_HANGEUL_CHARSET = 129
FXFONT_GB2312_CHARSET = 134
FXFONT_CHINESEBIG5_CHARSET = 136
FXFONT_GREEK_CHARSET = 161
FXFONT_VIETNAMESE_CHARSET = 163
FXFONT_HEBREW_CHARSET = 177
FXFONT_ARABIC_CHARSET = 178
FXFONT_CYRILLIC_CHARSET = 204
FXFONT_THAI_CHARSET = 222
FXFONT_EASTERNEUROPEAN_CHARSET = 238
FXFONT_FF_FIXEDPITCH = (1 << 0)
FXFONT_FF_ROMAN = (1 << 4)
FXFONT_FF_SCRIPT = (4 << 4)
FXFONT_FW_NORMAL = 400
FXFONT_FW_BOLD = 700
FPDF_MATCHCASE = 0x00000001
FPDF_MATCHWHOLEWORD = 0x00000002
FPDF_CONSECUTIVE = 0x00000004
fpdf_action_t__ = struct_fpdf_action_t__
fpdf_annotation_t__ = struct_fpdf_annotation_t__
fpdf_attachment_t__ = struct_fpdf_attachment_t__
fpdf_avail_t__ = struct_fpdf_avail_t__
fpdf_bitmap_t__ = struct_fpdf_bitmap_t__
fpdf_bookmark_t__ = struct_fpdf_bookmark_t__
fpdf_clippath_t__ = struct_fpdf_clippath_t__
fpdf_dest_t__ = struct_fpdf_dest_t__
fpdf_document_t__ = struct_fpdf_document_t__
fpdf_font_t__ = struct_fpdf_font_t__
fpdf_form_handle_t__ = struct_fpdf_form_handle_t__
fpdf_glyphpath_t__ = struct_fpdf_glyphpath_t__
fpdf_javascript_action_t = struct_fpdf_javascript_action_t
fpdf_link_t__ = struct_fpdf_link_t__
fpdf_page_t__ = struct_fpdf_page_t__
fpdf_pagelink_t__ = struct_fpdf_pagelink_t__
fpdf_pageobject_t__ = struct_fpdf_pageobject_t__
fpdf_pageobjectmark_t__ = struct_fpdf_pageobjectmark_t__
fpdf_pagerange_t__ = struct_fpdf_pagerange_t__
fpdf_pathsegment_t = struct_fpdf_pathsegment_t
fpdf_schhandle_t__ = struct_fpdf_schhandle_t__
fpdf_signature_t__ = struct_fpdf_signature_t__
fpdf_structelement_t__ = struct_fpdf_structelement_t__
fpdf_structelement_attr_t__ = struct_fpdf_structelement_attr_t__
fpdf_structtree_t__ = struct_fpdf_structtree_t__
fpdf_textpage_t__ = struct_fpdf_textpage_t__
fpdf_widget_t__ = struct_fpdf_widget_t__
fpdf_xobject_t__ = struct_fpdf_xobject_t__
FPDF_BSTR_ = struct_FPDF_BSTR_
_FS_MATRIX_ = struct__FS_MATRIX_
_FS_RECTF_ = struct__FS_RECTF_
FS_SIZEF_ = struct_FS_SIZEF_
FS_POINTF_ = struct_FS_POINTF_
_FS_QUADPOINTSF = struct__FS_QUADPOINTSF
FPDF_LIBRARY_CONFIG_ = struct_FPDF_LIBRARY_CONFIG_
FPDF_FILEHANDLER_ = struct_FPDF_FILEHANDLER_
FPDF_COLORSCHEME_ = struct_FPDF_COLORSCHEME_
_IPDF_JsPlatform = struct__IPDF_JsPlatform
_FPDF_SYSTEMTIME = struct__FPDF_SYSTEMTIME
_FPDF_FORMFILLINFO = struct__FPDF_FORMFILLINFO
_FX_FILEAVAIL = struct__FX_FILEAVAIL
_FX_DOWNLOADHINTS = struct__FX_DOWNLOADHINTS
FPDF_IMAGEOBJ_METADATA = struct_FPDF_IMAGEOBJ_METADATA
_UNSUPPORT_INFO = struct__UNSUPPORT_INFO
_IFSDK_PAUSE = struct__IFSDK_PAUSE
FPDF_FILEWRITE_ = struct_FPDF_FILEWRITE_
_FPDF_SYSFONTINFO = struct__FPDF_SYSFONTINFO
FPDF_CharsetFontMap_ = struct_FPDF_CharsetFontMap_
# No inserted files

