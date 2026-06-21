<!-- SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- New platforms: `manylinux_2_17_{mips64le,mipsle}` wheels added to release. `build_toolchained.py` is now capable of building these, based on upstream's `mips64el` and `mipsel` targets (with minor patches). This took a great deal of tinkering, however.
  Like `loongarch64`, PyPI does not accept MIPS wheels (yet), so they are only released to GitHub.
  Also, `pip` actually seems incapable of installing platform wheels on MIPS. We are providing a workaround script to bypass this limitation. Usage e.g. `./utils/enforce_install.sh ~/.local manylinux_2_17_mips64le ./pypdfium2-5.11.0-*.whl`.
  The `mipsle` build is untested, for lack of a container image and binfmt handler.
- Work around a bindings generation issue on Windows by avoiding inclusion of system `windows.h`.
  Added a notice to the Readme that ctypesgen may not work too well on non-Linux systems.
  Make test suite pass when reference bindings are used.
- Fix conda packaging of `pypdfium2_raw`, which was broken by the setup changes in 5.10.
  The root issue in setup with `PYPDFIUM_MODULES=raw` now requiring a pre-generated version file remains, though.
- Corrected minimum iOS requirement to `26_0` as per `macholib`.
  (We do not release iOS wheels but it is handled in setup.)
- `sbuild_one.yaml` now also tests Linux targets in Docker, to make sure cross-compiled builds actually work.
- Start using `ubuntu-26.04` and `windows-11-vs2026-arm` runners. Some workflows intentionally stick with `ubuntu-24.04` for the time being so we can keep testing older Python versions. (On `ubuntu-26.04`, the lowest python version shipped by `actions/setup-python` is 3.10 which is pretty high considering that some older distributions are still running Python 3.6.)
- `get_cross_deps.py`: Use GCC 16 on `ubuntu-26.04`, and GCC 14 on `ubuntu-24.04`.
- Docs: Comprehensive platform support table added – check it out!
- Put up a notice that AI issues/PRs are banned from this project, and updated templates accordingly.
  Any users who continue to file AI issues will be blocked.
  After half a dozen consecutive issues and PRs full of confusion, bloat and wildly invented false claims, which nearly all turned out to have been produced by Claude Code, we feel compelled to take this step.
  Frankly, dumping a big heap of AI garbage will ultimately take everyone involved far more time than writing a few truthful, hallucination-free lines on your own.
  **If you encounter an issue, our condition for your chance to have us investigate (and hopefully fix) your issue is that you must act respectfully and provide a workable bug report without any AI involvement.**
  If you want to keep talking to your clanker, that's your choice, but pypdfium2's issue tracker is not a waste deposit for AI garbage!
