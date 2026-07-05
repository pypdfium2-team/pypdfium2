<!-- SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- Major CI overhaul.
  + TODO
  + All actions are now hash-pinned across `pypdfium2`, `gn-dist` and our `ctypesgen` fork.
- With 32-bit interpreters running on 64-bit hosts, setup should now select the 32-bit target.
- Increased tool dependency requirements:
  + `build_native.py` now expects `git >= 2.49.0` so we can use modern `git clone --revision` features.
  + If `gh` is installed, `gh >= 2.47.0` will be required, as we now assume availability of the `gh attestation` subcommand without consulting `gh --version`.
