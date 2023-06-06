<!-- SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- In helpers, closing a parent object now automatically closes the children to ensure correct order.
  This notably enhances safety of closing and absorbs the common mistake of closing a parent but missing child close calls. See commit [eb07605](https://github.com/pypdfium2-team/pypdfium2/commit/eb07605fcac124b4fe68f6baf60c86183170d259) for more info.
- In `init_forms()`, attempt to call `FPDF_LoadXFA()` and warn on failure, though as of this writing it always fails.
  An upstream issue is suspected.
