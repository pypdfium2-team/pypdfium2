<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

Tasks
=====

(These are various tasks for the maintainer to keep in mind, in no specific order.)

* Rename `translate_...()` utility functions to something shorter. Maybe switch to dictionaries?
* Increase test coverage. Probably need to overhaul testing completely. We would like to have a test for every single passage of the support model code. Some automated tests for the setup infrastructure would also be nice.
* Add test case for rendering a PDF with interactive forms.
* Move development section of the Readme into a dedicated file and add some more information.
* Add a ctypes primer explaining how to interoperate with the PDFium C API.
* Add capabilities to render a certain area of a page (issue #38).
* Think about the possibility of using `FPDFPage_Flatten()` rather than `FPDF_FFLDraw()` and all the extra commands that it needs.
* Create a support model for progressive rendering (`FPDF_RenderPageBitmap_Start()` & `IFSDK_PAUSE`)
* Set the version appropriately when doing a source build (i. e. append current PDFium commit hash to version string).
* sourcebuild/win: fix dynamic values in resources.rc
* Look into setting up Github Actions CI.
* Ask Linux distributors to package PDFium, as this could greatly simplify the installation of pypdfium2 for many users. Since most distributions are already compiling PDFium for their Chromium package anyway, it should be feasible to build PDFium as a dynamically linked library and add a development package containing the header files. To prepare, we should add means to plug in PDFium headers from an arbitrary location using a custom setup environment variable (PDFIUM_INCLUDE_DIR or something).
