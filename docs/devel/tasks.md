<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Tasks

These are various tasks for the maintainer to keep in mind, in no specific order.
Also see the issues panel and inline `TODO` marks in source code.

### Main Code
* Raise an exception if objects were not closed in correct order. On `__del__`, issue a warning if an object is not closed yet.
* Investigate if we can implement interruptible rendering.
* When rendering with multiple processes and bytes were provided as input, is the memory duplicated or shared? If it's duplicated, find a way to share it or write a tempfile instead.
* Move init/destroy into a separate file. Provide public init/destroy functions, given that embedders who deal with long-running applications might not want to have PDFium in memory all the time.
* Make the bindings file `_pypdfium.py` public ?
* Add support models for attachments and image extraction.
* Ensure we correctly handle PDFium return codes indicating failure.
* Consolidate and extend helper classes.

### Setup Infrastructure
* craft_wheels: add means to skip platforms for which artefacts are missing.
* update_pdfium: only generate the bindings file once for all platforms.
* update_pdfium: add option to download a custom pdfium-binaries release (i. e. not the latest).
* packaging_base: use a class for `VerNamespace` so it can be flushed more easily (?)
* use the logging module rather than `print()`.
* autorelease: on the long term, consider switching to a proper configuration file rather than placing empty indicator files in a directory.

### Tests
* Unify rendering tests with `RenderTestCase` class and a single, parametrized function
* Overhaul outdated tests and improve coverage
* Add new test cases
    * finding of nested objects
* Find a better replacement for `importchecker`.

### Documentation
* Add/rewrite remaining Readme sections.

### GitHub Workflows
* release: restructure so that it can be run without the publishing part.
* test_release: make it possible to run this workflow on wheels that are not published yet (will probably need upload-artifact and download-artifact actions).
* test_release: add `pypy` interpreter.
* Add a new workflow to test the build script.
* Set up CodeQL (see `Code security and analysis -> Code scanning` in the settings).

### Miscellaneous
* Ask Linux distributors to package PDFium.
* Discuss rendering methods in PDFium's mailing list (we'd like a way to combine matrix, colour scheme and interruptibility).
* Add means to plug in PDFium headers/binaries from an arbitrary location, probably using custom environment variables.
* Keep in mind that `ctypes.pythonapi` exists. Maybe we could replace our wonky `id()` based keep-the-object-alive approach with proper incref/decref calls?
* Find out if/when we need to use `ctypes.byref()`.
