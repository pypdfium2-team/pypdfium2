# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import io
import filecmp
import contextlib
from pathlib import Path
import pytest
import pypdfium2 as pdfium
import pypdfium2.raw as pdfium_c
import pypdfium2.__main__ as pdfium_cli
from .conftest import TestResources, TestExpectations


def run_cli(argv, exp_stdout=None, normalize_lfs=False):
    
    argv = [str(a) for a in argv]
    
    if exp_stdout is None:
        pdfium_cli.api_main(argv)
        
    else:
        
        stdout_buf = io.StringIO()
        with contextlib.redirect_stdout(stdout_buf):
            pdfium_cli.api_main(argv)
        
        if isinstance(exp_stdout, Path):
            exp_stdout = exp_stdout.read_text()
        
        stdout = stdout_buf.getvalue()
        if normalize_lfs:
            stdout = stdout.replace("\r\n", "\n")
        
        assert stdout == exp_stdout


def _get_files(dir):
    return sorted([p.name for p in dir.iterdir() if p.is_file()])


def _get_text(pdf, index):
    return pdf[index].get_textpage().get_text_bounded()


@pytest.mark.parametrize("resource", ["toc", "toc_viewmodes", "toc_circular", "toc_maxdepth"])
def test_toc(resource):
    run_cli(["toc", getattr(TestResources, resource)], getattr(TestExpectations, resource))


def test_attachments(tmp_path):
    
    run_cli(["attachments", TestResources.attachments, "list"], TestExpectations.attachments_list)
    
    run_cli(["attachments", TestResources.attachments, "extract", "-o", tmp_path])
    assert _get_files(tmp_path) == ["1_1.txt", "2_attached.pdf"]
    
    edited_pdf = tmp_path / "edited.pdf"
    run_cli(["attachments", TestResources.attachments, "edit", "--del-numbers", "1,2", "--add-files", TestResources.mona_lisa, "-o", edited_pdf])
    run_cli(["attachments", edited_pdf, "list"], "[1] mona_lisa.jpg\n")


def test_images(tmp_path):
    
    img_pdf = tmp_path / "img_pdf.pdf"
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    
    run_cli(["imgtopdf", TestResources.mona_lisa, "-o", img_pdf])
    run_cli(["extract-images", img_pdf, "-o", output_dir])
    
    output_name = "img_pdf_1.jpg"
    assert _get_files(output_dir) == [output_name]
    assert filecmp.cmp(TestResources.mona_lisa, output_dir/output_name)


@pytest.mark.parametrize("strategy", ["range", "bounded"])
def test_extract_text(strategy):
    run_cli(["extract-text", TestResources.text, "--strategy", strategy], TestExpectations.text_extract, normalize_lfs=True)


@pytest.mark.parametrize("resource", ["multipage", "attachments", "forms"])
def test_pdfinfo(resource):
    run_cli(["pdfinfo", getattr(TestResources, resource)], getattr(TestExpectations, "pdfinfo_%s" % resource))


@pytest.mark.parametrize("resource", ["images"])
def test_pageobjects(resource):
    run_cli(["pageobjects", getattr(TestResources, resource)], getattr(TestExpectations, "pageobjects_%s" % resource))


def test_arrange(tmp_path):
    
    out = tmp_path / "out.pdf"
    run_cli(["arrange", TestResources.multipage, TestResources.encrypted, TestResources.empty, "--pages", "1,3", "--passwords", "_", "test_user", "-o", out])
    
    pdf = pdfium.PdfDocument(out)
    assert len(pdf) == 4
    
    exp_texts = ["Page\r\n1", "Page\r\n3", "Encrypted PDF", ""]
    assert [_get_text(pdf, i) for i in range(len(pdf))] == exp_texts


def test_tile(tmp_path):
    
    out = tmp_path / "out.pdf"
    run_cli(["tile", TestResources.multipage, "-r", 2, "-c", 2, "--width", 21.0, "--height", 29.7, "-u", "cm", "-o", out])
    
    pdf = pdfium.PdfDocument(out)
    assert len(pdf) == 1
    page = pdf.get_page(0)
    pageobjs = list( page.get_objects(max_depth=1) )
    assert len(pageobjs) == 3
    assert all(o.type == pdfium_c.FPDF_PAGEOBJ_FORM for o in pageobjs)


def test_render_multipage(tmp_path):
    
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    
    run_cli(["render", TestResources.multipage, "-o", out_dir, "--scale", 0.2, "-f", "jpg"])
    
    out_files = list(out_dir.iterdir())
    assert sorted([f.name for f in out_files]) == ["multipage_1.jpg", "multipage_2.jpg", "multipage_3.jpg"]


def test_version():
    
    exp_message = "pypdfium2 %s (libpdfium %s, %s build)\n" % (pdfium.V_PYPDFIUM2, pdfium.V_LIBPDFIUM, pdfium.V_BUILDNAME)
    
    try:
        run_cli(["--version"], exp_message)
    except SystemExit:
        pass
