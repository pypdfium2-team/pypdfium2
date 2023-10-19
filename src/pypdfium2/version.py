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
    
    @cached_property
    def version(self):
        return f"{self.tag}+{self.desc}"
    
    def __repr__(self):
        return self.version


# TODO handle data source & editable installs
class _version_pypdfium2 (_abc_version):
    
    _FILE = Path(__file__).parent / "version.json"
    _TAG_FIELDS = ("major", "minor", "patch")
    
    @cached_property
    def api_tag(self):
        return tuple(self._data[k] for k in self._TAG_FIELDS)
    
    @cached_property
    def tag(self):
        tag = ".".join(str(v) for v in self.api_tag)
        if self.beta is not None:
            tag += f"b{self.beta}"
        return tag
    
    @cached_property
    def desc(self):
        
        desc = []
        if self.n_commits > 0:
            desc += [str(self.n_commits), str(self.hash)]
        if self.dirty:
            desc += ["dirty"]
        desc = ".".join(desc)
        
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
    def api_tag(self):
        if self.origin == "pdfium-binaries":
            return tuple(self._data[k] for k in self._TAG_FIELDS)
        else:
            return self.build
    
    @cached_property
    def tag(self):
        if self.origin == "pdfium-binaries":
            return ".".join(str(v) for v in self.api_tag)
        else:
            return str(self.build)
    
    @cached_property
    def desc(self):
        desc = f"{self.origin}"
        if self.flags:
            desc += ":{%s}" % ','.join(self.flags)
        return desc


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
        - ``git``: Parsed from git describe. Highest accuracy. Always used if ``git describe`` is available.
        - ``given``: Pre-supplied version file (e.g. packaged with sdist, or else created by caller).
        - ``record``: Parsed from autorelease record. Implies that possible changes after tag are unknown.\n
        Note that *given* and *record* are not "trustworthy", they can be easily abused to pass arbitrary values. *git* should be correct provided the installed version file is not corrupted.
    is_editable (bool):
        True for editable install, False otherwise.\n
        If True, the version info is the one captured at install time. An arbitrary number of forward or reverse changes may have happened since. The actual current state is unknown.
"""


# FIXME Integration of sourcebuild is quite polluted. Possible improvements:
# - Always use the latest available tag, and add hash/n_commits similar to PYPDFIUM_INFO. This would require a sufficiently deep checkout, though.
# - the build script might fail to check out tags - investigate and fix this
# - Determine major/minor/patch on sourcebuild (pdfium-binaries show how to do this)

PDFIUM_INFO = PDFIUM_INFO
"""
PDFium version.

It is suggesed to compare against *build* (see below).

Parameters:
    version (str):
        Joined tag and desc, forming the full version.
    tag (str):
        Version ciphers joined as str. Just *str(build)* if other ciphers are unknown.
    desc (str):
        Descriptors (origin, flags) represented as str.
    api_tag (tuple[int] | int | str):
        Version ciphers joined as tuple, or just the build value (without tuple) if other ciphers are unknown.
    major (int | None):
        Chromium major cipher.
    minor (int | None):
        Chromium minor cipher.
    build (int | str):
        PDFium tag rsp. Chromium build cipher (int), or commit hash (str).
        This value allows to uniquely identify the pdfium sources the binary was built from.
        For origin pdfium-binaries: always tag. For origin sourcebuild: tag if available, head commit otherwise.
    patch (int | None):
        Chromium patch cipher.
    origin (str):
        The pdfium binary's origin. Possible values:\n
        - ``pdfium-binaries``: Compiled by bblanchon/pdfium-binaries, and bundled into pypdfium2. Chromium ciphers known.
        - ``sourcebuild``: Provided by the caller (commonly compiled using pypdfium2's integrated build script), and bundled into pypdfium2. Chromium ciphers unknown.
        - ``sys``: Dynamically loaded from a standard system location using :func:`ctypes.util.find_library`.
    flags (tuple[str]):
        Tuple of pdfium feature flags. Empty for default build. (V8, XFA) for pdfium-binaries V8 build.
"""

# -----
