<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

Tasks
=====

(These are various tasks for the maintainer to keep in mind, in no specific order.)

* Allow for only returning bytes rather than creating an `Image.Image` object when rendering, so that callers may use the data in any way they like (e. g. directly inject into a GUI widget buffer), without having to go through an intermediate PIL object. Depending on how we will implement this, API breaking changes might be involved.
* Add capabilities to render a certain area of a page (issue #38).
* Add test case for rendering a PDF with interactive forms.
* Think about the possibility of using `FPDFPage_Flatten()` rather than `FPDF_FFLDraw()` and all the extra commands that it needs.
* Create a support model for progressive rendering (`FPDF_RenderPageBitmap_Start()` & `IFSDK_PAUSE`)
* Set the version appropriately when doing a source build (i. e. append current PDFium commit hash to version string).
* Sourcebuild: regroup patches to be operating system specific.
* Think about further extending support for older Python versions (see changelog).
* Create a `.readthedocs.yaml` configuration file (issue #32).
* Look into setting up Github Actions CI.
* Ask Linux distributors to package PDFium, as this could greatly simplify the installation of PyPDFium2 for many users. Since most distributions are already compiling PDFium for their Chromium package anyway, it should be feasible to build PDFium as a dynamically linked library and add a development package containing the header files. We could then add a custom setup file that will create bindings using the system-provided PDFium headers.
