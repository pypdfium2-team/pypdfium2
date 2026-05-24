<!-- SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- Finally updated native sourcebuild from pdfium `7191` to `7841`.
  Updating the script & patches, and tracking down any issues that cropped up, adding new patches to fix them, turned out to be a huge undertaking.
- Created `gn-dist` project providing recent builds of GN (`generate-ninja`) for Linux (glibc and musl, full set of architectures).
  Updated cibuildwheel config and workflows accordingly to use `gn-dist` rather than outdated distro packages of GN.
  Scripting to build GN from source previously included in pypdfium2's setup has moved to `gn-dist`.
- Workflows overhaul.
  * Deduplicated `workflow_dispatch` and `workflow_call` inputs using YAML anchors & aliases (available on GHA since 09/2025).
  * Replaced `benc-uk/workflow-dispatch` action with reusable workflow calls.
  * Deduplicated series of individual jobs by switching to matrices. Handle `if`-conditions through an input parameter to the called workflow, because (unlike jobs) matrix entries have no built-in conditionality.
  * Updated to Python `3.14` (mostly). Simplified test matrices to probe just a few Python versions (e.g. `3.8, 3.11, 3.14`).
