"""Thread-safe in-memory storage for short links.

This is intentionally a demo store: data lives only in the process and is lost
on restart. A production implementation would swap ``LinkStore`` for a database
or cache behind the same small interface.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock

from app.base62 import encode


@dataclass
class Link:
    """A single stored short link."""

    code: str
    target_url: str
    created_at: datetime
    hits: int = 0


class LinkStore:
    """In-memory, thread-safe map of short codes to target URLs.

    Codes are produced by base62-encoding a monotonically increasing counter,
    which keeps them short and collision-free. Repeated requests for the same
    URL return the existing link instead of allocating a new code.
    """

    def __init__(self) -> None:
        self._lock = Lock()
        self._counter = 0
        self._by_code: dict[str, Link] = {}
        self._by_url: dict[str, str] = {}

    def shorten(self, target_url: str) -> Link:
        """Create (or reuse) a short link for ``target_url``."""
        with self._lock:
            existing_code = self._by_url.get(target_url)
            if existing_code is not None:
                return self._by_code[existing_code]
            self._counter += 1
            code = encode(self._counter)
            link = Link(
                code=code,
                target_url=target_url,
                created_at=datetime.now(timezone.utc),
            )
            self._by_code[code] = link
            self._by_url[target_url] = code
            return link

    def get(self, code: str) -> Link | None:
        """Return the link for ``code``, or ``None`` if it does not exist."""
        return self._by_code.get(code)

    def resolve(self, code: str) -> Link | None:
        """Look up ``code`` and atomically increment its hit counter.

        Returns ``None`` if the code is unknown.
        """
        with self._lock:
            link = self._by_code.get(code)
            if link is None:
                return None
            link.hits += 1
            return link

    def count(self) -> int:
        """Return the number of stored links."""
        return len(self._by_code)

    def clear(self) -> None:
        """Remove all links and reset the counter (used by tests)."""
        with self._lock:
            self._counter = 0
            self._by_code.clear()
            self._by_url.clear()
