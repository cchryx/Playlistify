# Extract sub-dataset by random from the songs csv.file
# Chopped out 8000 songs by random
# DON'T HAVE TO RUN IT AGAIN
import pandas as pd


def extract_random_subset(input_path, output_path, n_rows=8000, seed=42):
    chunk_size = 50000
    chunks = []

    print("Reading file in chunks...")
    for chunk in pd.read_csv(input_path, chunksize=chunk_size):
        chunks.append(chunk)

    print("Combining chunks...")
    full_df = pd.concat(chunks)
    print(f"Total rows loaded: {len(full_df)}")

    print(f"Taking random sample of {n_rows} rows...")
    subset = full_df.sample(n=n_rows, random_state=seed)

    subset.to_csv(output_path, index=False)
    print(f"Done! Saved {len(subset)} rows to '{output_path}'")


extract_random_subset(
    input_path="/Users/norah/.cache/kagglehub/datasets/amitanshjoshi/spotify-1million-tracks/versions/1/spotify_data.csv",
    output_path="unfiltered_song_file.csv",
    n_rows=8000,
    seed=42
)
