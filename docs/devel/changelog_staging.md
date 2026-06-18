<!-- SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- `mips64le` wheel added to release. `build_toolchained.py` is now capable of building it, based on upstream's `mips64el` target (with patches). This took a great deal of tinkering.
- `sbuild_one.yaml` now also docker-tests Linux wheels, to make sure cross-compiled builds actually work.
