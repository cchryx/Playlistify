"""
CSC111 Project: Playlistify (Mood-Aware Music Recommendation Engine)

This is the main entry point for Playlistify. It loads song and genre data,
filters songs based on simulated user preferences, and builds a candidate
playlist for further recommendation.

Copyright (c) 2026 Xing Xu Chen, Tianqi Pan, Norah Liu, Denise Ma
"""
import time

import genre_tree
import graph_display
import song_graph

if __name__ == '__main__':
    # When you are ready to check your work with python_ta, uncomment the following lines.
    # (Delete the "#" and space before each line.)
    # IMPORTANT: keep this code indented inside the "if __name__ == '__main__'" block
    import python_ta

    python_ta.check_all(config={
        'max-line-length': 120,
        'extra-imports': ['time', 'genre_tree', 'song_graph', 'graph_display'],
        'allowed-io': ['load_song_graph'],
        'disable': []

    })

    print("Loading song graph...")

    start_time = time.perf_counter()

    # Load data structures from CSV
    tree_genre = genre_tree.load_genre_tree('data/spotify_data.csv')
    graph_song = song_graph.load_song_graph('data/spotify_data.csv')

    end_time = time.perf_counter()
    duration = end_time - start_time
    print(f"Loading completed in {duration:.2f} seconds.")

    preferred_genres = []  # genres the user enjoys
    preferred_energy = 0.0  # minimum energy level (0.0 to 1.0)
    preferred_viral = False  # True = popular songs, False = hidden gems
    recommend_n_songs = 0  # number of songs in the playlist

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

    # --- Collect number of songs in playlist ---
    while True:
        num_songs_input = input("How many songs would you like in your playlist? ")
        try:
            recommend_n_songs = int(num_songs_input)
            if recommend_n_songs > 0:
                break
            else:
                print("Please enter a number greater than 0.")
        except ValueError:
            print("Invalid input, please enter a whole number.")

    print("\nPreferences collected:")
    print(f"  Genres: {preferred_genres}")
    print(f"  Viral songs: {preferred_viral}")
    print(f"  Min energy: {preferred_energy}")
    print(f"  Playlist size: {recommend_n_songs}")

    viral_threshold = 10  # popularity cutoff out of 100

    # --- Filter candidate songs based on user preferences ---
    candidate_songs = set()

    for genre in preferred_genres:
        genre_node = tree_genre.find(genre)

        if genre_node is None:
            continue

        for song in graph_song.get_all_songs():
            if song.genre != genre:
                continue

            meets_energy = song.features.energy >= preferred_energy
            meets_popularity = (song.popularity >= viral_threshold) if preferred_viral else True

            if meets_energy and meets_popularity:
                candidate_songs.add((song.popularity, song))

    print(f"Number of songs in user preference filtering stage: {len(candidate_songs)}")

    # Sort candidate songs by popularity (highest first) and take the top N as seeds.
    # These seed songs represent the best match to the user's preferences and will
    # be used to find similar songs via the graph's neighbour edges.
    num_top_ranked = 5
    seed_songs = sorted(list(candidate_songs), key=lambda x: x[0], reverse=True)[:num_top_ranked]

    # For each seed song, look up its neighbours in the song graph.
    # Neighbours are songs connected by an edge, meaning they are acoustically
    # similar based on the cosine angle of their audio features.
    # Each recommended song is stored as (weight, track_name, genre) so the
    # final list can be sorted by similarity weight.
    song_graph_recommendation = set()
    for _, song in seed_songs:
        for neighbour_song in graph_song.get_neighbours(song):
            weight = graph_song.get_weight(song, neighbour_song)
            song_graph_recommendation.add((weight, neighbour_song.track_name, neighbour_song.genre))

    # Sort recommendations by similarity weight (highest first) and take the top N.
    final_recommendation = sorted(list(song_graph_recommendation), reverse=True)[:recommend_n_songs]

    # Print final recommendations in a numbered list with song name and genre.
    print("\nYour playlist:")
    for i, song in enumerate(final_recommendation):
        print(f"{i + 1}. {song[1]} - {song[2]}")

    # GRAPH DISPLAY

    seed_song_objects = [s for _, s in seed_songs]

    song_lookup = {s.track_name: s for s in graph_song.get_all_songs()}

    final_song_objects = set()
    for w, track_name, genre in final_recommendation:
        if track_name in song_lookup:
            final_song_objects.add(song_lookup[track_name])

    graph_display.run_visualization(seed_song_objects, graph_song, final_song_objects)
