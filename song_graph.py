"""
CSC111 Project: Playlistify (Mood-Aware Music Recommendation Engine)

This module defines the data classes and graph structure used to represent songs
and their audio similarities. It includes AudioMood, AudioTechnical, Song, and
SongGraph, as well as functions to load and build the graph from a CSV dataset.

Copyright (c) 2026 Xing Xu Chen, Tianqi Pan, Norah Liu, Denise Ma
"""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass

import numpy


@dataclass(frozen=True)
class AudioMood:
    """Quantitative mood features of a track.

    Instance Attributes:
        - danceability: How suitable the track is for dancing, from 0.0 (least) to 1.0 (most).
        - energy: Perceptual measure of intensity and activity, from 0.0 (lowest) to 1.0 (highest).
        - valence: Musical positiveness conveyed, from 0.0 (negative/sad) to 1.0 (positive/happy).
        - speechiness: Presence of spoken words in the track, from 0.0 (none) to 1.0 (speech-only).
        - acousticness: Confidence that the track is acoustic, from 0.0 (not acoustic) to 1.0 (fully acoustic).
        - instrumentalness: Likelihood the track contains no vocals, from 0.0 (has vocals) to 1.0 (fully instrumental).
        - liveness: Probability the track was recorded with a live audience, from 0.0 (studio) to 1.0 (live).

    Representation Invariants:
        - 0.0 <= self.danceability <= 1.0
        - 0.0 <= self.energy <= 1.0
        - 0.0 <= self.valence <= 1.0
        - 0.0 <= self.speechiness <= 1.0
        - 0.0 <= self.acousticness <= 1.0
        - 0.0 <= self.instrumentalness <= 1.0
        - 0.0 <= self.liveness <= 1.0
    """
    danceability: float
    energy: float
    valence: float
    speechiness: float
    acousticness: float
    instrumentalness: float
    liveness: float


@dataclass(frozen=True)
class AudioTechnical:
    """Technical properties of a track's recording.

    Instance Attributes:
        - key: The musical key the track is in, as a pitch class integer (0 = C, 1 = C#/Db, ... 11 = B).
            -1 if undetected.
        - loudness: Overall loudness of the track in decibels (dB), typically between -60.0 and 0.0.
        - mode: Modality of the track; 1 for major, 0 for minor.
        - tempo: Estimated tempo of the track in beats per minute (BPM).
        - duration_ms: Duration of the track in milliseconds.
        - time_signature: Estimated number of beats per bar (e.g. 3 for 3/4, 4 for 4/4).

    Representation Invariants:
        - -1 <= self.key <= 11
        - self.mode in {0, 1}
        - self.tempo > 0.0
        - self.duration_ms > 0
        - self.time_signature > 0
    """
    key: int
    loudness: float
    mode: int
    tempo: float
    duration_ms: int
    time_signature: int


@dataclass(frozen=True)
class Song:
    """A dataclass representing a song and its audio features.

    Instance Attributes:
        - artist_name: The name of the artist or band.
        - track_name: The title of the song.
        - track_id: A unique identifier for the track.
        - popularity: The popularity score (0-100).
        - genre: The musical genre classification.
        - features: An AudioMood object containing qualitative features.
        - technical: An AudioTechnical object containing recording properties.

    Representation Invariants:
        - 0 <= popularity <= 100
        - self.features is not None
        - self.technical is not None
    """
    artist_name: str
    track_name: str
    track_id: str
    popularity: int
    genre: str
    features: AudioMood
    technical: AudioTechnical


