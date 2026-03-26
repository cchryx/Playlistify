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

    preferred_genres = []   # genres the user enjoys
    preferred_energy = 0.0  # minimum energy level (0.0 to 1.0)
    preferred_viral = False # True = popular songs, False = hidden gems

    # --- Collect preferred genres (allow multiple) ---
    # needs the exact spelling in genre_tree, not case-sensitive
    while True:
        genre = input("Enter a genre you want (must match exact genre or sub-genre in the tree): ")

        if genre not in genre_tree.GENRE_HIERARCHY:
            print("Genre not found in genre tree, try again.")
        else:
            preferred_genres.append(genre)
            another = input("Add another genre? (yes/no): ")
            if another.lower() != 'yes':
                break

    # --- Collect viral song preference ---
    # needs to be either 'yes' or 'no', not case-sensitive
    while True:
        bool_viral_song = input("Do you like viral songs? (yes/no): ")
        if bool_viral_song.lower() == 'yes':
            preferred_viral = True
            break
        elif bool_viral_song.lower() == 'no':
            preferred_viral = False
            break
        else:
            print("Invalid response, please enter yes or no.")

    # --- Collect energy level ---
    # a float between [1, 10], inclusive — mapped to [0.0, 1.0] for song.energy
    while True:
        energy_level = input("Enter your energy level from 1 to 10: ")
        try:
            energy_value = float(energy_level)
            if 1 <= energy_value <= 10:
                preferred_energy = energy_value / 10  # normalize to [0.0, 1.0]
                break
            else:
                print("Invalid energy level, please enter a number between 1 and 10.")
        except ValueError:
            print("Invalid input, please enter a number.")

    print(f"\nPreferences collected:")
    print(f"  Genres: {preferred_genres}")
    print(f"  Viral songs: {preferred_viral}")
    print(f"  Min energy: {preferred_energy}")

    viral_threshold = 75  # popularity cutoff out of 100

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

    print(f"\nFound {len(candidate_songs)} candidate songs.")
