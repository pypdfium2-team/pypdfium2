<!-- SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# PyPDFium2

[PyPDFium2](https://github.com/pypdfium2-team/pypdfium2) is a Python 3 binding to
[PDFium](https://pdfium.googlesource.com/pdfium/+/refs/heads/main), the liberal-licensed
PDF rendering library authored by Foxit and maintained by Google.


## Install/Update

### Install from PyPI

```bash
python3 -m pip install -U pypdfium2
```

### Manual installation

The following steps require the external tools `git`, `ctypesgen` and `gcc` to be
installed and available in `PATH`. Additionally, the python package `wheel` is required.

For source build, more dependencies may be necessary (see [`DEPS.txt`](DEPS.txt)).


#### Package locally

This will download a pre-built binary for PDFium, generate the bindings and
build a wheel.

```bash
python3 update.py -p ${platform_name}
python3 setup_${platform_name}.py bdist_wheel
python3 -m pip install -U dist/pypdfium2-${version}-py3-none-${platform_tag}.whl
```

#### Source build

If you are using a platform where no pre-compiled package is available, it might be
possible to build PDFium from source. However, this is a complex process that can vary
depending on the host system, and it may take a long time.

```bash
python3 build.py
python3 setup_source.py bdist_wheel
pip3 install dist/pypdfium2-${version}-py3-none-${platform_tag}.whl
```


## Examples

### Using the command-line interface

Rasterise a PDF document:
```bash
pypdfium2 -i your_file.pdf -o your_output_dir/ --scale 1 --rotation 0 --optimise-mode none
```

If you want to render multiple files at once, a bash `for`-loop may be suitable:
```bash
for file in ./*.pdf; do echo "$file" && pypdfium2 -i "$file" -o your_output_dir/ --scale 2; done
```

Dump the table of contents of a PDF:
```bash
pypdfium2 --show-toc -i your_file.pdf
```

To obtain a full list of possible command-line parameters, run
```bash
pypdfium2 --help
```

CLI documentation: https://pypdfium2.readthedocs.io/en/latest/cli.html


### Using the support model

Import pypdfium2:

```python3
import pypdfium2 as pdfium
```

Open a PDF by function:

```python3
pdf = pdfium.open_pdf(filename)
# ... work with the PDF
pdfium.close_pdf(pdf)
```

Open a PDF by context manager:

```python3
with pdfium.PdfContext(filename) as pdf:
    # ... work with the PDF
```

Render a single page:

```python3
with pdfium.PdfContext(filename) as pdf:
    pil_image = pdfium.render_page(
        pdf,
        page_index = 0,
        scale = 1,
        rotation = 0,
        colour = 0xFFFFFFFF,
        annotations = True,
        greyscale = False,
        optimise_mode = pdfium.OptimiseMode.none,
    )

pil_image.save("out.png")
pil_image.close()
```

Render multiple pages concurrently:

```python3
for image, suffix in pdfium.render_pdf(filename):
    image.save(f'out_{suffix}.png')
    image.close()
```

Read the table of contents:

```python3
with pdfium.PdfContext(filename) as pdf:
    toc = pdfium.get_toc(pdf)
    pdfium.print_toc(toc)
```

Support model documentation: https://pypdfium2.readthedocs.io/en/latest/support_api.html


### Using the PDFium API

Rendering the first page of a PDF document:

```python3
import math
import ctypes
from PIL import Image
import pypdfium2 as pdfium

doc = pdfium.FPDF_LoadDocument(filename, None) # load document (filename, password string)
page_count = pdfium.FPDF_GetPageCount(doc)     # get page count
assert page_count >= 1

page   = pdfium.FPDF_LoadPage(doc, 0)                # load the first page
width  = math.ceil(pdfium.FPDF_GetPageWidthF(page))  # get page width
height = math.ceil(pdfium.FPDF_GetPageHeightF(page)) # get page height

# render to bitmap
bitmap = pdfium.FPDFBitmap_Create(width, height, 0)
pdfium.FPDFBitmap_FillRect(bitmap, 0, 0, width, height, 0xFFFFFFFF)
pdfium.FPDF_RenderPageBitmap(
    bitmap, page, 0, 0, width, height, 0, 
    pdfium.FPDF_LCD_TEXT | pdfium.FPDF_ANNOT
)

# retrieve data from bitmap
cbuffer = pdfium.FPDFBitmap_GetBuffer(bitmap)
buffer = ctypes.cast(cbuffer, ctypes.POINTER(ctypes.c_ubyte * (width * height * 4)))

img = Image.frombuffer("RGBA", (width, height), buffer.contents, "raw", "BGRA", 0, 1)
img.save("out.png")

pdfium.FPDFBitmap_Destroy(bitmap)
pdfium.FPDF_ClosePage(page)

pdfium.FPDF_CloseDocument(doc)
```

Documentation for the [PDFium API](https://developers.foxit.com/resources/pdf-sdk/c_api_reference_pdfium/group___f_p_d_f_i_u_m.html)
is available. PyPDFium2 transparently maps all PDFium classes, enums and functions to Python.
However, there can sometimes be minor differences between Foxit and open-source PDFium.
In case of doubt, take a look at the inline source code documentation of PDFium.


## Licensing

PDFium and PyPDFium2 are available by the terms and conditions of either Apache 2.0 or BSD-3-Clause, at your choice.

Documentation and examples are CC-BY-4.0.

Various other BSD- and MIT-style licenses apply to the dependencies of PDFium.

License texts for PDFium and its dependencies are included in the file
[`LICENSE-PDFium.txt`](LICENSE-PDFium.txt), which is also shipped with binary re-distributions.


## Development

PDFium builds are retrieved from [bblanchon/pdfium-binaries](https://github.com/bblanchon/pdfium-binaries).
Python bindings are auto-generated with [ctypesgen](https://github.com/ctypesgen/ctypesgen)

Currently supported architectures:

* macOS x86_64 *
* macOS arm64 *
* Linux x86_64
* Linux aarch64 (64-bit ARM) *
* Linux armv7l (32-bit ARM hard-float, e. g. Raspberry Pi 2)
* Windows 64bit
* Windows 32bit *

`*` Not tested yet

If you have access to a theoretically supported but untested system, please report
success or failure on the issues panel.

(In case `bblanchon/pdfium-binaries` would add support for more architectures, PyPDFium2
could be adapted easily.)

For wheel naming conventions, please see
[Python Packaging: Platform compatibility tags](https://packaging.python.org/specifications/platform-compatibility-tags/)
and the various referenced PEPs.

PyPDFium2 contains scripts to automate the release process:

* To build wheels for all platforms, run `./release.sh`. This will download binaries
  and header files, write finished Python wheels to `dist/`, and run `check-wheel-contents`.
* To clean up after a release, run `./clean.sh`. This will remove downloaded files and
  build artifacts.

### Testing

Run `pytest -sv` on the `tests` directory.

### Publishing the wheels

* You may want to upload to [TestPyPI](https://test.pypi.org/legacy/) first to ensure
  everything works as expected:
  ```bash
  twine upload --verbose --repository-url https://test.pypi.org/legacy/ dist/*
  ```
* If all went well, upload to the real PyPI:
  ```bash
  twine upload dist/*
  ```


## Issues

Since PyPDFium2 is built using upstream binaries and an automatic bindings creator,
issues that are not related to packaging most likely need to be addressed upstream.
However, the [PyPDFium2 issues panel](https://github.com/pypdfium2-team/pypdfium2/issues)
is always a good place to start if you have any problems, questions or suggestions.

If the cause of an issue could be determined to be in PDFium, the problem needs to be
reported at the [PDFium bug tracker](https://bugs.chromium.org/p/pdfium/issues/list).

Issues related to build configuration should be discussed at
[pdfium-binaries](https://github.com/bblanchon/pdfium-binaries/issues), though.

If your issue is caused by the bindings generator, refer to the
[ctypesgen bug tracker](https://github.com/ctypesgen/ctypesgen/issues).


## Known limitations

### Non-ascii file paths on Windows

On Windows, PDFium currently is not able to open documents with file names containing multi-byte, non-ascii
characters. This issue is [confirmed upstream](https://bugs.chromium.org/p/pdfium/issues/detail?id=682), but
has not been addressed yet.

  
## Thanks

Patches to PDFium and DepotTools originate from the [pdfium-binaries](https://github.com/bblanchon/pdfium-binaries/)
repository. Many thanks to @bblanchon and @BoLaMN.


## History

PyPDFium2 is the successor of *pypdfium* and *pypdfium-reboot*.

The initial *pypdfium* was packaged manually and did not get regular updates.
There were no platform-specific wheels, but only a single wheel that contained
binaries for 64-bit Linux, Windows and macOS.

*pypdfium-reboot* then added a script to automate binary deployment and bindings generation
to simplify regular updates. However, it was still not platform specific.

PyPDFium2 is a full rewrite of *pypdfium-reboot* to build platform-specific wheels.
It also adds a basic support model and a command-line interface on top of the PDFium
C API to simplify common use cases.
Moreover, PyPDFium2 includes facilities to build PDFium from source, to extend
platform compatibility.
