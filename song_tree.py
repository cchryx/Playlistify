"""
CSC111 Project: Playlistify (Mood-Aware Music Recommendation Engine)

This module contains the _Vertex and Song classes to represent music data in a graph,
along with the Graph dataclass for managing connections between songs.

Copyright (c) 2026 Xing Xu Chen, Tianqi Pan, Norah Liu, Denise Ma
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Song:
    """A dataclass representing a song and its audio features.

    Using a frozen dataclass allows Song objects to be hashable,
    meaning they can be used as dictionary keys or in sets.
    """
    track_id: str
    artist_name: str
    track_name: str
    genre: str
    popularity: int
    year: int
    danceability: float
    energy: float
    key: int
    loudness: float
    mode: int
    speechiness: float
    acousticness: float
    instrumentalness: float
    liveness: float
    valence: float
    tempo: float
    duration_ms: int
    time_signature: int


class _Vertex:
    """A vertex in the song graph.

    Instance Attributes:
        - item: The data stored in this vertex, representing a song.
        - neighbours: The vertices that are adjacent to this vertex.

    Representation Invariants:
        - self not in self.neighbours
        - all(self in u.neighbours for u in self.neighbours)

    """
    item: Song
    neighbours: set[_Vertex]

    def __init__(self, item: Song) -> None:
        """Initialize a new vertex with the given Song item."""
        self.item = item
        self.neighbours = set()

    def degree(self) -> int:
        """Return the degree of this vertex."""
        return len(self.neighbours)


@dataclass
class Graph:
    """A graph representing a music network where nodes are songs.

    Instance Attributes:
        - _vertices: A collection of the vertices contained in this graph.
                     Maps song track_id to the _Vertex object.
    """
    _vertices: dict[str, _Vertex] = field(default_factory=dict)

    def add_vertex(self, song: Song) -> None:
        """Add a vertex representing the given song to this graph.

        Do nothing if a song with the same track_id already exists.
        """
        if song.track_id not in self._vertices:
            self._vertices[song.track_id] = _Vertex(song)

    def add_edge(self, track_id1: str, track_id2: str) -> None:
        """Add an edge between the two songs with the given track_ids.

        Raise a ValueError if either track_id does not exist in the graph.
        """
        if track_id1 in self._vertices and track_id2 in self._vertices:
            v1 = self._vertices[track_id1]
            v2 = self._vertices[track_id2]

            v1.neighbours.add(v2)
            v2.neighbours.add(v1)
        else:
            raise ValueError("One or both track IDs not found in graph.")

    def get_song(self, track_id: str) -> Song | None:
        """Return the Song object associated with the track_id, or None if not found."""
        if track_id in self._vertices:
            return self._vertices[track_id].item
        return None

    def get_all_songs(self) -> list[Song]:
        """Return a list of all Song objects in the graph."""
        return [v.item for v in self._vertices.values()]
