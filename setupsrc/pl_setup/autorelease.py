#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import sys
import time
import copy
import argparse
import tempfile
from os.path import (
    join,
    abspath,
    dirname,
)

sys.path.insert(0, dirname(dirname(abspath(__file__))))
from pl_setup.packaging_base import (
    run_cmd,
    set_version,
    get_version_ns,
    get_latest_version,
    SourceTree,
    PDFium_URL,
    RepositoryURL,
    Changelog,
    ChangelogStaging,
    VersionFile,
    VerNamespace,
)


AutoreleaseDir  = join(SourceTree, "autorelease")
MajorUpdateFile = join(AutoreleaseDir, "update_major.txt")
BetaUpdateFile  = join(AutoreleaseDir, "update_beta.txt")


def run_local(*args, **kws):
    return run_cmd(*args, **kws, cwd=SourceTree)


def _check_py_updates(v_pypdfium2):
    # see if pypdfium2 code was updated by checking if the latest commit is tagged
    tag = run_local(["git", "tag", "--list", "--contains", "HEAD"], capture=True)
    if tag == "":
        return True   # untagged -> new commits since previous release
    elif tag == v_pypdfium2:
        return False  # tagged with previous version -> no new commits
    else:
        assert False  # tagged but not with previous version -> invalid state


def do_versioning(latest):
    
    # sourcebuild version changes must never be checked into version control
    # (autorelease can't work with that state because it needs information about the previous release for its version changes)
    assert not VerNamespace["IS_SOURCEBUILD"]
    assert VerNamespace["V_LIBPDFIUM"].isnumeric()
    
    v_beta = VerNamespace["V_BETA"]
    v_libpdfium = int(VerNamespace["V_LIBPDFIUM"])
    assert not v_libpdfium > latest  # the current libpdfium version must never be larger than the determined latest
    
    c_updates = (v_libpdfium < latest)
    py_updates = _check_py_updates(VerNamespace["V_PYPDFIUM2"])
    inc_major = os.path.exists(MajorUpdateFile)
    inc_beta = os.path.exists(BetaUpdateFile)
    
    if not c_updates and not py_updates:
        raise RuntimeError("Neither pypdfium2 code nor pdfium binaries updated. Making a new release would be pointless.")
    
    if c_updates:
        set_version("V_LIBPDFIUM", str(latest))
    
    if inc_major:
        set_version("V_MAJOR", VerNamespace["V_MAJOR"]+1)
        set_version("V_MINOR", 0)
        set_version("V_PATCH", 0)
        os.remove(MajorUpdateFile)
    else:
        if v_beta is None:
            if c_updates:
                set_version("V_MINOR", VerNamespace["V_MINOR"]+1)
                set_version("V_PATCH", 0)
            else:
                set_version("V_PATCH", VerNamespace["V_PATCH"]+1)
        elif not inc_beta:
            set_version("V_BETA", None)
    
    if inc_beta:
        if v_beta is None:
            v_beta = 0
        v_beta += 1
        set_version("V_BETA", v_beta)
        os.remove(BetaUpdateFile)


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
    run_local(["git", "add", AutoreleaseDir, VersionFile, Changelog, ChangelogStaging])
    run_local(["git", "commit", "-m", "[autorelease] update changelog and version file"])
    run_local(["git", "tag", "-a", curr_ns["V_PYPDFIUM2"], "-m", "Autorelease"])
    run_local(["git", "checkout", "stable"])
    run_local(["git", "reset", "--hard", "main"])
    run_local(["git", "checkout", "main"])


def _get_log(cwd, url, ver_a, ver_b, prefix_ver, prefix_commit, prefix_tag):
    log = ""
    log += "Commits between [`%s`](%s) and [`%s`](%s) " % (
        ver_a, url+prefix_ver+ver_a,
        ver_b, url+prefix_ver+ver_b,
    )
    log += "(latest commit first):\n\n"
    log += run_cmd(["git", "log",
        "%s..%s" % (prefix_tag+ver_a, prefix_tag+ver_b),
        "--pretty=format:* [`%h`]({}%H) %s".format(url+prefix_commit)],
        capture=True, cwd=cwd,
    )
    return log


def make_releasenotes(summary, prev_ns, curr_ns):
    
    relnotes = ""
    relnotes += "# Changes (Release %s)\n\n" % curr_ns["V_PYPDFIUM2"]
    relnotes += "## pypdfium2\n\n"
    relnotes += "### Summary\n\n"
    
    if summary:
        relnotes += summary + "\n"
    
    relnotes += "### Log\n\n"
    relnotes += _get_log(
        SourceTree, RepositoryURL,
        prev_ns["V_PYPDFIUM2"], curr_ns["V_PYPDFIUM2"],
        "/tree/", "/commit/", "",
    )
    relnotes += "\n"
    
    if int(prev_ns["V_LIBPDFIUM"]) < int(curr_ns["V_LIBPDFIUM"]):
        
        # FIXME is there a faster way to get pdfium's commit log?
        with tempfile.TemporaryDirectory() as tempdir:
            run_cmd(["git", "clone", "--filter=blob:none", "--no-checkout", PDFium_URL, "pdfium_history"], cwd=tempdir)
            pdfium_log = _get_log(
                join(tempdir, "pdfium_history"), PDFium_URL,
                prev_ns["V_LIBPDFIUM"], curr_ns["V_LIBPDFIUM"],
                "/+/refs/heads/chromium/", "/+/", "origin/chromium/",
            )
        
        relnotes += "\n## PDFium\n\n"
        relnotes += "### Log\n\n"
        relnotes += pdfium_log
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
