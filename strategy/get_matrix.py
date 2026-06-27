# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import json
import argparse
from pathlib import Path

STRATEGY_DIR = Path(__file__).parent.resolve()


def log(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)

def read_json(fp):
    with open(fp, "r") as buf:
        return json.load(buf)


def parse_args(argv):
    parser = argparse.ArgumentParser(
        formatter_class = argparse.RawTextHelpFormatter,
        description = """\
Generate build matrices for given targets. This is intended for use in pypdfium2's GHA workflows.

Check //strategy/targets.json for available targets per build strategy.
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
    return parser.parse_args(argv)


class Inference:
    
    @staticmethod
    def pbin(key, entry):
        return entry
    
    @staticmethod
    def cibw(key, entry):
        entry["cibw_target"] = key
        if "cibw_arch" not in entry:
            entry["cibw_arch"] = key.split("_", maxsplit=1)[-1]
        return entry
    
    @staticmethod
    def sbuild(key, entry):
        entry["target_id"] = key
        return entry


def main():
    
    args = parse_args(sys.argv[1:])
    log(vars(args))
    print()
    
    TARGETS_JSON = read_json(STRATEGY_DIR/"targets.json")
    for target_class in ("pbin", "cibw", "sbuild"):
        
        targets = TARGETS_JSON[target_class]
        selected_keys = getattr(args, target_class)
        if selected_keys == ["all"]:
            selected_keys = list(targets.keys())
        
        inference = getattr(Inference, target_class)
        for key in selected_keys:
            entry = inference(key, targets[key])
            log(f"{key}\n    {entry}")
        
        print()


if __name__ == '__main__':
    main()
