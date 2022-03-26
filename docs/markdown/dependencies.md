<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Dependencies

## Runtime

* Python >= 3.5
* Pillow (optional)


## Build

### Python packages

* pip [^1]
* setuptools [^1]
* setuptools-scm [^2]
* build
* wheel
* ctypesgen [^3]

### System packages

* git
* gcc

#### Nativebuild Extras

* llvm/clang
* lld
* gn (generate-ninja)
* ninja (ninja-build)

*Important notes*:
- If you have multiple versions of llvm, make sure the latest version also has a corresponding lld install!
- A C++17 compliant compiler is highly recommended.

#### Windows Extras

* Powershell
* Visual Studio
* Windows SDK


## Tests

* pytest


## Documentation

* sphinx
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


[^1]: A recent version is strongly recommended.

[^2]: Required for the `sdist` target to include all required files.

[^3]: You are encouraged to install the latest ctypesgen from git main, as lots of important improvements have been done since the last release on PyPI, which is rather outdated.
