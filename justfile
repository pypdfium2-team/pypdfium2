#! /usr/bin/env -S just -f
# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

BROWSER := env('BROWSER', 'google-chrome')

list:
	just -l
test *args:
	python3 -m pytest tests/ {{args}}
clean:
	rm -rf pypdfium2.egg-info/ build/ dist/ data/* tests/output/* conda/bundle/out/ conda/helpers/out/ conda/raw/out/

check:
	./utils/check.sh
distcheck:
	twine check dist/*
	check-wheel-contents dist/*.whl
zizmor *args:
     zizmor .github/ --persona auditor {{args}}
zizmor-noisy *args: (zizmor '--no-ignores --no-config' args)

docs-build:  # *args
	python3 -m sphinx -b html docs/source docs/build/html
docs-open:
	{{BROWSER}} docs/build/html/index.html &>/dev/null &
docs-clean:
	rm -rf docs/build/html

_coverage_impl OMISSIONS *args:
	python3 -m coverage run --omit "{{OMISSIONS}}" -m pytest tests/ {{args}}
	python3 -m coverage report
	python3 -m coverage html
	{{BROWSER}} ./htmlcov/index.html &
coverage *args:
	just _coverage_impl "src/pypdfium2_raw/bindings.py,tests/*,setupsrc/*" {{args}}
coverage-core *args:
	just _coverage_impl "src/pypdfium2/__main__.py,src/pypdfium2_cli/*,src/pypdfium2_raw/bindings.py,tests/*,setupsrc/*" {{args}}

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

# see the notes in craft.py for why clearing egg-info and build cache is essential
pkg platform='' *args='-w':
	rm -rf pypdfium2.egg-info/ build/
	PDFIUM_PLATFORM="{{platform}}" python3 -m build -xn {{args}}
sdist: (craft '--sdist')
sdist-unassisted: (pkg 'sdist' '-s')
xpack *platforms='all': clean check (download '-p' platforms) (craft '-p' platforms) distcheck

container *args:
	python3 utils/container_driver.py {{args}}
venv-create envname='.venv':
    #!/usr/bin/env bash
    set -euxo pipefail
    python3 -m venv --clear {{envname}}
    VENV_BIN=$(python3 utils/fix_venv.py {{envname}})
    $VENV_BIN/python3 utils/update_pip_cool.py

pyodide-venv-create envname='.pyodide-venv':
	pyodide venv --clear {{envname}}
	# Avoid "Index ... does not provide upload-time metadata" error when user-level pip config is configured with a dependency cooldown.
	{{envname}}/bin/pip config set --site install.uploaded-prior-to ""
	# then run e.g. `. .pyodide-venv/bin/activate` to enter, and `deactivate` to leave, as usual
pyodide-build:
	PDFIUM_PLATFORM="sourcebuild-native" BUILD_PARAMS="-c emscripten --vendor all --no-vendor libc++ --reset $BUILD_PARAMS" pyodide build . -vv
pyodide-test wheel:
    #!/usr/bin/env bash
    set -euxo pipefail
    export PATH="${PWD}/.pyodide-venv/bin:${PATH}"
    pip install {{wheel}}
    pip install pillow numpy pytest
    pytest tests/
pyodide: pyodide-build pyodide-venv-create (pyodide-test 'dist/pypdfium2-*-pyemscripten_*_wasm32.whl')
