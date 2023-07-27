r"""Wrapper for fpdf_annot.h

Generated with:
/opt/hostedtoolcache/Python/3.10.12/x64/bin/ctypesgen --library pdfium --runtime-libdir . ./fpdf_annot.h ./fpdf_attachment.h ./fpdf_catalog.h ./fpdf_dataavail.h ./fpdf_doc.h ./fpdf_edit.h ./fpdf_ext.h ./fpdf_flatten.h ./fpdf_formfill.h ./fpdf_fwlevent.h ./fpdf_javascript.h ./fpdf_ppo.h ./fpdf_progressive.h ./fpdf_save.h ./fpdf_searchex.h ./fpdf_signature.h ./fpdf_structtree.h ./fpdf_sysfontinfo.h ./fpdf_text.h ./fpdf_thumbnail.h ./fpdf_transformpage.h ./fpdfview.h -o ~/work/pypdfium2/pypdfium2/data/linux_x64/raw.py --no-srcinfo

Do not modify this file.
"""

# Begin preamble for Python

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


# As of ctypes 1.0, ctypes does not support custom error-checking
# functions on callbacks, nor does it support custom datatypes on
# callbacks, so we must ensure that all callbacks return
# primitive datatypes.
#
# Non-primitive return values wrapped with UNCHECKED won't be
# typechecked, and will be converted to ctypes.c_void_p.
def UNCHECKED(type):
    if hasattr(type, "_type_") and isinstance(type._type_, str) and type._type_ != "P":
        return type
    else:
        return ctypes.c_void_p


# ctypes doesn't have direct support for variadic functions, so we have to write
# our own wrapper class
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

_libs = {}
_libdirs = []

# Begin loader

"""
Load libraries - appropriately for all our supported platforms
"""
# ----------------------------------------------------------------------------
# Copyright (c) 2008 David James
# Copyright (c) 2006-2008 Alex Holkner
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

import ctypes
import ctypes.util
import glob
import os.path
import platform
import re
import sys


def _environ_path(name):
    """Split an environment variable into a path-like list elements"""
    if name in os.environ:
        return os.environ[name].split(":")
    return []


class LibraryLoader:
    """
    A base class For loading of libraries ;-)
    Subclasses load libraries for specific platforms.
    """

    # library names formatted specifically for platforms
    name_formats = ["%s"]

    class Lookup:
        """Looking up calling conventions for a platform"""

        mode = ctypes.DEFAULT_MODE

        def __init__(self, path):
            super(LibraryLoader.Lookup, self).__init__()
            self.access = dict(cdecl=ctypes.CDLL(path, self.mode))

        def get(self, name, calling_convention="cdecl"):
            """Return the given name according to the selected calling convention"""
            if calling_convention not in self.access:
                raise LookupError(
                    "Unknown calling convention '{}' for function '{}'".format(
                        calling_convention, name
                    )
                )
            return getattr(self.access[calling_convention], name)

        def has(self, name, calling_convention="cdecl"):
            """Return True if this given calling convention finds the given 'name'"""
            if calling_convention not in self.access:
                return False
            return hasattr(self.access[calling_convention], name)

        def __getattr__(self, name):
            return getattr(self.access["cdecl"], name)

    def __init__(self):
        self.other_dirs = []

    def __call__(self, libname):
        """Given the name of a library, load it."""
        paths = self.getpaths(libname)

        for path in paths:
            # noinspection PyBroadException
            try:
                return self.Lookup(path)
            except Exception:  # pylint: disable=broad-except
                pass

        raise ImportError("Could not load %s." % libname)

    def getpaths(self, libname):
        """Return a list of paths where the library might be found."""
        if os.path.isabs(libname):
            yield libname
        else:
            # search through a prioritized series of locations for the library

            # we first search any specific directories identified by user
            for dir_i in self.other_dirs:
                for fmt in self.name_formats:
                    # dir_i should be absolute already
                    yield os.path.join(dir_i, fmt % libname)

            # check if this code is even stored in a physical file
            try:
                this_file = __file__
            except NameError:
                this_file = None

            # then we search the directory where the generated python interface is stored
            if this_file is not None:
                for fmt in self.name_formats:
                    yield os.path.abspath(os.path.join(os.path.dirname(__file__), fmt % libname))

            # now, use the ctypes tools to try to find the library
            for fmt in self.name_formats:
                path = ctypes.util.find_library(fmt % libname)
                if path:
                    yield path

            # then we search all paths identified as platform-specific lib paths
            for path in self.getplatformpaths(libname):
                yield path

            # Finally, we'll try the users current working directory
            for fmt in self.name_formats:
                yield os.path.abspath(os.path.join(os.path.curdir, fmt % libname))

    def getplatformpaths(self, _libname):  # pylint: disable=no-self-use
        """Return all the library paths available in this platform"""
        return []


# Darwin (Mac OS X)


class DarwinLibraryLoader(LibraryLoader):
    """Library loader for MacOS"""

    name_formats = [
        "lib%s.dylib",
        "lib%s.so",
        "lib%s.bundle",
        "%s.dylib",
        "%s.so",
        "%s.bundle",
        "%s",
    ]

    class Lookup(LibraryLoader.Lookup):
        """
        Looking up library files for this platform (Darwin aka MacOS)
        """

        # Darwin requires dlopen to be called with mode RTLD_GLOBAL instead
        # of the default RTLD_LOCAL.  Without this, you end up with
        # libraries not being loadable, resulting in "Symbol not found"
        # errors
        mode = ctypes.RTLD_GLOBAL

    def getplatformpaths(self, libname):
        if os.path.pathsep in libname:
            names = [libname]
        else:
            names = [fmt % libname for fmt in self.name_formats]

        for directory in self.getdirs(libname):
            for name in names:
                yield os.path.join(directory, name)

    @staticmethod
    def getdirs(libname):
        """Implements the dylib search as specified in Apple documentation:

        http://developer.apple.com/documentation/DeveloperTools/Conceptual/
            DynamicLibraries/Articles/DynamicLibraryUsageGuidelines.html

        Before commencing the standard search, the method first checks
        the bundle's ``Frameworks`` directory if the application is running
        within a bundle (OS X .app).
        """

        dyld_fallback_library_path = _environ_path("DYLD_FALLBACK_LIBRARY_PATH")
        if not dyld_fallback_library_path:
            dyld_fallback_library_path = [
                os.path.expanduser("~/lib"),
                "/usr/local/lib",
                "/usr/lib",
            ]

        dirs = []

        if "/" in libname:
            dirs.extend(_environ_path("DYLD_LIBRARY_PATH"))
        else:
            dirs.extend(_environ_path("LD_LIBRARY_PATH"))
            dirs.extend(_environ_path("DYLD_LIBRARY_PATH"))
            dirs.extend(_environ_path("LD_RUN_PATH"))

        if hasattr(sys, "frozen") and getattr(sys, "frozen") == "macosx_app":
            dirs.append(os.path.join(os.environ["RESOURCEPATH"], "..", "Frameworks"))

        dirs.extend(dyld_fallback_library_path)

        return dirs


# Posix


class PosixLibraryLoader(LibraryLoader):
    """Library loader for POSIX-like systems (including Linux)"""

    _ld_so_cache = None

    _include = re.compile(r"^\s*include\s+(?P<pattern>.*)")

    name_formats = ["lib%s.so", "%s.so", "%s"]

    class _Directories(dict):
        """Deal with directories"""

        def __init__(self):
            dict.__init__(self)
            self.order = 0

        def add(self, directory):
            """Add a directory to our current set of directories"""
            if len(directory) > 1:
                directory = directory.rstrip(os.path.sep)
            # only adds and updates order if exists and not already in set
            if not os.path.exists(directory):
                return
            order = self.setdefault(directory, self.order)
            if order == self.order:
                self.order += 1

        def extend(self, directories):
            """Add a list of directories to our set"""
            for a_dir in directories:
                self.add(a_dir)

        def ordered(self):
            """Sort the list of directories"""
            return (i[0] for i in sorted(self.items(), key=lambda d: d[1]))

    def _get_ld_so_conf_dirs(self, conf, dirs):
        """
        Recursive function to help parse all ld.so.conf files, including proper
        handling of the `include` directive.
        """

        try:
            with open(conf) as fileobj:
                for dirname in fileobj:
                    dirname = dirname.strip()
                    if not dirname:
                        continue

                    match = self._include.match(dirname)
                    if not match:
                        dirs.add(dirname)
                    else:
                        for dir2 in glob.glob(match.group("pattern")):
                            self._get_ld_so_conf_dirs(dir2, dirs)
        except IOError:
            pass

    def _create_ld_so_cache(self):
        # Recreate search path followed by ld.so.  This is going to be
        # slow to build, and incorrect (ld.so uses ld.so.cache, which may
        # not be up-to-date).  Used only as fallback for distros without
        # /sbin/ldconfig.
        #
        # We assume the DT_RPATH and DT_RUNPATH binary sections are omitted.

        directories = self._Directories()
        for name in (
            "LD_LIBRARY_PATH",
            "SHLIB_PATH",  # HP-UX
            "LIBPATH",  # OS/2, AIX
            "LIBRARY_PATH",  # BE/OS
        ):
            if name in os.environ:
                directories.extend(os.environ[name].split(os.pathsep))

        self._get_ld_so_conf_dirs("/etc/ld.so.conf", directories)

        bitage = platform.architecture()[0]

        unix_lib_dirs_list = []
        if bitage.startswith("64"):
            # prefer 64 bit if that is our arch
            unix_lib_dirs_list += ["/lib64", "/usr/lib64"]

        # must include standard libs, since those paths are also used by 64 bit
        # installs
        unix_lib_dirs_list += ["/lib", "/usr/lib"]
        if sys.platform.startswith("linux"):
            # Try and support multiarch work in Ubuntu
            # https://wiki.ubuntu.com/MultiarchSpec
            if bitage.startswith("32"):
                # Assume Intel/AMD x86 compat
                unix_lib_dirs_list += ["/lib/i386-linux-gnu", "/usr/lib/i386-linux-gnu"]
            elif bitage.startswith("64"):
                # Assume Intel/AMD x86 compatible
                unix_lib_dirs_list += [
                    "/lib/x86_64-linux-gnu",
                    "/usr/lib/x86_64-linux-gnu",
                ]
            else:
                # guess...
                unix_lib_dirs_list += glob.glob("/lib/*linux-gnu")
        directories.extend(unix_lib_dirs_list)

        cache = {}
        lib_re = re.compile(r"lib(.*)\.s[ol]")
        # ext_re = re.compile(r"\.s[ol]$")
        for our_dir in directories.ordered():
            try:
                for path in glob.glob("%s/*.s[ol]*" % our_dir):
                    file = os.path.basename(path)

                    # Index by filename
                    cache_i = cache.setdefault(file, set())
                    cache_i.add(path)

                    # Index by library name
                    match = lib_re.match(file)
                    if match:
                        library = match.group(1)
                        cache_i = cache.setdefault(library, set())
                        cache_i.add(path)
            except OSError:
                pass

        self._ld_so_cache = cache

    def getplatformpaths(self, libname):
        if self._ld_so_cache is None:
            self._create_ld_so_cache()

        result = self._ld_so_cache.get(libname, set())
        for i in result:
            # we iterate through all found paths for library, since we may have
            # actually found multiple architectures or other library types that
            # may not load
            yield i


# Windows


class WindowsLibraryLoader(LibraryLoader):
    """Library loader for Microsoft Windows"""

    name_formats = ["%s.dll", "lib%s.dll", "%slib.dll", "%s"]

    class Lookup(LibraryLoader.Lookup):
        """Lookup class for Windows libraries..."""

        def __init__(self, path):
            super(WindowsLibraryLoader.Lookup, self).__init__(path)
            self.access["stdcall"] = ctypes.windll.LoadLibrary(path)


# Platform switching

# If your value of sys.platform does not appear in this dict, please contact
# the Ctypesgen maintainers.

loaderclass = {
    "darwin": DarwinLibraryLoader,
    "cygwin": WindowsLibraryLoader,
    "win32": WindowsLibraryLoader,
    "msys": WindowsLibraryLoader,
}

load_library = loaderclass.get(sys.platform, PosixLibraryLoader)()


def add_library_search_dirs(other_dirs):
    """
    Add libraries to search paths.
    If library paths are relative, convert them to absolute with respect to this
    file's directory
    """
    for path in other_dirs:
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        load_library.other_dirs.append(path)


del loaderclass

# End loader

add_library_search_dirs(['.'])

# Begin libraries
_libs["pdfium"] = load_library("pdfium")

# 1 libraries
# End libraries

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

class struct_fpdf_action_t__(Structure):
    pass
FPDF_ACTION = POINTER(struct_fpdf_action_t__)

class struct_fpdf_annotation_t__(Structure):
    pass
FPDF_ANNOTATION = POINTER(struct_fpdf_annotation_t__)

class struct_fpdf_attachment_t__(Structure):
    pass
FPDF_ATTACHMENT = POINTER(struct_fpdf_attachment_t__)

class struct_fpdf_avail_t__(Structure):
    pass
FPDF_AVAIL = POINTER(struct_fpdf_avail_t__)

class struct_fpdf_bitmap_t__(Structure):
    pass
FPDF_BITMAP = POINTER(struct_fpdf_bitmap_t__)

class struct_fpdf_bookmark_t__(Structure):
    pass
FPDF_BOOKMARK = POINTER(struct_fpdf_bookmark_t__)

class struct_fpdf_clippath_t__(Structure):
    pass
FPDF_CLIPPATH = POINTER(struct_fpdf_clippath_t__)

class struct_fpdf_dest_t__(Structure):
    pass
FPDF_DEST = POINTER(struct_fpdf_dest_t__)

class struct_fpdf_document_t__(Structure):
    pass
FPDF_DOCUMENT = POINTER(struct_fpdf_document_t__)

class struct_fpdf_font_t__(Structure):
    pass
FPDF_FONT = POINTER(struct_fpdf_font_t__)

class struct_fpdf_form_handle_t__(Structure):
    pass
FPDF_FORMHANDLE = POINTER(struct_fpdf_form_handle_t__)

class struct_fpdf_glyphpath_t__(Structure):
    pass
FPDF_GLYPHPATH = POINTER(struct_fpdf_glyphpath_t__)

class struct_fpdf_javascript_action_t(Structure):
    pass
FPDF_JAVASCRIPT_ACTION = POINTER(struct_fpdf_javascript_action_t)

class struct_fpdf_link_t__(Structure):
    pass
FPDF_LINK = POINTER(struct_fpdf_link_t__)

class struct_fpdf_page_t__(Structure):
    pass
FPDF_PAGE = POINTER(struct_fpdf_page_t__)

class struct_fpdf_pagelink_t__(Structure):
    pass
FPDF_PAGELINK = POINTER(struct_fpdf_pagelink_t__)

class struct_fpdf_pageobject_t__(Structure):
    pass
FPDF_PAGEOBJECT = POINTER(struct_fpdf_pageobject_t__)

class struct_fpdf_pageobjectmark_t__(Structure):
    pass
FPDF_PAGEOBJECTMARK = POINTER(struct_fpdf_pageobjectmark_t__)

class struct_fpdf_pagerange_t__(Structure):
    pass
FPDF_PAGERANGE = POINTER(struct_fpdf_pagerange_t__)

class struct_fpdf_pathsegment_t(Structure):
    pass
FPDF_PATHSEGMENT = POINTER(struct_fpdf_pathsegment_t)

class struct_fpdf_schhandle_t__(Structure):
    pass
FPDF_SCHHANDLE = POINTER(struct_fpdf_schhandle_t__)

class struct_fpdf_signature_t__(Structure):
    pass
FPDF_SIGNATURE = POINTER(struct_fpdf_signature_t__)
FPDF_SKIA_CANVAS = POINTER(None)

class struct_fpdf_structelement_t__(Structure):
    pass
FPDF_STRUCTELEMENT = POINTER(struct_fpdf_structelement_t__)

class struct_fpdf_structelement_attr_t__(Structure):
    pass
FPDF_STRUCTELEMENT_ATTR = POINTER(struct_fpdf_structelement_attr_t__)

class struct_fpdf_structtree_t__(Structure):
    pass
FPDF_STRUCTTREE = POINTER(struct_fpdf_structtree_t__)

class struct_fpdf_textpage_t__(Structure):
    pass
FPDF_TEXTPAGE = POINTER(struct_fpdf_textpage_t__)

class struct_fpdf_widget_t__(Structure):
    pass
FPDF_WIDGET = POINTER(struct_fpdf_widget_t__)

class struct_fpdf_xobject_t__(Structure):
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

class struct_FPDF_BSTR_(Structure):
    pass
struct_FPDF_BSTR_.__slots__ = [
    'str',
    'len',
]
struct_FPDF_BSTR_._fields_ = [
    ('str', POINTER(c_char)),
    ('len', c_int),
]
FPDF_BSTR = struct_FPDF_BSTR_
FPDF_STRING = POINTER(c_char)

class struct__FS_MATRIX_(Structure):
    pass
struct__FS_MATRIX_.__slots__ = [
    'a',
    'b',
    'c',
    'd',
    'e',
    'f',
]
struct__FS_MATRIX_._fields_ = [
    ('a', c_float),
    ('b', c_float),
    ('c', c_float),
    ('d', c_float),
    ('e', c_float),
    ('f', c_float),
]
FS_MATRIX = struct__FS_MATRIX_

class struct__FS_RECTF_(Structure):
    pass
struct__FS_RECTF_.__slots__ = [
    'left',
    'top',
    'right',
    'bottom',
]
struct__FS_RECTF_._fields_ = [
    ('left', c_float),
    ('top', c_float),
    ('right', c_float),
    ('bottom', c_float),
]
FS_LPRECTF = POINTER(struct__FS_RECTF_)
FS_RECTF = struct__FS_RECTF_
FS_LPCRECTF = POINTER(FS_RECTF)

class struct_FS_SIZEF_(Structure):
    pass
struct_FS_SIZEF_.__slots__ = [
    'width',
    'height',
]
struct_FS_SIZEF_._fields_ = [
    ('width', c_float),
    ('height', c_float),
]
FS_LPSIZEF = POINTER(struct_FS_SIZEF_)
FS_SIZEF = struct_FS_SIZEF_
FS_LPCSIZEF = POINTER(FS_SIZEF)

class struct_FS_POINTF_(Structure):
    pass
struct_FS_POINTF_.__slots__ = [
    'x',
    'y',
]
struct_FS_POINTF_._fields_ = [
    ('x', c_float),
    ('y', c_float),
]
FS_LPPOINTF = POINTER(struct_FS_POINTF_)
FS_POINTF = struct_FS_POINTF_
FS_LPCPOINTF = POINTER(FS_POINTF)

class struct__FS_QUADPOINTSF(Structure):
    pass
struct__FS_QUADPOINTSF.__slots__ = [
    'x1',
    'y1',
    'x2',
    'y2',
    'x3',
    'y3',
    'x4',
    'y4',
]
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

class struct_FPDF_LIBRARY_CONFIG_(Structure):
    pass
struct_FPDF_LIBRARY_CONFIG_.__slots__ = [
    'version',
    'm_pUserFontPaths',
    'm_pIsolate',
    'm_v8EmbedderSlot',
    'm_pPlatform',
    'm_RendererType',
]
struct_FPDF_LIBRARY_CONFIG_._fields_ = [
    ('version', c_int),
    ('m_pUserFontPaths', POINTER(POINTER(c_char))),
    ('m_pIsolate', POINTER(None)),
    ('m_v8EmbedderSlot', c_uint),
    ('m_pPlatform', POINTER(None)),
    ('m_RendererType', FPDF_RENDERER_TYPE),
]
FPDF_LIBRARY_CONFIG = struct_FPDF_LIBRARY_CONFIG_

if _libs["pdfium"].has("FPDF_InitLibraryWithConfig", "cdecl"):
    FPDF_InitLibraryWithConfig = _libs["pdfium"].get("FPDF_InitLibraryWithConfig", "cdecl")
    FPDF_InitLibraryWithConfig.argtypes = [POINTER(FPDF_LIBRARY_CONFIG)]
    FPDF_InitLibraryWithConfig.restype = None

if _libs["pdfium"].has("FPDF_InitLibrary", "cdecl"):
    FPDF_InitLibrary = _libs["pdfium"].get("FPDF_InitLibrary", "cdecl")
    FPDF_InitLibrary.argtypes = []
    FPDF_InitLibrary.restype = None

if _libs["pdfium"].has("FPDF_DestroyLibrary", "cdecl"):
    FPDF_DestroyLibrary = _libs["pdfium"].get("FPDF_DestroyLibrary", "cdecl")
    FPDF_DestroyLibrary.argtypes = []
    FPDF_DestroyLibrary.restype = None

if _libs["pdfium"].has("FPDF_SetSandBoxPolicy", "cdecl"):
    FPDF_SetSandBoxPolicy = _libs["pdfium"].get("FPDF_SetSandBoxPolicy", "cdecl")
    FPDF_SetSandBoxPolicy.argtypes = [FPDF_DWORD, FPDF_BOOL]
    FPDF_SetSandBoxPolicy.restype = None

if _libs["pdfium"].has("FPDF_LoadDocument", "cdecl"):
    FPDF_LoadDocument = _libs["pdfium"].get("FPDF_LoadDocument", "cdecl")
    FPDF_LoadDocument.argtypes = [FPDF_STRING, FPDF_BYTESTRING]
    FPDF_LoadDocument.restype = FPDF_DOCUMENT

if _libs["pdfium"].has("FPDF_LoadMemDocument", "cdecl"):
    FPDF_LoadMemDocument = _libs["pdfium"].get("FPDF_LoadMemDocument", "cdecl")
    FPDF_LoadMemDocument.argtypes = [POINTER(None), c_int, FPDF_BYTESTRING]
    FPDF_LoadMemDocument.restype = FPDF_DOCUMENT

if _libs["pdfium"].has("FPDF_LoadMemDocument64", "cdecl"):
    FPDF_LoadMemDocument64 = _libs["pdfium"].get("FPDF_LoadMemDocument64", "cdecl")
    FPDF_LoadMemDocument64.argtypes = [POINTER(None), c_size_t, FPDF_BYTESTRING]
    FPDF_LoadMemDocument64.restype = FPDF_DOCUMENT

class struct_anon_4(Structure):
    pass
struct_anon_4.__slots__ = [
    'm_FileLen',
    'm_GetBlock',
    'm_Param',
]
struct_anon_4._fields_ = [
    ('m_FileLen', c_ulong),
    ('m_GetBlock', CFUNCTYPE(UNCHECKED(c_int), POINTER(None), c_ulong, POINTER(c_ubyte), c_ulong)),
    ('m_Param', POINTER(None)),
]
FPDF_FILEACCESS = struct_anon_4

class struct_FPDF_FILEHANDLER_(Structure):
    pass
struct_FPDF_FILEHANDLER_.__slots__ = [
    'clientData',
    'Release',
    'GetSize',
    'ReadBlock',
    'WriteBlock',
    'Flush',
    'Truncate',
]
struct_FPDF_FILEHANDLER_._fields_ = [
    ('clientData', POINTER(None)),
    ('Release', CFUNCTYPE(UNCHECKED(None), POINTER(None))),
    ('GetSize', CFUNCTYPE(UNCHECKED(FPDF_DWORD), POINTER(None))),
    ('ReadBlock', CFUNCTYPE(UNCHECKED(FPDF_RESULT), POINTER(None), FPDF_DWORD, POINTER(None), FPDF_DWORD)),
    ('WriteBlock', CFUNCTYPE(UNCHECKED(FPDF_RESULT), POINTER(None), FPDF_DWORD, POINTER(None), FPDF_DWORD)),
    ('Flush', CFUNCTYPE(UNCHECKED(FPDF_RESULT), POINTER(None))),
    ('Truncate', CFUNCTYPE(UNCHECKED(FPDF_RESULT), POINTER(None), FPDF_DWORD)),
]
FPDF_FILEHANDLER = struct_FPDF_FILEHANDLER_

if _libs["pdfium"].has("FPDF_LoadCustomDocument", "cdecl"):
    FPDF_LoadCustomDocument = _libs["pdfium"].get("FPDF_LoadCustomDocument", "cdecl")
    FPDF_LoadCustomDocument.argtypes = [POINTER(FPDF_FILEACCESS), FPDF_BYTESTRING]
    FPDF_LoadCustomDocument.restype = FPDF_DOCUMENT

if _libs["pdfium"].has("FPDF_GetFileVersion", "cdecl"):
    FPDF_GetFileVersion = _libs["pdfium"].get("FPDF_GetFileVersion", "cdecl")
    FPDF_GetFileVersion.argtypes = [FPDF_DOCUMENT, POINTER(c_int)]
    FPDF_GetFileVersion.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDF_GetLastError", "cdecl"):
    FPDF_GetLastError = _libs["pdfium"].get("FPDF_GetLastError", "cdecl")
    FPDF_GetLastError.argtypes = []
    FPDF_GetLastError.restype = c_ulong

