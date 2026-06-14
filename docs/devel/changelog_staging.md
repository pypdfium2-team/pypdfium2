<!-- SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release

*Dependency updates*
- Updated `build_toolchained.py` PDFium pin from `7191` to `7890`. Despite the gap, this turned out fairly straightforward.
- Updated `build_native.py` PDFium pin from `7841` to `7890`.
- Updated `gn-dist` from `2385` to `2407.1`, to match the revision specified in upstream's `DEPS` file.
- Updated cibuildwheel to `4.1.0`.
- Let `install-static-clang.sh` use latest.
- We now try to track latest PDFium in CIBW targets that use `build_native.py` with GCC, as this mode needs few patches.
  In releases, this affects `musllinux_{x86_64,i686,aarch64,armv7l}`. Let's see how this goes.
  If it breaks too often, we may go back to the pinned version or even `pdfium-binaries` for some musl targets.

*Packaging*
- Corrected minimum macOS requirement to `12_0`, as determined by `vtool -show-build`. (Upstream config no longer specifies a deployment target.)
- Lowered `riscv64` wheel's glibc requirement from `2_38` to `2_34` by using upstream's sysroot.

*API changes*
- Fixed a long-standing issue concerning formenv autoclose logic.
  `PdfDocument` stores the formenv, but `PdfFormEnv` referenced back to the parent `PdfDocument` including in the formenv's finalizer, forming a reference circle / indirect self-reference. This is illegal with `weakref.finalize()`.
  Addressing this issue properly required some changes to the public API:
  * `PdfFormEnv`: The `pdf` attribute and `parent` alias have been removed. Since `pdf` is created on the caller side, it is expected that callers would access their object directly rather than through the formenv.
  * Formenv lifetime is now managed through `PdfDocument`.
    `PdfFormEnv.close()` has been deprecated and is now a no-op. It is superseded by the new `PdfDocument.close_forms()` API.
  * `PdfPage.parent` now always points to a `PdfDocument`, not sometimes a `PdfFormEnv`.
    Conversely, page weakrefs are always stored on `PdfDocument`, not sometimes on `PdfFormEnv`.
  
  We are aware that, technically, this is an API-breaking change, but it has been decided not to increment the major version, given that `PdfFormEnv`'s `pdf` and `parent` attributes are insignificant to most callers, and removing them helps fix a real issue.
  
  The exact consequences of this self-reference are yet unclear to us, but memory leaks (due to finalizers not being called) and/or corruption seem possible.
  Thanks to `@noxthot` for a report that triggered this investigation.

*Setup, Build scripts & Workflows*
- Finally, prevent custom setup code from running multiple times in `pip install` by deferring data files generation into `build_py`, as suggested in cibuildwheel FAQ.
  Also, make the DLL path available to the tagging stage.
  This took some refactoring the control flow.
- `build_toolchained.py`: Significantly improved code style. In `PORTABLE_MODE`, added ability to use a sysroot and/or clang (requires passing `--clang-path ...`). Fix `install_buildtools()` by calling it before any depot_tools wrappers are added to `PATH`.
- Pragmatic `build_native.py` changes to make updating a bit more feasible:
  Patches for legacy GN and the transitional `--no-legacy-gn` option have been removed; recent GN is now required.
  Clang patches now just aim for compatibility with clang >= 22, much reducing patch complexity. For clang versions older than that, `--clang-as-gcc` mode is implicitly enabled.
  More patches have been simplified, removed, changed to autopatch or upstreamed (pending removal, need to await dependency rolls).
  Overall, `build_native.py` is now more focused on producing builds with cibuildwheel; maintainability and easier updates are prioritized over excess compatibility with older dependencies. Basically, we will require what pdfium requires.
- On Linux with glibc, `build_native.py` is now capable of using a sysroot. With our current cibuildwheel config, this can be used to lower the glibc requirements of `manylinux_{ppc64le,riscv64,armv7l}` (opt-in via `USE_SYSROOT=1`).
- Made the PDFium version configurable in cibuildwheel config and workflows.
- Added `secrets: inherit` to trigger workflows to hopefully fix a publish issue caused by the change to reusable workflow calls.
- Other setup improvements. Use plain `git` instead of GH API to get the ctypesgen revision. Drastically speed up attestation verification by sharing the trusted root.
