#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import time
import shutil
import argparse
import tempfile
from pathlib import Path
from copy import deepcopy

# local
from base import *
from system_pdfium import _yield_lo_candidates


PlacesToRegister = (AutoreleaseDir, Changelog, ChangelogStaging, RefBindingsFile)

def run_local(*args, **kws):
    return run_cmd(*args, **kws, cwd=ProjectDir)


def update_refbindings(version):
    
    # We endeavor to make the reference bindings as universal and robust as possible, thus the symbol guards, flags, relative runtime libpath + system search.
    # Also, skip symbol source info for cleaner diffs, so one can see pdfium API changes at a glance.
    
    # REFBINDINGS_FLAGS:
    # Given the symbol guards, we can define all standalone feature flags.
    # We don't currently define flags that depend on external headers, though it should be possible in principle by adding them to $CPATH (or equivalent).
    # Note that Skia is currently a standalone flag because pdfium only provides a typedef void* for a Skia canvas and casts internally
    
    RefBindingsFile.unlink()
    build_pdfium_bindings(
        version, flags=REFBINDINGS_FLAGS,
        rt_paths=(f"./{CTG_LIBPATTERN}", *_yield_lo_candidates(SysNames.linux)),
        search_sys_despite_libpaths=True,
        guard_symbols=True, no_srcinfo=True,
    )
    shutil.copyfile(BindingsFile, RefBindingsFile)
    assert RefBindingsFile.exists()


def do_versioning(config, record, prev_helpers, new_pdfium):
    
    # make sure we have a valid state
    assert not record["pdfium"] > new_pdfium
    if prev_helpers["dirty"]:
        log("Warning: dirty state. This should not happen in CI.")
        assert not IS_CI
    
    py_updates = prev_helpers["n_commits"] > 0
    c_updates = record["pdfium"] < new_pdfium
    
    if not c_updates and not py_updates:
        log("Warning: Neither pypdfium2 code nor pdfium-binaries updated. New release pointless?")
    
    # reset prev_helpers to release state
    prev_helpers["n_commits"] = 0
    prev_helpers["hash"] = None
    new_config = deepcopy(config)
    new_helpers = deepcopy(prev_helpers)
    
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


def log_changes(summary, prev_pdfium, new_pdfium, new_tag, is_beta):
    
    pdfium_msg = f"## {new_tag} ({time.strftime('%Y-%m-%d')})\n\n"
    if prev_pdfium != new_pdfium:
        pdfium_msg += f"- Updated pdfium-binaries from `{prev_pdfium}` to `{new_pdfium}`."
    else:
        pdfium_msg += f"- No pdfium-binaries update, still at `{new_pdfium}`."
    
    pdfium_msg += f" Native and toolchained sourcebuild use pdfium "
    if SBUILD_NATIVE_PIN == SBUILD_TOOLCHAINED_PIN:
        pdfium_msg += f"`{SBUILD_NATIVE_PIN}`."
    else:
        pdfium_msg += f"`{SBUILD_NATIVE_PIN}` and `{SBUILD_TOOLCHAINED_PIN}`, respectively."
    
    content = Changelog.read_text()
    pos = content.index("\n", content.index("# Changelog")) + 1
    part_a = content[:pos].strip() + "\n"
    part_b = content[pos:].strip() + "\n"
    content = part_a + "\n\n" + pdfium_msg + "\n"
    if is_beta:
        content += f"- See the beta release notes on GitHub [here](https://github.com/pypdfium2-team/pypdfium2/releases/tag/{new_tag})\n"
    else:
        content += summary
    content += "\n\n" + part_b
    Changelog.write_text(content)


def register_changes(new_tag):
    run_local(["git", "checkout", "-B", "autorelease_tmp"])
    run_local(["git", "add", *PlacesToRegister])
    run_local(["git", "commit", "-m", f"[autorelease main] update {new_tag}"])
    # Note, the actually published tag will be a different one (though with same name), but it's nevertheless convenient to have this here because of changelog and git describe
    run_local(["git", "tag", "-a", new_tag, "-m", "Autorelease"])


