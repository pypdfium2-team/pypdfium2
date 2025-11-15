# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import functools
from collections import namedtuple

from _corebase import *

IGNORE_FULLVER = bool(int(os.environ.get("IGNORE_FULLVER", 0)))
GIVEN_FULLVER = os.environ.get("GIVEN_FULLVER")

class _PdfiumVerScheme (
    namedtuple("PdfiumVerScheme", ("major", "minor", "build", "patch"))
):
    def __str__(self):
        return ".".join(str(n) for n in self)

class _PdfiumVerClass:
    
    scheme = _PdfiumVerScheme
    
    def __init__(self):
        self._vlines = None
    
    @cached_property
    def _vdict(self):
        if GIVEN_FULLVER:
            log("Warning: taking full versions from caller via $GIVEN_FULLVER (could be incorrect)")
            version_strs = GIVEN_FULLVER.split(":")
            versions = (self.scheme(*(int(n) for n in ver.split("."))) for ver in version_strs)
            return {v.build: v for v in versions}
        else:
            return {}
    
    @staticmethod
    @functools.lru_cache(maxsize=1)
    def get_latest():
        "Returns the latest release version of pdfium-binaries."
        git_ls = run_cmd(["git", "ls-remote", f"{ReleaseRepo}.git"], cwd=None, capture=True)
        tag = git_ls.split("\t")[-1]
        return int( tag.split("/")[-1] )
    
    @functools.lru_cache(maxsize=1)
    def _get_chromium_refs(self):
        # FIXME The ls-remote call may take extremely long (~1min) with older versions of git!
        # With newer git, it's a lot better, but still noticeable (one or a few seconds).
        if self._vlines is None:
            log(f"Attempting to fetch chromium refs. If this causes setup to halt, set e.g. IGNORE_FULLVER=1")
            ChromiumURL = "https://chromium.googlesource.com/chromium/src"
            self._vlines = run_cmd(["git", "ls-remote", "--sort", "-version:refname", "--tags", f"{ChromiumURL}.git", '*.*.*.0'], cwd=None, capture=True).split("\n")
        return self._vlines
    
    def _parse_line(self, line):
        ref = line.split("\t")[-1].rsplit("/", maxsplit=1)[-1]
        full_ver = self.scheme(*[int(v) for v in ref.split(".")])
        self._vdict[full_ver.build] = full_ver
        return full_ver
    
    def get_latest_upstream(self):
        "Returns the latest version of upstream pdfium/chromium."
        lines = self._get_chromium_refs()
        full_ver = self._parse_line( lines.pop(0) )
        return full_ver
    
    if IGNORE_FULLVER:
        assert not IS_CI and not GIVEN_FULLVER
        def to_full(self, v_short):
            log(f"Warning: Full version ignored as per $IGNORE_FULLVER setting - will use NaN placeholders for {v_short}.")
            return self.scheme(NaN, NaN, v_short, NaN)
        
    else:
        def to_full(self, v_short):
            "Converts a build number to a full version."
            v_short = int(v_short)
            if v_short not in self._vdict:
                self._get_chromium_refs()
                for i, line in enumerate(self._vlines):
                    full_ver = self._parse_line(line)
                    if full_ver.build == v_short:
                        self._vlines = self._vlines[i+1:]
                        break
            full_ver = self._vdict[v_short]
            log(f"Resolved {v_short} -> {full_ver}")
            return full_ver
    
    @cached_property
    def pinned(self):
        # comments are not permitted in JSON, so the reason for the post_pdfium pin (if set) goes here:
        # (not currently pinned)
        record = read_json(AR_RecordFile)
        return record["post_pdfium"] or record["pdfium"]

PdfiumVer = _PdfiumVerClass()
NaN = float("nan")
PdfiumVerUnknown = PdfiumVer.scheme(NaN, NaN, NaN, NaN)

# def is_nan(value):
#     return isinstance(value, float) and value != value


def write_pdfium_info(dir, full_ver, origin, flags=(), n_commits=0, hash=None):
    if full_ver is PdfiumVerUnknown:
        log("Warning: pdfium version not known, will use NaN placeholders")
    info = dict(**full_ver._asdict(), n_commits=n_commits, hash=hash, origin=origin, flags=list(flags))
    write_json(dir/VersionFN, info)
    return info

def read_pdfium_info(dir):
    info = read_json(dir/VersionFN)
    full_ver = PdfiumVer.scheme(
        *(info.pop(k) for k in ("major", "minor", "build", "patch"))
    )
    return full_ver, info


def parse_given_tag(full_tag):
    
    info = dict()
    
    # note, `git describe --dirty` ignores new unregistered files
    tag = full_tag
    dirty = tag.endswith("-dirty")
    if dirty:
        tag = tag[:-len("-dirty")]
    tag, *id_parts = tag.split("-")
    
    ver_part, *beta_capture = tag.split("b")
    for v, k in zip(ver_part.split("."), ("major", "minor", "patch")):
        info[k] = int(v)
    assert len(beta_capture) in (0, 1)
    info["beta"] = int(beta_capture[0]) if beta_capture else None
    
    info.update(n_commits=0, hash=None, dirty=dirty)
    schema = ("n_commits", int), ("hash", str)
    for value, (key, cast) in zip(id_parts, schema):
        info[key] = cast(value)
    
    assert merge_tag(info, mode="git") == full_tag
    
    return info


def parse_git_tag():
    desc = run_cmd(["git", "describe", "--tags", "--dirty"], capture=True, cwd=ProjectDir)
    return parse_given_tag(desc)


def get_helpers_info():
    
    # TODO add some checks against record?
    
    have_git_describe = False
    if (ProjectDir/".git").exists():
        try:
            helpers_info = parse_git_tag()
        except subprocess.CalledProcessError as e:
            log(str(e))
            log("Version uncertain: git describe failure - possibly a shallow checkout")
        else:
            have_git_describe = True
            helpers_info["data_source"] = "git"
    else:
        log("Version uncertain: git repo not available.")
    
    if not have_git_describe:
        ver_file = ModuleDir_Helpers / VersionFN
        if ver_file.exists():
            log("Falling back to given version info (e.g. sdist).")
            helpers_info = read_json(ver_file)
            helpers_info["data_source"] = "given"
        else:
            log("Falling back to autorelease record.")
            record = read_json(AR_RecordFile)
            helpers_info = parse_given_tag(record["tag"])
            helpers_info["data_source"] = "record"
    
    return helpers_info


def merge_tag(info, mode):
    
    # some duplication with src/pypdfium2/version.py ...
    
    tag = ".".join([str(info[k]) for k in ("major", "minor", "patch")])
    if info['beta'] is not None:
        tag += f"b{info['beta']}"
    
    extra_info = []
    if info['n_commits'] > 0:
        extra_info += [f"{info['n_commits']}", f"{info['hash']}"]
    if info['dirty']:
        extra_info += ["dirty"]
    
    if extra_info:
        if mode == "git":
            tag += "-" + "-".join(extra_info)
        elif mode == "py":
            tag += "+" + ".".join(extra_info)
        else:
            log("Warning: Ignored post-tag desc. This should not happen in autorelease CI.")
    
    return tag
