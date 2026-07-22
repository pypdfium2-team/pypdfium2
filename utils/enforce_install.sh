#! /usr/bin/env bash
# See the comment in inside_docker.sh for why we need this.
set -exuo pipefail

WHEEL_PATH="$1"
WHEEL_DIR=$(dirname $WHEEL_PATH)

HOST_PLATFORM=$(python3 -c "import sysconfig; print(sysconfig.get_platform().replace('-', '_'))")
RETAGGED_WHEEL_NAME=$(python3 -m wheel tags --platform-tag="$HOST_PLATFORM" "$WHEEL_PATH")
python3 -m pip install -v $WHEEL_DIR/$RETAGGED_WHEEL_NAME
