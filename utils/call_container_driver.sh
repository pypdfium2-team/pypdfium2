#! /usr/bin/env bash
set -exuo pipefail

# q&d: infer container target name from wheel name
UTILS_DIR="$(dirname -- "$0")"
WHEEL_PATH="$1"
TARGET=$(python3 "$UTILS_DIR/regextract.py" "-(\w+linux)_[\d_]+_(\w+)\." "%s_%s" $(ls $WHEEL_PATH))
echo "$TARGET"
python3 "$UTILS_DIR/container_driver.py" "$TARGET" -w $WHEEL_PATH
