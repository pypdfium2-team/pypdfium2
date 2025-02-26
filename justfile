#! /usr/bin/env -S just -f
# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

test *args:
	python3 -m pytest tests/ {{args}}

_coverage_impl OMISSIONS *args:
	python3 -m coverage run --omit "{{OMISSIONS}}" -m pytest tests/ {{args}}
	python3 -m coverage report

coverage:
	just _coverage_impl "src/pypdfium2_raw/bindings.py,tests/*,setupsrc/*"

coverage-core:
	just _coverage_impl "src/pypdfium2/__main__.py,src/pypdfium2/_cli/*,src/pypdfium2_raw/bindings.py,tests/*,setupsrc/*"

docs-build:
	python3 -m sphinx -b html docs/source docs/build/html

docs-open:
	xdg-open docs/build/html/index.html &>/dev/null

clean:
	rm -rf pypdfium2*.egg-info/ src/pypdfium2*.egg-info/ build/ dist/ data/* tests/output/* conda/bundle/out/ conda/helpers/out/ conda/raw/out/

check:
	autoflake src/ setupsrc/ tests/ setup.py docs/source/conf.py --recursive --remove-all-unused-imports --ignore-pass-statements --ignore-init-module-imports
	codespell --skip="./docs/build,./tests/resources,./tests/output,./data,./sourcebuild,./dist,./LICENSES/*,./RELEASE.md,./.git,__pycache__,.mypy_cache,.hypothesis" -L "FitH,flate"
	reuse lint

packaging_pypi: clean check
	# calling update.py is not strictly necessary, but may improve performance because downloads are done in parallel, rather than linear with each package
	python3 setupsrc/pypdfium2_setup/update.py
	python3 setupsrc/pypdfium2_setup/craft.py
	twine check dist/*
	# ignore W002: erroneous detection of __init__.py files as duplicates
	check-wheel-contents dist/*.whl --ignore W002 --toplevel "pypdfium2,pypdfium2_raw"

update *args:
	python3 setupsrc/pypdfium2_setup/update.py {{args}}

craft *args:
	python3 setupsrc/pypdfium2_setup/craft.py {{args}}

craft-conda *args:
	python3 conda/craft_conda_pkgs.py {{args}}

sourcebuild *args:
	python3 setupsrc/pypdfium2_setup/sourcebuild.py {{args}}

emplace *args:
	python3 setupsrc/pypdfium2_setup/emplace.py {{args}}
