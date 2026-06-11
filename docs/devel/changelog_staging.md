<!-- SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release

*Dependency updates*
- Updated `build_toolchained.py` from PDFium `7191` to `7884`. Despite the gap, this turned out fairly straightforward.
- Updated `build_native.py` from PDFium `7841` to `7880`.
- Updated `gn-dist` from `2385` to `2407`, to match the revision specified in upstream's `DEPS` file.
- We now try to track latest PDFium in CIBW targets that use `build_native.py` with GCC, as this mode needs few patches.
  In releases, this affects `musllinux_{x86_64,i686,aarch64,armv7l}`. Let's see how this goes.
  If it breaks too often, we may go back to the pinned version or even `pdfium-binaries` for some musl targets.
- Updated cibuildwheel to `4.0.0`.
- Let `install-static-clang.sh` use latest.

*API changes*
- Fixed a long-standing issue concerning formenv autoclose logic.
  `PdfDocument` stores the formenv, but `PdfFormEnv` referenced back to the parent `PdfDocument` including in its finalizer, forming a reference circle / indirect self-reference. This is illegal with `weakref.finalize()`.
  Addressing this issue properly required some changes to the public API:
  * `PdfFormEnv`: The `pdf` attribute and `parent` alias have been removed. Since `pdf` is created on the caller side, it is expected that callers would access their object directly rather than through the formenv.
  * Formenv lifetime is now managed through `PdfDocument`.
    `PdfFormEnv.close()` has been deprecated and is now a no-op. It is superseded by the new `PdfDocument.close_forms()` API.
  * `PdfPage.parent` now always points to a `PdfDocument`, not sometimes a `PdfFormEnv`.
    Conversely, page weakrefs are always stored on `PdfDocument`, not sometimes on `PdfFormEnv`.
  
  We are aware that, technically, this is an API-breaking change, but it has been decided not to increment the major version, given that `PdfFormEnv`'s `pdf` and `parent` attributes are insignificant to most callers, and removing them helps fix a real issue.
  
  The exact consequences of this self-reference are still unclear to us, since for some reason formenvs seem to have been garbage collected / finalized anyway, but sings of corruption have been observed.

*Setup*
- Finally, prevent custom setup code from running multiple times in `pip install` by deferring data files generation into `build_py`, as suggested in cibuildwheel FAQ.
  Also, make the DLL path available to the tagging stage so that minimum OS requirements could be auto-detected from binaries in the future, instead of hardcoding them.
  This took some refactoring the control flow.
- Corrected minimum macOS requirement to `12_0`, as determined by `vtool -show-build`. (Upstream config no longer specifies a deployment target.)
  In the future, we plan to split packaging across native hosts and automate tagging using auditwheel/delocate.

*Workflows & Build scripts*
- Made the PDFium version configurable in cibuildwheel config and workflows.
- Added `secrets: inherit` to trigger workflows to hopefully fix a publish issue caused by the change to reusable workflow calls.
- `build_toolchained.py`: Significantly improved code style. Added ability to use a sysroot in `PORTABLE_MODE` (requires bringing your own clang). Fix `install_buildtools()` by calling it before any depot_tools wrappers are added to `PATH`.
- Pragmatic `build_native.py` changes to make updating a bit more feasible:
  Patches for legacy GN and the transitional `--no-legacy-gn` option have been removed; recent GN is now required.
  Clang patches now just aim for compatibility with clang >= 22, much reducing patch complexity. For clang versions older than that, `--clang-as-gcc` mode is implicitly enabled.
  More patches have been simplified, removed, changed to autopatch or upstreamed (pending removal, need to await dependency rolls).
  Overall, `build_native.py` is now more focused on producing builds with cibuildwheel; maintainability and easier updates are prioritized over excess compatibility with older dependencies. Basically, we will require what pdfium requires.
