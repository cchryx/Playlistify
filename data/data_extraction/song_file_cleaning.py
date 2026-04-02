"""
CSC111 Project: Playlistify (Data Cleaning)

Cleans the sub-dataset by removing redundant index columns
and saving the final version for the SongGraph to process.

Copyright (c) 2026 Xing Xu Chen, Tianqi Pan, Norah Liu, Denise Ma
"""

import pandas as pd

INPUT_FILE = '../unfiltered_spotify_data.csv'
OUTPUT_FILE = 'song_file.csv'


def clean_song_data(input_path: str, output_path: str) -> None:
    """
    Load the sampled Spotify data, remove the redundant 'Unnamed: 0'
    column, and save the cleaned version.
    """
    try:
        df = pd.read_csv(input_path)
        # Drop redundant index column if it exists
        if 'Unnamed: 0' in df.columns:
            df = df.drop(columns=['Unnamed: 0'])

        df.to_csv(output_path, index=False)
        print(f"Done! Saved {len(df)} rows to '{output_path}'")

    except FileNotFoundError:
        print(f"Error: {input_path} not found.")


if __name__ == "__main__":
    clean_song_data(INPUT_FILE, OUTPUT_FILE)

    import python_ta
    python_ta.check_all(config={
        'max-line-length': 120,
        'extra-imports': ['pandas'],
        'allowed-io': ['clean_song_data'],
    })
