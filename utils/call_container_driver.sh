#! /usr/bin/env bash
set -exuo pipefail

WHEEL_ARG="${1:-dist/*.whl}"
WHEEL_PATH="$(ls $WHEEL_ARG)"
# q&d: infer container target name from wheel name
TARGET="$(python3 utils/regextract.py "-(\w+linux)_[\d_]+_(\w+)\." "%s_%s" "$WHEEL_PATH")"
python3 utils/container_driver.py "$TARGET" -w "$WHEEL_PATH"
