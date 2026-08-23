#! /usr/bin/env bash

SYMLINKS_DIR=$(realpath "$1")
PY_VERSION="$2"
PYTHON=$(which "python${PY_VERSION}")

mkdir -p "$SYMLINKS_DIR"
ln -sf "$PYTHON" "${SYMLINKS_DIR}/python3"
ln -sf "$PYTHON" "${SYMLINKS_DIR}/python"

printf '%s' "$SYMLINKS_DIR"
