<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Dependencies

## Runtime

* Python >= 3.5
* Pillow


## Build

### System packages

* git
* gcc

#### Additional system packages for Native Build

*Important*: The compiler needs to be fully compliant with C++17

* llvm/clang
* lld
* gn (generate-ninja)
* ninja (ninja-build)

### Python packages

* pip [^1]
* setuptools
* setuptools-scm [^2]
* build
* ctypesgen [^3]
* wheel


## Tests

* pytest


## Documentation

* sphinx (>= 4.4.0 recommended)
* sphinx-rtd-theme >= 1.0
* sphinxcontrib-programoutput
* docutils >= 0.17
* myst-parser


## Utilities

* make
* importchecker
* codespell
* reuse
* twine
* check-wheel-contents


[^1]: A recent version of pip is strongly recommended.

[^2]: Required for the `sdist` target to include all required files.

[^3]: You are encouraged to install the latest ctypesgen from git main, as lots of important
      improvements have been done since the last release on PyPI, which is rather outdated.
