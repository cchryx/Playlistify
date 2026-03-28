"""
CSC111 Project: Playlistify (Mood-Aware Music Recommendation Engine)

This module contains the _Vertex and Song classes to represent music data in a graph,
along with the Graph dataclass for managing connections between songs.

Copyright (c) 2026 Xing Xu Chen, Tianqi Pan, Norah Liu, Denise Ma
"""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass, field
from timeit import timeit

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import joblib
import os

# TODO: check all docstrings in the file

@dataclass
class Song:
    """A dataclass representing a song and its audio features.

    Using a frozen dataclass allows Song objects to be hashable,
    meaning they can be used as dictionary keys or in sets.

    Instance Attributes:
        - TODO:
    Representation Invariants:
        - TODO:

    """
    artist_name: str
    track_name: str
    track_id: str
    popularity: int
    year: int
    genre: str
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


class _SongVertex:
    """A vertex in the song graph.

    Instance Attributes:
        - item: The data stored in this vertex, representing a song.
        - neighbours: The vertices that are adjacent to this vertex.

    Representation Invariants:
        - self not in self.neighbours
        - all(self in u.neighbours for u in self.neighbours)

    """
    item: Song
    neighbours: dict[_SongVertex, float]

    def __init__(self, item: Song) -> None:
        """Initialize a new vertex with the given Song item."""
        self.item = item
        self.neighbours = {}

    def degree(self) -> int:
        """Return the degree of this vertex."""
        return len(self.neighbours)


@dataclass
class SongGraph:
    """A graph representing a music network where nodes are songs.

    Instance Attributes:
        - _vertices: A collection of the vertices contained in this graph.
                     Maps song track_id to the _Vertex object.
    """
    _vertices: dict[str, _SongVertex]

    def add_vertex(self, song: Song) -> None:
        """Add a vertex representing the given song to this graph.

        Do nothing if a song with the same track_id already exists.
        """
        if song.track_id not in self._vertices:
            self._vertices[song.track_id] = _SongVertex(song)

    def add_edge(self, track_id1: str, track_id2: str, weight: float = 1.0) -> None:
        """Add an edge between the two songs with the given track_ids, with the given weight.
        Default weight is 1

        Raise a ValueError if either track_id does not exist in the graph.
        """
        if track_id1 in self._vertices and track_id2 in self._vertices:
            if weight >= 0.75:  # the value can be modified later
                v1 = self._vertices[track_id1]
                v2 = self._vertices[track_id2]

                v1.neighbours[v2] = weight
                v2.neighbours[v1] = weight
        else:
            raise ValueError("One or both track IDs not found in graph.")

    def get_song(self, track_id: str) -> Song | None:
        """Return the Song object associated with the track_id, or None if not found."""
        if track_id in self._vertices:
            return self._vertices[track_id].item
        return None

    def get_song_vertex(self, track_id: str) -> _SongVertex | None:
        """Return the Song object associated with the track_id, or None if not found."""
        if track_id in self._vertices:
            return self._vertices[track_id]
        return None

    def get_all_songs(self) -> list[Song]:
        """Return a list of all Song objects in the graph."""
        return [v.item for v in self._vertices.values()]

    def get_all_song_ids(self) -> list[str]:
        """Return a list of all Song IDs in the graph."""
        return list(self._vertices.keys())

    def get_feature_matrix(self) -> tuple[list[str], np.ndarray]:
        """Return all track IDs and their audio feature vectors as a NumPy matrix.

        Each row in the matrix corresponds to a song, with columns representing:
        danceability, energy, valence, tempo, acousticness, instrumentalness,
        loudness, and speechiness — matching the features used in get_cosine_similarity.
        """
        ids = list(self._vertices.keys())
        matrix = np.array([
            [v.item.danceability, v.item.energy, v.item.valence, v.item.tempo,
             v.item.acousticness, v.item.instrumentalness, v.item.loudness, v.item.speechiness]
            for v in self._vertices.values()
        ])
        return ids, matrix

    def get_cosine_similarity(self, track_id1: str, track_id2: str) -> float:
        """
        Return the cosine similarity value of two songs in the graph
        Raise a ValueError if item1 or item2 do not appear as vertices in this graph.
        When evaluating the similarity of songs, the following features are taken into consideration:
        - danceability
        - energy
        - valence
        - tempo
        - acousticness
        - instrumentalness
        - loudnness
        - speechiness
        """
        if track_id1 not in self._vertices or track_id2 not in self._vertices:
            raise ValueError
        else:
            song_1 = self._vertices[track_id1].item
            song_2 = self._vertices[track_id2].item

            vector_1 = [song_1.danceability,
                        song_1.energy,
                        song_1.valence,
                        song_1.tempo,
                        song_1.acousticness,
                        song_1.instrumentalness,
                        song_1.loudness,
                        song_1.speechiness]
            vector_2 = [song_2.danceability,
                        song_2.energy,
                        song_2.valence,
                        song_2.tempo,
                        song_2.acousticness,
                        song_2.instrumentalness,
                        song_2.loudness,
                        song_2.speechiness]

            dot_product = sum(vector_1[i] * vector_2[i] for i in range(len(vector_1)))

            norm_1 = math.sqrt(sum(v ** 2 for v in vector_1))
            norm_2 = math.sqrt(sum(v ** 2 for v in vector_2))

            if norm_1 == 0 or norm_2 == 0:
                return 0.0
            else:
                return round(dot_product / (norm_1 * norm_2), 3)

    def get_weight(self, track_id1: str, track_id2: str) -> float:
        """
        Return the weight of edge between the given two songs
        Return 0.0 if the two songs are not adjcent to each other in the graph

        Preconditions:
            - TODO:
        """
        ...
        song_1_vertex = self._vertices[track_id1]
        song_2_vertex = self._vertices[track_id2]
        return song_1_vertex.neighbours.get(song_2_vertex, 0.0)


