<!-- SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- Updated `build_toolchained.py` from PDFium `7191` to `7884`. Despite the gap, this turned out fairly straightforward.
  Also, significantly improved code style. Added ability to use a sysroot in `PORTABLE_MODE` (requires bringing your own clang). Fix `install_buildtools()` by calling it before any depot_tools wrappers are added to `PATH`.
- Updated `build_native.py` from PDFium `7841` to `7880` (see below for more info).
  Added patch to fix a build system issue introduced upstream.
  Updated `gn-dist` from `2385` to `2407`, to match the revision specified in upstream's `DEPS` file.
- Finally, prevent custom setup code from running multiple times in `pip install` by deferring data files generation into `build_py`, as suggested in cibuildwheel FAQ.
  Also, make the DLL path available to the tagging stage so that minimum OS requirements could be auto-detected from binaries in the future, instead of hardcoding them.
  This took some refactoring the control flow.
- Corrected minimum macOS requirement to `12_0`. Added an experimental code path to auto-detect the min version using `macholib`. This is not active in packaging yet, since a native macOS host is needed. (We plan to split packaging across native hosts in the future. Currently, all repacking is done in a single job.)
- Pragmatic `build_native.py` changes to make updating a bit more feasible:
  Patches for legacy GN and the transitional `--no-legacy-gn` option have been removed; recent GN is now required.
  Clang patches now just aim for compatibility with clang >= 22, much reducing patch complexity. For clang versions older than that, `--clang-as-gcc` mode is implicitly enabled.
  More patches have been simplified, removed, or changed to autopatch.
  Overall, `build_native.py` is now more focused on producing builds with cibuildwheel; maintainability and easier updates are prioritized over excess compatibility with older dependencies. Basically, we will require what pdfium requires.
- Updated cibuildwheel config and workflows to make the pdfium version configurable. We now try to track latest with the targets that use GCC, because this mode barely needs patching. In releases, this affects `musllinux_{x86_64,i686,aarch64,armv7l}`. Let's see how this goes. If it breaks too often, we can go back to the pinned version or even `pdfium-binaries` for some musl targets.
- Added `secrets: inherit` to trigger workflows to hopefully fix a publish issue caused by the change to reusable workflow calls.
