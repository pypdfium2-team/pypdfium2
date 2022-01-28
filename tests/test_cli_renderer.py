# SPDX-FileCopyrightText: 2021 Adam Huganir <adam@huganir.com>
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pytest
import os.path
import pypdfium2 as pdfium
from pypdfium2._cli import renderer


@pytest.mark.parametrize(
    "test_input, expected",
    [
        ("0", 0),
        ("90", 90),
        ("180", 180),
        ("270", 270),
    ],
)
def test_rotation_type(test_input, expected):
    assert renderer.rotation_type(test_input) == expected


def test_rotation_type_fail_oob():
    with pytest.raises(ValueError, match="Invalid rotation value"):
        renderer.rotation_type("101")
    with pytest.raises(ValueError, match="invalid literal for int()"):
        renderer.rotation_type("string")


@pytest.mark.parametrize(
    "test_input, expected",
    [
        ("None", None),
        ("none", None),
        ("10", 10),
        ("0xFFFFFFFF", 0xFFFFFFFF),
    ],
)
def test_colour_type(test_input, expected):
    assert renderer.colour_type(test_input) == expected


@pytest.mark.parametrize(
    "test_input, expected",
    [
        ("", None),
        ("1,2", [0, 1]),
        ("3-5", [2, 3, 4]),
        ("5-3", [4, 3, 2]),
        ("1", [0]),
    ],
)
def test_pagetext_type(test_input, expected):
    assert renderer.pagetext_type(test_input) == expected


def test_parse_args():
    
    argv = [
        'path/to/document.pdf',
        '-o', 'output_dir/',
        '--pages', '1,4,5-7,6-4',
        '--scale', '2',
        '--rotation', '90',
        '--colour', '0xFFFFFFFF',
        '--optimise-mode', 'none',
        '--processes', '4',
    ]
    
    args = renderer.parse_args(argv, prog="", desc="")
    
    assert args.inputs == ['path/to/document.pdf']
    assert args.output == os.path.abspath('output_dir/')
    assert args.pages == [0, 3, 4, 5, 6, 5, 4, 3]
    assert args.scale == 2
    assert args.rotation == 90
    assert args.colour == 0xFFFFFFFF
    assert args.no_annotations == False
    assert args.optimise_mode == pdfium.OptimiseMode.none
    assert args.greyscale == False
    assert args.processes == 4
