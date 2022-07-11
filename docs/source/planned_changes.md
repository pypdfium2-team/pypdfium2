<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Planned Changes

The following API breaking changes are being considered for the next major release:
* Removal of the public function `raise_error()`, considering that it is only usable for document loading APIs which are sufficiently managed by support models anyway.
* Possibly replacing some rendering parameters with means to forward arbitrary PDFium rendering flags, to reduce duplication. This might include the parameters `annotations`, `greyscale`, `optimise_mode` and `no_antialias`.
* The rendering CLI may be changed to accept single files only, to simplify the code and to be able to properly implement a password option.
