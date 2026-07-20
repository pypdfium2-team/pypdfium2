#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import time
import shutil
import argparse
import tempfile
from pathlib import Path
from copy import deepcopy
from collections import namedtuple

# local
from base import *
from system_pdfium import _yield_lo_candidates


def _versioning_impl(config, prev_info, prev_pdfium, new_pdfium):
    
    # make sure we have a valid state
    assert not prev_pdfium > new_pdfium
    if prev_info["dirty"]:
        log("Warning: dirty state. This should not happen in CI.")
        assert not IS_CI
    
    helpers_update = prev_info["n_commits"] > 0
    pdfium_update = prev_pdfium < new_pdfium
    if not pdfium_update and not helpers_update:
        log("Warning: Neither pypdfium2 code nor pdfium-binaries updated. New release pointless?")
    
    new_config = deepcopy(config)
    new_info = deepcopy(prev_info)
    # reset new_info to release state
    new_info["n_commits"] = 0
    new_info["hash"] = None
    
    if config["major"]:
        new_info["major"] += 1
        new_info["minor"] = 0
        new_info["patch"] = 0
        new_config["major"] = False
    elif prev_info["beta"] is None:
        # If we're not doing a major update and the previous version was not a beta, update minor and/or patch. Note that we still want to run this if adding a new beta tag.
        if (helpers_update and not config["humble"]) or config["humble"] is False:
            # py code update, or manually requested minor release -> increment minor version and reset patch version
            new_info["minor"] += 1
            new_info["patch"] = 0
        else:
            # no py code update, or manually requested patch release -> increment patch version
            new_info["patch"] += 1
    
    if config["humble"] is not None:
        new_config["humble"] = None
    if config["beta"]:
        # If the new version shall be a beta, set or increment the tag
        if new_info["beta"] is None:
            new_info["beta"] = 0
        new_info["beta"] += 1
        new_config["beta"] = False
    elif prev_info["beta"] is not None:
        # If the previous version was a beta but the new one shall not be, remove the tag
        new_info["beta"] = None
    
    write_json(AR_ConfigFile, new_config)
    
    return new_info, pdfium_update


VersionInfo = namedtuple("VersionInfo", ("prev_tag", "new_tag", "is_beta", "new_ver_map", "prev_pdfium", "new_pdfium", "pdfium_update"))

def handle_versions():
    
    config = read_json(AR_ConfigFile)
    record = read_json(AR_RecordFile)
    
    prev_pdfium = record["pdfium"]
    new_pdfium = PdfiumVer.get_latest()
    
    prev_ver_map = parse_git_tag()
    prev_tag = merge_tag(prev_ver_map, mode=None)
    assert prev_tag == record['tag'], f"{prev_tag} != {record['tag']}"
    
    new_ver_map, pdfium_update = _versioning_impl(config, prev_ver_map, prev_pdfium, new_pdfium)
    new_tag = merge_tag(new_ver_map, mode=None)
    write_json(AR_RecordFile, dict(tag=new_tag, pdfium=new_pdfium, post_pdfium=None))
    
    is_beta = new_ver_map["beta"] is not None
    return VersionInfo(
        prev_tag, new_tag, is_beta, new_ver_map,
        prev_pdfium, new_pdfium, pdfium_update,
    )


def update_refbindings(version):
    RefBindingsFile.unlink()
    build_pdfium_bindings(
        version, flags=REFBINDINGS_FLAGS,
        rt_paths=(f"./{CTG_LIBPATTERN}", *_yield_lo_candidates(SysNames.linux)),
        search_sys_despite_libpaths=True,
        guard_symbols=True, no_srcinfo=True,
        windows_cross=True,
    )
    shutil.copyfile(BindingsFile, RefBindingsFile)
    assert RefBindingsFile.exists()


