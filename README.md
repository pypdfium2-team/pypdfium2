<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# pypdfium2

[pypdfium2](https://github.com/pypdfium2-team/pypdfium2) is a Python 3 binding to [PDFium](https://pdfium.googlesource.com/pdfium/+/refs/heads/main), the liberal-licensed PDF rendering library authored by Foxit and maintained by Google.


## Install/Update

### Install from PyPI

```bash
pip3 install --no-build-isolation -U pypdfium2
```

### Manual installation

The following steps require the system tools `git` and `gcc` to be installed and available in `PATH`. In addition, the Python dependencies `setuptools`, `setuptools-scm` `wheel`, `build`, and `ctypesgen` are needed. Also make sure that your `pip` version is up-to-date. For more information, please refer to [`dependencies.md`](docs/markdown/dependencies.md).

#### Package locally

To get pre-compiled binaries, generate bindings and install pypdfium2, you may run
```bash
make install
```
in the directory you downloaded the repository to. This will resort to building PDFium if no pre-compiled binaries are available for your platform.

#### Source build

If you wish to perform a source build regardless of whether PDFium binaries are available or not, you can do the following:
```bash
make build
```

In case building failed, you could try
```bash
python3 platform_setup/build_pdfium.py --nativebuild --check-deps
PYP_TARGET_PLATFORM="sourcebuild" python3 -m pip install . -v --no-build-isolation
```
to prefer the use of system-provided build tools over the toolchain PDFium ships with. The problem is that the toolchain is limited to a curated set of platforms, as PDFium target cross-compilation for "non-standard" architectures. (Make sure you installed all packages from the `Native Build` section of [`dependencies.md`](docs/markdown/dependencies.md), in addition to the default requirements.)

## Examples

### Using the command-line interface

Rasterise a PDF document:
```bash
pypdfium2 render document.pdf -o output_dir/ --scale 3
```

You may also rasterise multiple files at once:
```bash
pypdfium2 render doc_1.pdf doc_2.pdf doc_3.pdf -o output_dir/
```

Show the table of contents for a PDF:
```bash
pypdfium2 toc document.pdf
```

To obtain a list of subcommands, run `pypdfium2 help`. Individual help for each subcommand is available can be accessed in the same way (`pypdfium any_subcommand help`)

CLI documentation: https://pypdfium2.readthedocs.io/en/stable/shell_api.html


### Using the support model

Import pypdfium2:

```python3
import pypdfium2 as pdfium
```

Open a PDF using the helper class `PdfDocument`:
```python3
doc = pdfium.PdfDocument(filename)
# ... use methods provided by the helper class
pdf = doc.raw
# ... work with the actual PDFium document handle
doc.close()
```

Open a PDF using the context manager `PdfContext`:
```python3
with pdfium.PdfContext(filename) as pdf:
    # ... work with the pdf
```

Render a single page:

```python3
with pdfium.PdfContext(filename) as pdf:
    pil_image = pdfium.render_page_topil(
        pdf,
        page_index = 0,
        scale = 1,
        rotation = 0,
        colour = (255, 255, 255, 255),
        annotations = True,
        greyscale = False,
        optimise_mode = pdfium.OptimiseMode.none,
    )

pil_image.save("out.png")
pil_image.close()
```

Render multiple pages concurrently:

```python3
for image, suffix in pdfium.render_pdf_topil(filename):
    image.save( 'out_{}.png'.format(suffix) )
    image.close()
```

Read the table of contents:

```python3
doc = pdfium.PdfDocument(filepath)
for item in doc.get_toc():
    print(
        '    ' * item.level +
        "{} -> {}  # {} {}".format(
            item.title,
            item.page_index + 1,
            item.view_mode,
            item.view_pos,
        )
    )
doc.close()
```

Support model documentation: https://pypdfium2.readthedocs.io/en/stable/python_api.html


### Using the PDFium API

Rendering the first page of a PDF document:

```python3
import math
import ctypes
from PIL import Image
import pypdfium2 as pdfium

filename = "your/path/to/document.pdf"

doc = pdfium.FPDF_LoadDocument(filename, None)
page_count = pdfium.FPDF_GetPageCount(doc)
assert page_count >= 1

form_config = pdfium.FPDF_FORMFILLINFO(2)
form_fill = pdfium.FPDFDOC_InitFormFillEnvironment(doc, form_config)

page = pdfium.FPDF_LoadPage(doc, 0)
width = math.ceil(pdfium.FPDF_GetPageWidthF(page))
height = math.ceil(pdfium.FPDF_GetPageHeightF(page))

bitmap = pdfium.FPDFBitmap_Create(width, height, 0)
pdfium.FPDFBitmap_FillRect(bitmap, 0, 0, width, height, 0xFFFFFFFF)

render_args = [bitmap, page, 0, 0, width, height, 0,  pdfium.FPDF_LCD_TEXT | pdfium.FPDF_ANNOT]
pdfium.FPDF_RenderPageBitmap(*render_args)
pdfium.FPDF_FFLDraw(form_fill, *render_args)

cbuffer = pdfium.FPDFBitmap_GetBuffer(bitmap)
buffer = ctypes.cast(cbuffer, ctypes.POINTER(ctypes.c_ubyte * (width * height * 4)))

img = Image.frombuffer("RGBA", (width, height), buffer.contents, "raw", "BGRA", 0, 1)
img.save("out.png")

pdfium.FPDFBitmap_Destroy(bitmap)
pdfium.FPDF_ClosePage(page)

pdfium.FPDFDOC_ExitFormFillEnvironment(form_fill)
pdfium.FPDF_CloseDocument(doc)
```

For more examples of using the raw API, take a look at the [support model source code](src/pypdfium2/_helpers) and the [examples directory](examples).

Documentation for the [PDFium API](https://developers.foxit.com/resources/pdf-sdk/c_api_reference_pdfium/group___f_p_d_f_i_u_m.html) is available. pypdfium2 transparently maps all PDFium classes, enums and functions to Python. However, there can sometimes be minor differences between Foxit and open-source PDFium. In case of doubt, take a look at the inline source code documentation of PDFium.


## Licensing

PDFium and pypdfium2 are available by the terms and conditions of either Apache 2.0 or BSD-3-Clause, at your choice.

Various other open-source licenses apply to the dependencies of PDFium. License texts for PDFium and its dependencies are included in the file [`LicenseRef-PdfiumThirdParty.txt`](LICENSES/LicenseRef-PdfiumThirdParty.txt), which is also shipped with binary redistributions.

Documentation and examples of pypdfium2 are CC-BY-4.0 licensed.


## In Use

* The [doctr](https://mindee.github.io/doctr/) OCR library uses pypdfium2 to rasterise PDF documents.
* The [Extract-URLs](https://github.com/elescamilla/Extract-URLs/) project extracts URLs from PDFs using pypdfium2.


## Development

PDFium builds are retrieved from [bblanchon/pdfium-binaries](https://github.com/bblanchon/pdfium-binaries). Python bindings are auto-generated with [ctypesgen](https://github.com/ctypesgen/ctypesgen)

Please see [#3](https://github.com/pypdfium2-team/pypdfium2/issues/3) for a list of platforms where binary wheels are available.
Some wheels are not tested, unfortunately. If you have access to a theoretically supported but untested system, please report success or failure on the issue or discussion panel.

For wheel naming conventions, please see [Python Packaging: Platform compatibility tags](https://packaging.python.org/specifications/platform-compatibility-tags/) and the various referenced PEPs. [This thread](https://discuss.python.org/t/wheel-platform-tag-for-windows/9025/5) may also provide helpful information.

pypdfium2 contains scripts to automate the release process:

* To build the wheels, run `make release`. This will download binaries and header files, write finished Python binary distributions to `dist/`, and run some checks.
* To clean up after a release, run `make clean`. This will remove downloaded files and build artifacts.

### Testing

Run `make test`.

### Publishing

Starting from version 1.3.0, the release process will be automated using a CI workflow that pushes to GitHub, TestPyPI and PyPI.
To do a release, first run `make release` locally to check that everything works as expected. Then add, commit and push possible changes to the version file.
Finally, add and push a tag to trigger the `Release` workflow, and monitor its process using the GitHub Actions panel:
```bash
git tag -a A.B.C
git push --tags
```

## Issues

Since pypdfium2 is built using upstream binaries and an automatic bindings creator, issues that are not related to packaging or support model code probably need to be addressed upstream. However, the [pypdfium2 issues panel](https://github.com/pypdfium2-team/pypdfium2/issues) is always a good place to start if you have any problems, questions or suggestions.

If the cause of an issue could be determined to be in PDFium, the problem needs to be reported at the [PDFium bug tracker](https://bugs.chromium.org/p/pdfium/issues/list).

Issues related to pre-compiled binaries should be discussed at [pdfium-binaries](https://github.com/bblanchon/pdfium-binaries/issues), though.

If your issue is caused by the bindings generator, refer to the [ctypesgen bug tracker](https://github.com/ctypesgen/ctypesgen/issues).


## Known limitations

### Incompatibility with CPython 3.7.6 and 3.8.1

pypdfium2 cannot be used with releases 3.7.6 and 3.8.1 of the CPython interpreter due to a [regression](https://github.com/python/cpython/pull/16799#issuecomment-612353119) that broke ctypesgen-created string handling code.


## Thanks

Patches to PDFium and DepotTools originate from the [pdfium-binaries](https://github.com/bblanchon/pdfium-binaries/) repository. Many thanks to @bblanchon and @BoLaMN.


## History

pypdfium2 is the successor of *pypdfium* and *pypdfium-reboot*.

The initial *pypdfium* was packaged manually and did not get regular updates. There were no platform-specific wheels, but only a single wheel that contained binaries for 64-bit Linux, Windows and macOS.

*pypdfium-reboot* then added a script to automate binary deployment and bindings generation to simplify regular updates. However, it was still not platform specific.

pypdfium2 is a full rewrite of *pypdfium-reboot* to build platform-specific wheels. It also adds a basic support model and a command-line interface on top of the PDFium C API to simplify common use cases. Moreover, pypdfium2 includes facilities to build PDFium from source, to extend platform compatibility.
