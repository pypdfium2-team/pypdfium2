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
    VersionFile,
    VerNamespace,
    SourceTree,
)
from pl_setup.update_pdfium import (
    get_latest_version,
    handle_versions,
)


Changelog = join(SourceTree, "docs", "source", "changelog.md")
ChangelogStaging = join(SourceTree, "docs", "devel", "changelog_staging.md")

def run_cmd(*args, **kws):
    return run_cmd(*args, **kws, cwd=SourceTree)


def do_versioning():
    
    v_before = VerNamespace["V_MINOR"]
    latest = get_latest_version()
    handle_versions(latest)
    
    v_after = VerNamespace["V_MINOR"]
    if v_before == v_after:
        set_version("V_PATCH", VerNamespace["V_PATCH"]+1)


def log_changes(prev_ns, curr_ns):
    
    pdfium_msg = "## %s (%s)\n\n- " % (curr_ns["V_PYPDFIUM2"], time.strftime("%Y-%m-%d"))
    if prev_ns["V_LIBPDFIUM"] != curr_ns["V_LIBPDFIUM"]:
        pdfium_msg += "Updated PDFium from `%s` to `%s`" % (prev_ns["V_LIBPDFIUM"], curr_ns["V_LIBPDFIUM"])
    else:
        pdfium_msg += "No PDFium update"
    pdfium_msg += " (autorelease)."
    
    with open(ChangelogStaging, "r") as fh:
        content = fh.read()
        pos = content.index("\n", content.index("# Changelog")) + 1
        header = content[:pos].strip() + "\n"
        devel_msg = content[pos:].strip()
        if devel_msg: devel_msg += "\n"
    with open(ChangelogStaging, "w") as fh:
        fh.write(header)
    
    with open(Changelog, "r") as fh:
        content = fh.read()
        pos = content.index("\n", content.index("# Changelog")) + 1
        part_a = content[:pos].strip() + "\n"
        part_b = content[pos:].strip()
        content = part_a + "\n\n" + pdfium_msg + "\n" + devel_msg + "\n\n" + part_b + "\n"
    with open(Changelog, "w") as fh:
        fh.write(content)


def push_changes(curr_ns):
    Git = shutil.which("git")
    run_cmd([Git, "add", Changelog, ChangelogStaging, VersionFile])
    run_cmd([Git, "commit", "-m", "[autorelease] update changelog and version file"])
    run_cmd([Git, "push"])
    run_cmd([Git, "tag", "-a", curr_ns["V_PYPDFIUM2"], "-m", "Autorelease"])
    run_cmd([Git, "push", "--tags"])
    run_cmd([Git, "checkout", "stable"])
    run_cmd([Git, "rebase", "main"])
    run_cmd([Git, "push"])
    run_cmd([Git, "checkout", "main"])


def main():
    prev_ns = copy.deepcopy(VerNamespace)
    do_versioning()
    curr_ns = get_version_ns()
    log_changes(prev_ns, curr_ns)
    push_changes(curr_ns)


if __name__ == "__main__":
    main()