class _SongVertex:
    """A vertex in the song graph.

    Instance Attributes:
        - item: The data stored in this vertex, representing a song.
        - neighbours: The vertices adjacent to this vertex, mapping each neighbour to its edge weight.

    Representation Invariants:
        - self not in self.neighbours
        - all(self in v.neighbours for v in self.neighbours)
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
    """A graph representing a music network where nodes are songs."""
    # Private Instance Attributes:
    #     - _vertices: A collection of the vertices contained in this graph.
    #             Maps song track_id to the _Vertex object.
    _vertices: dict[Song, _SongVertex]

    def __init__(self) -> None:
        """Initialize an empty graph (no vertices or edges)."""
        self._vertices = {}

    def add_vertex(self, song: Song) -> None:
        """Add a vertex representing the given song to this graph.

        If a vertex for this song already exists in the graph, do nothing.
        """
        if song not in self._vertices:
            self._vertices[song] = _SongVertex(song)

    def add_edge(self, song1: Song, song2: Song, weight: float) -> None:
        """Add an undirected edge between song1 and song2 with the given weight.

        Raise a ValueError if either song1 or song2 is not already a vertex
        in this graph.

        Preconditions:
            - 0.0 <= weight <= 1.0
        """
        if song1 in self._vertices and song2 in self._vertices:
            v1 = self._vertices[song1]
            v2 = self._vertices[song2]

            v1.neighbours[v2] = weight
            v2.neighbours[v1] = weight
        else:
            raise ValueError("One or both songs do not exist in the graph.")

    def get_song(self, song: Song) -> Song | None:
        """Return the Song object from the graph that matches the given song.

        Return None if the song is not found in the graph's vertices.
        """
        if song in self._vertices:
            return self._vertices[song].item
        return None

    def get_neighbours(self, song: Song) -> set[Song]:
        """Return a set of the neighbouring Song objects for the given song.

        Note that the Song items are returned, not the _SongVertex objects themselves.
        Raise a ValueError if song does not appear as a vertex in this graph.
        """
        if song in self._vertices:
            v = self._vertices[song]
            return {neighbour.item for neighbour in v.neighbours}
        else:
            raise ValueError

    def get_all_songs(self) -> list[Song]:
        """Return a list of all Song objects stored in this graph.

        The order of songs in the returned list is not guaranteed.
        """
        return list(self._vertices.keys())

    def get_weight(self, song1: Song, song2: Song) -> float:
        """Return the weight of the edge between the two given songs.
        Return 0.0 if the two songs are not adjacent to each other in the graph.

        Preconditions:
            - song1 in self._vertices
            - song2 in self._vertices
        """
        v1 = self._vertices[song1]
        v2 = self._vertices[song2]

        return v1.neighbours.get(v2, 0.0)

    def get_feature_matrix(self) -> numpy.ndarray:
        """Return a normalized audio feature matrix for all songs in the graph.

        Returns a 2D NumPy array of shape (n_songs, 8), where each row is a
        song's feature vector. The columns correspond to the following features
        (in order): danceability, energy, valence, tempo, acousticness,
        instrumentalness, loudness, and speechiness.

        Features are normalized to [0, 1] using min-max scaling so that
        features with large ranges (e.g. tempo, loudness) do not dominate
        the cosine similarity calculation.
        """
        matrix = numpy.array([
            [v.item.features.danceability, v.item.features.energy, v.item.features.valence,
             v.item.technical.tempo, v.item.features.acousticness, v.item.features.instrumentalness,
             v.item.technical.loudness, v.item.features.speechiness]
            for v in self._vertices.values()
        ])

        # Min-max normalize each feature column to [0, 1]
        col_min = matrix.min(axis=0)
        col_max = matrix.max(axis=0)
        col_range = col_max - col_min
        col_range[col_range == 0] = 1  # Avoid division by zero for constant columns
        matrix = (matrix - col_min) / col_range

        return matrix

    # This get_cosine_similarity funtion is too slow for computing matrix multiplication.
    # We are using numpy functions intead.
    def get_cosine_similarity(self, song1: Song, song2: Song) -> float:
        """Return the cosine similarity between two songs, as a float in [0.0, 1.0].

        Raises a ValueError if song1 or song2 do not appear as vertices in this graph.

        The following audio features are used to construct each song's feature vector:
        danceability, energy, valence, tempo, acousticness, instrumentalness,
        loudness, and speechiness.
        """
        if song1 in self._vertices and song2 in self._vertices:
            song1_item = self._vertices[song1].item  # was song2
            song2_item = self._vertices[song2].item
            vector1 = [song1_item.features.danceability,
                       song1_item.features.energy,
                       song1_item.features.valence,
                       song1_item.technical.tempo,
                       song1_item.features.acousticness,
                       song1_item.features.instrumentalness,
                       song1_item.technical.loudness,
                       song1_item.features.speechiness]
            vector2 = [song2_item.features.danceability,
                       song2_item.features.energy,
                       song2_item.features.valence,
                       song2_item.technical.tempo,
                       song2_item.features.acousticness,
                       song2_item.features.instrumentalness,
                       song2_item.technical.loudness,
                       song2_item.features.speechiness]

            dot_product = sum(vector1[i] * vector2[i] for i in range(len(vector1)))

            norm_1 = math.sqrt(sum(v ** 2 for v in vector1))
            norm_2 = math.sqrt(sum(v ** 2 for v in vector2))

            if norm_1 == 0 or norm_2 == 0:
                return 0.0
            else:
                return round(dot_product / (norm_1 * norm_2), 3)
        else:
            raise ValueError


def _load_vertices(song_graph: SongGraph, rows: list) -> None:
    """Add a vertex to song_graph for each song row in rows."""
    for song in rows:
        mood = AudioMood(
            danceability=float(song[7]),
            energy=float(song[8]),
            speechiness=float(song[12]),
            acousticness=float(song[13]),
            instrumentalness=float(song[14]),
            liveness=float(song[15]),
            valence=float(song[16]),
        )
        technical = AudioTechnical(
            key=int(song[9]),
            loudness=float(song[10]),
            mode=int(song[11]),
            tempo=float(song[17]),
            duration_ms=int(song[18]),
            time_signature=int(song[19]),
        )
        song_object = Song(
            artist_name=song[1],
            track_name=song[2],
            track_id=song[3],
            popularity=int(song[4]),
            genre=song[6],
            features=mood,
            technical=technical,
        )
        song_graph.add_vertex(song_object)


def _load_edges(song_graph: SongGraph, similarity_threshold: float) -> None:
    """Add edges between songs in song_graph whose cosine similarity meets the threshold."""
    all_songs = song_graph.get_all_songs()
    feature_matrix = song_graph.get_feature_matrix()

    # Compute the L2 norm of each song's feature vector (one scalar per row).
    # keepdims=True preserves the (n_songs, 1) shape so broadcasting works correctly
    # when dividing the matrix in the next step.
    norms = numpy.linalg.norm(feature_matrix, axis=1, keepdims=True)

    # Divide each row by its norm to produce unit vectors. After this step every
    # song's feature vector has length 1, so the dot product between any two rows
    # equals their cosine similarity directly.
    normalized = feature_matrix / norms

    # Multiply the normalized matrix by its own transpose to compute all pairwise
    # cosine similarities at once. The result is a symmetric (n_songs, n_songs)
    # matrix where entry [i][j] is the cosine similarity between song i and song j.
    # This is significantly faster than computing each pair individually in a loop.
    sim_matrix = normalized @ normalized.T  # Shape: (n_songs, n_songs)

    for i in range(len(all_songs)):
        for j in range(i + 1, len(all_songs)):
            similarity = round(float(sim_matrix[i][j]), 3)
            if similarity >= similarity_threshold:
                song_graph.add_edge(all_songs[i], all_songs[j], similarity)


def load_song_graph(song_file: str, similarity_threshold: float = 0.98) -> SongGraph:
    """Return a SongGraph loaded from song_file, with edges between songs whose
    cosine similarity is at or above similarity_threshold.

    Preconditions:
        - song_file is the path to a CSV file where the first row is headers and
          each subsequent row contains song data in the order defined by the Song dataclass.
        - 0.0 <= similarity_threshold <= 1.0
    """
    song_graph = SongGraph()

    with open(song_file, encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)
        rows = list(reader)
        _load_vertices(song_graph, rows)
        _load_edges(song_graph, similarity_threshold)

    return song_graph


if __name__ == "__main__":
    # When you are ready to check your work with python_ta, uncomment the following lines.
    # (Delete the "#" and space before each line.)
    # IMPORTANT: keep this code indented inside the "if __name__ == '__main__'" block
    import python_ta
    python_ta.check_all(config={
        'max-line-length': 120,
        'extra-imports': ['numpy', 'math', 'csv'],
        'allowed-io': ['load_song_graph'],
        'disable': []
    })
