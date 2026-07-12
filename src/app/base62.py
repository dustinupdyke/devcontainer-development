"""Base62 encoding and decoding for compact short codes.

Sequential integer IDs are encoded to short, URL-safe strings using the
alphabet ``[0-9A-Za-z]``. ``decode`` is the exact inverse of ``encode`` for
every non-negative integer.
"""

from __future__ import annotations

ALPHABET: str = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
BASE: int = len(ALPHABET)
_INDEX: dict[str, int] = {char: index for index, char in enumerate(ALPHABET)}


def encode(number: int) -> str:
    """Encode a non-negative integer as a base62 string.

    Args:
        number: The integer to encode. Must be ``>= 0``.

    Returns:
        The base62 representation. ``0`` encodes to ``"0"``.

    Raises:
        ValueError: If ``number`` is negative.
    """
    if number < 0:
        raise ValueError("number must be non-negative")
    if number == 0:
        return ALPHABET[0]
    digits: list[str] = []
    while number > 0:
        number, remainder = divmod(number, BASE)
        digits.append(ALPHABET[remainder])
    digits.reverse()
    return "".join(digits)


def decode(code: str) -> int:
    """Decode a base62 string back into its integer value.

    Args:
        code: A non-empty string of base62 characters.

    Returns:
        The decoded integer.

    Raises:
        ValueError: If ``code`` is empty or contains a non-base62 character.
    """
    if not code:
        raise ValueError("code must not be empty")
    number = 0
    for char in code:
        value = _INDEX.get(char)
        if value is None:
            raise ValueError(f"invalid base62 character: {char!r}")
        number = number * BASE + value
    return number
