#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

set -v

autoflake src/ tests/ --recursive --remove-all-unused-imports --ignore-pass-statements --exclude "src/pypdfium2/_namespace.py,src/pypdfium2/__init__.py,src/pypdfium2/_helpers/__init__.py"
codespell --skip="./docs/build,./tests/resources,./tests/output,./data,./sourcebuild,./dist,./.git,__pycache__,.mypy_cache,.hypothesis" -L "tabe,splitted"
reuse lint
