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

    preferred_genres = []  # genres the user enjoys
    preferred_energy = 0.0  # minimum energy level (0.0 to 1.0)
    preferred_viral = False  # True = popular songs, False = hidden gems

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

    viral_threshold = 10  # popularity cutoff out of 100

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

            # Check energy filter (always applied)
            meets_energy = song.energy >= preferred_energy

            # Check popularity filter (only applied if user wants viral songs)
            meets_popularity = (song.popularity >= viral_threshold) if preferred_viral else True

            if meets_energy and meets_popularity:
                candidate_songs.add((song.popularity, track_id))

    print(f"Number of songs in user preference filtering stage: {len(candidate_songs)}")

    # Sort candidate songs by popularity (highest first) and take the top N as seeds.
    # These seed songs represent the best match to the user's preferences and will
    # be used to find similar songs via the graph's neighbour edges.
    num_top_ranked = 5
    seed_songs = sorted(list(candidate_songs), reverse=True)[:num_top_ranked]

    print(f"Number of songs in popularity filtering stage: {len(seed_songs)}")

    # For each seed song, look up its neighbours in the song graph.
    # Neighbours are songs connected by an edge, meaning they are acoustically
    # similar based on the cosine angle of their audio features.
    # Each recommended song is stored as (weight, track_name, genre) so the
    # final list can be sorted by similarity weight.
    song_graph_recommendation = set()
    for song in seed_songs:
        neighbours = graph_song.get_song_vertex(song[1]).neighbours
        for neighbour_id, weight in neighbours.items():
            neighbour_song = graph_song.get_song(neighbour_id)
            if neighbour_song is not None:
                song_graph_recommendation.add((weight, neighbour_song.track_name, neighbour_song.genre))

    # Sort recommendations by similarity weight (highest first) and take the top N.
    recommend_n_songs = 10
    final_recommendation = sorted(list(song_graph_recommendation), reverse=True)[:recommend_n_songs]

    # Print final recommendations in a numbered list with song name and genre.
    for i, song in enumerate(final_recommendation):
        print(f"{i + 1}. {song[1]} - {song[2]}")
