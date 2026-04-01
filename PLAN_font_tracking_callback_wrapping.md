# Plan: FPDF_SYSFONTINFO Callback Wrapping for Font Miss Detection

## Context

PR #413 added `PdfFont.is_embedded()` and `PdfTextPage.get_font_substitutions()`. The maintainer (mara004) rejected `get_font_substitutions()` as heuristic-based (comparing base name vs family name) and too "caller-side" (doesn't use C APIs directly). They suggested wrapping `FPDF_GetDefaultSystemFontInfo()` callbacks to log what goes through `MapFont`/`GetFont`.

We experimentally verified this approach works on **both macOS and Linux**:
- macOS: `MapFont(NotoSansCJKsc)` → FOUND, `MapFont(FakeTestFont)` → MISS
- Linux (no CJK fonts): `MapFont(NotoSansCJKsc)` → MISS, `MapFont(FakeTestFont)` → MISS

The earlier finding that "MapFont/GetFont return NULL for ALL fonts on macOS" was wrong — it was caused by testing before `EnumFonts` populated the font map.

## How It Works

1. After `FPDF_InitLibraryWithConfig()`, call `FPDF_GetDefaultSystemFontInfo()` to get a fresh default font info
2. Create a wrapper `FPDF_SYSFONTINFO` struct that delegates all callbacks to the default
3. Install via `FPDF_SetSystemFontInfo(wrapper)` — replaces the current system font info
4. When PDFium loads pages, it calls `EnumFonts` on our wrapper (with a valid mapper pointer) — we delegate to the default, which populates its internal font map
5. `MapFont`/`GetFont` calls go through our wrapper — we log `{font_name: found_bool}` and delegate to the default
6. Users query the log via `pdfium.get_font_requests()`

## Files to Modify

### 1. `src/pypdfium2/_font_tracking.py` — **NEW**

All wrapper logic in a new internal module (matches `_library_scope.py`, `_lazy.py` naming convention).

**Private state** (module-level, kept alive for library lifetime):
- `_default_info` — pointer from `FPDF_GetDefaultSystemFontInfo()`
- `_wrapper` — our `FPDF_SYSFONTINFO` struct
- `_cb_refs` — list holding ctypes callback objects to prevent GC
- `_font_requests` — `dict[str, bool]` mapping font name → was_found
- `_lock` — `threading.RLock` for thread safety

**`_install_font_tracking()`** — called from `init_lib()`:
- Gets default font info, creates wrapper, installs it
- If `FPDF_GetDefaultSystemFontInfo()` returns NULL, silently skips (graceful degradation)
- Wrapper callbacks:
  - `MapFont`: delegate to default, log `{face_name: bool(result)}`
  - `GetFont`: delegate to default, log `{face_name: bool(result)}`
  - `EnumFonts`: delegate to default (passes mapper pointer through)
  - All others (`Release`, `GetFontData`, `GetFaceName`, `GetFontCharset`, `DeleteFont`): delegate to default
- Log semantics: a `True` never gets overwritten by a later `False` (font found once = found)
- Uses `pdfium_i.set_callback()` for callback installation, matching existing codebase pattern (`unsupported.py:43`, `page.py:472`)

**Atomicity**: `_install_font_tracking()` must be ordered so that `FPDF_SetSystemFontInfo()` is the **last** operation. All fallible work (getting default info, creating callbacks, building the wrapper struct, populating strong refs list) must complete first. Once `FPDF_SetSystemFontInfo()` is called, PDFium holds a pointer to the wrapper, so all supporting state must already be finalized. The sequence:
1. `FPDF_GetDefaultSystemFontInfo()` — get default info (may return NULL → early return)
2. Create all CFUNCTYPE callback objects and collect in a local list
3. Build the wrapper struct and assign all callback fields
4. Assign module-level strong refs (`_default_info`, `_wrapper`, `_cb_refs`) — these must be set before step 5
5. `FPDF_SetSystemFontInfo(wrapper)` — point of no return, no fallible work after this