if _libs["pdfium"].has("FPDF_DocumentHasValidCrossReferenceTable", "cdecl"):
    FPDF_DocumentHasValidCrossReferenceTable = _libs["pdfium"].get("FPDF_DocumentHasValidCrossReferenceTable", "cdecl")
    FPDF_DocumentHasValidCrossReferenceTable.argtypes = [FPDF_DOCUMENT]
    FPDF_DocumentHasValidCrossReferenceTable.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDF_GetTrailerEnds", "cdecl"):
    FPDF_GetTrailerEnds = _libs["pdfium"].get("FPDF_GetTrailerEnds", "cdecl")
    FPDF_GetTrailerEnds.argtypes = [FPDF_DOCUMENT, POINTER(c_uint), c_ulong]
    FPDF_GetTrailerEnds.restype = c_ulong

if _libs["pdfium"].has("FPDF_GetDocPermissions", "cdecl"):
    FPDF_GetDocPermissions = _libs["pdfium"].get("FPDF_GetDocPermissions", "cdecl")
    FPDF_GetDocPermissions.argtypes = [FPDF_DOCUMENT]
    FPDF_GetDocPermissions.restype = c_ulong

if _libs["pdfium"].has("FPDF_GetSecurityHandlerRevision", "cdecl"):
    FPDF_GetSecurityHandlerRevision = _libs["pdfium"].get("FPDF_GetSecurityHandlerRevision", "cdecl")
    FPDF_GetSecurityHandlerRevision.argtypes = [FPDF_DOCUMENT]
    FPDF_GetSecurityHandlerRevision.restype = c_int

if _libs["pdfium"].has("FPDF_GetPageCount", "cdecl"):
    FPDF_GetPageCount = _libs["pdfium"].get("FPDF_GetPageCount", "cdecl")
    FPDF_GetPageCount.argtypes = [FPDF_DOCUMENT]
    FPDF_GetPageCount.restype = c_int

if _libs["pdfium"].has("FPDF_LoadPage", "cdecl"):
    FPDF_LoadPage = _libs["pdfium"].get("FPDF_LoadPage", "cdecl")
    FPDF_LoadPage.argtypes = [FPDF_DOCUMENT, c_int]
    FPDF_LoadPage.restype = FPDF_PAGE

if _libs["pdfium"].has("FPDF_GetPageWidthF", "cdecl"):
    FPDF_GetPageWidthF = _libs["pdfium"].get("FPDF_GetPageWidthF", "cdecl")
    FPDF_GetPageWidthF.argtypes = [FPDF_PAGE]
    FPDF_GetPageWidthF.restype = c_float

if _libs["pdfium"].has("FPDF_GetPageWidth", "cdecl"):
    FPDF_GetPageWidth = _libs["pdfium"].get("FPDF_GetPageWidth", "cdecl")
    FPDF_GetPageWidth.argtypes = [FPDF_PAGE]
    FPDF_GetPageWidth.restype = c_double

if _libs["pdfium"].has("FPDF_GetPageHeightF", "cdecl"):
    FPDF_GetPageHeightF = _libs["pdfium"].get("FPDF_GetPageHeightF", "cdecl")
    FPDF_GetPageHeightF.argtypes = [FPDF_PAGE]
    FPDF_GetPageHeightF.restype = c_float

if _libs["pdfium"].has("FPDF_GetPageHeight", "cdecl"):
    FPDF_GetPageHeight = _libs["pdfium"].get("FPDF_GetPageHeight", "cdecl")
    FPDF_GetPageHeight.argtypes = [FPDF_PAGE]
    FPDF_GetPageHeight.restype = c_double

if _libs["pdfium"].has("FPDF_GetPageBoundingBox", "cdecl"):
    FPDF_GetPageBoundingBox = _libs["pdfium"].get("FPDF_GetPageBoundingBox", "cdecl")
    FPDF_GetPageBoundingBox.argtypes = [FPDF_PAGE, POINTER(FS_RECTF)]
    FPDF_GetPageBoundingBox.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDF_GetPageSizeByIndexF", "cdecl"):
    FPDF_GetPageSizeByIndexF = _libs["pdfium"].get("FPDF_GetPageSizeByIndexF", "cdecl")
    FPDF_GetPageSizeByIndexF.argtypes = [FPDF_DOCUMENT, c_int, POINTER(FS_SIZEF)]
    FPDF_GetPageSizeByIndexF.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDF_GetPageSizeByIndex", "cdecl"):
    FPDF_GetPageSizeByIndex = _libs["pdfium"].get("FPDF_GetPageSizeByIndex", "cdecl")
    FPDF_GetPageSizeByIndex.argtypes = [FPDF_DOCUMENT, c_int, POINTER(c_double), POINTER(c_double)]
    FPDF_GetPageSizeByIndex.restype = c_int

class struct_FPDF_COLORSCHEME_(Structure):
    pass
struct_FPDF_COLORSCHEME_.__slots__ = [
    'path_fill_color',
    'path_stroke_color',
    'text_fill_color',
    'text_stroke_color',
]
struct_FPDF_COLORSCHEME_._fields_ = [
    ('path_fill_color', FPDF_DWORD),
    ('path_stroke_color', FPDF_DWORD),
    ('text_fill_color', FPDF_DWORD),
    ('text_stroke_color', FPDF_DWORD),
]
FPDF_COLORSCHEME = struct_FPDF_COLORSCHEME_

if _libs["pdfium"].has("FPDF_RenderPageBitmap", "cdecl"):
    FPDF_RenderPageBitmap = _libs["pdfium"].get("FPDF_RenderPageBitmap", "cdecl")
    FPDF_RenderPageBitmap.argtypes = [FPDF_BITMAP, FPDF_PAGE, c_int, c_int, c_int, c_int, c_int, c_int]
    FPDF_RenderPageBitmap.restype = None

if _libs["pdfium"].has("FPDF_RenderPageBitmapWithMatrix", "cdecl"):
    FPDF_RenderPageBitmapWithMatrix = _libs["pdfium"].get("FPDF_RenderPageBitmapWithMatrix", "cdecl")
    FPDF_RenderPageBitmapWithMatrix.argtypes = [FPDF_BITMAP, FPDF_PAGE, POINTER(FS_MATRIX), POINTER(FS_RECTF), c_int]
    FPDF_RenderPageBitmapWithMatrix.restype = None

if _libs["pdfium"].has("FPDF_ClosePage", "cdecl"):
    FPDF_ClosePage = _libs["pdfium"].get("FPDF_ClosePage", "cdecl")
    FPDF_ClosePage.argtypes = [FPDF_PAGE]
    FPDF_ClosePage.restype = None

if _libs["pdfium"].has("FPDF_CloseDocument", "cdecl"):
    FPDF_CloseDocument = _libs["pdfium"].get("FPDF_CloseDocument", "cdecl")
    FPDF_CloseDocument.argtypes = [FPDF_DOCUMENT]
    FPDF_CloseDocument.restype = None

if _libs["pdfium"].has("FPDF_DeviceToPage", "cdecl"):
    FPDF_DeviceToPage = _libs["pdfium"].get("FPDF_DeviceToPage", "cdecl")
    FPDF_DeviceToPage.argtypes = [FPDF_PAGE, c_int, c_int, c_int, c_int, c_int, c_int, c_int, POINTER(c_double), POINTER(c_double)]
    FPDF_DeviceToPage.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDF_PageToDevice", "cdecl"):
    FPDF_PageToDevice = _libs["pdfium"].get("FPDF_PageToDevice", "cdecl")
    FPDF_PageToDevice.argtypes = [FPDF_PAGE, c_int, c_int, c_int, c_int, c_int, c_double, c_double, POINTER(c_int), POINTER(c_int)]
    FPDF_PageToDevice.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFBitmap_Create", "cdecl"):
    FPDFBitmap_Create = _libs["pdfium"].get("FPDFBitmap_Create", "cdecl")
    FPDFBitmap_Create.argtypes = [c_int, c_int, c_int]
    FPDFBitmap_Create.restype = FPDF_BITMAP

if _libs["pdfium"].has("FPDFBitmap_CreateEx", "cdecl"):
    FPDFBitmap_CreateEx = _libs["pdfium"].get("FPDFBitmap_CreateEx", "cdecl")
    FPDFBitmap_CreateEx.argtypes = [c_int, c_int, c_int, POINTER(None), c_int]
    FPDFBitmap_CreateEx.restype = FPDF_BITMAP

if _libs["pdfium"].has("FPDFBitmap_GetFormat", "cdecl"):
    FPDFBitmap_GetFormat = _libs["pdfium"].get("FPDFBitmap_GetFormat", "cdecl")
    FPDFBitmap_GetFormat.argtypes = [FPDF_BITMAP]
    FPDFBitmap_GetFormat.restype = c_int

if _libs["pdfium"].has("FPDFBitmap_FillRect", "cdecl"):
    FPDFBitmap_FillRect = _libs["pdfium"].get("FPDFBitmap_FillRect", "cdecl")
    FPDFBitmap_FillRect.argtypes = [FPDF_BITMAP, c_int, c_int, c_int, c_int, FPDF_DWORD]
    FPDFBitmap_FillRect.restype = None

if _libs["pdfium"].has("FPDFBitmap_GetBuffer", "cdecl"):
    FPDFBitmap_GetBuffer = _libs["pdfium"].get("FPDFBitmap_GetBuffer", "cdecl")
    FPDFBitmap_GetBuffer.argtypes = [FPDF_BITMAP]
    FPDFBitmap_GetBuffer.restype = POINTER(c_ubyte)
    FPDFBitmap_GetBuffer.errcheck = lambda v,*a : cast(v, c_void_p)

if _libs["pdfium"].has("FPDFBitmap_GetWidth", "cdecl"):
    FPDFBitmap_GetWidth = _libs["pdfium"].get("FPDFBitmap_GetWidth", "cdecl")
    FPDFBitmap_GetWidth.argtypes = [FPDF_BITMAP]
    FPDFBitmap_GetWidth.restype = c_int

if _libs["pdfium"].has("FPDFBitmap_GetHeight", "cdecl"):
    FPDFBitmap_GetHeight = _libs["pdfium"].get("FPDFBitmap_GetHeight", "cdecl")
    FPDFBitmap_GetHeight.argtypes = [FPDF_BITMAP]
    FPDFBitmap_GetHeight.restype = c_int

if _libs["pdfium"].has("FPDFBitmap_GetStride", "cdecl"):
    FPDFBitmap_GetStride = _libs["pdfium"].get("FPDFBitmap_GetStride", "cdecl")
    FPDFBitmap_GetStride.argtypes = [FPDF_BITMAP]
    FPDFBitmap_GetStride.restype = c_int

if _libs["pdfium"].has("FPDFBitmap_Destroy", "cdecl"):
    FPDFBitmap_Destroy = _libs["pdfium"].get("FPDFBitmap_Destroy", "cdecl")
    FPDFBitmap_Destroy.argtypes = [FPDF_BITMAP]
    FPDFBitmap_Destroy.restype = None

if _libs["pdfium"].has("FPDF_VIEWERREF_GetPrintScaling", "cdecl"):
    FPDF_VIEWERREF_GetPrintScaling = _libs["pdfium"].get("FPDF_VIEWERREF_GetPrintScaling", "cdecl")
    FPDF_VIEWERREF_GetPrintScaling.argtypes = [FPDF_DOCUMENT]
    FPDF_VIEWERREF_GetPrintScaling.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDF_VIEWERREF_GetNumCopies", "cdecl"):
    FPDF_VIEWERREF_GetNumCopies = _libs["pdfium"].get("FPDF_VIEWERREF_GetNumCopies", "cdecl")
    FPDF_VIEWERREF_GetNumCopies.argtypes = [FPDF_DOCUMENT]
    FPDF_VIEWERREF_GetNumCopies.restype = c_int

if _libs["pdfium"].has("FPDF_VIEWERREF_GetPrintPageRange", "cdecl"):
    FPDF_VIEWERREF_GetPrintPageRange = _libs["pdfium"].get("FPDF_VIEWERREF_GetPrintPageRange", "cdecl")
    FPDF_VIEWERREF_GetPrintPageRange.argtypes = [FPDF_DOCUMENT]
    FPDF_VIEWERREF_GetPrintPageRange.restype = FPDF_PAGERANGE

if _libs["pdfium"].has("FPDF_VIEWERREF_GetPrintPageRangeCount", "cdecl"):
    FPDF_VIEWERREF_GetPrintPageRangeCount = _libs["pdfium"].get("FPDF_VIEWERREF_GetPrintPageRangeCount", "cdecl")
    FPDF_VIEWERREF_GetPrintPageRangeCount.argtypes = [FPDF_PAGERANGE]
    FPDF_VIEWERREF_GetPrintPageRangeCount.restype = c_size_t

if _libs["pdfium"].has("FPDF_VIEWERREF_GetPrintPageRangeElement", "cdecl"):
    FPDF_VIEWERREF_GetPrintPageRangeElement = _libs["pdfium"].get("FPDF_VIEWERREF_GetPrintPageRangeElement", "cdecl")
    FPDF_VIEWERREF_GetPrintPageRangeElement.argtypes = [FPDF_PAGERANGE, c_size_t]
    FPDF_VIEWERREF_GetPrintPageRangeElement.restype = c_int

if _libs["pdfium"].has("FPDF_VIEWERREF_GetDuplex", "cdecl"):
    FPDF_VIEWERREF_GetDuplex = _libs["pdfium"].get("FPDF_VIEWERREF_GetDuplex", "cdecl")
    FPDF_VIEWERREF_GetDuplex.argtypes = [FPDF_DOCUMENT]
    FPDF_VIEWERREF_GetDuplex.restype = FPDF_DUPLEXTYPE

if _libs["pdfium"].has("FPDF_VIEWERREF_GetName", "cdecl"):
    FPDF_VIEWERREF_GetName = _libs["pdfium"].get("FPDF_VIEWERREF_GetName", "cdecl")
    FPDF_VIEWERREF_GetName.argtypes = [FPDF_DOCUMENT, FPDF_BYTESTRING, POINTER(c_char), c_ulong]
    FPDF_VIEWERREF_GetName.restype = c_ulong

if _libs["pdfium"].has("FPDF_CountNamedDests", "cdecl"):
    FPDF_CountNamedDests = _libs["pdfium"].get("FPDF_CountNamedDests", "cdecl")
    FPDF_CountNamedDests.argtypes = [FPDF_DOCUMENT]
    FPDF_CountNamedDests.restype = FPDF_DWORD

if _libs["pdfium"].has("FPDF_GetNamedDestByName", "cdecl"):
    FPDF_GetNamedDestByName = _libs["pdfium"].get("FPDF_GetNamedDestByName", "cdecl")
    FPDF_GetNamedDestByName.argtypes = [FPDF_DOCUMENT, FPDF_BYTESTRING]
    FPDF_GetNamedDestByName.restype = FPDF_DEST

if _libs["pdfium"].has("FPDF_GetNamedDest", "cdecl"):
    FPDF_GetNamedDest = _libs["pdfium"].get("FPDF_GetNamedDest", "cdecl")
    FPDF_GetNamedDest.argtypes = [FPDF_DOCUMENT, c_int, POINTER(None), POINTER(c_long)]
    FPDF_GetNamedDest.restype = FPDF_DEST

if _libs["pdfium"].has("FPDF_GetXFAPacketCount", "cdecl"):
    FPDF_GetXFAPacketCount = _libs["pdfium"].get("FPDF_GetXFAPacketCount", "cdecl")
    FPDF_GetXFAPacketCount.argtypes = [FPDF_DOCUMENT]
    FPDF_GetXFAPacketCount.restype = c_int

if _libs["pdfium"].has("FPDF_GetXFAPacketName", "cdecl"):
    FPDF_GetXFAPacketName = _libs["pdfium"].get("FPDF_GetXFAPacketName", "cdecl")
    FPDF_GetXFAPacketName.argtypes = [FPDF_DOCUMENT, c_int, POINTER(None), c_ulong]
    FPDF_GetXFAPacketName.restype = c_ulong

if _libs["pdfium"].has("FPDF_GetXFAPacketContent", "cdecl"):
    FPDF_GetXFAPacketContent = _libs["pdfium"].get("FPDF_GetXFAPacketContent", "cdecl")
    FPDF_GetXFAPacketContent.argtypes = [FPDF_DOCUMENT, c_int, POINTER(None), c_ulong, POINTER(c_ulong)]
    FPDF_GetXFAPacketContent.restype = FPDF_BOOL

class struct__IPDF_JsPlatform(Structure):
    pass
struct__IPDF_JsPlatform.__slots__ = [
    'version',
    'app_alert',
    'app_beep',
    'app_response',
    'Doc_getFilePath',
    'Doc_mail',
    'Doc_print',
    'Doc_submitForm',
    'Doc_gotoPage',
    'Field_browse',
    'm_pFormfillinfo',
    'm_isolate',
    'm_v8EmbedderSlot',
]
struct__IPDF_JsPlatform._fields_ = [
    ('version', c_int),
    ('app_alert', CFUNCTYPE(UNCHECKED(c_int), POINTER(struct__IPDF_JsPlatform), FPDF_WIDESTRING, FPDF_WIDESTRING, c_int, c_int)),
    ('app_beep', CFUNCTYPE(UNCHECKED(None), POINTER(struct__IPDF_JsPlatform), c_int)),
    ('app_response', CFUNCTYPE(UNCHECKED(c_int), POINTER(struct__IPDF_JsPlatform), FPDF_WIDESTRING, FPDF_WIDESTRING, FPDF_WIDESTRING, FPDF_WIDESTRING, FPDF_BOOL, POINTER(None), c_int)),
    ('Doc_getFilePath', CFUNCTYPE(UNCHECKED(c_int), POINTER(struct__IPDF_JsPlatform), POINTER(None), c_int)),
    ('Doc_mail', CFUNCTYPE(UNCHECKED(None), POINTER(struct__IPDF_JsPlatform), POINTER(None), c_int, FPDF_BOOL, FPDF_WIDESTRING, FPDF_WIDESTRING, FPDF_WIDESTRING, FPDF_WIDESTRING, FPDF_WIDESTRING)),
    ('Doc_print', CFUNCTYPE(UNCHECKED(None), POINTER(struct__IPDF_JsPlatform), FPDF_BOOL, c_int, c_int, FPDF_BOOL, FPDF_BOOL, FPDF_BOOL, FPDF_BOOL, FPDF_BOOL)),
    ('Doc_submitForm', CFUNCTYPE(UNCHECKED(None), POINTER(struct__IPDF_JsPlatform), POINTER(None), c_int, FPDF_WIDESTRING)),
    ('Doc_gotoPage', CFUNCTYPE(UNCHECKED(None), POINTER(struct__IPDF_JsPlatform), c_int)),
    ('Field_browse', CFUNCTYPE(UNCHECKED(c_int), POINTER(struct__IPDF_JsPlatform), POINTER(None), c_int)),
    ('m_pFormfillinfo', POINTER(None)),
    ('m_isolate', POINTER(None)),
    ('m_v8EmbedderSlot', c_uint),
]
IPDF_JSPLATFORM = struct__IPDF_JsPlatform
TimerCallback = CFUNCTYPE(UNCHECKED(None), c_int)

class struct__FPDF_SYSTEMTIME(Structure):
    pass
struct__FPDF_SYSTEMTIME.__slots__ = [
    'wYear',
    'wMonth',
    'wDayOfWeek',
    'wDay',
    'wHour',
    'wMinute',
    'wSecond',
    'wMilliseconds',
]
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

class struct__FPDF_FORMFILLINFO(Structure):
    pass
struct__FPDF_FORMFILLINFO.__slots__ = [
    'version',
    'Release',
    'FFI_Invalidate',
    'FFI_OutputSelectedRect',
    'FFI_SetCursor',
    'FFI_SetTimer',
    'FFI_KillTimer',
    'FFI_GetLocalTime',
    'FFI_OnChange',
    'FFI_GetPage',
    'FFI_GetCurrentPage',
    'FFI_GetRotation',
    'FFI_ExecuteNamedAction',
    'FFI_SetTextFieldFocus',
    'FFI_DoURIAction',
    'FFI_DoGoToAction',
    'm_pJsPlatform',
    'xfa_disabled',
    'FFI_DisplayCaret',
    'FFI_GetCurrentPageIndex',
    'FFI_SetCurrentPage',
    'FFI_GotoURL',
    'FFI_GetPageViewRect',
    'FFI_PageEvent',
    'FFI_PopupMenu',
    'FFI_OpenFile',
    'FFI_EmailTo',
    'FFI_UploadTo',
    'FFI_GetPlatform',
    'FFI_GetLanguage',
    'FFI_DownloadFromURL',
    'FFI_PostRequestURL',
    'FFI_PutRequestURL',
    'FFI_OnFocusChange',
    'FFI_DoURIActionWithKeyboardModifier',
]
struct__FPDF_FORMFILLINFO._fields_ = [
    ('version', c_int),
    ('Release', CFUNCTYPE(UNCHECKED(None), POINTER(struct__FPDF_FORMFILLINFO))),
    ('FFI_Invalidate', CFUNCTYPE(UNCHECKED(None), POINTER(struct__FPDF_FORMFILLINFO), FPDF_PAGE, c_double, c_double, c_double, c_double)),
    ('FFI_OutputSelectedRect', CFUNCTYPE(UNCHECKED(None), POINTER(struct__FPDF_FORMFILLINFO), FPDF_PAGE, c_double, c_double, c_double, c_double)),
    ('FFI_SetCursor', CFUNCTYPE(UNCHECKED(None), POINTER(struct__FPDF_FORMFILLINFO), c_int)),
    ('FFI_SetTimer', CFUNCTYPE(UNCHECKED(c_int), POINTER(struct__FPDF_FORMFILLINFO), c_int, TimerCallback)),
    ('FFI_KillTimer', CFUNCTYPE(UNCHECKED(None), POINTER(struct__FPDF_FORMFILLINFO), c_int)),
    ('FFI_GetLocalTime', CFUNCTYPE(UNCHECKED(FPDF_SYSTEMTIME), POINTER(struct__FPDF_FORMFILLINFO))),
    ('FFI_OnChange', CFUNCTYPE(UNCHECKED(None), POINTER(struct__FPDF_FORMFILLINFO))),
    ('FFI_GetPage', CFUNCTYPE(UNCHECKED(FPDF_PAGE), POINTER(struct__FPDF_FORMFILLINFO), FPDF_DOCUMENT, c_int)),
    ('FFI_GetCurrentPage', CFUNCTYPE(UNCHECKED(FPDF_PAGE), POINTER(struct__FPDF_FORMFILLINFO), FPDF_DOCUMENT)),
    ('FFI_GetRotation', CFUNCTYPE(UNCHECKED(c_int), POINTER(struct__FPDF_FORMFILLINFO), FPDF_PAGE)),
    ('FFI_ExecuteNamedAction', CFUNCTYPE(UNCHECKED(None), POINTER(struct__FPDF_FORMFILLINFO), FPDF_BYTESTRING)),
    ('FFI_SetTextFieldFocus', CFUNCTYPE(UNCHECKED(None), POINTER(struct__FPDF_FORMFILLINFO), FPDF_WIDESTRING, FPDF_DWORD, FPDF_BOOL)),
    ('FFI_DoURIAction', CFUNCTYPE(UNCHECKED(None), POINTER(struct__FPDF_FORMFILLINFO), FPDF_BYTESTRING)),
    ('FFI_DoGoToAction', CFUNCTYPE(UNCHECKED(None), POINTER(struct__FPDF_FORMFILLINFO), c_int, c_int, POINTER(c_float), c_int)),
    ('m_pJsPlatform', POINTER(IPDF_JSPLATFORM)),
    ('xfa_disabled', FPDF_BOOL),
    ('FFI_DisplayCaret', CFUNCTYPE(UNCHECKED(None), POINTER(struct__FPDF_FORMFILLINFO), FPDF_PAGE, FPDF_BOOL, c_double, c_double, c_double, c_double)),
    ('FFI_GetCurrentPageIndex', CFUNCTYPE(UNCHECKED(c_int), POINTER(struct__FPDF_FORMFILLINFO), FPDF_DOCUMENT)),
    ('FFI_SetCurrentPage', CFUNCTYPE(UNCHECKED(None), POINTER(struct__FPDF_FORMFILLINFO), FPDF_DOCUMENT, c_int)),
    ('FFI_GotoURL', CFUNCTYPE(UNCHECKED(None), POINTER(struct__FPDF_FORMFILLINFO), FPDF_DOCUMENT, FPDF_WIDESTRING)),
    ('FFI_GetPageViewRect', CFUNCTYPE(UNCHECKED(None), POINTER(struct__FPDF_FORMFILLINFO), FPDF_PAGE, POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double))),
    ('FFI_PageEvent', CFUNCTYPE(UNCHECKED(None), POINTER(struct__FPDF_FORMFILLINFO), c_int, FPDF_DWORD)),
    ('FFI_PopupMenu', CFUNCTYPE(UNCHECKED(FPDF_BOOL), POINTER(struct__FPDF_FORMFILLINFO), FPDF_PAGE, FPDF_WIDGET, c_int, c_float, c_float)),
    ('FFI_OpenFile', CFUNCTYPE(UNCHECKED(POINTER(FPDF_FILEHANDLER)), POINTER(struct__FPDF_FORMFILLINFO), c_int, FPDF_WIDESTRING, POINTER(c_char))),
    ('FFI_EmailTo', CFUNCTYPE(UNCHECKED(None), POINTER(struct__FPDF_FORMFILLINFO), POINTER(FPDF_FILEHANDLER), FPDF_WIDESTRING, FPDF_WIDESTRING, FPDF_WIDESTRING, FPDF_WIDESTRING, FPDF_WIDESTRING)),
    ('FFI_UploadTo', CFUNCTYPE(UNCHECKED(None), POINTER(struct__FPDF_FORMFILLINFO), POINTER(FPDF_FILEHANDLER), c_int, FPDF_WIDESTRING)),
    ('FFI_GetPlatform', CFUNCTYPE(UNCHECKED(c_int), POINTER(struct__FPDF_FORMFILLINFO), POINTER(None), c_int)),
    ('FFI_GetLanguage', CFUNCTYPE(UNCHECKED(c_int), POINTER(struct__FPDF_FORMFILLINFO), POINTER(None), c_int)),
    ('FFI_DownloadFromURL', CFUNCTYPE(UNCHECKED(POINTER(FPDF_FILEHANDLER)), POINTER(struct__FPDF_FORMFILLINFO), FPDF_WIDESTRING)),
    ('FFI_PostRequestURL', CFUNCTYPE(UNCHECKED(FPDF_BOOL), POINTER(struct__FPDF_FORMFILLINFO), FPDF_WIDESTRING, FPDF_WIDESTRING, FPDF_WIDESTRING, FPDF_WIDESTRING, FPDF_WIDESTRING, POINTER(FPDF_BSTR))),
    ('FFI_PutRequestURL', CFUNCTYPE(UNCHECKED(FPDF_BOOL), POINTER(struct__FPDF_FORMFILLINFO), FPDF_WIDESTRING, FPDF_WIDESTRING, FPDF_WIDESTRING)),
    ('FFI_OnFocusChange', CFUNCTYPE(UNCHECKED(None), POINTER(struct__FPDF_FORMFILLINFO), FPDF_ANNOTATION, c_int)),
    ('FFI_DoURIActionWithKeyboardModifier', CFUNCTYPE(UNCHECKED(None), POINTER(struct__FPDF_FORMFILLINFO), FPDF_BYTESTRING, c_int)),
]
FPDF_FORMFILLINFO = struct__FPDF_FORMFILLINFO

