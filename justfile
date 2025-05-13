#! /usr/bin/env -S just -f
# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

list:
	just -l

test *args:
	python3 -m pytest tests/ {{args}}

_coverage_impl OMISSIONS *args:
	python3 -m coverage run --omit "{{OMISSIONS}}" -m pytest tests/ {{args}}
	python3 -m coverage report
coverage *args:
	just _coverage_impl "src/pypdfium2_raw/bindings.py,tests/*,setupsrc/*" {{args}}
coverage-core *args:
	just _coverage_impl "src/pypdfium2/__main__.py,src/pypdfium2/_cli/*,src/pypdfium2_raw/bindings.py,tests/*,setupsrc/*" {{args}}

docs-build:
	python3 -m sphinx -b html docs/source docs/build/html
docs-open:
	xdg-open docs/build/html/index.html &>/dev/null

clean:
	rm -rf pypdfium2*.egg-info/ src/pypdfium2*.egg-info/ build/ dist/ data/* tests/output/* conda/bundle/out/ conda/helpers/out/ conda/raw/out/
check:
	autoflake src/ setupsrc/ tests/ setup.py docs/source/conf.py --recursive --remove-all-unused-imports --ignore-pass-statements --ignore-init-module-imports
	codespell --skip="./docs/build,./tests/resources,./tests/output,./data,./sbuild,./pdfium_patches,./dist,./LICENSES/*,./BUILD_LICENSES/*,./RELEASE.md,./.git,__pycache__,.mypy_cache,.hypothesis" -L "FitH,flate"
	reuse lint
distcheck:
	twine check dist/*
	# ignore W002: erroneous detection of __init__.py files as duplicates
	check-wheel-contents dist/*.whl --ignore W002 --toplevel "pypdfium2,pypdfium2_raw"

update *args:
	python3 setupsrc/pypdfium2_setup/update.py {{args}}
emplace *args:
	python3 setupsrc/pypdfium2_setup/emplace.py {{args}}
build-native *args:
	python3 setupsrc/pypdfium2_setup/build_native.py {{args}}
build-toolchained *args:
	python3 setupsrc/pypdfium2_setup/build_toolchained.py {{args}}
craft *args:
	python3 setupsrc/pypdfium2_setup/craft.py {{args}}
craft-conda *args:
	python3 conda/craft_conda_pkgs.py {{args}}

packaging-pypi: clean check update craft distcheck
