#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import time
import copy
import shutil
import argparse
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from pypdfium2_setup import update_pdfium
# TODO? consider glob import or dotted access
from pypdfium2_setup.packaging_base import (
    run_cmd,
    set_versions,
    get_version_ns,
    get_latest_version,
    get_changelog_staging,
    Host,
    DataTree,
    SourceTree,
    PDFium_URL,
    RepositoryURL,
    Changelog,
    ChangelogStaging,
    VersionFile,
    VerNamespace,
    BindingsFileName,
)


AutoreleaseDir  = SourceTree / "autorelease"
MajorUpdateFile = AutoreleaseDir / "update_major.txt"
BetaUpdateFile  = AutoreleaseDir / "update_beta.txt"
RefBindingsFile = SourceTree / "bindings" / BindingsFileName

# these files/dirs do not necessarily need to have been changed, `git add` silently skips that
PlacesToRegister = (AutoreleaseDir, VersionFile, Changelog, ChangelogStaging, RefBindingsFile)


def run_local(*args, **kws):
    return run_cmd(*args, **kws, cwd=SourceTree)


def update_refbindings():
    
    # re-generate host bindings
    host_bindings = DataTree / Host.platform / BindingsFileName
    host_bindings.unlink(missing_ok=True)
    update_pdfium.main([Host.platform])
    assert host_bindings.exists()
    
    # update reference bindings
    shutil.copyfile(host_bindings, RefBindingsFile)  # yes this overwrites


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
    assert VerNamespace["V_BUILDNAME"] == "pdfium-binaries"
    assert VerNamespace["V_LIBPDFIUM"].isnumeric()
    
    v_beta = VerNamespace["V_BETA"]
    v_libpdfium = int(VerNamespace["V_LIBPDFIUM"])
    assert not v_libpdfium > latest  # the current libpdfium version must never be higher than the determined latest
    
    c_updates = (v_libpdfium < latest)
    py_updates = _check_py_updates(VerNamespace["V_PYPDFIUM2"])
    inc_major = MajorUpdateFile.exists()
    inc_beta = BetaUpdateFile.exists()
    
    if not c_updates and not py_updates:
        raise RuntimeError("Neither pypdfium2 code nor pdfium binaries updated. Making a new release would be pointless.")
    
    ver_changes = dict()
    
    if c_updates:
        # denote pdfium update
        ver_changes["V_LIBPDFIUM"] = str(latest)
    
    if inc_major:
        # major update
        ver_changes["V_MAJOR"] = VerNamespace["V_MAJOR"] + 1
        ver_changes["V_MINOR"] = 0
        ver_changes["V_PATCH"] = 0
        MajorUpdateFile.unlink()
    elif v_beta is None:
        # if we're not doing a major update and the previous version was not a beta, update minor and/or patch
        # (note that we still want to run this if adding a new beta tag, though)
        if c_updates:
            # pdfium update -> increment minor version and reset patch version
            ver_changes["V_MINOR"] = VerNamespace["V_MINOR"] + 1
            ver_changes["V_PATCH"] = 0
        else:
            # no pdfium update -> increment patch version
            ver_changes["V_PATCH"] = VerNamespace["V_PATCH"] + 1
    
    if inc_beta:
        # if the new version shall be a beta, set or increment the tag
        if v_beta is None:
            v_beta = 0
        v_beta += 1
        ver_changes["V_BETA"] = v_beta
        BetaUpdateFile.unlink()
    elif v_beta is not None:
        # if the previous version was a beta but the new one shall not be, remove the tag
        ver_changes["V_BETA"] = None
    
    did_change = set_versions(ver_changes)
    assert did_change
    
    return (c_updates, py_updates)


