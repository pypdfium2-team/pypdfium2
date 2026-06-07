<!-- SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- `build_native.py` changes to make updating more straightforward:
  Patches for legacy GN and the transitional option `--no-legacy-gn` have been removed; recent GN is now required.
  Clang patches now just aim for compatibility with clang >= 22, much reducing patch complexity. For clang versions older than that, `--clang-as-gcc` mode is implicitly enabled.
  More patches have been simplified, removed, or changed to autopatch.
  Added a new patch to fix a build system issue introduced upstream.
  Updated to pdfium `7878`.<br/>
  Overall, `build_native.py` is now more focused on producing builds with cibuildwheel; maintainability and easier updates are prioritized over excessive compatibility with older dependencies. Basically we will require what pdfium requires and call it a day.
- Updated cibuildwheel config and workflows to make the pdfium version configurable. We now try to track latest with the targets that use GCC, because this mode barely needs patching. In releases, this affects `musllinux_{x86_64,i686,aarch64,armv7l}`. Let's see how this goes. If it breaks too often, we can go back to the pinned version or even `pdfium-binaries` for some musl targets.
- Added `secrets: inherit` to trigger workflows to hopefully fix a publish issue caused by the change to reusable workflow calls.
