#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2024 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import time
import shutil
import argparse
import tempfile
from pathlib import Path
from copy import deepcopy

sys.path.insert(0, str(Path(__file__).parents[1]))
# TODO consider dotted access?
from pypdfium2_setup.packaging_base import *


PlacesToRegister = (AutoreleaseDir, Changelog, ChangelogStaging, RefBindingsFile)

def run_local(*args, **kws):
    return run_cmd(*args, **kws, cwd=ProjectDir)


def update_refbindings(version):
    
    # We endeavor to make the reference bindings as universal and robust as possible, thus the symbol guards, flags, runtime libdir ["."] + system search.
    # Also, skip symbol source info to make for cleaner diffs, so one can see pdfium API changes at a glance.
    
    # REFBINDINGS_FLAGS:
    # Given the symbol guards, we can define all standalone feature flags.
    # We don't currently define flags that depend on external headers, though it should be possible in principle by adding them to $CPATH (or equivalent).
    # Note that Skia is currently a standalone flag because pdfium only provides a typedef void* for a Skia canvas and casts internally
    
    RefBindingsFile.unlink()
    build_pdfium_bindings(version, guard_symbols=True, flags=REFBINDINGS_FLAGS, allow_system_despite_libdirs=True, no_srcinfo=True)
    shutil.copyfile(DataDir_Bindings/BindingsFN, RefBindingsFile)
    assert RefBindingsFile.exists()


def do_versioning(config, record, prev_helpers, new_pdfium):
    
    # make sure we have a valid state
    assert isinstance(record["pdfium"], int)
    assert not record["pdfium"] > new_pdfium
    if prev_helpers["dirty"]:
        print("Warning: dirty state. This should not happen in CI.", file=sys.stderr)
    
    # TODO actually, we care only about updates to src/
    py_updates = prev_helpers["n_commits"] > 0
    c_updates = record["pdfium"] < new_pdfium
    
    if not c_updates and not py_updates:
        print("Warning: Neither pypdfium2 code nor pdfium-binaries updated. New release pointless?", file=sys.stderr)
    
    # reset prev_helpers to release state
    prev_helpers["n_commits"] = 0
    prev_helpers["hash"] = None
    new_config, new_helpers = [deepcopy(d) for d in (config, prev_helpers)]
    
    if config["major"]:
        new_helpers["major"] += 1
        new_helpers["minor"] = 0
        new_helpers["patch"] = 0
        new_config["major"] = False
    elif prev_helpers["beta"] is None:
        # If we're not doing a major update and the previous version was not a beta, update minor and/or patch. Note that we still want to run this if adding a new beta tag.
        if (py_updates and not config["humble"]) or config["humble"] is False:
            # py code update, or manually requested minor release -> increment minor version and reset patch version
            new_helpers["minor"] += 1
            new_helpers["patch"] = 0
        else:
            # no py code update, or manually requested patch release -> increment patch version
            new_helpers["patch"] += 1
    
    if config["humble"] is not None:
        new_config["humble"] = None
    if config["beta"]:
        # If the new version shall be a beta, set or increment the tag
        if new_helpers["beta"] is None:
            new_helpers["beta"] = 0
        new_helpers["beta"] += 1
        new_config["beta"] = False
    elif prev_helpers["beta"] is not None:
        # If the previous version was a beta but the new one shall not be, remove the tag
        new_helpers["beta"] = None
    
    write_json(AR_ConfigFile, new_config)
    
    return (c_updates, new_pdfium), (py_updates, new_helpers)


def log_changes(summary, prev_pdfium, new_pdfium, new_tag, beta):
    
    pdfium_msg = f"## {new_tag} ({time.strftime('%Y-%m-%d')})\n\n"
    if prev_pdfium != new_pdfium:
        pdfium_msg += f"- Updated PDFium from `{prev_pdfium}` to `{new_pdfium}`."
    else:
        pdfium_msg += "- No PDFium update."
    
    content = Changelog.read_text()
    pos = content.index("\n", content.index("# Changelog")) + 1
    part_a = content[:pos].strip() + "\n"
    part_b = content[pos:].strip() + "\n"
    content = part_a + "\n\n" + pdfium_msg + "\n"
    if beta is None:
        content += summary
    content += "\n\n" + part_b
    Changelog.write_text(content)


