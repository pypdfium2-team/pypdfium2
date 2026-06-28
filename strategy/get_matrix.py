# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# We endeavor to keep this script stdlib-only. Please do not import external dependencies or from setupsrc/ here.

import sys
import json
import argparse
import collections
from pathlib import Path


THIS_DIR = Path(__file__).parent.resolve()
STRATEGIES = ("pbin", "sbuild", "cibw")

def log(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)

def read_json(fp):
    with open(fp, "r") as buf:
        return json.load(buf)

def _get_duplicates(iterable):
    return tuple(k for k, v in collections.Counter(iterable).items() if v > 1)


class Inference:
    
    @staticmethod
    def _noop(key, entry):
        return entry
    
    @staticmethod
    def cibw(key, entry):
        entry["cibw_target"] = key
        if "cibw_arch" not in entry:
            entry["cibw_arch"] = key.split("_", maxsplit=1)[-1]
        return entry
    
    @staticmethod
    def sbuild(key, entry):
        if "tag" not in entry:
            tag = key.rsplit(":", maxsplit=1)[0]
            if tag.startswith("manylinux_"):
                arch = tag.split("_", maxsplit=1)[-1]
                tag = f"manylinux_2_17_{arch}.manylinux2014_{arch}"
            entry["tag"] = tag
        return entry


def get_matrices(args, all_targets):
    matrices = {}
    
    for strategy in STRATEGIES:
        
        targets = all_targets[strategy]
        matrices[strategy] = matrix_entries = []
        inference = getattr(Inference, strategy, Inference._noop)
        
        for key in getattr(args, strategy):
            entry = {"label": f"{strategy}/{key}", **inference(key, targets[key])}
            matrix_entries.append(entry)
    
    return matrices


def _repr_entry(entry):
    assert entry, "no empty entries expected"
    output = "\n".join(f"  {k}: {v!r}" for k, v in entry.items())
    output = "-" + output[1:]
    return output

def pprint_mat(matrices):
    for strategy, entries in matrices.items():
        log(f"{strategy}:")
        for entry in entries:
            log(_repr_entry(entry))
        log()

def dumpstr(matrices):
    output = []
    for strategy, entries in matrices.items():
        output.append(f"{strategy}_needed={str(bool(entries)).lower()}")
        output.append(f"{strategy}_matrix={json.dumps(entries)}")
    return "\n".join(output)

def dump(output, file, where, trailer=""):
    log(f"--- Dump output to {where} ---")
    print(output, file=file)
    log("--------- End dump ----------" + trailer)


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
        "--reveal",
        action = "store_true",
        help = "Print human-readable output to stderr.",
    )
    
    args = parser.parse_args(argv)
    
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
    if args.reveal:
        log(f"args: {vars(args)}\n")
        pprint_mat(matrices)
        dump(output, sys.stderr, "stderr", trailer="\n")
    
    dump(output, sys.stdout, "stdout")


if __name__ == '__main__':
    main()
