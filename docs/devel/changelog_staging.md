<!-- SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
*Requirements*
- macOS `13.0+` is now required for current PDFium (declared in upstream config and confirmed with dylib header inspection). Updated wheel tags accordingly.
- Setup: Increased tool dependency requirements
  + `build_native.py` now expects `git >= 2.49.0` so we can use modern `git clone --revision` features.
  + If `gh` is installed, `gh >= 2.47.0` will be required, as we now assume availability of the `gh attestation` subcommand without consulting `gh --version`.

*Packaging / CI*

Largest CI/workflows rework yet ("Strategic builds"). Many testing gaps filled (see the updated platform support table).

- Dynamic selection of targets and Python versions across 3 build strategies (pdfium-binaries, `build_toolchained.py`, cibuildwheel/`build_native.py`). This means releases can now be made using any selection of targets/strategies, configurable through workflow inputs on a per-run basis.
- In principle, this would allow us to make releases just using our own builds, without external binaries. We plan to explore this from time to time. That said, pypdfium2's conda packages continue to be tied to the pdfium-binaries, and setup will continue to provide you with pdfium-binaries by default.
- Test multiple Python versions in one job (either the build job, or a dedicated test job if another runner image is needed). Share testing across build strategies through composite action / reusable workflow. Use Docker testing where needed. Added ability to test macOS Intel from arm64 through Rosetta emulation (`arch -x86_64` prefix).
- Split up pdfium-binaries packaging in individual jobs.
- Hash-pinned all actions across `pypdfium2`, `gn-dist` and the `ctypesgen` fork. Tightened permissions. Replaced superfluous actions with built-in `gh` CLI. Use exact commit hash rather than branch name to transfer state between jobs. `zizmor` compliance (with a few intentional suppressions).

*Setup*
- With 32-bit interpreters running on 64-bit hosts, setup should now select the 32-bit target.
- With pdfium-binaries, use (and cache) the included pdfium headers.
  In most cases, this should let us avoid upstream Gitiles, which turns out to be flaky in automated access.
