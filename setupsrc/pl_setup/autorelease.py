#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import time
import copy
import shutil
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
    SourceTree,
    RepositoryURL,
    Changelog,
    ChangelogStaging,
    VersionFile,
    VerNamespace,
)
from pl_setup.update_pdfium import (
    get_latest_version,
    handle_versions,
)


def run_local(*args, **kws):
    return run_cmd(*args, **kws, cwd=SourceTree)


def do_versioning():
    
    v_before = VerNamespace["V_MINOR"]
    latest = get_latest_version()
    handle_versions(latest)
    
    v_after = VerNamespace["V_MINOR"]
    if v_before == v_after:
        set_version("V_PATCH", VerNamespace["V_PATCH"]+1)


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


def push_changes(curr_ns):
    run_local([Git, "add", Changelog, ChangelogStaging, VersionFile])
    run_local([Git, "commit", "-m", "[autorelease] update changelog and version file"])
    run_local([Git, "push"])
    run_local([Git, "tag", "-a", curr_ns["V_PYPDFIUM2"], "-m", "Autorelease"])
    run_local([Git, "push", "--tags"])
    run_local([Git, "checkout", "stable"])
    run_local([Git, "rebase", "main"])
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
    
    global Git
    Git = shutil.which("git")
    
    prev_ns = copy.deepcopy(VerNamespace)
    do_versioning()
    curr_ns = get_version_ns()
    
    summary = get_summary()
    log_changes(summary, prev_ns, curr_ns)
    push_changes(curr_ns)
    make_releasenotes(summary, prev_ns, curr_ns)


if __name__ == "__main__":
    main()