**Fail-open exception handling** — critical safety requirement:

Since the wrapper runs as a ctypes callback invoked by PDFium's C code, any unhandled Python exception in a callback will be swallowed by ctypes and may cause PDFium to receive a bad return value (NULL/0), turning a tracking bug into a rendering regression for all users. Every intercepting callback (`MapFont`, `GetFont`) **must**:
1. **Always delegate first** — call the default callback and capture the result before any logging
2. **Wrap all logging in `try/except Exception`** — if name decoding or dict update fails, swallow the error and return the delegation result unchanged
3. **Use `errors="replace"` for all byte-to-str decoding** — never let a decode error propagate

Pattern for MapFont/GetFont:
```python
def _map_font(pThis, weight, italic, charset, pf, face, exact):
    # Delegate FIRST — this must always succeed
    result = default.MapFont(_default_info, weight, italic, charset, pf, face, exact)
    # Log with fail-open — never let logging break delegation
    try:
        name = ctypes.string_at(face).decode("utf-8", errors="replace") if face else None
        if name:
            with _lock:
                if not _font_requests.get(name, False):
                    _font_requests[name] = bool(result)
    except Exception:
        pass
    return result
```

Pure delegation callbacks (`EnumFonts`, `GetFontData`, etc.) do not need `try/except` since they contain no logging logic — they just pass through to the default.

**Public functions** (both acquire `_lock` to prevent races with concurrent callbacks):
- `get_font_requests() → dict[str, bool]` — acquires `_lock`, returns a snapshot copy of the log
- `clear_font_requests()` — acquires `_lock`, clears the log

GC prevention: follows the `PdfUnspHandler` pattern (`unsupported.py:46`) — `atexit.register` to prevent GC of the wrapper/default_info/callbacks.

**Lifecycle and ownership**:

The wrapper's `Release` callback **delegates** to `default.Release(_default_info)`. This is the correct ownership path: once `FPDF_SetSystemFontInfo(wrapper)` is called, PDFium only knows about the wrapper. During `FPDF_DestroyLibrary()`, PDFium calls `wrapper.Release`, which must free the default font info's internal state by delegating.

**Teardown ordering**: `_wrapper`, `_cb_refs`, and `_default_info` must remain alive until **after** `FPDF_DestroyLibrary()` completes, because PDFium calls `wrapper.Release` during library shutdown. There is no cleanup call before `FPDF_DestroyLibrary()`.

Provide `_reset_font_tracking()` called from `destroy_lib()` **after** `FPDF_DestroyLibrary()` to clear Python-side state (`_font_requests`). The ctypes objects (`_wrapper`, `_default_info`, `_cb_refs`) are left for process exit / GC — they are inert after library destroy.

**Re-init contract**: If `init_lib()` is called again after `destroy_lib()`, `_install_font_tracking()` replaces the module state with fresh objects. The old `_default_info` was already freed by `Release` during the prior `FPDF_DestroyLibrary()`, so no explicit free is needed. The old `_wrapper` and `_cb_refs` are simply overwritten (old refs drop to GC).

### 2. `src/pypdfium2/_library_scope.py` — Hook installation and teardown

Add lines in `init_lib()` after `LIBRARY_AVAILABLE.value = True`. The call must be wrapped in `try/except Exception` so that a failure in wrapper creation/import/callback setup never propagates — PDFium is already initialized and usable, font tracking is optional:
```python
pdfium_i.LIBRARY_AVAILABLE.value = True

try:
    from pypdfium2._font_tracking import _install_font_tracking
    _install_font_tracking()
except Exception:
    pass
```

Add 2 lines in `destroy_lib()` **after** `FPDF_DestroyLibrary()` (the wrapper must remain live during library shutdown since PDFium calls `Release` during destroy):
```python
from pypdfium2._font_tracking import _reset_font_tracking
_reset_font_tracking()
```

### 3. `src/pypdfium2/__init__.py` — Export public API

Add 1 line:
```python
from pypdfium2._font_tracking import get_font_requests, clear_font_requests
```

