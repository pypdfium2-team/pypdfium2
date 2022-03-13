#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

set -v

find . -path ./sourcebuild -prune -o -name '*.py' -print |xargs -n 1 importchecker
codespell --skip="./sourcebuild,./docs/build,./data,./.git,__pycache__,.mypy_cache," -L "tabe,splitted"
reuse lint 
