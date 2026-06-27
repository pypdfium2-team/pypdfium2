# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import json
import argparse
from pathlib import Path


THIS_DIR = Path(__file__).parent.resolve()
STRATEGIES = ("pbin", "cibw", "sbuild")

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
        selected_keys = getattr(args, strategy)
        if selected_keys == ["all"]:
            selected_keys = list(targets.keys())
        
        matrices[strategy] = matrix_entries = []
        inference = getattr(Inference, strategy, Inference._noop)
        
        for key in selected_keys:
            entry = {"label": key}
            entry.update(targets[key])
            inference(entry)
            matrix_entries.append(entry)
    
    return matrices


def reveal_config(args, matrices):
    log(f"args: {vars(args)}\n")
    for strategy, entries in matrices.items():
        log(strategy)
        for entry in entries:
            log(entry)
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


def parse_args(argv):
    parser = argparse.ArgumentParser(
        formatter_class = argparse.RawTextHelpFormatter,
        description = """\
Generate build matrices for given targets. This is intended for use in pypdfium2's GHA workflows.

Check //strategy/targets.json for available targets per build strategy.\
""",
    )
    parser.add_argument(
        "--pbin", nargs="*", default=[],
        help = "pdfium-binaries targets to build.",
    )
    parser.add_argument(
        "--cibw", nargs="*", default=[],
        help = "CIBW targets to build.",
    )
    parser.add_argument(
        "--sbuild", nargs="*", default=[],
        help = "sbuild targets to build.",
    )
    parser.add_argument(
        "--reveal",
        action = "store_true",
        help = "Print human-readable output to stderr.",
    )
    return parser.parse_args(argv)


def main():
    
    args = parse_args(sys.argv[1:])
    strategic_targets = read_json(THIS_DIR/"targets.json")
    matrices = get_matrices(args, strategic_targets)
    output = dumpstr(matrices)
    
    if args.reveal:
        reveal_config(args, matrices)
        dump(output, sys.stderr, "stderr", trailer="\n")
    dump(output, sys.stdout, "stdout")


if __name__ == '__main__':
    main()