def load_song_data(song_file: str) -> SongGraph:
    """
    Return a SongGraph corresponding to the given data set of songs

    Preconditions:
        - song_file is the path to a CSV file corresponding the following format:
          the first row is headers, starting from the second row are song data. Headers and each column of data
          are in the EXACT SAME order as the instance attributes in Song class, and has the format written in Song
          class's docstring.

    """

    with open(song_file, encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)
        songs = list(reader)

    song_graph = SongGraph(_vertices={})

    for song in songs:
        song_object = Song(song[1],
                           song[2],
                           song[3],
                           int(song[4]),
                           int(song[5]),
                           song[6],
                           float(song[7]),
                           float(song[8]),
                           int(song[9]),
                           float(song[10]),
                           int(song[11]),
                           float(song[12]),
                           float(song[13]),
                           float(song[14]),
                           float(song[15]),
                           float(song[16]),
                           float(song[17]),
                           int(song[18]),
                           int(song[19]))

        song_graph.add_vertex(song_object)

    # Minimum cosine similarity required to create an edge between two songs
    similarity_threshold = 0.9

    # Compute all pairwise cosine similarities at once using NumPy.
    # This is significantly faster than the pure Python O(n^2) loop.
    all_ids, feature_matrix = song_graph.get_feature_matrix()
    sim_matrix = cosine_similarity(feature_matrix)  # shape: (n_songs, n_songs)

    for i in range(len(all_ids)):
        for j in range(i + 1, len(all_ids)):  # j starts at i+1 to avoid duplicates and self-comparisons
            similarity = round(sim_matrix[i][j], 3)
            if similarity >= similarity_threshold:
                song_graph.add_edge(all_ids[i], all_ids[j], similarity)

    return song_graph


def get_song_graph(csv_path: str, cache_path: str = 'data/song_graph.pkl') -> SongGraph:
    """Load SongGraph from cache if it exists, otherwise build it from CSV and cache it."""
    if os.path.exists(cache_path):
        print("Loading graph from cache...")
        return joblib.load(cache_path)
    else:
        print("Building graph from CSV (this may take a while)...")
        graph = load_song_data(csv_path)
        joblib.dump(graph, cache_path)
        return graph


if __name__ == '__main__':
    # song_graph = load_song_data('data/spotify_data.csv')
    print(timeit(lambda: load_song_data('data/spotify_data.csv'), number=1))
    # print(len(song_graph.get_all_song_ids()))

# from pathlib import Path
# code for testing load_song_data
# ROOT = Path(__file__).resolve().parent
# csv_path = ROOT / "data" / "song_file.csv"
# my_graph = load_song_data(str(csv_path))

"""
PS. 
Tried to use the visualization code Paul gave us on assignment 3 to visualize song_graph but failed with this error. 
I deleted the relevent code from song_graph for now 

graph = load_song_data(CSV_PATH)
from song_tree_visualization import visualize_graph
visualize_graph(graph)

Traceback (most recent call last):
  File "<input>", line 1, in <module>
  File "/Users/denisema/Documents/GitHub/Playlistify/song_tree_visualization.py", line 55, in visualize_graph
    graph_nx = graph.to_networkx(max_vertices)
  File "/Users/denisema/Documents/GitHub/Playlistify/song_graph.py", line 129, in to_networkx
    graph_nx.add_node(v.item)
    ~~~~~~~~~~~~~~~~~^^^^^^^^
  File "/Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/site-packages/networkx/classes/graph.py", line 574, in add_node
    if node_for_adding not in self._node:
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: unhashable type: 'Song'

"""
