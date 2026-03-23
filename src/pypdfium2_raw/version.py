# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# TODO(future) add bindings info (e.g. ctypesgen version, reference/generated, runtime libpaths)

__all__ = ("PDFIUM_INFO", )

import json
from pathlib import Path


class _version_class:
    
    def __init__(self):
        with open(self._FILE, "r") as buf:
            data = json.load(buf)
        for k, v in data.items():
            setattr(self, k, v)
        self.api_tag = tuple(data[k] for k in self._TAG_FIELDS)
        self._hook()
        self.version = self.tag + self.desc
    
    def __repr__(self):
        return self.version
    
    def _craft_tag(self):
        return ".".join(str(v) for v in self.api_tag)
    
    def _craft_desc(self, *suffixes):
        
        local_ver = []
        if self.n_commits > 0:
            local_ver += [str(self.n_commits), str(self.hash)]
        local_ver += suffixes
        
        desc = ""
        if local_ver:
            desc += "+" + ".".join(local_ver)
        return desc


class _version_pdfium (_version_class):
    
    _FILE = Path(__file__).parent / "version.json"
    _TAG_FIELDS = ("major", "minor", "build", "patch")
    
    def _hook(self):
        
        self.flags = tuple(self.flags)
        self.tag = self._craft_tag()
        
        self.desc = self._craft_desc()
        if self.flags:
            self.desc += f":{','.join(self.flags)}"
        if self.origin != "pdfium-binaries":
            self.desc += f"@{self.origin}"


PDFIUM_INFO = _version_pdfium()
"""
PDFium version.

It is suggesed to compare against *build* (see below).

Parameters:
    version (str):
        Joined tag and desc, forming the full version.
    tag (str):
        Version ciphers joined as string.
    desc (str):
        Descriptors (origin, flags) as string.
    api_tag (tuple[int]):
        Version ciphers grouped as tuple.
    major (int):
        Chromium major cipher.
    minor (int):
        Chromium minor cipher.
    build (int):
        Chromium/pdfium build cipher.
        This value uniquely identifies the pdfium version.
    patch (int):
        Chromium patch cipher.
    n_commits (int):
        Number of commits after tag at install time. 0 for tagged build commit.
    hash (str | None):
        Hash of head commit (prefixed with 'g') if n_commits > 0, None otherwise.
    origin (str):
        The pdfium binary's origin.
    flags (tuple[str]):
        Tuple of pdfium feature flags. Empty for default build. (V8, XFA) for pdfium-binaries V8 build.
"""
