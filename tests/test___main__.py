# SPDX-FileCopyrightText: 2021 Adam Huganir <adam@huganir.com>
# SPDX-License-Identifier: Apache-2.0

from pypdfium2 import OptimiseMode
from pypdfium2 import __main__ as main
import pytest


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("90", 90),
        ("0", 0),
    ],
)
def test_rotation_type(test_input, expected):
    assert main.rotation_type(test_input) == expected


def test_rotation_type_fail_oob():
    with pytest.raises(ValueError):
        main.rotation_type("101")


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("None", None),
        ("none", None),
        ("10", 10),
        ("0xFFFFFFFF", 0xFFFFFFFF),
    ],
)
def test_hex_or_none_type(test_input, expected):
    assert main.hex_or_none_type(test_input) == expected


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("", None),
        ("1,2", [0, 1]),
        ("3-5", [2, 3, 4]),
        ("5-3", [4, 3, 2]),
        ("1", [0]),
    ],
)
def test_pagetext_type(test_input, expected):
    assert main.pagetext_type(test_input) == expected


def test_parse_args():
    argv = [
        '-i', 'path/to/document.pdf',
        '-o', 'output_dir/',
        '--password', 'test-password',
        '--pages', '1,4,5-7,6-4',
    ]
    
    args = main.parse_args(argv)
    assert args.pages == [0, 3, 4, 5, 6, 5, 4, 3]
    assert args.pdffile == 'path/to/document.pdf'
    assert args.output == 'output_dir/'
    assert args.password == 'test-password'