### 4. `src/pypdfium2/_helpers/textpage.py` — Docstring update

Add `See also` reference to `get_font_requests()` in `get_font_substitutions()` docstring.

### 5. `tests/test_font_tracking.py` — **NEW** test file

Font resolution callbacks are triggered by **page loading** (`pdf[0]` / `FPDF_LoadPage`), not by `PdfDocument(...)` alone. `PdfDocument(...)` only opens the document handle; `MapFont`/`GetFont` fire when PDFium actually loads a page and encounters non-embedded fonts. Tests must therefore call `pdf[0]` (and optionally `page.get_textpage()` or `page.render()`) to trigger font resolution before asserting on the log.

**Log isolation**: The wrapper is installed once at import time and the log is process-global. Entries persist across documents until cleared. Every test must call `clear_font_requests()` at the start (or use an autouse fixture) to prevent stale state from earlier tests polluting assertions.

- `test_font_requests_fake_font` — `clear_font_requests()`, load `FAKE_FONT_PDF`, call `pdf[0]` and `page.get_textpage()`, assert "FakeTestFont" appears in log with `found=False`
- `test_font_requests_embedded` — `clear_font_requests()`, load text.pdf, call `pdf[0]` and `page.get_textpage()`, assert the full log state: log should be empty (embedded fonts don't trigger MapFont), not just absence of "Ubuntu"
- `test_clear_font_requests` — populate log with a fake-font PDF load, call `clear_font_requests()`, assert `get_font_requests() == {}`
- `test_font_tracking_clean_exit` — **subprocess smoke test**: run `sys.executable -c "import pypdfium2; ..."` (load a page, then exit) in a subprocess. Use `sys.executable` to match the current interpreter, and inherit `PYTHONPATH` / the editable-install environment so the local package is importable. Assert exit code 0 and no traceback / "Exception ignored" / ctypes callback error text in stderr (don't assert stderr is completely empty — that's brittle against unrelated interpreter noise). This exercises the wrapper's `Release` callback and GC retention through `destroy_lib()` at process exit.

## Design Decisions

1. **Always-on**: Wrapper installed at init, negligible overhead (one Python function call per MapFont/GetFont, which only fires during font resolution). No opt-in needed.

2. **No noise filtering**: Internal PDFium probes (e.g., Euphemia UCAS on macOS) are logged alongside real requests. Filtering would require a fragile platform-dependent list. The docstring documents this.

3. **No name normalization**: PDFium may call `MapFont("NotoSansCJKsc")` while the PDF BaseFont is `NotoSansCJKsc-Regular`. The log records exactly what PDFium used. Documented in docstring.

4. **Keep existing APIs**: `PdfFont.is_embedded()` (wraps C API directly) and `get_font_substitutions()` (per-page base→family mapping) remain. They're complementary:
   - `get_font_requests()` — system-level: which fonts were not found (exact, from C callbacks)
   - `get_font_substitutions()` — PDF-level: what each font was substituted with

5. **Separate module**: `_font_tracking.py` keeps `_library_scope.py` minimal (adds 2 lines in init + 2 lines in destroy). Lifecycle concerns (wrapper struct, callback refs, default_info pointer) are self-contained.

6. **RLock over Lock**: Protects against potential re-entrant MapFont calls from PDFium.

## Verification

```bash
# Run full test suite
python -m pytest tests/ -x

# Run font tracking tests
python -m pytest tests/test_font_tracking.py -v

# Manual verification — pdf[0] triggers page load which fires MapFont
python -c "
import pypdfium2 as pdfium
pdfium.clear_font_requests()
pdf = pdfium.PdfDocument('path/to/test.pdf')
page = pdf[0]          # triggers FPDF_LoadPage → EnumFonts + MapFont
page.get_textpage()    # may trigger additional font resolution
print(pdfium.get_font_requests())
"

# Docker (Linux without CJK):
# Expect {'NotoSansCJKsc': False, ...}
# macOS:
# Expect {'NotoSansCJKsc': True, ...}
```
