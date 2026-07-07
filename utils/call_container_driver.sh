#! /usr/bin/env bash
set -exuo pipefail

# q&d: infer container target name from wheel name
WHEEL_PATH="$1"
TARGET="$(python3 utils/regextract.py "-(\w+linux)_[\d_]+_(\w+)\." "%s_%s" "$WHEEL_PATH")"
python3 utils/container_driver.py "$TARGET" -w "$WHEEL_PATH"
