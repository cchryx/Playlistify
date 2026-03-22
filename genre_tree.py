from __future__ import annotations
import csv
from typing import Any, Optional

class Genre_Tree:

    _genre: str
    songs: list[str]
    _subtrees: list[Genre_Tree]

    def __init__(self, genre: Optional[Any], subtrees: list[Genre_Tree]):
        self._genre = genre
        self._subtrees = subtrees

    def is_empty(self) -> bool:
        return self._genre is None

    def add_subtree(self, subtree: Genre_Tree) -> None:
        self._subtrees.append(subtree)

    def get_subtrees(self) -> list[Genre_Tree]:
        return self._subtrees