if _libs["pdfium"].has("FPDFDOC_InitFormFillEnvironment", "cdecl"):
    FPDFDOC_InitFormFillEnvironment = _libs["pdfium"].get("FPDFDOC_InitFormFillEnvironment", "cdecl")
    FPDFDOC_InitFormFillEnvironment.argtypes = [FPDF_DOCUMENT, POINTER(FPDF_FORMFILLINFO)]
    FPDFDOC_InitFormFillEnvironment.restype = FPDF_FORMHANDLE

if _libs["pdfium"].has("FPDFDOC_ExitFormFillEnvironment", "cdecl"):
    FPDFDOC_ExitFormFillEnvironment = _libs["pdfium"].get("FPDFDOC_ExitFormFillEnvironment", "cdecl")
    FPDFDOC_ExitFormFillEnvironment.argtypes = [FPDF_FORMHANDLE]
    FPDFDOC_ExitFormFillEnvironment.restype = None

if _libs["pdfium"].has("FORM_OnAfterLoadPage", "cdecl"):
    FORM_OnAfterLoadPage = _libs["pdfium"].get("FORM_OnAfterLoadPage", "cdecl")
    FORM_OnAfterLoadPage.argtypes = [FPDF_PAGE, FPDF_FORMHANDLE]
    FORM_OnAfterLoadPage.restype = None

if _libs["pdfium"].has("FORM_OnBeforeClosePage", "cdecl"):
    FORM_OnBeforeClosePage = _libs["pdfium"].get("FORM_OnBeforeClosePage", "cdecl")
    FORM_OnBeforeClosePage.argtypes = [FPDF_PAGE, FPDF_FORMHANDLE]
    FORM_OnBeforeClosePage.restype = None

if _libs["pdfium"].has("FORM_DoDocumentJSAction", "cdecl"):
    FORM_DoDocumentJSAction = _libs["pdfium"].get("FORM_DoDocumentJSAction", "cdecl")
    FORM_DoDocumentJSAction.argtypes = [FPDF_FORMHANDLE]
    FORM_DoDocumentJSAction.restype = None

if _libs["pdfium"].has("FORM_DoDocumentOpenAction", "cdecl"):
    FORM_DoDocumentOpenAction = _libs["pdfium"].get("FORM_DoDocumentOpenAction", "cdecl")
    FORM_DoDocumentOpenAction.argtypes = [FPDF_FORMHANDLE]
    FORM_DoDocumentOpenAction.restype = None

if _libs["pdfium"].has("FORM_DoDocumentAAction", "cdecl"):
    FORM_DoDocumentAAction = _libs["pdfium"].get("FORM_DoDocumentAAction", "cdecl")
    FORM_DoDocumentAAction.argtypes = [FPDF_FORMHANDLE, c_int]
    FORM_DoDocumentAAction.restype = None

if _libs["pdfium"].has("FORM_DoPageAAction", "cdecl"):
    FORM_DoPageAAction = _libs["pdfium"].get("FORM_DoPageAAction", "cdecl")
    FORM_DoPageAAction.argtypes = [FPDF_PAGE, FPDF_FORMHANDLE, c_int]
    FORM_DoPageAAction.restype = None

if _libs["pdfium"].has("FORM_OnMouseMove", "cdecl"):
    FORM_OnMouseMove = _libs["pdfium"].get("FORM_OnMouseMove", "cdecl")
    FORM_OnMouseMove.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, c_int, c_double, c_double]
    FORM_OnMouseMove.restype = FPDF_BOOL

if _libs["pdfium"].has("FORM_OnMouseWheel", "cdecl"):
    FORM_OnMouseWheel = _libs["pdfium"].get("FORM_OnMouseWheel", "cdecl")
    FORM_OnMouseWheel.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, c_int, POINTER(FS_POINTF), c_int, c_int]
    FORM_OnMouseWheel.restype = FPDF_BOOL

if _libs["pdfium"].has("FORM_OnFocus", "cdecl"):
    FORM_OnFocus = _libs["pdfium"].get("FORM_OnFocus", "cdecl")
    FORM_OnFocus.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, c_int, c_double, c_double]
    FORM_OnFocus.restype = FPDF_BOOL

if _libs["pdfium"].has("FORM_OnLButtonDown", "cdecl"):
    FORM_OnLButtonDown = _libs["pdfium"].get("FORM_OnLButtonDown", "cdecl")
    FORM_OnLButtonDown.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, c_int, c_double, c_double]
    FORM_OnLButtonDown.restype = FPDF_BOOL

if _libs["pdfium"].has("FORM_OnRButtonDown", "cdecl"):
    FORM_OnRButtonDown = _libs["pdfium"].get("FORM_OnRButtonDown", "cdecl")
    FORM_OnRButtonDown.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, c_int, c_double, c_double]
    FORM_OnRButtonDown.restype = FPDF_BOOL

if _libs["pdfium"].has("FORM_OnLButtonUp", "cdecl"):
    FORM_OnLButtonUp = _libs["pdfium"].get("FORM_OnLButtonUp", "cdecl")
    FORM_OnLButtonUp.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, c_int, c_double, c_double]
    FORM_OnLButtonUp.restype = FPDF_BOOL

if _libs["pdfium"].has("FORM_OnRButtonUp", "cdecl"):
    FORM_OnRButtonUp = _libs["pdfium"].get("FORM_OnRButtonUp", "cdecl")
    FORM_OnRButtonUp.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, c_int, c_double, c_double]
    FORM_OnRButtonUp.restype = FPDF_BOOL

if _libs["pdfium"].has("FORM_OnLButtonDoubleClick", "cdecl"):
    FORM_OnLButtonDoubleClick = _libs["pdfium"].get("FORM_OnLButtonDoubleClick", "cdecl")
    FORM_OnLButtonDoubleClick.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, c_int, c_double, c_double]
    FORM_OnLButtonDoubleClick.restype = FPDF_BOOL

if _libs["pdfium"].has("FORM_OnKeyDown", "cdecl"):
    FORM_OnKeyDown = _libs["pdfium"].get("FORM_OnKeyDown", "cdecl")
    FORM_OnKeyDown.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, c_int, c_int]
    FORM_OnKeyDown.restype = FPDF_BOOL

if _libs["pdfium"].has("FORM_OnKeyUp", "cdecl"):
    FORM_OnKeyUp = _libs["pdfium"].get("FORM_OnKeyUp", "cdecl")
    FORM_OnKeyUp.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, c_int, c_int]
    FORM_OnKeyUp.restype = FPDF_BOOL

if _libs["pdfium"].has("FORM_OnChar", "cdecl"):
    FORM_OnChar = _libs["pdfium"].get("FORM_OnChar", "cdecl")
    FORM_OnChar.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, c_int, c_int]
    FORM_OnChar.restype = FPDF_BOOL

if _libs["pdfium"].has("FORM_GetFocusedText", "cdecl"):
    FORM_GetFocusedText = _libs["pdfium"].get("FORM_GetFocusedText", "cdecl")
    FORM_GetFocusedText.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, POINTER(None), c_ulong]
    FORM_GetFocusedText.restype = c_ulong

if _libs["pdfium"].has("FORM_GetSelectedText", "cdecl"):
    FORM_GetSelectedText = _libs["pdfium"].get("FORM_GetSelectedText", "cdecl")
    FORM_GetSelectedText.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, POINTER(None), c_ulong]
    FORM_GetSelectedText.restype = c_ulong

if _libs["pdfium"].has("FORM_ReplaceAndKeepSelection", "cdecl"):
    FORM_ReplaceAndKeepSelection = _libs["pdfium"].get("FORM_ReplaceAndKeepSelection", "cdecl")
    FORM_ReplaceAndKeepSelection.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, FPDF_WIDESTRING]
    FORM_ReplaceAndKeepSelection.restype = None

if _libs["pdfium"].has("FORM_ReplaceSelection", "cdecl"):
    FORM_ReplaceSelection = _libs["pdfium"].get("FORM_ReplaceSelection", "cdecl")
    FORM_ReplaceSelection.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, FPDF_WIDESTRING]
    FORM_ReplaceSelection.restype = None

if _libs["pdfium"].has("FORM_SelectAllText", "cdecl"):
    FORM_SelectAllText = _libs["pdfium"].get("FORM_SelectAllText", "cdecl")
    FORM_SelectAllText.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE]
    FORM_SelectAllText.restype = FPDF_BOOL

if _libs["pdfium"].has("FORM_CanUndo", "cdecl"):
    FORM_CanUndo = _libs["pdfium"].get("FORM_CanUndo", "cdecl")
    FORM_CanUndo.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE]
    FORM_CanUndo.restype = FPDF_BOOL

if _libs["pdfium"].has("FORM_CanRedo", "cdecl"):
    FORM_CanRedo = _libs["pdfium"].get("FORM_CanRedo", "cdecl")
    FORM_CanRedo.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE]
    FORM_CanRedo.restype = FPDF_BOOL

if _libs["pdfium"].has("FORM_Undo", "cdecl"):
    FORM_Undo = _libs["pdfium"].get("FORM_Undo", "cdecl")
    FORM_Undo.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE]
    FORM_Undo.restype = FPDF_BOOL

if _libs["pdfium"].has("FORM_Redo", "cdecl"):
    FORM_Redo = _libs["pdfium"].get("FORM_Redo", "cdecl")
    FORM_Redo.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE]
    FORM_Redo.restype = FPDF_BOOL

if _libs["pdfium"].has("FORM_ForceToKillFocus", "cdecl"):
    FORM_ForceToKillFocus = _libs["pdfium"].get("FORM_ForceToKillFocus", "cdecl")
    FORM_ForceToKillFocus.argtypes = [FPDF_FORMHANDLE]
    FORM_ForceToKillFocus.restype = FPDF_BOOL

if _libs["pdfium"].has("FORM_GetFocusedAnnot", "cdecl"):
    FORM_GetFocusedAnnot = _libs["pdfium"].get("FORM_GetFocusedAnnot", "cdecl")
    FORM_GetFocusedAnnot.argtypes = [FPDF_FORMHANDLE, POINTER(c_int), POINTER(FPDF_ANNOTATION)]
    FORM_GetFocusedAnnot.restype = FPDF_BOOL

if _libs["pdfium"].has("FORM_SetFocusedAnnot", "cdecl"):
    FORM_SetFocusedAnnot = _libs["pdfium"].get("FORM_SetFocusedAnnot", "cdecl")
    FORM_SetFocusedAnnot.argtypes = [FPDF_FORMHANDLE, FPDF_ANNOTATION]
    FORM_SetFocusedAnnot.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPage_HasFormFieldAtPoint", "cdecl"):
    FPDFPage_HasFormFieldAtPoint = _libs["pdfium"].get("FPDFPage_HasFormFieldAtPoint", "cdecl")
    FPDFPage_HasFormFieldAtPoint.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, c_double, c_double]
    FPDFPage_HasFormFieldAtPoint.restype = c_int

if _libs["pdfium"].has("FPDFPage_FormFieldZOrderAtPoint", "cdecl"):
    FPDFPage_FormFieldZOrderAtPoint = _libs["pdfium"].get("FPDFPage_FormFieldZOrderAtPoint", "cdecl")
    FPDFPage_FormFieldZOrderAtPoint.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, c_double, c_double]
    FPDFPage_FormFieldZOrderAtPoint.restype = c_int

if _libs["pdfium"].has("FPDF_SetFormFieldHighlightColor", "cdecl"):
    FPDF_SetFormFieldHighlightColor = _libs["pdfium"].get("FPDF_SetFormFieldHighlightColor", "cdecl")
    FPDF_SetFormFieldHighlightColor.argtypes = [FPDF_FORMHANDLE, c_int, c_ulong]
    FPDF_SetFormFieldHighlightColor.restype = None

if _libs["pdfium"].has("FPDF_SetFormFieldHighlightAlpha", "cdecl"):
    FPDF_SetFormFieldHighlightAlpha = _libs["pdfium"].get("FPDF_SetFormFieldHighlightAlpha", "cdecl")
    FPDF_SetFormFieldHighlightAlpha.argtypes = [FPDF_FORMHANDLE, c_ubyte]
    FPDF_SetFormFieldHighlightAlpha.restype = None

if _libs["pdfium"].has("FPDF_RemoveFormFieldHighlight", "cdecl"):
    FPDF_RemoveFormFieldHighlight = _libs["pdfium"].get("FPDF_RemoveFormFieldHighlight", "cdecl")
    FPDF_RemoveFormFieldHighlight.argtypes = [FPDF_FORMHANDLE]
    FPDF_RemoveFormFieldHighlight.restype = None

if _libs["pdfium"].has("FPDF_FFLDraw", "cdecl"):
    FPDF_FFLDraw = _libs["pdfium"].get("FPDF_FFLDraw", "cdecl")
    FPDF_FFLDraw.argtypes = [FPDF_FORMHANDLE, FPDF_BITMAP, FPDF_PAGE, c_int, c_int, c_int, c_int, c_int, c_int]
    FPDF_FFLDraw.restype = None

if _libs["pdfium"].has("FPDF_GetFormType", "cdecl"):
    FPDF_GetFormType = _libs["pdfium"].get("FPDF_GetFormType", "cdecl")
    FPDF_GetFormType.argtypes = [FPDF_DOCUMENT]
    FPDF_GetFormType.restype = c_int

if _libs["pdfium"].has("FORM_SetIndexSelected", "cdecl"):
    FORM_SetIndexSelected = _libs["pdfium"].get("FORM_SetIndexSelected", "cdecl")
    FORM_SetIndexSelected.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, c_int, FPDF_BOOL]
    FORM_SetIndexSelected.restype = FPDF_BOOL

if _libs["pdfium"].has("FORM_IsIndexSelected", "cdecl"):
    FORM_IsIndexSelected = _libs["pdfium"].get("FORM_IsIndexSelected", "cdecl")
    FORM_IsIndexSelected.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, c_int]
    FORM_IsIndexSelected.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDF_LoadXFA", "cdecl"):
    FPDF_LoadXFA = _libs["pdfium"].get("FPDF_LoadXFA", "cdecl")
    FPDF_LoadXFA.argtypes = [FPDF_DOCUMENT]
    FPDF_LoadXFA.restype = FPDF_BOOL
enum_FPDFANNOT_COLORTYPE = c_int
FPDFANNOT_COLORTYPE_Color = 0
FPDFANNOT_COLORTYPE_InteriorColor = (FPDFANNOT_COLORTYPE_Color + 1)
FPDFANNOT_COLORTYPE = enum_FPDFANNOT_COLORTYPE

if _libs["pdfium"].has("FPDFAnnot_IsSupportedSubtype", "cdecl"):
    FPDFAnnot_IsSupportedSubtype = _libs["pdfium"].get("FPDFAnnot_IsSupportedSubtype", "cdecl")
    FPDFAnnot_IsSupportedSubtype.argtypes = [FPDF_ANNOTATION_SUBTYPE]
    FPDFAnnot_IsSupportedSubtype.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPage_CreateAnnot", "cdecl"):
    FPDFPage_CreateAnnot = _libs["pdfium"].get("FPDFPage_CreateAnnot", "cdecl")
    FPDFPage_CreateAnnot.argtypes = [FPDF_PAGE, FPDF_ANNOTATION_SUBTYPE]
    FPDFPage_CreateAnnot.restype = FPDF_ANNOTATION

if _libs["pdfium"].has("FPDFPage_GetAnnotCount", "cdecl"):
    FPDFPage_GetAnnotCount = _libs["pdfium"].get("FPDFPage_GetAnnotCount", "cdecl")
    FPDFPage_GetAnnotCount.argtypes = [FPDF_PAGE]
    FPDFPage_GetAnnotCount.restype = c_int

if _libs["pdfium"].has("FPDFPage_GetAnnot", "cdecl"):
    FPDFPage_GetAnnot = _libs["pdfium"].get("FPDFPage_GetAnnot", "cdecl")
    FPDFPage_GetAnnot.argtypes = [FPDF_PAGE, c_int]
    FPDFPage_GetAnnot.restype = FPDF_ANNOTATION

if _libs["pdfium"].has("FPDFPage_GetAnnotIndex", "cdecl"):
    FPDFPage_GetAnnotIndex = _libs["pdfium"].get("FPDFPage_GetAnnotIndex", "cdecl")
    FPDFPage_GetAnnotIndex.argtypes = [FPDF_PAGE, FPDF_ANNOTATION]
    FPDFPage_GetAnnotIndex.restype = c_int

if _libs["pdfium"].has("FPDFPage_CloseAnnot", "cdecl"):
    FPDFPage_CloseAnnot = _libs["pdfium"].get("FPDFPage_CloseAnnot", "cdecl")
    FPDFPage_CloseAnnot.argtypes = [FPDF_ANNOTATION]
    FPDFPage_CloseAnnot.restype = None

if _libs["pdfium"].has("FPDFPage_RemoveAnnot", "cdecl"):
    FPDFPage_RemoveAnnot = _libs["pdfium"].get("FPDFPage_RemoveAnnot", "cdecl")
    FPDFPage_RemoveAnnot.argtypes = [FPDF_PAGE, c_int]
    FPDFPage_RemoveAnnot.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFAnnot_GetSubtype", "cdecl"):
    FPDFAnnot_GetSubtype = _libs["pdfium"].get("FPDFAnnot_GetSubtype", "cdecl")
    FPDFAnnot_GetSubtype.argtypes = [FPDF_ANNOTATION]
    FPDFAnnot_GetSubtype.restype = FPDF_ANNOTATION_SUBTYPE

if _libs["pdfium"].has("FPDFAnnot_IsObjectSupportedSubtype", "cdecl"):
    FPDFAnnot_IsObjectSupportedSubtype = _libs["pdfium"].get("FPDFAnnot_IsObjectSupportedSubtype", "cdecl")
    FPDFAnnot_IsObjectSupportedSubtype.argtypes = [FPDF_ANNOTATION_SUBTYPE]
    FPDFAnnot_IsObjectSupportedSubtype.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFAnnot_UpdateObject", "cdecl"):
    FPDFAnnot_UpdateObject = _libs["pdfium"].get("FPDFAnnot_UpdateObject", "cdecl")
    FPDFAnnot_UpdateObject.argtypes = [FPDF_ANNOTATION, FPDF_PAGEOBJECT]
    FPDFAnnot_UpdateObject.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFAnnot_AddInkStroke", "cdecl"):
    FPDFAnnot_AddInkStroke = _libs["pdfium"].get("FPDFAnnot_AddInkStroke", "cdecl")
    FPDFAnnot_AddInkStroke.argtypes = [FPDF_ANNOTATION, POINTER(FS_POINTF), c_size_t]
    FPDFAnnot_AddInkStroke.restype = c_int

if _libs["pdfium"].has("FPDFAnnot_RemoveInkList", "cdecl"):
    FPDFAnnot_RemoveInkList = _libs["pdfium"].get("FPDFAnnot_RemoveInkList", "cdecl")
    FPDFAnnot_RemoveInkList.argtypes = [FPDF_ANNOTATION]
    FPDFAnnot_RemoveInkList.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFAnnot_AppendObject", "cdecl"):
    FPDFAnnot_AppendObject = _libs["pdfium"].get("FPDFAnnot_AppendObject", "cdecl")
    FPDFAnnot_AppendObject.argtypes = [FPDF_ANNOTATION, FPDF_PAGEOBJECT]
    FPDFAnnot_AppendObject.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFAnnot_GetObjectCount", "cdecl"):
    FPDFAnnot_GetObjectCount = _libs["pdfium"].get("FPDFAnnot_GetObjectCount", "cdecl")
    FPDFAnnot_GetObjectCount.argtypes = [FPDF_ANNOTATION]
    FPDFAnnot_GetObjectCount.restype = c_int

if _libs["pdfium"].has("FPDFAnnot_GetObject", "cdecl"):
    FPDFAnnot_GetObject = _libs["pdfium"].get("FPDFAnnot_GetObject", "cdecl")
    FPDFAnnot_GetObject.argtypes = [FPDF_ANNOTATION, c_int]
    FPDFAnnot_GetObject.restype = FPDF_PAGEOBJECT

if _libs["pdfium"].has("FPDFAnnot_RemoveObject", "cdecl"):
    FPDFAnnot_RemoveObject = _libs["pdfium"].get("FPDFAnnot_RemoveObject", "cdecl")
    FPDFAnnot_RemoveObject.argtypes = [FPDF_ANNOTATION, c_int]
    FPDFAnnot_RemoveObject.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFAnnot_SetColor", "cdecl"):
    FPDFAnnot_SetColor = _libs["pdfium"].get("FPDFAnnot_SetColor", "cdecl")
    FPDFAnnot_SetColor.argtypes = [FPDF_ANNOTATION, FPDFANNOT_COLORTYPE, c_uint, c_uint, c_uint, c_uint]
    FPDFAnnot_SetColor.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFAnnot_GetColor", "cdecl"):
    FPDFAnnot_GetColor = _libs["pdfium"].get("FPDFAnnot_GetColor", "cdecl")
    FPDFAnnot_GetColor.argtypes = [FPDF_ANNOTATION, FPDFANNOT_COLORTYPE, POINTER(c_uint), POINTER(c_uint), POINTER(c_uint), POINTER(c_uint)]
    FPDFAnnot_GetColor.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFAnnot_HasAttachmentPoints", "cdecl"):
    FPDFAnnot_HasAttachmentPoints = _libs["pdfium"].get("FPDFAnnot_HasAttachmentPoints", "cdecl")
    FPDFAnnot_HasAttachmentPoints.argtypes = [FPDF_ANNOTATION]
    FPDFAnnot_HasAttachmentPoints.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFAnnot_SetAttachmentPoints", "cdecl"):
    FPDFAnnot_SetAttachmentPoints = _libs["pdfium"].get("FPDFAnnot_SetAttachmentPoints", "cdecl")
    FPDFAnnot_SetAttachmentPoints.argtypes = [FPDF_ANNOTATION, c_size_t, POINTER(FS_QUADPOINTSF)]
    FPDFAnnot_SetAttachmentPoints.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFAnnot_AppendAttachmentPoints", "cdecl"):
    FPDFAnnot_AppendAttachmentPoints = _libs["pdfium"].get("FPDFAnnot_AppendAttachmentPoints", "cdecl")
    FPDFAnnot_AppendAttachmentPoints.argtypes = [FPDF_ANNOTATION, POINTER(FS_QUADPOINTSF)]
    FPDFAnnot_AppendAttachmentPoints.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFAnnot_CountAttachmentPoints", "cdecl"):
    FPDFAnnot_CountAttachmentPoints = _libs["pdfium"].get("FPDFAnnot_CountAttachmentPoints", "cdecl")
    FPDFAnnot_CountAttachmentPoints.argtypes = [FPDF_ANNOTATION]
    FPDFAnnot_CountAttachmentPoints.restype = c_size_t

