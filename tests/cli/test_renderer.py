# SPDX-FileCopyrightText: 2021 Adam Huganir <adam@huganir.com>
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pytest
import os.path
import pypdfium2 as pdfium
from pypdfium2._cli import main
from pypdfium2._cli import render


def test_rotation_type():
    test_cases = [
        ("0", 0),
        ("90", 90),
        ("180", 180),
        ("270", 270),
    ]
    for input, expectation in test_cases:
        assert render.rotation_type(input) == expectation


def test_rotation_type_fail_oob():
    with pytest.raises(ValueError, match="Invalid rotation value"):
        render.rotation_type("101")
    with pytest.raises(ValueError, match="invalid literal for int()"):
        render.rotation_type("string")


def test_colour_type():
    test_cases = [
        ("None", None),
        ("none", None),
    ]
    for input, expectation in test_cases:
        assert render.colour_type(input) == expectation


def test_pagetext_type():
    test_cases = [
        ("", None),
        ("1,2", [0, 1]),
        ("3-5", [2, 3, 4]),
        ("5-3", [4, 3, 2]),
        ("1", [0]),
    ]
    for input, expectation in test_cases:
        assert render.pagetext_type(input) == expectation


def test_parse_args():
    
    argv = [
        'render',
        'path/to/document.pdf',
        '-o', 'output_dir/',
        '--pages', '1,4,5-7,6-4',
        '--scale', '2',
        '--rotation', '90',
        '--colour', '(255, 255, 255, 255)',
        '--optimise-mode', 'none',
        '--processes', '4',
    ]
    
    args = main.parse_args(argv)
    
    assert args.inputs == ['path/to/document.pdf']
    assert args.output == os.path.abspath('output_dir/')
    assert args.pages == [0, 3, 4, 5, 6, 5, 4, 3]
    assert args.scale == 2
    assert args.rotation == 90
    assert args.colour == (255, 255, 255, 255)
    assert args.no_annotations == False
    assert args.optimise_mode == pdfium.OptimiseMode.none
    assert args.greyscale == False
    assert args.processes == 4
