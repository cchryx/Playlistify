"""
CSC111 Project: Playlistify (Mood-Aware Music Recommendation Engine)

This module contains the Genre_Tree class to represent music genres in a tree structure,
where each node corresponds to a genre and its associated songs, enabling hierarchical
genre-based organization and traversal.

Copyright (c) 2026 Xing Xu Chen, Tianqi Pan, Norah Liu, Denise Ma
"""

from __future__ import annotations
import csv
from typing import Any, Optional


# Mapping of each genre to its parent category
GENRE_HIERARCHY = {
    # Electronic
    'electronic': 'root',
    'edm': 'electronic',
    'house': 'electronic',
    'deep-house': 'house',
    'chicago-house': 'house',
    'progressive-house': 'house',
    'techno': 'electronic',
    'detroit-techno': 'techno',
    'minimal-techno': 'techno',
    'trance': 'electronic',
    'dubstep': 'electronic',
    'drum-and-bass': 'electronic',
    'breakbeat': 'electronic',
    'hardstyle': 'electronic',
    'electro': 'electronic',
    'ambient': 'electronic',
    'new-age': 'ambient',
    'club': 'electronic',
    'trip-hop': 'electronic',

    # Dance
    'dance': 'root',
    'disco': 'dance',

    # Rock
    'rock': 'root',
    'alt-rock': 'rock',
    'hard-rock': 'rock',
    'punk-rock': 'rock',
    'punk': 'rock',
    'emo': 'punk',
    'psych-rock': 'rock',
    'rock-n-roll': 'rock',
    'garage': 'rock',
    'indie-pop': 'rock',
    'power-pop': 'rock',
    'goth': 'rock',
    'industrial': 'rock',
    'grindcore': 'rock',

    # Metal
    'metal': 'root',
    'heavy-metal': 'metal',
    'metalcore': 'metal',
    'black-metal': 'metal',
    'death-metal': 'metal',

    # Pop
    'pop': 'root',
    'pop-film': 'pop',
    'show-tunes': 'pop',
    'singer-songwriter': 'pop',
    'songwriter': 'singer-songwriter',
    'comedy': 'pop',
    'k-pop': 'pop',
    'cantopop': 'pop',

    # Hip-Hop / R&B
    'hip-hop': 'root',
    'dancehall': 'hip-hop',
    'afrobeat': 'hip-hop',
    'funk': 'hip-hop',
    'groove': 'funk',

    # Jazz / Soul / Blues
    'jazz': 'root',
    'soul': 'jazz',
    'blues': 'jazz',
    'gospel': 'soul',
    'dub': 'jazz',

    # Classical / Acoustic
    'classical': 'root',
    'piano': 'classical',
    'guitar': 'classical',
    'acoustic': 'classical',
    'opera': 'classical',

    # Folk / Country
    'folk': 'root',
    'country': 'folk',
    'sertanejo': 'country',
    'forro': 'folk',

    # World / Regional
    'world': 'root',
    'salsa': 'world',
    'samba': 'world',
    'tango': 'world',
    'romance': 'world',
    'spanish': 'world',
    'french': 'world',
    'german': 'world',
    'swedish': 'world',
    'indian': 'world',

    # Party / Mood
    'party': 'root',
    'chill': 'party',
    'sad': 'party',
    'sleep': 'party',
    'ska': 'party',
    'hardcore': 'party',
}


class GenreTree:
    """A tree representing a hierarchical organization of music genres.

    Each node in the tree corresponds to a genre label, and may contain
    a list of songs belonging to that genre, as well as subtrees representing
    more specific sub-genres.

    Instance Attributes:
        - _genre: The genre label for this node, or None if this tree is empty.
        - songs: The list of song track IDs associated with this genre.
        - _subtrees: The list of subtrees representing sub-genres of this genre.

    Representation Invariants:
        - self.is_empty() == (self._genre is None)
        - all(not subtree.is_empty() for subtree in self._subtrees)
    """

    _genre: str
    songs: list[str]
    _subtrees: list[GenreTree]

    def __init__(self, genre: Optional[Any], subtrees: list[GenreTree]) -> None:
        """Initialize a new Genre_Tree with the given genre label and subtrees.

        The songs list is initialized as empty. Use other methods to populate it.

        Preconditions:
            - genre is not None or subtrees == []
        """
        self._genre = genre
        self._subtrees = subtrees
        self.songs = []

    def is_empty(self) -> bool:
        """Return whether this Genre_Tree is empty.

        A GenreTree is empty if and only if its genre label is None.
        """
        return self._genre is None

    def add_subtree(self, subtree: GenreTree) -> None:
        """Add the given subtree as a sub-genre of this Genre_Tree.

        Do nothing if the given subtree is empty.
        """
        self._subtrees.append(subtree)

    def get_subtrees(self) -> list[GenreTree]:
        """Return the list of subtrees (sub-genres) of this Genre_Tree."""
        return self._subtrees

    def find(self, genre: str) -> Optional[GenreTree]:
        """Return the GenreTree node matching the given genre label, or None if not found.

        Search is performed recursively across all subtrees.
        """
        if self._genre == genre:
            return self
        for subtree in self._subtrees:
            result = subtree.find(genre)
            if result is not None:
                return result
        return None

    def add_song(self, genre: str, track_id: str) -> bool:
        """Add a track_id to the songs list of the node matching the given genre,
        and to all ancestor nodes up to the root.

        Return True if the genre was found and the song was added, False otherwise.
        """
        if self._genre == genre:
            self.songs.append(track_id)
            return True
        for subtree in self._subtrees:
            if subtree.add_song(genre, track_id):
                self.songs.append(track_id)  # propagate up to this ancestor
                return True
        return False

    def __str__(self, level: int = 0) -> str:
        """Return a string representation of this Genre_Tree, indented by level.

        Each level of depth is represented by two additional spaces of indentation.
        """
        indent = '  ' * level
        result = f"{indent}{self._genre} ({len(self.songs)} songs)\n"
        for subtree in self._subtrees:
            result += subtree.__str__(level + 1)
        return result


def build_genre_tree() -> GenreTree:
    """Build and return a Genre_Tree using the predefined GENRE_HIERARCHY mapping.

    The root node represents the entire music collection. Each genre in
    GENRE_HIERARCHY is inserted under its designated parent category.
    """
    nodes: dict[str, GenreTree] = {}
    for genre in GENRE_HIERARCHY:
        nodes[genre] = GenreTree(genre, [])

    root = GenreTree('root', [])

    for genre, parent in GENRE_HIERARCHY.items():
        if parent == 'root':
            root.add_subtree(nodes[genre])
        elif parent in nodes:
            nodes[parent].add_subtree(nodes[genre])

    return root


def create_genre_tree(data: str) -> GenreTree:
    """Build a GenreTree from the CSV file at the given filepath.

    Each song in the CSV is added to the node matching its genre label.
    Songs whose genre does not appear in the hierarchy are skipped.

    The CSV is expected to have track_id at column index 0 and genre at column index 6.
    """
    tree = build_genre_tree()

    with open(data, encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # skip header row
        for row in reader:
            track_id = row[0]
            genre = row[6]
            tree.add_song(genre, track_id)

    return tree
