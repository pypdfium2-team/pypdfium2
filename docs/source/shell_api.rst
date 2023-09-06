.. SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
.. SPDX-License-Identifier: CC-BY-4.0

Shell API
=========

pypdfium2 can also be used from the command-line.


Version
*******
.. command-output:: pypdfium2 --version


Main Help
*********
.. command-output:: pypdfium2 --help


.. FIXME we get a lot of duplication regarding input flags, which are attached to almost every subparser

Arranger
********
.. command-output:: pypdfium2 arrange --help


Attachments
***********
.. command-output:: pypdfium2 attachments --help
.. FIXME restructure attachments CLI so we can get help without having to specify a placeholder file
.. command-output:: pypdfium2 attachments file.pdf list --help
.. command-output:: pypdfium2 attachments file.pdf extract --help
.. command-output:: pypdfium2 attachments file.pdf edit --help


Image Extractor
***************
.. command-output:: pypdfium2 extract-images --help


Text Extractor
**************
.. command-output:: pypdfium2 extract-text --help


Image Converter
***************
.. command-output:: pypdfium2 imgtopdf --help


Page Objects Info
*****************
.. command-output:: pypdfium2 pageobjects --help


Document Info
*************
.. command-output:: pypdfium2 pdfinfo --help


Renderer
********
.. command-output:: pypdfium2 render --help


Page Tiler
**********
.. command-output:: pypdfium2 tile --help


TOC Reader
**********
.. command-output:: pypdfium2 toc --help
