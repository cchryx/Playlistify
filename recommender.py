"""
CSC111 Project: Playlistify (Mood-Aware Music Recommendation Engine)

This module contains the recommendation logic shared by the GUI and the console
version. It uses the GenreTree to find songs in the chosen genres (and their
sub-genres), then uses the SongGraph to find similar songs for the playlist.

Copyright (c) 2026 Xing Xu Chen, Tianqi Pan, Norah Liu, Denise Ma
"""
from __future__ import annotations

import os
from typing import Any

from genre_tree import GenreTree
from song_graph import Song, SongGraph

# Path to the song dataset, relative to this file, so the app works from any folder.
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'spotify_data.csv')

# A song counts as "popular" if its Spotify popularity is at least this value (out of 100).
# About the top 15% of songs in the dataset meet this threshold.
VIRAL_THRESHOLD = 40

# A song matches the chosen energy level if its energy is within this distance of it.
ENERGY_TOLERANCE = 0.15

# The number of most popular matching songs used as starting points in the graph.
NUM_SEEDS = 5


def find_candidates(genres: list[str], tree: GenreTree, graph: SongGraph,
                    energy: float, viral: bool) -> list[Song]:
    """Return the songs that match the user's preferences, most popular first.

    A song matches if:
        - its genre is one of the given genres, or a sub-genre of one of them,
        - it is popular (popularity >= VIRAL_THRESHOLD), if viral is True, and
        - its energy is within ENERGY_TOLERANCE of the given energy.

    If no song meets the energy rule, the NUM_SEEDS songs with the closest energy
    are used instead, so the user still gets a playlist.

    Preconditions:
        - 0.0 <= energy <= 1.0
    """
    pool = []
    seen = set()
    for genre in genres:
        node = tree.find(genre)
        if node is None:
            continue
        for track_id in node.songs:
            song = graph.get_song_by_id(track_id)
            if song is not None and song not in seen and (not viral or song.popularity >= VIRAL_THRESHOLD):
                seen.add(song)
                pool.append(song)

    matches = [s for s in pool if abs(s.features.energy - energy) <= ENERGY_TOLERANCE]
    if not matches:
        matches = sorted(pool, key=lambda s: abs(s.features.energy - energy))[:NUM_SEEDS]

    return sorted(matches, key=lambda s: (s.popularity, s.track_id), reverse=True)


def genre_track_ids(genres: list[str], tree: GenreTree) -> set[str]:
    """Return the track_ids of all songs in the given genres and their sub-genres."""
    track_ids = set()
    for genre in genres:
        node = tree.find(genre)
        if node is not None:
            track_ids.update(node.songs)
    return track_ids


def recommend(seeds: list[Song], candidates: list[Song], graph: SongGraph,
              n: int, prefs: dict[str, Any]) -> list[tuple[float, Song]]:
    """Return a playlist of up to n (similarity, song) pairs.

    The playlist is made of graph neighbours of the seed songs. Each neighbour is
    scored by its highest edge weight to any seed. Each song appears at most once.
    Neighbours in the user's genres (prefs['genre_ids']) come first, then the rest,
    each group sorted from most to least similar.
    If prefs['viral'] is True, neighbours below VIRAL_THRESHOLD are skipped.

    If there are fewer than n neighbours, the playlist is filled with the remaining
    candidate songs (in popularity order), scored by their similarity to the closest seed.

    prefs must have the keys 'viral' (a bool) and 'genre_ids' (a set of track_ids).

    Preconditions:
        - n > 0
        - all(seed in candidates for seed in seeds)
    """
    scores = _score_neighbours(seeds, graph, bool(prefs['viral']))
    genre_ids = prefs['genre_ids']

    ranked = sorted(scores.items(),
                    key=lambda item: (item[0].track_id in genre_ids, item[1], item[0].popularity),
                    reverse=True)
    playlist = [(item[1], item[0]) for item in ranked[:n]]

    used = {item[1] for item in playlist}
    for song in candidates:
        if len(playlist) >= n:
            break
        if song not in used:
            best = max(graph.get_cosine_similarity(song, s) for s in seeds)
            playlist.append((best, song))
            used.add(song)

    return playlist


def _score_neighbours(seeds: list[Song], graph: SongGraph, viral: bool) -> dict[Song, float]:
    """Return a mapping from each graph neighbour of the seeds to its highest edge weight to a seed.

    Seeds themselves are not included. If viral is True, neighbours below
    VIRAL_THRESHOLD are skipped.
    """
    seed_set = set(seeds)
    scores: dict[Song, float] = {}
    for seed in seeds:
        for neighbour in graph.get_neighbours(seed):
            if neighbour in seed_set or (viral and neighbour.popularity < VIRAL_THRESHOLD):
                continue
            weight = graph.get_weight(seed, neighbour)
            if weight > scores.get(neighbour, 0.0):
                scores[neighbour] = weight
    return scores


def make_playlist(genres: list[str], tree: GenreTree, graph: SongGraph,
                  prefs: dict[str, float | bool | int]) -> tuple[list[Song], list[tuple[float, Song]]]:
    """Return the seed songs and the playlist for the given genres and preferences.

    prefs must have these keys:
        - 'energy': the target energy level, in [0.0, 1.0]
        - 'viral': whether the user only wants popular songs
        - 'n': the number of songs in the playlist (> 0)

    The seeds are the NUM_SEEDS most popular matching songs. The playlist is empty
    if no song matches the user's genres and popularity preference.
    """
    candidates = find_candidates(genres, tree, graph, float(prefs['energy']), bool(prefs['viral']))
    seeds = candidates[:NUM_SEEDS]
    if not seeds:
        return [], []
    playlist = recommend(seeds, candidates, graph, int(prefs['n']),
                         {'viral': prefs['viral'], 'genre_ids': genre_track_ids(genres, tree)})
    return seeds, playlist


if __name__ == '__main__':
    import python_ta
    python_ta.check_all(config={
        'max-line-length': 120,
        'extra-imports': ['os', 'typing', 'genre_tree', 'song_graph'],
        'allowed-io': [],
    })
