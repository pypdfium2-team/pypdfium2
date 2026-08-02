#! /usr/bin/env bash
set -exuo pipefail

WHEEL_PATH="$1"
WHEEL_DIR=$(dirname $WHEEL_PATH)

# cf. https://github.com/pypa/pip/issues/14095
HOST_PLATFORM=$(python3 -c "import sysconfig; print(sysconfig.get_platform().replace('-', '_'))")
RETAGGED_WHEEL_NAME=$(python3 -m wheel tags --platform-tag="$HOST_PLATFORM" "$WHEEL_PATH")
python3 -m pip install -v $WHEEL_DIR/$RETAGGED_WHEEL_NAME
