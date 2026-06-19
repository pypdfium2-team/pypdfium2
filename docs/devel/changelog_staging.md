<!-- SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- New platform: `manylinux_2_17_mips64le` wheel added to release. `build_toolchained.py` is now capable of building it, based on upstream's `mips64el` target (with patches). This took a great deal of tinkering.
  Like `loongarch64`, PyPI does not accept MIPS wheels (yet), so they are only released to GitHub.
  Also, `pip` actually seems incapable of installing platform wheels on MIPS. We are providing a workaround script to bypass this limitation. Usage e.g. `./utils/enforce_install.sh ~/.local manylinux_2_17_mips64le ./pypdfium2-5.11.0-*.whl`.
- Work around a bindings generation issue on Windows by avoiding inclusion of system `windows.h`.
  Added a notice to the Readme that ctypesgen may not work too well on non-Linux systems.
  Make test suite pass when reference bindings are used.
- Corrected minimum iOS requirement to `26_0` according to `macholib`.
  (We do not release iOS wheels but it is handled in setup.)
- `sbuild_one.yaml` now also docker-tests Linux wheels, to make sure cross-compiled builds actually work.
- Updated to `ubuntu-26.04` and `windows-11-vs2026-arm` runners (mostly).
- `get_cross_deps.py`: Use GCC 16 on `ubuntu-26.04`, and GCC 14 on `ubuntu-24.04`.
- Docs: Comprehensive platform support table added – check it out!
- Put up a notice that AI issues/PRs are banned from this project, and updated templates accordingly.
  Any users who continue to file AI issues will be blocked.
  After receiving half a dozen consecutive issues and PRs full of bloat, confusion and wildly invented false claims, which nearly all turned out to have been produced by Claude Code, we feel compelled to take this step.
  Honestly, letting AI output a big heap of garbage will ultimately take everyone involved far more time than writing a few truthful, hallucination-free lines on your own.
  TLDR: If you encounter an issue that you want to see fixed, do not use AI to write bug reports. If you do not want your issue fixed, fine, keep talking to your clanker, but pypdfium2's issue tracker is not a good place to offload its garbage.
