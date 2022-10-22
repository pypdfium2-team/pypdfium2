<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# pypdfium2

[pypdfium2](https://github.com/pypdfium2-team/pypdfium2) is an ABI-level Python 3 binding to [PDFium](https://pdfium.googlesource.com/pdfium/+/refs/heads/main), a powerful and liberal-licensed library for PDF creation, inspection, manipulation and rendering.

The project is built using [ctypesgen](https://github.com/ctypesgen/ctypesgen) and external [PDFium binaries](https://github.com/bblanchon/pdfium-binaries/).
Its custom setup infrastructure provides a seamless packaging and installation process. A wide range of platforms and Python versions is supported with wheel packages.

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
    PDFIUM_BINARY="sourcebuild" python3 -m pip install .
    ```
    The build script provides a few options that can be listed by calling it with `--help`.
    Building PDFium may take a long time because it comes with its own toolchain and bundled dependencies, rather than using system-provided components.[^pdfium_buildsystem]
    
    [^pdfium_buildsystem]: Replacing PDFium's toolchain with a leaner and more elegant build system that is designed to run on any host platform constitutes a long-standing task. This would be required to be able to reliably perform a local source build when installing an `sdist` package. If you have the time and expertise to set up such a build system, please start a repository and inform us about it.
    
  The host system needs to provide `git` and `gcc`.
  Setup code also depends on the Python packages `ctypesgen`, `wheel`, and `setuptools`, which will usually get installed automatically.
  
  When installing from source, some additional options of the `pip` package manager may be relevant:
  * `-v`: Request more detailed logging output. Useful for debugging.
  * `-e`: Install in editable mode, so that the installation will point to the source tree. This way, changes directly take effect without needing to re-install. Recommended for development.
  * `--no-build-isolation`: Do not isolate the installation in a virtual environment and use system packages instead. In this case, dependencies specified in `pyproject.toml` (PEP 518) will not take effect and should be pre-installed by the caller. This is an indispensable option if wanting to run the installation with custom versions of setup dependencies.[^no_build_isolation]
  
  [^no_build_isolation]: Possible scenarios include using a locally modified version of a dependency, or supplying a dependency built from a certain commit (while not changing the code)
  
* Installing an unofficial distribution
  
  To the authors' knowledge, there currently are no other distributions of pypdfium2 apart from the official wheel releases on PyPI and GitHub.
  There is no conda package yet.
  So far, pypdfium2 has not been included in any operating system repositories. While we are interested in cooperation with external package maintainers to make this possible, the authors of this project have no control over and are not responsible for third-party distributions of pypdfium2.

### Setup magic

As pypdfium2 uses external binaries, there are some special setup aspects to consider.

* Binaries are stored in platform-specific sub-directories of `data/`, along with bindings and version information.
* The environment variable `PDFIUM_BINARY` controls which binary to include on setup.
  * If unset or `auto`, the host platform is detected and a corresponding binary will be selected.
    Platform files are downloaded/generated automatically, if not present yet. By default, existing platform files will also be updated if a newer version is available, but this may be prevented by creating an empty file called `.lock_autoupdate.txt` in `data/`.
  * If set to a certain platform identifier, binaries for the requested platform will be used.[^platform_ids]
    In this case, platform files will not be downloaded/generated automatically, but need to be supplied beforehand using the `update_pdfium.py` script.
  * If set to `sourcebuild`, binaries will be taken from the location where the build script places its artefacts, assuming a prior run of `build_pdfium.py`.
  * If set to `none`, no platform-dependent files will be injected, so as to create a source distribution.

[^platform_ids]: This is mainly of internal interest for packaging, so that wheels can be crafted for any platform without access to a native host.

### Runtime Dependencies

pypdfium2 does not have any mandatory runtime dependencies apart from Python and its standard library.

However, some optional support model features require additional packages:
* [`Pillow`](https://pillow.readthedocs.io/en/stable/) (module name `PIL`) is a highly pouplar imaging library for Python.
  pypdfium2 provides convenience methods to directly return PIL image objects when dealing with raster graphics.
* [`NumPy`](https://numpy.org/doc/stable/index.html) is a library for scientific computing. Similar to `Pillow`, pypdfium2 provides helpers to get raster graphics in the form of multidimensional numpy arrays.
* [`uharfbuzz`](https://github.com/harfbuzz/uharfbuzz) is a text shaping engine used by text insertion helpers, to support foreign writing systems.
  If you do not care about this, you may insert text using the raw PDFium functions `FPDFPageObj_NewTextObj()` (or `FPDFPageObj_CreateTextObj()`) and `FPDFText_SetText()` without being dependent on uharfbuzz.


## Usage

### [Support model](https://pypdfium2.readthedocs.io/en/stable/python_api.html)

Here are some examples of using the support model API.

* Import the library
  ```python
  import pypdfium2 as pdfium
  ```

* Open a PDF using the helper class `PdfDocument` (supports file path strings, bytes, and byte buffers)
  ```python
  pdf = pdfium.PdfDocument("./path/to/document.pdf")
  version = pdf.get_version()  # get the PDF standard version
  n_pages = len(pdf)  # get the number of pages in the document
  ```

* Render multiple pages concurrently
  ```python
  page_indices = [i for i in range(n_pages)]  # all pages
  renderer = pdf.render_to(
      pdfium.BitmapConv.pil_image,
      page_indices = page_indices,
      scale = 300/72,  # 300dpi resolution
  )
  for i, image in zip(page_indices, renderer):
      image.save("out_%0*d.jpg" % (n_digits, i))
  ```

* Read the table of contents
  ```python
  for item in pdf.get_toc():
    
      if item.n_kids == 0:
          state = "*"
      elif item.is_closed:
          state = "-"
      else:
          state = "+"
      
      if item.page_index is None:
          target = "?"
      else:
          target = item.page_index + 1
      
      print(
          "    " * item.level +
          "[%s] %s -> %s  # %s %s" % (
              state, item.title, target,
              pdfium.ViewmodeToStr[item.view_mode],
              [round(c, n_digits) for c in item.view_pos],
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
      print("    "*obj.level + pdfium.ObjectTypeToStr[obj.type], obj.get_pos())
  ```

* Render a single page
  ```python
  image = page.render_to(
      pdfium.BitmapConv.pil_image,
      scale = 1,                           # 72dpi resolution
      rotation = 0,                        # no additional rotation
      crop = (0, 0, 0, 0),                 # no crop (form: left, right, bottom, top)
      greyscale = False,                   # coloured output
      fill_colour = (255, 255, 255, 255),  # fill bitmap with white background before rendering (form: RGBA)
      colour_scheme = None,                # no custom colour scheme
      optimise_mode = OptimiseMode.NONE,   # no optimisations (e. g. subpixel rendering)
      draw_annots = True,                  # show annotations
      draw_forms = True,                   # show forms
      no_smoothtext = False,               # anti-alias text
      no_smoothimage = False,              # anti-alias images
      no_smoothpath = False,               # anti-alias paths
      force_halftone = False,              # don't force halftone for image stretching
      rev_byteorder = False,               # don't reverse byte order
      prefer_bgrx = False,                 # don't prefer four channels for coloured output
      force_bitmap_format = None,          # don't force a specific bitmap format
      extra_flags = 0,                     # no extra flags
      allocator = None,                    # no custom allocator
      memory_limit = 2**30,                # maximum allocation (1 GiB)
  )
  image.show()
  ```

* Extract and search text
  ```python
  # Load a text page helper
  textpage = page.get_textpage()
  
  # Extract text from the whole page
  text_all = textpage.get_text_range()
  # Extract text from a specific rectangular area
  text_part = textpage.get_text_bounded(left=50, bottom=100, right=width-50, top=height-100)
  
  # Extract URLs from the page
  links = [l for l in textpage.get_links()]
  
  # Locate text on the page
  searcher = textpage.search("something", match_case=False, match_whole_word=False)
  # This will be a list of bounding boxes of the form (left, right, bottom, top)
  first_occurrence = searcher.get_next()
  ```

* Finished objects may be closed explicitly to release memory allocated by PDFium.
  Otherwise, they will be finalised automatically on garbage collection.
  ```python
  # Attention: objects must be closed in correct order!
  for garbage in (searcher, textpage, page, pdf):
      garbage.close()
  ```

* Create a new PDF with an empty A4 sized page
  ```python
  pdf = pdfium.PdfDocument.new()
  width, height = (595, 842)
  page_a = pdf.new_page(width, height)
  ```

* Insert text content
  ```python
  NotoSans = "./tests/resources/NotoSans-Regular.ttf"
  hb_font = pdfium.HarfbuzzFont(NotoSans)
  pdf_font = pdf.add_font(
      NotoSans,
      type = pdfium.FPDF_FONT_TRUETYPE,
      is_cid = True,
  )
  page_a.insert_text(
      text = "मैं घोषणा, पुष्टि और सहमत हूँ कि:",
      pos_x = 50,
      pos_y = height - 75,
      font_size = 25,
      hb_font = hb_font,
      pdf_font = pdf_font,
  )
  page_a.generate_content()
  ```

* Add a JPEG image on a second page
  ```python
  pdf = pdfium.PdfDocument.new()

  image = pdfium.PdfImageObject.new(pdf)
  buffer = open("./tests/resources/mona_lisa.jpg", "rb")
  width, height = image.load_jpeg(buffer, autoclose=True)

  matrix = pdfium.PdfMatrix()
  matrix.scale(width, height)
  image.set_matrix(matrix)

  page = pdf.new_page(width, height)
  page.insert_object(image)
  page.generate_content()
  ```

* Save the document
  ```python
  with open("output.pdf", "wb") as buffer:
      pdf.save(buffer, version=17)  # use PDF 1.7 standard
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

For PDFium documentation, please look at the comments in its [public header files](https://pdfium.googlesource.com/pdfium/+/refs/heads/main/public/).[^pdfium_docs]
A large variety of examples on how to interface with the raw API using [`ctypes`](https://docs.python.org/3/library/ctypes.html) is already provided with [support model source code](src/pypdfium2/_helpers).
Nonetheless, the following guide may be helpful to get started with the raw API, especially for developers who are not familiar with `ctypes` yet.

[^pdfium_docs]: Unfortunately, no recent HTML-rendered documentation is available for PDFium at the moment. While large parts of the old [Foxit docs](https://developers.foxit.com/resources/pdf-sdk/c_api_reference_pdfium/group___f_p_d_f_i_u_m.html) still seem similar to PDFium's current API, many modifications and new functions are actually missing, which can be confusing.

* In general, PDFium functions can be called just like normal Python functions.
  However, parameters may only be passed positionally, i. e. it is not possible to use keyword arguments.
  There are no defaults, so you always need to provide a value for each argument.
  ```python
  # arguments: filepath (str|bytes), password (str|bytes|None)
  pdf = pdfium.FPDF_LoadDocument(filepath.encode("utf-8"), None)
  ```
  This is the underlying bindings declaration,[^bindings_decl] which loads the function from the binary and
  contains the information required to convert Python types to their C equivalents.
  ```python
  if _libs["pdfium"].has("FPDF_LoadDocument", "cdecl"):
      FPDF_LoadDocument = _libs["pdfium"].get("FPDF_LoadDocument", "cdecl")
      FPDF_LoadDocument.argtypes = [FPDF_STRING, FPDF_BYTESTRING]
      FPDF_LoadDocument.restype = FPDF_DOCUMENT
  ```
  For instance, Python `str` or `bytes` are converted to `FPDF_STRING` automatically.
  If a `str` is provided, its UTF-8 encoding will be used. However, it is usually advisable to encode strings explicitly.

[^bindings_decl]: From the auto-generated bindings file, which is not part of the repository. It is built into wheels, or created on installation. If you have an editable install, the bindings file may be found at `src/_pypdfium.py`.

* While some functions are quite easy to use, things soon get more complex.
  First of all, function parameters are not only used for input, but also for output:
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
  This may work differently depending on what type the function requires, which encoding is used, whether the number of bytes or characters is returned, and whether space for a null terminator is included or not. Carefully review the documentation for the function in question to fulfill its requirements.
  
  Example A: Getting the title string of a bookmark.
  ```python
  # (Assuming `bookmark` is an FPDF_BOOKMARK)
  # First call to get the required number of bytes (not characters!), including space for a null terminator
  n_bytes = pdfium.FPDFBookmark_GetTitle(bookmark, None, 0)
  # Initialise the output buffer
  buffer = ctypes.create_string_buffer(n_bytes)
  # Second call with the actual buffer
  pdfium.FPDFBookmark_GetTitle(bookmark, buffer, n_bytes)
  # Decode to string, cutting off the null terminator
  # Encoding: UTF-16LE (2 bytes per character)
  title = buffer.raw[:n_bytes-2].decode('utf-16-le')
  ```
  
  Example B: Extracting text in given boundaries.
  ```python
  # (Assuming `textpage` is an FPDF_TEXTPAGE and the boundary variables are set)
  # Store common arguments for the two calls
  args = (textpage, left, top, right, bottom)
  # First call to get the required number of characters (not bytes!) - a possible null terminator is not included
  n_chars = pdfium.FPDFText_GetBoundedText(*args, None, 0)
  # If no characters were found, return an empty string
  if n_chars <= 0:
      return ""
  # Calculate the required number of bytes
  # Encoding: UTF-16LE (2 bytes per character)
  n_bytes = 2 * n_chars
  # Initialise the output buffer - this function can work without null terminator, so skip it
  buffer = ctypes.create_string_buffer(n_bytes)
  # Re-interpret the type from char to unsigned short as required by the function
  buffer_ptr = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ushort))
  # Second call with the actual buffer
  pdfium.FPDFText_GetBoundedText(*args, buffer_ptr, n_chars)
  # Decode to string
  # (You may want to pass `errors="ignore"` to skip possible errors in the PDF's encoding)
  text = buffer.raw.decode("utf-16-le")
  ```

* Not only are there different ways of string output that need to be handled according to the requirements of the function in question.
  String input, too, can work differently depending on encoding, null termination, and type.
  While functions that take a `UTF-8` encoded `FPDF_STRING` or `FPDF_BYTESTRING` are easy to call, other functions may have more peculiar needs. For instance, `FPDFText_FindStart()` demands a UTF-16LE encoded string with null terminator, given as a pointer to an `unsigned short` array:
  ```python
  # (Assuming `text` is a str and `textpage` an FPDF_TEXTPAGE)
  # Add the null terminator and encode as UTF-16LE
  enc_text = (text + "\x00").encode("utf-16-le")
  # Obtain a pointer of type c_ushort to `enc_text`
  text_ptr = ctypes.cast(enc_text, ctypes.POINTER(ctypes.c_ushort))
  search = pdfium.FPDFText_FindStart(textpage, text_ptr, 0, 0)
  ```

* Suppose you have a C memory buffer allocated by PDFium and wish to read its data.
  PDFium will provide you with a pointer to the first item of the byte array.
  To access the data, you'll want to re-interpret the pointer using `ctypes.cast()` to encompass the whole array:
  ```python
  # (Assuming `bitmap` is an FPDF_BITMAP and `size` is the expected number of bytes in the buffer)
  first_item = pdfium.FPDFBitmap_GetBuffer(bitmap)
  buffer = ctypes.cast(first_item, ctypes.POINTER(ctypes.c_ubyte * size))
  # Buffer as ctypes array (referencing the original buffer, will be unavailable as soon as the bitmap is destroyed)
  c_array = buffer.contents
  # Buffer as Python bytes (independent copy)
  data = bytes(c_array)
  ```

* Writing data from Python into a C buffer works in a similar fashion:
  ```python
  # (Assuming `first_item` is a pointer to the first item of a C buffer to write into,
  #  `size` the number of bytes it can store, and `py_buffer` a Python byte buffer)
  c_buffer = ctypes.cast(first_item, ctypes.POINTER(ctypes.c_char * size))
  # Read from the Python buffer, starting at its current position, directly into the C buffer
  # (until the target is full or the end of the source is reached)
  n_bytes = py_buffer.readinto(c_buffer.contents)  # returns the number of bytes read
  ```

* In many situations, callback functions come in handy.[^callback_usecases] Thanks to `ctypes`, it is seamlessly possible to use callbacks across Python/C language boundaries.
  
  [^callback_usecases]: e. g. incremental reading/writing, progress bars, pausing of progressive tasks, ...
  
  Example: Loading a document from a Python buffer. This way, file access can be controlled in Python while the whole data does not need to be in memory at once.
  ```python
  # Factory class to create callable objects holding a reference to a Python buffer
  class _reader_class:
    
    def __init__(self, py_buffer):
        self.py_buffer = py_buffer
    
    def __call__(self, _, position, p_buf, size):
        # Write data from Python buffer into C buffer, as explained before
        c_buffer = ctypes.cast(p_buf, ctypes.POINTER(ctypes.c_char * size))
        self.py_buffer.seek(position)
        self.py_buffer.readinto(c_buffer.contents)
        return 1  # non-zero return code for success
  
  # (Assuming py_buffer is a Python file buffer, e. g. io.BufferedReader)
  # Get the length of the buffer
  py_buffer.seek(0, 2)
  file_len = py_buffer.tell()
  py_buffer.seek(0)
  
  # Set up an interface structure for custom file access
  fileaccess = pdfium.FPDF_FILEACCESS()
  fileaccess.m_FileLen = file_len
  # CFUNCTYPE declaration copied from the bindings file (unfortunately, this is not applied automatically)
  functype = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(None), ctypes.c_ulong, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_ulong)
  # Alternatively, the CFUNCTYPE declaration can also be extracted dynamically using a helper function of pypdfium2
  functype = pdfium.get_functype(pdfium.FPDF_FILEACCESS, "m_GetBlock")
  # Instantiate a callable object, wrapped with the CFUNCTYPE declaration
  fileaccess.m_GetBlock = functype( _reader_class(py_buffer) )
  # Finally, load the document
  pdf = pdfium.FPDF_LoadCustomDocument(fileaccess, None)
  ```

* When using the raw API, special care needs to be taken regarding object lifetime, considering that Python may garbage collect objects as soon as their reference count reaches zero. However, the interpreter has no way of magically knowing how long the underlying resources of a Python object might still be needed on the C side, so measures need to be taken to keep such objects referenced until PDFium does not depend on them anymore.
  
  If resources need to remain valid after the time of a function call, PDFium documentation usually indicates this clearly. Ignoring requirements on object lifetime will lead to memory corruption (commonly resulting in a segmentation fault).
  
  For instance, the documentation on `FPDF_LoadCustomDocument()` states that
  > The application must keep the file resources |pFileAccess| points to valid until the returned FPDF_DOCUMENT is closed. |pFileAccess| itself does not need to outlive the FPDF_DOCUMENT.
  
  This means that the callback function and the Python buffer need to be kept alive as long as the `FPDF_DOCUMENT` is used.
  This can be achieved by referencing these objects in an accompanying class, e. g.
  
  ```python
  class PdfDataHolder:
      
      def __init__(self, buffer, function):
          self.buffer = buffer
          self.function = function
      
      def close(self):
          # Make sure both objects remain available until this function is called
          # No-op id() call to denote that the object needs to stay in memory up to this point
          id(self.function)
          self.buffer.close()
  
  # ... set up an FPDF_FILEACCESS structure
  
  # (Assuming `py_buffer` is the buffer and `fileaccess` the FPDF_FILEACCESS interface)
  data_holder = PdfDataHolder(py_buffer, fileaccess.m_GetBlock)
  pdf = pdfium.FPDF_LoadCustomDocument(fileaccess, None)
  
  # ... work with the pdf
  
  # Close the PDF to free resources
  pdfium.FPDF_CloseDocument(pdf)
  # Close the data holder, to keep the object itself and thereby the objects it
  # references alive up to this point, as well as to release the buffer
  data_holder.close()
  ```

* If you wish to check whether two objects returned by PDFium are the same, the `is` operator won't help you because `ctypes` does not have original object return (OOR),
  i. e. new, equivalent Python objects are created each time, although they might represent one and the same C object.[^ctypes_no_oor] That's why you'll want to use `ctypes.addressof()` to get the memory addresses of the underlying C object.
  For instance, this is used to avoid infinite loops on circular bookmark references when iterating through the document outline:
  ```python
  # (Assuming `pdf` is an FPDF_DOCUMENT)
  seen = set()
  bookmark = pdfium.FPDFBookmark_GetFirstChild(pdf, None)
  while bookmark:
      # bookmark is a pointer, so we need to use its `contents` attribute to get the object the pointer refers to
      # (otherwise we'd only get the memory address of the pointer itself, which would result in random behaviour)
      address = ctypes.addressof(bookmark.contents)
      if address in seen:
          break  # circular reference detected
      else:
          seen.add(address)
      bookmark = pdfium.FPDFBookmark_GetNextSibling(pdf, bookmark)
  ```
  
  [^ctypes_no_oor]: Confer the [ctypes documentation on Pointers](https://docs.python.org/3/library/ctypes.html#pointers).

* Finally, let's finish this guide with an example on how to render the first page of a document to a `PIL` image in `RGBA` colour format.
  ```python
  import math
  import ctypes
  import os.path
  import PIL.Image
  import pypdfium2 as pdfium
  
  # Load the document
  filepath = os.path.abspath("tests/resources/render.pdf")
  pdf = pdfium.FPDF_LoadDocument(filepath, None)
  
  # Check page count to make sure it was loaded correctly
  page_count = pdfium.FPDF_GetPageCount(pdf)
  assert page_count >= 1
  
  # Load the first page and get its dimensions
  page = pdfium.FPDF_LoadPage(pdf, 0)
  width  = math.ceil(pdfium.FPDF_GetPageWidthF(page))
  height = math.ceil(pdfium.FPDF_GetPageHeightF(page))
  
  # Create a bitmap
  use_alpha = False  # We don't render with transparent background
  bitmap = pdfium.FPDFBitmap_Create(width, height, int(use_alpha))
  # Fill the whole bitmap with a white background
  # The colour is given as a 32-bit integer in ARGB format (8 bits per channel)
  pdfium.FPDFBitmap_FillRect(bitmap, 0, 0, width, height, 0xFFFFFFFF)
  
  # Store common rendering arguments
  render_args = (
      bitmap,  # the bitmap
      page,    # the page
      # positions and sizes are to be given in pixels and may exceed the bitmap
      0,       # left start position
      0,       # top start position
      width,   # horizontal size
      height,  # vertical size
      0,       # rotation (as constant, not in degrees!)
      pdfium.FPDF_LCD_TEXT | pdfium.FPDF_ANNOT,  # rendering flags, combined with binary or
  )
  
  # Render the page
  pdfium.FPDF_RenderPageBitmap(*render_args)
  
  # Get a pointer to the first item of the buffer
  first_item = pdfium.FPDFBitmap_GetBuffer(bitmap)
  # Re-interpret the pointer to encompass the whole buffer
  buffer = ctypes.cast(first_item, ctypes.POINTER(ctypes.c_ubyte * (width * height * 4)))
  
  # Create a PIL image from the buffer contents
  img = PIL.Image.frombuffer("RGBA", (width, height), buffer.contents, "raw", "BGRA", 0, 1)
  # Save it as file
  img.save("out.png")
  
  # Free resources
  pdfium.FPDFBitmap_Destroy(bitmap)
  pdfium.FPDF_ClosePage(page)
  pdfium.FPDF_CloseDocument(pdf)
  ```

### [Command-line Interface](https://pypdfium2.readthedocs.io/en/stable/shell_api.html)

pypdfium2 also ships with a simple command-line interface, providing access to key features of the support model in a shell environment (e. g. rendering, text extraction, TOC inspection, document merging, ...).

The primary motivation in providing a CLI is to simplify manual testing, but it may be helpful in a variety of other situations as well.
Usage should be largely self-explanatory, assuming a minimum of familiarity with the command-line.


## Licensing

PDFium and pypdfium2 are available by the terms and conditions of either [`Apache-2.0`](LICENSES/Apache-2.0.txt) or [`BSD-3-Clause`](LICENSES/BSD-3-Clause.txt), at your choice.

Various other open-source licenses apply to the dependencies of PDFium. Verbatim copies of their respective licenses are contained in the file [`LicenseRef-PdfiumThirdParty.txt`](LICENSES/LicenseRef-PdfiumThirdParty.txt), which is also shipped with binary redistributions.

Documentation and examples of pypdfium2 are licensed under [`CC-BY-4.0`](LICENSES/CC-BY-4.0.txt).

pypdfium2 complies with the [reuse standard](https://reuse.software/spec/) by including [SPDX](https://spdx.org/licenses/) headers in source files, and license information for data files in [`.reuse/dep5`](.reuse/dep5).

To the authors' knowledge, pypdfium2 is one of the very rare Python libraries that are capable of PDF rendering while not being covered by restrictive licenses which prohibit the use in closed-source projects (such as the `GPL`).[^liberal_pdf_renderlibs]

[^liberal_pdf_renderlibs]: The only other liberal-licensed PDF rendering libraries known to the authors are [`pdf.js`](https://github.com/mozilla/pdf.js/) (JavaScript) and [`Apache PDFBox`](https://github.com/apache/pdfbox) (Java). `pdf.js` is limited to a web environment. Creating Python bindings to `PDFBox` might be possible but there is no serious solution yet (apart from amateurish wrappers around its command-line API).


## Issues

While using pypdfium2, you might encounter bugs or missing features.

In the endeavour to improve the product, the maintainers wish to be informed about any problems related to pypdfium2 usage.
Therefore, the first place for your report should be this repository.
Remember to include applicable details such as tracebacks, operating system and CPU architecture, as well as the versions of pypdfium2 and used dependencies.

In case your issue could be tracked down to a third-party dependency, we will accompany or conduct subsequent measures.

Here is a roadmap of relevant places:
* pypdfium2
  - [Issues panel](https://github.com/pypdfium2-team/pypdfium2/issues): Initial reports of specific issues.
    They may need to be transferred to other projects. Issues related to support model code, packaging or documentation probably need to be addressed in pypdfium2 itself.
  - [Discussions page](https://github.com/pypdfium2-team/pypdfium2/discussions): General questions and suggestions.
  - In case you do not want to publicly disclose the issue or your code, you may also contact the maintainers privately via e-mail.
* PDFium
  - [Bug tracker](https://bugs.chromium.org/p/pdfium/issues/list): Defects in PDFium.
    Beware: The bridge between Python and C increases the probability of integration issues or API misuse.
    The symptoms can often make it look like a PDFium bug while it is not. In some cases, this may be quite difficult to distinguish.
  - [Mailing list](https://groups.google.com/g/pdfium/): Questions regarding PDFium usage.
* [pdfium-binaries](https://github.com/bblanchon/pdfium-binaries/issues): Binary builder.
* [ctypesgen](https://github.com/ctypesgen/ctypesgen/issues): Bindings generator.

### Known limitations

pypdfium2 also has some drawbacks, of which you will be informed below.

#### Incompatibility with CPython 3.7.6 and 3.8.1

pypdfium2 cannot be used with releases 3.7.6 and 3.8.1 of the CPython interpreter due to a [regression](https://github.com/python/cpython/pull/16799#issuecomment-612353119) that broke ctypesgen-created string handling code.

#### Risk of unknown object lifetime violations

As outlined in the raw API section, it is essential that Python-managed resources remain available as long as they are needed by PDFium.

The problem is that the Python interpreter may garbage collect objects with reference count zero at any time. Thus, it can happen that an unreferenced but still required object by chance stays around long enough before it is garbage collected. Such dangling objects are likely to cause non-deterministic segmentation faults.
If the timeframe between reaching reference count zero and removal is sufficiently large and roughly consistent across different runs, it is even possible that mistakes regarding object lifetime remain unnoticed for a long time.

Although great care has been taken while developing the support model, it cannot be fully excluded that unknown object lifetime violations are still lurking around somewhere, especially if unexpected requirements were not documented by the time the code was written.

#### No direct access to PDF data structures

It should be noted that PDFium, unlike many other PDF libraries, is currently not providing direct access to raw PDF data structures. It does not publicly expose APIs to read/write PDF dictionaries, name trees, etc. Instead, it merely offers a variety of higher-level functions to modify PDFs. While these are certainly useful to abstract away some of the format's complexity and to avoid the creation of invalid PDFs, the fact that universal instruments for low-level access are largely missing in the public API does considerably limit the library's potential. If PDFium's capabilities are not sufficient for your use case, or you just wish to work with the raw PDF structure on your own, you may want to consider other products such as [`pikepdf`](https://github.com/pikepdf/pikepdf) to use instead of, or in conjunction with, pypdfium2.


## Development

This section contains some key information relevant for project maintainers.

<!-- TODO wheel tags, maintainer access, GitHub peculiarities -->

### Documentation

pypdfium2 provides API documentation using [sphinx](https://github.com/sphinx-doc/sphinx/). It may be rendered to various formats, including HTML:
```bash
sphinx-build -b html ./docs/source ./docs/build/html/
```

Built documentation is hosted on [`readthedocs.org`](https://readthedocs.org/projects/pypdfium2/).
It is primarily configured using a [`.readthedocs.yaml`](.readthedocs.yaml) file (see the [instructions](https://docs.readthedocs.io/en/stable/config-file/v2.html)).
The web interface also provides an administration page for maintainers.

### Testing

pypdfium2 contains a small test suite to verify the library's functionality. It is written with [pytest](https://github.com/pytest-dev/pytest/):
```bash
python3 -m pytest tests/
```
You may pass `-sv` to get more detailed output.

### Release workflow

The release process is fully automated using Python scripts and a CI setup for GitHub Actions.
A new release is triggered every Monday, following the schedule of `pdfium-binaries`.
You may also trigger the workflow manually using the GitHub Actions panel or the [`gh`](https://cli.github.com/) command-line tool.

Python release scripts are located in the folder `setupsrc/pl_setup`, along with custom setup code:
* `update_pdfium.py` downloads binaries and generates the bindings.
* `craft_wheels.py` builds platform-specific wheel packages and a source distribution suitable for PyPI upload.
* `autorelease.py` takes care of versioning, changelog, release note generation and VCS checkin.

The autorelease script has some peculiarities maintainers should know about:
* The changelog for the next release shall be written into `docs/devel/changelog_staging.md`.
  On release, it will be moved into the main changelog under `docs/source/changelog.md`, annotated with the PDFium version update.
  It will also be shown on the GitHub release page.
* pypdfium2 versioning uses the pattern `major.minor.patch`, optionally with an appended beta mark (e. g. `2.7.1`, `2.11.0`, `3.0.0b1`, ...).
  Version changes are based on the following logic:
  * If PDFium was updated, the minor version is incremented.
  * If only pypdfium2 code was updated, the patch version is incremented instead.
  * Major updates and beta marks are controlled via empty files in the `autorelease/` directory.
    If `update_major.txt` exists, the major version is incremented.
    If `update_beta.txt` exists, a new beta tag is set, or an existing one is incremented.
    These files are removed automatically once the release is finished.
  * If switching from a beta release to a non-beta release, only the beta mark is removed while minor and patch versions remain unchanged.

In case of necessity, you may also forego autorelease/CI and do the release manually, which will roughly work like this (though ideally it should never be needed):
* Commit changes to the version file
  ```bash
  git add src/pypdfium2/version.py
  git commit -m "increment version"
  git push
  ```
* Create a new tag that matches the version file
  ```bash
  # substitute $VERSION accordingly
  git tag -a $VERSION
  git push --tags
  ```
* Build the packages
  ```bash
  python3 setupsrc/pl_setup/update_pdfium.py
  python3 setupsrc/pl_setup/craft_wheels.py
  ```
* Upload to PyPI
  ```bash
  # make sure the packages are valid
  twine check dist/*
  # upload to PyPI (this will interactively ask for your username/password)
  twine upload dist/*
  ```
* Update the `stable` branch to trigger a documentation rebuild
  ```bash
  git checkout stable
  git rebase origin/main  # alternatively: git reset --hard main
  git checkout main
  ```

If something went wrong with commit or tag, you can still revert the changes:
```bash
# perform an interactive rebase to change history (substitute $N_COMMITS with the number of commits to drop or modify)
git rebase -i HEAD~$N_COMMITS
git push --force
# delete local tag (substitute $TAGNAME accordingly)
git tag -d $TAGNAME
# delete remote tag
git push --delete origin $TAGNAME
```
Faulty PyPI releases may be yanked using the web interface.


## In Use

We are curious to see what people are doing with pypdfium2. Always feel free to share knowledge or code samples on the discussions page.
Here are some public projects that are known to use pypdfium2:

* [doctr](https://github.com/mindee/doctr), an OCR library powered by deep learning, uses pypdfium2 to render PDFs.
* [EDS-PDF](https://github.com/aphp/edspdf), a framework for PDF text extraction and classification, also uses pypdfium2 for rendering.
* [Arabic-OCR](https://github.com/ssraza21/Arabic-OCR), a small web application to create digital documents from the result of arabic OCR, renders PDF pages with pypdfium2.
* [Extract-URLs](https://github.com/elescamilla/Extract-URLs/), uses pypdfium2 to extract URLs from PDF documents.
* [py-pdf/benchmarks](https://github.com/py-pdf/benchmarks) compares pypdfium2's text extraction capabilities with other Python PDF libraries.
* [pdfbrain](https://github.com/innodatalabs/pdfbrain) provides alternative helper classes around the raw API exposed by pypdfium2. It predates pypdfium2's own support model and only covers PDF parsing, not manipulation.

*Your project uses pypdfium2, but is not part of the list yet? Please let us know!*

There are also a few projects that *could* update to pypdfium2 but are still using its predecessor, pypdfium:
* [kuafu](https://github.com/YinlinHu/kuafu), an unmaintained PyQt5-based PDF reader, provides a PDFium backend.
* [microsoft/OCR-Form-Tools](https://github.com/microsoft/OCR-Form-Tools) uses pypdfium to render PDFs.


## Thanks to[^thanks_to]

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

[^thanks_to]: People listed in this section may not necessarily have contributed any copyrightable code to the repository. Some have rather helped with ideas, or contributions to dependencies of pypdfium2.


## History

pypdfium2 is the successor of *pypdfium* and *pypdfium-reboot*.

Inspired by *wowpng*, the first known proof of concept Python binding to PDFium using ctypesgen, the initial *pypdfium* package was created. It had to be updated manually, which did not happen frequently. There were no platform-specific wheels, but only a single wheel that contained binaries for 64-bit Linux, Windows and macOS.

*pypdfium-reboot* then added a script to automate binary deployment and bindings generation to simplify regular updates. However, it was still not platform specific.

pypdfium2 is a full rewrite of *pypdfium-reboot* to build platform-specific wheels and consolidate the setup scripts. Further additions include ...
* A CI workflow to automatically release new wheels every Monday
* Support models that conveniently wrap the raw PDFium/ctypes API
* Test code
* A script to build PDFium from source
