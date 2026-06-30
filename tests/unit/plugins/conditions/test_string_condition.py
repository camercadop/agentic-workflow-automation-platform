import pytest
from src.plugins.conditions.string_condition import (
    StringContains,
    StringStartsWith,
    StringEndsWith,
    StringRegexMatch,
)


@pytest.fixture
def data():
    return {"field": "HelloWorld"}


def test_contains(data):
    cond = StringContains(key="field", value="loWo")
    assert cond.evaluate(data)


def test_startswith(data):
    cond = StringStartsWith(key="field", value="Hello")
    assert cond.evaluate(data)


def test_endswith(data):
    cond = StringEndsWith(key="field", value="World")
    assert cond.evaluate(data)


def test_regex_match(data):
    cond = StringRegexMatch(key="field", value=r"Hello.*d")
    assert cond.evaluate(data)


def test_non_string(data):
    cond = StringContains(key="missing", value="test")
    assert not cond.evaluate(data)


# Edge case tests


def test_invalid_regex():
    """Test that invalid regex patterns return False instead of crashing."""
    cond = StringRegexMatch(key="field", value="[invalid")
    data = {"field": "HelloWorld"}
    assert not cond.evaluate(data)


def test_empty_string():
    """Test empty string values."""
    cond = StringContains(key="field", value="")
    data = {"field": "HelloWorld"}
    assert cond.evaluate(data)  # Empty string is contained in any string

    cond = StringStartsWith(key="field", value="")
    assert cond.evaluate(data)  # Empty string is prefix of any string

    cond = StringEndsWith(key="field", value="")
    assert cond.evaluate(data)  # Empty string is suffix of any string

    cond = StringRegexMatch(key="field", value="")
    assert cond.evaluate(data)  # Empty regex matches any string


def test_case_sensitivity():
    """Test case sensitivity of string operations."""
    data = {"field": "Hello"}
    cond = StringContains(key="field", value="hello")
    assert not cond.evaluate(data)  # Case-sensitive, should be False

    cond = StringStartsWith(key="field", value="HELLO")
    assert not cond.evaluate(data)

    cond = StringEndsWith(key="field", value="HELLO")
    assert not cond.evaluate(data)

    cond = StringRegexMatch(key="field", value=r"HELLO")
    assert not cond.evaluate(data)  # Regex is case-sensitive by default

    # Case-insensitive regex
    cond = StringRegexMatch(key="field", value=r"(?i)hello")
    assert cond.evaluate(data)


def test_empty_actual_string():
    """Test when actual value is empty string."""
    data = {"field": ""}
    cond = StringContains(key="field", value="")
    assert cond.evaluate(data)

    cond = StringStartsWith(key="field", value="")
    assert cond.evaluate(data)

    cond = StringEndsWith(key="field", value="")
    assert cond.evaluate(data)

    cond = StringRegexMatch(key="field", value="")
    assert cond.evaluate(data)

    cond = StringRegexMatch(key="field", value="a")
    assert not cond.evaluate(data)


def test_none_actual_value():
    """Test when actual value is None."""
    data = {"field": None}
    cond = StringContains(key="field", value="test")
    assert not cond.evaluate(data)

    cond = StringStartsWith(key="field", value="test")
    assert not cond.evaluate(data)

    cond = StringEndsWith(key="field", value="test")
    assert not cond.evaluate(data)

    cond = StringRegexMatch(key="field", value="test")
    assert not cond.evaluate(data)
