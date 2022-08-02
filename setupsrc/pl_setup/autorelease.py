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
)

sys.path.insert(0, dirname(dirname(abspath(__file__))))
from pl_setup.packaging_base import (
    run_cmd,
    set_version,
    get_version_ns,
    SourceTree,
    RepositoryURL,
    Changelog,
    ChangelogStaging,
    VersionFile,
    VerNamespace,
)
from pl_setup.update_pdfium import get_latest_version

AutoreleaseDir = join(SourceTree, "autorelease")
MajorUpdate = join(AutoreleaseDir, "majorupdate.txt")
BetaUpdate = join(AutoreleaseDir, "betaupdate.txt")


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
    
    if exists(MajorUpdate):
        set_version("V_MAJOR", VerNamespace["V_MAJOR"]+1)
        set_version("V_MINOR", 0)
        set_version("V_PATCH", 0)
        set_version("V_LIBPDFIUM", str(latest))
        os.remove(MajorUpdate)
    elif v_libpdfium < latest:
        set_version("V_MINOR", VerNamespace["V_MINOR"]+1)
        set_version("V_PATCH", 0)
        set_version("V_LIBPDFIUM", str(latest))
    else:
        set_version("V_PATCH", VerNamespace["V_PATCH"]+1)
    
    if exists(BetaUpdate):
        v_beta = VerNamespace["V_BETA"]
        if v_beta is None:
            v_beta = 0
        set_version("V_BETA", v_beta+1)
        os.remove(BetaUpdate)


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


def register_changes(curr_ns, publish=False):
    
    run_local([Git, "add", AutoreleaseDir, VersionFile, Changelog, ChangelogStaging])
    run_local([Git, "commit", "-m", "[autorelease] update changelog and version file"])
    if publish:
        run_local([Git, "push"])
    
    run_local([Git, "tag", "-a", curr_ns["V_PYPDFIUM2"], "-m", "Autorelease"])
    if publish:
        run_local([Git, "push", "--tags"])
    
    run_local([Git, "checkout", "stable"])
    run_local([Git, "reset", "--hard", "main"])
    if publish:
        run_local([Git, "push"])
    
    run_local([Git, "checkout", "main"])


def link_for_tag(tag):
    return RepositoryURL + "/tree/%s" % tag


def make_releasenotes(summary, prev_ns, curr_ns):
    
    prev_ver = prev_ns["V_PYPDFIUM2"]
    curr_ver = curr_ns["V_PYPDFIUM2"]
    
    relnotes = "Release %s\n\n" % curr_ver
    relnotes += "## Changes\n\n"
    relnotes += "### Manual Summary\n\n"
    if summary:
        relnotes += summary + "\n"
    relnotes += "### Git History\n\nCommits between "
    relnotes += "[`%s`](%s) and [`%s`](%s) " % (prev_ver, link_for_tag(prev_ver), curr_ver, link_for_tag(curr_ver))
    relnotes += "(latest commit first):\n\n"
    relnotes += run_local([Git, "log", "%s..%s" % (prev_ver, curr_ver), "--pretty=format:* %H %s"], capture=True)
    relnotes += "\n"
    
    with open(join(SourceTree, "RELEASE.md"), "w") as fh:
        fh.write(relnotes)


def main():
    
    # The `--checkin` and `--publish` options exist to avoid accidential repository changes or even pushes, and to simplify testing this script.
    parser = argparse.ArgumentParser(
        description = "Automatic update script for pypdfium2, to be run in the CI release workflow."
    )
    parser.add_argument(
        "--checkin",
        action = "store_true",
        help = "Allow running modifying git commands (commit, tag, reset)."
    )
    parser.add_argument(
        "--publish",
        action = "store_true",
        help = "Allow pushing changes to the public repository. Takes no effect if `--checkin` is not given.",
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
        register_changes(curr_ns, publish=args.publish)
    make_releasenotes(summary, prev_ns, curr_ns)


if __name__ == "__main__":
    main()
