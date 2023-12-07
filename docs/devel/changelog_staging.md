<!-- SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release

- Removed multiprocessing from deprecated `PdfDocument.render()` API and replaced with linear rendering. See below for more info.
- Improved issue templates, added pull request template.
- conda/workflows: Added ability to (re-)build pypdfium2_raw bindings with any given version of pdfium. Fixes {issue}`279`.
- conda: Improved installation docs and channel config.
- Made reference bindings more universal by including V8, XFA and Skia symbols. This is possible due to the dynamic symbol guards.
- setup: Fixed blunder in headers cache logic that would cause existing headers to be always reused regardless of version. *Note, this did not affect release workflows, only local source re-installs.*
- Show path of linked binary in `pypdfium2 -v`.

#### Rationale for `PdfDocument.render()` deprecation

- The parallel rendering API unfortunately was an inherent design mistake: Multiprocessing is not meant to transfer large amounts of pixel data from workers to the main process.
- This was such a heavy drawback that it basically outweighed the parallelization, so there was no real performance advantage, only higher memory load.
- As a related problem, the worker pool produces bitmaps at an indepedent speed, regardless of where the receiving iteration might be, so bitmaps could queue up in memory, possibly causing an enormeous rise in memory consumption over time. This effect was pronounced e.g. with PNG saving via PIL, as exhibited in Facebook's `nougat` project.
- Instead, each bitmap should be processed (e.g. saved) in the job which created it. Only a minimal, final result should be sent back to the main process (e.g. a file path).
- This means we cannot reasonably provide a generic parallel renderer, instead it needs to be implemented by callers.
- Historically, note that there had been even more faults in the implementation:
  * Prior to `4.22.0`, the pool was always initialized with `os.cpu_count()` processes by default, even when rendering less pages.
  * Prior to `4.20.0`, a full-scale input transfer was conducted on each job (rendering it unusable with bytes input). However, this can and should be done only once on process creation.
- pypdfium2's rendering CLI cleanly re-implements parallel rendering to files. We may want to turn this into an API in the future.

**Due to the potential for serious issues as outlined above, we strongly recommend that end users update and dependants bump their minimum requirement to this version. Callers should move away from `PdfDocument.render()` and use `PdfPage.render()` instead.**
