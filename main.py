"""
CSC111 Project: Playlistify (Mood-Aware Music Recommendation Engine)

This is the main entry point for Playlistify. It loads song and genre data,
filters songs based on simulated user preferences, and builds a candidate
playlist for further recommendation.

Copyright (c) 2026 Xing Xu Chen, Tianqi Pan, Norah Liu, Denise Ma
"""

import genre_tree
import song_graph


if __name__ == '__main__':
    # Load data structures from CSV
    tree_genre = genre_tree.create_genre_tree('data/spotify_data.csv')
    graph_song = song_graph.load_song_data('data/spotify_data.csv')

    # --- Simulated user preferences (to be replaced with real user input) ---
    preferred_genres = ['rock', 'pop']  # genres the user enjoys
    preferred_energy = 0.5              # minimum energy level (0.0 to 1.0)
    preferred_viral = True              # True = popular songs, False = hidden gems
    viral_threshold = 75                # popularity cutoff out of 100

    # --- Filter candidate songs based on user preferences ---
    candidate_songs = set()

    for genre in preferred_genres:
        genre_node = tree_genre.find(genre)

        # Skip if the genre doesn't exist in the tree
        if genre_node is None:
            continue

        for track_id in genre_node.songs:
            song = graph_song.get_song(track_id)

            # Skip if the song isn't found in the graph
            if song is None:
                continue

            # Check energy and popularity filters
            meets_energy = song.energy >= preferred_energy
            meets_popularity = (song.popularity >= viral_threshold) if preferred_viral else (song.popularity < viral_threshold)

            if meets_energy and meets_popularity:
                candidate_songs.add(track_id)

    print(f"Found {len(candidate_songs)} candidate songs.")
