import pandas as pd

# Load the CSV
df = pd.read_csv('../unfiltered_spotify_data.csv')

# Drop the first column
df = df.drop(columns=['Unnamed: 0'])

# Save it back to a new CSV
df.to_csv('song_file.csv', index=False)

print(df.head())
print("Done! Saved as song_file.csv")
