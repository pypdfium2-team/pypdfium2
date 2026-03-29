# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import sys
import subprocess
import pytest
import pypdfium2 as pdfium
from .conftest import TestFiles


# Minimal PDF with a non-embedded reference to a non-existent font ("FakeTestFont").
FAKE_FONT_PDF = (
    b"%PDF-1.0\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]"
    b"/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
    b"4 0 obj<</Length 23>>\nstream\nBT /F1 12 Tf (X) Tj ET\nendstream\nendobj\n"
    b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/FakeTestFont>>endobj\n"
    b"xref\n0 6\n"
    b"0000000000 65535 f \n"
    b"0000000009 00000 n \n"
    b"0000000052 00000 n \n"
    b"0000000101 00000 n \n"
    b"0000000211 00000 n \n"
    b"0000000280 00000 n \n"
    b"trailer<</Size 6/Root 1 0 R>>\nstartxref\n344\n%%EOF\n"
)


@pytest.fixture
def listener():
    l = pdfium.PdfSysfontListener()
    yield l
    l.close()


def test_listener_tracks_fake_font(listener):
    pdf = pdfium.PdfDocument(FAKE_FONT_PDF)
    page = pdf[0]
    page.get_textpage()

    requests = listener.get_font_requests()
    fake_entries = {k: v for k, v in requests.items() if "FakeTestFont" in k}
    assert len(fake_entries) > 0
    assert any(v is False for v in fake_entries.values())


def test_listener_embedded_no_requests(listener):
    pdf = pdfium.PdfDocument(TestFiles.text)
    page = pdf[0]
    page.get_textpage()

    requests = listener.get_font_requests()
    # text.pdf uses embedded Ubuntu font — embedded fonts don't trigger MapFont/GetFont
    assert requests == {}


def test_listener_clear(listener):
    pdf = pdfium.PdfDocument(FAKE_FONT_PDF)
    page = pdf[0]
    page.get_textpage()
    assert listener.get_font_requests() != {}

    listener.clear_font_requests()
    assert listener.get_font_requests() == {}


def test_listener_manual_close():
    listener = pdfium.PdfSysfontListener()
    pdf = pdfium.PdfDocument(FAKE_FONT_PDF)
    page = pdf[0]
    page.get_textpage()
    assert listener.get_font_requests() != {}
    listener.close()


def test_listener_clean_exit():
    env = os.environ.copy()
    # Ensure the child imports the local source tree, not an installed package
    src_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
    env["PYTHONPATH"] = src_dir + os.pathsep + env.get("PYTHONPATH", "")

    result = subprocess.run(
        [sys.executable, "-c", (
            "import pypdfium2 as pdfium; "
            "listener = pdfium.PdfSysfontListener(); "
            "pdf = pdfium.PdfDocument(%r); "
            "page = pdf[0]; "
            "tp = page.get_textpage(); "
        ) % FAKE_FONT_PDF],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )
    assert result.returncode == 0, f"stdout={result.stdout!r}, stderr={result.stderr!r}"
    for marker in ["Traceback", "Exception ignored", "Error in atexit"]:
        assert marker not in result.stderr, f"Found {marker!r} in stderr: {result.stderr!r}"
