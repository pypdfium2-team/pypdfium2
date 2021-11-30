from pypdfium2 import OptimiseMode, _pypdfium
from pypdfium2.__main__ import (
    hex_or_none_type,
    pagetext_type,
    parse_args,
    rotation_type,
)
import pytest


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("90", 90),
        ("0", 0),
    ],
)
def test_rotation_type(test_input, expected):
    assert rotation_type(test_input) == expected


def test_rotation_type_fail_oob():
    with pytest.raises(ValueError):
        rotation_type("101")


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
    assert hex_or_none_type(test_input) == expected


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
    assert pagetext_type(test_input) == expected


_base_parsed_args = {
    "pdffile": None,
    "output": None,
    "prefix": None,
    "password": None,
    "pages": None,
    "scale": 2.0,
    "rotation": 0,
    "background_colour": 0xFFFFFFFF,
    "no_annotations": False,
    "optimise_mode": OptimiseMode.none,
    "processes": 16,
    "version": False,
}


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (["python"], _base_parsed_args),
        (["python", "--pages=1,2"], {**_base_parsed_args, "pages": [1, 2]}),
        (["python", "--scale=3.14"], {**_base_parsed_args, "scale": 3.14}),
    ],
)
def test_parse_args(test_input, expected):
    assert vars(parse_args(test_input)) == expected
    assert True