if _libs["pdfium"].has("FPDFAnnot_GetAttachmentPoints", "cdecl"):
    FPDFAnnot_GetAttachmentPoints = _libs["pdfium"].get("FPDFAnnot_GetAttachmentPoints", "cdecl")
    FPDFAnnot_GetAttachmentPoints.argtypes = [FPDF_ANNOTATION, c_size_t, POINTER(FS_QUADPOINTSF)]
    FPDFAnnot_GetAttachmentPoints.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFAnnot_SetRect", "cdecl"):
    FPDFAnnot_SetRect = _libs["pdfium"].get("FPDFAnnot_SetRect", "cdecl")
    FPDFAnnot_SetRect.argtypes = [FPDF_ANNOTATION, POINTER(FS_RECTF)]
    FPDFAnnot_SetRect.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFAnnot_GetRect", "cdecl"):
    FPDFAnnot_GetRect = _libs["pdfium"].get("FPDFAnnot_GetRect", "cdecl")
    FPDFAnnot_GetRect.argtypes = [FPDF_ANNOTATION, POINTER(FS_RECTF)]
    FPDFAnnot_GetRect.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFAnnot_GetVertices", "cdecl"):
    FPDFAnnot_GetVertices = _libs["pdfium"].get("FPDFAnnot_GetVertices", "cdecl")
    FPDFAnnot_GetVertices.argtypes = [FPDF_ANNOTATION, POINTER(FS_POINTF), c_ulong]
    FPDFAnnot_GetVertices.restype = c_ulong

if _libs["pdfium"].has("FPDFAnnot_GetInkListCount", "cdecl"):
    FPDFAnnot_GetInkListCount = _libs["pdfium"].get("FPDFAnnot_GetInkListCount", "cdecl")
    FPDFAnnot_GetInkListCount.argtypes = [FPDF_ANNOTATION]
    FPDFAnnot_GetInkListCount.restype = c_ulong

if _libs["pdfium"].has("FPDFAnnot_GetInkListPath", "cdecl"):
    FPDFAnnot_GetInkListPath = _libs["pdfium"].get("FPDFAnnot_GetInkListPath", "cdecl")
    FPDFAnnot_GetInkListPath.argtypes = [FPDF_ANNOTATION, c_ulong, POINTER(FS_POINTF), c_ulong]
    FPDFAnnot_GetInkListPath.restype = c_ulong

if _libs["pdfium"].has("FPDFAnnot_GetLine", "cdecl"):
    FPDFAnnot_GetLine = _libs["pdfium"].get("FPDFAnnot_GetLine", "cdecl")
    FPDFAnnot_GetLine.argtypes = [FPDF_ANNOTATION, POINTER(FS_POINTF), POINTER(FS_POINTF)]
    FPDFAnnot_GetLine.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFAnnot_SetBorder", "cdecl"):
    FPDFAnnot_SetBorder = _libs["pdfium"].get("FPDFAnnot_SetBorder", "cdecl")
    FPDFAnnot_SetBorder.argtypes = [FPDF_ANNOTATION, c_float, c_float, c_float]
    FPDFAnnot_SetBorder.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFAnnot_GetBorder", "cdecl"):
    FPDFAnnot_GetBorder = _libs["pdfium"].get("FPDFAnnot_GetBorder", "cdecl")
    FPDFAnnot_GetBorder.argtypes = [FPDF_ANNOTATION, POINTER(c_float), POINTER(c_float), POINTER(c_float)]
    FPDFAnnot_GetBorder.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFAnnot_GetFormAdditionalActionJavaScript", "cdecl"):
    FPDFAnnot_GetFormAdditionalActionJavaScript = _libs["pdfium"].get("FPDFAnnot_GetFormAdditionalActionJavaScript", "cdecl")
    FPDFAnnot_GetFormAdditionalActionJavaScript.argtypes = [FPDF_FORMHANDLE, FPDF_ANNOTATION, c_int, POINTER(FPDF_WCHAR), c_ulong]
    FPDFAnnot_GetFormAdditionalActionJavaScript.restype = c_ulong

if _libs["pdfium"].has("FPDFAnnot_HasKey", "cdecl"):
    FPDFAnnot_HasKey = _libs["pdfium"].get("FPDFAnnot_HasKey", "cdecl")
    FPDFAnnot_HasKey.argtypes = [FPDF_ANNOTATION, FPDF_BYTESTRING]
    FPDFAnnot_HasKey.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFAnnot_GetValueType", "cdecl"):
    FPDFAnnot_GetValueType = _libs["pdfium"].get("FPDFAnnot_GetValueType", "cdecl")
    FPDFAnnot_GetValueType.argtypes = [FPDF_ANNOTATION, FPDF_BYTESTRING]
    FPDFAnnot_GetValueType.restype = FPDF_OBJECT_TYPE

if _libs["pdfium"].has("FPDFAnnot_SetStringValue", "cdecl"):
    FPDFAnnot_SetStringValue = _libs["pdfium"].get("FPDFAnnot_SetStringValue", "cdecl")
    FPDFAnnot_SetStringValue.argtypes = [FPDF_ANNOTATION, FPDF_BYTESTRING, FPDF_WIDESTRING]
    FPDFAnnot_SetStringValue.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFAnnot_GetStringValue", "cdecl"):
    FPDFAnnot_GetStringValue = _libs["pdfium"].get("FPDFAnnot_GetStringValue", "cdecl")
    FPDFAnnot_GetStringValue.argtypes = [FPDF_ANNOTATION, FPDF_BYTESTRING, POINTER(FPDF_WCHAR), c_ulong]
    FPDFAnnot_GetStringValue.restype = c_ulong

if _libs["pdfium"].has("FPDFAnnot_GetNumberValue", "cdecl"):
    FPDFAnnot_GetNumberValue = _libs["pdfium"].get("FPDFAnnot_GetNumberValue", "cdecl")
    FPDFAnnot_GetNumberValue.argtypes = [FPDF_ANNOTATION, FPDF_BYTESTRING, POINTER(c_float)]
    FPDFAnnot_GetNumberValue.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFAnnot_SetAP", "cdecl"):
    FPDFAnnot_SetAP = _libs["pdfium"].get("FPDFAnnot_SetAP", "cdecl")
    FPDFAnnot_SetAP.argtypes = [FPDF_ANNOTATION, FPDF_ANNOT_APPEARANCEMODE, FPDF_WIDESTRING]
    FPDFAnnot_SetAP.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFAnnot_GetAP", "cdecl"):
    FPDFAnnot_GetAP = _libs["pdfium"].get("FPDFAnnot_GetAP", "cdecl")
    FPDFAnnot_GetAP.argtypes = [FPDF_ANNOTATION, FPDF_ANNOT_APPEARANCEMODE, POINTER(FPDF_WCHAR), c_ulong]
    FPDFAnnot_GetAP.restype = c_ulong

if _libs["pdfium"].has("FPDFAnnot_GetLinkedAnnot", "cdecl"):
    FPDFAnnot_GetLinkedAnnot = _libs["pdfium"].get("FPDFAnnot_GetLinkedAnnot", "cdecl")
    FPDFAnnot_GetLinkedAnnot.argtypes = [FPDF_ANNOTATION, FPDF_BYTESTRING]
    FPDFAnnot_GetLinkedAnnot.restype = FPDF_ANNOTATION

if _libs["pdfium"].has("FPDFAnnot_GetFlags", "cdecl"):
    FPDFAnnot_GetFlags = _libs["pdfium"].get("FPDFAnnot_GetFlags", "cdecl")
    FPDFAnnot_GetFlags.argtypes = [FPDF_ANNOTATION]
    FPDFAnnot_GetFlags.restype = c_int

if _libs["pdfium"].has("FPDFAnnot_SetFlags", "cdecl"):
    FPDFAnnot_SetFlags = _libs["pdfium"].get("FPDFAnnot_SetFlags", "cdecl")
    FPDFAnnot_SetFlags.argtypes = [FPDF_ANNOTATION, c_int]
    FPDFAnnot_SetFlags.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFAnnot_GetFormFieldFlags", "cdecl"):
    FPDFAnnot_GetFormFieldFlags = _libs["pdfium"].get("FPDFAnnot_GetFormFieldFlags", "cdecl")
    FPDFAnnot_GetFormFieldFlags.argtypes = [FPDF_FORMHANDLE, FPDF_ANNOTATION]
    FPDFAnnot_GetFormFieldFlags.restype = c_int

if _libs["pdfium"].has("FPDFAnnot_GetFormFieldAtPoint", "cdecl"):
    FPDFAnnot_GetFormFieldAtPoint = _libs["pdfium"].get("FPDFAnnot_GetFormFieldAtPoint", "cdecl")
    FPDFAnnot_GetFormFieldAtPoint.argtypes = [FPDF_FORMHANDLE, FPDF_PAGE, POINTER(FS_POINTF)]
    FPDFAnnot_GetFormFieldAtPoint.restype = FPDF_ANNOTATION

if _libs["pdfium"].has("FPDFAnnot_GetFormFieldName", "cdecl"):
    FPDFAnnot_GetFormFieldName = _libs["pdfium"].get("FPDFAnnot_GetFormFieldName", "cdecl")
    FPDFAnnot_GetFormFieldName.argtypes = [FPDF_FORMHANDLE, FPDF_ANNOTATION, POINTER(FPDF_WCHAR), c_ulong]
    FPDFAnnot_GetFormFieldName.restype = c_ulong

if _libs["pdfium"].has("FPDFAnnot_GetFormFieldAlternateName", "cdecl"):
    FPDFAnnot_GetFormFieldAlternateName = _libs["pdfium"].get("FPDFAnnot_GetFormFieldAlternateName", "cdecl")
    FPDFAnnot_GetFormFieldAlternateName.argtypes = [FPDF_FORMHANDLE, FPDF_ANNOTATION, POINTER(FPDF_WCHAR), c_ulong]
    FPDFAnnot_GetFormFieldAlternateName.restype = c_ulong

if _libs["pdfium"].has("FPDFAnnot_GetFormFieldType", "cdecl"):
    FPDFAnnot_GetFormFieldType = _libs["pdfium"].get("FPDFAnnot_GetFormFieldType", "cdecl")
    FPDFAnnot_GetFormFieldType.argtypes = [FPDF_FORMHANDLE, FPDF_ANNOTATION]
    FPDFAnnot_GetFormFieldType.restype = c_int

if _libs["pdfium"].has("FPDFAnnot_GetFormFieldValue", "cdecl"):
    FPDFAnnot_GetFormFieldValue = _libs["pdfium"].get("FPDFAnnot_GetFormFieldValue", "cdecl")
    FPDFAnnot_GetFormFieldValue.argtypes = [FPDF_FORMHANDLE, FPDF_ANNOTATION, POINTER(FPDF_WCHAR), c_ulong]
    FPDFAnnot_GetFormFieldValue.restype = c_ulong

if _libs["pdfium"].has("FPDFAnnot_GetOptionCount", "cdecl"):
    FPDFAnnot_GetOptionCount = _libs["pdfium"].get("FPDFAnnot_GetOptionCount", "cdecl")
    FPDFAnnot_GetOptionCount.argtypes = [FPDF_FORMHANDLE, FPDF_ANNOTATION]
    FPDFAnnot_GetOptionCount.restype = c_int

if _libs["pdfium"].has("FPDFAnnot_GetOptionLabel", "cdecl"):
    FPDFAnnot_GetOptionLabel = _libs["pdfium"].get("FPDFAnnot_GetOptionLabel", "cdecl")
    FPDFAnnot_GetOptionLabel.argtypes = [FPDF_FORMHANDLE, FPDF_ANNOTATION, c_int, POINTER(FPDF_WCHAR), c_ulong]
    FPDFAnnot_GetOptionLabel.restype = c_ulong

if _libs["pdfium"].has("FPDFAnnot_IsOptionSelected", "cdecl"):
    FPDFAnnot_IsOptionSelected = _libs["pdfium"].get("FPDFAnnot_IsOptionSelected", "cdecl")
    FPDFAnnot_IsOptionSelected.argtypes = [FPDF_FORMHANDLE, FPDF_ANNOTATION, c_int]
    FPDFAnnot_IsOptionSelected.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFAnnot_GetFontSize", "cdecl"):
    FPDFAnnot_GetFontSize = _libs["pdfium"].get("FPDFAnnot_GetFontSize", "cdecl")
    FPDFAnnot_GetFontSize.argtypes = [FPDF_FORMHANDLE, FPDF_ANNOTATION, POINTER(c_float)]
    FPDFAnnot_GetFontSize.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFAnnot_IsChecked", "cdecl"):
    FPDFAnnot_IsChecked = _libs["pdfium"].get("FPDFAnnot_IsChecked", "cdecl")
    FPDFAnnot_IsChecked.argtypes = [FPDF_FORMHANDLE, FPDF_ANNOTATION]
    FPDFAnnot_IsChecked.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFAnnot_SetFocusableSubtypes", "cdecl"):
    FPDFAnnot_SetFocusableSubtypes = _libs["pdfium"].get("FPDFAnnot_SetFocusableSubtypes", "cdecl")
    FPDFAnnot_SetFocusableSubtypes.argtypes = [FPDF_FORMHANDLE, POINTER(FPDF_ANNOTATION_SUBTYPE), c_size_t]
    FPDFAnnot_SetFocusableSubtypes.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFAnnot_GetFocusableSubtypesCount", "cdecl"):
    FPDFAnnot_GetFocusableSubtypesCount = _libs["pdfium"].get("FPDFAnnot_GetFocusableSubtypesCount", "cdecl")
    FPDFAnnot_GetFocusableSubtypesCount.argtypes = [FPDF_FORMHANDLE]
    FPDFAnnot_GetFocusableSubtypesCount.restype = c_int

if _libs["pdfium"].has("FPDFAnnot_GetFocusableSubtypes", "cdecl"):
    FPDFAnnot_GetFocusableSubtypes = _libs["pdfium"].get("FPDFAnnot_GetFocusableSubtypes", "cdecl")
    FPDFAnnot_GetFocusableSubtypes.argtypes = [FPDF_FORMHANDLE, POINTER(FPDF_ANNOTATION_SUBTYPE), c_size_t]
    FPDFAnnot_GetFocusableSubtypes.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFAnnot_GetLink", "cdecl"):
    FPDFAnnot_GetLink = _libs["pdfium"].get("FPDFAnnot_GetLink", "cdecl")
    FPDFAnnot_GetLink.argtypes = [FPDF_ANNOTATION]
    FPDFAnnot_GetLink.restype = FPDF_LINK

if _libs["pdfium"].has("FPDFAnnot_GetFormControlCount", "cdecl"):
    FPDFAnnot_GetFormControlCount = _libs["pdfium"].get("FPDFAnnot_GetFormControlCount", "cdecl")
    FPDFAnnot_GetFormControlCount.argtypes = [FPDF_FORMHANDLE, FPDF_ANNOTATION]
    FPDFAnnot_GetFormControlCount.restype = c_int

if _libs["pdfium"].has("FPDFAnnot_GetFormControlIndex", "cdecl"):
    FPDFAnnot_GetFormControlIndex = _libs["pdfium"].get("FPDFAnnot_GetFormControlIndex", "cdecl")
    FPDFAnnot_GetFormControlIndex.argtypes = [FPDF_FORMHANDLE, FPDF_ANNOTATION]
    FPDFAnnot_GetFormControlIndex.restype = c_int

if _libs["pdfium"].has("FPDFAnnot_GetFormFieldExportValue", "cdecl"):
    FPDFAnnot_GetFormFieldExportValue = _libs["pdfium"].get("FPDFAnnot_GetFormFieldExportValue", "cdecl")
    FPDFAnnot_GetFormFieldExportValue.argtypes = [FPDF_FORMHANDLE, FPDF_ANNOTATION, POINTER(FPDF_WCHAR), c_ulong]
    FPDFAnnot_GetFormFieldExportValue.restype = c_ulong

if _libs["pdfium"].has("FPDFAnnot_SetURI", "cdecl"):
    FPDFAnnot_SetURI = _libs["pdfium"].get("FPDFAnnot_SetURI", "cdecl")
    FPDFAnnot_SetURI.argtypes = [FPDF_ANNOTATION, POINTER(c_char)]
    FPDFAnnot_SetURI.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFDoc_GetAttachmentCount", "cdecl"):
    FPDFDoc_GetAttachmentCount = _libs["pdfium"].get("FPDFDoc_GetAttachmentCount", "cdecl")
    FPDFDoc_GetAttachmentCount.argtypes = [FPDF_DOCUMENT]
    FPDFDoc_GetAttachmentCount.restype = c_int

if _libs["pdfium"].has("FPDFDoc_AddAttachment", "cdecl"):
    FPDFDoc_AddAttachment = _libs["pdfium"].get("FPDFDoc_AddAttachment", "cdecl")
    FPDFDoc_AddAttachment.argtypes = [FPDF_DOCUMENT, FPDF_WIDESTRING]
    FPDFDoc_AddAttachment.restype = FPDF_ATTACHMENT

if _libs["pdfium"].has("FPDFDoc_GetAttachment", "cdecl"):
    FPDFDoc_GetAttachment = _libs["pdfium"].get("FPDFDoc_GetAttachment", "cdecl")
    FPDFDoc_GetAttachment.argtypes = [FPDF_DOCUMENT, c_int]
    FPDFDoc_GetAttachment.restype = FPDF_ATTACHMENT

if _libs["pdfium"].has("FPDFDoc_DeleteAttachment", "cdecl"):
    FPDFDoc_DeleteAttachment = _libs["pdfium"].get("FPDFDoc_DeleteAttachment", "cdecl")
    FPDFDoc_DeleteAttachment.argtypes = [FPDF_DOCUMENT, c_int]
    FPDFDoc_DeleteAttachment.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFAttachment_GetName", "cdecl"):
    FPDFAttachment_GetName = _libs["pdfium"].get("FPDFAttachment_GetName", "cdecl")
    FPDFAttachment_GetName.argtypes = [FPDF_ATTACHMENT, POINTER(FPDF_WCHAR), c_ulong]
    FPDFAttachment_GetName.restype = c_ulong

if _libs["pdfium"].has("FPDFAttachment_HasKey", "cdecl"):
    FPDFAttachment_HasKey = _libs["pdfium"].get("FPDFAttachment_HasKey", "cdecl")
    FPDFAttachment_HasKey.argtypes = [FPDF_ATTACHMENT, FPDF_BYTESTRING]
    FPDFAttachment_HasKey.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFAttachment_GetValueType", "cdecl"):
    FPDFAttachment_GetValueType = _libs["pdfium"].get("FPDFAttachment_GetValueType", "cdecl")
    FPDFAttachment_GetValueType.argtypes = [FPDF_ATTACHMENT, FPDF_BYTESTRING]
    FPDFAttachment_GetValueType.restype = FPDF_OBJECT_TYPE

if _libs["pdfium"].has("FPDFAttachment_SetStringValue", "cdecl"):
    FPDFAttachment_SetStringValue = _libs["pdfium"].get("FPDFAttachment_SetStringValue", "cdecl")
    FPDFAttachment_SetStringValue.argtypes = [FPDF_ATTACHMENT, FPDF_BYTESTRING, FPDF_WIDESTRING]
    FPDFAttachment_SetStringValue.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFAttachment_GetStringValue", "cdecl"):
    FPDFAttachment_GetStringValue = _libs["pdfium"].get("FPDFAttachment_GetStringValue", "cdecl")
    FPDFAttachment_GetStringValue.argtypes = [FPDF_ATTACHMENT, FPDF_BYTESTRING, POINTER(FPDF_WCHAR), c_ulong]
    FPDFAttachment_GetStringValue.restype = c_ulong

if _libs["pdfium"].has("FPDFAttachment_SetFile", "cdecl"):
    FPDFAttachment_SetFile = _libs["pdfium"].get("FPDFAttachment_SetFile", "cdecl")
    FPDFAttachment_SetFile.argtypes = [FPDF_ATTACHMENT, FPDF_DOCUMENT, POINTER(None), c_ulong]
    FPDFAttachment_SetFile.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFAttachment_GetFile", "cdecl"):
    FPDFAttachment_GetFile = _libs["pdfium"].get("FPDFAttachment_GetFile", "cdecl")
    FPDFAttachment_GetFile.argtypes = [FPDF_ATTACHMENT, POINTER(None), c_ulong, POINTER(c_ulong)]
    FPDFAttachment_GetFile.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFCatalog_IsTagged", "cdecl"):
    FPDFCatalog_IsTagged = _libs["pdfium"].get("FPDFCatalog_IsTagged", "cdecl")
    FPDFCatalog_IsTagged.argtypes = [FPDF_DOCUMENT]
    FPDFCatalog_IsTagged.restype = FPDF_BOOL

class struct__FX_FILEAVAIL(Structure):
    pass
struct__FX_FILEAVAIL.__slots__ = [
    'version',
    'IsDataAvail',
]
struct__FX_FILEAVAIL._fields_ = [
    ('version', c_int),
    ('IsDataAvail', CFUNCTYPE(UNCHECKED(FPDF_BOOL), POINTER(struct__FX_FILEAVAIL), c_size_t, c_size_t)),
]
FX_FILEAVAIL = struct__FX_FILEAVAIL

if _libs["pdfium"].has("FPDFAvail_Create", "cdecl"):
    FPDFAvail_Create = _libs["pdfium"].get("FPDFAvail_Create", "cdecl")
    FPDFAvail_Create.argtypes = [POINTER(FX_FILEAVAIL), POINTER(FPDF_FILEACCESS)]
    FPDFAvail_Create.restype = FPDF_AVAIL

if _libs["pdfium"].has("FPDFAvail_Destroy", "cdecl"):
    FPDFAvail_Destroy = _libs["pdfium"].get("FPDFAvail_Destroy", "cdecl")
    FPDFAvail_Destroy.argtypes = [FPDF_AVAIL]
    FPDFAvail_Destroy.restype = None

class struct__FX_DOWNLOADHINTS(Structure):
    pass
struct__FX_DOWNLOADHINTS.__slots__ = [
    'version',
    'AddSegment',
]
struct__FX_DOWNLOADHINTS._fields_ = [
    ('version', c_int),
    ('AddSegment', CFUNCTYPE(UNCHECKED(None), POINTER(struct__FX_DOWNLOADHINTS), c_size_t, c_size_t)),
]
FX_DOWNLOADHINTS = struct__FX_DOWNLOADHINTS

if _libs["pdfium"].has("FPDFAvail_IsDocAvail", "cdecl"):
    FPDFAvail_IsDocAvail = _libs["pdfium"].get("FPDFAvail_IsDocAvail", "cdecl")
    FPDFAvail_IsDocAvail.argtypes = [FPDF_AVAIL, POINTER(FX_DOWNLOADHINTS)]
    FPDFAvail_IsDocAvail.restype = c_int

if _libs["pdfium"].has("FPDFAvail_GetDocument", "cdecl"):
    FPDFAvail_GetDocument = _libs["pdfium"].get("FPDFAvail_GetDocument", "cdecl")
    FPDFAvail_GetDocument.argtypes = [FPDF_AVAIL, FPDF_BYTESTRING]
    FPDFAvail_GetDocument.restype = FPDF_DOCUMENT

if _libs["pdfium"].has("FPDFAvail_GetFirstPageNum", "cdecl"):
    FPDFAvail_GetFirstPageNum = _libs["pdfium"].get("FPDFAvail_GetFirstPageNum", "cdecl")
    FPDFAvail_GetFirstPageNum.argtypes = [FPDF_DOCUMENT]
    FPDFAvail_GetFirstPageNum.restype = c_int

if _libs["pdfium"].has("FPDFAvail_IsPageAvail", "cdecl"):
    FPDFAvail_IsPageAvail = _libs["pdfium"].get("FPDFAvail_IsPageAvail", "cdecl")
    FPDFAvail_IsPageAvail.argtypes = [FPDF_AVAIL, c_int, POINTER(FX_DOWNLOADHINTS)]
    FPDFAvail_IsPageAvail.restype = c_int

if _libs["pdfium"].has("FPDFAvail_IsFormAvail", "cdecl"):
    FPDFAvail_IsFormAvail = _libs["pdfium"].get("FPDFAvail_IsFormAvail", "cdecl")
    FPDFAvail_IsFormAvail.argtypes = [FPDF_AVAIL, POINTER(FX_DOWNLOADHINTS)]
    FPDFAvail_IsFormAvail.restype = c_int

if _libs["pdfium"].has("FPDFAvail_IsLinearized", "cdecl"):
    FPDFAvail_IsLinearized = _libs["pdfium"].get("FPDFAvail_IsLinearized", "cdecl")
    FPDFAvail_IsLinearized.argtypes = [FPDF_AVAIL]
    FPDFAvail_IsLinearized.restype = c_int
enum_anon_5 = c_int
FILEIDTYPE_PERMANENT = 0
FILEIDTYPE_CHANGING = 1
FPDF_FILEIDTYPE = enum_anon_5

if _libs["pdfium"].has("FPDFBookmark_GetFirstChild", "cdecl"):
    FPDFBookmark_GetFirstChild = _libs["pdfium"].get("FPDFBookmark_GetFirstChild", "cdecl")
    FPDFBookmark_GetFirstChild.argtypes = [FPDF_DOCUMENT, FPDF_BOOKMARK]
    FPDFBookmark_GetFirstChild.restype = FPDF_BOOKMARK