def log_changes(summary, v_info: VersionInfo):
    
    pdfium_msg = f"## {v_info.new_tag} ({time.strftime('%Y-%m-%d')})\n\n"
    if v_info.prev_pdfium != v_info.new_pdfium:
        pdfium_msg += f"- Updated pdfium-binaries from `{v_info.prev_pdfium}` to `{v_info.new_pdfium}`."
    else:
        pdfium_msg += f"- No pdfium-binaries update, still at `{v_info.new_pdfium}`."
    pdfium_msg += " Additional builds may use various other versions of pdfium."
    
    content = Changelog.read_text()
    pos = content.index("\n", content.index("# Changelog")) + 1
    part_a = content[:pos].strip() + "\n"
    part_b = content[pos:].strip() + "\n"
    content = part_a + "\n" + pdfium_msg + "\n"
    if v_info.is_beta:
        content += f"- See the beta release notes on GitHub [here](https://github.com/pypdfium2-team/pypdfium2/releases/tag/{v_info.new_tag})\n"
    else:
        content += summary
    content += "\n\n" + part_b
    Changelog.write_text(content)


# TODO(geisserml) do not pass in so many individual parameters here

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


GitRegisterPaths = (AutoreleaseDir, Changelog, ChangelogStaging, RefBindingsFile)

def _run_local(*args, **kws):
    return run_cmd(*args, **kws, cwd=ProjectDir)

def register_changes(args, v_info: VersionInfo):
    
    _run_local(["git", "checkout", "-B", args.branch])
    _run_local(["git", "add", *GitRegisterPaths])
    _run_local(["git", "commit", "-m", f"[autorelease main] update {v_info.new_tag}"])
    # Note, the actually published tag will be a different one (though with same name), but it's nevertheless convenient to have this here because of changelog and git describe
    _run_local(["git", "tag", "-a", v_info.new_tag, "-m", "Autorelease"])
    
    parsed_ver_map = parse_git_tag()
    if v_info.new_ver_map != parsed_ver_map:
        log(
            "Warning: Written and parsed helpers do not match. This should not happen in CI.\n"
            f"In: {v_info.new_ver_map}\n" + f"Out: {parsed_ver_map}"
        )
        assert not IS_CI


def make_releasenotes(summary, args, v_info: VersionInfo):
    
    relnotes = ""
    relnotes += f"## Release {v_info.new_tag}\n\n"
    if summary:
        relnotes += "### Summary\n\n"
        relnotes += summary
    if args.strategy_file:
        strategies = args.strategy_file["strategies"]
        relnotes += f"""
### Build info\n
This release was made with the following build strategies:
- PBIN: [{', '.join(strategies["pbin"])}]
- SBLD: [{', '.join(strategies["sbuild"])}]
- CIBW: [{', '.join(strategies["cibw"])}]
"""
    
    # even if python code was not updated, there will be a release commit
    clog = "### Commit logs\n"
    clog += _get_log(
        "pypdfium2", RepositoryURL, ProjectDir,
        v_info.prev_tag, v_info.new_tag,
        "/tree/", "/commit/", "",
        target_known=bool(args.branch)
    )
    
    if v_info.pdfium_update and args.pdfium_history:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            run_cmd(["git", "clone", "--filter=blob:none", "--no-checkout", PdfiumURL, "pdfium_history"], cwd=tmpdir)
            # nb: prev_pdfium / new_pdfium are integer (build number)
            clog += _get_log(
                "PDFium", PdfiumURL, tmpdir/"pdfium_history",
                str(v_info.prev_pdfium), str(v_info.new_pdfium),
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
    
    (args.output_dir/"RELEASE.md").write_text(relnotes)


def parse_args():
    parser = argparse.ArgumentParser(
        description = "Automatic update script for pypdfium2, to be run in the CI release workflow."
    )
    parser.add_argument(
        "--to-branch",
        dest = "branch",
        help = "Save changes to given branch name."
    )
    parser.add_argument(
        "--strategy-file",
        type = lambda p: read_json(Path(p).expanduser().resolve()),
        help = "Build strategy info written by //strategy/get_matrix.py",
    )
    parser.add_argument(
        "-o", "--output-dir",
        type = lambda p: Path(p).expanduser().resolve(),
        default = ProjectDir/"release_info",
        help = "Output dir for release notes.",
    )
    parser.add_argument(
        "--pdfium-history",
        action = "store_true",
        help = "Whether to include pdfium commit log (requires cloning pdfium)",
    )
    return parser.parse_args()


def main():
    
    args = parse_args()
    v_info = handle_versions()
    update_refbindings(v_info.new_pdfium)
    
    summary = get_next_changelog(flush=(not v_info.is_beta))
    log_changes(summary, v_info)
    if args.branch:
        register_changes(args, v_info)
    make_releasenotes(summary, args, v_info)


if __name__ == "__main__":
    main()
