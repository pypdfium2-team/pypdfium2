# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

__all__ = ("PYPDFIUM_INFO", "PDFIUM_INFO")

from pathlib import Path
from pypdfium2_raw.version import _version_class, PDFIUM_INFO


class _version_pypdfium2 (_version_class):
    
    _FILE = Path(__file__).parent / "version.json"
    _TAG_FIELDS = ("major", "minor", "patch")
    
    def _hook(self):
        
        self.tag = self._craft_tag()
        if self.beta is not None:
            self.tag += f"b{self.beta}"
        
        suffixes = ["dirty"] if self.dirty else []
        self.desc = self._craft_desc(*suffixes)
        if self.data_source != "git":
            self.desc += f":{self.data_source}"
        if self.is_editable:
            self.desc += "@editable"


PYPDFIUM_INFO = _version_pypdfium2()
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
        Hash of head commit (prefixed with 'g') if n_commits > 0, None otherwise.
    dirty (bool):
        True if there were uncommitted changes at install time, False otherwise.
    data_source (str):
        Source of this version info. Possible values:\n
        - ``git``: Parsed from git describe. Always used if available. Highest accuracy.
        - ``given``: Pre-supplied version file (e.g. packaged with sdist, or else created by caller).
        - ``record``: Parsed from autorelease record. Implies that possible changes after tag are unknown.
    is_editable (bool | None):
        True for editable install, False otherwise. None if unknown.\n
        If True, the version info is the one captured at install time. An arbitrary number of forward or reverse changes may have happened since.
"""


# Freeze the base class after we have constructed the instance objects
def _frozen_setattr(self, name, value):
    raise AttributeError(f"Version class is read-only - assignment '{name} = {value}' not allowed")
_version_class.__setattr__ = _frozen_setattr
