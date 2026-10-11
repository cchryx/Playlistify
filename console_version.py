"""
CSC111 Project: Playlistify (Mood-Aware Music Recommendation Engine)

This module contains the console-based interface for the recommendation engine.
It collects user preferences via the terminal and displays results.

Copyright (c) 2026 Xing Xu Chen, Tianqi Pan, Norah Liu, Denise Ma
"""
from __future__ import annotations
import time

import genre_tree
import graph_visualization
import recommender
import song_graph


def run_console() -> None:
    """Run the interactive console version of Playlistify.

    Loads data, collects user preferences, builds the playlist, and triggers
    the 3D graph visualization.
    """
    print("Loading song graph...")
    start_time = time.perf_counter()

    # Load data structures from CSV
    tree_genre = genre_tree.load_genre_tree(recommender.DATA_FILE)
    graph_song = song_graph.load_song_graph(recommender.DATA_FILE)

    duration = time.perf_counter() - start_time
    print(f"Loading completed in {duration:.2f} seconds.")

    # 1. Collect preferences
    pref_genres = _collect_genres()
    preferences = {
        'energy': _collect_energy(),
        'viral': _collect_viral(),
        'n': _collect_count(),
    }

    # 2. Build the playlist from the genre tree and the song graph
    seeds, playlist = recommender.make_playlist(pref_genres, tree_genre, graph_song, preferences)

    if not playlist:
        print("\nNo songs found. Try a broader genre or say 'no' to viral songs.")
        return None

    # 3. Display results
    print("\nYour playlist:")
    for i, (weight, song) in enumerate(playlist):
        print(f"{i + 1}. {song.track_name} by {song.artist_name} ({song.genre}, {int(weight * 100)}% match)")

    # 4. Launch 3D visualization
    print("\nOpening the recommendation graph in your browser...")
    graph_visualization.run_visualization(seeds, graph_song, {item[1] for item in playlist})
    return None


def _should_add_another() -> bool:
    """Prompt the user to decide whether to add another genre.

    Returns True if 'yes', False if 'no'. Forces valid input.
    """
    while True:
        repeat = input("Add another genre? (yes/no): ").strip().lower()
        if repeat == 'yes':
            return True
        if repeat == 'no':
            return False
        print("Invalid response, please enter 'yes' or 'no'.")

    return False  # Satisfy PythonTA


def _collect_genres() -> list[str]:
    """Prompt user for genres and return a list of valid choices.

    Continues to prompt until the user explicitly says 'no' to adding more.
    """
    selected = []
    in_selection_mode = True

    while in_selection_mode:
        genre = input("Enter a genre you want: ").strip().lower()

        if genre not in genre_tree.GENRE_HIERARCHY:
            print("Genre not found in genre tree, try again.")
        else:
            selected.append(genre)
            # Flattened: Calling the helper instead of nesting another loop
            in_selection_mode = _should_add_another()

    return selected


def _collect_viral() -> bool:
    """Prompt user for popularity preference."""
    while True:
        ans = input("Do you like viral songs? (yes/no): ").strip().lower()
        if ans in {'yes', 'no'}:
            return ans == 'yes'
        print("Invalid response, please enter yes or no.")

    return False  # Satisfy PythonTA


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

    return 0.0  # Satisfy PythonTA


def _collect_count() -> int:
    """Prompt user for playlist size."""
    while True:
        val = input("How many songs would you like in your playlist? ")
        if val.isdigit() and int(val) > 0:
            return int(val)
        print("Please enter a whole number greater than 0.")

    return 0  # Satisfy PythonTA


if __name__ == '__main__':
    import python_ta
    python_ta.check_all(config={
        'max-line-length': 120,
        'extra-imports': ['time', 'genre_tree', 'song_graph', 'graph_visualization', 'recommender'],
        'allowed-io': ['run_console', '_collect_genres', '_collect_viral',
                       '_collect_energy', '_collect_count', '_should_add_another'],
    })
    run_console()
