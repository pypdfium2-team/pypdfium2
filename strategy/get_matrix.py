# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# We endeavor to keep this script stdlib-only. Please do not import external dependencies or from setupsrc/ here.

import sys
import json
import shlex
import argparse
import collections
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
STRATEGIES = ("pbin", "sbuild", "cibw")

def log(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)

def read_json(fp):
    with open(fp, "r") as buf:
        return json.load(buf)

def _get_duplicates(iterable):
    return tuple(k for k, v in collections.Counter(iterable).items() if v > 1)


class Inference:
    
    def __init__(self, py_vers):
        self.py_vers = py_vers
    
    def _add_pys(self, entry, condition):
        if condition or entry.pop("py_vers", None):
            entry["py_vers"] = self.py_vers.for_runner(entry["runner_os"]).to_str()
        else:
            entry["py_vers"] = self.py_vers.peek_str()
    
    def pbin(self, key, entry):
        self._add_pys(entry, entry["test_on_host"])
        return entry
    
    def cibw(self, key, entry):
        entry["cibw_target"] = key.rsplit(":", maxsplit=1)[0]
        if "cibw_arch" not in entry:
            cibw_arch = entry["cibw_target"].split("_", maxsplit=1)[-1]
            if key.startswith("win_"):
                cibw_arch = cibw_arch.upper()
            entry["cibw_arch"] = cibw_arch
        return entry
    
    def sbuild(self, key, entry):
        if "tag" not in entry:
            tag = key.rsplit(":", maxsplit=1)[0]
            if tag.startswith("manylinux_"):
                arch = tag.split("_", maxsplit=1)[-1]
                tag = f"manylinux_2_17_{arch}.manylinux2014_{arch}"
            entry["tag"] = tag
        self._add_pys(entry, not ("target_os" in entry or "target_cpu" in entry))
        return entry


class PyVers:
    
    _RunnerMinPy = {
        "windows-11-arm": (3, 11),
        "ubuntu-26.04": (3, 10),
        "ubuntu-26.04-arm": (3, 10),
    }
    
    def __init__(self, versions):
        self.versions = tuple(versions)
    
    @classmethod
    def from_str(cls, str_versions):
        versions = []
        for str_ver in str_versions:
            major, minor = str_ver.split(".")
            versions.append((int(major), int(minor)))
        return PyVers(versions)
    
    def bounds(self, min_py):
        return PyVers(v for v in self.versions if v >= min_py)
    
    def for_runner(self, runner_os):
        min_py = self._RunnerMinPy.get(runner_os, None)
        return self.bounds(min_py) if min_py else self
    
    def to_str(self):
        return shlex.join(f"{major}.{minor}" for (major, minor) in self.versions)
    
    def peek_str(self, index=-1):
        major, minor = self.versions[index]
        return f"{major}.{minor}"


def get_matrices(args, all_targets):
    matrices = {}
    
    for strategy in STRATEGIES:
        
        targets = all_targets[strategy]
        matrices[strategy] = matrix_entries = []
        inference = getattr(Inference(args.py_vers), strategy)
        
        for key in getattr(args, strategy):
            entry = {"label": f"{strategy}-{key}", **inference(key, targets[key])}
            matrix_entries.append(entry)
    
    return matrices


def pprint_mat(matrices):
    for strategy, entries in matrices.items():
        log(f"{strategy}:")
        for entry in entries:
            assert entry, "no empty entries expected"
            log("- " + "\n  ".join(f"{k}: {v!r}" for k, v in entry.items()))
        log()

def dumpstr(matrices):
    output = []
    for strategy, entries in matrices.items():
        output.append(f"{strategy}_needed={str(bool(entries)).lower()}")
        output.append('%s_matrix={"include": %s}' % (strategy, json.dumps(entries)))
    return "\n".join(output)

def dump(output, file, where, trailer=""):
    log(f"--- Dump output to {where} ---")
    print(output, file=file)
    log("--------- End dump ----------" + trailer)

def reveal_info(args, matrices, output):
    if not args.reveal:
        return
    log(f"args: {vars(args)}\n")
    pprint_mat(matrices)
    n_targets = sum(len(l) for l in matrices.values())
    log(f"A total of {n_targets} targets will be built.\n")
    dump(output, sys.stderr, "stderr", trailer="\n")


def parse_args(argv, all_targets):
    
    targets_help = "\n".join(
        f"{s.upper()}: " + " ".join(all_targets[s].keys()) for s in STRATEGIES
    )
    
    parser = argparse.ArgumentParser(
        formatter_class = argparse.RawTextHelpFormatter,
        description = f"""\
Generate build matrices for given targets. This is intended for use in pypdfium2's GHA workflows.
See //strategy/targets.json for canonical configuration, or below for available targets per build strategy.\n
""" + targets_help,
    )
    parser.add_argument(
        "--profile",
        help = "Targets profile or template to use. Check //strategy/profiles.json for available profiles. (The target options below append to the template.)",
    )
    parser.add_argument(
        "--pbin", nargs="*", default=[],
        help = "PBIN (pdfium-binaries) targets to build. Either a sequence of platform IDs as seen above, or 'all'.",
    )
    parser.add_argument(
        "--sbuild", nargs="*", default=[],
        help = "SBLD (sbuild) targets to build. dto.",
    )
    parser.add_argument(
        "--cibw", nargs="*", default=[],
        help = "CIBW (cibuildwheel) targets to build. dto.",
    )
    parser.add_argument(
        "--py-vers", nargs="+",
        help = "Sequence of Python versions, as passed to setup-python and multitest.py. The last version specified becomes the main version used for build; other versions are for testing, which will be performed in reverse order, with the main version tested first. Versions unavailable to the runner in question will be implicitly excluded on a per-target basis.",
    )
    parser.add_argument(
        "--reveal",
        action = "store_true",
        help = "Print human-readable output to stderr.",
    )
    
    args = parser.parse_args(argv)
    
    if not args.py_vers:
        args.py_vers = ("3.8", "3.11", "3.14")
    args.py_vers = PyVers.from_str(args.py_vers)
    
    if args.profile:
        profile_json = read_json(THIS_DIR/"profiles.json")[args.profile]
        for s in STRATEGIES:
            setattr(args, s, profile_json[s]+getattr(args, s))
    
    for strategy in STRATEGIES:
        selected_targets = getattr(args, strategy)
        duplicates = _get_duplicates(selected_targets)
        assert not duplicates, f"Duplicates within {strategy.upper()} strategy: {duplicates}"
        if selected_targets == ["all"]:
            selected_targets = list(all_targets[strategy].keys())
            setattr(args, strategy, selected_targets)
    
    assert any(getattr(args, s) for s in STRATEGIES), "At least one target must be given."
    
    return args


def main():
    
    all_targets = read_json(THIS_DIR/"targets.json")
    args = parse_args(sys.argv[1:], all_targets)
    
    matrices = get_matrices(args, all_targets)
    output = dumpstr(matrices)
    reveal_info(args, matrices, output)
    dump(output, sys.stdout, "stdout")


if __name__ == '__main__':
    main()
