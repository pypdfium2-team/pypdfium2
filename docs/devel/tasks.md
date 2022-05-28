<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Tasks

(These are various tasks for the maintainer to keep in mind, in no specific order.)

### Main Code
* Switch rendering to `FPDF_RenderPageBitmapWithMatrix()` (more flexible, easier cropping, maybe possibility to add margins and flip), and use `FPDFPage_Flatten()` for form rendering as there apparently is no matrix rendering counterpart to `FPDF_FFLDraw()`.

### Setup Infrastructure
* sourcebuild/win: fix dynamic values in `resources.rc`.
* PDFium's build system is over-complex because of the tight integration with Chromium. Just getting the sources takes unusually long due to the huge toolchains. That's why it would be good if we could create a custom CMake build system for PDFium, so as to speed up the process and shrink the dependency tree. We should still keep the current build script for PDFium contributing, though.

### Tests
* Add test case for rendering a PDF with interactive forms.

### Documentation
* Move development section of the Readme into a dedicated file and add some more information.
* Add a ctypes primer explaining how to interoperate with the PDFium C API.

### GitHub Workflows
* Restructure workflow so that it can be run without the publishing part.
* Make it possible to run test_release on wheels that are not published yet (will probably need upload-artifact and download-artifact actions).
* Set up CodeQL (see `Code security and analysis -> Code scanning` in the settings).
* Add a new workflow to test the build script.

### Miscellaneous
* Ask Linux distributors to package PDFium, as this could greatly simplify the installation of pypdfium2 for many users. Since most distributions are already compiling PDFium for their Chromium package anyway, it should be feasible to build PDFium as a dynamically linked library and add a development package containing the header files. To prepare, we should add means to plug in PDFium headers from an arbitrary location using a custom setup environment variable (PDFIUM_INCLUDE_DIR or something).
