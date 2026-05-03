<!-- SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- Autoclose machinery update.
  + Encapsulate finalizer state in a mutable object.
  + Objects now remove themselves from their parent's kids cache on garbage collection / closing, to avoid accumulation.
  + Global `ObjectTracker` added (objects are grouped by type and remove themselves from the tracker on finalization likewise). This may allow to destroy and re-initalize the library during a session.
  + Fixed some issues and inconsistencies in autoclose hooks that were unmasked by the above changes. `PdfDocument.page_as_xobject()` now registers the XObject as a child of `dest_pdf` rather than `self`. Pageobjects (`PdfObject`) are marked as untracked. For pages registered as kids of a formenv, `PdfPage.parent` now points at the formenv. The `.parent` property should now be seen as purely an autoclose hook and not something to use for other puposes.
  + Should any issues surface with these changes (e.g. hitting assertions, or performance concerns), please let us know and we'll see what can be done. Provide logs with autoclose debugging enabled if applicable.
- `PdfPage.get_objects()`: Added `textpage` passthrough parameter. This is required for `PdfTextObj.extract()`. Raise a meaningful exception if the textpage is missing. Demonstrate `.extract()` in pageobjects CLI.
- `PdfFont.get_base_name()`, `.get_family_name()`: decoding `errors` option added, now defaults to `"replace"`.
- New helpers `PdfFont.load_standard()` and `PdfDefaultTTFMap` added.
- New font diagnostic CLIs added (`pypdfium2 fonts` and `default-fonts`). Optional dependency `tabulate`.
- Errchecks added to `PdfPage.get_rotation()`, `.insert_obj()` and `PdfUnspHandler.setup()`.
