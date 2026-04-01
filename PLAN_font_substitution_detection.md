# Plan: Missing Font Detection for pypdfium2

## Context

PR #396 attempted to warn users about non-embedded fonts during PDF rendering. It was closed due to two issues:
1. **Crash**: Passing `textpage` kwarg through `PdfObject.__init__()` broke non-text objects (images, paths, forms)
2. **False positives**: Warned about ALL non-embedded fonts, even those installed on the system

## Approaches Explored & Discarded

### `FPDF_GetDefaultSystemFontInfo` (pdfium sysfontinfo API)
`GetFont()` and `MapFont()` return NULL for ALL fonts on macOS, despite pdfium rendering those fonts correctly. The internal font resolution uses different code paths not accessible through this API.

### Platform-native font enumeration (Core Text / fontconfig / registry)
Works but introduces ~80 lines of platform-specific code in a project that currently has zero. Also fragile on macOS Sequoia where core fonts (Arial, Helvetica) are missing from `CTFontManagerCopyAvailableFontFamilyNames()` enumeration.

## Solution: PDFium-Native Substitution Detection

Instead of asking "is the font installed?", ask "what did PDFium actually substitute?"

**Two signals, from existing PDFium APIs:**
- `FPDFFont_GetBaseFontName()` — what the PDF requested
- `FPDFFont_GetFamilyName()` — what PDFium actually resolved to

**Empirically verified behavior:**

| Scenario | Base Name | Family Name | Data Size |
|---|---|---|---|
| Embedded | Ubuntu | Ubuntu | 14,824 |
| Resolved from system | Helvetica | Arial | 773,236 |
| Resolved from system | STSong | Songti SC | 66,933,080 |
| PDFium built-in | Symbol | Chrom Symbol OTF | 16,729 |
| **Missing font** | **NotoSansCJKsc-Regular** | **Chrome Sans MM** | **66,919** |
| **Missing font** | **SimSun** | **Chrome Sans MM** | **66,919** |

**Two reliably detectable categories of non-embedded font resolution:**
1. **Resolved** (e.g., Helvetica → Arial) — expected substitution
2. **Unresolved** (e.g., NotoSansCJKsc-Regular → Chrome Sans MM) — font completely missing

A third category exists but is **not reliably detected** by this API:
3. **Wrong variant** (Linux scenario) — the correct font family IS found but the wrong weight/style is used. Since `FPDFFont_GetFamilyName()` only returns the family, not the resolved face/style, variant-level mismatches collapse to the same output as a correct resolution. Style-sensitive detection is deferred along with `get_unresolved_fonts()`.

`get_font_substitutions()` exposes categories 1 and 2 — the user inspects `{base: {families}}` and can spot family-level mismatches. Variant-level mismatches require manual inspection of rendered output.

## Files to Modify

### 1. `src/pypdfium2/_helpers/pageobjects.py` — Add `PdfFont.is_embedded()`

`FPDFFont_GetIsEmbedded()` returns 1 (embedded), 0 (not embedded), or -1 (failure). Must handle the -1 case explicitly:

```python
def is_embedded(self):
    rc = pdfium_c.FPDFFont_GetIsEmbedded(self)
    if rc == -1:
        raise PdfiumError("Failed to determine font embedding status.")
    return rc == 1
```

### 2. `src/pypdfium2/_helpers/textpage.py` — Add `get_font_substitutions()` to `PdfTextPage`

**`get_font_substitutions()`** — Iterates text objects on the page via `self.page.get_objects(filter=[FPDF_PAGEOBJ_TEXT])`, calls `obj.get_font()` on each. For non-embedded fonts, records `{base_name: {family_names}}`.

Returns `dict[str, set[str]]` — maps each non-embedded base font name to the set of family names PDFium resolved it to. Using `set` avoids silent overwrites if the same base name resolves differently across objects (e.g., different FontDescriptor flags).

No `textpage` assignment needed — `get_font()`, `is_embedded()`, `get_base_name()`, and `get_family_name()` all work without a textpage. Only `extract()` requires it, and we don't call it.

**`get_unresolved_fonts()`** — **Deferred.** PDFium has multiple internal fallback paths (generic sans, serif, symbol, etc. — see `cfx_fontmapper.cpp`). A single-sentinel probe would miss unresolved fonts that land on a different internal fallback. Will revisit when we have a robust multi-fallback detection strategy or when PDFium adds a proper "font not found" callback (tracked in https://issues.chromium.org/issues/464315000).

### 3. `tests/test_textpage.py` — Tests

- `test_font_is_embedded()` — Verify on text.pdf: embedded Ubuntu returns True. For the -1 (failure) path, test with an invalid handle via `PdfFont(None)` to trigger `FPDFFont_GetIsEmbedded` returning -1, and assert `PdfiumError` is raised.
- `test_get_font_substitutions_embedded()` — text.pdf (all fonts embedded) → empty dict
- `test_get_font_substitutions_empty_page()` — empty.pdf → empty dict
- `test_get_font_substitutions_fake_font()` — Load a handcrafted test PDF fixture containing a non-embedded reference to a non-existent font. Assert the dict contains the fake font name mapped to a non-empty set of family names.

### 4. Test fixture

A minimal handcrafted PDF byte string, defined inline in the test module, that references a non-existent, non-embedded font. Inline bytes are preferred over a resource file to avoid REUSE/licensing overhead for test resources. This is needed because the helper APIs don't expose a clean way to create a text object with an arbitrary bogus font name — `FPDFText_LoadStandardFont` only accepts the 14 standard fonts.

### 5. No changes to:
- `page.py` — No `textpage` parameter added to `get_objects()`
- `PdfObject.__init__` — No `textpage` kwarg (fixes the original crash)
- No new internal modules

## Design Decisions

1. **No textpage assignment**: `get_font_substitutions()` only needs `get_font()`, `is_embedded()`, `get_base_name()`, `get_family_name()` — none require a textpage.

2. **`dict[str, set[str]]`** instead of `dict[str, str]`: The same base name could theoretically resolve to different families across objects (different FontDescriptor flags). Using `set` is correct and avoids silent data loss.

3. **Methods on PdfTextPage** (not PdfPage): Per reviewer feedback — the textpage is the natural context for text/font operations.

4. **Opt-in** (not called in render()): Per reviewer preference.

5. **Ship `get_font_substitutions()` first**: This is the solid, immediately useful API. `get_unresolved_fonts()` is deferred until a robust multi-fallback detection strategy is available.

6. **Proper error handling in `is_embedded()`**: `FPDFFont_GetIsEmbedded()` returns -1 on failure; raise `PdfiumError` instead of masking it as `True`.

## Verification

```bash
# Run existing tests (ensure no regressions)
python -m pytest tests/ -x

# Run new tests specifically
python -m pytest tests/test_textpage.py -v -k "font"

# Manual verification
python -c "
import pypdfium2 as pdfium
pdf = pdfium.PdfDocument('tests/resources/text.pdf')
page = pdf[0]
tp = page.get_textpage()
print('Substitutions:', tp.get_font_substitutions())
"
```
