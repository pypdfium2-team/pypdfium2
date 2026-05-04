<!-- SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- Autoclose machinery update.
  + Encapsulate finalizer state in a mutable object.
  + Objects now remove themselves from their parent's kids cache on garbage collection / closing, to avoid accumulation.
  + Global `ObjectTracker` added (objects are grouped by type and remove themselves from the tracker on finalization likewise). This may allow to destroy and re-initalize the library during a session.
  + Fixed some issues and inconsistencies in autoclose hooks that were unmasked by the above changes.
    * `PdfDocument.page_as_xobject()` now registers the XObject as a child of `dest_pdf` rather than `self`.
    * Mark pageobjects (`PdfObject`) as untracked.
    * For pages registered as kids of a formenv, `PdfPage.parent` now points at the formenv.
      This means the `.parent` property should be seen as purely an autoclose hook and not something to use for other purposes.
    * Fixed a test case to use `_detach_finalizer()` instead of `_finalizer.detach()`.
  + Should any issues surface with these changes (e.g. hitting assertions, or performance concerns), please let us know. Provide logs with `DEBUG_AUTOCLOSE` enabled if applicable.
- `PdfPage.get_objects()`: Added `textpage` passthrough parameter. This is required for `PdfTextObj.extract()`. Raise a meaningful exception if the textpage is missing. Demonstrate `.extract()` in pageobjects CLI.
- `PdfFont.get_base_name()`, `.get_family_name()`: decoding `errors` option added, now defaults to `"replace"`.
- New helpers `PdfFont.load_standard()`, `.STANDARD_FONTS` and `PdfDefaultTTFMap` added.
- Errchecks added to `PdfPage.get_rotation()`, `.insert_obj()` and `PdfUnspHandler.setup()`.
- New font diagnostic CLIs added (`pypdfium2 fonts` and `default-fonts`). Optional dependency `tabulate`.
- In the CLI dispatcher, try to load only the module that is actually used.
- CLI / `setup_logging()`: Fix warnings to be shown by removing an incorrect `logging.captureWarnings(True)` (that would require configuring the `py.warnings` logger or root logger which we did not do). Instead, use just `warnings.simplefilter("always")` for now. Also, fix `DEBUG_SYSFONTS` being a boolean option.
