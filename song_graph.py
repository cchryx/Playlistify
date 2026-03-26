"""
CSC111 Project: Playlistify (Mood-Aware Music Recommendation Engine)

This module contains the _Vertex and Song classes to represent music data in a graph,
along with the Graph dataclass for managing connections between songs.

Copyright (c) 2026 Xing Xu Chen, Tianqi Pan, Norah Liu, Denise Ma
"""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass

# TODO: check all docstrings in the file

@dataclass
class Song:
    """A dataclass representing a song and its audio features.

    Using a frozen dataclass allows Song objects to be hashable,
    meaning they can be used as dictionary keys or in sets.

    Instance Attributes:
        - artist_name: string of name of the artist
        - track_name: string of name of the song
        - track_id: unique string of ID of the song
        - popularity: value of popularity of the song (0 to 100)
        - year: year released (2000 to 2023)
        - genre: genre of the song
        - dandeability: song's suitability for dancing (0.0 to 1.0)
        - energy: the perceptual measure of intensity and activity (0.0 to 1.0)
        - key: the key that the song is in (-1 to -11)
        - loudness: overall loudness of track in decibels (-60 to 0 dB)
        - mode: modality of the track (major '1' / minor '0')
        - speechiness: presence of spojen words in the track
        - acousticness: confidence measure from 0 to 1 of whether the track is acoustic
        - instrumentalness: whether the song contains vocal (0.0 to 1.0)
        - liveness: presence of audience in recording (0.0 to 1.0)
        - valence: musicial positiveness (0.0 to 1.0)
        - tempo: tempo of the track in beats per minute (BPM)
        - duration_ms: duration of song in milliseconds
        - time_signature: estimated time signature (3 to 7)

    Representation Invariants:
        - self.popularity >= 0 and self.popularity <= 100
        - self.year >= 2000 and self.year <= 2023
        - self.dandeability >= 0.0 and self.dandeability <= 1.0
        - self.energy >= 0.0 and self.energy <= 1.0
        - self.key >= -11 and self.key <= -1
        - self.loudness >= -60 and self.loudness <= 0
        - self.mode == 0 or self.mode == 1
        - self.acousticness <= 1 and self.acousticness >= 0
        - self.instrumentalness >= 0.0 and self.instrumentalness <= 1.0
        - self.liveness >= 0.0 and self.liveness <= 1.0
        - self.valence >= 0.0 and self.valence <= 1.0
        - self.duration_ms > 0
        - self.time_signature >= 3 and self.time_signature <= 7
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
    neighbours: dict[_SongVertex, int]

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

    def add_edge(self, track_id1: str, track_id2: str, weight: int = 1) -> None:
        """Add an edge between the two songs with the given track_ids, with the given weight.
        Default weight is 1

        Raise a ValueError if either track_id does not exist in the graph.
        """
        if track_id1 in self._vertices and track_id2 in self._vertices:
            if weight >= 0.75:  # TODO:the value can be modified later
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

    def get_all_songs(self) -> list[Song]:
        """Return a list of all Song objects in the graph."""
        return [v.item for v in self._vertices.values()]

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

    with open(song_file, 'r') as file:
        reader = csv.reader(file)
        next(reader)
        songs = list(reader)

    song_graph = SongGraph()

    for song in songs:
        song_object = Song(song[0],
                           song[1],
                           song[2],
                           int(song[3]),
                           int(song[4]),
                           song[5],
                           float(song[6]),
                           float(song[7]),
                           int(song[8]),
                           float(song[9]),
                           int(song[10]),
                           float(song[11]),
                           float(song[12]),
                           float(song[13]),
                           float(song[14]),
                           float(song[15]),
                           float(song[16]),
                           int(song[17]),
                           int(song[18]))

        song_graph.add_vertex(song_object)

        # TODO: Add edge, which is the weight. Need weight/similarity calculation first

    return song_graph

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
