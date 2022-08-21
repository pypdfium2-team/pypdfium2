<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# pypdfium2

[pypdfium2](https://github.com/pypdfium2-team/pypdfium2) is an ABI-level Python 3 binding to [PDFium](https://pdfium.googlesource.com/pdfium/+/refs/heads/main), a powerful and liberal-licensed library for PDF creation, inspection, manipulation and rendering.

The project is built using [ctypesgen](https://github.com/ctypesgen/ctypesgen) and external [PDFium binaries](https://github.com/bblanchon/pdfium-binaries/).
Its custom setup infrastructure provides a seamless packaging and installation process. A wide range of platforms and Python versions is supported.

pypdfium2 includes helper classes to simplify common use cases, while the raw PDFium/ctypes API remains accessible as well.


## Installation

* Installing the latest PyPI release (recommended)
  ```bash
  python3 -m pip install -U pypdfium2
  ```
  This will use a pre-built wheel package, the easiest way of installing pypdfium2.

* Installing from source
  
  * With an external PDFium binary
    ```bash
    # In the directory containing the source code of pypdfium2
    python3 -m pip install .
    ```

  * With a locally built PDFium binary
    ```bash
    python3 setupsrc/pl_setup/build_pdfium.py
    PYP_TARGET_PLATFORM="sourcebuild" python3 -m pip install .
    ```
    The build script provides a few options that can be listed by calling it with `--help`.
    Building PDFium may take a long time because it comes with its own toolchain and bundled dependencies, rather than using system-provided components.[^1]
  
  The host system needs to provide `git` and `gcc`.
  Setup code also depends on the Python packages `ctypesgen`, `wheel`, `setuptools` and `setuptools-scm`, which will usually get installed automatically.
  
  When installing from source, some additional options of the `pip` package manager may be relevant:
  * `-v`: Request more detailed logging output. Useful for debugging.
  * `-e`: Install in editable mode, so that the installation will point to the source tree. This way, changes directly take effect without needing to re-install. Recommended for development.
  * `--no-build-isolation`: Do not isolate the installation in a virtual environment and use system packages instead. In this case, dependencies specified in `pyproject.toml` (PEP 518) will not take effect and should be pre-installed by the caller.[^2] This is an indispensable option if wanting to run the installation with custom versions of setup dependencies.[^3]

* Installing an unofficial distribution
  
  To the authors' knowledge, there currently are no other distributions of pypdfium2 apart from the official releases on PyPI and GitHub.
  There is no conda package yet.
  So far, pypdfium2 has not been included in any operating system repositories. While we are interested in cooperation with external package maintainers to make this possible, the authors of this project have no control over and are not responsible for third-party distributions of pypdfium2.

### Setup magic

As pypdfium2 uses external binaries, there are a few special ways of controling setup behaviour.
They do not represent standardised solutions, but are specific to this project.

* The environment variable `PYP_TARGET_PLATFORM` defines which binaries to include.
  If unset or `auto`, the host platform is detected automatically and corresponding binaries will be selected (if available).
  If set to a certain platform identifier, binaries for the requested platform will be used.[^4]
  If set to `sourcebuild`, binaries will be taken from the location where the build script places its artefacts.
  If set to `sdist`, no platform-dependant files will be injected, so as to create a source distribution.

* The presence of the file `data/.presetup_done.txt` is used to decide if setup code should download binaries and create bindings, or if existing artefacts should be used instead, as re-creating them may not be desirable with every single run.[^5] Consequently, this file needs to be removed if you wish to update the artefacts with the next installation. We are planning to make this procedure more obvious in the future.

[^1]: Replacing PDFium's toolchain with a leaner and more elegant build system that is designed to run on any host platform constitutes a long-standing task. This would be required to be able to reliably perform a local source build when installing an `sdist` package. If you have the time and expertise to set up such a build system, please start a repository and inform us about it.

[^2]: pypdfium2 still has a fallback mechanism, though it might not be entirely reliable.

[^3]: Possible scenarios include using a locally modified version of a dependency, or needing to supply a dependency built from a certain commit (in situations where it is not actionable to modify `pyproject.toml` manually, e. g. an installation script).

[^4]: This is mainly of internal interest for packaging, so that wheels can be crafted for any platform without access to a native host.

[^5]: This is especially relevant as `pip install` may run the code in `setup.py` multiple times.


## Usage

### [Support model](https://pypdfium2.readthedocs.io/en/stable/python_api.html)

Here are some examples of using the support model API.

* Import the library
  ```python
  import pypdfium2 as pdfium
  ```

* Open a PDF using the helper class `PdfDocument` (supports file path strings, bytes, and byte buffers)
  ```python
  pdf = pdfium.PdfDocument(filepath)
  version = pdf.get_version()  # get the PDF standard version
  n_pages = len(pdf)  # get the number of pages in the document
  ```

* Render multiple pages concurrently
  ```python
  page_indices = [i for i in range(n_pages)]  # all pages
  renderer = pdf.render_topil(
      page_indices = page_indices,
      scale = 300/72,  # 300dpi resolution
  )
  for i, image in zip(page_indices, renderer):
      image.save("out_%s.jpg" % str(i).zfill(n_pages))
      image.close()
  ```

* Read the table of contents
  ```python
  for item in pdf.get_toc():
      print(
          "    " * item.level +
          "[%s] " % ("-" if item.is_closed else "+") +
          "%s -> %s  # %s %s" % (
              item.title,
              item.page_index + 1,
              item.view_mode,
              item.view_pos,
          )
      )
  ```

* Load a page to work with
  ```python
  page = pdf[0]  # or pdf.get_page(0)
  
  # Get page dimensions in PDF canvas units (1pt->1/72in by default)
  width, height = page.get_size()
  # Set the absolute page rotation to 90° clockwise
  page.set_rotation(90)
  
  # Locate objects on the page
  for obj in page.get_objects():
      print(obj.get_type(), obj.get_pos())
  ```

* Render a single page
  ```python
  image = page.render_topil(
      scale = 1,  # 72dpi resolution
      rotation = 0,  # no additional rotation
      crop = (0, 0, 0, 0),  # no crop (left, right, bottom, top)
      colour = (255, 255, 255, 255),  # RGBA background colour (white)
      annotations = True,  # show annotations
      greyscale = False,  # render coloured
      optimise_mode = pdfium.OptimiseMode.NONE,  # no subpixel rendering
  )
  image.show()
  image.close()
  ```

* Work with text
  ```python
  # Load a corresponding text page
  textpage = page.get_textpage()
  
  # Extract text from the whole page
  text_all = textpage.get_text()
  # Extract text from a specific rectangular area
  text_part = textpage.get_text(left=50, bottom=100, right=width-50, top=height-100)
  
  # Extract URLs from the page
  links = [l for l in textpage.get_links()]
  
  # Locate text on the page
  searcher = textpage.search("something", match_case=False, match_whole_word=False)
  first_occurrence = searcher.get_next()  # list of bounding boxes (left, right, bottom, top)
  ```

* Release allocated memory by closing finished objects
  ```python
  # Attention: objects must be closed in correct order!
  for garbage in (searcher, textpage, page, pdf):
      garbage.close()
  ```

* Create a new, empty PDF
  ```python
  pdf = pdfium.PdfDocument.new()
  width, height = (595, 842)  # A4
  page = pdf.new_page(width, height)
  ```

* Add text content
  ```python
  NotoSans = ".../NotoSans-Regular.ttf"
  hb_font = pdfium.HarfbuzzFont(NotoSans)
  pdf_font = pdf.add_font(
      NotoSans,
      type = pdfium.FPDF_FONT_TRUETYPE,
      is_cid = True,
  )
  page.insert_text(
      text = "मैं घोषणा, पुष्टि और सहमत हूँ कि:",
      pos_x = 50,
      pos_y = height - 75,
      font_size = 25,
      hb_font = hb_font,
      pdf_font = pdf_font,
  )
  ```

* Save the document (and close objects)
  ```python
  with open("output.pdf", "wb") as buffer:
      pdf.save(buffer, version=17)  # use PDF 1.7 standard
  for garbage in (page, pdf_font, pdf):
      garbage.close()
  ```

PDFium provides a large amount of functions, many of which are not covered by support models yet.
You may seamlessly interact with these functions while still using helper classes where available, as they provide a `raw` attribute to access the underlying PDFium/ctypes object, e. g.

```python
permission_flags = pdfium.FPDF_GetDocPermission(pdf.raw)
has_transparency = pdfium.FPDFPage_HasTransparency(page.raw)
```


### Raw PDFium API

While helper classes conveniently wrap the raw PDFium API, it may still be accessed directly and is publicly exposed in the main namespace of pypdfium2.
As the vast majority of PDFium members is prefixed with `FPDF`, they are clearly distinguishable from support model components.

For PDFium documentation, please look at the comments in its [public header files](https://pdfium.googlesource.com/pdfium/+/refs/heads/main/public/).[^6]
A large variety of examples on how to interface with the raw API using [`ctypes`](https://docs.python.org/3/library/ctypes.html) is already provided with [support model source code](src/pypdfium2/_helpers).
Nonetheless, the following guide may be helpful to get started with the raw API.

[^6]: Unfortunately, no recent HTML-rendered documentation is available for PDFium at the moment. While large parts of the old [Foxit docs](https://developers.foxit.com/resources/pdf-sdk/c_api_reference_pdfium/group___f_p_d_f_i_u_m.html) still seem similar to PDFium's current API, many modifications and new functions are actually missing, which can be confusing.

* In general, PDFium functions can be called just like normal Python functions.
  However, parameters may only be passed positionally, i. e. it is not possible to use keyword arguments.
  There are no defaults, so you always need to provide a value for each argument.
  ```python
  # arguments: filepath (str|bytes), password (str|bytes|None)
  pdf = pdfium.FPDF_LoadDocument(filepath, None)
  ```
  This is the underlying bindings declaration,[^7] which loads the function from the binary and
  contains the information required to convert Python types to their C equivalents.
  ```python
  if _libs["pdfium"].has("FPDF_LoadDocument", "cdecl"):
      FPDF_LoadDocument = _libs["pdfium"].get("FPDF_LoadDocument", "cdecl")
      FPDF_LoadDocument.argtypes = [FPDF_STRING, FPDF_BYTESTRING]
      FPDF_LoadDocument.restype = FPDF_DOCUMENT
  ```
  For instance, Python `str` or `bytes` are converted to `FPDF_STRING` implicitly. If a `str` is provided, its `utf-8` encoding will be used.

[^7]: From the auto-generated bindings file, which is not part of the repository. It is built into wheels, or created on installation. If you have an editable install, the bindings file may be found at `src/_pypdfium.py`.

* While some functions are quite easy to use, things soon get more complex.
  For a start, function parameters are not only used for input, but also for output:
  ```python
  # Initialise an integer object (defaults to 0)
  c_version = ctypes.c_int()
  # Let the function assign a value to the c_int object, and capture its return code (True for success, False for failure)
  success = pdfium.FPDF_GetFileVersion(pdf, c_version)
  # Get the Python int by accessing the `value` attribute of the c_int object
  py_version = c_version.value
  ```

* If an array is required as output parameter, you can initialise one like this (conceived in general terms):
  ```python
  # long form
  array_type = (c_type * array_length)
  array_object = array_type()
  # short form
  array_object = (c_type * array_length)()
  ```
  Example: Getting view mode and target position from a destination object returned by some other function.
  ```python
  # (Assuming `dest` is an FPDF_DEST)
  n_params = ctypes.c_ulong()
  # Create a C array to store up to four coordinates
  view_pos = (pdfium.FS_FLOAT * 4)()
  view_mode = pdfium.FPDFDest_GetView(dest, n_params, view_pos)
  # Convert the C array to a Python list and cut it down to the actual number of coordinates
  view_pos = list(view_pos)[:n_params.value]
  ```

* For string output parameters, callers needs to provide a sufficiently long, pre-allocated buffer.
  
  Example: Getting the title string of a bookmark.
  ```python
  # (Assuming `bookmark` is an FPDF_BOOKMARK)
  # First call to get the required number of bytes (not characters!)
  # With this function, space for a NUL terminator is included already
  n_bytes = pdfium.FPDFBookmark_GetTitle(bookmark, None, 0)
  # Initialisation of the string buffer
  # Internally, this will create a C char array of length `n_bytes` (1 char is 1 byte wide)
  buffer = ctypes.create_string_buffer(n_bytes)
  # Second call with the actual buffer
  pdfium.FPDFBookmark_GetTitle(bookmark, buffer, n_bytes)
  # Decode bytes to str and cut off the terminating NUL character
  # The docs for the function in question indicate which decoder to use (usually: UTF-16LE)
  # You might want to pass `errors="ignore"` to skip possible encoding errors without raising an exception
  title = buffer.raw.decode('utf-16-le')[:-1]
  ```
  
  The above pattern applies to functions that require type `char`.
  However, some functions use `unsigned short` instead, which works a bit differently.
  Concerning functions that take a typeless pointer (`void`) for a string buffer, it is recommended to judge which approach to use depending on whether the function returns the number of bytes or characters.
  In principle, you could use either approach, provided that you allocate enough memory (2 bytes per character for UTF-16LE) and types match in the end.
  
  Example: Extracting text in given boundaries.
  ```python
  # (Assuming `textpage` is an FPDF_TEXTPAGE and the boundary variables are set to int or float values)
  # Store common arguments for the two function calls
  args = (textpage, left, top, right, bottom)
  # Get the expected number of characters (not bytes!). Return an empty string if no characters were found.
  n_characters = pdfium.FPDFText_GetBoundedText(*args, None, 0)
  if n_characters <= 0:
      return ""
  # Initialise an array of `unsigned short` slots for the characters, plus a NUL terminator
  c_array = (ctypes.c_ushort * (n_characters+1))()
  pdfium.FPDFText_GetBoundedText(*args, c_array, n_characters)
  # Convert the c_ushort array to bytes and decode them, cutting off the NUL terminator
  text = bytes(c_array).decode("utf-16-le")[:-1]
  ```

* Not only are there different ways of string output that need to be handled according to the requirements of the function in question.
  String input, too, can work differently depending on encoding, NUL termination, and type.
  If a function takes a UTF-8 encoded `FPDF_STRING` or `FPDF_BYTESTRING` (e. g. `FPDF_LoadDocument()`), you may simply pass the Python string, and bindings code will handle the rest.
  However, functions such as `FPDFText_FindStart()` demand a UTF-16-LE encoded string with NUL terminator, given as a pointer to the first element of an `unsigned short` array:
  ```python
  # (Assuming `text` is a str and `textpage` an FPDF_TEXTPAGE)
  # encode to UTF-16LE and add the NUL terminator
  enc_text = text.encode("utf-16-le") + b"\x00\x00"
  # obtain a pointer to `enc_text` typed as c_ushort
  text_ptr = ctypes.cast(enc_text, ctypes.POINTER(ctypes.c_ushort))
  search = pdfium.FPDFText_FindStart(textpage, text_ptr, 0, index)
  ```

* Supposing you have a C memory buffer allocated by PDFium, you will commonly get a pointer to the first item of the byte array.
  If you wish to read the data, you need to re-interpret this pointer using `ctypes.cast()` to encompass the whole array:
  ```python
  # (Assuming `bitmap` is an FPDF_BITMAP and `size` is the expected number of bytes in the buffer)
  first_item = pdfium.FPDFBitmap_GetBuffer(bitmap)
  buffer = ctypes.cast(first_item, ctypes.POINTER(ctypes.c_ubyte * size))
  data = bytes(buffer.contents)  # buffer as python bytes (independant copy)
  ```

* Now that we have covered transferring data from a C buffer to Python, you may be interested in how to write Python data into a C buffer:
  ```python
  # (Assuming `c_buffer_ptr` is a pointer to a C buffer to write into,
  #  and `py_buffer` a Python byte buffer (io.BufferedReader or similar))
  # Get the memory address the pointer refers to (first item of the byte array)
  address = ctypes.addressof(c_buffer_ptr.contents)
  # Get a writable ctypes array at the given place in memory
  c_buffer = (ctypes.c_char * size).from_address(address)
  # Read from `py_buffer` directly into `c_buffer`, until `c_buffer` is full or `py_buffer` has reached its end
  # If the data is not in memory yet and read just now, this is a zero-copy operation
  n_bytes = py_buffer.readinto(c_buffer)  # returns the number of bytes read
  ```

* If you wish to check whether two objects returned by PDFium are the same, the `is` operator won't help you because `ctypes` does not have original object return (OOR),
  i. e. new, equivalent Python objects are created each time, although they might represent one and the same C object.[^8] That's why you'll want to use `ctypes.addressof()` to get the memory addresses of the underlying C object.
  For instance, this is used to avoid infinite loops on circular bookmark references when iterating through the document outline:
  ```python
  # (Assuming `pdf` is an FPDF_DOCUMENT)
  seen = set()
  bookmark = pdfium.FPDFBookmark_GetFirstChild(pdf, None)
  while bookmark:
      # bookmark is a pointer, so we need to use its `contents` attribute to get the object the pointer refers to
      # (otherwise we'd only get the memory address of the pointer itself, which is useless as each call creates a new pointer)
      address = ctypes.addressof(bookmark.contents)
      if address in seen:
          break  # circular reference detected
      else:
          seen.add(address)
      bookmark = pdfium.FPDFBookmark_GetNextSibling(pdf, bookmark)
  ```

[^8]: This is not only the case for objects received from different function calls - even checking if the contents attribute of a pointer is identical to itself (`ptr.contents is ptr.contents`) will always return `False` because a new object is constructed with each attribute access. Confer the [ctypes documentation on Pointers](https://docs.python.org/3/library/ctypes.html#pointers).

<!-- TODO
* getting a python object by memory address (reverting id())
* casting
* callbacks
* object lifetime
-->


### [Command-line Interface](https://pypdfium2.readthedocs.io/en/stable/shell_api.html)

<!-- TODO -->


## Licensing

PDFium and pypdfium2 are available by the terms and conditions of either [`Apache-2.0`](LICENSES/Apache-2.0.txt) or [`BSD-3-Clause`](LICENSES/BSD-3-Clause.txt), at your choice.

Various other open-source licenses apply to the dependencies of PDFium. Verbatim copies of their respective licenses are contained in the file [`LicenseRef-PdfiumThirdParty.txt`](LICENSES/LicenseRef-PdfiumThirdParty.txt), which is also shipped with binary redistributions.

Documentation and examples of pypdfium2 are licensed under [`CC-BY-4.0`](LICENSES/CC-BY-4.0.txt).

pypdfium2 complies with the [reuse standard](https://reuse.software/spec/) by including [SPDX](https://spdx.org/licenses/) headers in source files, and license information for data files in [`.reuse/dep5`](.reuse/dep5).


## Development

<!-- TODO - possibly use a separate file? -->

### Testing

<!-- TODO -->

### Issues

Since pypdfium2 is built using external binaries and an automatic bindings creator, issues that are not related to packaging or support model code likely need to be addressed upstream. However, the [issue](https://github.com/pypdfium2-team/pypdfium2/issues) or [discussion](https://github.com/pypdfium2-team/pypdfium2/discussions) panels are always a good place to start if you have any problems, questions or suggestions.

If the cause of an issue could be determined to be in PDFium, the problem needs to be reported at the [PDFium bug tracker](https://bugs.chromium.org/p/pdfium/issues/list). For discussion and general questions, also consider joining the [PDFium mailing list](https://groups.google.com/g/pdfium/).

Issues related to pre-compiled packages should be discussed at [pdfium-binaries](https://github.com/bblanchon/pdfium-binaries/issues), though.

If your issue is caused by the bindings generator, refer to the [ctypesgen bug tracker](https://github.com/ctypesgen/ctypesgen/issues).


## Known limitations

### Incompatibility with CPython 3.7.6 and 3.8.1

pypdfium2 cannot be used with releases 3.7.6 and 3.8.1 of the CPython interpreter due to a [regression](https://github.com/python/cpython/pull/16799#issuecomment-612353119) that broke ctypesgen-created string handling code.


## In Use

* The [doctr](https://mindee.github.io/doctr/) OCR library uses pypdfium2 to rasterise PDFs.
* [Extract-URLs](https://github.com/elescamilla/Extract-URLs/) use pypdfium2 to extract URLs from PDF documents.
* [py-pdf/benchmarks](https://github.com/py-pdf/benchmarks) compares pypdfium2's text extraction capabilities with other libraries.

*Your project uses pypdfium2, but is not part of the list yet? Please let us know!*


## Thanks to[^9]

<!-- order: alphabetical by surname -->

* [Anurag Bansal](https://github.com/banagg): Support model for text insertion (`PdfPage.insert_text()`).
* [Benoît Blanchon](https://github.com/bblanchon): Author of [PDFium binaries](https://github.com/bblanchon/pdfium-binaries/) and [patches](sourcebuild/patches/).
* [Anderson Bravalheri](https://github.com/abravalheri): Help with PEP 517/518 compliance. Hint to use an environment variable rather than separate setup files.
* [Bastian Germann](https://github.com/bgermann): Help with inclusion of licenses for third-party components of PDFium.
* [Tim Head](https://github.com/betatim): Original idea for Python bindings to PDFium with ctypesgen in `wowpng`.
* [Yinlin Hu](https://github.com/YinlinHu): `pypdfium` prototype and `kuafu` PDF viewer.
* [Adam Huganir](https://github.com/adam-huganir): Help with maintenance and development decisions since the beginning of the project.
* [kobaltcore](https://github.com/kobaltcore): Bug fix for `PdfDocument.save()`.
* [Mike Kroutikov](https://github.com/mkroutikov): Examples on how to use PDFium with ctypes in `redstork` and `pdfbrain`.
* [Peter Saalbrink](https://github.com/petersaalbrink): Code style improvements to the multipage renderer.
* [Lei Zhang](https://github.com/leizleiz): Windows-specific fixes concerning `FPDF_LoadDocument()`.

*If you have somehow contributed to this project but we forgot to mention you here, feel encouraged to help us correct this oversight.*

[^9]: People listed in this section may not necessarily have contributed any copyrightable code to the repository. Some have rather helped with ideas, or contributions to dependencies of pypdfium2.


## History

pypdfium2 is the successor of *pypdfium* and *pypdfium-reboot*.

Inspired by *wowpng*, the first known proof of concept Python binding to PDFium using ctypesgen, the initial *pypdfium* package was created. It had to be updated manually, which did not happen frequently. There were no platform-specific wheels, but only a single wheel that contained binaries for 64-bit Linux, Windows and macOS.

*pypdfium-reboot* then added a script to automate binary deployment and bindings generation to simplify regular updates. However, it was still not platform specific.

pypdfium2 is a full rewrite of *pypdfium-reboot* to build platform-specific wheels and consolidate the setup scripts. Further additions include ...
* A CI workflow to automatically release new wheels every Monday
* Support models that wrap the raw PDFium/ctypes API
* Test code
* A script to build PDFium from source
