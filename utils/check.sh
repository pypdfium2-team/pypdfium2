#! /usr/bin/env bash

autoflake src/ setupsrc/ tests/ setup.py docs/source/conf.py --recursive --remove-all-unused-imports --ignore-pass-statements --ignore-init-module-imports
codespell --skip="./docs/build,./tests/resources,./tests/output,./data,./sbuild,./patches,./dist,./LICENSES,./BUILD_LICENSES,./RELEASE.md,./.git,./htmlcov,__pycache__,.mypy_cache,.hypothesis" -L "FitH,flate,intoto"
reuse lint
