#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

bash clean.sh
python3 update.py
bash setup_all.sh
check-wheel-contents dist/*
