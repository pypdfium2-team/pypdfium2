<!-- SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- New platform: `manylinux_2_17_mips64le` wheel added to release. `build_toolchained.py` is now capable of building it, based on upstream's `mips64el` target (with patches). This took a great deal of tinkering.
  Like `loongarch64`, PyPI does not accept MIPS wheels (yet), so they are only released to GitHub.
  Also, `pip` actually seems incapable of installing platform wheels on MIPS. We are providing a workaround script to bypass this limitation. Usage e.g. `./utils/enforce_install.sh ~/.local manylinux_2_17_mips64le ./pypdfium2-5.11.0-*.whl`.
- `sbuild_one.yaml` now also docker-tests Linux wheels, to make sure cross-compiled builds actually work.
- CI: Updated to `ubuntu-26.04` and `windows-11-vs2026-arm` runners (mostly).
- `get_cross_deps.py`: Use GCC 16 on `ubuntu-26.04`, and GCC 14 on `ubuntu-24.04`.