if _libs["pdfium"].has("FPDFBookmark_GetNextSibling", "cdecl"):
    FPDFBookmark_GetNextSibling = _libs["pdfium"].get("FPDFBookmark_GetNextSibling", "cdecl")
    FPDFBookmark_GetNextSibling.argtypes = [FPDF_DOCUMENT, FPDF_BOOKMARK]
    FPDFBookmark_GetNextSibling.restype = FPDF_BOOKMARK

if _libs["pdfium"].has("FPDFBookmark_GetTitle", "cdecl"):
    FPDFBookmark_GetTitle = _libs["pdfium"].get("FPDFBookmark_GetTitle", "cdecl")
    FPDFBookmark_GetTitle.argtypes = [FPDF_BOOKMARK, POINTER(None), c_ulong]
    FPDFBookmark_GetTitle.restype = c_ulong

if _libs["pdfium"].has("FPDFBookmark_GetCount", "cdecl"):
    FPDFBookmark_GetCount = _libs["pdfium"].get("FPDFBookmark_GetCount", "cdecl")
    FPDFBookmark_GetCount.argtypes = [FPDF_BOOKMARK]
    FPDFBookmark_GetCount.restype = c_int

if _libs["pdfium"].has("FPDFBookmark_Find", "cdecl"):
    FPDFBookmark_Find = _libs["pdfium"].get("FPDFBookmark_Find", "cdecl")
    FPDFBookmark_Find.argtypes = [FPDF_DOCUMENT, FPDF_WIDESTRING]
    FPDFBookmark_Find.restype = FPDF_BOOKMARK

if _libs["pdfium"].has("FPDFBookmark_GetDest", "cdecl"):
    FPDFBookmark_GetDest = _libs["pdfium"].get("FPDFBookmark_GetDest", "cdecl")
    FPDFBookmark_GetDest.argtypes = [FPDF_DOCUMENT, FPDF_BOOKMARK]
    FPDFBookmark_GetDest.restype = FPDF_DEST

if _libs["pdfium"].has("FPDFBookmark_GetAction", "cdecl"):
    FPDFBookmark_GetAction = _libs["pdfium"].get("FPDFBookmark_GetAction", "cdecl")
    FPDFBookmark_GetAction.argtypes = [FPDF_BOOKMARK]
    FPDFBookmark_GetAction.restype = FPDF_ACTION

if _libs["pdfium"].has("FPDFAction_GetType", "cdecl"):
    FPDFAction_GetType = _libs["pdfium"].get("FPDFAction_GetType", "cdecl")
    FPDFAction_GetType.argtypes = [FPDF_ACTION]
    FPDFAction_GetType.restype = c_ulong

if _libs["pdfium"].has("FPDFAction_GetDest", "cdecl"):
    FPDFAction_GetDest = _libs["pdfium"].get("FPDFAction_GetDest", "cdecl")
    FPDFAction_GetDest.argtypes = [FPDF_DOCUMENT, FPDF_ACTION]
    FPDFAction_GetDest.restype = FPDF_DEST

if _libs["pdfium"].has("FPDFAction_GetFilePath", "cdecl"):
    FPDFAction_GetFilePath = _libs["pdfium"].get("FPDFAction_GetFilePath", "cdecl")
    FPDFAction_GetFilePath.argtypes = [FPDF_ACTION, POINTER(None), c_ulong]
    FPDFAction_GetFilePath.restype = c_ulong

if _libs["pdfium"].has("FPDFAction_GetURIPath", "cdecl"):
    FPDFAction_GetURIPath = _libs["pdfium"].get("FPDFAction_GetURIPath", "cdecl")
    FPDFAction_GetURIPath.argtypes = [FPDF_DOCUMENT, FPDF_ACTION, POINTER(None), c_ulong]
    FPDFAction_GetURIPath.restype = c_ulong

if _libs["pdfium"].has("FPDFDest_GetDestPageIndex", "cdecl"):
    FPDFDest_GetDestPageIndex = _libs["pdfium"].get("FPDFDest_GetDestPageIndex", "cdecl")
    FPDFDest_GetDestPageIndex.argtypes = [FPDF_DOCUMENT, FPDF_DEST]
    FPDFDest_GetDestPageIndex.restype = c_int

if _libs["pdfium"].has("FPDFDest_GetView", "cdecl"):
    FPDFDest_GetView = _libs["pdfium"].get("FPDFDest_GetView", "cdecl")
    FPDFDest_GetView.argtypes = [FPDF_DEST, POINTER(c_ulong), POINTER(FS_FLOAT)]
    FPDFDest_GetView.restype = c_ulong

if _libs["pdfium"].has("FPDFDest_GetLocationInPage", "cdecl"):
    FPDFDest_GetLocationInPage = _libs["pdfium"].get("FPDFDest_GetLocationInPage", "cdecl")
    FPDFDest_GetLocationInPage.argtypes = [FPDF_DEST, POINTER(FPDF_BOOL), POINTER(FPDF_BOOL), POINTER(FPDF_BOOL), POINTER(FS_FLOAT), POINTER(FS_FLOAT), POINTER(FS_FLOAT)]
    FPDFDest_GetLocationInPage.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFLink_GetLinkAtPoint", "cdecl"):
    FPDFLink_GetLinkAtPoint = _libs["pdfium"].get("FPDFLink_GetLinkAtPoint", "cdecl")
    FPDFLink_GetLinkAtPoint.argtypes = [FPDF_PAGE, c_double, c_double]
    FPDFLink_GetLinkAtPoint.restype = FPDF_LINK

if _libs["pdfium"].has("FPDFLink_GetLinkZOrderAtPoint", "cdecl"):
    FPDFLink_GetLinkZOrderAtPoint = _libs["pdfium"].get("FPDFLink_GetLinkZOrderAtPoint", "cdecl")
    FPDFLink_GetLinkZOrderAtPoint.argtypes = [FPDF_PAGE, c_double, c_double]
    FPDFLink_GetLinkZOrderAtPoint.restype = c_int

if _libs["pdfium"].has("FPDFLink_GetDest", "cdecl"):
    FPDFLink_GetDest = _libs["pdfium"].get("FPDFLink_GetDest", "cdecl")
    FPDFLink_GetDest.argtypes = [FPDF_DOCUMENT, FPDF_LINK]
    FPDFLink_GetDest.restype = FPDF_DEST

if _libs["pdfium"].has("FPDFLink_GetAction", "cdecl"):
    FPDFLink_GetAction = _libs["pdfium"].get("FPDFLink_GetAction", "cdecl")
    FPDFLink_GetAction.argtypes = [FPDF_LINK]
    FPDFLink_GetAction.restype = FPDF_ACTION

if _libs["pdfium"].has("FPDFLink_Enumerate", "cdecl"):
    FPDFLink_Enumerate = _libs["pdfium"].get("FPDFLink_Enumerate", "cdecl")
    FPDFLink_Enumerate.argtypes = [FPDF_PAGE, POINTER(c_int), POINTER(FPDF_LINK)]
    FPDFLink_Enumerate.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFLink_GetAnnot", "cdecl"):
    FPDFLink_GetAnnot = _libs["pdfium"].get("FPDFLink_GetAnnot", "cdecl")
    FPDFLink_GetAnnot.argtypes = [FPDF_PAGE, FPDF_LINK]
    FPDFLink_GetAnnot.restype = FPDF_ANNOTATION

if _libs["pdfium"].has("FPDFLink_GetAnnotRect", "cdecl"):
    FPDFLink_GetAnnotRect = _libs["pdfium"].get("FPDFLink_GetAnnotRect", "cdecl")
    FPDFLink_GetAnnotRect.argtypes = [FPDF_LINK, POINTER(FS_RECTF)]
    FPDFLink_GetAnnotRect.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFLink_CountQuadPoints", "cdecl"):
    FPDFLink_CountQuadPoints = _libs["pdfium"].get("FPDFLink_CountQuadPoints", "cdecl")
    FPDFLink_CountQuadPoints.argtypes = [FPDF_LINK]
    FPDFLink_CountQuadPoints.restype = c_int

if _libs["pdfium"].has("FPDFLink_GetQuadPoints", "cdecl"):
    FPDFLink_GetQuadPoints = _libs["pdfium"].get("FPDFLink_GetQuadPoints", "cdecl")
    FPDFLink_GetQuadPoints.argtypes = [FPDF_LINK, c_int, POINTER(FS_QUADPOINTSF)]
    FPDFLink_GetQuadPoints.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDF_GetPageAAction", "cdecl"):
    FPDF_GetPageAAction = _libs["pdfium"].get("FPDF_GetPageAAction", "cdecl")
    FPDF_GetPageAAction.argtypes = [FPDF_PAGE, c_int]
    FPDF_GetPageAAction.restype = FPDF_ACTION

if _libs["pdfium"].has("FPDF_GetFileIdentifier", "cdecl"):
    FPDF_GetFileIdentifier = _libs["pdfium"].get("FPDF_GetFileIdentifier", "cdecl")
    FPDF_GetFileIdentifier.argtypes = [FPDF_DOCUMENT, FPDF_FILEIDTYPE, POINTER(None), c_ulong]
    FPDF_GetFileIdentifier.restype = c_ulong

if _libs["pdfium"].has("FPDF_GetMetaText", "cdecl"):
    FPDF_GetMetaText = _libs["pdfium"].get("FPDF_GetMetaText", "cdecl")
    FPDF_GetMetaText.argtypes = [FPDF_DOCUMENT, FPDF_BYTESTRING, POINTER(None), c_ulong]
    FPDF_GetMetaText.restype = c_ulong

if _libs["pdfium"].has("FPDF_GetPageLabel", "cdecl"):
    FPDF_GetPageLabel = _libs["pdfium"].get("FPDF_GetPageLabel", "cdecl")
    FPDF_GetPageLabel.argtypes = [FPDF_DOCUMENT, c_int, POINTER(None), c_ulong]
    FPDF_GetPageLabel.restype = c_ulong
__uint8_t = c_ubyte
__uint16_t = c_ushort
__uint32_t = c_uint
__time_t = c_long
uint8_t = __uint8_t
uint16_t = __uint16_t
uint32_t = __uint32_t

class struct_FPDF_IMAGEOBJ_METADATA(Structure):
    pass
struct_FPDF_IMAGEOBJ_METADATA.__slots__ = [
    'width',
    'height',
    'horizontal_dpi',
    'vertical_dpi',
    'bits_per_pixel',
    'colorspace',
    'marked_content_id',
]
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

if _libs["pdfium"].has("FPDF_CreateNewDocument", "cdecl"):
    FPDF_CreateNewDocument = _libs["pdfium"].get("FPDF_CreateNewDocument", "cdecl")
    FPDF_CreateNewDocument.argtypes = []
    FPDF_CreateNewDocument.restype = FPDF_DOCUMENT

if _libs["pdfium"].has("FPDFPage_New", "cdecl"):
    FPDFPage_New = _libs["pdfium"].get("FPDFPage_New", "cdecl")
    FPDFPage_New.argtypes = [FPDF_DOCUMENT, c_int, c_double, c_double]
    FPDFPage_New.restype = FPDF_PAGE

if _libs["pdfium"].has("FPDFPage_Delete", "cdecl"):
    FPDFPage_Delete = _libs["pdfium"].get("FPDFPage_Delete", "cdecl")
    FPDFPage_Delete.argtypes = [FPDF_DOCUMENT, c_int]
    FPDFPage_Delete.restype = None

if _libs["pdfium"].has("FPDFPage_GetRotation", "cdecl"):
    FPDFPage_GetRotation = _libs["pdfium"].get("FPDFPage_GetRotation", "cdecl")
    FPDFPage_GetRotation.argtypes = [FPDF_PAGE]
    FPDFPage_GetRotation.restype = c_int

if _libs["pdfium"].has("FPDFPage_SetRotation", "cdecl"):
    FPDFPage_SetRotation = _libs["pdfium"].get("FPDFPage_SetRotation", "cdecl")
    FPDFPage_SetRotation.argtypes = [FPDF_PAGE, c_int]
    FPDFPage_SetRotation.restype = None

if _libs["pdfium"].has("FPDFPage_InsertObject", "cdecl"):
    FPDFPage_InsertObject = _libs["pdfium"].get("FPDFPage_InsertObject", "cdecl")
    FPDFPage_InsertObject.argtypes = [FPDF_PAGE, FPDF_PAGEOBJECT]
    FPDFPage_InsertObject.restype = None

if _libs["pdfium"].has("FPDFPage_RemoveObject", "cdecl"):
    FPDFPage_RemoveObject = _libs["pdfium"].get("FPDFPage_RemoveObject", "cdecl")
    FPDFPage_RemoveObject.argtypes = [FPDF_PAGE, FPDF_PAGEOBJECT]
    FPDFPage_RemoveObject.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPage_CountObjects", "cdecl"):
    FPDFPage_CountObjects = _libs["pdfium"].get("FPDFPage_CountObjects", "cdecl")
    FPDFPage_CountObjects.argtypes = [FPDF_PAGE]
    FPDFPage_CountObjects.restype = c_int

if _libs["pdfium"].has("FPDFPage_GetObject", "cdecl"):
    FPDFPage_GetObject = _libs["pdfium"].get("FPDFPage_GetObject", "cdecl")
    FPDFPage_GetObject.argtypes = [FPDF_PAGE, c_int]
    FPDFPage_GetObject.restype = FPDF_PAGEOBJECT

if _libs["pdfium"].has("FPDFPage_HasTransparency", "cdecl"):
    FPDFPage_HasTransparency = _libs["pdfium"].get("FPDFPage_HasTransparency", "cdecl")
    FPDFPage_HasTransparency.argtypes = [FPDF_PAGE]
    FPDFPage_HasTransparency.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPage_GenerateContent", "cdecl"):
    FPDFPage_GenerateContent = _libs["pdfium"].get("FPDFPage_GenerateContent", "cdecl")
    FPDFPage_GenerateContent.argtypes = [FPDF_PAGE]
    FPDFPage_GenerateContent.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPageObj_Destroy", "cdecl"):
    FPDFPageObj_Destroy = _libs["pdfium"].get("FPDFPageObj_Destroy", "cdecl")
    FPDFPageObj_Destroy.argtypes = [FPDF_PAGEOBJECT]
    FPDFPageObj_Destroy.restype = None

if _libs["pdfium"].has("FPDFPageObj_HasTransparency", "cdecl"):
    FPDFPageObj_HasTransparency = _libs["pdfium"].get("FPDFPageObj_HasTransparency", "cdecl")
    FPDFPageObj_HasTransparency.argtypes = [FPDF_PAGEOBJECT]
    FPDFPageObj_HasTransparency.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPageObj_GetType", "cdecl"):
    FPDFPageObj_GetType = _libs["pdfium"].get("FPDFPageObj_GetType", "cdecl")
    FPDFPageObj_GetType.argtypes = [FPDF_PAGEOBJECT]
    FPDFPageObj_GetType.restype = c_int

if _libs["pdfium"].has("FPDFPageObj_Transform", "cdecl"):
    FPDFPageObj_Transform = _libs["pdfium"].get("FPDFPageObj_Transform", "cdecl")
    FPDFPageObj_Transform.argtypes = [FPDF_PAGEOBJECT, c_double, c_double, c_double, c_double, c_double, c_double]
    FPDFPageObj_Transform.restype = None

if _libs["pdfium"].has("FPDFPageObj_GetMatrix", "cdecl"):
    FPDFPageObj_GetMatrix = _libs["pdfium"].get("FPDFPageObj_GetMatrix", "cdecl")
    FPDFPageObj_GetMatrix.argtypes = [FPDF_PAGEOBJECT, POINTER(FS_MATRIX)]
    FPDFPageObj_GetMatrix.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPageObj_SetMatrix", "cdecl"):
    FPDFPageObj_SetMatrix = _libs["pdfium"].get("FPDFPageObj_SetMatrix", "cdecl")
    FPDFPageObj_SetMatrix.argtypes = [FPDF_PAGEOBJECT, POINTER(FS_MATRIX)]
    FPDFPageObj_SetMatrix.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPage_TransformAnnots", "cdecl"):
    FPDFPage_TransformAnnots = _libs["pdfium"].get("FPDFPage_TransformAnnots", "cdecl")
    FPDFPage_TransformAnnots.argtypes = [FPDF_PAGE, c_double, c_double, c_double, c_double, c_double, c_double]
    FPDFPage_TransformAnnots.restype = None

if _libs["pdfium"].has("FPDFPageObj_NewImageObj", "cdecl"):
    FPDFPageObj_NewImageObj = _libs["pdfium"].get("FPDFPageObj_NewImageObj", "cdecl")
    FPDFPageObj_NewImageObj.argtypes = [FPDF_DOCUMENT]
    FPDFPageObj_NewImageObj.restype = FPDF_PAGEOBJECT

if _libs["pdfium"].has("FPDFPageObj_CountMarks", "cdecl"):
    FPDFPageObj_CountMarks = _libs["pdfium"].get("FPDFPageObj_CountMarks", "cdecl")
    FPDFPageObj_CountMarks.argtypes = [FPDF_PAGEOBJECT]
    FPDFPageObj_CountMarks.restype = c_int

if _libs["pdfium"].has("FPDFPageObj_GetMark", "cdecl"):
    FPDFPageObj_GetMark = _libs["pdfium"].get("FPDFPageObj_GetMark", "cdecl")
    FPDFPageObj_GetMark.argtypes = [FPDF_PAGEOBJECT, c_ulong]
    FPDFPageObj_GetMark.restype = FPDF_PAGEOBJECTMARK

if _libs["pdfium"].has("FPDFPageObj_AddMark", "cdecl"):
    FPDFPageObj_AddMark = _libs["pdfium"].get("FPDFPageObj_AddMark", "cdecl")
    FPDFPageObj_AddMark.argtypes = [FPDF_PAGEOBJECT, FPDF_BYTESTRING]
    FPDFPageObj_AddMark.restype = FPDF_PAGEOBJECTMARK

if _libs["pdfium"].has("FPDFPageObj_RemoveMark", "cdecl"):
    FPDFPageObj_RemoveMark = _libs["pdfium"].get("FPDFPageObj_RemoveMark", "cdecl")
    FPDFPageObj_RemoveMark.argtypes = [FPDF_PAGEOBJECT, FPDF_PAGEOBJECTMARK]
    FPDFPageObj_RemoveMark.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPageObjMark_GetName", "cdecl"):
    FPDFPageObjMark_GetName = _libs["pdfium"].get("FPDFPageObjMark_GetName", "cdecl")
    FPDFPageObjMark_GetName.argtypes = [FPDF_PAGEOBJECTMARK, POINTER(None), c_ulong, POINTER(c_ulong)]
    FPDFPageObjMark_GetName.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPageObjMark_CountParams", "cdecl"):
    FPDFPageObjMark_CountParams = _libs["pdfium"].get("FPDFPageObjMark_CountParams", "cdecl")
    FPDFPageObjMark_CountParams.argtypes = [FPDF_PAGEOBJECTMARK]
    FPDFPageObjMark_CountParams.restype = c_int

if _libs["pdfium"].has("FPDFPageObjMark_GetParamKey", "cdecl"):
    FPDFPageObjMark_GetParamKey = _libs["pdfium"].get("FPDFPageObjMark_GetParamKey", "cdecl")
    FPDFPageObjMark_GetParamKey.argtypes = [FPDF_PAGEOBJECTMARK, c_ulong, POINTER(None), c_ulong, POINTER(c_ulong)]
    FPDFPageObjMark_GetParamKey.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPageObjMark_GetParamValueType", "cdecl"):
    FPDFPageObjMark_GetParamValueType = _libs["pdfium"].get("FPDFPageObjMark_GetParamValueType", "cdecl")
    FPDFPageObjMark_GetParamValueType.argtypes = [FPDF_PAGEOBJECTMARK, FPDF_BYTESTRING]
    FPDFPageObjMark_GetParamValueType.restype = FPDF_OBJECT_TYPE

if _libs["pdfium"].has("FPDFPageObjMark_GetParamIntValue", "cdecl"):
    FPDFPageObjMark_GetParamIntValue = _libs["pdfium"].get("FPDFPageObjMark_GetParamIntValue", "cdecl")
    FPDFPageObjMark_GetParamIntValue.argtypes = [FPDF_PAGEOBJECTMARK, FPDF_BYTESTRING, POINTER(c_int)]
    FPDFPageObjMark_GetParamIntValue.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPageObjMark_GetParamStringValue", "cdecl"):
    FPDFPageObjMark_GetParamStringValue = _libs["pdfium"].get("FPDFPageObjMark_GetParamStringValue", "cdecl")
    FPDFPageObjMark_GetParamStringValue.argtypes = [FPDF_PAGEOBJECTMARK, FPDF_BYTESTRING, POINTER(None), c_ulong, POINTER(c_ulong)]
    FPDFPageObjMark_GetParamStringValue.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPageObjMark_GetParamBlobValue", "cdecl"):
    FPDFPageObjMark_GetParamBlobValue = _libs["pdfium"].get("FPDFPageObjMark_GetParamBlobValue", "cdecl")
    FPDFPageObjMark_GetParamBlobValue.argtypes = [FPDF_PAGEOBJECTMARK, FPDF_BYTESTRING, POINTER(None), c_ulong, POINTER(c_ulong)]
    FPDFPageObjMark_GetParamBlobValue.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPageObjMark_SetIntParam", "cdecl"):
    FPDFPageObjMark_SetIntParam = _libs["pdfium"].get("FPDFPageObjMark_SetIntParam", "cdecl")
    FPDFPageObjMark_SetIntParam.argtypes = [FPDF_DOCUMENT, FPDF_PAGEOBJECT, FPDF_PAGEOBJECTMARK, FPDF_BYTESTRING, c_int]
    FPDFPageObjMark_SetIntParam.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPageObjMark_SetStringParam", "cdecl"):
    FPDFPageObjMark_SetStringParam = _libs["pdfium"].get("FPDFPageObjMark_SetStringParam", "cdecl")
    FPDFPageObjMark_SetStringParam.argtypes = [FPDF_DOCUMENT, FPDF_PAGEOBJECT, FPDF_PAGEOBJECTMARK, FPDF_BYTESTRING, FPDF_BYTESTRING]
    FPDFPageObjMark_SetStringParam.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPageObjMark_SetBlobParam", "cdecl"):
    FPDFPageObjMark_SetBlobParam = _libs["pdfium"].get("FPDFPageObjMark_SetBlobParam", "cdecl")
    FPDFPageObjMark_SetBlobParam.argtypes = [FPDF_DOCUMENT, FPDF_PAGEOBJECT, FPDF_PAGEOBJECTMARK, FPDF_BYTESTRING, POINTER(None), c_ulong]
    FPDFPageObjMark_SetBlobParam.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPageObjMark_RemoveParam", "cdecl"):
    FPDFPageObjMark_RemoveParam = _libs["pdfium"].get("FPDFPageObjMark_RemoveParam", "cdecl")
    FPDFPageObjMark_RemoveParam.argtypes = [FPDF_PAGEOBJECT, FPDF_PAGEOBJECTMARK, FPDF_BYTESTRING]
    FPDFPageObjMark_RemoveParam.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFImageObj_LoadJpegFile", "cdecl"):
    FPDFImageObj_LoadJpegFile = _libs["pdfium"].get("FPDFImageObj_LoadJpegFile", "cdecl")
    FPDFImageObj_LoadJpegFile.argtypes = [POINTER(FPDF_PAGE), c_int, FPDF_PAGEOBJECT, POINTER(FPDF_FILEACCESS)]
    FPDFImageObj_LoadJpegFile.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFImageObj_LoadJpegFileInline", "cdecl"):
    FPDFImageObj_LoadJpegFileInline = _libs["pdfium"].get("FPDFImageObj_LoadJpegFileInline", "cdecl")
    FPDFImageObj_LoadJpegFileInline.argtypes = [POINTER(FPDF_PAGE), c_int, FPDF_PAGEOBJECT, POINTER(FPDF_FILEACCESS)]
    FPDFImageObj_LoadJpegFileInline.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFImageObj_SetMatrix", "cdecl"):
    FPDFImageObj_SetMatrix = _libs["pdfium"].get("FPDFImageObj_SetMatrix", "cdecl")
    FPDFImageObj_SetMatrix.argtypes = [FPDF_PAGEOBJECT, c_double, c_double, c_double, c_double, c_double, c_double]
    FPDFImageObj_SetMatrix.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFImageObj_SetBitmap", "cdecl"):
    FPDFImageObj_SetBitmap = _libs["pdfium"].get("FPDFImageObj_SetBitmap", "cdecl")
    FPDFImageObj_SetBitmap.argtypes = [POINTER(FPDF_PAGE), c_int, FPDF_PAGEOBJECT, FPDF_BITMAP]
    FPDFImageObj_SetBitmap.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFImageObj_GetBitmap", "cdecl"):
    FPDFImageObj_GetBitmap = _libs["pdfium"].get("FPDFImageObj_GetBitmap", "cdecl")
    FPDFImageObj_GetBitmap.argtypes = [FPDF_PAGEOBJECT]
    FPDFImageObj_GetBitmap.restype = FPDF_BITMAP

if _libs["pdfium"].has("FPDFImageObj_GetRenderedBitmap", "cdecl"):
    FPDFImageObj_GetRenderedBitmap = _libs["pdfium"].get("FPDFImageObj_GetRenderedBitmap", "cdecl")
    FPDFImageObj_GetRenderedBitmap.argtypes = [FPDF_DOCUMENT, FPDF_PAGE, FPDF_PAGEOBJECT]
    FPDFImageObj_GetRenderedBitmap.restype = FPDF_BITMAP

