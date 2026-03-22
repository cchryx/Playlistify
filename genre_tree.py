from __future__ import annotations
import csv
from typing import Any

class Genre_Tree:

    genre: str
    songs: list[str]
    _subtrees: list[Genre_Tree]


