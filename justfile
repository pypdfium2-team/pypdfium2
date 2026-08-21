# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# Good to know:
# 
# *Just*
# - https://github.com/casey/just/blob/13bf03f642f4cec7799c19f1f8f039e1cb3b095d/README.md
#   sections: #reference, #script-recipes, #shebang-recipes, #safer-bash-shebang-recipes, #python-recipes-with-uv, #activating-environments
# 
# *Shell*
# - https://blog.yossarian.net/2020/01/23/Anybody-can-write-good-bash-with-a-little-effort#basics
# - https://google.github.io/styleguide/shellguide.html

BROWSER := env('BROWSER', 'google-chrome')
BUILD_PARAMS := env('BUILD_PARAMS', '')
set script-interpreter := ['bash', '-euo', 'pipefail']
verbose := 'set -x &&'

list:
	just -l
test *args:
	python3 -m pytest tests/ {{args}}
clean-before-build:
	# see the notes in utils/craft.py why clearing this is essential before running pyproject-build
	rm -rf pypdfium2.egg-info/ build/
clean: clean-before-build
	rm -rf data/* tests/output/* dist/ .pytest_cache/ .mypy_cache/ .venv/ .pyodide-venv/ .pyodide_build/ .python_symlinks/

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
craft *args:
	python3 utils/craft.py {{args}}
pkg *platforms='auto': (craft '-p' platforms '--wheels')
pyproject-build platform='' *args='-w': clean-before-build
	PDFIUM_PLATFORM="{{platform}}" python3 -m build -xn {{args}}
sdist: (craft '--sdist')
sdist-unassisted: (pyproject-build 'sdist' '-s')
container *args:
	python3 utils/container_driver.py {{args}}
xpack *platforms='all': clean check (download '-p' platforms) (craft '-p' platforms) distcheck

build-native *args:
	python3 setupsrc/build_native.py {{args}}
build-toolchained *args:
	python3 setupsrc/build_toolchained.py {{args}}

[script]
venv-create envname='.venv':
	{{verbose}} python3 -m venv --clear {{envname}}
	VENV_BIN=$(python3 utils/misc/fix_venv.py {{envname}})
	$VENV_BIN/python3 utils/update_pip.py


# NOTE you may want to make pinact a wrapper script that translates to something like
# GITHUB_TOKEN=$(kwallet-query -f Passwords -r pinact kdewallet) pinact_raw $@
update-actions min_age='7':
	pinact run -update -min-age {{min_age}} || true

[script]
update-locks:
	{{verbose}} rm -f lock/{pip,distcheck}.txt
	pip-compile -v --upgrade --generate-hashes --uploaded-prior-to=P3D --allow-unsafe lock/pip.in -o lock/pip.txt
	pip-compile -v --upgrade --generate-hashes --uploaded-prior-to=P7D lock/distcheck.in -o lock/distcheck.txt

update-all-pins: update-actions update-locks


# Pyodide support recipes (note the warning in setupsrc/_pyodide.py though)

pyodide-venv-create envname='.pyodide-venv':
	pyodide venv --clear {{envname}}
	# Avoid "Index ... does not provide upload-time metadata" error when user-level pip config is configured with a dependency cooldown.
	{{envname}}/bin/pip config set --site install.uploaded-prior-to ""

[script]
pyodide-build *args:
	# Make sure that `python3` points to the interpreter that hosts pyodide, because .pyodide_build/pywasmcross_symlinks/pywasmcross.py contains a `#!/usr/bin/env python3` shebang. If it's a different python, ctypesgen will run into issues when invoking pyodide's `gcc` which points to the wrapper script.
	{{verbose}} PY_VERSION=$(pyodide config get python_version | cut -d. -f1,2)
	SYMLINKS_DIR=$(./utils/misc/symlink_py.sh ".python_symlinks" "$PY_VERSION")
	export PATH="${SYMLINKS_DIR}:${PATH}"
	# Note, you may want to set BUILD_PARAMS="--reset" on your side.
	# If -nx is passed, it's down to you to ensure the interpreter that hosts pyodide has the setup dependencies installed.
	PDFIUM_PLATFORM="sourcebuild-native" BUILD_PARAMS="--pyodide --vendor all --no-vendor libc++ {{BUILD_PARAMS}}" pyodide build . -vv {{args}}  # -nx

[script]
pyodide-test wheel='dist/pypdfium2-*-pyemscripten_*_wasm32.whl':
	{{verbose}} export PATH="${PWD}/.pyodide-venv/bin:${PATH}"
	pip install {{wheel}}
	pip install pillow numpy pytest
	python -m pytest tests/

pyodide *args: (pyodide-build args) pyodide-venv-create pyodide-test