if _libs["pdfium"].has("FPDFImageObj_GetImageDataDecoded", "cdecl"):
    FPDFImageObj_GetImageDataDecoded = _libs["pdfium"].get("FPDFImageObj_GetImageDataDecoded", "cdecl")
    FPDFImageObj_GetImageDataDecoded.argtypes = [FPDF_PAGEOBJECT, POINTER(None), c_ulong]
    FPDFImageObj_GetImageDataDecoded.restype = c_ulong

if _libs["pdfium"].has("FPDFImageObj_GetImageDataRaw", "cdecl"):
    FPDFImageObj_GetImageDataRaw = _libs["pdfium"].get("FPDFImageObj_GetImageDataRaw", "cdecl")
    FPDFImageObj_GetImageDataRaw.argtypes = [FPDF_PAGEOBJECT, POINTER(None), c_ulong]
    FPDFImageObj_GetImageDataRaw.restype = c_ulong

if _libs["pdfium"].has("FPDFImageObj_GetImageFilterCount", "cdecl"):
    FPDFImageObj_GetImageFilterCount = _libs["pdfium"].get("FPDFImageObj_GetImageFilterCount", "cdecl")
    FPDFImageObj_GetImageFilterCount.argtypes = [FPDF_PAGEOBJECT]
    FPDFImageObj_GetImageFilterCount.restype = c_int

if _libs["pdfium"].has("FPDFImageObj_GetImageFilter", "cdecl"):
    FPDFImageObj_GetImageFilter = _libs["pdfium"].get("FPDFImageObj_GetImageFilter", "cdecl")
    FPDFImageObj_GetImageFilter.argtypes = [FPDF_PAGEOBJECT, c_int, POINTER(None), c_ulong]
    FPDFImageObj_GetImageFilter.restype = c_ulong

if _libs["pdfium"].has("FPDFImageObj_GetImageMetadata", "cdecl"):
    FPDFImageObj_GetImageMetadata = _libs["pdfium"].get("FPDFImageObj_GetImageMetadata", "cdecl")
    FPDFImageObj_GetImageMetadata.argtypes = [FPDF_PAGEOBJECT, FPDF_PAGE, POINTER(FPDF_IMAGEOBJ_METADATA)]
    FPDFImageObj_GetImageMetadata.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFImageObj_GetImagePixelSize", "cdecl"):
    FPDFImageObj_GetImagePixelSize = _libs["pdfium"].get("FPDFImageObj_GetImagePixelSize", "cdecl")
    FPDFImageObj_GetImagePixelSize.argtypes = [FPDF_PAGEOBJECT, POINTER(c_uint), POINTER(c_uint)]
    FPDFImageObj_GetImagePixelSize.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPageObj_CreateNewPath", "cdecl"):
    FPDFPageObj_CreateNewPath = _libs["pdfium"].get("FPDFPageObj_CreateNewPath", "cdecl")
    FPDFPageObj_CreateNewPath.argtypes = [c_float, c_float]
    FPDFPageObj_CreateNewPath.restype = FPDF_PAGEOBJECT

if _libs["pdfium"].has("FPDFPageObj_CreateNewRect", "cdecl"):
    FPDFPageObj_CreateNewRect = _libs["pdfium"].get("FPDFPageObj_CreateNewRect", "cdecl")
    FPDFPageObj_CreateNewRect.argtypes = [c_float, c_float, c_float, c_float]
    FPDFPageObj_CreateNewRect.restype = FPDF_PAGEOBJECT

if _libs["pdfium"].has("FPDFPageObj_GetBounds", "cdecl"):
    FPDFPageObj_GetBounds = _libs["pdfium"].get("FPDFPageObj_GetBounds", "cdecl")
    FPDFPageObj_GetBounds.argtypes = [FPDF_PAGEOBJECT, POINTER(c_float), POINTER(c_float), POINTER(c_float), POINTER(c_float)]
    FPDFPageObj_GetBounds.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPageObj_GetRotatedBounds", "cdecl"):
    FPDFPageObj_GetRotatedBounds = _libs["pdfium"].get("FPDFPageObj_GetRotatedBounds", "cdecl")
    FPDFPageObj_GetRotatedBounds.argtypes = [FPDF_PAGEOBJECT, POINTER(FS_QUADPOINTSF)]
    FPDFPageObj_GetRotatedBounds.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPageObj_SetBlendMode", "cdecl"):
    FPDFPageObj_SetBlendMode = _libs["pdfium"].get("FPDFPageObj_SetBlendMode", "cdecl")
    FPDFPageObj_SetBlendMode.argtypes = [FPDF_PAGEOBJECT, FPDF_BYTESTRING]
    FPDFPageObj_SetBlendMode.restype = None

if _libs["pdfium"].has("FPDFPageObj_SetStrokeColor", "cdecl"):
    FPDFPageObj_SetStrokeColor = _libs["pdfium"].get("FPDFPageObj_SetStrokeColor", "cdecl")
    FPDFPageObj_SetStrokeColor.argtypes = [FPDF_PAGEOBJECT, c_uint, c_uint, c_uint, c_uint]
    FPDFPageObj_SetStrokeColor.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPageObj_GetStrokeColor", "cdecl"):
    FPDFPageObj_GetStrokeColor = _libs["pdfium"].get("FPDFPageObj_GetStrokeColor", "cdecl")
    FPDFPageObj_GetStrokeColor.argtypes = [FPDF_PAGEOBJECT, POINTER(c_uint), POINTER(c_uint), POINTER(c_uint), POINTER(c_uint)]
    FPDFPageObj_GetStrokeColor.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPageObj_SetStrokeWidth", "cdecl"):
    FPDFPageObj_SetStrokeWidth = _libs["pdfium"].get("FPDFPageObj_SetStrokeWidth", "cdecl")
    FPDFPageObj_SetStrokeWidth.argtypes = [FPDF_PAGEOBJECT, c_float]
    FPDFPageObj_SetStrokeWidth.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPageObj_GetStrokeWidth", "cdecl"):
    FPDFPageObj_GetStrokeWidth = _libs["pdfium"].get("FPDFPageObj_GetStrokeWidth", "cdecl")
    FPDFPageObj_GetStrokeWidth.argtypes = [FPDF_PAGEOBJECT, POINTER(c_float)]
    FPDFPageObj_GetStrokeWidth.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPageObj_GetLineJoin", "cdecl"):
    FPDFPageObj_GetLineJoin = _libs["pdfium"].get("FPDFPageObj_GetLineJoin", "cdecl")
    FPDFPageObj_GetLineJoin.argtypes = [FPDF_PAGEOBJECT]
    FPDFPageObj_GetLineJoin.restype = c_int

if _libs["pdfium"].has("FPDFPageObj_SetLineJoin", "cdecl"):
    FPDFPageObj_SetLineJoin = _libs["pdfium"].get("FPDFPageObj_SetLineJoin", "cdecl")
    FPDFPageObj_SetLineJoin.argtypes = [FPDF_PAGEOBJECT, c_int]
    FPDFPageObj_SetLineJoin.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPageObj_GetLineCap", "cdecl"):
    FPDFPageObj_GetLineCap = _libs["pdfium"].get("FPDFPageObj_GetLineCap", "cdecl")
    FPDFPageObj_GetLineCap.argtypes = [FPDF_PAGEOBJECT]
    FPDFPageObj_GetLineCap.restype = c_int

if _libs["pdfium"].has("FPDFPageObj_SetLineCap", "cdecl"):
    FPDFPageObj_SetLineCap = _libs["pdfium"].get("FPDFPageObj_SetLineCap", "cdecl")
    FPDFPageObj_SetLineCap.argtypes = [FPDF_PAGEOBJECT, c_int]
    FPDFPageObj_SetLineCap.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPageObj_SetFillColor", "cdecl"):
    FPDFPageObj_SetFillColor = _libs["pdfium"].get("FPDFPageObj_SetFillColor", "cdecl")
    FPDFPageObj_SetFillColor.argtypes = [FPDF_PAGEOBJECT, c_uint, c_uint, c_uint, c_uint]
    FPDFPageObj_SetFillColor.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPageObj_GetFillColor", "cdecl"):
    FPDFPageObj_GetFillColor = _libs["pdfium"].get("FPDFPageObj_GetFillColor", "cdecl")
    FPDFPageObj_GetFillColor.argtypes = [FPDF_PAGEOBJECT, POINTER(c_uint), POINTER(c_uint), POINTER(c_uint), POINTER(c_uint)]
    FPDFPageObj_GetFillColor.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPageObj_GetDashPhase", "cdecl"):
    FPDFPageObj_GetDashPhase = _libs["pdfium"].get("FPDFPageObj_GetDashPhase", "cdecl")
    FPDFPageObj_GetDashPhase.argtypes = [FPDF_PAGEOBJECT, POINTER(c_float)]
    FPDFPageObj_GetDashPhase.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPageObj_SetDashPhase", "cdecl"):
    FPDFPageObj_SetDashPhase = _libs["pdfium"].get("FPDFPageObj_SetDashPhase", "cdecl")
    FPDFPageObj_SetDashPhase.argtypes = [FPDF_PAGEOBJECT, c_float]
    FPDFPageObj_SetDashPhase.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPageObj_GetDashCount", "cdecl"):
    FPDFPageObj_GetDashCount = _libs["pdfium"].get("FPDFPageObj_GetDashCount", "cdecl")
    FPDFPageObj_GetDashCount.argtypes = [FPDF_PAGEOBJECT]
    FPDFPageObj_GetDashCount.restype = c_int

if _libs["pdfium"].has("FPDFPageObj_GetDashArray", "cdecl"):
    FPDFPageObj_GetDashArray = _libs["pdfium"].get("FPDFPageObj_GetDashArray", "cdecl")
    FPDFPageObj_GetDashArray.argtypes = [FPDF_PAGEOBJECT, POINTER(c_float), c_size_t]
    FPDFPageObj_GetDashArray.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPageObj_SetDashArray", "cdecl"):
    FPDFPageObj_SetDashArray = _libs["pdfium"].get("FPDFPageObj_SetDashArray", "cdecl")
    FPDFPageObj_SetDashArray.argtypes = [FPDF_PAGEOBJECT, POINTER(c_float), c_size_t, c_float]
    FPDFPageObj_SetDashArray.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPath_CountSegments", "cdecl"):
    FPDFPath_CountSegments = _libs["pdfium"].get("FPDFPath_CountSegments", "cdecl")
    FPDFPath_CountSegments.argtypes = [FPDF_PAGEOBJECT]
    FPDFPath_CountSegments.restype = c_int

if _libs["pdfium"].has("FPDFPath_GetPathSegment", "cdecl"):
    FPDFPath_GetPathSegment = _libs["pdfium"].get("FPDFPath_GetPathSegment", "cdecl")
    FPDFPath_GetPathSegment.argtypes = [FPDF_PAGEOBJECT, c_int]
    FPDFPath_GetPathSegment.restype = FPDF_PATHSEGMENT

if _libs["pdfium"].has("FPDFPathSegment_GetPoint", "cdecl"):
    FPDFPathSegment_GetPoint = _libs["pdfium"].get("FPDFPathSegment_GetPoint", "cdecl")
    FPDFPathSegment_GetPoint.argtypes = [FPDF_PATHSEGMENT, POINTER(c_float), POINTER(c_float)]
    FPDFPathSegment_GetPoint.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPathSegment_GetType", "cdecl"):
    FPDFPathSegment_GetType = _libs["pdfium"].get("FPDFPathSegment_GetType", "cdecl")
    FPDFPathSegment_GetType.argtypes = [FPDF_PATHSEGMENT]
    FPDFPathSegment_GetType.restype = c_int

if _libs["pdfium"].has("FPDFPathSegment_GetClose", "cdecl"):
    FPDFPathSegment_GetClose = _libs["pdfium"].get("FPDFPathSegment_GetClose", "cdecl")
    FPDFPathSegment_GetClose.argtypes = [FPDF_PATHSEGMENT]
    FPDFPathSegment_GetClose.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPath_MoveTo", "cdecl"):
    FPDFPath_MoveTo = _libs["pdfium"].get("FPDFPath_MoveTo", "cdecl")
    FPDFPath_MoveTo.argtypes = [FPDF_PAGEOBJECT, c_float, c_float]
    FPDFPath_MoveTo.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPath_LineTo", "cdecl"):
    FPDFPath_LineTo = _libs["pdfium"].get("FPDFPath_LineTo", "cdecl")
    FPDFPath_LineTo.argtypes = [FPDF_PAGEOBJECT, c_float, c_float]
    FPDFPath_LineTo.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPath_BezierTo", "cdecl"):
    FPDFPath_BezierTo = _libs["pdfium"].get("FPDFPath_BezierTo", "cdecl")
    FPDFPath_BezierTo.argtypes = [FPDF_PAGEOBJECT, c_float, c_float, c_float, c_float, c_float, c_float]
    FPDFPath_BezierTo.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPath_Close", "cdecl"):
    FPDFPath_Close = _libs["pdfium"].get("FPDFPath_Close", "cdecl")
    FPDFPath_Close.argtypes = [FPDF_PAGEOBJECT]
    FPDFPath_Close.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPath_SetDrawMode", "cdecl"):
    FPDFPath_SetDrawMode = _libs["pdfium"].get("FPDFPath_SetDrawMode", "cdecl")
    FPDFPath_SetDrawMode.argtypes = [FPDF_PAGEOBJECT, c_int, FPDF_BOOL]
    FPDFPath_SetDrawMode.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPath_GetDrawMode", "cdecl"):
    FPDFPath_GetDrawMode = _libs["pdfium"].get("FPDFPath_GetDrawMode", "cdecl")
    FPDFPath_GetDrawMode.argtypes = [FPDF_PAGEOBJECT, POINTER(c_int), POINTER(FPDF_BOOL)]
    FPDFPath_GetDrawMode.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPageObj_NewTextObj", "cdecl"):
    FPDFPageObj_NewTextObj = _libs["pdfium"].get("FPDFPageObj_NewTextObj", "cdecl")
    FPDFPageObj_NewTextObj.argtypes = [FPDF_DOCUMENT, FPDF_BYTESTRING, c_float]
    FPDFPageObj_NewTextObj.restype = FPDF_PAGEOBJECT

if _libs["pdfium"].has("FPDFText_SetText", "cdecl"):
    FPDFText_SetText = _libs["pdfium"].get("FPDFText_SetText", "cdecl")
    FPDFText_SetText.argtypes = [FPDF_PAGEOBJECT, FPDF_WIDESTRING]
    FPDFText_SetText.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFText_SetCharcodes", "cdecl"):
    FPDFText_SetCharcodes = _libs["pdfium"].get("FPDFText_SetCharcodes", "cdecl")
    FPDFText_SetCharcodes.argtypes = [FPDF_PAGEOBJECT, POINTER(uint32_t), c_size_t]
    FPDFText_SetCharcodes.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFText_LoadFont", "cdecl"):
    FPDFText_LoadFont = _libs["pdfium"].get("FPDFText_LoadFont", "cdecl")
    FPDFText_LoadFont.argtypes = [FPDF_DOCUMENT, POINTER(uint8_t), uint32_t, c_int, FPDF_BOOL]
    FPDFText_LoadFont.restype = FPDF_FONT

if _libs["pdfium"].has("FPDFText_LoadStandardFont", "cdecl"):
    FPDFText_LoadStandardFont = _libs["pdfium"].get("FPDFText_LoadStandardFont", "cdecl")
    FPDFText_LoadStandardFont.argtypes = [FPDF_DOCUMENT, FPDF_BYTESTRING]
    FPDFText_LoadStandardFont.restype = FPDF_FONT

if _libs["pdfium"].has("FPDFTextObj_GetFontSize", "cdecl"):
    FPDFTextObj_GetFontSize = _libs["pdfium"].get("FPDFTextObj_GetFontSize", "cdecl")
    FPDFTextObj_GetFontSize.argtypes = [FPDF_PAGEOBJECT, POINTER(c_float)]
    FPDFTextObj_GetFontSize.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFFont_Close", "cdecl"):
    FPDFFont_Close = _libs["pdfium"].get("FPDFFont_Close", "cdecl")
    FPDFFont_Close.argtypes = [FPDF_FONT]
    FPDFFont_Close.restype = None

if _libs["pdfium"].has("FPDFPageObj_CreateTextObj", "cdecl"):
    FPDFPageObj_CreateTextObj = _libs["pdfium"].get("FPDFPageObj_CreateTextObj", "cdecl")
    FPDFPageObj_CreateTextObj.argtypes = [FPDF_DOCUMENT, FPDF_FONT, c_float]
    FPDFPageObj_CreateTextObj.restype = FPDF_PAGEOBJECT

if _libs["pdfium"].has("FPDFTextObj_GetTextRenderMode", "cdecl"):
    FPDFTextObj_GetTextRenderMode = _libs["pdfium"].get("FPDFTextObj_GetTextRenderMode", "cdecl")
    FPDFTextObj_GetTextRenderMode.argtypes = [FPDF_PAGEOBJECT]
    FPDFTextObj_GetTextRenderMode.restype = FPDF_TEXT_RENDERMODE

if _libs["pdfium"].has("FPDFTextObj_SetTextRenderMode", "cdecl"):
    FPDFTextObj_SetTextRenderMode = _libs["pdfium"].get("FPDFTextObj_SetTextRenderMode", "cdecl")
    FPDFTextObj_SetTextRenderMode.argtypes = [FPDF_PAGEOBJECT, FPDF_TEXT_RENDERMODE]
    FPDFTextObj_SetTextRenderMode.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFTextObj_GetText", "cdecl"):
    FPDFTextObj_GetText = _libs["pdfium"].get("FPDFTextObj_GetText", "cdecl")
    FPDFTextObj_GetText.argtypes = [FPDF_PAGEOBJECT, FPDF_TEXTPAGE, POINTER(FPDF_WCHAR), c_ulong]
    FPDFTextObj_GetText.restype = c_ulong

if _libs["pdfium"].has("FPDFTextObj_GetRenderedBitmap", "cdecl"):
    FPDFTextObj_GetRenderedBitmap = _libs["pdfium"].get("FPDFTextObj_GetRenderedBitmap", "cdecl")
    FPDFTextObj_GetRenderedBitmap.argtypes = [FPDF_DOCUMENT, FPDF_PAGE, FPDF_PAGEOBJECT, c_float]
    FPDFTextObj_GetRenderedBitmap.restype = FPDF_BITMAP

if _libs["pdfium"].has("FPDFTextObj_GetFont", "cdecl"):
    FPDFTextObj_GetFont = _libs["pdfium"].get("FPDFTextObj_GetFont", "cdecl")
    FPDFTextObj_GetFont.argtypes = [FPDF_PAGEOBJECT]
    FPDFTextObj_GetFont.restype = FPDF_FONT

if _libs["pdfium"].has("FPDFFont_GetFontName", "cdecl"):
    FPDFFont_GetFontName = _libs["pdfium"].get("FPDFFont_GetFontName", "cdecl")
    FPDFFont_GetFontName.argtypes = [FPDF_FONT, POINTER(c_char), c_ulong]
    FPDFFont_GetFontName.restype = c_ulong

if _libs["pdfium"].has("FPDFFont_GetFontData", "cdecl"):
    FPDFFont_GetFontData = _libs["pdfium"].get("FPDFFont_GetFontData", "cdecl")
    FPDFFont_GetFontData.argtypes = [FPDF_FONT, POINTER(uint8_t), c_size_t, POINTER(c_size_t)]
    FPDFFont_GetFontData.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFFont_GetIsEmbedded", "cdecl"):
    FPDFFont_GetIsEmbedded = _libs["pdfium"].get("FPDFFont_GetIsEmbedded", "cdecl")
    FPDFFont_GetIsEmbedded.argtypes = [FPDF_FONT]
    FPDFFont_GetIsEmbedded.restype = c_int

if _libs["pdfium"].has("FPDFFont_GetFlags", "cdecl"):
    FPDFFont_GetFlags = _libs["pdfium"].get("FPDFFont_GetFlags", "cdecl")
    FPDFFont_GetFlags.argtypes = [FPDF_FONT]
    FPDFFont_GetFlags.restype = c_int

if _libs["pdfium"].has("FPDFFont_GetWeight", "cdecl"):
    FPDFFont_GetWeight = _libs["pdfium"].get("FPDFFont_GetWeight", "cdecl")
    FPDFFont_GetWeight.argtypes = [FPDF_FONT]
    FPDFFont_GetWeight.restype = c_int

if _libs["pdfium"].has("FPDFFont_GetItalicAngle", "cdecl"):
    FPDFFont_GetItalicAngle = _libs["pdfium"].get("FPDFFont_GetItalicAngle", "cdecl")
    FPDFFont_GetItalicAngle.argtypes = [FPDF_FONT, POINTER(c_int)]
    FPDFFont_GetItalicAngle.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFFont_GetAscent", "cdecl"):
    FPDFFont_GetAscent = _libs["pdfium"].get("FPDFFont_GetAscent", "cdecl")
    FPDFFont_GetAscent.argtypes = [FPDF_FONT, c_float, POINTER(c_float)]
    FPDFFont_GetAscent.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFFont_GetDescent", "cdecl"):
    FPDFFont_GetDescent = _libs["pdfium"].get("FPDFFont_GetDescent", "cdecl")
    FPDFFont_GetDescent.argtypes = [FPDF_FONT, c_float, POINTER(c_float)]
    FPDFFont_GetDescent.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFFont_GetGlyphWidth", "cdecl"):
    FPDFFont_GetGlyphWidth = _libs["pdfium"].get("FPDFFont_GetGlyphWidth", "cdecl")
    FPDFFont_GetGlyphWidth.argtypes = [FPDF_FONT, uint32_t, c_float, POINTER(c_float)]
    FPDFFont_GetGlyphWidth.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFFont_GetGlyphPath", "cdecl"):
    FPDFFont_GetGlyphPath = _libs["pdfium"].get("FPDFFont_GetGlyphPath", "cdecl")
    FPDFFont_GetGlyphPath.argtypes = [FPDF_FONT, uint32_t, c_float]
    FPDFFont_GetGlyphPath.restype = FPDF_GLYPHPATH

if _libs["pdfium"].has("FPDFGlyphPath_CountGlyphSegments", "cdecl"):
    FPDFGlyphPath_CountGlyphSegments = _libs["pdfium"].get("FPDFGlyphPath_CountGlyphSegments", "cdecl")
    FPDFGlyphPath_CountGlyphSegments.argtypes = [FPDF_GLYPHPATH]
    FPDFGlyphPath_CountGlyphSegments.restype = c_int

if _libs["pdfium"].has("FPDFGlyphPath_GetGlyphPathSegment", "cdecl"):
    FPDFGlyphPath_GetGlyphPathSegment = _libs["pdfium"].get("FPDFGlyphPath_GetGlyphPathSegment", "cdecl")
    FPDFGlyphPath_GetGlyphPathSegment.argtypes = [FPDF_GLYPHPATH, c_int]
    FPDFGlyphPath_GetGlyphPathSegment.restype = FPDF_PATHSEGMENT

if _libs["pdfium"].has("FPDFFormObj_CountObjects", "cdecl"):
    FPDFFormObj_CountObjects = _libs["pdfium"].get("FPDFFormObj_CountObjects", "cdecl")
    FPDFFormObj_CountObjects.argtypes = [FPDF_PAGEOBJECT]
    FPDFFormObj_CountObjects.restype = c_int

if _libs["pdfium"].has("FPDFFormObj_GetObject", "cdecl"):
    FPDFFormObj_GetObject = _libs["pdfium"].get("FPDFFormObj_GetObject", "cdecl")
    FPDFFormObj_GetObject.argtypes = [FPDF_PAGEOBJECT, c_ulong]
    FPDFFormObj_GetObject.restype = FPDF_PAGEOBJECT
time_t = __time_t

class struct_tm(Structure):
    pass
struct_tm.__slots__ = [
    'tm_sec',
    'tm_min',
    'tm_hour',
    'tm_mday',
    'tm_mon',
    'tm_year',
    'tm_wday',
    'tm_yday',
    'tm_isdst',
    'tm_gmtoff',
    'tm_zone',
]
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

class struct__UNSUPPORT_INFO(Structure):
    pass
struct__UNSUPPORT_INFO.__slots__ = [
    'version',
    'FSDK_UnSupport_Handler',
]
struct__UNSUPPORT_INFO._fields_ = [
    ('version', c_int),
    ('FSDK_UnSupport_Handler', CFUNCTYPE(UNCHECKED(None), POINTER(struct__UNSUPPORT_INFO), c_int)),
]
UNSUPPORT_INFO = struct__UNSUPPORT_INFO

if _libs["pdfium"].has("FSDK_SetUnSpObjProcessHandler", "cdecl"):
    FSDK_SetUnSpObjProcessHandler = _libs["pdfium"].get("FSDK_SetUnSpObjProcessHandler", "cdecl")
    FSDK_SetUnSpObjProcessHandler.argtypes = [POINTER(UNSUPPORT_INFO)]
    FSDK_SetUnSpObjProcessHandler.restype = FPDF_BOOL

