<!-- SPDX-FileCopyrightText: 2024 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- Added ability to define `$CTYPESGEN_PIN` when building sdist via `./run craft pypi --sdist`, which allows to reproduce our sdists when set to the head commit hash of `pypdfium2-team/ctypesgen` at the time of the build to reproduce. Alternatively, you may patch the relevant `pyproject.toml` entry yourself and use `PDFIUM_PLATFORM=sdist python -m build --sdist` as usual.
