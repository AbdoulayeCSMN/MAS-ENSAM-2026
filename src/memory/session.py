"""Session memory: in-memory store scoped to a single scan run."""

from __future__ import annotations

from typing import Any


class SessionMemory:
    def __init__(self) -> None:
        self._store: dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        self._store[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._store.get(key, default)

    def append(self, key: str, value: Any) -> None:
        if key not in self._store:
            self._store[key] = []
        self._store[key].append(value)

    def all(self) -> dict[str, Any]:
        return dict(self._store)

    def clear(self) -> None:
        self._store.clear()
