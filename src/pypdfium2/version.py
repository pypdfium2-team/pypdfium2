# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

__all__ = []

import sys
import json
import functools
from pathlib import Path
from types import MappingProxyType
import pypdfium2_raw


# TODO move to shared compat file
if sys.version_info < (3, 8):
    def cached_property(func):
        return property( functools.lru_cache(maxsize=1)(func) )
else:
    cached_property = functools.cached_property


class _abc_version:
    
    @cached_property
    def _data(self):
        with open(self._FILE, "r") as buf:
            data = json.load(buf)
        self._process_data(data)
        return MappingProxyType(data)
    
    def _process_data(self, data):
        pass
    
    def __getattr__(self, attr):
        return self._data[attr]
    
    def __setattr__(self, name, value):
        raise AttributeError(f"Version class is immutable - assignment '{name} = {value}' not allowed")
    
    def __repr__(self):
        return self.version
    
    @cached_property
    def api_tag(self):
        return tuple(self._data[k] for k in self._TAG_FIELDS)
    
    def _craft_tag(self):
        return ".".join(str(v) for v in self.api_tag)
    
    def _craft_desc(self, extra=[]):
        
        local_ver = []
        if self.n_commits > 0:
            local_ver += [str(self.n_commits), str(self.hash)]
        local_ver += extra
        
        desc = ""
        if local_ver:
            desc += "+" + ".".join(local_ver)
        return desc
    
    @cached_property
    def version(self):
        return self.tag + self.desc


class _version_pypdfium2 (_abc_version):
    
    _FILE = Path(__file__).parent / "version.json"
    _TAG_FIELDS = ("major", "minor", "patch")
    
    @cached_property
    def tag(self):
        tag = self._craft_tag()
        if self.beta is not None:
            tag += f"b{self.beta}"
        return tag
    
    @cached_property
    def desc(self):
        
        extra = []
        if self.dirty:
            extra += ["dirty"]
        
        desc = self._craft_desc(extra)
        if self.data_source != "git":
            desc += f":{self.data_source}"
        if self.is_editable:
            desc += "@editable"
        
        return desc


class _version_pdfium (_abc_version):
    
    _FILE = Path(pypdfium2_raw.__file__).parent / "version.json"
    _TAG_FIELDS = ("major", "minor", "build", "patch")
    
    def _process_data(self, data):
        data["flags"] = tuple(data["flags"])
    
    @cached_property
    def tag(self):
        return self._craft_tag()
    
    @cached_property
    def desc(self):
        desc = self._craft_desc()
        if self.flags:
            desc += ":{%s}" % ",".join(self.flags)
        if self.origin != "pdfium-binaries":
            desc += f"@{self.origin}"
        return desc

# TODO(future) add bindings info (e.g. ctypesgen version, reference/generated, runtime libdirs)


# Current API

PYPDFIUM_INFO = _version_pypdfium2()
PDFIUM_INFO = _version_pdfium()

__all__ += ["PYPDFIUM_INFO", "PDFIUM_INFO"]

# -----


# Deprecated API, to be removed with v5
# Known issue: causes eager evaluation of the new API's theoretically deferred properties.

V_PYPDFIUM2 = PYPDFIUM_INFO.version
V_LIBPDFIUM = str(PDFIUM_INFO.build)
V_BUILDNAME = PDFIUM_INFO.origin
V_PDFIUM_IS_V8 = "V8" in PDFIUM_INFO.flags  # implies XFA
V_LIBPDFIUM_FULL = PDFIUM_INFO.version

__all__ += ["V_PYPDFIUM2", "V_LIBPDFIUM", "V_LIBPDFIUM_FULL", "V_BUILDNAME", "V_PDFIUM_IS_V8"]

# -----


# Docs

PYPDFIUM_INFO = PYPDFIUM_INFO
"""
pypdfium2 helpers version.

It is suggesed to compare against *api_tag* and possibly also *beta* (see below).

Parameters:
    version (str):
        Joined tag and desc, forming the full version.
    tag (str):
        Version ciphers joined as str, including possible beta. Corresponds to the latest release tag at install time.
    desc (str):
        Non-cipher descriptors represented as str.
    api_tag (tuple[int]):
        Version ciphers joined as tuple, excluding possible beta.
    major (int):
        Major cipher.
    minor (int):
        Minor cipher.
    patch (int):
        Patch cipher.
    beta (int | None):
        Beta cipher, or None if not a beta version.
    n_commits (int):
        Number of commits after tag at install time. 0 for release.
    hash (str | None):
        Hash of head commit if n_commits > 0, None otherwise.
    dirty (bool):
        True if there were uncommitted changes at install time, False otherwise.
    data_source (str):
        Source of this version info. Possible values:\n
        - ``git``: Parsed from git describe. Always used if available. Highest accuracy.
        - ``given``: Pre-supplied version file (e.g. packaged with sdist, or else created by caller).
        - ``record``: Parsed from autorelease record. Implies that possible changes after tag are unknown.
    is_editable (bool | None):
        True for editable install, False otherwise. None if unknown.\n
        If True, the version info is the one captured at install time. An arbitrary number of forward or reverse changes may have happened since. The actual current state is unknown.
"""


PDFIUM_INFO = PDFIUM_INFO
"""
PDFium version.

It is suggesed to compare against *build* (see below).

Parameters:
    version (str):
        Joined tag and desc, forming the full version.
    tag (str):
        Version ciphers joined as str.
    desc (str):
        Descriptors (origin, flags) represented as str.
    api_tag (tuple[int]):
        Version ciphers joined as tuple.
    major (int):
        Chromium major cipher.
    minor (int):
        Chromium minor cipher.
    build (int):
        Chromium/pdfium build cipher.
        This value allows to uniquely identify the pdfium sources the binary was built from.
    patch (int):
        Chromium patch cipher.
    n_commits (int):
        Number of commits after tag at install time. 0 for tagged build commit.
    hash (str | None):
        Hash of head commit if n_commits > 0, None otherwise.
    origin (str):
        The pdfium binary's origin. Possible values:\n
        - ``pdfium-binaries``: Compiled by bblanchon/pdfium-binaries, and bundled into pypdfium2.
        - ``sourcebuild``: Provided by the caller (commonly compiled using pypdfium2's integrated build script), and bundled into pypdfium2.
        - ``system``: Loaded from a standard system location using :func:`ctypes.util.find_library()`, or an explicit directory provided at setup time.
    flags (tuple[str]):
        Tuple of pdfium feature flags. Empty for default build. (V8, XFA) for pdfium-binaries V8 build.
"""

# -----
