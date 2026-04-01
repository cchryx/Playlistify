"""
CSC111 Project: Playlistify (Mood-Aware Music Recommendation Engine)

This module contains the console-based interface for the recommendation engine.
It collects user preferences via the terminal and displays results.

Copyright (c) 2026 Xing Xu Chen, Tianqi Pan, Norah Liu, Denise Ma
"""
from __future__ import annotations
import time
from typing import Any

import genre_tree
import graph_visualization
import song_graph


def run_console() -> None:
    """Run the interactive console version of Playlistify.

    Loads data, collects user preferences, filters songs, and triggers
    the 3D graph visualization.
    """
    print("Loading song graph...")
    start_time = time.perf_counter()

    # Load data structures from CSV
    tree_genre = genre_tree.load_genre_tree('data/spotify_data.csv')
    graph_song = song_graph.load_song_graph('data/spotify_data.csv')

    duration = time.perf_counter() - start_time
    print(f"Loading completed in {duration:.2f} seconds.")

    # 1. Collect Preferences via Helpers
    pref_genres = _collect_genres()

    # Bundle preferences into a dictionary to reduce parameter count (R0913 fix)
    preferences = {
        'energy': _collect_energy(),
        'viral': _collect_viral(),
        'threshold': 10
    }
    n_songs = _collect_count()

    # 2. Filter Candidate Songs
    candidates = _filter_candidates(pref_genres, tree_genre, graph_song, preferences)

    print(f"\nSongs matching your initial filters: {len(candidates)}")

    # 3. Generate Recommendations via Graph
    seed_songs = sorted(list(candidates), key=lambda x: x[0], reverse=True)[:5]
    recommendations = _get_graph_recommendations(seed_songs, graph_song)
    final_list = sorted(list(recommendations), reverse=True)[:n_songs]

    # 4. Display Results
    print("\nYour playlist:")
    for i, song in enumerate(final_list):
        print(f"{i + 1}. {song[1]} - {song[2]}")

    # 5. Launch 3D Visualization
    _launch_viz(seed_songs, graph_song, final_list)
    return None


def _collect_genres() -> list[str]:
    """Prompt user for genres and return a list of valid choices."""
    selected = []
    while True:
        genre = input("Enter a genre you want: ")
        if genre not in genre_tree.GENRE_HIERARCHY:
            print("Genre not found in genre tree, try again.")
        else:
            selected.append(genre)
            if input("Add another genre? (yes/no): ").lower() != 'yes':
                break
    return selected


def _collect_viral() -> bool:
    """Prompt user for popularity preference."""
    while True:
        ans = input("Do you like viral songs? (yes/no): ").lower()
        if ans in {'yes', 'no'}:
            return ans == 'yes'
        print("Invalid response, please enter yes or no.")

    return False


def _collect_energy() -> float:
    """Prompt user for energy level (1-10) and return normalized float."""
    while True:
        val = input("Enter your energy level from 1 to 10: ")
        try:
            energy_val = float(val)
            if 1 <= energy_val <= 10:
                return energy_val / 10
            print("Invalid energy level, please enter a number between 1 and 10.")
        except ValueError:
            print("Invalid input, please enter a number.")

    return 0.0


def _collect_count() -> int:
    """Prompt user for playlist size."""
    while True:
        val = input("How many songs would you like in your playlist? ")
        if val.isdigit() and int(val) > 0:
            return int(val)
        print("Please enter a whole number greater than 0.")

    return 0


def _filter_candidates(genres: list[str], tree: Any, graph: Any,
                       prefs: dict[str, Any]) -> set:
    """Return a set of (popularity, song) tuples based on user filters.

    Uses a dictionary for preferences to keep parameter count low.
    """
    candidates = set()
    for g in genres:
        if tree.find(g) is not None:
            _add_genre_candidates(g, graph, prefs, candidates)

    return candidates


def _add_genre_candidates(genre: str, graph: Any,
                          prefs: dict[str, Any], candidates: set) -> None:
    """Check all songs in the graph and add those matching the genre and filters."""
    for song in graph.get_all_songs():
        if song.genre == genre:
            meets_e = song.features.energy >= prefs['energy']

            # Popularity check
            if prefs['viral']:
                meets_p = song.popularity >= prefs['threshold']
            else:
                meets_p = True

            if meets_e and meets_p:
                candidates.add((song.popularity, song))

    return None


def _get_graph_recommendations(seeds: list, graph: Any) -> set:
    """Find similar songs using graph neighbors of the seed songs."""
    recs = set()
    for _, song in seeds:
        for neighbor in graph.get_neighbours(song):
            weight = graph.get_weight(song, neighbor)
            recs.add((weight, neighbor.track_name, neighbor.genre))
    return recs


def _launch_viz(seeds: list, graph: Any, final_list: list) -> None:
    """Map song names back to objects and launch the 3D Plotly visualization."""
    seed_objs = [s for _, s in seeds]
    song_map = {s.track_name: s for s in graph.get_all_songs()}
    final_objs = {song_map[name] for _, name, _ in final_list if name in song_map}

    graph_visualization.run_visualization(seed_objs, graph, final_objs)
    return None


if __name__ == '__main__':
    import python_ta
    python_ta.check_all(config={
        'max-line-length': 120,
        'extra-imports': ['time', 'genre_tree', 'song_graph', 'graph_visualization'],
        'allowed-io': ['run_console', '_collect_genres', '_collect_viral',
                       '_collect_energy', '_collect_count'],
    })
    run_console()
