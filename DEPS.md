<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

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

* pip >= 21.3 [^1]
* setuptools
* wheel
* ctypesgen

[^1]: It is important that you provide a recent version of pip because pypdfium2
      relies on in-place packaging without an intermediate temporary directory.
      See [issue #56](https://github.com/pypdfium2-team/pypdfium2/issues/56).

## Tests

* pytest


## Documentation

* sphinx [^2]
* sphinx-rtd-theme
* sphinxcontrib-programoutput

[^2]: `>= 4.4.0` recommended for full functionality.


## Utilities

* make
* importchecker
* codespell
* twine
* check-wheel-contents
