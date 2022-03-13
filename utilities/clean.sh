#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

set -v

rm -rf src/pypdfium2.egg-info/
rm -rf dist
rm -rf data/*
rm -f tests/output/*
