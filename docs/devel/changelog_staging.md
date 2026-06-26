<!-- SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- Build scripts: Updated PDFium pin from `7891` to `7913`.
- New API `PdfBookmark.get_color()` added. This is based on upstream's new `FPDFBookmark_GetColor()` API. Integrated `get_color()` into `pypdfium2 toc` CLI.
  Thanks to Aryan Krishnan for the upstream part.
- New platforms: `manylinux_2_17_{mips64le,mipsle}` wheels added to release.
  * `build_toolchained.py` is now capable of building these, based on upstream's `mips64el` and `mipsel` targets (with minor patches). This took a great deal of tinkering, however.
  * Like `loongarch64`, PyPI does not accept MIPS wheels (yet), so they are only released to GitHub.
  * Note that `pip` actually rejects our wheels because MIPS is not officially part of the manylinux standard and thus not contained in pip's internal whitelist. This can be remedied by re-tagging with `wheel` locally to match the host's `sysconfig.get_platform()` value. See [pip ticket #14095](https://github.com/pypa/pip/issues/14095) for more info.
  * The `mipsle` build is untested (apart from `file` showing the correct target signature), for lack of a container image and binfmt handler.
- Docs: Comprehensive [platform support table](https://pypdfium2-team.github.io/pypdfium2/platforms.html) added – check it out!
- Work around a bindings generation issue on Windows by avoiding inclusion of system `windows.h`.
  Added a notice that ctypesgen may not work too well on non-Linux systems.
- Honor reference bindings properly: don't download headers or reuse cached bindings.
  Make test suite pass when reference bindings are used.
- Fix conda packaging of `pypdfium2_raw`, which was broken by setup changes in 5.10.
  The root issue in setup with `PYPDFIUM_MODULES=raw` now requiring a pre-generated version file remains, though.
- Corrected minimum iOS requirement to `26_0` as per `macholib`.
  (We do not release iOS wheels but it is handled in setup.)
- `sbuild_one.yaml` now also tests Linux targets in Docker, to make sure cross-compiled builds actually work.
- Start using `ubuntu-26.04` and `windows-11-vs2026-arm` runners. Some workflows intentionally stick with `ubuntu-24.04` for the time being so we can keep testing older Python versions. (On `ubuntu-26.04`, the lowest python version shipped by `actions/setup-python` is 3.10 which is pretty high considering that some older distributions are still running Python 3.6.)
- `get_cross_deps.py`: Use GCC 16 on `ubuntu-26.04`, and GCC 14 on `ubuntu-24.04`.
- Put up a notice that AI issues/PRs are banned from this project, and updated templates accordingly.
  Any users who continue to file AI issues will be blocked.
  After half a dozen consecutive issues and PRs full of confusion, bloat and wildly invented false claims, which nearly all turned out to have been produced by Claude Code, we feel compelled to take this step.
  **If you encounter an issue, our condition for your chance to have us investigate (and hopefully fix) your issue is that you must act respectfully and provide a workable bug report without any AI involvement.**
  TLDR pypdfium2's issue tracker is not a waste deposit for AI garbage.
