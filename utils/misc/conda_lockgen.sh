#! /usr/bin/env bash
set -euo pipefail

NAME="$1"
PYVER="$2"
PACKAGES="$3"

. "$HOME/miniconda3/etc/profile.d/conda.sh"
conda create -y -n "$NAME" "python=$PYVER"
conda activate "$NAME"
conda install -y $PACKAGES
conda list --name "$NAME" --explicit --sha256 > "conda/lock/$NAME.txt"
conda deactivate
