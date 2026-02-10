// SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
// SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

// This is a fake <windows.h> shim providing a nullpointer handle for the one windows type pdfium uses (HDC)
// This will allow us to cross-generate bindings that include windows-only members from non-windows hosts.
// pypdfium2-ctypesgen's Readme suggests this approach in the Tips & Tricks section.

// https://learn.microsoft.com/en-us/windows/win32/winprog/windows-data-types
// typedef HANDLE HDC; <- typedef PVOID HANDLE; <- typedef void *PVOID;
typedef void* HDC;
