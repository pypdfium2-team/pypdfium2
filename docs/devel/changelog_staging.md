<!-- SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- Major CI overhaul.
  + TODO
  + Hash-pinned all actions across `pypdfium2`, `gn-dist` and the `ctypesgen` fork. Tightened permissions. `zizmor` compliance (with a few intentional suppressions).

*Setup / Packaging*
- macOS `13.0+` is now required for current PDFium, according to dylib header inspection. Updated wheel tags accordingly.
- Increased tool dependency requirements
  + `build_native.py` now expects `git >= 2.49.0` so we can use modern `git clone --revision` features.
  + If `gh` is installed, `gh >= 2.47.0` will be required, as we now assume availability of the `gh attestation` subcommand without consulting `gh --version`.
- With 32-bit interpreters running on 64-bit hosts, setup should now select the 32-bit target.
- With pdfium-binaries, use (and cache) the included pdfium headers.
  In most cases, this should let us avoid upstream Gitiles, which turns out to be flaky in automated access.
