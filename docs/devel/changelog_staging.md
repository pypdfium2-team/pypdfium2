<!-- SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- `mips64le` wheel added to release. `build_toolchained.py` is now capable of building it, based on upstream's `mips64el` target (with patches). This took a great deal of tinkering.
- `sbuild_one.yaml` now also docker-tests Linux wheels, to make sure cross-compiled builds actually work.
- CI: Updated to `ubuntu-26.04` and `windows-11-vs2026-arm` runners (mostly).
- `get_cross_deps.py`: Use GCC 16 on `ubuntu-26.04`, and GCC 14 on `ubuntu-24.04`.
