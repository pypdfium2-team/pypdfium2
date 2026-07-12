#! /usr/bin/env -S just -f
# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

BROWSER := env('BROWSER', 'google-chrome')

list:
	just -l

test *args:
	python3 -m pytest tests/ {{args}}

_coverage_impl OMISSIONS *args:
	python3 -m coverage run --omit "{{OMISSIONS}}" -m pytest tests/ {{args}}
	python3 -m coverage report
	python3 -m coverage html
	{{BROWSER}} ./htmlcov/index.html &
coverage *args:
	just _coverage_impl "src/pypdfium2_raw/bindings.py,tests/*,setupsrc/*" {{args}}
coverage-core *args:
	just _coverage_impl "src/pypdfium2/__main__.py,src/pypdfium2_cli/*,src/pypdfium2_raw/bindings.py,tests/*,setupsrc/*" {{args}}

docs-build:  # *args
	python3 -m sphinx -b html docs/source docs/build/html
docs-open:
	{{BROWSER}} docs/build/html/index.html &>/dev/null &
docs-clean:
	rm -rf docs/build/html

clean:
	rm -rf pypdfium2*.egg-info/ src/pypdfium2*.egg-info/ build/ dist/ data/* tests/output/* conda/bundle/out/ conda/helpers/out/ conda/raw/out/
check:
	./utils/check.sh
distcheck:
	twine check dist/*
	check-wheel-contents dist/*.whl

# pass --no-ignores --no-config to emit all findings
zizmor *args:
     zizmor .github/ --persona auditor {{args}}

download *args:
	python3 setupsrc/update.py --verify {{args}}
emplace *args:
	python3 setupsrc/emplace.py {{args}}
build-native *args:
	python3 setupsrc/build_native.py {{args}}
build-toolchained *args:
	python3 setupsrc/build_toolchained.py {{args}}
craft *args:
	python3 setupsrc/craft.py {{args}}
craft-conda *args:
	python3 conda/craft_conda_pkgs.py {{args}}

xpack *platforms='all': clean check (download '-p' platforms) (craft '-p' platforms) distcheck
