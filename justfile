#! /usr/bin/env -S just -f
# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# Good to know:
# - https://github.com/casey/just/blob/13bf03f642f4cec7799c19f1f8f039e1cb3b095d/README.md
#   sections: #reference, #script-recipes, #shebang-recipes, #safer-bash-shebang-recipes, #python-recipes-with-uv, #activating-environments
# - https://blog.yossarian.net/2020/01/23/Anybody-can-write-good-bash-with-a-little-effort#basics

BROWSER := env('BROWSER', 'google-chrome')
BUILD_PARAMS := env('BUILD_PARAMS', '')
set script-interpreter := ['bash', '-euo', 'pipefail']

list:
	just -l
test *args:
	python3 -m pytest tests/ {{args}}
clean:
	rm -rf pypdfium2.egg-info/ build/ dist/ data/* tests/output/* conda/bundle/out/ conda/helpers/out/ conda/raw/out/

check:
	./utils/misc/check.sh
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
	python3 utils/craft.py {{args}}
craft-conda *args:
	python3 conda/craft_conda_pkgs.py {{args}}

pkg platform='' *args='-w':
	# see the notes in craft.py for why clearing egg-info and build cache is essential
	rm -rf pypdfium2.egg-info/ build/
	PDFIUM_PLATFORM="{{platform}}" python3 -m build -xn {{args}}
container *args:
	python3 utils/container_driver.py {{args}}
sdist: (craft '--sdist')
sdist-unassisted: (pkg 'sdist' '-s')
xpack *platforms='all': clean check (download '-p' platforms) (craft '-p' platforms) distcheck

[script]
@venv-create envname='.venv':
	python3 -m venv --clear {{envname}}
	VENV_BIN=$(python3 utils/misc/fix_venv.py {{envname}})
	$VENV_BIN/python3 utils/misc/update_pip_cool.py

# Concerning pypdfium2 on Pyodide, note the warning in setupsrc/_pyodide.py
pyodide: pyodide-build pyodide-venv-create (pyodide-test 'dist/pypdfium2-*-pyemscripten_*_wasm32.whl')

pyodide-venv-create envname='.pyodide-venv':
	pyodide venv --clear {{envname}}
	# Avoid "Index ... does not provide upload-time metadata" error when user-level pip config is configured with a dependency cooldown.
	{{envname}}/bin/pip config set --site install.uploaded-prior-to ""

# Note, it's up to you to ensure the interpreter that hosts pyodide has the setup dependencies installed.
[script]
@pyodide-build:
	# Make sure that `python3` points to the interpreter that hosts pyodide, because .pyodide_build/pywasmcross_symlinks/pywasmcross.py contains a `#!/usr/bin/env python3` shebang. If it's a different python, ctypesgen will run into issues when invoking pyodide's `gcc` which points to the wrapper script.
	PY_VERSION=$(pyodide config get python_version | cut -d. -f1,2)
	SYMLINKS_DIR="$PWD/.python_symlinks"
	./utils/misc/symlink_py.sh "$SYMLINKS_DIR" "$PY_VERSION"
	export PATH="$SYMLINKS_DIR:$PATH"
	PDFIUM_PLATFORM="sourcebuild-native" BUILD_PARAMS="--pyodide --vendor all --no-vendor libc++ --reset {{BUILD_PARAMS}}" pyodide build . -vv  # -nx

[script]
@pyodide-test wheel:
	export PATH="${PWD}/.pyodide-venv/bin:${PATH}"
	pip install {{wheel}}
	pip install pillow numpy pytest
	python -m pytest tests/
