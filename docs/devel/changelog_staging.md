<!-- SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release

*Runtime*
- `PdfDocument` and `PdfImage.load_jpeg()`: With byte stream input, in the `_buffer_reader` callback, check that the number of bytes read into the buffer is no less than the buffer's size, otherwise indicate error.
  `@Stjorn` filed a security ticket that triggered this change; however we consider this more of a theoretical safety *enhancement* and not actually a vulnerability, since under valid cirucmstances we do not envisage a situation where `readinto()` would fall short on data. It's clear enough that it is invalid to modify a file while bound by an object handle, and an attacker being able to do that would imply an already heavily compromised system. [No exploit from the heavens.](https://vulnbrocards.com/brocards/vb002-no-exploit-from-heavens/) Updated documentation.
  (With older versions of pypdfium2, consider wrapping buffer input so that `readinto()` raises an exception if it could not consume enough data to fill the buffer.)
- In `PdfBitmap`, unconditionally call `FPDFBitmap_Destroy()` when the bitmap is closed/finalized, i.e. including bitmaps created from a native, pdfium-external buffer (the default). The API does not affect external buffers, but assumably should still be called to release the `FPDF_BITMAP` shell itself.
- On foreign bitmaps, `PdfBitmap.close()` now warns about being a potentially unsafe operation, since it frees the C-side buffer. Set `.warn_on_close = False` to silence the warning, if you have made sure your usage is safe.
- In `AutoCloseable`, avoid assigning `self` to an instance attribute. This should result in improved GC behavior. Many thanks to James Barlow for pointing this out.
- Added bindings to some new PDFium APIs, along with CLI integration:
  * `PdfAttachment`: `.{get,set}_desc()` to read/write attachment descriptions, and `.get_subtype()` to obtain the MIME type.
  * `PdfBookmark.get_style()` and `PdfBookmarkStyle`.
  * _Note: On platforms where we pin the PDFium version, the underlying PDFium APIs are not available yet, but they will be once the build scripts are updated to a new base._

*Platforms*
- Pyodide: Patch freetype load flags to avoid `FT_Load_Glyph()` somehow corrupting the heap. It seems that this addresses the previously encountered crashes/freezes; however, the exact cause remains elusive. Anyway, many thanks to Hood Chatham for this finding.
  * Dropped debug symbols. Enabled PyPI upload. Updated documentation.

*Setup*
- Refactored ctypesgen integration. It is now cloned into pypdfium2's source tree and bundled in sdists. This avoids having an external git URL in pyproject setup dependencies that defeats the idea of a hermetic (self-contained) package index. ctypesgen's own setup and versioning code has been removed, owing to the project's special status as setup-only dependency with a head-to-head development model that allows for a constantly evolving API. See the [updated pypdfium2-ctypesgen `README.md`](https://github.com/pypdfium2-team/ctypesgen/blob/acf905804b2ae50d2b230308e1ca62875f4fe16c/README.md#installation) for integration instructions. This also made Python 3.6 compatibility straightforward to restore after all, aligning to a common baseline with pypdfium2 and gn-dist.
- Dropped module splitting (`PYPDFIUM_MODULES={raw,helpers}`) and the `system-generate` target, which had been introduced for pypdfium2's own conda packaging (see below).<br>
  We recognize that module splitting may still be desirable in some downstream packaging contexts; however, the dynamic implementation had been standing in the way of a proper `pyproject.toml` migration, since the `[project]` table does not allow for `name` to be specified dynamically. This means we could not retain a first-party dynamic setting much longer without impairing the project's progress. Instead we suggest that you simply patch the project name / module include rules (possibly via some kind of automation) if module splitting is needed. This change does not affect the module layout in `src/` which upholds the logical separation.
- Lowered iOS min version from `26_0` to `17_0` thanks to an upstream contribution. (We have not released any iOS wheels yet, but it is handled in setup.)

*Conda*

Removed pypdfium2's own conda packaging (`pypdfium2-team` channel), following [thorough](https://github.com/mindee/doctr/discussions/2127) [consideration](https://github.com/mindee/doctr/issues/113#issuecomment-5340008535).
Upstream `pdfium-binaries` (`bblanchon` channel) followed suit and removed conda packaging as well, since pypdfium2 was the only known dependant.

- Key reasons include that it ended up covering far less platforms than we do with PyPI wheels, did not integrate with our own build strategies, and seemed fraught with workarounds.
In part, this has been a result of outsourcing the pdfium dependency (which seemed about the only viable option prior to [CEP 20](https://github.com/conda/ceps/blob/main/cep-0020.md)), along with other limitations, like conda generally supporting less platforms, and tight storage limits at `anaconda.org` that leave maintainers with tradeoffs between release frequency and platform inclusion vs. sustainability.
  There is no fallback setup, either, which even seems to be an intentional limitation of conda's.
- To add to that, builds in a custom channel are inaccessible to dependents within the main anaconda/conda-forge ecosystems themselves, and generally a pain to manage, which resulted in negligible demand compared to PyPI. In short, the problems are manifold and technical debt is not far off.
- This means conda is effectively a third-party package environment similar to nixpkgs or Linux distribution packaging, unlike PyPI, which is a first-party package index where upstream authors publish directly. Conda build tools did not feel like being conceived for in-project packaging, either (the contrast to PyPA build backends is quite stark).
  Overall, there has been an unjustifably high complexity and amount of workarounds in relation to the low or nonexistent benefit.
- To be clear, any builds of pypdfium2 in conda-forge or anaconda/main are [unofficial (third-party)](https://github.com/pypdfium2-team/pypdfium2#unofficial-packages). We generally do not recommend using third-party distributions of pypdfium2, and their varying maintainership is a potential concern as well. Anyway, we cannot support what we don't maintain.
- Instead, we want to highlight that you can just install pypdfium2 from PyPI even in a conda env. There are no mandatory runtime dependencies, so the usual reasons against mixing in PyPI packages do not apply.
- *Maintainer's note: If upstream ever (drastically) improve integration with custom channels to allow for meaningful first-party publishing, the door remains ajar to redo pypdfium2's conda packaging the CEP 20 way.*
