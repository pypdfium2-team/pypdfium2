#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

set -exuo pipefail

TAG="$1"

git config user.email "geisserml@gmail.com"
git config user.name "geisserml"
git tag -a "$TAG" -m "Autorelease"