def _get_log(name, url, cwd, ver_a, ver_b, prefix_ver, prefix_commit, prefix_tag, target_known):
    clog = "\n<details>\n"
    clog += f"  <summary>{name} commit log</summary>\n\n"
    clog += f"Commits between [`{ver_a}`]({url+prefix_ver+ver_a}) and [`{ver_b}`]({url+prefix_ver+ver_b})"
    clog += " (latest commit first):\n\n"
    ref_a = prefix_tag+ver_a
    ref_b = prefix_tag+ver_b if target_known else "HEAD"
    clog += run_cmd(
        ["git", "log", f"{ref_a}..{ref_b}", f"--pretty=format:* [`%h`]({url+prefix_commit}%H) %s"],
        capture=True, check=True, cwd=cwd,
    )
    clog += "\n\n</details>\n"
    return clog


def make_releasenotes(summary, prev_pdfium, new_pdfium, prev_tag, new_tag, c_updates, register):
    
    relnotes = ""
    relnotes += f"## Changes (Release {new_tag})\n\n"
    relnotes += "### Summary (pypdfium2)\n\n"
    if summary:
        relnotes += summary
    
    # even if python code was not updated, there will be a release commit
    clog = _get_log(
        "pypdfium2", RepositoryURL, ProjectDir,
        prev_tag, new_tag,
        "/tree/", "/commit/", "",
        target_known=register
    )
    
    # FIXME seems to take rather long - possibility to limit history size?
    # TODO specifically show changes to public/ ?
    if c_updates:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            run_cmd(["git", "clone", "--filter=blob:none", "--no-checkout", PdfiumURL, "pdfium_history"], cwd=tmpdir)
            clog += "\n" + _get_log(
                "PDFium", PdfiumURL, tmpdir/"pdfium_history",
                str(prev_pdfium), str(new_pdfium),
                "/+/refs/heads/chromium/", "/+/", "origin/chromium/",
                target_known=True
            )
    
    # https://github.com/ncipollo/release-action/issues/493
    # GH appears to impose an (undocumented) limit of 125000 characters on release note.
    # We've been hit by this in v4.30.1, due to an excessively long pdfium commit log.
    # To be on the safe side, we stay below 125000 *bytes*, not just python chars.
    intended_relnotes = relnotes + "\n" + clog
    if len(intended_relnotes.encode()) < 125000:
        relnotes = intended_relnotes
    else:
        log("Warning: commit logs are too long for GH release, will be skipped")
        relnotes += "\n" + "*Commit logs skipped (too big).*"
    relnotes += "\n"
    
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
    
    latest_pdfium = PdfiumVer.get_latest()
    config = read_json(AR_ConfigFile)
    record = read_json(AR_RecordFile)
    prev_helpers = parse_git_tag()
    (c_updates, new_pdfium), (py_updates, new_helpers) = \
        do_versioning(config, record, prev_helpers, latest_pdfium)
    
    prev_tag = merge_tag(prev_helpers, mode=None)
    assert prev_tag == record["tag"]
    new_tag = merge_tag(new_helpers, mode=None)
    write_json(AR_RecordFile, dict(tag=new_tag, pdfium=new_pdfium, post_pdfium=None))
    
    update_refbindings(latest_pdfium)
    is_beta = new_helpers["beta"] is not None
    summary = get_next_changelog(flush=(not is_beta))
    log_changes(summary, record["pdfium"], new_pdfium, new_tag, is_beta)
    if args.register:
        register_changes(new_tag)
        parsed_helpers = parse_git_tag()
        if new_helpers != parsed_helpers:
            log(
                "Warning: Written and parsed helpers do not match. This should not happen in CI.\n"
                f"In: {new_helpers}\n" + f"Out: {parsed_helpers}"
            )
            assert not IS_CI
    make_releasenotes(summary, record["pdfium"], new_pdfium, prev_tag, new_tag, c_updates, args.register)


if __name__ == "__main__":
    main()
