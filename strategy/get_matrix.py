# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import json
import argparse
import collections
from pathlib import Path


THIS_DIR = Path(__file__).parent.resolve()
STRATEGIES = ("pbin", "cibw", "sbld")

def log(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)

def read_json(fp):
    with open(fp, "r") as buf:
        return json.load(buf)


class Inference:
    
    @staticmethod
    def _noop(entry):
        pass
    
    @staticmethod
    def cibw(entry):
        if "cibw_arch" not in entry:
            entry["cibw_arch"] = entry["label"].split("_", maxsplit=1)[-1]


def get_matrices(args, strategic_targets):
    matrices = {}
    
    for strategy in STRATEGIES:
        
        targets = strategic_targets[strategy]
        matrices[strategy] = matrix_entries = []
        inference = getattr(Inference, strategy, Inference._noop)
        
        for key in getattr(args, strategy):
            entry = {"label": key}
            entry.update(targets[key])
            inference(entry)
            matrix_entries.append(entry)
    
    return matrices


def _repr_entry(entry):
    assert entry, "no empty entries expected"
    output = "\n".join(f"  {k}: {v!r}" for k, v in entry.items())
    output = "-" + output[1:]
    return output

def pprint_matrices(matrices):
    for strategy, entries in matrices.items():
        log(f"{strategy}:")
        for entry in entries:
            log(_repr_entry(entry))
        log()

def dumpstr(matrices):
    output = []
    for strategy, entries in matrices.items():
        output.append(f"{strategy}_needed={bool(entries)}")
        output.append(f"{strategy}_matrix={json.dumps(entries)}")
    return "\n".join(output)

def dump(output, file, where, trailer=""):
    log(f"--- Dump output to {where} ---")
    print(output, file=file)
    log("--------- End dump ----------" + trailer)


def _get_duplicates(iterable):
    return tuple(k for k, v in collections.Counter(iterable).items() if v > 1)

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
        "--pbin", nargs="*", default=[],
        help = "PBIN (pdfium-binaries) targets to build.",
    )
    parser.add_argument(
        "--cibw", nargs="*", default=[],
        help = "CIBW (cibuildwheel) targets to build.",
    )
    parser.add_argument(
        "--sbld", nargs="*", default=[],
        help = "SBLD (sbuild) targets to build.",
    )
    parser.add_argument(
        "--reveal",
        action = "store_true",
        help = "Print human-readable output to stderr.",
    )
    
    args = parser.parse_args(argv)
    for strategy in STRATEGIES:
        selected_targets = getattr(args, strategy)
        duplicates = _get_duplicates(selected_targets)
        assert not duplicates, f"Duplicate targets: {duplicates}"
        if selected_targets == ["all"]:
            selected_targets = list(all_targets[strategy].keys())
            setattr(args, strategy, selected_targets)
    
    return args


def main():
    
    strategic_targets = read_json(THIS_DIR/"targets.json")
    args = parse_args(sys.argv[1:], strategic_targets)
    matrices = get_matrices(args, strategic_targets)
    output = dumpstr(matrices)
    
    if args.reveal:
        log(f"args: {vars(args)}\n")
        pprint_matrices(matrices)
        dump(output, sys.stderr, "stderr", trailer="\n")
    dump(output, sys.stdout, "stdout")


if __name__ == '__main__':
    main()
