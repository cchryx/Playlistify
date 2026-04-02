"""
CSC111 Project: Playlistify (Data Acquisition)

This script handles the downloading of the Spotify 1-million tracks dataset
from Kaggle using the kagglehub library.

Copyright (c) 2026 Xing Xu Chen, Tianqi Pan, Norah Liu, Denise Ma
"""

import os
import kagglehub


def download_spotify_dataset() -> str:
    """
    Download the Spotify 1-million tracks dataset from Kaggle.

    Returns the local path to the downloaded dataset files.
    """
    os.environ['KAGGLE_CONFIG_DIR'] = os.path.expanduser("~/.kaggle")
    dataset_handle = "amitanshjoshi/spotify-1million-tracks"

    print(f"Downloading dataset: {dataset_handle}...")
    local_path = kagglehub.dataset_download(dataset_handle)

    print(f"Dataset downloaded successfully to: {local_path}")
    return local_path


if __name__ == "__main__":
    download_spotify_dataset()

    import python_ta
    python_ta.check_all(config={
        'max-line-length': 120,
        'extra-imports': ['kagglehub', 'os'],
        'allowed-io': ['download_spotify_dataset'],
    })