if _libs["pdfium"].has("FSDK_SetTimeFunction", "cdecl"):
    FSDK_SetTimeFunction = _libs["pdfium"].get("FSDK_SetTimeFunction", "cdecl")
    FSDK_SetTimeFunction.argtypes = [CFUNCTYPE(UNCHECKED(time_t), )]
    FSDK_SetTimeFunction.restype = None

if _libs["pdfium"].has("FSDK_SetLocaltimeFunction", "cdecl"):
    FSDK_SetLocaltimeFunction = _libs["pdfium"].get("FSDK_SetLocaltimeFunction", "cdecl")
    FSDK_SetLocaltimeFunction.argtypes = [CFUNCTYPE(UNCHECKED(POINTER(struct_tm)), POINTER(time_t))]
    FSDK_SetLocaltimeFunction.restype = None

if _libs["pdfium"].has("FPDFDoc_GetPageMode", "cdecl"):
    FPDFDoc_GetPageMode = _libs["pdfium"].get("FPDFDoc_GetPageMode", "cdecl")
    FPDFDoc_GetPageMode.argtypes = [FPDF_DOCUMENT]
    FPDFDoc_GetPageMode.restype = c_int

if _libs["pdfium"].has("FPDFPage_Flatten", "cdecl"):
    FPDFPage_Flatten = _libs["pdfium"].get("FPDFPage_Flatten", "cdecl")
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

if _libs["pdfium"].has("FPDFDoc_GetJavaScriptActionCount", "cdecl"):
    FPDFDoc_GetJavaScriptActionCount = _libs["pdfium"].get("FPDFDoc_GetJavaScriptActionCount", "cdecl")
    FPDFDoc_GetJavaScriptActionCount.argtypes = [FPDF_DOCUMENT]
    FPDFDoc_GetJavaScriptActionCount.restype = c_int

if _libs["pdfium"].has("FPDFDoc_GetJavaScriptAction", "cdecl"):
    FPDFDoc_GetJavaScriptAction = _libs["pdfium"].get("FPDFDoc_GetJavaScriptAction", "cdecl")
    FPDFDoc_GetJavaScriptAction.argtypes = [FPDF_DOCUMENT, c_int]
    FPDFDoc_GetJavaScriptAction.restype = FPDF_JAVASCRIPT_ACTION

if _libs["pdfium"].has("FPDFDoc_CloseJavaScriptAction", "cdecl"):
    FPDFDoc_CloseJavaScriptAction = _libs["pdfium"].get("FPDFDoc_CloseJavaScriptAction", "cdecl")
    FPDFDoc_CloseJavaScriptAction.argtypes = [FPDF_JAVASCRIPT_ACTION]
    FPDFDoc_CloseJavaScriptAction.restype = None

if _libs["pdfium"].has("FPDFJavaScriptAction_GetName", "cdecl"):
    FPDFJavaScriptAction_GetName = _libs["pdfium"].get("FPDFJavaScriptAction_GetName", "cdecl")
    FPDFJavaScriptAction_GetName.argtypes = [FPDF_JAVASCRIPT_ACTION, POINTER(FPDF_WCHAR), c_ulong]
    FPDFJavaScriptAction_GetName.restype = c_ulong

if _libs["pdfium"].has("FPDFJavaScriptAction_GetScript", "cdecl"):
    FPDFJavaScriptAction_GetScript = _libs["pdfium"].get("FPDFJavaScriptAction_GetScript", "cdecl")
    FPDFJavaScriptAction_GetScript.argtypes = [FPDF_JAVASCRIPT_ACTION, POINTER(FPDF_WCHAR), c_ulong]
    FPDFJavaScriptAction_GetScript.restype = c_ulong

if _libs["pdfium"].has("FPDF_ImportPagesByIndex", "cdecl"):
    FPDF_ImportPagesByIndex = _libs["pdfium"].get("FPDF_ImportPagesByIndex", "cdecl")
    FPDF_ImportPagesByIndex.argtypes = [FPDF_DOCUMENT, FPDF_DOCUMENT, POINTER(c_int), c_ulong, c_int]
    FPDF_ImportPagesByIndex.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDF_ImportPages", "cdecl"):
    FPDF_ImportPages = _libs["pdfium"].get("FPDF_ImportPages", "cdecl")
    FPDF_ImportPages.argtypes = [FPDF_DOCUMENT, FPDF_DOCUMENT, FPDF_BYTESTRING, c_int]
    FPDF_ImportPages.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDF_ImportNPagesToOne", "cdecl"):
    FPDF_ImportNPagesToOne = _libs["pdfium"].get("FPDF_ImportNPagesToOne", "cdecl")
    FPDF_ImportNPagesToOne.argtypes = [FPDF_DOCUMENT, c_float, c_float, c_size_t, c_size_t]
    FPDF_ImportNPagesToOne.restype = FPDF_DOCUMENT

if _libs["pdfium"].has("FPDF_NewXObjectFromPage", "cdecl"):
    FPDF_NewXObjectFromPage = _libs["pdfium"].get("FPDF_NewXObjectFromPage", "cdecl")
    FPDF_NewXObjectFromPage.argtypes = [FPDF_DOCUMENT, FPDF_DOCUMENT, c_int]
    FPDF_NewXObjectFromPage.restype = FPDF_XOBJECT

if _libs["pdfium"].has("FPDF_CloseXObject", "cdecl"):
    FPDF_CloseXObject = _libs["pdfium"].get("FPDF_CloseXObject", "cdecl")
    FPDF_CloseXObject.argtypes = [FPDF_XOBJECT]
    FPDF_CloseXObject.restype = None

if _libs["pdfium"].has("FPDF_NewFormObjectFromXObject", "cdecl"):
    FPDF_NewFormObjectFromXObject = _libs["pdfium"].get("FPDF_NewFormObjectFromXObject", "cdecl")
    FPDF_NewFormObjectFromXObject.argtypes = [FPDF_XOBJECT]
    FPDF_NewFormObjectFromXObject.restype = FPDF_PAGEOBJECT

if _libs["pdfium"].has("FPDF_CopyViewerPreferences", "cdecl"):
    FPDF_CopyViewerPreferences = _libs["pdfium"].get("FPDF_CopyViewerPreferences", "cdecl")
    FPDF_CopyViewerPreferences.argtypes = [FPDF_DOCUMENT, FPDF_DOCUMENT]
    FPDF_CopyViewerPreferences.restype = FPDF_BOOL

class struct__IFSDK_PAUSE(Structure):
    pass
struct__IFSDK_PAUSE.__slots__ = [
    'version',
    'NeedToPauseNow',
    'user',
]
struct__IFSDK_PAUSE._fields_ = [
    ('version', c_int),
    ('NeedToPauseNow', CFUNCTYPE(UNCHECKED(FPDF_BOOL), POINTER(struct__IFSDK_PAUSE))),
    ('user', POINTER(None)),
]
IFSDK_PAUSE = struct__IFSDK_PAUSE

if _libs["pdfium"].has("FPDF_RenderPageBitmapWithColorScheme_Start", "cdecl"):
    FPDF_RenderPageBitmapWithColorScheme_Start = _libs["pdfium"].get("FPDF_RenderPageBitmapWithColorScheme_Start", "cdecl")
    FPDF_RenderPageBitmapWithColorScheme_Start.argtypes = [FPDF_BITMAP, FPDF_PAGE, c_int, c_int, c_int, c_int, c_int, c_int, POINTER(FPDF_COLORSCHEME), POINTER(IFSDK_PAUSE)]
    FPDF_RenderPageBitmapWithColorScheme_Start.restype = c_int

if _libs["pdfium"].has("FPDF_RenderPageBitmap_Start", "cdecl"):
    FPDF_RenderPageBitmap_Start = _libs["pdfium"].get("FPDF_RenderPageBitmap_Start", "cdecl")
    FPDF_RenderPageBitmap_Start.argtypes = [FPDF_BITMAP, FPDF_PAGE, c_int, c_int, c_int, c_int, c_int, c_int, POINTER(IFSDK_PAUSE)]
    FPDF_RenderPageBitmap_Start.restype = c_int

if _libs["pdfium"].has("FPDF_RenderPage_Continue", "cdecl"):
    FPDF_RenderPage_Continue = _libs["pdfium"].get("FPDF_RenderPage_Continue", "cdecl")
    FPDF_RenderPage_Continue.argtypes = [FPDF_PAGE, POINTER(IFSDK_PAUSE)]
    FPDF_RenderPage_Continue.restype = c_int

if _libs["pdfium"].has("FPDF_RenderPage_Close", "cdecl"):
    FPDF_RenderPage_Close = _libs["pdfium"].get("FPDF_RenderPage_Close", "cdecl")
    FPDF_RenderPage_Close.argtypes = [FPDF_PAGE]
    FPDF_RenderPage_Close.restype = None

class struct_FPDF_FILEWRITE_(Structure):
    pass
struct_FPDF_FILEWRITE_.__slots__ = [
    'version',
    'WriteBlock',
]
struct_FPDF_FILEWRITE_._fields_ = [
    ('version', c_int),
    ('WriteBlock', CFUNCTYPE(UNCHECKED(c_int), POINTER(struct_FPDF_FILEWRITE_), POINTER(None), c_ulong)),
]
FPDF_FILEWRITE = struct_FPDF_FILEWRITE_

if _libs["pdfium"].has("FPDF_SaveAsCopy", "cdecl"):
    FPDF_SaveAsCopy = _libs["pdfium"].get("FPDF_SaveAsCopy", "cdecl")
    FPDF_SaveAsCopy.argtypes = [FPDF_DOCUMENT, POINTER(FPDF_FILEWRITE), FPDF_DWORD]
    FPDF_SaveAsCopy.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDF_SaveWithVersion", "cdecl"):
    FPDF_SaveWithVersion = _libs["pdfium"].get("FPDF_SaveWithVersion", "cdecl")
    FPDF_SaveWithVersion.argtypes = [FPDF_DOCUMENT, POINTER(FPDF_FILEWRITE), FPDF_DWORD, c_int]
    FPDF_SaveWithVersion.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFText_GetCharIndexFromTextIndex", "cdecl"):
    FPDFText_GetCharIndexFromTextIndex = _libs["pdfium"].get("FPDFText_GetCharIndexFromTextIndex", "cdecl")
    FPDFText_GetCharIndexFromTextIndex.argtypes = [FPDF_TEXTPAGE, c_int]
    FPDFText_GetCharIndexFromTextIndex.restype = c_int

if _libs["pdfium"].has("FPDFText_GetTextIndexFromCharIndex", "cdecl"):
    FPDFText_GetTextIndexFromCharIndex = _libs["pdfium"].get("FPDFText_GetTextIndexFromCharIndex", "cdecl")
    FPDFText_GetTextIndexFromCharIndex.argtypes = [FPDF_TEXTPAGE, c_int]
    FPDFText_GetTextIndexFromCharIndex.restype = c_int

if _libs["pdfium"].has("FPDF_GetSignatureCount", "cdecl"):
    FPDF_GetSignatureCount = _libs["pdfium"].get("FPDF_GetSignatureCount", "cdecl")
    FPDF_GetSignatureCount.argtypes = [FPDF_DOCUMENT]
    FPDF_GetSignatureCount.restype = c_int

if _libs["pdfium"].has("FPDF_GetSignatureObject", "cdecl"):
    FPDF_GetSignatureObject = _libs["pdfium"].get("FPDF_GetSignatureObject", "cdecl")
    FPDF_GetSignatureObject.argtypes = [FPDF_DOCUMENT, c_int]
    FPDF_GetSignatureObject.restype = FPDF_SIGNATURE

if _libs["pdfium"].has("FPDFSignatureObj_GetContents", "cdecl"):
    FPDFSignatureObj_GetContents = _libs["pdfium"].get("FPDFSignatureObj_GetContents", "cdecl")
    FPDFSignatureObj_GetContents.argtypes = [FPDF_SIGNATURE, POINTER(None), c_ulong]
    FPDFSignatureObj_GetContents.restype = c_ulong

if _libs["pdfium"].has("FPDFSignatureObj_GetByteRange", "cdecl"):
    FPDFSignatureObj_GetByteRange = _libs["pdfium"].get("FPDFSignatureObj_GetByteRange", "cdecl")
    FPDFSignatureObj_GetByteRange.argtypes = [FPDF_SIGNATURE, POINTER(c_int), c_ulong]
    FPDFSignatureObj_GetByteRange.restype = c_ulong

if _libs["pdfium"].has("FPDFSignatureObj_GetSubFilter", "cdecl"):
    FPDFSignatureObj_GetSubFilter = _libs["pdfium"].get("FPDFSignatureObj_GetSubFilter", "cdecl")
    FPDFSignatureObj_GetSubFilter.argtypes = [FPDF_SIGNATURE, POINTER(c_char), c_ulong]
    FPDFSignatureObj_GetSubFilter.restype = c_ulong

if _libs["pdfium"].has("FPDFSignatureObj_GetReason", "cdecl"):
    FPDFSignatureObj_GetReason = _libs["pdfium"].get("FPDFSignatureObj_GetReason", "cdecl")
    FPDFSignatureObj_GetReason.argtypes = [FPDF_SIGNATURE, POINTER(None), c_ulong]
    FPDFSignatureObj_GetReason.restype = c_ulong

if _libs["pdfium"].has("FPDFSignatureObj_GetTime", "cdecl"):
    FPDFSignatureObj_GetTime = _libs["pdfium"].get("FPDFSignatureObj_GetTime", "cdecl")
    FPDFSignatureObj_GetTime.argtypes = [FPDF_SIGNATURE, POINTER(c_char), c_ulong]
    FPDFSignatureObj_GetTime.restype = c_ulong

if _libs["pdfium"].has("FPDFSignatureObj_GetDocMDPPermission", "cdecl"):
    FPDFSignatureObj_GetDocMDPPermission = _libs["pdfium"].get("FPDFSignatureObj_GetDocMDPPermission", "cdecl")
    FPDFSignatureObj_GetDocMDPPermission.argtypes = [FPDF_SIGNATURE]
    FPDFSignatureObj_GetDocMDPPermission.restype = c_uint

if _libs["pdfium"].has("FPDF_StructTree_GetForPage", "cdecl"):
    FPDF_StructTree_GetForPage = _libs["pdfium"].get("FPDF_StructTree_GetForPage", "cdecl")
    FPDF_StructTree_GetForPage.argtypes = [FPDF_PAGE]
    FPDF_StructTree_GetForPage.restype = FPDF_STRUCTTREE

if _libs["pdfium"].has("FPDF_StructTree_Close", "cdecl"):
    FPDF_StructTree_Close = _libs["pdfium"].get("FPDF_StructTree_Close", "cdecl")
    FPDF_StructTree_Close.argtypes = [FPDF_STRUCTTREE]
    FPDF_StructTree_Close.restype = None

if _libs["pdfium"].has("FPDF_StructTree_CountChildren", "cdecl"):
    FPDF_StructTree_CountChildren = _libs["pdfium"].get("FPDF_StructTree_CountChildren", "cdecl")
    FPDF_StructTree_CountChildren.argtypes = [FPDF_STRUCTTREE]
    FPDF_StructTree_CountChildren.restype = c_int

if _libs["pdfium"].has("FPDF_StructTree_GetChildAtIndex", "cdecl"):
    FPDF_StructTree_GetChildAtIndex = _libs["pdfium"].get("FPDF_StructTree_GetChildAtIndex", "cdecl")
    FPDF_StructTree_GetChildAtIndex.argtypes = [FPDF_STRUCTTREE, c_int]
    FPDF_StructTree_GetChildAtIndex.restype = FPDF_STRUCTELEMENT

if _libs["pdfium"].has("FPDF_StructElement_GetAltText", "cdecl"):
    FPDF_StructElement_GetAltText = _libs["pdfium"].get("FPDF_StructElement_GetAltText", "cdecl")
    FPDF_StructElement_GetAltText.argtypes = [FPDF_STRUCTELEMENT, POINTER(None), c_ulong]
    FPDF_StructElement_GetAltText.restype = c_ulong

if _libs["pdfium"].has("FPDF_StructElement_GetActualText", "cdecl"):
    FPDF_StructElement_GetActualText = _libs["pdfium"].get("FPDF_StructElement_GetActualText", "cdecl")
    FPDF_StructElement_GetActualText.argtypes = [FPDF_STRUCTELEMENT, POINTER(None), c_ulong]
    FPDF_StructElement_GetActualText.restype = c_ulong

if _libs["pdfium"].has("FPDF_StructElement_GetID", "cdecl"):
    FPDF_StructElement_GetID = _libs["pdfium"].get("FPDF_StructElement_GetID", "cdecl")
    FPDF_StructElement_GetID.argtypes = [FPDF_STRUCTELEMENT, POINTER(None), c_ulong]
    FPDF_StructElement_GetID.restype = c_ulong

if _libs["pdfium"].has("FPDF_StructElement_GetLang", "cdecl"):
    FPDF_StructElement_GetLang = _libs["pdfium"].get("FPDF_StructElement_GetLang", "cdecl")
    FPDF_StructElement_GetLang.argtypes = [FPDF_STRUCTELEMENT, POINTER(None), c_ulong]
    FPDF_StructElement_GetLang.restype = c_ulong

if _libs["pdfium"].has("FPDF_StructElement_GetStringAttribute", "cdecl"):
    FPDF_StructElement_GetStringAttribute = _libs["pdfium"].get("FPDF_StructElement_GetStringAttribute", "cdecl")
    FPDF_StructElement_GetStringAttribute.argtypes = [FPDF_STRUCTELEMENT, FPDF_BYTESTRING, POINTER(None), c_ulong]
    FPDF_StructElement_GetStringAttribute.restype = c_ulong

if _libs["pdfium"].has("FPDF_StructElement_GetMarkedContentID", "cdecl"):
    FPDF_StructElement_GetMarkedContentID = _libs["pdfium"].get("FPDF_StructElement_GetMarkedContentID", "cdecl")
    FPDF_StructElement_GetMarkedContentID.argtypes = [FPDF_STRUCTELEMENT]
    FPDF_StructElement_GetMarkedContentID.restype = c_int

if _libs["pdfium"].has("FPDF_StructElement_GetType", "cdecl"):
    FPDF_StructElement_GetType = _libs["pdfium"].get("FPDF_StructElement_GetType", "cdecl")
    FPDF_StructElement_GetType.argtypes = [FPDF_STRUCTELEMENT, POINTER(None), c_ulong]
    FPDF_StructElement_GetType.restype = c_ulong

if _libs["pdfium"].has("FPDF_StructElement_GetObjType", "cdecl"):
    FPDF_StructElement_GetObjType = _libs["pdfium"].get("FPDF_StructElement_GetObjType", "cdecl")
    FPDF_StructElement_GetObjType.argtypes = [FPDF_STRUCTELEMENT, POINTER(None), c_ulong]
    FPDF_StructElement_GetObjType.restype = c_ulong

if _libs["pdfium"].has("FPDF_StructElement_GetTitle", "cdecl"):
    FPDF_StructElement_GetTitle = _libs["pdfium"].get("FPDF_StructElement_GetTitle", "cdecl")
    FPDF_StructElement_GetTitle.argtypes = [FPDF_STRUCTELEMENT, POINTER(None), c_ulong]
    FPDF_StructElement_GetTitle.restype = c_ulong

if _libs["pdfium"].has("FPDF_StructElement_CountChildren", "cdecl"):
    FPDF_StructElement_CountChildren = _libs["pdfium"].get("FPDF_StructElement_CountChildren", "cdecl")
    FPDF_StructElement_CountChildren.argtypes = [FPDF_STRUCTELEMENT]
    FPDF_StructElement_CountChildren.restype = c_int

if _libs["pdfium"].has("FPDF_StructElement_GetChildAtIndex", "cdecl"):
    FPDF_StructElement_GetChildAtIndex = _libs["pdfium"].get("FPDF_StructElement_GetChildAtIndex", "cdecl")
    FPDF_StructElement_GetChildAtIndex.argtypes = [FPDF_STRUCTELEMENT, c_int]
    FPDF_StructElement_GetChildAtIndex.restype = FPDF_STRUCTELEMENT

if _libs["pdfium"].has("FPDF_StructElement_GetParent", "cdecl"):
    FPDF_StructElement_GetParent = _libs["pdfium"].get("FPDF_StructElement_GetParent", "cdecl")
    FPDF_StructElement_GetParent.argtypes = [FPDF_STRUCTELEMENT]
    FPDF_StructElement_GetParent.restype = FPDF_STRUCTELEMENT

if _libs["pdfium"].has("FPDF_StructElement_GetAttributeCount", "cdecl"):
    FPDF_StructElement_GetAttributeCount = _libs["pdfium"].get("FPDF_StructElement_GetAttributeCount", "cdecl")
    FPDF_StructElement_GetAttributeCount.argtypes = [FPDF_STRUCTELEMENT]
    FPDF_StructElement_GetAttributeCount.restype = c_int

if _libs["pdfium"].has("FPDF_StructElement_GetAttributeAtIndex", "cdecl"):
    FPDF_StructElement_GetAttributeAtIndex = _libs["pdfium"].get("FPDF_StructElement_GetAttributeAtIndex", "cdecl")
    FPDF_StructElement_GetAttributeAtIndex.argtypes = [FPDF_STRUCTELEMENT, c_int]
    FPDF_StructElement_GetAttributeAtIndex.restype = FPDF_STRUCTELEMENT_ATTR

if _libs["pdfium"].has("FPDF_StructElement_Attr_GetCount", "cdecl"):
    FPDF_StructElement_Attr_GetCount = _libs["pdfium"].get("FPDF_StructElement_Attr_GetCount", "cdecl")
    FPDF_StructElement_Attr_GetCount.argtypes = [FPDF_STRUCTELEMENT_ATTR]
    FPDF_StructElement_Attr_GetCount.restype = c_int

if _libs["pdfium"].has("FPDF_StructElement_Attr_GetName", "cdecl"):
    FPDF_StructElement_Attr_GetName = _libs["pdfium"].get("FPDF_StructElement_Attr_GetName", "cdecl")
    FPDF_StructElement_Attr_GetName.argtypes = [FPDF_STRUCTELEMENT_ATTR, c_int, POINTER(None), c_ulong, POINTER(c_ulong)]
    FPDF_StructElement_Attr_GetName.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDF_StructElement_Attr_GetType", "cdecl"):
    FPDF_StructElement_Attr_GetType = _libs["pdfium"].get("FPDF_StructElement_Attr_GetType", "cdecl")
    FPDF_StructElement_Attr_GetType.argtypes = [FPDF_STRUCTELEMENT_ATTR, FPDF_BYTESTRING]
    FPDF_StructElement_Attr_GetType.restype = FPDF_OBJECT_TYPE

if _libs["pdfium"].has("FPDF_StructElement_Attr_GetBooleanValue", "cdecl"):
    FPDF_StructElement_Attr_GetBooleanValue = _libs["pdfium"].get("FPDF_StructElement_Attr_GetBooleanValue", "cdecl")
    FPDF_StructElement_Attr_GetBooleanValue.argtypes = [FPDF_STRUCTELEMENT_ATTR, FPDF_BYTESTRING, POINTER(FPDF_BOOL)]
    FPDF_StructElement_Attr_GetBooleanValue.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDF_StructElement_Attr_GetNumberValue", "cdecl"):
    FPDF_StructElement_Attr_GetNumberValue = _libs["pdfium"].get("FPDF_StructElement_Attr_GetNumberValue", "cdecl")
    FPDF_StructElement_Attr_GetNumberValue.argtypes = [FPDF_STRUCTELEMENT_ATTR, FPDF_BYTESTRING, POINTER(c_float)]
    FPDF_StructElement_Attr_GetNumberValue.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDF_StructElement_Attr_GetStringValue", "cdecl"):
    FPDF_StructElement_Attr_GetStringValue = _libs["pdfium"].get("FPDF_StructElement_Attr_GetStringValue", "cdecl")
    FPDF_StructElement_Attr_GetStringValue.argtypes = [FPDF_STRUCTELEMENT_ATTR, FPDF_BYTESTRING, POINTER(None), c_ulong, POINTER(c_ulong)]
    FPDF_StructElement_Attr_GetStringValue.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDF_StructElement_Attr_GetBlobValue", "cdecl"):
    FPDF_StructElement_Attr_GetBlobValue = _libs["pdfium"].get("FPDF_StructElement_Attr_GetBlobValue", "cdecl")
    FPDF_StructElement_Attr_GetBlobValue.argtypes = [FPDF_STRUCTELEMENT_ATTR, FPDF_BYTESTRING, POINTER(None), c_ulong, POINTER(c_ulong)]
    FPDF_StructElement_Attr_GetBlobValue.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDF_StructElement_GetMarkedContentIdCount", "cdecl"):
    FPDF_StructElement_GetMarkedContentIdCount = _libs["pdfium"].get("FPDF_StructElement_GetMarkedContentIdCount", "cdecl")
    FPDF_StructElement_GetMarkedContentIdCount.argtypes = [FPDF_STRUCTELEMENT]
    FPDF_StructElement_GetMarkedContentIdCount.restype = c_int

