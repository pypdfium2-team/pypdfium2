# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import re
import sys
import json
import shutil
import tarfile
import argparse
import functools
import subprocess
import contextlib
from pathlib import Path
from collections import namedtuple
import urllib.request as url_request

from _platbase import *  # local

if sys.version_info < (3, 8):
    class ExtendAction (argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            items = getattr(namespace, self.dest) or []
            items.extend(values)
            setattr(namespace, self.dest, items)
else:
    ExtendAction = None


PDFIUM_MIN_REQ = 6635

PlatSpec_EnvVar = "PDFIUM_PLATFORM"
PlatSpec_VerSep = ":"
PlatSpec_V8Sym  = "-v8"

BindSpec_EnvVar = "PDFIUM_BINDINGS"
IS_CI = bool(os.getenv("GITHUB_ACTIONS")) or bool(int(os.getenv("CIBUILDWHEEL", 0)))
USE_REFBINDINGS = os.getenv(BindSpec_EnvVar) == "reference" or not any((shutil.which("ctypesgen"), IS_CI))

ModulesSpec_EnvVar = "PYPDFIUM_MODULES"
ModuleRaw          = "raw"
ModuleHelpers      = "helpers"
ModulesAll         = (ModuleRaw, ModuleHelpers)

BindingsFN = "bindings.py"
VersionFN  = "version.json"

ProjectDir        = Path(__file__).parents[1].resolve()
DataDir           = ProjectDir / "data"
DataDir_Bindings  = DataDir / "bindings"
BindingsFile      = DataDir_Bindings / BindingsFN
PatchDir          = ProjectDir / "patches"
ModuleDir_Raw     = ProjectDir / "src" / "pypdfium2_raw"
ModuleDir_Helpers = ProjectDir / "src" / "pypdfium2"
Changelog         = ProjectDir / "docs" / "devel" / "changelog.md"
ChangelogStaging  = ProjectDir / "docs" / "devel" / "changelog_staging.md"

AutoreleaseDir  = ProjectDir / "autorelease"
AR_RecordFile   = AutoreleaseDir / "record.json"
AR_ConfigFile   = AutoreleaseDir / "config.json"
RefBindingsFile = AutoreleaseDir / BindingsFN

RepositoryURL  = "https://github.com/pypdfium2-team/pypdfium2"
PdfiumURL      = "https://pdfium.googlesource.com/pdfium"
DepotToolsURL  = "https://chromium.googlesource.com/chromium/tools/depot_tools.git"
ReleaseRepo    = "https://github.com/bblanchon/pdfium-binaries"
ReleaseURL     = ReleaseRepo + "/releases/download/chromium%2F"
ReleaseInfoURL = ReleaseURL.replace("github.com/", "api.github.com/repos/").replace("download/", "tags/")

LIBNAME_GLOBS = ("lib*.so", "lib*.dylib", "*.dll")
REFBINDINGS_FLAGS = ("V8", "XFA", "SKIA")

PdfiumFlagsDict = {
    "V8": "PDF_ENABLE_V8",
    "XFA": "PDF_ENABLE_XFA",
    "SKIA": "PDF_USE_SKIA",
}


def mkdir(path, exist_ok=True, parents=True):
    path.mkdir(exist_ok=exist_ok, parents=parents)

def read_json(fp):
    with open(fp, "r") as buf:
        return json.load(buf)

def write_json(fp, data, indent=2):
    with open(fp, "w") as buf:
        return json.dump(data, buf, indent=indent)


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


def run_cmd(command, cwd, capture=False, check=True, str_cast=True, stderr=None, **kwargs):
    
    if str_cast:
        command = [str(c) for c in command]
    
    log(f"{command} (cwd={cwd!r})")
    if capture:
        kwargs["stdout"] = subprocess.PIPE
        if stderr is not None:
            # allow the caller to pass e.g. subprocess.STDOUT
            kwargs["stderr"] = stderr
    
    comp_process = subprocess.run(command, cwd=cwd, check=check, **kwargs)
    if capture:
        return comp_process.stdout.decode("utf-8").strip()
    else:
        return comp_process


def tar_extract_file(tar, path_or_member, dst_path):
    src_buf = tar.extractfile(path_or_member)
    assert src_buf is not None, f"Failed to extract {path_or_member}"
    with open(dst_path, "wb") as dst_buf:
        shutil.copyfileobj(src_buf, dst_buf)


@contextlib.contextmanager
def tmp_cwd_context(tmp_cwd):
    orig_cwd = os.getcwd()
    os.chdir(str(tmp_cwd.resolve()))
    try:
        yield
    finally:
        os.chdir(orig_cwd)


CTG_LIBPATTERN = "{prefix}{name}.{suffix}"

# TODO make version mandatory
def run_ctypesgen(
        target_path, headers_dir, flags=(),
        rt_paths=(f"./{CTG_LIBPATTERN}", ), ct_paths=(), univ_paths=(),
        search_sys_despite_libpaths=False,
        guard_symbols=False, no_srcinfo=False, version=None
    ):
    
    if USE_REFBINDINGS:
        log("Using reference bindings - this will bypass all bindings params. If this is not intentional, make sure ctypesgen is installed.")
        record_ver = PdfiumVer.pinned
        if version != record_ver:
            log(f"Warning: binary/bindings version mismatch ({version} != {record_ver}). This is ABI-unsafe!")
        shutil.copyfile(RefBindingsFile, target_path)
        return target_path
    
    # Import ctypesgen only in this function so it does not have to be available for other setup tasks
    import ctypesgen
    assert getattr(ctypesgen, "PYPDFIUM2_SPECIFIC", False), "pypdfium2 requires fork of ctypesgen"
    import ctypesgen.__main__
    
    # library loading
    args = ["-l", "pdfium"]
    if rt_paths:
        args += ["--rt-libpaths", *rt_paths]
    if univ_paths:
        args += ["--univ-libpaths", *univ_paths]
    if (rt_paths or univ_paths) and not search_sys_despite_libpaths:
        args += ["--no-system-libsearch"]
    if ct_paths:
        args += ["--ct-libpaths", *ct_paths]
    else:
        args += ["--no-load-library"]
    
    # style
    args += ["--no-macro-guards"]
    if not guard_symbols:
        args += ["--no-symbol-guards"]
    if no_srcinfo:
        args += ["--no-srcinfo"]
    
    # pre-processor - if not given, pypdfium2-ctypesgen will try to auto-select as available (gcc/clang)
    c_preproc = os.environ.get("CPP", None)
    if c_preproc:
        args += ["--cpp", c_preproc]
    if flags:
        args += ["-D"] + [PdfiumFlagsDict[f] for f in flags]
    if Host.system == SysNames.windows:
        # If we are on a Windows host, add the relevant define to expose Windows-only members.
        # Note, this is not currently active for our wheels, since we're packaging everything on Linux. It might be possible to divide packaging in native OS hosts in the future, or specify external headers for symbol spoofing.
        args += ["-D", "_WIN32"]
    
    # symbols - try to exclude some garbage aliases that get pulled in from struct tags
    # (this captures anything that ends with _, _t, or begins with _, and is not needed by other symbols)
    args += ["--symbol-rules", r"if_needed=\w+_$|\w+_t$|_\w+"]
    
    # input / output
    args += ["--headers"] + [h.name for h in sorted(headers_dir.glob("*.h"))] + ["-o", target_path]
    
    with tmp_cwd_context(headers_dir):
        ctypesgen.__main__.main([str(a) for a in args])


def _make_json_compat(obj):
    if isinstance(obj, dict):
        return {k: _make_json_compat(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_make_json_compat(v) for v in obj]
    elif isinstance(obj, Path):
        return str(obj)
    else:
        return obj


def build_pdfium_bindings(version, headers_dir=None, **kwargs):
    
    ver_path = DataDir_Bindings/VersionFN
    bind_path = BindingsFile
    if not headers_dir:
        headers_dir = DataDir_Bindings/"headers"
    
    # TODO register all defaults?
    curr_info = {"version": version, **kwargs}
    curr_info.pop("ct_paths", None)  # ignore
    curr_info.setdefault("flags", [])
    curr_info = _make_json_compat(curr_info)
    
    prev_ver = None
    if ver_path.exists():
        prev_info = read_json(ver_path)
        prev_ver = prev_info["version"]
        if bind_path.exists() and prev_info == curr_info:
            log(f"Using cached bindings")
            return
        else:
            log(f"Bindings cache state differs:", prev_info, curr_info, sep="\n")
    
    # try to reuse headers if only bindings params differ, not version
    if prev_ver == version and headers_dir.exists() and list(headers_dir.glob("fpdf*.h")):
        log("Using cached headers")
    else:
        log("Downloading headers...")
        mkdir(headers_dir)
        archive_url = f"{PdfiumURL}/+archive/refs/heads/chromium/{version}/public.tar.gz"
        archive_path = DataDir_Bindings / "pdfium_public.tar.gz"
        url_request.urlretrieve(archive_url, archive_path)
        with tarfile.open(archive_path) as tar:
            for m in tar.getmembers():
                if m.isfile() and re.fullmatch(r"fpdf(\w+)\.h", m.name, flags=re.ASCII):
                    tar_extract_file(tar, m, headers_dir/m.name)
        archive_path.unlink()
    
    log(f"Building bindings ...")
    bindings_path = DataDir_Bindings/BindingsFN
    run_ctypesgen(bindings_path, headers_dir, version=version, **kwargs)
    write_json(ver_path, curr_info)


def clean_platfiles():
    
    deletables = [
        ProjectDir / "build",
        ModuleDir_Raw / BindingsFN,
        ModuleDir_Raw / VersionFN,
    ]
    for pattern in LIBNAME_GLOBS:
        deletables += ModuleDir_Raw.glob(pattern)
    
    for fp in deletables:
        if fp.is_file():
            fp.unlink()
        elif fp.is_dir():
            shutil.rmtree(fp)


def build_pl_suffix(version, use_v8):
    return (PlatSpec_V8Sym if use_v8 else "") + PlatSpec_VerSep + str(version)


def parse_pl_spec(pl_spec):
    
    # TODO split up in individual env vars after all?
    
    req_ver, flags = None, ()
    if PlatSpec_VerSep in pl_spec:
        pl_spec, req_ver = pl_spec.rsplit(PlatSpec_VerSep)
    if pl_spec.endswith(PlatSpec_V8Sym):
        pl_spec, flags = pl_spec[:-len(PlatSpec_V8Sym)], ("V8", "XFA")
    
    subspec = None
    if not pl_spec or pl_spec == "auto":
        if Host.platform is None:
            log(str(Host._exc))
            pl_name = ExtPlats.fallback
        else:
            pl_name = Host.platform
    else:
        if "-" in pl_spec:
            pl_spec, subspec = pl_spec.split("-", maxsplit=1)
        if hasattr(ExtPlats, pl_spec):
            pl_name = getattr(ExtPlats, pl_spec)
        elif hasattr(PlatNames, pl_spec):
            pl_name = getattr(PlatNames, pl_spec)
        else:
            raise ValueError(f"Invalid binary spec '{pl_spec}'")
    
    if req_ver and req_ver.isnumeric():
        req_ver = int(req_ver)
    
    return pl_name, subspec, req_ver, flags


def parse_modspec(modspec):
    if modspec:
        modnames = modspec.split(",")
        assert set(modnames).issubset(ModulesAll)
        assert len(modnames) in (1, 2)
    else:
        modnames = ModulesAll
    return modnames


def get_next_changelog(flush=False):
    
    content = ChangelogStaging.read_text()
    pos = content.index("\n", content.index("# Changelog")) + 1
    header = content[:pos].strip() + "\n"
    devel_msg = content[pos:].strip()
    if devel_msg:
        devel_msg += "\n"
    
    if flush:
        ChangelogStaging.write_text(header)
    
    return devel_msg


def purge_dir(dir):
    if dir.exists():
        shutil.rmtree(dir)
    dir.mkdir(parents=True)