def log_changes(summary, prev_ns, curr_ns):
    
    pdfium_msg = "## %s (%s)\n\n- " % (curr_ns["V_PYPDFIUM2"], time.strftime("%Y-%m-%d"))
    if prev_ns["V_LIBPDFIUM"] != curr_ns["V_LIBPDFIUM"]:
        pdfium_msg += "Updated PDFium from `%s` to `%s`." % (prev_ns["V_LIBPDFIUM"], curr_ns["V_LIBPDFIUM"])
    else:
        pdfium_msg += "No PDFium update."
    
    content = Changelog.read_text()
    pos = content.index("\n", content.index("# Changelog")) + 1
    part_a = content[:pos].strip() + "\n"
    part_b = content[pos:].strip() + "\n"
    content = part_a + "\n\n" + pdfium_msg + "\n"
    if curr_ns["V_BETA"] is None:
        content += summary
    content += "\n\n" + part_b
    Changelog.write_text(content)


def register_changes(curr_ns):
    run_local(["git", "checkout", "-B", "autorelease_tmp"])
    run_local(["git", "add", *PlacesToRegister])
    run_local(["git", "commit", "-m", "[autorelease] update changelog and version file"])
    # NOTE the actually pushed tag will be a different one, but it's nevertheless convenient to have this here because of the changelog
    run_local(["git", "tag", "-a", curr_ns["V_PYPDFIUM2"], "-m", "Autorelease"])


def _get_log(name, url, cwd, ver_a, ver_b, prefix_ver, prefix_commit, prefix_tag):
    log = ""
    log += "\n<details>\n"
    log += "  <summary>%s commit log</summary>\n\n" % (name, )
    # TODO add GH compare link
    log += "Commits between [`%s`](%s) and [`%s`](%s) " % (
        ver_a, url+prefix_ver+ver_a,
        ver_b, url+prefix_ver+ver_b,
    )
    log += "(latest commit first):\n\n"
    log += run_cmd(
        ["git", "log", "%s..%s" % (prefix_tag+ver_a, prefix_tag+ver_b), f"--pretty=format:* [`%h`]({url+prefix_commit}%H) %s"],
        capture=True, check=True, cwd=cwd,
    )
    log += "\n\n</details>\n"
    return log


def make_releasenotes(summary, prev_ns, curr_ns, c_updates):
    
    relnotes = ""
    relnotes += "## Changes (Release %s)\n\n" % (curr_ns["V_PYPDFIUM2"], )
    relnotes += "### Summary (pypdfium2)\n\n"
    if summary:
        relnotes += summary + "\n"
    
    # even if python code was not updated, there will be a release commit
    relnotes += _get_log(
        "pypdfium2", RepositoryURL, SourceTree,
        prev_ns["V_PYPDFIUM2"], curr_ns["V_PYPDFIUM2"],
        "/tree/", "/commit/", "",
    )
    relnotes += "\n"
    
    if c_updates:
        
        # FIXME is there a faster way to get pdfium's commit log?
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            run_cmd(["git", "clone", "--filter=blob:none", "--no-checkout", PDFium_URL, "pdfium_history"], cwd=tmpdir)
            relnotes += _get_log(
                "PDFium", PDFium_URL, tmpdir/"pdfium_history",
                prev_ns["V_LIBPDFIUM"], curr_ns["V_LIBPDFIUM"],
                "/+/refs/heads/chromium/", "/+/", "origin/chromium/",
            )
    
    (SourceTree / "RELEASE.md").write_text(relnotes)


def main():
    
    parser = argparse.ArgumentParser(
        description = "Automatic update script for pypdfium2, to be run in the CI release workflow."
    )
    parser.add_argument(
        "--register",
        action = "store_true",
        help = "Save changes in autorelease_tmp branch."
    )
    args = parser.parse_args()
    
    update_refbindings()
    
    prev_ns = copy.deepcopy(VerNamespace)
    latest = get_latest_version()
    c_updates, py_updates = do_versioning(latest)
    curr_ns = get_version_ns()
    
    summary = get_changelog_staging(
        flush = (curr_ns["V_BETA"] is None),
    )
    log_changes(summary, prev_ns, curr_ns)
    
    if args.register:
        register_changes(curr_ns)
    
    make_releasenotes(summary, prev_ns, curr_ns, c_updates)


if __name__ == "__main__":
    main()
