"""
CSC111 Project: Playlistify (Data Sampling)

Extracts a random subset of songs from the main 1-million track CSV file
to create a manageable local dataset for development.

Copyright (c) 2026 Xing Xu Chen, Tianqi Pan, Norah Liu, Denise Ma
"""

import pandas as pd

# Constants for file paths
INPUT_CSV = (
    "/Users/norah/.cache/kagglehub/datasets/amitanshjoshi/"
    "spotify-1million-tracks/versions/1/spotify_data.csv"
)
OUTPUT_CSV = "../unfiltered_spotify_data.csv"


def extract_random_subset(input_path: str, output_path: str,
                          n_rows: int = 8000, seed: int = 42) -> None:
    """
    Extract a random subset of rows from a large CSV file and save to a new file.
    """
    print(f"Reading data from: {input_path}")

    try:
        full_df = pd.read_csv(input_path)
        subset = full_df.sample(n=n_rows, random_state=seed)
        subset.to_csv(output_path, index=False)
        print(f"Successfully saved {len(subset)} rows to '{output_path}'")

    except FileNotFoundError:
        print("Error: Input file not found. Check your path constants.")


if __name__ == "__main__":
    # extract_random_subset(INPUT_CSV, OUTPUT_CSV)

    import python_ta
    python_ta.check_all(config={
        'max-line-length': 120,
        'extra-imports': ['pandas'],
        'allowed-io': ['extract_random_subset'],
    })
