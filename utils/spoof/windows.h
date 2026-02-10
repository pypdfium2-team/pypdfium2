// SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
// SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

// This is a fake <windows.h> shim providing a nullpointer replacement for the one windows type pdfium uses (HDC)
// This will allow us to cross-generate bindings that include windows-only members from non-windows hosts.
// pypdfium2-ctypesgen's Readme suggests this approach in the Tips & Tricks section.

typedef void* HDC;
