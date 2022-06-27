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
import pl_setup.packaging_base as pkg_base
import pl_setup.update_pdfium as fpdf_up

Changelog = join(pkg_base.SourceTree, "docs", "source", "changelog.md")


def run_cmd(*args, **kws):
    return pkg_base.run_cmd(*args, **kws, cwd=pkg_base.SourceTree)


def update_version():
    
    v_before = pkg_base.VerNamespace["V_MINOR"]
    latest = fpdf_up.get_latest_version()
    fpdf_up.handle_versions(latest)
    
    v_after = pkg_base.VerNamespace["V_MINOR"]
    if v_before == v_after:
        pkg_base.set_version("V_PATCH", pkg_base.VerNamespace["V_PATCH"]+1)
        pkg_base.set_version("V_BETA", None)


def update_changelog(prev_ns, curr_ns):
    
    message = 3*"\n" + "## %s (%s)\n - " % (
        curr_ns["V_PYPDFIUM2"],
        time.strftime("%Y-%m-%d"),
    )
    if prev_ns["V_LIBPDFIUM"] != curr_ns["V_LIBPDFIUM"]:
        message += "Updated PDFium from `%s` to `%s`" % (prev_ns["V_LIBPDFIUM"], curr_ns["V_LIBPDFIUM"])
    else:
        message += "No PDFium update"
    message += " (autorelease)."
    
    with open(Changelog, "r") as fh:
        content = fh.read()
        exp = "# Changelog"
        pos = content.index(exp) + len(exp)
        content = content[:pos] + message + content[pos:]
    with open(Changelog, "w") as fh:
        fh.write(content)


def set_tag(curr_ns):
    Git = shutil.which("git")
    run_cmd([Git, "add", Changelog, pkg_base.VersionFile])
    run_cmd([Git, "commit", "-m", "[autorelease] update changelog and version file"])
    run_cmd([Git, "push"])
    run_cmd([Git, "tag", "-a", curr_ns["V_PYPDFIUM2"], "-m", "Autorelease"])
    run_cmd([Git, "push", "--tags"])
    run_cmd([Git, "checkout", "stable"])
    run_cmd([Git, "rebase", "main"])
    run_cmd([Git, "push"])
    run_cmd([Git, "checkout", "main"])


def main():
    prev_ns = copy.deepcopy(pkg_base.VerNamespace)
    update_version()
    curr_ns = pkg_base.get_version_ns()
    update_changelog(prev_ns, curr_ns)
    set_tag(curr_ns)


if __name__ == "__main__":
    main()
