<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Planned Changes

The following API breaking changes are being considered for the next major release:
* Removal of the public function `raise_error()`, given that it is only usable for document loading APIs which are sufficiently managed by support models anyway.
* The rendering CLI may be adapted to accept only a single file, to simplify the code and to be able to properly implement a password option.
* Rendering parameters might change.
