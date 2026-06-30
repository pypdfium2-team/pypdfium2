#! /usr/bin/env bash
set -exuo pipefail

PYTHON="$1"

$PYTHON -m pip install dist/*.whl
$PYTHON -m pip install -U -r req/test.txt
$PYTHON -m pypdfium2_cli --version
$PYTHON -m pytest tests/ -sv
