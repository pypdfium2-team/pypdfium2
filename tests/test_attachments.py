# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import io
import re
import ctypes
import pytest
import hashlib
import pypdfium2 as pdfium
import pypdfium2.raw as pdfium_c
from .conftest import TestFiles, OutputDir


def test_attachment():
    
    # TODO(geisserml) Break up in individual test cases. This has become far too convoluted.
    
    pdf = pdfium.PdfDocument(TestFiles.attachments)
    assert pdf.count_attachments() == 2
    
    atm_a = pdf.get_attachment(0)
    assert isinstance(atm_a, pdfium.PdfAttachment)
    assert isinstance(atm_a.raw, pdfium_c.FPDF_ATTACHMENT)
    assert atm_a.get_name() == "1.txt"
    assert atm_a.get_desc() == ""  # no previous desc
    atm_a.set_desc("Test description A")
    assert atm_a.get_desc() == "Test description A"
    atm_a.set_desc("Test description A_2")
    assert atm_a.get_desc() == "Test description A_2"
    data_a = atm_a.get_data()
    assert len(data_a) == 4
    assert data_a._type_ is ctypes.c_char
    assert str(data_a, encoding="utf-8") == "test"
    
    atm_b = pdf.get_attachment(1)
    assert atm_b.get_name() == "attached.pdf"
    assert atm_b.get_desc() == "This is a test string."  # has previous desc
    atm_b.set_desc("")  # set to empty
    assert atm_b.get_desc() ==""
    data_b = atm_b.get_data()
    assert len(data_b) == 5869
    
    assert atm_a.has_key("CreationDate")
    assert atm_a.get_str_value("CreationDate") == "D:20170712214438-07'00'"
    assert atm_a.get_str_value("ModDate") == "D:20160115091400"
    moddate_new = "D:20190115091400"
    atm_a.set_str_value("ModDate", moddate_new)
    assert atm_a.get_str_value("ModDate") == moddate_new
    
    exp_checksum = "098f6bcd4621d373cade4e832627b4f6"
    assert atm_a.get_value_type("CheckSum") == pdfium_c.FPDF_OBJECT_STRING
    assert atm_a.get_str_value("CheckSum") == "<%s>" % (exp_checksum.upper(), )
    assert exp_checksum == hashlib.md5(data_a).hexdigest()
    
    assert atm_a.has_key("Size")
    assert atm_a.get_value_type("Size") == pdfium_c.FPDF_OBJECT_NUMBER
    assert atm_a.get_str_value("Size") == ""
    
    assert not atm_a.has_key("asdf")
    assert atm_a.get_str_value("asdf") == ""
    
    in_text = "pypdfium2 test"
    atm_a.set_data(in_text.encode("utf-8"))
    assert str(atm_a.get_data(), encoding="utf-8") == in_text
    assert atm_a.get_str_value("ModDate") == ""
    cdate_new = atm_a.get_str_value("CreationDate")
    atm_a.set_str_value("ModDate", cdate_new)
    assert atm_a.get_str_value("ModDate") == cdate_new
    
    pdf_attached = pdfium.PdfDocument(data_b)
    assert len(pdf_attached) == 1
    page = pdf_attached[0]
    textpage = page.get_textpage()
    assert textpage.get_text_range() == "test"
    pdf_attached.close()  # implies closing page & textpage
    del page, textpage, pdf_attached
    
    # NOTE new attachment may appear at an arbitrary index (?)
    name_c = "Mona Lisa.jpg"
    atm_c = pdf.new_attachment(name_c)
    assert pdf.count_attachments() == 3
    assert atm_c.get_name() == name_c
    with pytest.raises(pdfium.PdfiumError, match=re.escape("Failed to extract attachment (buffer length 0).")):
        atm_c.get_data()
    data_c = TestFiles.mona_lisa.read_bytes()
    atm_c.set_data(data_c)
    assert atm_c.get_data().raw == data_c
    
    # obtain new attachment handles
    del atm_a, atm_b, atm_c
    atm_0 = pdf.get_attachment(0)
    assert atm_0.get_name() == "1.txt"
    assert atm_0.get_desc() == "Test description A_2"
    atm_1 = pdf.get_attachment(1)
    assert atm_1.get_name() == "Mona Lisa.jpg"
    assert atm_1.get_desc() == ""
    atm_2 = pdf.get_attachment(2)
    assert atm_2.get_name() == "attached.pdf"
    assert atm_2.get_desc() == ""
    del atm_0, atm_1, atm_2
    
    out_buffer_a = io.BytesIO()
    pdf.save(out_buffer_a)
    ro_pdf_a = pdfium.PdfDocument(out_buffer_a, autoclose=True)
    assert ro_pdf_a.count_attachments() == 3
    atm_2 = ro_pdf_a.get_attachment(2)
    assert atm_2.get_name() == "attached.pdf"
    assert atm_2.get_desc() == ""  # confirm that unsetting the desc passed saving
    ro_pdf_a.close()
    del atm_2
    
    # delete the above attachment and confirm the remaining attachments
    pdf.del_attachment(2)
    assert pdf.count_attachments() == 2
    out_path_b = OutputDir / "attachments_b.pdf"
    pdf.save(out_path_b)
    ro_pdf_b = pdfium.PdfDocument(out_path_b)
    assert ro_pdf_b.count_attachments() == 2
    atm_0 = ro_pdf_b.get_attachment(0)
    assert atm_0.get_name() == "1.txt"
    assert atm_0.get_desc() == "Test description A_2"
    atm_1 = ro_pdf_b.get_attachment(1)
    assert atm_1.get_name() == "Mona Lisa.jpg"
    assert atm_1.get_desc() == ""