if _libs["pdfium"].has("FPDF_StructElement_GetMarkedContentIdAtIndex", "cdecl"):
    FPDF_StructElement_GetMarkedContentIdAtIndex = _libs["pdfium"].get("FPDF_StructElement_GetMarkedContentIdAtIndex", "cdecl")
    FPDF_StructElement_GetMarkedContentIdAtIndex.argtypes = [FPDF_STRUCTELEMENT, c_int]
    FPDF_StructElement_GetMarkedContentIdAtIndex.restype = c_int

class struct__FPDF_SYSFONTINFO(Structure):
    pass
struct__FPDF_SYSFONTINFO.__slots__ = [
    'version',
    'Release',
    'EnumFonts',
    'MapFont',
    'GetFont',
    'GetFontData',
    'GetFaceName',
    'GetFontCharset',
    'DeleteFont',
]
struct__FPDF_SYSFONTINFO._fields_ = [
    ('version', c_int),
    ('Release', CFUNCTYPE(UNCHECKED(None), POINTER(struct__FPDF_SYSFONTINFO))),
    ('EnumFonts', CFUNCTYPE(UNCHECKED(None), POINTER(struct__FPDF_SYSFONTINFO), POINTER(None))),
    ('MapFont', CFUNCTYPE(UNCHECKED(POINTER(c_ubyte)), POINTER(struct__FPDF_SYSFONTINFO), c_int, FPDF_BOOL, c_int, c_int, POINTER(c_char), POINTER(FPDF_BOOL))),
    ('GetFont', CFUNCTYPE(UNCHECKED(POINTER(c_ubyte)), POINTER(struct__FPDF_SYSFONTINFO), POINTER(c_char))),
    ('GetFontData', CFUNCTYPE(UNCHECKED(c_ulong), POINTER(struct__FPDF_SYSFONTINFO), POINTER(None), c_uint, POINTER(c_ubyte), c_ulong)),
    ('GetFaceName', CFUNCTYPE(UNCHECKED(c_ulong), POINTER(struct__FPDF_SYSFONTINFO), POINTER(None), POINTER(c_char), c_ulong)),
    ('GetFontCharset', CFUNCTYPE(UNCHECKED(c_int), POINTER(struct__FPDF_SYSFONTINFO), POINTER(None))),
    ('DeleteFont', CFUNCTYPE(UNCHECKED(None), POINTER(struct__FPDF_SYSFONTINFO), POINTER(None))),
]
FPDF_SYSFONTINFO = struct__FPDF_SYSFONTINFO

class struct_FPDF_CharsetFontMap_(Structure):
    pass
struct_FPDF_CharsetFontMap_.__slots__ = [
    'charset',
    'fontname',
]
struct_FPDF_CharsetFontMap_._fields_ = [
    ('charset', c_int),
    ('fontname', POINTER(c_char)),
]
FPDF_CharsetFontMap = struct_FPDF_CharsetFontMap_

if _libs["pdfium"].has("FPDF_GetDefaultTTFMap", "cdecl"):
    FPDF_GetDefaultTTFMap = _libs["pdfium"].get("FPDF_GetDefaultTTFMap", "cdecl")
    FPDF_GetDefaultTTFMap.argtypes = []
    FPDF_GetDefaultTTFMap.restype = POINTER(FPDF_CharsetFontMap)

if _libs["pdfium"].has("FPDF_AddInstalledFont", "cdecl"):
    FPDF_AddInstalledFont = _libs["pdfium"].get("FPDF_AddInstalledFont", "cdecl")
    FPDF_AddInstalledFont.argtypes = [POINTER(None), POINTER(c_char), c_int]
    FPDF_AddInstalledFont.restype = None

if _libs["pdfium"].has("FPDF_SetSystemFontInfo", "cdecl"):
    FPDF_SetSystemFontInfo = _libs["pdfium"].get("FPDF_SetSystemFontInfo", "cdecl")
    FPDF_SetSystemFontInfo.argtypes = [POINTER(FPDF_SYSFONTINFO)]
    FPDF_SetSystemFontInfo.restype = None

if _libs["pdfium"].has("FPDF_GetDefaultSystemFontInfo", "cdecl"):
    FPDF_GetDefaultSystemFontInfo = _libs["pdfium"].get("FPDF_GetDefaultSystemFontInfo", "cdecl")
    FPDF_GetDefaultSystemFontInfo.argtypes = []
    FPDF_GetDefaultSystemFontInfo.restype = POINTER(FPDF_SYSFONTINFO)

if _libs["pdfium"].has("FPDF_FreeDefaultSystemFontInfo", "cdecl"):
    FPDF_FreeDefaultSystemFontInfo = _libs["pdfium"].get("FPDF_FreeDefaultSystemFontInfo", "cdecl")
    FPDF_FreeDefaultSystemFontInfo.argtypes = [POINTER(FPDF_SYSFONTINFO)]
    FPDF_FreeDefaultSystemFontInfo.restype = None

if _libs["pdfium"].has("FPDFText_LoadPage", "cdecl"):
    FPDFText_LoadPage = _libs["pdfium"].get("FPDFText_LoadPage", "cdecl")
    FPDFText_LoadPage.argtypes = [FPDF_PAGE]
    FPDFText_LoadPage.restype = FPDF_TEXTPAGE

if _libs["pdfium"].has("FPDFText_ClosePage", "cdecl"):
    FPDFText_ClosePage = _libs["pdfium"].get("FPDFText_ClosePage", "cdecl")
    FPDFText_ClosePage.argtypes = [FPDF_TEXTPAGE]
    FPDFText_ClosePage.restype = None

if _libs["pdfium"].has("FPDFText_CountChars", "cdecl"):
    FPDFText_CountChars = _libs["pdfium"].get("FPDFText_CountChars", "cdecl")
    FPDFText_CountChars.argtypes = [FPDF_TEXTPAGE]
    FPDFText_CountChars.restype = c_int

if _libs["pdfium"].has("FPDFText_GetUnicode", "cdecl"):
    FPDFText_GetUnicode = _libs["pdfium"].get("FPDFText_GetUnicode", "cdecl")
    FPDFText_GetUnicode.argtypes = [FPDF_TEXTPAGE, c_int]
    FPDFText_GetUnicode.restype = c_uint

if _libs["pdfium"].has("FPDFText_IsGenerated", "cdecl"):
    FPDFText_IsGenerated = _libs["pdfium"].get("FPDFText_IsGenerated", "cdecl")
    FPDFText_IsGenerated.argtypes = [FPDF_TEXTPAGE, c_int]
    FPDFText_IsGenerated.restype = c_int

if _libs["pdfium"].has("FPDFText_HasUnicodeMapError", "cdecl"):
    FPDFText_HasUnicodeMapError = _libs["pdfium"].get("FPDFText_HasUnicodeMapError", "cdecl")
    FPDFText_HasUnicodeMapError.argtypes = [FPDF_TEXTPAGE, c_int]
    FPDFText_HasUnicodeMapError.restype = c_int

if _libs["pdfium"].has("FPDFText_GetFontSize", "cdecl"):
    FPDFText_GetFontSize = _libs["pdfium"].get("FPDFText_GetFontSize", "cdecl")
    FPDFText_GetFontSize.argtypes = [FPDF_TEXTPAGE, c_int]
    FPDFText_GetFontSize.restype = c_double

if _libs["pdfium"].has("FPDFText_GetFontInfo", "cdecl"):
    FPDFText_GetFontInfo = _libs["pdfium"].get("FPDFText_GetFontInfo", "cdecl")
    FPDFText_GetFontInfo.argtypes = [FPDF_TEXTPAGE, c_int, POINTER(None), c_ulong, POINTER(c_int)]
    FPDFText_GetFontInfo.restype = c_ulong

if _libs["pdfium"].has("FPDFText_GetFontWeight", "cdecl"):
    FPDFText_GetFontWeight = _libs["pdfium"].get("FPDFText_GetFontWeight", "cdecl")
    FPDFText_GetFontWeight.argtypes = [FPDF_TEXTPAGE, c_int]
    FPDFText_GetFontWeight.restype = c_int

if _libs["pdfium"].has("FPDFText_GetTextRenderMode", "cdecl"):
    FPDFText_GetTextRenderMode = _libs["pdfium"].get("FPDFText_GetTextRenderMode", "cdecl")
    FPDFText_GetTextRenderMode.argtypes = [FPDF_TEXTPAGE, c_int]
    FPDFText_GetTextRenderMode.restype = FPDF_TEXT_RENDERMODE

if _libs["pdfium"].has("FPDFText_GetFillColor", "cdecl"):
    FPDFText_GetFillColor = _libs["pdfium"].get("FPDFText_GetFillColor", "cdecl")
    FPDFText_GetFillColor.argtypes = [FPDF_TEXTPAGE, c_int, POINTER(c_uint), POINTER(c_uint), POINTER(c_uint), POINTER(c_uint)]
    FPDFText_GetFillColor.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFText_GetStrokeColor", "cdecl"):
    FPDFText_GetStrokeColor = _libs["pdfium"].get("FPDFText_GetStrokeColor", "cdecl")
    FPDFText_GetStrokeColor.argtypes = [FPDF_TEXTPAGE, c_int, POINTER(c_uint), POINTER(c_uint), POINTER(c_uint), POINTER(c_uint)]
    FPDFText_GetStrokeColor.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFText_GetCharAngle", "cdecl"):
    FPDFText_GetCharAngle = _libs["pdfium"].get("FPDFText_GetCharAngle", "cdecl")
    FPDFText_GetCharAngle.argtypes = [FPDF_TEXTPAGE, c_int]
    FPDFText_GetCharAngle.restype = c_float

if _libs["pdfium"].has("FPDFText_GetCharBox", "cdecl"):
    FPDFText_GetCharBox = _libs["pdfium"].get("FPDFText_GetCharBox", "cdecl")
    FPDFText_GetCharBox.argtypes = [FPDF_TEXTPAGE, c_int, POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double)]
    FPDFText_GetCharBox.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFText_GetLooseCharBox", "cdecl"):
    FPDFText_GetLooseCharBox = _libs["pdfium"].get("FPDFText_GetLooseCharBox", "cdecl")
    FPDFText_GetLooseCharBox.argtypes = [FPDF_TEXTPAGE, c_int, POINTER(FS_RECTF)]
    FPDFText_GetLooseCharBox.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFText_GetMatrix", "cdecl"):
    FPDFText_GetMatrix = _libs["pdfium"].get("FPDFText_GetMatrix", "cdecl")
    FPDFText_GetMatrix.argtypes = [FPDF_TEXTPAGE, c_int, POINTER(FS_MATRIX)]
    FPDFText_GetMatrix.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFText_GetCharOrigin", "cdecl"):
    FPDFText_GetCharOrigin = _libs["pdfium"].get("FPDFText_GetCharOrigin", "cdecl")
    FPDFText_GetCharOrigin.argtypes = [FPDF_TEXTPAGE, c_int, POINTER(c_double), POINTER(c_double)]
    FPDFText_GetCharOrigin.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFText_GetCharIndexAtPos", "cdecl"):
    FPDFText_GetCharIndexAtPos = _libs["pdfium"].get("FPDFText_GetCharIndexAtPos", "cdecl")
    FPDFText_GetCharIndexAtPos.argtypes = [FPDF_TEXTPAGE, c_double, c_double, c_double, c_double]
    FPDFText_GetCharIndexAtPos.restype = c_int

if _libs["pdfium"].has("FPDFText_GetText", "cdecl"):
    FPDFText_GetText = _libs["pdfium"].get("FPDFText_GetText", "cdecl")
    FPDFText_GetText.argtypes = [FPDF_TEXTPAGE, c_int, c_int, POINTER(c_ushort)]
    FPDFText_GetText.restype = c_int

if _libs["pdfium"].has("FPDFText_CountRects", "cdecl"):
    FPDFText_CountRects = _libs["pdfium"].get("FPDFText_CountRects", "cdecl")
    FPDFText_CountRects.argtypes = [FPDF_TEXTPAGE, c_int, c_int]
    FPDFText_CountRects.restype = c_int

if _libs["pdfium"].has("FPDFText_GetRect", "cdecl"):
    FPDFText_GetRect = _libs["pdfium"].get("FPDFText_GetRect", "cdecl")
    FPDFText_GetRect.argtypes = [FPDF_TEXTPAGE, c_int, POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double)]
    FPDFText_GetRect.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFText_GetBoundedText", "cdecl"):
    FPDFText_GetBoundedText = _libs["pdfium"].get("FPDFText_GetBoundedText", "cdecl")
    FPDFText_GetBoundedText.argtypes = [FPDF_TEXTPAGE, c_double, c_double, c_double, c_double, POINTER(c_ushort), c_int]
    FPDFText_GetBoundedText.restype = c_int

if _libs["pdfium"].has("FPDFText_FindStart", "cdecl"):
    FPDFText_FindStart = _libs["pdfium"].get("FPDFText_FindStart", "cdecl")
    FPDFText_FindStart.argtypes = [FPDF_TEXTPAGE, FPDF_WIDESTRING, c_ulong, c_int]
    FPDFText_FindStart.restype = FPDF_SCHHANDLE

if _libs["pdfium"].has("FPDFText_FindNext", "cdecl"):
    FPDFText_FindNext = _libs["pdfium"].get("FPDFText_FindNext", "cdecl")
    FPDFText_FindNext.argtypes = [FPDF_SCHHANDLE]
    FPDFText_FindNext.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFText_FindPrev", "cdecl"):
    FPDFText_FindPrev = _libs["pdfium"].get("FPDFText_FindPrev", "cdecl")
    FPDFText_FindPrev.argtypes = [FPDF_SCHHANDLE]
    FPDFText_FindPrev.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFText_GetSchResultIndex", "cdecl"):
    FPDFText_GetSchResultIndex = _libs["pdfium"].get("FPDFText_GetSchResultIndex", "cdecl")
    FPDFText_GetSchResultIndex.argtypes = [FPDF_SCHHANDLE]
    FPDFText_GetSchResultIndex.restype = c_int

if _libs["pdfium"].has("FPDFText_GetSchCount", "cdecl"):
    FPDFText_GetSchCount = _libs["pdfium"].get("FPDFText_GetSchCount", "cdecl")
    FPDFText_GetSchCount.argtypes = [FPDF_SCHHANDLE]
    FPDFText_GetSchCount.restype = c_int

if _libs["pdfium"].has("FPDFText_FindClose", "cdecl"):
    FPDFText_FindClose = _libs["pdfium"].get("FPDFText_FindClose", "cdecl")
    FPDFText_FindClose.argtypes = [FPDF_SCHHANDLE]
    FPDFText_FindClose.restype = None

if _libs["pdfium"].has("FPDFLink_LoadWebLinks", "cdecl"):
    FPDFLink_LoadWebLinks = _libs["pdfium"].get("FPDFLink_LoadWebLinks", "cdecl")
    FPDFLink_LoadWebLinks.argtypes = [FPDF_TEXTPAGE]
    FPDFLink_LoadWebLinks.restype = FPDF_PAGELINK

if _libs["pdfium"].has("FPDFLink_CountWebLinks", "cdecl"):
    FPDFLink_CountWebLinks = _libs["pdfium"].get("FPDFLink_CountWebLinks", "cdecl")
    FPDFLink_CountWebLinks.argtypes = [FPDF_PAGELINK]
    FPDFLink_CountWebLinks.restype = c_int

if _libs["pdfium"].has("FPDFLink_GetURL", "cdecl"):
    FPDFLink_GetURL = _libs["pdfium"].get("FPDFLink_GetURL", "cdecl")
    FPDFLink_GetURL.argtypes = [FPDF_PAGELINK, c_int, POINTER(c_ushort), c_int]
    FPDFLink_GetURL.restype = c_int

if _libs["pdfium"].has("FPDFLink_CountRects", "cdecl"):
    FPDFLink_CountRects = _libs["pdfium"].get("FPDFLink_CountRects", "cdecl")
    FPDFLink_CountRects.argtypes = [FPDF_PAGELINK, c_int]
    FPDFLink_CountRects.restype = c_int

if _libs["pdfium"].has("FPDFLink_GetRect", "cdecl"):
    FPDFLink_GetRect = _libs["pdfium"].get("FPDFLink_GetRect", "cdecl")
    FPDFLink_GetRect.argtypes = [FPDF_PAGELINK, c_int, c_int, POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double)]
    FPDFLink_GetRect.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFLink_GetTextRange", "cdecl"):
    FPDFLink_GetTextRange = _libs["pdfium"].get("FPDFLink_GetTextRange", "cdecl")
    FPDFLink_GetTextRange.argtypes = [FPDF_PAGELINK, c_int, POINTER(c_int), POINTER(c_int)]
    FPDFLink_GetTextRange.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFLink_CloseWebLinks", "cdecl"):
    FPDFLink_CloseWebLinks = _libs["pdfium"].get("FPDFLink_CloseWebLinks", "cdecl")
    FPDFLink_CloseWebLinks.argtypes = [FPDF_PAGELINK]
    FPDFLink_CloseWebLinks.restype = None

if _libs["pdfium"].has("FPDFPage_GetDecodedThumbnailData", "cdecl"):
    FPDFPage_GetDecodedThumbnailData = _libs["pdfium"].get("FPDFPage_GetDecodedThumbnailData", "cdecl")
    FPDFPage_GetDecodedThumbnailData.argtypes = [FPDF_PAGE, POINTER(None), c_ulong]
    FPDFPage_GetDecodedThumbnailData.restype = c_ulong

if _libs["pdfium"].has("FPDFPage_GetRawThumbnailData", "cdecl"):
    FPDFPage_GetRawThumbnailData = _libs["pdfium"].get("FPDFPage_GetRawThumbnailData", "cdecl")
    FPDFPage_GetRawThumbnailData.argtypes = [FPDF_PAGE, POINTER(None), c_ulong]
    FPDFPage_GetRawThumbnailData.restype = c_ulong

if _libs["pdfium"].has("FPDFPage_GetThumbnailAsBitmap", "cdecl"):
    FPDFPage_GetThumbnailAsBitmap = _libs["pdfium"].get("FPDFPage_GetThumbnailAsBitmap", "cdecl")
    FPDFPage_GetThumbnailAsBitmap.argtypes = [FPDF_PAGE]
    FPDFPage_GetThumbnailAsBitmap.restype = FPDF_BITMAP

if _libs["pdfium"].has("FPDFPage_SetMediaBox", "cdecl"):
    FPDFPage_SetMediaBox = _libs["pdfium"].get("FPDFPage_SetMediaBox", "cdecl")
    FPDFPage_SetMediaBox.argtypes = [FPDF_PAGE, c_float, c_float, c_float, c_float]
    FPDFPage_SetMediaBox.restype = None

if _libs["pdfium"].has("FPDFPage_SetCropBox", "cdecl"):
    FPDFPage_SetCropBox = _libs["pdfium"].get("FPDFPage_SetCropBox", "cdecl")
    FPDFPage_SetCropBox.argtypes = [FPDF_PAGE, c_float, c_float, c_float, c_float]
    FPDFPage_SetCropBox.restype = None

if _libs["pdfium"].has("FPDFPage_SetBleedBox", "cdecl"):
    FPDFPage_SetBleedBox = _libs["pdfium"].get("FPDFPage_SetBleedBox", "cdecl")
    FPDFPage_SetBleedBox.argtypes = [FPDF_PAGE, c_float, c_float, c_float, c_float]
    FPDFPage_SetBleedBox.restype = None

if _libs["pdfium"].has("FPDFPage_SetTrimBox", "cdecl"):
    FPDFPage_SetTrimBox = _libs["pdfium"].get("FPDFPage_SetTrimBox", "cdecl")
    FPDFPage_SetTrimBox.argtypes = [FPDF_PAGE, c_float, c_float, c_float, c_float]
    FPDFPage_SetTrimBox.restype = None

if _libs["pdfium"].has("FPDFPage_SetArtBox", "cdecl"):
    FPDFPage_SetArtBox = _libs["pdfium"].get("FPDFPage_SetArtBox", "cdecl")
    FPDFPage_SetArtBox.argtypes = [FPDF_PAGE, c_float, c_float, c_float, c_float]
    FPDFPage_SetArtBox.restype = None

if _libs["pdfium"].has("FPDFPage_GetMediaBox", "cdecl"):
    FPDFPage_GetMediaBox = _libs["pdfium"].get("FPDFPage_GetMediaBox", "cdecl")
    FPDFPage_GetMediaBox.argtypes = [FPDF_PAGE, POINTER(c_float), POINTER(c_float), POINTER(c_float), POINTER(c_float)]
    FPDFPage_GetMediaBox.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPage_GetCropBox", "cdecl"):
    FPDFPage_GetCropBox = _libs["pdfium"].get("FPDFPage_GetCropBox", "cdecl")
    FPDFPage_GetCropBox.argtypes = [FPDF_PAGE, POINTER(c_float), POINTER(c_float), POINTER(c_float), POINTER(c_float)]
    FPDFPage_GetCropBox.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPage_GetBleedBox", "cdecl"):
    FPDFPage_GetBleedBox = _libs["pdfium"].get("FPDFPage_GetBleedBox", "cdecl")
    FPDFPage_GetBleedBox.argtypes = [FPDF_PAGE, POINTER(c_float), POINTER(c_float), POINTER(c_float), POINTER(c_float)]
    FPDFPage_GetBleedBox.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPage_GetTrimBox", "cdecl"):
    FPDFPage_GetTrimBox = _libs["pdfium"].get("FPDFPage_GetTrimBox", "cdecl")
    FPDFPage_GetTrimBox.argtypes = [FPDF_PAGE, POINTER(c_float), POINTER(c_float), POINTER(c_float), POINTER(c_float)]
    FPDFPage_GetTrimBox.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPage_GetArtBox", "cdecl"):
    FPDFPage_GetArtBox = _libs["pdfium"].get("FPDFPage_GetArtBox", "cdecl")
    FPDFPage_GetArtBox.argtypes = [FPDF_PAGE, POINTER(c_float), POINTER(c_float), POINTER(c_float), POINTER(c_float)]
    FPDFPage_GetArtBox.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPage_TransFormWithClip", "cdecl"):
    FPDFPage_TransFormWithClip = _libs["pdfium"].get("FPDFPage_TransFormWithClip", "cdecl")
    FPDFPage_TransFormWithClip.argtypes = [FPDF_PAGE, POINTER(FS_MATRIX), POINTER(FS_RECTF)]
    FPDFPage_TransFormWithClip.restype = FPDF_BOOL

if _libs["pdfium"].has("FPDFPageObj_TransformClipPath", "cdecl"):
    FPDFPageObj_TransformClipPath = _libs["pdfium"].get("FPDFPageObj_TransformClipPath", "cdecl")
    FPDFPageObj_TransformClipPath.argtypes = [FPDF_PAGEOBJECT, c_double, c_double, c_double, c_double, c_double, c_double]
    FPDFPageObj_TransformClipPath.restype = None

if _libs["pdfium"].has("FPDFPageObj_GetClipPath", "cdecl"):
    FPDFPageObj_GetClipPath = _libs["pdfium"].get("FPDFPageObj_GetClipPath", "cdecl")
    FPDFPageObj_GetClipPath.argtypes = [FPDF_PAGEOBJECT]
    FPDFPageObj_GetClipPath.restype = FPDF_CLIPPATH

if _libs["pdfium"].has("FPDFClipPath_CountPaths", "cdecl"):
    FPDFClipPath_CountPaths = _libs["pdfium"].get("FPDFClipPath_CountPaths", "cdecl")
    FPDFClipPath_CountPaths.argtypes = [FPDF_CLIPPATH]
    FPDFClipPath_CountPaths.restype = c_int

if _libs["pdfium"].has("FPDFClipPath_CountPathSegments", "cdecl"):
    FPDFClipPath_CountPathSegments = _libs["pdfium"].get("FPDFClipPath_CountPathSegments", "cdecl")
    FPDFClipPath_CountPathSegments.argtypes = [FPDF_CLIPPATH, c_int]
    FPDFClipPath_CountPathSegments.restype = c_int

if _libs["pdfium"].has("FPDFClipPath_GetPathSegment", "cdecl"):
    FPDFClipPath_GetPathSegment = _libs["pdfium"].get("FPDFClipPath_GetPathSegment", "cdecl")
    FPDFClipPath_GetPathSegment.argtypes = [FPDF_CLIPPATH, c_int, c_int]
    FPDFClipPath_GetPathSegment.restype = FPDF_PATHSEGMENT

if _libs["pdfium"].has("FPDF_CreateClipPath", "cdecl"):
    FPDF_CreateClipPath = _libs["pdfium"].get("FPDF_CreateClipPath", "cdecl")
    FPDF_CreateClipPath.argtypes = [c_float, c_float, c_float, c_float]
    FPDF_CreateClipPath.restype = FPDF_CLIPPATH

if _libs["pdfium"].has("FPDF_DestroyClipPath", "cdecl"):
    FPDF_DestroyClipPath = _libs["pdfium"].get("FPDF_DestroyClipPath", "cdecl")
    FPDF_DestroyClipPath.argtypes = [FPDF_CLIPPATH]
    FPDF_DestroyClipPath.restype = None

if _libs["pdfium"].has("FPDFPage_InsertClipPath", "cdecl"):
    FPDFPage_InsertClipPath = _libs["pdfium"].get("FPDFPage_InsertClipPath", "cdecl")
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

# No prefix-stripping

