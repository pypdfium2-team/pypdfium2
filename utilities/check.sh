#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

echo "Checking for unused imports..."
find . -path ./sourcebuild -prune -o -name '*.py' -print |xargs -n 1 importchecker

echo "Checking for spelling mistakes..."
codespell --skip="./sourcebuild,./docs/build,./data,./.git,__pycache__,.mypy_cache," -L "tabe,splitted"

echo "Checking for missing license/copyright information..."
reuse lint 
