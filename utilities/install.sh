#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

python3 platform_setup/check_deps.py
python3 -m pip install . -v --no-build-isolation
printf "InitialState" > platform_setup/setup_status.txt