def register_changes(new_tag):
    run_local(["git", "checkout", "-B", "autorelease_tmp"])
    run_local(["git", "add", *PlacesToRegister])
    run_local(["git", "commit", "-m", f"[autorelease main] update {new_tag}"])
    # Note, the actually published tag will be a different one (though with same name), but it's nevertheless convenient to have this here because of changelog and git describe
    run_local(["git", "tag", "-a", new_tag, "-m", "Autorelease"])


def _get_log(name, url, cwd, ver_a, ver_b, prefix_ver, prefix_commit, prefix_tag):
    # known issue: log fails if args.register is False
    log = ""
    log += "\n<details>\n"
    log += f"  <summary>{name} commit log</summary>\n\n"
    log += f"Commits between [`{ver_a}`]({url+prefix_ver+ver_a}) and [`{ver_b}`]({url+prefix_ver+ver_b})"
    log += " (latest commit first):\n\n"
    log += run_cmd(
        ["git", "log", f"{prefix_tag+ver_a}..{prefix_tag+ver_b}", f"--pretty=format:* [`%h`]({url+prefix_commit}%H) %s"],
        capture=True, check=True, cwd=cwd,
    )
    log += "\n\n</details>\n"
    return log


def make_releasenotes(summary, prev_pdfium, new_pdfium, prev_tag, new_tag, c_updates):
    
    # TODO specifically show changes to public/ ?
    
    relnotes = ""
    relnotes += f"## Changes (Release {new_tag})\n\n"
    relnotes += "### Summary (pypdfium2)\n\n"
    if summary:
        relnotes += summary + "\n"
    
    # even if python code was not updated, there will be a release commit
    relnotes += _get_log(
        "pypdfium2", RepositoryURL, ProjectDir,
        prev_tag, new_tag,
        "/tree/", "/commit/", "",
    )
    relnotes += "\n"
    
    if c_updates:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            # FIXME seems to take rather long - possibility to limit history size?
            run_cmd(["git", "clone", "--filter=blob:none", "--no-checkout", PdfiumURL, "pdfium_history"], cwd=tmpdir)
            relnotes += _get_log(
                "PDFium", PdfiumURL, tmpdir/"pdfium_history",
                str(prev_pdfium), str(new_pdfium),
                "/+/refs/heads/chromium/", "/+/", "origin/chromium/",
            )
    
    (ProjectDir/"RELEASE.md").write_text(relnotes)


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
    
    # TODO dump input/output data for debugging
    
    latest_pdfium = PdfiumVer.get_latest()
    config = read_json(AR_ConfigFile)
    record = read_json(AR_RecordFile)
    prev_helpers = parse_git_tag()
    (c_updates, new_pdfium), (py_updates, new_helpers) = \
        do_versioning(config, record, prev_helpers, latest_pdfium)
    
    prev_tag = merge_tag(prev_helpers, mode=None)
    assert prev_tag == record["tag"]
    new_tag = merge_tag(new_helpers, mode=None)
    write_json(AR_RecordFile, dict(pdfium=new_pdfium, tag=new_tag))
    
    update_refbindings(latest_pdfium)
    summary = get_next_changelog(
        flush = new_helpers["beta"] is None
    )
    log_changes(summary, record["pdfium"], new_pdfium, new_tag, new_helpers["beta"])
    if args.register:
        register_changes(new_tag)
        parsed_helpers = parse_git_tag()
        if new_helpers != parsed_helpers:
            print(
                "Warning: Written and parsed helpers do not match. This should not happen in CI.\n"
                f"In: {new_helpers}\n" + f"Out: {parsed_helpers}"
            )
    make_releasenotes(summary, record["pdfium"], new_pdfium, prev_tag, new_tag, c_updates)


if __name__ == "__main__":
    main()
