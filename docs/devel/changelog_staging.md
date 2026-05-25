<!-- SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- Finally updated native sourcebuild from pdfium `7191` to `7841`.
  Updating the script & patches, and tracking down any issues that cropped up, adding new patches to fix them, turned out to be a great deal of work.
- Created `gn-dist` project providing recent builds of GN (`generate-ninja`) for Linux (glibc and musl, full set of architectures).
  Updated pypdfium2's cibuildwheel config and workflows accordingly to use `gn-dist` rather than outdated distro packages of GN.
  Scripting to build GN from source previously included in pypdfium2's setup has moved to `gn-dist`.
  In `build_native.py`, patches for legacy GN are still included and enabled by default for now, but you can pass `--no-legacy-gn` to skip them.
  To make updating more straightforward, this mode will be made default and the patches will be removed in the future.
- Workflows overhaul.
  * Deduplicated `workflow_dispatch` and `workflow_call` inputs using YAML anchors & aliases (available on GHA since 09/2025).
  * Replaced `benc-uk/workflow-dispatch` action with reusable workflow calls.
  * Deduplicated series of individual jobs by switching to matrices. Handle `if`-conditions through an input parameter to the called workflow, because (unlike jobs) matrix entries have no built-in conditionality.
  * Updated to Python `3.14` (mostly). Simplified test matrices to probe just a few Python versions (e.g. `3.8, 3.11, 3.14`).
- Limited who has maintainer access to the repo and project sites.
  `mara004`, the author and so far only active committer of pypdfium2, now is (and will remain) sole owner.
  Inactive co-maintainers no longer have access, but are welcome to submit PRs.
  In the event of the author being unable to pursue this project further, it can be forked and a new maintainer may build their own trust, but given the risks inherent to maintainer changes, it has been decided that pypdfium2 will remain `mara004`'s personal project. The existing userbase will not be handed over to another maintainer.
