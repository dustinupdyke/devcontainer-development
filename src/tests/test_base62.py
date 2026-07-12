"""Unit tests for the base62 codec."""

from __future__ import annotations

import pytest
from app import base62


@pytest.mark.parametrize(
    ("number", "expected"),
    [
        (0, "0"),
        (1, "1"),
        (10, "A"),
        (61, "z"),
        (62, "10"),
        (3843, "zz"),
        (3844, "100"),
    ],
)
def test_encode_known_values(number: int, expected: str) -> None:
    assert base62.encode(number) == expected


@pytest.mark.parametrize("number", [0, 1, 9, 61, 62, 125, 9999, 123_456_789])
def test_encode_decode_round_trip(number: int) -> None:
    assert base62.decode(base62.encode(number)) == number


def test_encode_negative_raises() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        base62.encode(-1)


def test_decode_empty_raises() -> None:
    with pytest.raises(ValueError, match="empty"):
        base62.decode("")


def test_decode_invalid_character_raises() -> None:
    with pytest.raises(ValueError, match="invalid base62 character"):
        base62.decode("abc-!")


def test_alphabet_is_62_unique_characters() -> None:
    assert base62.BASE == 62
    assert len(base62.ALPHABET) == 62
    assert len(set(base62.ALPHABET)) == 62
