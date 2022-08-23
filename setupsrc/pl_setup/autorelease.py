#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import sys
import time
import copy
import shutil
import argparse
from os.path import (
    join,
    exists,
    abspath,
    dirname,
    basename,
)

sys.path.insert(0, dirname(dirname(abspath(__file__))))
from pl_setup.packaging_base import (
    run_cmd,
    set_version,
    get_version_ns,
    SourceTree,
    SB_Dir,
    PDFium_URL,
    RepositoryURL,
    Changelog,
    ChangelogStaging,
    VersionFile,
    VerNamespace,
)
from pl_setup.update_pdfium import get_latest_version


PdfiumHistoryDir = join(SB_Dir, "pdfium_history")
AutoreleaseDir = join(SourceTree, "autorelease")
UpdateMajor = join(AutoreleaseDir, "update_major.txt")
UpdateBeta  = join(AutoreleaseDir, "update_beta.txt")


def run_local(*args, **kws):
    return run_cmd(*args, **kws, cwd=SourceTree)


def do_versioning(latest):
    
    # sourcebuild version changes must never be checked into version control
    # autorelease can't work with that state because it needs information about the previous release for its version changes
    assert not VerNamespace["IS_SOURCEBUILD"]
    assert VerNamespace["V_LIBPDFIUM"].isnumeric()
    
    v_libpdfium = int(VerNamespace["V_LIBPDFIUM"])
    
    # current libpdfium version mustn't be larger than determined latest, or something went badly wrong
    assert v_libpdfium <= latest
    
    if exists(UpdateMajor):
        set_version("V_MAJOR", VerNamespace["V_MAJOR"]+1)
        set_version("V_MINOR", 0)
        set_version("V_PATCH", 0)
        set_version("V_LIBPDFIUM", str(latest))
        os.remove(UpdateMajor)
    elif v_libpdfium < latest:
        set_version("V_MINOR", VerNamespace["V_MINOR"]+1)
        set_version("V_PATCH", 0)
        set_version("V_LIBPDFIUM", str(latest))
    else:
        # TODO check if there are any new commits compared to the previous release - if not, stop
        set_version("V_PATCH", VerNamespace["V_PATCH"]+1)
    
    if exists(UpdateBeta):
        v_beta = VerNamespace["V_BETA"]
        if v_beta is None:
            v_beta = 0
        set_version("V_BETA", v_beta+1)
        os.remove(UpdateBeta)


def get_summary():
    
    with open(ChangelogStaging, "r") as fh:
        content = fh.read()
        pos = content.index("\n", content.index("# Changelog")) + 1
        header = content[:pos].strip() + "\n"
        devel_msg = content[pos:].strip()
        if devel_msg:
            devel_msg += "\n"

    with open(ChangelogStaging, "w") as fh:
        fh.write(header)
    
    return devel_msg


def log_changes(summary, prev_ns, curr_ns):
    
    pdfium_msg = "## %s (%s)\n\n- " % (curr_ns["V_PYPDFIUM2"], time.strftime("%Y-%m-%d"))
    if prev_ns["V_LIBPDFIUM"] != curr_ns["V_LIBPDFIUM"]:
        pdfium_msg += "Updated PDFium from `%s` to `%s`" % (prev_ns["V_LIBPDFIUM"], curr_ns["V_LIBPDFIUM"])
    else:
        pdfium_msg += "No PDFium update"
    pdfium_msg += " (autorelease)."
    
    with open(Changelog, "r") as fh:
        content = fh.read()
        pos = content.index("\n", content.index("# Changelog")) + 1
        part_a = content[:pos].strip() + "\n"
        part_b = content[pos:].strip()
        content = part_a + "\n\n" + pdfium_msg + "\n" + summary + "\n\n" + part_b + "\n"
    with open(Changelog, "w") as fh:
        fh.write(content)


def register_changes(curr_ns):
    run_local([Git, "add", AutoreleaseDir, VersionFile, Changelog, ChangelogStaging])
    run_local([Git, "commit", "-m", "[autorelease] update changelog and version file"])
    run_local([Git, "tag", "-a", curr_ns["V_PYPDFIUM2"], "-m", "Autorelease"])
    run_local([Git, "checkout", "stable"])
    run_local([Git, "reset", "--hard", "main"])
    run_local([Git, "checkout", "main"])


def _get_log(url, cwd, ver_a, ver_b, prefix=""):
    log = ""
    log += "Commits between `%s` and `%s` (latest commit first):\n\n" % (ver_a, ver_b)
    log += run_cmd([Git, "log", "%s..%s" % (prefix+ver_a, prefix+ver_b), "--pretty=format:* [`%h`]({}/%H) %s".format(url)], capture=True, cwd=cwd)
    return log


def _get_pdfium_history():
    if not exists(PdfiumHistoryDir):
        # get a cut-down clone of pdfium that only contains the commit history
        run_cmd([Git, "clone", "--filter=blob:none", "--no-checkout", PDFium_URL, basename(PdfiumHistoryDir)], cwd=SB_Dir)
    else:
        run_cmd([Git, "pull"], cwd=PdfiumHistoryDir)


def make_releasenotes(summary, prev_ns, curr_ns):
    
    relnotes = ""
    relnotes += "# Changes (Release %s)\n\n" % curr_ns["V_PYPDFIUM2"]
    relnotes += "## pypdfium2\n\n"
    relnotes += "### Summary\n\n"
    
    if summary:
        relnotes += summary + "\n"
    
    relnotes += "### Log\n\n"
    relnotes += _get_log(RepositoryURL+"/commit", SourceTree, prev_ns["V_PYPDFIUM2"], curr_ns["V_PYPDFIUM2"]) + "\n"
    
    if int(prev_ns["V_LIBPDFIUM"]) < int(curr_ns["V_LIBPDFIUM"]):
        _get_pdfium_history()
        relnotes += "\n## PDFium\n\n"
        relnotes += "### Log\n\n"
        relnotes += _get_log(PDFium_URL+"/+", PdfiumHistoryDir, prev_ns["V_LIBPDFIUM"], curr_ns["V_LIBPDFIUM"], prefix="origin/chromium/")
        relnotes += "\n"
    
    with open(join(SourceTree, "RELEASE.md"), "w") as fh:
        fh.write(relnotes)


def main():
    
    parser = argparse.ArgumentParser(
        description = "Automatic update script for pypdfium2, to be run in the CI release workflow."
    )
    parser.add_argument(
        "--checkin",
        action = "store_true",
        help = "Allow running modifying git commands (commit, tag, reset)."
    )
    args = parser.parse_args()
    
    global Git
    Git = shutil.which("git")
    
    prev_ns = copy.deepcopy(VerNamespace)
    latest = get_latest_version()
    do_versioning(latest)
    curr_ns = get_version_ns()
    
    summary = get_summary()
    log_changes(summary, prev_ns, curr_ns)
    if args.checkin:
        register_changes(curr_ns)
    make_releasenotes(summary, prev_ns, curr_ns)


if __name__ == "__main__":
    main()
