#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

set -v

autoflake src/ setupsrc/ tests/ tests_old/ setup.py docs/source/conf.py --recursive --remove-all-unused-imports --ignore-pass-statements --ignore-init-module-imports
codespell --skip="./docs/build,./tests/resources,./tests/output,./tests_old/output,./data,./sourcebuild,./dist,./.git,__pycache__,.mypy_cache,.hypothesis" -L "tabe,splitted,fith,flate"
reuse lint
